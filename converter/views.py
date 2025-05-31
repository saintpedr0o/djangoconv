from django.shortcuts import redirect, render
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from .utils import DOC_FORMATS, IMAGE_FORMATS, ImageConverter, DocConverter, get_output_choices, AudioConverter, AUDIO_FORMATS, VIDEO_FORMATS, VideoConverter
from .forms import ConvertForm, FileForm


def get_target_formats_view(request):
    input_format = request.GET.get("input_format")
    choices = get_output_choices(input_format)
    return JsonResponse({'choices': choices})

def select_format_view(request):
    input_format = request.POST.get('input_format')
    choices = get_output_choices(input_format)

    if request.method == 'POST':
        form = ConvertForm(request.POST)
        form.fields['output_format'].choices = choices
        if form.is_valid():
            output_format = form.cleaned_data['output_format']
            url = reverse('convert', kwargs={ 'input_format': input_format, 'output_format': output_format,})
            return redirect(url)
    else:
        form = ConvertForm()
    return render(request, 'converter/convert/select_format.html', {'form': form})

def convert_view(request, input_format, output_format):
    
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            file = cd['file']
            if output_format in DOC_FORMATS:
                converter = DocConverter()
            elif output_format in IMAGE_FORMATS:
                converter = ImageConverter()
            elif output_format in AUDIO_FORMATS:
                converter = AudioConverter()
            elif output_format in VIDEO_FORMATS:
                converter = VideoConverter()
            else:
                raise Http404 
            
            out_file = converter.convert(file, output_format)
            response = HttpResponse(out_file)
            filename = file.name.rsplit('.')[0]
            response['Content-Disposition'] = f'attachment; filename="converted_{filename}.{output_format}"'
            return response   #подумать как возвращать мб чето переделать

    else:
        form = FileForm()
    return render(request, 'converter/convert/file_converter.html', {'form': form, 'input_format': input_format, 'output_format': output_format})