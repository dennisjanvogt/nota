"""
Tests für das vereinfachte Workflow-System (Checklisten).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.workflows.models import (
    WorkflowTyp,
    WorkflowSchritt,
    WorkflowInstanz,
    WorkflowSchrittInstanz
)
from apps.workflows.services import WorkflowService

KammerBenutzer = get_user_model()


class WorkflowTypModelTest(TestCase):
    """Tests für WorkflowTyp Model."""

    def setUp(self):
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test-Checkliste',
            beschreibung='Eine Test-Checkliste',
            ist_aktiv=True
        )

    def test_workflow_typ_string_representation(self):
        """Test der String-Repräsentation."""
        self.assertEqual(str(self.workflow_typ), 'Test-Checkliste')

    def test_workflow_typ_creation(self):
        """Test Erstellung eines Workflow-Typs."""
        self.assertEqual(self.workflow_typ.name, 'Test-Checkliste')
        self.assertTrue(self.workflow_typ.ist_aktiv)


class WorkflowSchrittModelTest(TestCase):
    """Tests für WorkflowSchritt Model."""

    def setUp(self):
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test-Checkliste',
            ist_aktiv=True
        )
        self.schritt = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test-Schritt',
            reihenfolge=1,
            ist_optional=False
        )

    def test_workflow_schritt_string_representation(self):
        """Test der String-Repräsentation."""
        self.assertEqual(str(self.schritt), 'Test-Checkliste - Schritt 1: Test-Schritt')

    def test_workflow_schritt_ordering(self):
        """Test der Reihenfolge."""
        schritt2 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Zweiter Schritt',
            reihenfolge=2
        )
        schritte = list(WorkflowSchritt.objects.filter(
            workflow_typ=self.workflow_typ
        ).order_by('reihenfolge'))
        self.assertEqual(schritte[0], self.schritt)
        self.assertEqual(schritte[1], schritt2)


class WorkflowInstanzModelTest(TestCase):
    """Tests für WorkflowInstanz Model."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test-Workflow',
            ist_aktiv=True
        )
        # Schritte erstellen
        self.schritt1 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )
        self.schritt2 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 2',
            reihenfolge=2
        )

    def test_workflow_instanz_creation(self):
        """Test Erstellung einer Workflow-Instanz."""
        workflow = WorkflowInstanz.objects.create(
            workflow_typ=self.workflow_typ,
            name='Mein Test-Workflow',
            status='entwurf',
            erstellt_von=self.benutzer
        )
        self.assertEqual(workflow.name, 'Mein Test-Workflow')
        self.assertEqual(workflow.status, 'entwurf')

    def test_workflow_fortschritt_prozent(self):
        """Test der Fortschrittsberechnung."""
        workflow = WorkflowInstanz.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test',
            status='aktiv',
            erstellt_von=self.benutzer
        )
        # Schritt-Instanzen erstellen
        schritt_instanz1 = WorkflowSchrittInstanz.objects.create(
            workflow_instanz=workflow,
            workflow_schritt=self.schritt1,
            status='pending'
        )
        schritt_instanz2 = WorkflowSchrittInstanz.objects.create(
            workflow_instanz=workflow,
            workflow_schritt=self.schritt2,
            status='completed'
        )

        # 1 von 2 Schritten abgeschlossen = 50%
        self.assertEqual(workflow.fortschritt_prozent, 50)


class WorkflowServiceTest(TestCase):
    """Tests für WorkflowService."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test-Workflow',
            ist_aktiv=True
        )
        self.schritt1 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )
        self.schritt2 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 2',
            reihenfolge=2
        )

    def test_workflow_erstellen(self):
        """Test Workflow-Erstellung mit Service."""
        workflow = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test',
            erstellt_von=self.benutzer
        )

        self.assertEqual(workflow.name, 'Test')
        self.assertEqual(workflow.status, 'entwurf')
        self.assertEqual(workflow.schritt_instanzen.count(), 2)

        # Alle Schritte sollten initial 'pending' sein
        for schritt_instanz in workflow.schritt_instanzen.all():
            self.assertEqual(schritt_instanz.status, 'pending')

    def test_workflow_starten(self):
        """Test Workflow starten."""
        workflow = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test',
            erstellt_von=self.benutzer
        )

        WorkflowService.workflow_starten(workflow)
        workflow.refresh_from_db()

        self.assertEqual(workflow.status, 'aktiv')

    def test_schritt_abschliessen(self):
        """Test Schritt abschließen."""
        workflow = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test',
            erstellt_von=self.benutzer
        )

        schritt_instanz = workflow.schritt_instanzen.first()
        WorkflowService.schritt_abschliessen(schritt_instanz, notizen='Erledigt')
        schritt_instanz.refresh_from_db()

        self.assertEqual(schritt_instanz.status, 'completed')
        self.assertEqual(schritt_instanz.notizen, 'Erledigt')

    def test_workflow_auto_archivierung(self):
        """Test automatische Archivierung wenn alle Schritte completed."""
        workflow = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test',
            erstellt_von=self.benutzer
        )
        WorkflowService.workflow_starten(workflow)

        # Alle Schritte abschließen
        for schritt_instanz in workflow.schritt_instanzen.all():
            WorkflowService.schritt_abschliessen(schritt_instanz)

        workflow.refresh_from_db()
        self.assertEqual(workflow.status, 'archiviert')
        self.assertIsNotNone(workflow.archiviert_am)

    def test_workflow_suchen(self):
        """Test Workflow-Suche."""
        workflow1 = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Projekt Alpha',
            erstellt_von=self.benutzer
        )
        workflow2 = WorkflowService.workflow_erstellen(
            workflow_typ=self.workflow_typ,
            name='Projekt Beta',
            erstellt_von=self.benutzer
        )

        ergebnisse = WorkflowService.workflow_suchen('Alpha')
        self.assertEqual(ergebnisse.count(), 1)
        self.assertEqual(ergebnisse.first(), workflow1)
