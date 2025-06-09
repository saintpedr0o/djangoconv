import os
from django.shortcuts import redirect, render
from django.http import (
    FileResponse,
    JsonResponse,
)
from django.urls import reverse
from .utils import get_output_choices
from .forms import ConvertForm, FileForm
from .tasks import convert_task
from celery.result import AsyncResult


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
            task = convert_task.delay(file_bin, input_format, output_format)
            progress_url = reverse("converter:convert_progress", args=[task.id])
            return JsonResponse({"task_id": task.id, "redirect_url": progress_url})
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


def convert_progress_view(request, task_id):
    return render(request, "converter/convert/progress.html", {"task_id": task_id})


def download_file_view(request, task_id):
    result = AsyncResult(task_id)
    temp_path = result.result

    if not temp_path or not os.path.exists(temp_path):
        return render(request, "converter/file_not_found.html")

    response = FileResponse(
        open(temp_path, "rb"), as_attachment=True, filename=os.path.basename(temp_path)
    )
    return response
