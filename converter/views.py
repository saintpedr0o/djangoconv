import os
import time
import secrets
from django.shortcuts import render
from django.http import FileResponse, JsonResponse
from django.urls import reverse
from .utils.cache_func import get_input_choices, get_output_choices
from .utils.redis_ext_client import redis_client
from .forms import ConvertForm, FileForm
from .tasks import convert_task
from celery.result import AsyncResult
from django.conf import settings
from celery_progress.backend import Progress
from .models import FormatType
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.views import View


class GetTargetFormatView(View):
    http_method_names = ["get"]

    def get(self, request):
        input_format = request.GET.get("input_format")
        if not input_format:
            return JsonResponse({"choices": []})
        return JsonResponse({"choices": get_output_choices(input_format)})


class SelectFileView(TemplateView):
    template_name = "converter/convert/select_file.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["format_types"] = FormatType.choices
        return context


class SelectFormatView(FormView):
    template_name = "converter/convert/select_format.html"
    form_class = ConvertForm

    def dispatch(self, request, *args, **kwargs):
        self.category = kwargs["category"]
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        input_choices = get_input_choices(self.category)
        selected_input = (
            self.request.POST.get("input_format")
            or self.request.GET.get("input_format")
            or (input_choices[0][0] if input_choices else None)
        )

        output_choices = get_output_choices(selected_input) if selected_input else []
        selected_output = (
            self.request.POST.get("output_format")
            or self.request.GET.get("output_format")
            or (output_choices[0][0] if output_choices else None)
        )

        self.input_choices = input_choices
        self.output_choices = output_choices

        return {
            "input_format": selected_input,
            "output_format": selected_output,
        }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["input_format"].choices = self.input_choices
        form.fields["output_format"].choices = self.output_choices
        return form

    def form_valid(self, form):
        self.cleaned_data = form.cleaned_data
        self.request.session["input_format"] = form.cleaned_data["input_format"]
        self.request.session["output_format"] = form.cleaned_data["output_format"]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("converter:convert", kwargs=self.cleaned_data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class ConvertView(FormView):
    form_class = FileForm
    template_name = "converter/convert/file_converter.html"

    def dispatch(self, request, *args, **kwargs):
        self.input_format = kwargs.get("input_format")
        self.output_format = kwargs.get("output_format")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "input_format": self.input_format,
                "output_format": self.output_format,
                "MAX_FORM_FILE_SIZE": settings.MAX_FORM_FILE_SIZE,
            }
        )
        return context

    def form_valid(self, form):
        file = form.cleaned_data["file"]
        file_bin = file.read()
        token = secrets.token_urlsafe(16)
        task = convert_task.delay(
            file_bin, self.input_format, self.output_format, token
        )
        redis_client.setex(f"conv:{token}", settings.FILE_TTL, task.id)
        progress_url = reverse("converter:convert_progress_info", args=[token])
        return JsonResponse({"token": token, "redirect_url": progress_url})

    def form_invalid(self, form):
        return JsonResponse({"error": form.errors.as_text()}, status=400)


class ProgressbarView(TemplateView):
    template_name = "converter/convert/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"] = kwargs.get("token")
        return context


class ConvertProgressView(View):
    http_method_names = ["get"]

    def get(self, request, token, *args, **kwargs):
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

        except Exception:
            return JsonResponse(
                {
                    "complete": True,
                    "success": False,
                    "result": "Unexpected error",
                }
            )


class DownloadFileView(View):
    http_method_names = ["get"]

    def get(self, request, token):
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
