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
    anwaerter_ids = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label='Notariatskandidat'
    )

    def clean_anwaerter_ids(self):
        """Parse und validiere kandidat IDs aus dem Autocomplete-Format."""
        encoded = self.cleaned_data.get('anwaerter_ids', '')

        if not encoded:
            raise forms.ValidationError('Bitte wählen Sie mindestens einen Kandidat aus.')

        # Parse "kandidat:ID,kandidat:ID,..." Format
        anwaerter_ids = []
        for item in encoded.split(','):
            if ':' not in item:
                continue
            typ, person_id = item.split(':', 1)

            # Nur Kandidaten erlaubt
            if typ != 'kandidat':
                raise forms.ValidationError('Es können nur Notariatskandidaten ausgewählt werden.')

            anwaerter_ids.append(person_id)

        if len(anwaerter_ids) == 0:
            raise forms.ValidationError('Bitte wählen Sie mindestens einen Kandidat aus.')

        # Validiere dass alle IDs existieren und hole die numerischen Datenbank-IDs
        kandidaten = NotarAnwaerter.objects.filter(
            anwaerter_id__in=anwaerter_ids,
            ist_aktiv=True
        )

        if kandidaten.count() != len(anwaerter_ids):
            raise forms.ValidationError('Einer oder mehrere ausgewählte Kandidaten existieren nicht oder sind inaktiv.')

        # Rückgabe: Liste der numerischen Datenbank-IDs (nicht anwaerter_id!)
        return list(kandidaten.values_list('id', flat=True))


class BesetzungsvorschlagForm(forms.Form):
    """Form für Besetzungsvorschlag Service."""
    kandidaten_ids = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        label='Kandidaten (genau 3 in Prioritätsreihenfolge)',
        help_text='Wählen Sie genau 3 Kandidaten in Prioritätsreihenfolge'
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

    def clean_kandidaten_ids(self):
        """Parse und validiere exakt 3 Kandidaten-IDs in Prioritätsreihenfolge."""
        encoded = self.cleaned_data.get('kandidaten_ids', '')

        if not encoded:
            raise forms.ValidationError('Bitte wählen Sie genau 3 Kandidaten in Prioritätsreihenfolge aus.')

        # Parse "kandidat:ID,kandidat:ID,kandidat:ID" Format
        anwaerter_ids = []
        for item in encoded.split(','):
            if ':' not in item:
                continue
            typ, person_id = item.split(':', 1)

            # Nur Kandidaten erlaubt
            if typ != 'kandidat':
                raise forms.ValidationError('Es können nur Notariatskandidaten ausgewählt werden.')

            anwaerter_ids.append(person_id)

        # Validiere exakt 3 Kandidaten
        if len(anwaerter_ids) != 3:
            raise forms.ValidationError(f'Sie müssen genau 3 Kandidaten auswählen (aktuell: {len(anwaerter_ids)}).')

        # Validiere keine Duplikate
        if len(anwaerter_ids) != len(set(anwaerter_ids)):
            raise forms.ValidationError('Sie können nicht denselben Kandidat mehrfach auswählen.')

        # Kandidaten in der richtigen Reihenfolge laden
        kandidaten_dict = {
            k.anwaerter_id: k.id
            for k in NotarAnwaerter.objects.filter(
                anwaerter_id__in=anwaerter_ids,
                ist_aktiv=True
            )
        }

        if len(kandidaten_dict) != 3:
            raise forms.ValidationError('Einer oder mehrere ausgewählte Kandidaten existieren nicht oder sind inaktiv.')

        # Rückgabe: Liste der numerischen IDs IN DER GLEICHEN REIHENFOLGE
        return [kandidaten_dict[anwaerter_id] for anwaerter_id in anwaerter_ids]


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
