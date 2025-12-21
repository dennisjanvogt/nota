"""
Management Command zur Migration der IDs auf das neue Format.

NOT-001 → NOT-000001
ANW-001 → NKA-000001
NOT-1   → NST-000001

WICHTIG: Vor Ausführung Datenbank-Backup erstellen!
"""
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.personen.models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle


class Command(BaseCommand):
    help = 'Migriert IDs auf neues Format: NOT-000001, NKA-000001, NST-000001'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeigt Änderungen an ohne sie zu speichern',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN Modus - keine Änderungen werden gespeichert'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  ACHTUNG: Dies ändert alle IDs in der Datenbank!'))
            confirm = input('Fortfahren? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Abgebrochen.'))
                return

        try:
            with transaction.atomic():
                # Schritt 1: Notare migrieren
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write('SCHRITT 1: Notare migrieren')
                self.stdout.write('=' * 60)
                self.migrate_notare(dry_run)

                # Schritt 2: Kandidaten migrieren
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write('SCHRITT 2: Notariatskandidaten migrieren')
                self.stdout.write('=' * 60)
                self.migrate_kandidaten(dry_run)

                # Schritt 3: Notarstellen migrieren
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write('SCHRITT 3: Notarstellen migrieren')
                self.stdout.write('=' * 60)
                self.migrate_notarstellen(dry_run)

                if dry_run:
                    raise Exception("DRY RUN - Rollback")

            self.stdout.write(self.style.SUCCESS('\n✅ Migration erfolgreich abgeschlossen!'))

        except Exception as e:
            if str(e) == "DRY RUN - Rollback":
                self.stdout.write(self.style.SUCCESS('\n✅ DRY RUN abgeschlossen - keine Änderungen gespeichert'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Fehler: {e}'))
                self.stdout.write(self.style.ERROR('Migration wurde rückgängig gemacht (rollback)'))

    def extract_nummer(self, old_id):
        """Extrahiert Nummer aus alten IDs."""
        match = re.search(r'(\d+)', old_id)
        return int(match.group(1)) if match else 0

    def migrate_notare(self, dry_run=False):
        """Migriert Notar-IDs: NOT-001 → NOT-000001"""
        notare = Notar.objects.all()
        total = notare.count()
        self.stdout.write(f'Gefunden: {total} Notare')

        migrated = 0
        for notar in notare:
            old_id = notar.notar_id
            nummer = self.extract_nummer(old_id)
            new_id = f"NOT-{nummer:06d}"

            if old_id != new_id:
                self.stdout.write(f'  {old_id} → {new_id} ({notar.get_voller_name()})')
                if not dry_run:
                    notar.notar_id = new_id
                    notar.save()
                migrated += 1
            else:
                self.stdout.write(self.style.WARNING(f'  {old_id} (bereits im neuen Format)'))

        self.stdout.write(self.style.SUCCESS(f'✓ {migrated} Notare migriert'))

    def migrate_kandidaten(self, dry_run=False):
        """Migriert Kandidaten-IDs: ANW-001 → NKA-000001"""
        kandidaten = NotarAnwaerter.objects.all()
        total = kandidaten.count()
        self.stdout.write(f'Gefunden: {total} Notariatskandidaten')

        migrated = 0
        for kandidat in kandidaten:
            old_id = kandidat.anwaerter_id
            nummer = self.extract_nummer(old_id)
            new_id = f"NKA-{nummer:06d}"

            if old_id != new_id:
                self.stdout.write(f'  {old_id} → {new_id} ({kandidat.get_voller_name()})')
                if not dry_run:
                    kandidat.anwaerter_id = new_id
                    kandidat.save()
                migrated += 1
            else:
                self.stdout.write(self.style.WARNING(f'  {old_id} (bereits im neuen Format)'))

        self.stdout.write(self.style.SUCCESS(f'✓ {migrated} Kandidaten migriert'))

    def migrate_notarstellen(self, dry_run=False):
        """Migriert Notarstellen-Bezeichnungen: NOT-1 → NST-000001"""
        notarstellen = Notarstelle.objects.all()
        total = notarstellen.count()
        self.stdout.write(f'Gefunden: {total} Notarstellen')

        migrated = 0
        for stelle in notarstellen:
            old_bez = stelle.bezeichnung
            nummer = self.extract_nummer(old_bez)
            new_bez = f"NST-{nummer:06d}"

            if old_bez != new_bez:
                self.stdout.write(f'  {old_bez} → {new_bez} ({stelle.name})')
                if not dry_run:
                    # Nur bezeichnung updaten (notarnummer-Feld existiert noch in DB, aber nicht mehr im Model)
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE notarstellen_notarstelle SET bezeichnung = %s WHERE bezeichnung = %s",
                            [new_bez, old_bez]
                        )
                migrated += 1
            else:
                self.stdout.write(self.style.WARNING(f'  {old_bez} (bereits im neuen Format)'))

        self.stdout.write(self.style.SUCCESS(f'✓ {migrated} Notarstellen migriert'))
