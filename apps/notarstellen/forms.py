"""
Forms für Notarstellen-Verwaltung.
"""
from django import forms
from .models import Notarstelle


class NotarstelleForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Notarstellen."""

    class Meta:
        model = Notarstelle
        fields = [
            'notarnummer',
            'bezeichnung',
            'name',
            'strasse',
            'plz',
            'stadt',
            'bundesland',
            'telefon',
            'email',
            'ist_aktiv',
            'besetzt_seit',
            'notiz',
        ]
        widgets = {
            'notarnummer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. 1'}),
            'bezeichnung': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. NOT-1'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Notariat Wien 1'}),
            'strasse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Stephansplatz 3'}),
            'plz': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. 1010'}),
            'stadt': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'z.B. Wien'}),
            'bundesland': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', '-- Bundesland wählen --'),
                ('Wien', 'Wien'),
                ('Niederösterreich', 'Niederösterreich'),
                ('Burgenland', 'Burgenland'),
                ('Oberösterreich', 'Oberösterreich'),
                ('Salzburg', 'Salzburg'),
                ('Steiermark', 'Steiermark'),
                ('Kärnten', 'Kärnten'),
                ('Tirol', 'Tirol'),
                ('Vorarlberg', 'Vorarlberg'),
            ]),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+43 1 1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'office@notariat.at'}),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'besetzt_seit': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notiz': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
