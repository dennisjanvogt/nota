"""
Tests für Workflow-System.

Vereinfachte Tests für Models und Service.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import (
    WorkflowTyp,
    WorkflowSchritt,
    WorkflowInstanz,
    WorkflowSchrittInstanz
)
from .services import WorkflowService
from apps.personen.models import NotarAnwaerter, Notar
from apps.notarstellen.models import Notarstelle

KammerBenutzer = get_user_model()


class WorkflowTypModelTest(TestCase):
    """Tests für WorkflowTyp Model."""

    def setUp(self):
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            beschreibung='Ein Test-Workflow',
            ist_aktiv=True,
            erlaube_parallele_schritte=False,
            erfordert_sequentielle_abarbeitung=True
        )

    def test_workflow_typ_erstellen(self):
        """Test: WorkflowTyp kann erstellt werden."""
        self.assertEqual(self.workflow_typ.name, 'Test Workflow')
        self.assertTrue(self.workflow_typ.ist_aktiv)
        self.assertFalse(self.workflow_typ.erlaube_parallele_schritte)

    def test_schritte_anzahl(self):
        """Test: Schritte-Anzahl wird korrekt gezählt."""
        # Ohne Schritte
        self.assertEqual(self.workflow_typ.schritte_anzahl(), 0)

        # Mit Schritten
        WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )
        WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 2',
            reihenfolge=2
        )
        self.assertEqual(self.workflow_typ.schritte_anzahl(), 2)


class WorkflowSchrittModelTest(TestCase):
    """Tests für WorkflowSchritt Model."""

    def setUp(self):
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )
        self.schritt = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Schritt',
            beschreibung='Ein Test-Schritt',
            reihenfolge=1,
            geschaetzte_dauer_tage=5,
            standard_zustaendige_rolle='sachbearbeiter'
        )

    def test_schritt_erstellen(self):
        """Test: Schritt kann erstellt werden."""
        self.assertEqual(self.schritt.name, 'Test Schritt')
        self.assertEqual(self.schritt.reihenfolge, 1)
        self.assertEqual(self.schritt.geschaetzte_dauer_tage, 5)


class WorkflowSchrittUebergangModelTest(TestCase):
    """Tests für WorkflowSchrittUebergang Model."""

    def setUp(self):
        self.workflow_typ = WorkflowTyp.objects.create(name='Test Workflow')
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

    def test_uebergang_erstellen(self):
        """Test: Übergang kann erstellt werden."""
        uebergang = WorkflowSchrittUebergang.objects.create(
            von_schritt=self.schritt1,
            zu_schritt=self.schritt2
        )
        self.assertEqual(uebergang.von_schritt, self.schritt1)
        self.assertEqual(uebergang.zu_schritt, self.schritt2)

    def test_uebergang_verschiedene_workflow_typen_validierung(self):
        """Test: Übergänge zwischen verschiedenen Workflow-Typen sind nicht erlaubt."""
        anderer_workflow_typ = WorkflowTyp.objects.create(name='Anderer Workflow')
        schritt3 = WorkflowSchritt.objects.create(
            workflow_typ=anderer_workflow_typ,
            name='Schritt 3',
            reihenfolge=1
        )

        uebergang = WorkflowSchrittUebergang(
            von_schritt=self.schritt1,
            zu_schritt=schritt3
        )

        with self.assertRaises(ValidationError):
            uebergang.clean()


class WorkflowInstanzModelTest(TestCase):
    """Tests für WorkflowInstanz Model."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.workflow_typ = WorkflowTyp.objects.create(name='Test Workflow')
        self.workflow_instanz = WorkflowInstanz.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Instanz',
            status='entwurf',
            erstellt_von=self.benutzer
        )

    def test_workflow_instanz_erstellen(self):
        """Test: Workflow-Instanz kann erstellt werden."""
        self.assertEqual(self.workflow_instanz.name, 'Test Instanz')
        self.assertEqual(self.workflow_instanz.status, 'entwurf')
        self.assertEqual(self.workflow_instanz.erstellt_von, self.benutzer)

    def test_fortschritt_prozent_ohne_schritte(self):
        """Test: Fortschritt ist 0% ohne Schritte."""
        self.assertEqual(self.workflow_instanz.fortschritt_prozent(), 0)

    def test_fortschritt_prozent_mit_schritten(self):
        """Test: Fortschritt wird korrekt berechnet."""
        # Erstelle Schritte
        schritt1 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )
        schritt2 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 2',
            reihenfolge=2
        )

        # Erstelle Schritt-Instanzen
        WorkflowSchrittInstanz.objects.create(
            workflow_instanz=self.workflow_instanz,
            workflow_schritt=schritt1,
            status='abgeschlossen'
        )
        WorkflowSchrittInstanz.objects.create(
            workflow_instanz=self.workflow_instanz,
            workflow_schritt=schritt2,
            status='in_bearbeitung'
        )

        # 1 von 2 Schritten abgeschlossen = 50%
        self.assertEqual(self.workflow_instanz.fortschritt_prozent(), 50)


class WorkflowZustandsmaschineTest(TestCase):
    """Tests für WorkflowZustandsmaschine."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )

        # Erstelle Schritte
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
        self.schritt3 = WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 3',
            reihenfolge=3,
            ist_optional=True
        )

        self.workflow_instanz = WorkflowInstanz.objects.create(
            workflow_typ=self.workflow_typ,
            name='Test Instanz',
            status='entwurf',
            erstellt_von=self.benutzer
        )

    def test_workflow_starten(self):
        """Test: Workflow kann gestartet werden."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Workflow-Status sollte 'aktiv' sein
        self.workflow_instanz.refresh_from_db()
        self.assertEqual(self.workflow_instanz.status, 'aktiv')
        self.assertIsNotNone(self.workflow_instanz.gestartet_am)

        # Alle Schritte sollten erstellt sein
        self.assertEqual(self.workflow_instanz.schritt_instanzen.count(), 3)

        # Erster Schritt sollte 'in_bearbeitung' sein
        erster_schritt = self.workflow_instanz.schritt_instanzen.first()
        self.assertEqual(erster_schritt.status, 'in_bearbeitung')

    def test_workflow_starten_ohne_schritte(self):
        """Test: Workflow ohne Schritte kann nicht gestartet werden."""
        # Lösche alle Schritte
        WorkflowSchritt.objects.all().delete()

        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        with self.assertRaises(ValidationError):
            zustandsmaschine.workflow_starten()

    def test_schritt_abschliessen(self):
        """Test: Schritt kann abgeschlossen werden."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Hole ersten Schritt
        schritt_instanz = self.workflow_instanz.schritt_instanzen.first()

        # Schließe Schritt ab
        naechster_schritt = zustandsmaschine.schritt_abschliessen(
            schritt_instanz,
            notizen='Test abgeschlossen'
        )

        # Schritt sollte abgeschlossen sein
        schritt_instanz.refresh_from_db()
        self.assertEqual(schritt_instanz.status, 'abgeschlossen')
        self.assertIsNotNone(schritt_instanz.abgeschlossen_am)
        self.assertEqual(schritt_instanz.notizen, 'Test abgeschlossen')

        # Nächster Schritt sollte aktiv sein
        self.assertIsNotNone(naechster_schritt)
        self.assertEqual(naechster_schritt.status, 'in_bearbeitung')

    def test_schritt_ueberspringen(self):
        """Test: Optionaler Schritt kann übersprungen werden."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Schließe ersten und zweiten Schritt ab
        schritt1 = self.workflow_instanz.schritt_instanzen.get(
            workflow_schritt__reihenfolge=1
        )
        zustandsmaschine.schritt_abschliessen(schritt1)

        schritt2 = self.workflow_instanz.schritt_instanzen.get(
            workflow_schritt__reihenfolge=2
        )
        zustandsmaschine.schritt_abschliessen(schritt2)

        # Hole dritten Schritt (optional)
        schritt3 = self.workflow_instanz.schritt_instanzen.get(
            workflow_schritt__reihenfolge=3
        )

        # Überspringe Schritt
        zustandsmaschine.schritt_ueberspringen(schritt3, grund='Nicht benötigt')

        # Schritt sollte übersprungen sein
        schritt3.refresh_from_db()
        self.assertEqual(schritt3.status, 'uebersprungen')
        self.assertIn('Übersprungen', schritt3.notizen)

    def test_schritt_ueberspringen_nicht_optional(self):
        """Test: Nicht-optionaler Schritt kann nicht übersprungen werden."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Hole ersten Schritt (nicht optional)
        schritt_instanz = self.workflow_instanz.schritt_instanzen.first()

        with self.assertRaises(ValidationError):
            zustandsmaschine.schritt_ueberspringen(schritt_instanz)

    def test_workflow_abschluss(self):
        """Test: Workflow wird automatisch abgeschlossen."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Schließe alle Schritte ab
        for schritt_instanz in self.workflow_instanz.schritt_instanzen.all():
            schritt_instanz.refresh_from_db()
            if schritt_instanz.status == 'in_bearbeitung':
                zustandsmaschine.schritt_abschliessen(schritt_instanz)

        # Workflow sollte abgeschlossen sein
        self.workflow_instanz.refresh_from_db()
        self.assertEqual(self.workflow_instanz.status, 'abgeschlossen')
        self.assertIsNotNone(self.workflow_instanz.abgeschlossen_am)

    def test_workflow_abbrechen(self):
        """Test: Workflow kann abgebrochen werden."""
        zustandsmaschine = WorkflowZustandsmaschine(self.workflow_instanz)
        zustandsmaschine.workflow_starten()

        # Breche Workflow ab
        zustandsmaschine.workflow_abbrechen(grund='Test abgebrochen')

        # Workflow sollte abgebrochen sein
        self.workflow_instanz.refresh_from_db()
        self.assertEqual(self.workflow_instanz.status, 'abgebrochen')
        self.assertIn('abgebrochen', self.workflow_instanz.notizen.lower())


class WorkflowServiceTest(TestCase):
    """Tests für WorkflowService."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            password='testpass123',
            rolle='sachbearbeiter'
        )

        # Erstelle Workflow-Typ mit Schritten
        self.workflow_typ = WorkflowTyp.objects.create(
            name='Test Workflow',
            ist_aktiv=True
        )
        WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 1',
            reihenfolge=1
        )
        WorkflowSchritt.objects.create(
            workflow_typ=self.workflow_typ,
            name='Schritt 2',
            reihenfolge=2
        )

    def test_workflow_instanz_erstellen(self):
        """Test: Workflow-Instanz kann über Service erstellt werden."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test Service Workflow',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=False
        )

        self.assertIsNotNone(workflow_instanz)
        self.assertEqual(workflow_instanz.name, 'Test Service Workflow')
        self.assertEqual(workflow_instanz.status, 'entwurf')
        self.assertIsNone(workflow_instanz.aktenzeichen)

    def test_workflow_instanz_erstellen_mit_aktenzeichen(self):
        """Test: Workflow-Instanz mit Aktenzeichen erstellen."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test mit AZ',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=True,
            aktenzeichen_praefix='ALL',
            aktenzeichen_kategorie='Allgemein'
        )

        self.assertIsNotNone(workflow_instanz.aktenzeichen)
        self.assertTrue(
            workflow_instanz.aktenzeichen.vollstaendige_nummer.startswith('ALL')
        )

    def test_workflow_starten_ueber_service(self):
        """Test: Workflow kann über Service gestartet werden."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test Start',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=False
        )

        workflow_instanz = WorkflowService.workflow_starten(workflow_instanz)

        self.assertEqual(workflow_instanz.status, 'aktiv')
        self.assertEqual(workflow_instanz.schritt_instanzen.count(), 2)

    def test_schritt_zuweisen(self):
        """Test: Schritt kann zugewiesen werden."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test Zuweisung',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=False
        )
        WorkflowService.workflow_starten(workflow_instanz)

        schritt_instanz = workflow_instanz.schritt_instanzen.first()

        # Weise Schritt zu
        WorkflowService.schritt_zuweisen(schritt_instanz, self.benutzer)

        schritt_instanz.refresh_from_db()
        self.assertEqual(schritt_instanz.zugewiesen_an, self.benutzer)

    def test_kommentar_hinzufuegen(self):
        """Test: Kommentar kann hinzugefügt werden."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test Kommentar',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=False
        )

        kommentar = WorkflowService.kommentar_hinzufuegen(
            workflow_instanz=workflow_instanz,
            benutzer=self.benutzer,
            kommentar='Test Kommentar Text'
        )

        self.assertIsNotNone(kommentar)
        self.assertEqual(kommentar.kommentar, 'Test Kommentar Text')
        self.assertEqual(kommentar.benutzer, self.benutzer)

    def test_meine_aufgaben_holen(self):
        """Test: Eigene Aufgaben können abgerufen werden."""
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Test Workflow',
            name='Test Aufgaben',
            erstellt_von=self.benutzer,
            mit_aktenzeichen=False
        )
        WorkflowService.workflow_starten(workflow_instanz)

        # Weise ersten Schritt zu
        schritt_instanz = workflow_instanz.schritt_instanzen.first()
        WorkflowService.schritt_zuweisen(schritt_instanz, self.benutzer)

        # Hole eigene Aufgaben
        aufgaben = WorkflowService.meine_aufgaben_holen(self.benutzer)

        self.assertEqual(aufgaben.count(), 1)
        self.assertEqual(aufgaben.first(), schritt_instanz)


class BestellungsprozessTest(TestCase):
    """Tests für Bestellungsprozess-Workflow."""

    def setUp(self):
        self.benutzer = KammerBenutzer.objects.create_user(
            username='testuser',
            password='testpass123',
            rolle='sachbearbeiter'
        )

        # Erstelle Notarstelle
        self.notarstelle = Notarstelle.objects.create(
            notarnummer='1',
            bezeichnung='TEST-1',
            name='Test Notariat',
            plz='12345',
            stadt='Teststadt'
        )

        # Erstelle betreuenden Notar
        self.betreuender_notar = Notar.objects.create(
            vorname='Max',
            nachname='Mustermann',
            notar_id='N001',
            notarstelle=self.notarstelle,
            beginn_datum=timezone.now().date(),
            bestellt_am=timezone.now().date()
        )

        # Erstelle Notar-Anwärter
        self.notar_anwaerter = NotarAnwaerter.objects.create(
            vorname='Erika',
            nachname='Musterfrau',
            anwaerter_id='A001',
            betreuender_notar=self.betreuender_notar,
            notarstelle=self.notarstelle,
            beginn_datum=timezone.now().date(),
            zugelassen_am=timezone.now().date()
        )

        # Erstelle Bestellungsprozess-Workflow
        self.workflow_typ = WorkflowTyp.objects.get_or_create(
            name='Bestellungsprozess',
            defaults={'ist_aktiv': True}
        )[0]

        # Erstelle mindestens einen Schritt
        if not self.workflow_typ.schritte.exists():
            WorkflowSchritt.objects.create(
                workflow_typ=self.workflow_typ,
                name='Antrag prüfen',
                reihenfolge=1
            )

    def test_bestellungsprozess_starten(self):
        """Test: Bestellungsprozess kann gestartet werden."""
        workflow_instanz = WorkflowService.bestellungsprozess_starten(
            notar_anwaerter=self.notar_anwaerter,
            erstellt_von=self.benutzer
        )

        self.assertIsNotNone(workflow_instanz)
        self.assertEqual(workflow_instanz.status, 'aktiv')
        self.assertEqual(workflow_instanz.betroffene_person, self.notar_anwaerter)
        self.assertIsNotNone(workflow_instanz.aktenzeichen)
        self.assertTrue(
            workflow_instanz.aktenzeichen.vollstaendige_nummer.startswith('BES')
        )
