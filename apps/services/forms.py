"""
Service-Forms für benutzerfreundliche Service-Ausführung.
"""
from django import forms
from apps.personen.models import NotarAnwaerter, Notar
from apps.notarstellen.models import Notarstelle
from apps.services.models import Dokument
from apps.emails.models import EmailVorlage


# --- Dokument-Services ---

class StammblattPDFEinzelnForm(forms.Form):
    """Form für Stammblatt-PDF Einzeln Service."""
    anwaerter = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='Notariatskandidat',
        help_text='Wählen Sie den Kandidat aus',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class StammblattPDFMassenForm(forms.Form):
    """Form für Stammblatt-PDF Masse Service."""
    anwaerter = forms.ModelMultipleChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='Notariatskandidat',
        help_text='Wählen Sie mehrere Kandidat aus (Strg/Cmd + Klick)',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'})
    )


class BesetzungsvorschlagForm(forms.Form):
    """Form für Besetzungsvorschlag Service."""
    anwaerter_1 = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='1. Priorität',
        help_text='Erster Kandidat',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    anwaerter_2 = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='2. Priorität',
        help_text='Zweiter Kandidat',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    anwaerter_3 = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='3. Priorität',
        help_text='Dritter Kandidat',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notarstelle = forms.ModelChoiceField(
        queryset=Notarstelle.objects.filter(ist_aktiv=True),
        label='Zu besetzende Notarstelle',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empfehlung = forms.CharField(
        required=False,
        label='Empfehlung der Kammer',
        help_text='Optionaler Empfehlungstext',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )

    def clean(self):
        """Validiert dass alle 3 Kandidat unterschiedlich sind."""
        cleaned_data = super().clean()
        anwaerter_1 = cleaned_data.get('anwaerter_1')
        anwaerter_2 = cleaned_data.get('anwaerter_2')
        anwaerter_3 = cleaned_data.get('anwaerter_3')

        if anwaerter_1 and anwaerter_2 and anwaerter_1 == anwaerter_2:
            raise forms.ValidationError('Die ersten beiden Kandidaten dürfen nicht identisch sein.')

        if anwaerter_1 and anwaerter_3 and anwaerter_1 == anwaerter_3:
            raise forms.ValidationError('Der erste und dritte Kandidat dürfen nicht identisch sein.')

        if anwaerter_2 and anwaerter_3 and anwaerter_2 == anwaerter_3:
            raise forms.ValidationError('Der zweite und dritte Kandidat dürfen nicht identisch sein.')

        return cleaned_data


# --- E-Mail-Services ---

class StrafregisterauszugAnfordernForm(forms.Form):
    """Form für Strafregisterauszug anfordern Service."""
    anwaerter = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='Notariatskandidat',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    vorlage = forms.ModelChoiceField(
        queryset=EmailVorlage.objects.filter(kategorie='strafregister', ist_aktiv=True),
        label='E-Mail-Vorlage',
        required=False,
        help_text='Optional: Spezifische Vorlage wählen',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class UnterlagenAnReferentenSendenForm(forms.Form):
    """Form für Unterlagen an Referenten senden Service."""
    dokumente = forms.ModelMultipleChoiceField(
        queryset=Dokument.objects.all(),
        label='Anzuhängende Dokumente',
        help_text='Wählen Sie die Dokumente aus (Strg/Cmd + Klick)',
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'})
    )
    vorlage = forms.ModelChoiceField(
        queryset=EmailVorlage.objects.filter(ist_aktiv=True),
        label='E-Mail-Vorlage',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    betreff = forms.CharField(
        required=False,
        max_length=200,
        label='Eigener Betreff',
        help_text='Optional: Überschreibt Vorlage',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    nachricht = forms.CharField(
        required=False,
        label='Eigene Nachricht',
        help_text='Optional: Überschreibt Vorlage',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )

    def clean_dokumente(self):
        """Validiert dass mindestens 1 Dokument ausgewählt wurde."""
        dokumente = self.cleaned_data['dokumente']
        if len(dokumente) == 0:
            raise forms.ValidationError('Bitte wählen Sie mindestens 1 Dokument aus.')
        return dokumente

    def __init__(self, *args, workflow_instanz=None, **kwargs):
        """Filter Dokumente basierend auf Workflow."""
        super().__init__(*args, **kwargs)
        if workflow_instanz:
            # Nur Dokumente des Workflows anzeigen
            self.fields['dokumente'].queryset = workflow_instanz.dokumente.all()


# --- Workflow-Services ---

class AnwaerterZuNotarBefoerdernForm(forms.Form):
    """Form für Kandidat zu Notar befördern Service."""
    anwaerter = forms.ModelChoiceField(
        queryset=NotarAnwaerter.objects.filter(ist_aktiv=True),
        label='Notariatskandidat',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notarstelle = forms.ModelChoiceField(
        queryset=Notarstelle.objects.filter(ist_aktiv=True),
        label='Notarstelle',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    bestellt_am = forms.DateField(
        required=False,
        label='Bestellungsdatum',
        help_text='Optional: Standard = heute',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


# --- Form-Factory ---

def get_service_form_class(service_id):
    """
    Gibt die passende Form-Klasse für einen Service zurück.

    Args:
        service_id: Die Service-ID

    Returns:
        Form-Klasse oder None
    """
    FORM_MAPPING = {
        'stammblatt_pdf_einzeln': StammblattPDFEinzelnForm,
        'stammblatt_pdf_masse': StammblattPDFMassenForm,
        'besetzungsvorschlag_erstellen': BesetzungsvorschlagForm,
        'strafregisterauszug_anfordern': StrafregisterauszugAnfordernForm,
        'unterlagen_an_referenten_senden': UnterlagenAnReferentenSendenForm,
        'anwaerter_zu_notar_befoerdern': AnwaerterZuNotarBefoerdernForm,
    }
    return FORM_MAPPING.get(service_id)
