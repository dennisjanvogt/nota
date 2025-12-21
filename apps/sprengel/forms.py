"""
Forms für Sprengel-Verwaltung.
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Sprengel


class SprengelForm(forms.ModelForm):
    """Form für Sprengel-Erstellung und -Bearbeitung."""

    class Meta:
        model = Sprengel
        fields = [
            'bezeichnung',
            'name',
            'gerichtsbezirk',
            'bundesland',
            'beschreibung',
            'ist_aktiv',
        ]
        widgets = {
            'bezeichnung': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SPR-000001'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Sprengel Wien Innere Stadt'
            }),
            'gerichtsbezirk': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Bezirksgericht Innere Stadt Wien'
            }),
            'bundesland': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beschreibung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Zusätzliche Informationen...'
            }),
            'ist_aktiv': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_bezeichnung(self):
        """Validiert das Format der Sprengel-Bezeichnung: SPR-000001"""
        bezeichnung = self.cleaned_data.get('bezeichnung')
        if bezeichnung and not re.match(r'^SPR-\d{6}$', bezeichnung):
            raise ValidationError(
                'Ungültiges Format. Erwartetes Format: SPR-000001 (3 Buchstaben, Bindestrich, 6 Ziffern)'
            )
        return bezeichnung
