from django.shortcuts import redirect, render
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from .utils import get_output_choices, FORMATS_MAP
from .forms import ConvertForm, FileForm
import uuid


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
    entry = FORMATS_MAP.get(input_format)
    if not entry or output_format not in entry["outputs"]:
        raise Http404(f"Unsupported conversion: {input_format} -> {output_format}")

    converter = entry["converter"]
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]
            out_file = converter.convert(file, output_format)
            response = HttpResponse(out_file)
            filename = uuid.uuid4().hex[:10]
            response["Content-Disposition"] = (
                f'attachment; filename="converted_{filename}.{output_format}"'
            )
            return response
    else:
        form = FileForm()
    return render(
        request,
        "converter/convert/file_converter.html",
        {"form": form, "input_format": input_format, "output_format": output_format},
    )
