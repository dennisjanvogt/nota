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


# ============================================
# Besetzungsverfahren-spezifische Views
# ============================================

@login_required
def bewerber_auswaehlen_view(request, workflow_id):
    """
    Schritt 2: Bewerber auswählen.
    Aus allen Anwärtern werden 3 für das Verfahren ausgewählt.
    """
    from .models import WorkflowBewerber

    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    # Prüfen ob Workflow Besetzungsverfahren ist
    if workflow.workflow_typ.name != 'Besetzungsverfahren':
        messages.error(request, 'Diese Aktion ist nur für Besetzungsverfahren verfügbar.')
        return redirect('workflow_detail', workflow_id=workflow_id)

    if request.method == 'POST':
        # Ausgewählte Anwärter IDs aus POST
        ausgewaehlte_ids = request.POST.getlist('anwaerter_ids')

        if len(ausgewaehlte_ids) != 3:
            messages.error(request, 'Bitte wählen Sie genau 3 Bewerber aus.')
        else:
            # Bestehende Bewerber auf "abgelehnt" setzen, die nicht ausgewählt wurden
            WorkflowBewerber.objects.filter(
                workflow_instanz=workflow
            ).exclude(
                anwaerter_id__in=ausgewaehlte_ids
            ).update(status='abgelehnt')

            # Ausgewählte Bewerber erstellen oder aktualisieren
            for anwaerter_id in ausgewaehlte_ids:
                anwaerter = get_object_or_404(NotarAnwaerter, id=anwaerter_id)
                WorkflowBewerber.objects.update_or_create(
                    workflow_instanz=workflow,
                    anwaerter=anwaerter,
                    defaults={'status': 'ausgewaehlt'}
                )

            messages.success(request, f'3 Bewerber wurden erfolgreich ausgewählt.')

            # Schritt 2 abschließen
            schritt = workflow.schritt_instanzen.filter(
                workflow_schritt__reihenfolge=2
            ).first()
            if schritt and schritt.status == 'in_bearbeitung':
                WorkflowService.schritt_abschliessen(
                    schritt,
                    request.user,
                    notizen=f"3 Bewerber ausgewählt: {', '.join([NotarAnwaerter.objects.get(id=id).get_full_name() for id in ausgewaehlte_ids])}"
                )

            return redirect('workflow_detail', workflow_id=workflow_id)

    # Alle aktiven Anwärter
    anwaerter = NotarAnwaerter.objects.filter(ist_aktiv=True).order_by('nachname', 'vorname')

    # Bereits ausgewählte Bewerber
    ausgewaehlte_bewerber = WorkflowBewerber.objects.filter(
        workflow_instanz=workflow,
        status='ausgewaehlt'
    ).values_list('anwaerter_id', flat=True)

    context = {
        'workflow': workflow,
        'anwaerter': anwaerter,
        'ausgewaehlte_bewerber': list(ausgewaehlte_bewerber),
    }
    return render(request, 'workflows/bewerber_auswaehlen.html', context)


@login_required
def ranking_festlegen_view(request, workflow_id):
    """
    Schritt 8: Ranking nach Kammer-Sitzung festlegen.
    Die 3 ausgewählten Bewerber werden auf Platz 1, 2, 3 gesetzt.
    """
    from .models import WorkflowBewerber

    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if workflow.workflow_typ.name != 'Besetzungsverfahren':
        messages.error(request, 'Diese Aktion ist nur für Besetzungsverfahren verfügbar.')
        return redirect('workflow_detail', workflow_id=workflow_id)

    # Die 3 ausgewählten Bewerber
    bewerber = WorkflowBewerber.objects.filter(
        workflow_instanz=workflow,
        status='ausgewaehlt'
    ).select_related('anwaerter')

    if bewerber.count() != 3:
        messages.error(request, 'Es müssen genau 3 Bewerber ausgewählt sein.')
        return redirect('workflow_detail', workflow_id=workflow_id)

    if request.method == 'POST':
        platz_1_id = request.POST.get('platz_1')
        platz_2_id = request.POST.get('platz_2')
        platz_3_id = request.POST.get('platz_3')

        if not all([platz_1_id, platz_2_id, platz_3_id]):
            messages.error(request, 'Bitte ordnen Sie alle 3 Bewerber einem Platz zu.')
        elif len(set([platz_1_id, platz_2_id, platz_3_id])) != 3:
            messages.error(request, 'Jeder Bewerber darf nur einen Platz belegen.')
        else:
            # Ranking zuweisen
            for bewerber_obj in bewerber:
                if str(bewerber_obj.anwaerter.id) == platz_1_id:
                    bewerber_obj.status = 'platz_1'
                    bewerber_obj.ranking = 1
                elif str(bewerber_obj.anwaerter.id) == platz_2_id:
                    bewerber_obj.status = 'platz_2'
                    bewerber_obj.ranking = 2
                elif str(bewerber_obj.anwaerter.id) == platz_3_id:
                    bewerber_obj.status = 'platz_3'
                    bewerber_obj.ranking = 3
                bewerber_obj.save()

            messages.success(request, 'Ranking wurde erfolgreich festgelegt.')

            # Schritt 8 abschließen
            schritt = workflow.schritt_instanzen.filter(
                workflow_schritt__reihenfolge=8
            ).first()
            if schritt and schritt.status == 'in_bearbeitung':
                erstplatzierter = NotarAnwaerter.objects.get(id=platz_1_id)
                WorkflowService.schritt_abschliessen(
                    schritt,
                    request.user,
                    notizen=f"Ranking festgelegt. 1. Platz: {erstplatzierter.get_full_name()}"
                )

            return redirect('workflow_detail', workflow_id=workflow_id)

    context = {
        'workflow': workflow,
        'bewerber': bewerber,
    }
    return render(request, 'workflows/ranking_festlegen.html', context)


@login_required
def bestellung_durchfuehren_view(request, workflow_id):
    """
    Schritt 10: Bestellung durchführen.
    Der Erstplatzierte wird zum Notar befördert.
    """
    from .models import WorkflowBewerber
    from apps.personen.services import anwaerter_zu_notar_befoerdern

    workflow = get_object_or_404(WorkflowInstanz, id=workflow_id)

    if workflow.workflow_typ.name != 'Besetzungsverfahren':
        messages.error(request, 'Diese Aktion ist nur für Besetzungsverfahren verfügbar.')
        return redirect('workflow_detail', workflow_id=workflow_id)

    # Erstplatzierter holen
    erstplatzierter_bewerber = WorkflowBewerber.objects.filter(
        workflow_instanz=workflow,
        status='platz_1'
    ).select_related('anwaerter').first()

    if not erstplatzierter_bewerber:
        messages.error(request, 'Es wurde kein Erstplatzierter festgelegt.')
        return redirect('workflow_detail', workflow_id=workflow_id)

    anwaerter = erstplatzierter_bewerber.anwaerter

    if request.method == 'POST':
        notarstelle_id = request.POST.get('notarstelle')
        bestellt_am = request.POST.get('bestellt_am')

        if not notarstelle_id:
            messages.error(request, 'Bitte wählen Sie eine Notarstelle aus.')
        else:
            notarstelle = get_object_or_404(Notarstelle, id=notarstelle_id)

            try:
                # Anwärter zu Notar befördern
                from datetime import datetime
                bestellt_am_date = datetime.strptime(bestellt_am, '%Y-%m-%d').date() if bestellt_am else None

                notar = anwaerter_zu_notar_befoerdern(
                    anwaerter=anwaerter,
                    notarstelle=notarstelle,
                    bestellt_am=bestellt_am_date,
                    erstellt_von=request.user
                )

                messages.success(
                    request,
                    f'{anwaerter.get_full_name()} wurde erfolgreich zum Notar bestellt! (Notar-ID: {notar.notar_id})'
                )

                # Schritt 10 abschließen
                schritt = workflow.schritt_instanzen.filter(
                    workflow_schritt__reihenfolge=10
                ).first()
                if schritt and schritt.status == 'in_bearbeitung':
                    WorkflowService.schritt_abschliessen(
                        schritt,
                        request.user,
                        notizen=f"Bestellung durchgeführt. {anwaerter.get_full_name()} → Notar {notar.notar_id}"
                    )

                # Workflow abschließen
                workflow.status = 'abgeschlossen'
                workflow.abgeschlossen_am = timezone.now()
                workflow.save()

                return redirect('workflow_detail', workflow_id=workflow_id)

            except Exception as e:
                messages.error(request, f'Fehler bei der Bestellung: {str(e)}')

    # Alle Notarstellen
    notarstellen = Notarstelle.objects.filter(ist_aktiv=True).order_by('bezeichnung')

    context = {
        'workflow': workflow,
        'anwaerter': anwaerter,
        'notarstellen': notarstellen,
    }
    return render(request, 'workflows/bestellung_durchfuehren.html', context)
