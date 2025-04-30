from django import forms
from .models import *

class GalloForm(forms.ModelForm):
    class Meta:
        model = Gallo
        exclude = ['placaPadre', 'placaMadre']
        widgets = {
            'nroPlaca': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'tipoGallo': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nombre_img': forms.FileInput(attrs={'class': 'form-control'}),
        }

    fechaNac = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label="Fecha de Nacimiento"
    )

class EncuentroForm(forms.ModelForm):
    class Meta:
        model = Encuentro
        fields = [
            'fechaYHora', 'galpon1', 'galpon2', 'video',
            'pactada', 'pago_juez', 'apuesta_general',
            'premio_mayor', 'porcentaje_premio_mayor', 'apuesta_por_fuera'
        ]
        widgets = {
            'fechaYHora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'video': forms.ClearableFileInput(attrs={'accept': 'video/*'})
        }

    def __init__(self, *args, **kwargs):
        super(EncuentroForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[field].label
            })
        self.fields['video'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        participantes = self.data.getlist("participantes")
        if len(participantes) < 2:
            raise forms.ValidationError("Debe seleccionar al menos 2 participantes.")
        return cleaned_data
