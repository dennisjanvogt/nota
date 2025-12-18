"""
Views für Workflow-System und Dashboard.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import WorkflowInstanz, WorkflowSchrittInstanz
from .services import WorkflowService
from .forms import WorkflowInstanzForm, WorkflowKommentarForm
from apps.personen.models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle
from apps.aktenzeichen.models import Aktenzeichen


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
        'workflows_aktiv': WorkflowInstanz.objects.filter(status='aktiv').count(),
        'workflows_gesamt': WorkflowInstanz.objects.count(),
    }

    # Meine Aufgaben (zugewiesene Schritte)
    meine_aufgaben = WorkflowService.meine_aufgaben_holen(benutzer)[:5]

    # Offene Workflows (neueste 10)
    offene_workflows = WorkflowService.offene_workflows_holen()[:10]

    # Letzte Aktenzeichen
    letzte_aktenzeichen = Aktenzeichen.objects.all().order_by('-erstellt_am')[:5]

    # Workflows nach Status
    workflows_nach_status = WorkflowInstanz.objects.values('status').annotate(
        anzahl=Count('id')
    ).order_by('status')

    context = {
        'statistiken': statistiken,
        'meine_aufgaben': meine_aufgaben,
        'offene_workflows': offene_workflows,
        'letzte_aktenzeichen': letzte_aktenzeichen,
        'workflows_nach_status': workflows_nach_status,
    }

    return render(request, 'workflows/dashboard.html', context)


@login_required
def workflow_liste_view(request):
    """
    Liste aller Workflow-Instanzen mit Filterung.
    """
    workflows = WorkflowInstanz.objects.select_related(
        'workflow_typ',
        'erstellt_von',
        'aktenzeichen',
        'betroffene_person'
    ).order_by('-erstellt_am')

    # Filter nach Status
    status_filter = request.GET.get('status')
    if status_filter:
        workflows = workflows.filter(status=status_filter)

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
            'erstellt_von',
            'aktenzeichen',
            'betroffene_person'
        ),
        id=workflow_id
    )

    # Schritte mit Status
    schritte = workflow.schritt_instanzen.select_related(
        'workflow_schritt',
        'zugewiesen_an'
    ).order_by('workflow_schritt__reihenfolge')

    # Kommentare
    kommentare = workflow.kommentare.select_related('benutzer').order_by('-erstellt_am')

    # Statistik
    statistik = WorkflowService.statistik_holen(workflow)

    context = {
        'workflow': workflow,
        'schritte': schritte,
        'kommentare': kommentare,
        'statistik': statistik,
    }

    return render(request, 'workflows/workflow_detail.html', context)


@login_required
def meine_aufgaben_view(request):
    """
    Zeigt alle mir zugewiesenen Aufgaben (Workflow-Schritte).
    """
    benutzer = request.user
    aufgaben = WorkflowService.meine_aufgaben_holen(benutzer)

    context = {
        'aufgaben': aufgaben,
    }

    return render(request, 'workflows/meine_aufgaben.html', context)


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
def schritt_zuweisen_view(request, schritt_id):
    """
    Weist einen Schritt einem Benutzer zu.
    """
    schritt = get_object_or_404(WorkflowSchrittInstanz, id=schritt_id)

    if request.method == 'POST':
        benutzer_id = request.POST.get('benutzer_id')
        if benutzer_id:
            from django.contrib.auth import get_user_model
            KammerBenutzer = get_user_model()
            benutzer = get_object_or_404(KammerBenutzer, id=benutzer_id)

            try:
                WorkflowService.schritt_zuweisen(schritt, benutzer)
                messages.success(
                    request,
                    f'Schritt wurde {benutzer.get_full_name() or benutzer.username} zugewiesen.'
                )
            except Exception as e:
                messages.error(request, f'Fehler bei der Zuweisung: {str(e)}')

        return redirect('workflow_detail', workflow_id=schritt.workflow_instanz.id)

    # Hole alle Benutzer für Zuweisung
    from django.contrib.auth import get_user_model
    KammerBenutzer = get_user_model()
    benutzer = KammerBenutzer.objects.filter(is_active=True).order_by('username')

    context = {
        'schritt': schritt,
        'benutzer': benutzer,
    }

    return render(request, 'workflows/schritt_zuweisen.html', context)


@login_required
def kommentar_hinzufuegen_view(request, workflow_id):
    """
    Fügt einen Kommentar zu einem Workflow hinzu.
    """
    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if request.method == 'POST':
        kommentar_text = request.POST.get('kommentar', '')
        schritt_id = request.POST.get('schritt_id')

        if kommentar_text:
            schritt_instanz = None
            if schritt_id:
                schritt_instanz = get_object_or_404(WorkflowSchrittInstanz, id=schritt_id)

            WorkflowService.kommentar_hinzufuegen(
                workflow_instanz=workflow,
                benutzer=request.user,
                kommentar=kommentar_text,
                schritt_instanz=schritt_instanz
            )
            messages.success(request, 'Kommentar wurde hinzugefügt.')
        else:
            messages.error(request, 'Kommentar darf nicht leer sein.')

    return redirect('workflow_detail', workflow_id=workflow_id)


@login_required
def workflow_abbrechen_view(request, workflow_id):
    """
    Bricht einen Workflow ab.
    """
    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if request.method == 'POST':
        grund = request.POST.get('grund', '')

        try:
            WorkflowService.workflow_abbrechen(workflow, grund)
            messages.success(request, f'Workflow "{workflow.name}" wurde abgebrochen.')
        except Exception as e:
            messages.error(request, f'Fehler beim Abbrechen: {str(e)}')

        return redirect('workflow_detail', workflow_id=workflow_id)

    context = {
        'workflow': workflow,
    }

    return render(request, 'workflows/workflow_abbrechen.html', context)


# ===== CRUD Views für Workflow-Instanzen =====

@login_required
def workflow_erstellen_view(request):
    """Erstellen einer neuen Workflow-Instanz."""
    if request.method == 'POST':
        form = WorkflowInstanzForm(request.POST)
        if form.is_valid():
            workflow = form.save(commit=False)
            workflow.erstellt_von = request.user
            workflow.status = 'entwurf'
            workflow.save()

            messages.success(
                request,
                f'Workflow "{workflow.name}" wurde erfolgreich erstellt.'
            )
            return redirect('workflow_detail', workflow_id=workflow.id)
    else:
        form = WorkflowInstanzForm()

    context = {
        'form': form,
        'title': 'Neuer Workflow',
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
        try:
            WorkflowService.workflow_starten(workflow)
            messages.success(
                request,
                f'Workflow "{workflow.name}" wurde gestartet.'
            )
        except Exception as e:
            messages.error(request, f'Fehler beim Starten: {str(e)}')

        return redirect('workflow_detail', workflow_id=workflow_id)

    context = {
        'workflow': workflow,
    }

    return render(request, 'workflows/workflow_starten.html', context)
