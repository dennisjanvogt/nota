"""
Management Command zum Testen der E-Mail-Konfiguration.
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.emails.services import EmailService
from apps.benutzer.models import KammerBenutzer


class Command(BaseCommand):
    help = 'Sendet eine Test-E-Mail zum Überprüfen der E-Mail-Konfiguration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='d.vogt@sk-advisory.com',
            help='Empfänger-E-Mail-Adresse'
        )

    def handle(self, *args, **options):
        empfaenger = options['to']

        self.stdout.write(self.style.WARNING(f'Sende Test-E-Mail an {empfaenger}...'))

        try:
            # Ersten verfügbaren User als Benutzer verwenden
            benutzer = KammerBenutzer.objects.first()

            if not benutzer:
                raise CommandError('Kein Benutzer gefunden. Bitte zuerst einen Benutzer anlegen.')

            # E-Mail mit HTML-Template versenden
            EmailService.email_einfach_senden(
                empfaenger=empfaenger,
                betreff='Test-E-Mail - Notariatskammer Verwaltungssystem',
                nachricht=(
                    'Dies ist eine Test-E-Mail vom Notariatskammer Verwaltungssystem.\n\n'
                    'Wenn Sie diese E-Mail erhalten, funktioniert die E-Mail-Konfiguration korrekt.\n\n'
                    f'Server: {settings.EMAIL_HOST}\n'
                    f'Port: {settings.EMAIL_PORT}\n'
                    f'Von: {settings.DEFAULT_FROM_EMAIL}\n\n'
                    '✅ Das E-Mail-Template mit Header/Logo wird korrekt verwendet.'
                ),
                benutzer=benutzer,
                service_ausfuehrung=None
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Test-E-Mail wurde erfolgreich an {empfaenger} gesendet!')
            )
            self.stdout.write(
                self.style.SUCCESS('✓ E-Mail enthält HTML-Template mit Header und Logo')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Fehler beim Senden der E-Mail: {str(e)}')
            )
