"""
Forms für Workflow-Verwaltung.
"""
from django import forms
from django.forms import inlineformset_factory
from .models import WorkflowInstanz, WorkflowSchrittInstanz, WorkflowTyp, WorkflowSchritt
from apps.personen.models import NotarAnwaerter


class WorkflowInstanzForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Workflow-Instanzen."""

    class Meta:
        model = WorkflowInstanz
        fields = [
            'workflow_typ',
            'name',
            'betroffene_person',
            'notizen',
        ]
        widgets = {
            'workflow_typ': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Bestellung Max Mustermann'
            }),
            'betroffene_person': forms.Select(attrs={'class': 'form-control'}),
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
        # Nur aktive Anwärter anzeigen
        self.fields['betroffene_person'].queryset = NotarAnwaerter.objects.filter(ist_aktiv=True)
        # Betroffene Person ist optional
        self.fields['betroffene_person'].required = False


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
        fields = ['name', 'beschreibung', 'reihenfolge', 'ist_optional']
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
        }


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


