"""
Forms für Workflow-Verwaltung.
"""
from django import forms
from .models import WorkflowInstanz, WorkflowSchrittInstanz, WorkflowKommentar, WorkflowTyp
from apps.personen.models import NotarAnwaerter
from apps.aktenzeichen.models import Aktenzeichen


class WorkflowInstanzForm(forms.ModelForm):
    """Form für Erstellen und Bearbeiten von Workflow-Instanzen."""

    class Meta:
        model = WorkflowInstanz
        fields = [
            'workflow_typ',
            'name',
            'betroffene_person',
            'faellig_am',
            'notizen',
        ]
        widgets = {
            'workflow_typ': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Bestellung Max Mustermann'
            }),
            'betroffene_person': forms.Select(attrs={'class': 'form-control'}),
            'faellig_am': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
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
        # Nur aktive Anwärter anzeigen
        self.fields['betroffene_person'].queryset = NotarAnwaerter.objects.filter(ist_aktiv=True)
        # Betroffene Person ist optional
        self.fields['betroffene_person'].required = False


class WorkflowSchrittZuweisungForm(forms.Form):
    """Form zum Zuweisen eines Schritts an einen Benutzer."""

    zugewiesen_an = forms.ModelChoiceField(
        queryset=None,  # Wird in __init__ gesetzt
        required=False,
        label='Zuweisen an',
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='(Nicht zugewiesen)'
    )

    def __init__(self, *args, **kwargs):
        from apps.benutzer.models import KammerBenutzer
        super().__init__(*args, **kwargs)
        # Alle aktiven Benutzer
        self.fields['zugewiesen_an'].queryset = KammerBenutzer.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')


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


class WorkflowKommentarForm(forms.ModelForm):
    """Form zum Hinzufügen eines Kommentars."""

    class Meta:
        model = WorkflowKommentar
        fields = ['kommentar']
        widgets = {
            'kommentar': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Kommentar schreiben...'
            }),
        }
