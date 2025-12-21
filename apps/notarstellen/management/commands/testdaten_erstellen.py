"""
Management Command zum Erstellen von Testdaten.

Usage: python manage.py testdaten_erstellen
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.notarstellen.models import Notarstelle
from apps.personen.models import Notar, NotarAnwaerter


class Command(BaseCommand):
    help = 'Erstellt Testdaten für Notarstellen, Notare und Notariatskandidat'

    def handle(self, *args, **options):
        self.stdout.write('Erstelle Testdaten...\n')

        # Notarstellen erstellen
        self.stdout.write('Erstelle Notarstellen...')
        notarstelle1 = Notarstelle.objects.create(
            notarnummer='1',
            bezeichnung='NOT-HH-1',
            name='Notariat Hamburg I',
            strasse='Jungfernstieg 42',
            plz='20354',
            stadt='Hamburg',
            bundesland='Hamburg',
            telefon='040-123456',
            email='notariat1@hamburg.de',
            besetzt_seit=date(2020, 1, 1)
        )

        notarstelle2 = Notarstelle.objects.create(
            notarnummer='2',
            bezeichnung='NOT-HH-2',
            name='Notariat Hamburg II',
            strasse='Mönckebergstraße 12',
            plz='20095',
            stadt='Hamburg',
            bundesland='Hamburg',
            telefon='040-234567',
            email='notariat2@hamburg.de',
            besetzt_seit=date(2019, 6, 1)
        )

        notarstelle3 = Notarstelle.objects.create(
            notarnummer='3',
            bezeichnung='NOT-HH-3',
            name='Notariat Hamburg III',
            strasse='Rothenbaumchaussee 78',
            plz='20148',
            stadt='Hamburg',
            bundesland='Hamburg',
            telefon='040-345678',
            email='notariat3@hamburg.de',
            besetzt_seit=date(2021, 3, 15)
        )

        self.stdout.write(self.style.SUCCESS(f'✓ {Notarstelle.objects.count()} Notarstellen erstellt'))

        # Notare erstellen
        self.stdout.write('Erstelle Notare...')
        notar1 = Notar.objects.create(
            notar_id='NOT-001',
            vorname='Max',
            nachname='Mustermann',
            titel='Dr.',
            email='max.mustermann@notariat-hh.de',
            telefon='040-123456-10',
            notarstelle=notarstelle1,
            bestellt_am=date(2020, 1, 15),
            beginn_datum=date(2020, 1, 15),
            war_vorher_anwaerter=True,
            notiz='Erfahrener Notar, spezialisiert auf Immobilienrecht'
        )

        notar2 = Notar.objects.create(
            notar_id='NOT-002',
            vorname='Anna',
            nachname='Schmidt',
            email='anna.schmidt@notariat-hh.de',
            telefon='040-234567-10',
            notarstelle=notarstelle2,
            bestellt_am=date(2019, 8, 1),
            beginn_datum=date(2019, 8, 1),
            war_vorher_anwaerter=False,
            notiz='Schwerpunkt Unternehmensrecht und Handelsregister'
        )

        notar3 = Notar.objects.create(
            notar_id='NOT-003',
            vorname='Thomas',
            nachname='Müller',
            titel='Prof. Dr.',
            email='thomas.mueller@notariat-hh.de',
            telefon='040-345678-10',
            notarstelle=notarstelle3,
            bestellt_am=date(2021, 4, 1),
            beginn_datum=date(2021, 4, 1),
            war_vorher_anwaerter=True,
            notiz='Zusätzlich Lehrauftrag an der Universität Hamburg'
        )

        self.stdout.write(self.style.SUCCESS(f'✓ {Notar.objects.count()} Notare erstellt'))

        # Notariatskandidat erstellen
        self.stdout.write('Erstelle Notariatskandidat...')
        anwaerter1 = NotarAnwaerter.objects.create(
            anwaerter_id='ANW-001',
            vorname='Lisa',
            nachname='Weber',
            email='lisa.weber@notariat-hh.de',
            telefon='040-123456-20',
            betreuender_notar=notar1,
            notarstelle=notarstelle1,
            zugelassen_am=date(2022, 10, 1),
            beginn_datum=date(2022, 10, 1),
            geplante_bestellung=date(2025, 10, 1),
            notiz='Sehr engagiert, gute Fortschritte'
        )

        anwaerter2 = NotarAnwaerter.objects.create(
            anwaerter_id='ANW-002',
            vorname='Michael',
            nachname='Becker',
            email='michael.becker@notariat-hh.de',
            telefon='040-234567-20',
            betreuender_notar=notar2,
            notarstelle=notarstelle2,
            zugelassen_am=date(2023, 4, 1),
            beginn_datum=date(2023, 4, 1),
            geplante_bestellung=date(2026, 4, 1),
            notiz='Schwerpunkt Erbrecht'
        )

        anwaerter3 = NotarAnwaerter.objects.create(
            anwaerter_id='ANW-003',
            vorname='Sarah',
            nachname='Fischer',
            titel='Dr.',
            email='sarah.fischer@notariat-hh.de',
            telefon='040-345678-20',
            betreuender_notar=notar3,
            notarstelle=notarstelle3,
            zugelassen_am=date(2024, 1, 1),
            beginn_datum=date(2024, 1, 1),
            geplante_bestellung=date(2027, 1, 1),
            notiz='Promotion im Gesellschaftsrecht'
        )

        self.stdout.write(self.style.SUCCESS(f'✓ {NotarAnwaerter.objects.count()} Notariatskandidat erstellt'))

        self.stdout.write(self.style.SUCCESS('\n✓ Testdaten erfolgreich erstellt!'))
        self.stdout.write('\nZusammenfassung:')
        self.stdout.write(f'  - {Notarstelle.objects.count()} Notarstellen')
        self.stdout.write(f'  - {Notar.objects.count()} Notare')
        self.stdout.write(f'  - {NotarAnwaerter.objects.count()} Notariatskandidat')
        self.stdout.write('\nSie können sich jetzt im Admin einloggen: http://localhost:8000/admin/')
        self.stdout.write('Benutzername: admin | Passwort: admin\n')
