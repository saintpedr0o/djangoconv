from django import forms
from .utils.converters import FORMATS_MAP


format_choices = [(fmt, fmt.upper()) for fmt in FORMATS_MAP.keys()]


class ConvertForm(forms.Form):
    input_format = forms.ChoiceField(choices=format_choices)
    output_format = forms.ChoiceField(choices=[])  # ajax


class FileForm(forms.Form):
    file = forms.FileField()
