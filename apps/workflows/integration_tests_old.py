"""
Integrationstests für komplette Workflows.
Diese Tests prüfen End-to-End-Szenarien für Workflow-Abläufe.
"""
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.notarstellen.models import Notarstelle
from apps.personen.models import Notar, NotarAnwaerter
from apps.workflows.models import (
    WorkflowTyp, WorkflowSchritt, WorkflowInstanz, WorkflowSchrittInstanz,
    WorkflowKommentar
)
from apps.workflows.services import WorkflowService
from apps.workflows.zustandsmaschine import WorkflowZustandsmaschine
from apps.aktenzeichen.models import Aktenzeichen

KammerBenutzer = get_user_model()


class BestellungsprozessIntegrationTest(TestCase):
    """Integrationstests für den kompletten Bestellungsprozess."""

    def setUp(self):
        """Test-Daten erstellen."""
        # Benutzer mit verschiedenen Rollen
        self.admin = KammerBenutzer.objects.create_user(
            username='admin',
            password='admin123',
            first_name='Admin',
            last_name='Benutzer',
            rolle='admin'
        )

        self.sachbearbeiter = KammerBenutzer.objects.create_user(
            username='sachbearbeiter',
            password='sb123',
            first_name='Sach',
            last_name='Bearbeiter',
            rolle='sachbearbeiter'
        )

        self.leitung = KammerBenutzer.objects.create_user(
            username='leitung',
            password='leitung123',
            first_name='Abteilungs',
            last_name='Leiter',
            rolle='leitung'
        )

        # Notarstelle
        self.notarstelle = Notarstelle.objects.create(
            notarnummer='1',
            bezeichnung='NOT-1',
            name='Notariat Hamburg I',
            strasse='Hauptstraße 1',
            plz='20095',
            stadt='Hamburg',
            bundesland='HH',
            ist_aktiv=True
        )

        # Notar
        self.notar = Notar.objects.create(
            vorname='Max',
            nachname='Mustermann',
            notar_id='N-001',
            notarstelle=self.notarstelle,
            bestellt_am=timezone.now().date(),
            beginn_datum=timezone.now().date(),
            ist_aktiv=True
        )

        # Notar-Anwärter
        self.anwaerter = NotarAnwaerter.objects.create(
            vorname='Maria',
            nachname='Musterfrau',
            anwaerter_id='A-001',
            betreuender_notar=self.notar,
            notarstelle=self.notarstelle,
            zugelassen_am=timezone.now().date(),
            beginn_datum=timezone.now().date(),
            ist_aktiv=True
        )

        # Workflow-Typ mit Schritten
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Bestellungsprozess Test',
            beschreibung='Test-Bestellungsprozess',
            ist_aktiv=True
        )

        # Schritte erstellen
        self.schritt1 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Antrag prüfen',
            reihenfolge=1,
            ist_optional=False,
            standard_zustaendige_rolle='sachbearbeiter',
            geschaetzte_dauer_tage=5
        )

        self.schritt2 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Dokumente nachfordern',
            reihenfolge=2,
            ist_optional=True,
            standard_zustaendige_rolle='sachbearbeiter',
            geschaetzte_dauer_tage=3
        )

        self.schritt3 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Präsidium vorlegen',
            reihenfolge=3,
            ist_optional=False,
            standard_zustaendige_rolle='leitung',
            geschaetzte_dauer_tage=7
        )

    def test_kompletter_bestellungsprozess(self):
        """Test: Kompletter Bestellungsprozess von Anfang bis Ende."""
        # 1. Workflow erstellen und starten
        workflow = WorkflowService.workflow_instanz_erstellen(
            workflow_typ=self.workflow_typ,
            name=f'Bestellung {self.anwaerter.vorname} {self.anwaerter.nachname}',
            erstellt_von=self.admin,
            erstelle_aktenzeichen=True,
            aktenzeichen_praefix='BES',
            aktenzeichen_kategorie='bestellung'
        )

        self.assertEqual(workflow.status, 'entwurf')
        self.assertIsNotNone(workflow.aktenzeichen)
        self.assertTrue(workflow.aktenzeichen.vollstaendige_nummer.startswith('BES-'))

        # 2. Workflow starten
        WorkflowService.workflow_starten(workflow)
        workflow.refresh_from_db()

        self.assertEqual(workflow.status, 'aktiv')
        self.assertIsNotNone(workflow.gestartet_am)

        # 3. Schritt-Instanzen prüfen
        schritte = WorkflowSchrittInstanz.objects.filter(
            workflow_instanz=workflow
        ).order_by('workflow_schritt__reihenfolge')

        self.assertEqual(schritte.count(), 3)

        # Erster Schritt sollte in_bearbeitung sein
        erster_schritt = schritte.first()
        self.assertEqual(erster_schritt.status, 'in_bearbeitung')
        self.assertIsNotNone(erster_schritt.gestartet_am)

        # Andere Schritte sollten ausstehend sein
        self.assertEqual(schritte[1].status, 'ausstehend')
        self.assertEqual(schritte[2].status, 'ausstehend')

        # 4. Ersten Schritt zuweisen
        WorkflowService.schritt_zuweisen(erster_schritt, self.sachbearbeiter)
        erster_schritt.refresh_from_db()
        self.assertEqual(erster_schritt.zugewiesen_an, self.sachbearbeiter)

        # 5. Ersten Schritt abschließen
        WorkflowService.schritt_abschliessen(
            erster_schritt,
            notizen='Antrag wurde geprüft und ist vollständig.'
        )
        erster_schritt.refresh_from_db()

        self.assertEqual(erster_schritt.status, 'abgeschlossen')
        self.assertIsNotNone(erster_schritt.abgeschlossen_am)
        self.assertEqual(erster_schritt.notizen, 'Antrag wurde geprüft und ist vollständig.')

        # 6. Zweiter Schritt sollte jetzt aktiv sein
        zweiter_schritt = schritte[1]
        zweiter_schritt.refresh_from_db()
        self.assertEqual(zweiter_schritt.status, 'in_bearbeitung')

        # 7. Zweiten Schritt (optional) überspringen
        zweiter_schritt.status = 'uebersprungen'
        zweiter_schritt.notizen = 'Nicht erforderlich - Dokumente vollständig.'
        zweiter_schritt.save()

        # Manuell nächsten Schritt aktivieren
        zustandsmaschine = WorkflowZustandsmaschine(workflow)
        naechster = zustandsmaschine._naechsten_schritt_ermitteln(zweiter_schritt)
        if naechster:
            naechster.status = 'in_bearbeitung'
            naechster.gestartet_am = timezone.now()
            naechster.save()

        # 8. Dritter Schritt sollte jetzt aktiv sein
        dritter_schritt = schritte[2]
        dritter_schritt.refresh_from_db()
        self.assertEqual(dritter_schritt.status, 'in_bearbeitung')

        # 9. Dritten Schritt zuweisen und abschließen
        WorkflowService.schritt_zuweisen(dritter_schritt, self.leitung)
        WorkflowService.schritt_abschliessen(
            dritter_schritt,
            notizen='Präsidium hat zugestimmt.'
        )

        # 10. Workflow sollte jetzt abgeschlossen sein
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, 'abgeschlossen')
        self.assertIsNotNone(workflow.abgeschlossen_am)

        # 11. Fortschritt sollte 100% sein
        self.assertEqual(workflow.fortschritt_prozent, 100)


class WorkflowKommentareIntegrationTest(TestCase):
    """Integrationstests für Workflow-Kommentare."""

    def setUp(self):
        """Test-Daten erstellen."""
        self.benutzer1 = KammerBenutzer.objects.create_user(
            username='user1',
            password='pass123',
            first_name='Benutzer',
            last_name='Eins',
            rolle='sachbearbeiter'
        )

        self.benutzer2 = KammerBenutzer.objects.create_user(
            username='user2',
            password='pass123',
            first_name='Benutzer',
            last_name='Zwei',
            rolle='leitung'
        )

        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )

        self.workflow = WorkflowInstanz.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Workflow Instanz',
            status='aktiv',
            erstellt_von=self.benutzer1
        )

        self.schritt = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Schritt',
            reihenfolge=1
        )

        self.schritt_instanz = WorkflowSchrittInstanz.objects.create(
            workflow_instanz=self.workflow,
            workflow_schritt=self.schritt,
            status='in_bearbeitung'
        )

    def test_kommentare_zu_workflow(self):
        """Test: Mehrere Benutzer können Kommentare zum Workflow hinzufügen."""
        # Benutzer 1 kommentiert
        kommentar1 = WorkflowKommentar.objects.create(
            workflow_instanz=self.workflow,
            benutzer=self.benutzer1,
            kommentar='Ich habe den Workflow gestartet.'
        )

        # Benutzer 2 kommentiert
        kommentar2 = WorkflowKommentar.objects.create(
            workflow_instanz=self.workflow,
            benutzer=self.benutzer2,
            kommentar='Bitte um Prüfung der Dokumente.'
        )

        # Benutzer 1 antwortet
        kommentar3 = WorkflowKommentar.objects.create(
            workflow_instanz=self.workflow,
            benutzer=self.benutzer1,
            kommentar='Dokumente sind vollständig.'
        )

        # Kommentare abrufen
        kommentare = WorkflowKommentar.objects.filter(
            workflow_instanz=self.workflow
        ).order_by('erstellt_am')

        self.assertEqual(kommentare.count(), 3)
        self.assertEqual(list(kommentare), [kommentar1, kommentar2, kommentar3])

    def test_kommentare_zu_schritt(self):
        """Test: Kommentare können spezifischen Schritten zugeordnet werden."""
        # Kommentar zum Workflow allgemein
        kommentar_workflow = WorkflowKommentar.objects.create(
            workflow_instanz=self.workflow,
            benutzer=self.benutzer1,
            kommentar='Allgemeiner Kommentar'
        )

        # Kommentar zu spezifischem Schritt
        kommentar_schritt = WorkflowKommentar.objects.create(
            workflow_instanz=self.workflow,
            schritt_instanz=self.schritt_instanz,
            benutzer=self.benutzer1,
            kommentar='Kommentar zu diesem Schritt'
        )

        # Nur Schritt-Kommentare abrufen
        schritt_kommentare = WorkflowKommentar.objects.filter(
            schritt_instanz=self.schritt_instanz
        )

        self.assertEqual(schritt_kommentare.count(), 1)
        self.assertEqual(schritt_kommentare.first(), kommentar_schritt)


class WorkflowAbbrechenIntegrationTest(TestCase):
    """Integrationstests für Workflow-Abbruch."""

    def setUp(self):
        """Test-Daten erstellen."""
        self.benutzer = KammerBenutzer.objects.create_user(
            username='user',
            password='pass123',
            rolle='admin'
        )

        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )

        for i in range(1, 4):
            WorkflowSchritt.objects.create(
                workflow_typ=self.workflow_typ,
                name=f'Schritt {i}',
                reihenfolge=i
            )

    def test_workflow_abbrechen(self):
        """Test: Workflow kann abgebrochen werden."""
        # Workflow erstellen und starten
        workflow = WorkflowService.workflow_instanz_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test Workflow',
            erstellt_von=self.benutzer
        )
        WorkflowService.workflow_starten(workflow)

        # Ersten Schritt abschließen
        erster_schritt = WorkflowSchrittInstanz.objects.filter(
            workflow_instanz=workflow,
            status='in_bearbeitung'
        ).first()
        WorkflowService.schritt_abschliessen(erster_schritt)

        # Workflow abbrechen
        zustandsmaschine = WorkflowZustandsmaschine(workflow)
        grund = 'Anwärter hat zurückgezogen.'
        zustandsmaschine.workflow_abbrechen(grund)

        # Workflow-Status prüfen
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, 'abgebrochen')
        self.assertIsNotNone(workflow.abgeschlossen_am)

        # Laufende Schritte sollten fehlgeschlagen sein
        schritte = WorkflowSchrittInstanz.objects.filter(
            workflow_instanz=workflow
        )

        abgeschlossen = schritte.filter(status='abgeschlossen').count()
        fehlgeschlagen = schritte.filter(status='fehlgeschlagen').count()
        ausstehend = schritte.filter(status='ausstehend').count()

        self.assertEqual(abgeschlossen, 1)  # Erster Schritt war abgeschlossen
        self.assertGreater(fehlgeschlagen, 0)  # Laufende Schritte
        self.assertGreaterEqual(ausstehend, 0)  # Restliche Schritte


class WorkflowWebIntegrationTest(TestCase):
    """Integrationstests für Workflow-Web-Interface."""

    def setUp(self):
        """Test-Daten erstellen."""
        self.client = Client()

        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            rolle='sachbearbeiter'
        )

        self.workflow_typ = WorkflowTyp.objects.create(
            name='Web Test Workflow',
            ist_aktiv=True
        )

        self.schritt = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Schritt',
            reihenfolge=1
        )

        self.workflow = WorkflowService.workflow_instanz_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test Workflow',
            erstellt_von=self.benutzer
        )

    def test_dashboard_zugriff_ohne_login(self):
        """Test: Dashboard erfordert Login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_zugriff_mit_login(self):
        """Test: Dashboard ist mit Login erreichbar."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'workflows/dashboard.html')

    def test_workflow_detail_ansicht(self):
        """Test: Workflow-Detail-Ansicht zeigt alle Informationen."""
        self.client.login(username='testuser', password='testpass123')

        WorkflowService.workflow_starten(self.workflow)

        response = self.client.get(
            reverse('workflow_detail', args=[self.workflow.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.workflow.name)
        self.assertContains(response, self.workflow_typ.name)

    def test_workflow_liste(self):
        """Test: Workflow-Liste zeigt alle Workflows."""
        self.client.login(username='testuser', password='testpass123')

        # Mehrere Workflows erstellen
        for i in range(3):
            WorkflowService.workflow_instanz_erstellen(
                workflow_typ=self.workflow_typ,
                name=f'Workflow {i+1}',
                erstellt_von=self.benutzer
            )

        response = self.client.get(reverse('workflow_liste'))
        self.assertEqual(response.status_code, 200)

        # Sollte alle 4 Workflows anzeigen (inklusive setUp)
        workflows = response.context['workflows']
        self.assertEqual(workflows.count(), 4)

    def test_meine_aufgaben_ansicht(self):
        """Test: 'Meine Aufgaben' zeigt zugewiesene Schritte."""
        self.client.login(username='testuser', password='testpass123')

        # Workflow starten
        WorkflowService.workflow_starten(self.workflow)

        # Schritt zuweisen
        schritt_instanz = WorkflowSchrittInstanz.objects.filter(
            workflow_instanz=self.workflow,
            status='in_bearbeitung'
        ).first()

        WorkflowService.schritt_zuweisen(schritt_instanz, self.benutzer)

        # Meine Aufgaben aufrufen
        response = self.client.get(reverse('meine_aufgaben'))
        self.assertEqual(response.status_code, 200)

        aufgaben = response.context['aufgaben']
        self.assertEqual(aufgaben.count(), 1)
        self.assertEqual(aufgaben.first(), schritt_instanz)

    def test_schritt_abschliessen_formular(self):
        """Test: Schritt kann über Formular abgeschlossen werden."""
        self.client.login(username='testuser', password='testpass123')

        # Workflow starten
        WorkflowService.workflow_starten(self.workflow)

        schritt_instanz = WorkflowSchrittInstanz.objects.filter(
            workflow_instanz=self.workflow,
            status='in_bearbeitung'
        ).first()

        # Formular aufrufen
        response = self.client.get(
            reverse('schritt_abschliessen', args=[schritt_instanz.id])
        )
        self.assertEqual(response.status_code, 200)

        # Schritt abschließen via POST
        response = self.client.post(
            reverse('schritt_abschliessen', args=[schritt_instanz.id]),
            {'notizen': 'Schritt wurde erfolgreich abgeschlossen.'}
        )

        # Sollte zu Workflow-Detail umleiten
        self.assertEqual(response.status_code, 302)

        schritt_instanz.refresh_from_db()
        self.assertEqual(schritt_instanz.status, 'abgeschlossen')
        self.assertEqual(
            schritt_instanz.notizen,
            'Schritt wurde erfolgreich abgeschlossen.'
        )

    def test_kommentar_hinzufuegen(self):
        """Test: Kommentar kann über Formular hinzugefügt werden."""
        self.client.login(username='testuser', password='testpass123')

        # Kommentar hinzufügen
        response = self.client.post(
            reverse('kommentar_hinzufuegen', args=[self.workflow.id]),
            {'kommentar': 'Dies ist ein Test-Kommentar.'}
        )

        # Sollte zu Workflow-Detail umleiten
        self.assertEqual(response.status_code, 302)

        # Kommentar prüfen
        kommentare = WorkflowKommentar.objects.filter(
            workflow_instanz=self.workflow
        )
        self.assertEqual(kommentare.count(), 1)
        self.assertEqual(
            kommentare.first().kommentar,
            'Dies ist ein Test-Kommentar.'
        )

    def test_workflow_abbrechen_formular(self):
        """Test: Workflow kann über Formular abgebrochen werden."""
        self.client.login(username='testuser', password='testpass123')

        WorkflowService.workflow_starten(self.workflow)

        # Abbrechen-Formular aufrufen
        response = self.client.get(
            reverse('workflow_abbrechen', args=[self.workflow.id])
        )
        self.assertEqual(response.status_code, 200)

        # Workflow abbrechen
        response = self.client.post(
            reverse('workflow_abbrechen', args=[self.workflow.id]),
            {'grund': 'Test-Abbruch'}
        )

        self.assertEqual(response.status_code, 302)

        self.workflow.refresh_from_db()
        self.assertEqual(self.workflow.status, 'abgebrochen')


class AktenzeichenWorkflowIntegrationTest(TestCase):
    """Integrationstests für Aktenzeichen + Workflow Integration."""

    def setUp(self):
        """Test-Daten erstellen."""
        self.benutzer = KammerBenutzer.objects.create_user(
            username='user',
            password='pass123',
            rolle='admin'
        )

        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )

        WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )

    def test_automatische_aktenzeichen_generierung(self):
        """Test: Aktenzeichen wird automatisch beim Workflow erstellt."""
        workflow = WorkflowService.workflow_instanz_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test Workflow',
            erstellt_von=self.benutzer,
            erstelle_aktenzeichen=True,
            aktenzeichen_praefix='TEST',
            aktenzeichen_kategorie='allgemein'
        )

        self.assertIsNotNone(workflow.aktenzeichen)
        self.assertEqual(workflow.aktenzeichen.kategorie, 'allgemein')
        self.assertTrue(
            workflow.aktenzeichen.vollstaendige_nummer.startswith('TEST-')
        )

    def test_workflow_ohne_aktenzeichen(self):
        """Test: Workflow kann auch ohne Aktenzeichen erstellt werden."""
        workflow = WorkflowService.workflow_instanz_erstellen(
            workflow_typ=self.workflow_typ,
            name='Test Workflow',
            erstellt_von=self.benutzer,
            erstelle_aktenzeichen=False
        )

        self.assertIsNone(workflow.aktenzeichen)

    def test_mehrere_workflows_mit_sequenziellen_nummern(self):
        """Test: Mehrere Workflows erhalten sequenzielle Aktenzeichen."""
        workflows = []
        for i in range(5):
            workflow = WorkflowService.workflow_instanz_erstellen(
                workflow_typ=self.workflow_typ,
                name=f'Workflow {i+1}',
                erstellt_von=self.benutzer,
                erstelle_aktenzeichen=True,
                aktenzeichen_praefix='BES',
                aktenzeichen_kategorie='bestellung'
            )
            workflows.append(workflow)

        # Alle sollten Aktenzeichen haben
        for workflow in workflows:
            self.assertIsNotNone(workflow.aktenzeichen)

        # Nummern sollten aufsteigend sein
        nummern = [
            int(w.aktenzeichen.vollstaendige_nummer.split('-')[-1])
            for w in workflows
        ]
        self.assertEqual(nummern, sorted(nummern))

        # Sollten lückenlos sein
        self.assertEqual(nummern[-1] - nummern[0], 4)
