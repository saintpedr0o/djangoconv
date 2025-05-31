from django import forms
from .utils import DOC_FORMATS, IMAGE_FORMATS, AUDIO_FORMATS, VIDEO_FORMATS


doc_choices = [(fmt, fmt.upper()) for fmt in DOC_FORMATS.keys()]
img_choices = [(fmt, fmt) for fmt in IMAGE_FORMATS.keys()]
aud_choices = [(fmt, fmt.upper()) for fmt in AUDIO_FORMATS.keys()]
vid_choices = [(fmt, fmt) for fmt in VIDEO_FORMATS.keys()]

class ConvertForm(forms.Form):
    input_format = forms.ChoiceField(choices=doc_choices+img_choices+aud_choices+vid_choices)
    output_format = forms.ChoiceField(choices=[]) #ajax


class FileForm(forms.Form):
    file = forms.FileField()