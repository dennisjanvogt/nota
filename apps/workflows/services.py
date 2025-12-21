"""
Vereinfachter Service für Checklisten-Workflow.
"""
from django.db import transaction
from django.utils import timezone
from .models import (
    WorkflowInstanz,
    WorkflowSchrittInstanz
)


class WorkflowService:
    """
    Vereinfachter Service für grundlegende Checklisten-Operationen.
    """

    @staticmethod
    @transaction.atomic
    def workflow_erstellen(workflow_typ, name, erstellt_von):
        """
        Erstellt einen neuen Workflow und alle zugehörigen Schritt-Instanzen.

        Args:
            workflow_typ: Der Workflow-Typ (Template)
            name: Name des Workflows
            erstellt_von: Benutzer, der den Workflow erstellt

        Returns:
            WorkflowInstanz: Der erstellte Workflow
        """
        # Workflow erstellen
        workflow = WorkflowInstanz.objects.create(
            workflow_typ=workflow_typ,
            name=name,
            status='entwurf',
            erstellt_von=erstellt_von
        )

        # Alle Schritt-Instanzen erstellen
        for schritt in workflow_typ.schritte.all().order_by('reihenfolge'):
            WorkflowSchrittInstanz.objects.create(
                workflow_instanz=workflow,
                workflow_schritt=schritt,
                status='pending'
            )

        return workflow

    @staticmethod
    def workflow_starten(workflow_instanz):
        """
        Setzt Workflow-Status von 'entwurf' auf 'aktiv'.

        Args:
            workflow_instanz: Die Workflow-Instanz
        """
        workflow_instanz.status = 'aktiv'
        workflow_instanz.save()

    @staticmethod
    def schritt_abschliessen(schritt_instanz, notizen=''):
        """
        Markiert einen Schritt als 'completed'.
        Prüft automatisch, ob alle Schritte abgeschlossen sind und archiviert ggf. den Workflow.

        Args:
            schritt_instanz: Die Schritt-Instanz
            notizen: Optionale Notizen zum Abschluss
        """
        schritt_instanz.status = 'completed'
        if notizen:
            schritt_instanz.notizen = notizen
        schritt_instanz.save()

        # Prüfen ob alle Schritte completed sind
        workflow = schritt_instanz.workflow_instanz
        if workflow.schritt_instanzen.filter(status='pending').count() == 0:
            WorkflowService.workflow_archivieren(workflow)

    @staticmethod
    @transaction.atomic
    def schritt_rueckgaengig_machen(schritt_instanz):
        """
        Setzt einen abgeschlossenen Schritt zurück auf 'pending'.
        Falls der Workflow archiviert war, wird er wieder auf 'aktiv' gesetzt.

        Args:
            schritt_instanz: Die Schritt-Instanz
        """
        schritt_instanz.status = 'pending'
        schritt_instanz.save()

        # Falls Workflow archiviert war, wieder aktivieren
        workflow = schritt_instanz.workflow_instanz
        if workflow.status == 'archiviert':
            workflow.status = 'aktiv'
            workflow.archiviert_am = None
            workflow.save()

    @staticmethod
    def workflow_archivieren(workflow_instanz):
        """
        Archiviert einen Workflow (Status = 'archiviert').

        Args:
            workflow_instanz: Die Workflow-Instanz
        """
        workflow_instanz.status = 'archiviert'
        workflow_instanz.archiviert_am = timezone.now()
        workflow_instanz.save()

    @staticmethod
    def offene_workflows_holen():
        """
        Liefert alle offenen Workflows (nicht archiviert).

        Returns:
            QuerySet: Alle offenen Workflow-Instanzen (Entwurf und Aktiv)
        """
        return WorkflowInstanz.objects.exclude(
            status='archiviert'
        ).select_related(
            'workflow_typ',
            'erstellt_von'
        ).prefetch_related(
            'betroffene_notare',
            'betroffene_kandidaten'
        ).order_by('-erstellt_am')

    @staticmethod
    def workflow_suchen(suchbegriff):
        """
        Sucht Workflows nach Name oder Workflow-Typ.

        Args:
            suchbegriff: Suchbegriff für die Suche

        Returns:
            QuerySet: Gefilterte Workflow-Instanzen
        """
        from django.db.models import Q
        return WorkflowInstanz.objects.filter(
            Q(name__icontains=suchbegriff) |
            Q(workflow_typ__name__icontains=suchbegriff) |
            Q(notizen__icontains=suchbegriff)
        ).select_related(
            'workflow_typ',
            'erstellt_von',
            'betroffene_person'
        ).order_by('-erstellt_am')
