"""
Management Command zum Importieren von echten österreichischen Notaren aus CSV-Dateien.
"""
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.personen.models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle
from datetime import datetime


class Command(BaseCommand):
    help = 'Importiert echte österreichische Notare, Kandidat und Notarstellen aus CSV-Dateien'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-dummy',
            action='store_true',
            help='Löscht alle bestehenden Dummy-Daten vor dem Import',
        )
        parser.add_argument(
            '--notarstellen',
            type=str,
            help='Pfad zur CSV-Datei mit Notarstellen',
        )
        parser.add_argument(
            '--notare',
            type=str,
            help='Pfad zur CSV-Datei mit Notaren',
        )
        parser.add_argument(
            '--anwaerter',
            type=str,
            help='Pfad zur CSV-Datei mit Notariatskandidatn',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear_dummy']:
            self.stdout.write(self.style.WARNING('Lösche bestehende Dummy-Daten...'))
            NotarAnwaerter.objects.all().delete()
            Notar.objects.all().delete()
            Notarstelle.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Dummy-Daten gelöscht'))

        # Import Notarstellen
        if options['notarstellen']:
            self.import_notarstellen(options['notarstellen'])

        # Import Notare
        if options['notare']:
            self.import_notare(options['notare'])

        # Import Kandidat
        if options['anwaerter']:
            self.import_anwaerter(options['anwaerter'])

        self.stdout.write(self.style.SUCCESS('\n✓ Import erfolgreich abgeschlossen!'))

    def import_notarstellen(self, csv_path):
        self.stdout.write(f'\nImportiere Notarstellen aus {csv_path}...')
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                notarstelle, created = Notarstelle.objects.update_or_create(
                    bezeichnung=row['bezeichnung'],
                    defaults={
                        'name': row['name'],
                        'strasse': row['strasse'],
                        'plz': row['plz'],
                        'stadt': row['stadt'],
                        'bundesland': row['bundesland'],
                        'telefon': row.get('telefon', ''),
                        'email': row.get('email', ''),
                        'ist_aktiv': row.get('ist_aktiv', 'True').lower() == 'true',
                    }
                )
                count += 1
                if created:
                    self.stdout.write(f'  + {notarstelle.name}')
                else:
                    self.stdout.write(f'  → {notarstelle.name} (aktualisiert)')

        self.stdout.write(self.style.SUCCESS(f'✓ {count} Notarstellen importiert'))

    def import_notare(self, csv_path):
        self.stdout.write(f'\nImportiere Notare aus {csv_path}...')
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Notarstelle finden
                try:
                    notarstelle = Notarstelle.objects.get(bezeichnung=row['notarstelle'])
                except Notarstelle.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ! Notarstelle {row["notarstelle"]} nicht gefunden für {row["vorname"]} {row["nachname"]}'
                        )
                    )
                    continue

                notar, created = Notar.objects.update_or_create(
                    notar_id=row['notar_id'],
                    defaults={
                        'vorname': row['vorname'],
                        'nachname': row['nachname'],
                        'titel': row.get('titel', ''),
                        'email': row['email'],
                        'telefon': row.get('telefon', ''),
                        'notarstelle': notarstelle,
                        'bestellt_am': datetime.strptime(row['bestellt_am'], '%Y-%m-%d').date(),
                        'beginn_datum': datetime.strptime(row['beginn_datum'], '%Y-%m-%d').date(),
                        'ende_datum': datetime.strptime(row['ende_datum'], '%Y-%m-%d').date() if row.get('ende_datum') else None,
                        'war_vorher_anwaerter': row.get('war_vorher_anwaerter', 'False').lower() == 'true',
                        'ist_aktiv': row.get('ist_aktiv', 'True').lower() == 'true',
                    }
                )
                count += 1
                if created:
                    self.stdout.write(f'  + {notar.titel} {notar.vorname} {notar.nachname}')
                else:
                    self.stdout.write(f'  → {notar.titel} {notar.vorname} {notar.nachname} (aktualisiert)')

        self.stdout.write(self.style.SUCCESS(f'✓ {count} Notare importiert'))

    def import_anwaerter(self, csv_path):
        self.stdout.write(f'\nImportiere Notariatskandidat aus {csv_path}...')
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Notarstelle finden
                try:
                    notarstelle = Notarstelle.objects.get(bezeichnung=row['notarstelle'])
                except Notarstelle.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ! Notarstelle {row["notarstelle"]} nicht gefunden für {row["vorname"]} {row["nachname"]}'
                        )
                    )
                    continue

                # Betreuender Notar (optional)
                betreuender_notar = None
                if row.get('betreuender_notar'):
                    try:
                        betreuender_notar = Notar.objects.get(notar_id=row['betreuender_notar'])
                    except Notar.DoesNotExist:
                        pass

                anwaerter, created = NotarAnwaerter.objects.update_or_create(
                    anwaerter_id=row['anwaerter_id'],
                    defaults={
                        'vorname': row['vorname'],
                        'nachname': row['nachname'],
                        'titel': row.get('titel', ''),
                        'email': row['email'],
                        'telefon': row.get('telefon', ''),
                        'notarstelle': notarstelle,
                        'betreuender_notar': betreuender_notar,
                        'zugelassen_am': datetime.strptime(row['zugelassen_am'], '%Y-%m-%d').date(),
                        'beginn_datum': datetime.strptime(row['beginn_datum'], '%Y-%m-%d').date(),
                        'geplante_bestellung': datetime.strptime(row['geplante_bestellung'], '%Y-%m-%d').date() if row.get('geplante_bestellung') else None,
                        'ist_aktiv': row.get('ist_aktiv', 'True').lower() == 'true',
                    }
                )
                count += 1
                if created:
                    self.stdout.write(f'  + {anwaerter.titel} {anwaerter.vorname} {anwaerter.nachname}')
                else:
                    self.stdout.write(f'  → {anwaerter.titel} {anwaerter.vorname} {anwaerter.nachname} (aktualisiert)')

        self.stdout.write(self.style.SUCCESS(f'✓ {count} Notariatskandidat importiert'))
