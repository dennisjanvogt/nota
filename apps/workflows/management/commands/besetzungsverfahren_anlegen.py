"""
Management Command zum Anlegen des Besetzungsverfahren-Workflows.
"""
from django.core.management.base import BaseCommand
from apps.workflows.models import WorkflowTyp, WorkflowSchritt


class Command(BaseCommand):
    help = 'Erstellt den Besetzungsverfahren-Workflow mit allen Schritten'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Erstelle Besetzungsverfahren-Workflow...'))

        # Workflow-Typ erstellen oder aktualisieren
        workflow_typ, created = WorkflowTyp.objects.get_or_create(
            name='Besetzungsverfahren',
            defaults={
                'beschreibung': '''Workflow für das Besetzungsverfahren einer Notarstelle.

Dieser Workflow führt durch den gesamten Prozess:
1. Bewerbungen empfangen und ablegen
2. Bewerber auswählen (3 aus allen Bewerbungen)
3. Stammblätter der 3 Bewerber vergleichen
4. Strafregisterauszüge anfordern
5. Ausgewählte Bewerber kontaktieren
6. Bewerber zur Kammer-Sitzung einladen
7. Präsentationen vorbereiten
8. Kammer-Sitzung durchführen und Ranking festlegen
9. Ergebnis an alle Bewerber versenden
10. Erstplatzierten zum Notar befördern

Das Verfahren generiert automatisch eine Geschäftszahl (z.B. BES-2025-0001).''',
                'ist_aktiv': True,
                'kuerzel': 'BP',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Workflow-Typ "{workflow_typ.name}" wurde erstellt.'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Workflow-Typ "{workflow_typ.name}" existiert bereits.'))

        # Alle Schritte definieren
        schritte = [
            {
                'reihenfolge': 1,
                'name': 'Bewerbungen empfangen und ablegen',
                'beschreibung': '''Bewerbungen per E-Mail oder im Original empfangen und in den Workflow hochladen.

Aufgaben:
- Bewerbungsunterlagen einscannen (falls Original)
- PDF-Dateien hochladen
- Checkbox abhaken wenn alle Bewerbungen abgelegt sind''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 2,
                'name': 'Bewerber auswählen',
                'beschreibung': '''Aus allen eingegangenen Bewerbungen werden 3 Kandidat für das Verfahren ausgewählt.

Aufgaben:
- Bewerbungen sichten
- 3 geeignete Kandidaten auswählen
- Als "ausgewählt" markieren''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 3,
                'name': 'Stammblätter vergleichen',
                'beschreibung': '''Die 3 ausgewählten Bewerber in der Vergleichsansicht gegenüberstellen.

Aufgaben:
- Vergleichsansicht öffnen (Button)
- Stammblätter prüfen
- Notizen zu jedem Bewerber machen''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 4,
                'name': 'Strafregisterauszüge anfordern',
                'beschreibung': '''Für alle 3 ausgewählten Bewerber Strafregisterauszüge anfordern.

Aufgaben:
- E-Mail-Vorlage "Strafregisterauszug" nutzen
- An alle 3 Bewerber senden
- Eingang der Auszüge prüfen''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 5,
                'name': 'Ausgewählte Bewerber kontaktieren',
                'beschreibung': '''Die 3 ausgewählten Bewerber informieren, dass sie für das Verfahren ausgewählt wurden.

Aufgaben:
- E-Mail-Vorlage "Auswahl Besetzungsverfahren" nutzen
- An alle 3 Bewerber senden''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 6,
                'name': 'Bewerber zur Kammer-Sitzung einladen',
                'beschreibung': '''Einladung mit Termin und Informationen zur Kammer-Sitzung versenden.

Aufgaben:
- Termin für Kammer-Sitzung festlegen
- E-Mail-Vorlage "Einladung Kammer-Sitzung" nutzen
- An alle 3 Bewerber senden''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 7,
                'name': 'Präsentationen vorbereiten',
                'beschreibung': '''Präsentationsunterlagen für die Kammer-Sitzung vorbereiten.

Aufgaben:
- Für jeden der 3 Bewerber Checkbox abhaken wenn Präsentation vorbereitet
- Unterlagen zusammenstellen
- Präsentationsfolien erstellen (optional)''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 8,
                'name': 'Kammer-Sitzung durchführen',
                'beschreibung': '''In der Kammer-Sitzung werden die 3 Bewerber präsentiert und das Ranking festgelegt.

Aufgaben:
- Bewerber vorstellen
- Ranking festlegen (1., 2., 3. Platz)
- Protokoll erstellen''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 9,
                'name': 'Ergebnis an Bewerber versenden',
                'beschreibung': '''Alle Bewerber über das Ergebnis des Verfahrens informieren.

Aufgaben:
- E-Mail an 1. Platz: "Bestellung erfolgt"
- E-Mail an 2./3. Platz und andere: "Absage"
- Weitere Schritte kommunizieren''',
                'ist_optional': False,
            },
            {
                'reihenfolge': 10,
                'name': 'Bestellung durchführen',
                'beschreibung': '''Den Erstplatzierten offiziell zum Notar bestellen.

Aufgaben:
- Notarstelle zuweisen
- Bestellungsdatum festlegen
- Im System: Kandidat → Notar transformieren
- Bestellungsurkunde ausstellen''',
                'ist_optional': False,
            },
        ]

        # Schritte erstellen
        for schritt_data in schritte:
            schritt, created = WorkflowSchritt.objects.update_or_create(
                workflow_typ=workflow_typ,
                reihenfolge=schritt_data['reihenfolge'],
                defaults={
                    'name': schritt_data['name'],
                    'beschreibung': schritt_data['beschreibung'],
                    'ist_optional': schritt_data['ist_optional'],
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Schritt {schritt.reihenfolge}: {schritt.name}'))
            else:
                self.stdout.write(f'  ○ Schritt {schritt.reihenfolge}: {schritt.name} (aktualisiert)')

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Besetzungsverfahren-Workflow mit {len(schritte)} Schritten wurde erstellt!')
        )
