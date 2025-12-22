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

        # Service QuerySet: Nur aktive Services anzeigen
        service_qs = ServiceDefinition.objects.filter(ist_aktiv=True)

        # Falls bestehender Schritt einen inaktiven Service hat, füge ihn hinzu
        if self.instance and self.instance.pk and self.instance.service:
            if not self.instance.service.ist_aktiv:
                service_qs = ServiceDefinition.objects.filter(
                    Q(ist_aktiv=True) | Q(id=self.instance.service.id)
                )

        self.fields['service'].queryset = service_qs.select_related('kategorie').order_by('kategorie__name', 'name')
        self.fields['service'].required = False
        self.fields['service'].empty_label = "---------"  # Explizit leere Option

        # E-Mail-Vorlage QuerySet: Nur aktive Vorlagen anzeigen
        email_qs = EmailVorlage.objects.filter(ist_aktiv=True)

        # Falls bestehender Schritt eine inaktive E-Mail-Vorlage hat, füge sie hinzu
        if self.instance and self.instance.pk and self.instance.email_vorlage:
            if not self.instance.email_vorlage.ist_aktiv:
                email_qs = EmailVorlage.objects.filter(
                    Q(ist_aktiv=True) | Q(id=self.instance.email_vorlage.id)
                )

        self.fields['email_vorlage'].queryset = email_qs.order_by('kategorie', 'name')
        self.fields['email_vorlage'].required = False
        self.fields['email_vorlage'].empty_label = "---------"  # Explizit leere Option


# Formset für Workflow-Schritte
WorkflowSchrittFormSet = inlineformset_factory(
    WorkflowTyp,
    WorkflowSchritt,
    form=WorkflowSchrittForm,
    extra=0,  # KEIN extra-Formular (Nutzer klickt "Schritt hinzufügen" Button)
    can_delete=True,
    min_num=1,  # Mindestens ein Schritt erforderlich
    validate_min=True,
)


