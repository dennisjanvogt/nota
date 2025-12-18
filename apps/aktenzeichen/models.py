"""
Models für Aktenzeichen-Verwaltung.

Das Aktenzeichen-System generiert eindeutige, strukturierte Nummern für Vorgänge der Kammer.
Format: PREFIX-JAHR-LAUFNUMMER (z.B. BES-2025-0001)
"""
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.kern.models import ZeitstempelModel


class Nummernsequenz(ZeitstempelModel):
    """
    Verwaltet Sequenzen für Aktenzeichen-Generierung.

    Eine Sequenz pro Jahr und Präfix. Thread-safe durch SELECT FOR UPDATE.
    """

    PRAEFIX_CHOICES = [
        ('BES', 'Bestellung'),
        ('ZUL', 'Zulassung'),
        ('AUF', 'Aufsicht'),
        ('ALL', 'Allgemein'),
    ]

    jahr = models.PositiveIntegerField(
        verbose_name='Jahr'
    )
    praefix = models.CharField(
        max_length=10,
        choices=PRAEFIX_CHOICES,
        verbose_name='Präfix',
        help_text='Präfix für das Aktenzeichen'
    )
    aktuelle_nummer = models.PositiveIntegerField(
        default=0,
        verbose_name='Aktuelle Nummer',
        help_text='Letzte vergebene laufende Nummer'
    )

    class Meta:
        verbose_name = 'Nummernsequenz'
        verbose_name_plural = 'Nummernsequenzen'
        unique_together = [['jahr', 'praefix']]
        ordering = ['-jahr', 'praefix']
        indexes = [
            models.Index(fields=['jahr', 'praefix']),
        ]

    def __str__(self):
        return f"{self.praefix}-{self.jahr} (aktuelle Nummer: {self.aktuelle_nummer})"

    @transaction.atomic
    def naechste_nummer_holen(self):
        """
        Generiert die nächste Nummer in der Sequenz.

        Thread-safe durch SELECT FOR UPDATE.
        Muss in einer Transaktion aufgerufen werden!

        Returns:
            int: Die nächste laufende Nummer
        """
        # SELECT FOR UPDATE verhindert Race Conditions
        sequenz = Nummernsequenz.objects.select_for_update().get(pk=self.pk)
        sequenz.aktuelle_nummer += 1
        sequenz.save()
        return sequenz.aktuelle_nummer

    def vorschau_naechste_nummer(self):
        """
        Zeigt Vorschau der nächsten Nummer ohne zu generieren.

        Returns:
            int: Die nächste Nummer (ohne zu speichern)
        """
        return self.aktuelle_nummer + 1


class Aktenzeichen(ZeitstempelModel):
    """
    Aktenzeichen der Kammer.

    Format: PREFIX-JAHR-LAUFNUMMER
    Beispiel: BES-2025-0001
    """

    KATEGORIE_CHOICES = [
        ('Bestellung', 'Bestellung'),
        ('Zulassung', 'Zulassung'),
        ('Aufsicht', 'Aufsicht'),
        ('Allgemein', 'Allgemein'),
    ]

    sequenz = models.ForeignKey(
        Nummernsequenz,
        on_delete=models.PROTECT,
        related_name='aktenzeichen',
        verbose_name='Sequenz'
    )
    vollstaendige_nummer = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='Aktenzeichen',
        help_text='Vollständiges Aktenzeichen (wird automatisch generiert)'
    )
    laufnummer = models.PositiveIntegerField(
        verbose_name='Laufnummer'
    )
    jahr = models.PositiveIntegerField(
        verbose_name='Jahr'
    )
    kategorie = models.CharField(
        max_length=50,
        choices=KATEGORIE_CHOICES,
        verbose_name='Kategorie',
        help_text='Kategorie des Vorgangs'
    )
    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung',
        help_text='Kurze Beschreibung des Vorgangs'
    )

    class Meta:
        verbose_name = 'Aktenzeichen'
        verbose_name_plural = 'Aktenzeichen'
        ordering = ['-jahr', '-laufnummer']
        indexes = [
            models.Index(fields=['vollstaendige_nummer']),
            models.Index(fields=['jahr', 'sequenz']),
            models.Index(fields=['kategorie']),
        ]

    def __str__(self):
        return self.vollstaendige_nummer

    def save(self, *args, **kwargs):
        """Generiert automatisch die vollständige Nummer beim Speichern."""
        if not self.vollstaendige_nummer:
            self.vollstaendige_nummer = self.nummer_generieren()
        super().save(*args, **kwargs)

    def nummer_generieren(self):
        """
        Generiert die formatierte Aktenzeichennummer.

        Format: PREFIX-JAHR-LAUFNUMMER
        Beispiel: BES-2025-0001

        Returns:
            str: Formatiertes Aktenzeichen
        """
        praefix = self.sequenz.praefix
        jahr = self.jahr
        # Laufnummer mit führenden Nullen (4 Stellen)
        nummer = str(self.laufnummer).zfill(4)

        return f"{praefix}-{jahr}-{nummer}"

    def clean(self):
        """Validierung vor dem Speichern."""
        super().clean()

        # Jahr muss mit Sequenz-Jahr übereinstimmen
        if self.jahr != self.sequenz.jahr:
            raise ValidationError({
                'jahr': f'Jahr muss {self.sequenz.jahr} sein (Sequenz-Jahr)'
            })
