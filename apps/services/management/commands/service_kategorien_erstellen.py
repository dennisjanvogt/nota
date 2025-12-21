"""
Management Command zum Erstellen der Service-Kategorien.
"""
from django.core.management.base import BaseCommand
from apps.services.models import ServiceKategorie


class Command(BaseCommand):
    help = 'Erstellt die Standard-Service-Kategorien'

    def handle(self, *args, **options):
        """Erstellt die Service-Kategorien."""

        kategorien = [
            {
                'name': 'dokumente',
                'beschreibung': 'Dokument-Generierung und PDF-Erstellung',
                'icon': 'file-earmark-pdf',
                'reihenfolge': 10
            },
            {
                'name': 'kommunikation',
                'beschreibung': 'E-Mail-Versand und Kommunikation',
                'icon': 'envelope',
                'reihenfolge': 20
            },
            {
                'name': 'verwaltung',
                'beschreibung': 'Verwaltungsakte und kritische Operationen',
                'icon': 'gear',
                'reihenfolge': 30
            },
            {
                'name': 'berichte',
                'beschreibung': 'Berichte und Auswertungen',
                'icon': 'file-earmark-bar-graph',
                'reihenfolge': 40
            },
            {
                'name': 'sonstiges',
                'beschreibung': 'Sonstige Services',
                'icon': 'box',
                'reihenfolge': 999
            },
        ]

        erstellt = 0
        aktualisiert = 0

        for kategorie_data in kategorien:
            kategorie, created = ServiceKategorie.objects.update_or_create(
                name=kategorie_data['name'],
                defaults={
                    'beschreibung': kategorie_data['beschreibung'],
                    'icon': kategorie_data['icon'],
                    'reihenfolge': kategorie_data['reihenfolge']
                }
            )

            if created:
                erstellt += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Kategorie "{kategorie.name}" erstellt')
                )
            else:
                aktualisiert += 1
                self.stdout.write(
                    self.style.WARNING(f'• Kategorie "{kategorie.name}" aktualisiert')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nFertig! {erstellt} erstellt, {aktualisiert} aktualisiert'
            )
        )
