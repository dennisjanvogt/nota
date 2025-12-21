"""
Workflow-Services für Verwaltungsakte.
"""
from typing import Dict, Any
from django.db import transaction
import logging

from apps.services.base import BaseService, service
from apps.personen.models import NotarAnwaerter, Notar
from apps.notarstellen.models import Notarstelle
from apps.personen.services import anwaerter_zu_notar_befoerdern

logger = logging.getLogger(__name__)


@service(
    kategorie='verwaltung',
    icon='person-check',
    button_text='Kandidat zum Notar befördern',
    button_css_class='btn-danger'  # Rot wegen irreversibel
)
class AnwaerterZuNotarBefoerdernService(BaseService):
    """
    Befördert einen Notariatskandidat zum Notar.

    ⚠️ **WICHTIG: Diese Aktion kann nicht rückgängig gemacht werden!**

    Der Kandidat wird:
    - Als inaktiv markiert (NICHT gelöscht)
    - Ein neuer Notar-Eintrag wird erstellt
    - Der Notarstelle zugeordnet
    - Historie wird beibehalten

    **Parameter:**
    - anwaerter_id: ID des Anwärters (required)
    - notarstelle_id: ID der Notarstelle (required)
    - bestellt_am: Datum der Bestellung (optional, default: heute)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    service_id = 'anwaerter_zu_notar_befoerdern'
    name = 'Kandidat zum Notar befördern'
    beschreibung = """
    Befördert einen Notariatskandidat zum Notar.

    ⚠️ **WICHTIG: Diese Aktion kann nicht rückgängig gemacht werden!**

    Der Service:
    1. Erstellt einen neuen Notar mit allen Daten des Anwärters
    2. Ordnet den Notar der Notarstelle zu
    3. Markiert den Kandidat als inaktiv (bleibt für Historie erhalten)
    4. Verknüpft Notar und Kandidat für Nachverfolgbarkeit

    **Parameter:**
    - anwaerter_id: ID des Anwärters
    - notarstelle_id: ID der Notarstelle
    - bestellt_am: Datum der Bestellung (optional)
    - workflow_instanz: Workflow-Zuordnung (optional)
    """

    # Erfordert höhere Berechtigung
    erforderliche_rolle = 'leitung'

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        anwaerter_id = self.hole_parameter('anwaerter_id', required=True)
        notarstelle_id = self.hole_parameter('notarstelle_id', required=True)

        # Prüfen ob Kandidat existiert und aktiv ist
        try:
            anwaerter = NotarAnwaerter.objects.get(id=anwaerter_id)
        except NotarAnwaerter.DoesNotExist:
            raise ValueError(f"Notariatskandidat mit ID {anwaerter_id} nicht gefunden")

        if not anwaerter.ist_aktiv:
            raise ValueError(
                f"Kandidat {anwaerter.get_voller_name()} ist bereits inaktiv "
                f"und kann nicht befördert werden"
            )

        # Prüfen ob Notarstelle existiert
        try:
            notarstelle = Notarstelle.objects.get(pk=notarstelle_id)
        except Notarstelle.DoesNotExist:
            raise ValueError(f"Notarstelle mit ID {notarstelle_id} nicht gefunden")

        # Warnung wenn Notarstelle bereits besetzt
        if hasattr(notarstelle, 'aktueller_notar') and notarstelle.aktueller_notar:
            logger.warning(
                f"Notarstelle {notarstelle} ist bereits besetzt durch "
                f"{notarstelle.aktueller_notar.get_voller_name()}"
            )

    @transaction.atomic
    def ausfuehren(self) -> Dict[str, Any]:
        """Führt die Beförderung durch."""
        anwaerter_id = self.hole_parameter('anwaerter_id')
        notarstelle_id = self.hole_parameter('notarstelle_id')
        bestellt_am = self.hole_parameter('bestellt_am', required=False)

        # Daten laden
        anwaerter = NotarAnwaerter.objects.get(id=anwaerter_id)
        notarstelle = Notarstelle.objects.get(pk=notarstelle_id)

        # Beförderung durchführen (nutzt bestehende Funktion)
        notar = anwaerter_zu_notar_befoerdern(
            anwaerter=anwaerter,
            notarstelle=notarstelle,
            bestellt_am=bestellt_am,
            erstellt_von=self.benutzer
        )

        logger.info(
            f"Kandidat {anwaerter.get_voller_name()} (ID: {anwaerter.id}) "
            f"erfolgreich zum Notar befördert (Notar-ID: {notar.id}, "
            f"Notarstelle: {notarstelle})"
        )

        return {
            'notar_id': notar.id,
            'notar_nummer': notar.notar_id,
            'name': notar.get_voller_name(),
            'notarstelle_id': notarstelle.pk,
            'notarstelle': str(notarstelle),
            'bestellt_am': notar.bestellt_am.strftime('%d.%m.%Y') if notar.bestellt_am else None,
            'anwaerter_id_alt': anwaerter.id,
            'anwaerter_nummer_alt': anwaerter.anwaerter_id,
            'erfolg': True
        }
