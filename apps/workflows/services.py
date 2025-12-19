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
    def workflow_erstellen(workflow_typ, name, erstellt_von, betroffene_person=None):
        """
        Erstellt einen neuen Workflow und alle zugehörigen Schritt-Instanzen.

        Args:
            workflow_typ: Der Workflow-Typ (Template)
            name: Name des Workflows
            erstellt_von: Benutzer, der den Workflow erstellt
            betroffene_person: Optional - betroffene Person (z.B. Notar-Anwärter)

        Returns:
            WorkflowInstanz: Der erstellte Workflow
        """
        # Workflow erstellen
        workflow = WorkflowInstanz.objects.create(
            workflow_typ=workflow_typ,
            name=name,
            status='entwurf',
            erstellt_von=erstellt_von,
            betroffene_person=betroffene_person
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
    def schritt_abhaken(schritt_instanz):
        """
        Markiert einen Schritt als 'completed'.
        Prüft automatisch, ob alle Schritte abgeschlossen sind und archiviert ggf. den Workflow.

        Args:
            schritt_instanz: Die Schritt-Instanz
        """
        schritt_instanz.status = 'completed'
        schritt_instanz.save()

        # Prüfen ob alle Schritte completed sind
        workflow = schritt_instanz.workflow_instanz
        if workflow.schritt_instanzen.filter(status='pending').count() == 0:
            WorkflowService.workflow_archivieren(workflow)

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
        Liefert alle aktiven Workflows.

        Returns:
            QuerySet: Alle aktiven Workflow-Instanzen
        """
        return WorkflowInstanz.objects.filter(
            status='aktiv'
        ).select_related(
            'workflow_typ',
            'erstellt_von',
            'betroffene_person'
        ).order_by('-erstellt_am')
