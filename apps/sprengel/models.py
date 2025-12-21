"""
Models für Sprengel-Verwaltung.
"""
from django.db import models
from apps.kern.models import ZeitstempelModel, AktivModel


class Sprengel(ZeitstempelModel, AktivModel):
    """
    Notarsprengel / Amtssprengel - gerichtlicher Zuständigkeitsbereich.

    Ein Sprengel definiert den gerichtlichen Zuständigkeitsbereich für Notarstellen,
    basierend auf Gerichtsbezirken (Bezirksgerichte).
    """

    bezeichnung = models.CharField(
        max_length=50,
        unique=True,
        primary_key=True,
        verbose_name='Bezeichnung',
        help_text='Format: SPR-000001'
    )

    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='z.B. "Sprengel Wien Innere Stadt"'
    )

    gerichtsbezirk = models.CharField(
        max_length=200,
        verbose_name='Gerichtsbezirk',
        help_text='Zugehöriger Gerichtsbezirk'
    )

    bundesland = models.CharField(
        max_length=100,
        verbose_name='Bundesland',
        choices=[
            ('Wien', 'Wien'),
            ('Niederösterreich', 'Niederösterreich'),
            ('Oberösterreich', 'Oberösterreich'),
            ('Steiermark', 'Steiermark'),
            ('Kärnten', 'Kärnten'),
            ('Salzburg', 'Salzburg'),
            ('Tirol', 'Tirol'),
            ('Vorarlberg', 'Vorarlberg'),
            ('Burgenland', 'Burgenland'),
        ]
    )

    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung',
        help_text='Zusätzliche Informationen zum Sprengel'
    )

    class Meta:
        verbose_name = 'Sprengel'
        verbose_name_plural = 'Sprengel'
        ordering = ['bezeichnung']
        indexes = [
            models.Index(fields=['bundesland']),
            models.Index(fields=['ist_aktiv']),
        ]

    def __str__(self):
        return f"{self.name} ({self.gerichtsbezirk})"

    @classmethod
    def generate_next_id(cls):
        """Generiert die nächste Sprengel-ID im Format: SPR-000001"""
        import re

        last = cls.objects.filter(
            bezeichnung__startswith='SPR-'
        ).order_by('-bezeichnung').first()

        if last:
            match = re.search(r'-(\d+)$', last.bezeichnung)
            nummer = int(match.group(1)) + 1 if match else 1
        else:
            nummer = 1

        return f"SPR-{nummer:06d}"

    @property
    def anzahl_notarstellen(self):
        """Anzahl der Notarstellen in diesem Sprengel."""
        return self.notarstellen.count()

    @property
    def anzahl_aktive_notarstellen(self):
        """Anzahl der aktiven Notarstellen in diesem Sprengel."""
        return self.notarstellen.filter(ist_aktiv=True).count()
