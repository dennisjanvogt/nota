"""
Kern-Models: Gemeinsame Basis-Funktionalität für alle Models.

Diese abstrakten Models werden von anderen Models vererbt und bieten
gemeinsame Felder und Funktionalität.
"""
from django.db import models


class ZeitstempelModel(models.Model):
    """
    Abstract Base Model mit Zeitstempeln.

    Fügt automatisch Felder für Erstellungs- und Aktualisierungszeitpunkt hinzu.
    """
    erstellt_am = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Erstellt am'
    )
    aktualisiert_am = models.DateTimeField(
        auto_now=True,
        verbose_name='Aktualisiert am'
    )

    class Meta:
        abstract = True


class AktivModel(models.Model):
    """
    Abstract Base Model mit Aktiv/Inaktiv Status.

    Ermöglicht das Deaktivieren von Datensätzen ohne Löschen.
    """
    ist_aktiv = models.BooleanField(
        default=True,
        verbose_name='Ist aktiv',
        help_text='Deaktivierte Einträge bleiben erhalten, werden aber nicht mehr verwendet'
    )

    class Meta:
        abstract = True

    def aktivieren(self):
        """Aktiviert den Datensatz."""
        self.ist_aktiv = True
        self.save()

    def deaktivieren(self):
        """Deaktiviert den Datensatz."""
        self.ist_aktiv = False
        self.save()
