"""
Forms für Benutzer-Verwaltung.
"""
from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import KammerBenutzer


class ProfilBearbeitenForm(forms.ModelForm):
    """
    Formular zur Bearbeitung des eigenen Benutzerprofils.
    """
    class Meta:
        model = KammerBenutzer
        fields = ['first_name', 'last_name', 'email', 'telefon', 'abteilung', 'profilbild']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'abteilung': forms.TextInput(attrs={'class': 'form-control'}),
            'profilbild': forms.FileInput(attrs={'class': 'form-control'}),
        }
