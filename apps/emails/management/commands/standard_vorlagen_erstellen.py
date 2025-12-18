"""
Management Command zum Erstellen von Standard-E-Mail-Vorlagen.
"""
from django.core.management.base import BaseCommand
from apps.emails.models import EmailVorlage


class Command(BaseCommand):
    help = 'Erstellt Standard-E-Mail-Vorlagen'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Erstelle Standard-E-Mail-Vorlagen...'))

        # Vorlage: Strafregisterauszug Anforderung
        vorlage, created = EmailVorlage.objects.get_or_create(
            name='Strafregisterauszug Anforderung',
            defaults={
                'kategorie': 'zulassung',
                'betreff': 'Anforderung Strafregisterauszug - {titel} {vorname} {nachname}',
                'nachricht': '''Sehr geehrte Damen und Herren,

im Rahmen des Zulassungsverfahrens für die Position als Notar/Notar-Anwärter benötigen wir für folgende Person einen aktuellen Strafregisterauszug:

Name: {titel} {vorname} {nachname}
E-Mail: {email}
Telefon: {telefon}
Notarstelle: {notarstelle}

Bitte senden Sie den Strafregisterauszug an die Notariatskammer.

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage.name}" existiert bereits.')
            )

        # Weitere Standard-Vorlagen können hier hinzugefügt werden
        # Vorlage: Bestellungsurkunde
        vorlage2, created2 = EmailVorlage.objects.get_or_create(
            name='Bestellungsurkunde Übermittlung',
            defaults={
                'kategorie': 'bestellung',
                'betreff': 'Bestellungsurkunde - {titel} {vorname} {nachname}',
                'nachricht': '''Sehr geehrte Damen und Herren,

anbei erhalten Sie die Bestellungsurkunde für:

Name: {titel} {vorname} {nachname}
Notarstelle: {notarstelle}
E-Mail: {email}
Telefon: {telefon}

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created2:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage2.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage2.name}" existiert bereits.')
            )

        self.stdout.write(
            self.style.SUCCESS('\n✓ Standard-Vorlagen wurden erfolgreich erstellt!')
        )
