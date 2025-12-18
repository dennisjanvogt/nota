"""
Forms für Aktenzeichen-Verwaltung.
"""
from django import forms
from .models import Aktenzeichen, Nummernsequenz
from django.utils import timezone


class AktenzeichenForm(forms.ModelForm):
    """Form für Erstellen eines neuen Aktenzeichens."""

    class Meta:
        model = Aktenzeichen
        fields = [
            'kategorie',
            'beschreibung',
        ]
        widgets = {
            'kategorie': forms.Select(attrs={'class': 'form-control'}),
            'beschreibung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Kurze Beschreibung des Vorgangs...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Kategorie ist Pflichtfeld
        self.fields['kategorie'].required = True

    def save(self, commit=True):
        """
        Speichert das Aktenzeichen und generiert automatisch die Nummer.

        Die Sequenz und Laufnummer werden automatisch basierend auf der
        gewählten Kategorie und dem aktuellen Jahr generiert.
        """
        aktenzeichen = super().save(commit=False)

        # Mapping von Kategorie zu Präfix
        kategorie_praefix_map = {
            'Bestellung': 'BES',
            'Zulassung': 'ZUL',
            'Aufsicht': 'AUF',
            'Allgemein': 'ALL',
        }

        praefix = kategorie_praefix_map.get(aktenzeichen.kategorie, 'ALL')
        aktuelles_jahr = timezone.now().year

        # Sequenz holen oder erstellen (thread-safe)
        from django.db import transaction
        with transaction.atomic():
            sequenz, created = Nummernsequenz.objects.select_for_update().get_or_create(
                jahr=aktuelles_jahr,
                praefix=praefix,
                defaults={'aktuelle_nummer': 0}
            )

            # Nächste Nummer holen
            naechste_nummer = sequenz.naechste_nummer_holen()

            # Aktenzeichen-Felder setzen
            aktenzeichen.sequenz = sequenz
            aktenzeichen.laufnummer = naechste_nummer
            aktenzeichen.jahr = aktuelles_jahr

            if commit:
                aktenzeichen.save()

        return aktenzeichen
