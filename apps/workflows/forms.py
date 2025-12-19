"""
Forms für Workflow-Verwaltung.
"""
from django import forms
from .models import WorkflowInstanz, WorkflowSchrittInstanz, WorkflowTyp
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


