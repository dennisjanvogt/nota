"""
Views für das Service-System.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from collections import defaultdict
import logging

from apps.services.models import ServiceDefinition, ServiceKategorie, ServiceAusfuehrung
from apps.services.registry import service_registry

logger = logging.getLogger(__name__)


@login_required
def service_katalog_view(request):
    """
    Zeigt alle verfügbaren Services nach Kategorien gruppiert.

    Nur Services die der Benutzer ausführen darf werden angezeigt.
    """
    # Alle aktiven Services holen
    alle_services = ServiceDefinition.objects.filter(
        ist_aktiv=True
    ).select_related('kategorie').order_by('kategorie__reihenfolge', 'name')

    # Nach Kategorien gruppieren
    services_nach_kategorie = defaultdict(list)

    for service in alle_services:
        # Nur Services anzeigen die User ausführen darf
        if service.kann_benutzer_ausfuehren(request.user):
            services_nach_kategorie[service.kategorie].append(service)

    # In Liste umwandeln für Template
    kategorien_mit_services = [
        {
            'kategorie': kategorie,
            'services': services
        }
        for kategorie, services in services_nach_kategorie.items()
    ]

    # Nach Kategorie-Reihenfolge sortieren
    kategorien_mit_services.sort(key=lambda x: x['kategorie'].reihenfolge)

    context = {
        'kategorien_mit_services': kategorien_mit_services,
        'anzahl_services': sum(len(k['services']) for k in kategorien_mit_services)
    }

    return render(request, 'services/katalog.html', context)


@login_required
def service_ausfuehren_view(request, service_id):
    """
    Führt einen Service aus mit dynamischem Form.

    GET: Zeigt Form mit Service-spezifischen Feldern
    POST: Führt Service aus
    """
    from apps.services.forms import get_service_form_class

    # Service-Definition aus DB holen
    service_def = get_object_or_404(
        ServiceDefinition,
        service_id=service_id,
        ist_aktiv=True
    )

    # Berechtigungen prüfen
    if not service_def.kann_benutzer_ausfuehren(request.user):
        messages.error(request, f"Keine Berechtigung für '{service_def.name}'")
        return redirect('service_katalog')

    # Service-Klasse aus Registry holen
    try:
        service_class = service_registry.get(service_id)
    except KeyError:
        messages.error(request, f"Service '{service_id}' nicht registriert")
        return redirect('service_katalog')

    # Form-Klasse holen
    form_class = get_service_form_class(service_id)
    if not form_class:
        messages.error(request, f"Kein Formular für Service '{service_id}' definiert")
        return redirect('service_katalog')

    # Workflow-Kontext (falls vorhanden)
    workflow_instanz = None
    workflow_instanz_id = request.GET.get('workflow_instanz_id')
    if workflow_instanz_id:
        from apps.workflows.models import WorkflowInstanz
        try:
            workflow_instanz = WorkflowInstanz.objects.get(id=workflow_instanz_id)
        except WorkflowInstanz.DoesNotExist:
            pass

    if request.method == 'POST':
        # Form mit POST-Daten initialisieren
        if service_id == 'unterlagen_an_referenten_senden' and workflow_instanz:
            form = form_class(request.POST, workflow_instanz=workflow_instanz)
        else:
            form = form_class(request.POST)

        if form.is_valid():
            # Parameter aus Form extrahieren
            parameter = {}

            # Workflow-Instanz hinzufügen (falls vorhanden)
            if workflow_instanz:
                parameter['workflow_instanz'] = workflow_instanz

            # Spezialfall: Besetzungsvorschlag mit 3 separaten Kandidaten-Feldern
            if service_id == 'besetzungsvorschlag_erstellen':
                anwaerter_ids = [
                    form.cleaned_data['anwaerter_1'].pk,
                    form.cleaned_data['anwaerter_2'].pk,
                    form.cleaned_data['anwaerter_3'].pk
                ]
                parameter['anwaerter_ids'] = anwaerter_ids
                parameter['notarstelle_id'] = form.cleaned_data['notarstelle'].pk
                if form.cleaned_data.get('empfehlung'):
                    parameter['empfehlung'] = form.cleaned_data['empfehlung']
            else:
                # Standard Form-Daten zu Service-Parametern konvertieren
                for field_name, value in form.cleaned_data.items():
                    # ModelChoiceField → ID extrahieren
                    if hasattr(value, 'pk'):
                        parameter[f'{field_name}_id'] = value.pk
                    # ModelMultipleChoiceField → Liste von IDs
                    elif hasattr(value, 'values_list'):
                        parameter[f'{field_name}_ids'] = list(value.values_list('id', flat=True))
                    # Andere Felder direkt übernehmen
                    else:
                        parameter[field_name] = value

            try:
                # Service ausführen
                service_instance = service_class(benutzer=request.user, **parameter)
                ausfuehrung = service_instance.execute()

                messages.success(request, f"Service '{service_def.name}' erfolgreich ausgeführt!")
                return redirect('service_ausfuehrung_detail', ausfuehrung_id=ausfuehrung.id)

            except Exception as e:
                messages.error(request, f"Fehler: {str(e)}")
                logger.error(f"Service-Ausführung fehlgeschlagen: {e}", exc_info=True)
    else:
        # GET: Leeres Form anzeigen
        if service_id == 'unterlagen_an_referenten_senden' and workflow_instanz:
            form = form_class(workflow_instanz=workflow_instanz)
        else:
            form = form_class()

    context = {
        'service': service_def,
        'form': form,
        'workflow_instanz': workflow_instanz
    }

    return render(request, 'services/service_ausfuehren.html', context)


@login_required
def service_ausfuehrung_detail_view(request, ausfuehrung_id):
    """
    Zeigt Details einer Service-Ausführung.
    """
    ausfuehrung = get_object_or_404(
        ServiceAusfuehrung.objects.select_related(
            'service',
            'service__kategorie',
            'ausgefuehrt_von',
            'workflow_instanz'
        ),
        id=ausfuehrung_id
    )

    # Generierte Dokumente holen (falls vorhanden)
    dokumente = ausfuehrung.generierte_dokumente.all()

    # Gesendete E-Mails holen (falls vorhanden)
    emails = ausfuehrung.gesendete_emails.all()

    context = {
        'ausfuehrung': ausfuehrung,
        'dokumente': dokumente,
        'emails': emails
    }

    return render(request, 'services/ausfuehrung_detail.html', context)


@login_required
def service_historie_view(request):
    """
    Zeigt die Historie aller Service-Ausführungen.
    """
    # Filter-Parameter
    service_id = request.GET.get('service')
    nur_erfolgreich = request.GET.get('nur_erfolgreich')
    nur_fehlgeschlagen = request.GET.get('nur_fehlgeschlagen')

    # Basis-Queryset
    ausfuehrungen = ServiceAusfuehrung.objects.select_related(
        'service',
        'service__kategorie',
        'ausgefuehrt_von'
    ).order_by('-erstellt_am')

    # Filter anwenden
    if service_id:
        ausfuehrungen = ausfuehrungen.filter(service__service_id=service_id)

    if nur_erfolgreich:
        ausfuehrungen = ausfuehrungen.filter(erfolgreich=True)
    elif nur_fehlgeschlagen:
        ausfuehrungen = ausfuehrungen.filter(erfolgreich=False)

    # Paginierung
    from django.core.paginator import Paginator
    paginator = Paginator(ausfuehrungen, 25)  # 25 pro Seite
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Alle Services für Filter-Dropdown
    alle_services = ServiceDefinition.objects.filter(ist_aktiv=True).order_by('name')

    # Statistiken für aktuelle Seite berechnen
    statistik_erfolgreich = sum(1 for a in page_obj.object_list if a.erfolgreich)
    statistik_fehlgeschlagen = sum(1 for a in page_obj.object_list if not a.erfolgreich)

    context = {
        'page_obj': page_obj,
        'alle_services': alle_services,
        'selected_service': service_id,
        'nur_erfolgreich': nur_erfolgreich,
        'nur_fehlgeschlagen': nur_fehlgeschlagen,
        'statistik_erfolgreich': statistik_erfolgreich,
        'statistik_fehlgeschlagen': statistik_fehlgeschlagen,
    }

    return render(request, 'services/historie.html', context)
