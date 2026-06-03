from django import forms
from .models import Voyageur, Expedition

class VoyageurForm(forms.ModelForm):
    class Meta:
        model = Voyageur
        fields = '__all__'

class ExpeditionForm(forms.ModelForm):
    class Meta:
        model = Expedition
        fields = '__all__'
