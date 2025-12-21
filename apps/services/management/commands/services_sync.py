"""
Management Command zum Synchronisieren der Services mit der Datenbank.
"""
from django.core.management.base import BaseCommand
from apps.services.registry import service_registry


class Command(BaseCommand):
    help = 'Synchronisiert registrierte Services mit der Datenbank'

    def add_arguments(self, parser):
        """Fügt Command-Line-Argumente hinzu."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Erzwingt Neuimport aller Service-Module'
        )

    def handle(self, *args, **options):
        """Synchronisiert die Services."""

        force = options.get('force', False)

        self.stdout.write('Services werden synchronisiert...\n')

        # Services importieren (damit @service Decorator läuft)
        try:
            import apps.services.services
            self.stdout.write(self.style.SUCCESS('✓ Service-Module importiert'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Fehler beim Importieren der Service-Module: {e}')
            )
            return

        # Registry-Status anzeigen
        anzahl_services = len(service_registry.alle_service_ids())
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ {anzahl_services} Services in Registry gefunden'
            )
        )

        # Service-IDs anzeigen
        if anzahl_services > 0:
            self.stdout.write('\nRegistrierte Services:')
            for service_id in sorted(service_registry.alle_service_ids()):
                self.stdout.write(f'  - {service_id}')

        # Mit Datenbank synchronisieren
        self.stdout.write('\nSynchronisiere mit Datenbank...')

        try:
            statistik = service_registry.sync_mit_datenbank()

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ {statistik["erstellt"]} Services erstellt')
            )
            self.stdout.write(
                self.style.WARNING(f'• {statistik["aktualisiert"]} Services aktualisiert')
            )

            if statistik['deaktiviert'] > 0:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ {statistik["deaktiviert"]} veraltete Services deaktiviert'
                    )
                )

            self.stdout.write(
                self.style.SUCCESS('\nFertig! Services sind synchronisiert.')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Fehler bei Synchronisierung: {e}')
            )
            if options.get('verbosity', 1) >= 2:
                import traceback
                traceback.print_exc()
