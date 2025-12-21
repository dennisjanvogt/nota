"""
Models für Personen-Verwaltung.

Notare und Notariatskandidaten, die von der Kammer verwaltet werden.
"""
from django.db import models
from apps.kern.models import ZeitstempelModel, AktivModel
from apps.notarstellen.models import Notarstelle


class PersonBasis(ZeitstempelModel, AktivModel):
    """
    Abstract Base Model für alle Personentypen.

    Gemeinsame Felder für Notare und Notariatskandidaten.
    """
    vorname = models.CharField(
        max_length=100,
        verbose_name='Vorname'
    )
    nachname = models.CharField(
        max_length=100,
        verbose_name='Nachname'
    )
    titel = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Titel',
        help_text='z.B. "Dr.", "Prof. Dr."'
    )

    # Kontaktdaten
    email = models.EmailField(
        unique=True,
        verbose_name='E-Mail'
    )
    telefon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Telefon'
    )

    # Zeitraum
    beginn_datum = models.DateField(
        verbose_name='Beginn',
        help_text='Beginn der Tätigkeit'
    )
    ende_datum = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ende',
        help_text='Ende der Tätigkeit (falls beendet)'
    )

    class Meta:
        abstract = True

    def get_voller_name(self):
        """Gibt den vollständigen Namen inkl. Titel zurück."""
        teile = [self.titel, self.vorname, self.nachname]
        return ' '.join(filter(None, teile))

    def ist_aktiv_beschaeftigt(self):
        """Prüft ob Person aktuell tätig ist."""
        return self.ist_aktiv and self.ende_datum is None


class Notar(PersonBasis):
    """
    Notar - Voll qualifizierter Notar.

    Ein Notar ist ein bestellter Notar, der bei einer Notarstelle tätig ist.
    """
    notarstelle = models.ForeignKey(
        Notarstelle,
        on_delete=models.PROTECT,
        related_name='notare',
        verbose_name='Notarstelle'
    )
    notar_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Bezeichnung',
        help_text='Format: NOT-000001'
    )
    bestellt_am = models.DateField(
        verbose_name='Bestellt am',
        help_text='Datum der Bestellung zum Notar'
    )
    war_vorher_anwaerter = models.BooleanField(
        default=False,
        verbose_name='War vorher Notariatskandidat',
        help_text='Hat die Person vorher als Notariatskandidat gearbeitet?'
    )
    notiz = models.TextField(
        blank=True,
        verbose_name='Notizen',
        help_text='Interne Notizen und Bemerkungen'
    )

    class Meta:
        verbose_name = 'Notar'
        verbose_name_plural = 'Notare'
        ordering = ['nachname', 'vorname']
        indexes = [
            models.Index(fields=['notar_id']),
            models.Index(fields=['notarstelle', 'ist_aktiv']),
            models.Index(fields=['nachname', 'vorname']),
        ]

    def __str__(self):
        return f"{self.get_voller_name()} (Notar {self.notar_id})"

    def anzahl_betreute_anwaerter(self):
        """Gibt die Anzahl der aktuell betreuten Kandidaten zurück."""
        return self.betreute_anwaerter.filter(
            ist_aktiv=True,
            ende_datum__isnull=True
        ).count()

    @classmethod
    def generate_next_id(cls):
        """Generiert die nächste Notar-ID im Format: NOT-000001"""
        import re

        last = cls.objects.filter(
            notar_id__startswith='NOT-'
        ).order_by('-notar_id').first()

        if last:
            match = re.search(r'-(\d+)$', last.notar_id)
            nummer = int(match.group(1)) + 1 if match else 1
        else:
            nummer = 1

        return f"NOT-{nummer:06d}"


class NotarAnwaerter(PersonBasis):
    """
    Notariatskandidat - Notar in Ausbildung.

    Ein Notariatskandidat lernt bei einem betreuenden Notar und wird später zum Notar bestellt.
    """
    betreuender_notar = models.ForeignKey(
        Notar,
        on_delete=models.PROTECT,
        related_name='betreute_anwaerter',
        verbose_name='Betreuender Notar',
        help_text='Der Notar, bei dem der Kandidat lernt'
    )
    notarstelle = models.ForeignKey(
        Notarstelle,
        on_delete=models.PROTECT,
        related_name='anwaerter',
        verbose_name='Notarstelle'
    )
    anwaerter_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Bezeichnung',
        help_text='Format: NKA-000001'
    )
    zugelassen_am = models.DateField(
        verbose_name='Zugelassen am',
        help_text='Datum der Zulassung als Notariatskandidat'
    )
    geplante_bestellung = models.DateField(
        null=True,
        blank=True,
        verbose_name='Geplante Bestellung',
        help_text='Geplantes Datum für Bestellung zum Notar'
    )
    notiz = models.TextField(
        blank=True,
        verbose_name='Notizen',
        help_text='Interne Notizen und Bemerkungen'
    )

    class Meta:
        verbose_name = 'Notariatskandidat'
        verbose_name_plural = 'Notariatskandidaten'
        ordering = ['nachname', 'vorname']
        indexes = [
            models.Index(fields=['anwaerter_id']),
            models.Index(fields=['betreuender_notar', 'ist_aktiv']),
            models.Index(fields=['notarstelle', 'ist_aktiv']),
            models.Index(fields=['nachname', 'vorname']),
        ]

    def __str__(self):
        return f"{self.get_voller_name()} (Kandidat {self.anwaerter_id})"

    def dauer_in_monaten(self):
        """Berechnet die Dauer der Kandidatenzeit in Monaten."""
        from datetime import date
        ende = self.ende_datum or date.today()
        delta = (ende.year - self.beginn_datum.year) * 12 + ende.month - self.beginn_datum.month
        return delta

    @classmethod
    def generate_next_id(cls):
        """Generiert die nächste Kandidaten-ID im Format: NKA-000001"""
        import re

        last = cls.objects.filter(
            anwaerter_id__startswith='NKA-'
        ).order_by('-anwaerter_id').first()

        if last:
            match = re.search(r'-(\d+)$', last.anwaerter_id)
            nummer = int(match.group(1)) + 1 if match else 1
        else:
            nummer = 1

        return f"NKA-{nummer:06d}"
