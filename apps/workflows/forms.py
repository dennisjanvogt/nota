"""
Forms für Workflow-Verwaltung.
"""
from django import forms
from django.forms import inlineformset_factory
from django.db.models import Q
from .models import WorkflowInstanz, WorkflowSchrittInstanz, WorkflowTyp, WorkflowSchritt
from apps.personen.models import NotarAnwaerter
from apps.services.models import ServiceDefinition
from apps.emails.models import EmailVorlage


class WorkflowInstanzForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Workflow-Instanzen."""

    # Verstecktes Feld für ausgewählte Personen (wird via JavaScript gefüllt)
    betroffene_personen_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = WorkflowInstanz
        fields = [
            'workflow_typ',
            'name',
            'notizen',
        ]
        widgets = {
            'workflow_typ': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Bestellung Max Mustermann'
            }),
            'notizen': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notizen zum Workflow...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur aktive Workflow-Typen anzeigen
        self.fields['workflow_typ'].queryset = WorkflowTyp.objects.filter(ist_aktiv=True)


class WorkflowSchrittAbschlussForm(forms.Form):
    """Form zum Abschließen eines Workflow-Schritts."""

    notizen = forms.CharField(
        required=False,
        label='Abschluss-Notizen',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optionale Notizen zum Abschluss...'
        })
    )


# ===== TEMPLATE-VERWALTUNG FORMS =====

class WorkflowTypForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Workflow-Templates."""

    class Meta:
        model = WorkflowTyp
        fields = ['name', 'kuerzel', 'beschreibung', 'ist_aktiv']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Bestellungsprozess'
            }),
            'kuerzel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. BP',
                'maxlength': '10'
            }),
            'beschreibung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detaillierte Beschreibung des Workflow-Typs...'
            }),
            'ist_aktiv': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'kuerzel': 'Kürzel für Kennung (z.B. BES, BP, NOT)',
            'ist_aktiv': 'Kann dieser Workflow-Typ für neue Instanzen verwendet werden?',
        }


class WorkflowSchrittForm(forms.ModelForm):
    """Form für einzelne Workflow-Schritte."""

    class Meta:
        model = WorkflowSchritt
        fields = ['name', 'beschreibung', 'reihenfolge', 'ist_optional', 'service', 'email_vorlage']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Antrag prüfen'
            }),
            'beschreibung': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Was muss in diesem Schritt gemacht werden?'
            }),
            'reihenfolge': forms.HiddenInput(),  # Wird automatisch durch Drag & Drop gesetzt
            'ist_optional': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'service': forms.Select(attrs={
                'class': 'form-select',
            }),
            'email_vorlage': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'service': 'Verknüpfter Service',
            'email_vorlage': 'E-Mail-Vorlage',
        }
        help_texts = {
            'service': 'Service der bei diesem Schritt ausgeführt werden kann',
            'email_vorlage': 'E-Mail-Vorlage für diesen Schritt',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Nur aktive Services anzeigen
        self.fields['service'].queryset = ServiceDefinition.objects.filter(
            ist_aktiv=True
        ).select_related('kategorie').order_by('kategorie__name', 'name')

        # Service-Feld optional machen
        self.fields['service'].required = False

        # E-Mail-Vorlage-Feld: Nur aktive Vorlagen
        self.fields['email_vorlage'].queryset = EmailVorlage.objects.filter(
            ist_aktiv=True
        ).order_by('kategorie', 'name')

        # E-Mail-Vorlage optional
        self.fields['email_vorlage'].required = False


# Formset für Workflow-Schritte
WorkflowSchrittFormSet = inlineformset_factory(
    WorkflowTyp,
    WorkflowSchritt,
    form=WorkflowSchrittForm,
    extra=1,  # Eine leere Form zum Hinzufügen
    can_delete=True,
    min_num=1,  # Mindestens ein Schritt erforderlich
    validate_min=True,
)


