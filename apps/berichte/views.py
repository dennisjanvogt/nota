"""
Views für Berichte und Exports.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from apps.personen.models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle
from apps.workflows.models import WorkflowInstanz
from .exporters import export_data
from apps.sprengel.models import Sprengel
from .forms import (
    NotareFilterForm,
    AnwaerterFilterForm,
    NotarstellenFilterForm,
    WorkflowsFilterForm,
    SprengelFilterForm
)


@login_required
def berichte_uebersicht_view(request):
    """
    Übersicht aller verfügbaren Berichte.
    """
    context = {
        'berichte': [
            {
                'titel': 'Notare',
                'beschreibung': 'Liste aller Notare mit Notarstellen und Status',
                'filter_url': 'filter_notare',
                'export_url': 'export_notare',
            },
            {
                'titel': 'Notariatskandidat',
                'beschreibung': 'Liste aller Notariatskandidat mit betreuenden Notaren',
                'filter_url': 'filter_anwaerter',
                'export_url': 'export_anwaerter',
            },
            {
                'titel': 'Notarstellen',
                'beschreibung': 'Liste aller Notarstellen mit Kontaktdaten',
                'filter_url': 'filter_notarstellen',
                'export_url': 'export_notarstellen',
            },
            {
                'titel': 'Workflows',
                'beschreibung': 'Liste aller Workflow-Instanzen mit Status',
                'filter_url': 'filter_workflows',
                'export_url': 'export_workflows',
            },
            {
                'titel': 'Sprengel',
                'beschreibung': 'Liste aller Notarsprengel mit Gerichtsbezirken',
                'filter_url': 'filter_sprengel',
                'export_url': 'export_sprengel',
            },
        ]
    }
    return render(request, 'berichte/uebersicht.html', context)


@login_required
def notare_filter_view(request):
    """Filter-Seite für Notare-Export."""
    form = NotareFilterForm(request.GET or None)

    # Basis-Queryset
    queryset = Notar.objects.select_related('notarstelle').order_by('nachname', 'vorname')

    # Filter anwenden wenn Formular ausgefüllt
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(vorname__icontains=search) |
                Q(nachname__icontains=search) |
                Q(notar_id__icontains=search) |
                Q(email__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True, ende_datum__isnull=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

        if form.cleaned_data.get('notarstelle'):
            queryset = queryset.filter(notarstelle=form.cleaned_data['notarstelle'])

        if form.cleaned_data.get('bestellt_von'):
            queryset = queryset.filter(bestellt_am__gte=form.cleaned_data['bestellt_von'])

        if form.cleaned_data.get('bestellt_bis'):
            queryset = queryset.filter(bestellt_am__lte=form.cleaned_data['bestellt_bis'])

    context = {
        'form': form,
        'queryset': queryset,
        'anzahl': queryset.count(),
        'titel': 'Notare',
        'export_url_name': 'export_notare',
    }
    return render(request, 'berichte/filter.html', context)


@login_required
def export_notare_view(request):
    """Exportiert Notare-Liste mit Filtern."""
    format_typ = request.GET.get('format', 'csv')

    # Basis-Queryset
    queryset = Notar.objects.select_related('notarstelle').order_by('nachname', 'vorname')

    # Filter anwenden
    form = NotareFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(vorname__icontains=search) |
                Q(nachname__icontains=search) |
                Q(notar_id__icontains=search) |
                Q(email__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True, ende_datum__isnull=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

        if form.cleaned_data.get('notarstelle'):
            queryset = queryset.filter(notarstelle=form.cleaned_data['notarstelle'])

        if form.cleaned_data.get('bestellt_von'):
            queryset = queryset.filter(bestellt_am__gte=form.cleaned_data['bestellt_von'])

        if form.cleaned_data.get('bestellt_bis'):
            queryset = queryset.filter(bestellt_am__lte=form.cleaned_data['bestellt_bis'])

    spalten = [
        ('notar_id', 'Notar-ID'),
        ('titel', 'Titel'),
        ('vorname', 'Vorname'),
        ('nachname', 'Nachname'),
        ('notarstelle__name', 'Notarstelle'),
        ('notarstelle__notarnummer', 'Notarnummer'),
        ('email', 'E-Mail'),
        ('telefon', 'Telefon'),
        ('bestellt_am', 'Bestellt am'),
        ('beginn_datum', 'Beginn'),
        ('ende_datum', 'Ende'),
        ('ist_aktiv', 'Aktiv'),
    ]

    return export_data(queryset, spalten, format_typ, titel='Notare')


@login_required
def anwaerter_filter_view(request):
    """Filter-Seite für Kandidaten-Export."""
    form = AnwaerterFilterForm(request.GET or None)

    # Basis-Queryset
    queryset = NotarAnwaerter.objects.select_related('betreuender_notar', 'notarstelle').order_by('nachname', 'vorname')

    # Filter anwenden
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(vorname__icontains=search) |
                Q(nachname__icontains=search) |
                Q(anwaerter_id__icontains=search) |
                Q(email__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True, ende_datum__isnull=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

        if form.cleaned_data.get('notarstelle'):
            queryset = queryset.filter(notarstelle=form.cleaned_data['notarstelle'])

        if form.cleaned_data.get('bestellung_status'):
            bestellung = form.cleaned_data['bestellung_status']
            if bestellung == 'geplant':
                queryset = queryset.filter(geplante_bestellung__isnull=False)
            elif bestellung == 'nicht_geplant':
                queryset = queryset.filter(geplante_bestellung__isnull=True)

        if form.cleaned_data.get('zugelassen_von'):
            queryset = queryset.filter(zugelassen_am__gte=form.cleaned_data['zugelassen_von'])

        if form.cleaned_data.get('zugelassen_bis'):
            queryset = queryset.filter(zugelassen_am__lte=form.cleaned_data['zugelassen_bis'])

    context = {
        'form': form,
        'queryset': queryset,
        'anzahl': queryset.count(),
        'titel': 'Notariatskandidat',
        'export_url_name': 'export_anwaerter',
    }
    return render(request, 'berichte/filter.html', context)


@login_required
def export_anwaerter_view(request):
    """Exportiert Notariatskandidat-Liste mit Filtern."""
    format_typ = request.GET.get('format', 'csv')

    # Basis-Queryset
    queryset = NotarAnwaerter.objects.select_related('betreuender_notar', 'notarstelle').order_by('nachname', 'vorname')

    # Filter anwenden
    form = AnwaerterFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(vorname__icontains=search) |
                Q(nachname__icontains=search) |
                Q(anwaerter_id__icontains=search) |
                Q(email__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True, ende_datum__isnull=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

        if form.cleaned_data.get('notarstelle'):
            queryset = queryset.filter(notarstelle=form.cleaned_data['notarstelle'])

        if form.cleaned_data.get('bestellung_status'):
            bestellung = form.cleaned_data['bestellung_status']
            if bestellung == 'geplant':
                queryset = queryset.filter(geplante_bestellung__isnull=False)
            elif bestellung == 'nicht_geplant':
                queryset = queryset.filter(geplante_bestellung__isnull=True)

        if form.cleaned_data.get('zugelassen_von'):
            queryset = queryset.filter(zugelassen_am__gte=form.cleaned_data['zugelassen_von'])

        if form.cleaned_data.get('zugelassen_bis'):
            queryset = queryset.filter(zugelassen_am__lte=form.cleaned_data['zugelassen_bis'])

    spalten = [
        ('anwaerter_id', 'Kandidaten-ID'),
        ('titel', 'Titel'),
        ('vorname', 'Vorname'),
        ('nachname', 'Nachname'),
        ('betreuender_notar__nachname', 'Betreuender Notar (Nachname)'),
        ('betreuender_notar__vorname', 'Betreuender Notar (Vorname)'),
        ('notarstelle__name', 'Notarstelle'),
        ('email', 'E-Mail'),
        ('telefon', 'Telefon'),
        ('zugelassen_am', 'Zugelassen am'),
        ('beginn_datum', 'Beginn'),
        ('geplante_bestellung', 'Geplante Bestellung'),
        ('ist_aktiv', 'Aktiv'),
    ]

    return export_data(queryset, spalten, format_typ, titel='Notar-Anwaerter')


@login_required
def export_notarstellen_view(request):
    """Exportiert Notarstellen-Liste mit Filtern."""
    format_typ = request.GET.get('format', 'csv')

    # Basis-Queryset
    queryset = Notarstelle.objects.all().order_by('notarnummer')

    # Filter anwenden
    form = NotarstellenFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(bezeichnung__icontains=search) |
                Q(notarnummer__icontains=search) |
                Q(stadt__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(ist_aktiv=False)

        if form.cleaned_data.get('bundesland'):
            queryset = queryset.filter(bundesland=form.cleaned_data['bundesland'])

    spalten = [
        ('notarnummer', 'Notarnummer'),
        ('bezeichnung', 'Bezeichnung'),
        ('name', 'Name'),
        ('strasse', 'Straße'),
        ('plz', 'PLZ'),
        ('stadt', 'Stadt'),
        ('bundesland', 'Bundesland'),
        ('telefon', 'Telefon'),
        ('email', 'E-Mail'),
        ('besetzt_seit', 'Besetzt seit'),
        ('ist_aktiv', 'Aktiv'),
    ]

    return export_data(queryset, spalten, format_typ, titel='Notarstellen')


@login_required
def export_workflows_view(request):
    """Exportiert Workflow-Liste mit Filtern."""
    format_typ = request.GET.get('format', 'csv')

    # Basis-Queryset
    queryset = WorkflowInstanz.objects.select_related(
        'workflow_typ', 'erstellt_von'
    ).prefetch_related(
        'betroffene_notare',
        'betroffene_kandidaten'
    ).order_by('-erstellt_am')

    # Filter anwenden
    form = WorkflowsFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(aktenzeichen__vollstaendige_nummer__icontains=search)
            )

        if form.cleaned_data.get('workflow_typ'):
            queryset = queryset.filter(workflow_typ=form.cleaned_data['workflow_typ'])

        if form.cleaned_data.get('status'):
            queryset = queryset.filter(status=form.cleaned_data['status'])

        if form.cleaned_data.get('erstellt_von'):
            queryset = queryset.filter(erstellt_am__gte=form.cleaned_data['erstellt_von'])

        if form.cleaned_data.get('erstellt_bis'):
            queryset = queryset.filter(erstellt_am__lte=form.cleaned_data['erstellt_bis'])

    spalten = [
        ('id', 'ID'),
        ('name', 'Name'),
        ('workflow_typ__name', 'Workflow-Typ'),
        ('status', 'Status'),
        ('aktenzeichen__vollstaendige_nummer', 'Aktenzeichen'),
        # Betroffene Personen sind jetzt ManyToMany - Export-Unterstützung folgt später
        # ('betroffene_person__nachname', 'Betroffene Person (Nachname)'),
        # ('betroffene_person__vorname', 'Betroffene Person (Vorname)'),
        ('erstellt_von__username', 'Erstellt von'),
        ('erstellt_am', 'Erstellt am'),
        ('gestartet_am', 'Gestartet am'),
        ('abgeschlossen_am', 'Abgeschlossen am'),
        ('faellig_am', 'Fällig am'),
    ]

    return export_data(queryset, spalten, format_typ, titel='Workflows')


@login_required
def notarstellen_filter_view(request):
    """Filter-Seite für Notarstellen-Export."""
    form = NotarstellenFilterForm(request.GET or None)

    # Basis-Queryset
    queryset = Notarstelle.objects.all().order_by('notarnummer')

    # Filter anwenden
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(bezeichnung__icontains=search) |
                Q(notarnummer__icontains=search) |
                Q(stadt__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(ist_aktiv=False)

        if form.cleaned_data.get('bundesland'):
            queryset = queryset.filter(bundesland=form.cleaned_data['bundesland'])

    context = {
        'form': form,
        'queryset': queryset,
        'anzahl': queryset.count(),
        'titel': 'Notarstellen',
        'export_url_name': 'export_notarstellen',
    }
    return render(request, 'berichte/filter.html', context)


@login_required
def workflows_filter_view(request):
    """Filter-Seite für Workflows-Export."""
    form = WorkflowsFilterForm(request.GET or None)

    # Basis-Queryset
    queryset = WorkflowInstanz.objects.select_related(
        'workflow_typ', 'erstellt_von'
    ).prefetch_related(
        'betroffene_notare',
        'betroffene_kandidaten'
    ).order_by('-erstellt_am')

    # Filter anwenden
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(aktenzeichen__vollstaendige_nummer__icontains=search)
            )

        if form.cleaned_data.get('workflow_typ'):
            queryset = queryset.filter(workflow_typ=form.cleaned_data['workflow_typ'])

        if form.cleaned_data.get('status'):
            queryset = queryset.filter(status=form.cleaned_data['status'])

        if form.cleaned_data.get('erstellt_von'):
            queryset = queryset.filter(erstellt_am__gte=form.cleaned_data['erstellt_von'])

        if form.cleaned_data.get('erstellt_bis'):
            queryset = queryset.filter(erstellt_am__lte=form.cleaned_data['erstellt_bis'])

    context = {
        'form': form,
        'queryset': queryset,
        'anzahl': queryset.count(),
        'titel': 'Workflows',
        'export_url_name': 'export_workflows',
    }
    return render(request, 'berichte/filter.html', context)


@login_required
def sprengel_filter_view(request):
    """Filter-Seite für Sprengel-Export."""
    form = SprengelFilterForm(request.GET or None)

    # Basis-Queryset
    queryset = Sprengel.objects.all().order_by('bezeichnung')

    # Filter anwenden
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(bezeichnung__icontains=search) |
                Q(name__icontains=search) |
                Q(gerichtsbezirk__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(ist_aktiv=False)

        if form.cleaned_data.get('bundesland'):
            queryset = queryset.filter(bundesland=form.cleaned_data['bundesland'])

    context = {
        'form': form,
        'queryset': queryset,
        'anzahl': queryset.count(),
        'titel': 'Sprengel',
        'export_url_name': 'export_sprengel',
    }
    return render(request, 'berichte/filter.html', context)


@login_required
def export_sprengel_view(request):
    """Exportiert Sprengel-Liste mit Filtern."""
    format_typ = request.GET.get('format', 'csv')

    # Basis-Queryset
    queryset = Sprengel.objects.all().order_by('bezeichnung')

    # Filter anwenden
    form = SprengelFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            queryset = queryset.filter(
                Q(bezeichnung__icontains=search) |
                Q(name__icontains=search) |
                Q(gerichtsbezirk__icontains=search)
            )

        if form.cleaned_data.get('status'):
            status = form.cleaned_data['status']
            if status == 'aktiv':
                queryset = queryset.filter(ist_aktiv=True)
            elif status == 'inaktiv':
                queryset = queryset.filter(ist_aktiv=False)

        if form.cleaned_data.get('bundesland'):
            queryset = queryset.filter(bundesland=form.cleaned_data['bundesland'])

    spalten = [
        ('bezeichnung', 'Bezeichnung'),
        ('name', 'Name'),
        ('gerichtsbezirk', 'Gerichtsbezirk'),
        ('bundesland', 'Bundesland'),
        ('anzahl_notarstellen', 'Anzahl Notarstellen'),
        ('anzahl_aktive_notarstellen', 'Davon aktiv'),
        ('ist_aktiv', 'Aktiv'),
        ('erstellt_am', 'Erstellt am'),
    ]

    return export_data(queryset, spalten, format_typ, titel='Sprengel')
