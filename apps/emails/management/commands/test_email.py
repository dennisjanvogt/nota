"""
Management Command zum Testen der E-Mail-Konfiguration.
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


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
            send_mail(
                subject='Test-E-Mail - Notariatskammer Verwaltungssystem',
                message='Dies ist eine Test-E-Mail vom Notariatskammer Verwaltungssystem.\n\n'
                        'Wenn Sie diese E-Mail erhalten, funktioniert die E-Mail-Konfiguration korrekt.\n\n'
                        f'Server: {settings.EMAIL_HOST}\n'
                        f'Port: {settings.EMAIL_PORT}\n'
                        f'Von: {settings.DEFAULT_FROM_EMAIL}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[empfaenger],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Test-E-Mail wurde erfolgreich an {empfaenger} gesendet!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Fehler beim Senden der E-Mail: {str(e)}')
            )
