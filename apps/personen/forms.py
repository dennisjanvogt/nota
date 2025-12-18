"""
Forms für Personen-Verwaltung (Notare und Notar-Anwärter).
"""
from django import forms
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
            'notar_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NOT-001'}),
            'vorname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maria'}),
            'nachname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hofer'}),
            'titel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dr.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'maria.hofer@notariat.at'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+43 1 1234567'}),
            'notarstelle': forms.Select(attrs={'class': 'form-control'}),
            'bestellt_am': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'beginn_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ende_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'war_vorher_anwaerter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notiz': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class NotarAnwaerterForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Notar-Anwärtern."""

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
            'geplante_bestellung',
            'ist_aktiv',
            'notiz',
        ]
        widgets = {
            'anwaerter_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ANW-001'}),
            'vorname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lisa'}),
            'nachname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Schöller'}),
            'titel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mag.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'lisa.schoeller@notariat.at'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+43 1 1234567'}),
            'notarstelle': forms.Select(attrs={'class': 'form-control'}),
            'betreuender_notar': forms.Select(attrs={'class': 'form-control'}),
            'zugelassen_am': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'beginn_datum': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'geplante_bestellung': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notiz': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
