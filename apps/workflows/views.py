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
from .forms import WorkflowInstanzForm
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
        'workflows_aktiv': WorkflowInstanz.objects.filter(status='aktiv').count(),
        'workflows_gesamt': WorkflowInstanz.objects.count(),
    }

    # Offene Workflows (neueste 10)
    offene_workflows = WorkflowService.offene_workflows_holen()[:10]

    # Workflows nach Status
    workflows_nach_status = WorkflowInstanz.objects.values('status').annotate(
        anzahl=Count('id')
    ).order_by('status')

    context = {
        'statistiken': statistiken,
        'offene_workflows': offene_workflows,
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
            'betroffene_person'
        ),
        id=workflow_id
    )

    # Schritte mit Status
    schritte = workflow.schritt_instanzen.select_related(
        'workflow_schritt'
    ).order_by('workflow_schritt__reihenfolge')

    context = {
        'workflow': workflow,
        'schritte': schritte,
    }

    return render(request, 'workflows/workflow_detail.html', context)


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
                erstellt_von=request.user,
                betroffene_person=form.cleaned_data.get('betroffene_person')
            )

            # Notizen hinzufügen falls vorhanden
            if form.cleaned_data.get('notizen'):
                workflow.notizen = form.cleaned_data['notizen']
                workflow.save()

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
