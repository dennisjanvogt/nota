"""
Forms für Personen-Verwaltung (Notare und Notariatskandidat).
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Notar, NotarAnwaerter


class NotarForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Notaren."""

    class Meta:
        model = Notar
        fields = [
            'notar_id',
            'vorname',
            'nachname',
            'titel',
            'email',
            'telefon',
            'notarstelle',
            'bestellt_am',
            'beginn_datum',
            'ende_datum',
            'war_vorher_anwaerter',
            'ist_aktiv',
            'notiz',
        ]
        widgets = {
            'notar_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NOT-000001'}),
            'vorname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maria'}),
            'nachname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hofer'}),
            'titel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dr.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'maria.hofer@notariat.at'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+43 1 1234567'}),
            'notarstelle': forms.Select(attrs={'class': 'form-control'}),
            'bestellt_am': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'beginn_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'ende_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'war_vorher_anwaerter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notiz': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_notar_id(self):
        """Validiert das Format der Notar-ID: NOT-000001"""
        notar_id = self.cleaned_data.get('notar_id')
        if notar_id and not re.match(r'^NOT-\d{6}$', notar_id):
            raise ValidationError(
                'Ungültiges Format. Erwartetes Format: NOT-000001 (3 Buchstaben, Bindestrich, 6 Ziffern)'
            )
        return notar_id


class NotarAnwaerterForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Notariatskandidatn."""

    class Meta:
        model = NotarAnwaerter
        fields = [
            'anwaerter_id',
            'vorname',
            'nachname',
            'titel',
            'email',
            'telefon',
            'notarstelle',
            'betreuender_notar',
            'zugelassen_am',
            'beginn_datum',
            'ist_aktiv',
            'notiz',
        ]
        widgets = {
            'anwaerter_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NKA-000001'}),
            'vorname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lisa'}),
            'nachname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Schöller'}),
            'titel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mag.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'lisa.schoeller@notariat.at'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+43 1 1234567'}),
            'notarstelle': forms.Select(attrs={'class': 'form-control'}),
            'betreuender_notar': forms.Select(attrs={'class': 'form-control'}),
            'zugelassen_am': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'beginn_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notiz': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_anwaerter_id(self):
        """Validiert das Format der Kandidaten-ID: NKA-000001"""
        anwaerter_id = self.cleaned_data.get('anwaerter_id')
        if anwaerter_id and not re.match(r'^NKA-\d{6}$', anwaerter_id):
            raise ValidationError(
                'Ungültiges Format. Erwartetes Format: NKA-000001 (3 Buchstaben, Bindestrich, 6 Ziffern)'
            )
        return anwaerter_id
