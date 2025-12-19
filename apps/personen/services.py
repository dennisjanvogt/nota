"""
Service-Layer für Personen-App.
Enthält Business-Logik für Notare und Notar-Anwärter.
"""
from django.db import transaction
from django.utils import timezone
from .models import Notar, NotarAnwaerter


@transaction.atomic
def anwaerter_zu_notar_befoerdern(anwaerter, notarstelle, bestellt_am=None, erstellt_von=None):
    """
    Befördert einen Notar-Anwärter zum Notar.

    Diese Methode:
    1. Erstellt einen neuen Notar mit den Daten des Anwärters
    2. Markiert den Anwärter als inaktiv (wird NICHT gelöscht für Historie!)
    3. Verknüpft Notar mit Anwärter für Nachverfolgbarkeit

    Args:
        anwaerter: NotarAnwaerter-Instanz die befördert werden soll
        notarstelle: Notarstelle zu der der Notar bestellt wird
        bestellt_am: Datum der Bestellung (default: heute)
        erstellt_von: KammerBenutzer der die Bestellung durchführt (optional)

    Returns:
        Notar: Die neu erstellte Notar-Instanz

    Raises:
        ValueError: Wenn der Anwärter nicht aktiv ist
    """
    if not anwaerter.ist_aktiv:
        raise ValueError(
            f"Anwärter {anwaerter.get_full_name()} ist bereits inaktiv und kann nicht befördert werden."
        )

    # Standardwert für bestellt_am
    if bestellt_am is None:
        bestellt_am = timezone.now().date()

    # Neuen Notar erstellen mit allen Daten des Anwärters
    notar = Notar.objects.create(
        # Basisdaten von PersonBasis
        vorname=anwaerter.vorname,
        nachname=anwaerter.nachname,
        titel=anwaerter.titel or '',
        email=anwaerter.email,
        telefon=anwaerter.telefon,

        # Notar-spezifische Felder
        notarstelle=notarstelle,
        bestellt_am=bestellt_am,
        beginn_datum=bestellt_am,  # Beginn als Notar = Bestellungsdatum

        # Markierung dass er vorher Anwärter war
        war_vorher_anwaerter=True,

        # Notiz mit Referenz zum Anwärter
        notiz=f"Befördert von Notar-Anwärter {anwaerter.anwaerter_id} am {bestellt_am.strftime('%d.%m.%Y')}",

        # Status
        ist_aktiv=True
    )

    # Anwärter als inaktiv markieren (NICHT löschen!)
    anwaerter.ist_aktiv = False
    anwaerter.ende_datum = bestellt_am

    # Notiz hinzufügen
    alte_notiz = anwaerter.notiz or ''
    neue_notiz = f"Zum Notar bestellt am {bestellt_am.strftime('%d.%m.%Y')} (Notar-ID: {notar.notar_id}, Notarstelle: {notarstelle.bezeichnung})"
    anwaerter.notiz = f"{alte_notiz}\n\n{neue_notiz}".strip()

    anwaerter.save()

    return notar


def anwaerter_wartezeit_berechnen(anwaerter):
    """
    Berechnet wie lange ein Anwärter bereits wartet.

    Args:
        anwaerter: NotarAnwaerter-Instanz

    Returns:
        dict: {
            'tage': Anzahl Tage seit Zulassung,
            'jahre': Anzahl Jahre (gerundet),
            'zugelassen_am': Datum der Zulassung
        }
    """
    if not anwaerter.zugelassen_am:
        return {
            'tage': 0,
            'jahre': 0,
            'zugelassen_am': None
        }

    heute = timezone.now().date()
    delta = heute - anwaerter.zugelassen_am
    tage = delta.days
    jahre = round(tage / 365.25, 1)  # Schaltjahre berücksichtigen

    return {
        'tage': tage,
        'jahre': jahre,
        'zugelassen_am': anwaerter.zugelassen_am
    }
