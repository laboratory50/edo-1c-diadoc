from django import forms

MAX_SIZE = 64 * 1024


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label='ZIP-архив',
        widget=forms.FileInput(attrs={'accept': '.zip'}),
    )

    def clean_file(self):
        uploaded = self.cleaned_data.get('file')
        if uploaded and uploaded.size > MAX_SIZE:
            raise forms.ValidationError('Файл не должен превышать 64 Кбайт')
        return uploaded
