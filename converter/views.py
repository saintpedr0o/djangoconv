import os
import time
from django.shortcuts import redirect, render
from django.http import (
    FileResponse,
    JsonResponse,
)
from django.urls import reverse
from .utils.converters import get_output_choices
from .forms import ConvertForm, FileForm
from .tasks import convert_task
from celery.result import AsyncResult
from django.conf import settings
import secrets
from .utils.redis_ext_client import redis_client
from celery_progress.backend import Progress
from django.views.decorators.http import require_GET


def get_target_formats_view(request):
    input_format = request.GET.get("input_format")
    choices = get_output_choices(input_format)
    return JsonResponse({"choices": choices})


def select_format_view(request):
    input_format = request.POST.get("input_format") or "markdown"  # default: markdown
    choices = get_output_choices(input_format)

    if request.method == "POST":
        form = ConvertForm(request.POST)
        form.fields["output_format"].choices = choices
        if form.is_valid():
            output_format = form.cleaned_data["output_format"]
            url = reverse(
                "converter:convert",
                kwargs={
                    "input_format": input_format,
                    "output_format": output_format,
                },
            )
            return redirect(url)
    else:
        form = ConvertForm(initial={"input_format": input_format})
        form.fields["output_format"].choices = choices
    return render(request, "converter/convert/select_format.html", {"form": form})


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
            return JsonResponse({"error": "Invalid request"}, status=400)
    else:
        form = FileForm()
    return render(
        request,
        "converter/convert/file_converter.html",
        {
            "form": form,
            "input_format": input_format,
            "output_format": output_format,
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
                "result": f"Unexpected error: {str(e)}",
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
