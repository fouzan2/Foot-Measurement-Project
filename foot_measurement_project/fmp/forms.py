from django import forms

class FootImageForm(forms.Form):
    image = forms.ImageField()
