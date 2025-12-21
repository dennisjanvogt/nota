"""
Models für Notarstellen-Verwaltung.

Notarstellen sind die Notariate, die von der Kammer verwaltet werden.
"""
from django.db import models
from apps.kern.models import ZeitstempelModel, AktivModel


class Notarstelle(ZeitstempelModel, AktivModel):
    """
    Notarstelle/Notariat.

    Eine Notarstelle ist ein Notariat, das von der Notariatskammer verwaltet wird.
    """
    bezeichnung = models.CharField(
        max_length=50,
        primary_key=True,
        verbose_name='Bezeichnung',
        help_text='Format: NST-000001'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='Offizieller Name der Notarstelle'
    )

    # Adresse
    strasse = models.CharField(
        max_length=200,
        verbose_name='Straße'
    )
    plz = models.CharField(
        max_length=10,
        verbose_name='PLZ'
    )
    stadt = models.CharField(
        max_length=100,
        verbose_name='Stadt'
    )
    bundesland = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Bundesland'
    )

    # Sprengel-Zuordnung
    sprengel = models.ForeignKey(
        'sprengel.Sprengel',
        on_delete=models.PROTECT,
        related_name='notarstellen',
        null=True,
        blank=True,
        verbose_name='Sprengel',
        help_text='Zugehöriger Notarsprengel (Gerichtsbezirk)'
    )

    # Kontaktdaten
    telefon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Telefon'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='E-Mail'
    )

    # Zusätzliche Informationen
    besetzt_seit = models.DateField(
        null=True,
        blank=True,
        verbose_name='Besetzt seit',
        help_text='Datum der letzten Besetzung'
    )
    notiz = models.TextField(
        blank=True,
        verbose_name='Notizen',
        help_text='Interne Notizen und Bemerkungen'
    )

    class Meta:
        verbose_name = 'Notarstelle'
        verbose_name_plural = 'Notarstellen'
        ordering = ['bezeichnung']
        indexes = [
            models.Index(fields=['ist_aktiv']),
            models.Index(fields=['stadt']),
        ]

    def __str__(self):
        return f"{self.bezeichnung} - {self.name}"

    def get_adresse(self):
        """Gibt die vollständige Adresse als String zurück."""
        teile = [self.strasse, f"{self.plz} {self.stadt}"]
        if self.bundesland:
            teile.append(self.bundesland)
        return ', '.join(teile)

    def anzahl_notare(self):
        """Gibt die Anzahl der zugeordneten Notare zurück."""
        return self.notare.filter(ende_datum__isnull=True).count()

    def anzahl_anwaerter(self):
        """Gibt die Anzahl der zugeordneten Notariatskandidat zurück."""
        return self.anwaerter.filter(ende_datum__isnull=True).count()

    @classmethod
    def generate_next_id(cls):
        """Generiert die nächste Notarstellen-Bezeichnung im Format: NST-000001"""
        import re

        last = cls.objects.filter(
            bezeichnung__startswith='NST-'
        ).order_by('-bezeichnung').first()

        if last:
            match = re.search(r'-(\d+)$', last.bezeichnung)
            nummer = int(match.group(1)) + 1 if match else 1
        else:
            nummer = 1

        return f"NST-{nummer:06d}"
