"""
Service-Layer für Aktenzeichen-Generierung.

Der AktenzeichenService bietet Thread-safe Methoden zur Generierung von Aktenzeichen.
"""
from django.db import transaction
from django.utils import timezone
from .models import Nummernsequenz, Aktenzeichen


class AktenzeichenService:
    """
    Service für Thread-safe Aktenzeichen-Generierung.

    Alle Methoden sind transaktionssicher und können parallel aufgerufen werden.
    """

    @staticmethod
    @transaction.atomic
    def aktenzeichen_generieren(praefix, kategorie, jahr=None, beschreibung=''):
        """
        Generiert ein neues Aktenzeichen.

        Thread-safe durch Transaktion und SELECT FOR UPDATE.

        Args:
            praefix (str): Präfix (z.B. 'BES', 'ZUL', 'AUF', 'ALL')
            kategorie (str): Kategorie (z.B. 'Bestellung', 'Zulassung')
            jahr (int, optional): Jahr. Defaults to aktuelles Jahr.
            beschreibung (str, optional): Beschreibung des Vorgangs. Defaults to ''.

        Returns:
            Aktenzeichen: Das neu generierte Aktenzeichen-Objekt

        Raises:
            ValueError: Wenn ungültiger Präfix oder Kategorie
        """
        # Validiere Präfix
        gueltige_praefixe = dict(Nummernsequenz.PRAEFIX_CHOICES)
        if praefix not in gueltige_praefixe:
            raise ValueError(
                f"Ungültiger Präfix '{praefix}'. "
                f"Gültige Werte: {', '.join(gueltige_praefixe.keys())}"
            )

        # Validiere Kategorie
        gueltige_kategorien = dict(Aktenzeichen.KATEGORIE_CHOICES)
        if kategorie not in gueltige_kategorien:
            raise ValueError(
                f"Ungültige Kategorie '{kategorie}'. "
                f"Gültige Werte: {', '.join(gueltige_kategorien.keys())}"
            )

        # Bestimme Jahr
        if jahr is None:
            jahr = timezone.now().year

        # Hole oder erstelle Sequenz (mit Lock!)
        sequenz, created = Nummernsequenz.objects.select_for_update().get_or_create(
            jahr=jahr,
            praefix=praefix,
            defaults={'aktuelle_nummer': 0}
        )

        # Generiere nächste Nummer (Thread-safe)
        laufnummer = sequenz.naechste_nummer_holen()

        # Erstelle Aktenzeichen
        aktenzeichen = Aktenzeichen.objects.create(
            sequenz=sequenz,
            laufnummer=laufnummer,
            jahr=jahr,
            kategorie=kategorie,
            beschreibung=beschreibung
        )

        return aktenzeichen

    @staticmethod
    def vorschau_holen(praefix, jahr=None):
        """
        Zeigt Vorschau der nächsten Nummer ohne zu generieren.

        Args:
            praefix (str): Präfix (z.B. 'BES', 'ZUL')
            jahr (int, optional): Jahr. Defaults to aktuelles Jahr.

        Returns:
            str: Vorschau des nächsten Aktenzeichens (z.B. "BES-2025-0001")
        """
        if jahr is None:
            jahr = timezone.now().year

        try:
            sequenz = Nummernsequenz.objects.get(jahr=jahr, praefix=praefix)
            naechste_nummer = sequenz.vorschau_naechste_nummer()
        except Nummernsequenz.DoesNotExist:
            # Sequenz existiert noch nicht -> erste Nummer wäre 1
            naechste_nummer = 1

        # Formatiere Vorschau
        nummer_str = str(naechste_nummer).zfill(4)
        return f"{praefix}-{jahr}-{nummer_str}"

    @staticmethod
    def statistik_holen(jahr=None):
        """
        Liefert Statistiken über generierte Aktenzeichen.

        Args:
            jahr (int, optional): Jahr für Statistik. Defaults to aktuelles Jahr.

        Returns:
            dict: Statistiken pro Präfix
                {
                    'BES': {'anzahl': 10, 'letzte_nummer': 10},
                    'ZUL': {'anzahl': 5, 'letzte_nummer': 5},
                    ...
                }
        """
        if jahr is None:
            jahr = timezone.now().year

        statistik = {}

        sequenzen = Nummernsequenz.objects.filter(jahr=jahr)
        for sequenz in sequenzen:
            statistik[sequenz.praefix] = {
                'bezeichnung': sequenz.get_praefix_display(),
                'anzahl': sequenz.aktuelle_nummer,
                'letzte_nummer': sequenz.aktuelle_nummer,
                'vorschau_naechste': sequenz.vorschau_naechste_nummer(),
            }

        return statistik

    @staticmethod
    def aktenzeichen_suchen(suchbegriff):
        """
        Sucht Aktenzeichen.

        Args:
            suchbegriff (str): Suchbegriff (Teil der Nummer oder Beschreibung)

        Returns:
            QuerySet: Gefundene Aktenzeichen
        """
        return Aktenzeichen.objects.filter(
            vollstaendige_nummer__icontains=suchbegriff
        ) | Aktenzeichen.objects.filter(
            beschreibung__icontains=suchbegriff
        )
