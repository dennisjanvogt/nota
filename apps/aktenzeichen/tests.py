"""
Tests für Aktenzeichen-System.

Insbesondere Tests für Thread-Safety der Nummern-Generierung.
"""
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
import threading
from .models import Nummernsequenz, Aktenzeichen
from .services import AktenzeichenService


class NummernsequenzModelTest(TestCase):
    """Tests für Nummernsequenz Model."""

    def setUp(self):
        self.jahr = timezone.now().year
        self.sequenz = Nummernsequenz.objects.create(
            jahr=self.jahr,
            praefix='BES',
            aktuelle_nummer=0
        )

    def test_sequenz_erstellen(self):
        """Test: Sequenz kann erstellt werden."""
        self.assertEqual(self.sequenz.praefix, 'BES')
        self.assertEqual(self.sequenz.jahr, self.jahr)
        self.assertEqual(self.sequenz.aktuelle_nummer, 0)

    def test_naechste_nummer_holen(self):
        """Test: Nächste Nummer wird korrekt generiert."""
        nummer1 = self.sequenz.naechste_nummer_holen()
        self.assertEqual(nummer1, 1)

        nummer2 = self.sequenz.naechste_nummer_holen()
        self.assertEqual(nummer2, 2)

        nummer3 = self.sequenz.naechste_nummer_holen()
        self.assertEqual(nummer3, 3)

    def test_vorschau_naechste_nummer(self):
        """Test: Vorschau ändert Sequenz nicht."""
        vorschau1 = self.sequenz.vorschau_naechste_nummer()
        self.assertEqual(vorschau1, 1)

        # Vorschau sollte Sequenz nicht ändern
        vorschau2 = self.sequenz.vorschau_naechste_nummer()
        self.assertEqual(vorschau2, 1)


class AktenzeichenModelTest(TestCase):
    """Tests für Aktenzeichen Model."""

    def setUp(self):
        self.jahr = timezone.now().year
        self.sequenz = Nummernsequenz.objects.create(
            jahr=self.jahr,
            praefix='BES',
            aktuelle_nummer=0
        )

    def test_aktenzeichen_erstellen(self):
        """Test: Aktenzeichen wird korrekt erstellt."""
        az = Aktenzeichen.objects.create(
            sequenz=self.sequenz,
            laufnummer=1,
            jahr=self.jahr,
            kategorie='Bestellung',
            beschreibung='Test Aktenzeichen'
        )

        self.assertEqual(az.vollstaendige_nummer, f'BES-{self.jahr}-0001')

    def test_nummer_generierung_format(self):
        """Test: Nummer wird im korrekten Format generiert."""
        az = Aktenzeichen.objects.create(
            sequenz=self.sequenz,
            laufnummer=42,
            jahr=self.jahr,
            kategorie='Bestellung'
        )

        self.assertEqual(az.vollstaendige_nummer, f'BES-{self.jahr}-0042')

    def test_fuehrende_nullen(self):
        """Test: Führende Nullen werden korrekt hinzugefügt."""
        test_cases = [
            (1, '0001'),
            (10, '0010'),
            (100, '0100'),
            (1000, '1000'),
        ]

        for laufnummer, erwartete_nummer in test_cases:
            az = Aktenzeichen.objects.create(
                sequenz=self.sequenz,
                laufnummer=laufnummer,
                jahr=self.jahr,
                kategorie='Bestellung'
            )
            self.assertTrue(az.vollstaendige_nummer.endswith(erwartete_nummer))


class AktenzeichenServiceTest(TestCase):
    """Tests für AktenzeichenService."""

    def setUp(self):
        self.jahr = timezone.now().year

    def test_aktenzeichen_generieren(self):
        """Test: Service generiert Aktenzeichen korrekt."""
        az = AktenzeichenService.aktenzeichen_generieren(
            praefix='BES',
            kategorie='Bestellung',
            jahr=self.jahr,
            beschreibung='Test'
        )

        self.assertIsNotNone(az)
        self.assertEqual(az.kategorie, 'Bestellung')
        self.assertEqual(az.jahr, self.jahr)
        self.assertTrue(az.vollstaendige_nummer.startswith('BES'))

    def test_sequentielle_generierung(self):
        """Test: Mehrere Aktenzeichen werden sequentiell generiert."""
        az1 = AktenzeichenService.aktenzeichen_generieren(
            praefix='BES',
            kategorie='Bestellung',
            jahr=self.jahr
        )
        az2 = AktenzeichenService.aktenzeichen_generieren(
            praefix='BES',
            kategorie='Bestellung',
            jahr=self.jahr
        )
        az3 = AktenzeichenService.aktenzeichen_generieren(
            praefix='BES',
            kategorie='Bestellung',
            jahr=self.jahr
        )

        self.assertEqual(az1.laufnummer, 1)
        self.assertEqual(az2.laufnummer, 2)
        self.assertEqual(az3.laufnummer, 3)

    def test_vorschau_holen(self):
        """Test: Vorschau wird korrekt generiert."""
        vorschau = AktenzeichenService.vorschau_holen('BES', self.jahr)
        self.assertEqual(vorschau, f'BES-{self.jahr}-0001')

        # Generiere ein Aktenzeichen
        AktenzeichenService.aktenzeichen_generieren('BES', 'Bestellung', self.jahr)

        # Vorschau sollte jetzt 0002 sein
        vorschau = AktenzeichenService.vorschau_holen('BES', self.jahr)
        self.assertEqual(vorschau, f'BES-{self.jahr}-0002')

    def test_statistik_holen(self):
        """Test: Statistik wird korrekt erstellt."""
        # Generiere einige Aktenzeichen
        for _ in range(3):
            AktenzeichenService.aktenzeichen_generieren('BES', 'Bestellung', self.jahr)

        for _ in range(2):
            AktenzeichenService.aktenzeichen_generieren('ZUL', 'Zulassung', self.jahr)

        statistik = AktenzeichenService.statistik_holen(self.jahr)

        self.assertIn('BES', statistik)
        self.assertIn('ZUL', statistik)
        self.assertEqual(statistik['BES']['anzahl'], 3)
        self.assertEqual(statistik['ZUL']['anzahl'], 2)


class ThreadSafetyTest(TransactionTestCase):
    """
    Tests für Thread-Safety der Nummern-Generierung.

    WICHTIG: Verwendet TransactionTestCase für echte Parallelität!
    """

    def setUp(self):
        self.jahr = timezone.now().year
        self.generated_numbers = []
        self.lock = threading.Lock()

    def test_concurrent_generation(self):
        """
        Test: Parallele Generierung erzeugt eindeutige Nummern.

        Dieser Test startet mehrere Threads parallel, die gleichzeitig
        Aktenzeichen generieren. Alle Nummern müssen eindeutig sein!
        """
        anzahl_threads = 10
        results = []

        def generate_aktenzeichen():
            """Generiert ein Aktenzeichen und speichert die Laufnummer."""
            az = AktenzeichenService.aktenzeichen_generieren(
                praefix='BES',
                kategorie='Bestellung',
                jahr=self.jahr
            )
            with self.lock:
                results.append(az.laufnummer)

        # Starte Threads
        threads = [threading.Thread(target=generate_aktenzeichen) for _ in range(anzahl_threads)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Prüfe: Alle Nummern müssen eindeutig sein
        self.assertEqual(len(results), anzahl_threads)
        self.assertEqual(len(set(results)), anzahl_threads)

        # Prüfe: Nummern müssen von 1 bis anzahl_threads gehen
        self.assertEqual(sorted(results), list(range(1, anzahl_threads + 1)))

    def test_concurrent_different_prefixes(self):
        """Test: Parallele Generierung mit verschiedenen Präfixen."""
        anzahl_pro_praefix = 5
        praefixe = ['BES', 'ZUL', 'AUF']
        results = {p: [] for p in praefixe}

        def generate_for_praefix(praefix):
            """Generiert mehrere Aktenzeichen für einen Präfix."""
            for _ in range(anzahl_pro_praefix):
                az = AktenzeichenService.aktenzeichen_generieren(
                    praefix=praefix,
                    kategorie='Bestellung' if praefix == 'BES' else 'Allgemein',
                    jahr=self.jahr
                )
                with self.lock:
                    results[praefix].append(az.laufnummer)

        # Starte Threads für jeden Präfix
        threads = [threading.Thread(target=generate_for_praefix, args=(p,)) for p in praefixe]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Prüfe: Jeder Präfix hat eindeutige Nummern
        for praefix in praefixe:
            self.assertEqual(len(results[praefix]), anzahl_pro_praefix)
            self.assertEqual(len(set(results[praefix])), anzahl_pro_praefix)
            self.assertEqual(sorted(results[praefix]), list(range(1, anzahl_pro_praefix + 1)))
