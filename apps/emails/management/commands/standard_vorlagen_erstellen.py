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

        # Vorlage: Auswahl für Besetzungsverfahren
        vorlage3, created3 = EmailVorlage.objects.get_or_create(
            name='Auswahl Besetzungsverfahren',
            defaults={
                'kategorie': 'bestellung',
                'betreff': 'Auswahl für Besetzungsverfahren - Notarstelle',
                'nachricht': '''Sehr geehrte/r {titel} {vorname} {nachname},

wir freuen uns, Ihnen mitteilen zu können, dass Sie für das Besetzungsverfahren der Notarstelle {notarstelle} ausgewählt wurden.

Sie gehören zu den 3 Kandidaten, die in das weitere Verfahren aufgenommen wurden.

In den nächsten Tagen erhalten Sie weitere Informationen zum Ablauf und den nächsten Schritten.

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created3:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage3.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage3.name}" existiert bereits.')
            )

        # Vorlage: Einladung Kammer-Sitzung
        vorlage4, created4 = EmailVorlage.objects.get_or_create(
            name='Einladung Kammer-Sitzung',
            defaults={
                'kategorie': 'bestellung',
                'betreff': 'Einladung zur Kammer-Sitzung - Besetzungsverfahren',
                'nachricht': '''Sehr geehrte/r {titel} {vorname} {nachname},

hiermit laden wir Sie zur Kammer-Sitzung ein, in der über die Besetzung der Notarstelle {notarstelle} entschieden wird.

Termin: [Bitte Termin eintragen]
Ort: [Bitte Ort eintragen]

Sie werden gebeten, sich und Ihre Motivation für die Position vorzustellen.

Bitte bestätigen Sie Ihre Teilnahme bis [Datum].

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created4:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage4.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage4.name}" existiert bereits.')
            )

        # Vorlage: Zusage Bestellung (1. Platz)
        vorlage5, created5 = EmailVorlage.objects.get_or_create(
            name='Zusage Bestellung',
            defaults={
                'kategorie': 'bestellung',
                'betreff': 'Bestellung zum Notar - {titel} {vorname} {nachname}',
                'nachricht': '''Sehr geehrte/r {titel} {vorname} {nachname},

wir freuen uns, Ihnen mitteilen zu können, dass Sie im Besetzungsverfahren ausgewählt wurden.

Sie werden zum Notar für die Notarstelle {notarstelle} bestellt.

Die formelle Bestellung erfolgt in den nächsten Tagen. Sie werden rechtzeitig über alle weiteren Schritte informiert.

Wir gratulieren Ihnen herzlich zu dieser Position und freuen uns auf die Zusammenarbeit.

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created5:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage5.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage5.name}" existiert bereits.')
            )

        # Vorlage: Absage Besetzungsverfahren
        vorlage6, created6 = EmailVorlage.objects.get_or_create(
            name='Absage Besetzungsverfahren',
            defaults={
                'kategorie': 'bestellung',
                'betreff': 'Ergebnis Besetzungsverfahren',
                'nachricht': '''Sehr geehrte/r {titel} {vorname} {nachname},

vielen Dank für Ihre Teilnahme am Besetzungsverfahren für die Notarstelle {notarstelle}.

Nach sorgfältiger Prüfung aller Kandidaten müssen wir Ihnen leider mitteilen, dass die Entscheidung zugunsten eines anderen Bewerbers gefallen ist.

Wir bedanken uns für Ihr Interesse und Ihre Bewerbung. Wir wünschen Ihnen für Ihre berufliche Zukunft alles Gute.

Mit freundlichen Grüßen
Notariatskammer''',
                'standard_empfaenger': 'd.vogt@sk-advisory.com',
                'cc_empfaenger': '',
                'ist_aktiv': True,
            }
        )

        if created6:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Vorlage "{vorlage6.name}" wurde erstellt.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'○ Vorlage "{vorlage6.name}" existiert bereits.')
            )

        self.stdout.write(
            self.style.SUCCESS('\n✓ Alle Standard-Vorlagen wurden erfolgreich erstellt!')
        )
