"""
Service-Registry für die zentrale Verwaltung aller Services.

Die Registry verwaltet alle verfügbaren Services und synchronisiert sie mit der Datenbank.
"""
from typing import Dict, Type, List, Optional
import logging

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Zentrale Registry für alle Services.

    Services werden per @service Decorator automatisch registriert.
    """

    def __init__(self):
        """Initialisiert die Registry mit leerem Service-Dictionary."""
        self._services: Dict[str, Type] = {}

    def register(self, service_class: Type) -> None:
        """
        Registriert eine Service-Klasse in der Registry.

        Args:
            service_class: Die zu registrierende Service-Klasse

        Raises:
            ValueError: Wenn service_id fehlt oder bereits registriert
        """
        if not hasattr(service_class, 'service_id') or not service_class.service_id:
            raise ValueError(
                f"Service-Klasse {service_class.__name__} muss ein 'service_id' Attribut haben"
            )

        service_id = service_class.service_id

        if service_id in self._services:
            logger.warning(
                f"Service '{service_id}' wird überschrieben. "
                f"Alte Klasse: {self._services[service_id].__name__}, "
                f"Neue Klasse: {service_class.__name__}"
            )

        self._services[service_id] = service_class
        logger.debug(f"Service '{service_id}' registriert: {service_class.__name__}")

    def get(self, service_id: str) -> Type:
        """
        Holt eine Service-Klasse nach ID.

        Args:
            service_id: Die eindeutige Service-ID

        Returns:
            Die Service-Klasse

        Raises:
            KeyError: Wenn Service-ID nicht gefunden
        """
        if service_id not in self._services:
            raise KeyError(
                f"Service '{service_id}' nicht gefunden. "
                f"Verfügbare Services: {', '.join(self._services.keys())}"
            )
        return self._services[service_id]

    def alle_services(self) -> List[Type]:
        """
        Gibt alle registrierten Services zurück.

        Returns:
            Liste aller Service-Klassen
        """
        return list(self._services.values())

    def alle_service_ids(self) -> List[str]:
        """
        Gibt alle registrierten Service-IDs zurück.

        Returns:
            Liste aller Service-IDs
        """
        return list(self._services.keys())

    def ist_registriert(self, service_id: str) -> bool:
        """
        Prüft ob ein Service registriert ist.

        Args:
            service_id: Die zu prüfende Service-ID

        Returns:
            True wenn Service registriert, sonst False
        """
        return service_id in self._services

    def sync_mit_datenbank(self) -> Dict[str, int]:
        """
        Synchronisiert registrierte Services mit der Datenbank.

        Erstellt oder aktualisiert ServiceDefinition-Records für alle
        registrierten Services. Deaktiviert Services die nicht mehr im Code sind.

        Returns:
            Dictionary mit Statistiken: {
                'erstellt': Anzahl neu erstellter Services,
                'aktualisiert': Anzahl aktualisierter Services,
                'deaktiviert': Anzahl deaktivierter Services
            }
        """
        from apps.services.models import ServiceDefinition, ServiceKategorie

        statistik = {
            'erstellt': 0,
            'aktualisiert': 0,
            'deaktiviert': 0
        }

        # Alle Service-IDs aus der Registry holen
        registrierte_ids = set(self._services.keys())

        # Services erstellen/aktualisieren
        for service_id, service_class in self._services.items():
            # Kategorie holen oder erstellen
            kategorie_name = getattr(service_class, 'kategorie', 'sonstiges')
            kategorie, _ = ServiceKategorie.objects.get_or_create(
                name=kategorie_name,
                defaults={
                    'beschreibung': f'Services für {kategorie_name}',
                    'reihenfolge': 999
                }
            )

            # ServiceDefinition erstellen oder aktualisieren
            service_def, created = ServiceDefinition.objects.update_or_create(
                service_id=service_id,
                defaults={
                    'name': getattr(service_class, 'name', service_id),
                    'beschreibung': getattr(service_class, 'beschreibung', ''),
                    'kategorie': kategorie,
                    'icon': getattr(service_class, 'icon', 'tools'),
                    'button_text': getattr(service_class, 'button_text', 'Service ausführen'),
                    'button_css_class': getattr(service_class, 'button_css_class', 'btn-primary'),
                    'erforderliche_rolle': getattr(service_class, 'erforderliche_rolle', ''),
                    'ist_aktiv': True
                }
            )

            if created:
                statistik['erstellt'] += 1
                logger.info(f"Service '{service_id}' in Datenbank erstellt")
            else:
                statistik['aktualisiert'] += 1
                logger.debug(f"Service '{service_id}' in Datenbank aktualisiert")

        # Services deaktivieren die nicht mehr im Code sind
        db_service_ids = set(
            ServiceDefinition.objects.filter(ist_aktiv=True).values_list('service_id', flat=True)
        )
        veraltete_ids = db_service_ids - registrierte_ids

        if veraltete_ids:
            anzahl_deaktiviert = ServiceDefinition.objects.filter(
                service_id__in=veraltete_ids,
                ist_aktiv=True
            ).update(ist_aktiv=False)

            statistik['deaktiviert'] = anzahl_deaktiviert
            logger.warning(
                f"{anzahl_deaktiviert} veraltete Services deaktiviert: {', '.join(veraltete_ids)}"
            )

        logger.info(
            f"Service-Sync abgeschlossen: "
            f"{statistik['erstellt']} erstellt, "
            f"{statistik['aktualisiert']} aktualisiert, "
            f"{statistik['deaktiviert']} deaktiviert"
        )

        return statistik


# Globale Singleton-Instanz
service_registry = ServiceRegistry()
