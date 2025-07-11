from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings


class ConvertForm(forms.Form):
    input_format = forms.ChoiceField()
    output_format = forms.ChoiceField()


class FileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data.get("file")
        max_size = settings.MAX_FORM_FILE_SIZE

        if file and file.size > max_size:
            raise ValidationError(f"Max file size is {max_size / (1024 ** 3):.1f} GB")
        return file
