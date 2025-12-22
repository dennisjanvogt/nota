"""
Views für Workflow-System und Dashboard.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from django.utils import timezone
from .models import WorkflowInstanz, WorkflowSchrittInstanz, WorkflowTyp, WorkflowSchritt
from .services import WorkflowService
from .forms import WorkflowInstanzForm, WorkflowTypForm, WorkflowSchrittFormSet
from apps.personen.models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle


@login_required
def dashboard_view(request):
    """
    Haupt-Dashboard mit Übersicht und Statistiken.
    """
    benutzer = request.user

    # Statistiken
    statistiken = {
        'notare_gesamt': Notar.objects.filter(ist_aktiv=True).count(),
        'anwaerter_gesamt': NotarAnwaerter.objects.filter(ist_aktiv=True).count(),
        'notarstellen_gesamt': Notarstelle.objects.filter(ist_aktiv=True).count(),
        'workflows_offen': WorkflowInstanz.objects.exclude(status='archiviert').count(),
        'workflows_gesamt': WorkflowInstanz.objects.count(),
        'workflows_abgeschlossen': WorkflowInstanz.objects.filter(status='archiviert').count(),
    }

    # Deadline-Statistiken (alle offenen Workflows mit Fertigstellungsdatum)
    offene_workflows_mit_datum = WorkflowInstanz.objects.exclude(
        status='archiviert'
    ).exclude(
        fertigstellungsdatum__isnull=True
    )
    deadline_stats = {
        'ueberfaellig': 0,
        '1_tag': 0,
        '5_tage': 0,
        'mehr': 0,
    }

    for workflow in offene_workflows_mit_datum:
        status = workflow.deadline_status
        if status in deadline_stats:
            deadline_stats[status] += 1

    # Offene Workflows (neueste 10)
    offene_workflows = WorkflowService.offene_workflows_holen()[:10]

    # Workflows nach Status
    workflows_nach_status = WorkflowInstanz.objects.values('status').annotate(
        anzahl=Count('id')
    ).order_by('status')

    context = {
        'statistiken': statistiken,
        'deadline_stats': deadline_stats,
        'offene_workflows': offene_workflows,
        'workflows_nach_status': workflows_nach_status,
    }

    return render(request, 'workflows/dashboard.html', context)


@login_required
def workflow_liste_view(request):
    """
    Liste aller Workflow-Instanzen mit Filterung.

    Archivierte Workflows werden standardmäßig ausgeblendet.
    """
    workflows = WorkflowInstanz.objects.select_related(
        'workflow_typ',
        'erstellt_von'
    ).prefetch_related(
        'betroffene_notare',
        'betroffene_kandidaten'
    ).order_by('-erstellt_am')

    # Filter nach Status
    status_filter = request.GET.get('status')
    if status_filter:
        # Expliziter Status-Filter (inkl. archiviert)
        workflows = workflows.filter(status=status_filter)
    else:
        # Standard: Nur aktive Workflows anzeigen (archivierte ausblenden)
        workflows = workflows.exclude(status='archiviert')

    # Filter nach Workflow-Typ
    typ_filter = request.GET.get('typ')
    if typ_filter:
        workflows = workflows.filter(workflow_typ__id=typ_filter)

    # Suche
    suche = request.GET.get('suche')
    if suche:
        workflows = WorkflowService.workflow_suchen(suche)

    context = {
        'workflows': workflows,
        'status_filter': status_filter,
        'typ_filter': typ_filter,
        'suche': suche,
    }

    return render(request, 'workflows/workflow_liste.html', context)


@login_required
def workflow_detail_view(request, workflow_id):
    """
    Detail-Ansicht einer Workflow-Instanz mit Schritt-Tracking.
    """
    workflow = get_object_or_404(
        WorkflowInstanz.objects.select_related(
            'workflow_typ',
            'erstellt_von'
        ).prefetch_related(
            'betroffene_notare',
            'betroffene_kandidaten'
        ),
        id=workflow_id
    )

    # Schritte mit Status
    schritte = workflow.schritt_instanzen.select_related(
        'workflow_schritt'
    ).order_by('workflow_schritt__reihenfolge')

    from django.utils import timezone
    context = {
        'workflow': workflow,
        'schritte': schritte,
        'heute': timezone.now().date(),
    }

    return render(request, 'workflows/workflow_detail.html', context)


@login_required
def workflow_name_aendern_view(request, workflow_id):
    """
    Ändert den Namen eines Workflows via AJAX.
    """
    if request.method == 'POST':
        workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)
        new_name = request.POST.get('name', '').strip()

        if not new_name:
            return JsonResponse({'success': False, 'error': 'Name darf nicht leer sein'})

        workflow.name = new_name
        workflow.save()

        return JsonResponse({'success': True, 'name': new_name})

    return JsonResponse({'success': False, 'error': 'Nur POST-Anfragen erlaubt'})


@login_required
def workflow_datum_aendern_view(request, workflow_id):
    """
    Ändert das Fertigstellungsdatum eines Workflows via AJAX.
    """
    if request.method == 'POST':
        workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)
        fertigstellungsdatum = request.POST.get('fertigstellungsdatum', '').strip()

        if fertigstellungsdatum:
            from datetime import datetime
            try:
                workflow.fertigstellungsdatum = datetime.strptime(fertigstellungsdatum, '%Y-%m-%d').date()
                workflow.save()
                return JsonResponse({
                    'success': True,
                    'fertigstellungsdatum': workflow.fertigstellungsdatum.strftime('%d.%m.%Y')
                })
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Ungültiges Datumsformat'})
        else:
            # Datum entfernen
            workflow.fertigstellungsdatum = None
            workflow.save()
            return JsonResponse({'success': True, 'fertigstellungsdatum': None})

    return JsonResponse({'success': False, 'error': 'Nur POST-Anfragen erlaubt'})


@login_required
def schritt_abschliessen_view(request, schritt_id):
    """
    Schließt einen Workflow-Schritt ab.
    """
    schritt = get_object_or_404(WorkflowSchrittInstanz, id=schritt_id)

    if request.method == 'POST':
        notizen = request.POST.get('notizen', '')

        try:
            WorkflowService.schritt_abschliessen(schritt, notizen)
            messages.success(
                request,
                f'Schritt "{schritt.workflow_schritt.name}" wurde erfolgreich abgeschlossen.'
            )
        except Exception as e:
            messages.error(request, f'Fehler beim Abschließen des Schritts: {str(e)}')

        return redirect('workflow_detail', workflow_id=schritt.workflow_instanz.id)

    context = {
        'schritt': schritt,
    }

    return render(request, 'workflows/schritt_abschliessen.html', context)


@login_required
def schritt_rueckgaengig_machen_view(request, schritt_id):
    """
    Macht einen abgeschlossenen Workflow-Schritt rückgängig (zurück auf pending).
    """
    schritt = get_object_or_404(WorkflowSchrittInstanz, id=schritt_id)

    if request.method == 'POST':
        try:
            WorkflowService.schritt_rueckgaengig_machen(schritt)
            messages.success(
                request,
                f'Schritt "{schritt.workflow_schritt.name}" wurde rückgängig gemacht.'
            )
        except Exception as e:
            messages.error(request, f'Fehler beim Rückgängigmachen: {str(e)}')

        return redirect('workflow_detail', workflow_id=schritt.workflow_instanz.id)

    # Bei GET-Request: Bestätigungs-Seite anzeigen
    context = {
        'schritt': schritt,
    }
    return render(request, 'workflows/schritt_rueckgaengig.html', context)


@login_required
@require_http_methods(["POST"])
def schritt_toggle_view(request, schritt_id):
    """
    AJAX-Endpoint: Toggle Schritt-Status (pending ↔ completed).

    Returns JSON:
    {
        "success": true,
        "status": "completed",  # neuer Status
        "fortschritt_prozent": 75,
        "workflow_status": "aktiv"  # kann zu "archiviert" wechseln
    }
    """
    try:
        schritt = get_object_or_404(WorkflowSchrittInstanz, pk=schritt_id)
        workflow = schritt.workflow_instanz

        # Status togglen
        if schritt.status == 'pending':
            WorkflowService.schritt_abschliessen(schritt, notizen='')
            neuer_status = 'completed'
        else:
            WorkflowService.schritt_rueckgaengig_machen(schritt)
            neuer_status = 'pending'

        # Workflow neu laden (könnte archiviert worden sein)
        workflow.refresh_from_db()

        return JsonResponse({
            'success': True,
            'status': neuer_status,
            'fortschritt_prozent': workflow.fortschritt_prozent,
            'workflow_status': workflow.status
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===== CRUD Views für Workflow-Instanzen =====

@login_required
def workflow_erstellen_view(request):
    """Erstellen einer neuen Workflow-Instanz aus einem Template."""
    if request.method == 'POST':
        form = WorkflowInstanzForm(request.POST)
        if form.is_valid():
            # Nutze den WorkflowService um Workflow + Schritte zu erstellen
            workflow = WorkflowService.workflow_erstellen(
                workflow_typ=form.cleaned_data['workflow_typ'],
                name=form.cleaned_data['name'],
                erstellt_von=request.user
            )

            # Notizen hinzufügen falls vorhanden
            if form.cleaned_data.get('notizen'):
                workflow.notizen = form.cleaned_data['notizen']
                workflow.save()

            # Betroffene Personen hinzufügen (aus verstecktem Feld)
            betroffene_personen_ids = form.cleaned_data.get('betroffene_personen_ids', '')
            if betroffene_personen_ids:
                for person_data in betroffene_personen_ids.split(','):
                    if ':' in person_data:
                        typ, person_id = person_data.split(':', 1)
                        if typ == 'notar':
                            try:
                                notar = Notar.objects.get(notar_id=person_id)
                                workflow.betroffene_notare.add(notar)
                            except Notar.DoesNotExist:
                                pass
                        elif typ == 'kandidat':
                            try:
                                kandidat = NotarAnwaerter.objects.get(anwaerter_id=person_id)
                                workflow.betroffene_kandidaten.add(kandidat)
                            except NotarAnwaerter.DoesNotExist:
                                pass

            messages.success(
                request,
                f'Workflow "{workflow.name}" wurde aus Template "{workflow.workflow_typ.name}" erstellt.'
            )
            return redirect('workflow_detail', workflow_id=workflow.id)
    else:
        form = WorkflowInstanzForm()

    context = {
        'form': form,
        'title': 'Neuer Workflow aus Template',
        'submit_text': 'Erstellen',
    }
    return render(request, 'workflows/workflow_form.html', context)


@login_required
def workflow_bearbeiten_view(request, workflow_id):
    """Bearbeiten einer Workflow-Instanz."""
    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if request.method == 'POST':
        form = WorkflowInstanzForm(request.POST, instance=workflow)
        if form.is_valid():
            workflow = form.save()
            messages.success(
                request,
                f'Workflow "{workflow.name}" wurde erfolgreich aktualisiert.'
            )
            return redirect('workflow_detail', workflow_id=workflow.id)
    else:
        form = WorkflowInstanzForm(instance=workflow)

    context = {
        'form': form,
        'workflow': workflow,
        'title': f'Workflow bearbeiten: {workflow.name}',
        'submit_text': 'Speichern',
    }
    return render(request, 'workflows/workflow_form.html', context)


@login_required
def workflow_loeschen_view(request, workflow_id):
    """Löschen einer Workflow-Instanz."""
    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if request.method == 'POST':
        name = workflow.name
        try:
            workflow.delete()
            messages.success(request, f'Workflow "{name}" wurde gelöscht.')
            return redirect('workflow_liste')
        except Exception as e:
            messages.error(
                request,
                f'Fehler beim Löschen: {str(e)}'
            )
            return redirect('workflow_detail', workflow_id=workflow_id)

    context = {
        'workflow': workflow,
    }
    return render(request, 'workflows/workflow_loeschen.html', context)


@login_required
def workflow_starten_view(request, workflow_id):
    """Startet einen Workflow (von Entwurf zu Aktiv)."""
    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if request.method == 'POST':
        fertigstellungsdatum = request.POST.get('fertigstellungsdatum')

        try:
            # Fertigstellungsdatum setzen (falls angegeben)
            if fertigstellungsdatum:
                from datetime import datetime
                workflow.fertigstellungsdatum = datetime.strptime(fertigstellungsdatum, '%Y-%m-%d').date()
                workflow.save()

            WorkflowService.workflow_starten(workflow)
            messages.success(
                request,
                f'Workflow "{workflow.name}" wurde gestartet.'
            )
        except Exception as e:
            messages.error(request, f'Fehler beim Starten: {str(e)}')

        return redirect('workflow_detail', workflow_id=workflow_id)

    from django.utils import timezone
    context = {
        'workflow': workflow,
        'heute': timezone.now().date(),
    }

    return render(request, 'workflows/workflow_starten.html', context)


# ===== TEMPLATE-VERWALTUNG VIEWS =====

@login_required
def workflow_template_liste_view(request):
    """Liste aller Workflow-Templates (WorkflowTypen)."""
    templates = WorkflowTyp.objects.annotate(
        anzahl_schritte=Count('schritte'),
        anzahl_instanzen=Count('instanzen')
    ).order_by('name')

    # Filter nach Status (aktiv/inaktiv)
    status_filter = request.GET.get('status')
    if status_filter == 'aktiv':
        templates = templates.filter(ist_aktiv=True)
    elif status_filter == 'inaktiv':
        templates = templates.filter(ist_aktiv=False)

    context = {
        'templates': templates,
        'status_filter': status_filter,
    }

    return render(request, 'workflows/template_liste.html', context)


@login_required
def workflow_template_detail_view(request, template_id):
    """Detail-Ansicht eines Workflow-Templates mit allen Schritten."""
    template = get_object_or_404(
        WorkflowTyp.objects.annotate(
            anzahl_instanzen=Count('instanzen')
        ),
        id=template_id
    )

    # Schritte des Templates
    schritte = template.schritte.order_by('reihenfolge')

    # Letzte Instanzen (max 5)
    letzte_instanzen = template.instanzen.order_by('-erstellt_am')[:5]

    context = {
        'template': template,
        'schritte': schritte,
        'letzte_instanzen': letzte_instanzen,
    }

    return render(request, 'workflows/template_detail.html', context)


@login_required
def workflow_template_erstellen_view(request):
    """Erstellen eines neuen Workflow-Templates mit Schritten."""
    if request.method == 'POST':
        form = WorkflowTypForm(request.POST)
        formset = WorkflowSchrittFormSet(request.POST)

        # DEBUG: Ausgabe der Formular-Fehler
        if not form.is_valid():
            print("=== FORM ERRORS (ERSTELLEN) ===")
            print(form.errors)

        if not formset.is_valid():
            print("=== FORMSET ERRORS (ERSTELLEN) ===")
            for i, form_in_set in enumerate(formset):
                if form_in_set.errors:
                    print(f"Form {i}: {form_in_set.errors}")
            print(f"Formset non-form errors: {formset.non_form_errors()}")

        if form.is_valid() and formset.is_valid():
            # Template speichern
            template = form.save()

            # Schritte speichern
            formset.instance = template
            formset.save()

            messages.success(
                request,
                f'Template "{template.name}" mit {template.schritte.count()} Schritten wurde erstellt.'
            )
            return redirect('workflow_template_detail', template_id=template.id)
    else:
        form = WorkflowTypForm()
        formset = WorkflowSchrittFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Neues Workflow-Template',
        'submit_text': 'Template erstellen',
    }

    return render(request, 'workflows/template_form.html', context)


@login_required
def workflow_template_bearbeiten_view(request, template_id):
    """Bearbeiten eines Workflow-Templates mit Schritten."""
    template = get_object_or_404(WorkflowTyp, id=template_id)

    if request.method == 'POST':
        # === NEUE DEBUG-AUSGABEN VOR FORM-VALIDIERUNG ===
        print("\n" + "="*80)
        print("=== WORKFLOW TEMPLATE BEARBEITEN - POST REQUEST ===")
        print("="*80)

        # 1. Management Form Daten
        print("\n--- FORMSET MANAGEMENT FORM ---")
        print(f"TOTAL_FORMS: {request.POST.get('schritte-TOTAL_FORMS')}")
        print(f"INITIAL_FORMS: {request.POST.get('schritte-INITIAL_FORMS')}")
        print(f"MIN_NUM_FORMS: {request.POST.get('schritte-MIN_NUM_FORMS')}")
        print(f"MAX_NUM_FORMS: {request.POST.get('schritte-MAX_NUM_FORMS')}")

        # 2. Alle Formulare durchgehen
        total_forms = int(request.POST.get('schritte-TOTAL_FORMS', 0))
        print(f"\n--- ANALYZING {total_forms} FORM(S) ---")

        for i in range(total_forms):
            print(f"\nForm {i}:")
            print(f"  - id: {request.POST.get(f'schritte-{i}-id', 'MISSING')}")
            print(f"  - name: {request.POST.get(f'schritte-{i}-name', 'MISSING')}")
            print(f"  - reihenfolge: {request.POST.get(f'schritte-{i}-reihenfolge', 'MISSING')}")
            print(f"  - service: {request.POST.get(f'schritte-{i}-service', 'MISSING')}")
            print(f"  - email_vorlage: {request.POST.get(f'schritte-{i}-email_vorlage', 'MISSING')}")
            print(f"  - DELETE: {request.POST.get(f'schritte-{i}-DELETE', 'MISSING')}")

        # 3. Aktuelle Schritte in DB
        actual_schritte = template.schritte.count()
        print(f"\n--- DATABASE STATE ---")
        print(f"Actual schritte in DB: {actual_schritte}")

        print("\n" + "="*80 + "\n")

        # Jetzt Forms erstellen
        form = WorkflowTypForm(request.POST, instance=template)
        formset = WorkflowSchrittFormSet(request.POST, instance=template)

        # DEBUG: Ausgabe der Formular-Fehler
        if not form.is_valid():
            print("=== FORM ERRORS ===")
            print(form.errors)

        if not formset.is_valid():
            print("=== FORMSET ERRORS ===")
            print(f"Formset is_valid: {formset.is_valid()}")
            print(f"Management form is_valid: {formset.management_form.is_valid()}")
            print(f"Management form errors: {formset.management_form.errors}")

            for i, form_in_set in enumerate(formset):
                if form_in_set.errors:
                    print(f"Form {i}: {form_in_set.errors}")
            print(f"Formset non-form errors: {formset.non_form_errors()}")

        if form.is_valid() and formset.is_valid():
            template = form.save()
            formset.save()

            messages.success(
                request,
                f'Template "{template.name}" wurde erfolgreich aktualisiert.'
            )
            return redirect('workflow_template_detail', template_id=template.id)
    else:
        form = WorkflowTypForm(instance=template)
        formset = WorkflowSchrittFormSet(instance=template)

    context = {
        'form': form,
        'formset': formset,
        'template': template,
        'title': f'Template bearbeiten: {template.name}',
        'submit_text': 'Änderungen speichern',
    }

    return render(request, 'workflows/template_form.html', context)


@login_required
def workflow_template_loeschen_view(request, template_id):
    """Löschen eines Workflow-Templates (nur wenn keine Instanzen existieren)."""
    template = get_object_or_404(
        WorkflowTyp.objects.annotate(
            anzahl_instanzen=Count('instanzen')
        ),
        id=template_id
    )

    # Prüfen ob Instanzen existieren
    if template.anzahl_instanzen > 0:
        messages.error(
            request,
            f'Template "{template.name}" kann nicht gelöscht werden, '
            f'da {template.anzahl_instanzen} Workflow-Instanz(en) darauf basieren.'
        )
        return redirect('workflow_template_detail', template_id=template_id)

    if request.method == 'POST':
        name = template.name
        try:
            template.delete()
            messages.success(request, f'Template "{name}" wurde gelöscht.')
            return redirect('workflow_template_liste')
        except Exception as e:
            messages.error(
                request,
                f'Fehler beim Löschen: {str(e)}'
            )
            return redirect('workflow_template_detail', template_id=template_id)

    context = {
        'template': template,
    }

    return render(request, 'workflows/template_loeschen.html', context)


@login_required
def workflow_alle_schritte_abhaken_view(request, workflow_id):
    """
    Markiert alle Schritte eines Workflows als abgeschlossen.
    """
    if request.method == 'POST':
        workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

        # Alle pending Schritte holen
        pending_schritte = workflow.schritt_instanzen.filter(status='pending')
        anzahl = pending_schritte.count()

        # Alle Schritte abschließen
        for schritt in pending_schritte:
            try:
                WorkflowService.schritt_abschliessen(schritt, notizen='')
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Fehler beim Abschließen: {str(e)}'
                })

        return JsonResponse({
            'success': True,
            'anzahl': anzahl,
            'message': f'{anzahl} Schritt(e) wurden als erledigt markiert.'
        })

    return JsonResponse({'success': False, 'error': 'Nur POST-Anfragen erlaubt'})


@login_required
def workflow_alle_schritte_zuruecksetzen_view(request, workflow_id):
    """
    Setzt alle Schritte eines Workflows auf pending zurück.
    """
    if request.method == 'POST':
        workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

        # Alle completed Schritte holen
        completed_schritte = workflow.schritt_instanzen.filter(status='completed')
        anzahl = completed_schritte.count()

        # Alle Schritte zurücksetzen
        for schritt in completed_schritte:
            try:
                WorkflowService.schritt_rueckgaengig_machen(schritt)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Fehler beim Zurücksetzen: {str(e)}'
                })

        return JsonResponse({
            'success': True,
            'anzahl': anzahl,
            'message': f'{anzahl} Schritt(e) wurden zurückgesetzt.'
        })

    return JsonResponse({'success': False, 'error': 'Nur POST-Anfragen erlaubt'})


@login_required
def personen_autocomplete_api(request):
    """
    API-Endpoint für Autocomplete-Suche von Notaren und Kandidaten.

    Query-Parameter:
        - q: Suchbegriff (min. 2 Zeichen)
        - typ: Optional 'notar' oder 'kandidat' zum Filtern

    Returns JSON: [
        {"id": "NOT-000001", "name": "Max Mustermann", "typ": "notar", "zusatz": "..."},
        {"id": "NKA-000005", "name": "Anna Schmidt", "typ": "kandidat", "zusatz": "..."},
    ]
    """
    query = request.GET.get('q', '').strip()
    typ_filter = request.GET.get('typ', '').strip()

    if len(query) < 2:
        return JsonResponse([], safe=False)

    results = []

    # Notare durchsuchen (nur wenn kein Filter oder Filter = 'notar')
    if not typ_filter or typ_filter == 'notar':
        notare = Notar.objects.filter(
            Q(vorname__icontains=query) |
            Q(nachname__icontains=query) |
            Q(notar_id__icontains=query),
            ist_aktiv=True
        )[:10]

        for notar in notare:
            results.append({
                'id': notar.notar_id,
                'name': notar.get_voller_name(),
                'typ': 'notar',
                'zusatz': notar.notarstelle.name if notar.notarstelle else ''
            })

    # Kandidaten durchsuchen (nur wenn kein Filter oder Filter = 'kandidat')
    if not typ_filter or typ_filter == 'kandidat':
        kandidaten = NotarAnwaerter.objects.filter(
            Q(vorname__icontains=query) |
            Q(nachname__icontains=query) |
            Q(anwaerter_id__icontains=query),
            ist_aktiv=True
        )[:10]

        for kandidat in kandidaten:
            results.append({
                'id': kandidat.anwaerter_id,
                'name': kandidat.get_voller_name(),
                'typ': 'kandidat',
                'zusatz': f'bei {kandidat.betreuender_notar.get_voller_name()}' if kandidat.betreuender_notar else ''
            })

    return JsonResponse(results, safe=False)
