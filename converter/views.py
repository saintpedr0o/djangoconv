import os
import time
from django.shortcuts import redirect, render
from django.http import FileResponse, JsonResponse
from django.urls import reverse
from .utils.cache_func import get_input_choices, get_output_choices
from .utils.redis_ext_client import redis_client
from .forms import ConvertForm, FileForm
from .tasks import convert_task
from celery.result import AsyncResult
from django.conf import settings
import secrets
from celery_progress.backend import Progress
from django.views.decorators.http import require_GET
from .models import FormatType


def get_target_formats_view(request):
    input_format = request.GET.get("input_format")
    choices = get_output_choices(input_format)
    return JsonResponse({"choices": choices})


def select_file_view(request):
    format_types = FormatType.choices
    return render(
        request, "converter/convert/select_file.html", {"format_types": format_types}
    )


def select_format_view(request, category):
    input_choices = get_input_choices(category)
    selected_input = input_choices[0][0]
    output_choices = get_output_choices(selected_input)
    form = ConvertForm(
        data=request.POST if request.method == "POST" else None,
        initial={
            "input_format": selected_input,
        }
    )
    form.fields["input_format"].choices = input_choices
    form.fields["output_format"].choices = output_choices

    if request.method == "POST" and form.is_valid():
        return redirect(reverse("converter:convert", kwargs=form.cleaned_data))

    return render(request, "converter/convert/select_format.html", {
        "form": form,
        "category": category,
    })


def convert_view(request, input_format, output_format):
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            file_bin = file.read()
            token = secrets.token_urlsafe(16)
            task = convert_task.delay(file_bin, input_format, output_format, token)
            redis_client.setex(f"conv:{token}", settings.FILE_TTL, task.id)
            progress_url = reverse("converter:convert_progress_info", args=[token])
            return JsonResponse({"token": token, "redirect_url": progress_url})
        else:
            return JsonResponse({"error": form.errors.as_text()}, status=400)
    else:
        form = FileForm()
    return render(
        request,
        "converter/convert/file_converter.html",
        {
            "form": form,
            "input_format": input_format,
            "output_format": output_format,
            'MAX_FORM_FILE_SIZE': settings.MAX_FORM_FILE_SIZE,
        },
    )


def convert_progressbar(request, token):
    return render(
        request,
        "converter/convert/progress.html",
        {"token": token},
    )


@require_GET
def convert_progress_view(request, token):
    try:
        task_id = redis_client.get(f"conv:{token}")
        if not task_id:
            return JsonResponse(
                {
                    "complete": True,
                    "success": False,
                    "result": "Invalid convert token",
                }
            )
        task_result = AsyncResult(task_id.decode())
        if task_result.failed():
            return JsonResponse(
                {
                    "complete": True,
                    "success": False,
                    "result": "Conversion task failed",
                }
            )

        progress_data = Progress(task_result).get_info()
        return JsonResponse(progress_data)

    except Exception as e:
        return JsonResponse(
            {
                "complete": True,
                "success": False,
                "result": f"Unexpected error",
            }
        )


def download_file_view(request, token):
    temp_path = redis_client.get(f"path:{token}")
    if not temp_path:
        return render(request, "converter/file_not_found.html")

    temp_path = temp_path.decode()

    if (
        not os.path.exists(temp_path)
        or (time.time() - os.path.getmtime(temp_path)) > settings.FILE_TTL
    ):
        return render(request, "converter/file_not_found.html")

    try:
        return FileResponse(
            open(temp_path, "rb"),
            as_attachment=True,
            filename=os.path.basename(temp_path),
        )
    except OSError:
        return render(request, "converter/file_not_found.html")
