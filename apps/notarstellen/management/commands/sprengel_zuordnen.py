"""
Management Command zum automatischen Zuordnen von Sprengeln zu Notarstellen.

Ordnet Notarstellen basierend auf ihrer Stadt einem passenden Sprengel zu.
"""
from django.core.management.base import BaseCommand
from apps.notarstellen.models import Notarstelle
from apps.sprengel.models import Sprengel


class Command(BaseCommand):
    help = 'Ordnet Notarstellen automatisch Sprengeln zu basierend auf Stadt/Gerichtsbezirk'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starte Sprengel-Zuordnung...'))

        # Mapping von Stadt zu Sprengel (basierend auf Gerichtsbezirk)
        stadt_mapping = {
            # Wien - verteilen auf verschiedene Sprengel
            'Wien': 'SPR-000001',  # Wien Innere Stadt als Standard
            # Niederösterreich
            'St. Pölten': 'SPR-000004',
            'Wiener Neustadt': 'SPR-000005',
            'Baden': 'SPR-000006',
            'Krems': 'SPR-000007',
            'Amstetten': 'SPR-000004',  # → St. Pölten
            # Oberösterreich
            'Linz': 'SPR-000008',
            'Wels': 'SPR-000009',
            'Steyr': 'SPR-000010',
            'Traun': 'SPR-000008',  # → Linz
            # Steiermark
            'Graz': 'SPR-000011',
            'Leoben': 'SPR-000012',
            'Kapfenberg': 'SPR-000012',  # → Leoben
            # Kärnten
            'Klagenfurt': 'SPR-000013',
            'Villach': 'SPR-000014',
            'Wolfsberg': 'SPR-000013',  # → Klagenfurt
            'Spittal an der Drau': 'SPR-000014',  # → Villach
            # Salzburg
            'Salzburg': 'SPR-000015',
            'Hallein': 'SPR-000016',
            # Tirol
            'Innsbruck': 'SPR-000017',
            'Kufstein': 'SPR-000018',
            'Schwaz': 'SPR-000019',
            # Vorarlberg
            'Bregenz': 'SPR-000020',
            'Feldkirch': 'SPR-000021',
            'Dornbirn': 'SPR-000022',
            # Burgenland
            'Eisenstadt': 'SPR-000023',
        }

        notarstellen = Notarstelle.objects.all()
        zugeordnet = 0
        nicht_zugeordnet = 0

        for stelle in notarstellen:
            # Wenn bereits Sprengel zugeordnet, überspringen
            if stelle.sprengel:
                self.stdout.write(
                    f'  {stelle.bezeichnung} hat bereits Sprengel: {stelle.sprengel.bezeichnung}'
                )
                continue

            # Finde passenden Sprengel basierend auf Stadt
            sprengel_id = stadt_mapping.get(stelle.stadt)

            if sprengel_id:
                try:
                    sprengel = Sprengel.objects.get(bezeichnung=sprengel_id)
                    stelle.sprengel = sprengel
                    stelle.save()
                    zugeordnet += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {stelle.bezeichnung} ({stelle.stadt}) → {sprengel.name}'
                        )
                    )
                except Sprengel.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Sprengel {sprengel_id} nicht gefunden für {stelle.bezeichnung}'
                        )
                    )
                    nicht_zugeordnet += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Kein Sprengel-Mapping für Stadt "{stelle.stadt}" ({stelle.bezeichnung})'
                    )
                )
                nicht_zugeordnet += 1

        self.stdout.write(self.style.SUCCESS('\n=== Zusammenfassung ==='))
        self.stdout.write(f'Zugeordnet: {zugeordnet}')
        self.stdout.write(f'Nicht zugeordnet: {nicht_zugeordnet}')
        self.stdout.write(self.style.SUCCESS('\nSprengel-Zuordnung abgeschlossen!'))
