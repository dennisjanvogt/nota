"""
Management Command zum Anlegen des Bestellungsprozess-Workflows.
"""
from django.core.management.base import BaseCommand
from apps.workflows.models import WorkflowTyp, WorkflowSchritt


class Command(BaseCommand):
    help = 'Legt den Bestellungsprozess-Workflow mit allen Schritten an'

    def handle(self, *args, **options):
        self.stdout.write('Erstelle Bestellungsprozess-Workflow...')

        # Erstelle oder hole Workflow-Typ
        workflow_typ, created = WorkflowTyp.objects.get_or_create(
            name='Bestellungsprozess',
            defaults={
                'beschreibung': (
                    'Workflow für die Bestellung eines Notariatskandidats zum Notar. '
                    'Dieser Prozess umfasst alle notwendigen Schritte von der Antragsprüfung '
                    'bis zur offiziellen Bestellung.'
                ),
                'ist_aktiv': True,
                'kuerzel': 'BES'
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Workflow-Typ "{workflow_typ.name}" wurde erstellt'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ Workflow-Typ "{workflow_typ.name}" existiert bereits'
                )
            )

        # Definiere Schritte
        schritte_definitionen = [
            {
                'reihenfolge': 1,
                'name': 'Antrag prüfen',
                'beschreibung': (
                    'Prüfung der eingereichten Unterlagen und Voraussetzungen für die Bestellung. '
                    'Vollständigkeit der Dokumente und formale Anforderungen müssen erfüllt sein.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 2,
                'name': 'Dokumente nachfordern',
                'beschreibung': (
                    'Falls bei der Prüfung festgestellt wird, dass Dokumente fehlen oder '
                    'unvollständig sind, werden diese beim Antragsteller nachgefordert.'
                ),
                'ist_optional': True
            },
            {
                'reihenfolge': 3,
                'name': 'Notarstelle zuweisen',
                'beschreibung': (
                    'Zuweisung einer freien Notarstelle an den Notariatskandidat. '
                    'Prüfung der Verfügbarkeit und regionalen Zuständigkeit.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 4,
                'name': 'Gutachten einholen',
                'beschreibung': (
                    'Einholung eines Gutachtens über die fachliche und persönliche Eignung '
                    'des Notariatskandidats. Kann vom betreuenden Notar oder der Kammer erstellt werden.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 5,
                'name': 'Präsidium vorlegen',
                'beschreibung': (
                    'Vorlage aller Unterlagen beim Präsidium der Notariatskammer zur Entscheidung. '
                    'Das Präsidium prüft den Fall und entscheidet über die Bestellung.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 6,
                'name': 'Bestellung aussprechen',
                'beschreibung': (
                    'Offizielle Bestellung des Notariatskandidats zum Notar durch das Präsidium. '
                    'Erstellung der Bestellungsurkunde und Benachrichtigung des Notars.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 7,
                'name': 'Notar-Objekt erstellen',
                'beschreibung': (
                    'Anlegen des neuen Notars im System und Aktualisierung des Status '
                    'des ehemaligen Notariatskandidats. Zuweisung der Notarstelle.'
                ),
                'ist_optional': False
            },
            {
                'reihenfolge': 8,
                'name': 'Benachrichtigungen versenden',
                'beschreibung': (
                    'Versand von Benachrichtigungen an alle relevanten Stellen: '
                    'Landesjustizverwaltung, andere Kammern, Register, etc.'
                ),
                'ist_optional': False
            }
        ]

        # Erstelle Schritte
        schritte_erstellt = 0
        schritte_existieren = 0

        for schritt_def in schritte_definitionen:
            schritt, created = WorkflowSchritt.objects.get_or_create(
                workflow_typ=workflow_typ,
                reihenfolge=schritt_def['reihenfolge'],
                defaults={
                    'name': schritt_def['name'],
                    'beschreibung': schritt_def['beschreibung'],
                    'ist_optional': schritt_def['ist_optional']
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Schritt {schritt.reihenfolge}: {schritt.name}'
                    )
                )
                schritte_erstellt += 1
            else:
                self.stdout.write(
                    f'  • Schritt {schritt.reihenfolge}: {schritt.name} (existiert bereits)'
                )
                schritte_existieren += 1

        # Zusammenfassung
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Zusammenfassung:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Workflow-Typ: {workflow_typ.name}')
        self.stdout.write(f'Schritte gesamt: {len(schritte_definitionen)}')
        self.stdout.write(self.style.SUCCESS(f'Schritte erstellt: {schritte_erstellt}'))
        if schritte_existieren > 0:
            self.stdout.write(f'Schritte bereits vorhanden: {schritte_existieren}')
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                '✓ Bestellungsprozess-Workflow wurde erfolgreich eingerichtet!'
            )
        )
