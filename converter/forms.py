from django import forms


class ConvertForm(forms.Form):
    input_format = forms.ChoiceField()
    output_format = forms.ChoiceField()


class FileForm(forms.Form):
    file = forms.FileField()
