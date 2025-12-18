"""
Filter-Formulare für Berichte.
"""
from django import forms
from apps.notarstellen.models import Notarstelle
from apps.workflows.models import WorkflowTyp


class NotareFilterForm(forms.Form):
    """Filter-Formular für Notare-Berichte."""

    STATUS_CHOICES = [
        ('', 'Alle'),
        ('aktiv', 'Nur Aktive'),
        ('inaktiv', 'Nur Inaktive'),
    ]

    search = forms.CharField(
        label='Suche',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name, ID oder E-Mail...'
        })
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    notarstelle = forms.ModelChoiceField(
        label='Notarstelle',
        queryset=Notarstelle.objects.all(),
        required=False,
        empty_label='Alle',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    bestellt_von = forms.DateField(
        label='Bestellt von',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    bestellt_bis = forms.DateField(
        label='Bestellt bis',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class AnwaerterFilterForm(forms.Form):
    """Filter-Formular für Notar-Anwärter-Berichte."""

    STATUS_CHOICES = [
        ('', 'Alle'),
        ('aktiv', 'Nur Aktive'),
        ('inaktiv', 'Nur Inaktive'),
    ]

    BESTELLUNG_CHOICES = [
        ('', 'Alle'),
        ('geplant', 'Mit geplanter Bestellung'),
        ('nicht_geplant', 'Ohne geplante Bestellung'),
    ]

    search = forms.CharField(
        label='Suche',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name, ID oder E-Mail...'
        })
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    notarstelle = forms.ModelChoiceField(
        label='Notarstelle',
        queryset=Notarstelle.objects.all(),
        required=False,
        empty_label='Alle',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    bestellung_status = forms.ChoiceField(
        label='Bestellungsstatus',
        choices=BESTELLUNG_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    zugelassen_von = forms.DateField(
        label='Zugelassen von',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    zugelassen_bis = forms.DateField(
        label='Zugelassen bis',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class NotarstellenFilterForm(forms.Form):
    """Filter-Formular für Notarstellen-Berichte."""

    STATUS_CHOICES = [
        ('', 'Alle'),
        ('aktiv', 'Nur Aktive'),
        ('inaktiv', 'Nur Inaktive'),
    ]

    BUNDESLAND_CHOICES = [
        ('', 'Alle'),
        ('Wien', 'Wien'),
        ('Niederösterreich', 'Niederösterreich'),
        ('Oberösterreich', 'Oberösterreich'),
        ('Salzburg', 'Salzburg'),
        ('Tirol', 'Tirol'),
        ('Vorarlberg', 'Vorarlberg'),
        ('Kärnten', 'Kärnten'),
        ('Steiermark', 'Steiermark'),
        ('Burgenland', 'Burgenland'),
    ]

    search = forms.CharField(
        label='Suche',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name, Nummer oder Stadt...'
        })
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    bundesland = forms.ChoiceField(
        label='Bundesland',
        choices=BUNDESLAND_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class WorkflowsFilterForm(forms.Form):
    """Filter-Formular für Workflow-Berichte."""

    STATUS_CHOICES = [
        ('', 'Alle'),
        ('entwurf', 'Entwurf'),
        ('aktiv', 'Aktiv'),
        ('abgeschlossen', 'Abgeschlossen'),
        ('abgebrochen', 'Abgebrochen'),
    ]

    search = forms.CharField(
        label='Suche',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name oder Aktenzeichen...'
        })
    )

    workflow_typ = forms.ModelChoiceField(
        label='Workflow-Typ',
        queryset=WorkflowTyp.objects.all(),
        required=False,
        empty_label='Alle',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    erstellt_von = forms.DateField(
        label='Erstellt von',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    erstellt_bis = forms.DateField(
        label='Erstellt bis',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class AktenzeichenFilterForm(forms.Form):
    """Filter-Formular für Aktenzeichen-Berichte."""

    KATEGORIE_CHOICES = [
        ('', 'Alle'),
        ('Bestellung', 'Bestellung'),
        ('Zulassung', 'Zulassung'),
        ('Aufsicht', 'Aufsicht'),
        ('Allgemein', 'Allgemein'),
    ]

    search = forms.CharField(
        label='Suche',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Aktenzeichen oder Beschreibung...'
        })
    )

    kategorie = forms.ChoiceField(
        label='Kategorie',
        choices=KATEGORIE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    jahr = forms.IntegerField(
        label='Jahr',
        required=False,
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'z.B. 2025'
        })
    )

    erstellt_von = forms.DateField(
        label='Erstellt von',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    erstellt_bis = forms.DateField(
        label='Erstellt bis',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
