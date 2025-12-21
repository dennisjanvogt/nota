"""
Management Command zum Erstellen von Sprengel-Daten.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.sprengel.models import Sprengel


class Command(BaseCommand):
    help = 'Erstellt initiale Sprengel-Daten basierend auf österreichischen Gerichtsbezirken'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Erstelle Sprengel-Daten...'))

        # Sprengel-Daten basierend auf Gerichtsbezirken
        sprengel_daten = [
            # Wien
            {
                'bezeichnung': 'SPR-000001',
                'name': 'Sprengel Wien Innere Stadt',
                'gerichtsbezirk': 'Bezirksgericht Innere Stadt Wien',
                'bundesland': 'Wien',
                'beschreibung': 'Notarsprengel für den 1. Wiener Gemeindebezirk',
            },
            {
                'bezeichnung': 'SPR-000002',
                'name': 'Sprengel Wien Leopoldstadt',
                'gerichtsbezirk': 'Bezirksgericht Leopoldstadt',
                'bundesland': 'Wien',
                'beschreibung': 'Notarsprengel für den 2. Wiener Gemeindebezirk',
            },
            {
                'bezeichnung': 'SPR-000003',
                'name': 'Sprengel Wien Donaustadt',
                'gerichtsbezirk': 'Bezirksgericht Donaustadt',
                'bundesland': 'Wien',
                'beschreibung': 'Notarsprengel für den 22. Wiener Gemeindebezirk',
            },
            # Niederösterreich
            {
                'bezeichnung': 'SPR-000004',
                'name': 'Sprengel St. Pölten',
                'gerichtsbezirk': 'Bezirksgericht St. Pölten',
                'bundesland': 'Niederösterreich',
                'beschreibung': 'Notarsprengel für den Bezirk St. Pölten',
            },
            {
                'bezeichnung': 'SPR-000005',
                'name': 'Sprengel Wiener Neustadt',
                'gerichtsbezirk': 'Bezirksgericht Wiener Neustadt',
                'bundesland': 'Niederösterreich',
                'beschreibung': 'Notarsprengel für den Bezirk Wiener Neustadt',
            },
            {
                'bezeichnung': 'SPR-000006',
                'name': 'Sprengel Baden',
                'gerichtsbezirk': 'Bezirksgericht Baden',
                'bundesland': 'Niederösterreich',
                'beschreibung': 'Notarsprengel für den Bezirk Baden',
            },
            {
                'bezeichnung': 'SPR-000007',
                'name': 'Sprengel Krems',
                'gerichtsbezirk': 'Bezirksgericht Krems',
                'bundesland': 'Niederösterreich',
                'beschreibung': 'Notarsprengel für den Bezirk Krems an der Donau',
            },
            # Oberösterreich
            {
                'bezeichnung': 'SPR-000008',
                'name': 'Sprengel Linz',
                'gerichtsbezirk': 'Bezirksgericht Linz',
                'bundesland': 'Oberösterreich',
                'beschreibung': 'Notarsprengel für die Stadt Linz',
            },
            {
                'bezeichnung': 'SPR-000009',
                'name': 'Sprengel Wels',
                'gerichtsbezirk': 'Bezirksgericht Wels',
                'bundesland': 'Oberösterreich',
                'beschreibung': 'Notarsprengel für die Stadt Wels',
            },
            {
                'bezeichnung': 'SPR-000010',
                'name': 'Sprengel Steyr',
                'gerichtsbezirk': 'Bezirksgericht Steyr',
                'bundesland': 'Oberösterreich',
                'beschreibung': 'Notarsprengel für die Stadt Steyr',
            },
            # Steiermark
            {
                'bezeichnung': 'SPR-000011',
                'name': 'Sprengel Graz',
                'gerichtsbezirk': 'Bezirksgericht für Zivilrechtssachen Graz',
                'bundesland': 'Steiermark',
                'beschreibung': 'Notarsprengel für die Stadt Graz',
            },
            {
                'bezeichnung': 'SPR-000012',
                'name': 'Sprengel Leoben',
                'gerichtsbezirk': 'Bezirksgericht Leoben',
                'bundesland': 'Steiermark',
                'beschreibung': 'Notarsprengel für den Bezirk Leoben',
            },
            # Kärnten
            {
                'bezeichnung': 'SPR-000013',
                'name': 'Sprengel Klagenfurt',
                'gerichtsbezirk': 'Bezirksgericht Klagenfurt',
                'bundesland': 'Kärnten',
                'beschreibung': 'Notarsprengel für die Stadt Klagenfurt',
            },
            {
                'bezeichnung': 'SPR-000014',
                'name': 'Sprengel Villach',
                'gerichtsbezirk': 'Bezirksgericht Villach',
                'bundesland': 'Kärnten',
                'beschreibung': 'Notarsprengel für die Stadt Villach',
            },
            # Salzburg
            {
                'bezeichnung': 'SPR-000015',
                'name': 'Sprengel Salzburg',
                'gerichtsbezirk': 'Bezirksgericht Salzburg',
                'bundesland': 'Salzburg',
                'beschreibung': 'Notarsprengel für die Stadt Salzburg',
            },
            {
                'bezeichnung': 'SPR-000016',
                'name': 'Sprengel Hallein',
                'gerichtsbezirk': 'Bezirksgericht Hallein',
                'bundesland': 'Salzburg',
                'beschreibung': 'Notarsprengel für den Bezirk Hallein',
            },
            # Tirol
            {
                'bezeichnung': 'SPR-000017',
                'name': 'Sprengel Innsbruck',
                'gerichtsbezirk': 'Bezirksgericht Innsbruck',
                'bundesland': 'Tirol',
                'beschreibung': 'Notarsprengel für die Stadt Innsbruck',
            },
            {
                'bezeichnung': 'SPR-000018',
                'name': 'Sprengel Kufstein',
                'gerichtsbezirk': 'Bezirksgericht Kufstein',
                'bundesland': 'Tirol',
                'beschreibung': 'Notarsprengel für den Bezirk Kufstein',
            },
            {
                'bezeichnung': 'SPR-000019',
                'name': 'Sprengel Schwaz',
                'gerichtsbezirk': 'Bezirksgericht Schwaz',
                'bundesland': 'Tirol',
                'beschreibung': 'Notarsprengel für den Bezirk Schwaz',
            },
            # Vorarlberg
            {
                'bezeichnung': 'SPR-000020',
                'name': 'Sprengel Bregenz',
                'gerichtsbezirk': 'Bezirksgericht Bregenz',
                'bundesland': 'Vorarlberg',
                'beschreibung': 'Notarsprengel für den Bezirk Bregenz',
            },
            {
                'bezeichnung': 'SPR-000021',
                'name': 'Sprengel Feldkirch',
                'gerichtsbezirk': 'Bezirksgericht Feldkirch',
                'bundesland': 'Vorarlberg',
                'beschreibung': 'Notarsprengel für den Bezirk Feldkirch',
            },
            {
                'bezeichnung': 'SPR-000022',
                'name': 'Sprengel Dornbirn',
                'gerichtsbezirk': 'Bezirksgericht Dornbirn',
                'bundesland': 'Vorarlberg',
                'beschreibung': 'Notarsprengel für den Bezirk Dornbirn',
            },
            # Burgenland
            {
                'bezeichnung': 'SPR-000023',
                'name': 'Sprengel Eisenstadt',
                'gerichtsbezirk': 'Bezirksgericht Eisenstadt',
                'bundesland': 'Burgenland',
                'beschreibung': 'Notarsprengel für den Bezirk Eisenstadt',
            },
        ]

        count = 0
        for daten in sprengel_daten:
            sprengel, created = Sprengel.objects.update_or_create(
                bezeichnung=daten['bezeichnung'],
                defaults=daten
            )
            count += 1
            if created:
                self.stdout.write(f'  + {sprengel.name}')
            else:
                self.stdout.write(f'  → {sprengel.name} (aktualisiert)')

        self.stdout.write(self.style.SUCCESS(f'\n✓ {count} Sprengel erstellt/aktualisiert'))
