"""
Models für E-Mail-Vorlagen und -Versand.
"""
from django.db import models
from django.conf import settings


class EmailVorlage(models.Model):
    """
    E-Mail-Vorlage für Standard-E-Mails.
    """
    KATEGORIE_CHOICES = [
        ('strafregister', 'Strafregisterauszug'),
        ('bestellung', 'Bestellungsverfahren'),
        ('zulassung', 'Zulassungsverfahren'),
        ('aufsicht', 'Aufsichtsangelegenheiten'),
        ('allgemein', 'Allgemein'),
        ('sonstiges', 'Sonstiges'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='Name der Vorlage',
        help_text='z.B. "Anfrage Strafregisterauszug"'
    )
    kategorie = models.CharField(
        max_length=50,
        choices=KATEGORIE_CHOICES,
        default='allgemein',
        verbose_name='Kategorie'
    )
    betreff = models.CharField(
        max_length=200,
        verbose_name='E-Mail-Betreff'
    )
    nachricht = models.TextField(
        verbose_name='E-Mail-Text',
        help_text='Platzhalter: {vorname}, {nachname}, {titel}, {notar_id}, {anwaerter_id}, {notarstelle}'
    )
    standard_empfaenger = models.EmailField(
        verbose_name='Standard-Empfänger',
        help_text='Standard-E-Mail-Adresse, an die diese Vorlage gesendet wird'
    )
    cc_empfaenger = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='CC-Empfänger',
        help_text='Mehrere E-Mail-Adressen mit Komma trennen'
    )
    ist_aktiv = models.BooleanField(
        default=True,
        verbose_name='Aktiv'
    )
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'E-Mail-Vorlage'
        verbose_name_plural = 'E-Mail-Vorlagen'
        ordering = ['kategorie', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_kategorie_display()})"


class GesendeteEmail(models.Model):
    """
    Protokoll gesendeter E-Mails.
    """
    vorlage = models.ForeignKey(
        EmailVorlage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Verwendete Vorlage'
    )
    gesendet_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Gesendet von'
    )
    empfaenger = models.EmailField(verbose_name='Empfänger')
    cc_empfaenger = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='CC-Empfänger'
    )
    betreff = models.CharField(max_length=200, verbose_name='Betreff')
    nachricht = models.TextField(verbose_name='Nachricht')

    # Verlinkung zu Notar oder Anwärter
    notar = models.ForeignKey(
        'personen.Notar',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gesendete_emails',
        verbose_name='Notar'
    )
    anwaerter = models.ForeignKey(
        'personen.NotarAnwaerter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gesendete_emails',
        verbose_name='Anwärter'
    )

    erfolgreich = models.BooleanField(
        default=True,
        verbose_name='Erfolgreich gesendet'
    )
    fehler = models.TextField(
        blank=True,
        verbose_name='Fehlermeldung'
    )
    gesendet_am = models.DateTimeField(auto_now_add=True, verbose_name='Gesendet am')

    class Meta:
        verbose_name = 'Gesendete E-Mail'
        verbose_name_plural = 'Gesendete E-Mails'
        ordering = ['-gesendet_am']

    def __str__(self):
        return f"{self.betreff} → {self.empfaenger} ({self.gesendet_am.strftime('%d.%m.%Y %H:%M')})"
