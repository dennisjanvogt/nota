"""
Basis-Klassen und Decorators für das Service-System.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from decimal import Decimal
import time
import logging
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.services.registry import service_registry

logger = logging.getLogger(__name__)
User = get_user_model()


class BaseService(ABC):
    """
    Abstrakte Basis-Klasse für alle Services.

    Subklassen müssen folgende Klassen-Attribute definieren:
    - service_id: Eindeutige ID (z.B. 'stammblatt_pdf_einzeln')
    - name: Benutzerfreundlicher Name
    - beschreibung: Was macht der Service?
    - kategorie: Kategorie-Name (z.B. 'dokumente', 'kommunikation')

    Optional:
    - icon: Bootstrap Icon Name (default: 'tools')
    - button_text: Text für Ausführungs-Button (default: 'Service ausführen')
    - button_css_class: CSS-Klasse für Button (default: 'btn-primary')
    - erforderliche_rolle: Rolle die benötigt wird (default: '')

    Subklassen müssen die Methode ausfuehren() implementieren.
    """

    # Klassen-Attribute (von Subklassen überschrieben)
    service_id: str = None
    name: str = None
    beschreibung: str = None
    kategorie: str = None
    icon: str = 'tools'
    button_text: str = 'Service ausführen'
    button_css_class: str = 'btn-primary'
    erforderliche_rolle: str = ''

    def __init__(self, benutzer: User, **kwargs):
        """
        Initialisiert den Service.

        Args:
            benutzer: Der ausführende Benutzer
            **kwargs: Service-Parameter
        """
        self.benutzer = benutzer
        self.parameter = kwargs
        self._start_zeit = None
        self._service_ausfuehrung = None

    @abstractmethod
    def ausfuehren(self) -> Dict[str, Any]:
        """
        Führt den Service aus.

        Diese Methode MUSS von Subklassen implementiert werden.

        Returns:
            Dictionary mit Ergebnis-Daten (wird in ServiceAusfuehrung.ergebnis_daten gespeichert)

        Raises:
            Exception: Bei Fehlern während der Ausführung
        """
        pass

    def validiere_parameter(self) -> None:
        """
        Validiert die Service-Parameter.

        Diese Methode kann von Subklassen überschrieben werden um
        Parameter vor der Ausführung zu prüfen.

        Raises:
            ValueError: Wenn Parameter ungültig sind
        """
        pass

    @transaction.atomic
    def execute(self) -> 'ServiceAusfuehrung':
        """
        Wrapper-Methode die den Service ausführt und protokolliert.

        Diese Methode sollte NICHT überschrieben werden.
        Sie kümmert sich um:
        - Parameter-Validierung
        - Performance-Messung
        - Error-Handling
        - Datenbank-Protokollierung

        Returns:
            ServiceAusfuehrung-Instanz mit Ergebnis

        Raises:
            Exception: Bei kritischen Fehlern
        """
        from apps.services.models import ServiceDefinition, ServiceAusfuehrung

        # Service-Definition aus DB holen
        try:
            service_def = ServiceDefinition.objects.get(service_id=self.service_id)
        except ServiceDefinition.DoesNotExist:
            raise ValueError(
                f"Service '{self.service_id}' ist nicht in der Datenbank registriert. "
                f"Bitte 'python manage.py services_sync' ausführen."
            )

        # Berechtigungen prüfen
        if not service_def.kann_benutzer_ausfuehren(self.benutzer):
            raise PermissionError(
                f"Benutzer '{self.benutzer.username}' hat keine Berechtigung "
                f"für Service '{service_def.name}'"
            )

        # Service-Ausführung erstellen
        self._service_ausfuehrung = ServiceAusfuehrung.objects.create(
            service=service_def,
            ausgefuehrt_von=self.benutzer,
            workflow_instanz=self.parameter.get('workflow_instanz'),
            workflow_schritt=self.parameter.get('workflow_schritt'),
        )

        # Performance-Messung starten
        self._start_zeit = time.time()

        try:
            # Parameter validieren
            logger.info(
                f"Service '{self.service_id}' wird ausgeführt von {self.benutzer.username}"
            )
            self.validiere_parameter()

            # Service ausführen
            ergebnis = self.ausfuehren()

            # Erfolg protokollieren
            dauer = Decimal(str(time.time() - self._start_zeit))
            self._service_ausfuehrung.erfolgreich = True
            self._service_ausfuehrung.ergebnis_daten = ergebnis or {}
            self._service_ausfuehrung.dauer_sekunden = dauer
            self._service_ausfuehrung.save()

            logger.info(
                f"Service '{self.service_id}' erfolgreich ausgeführt in {dauer:.3f}s"
            )

            return self._service_ausfuehrung

        except Exception as e:
            # Fehler protokollieren
            dauer = Decimal(str(time.time() - self._start_zeit)) if self._start_zeit else None
            self._service_ausfuehrung.erfolgreich = False
            self._service_ausfuehrung.fehlermeldung = str(e)
            self._service_ausfuehrung.dauer_sekunden = dauer
            self._service_ausfuehrung.save()

            logger.error(
                f"Service '{self.service_id}' fehlgeschlagen: {e}",
                exc_info=True
            )

            # Exception weiterwerfen
            raise

    def hole_parameter(self, name: str, required: bool = True, default: Any = None) -> Any:
        """
        Hilfsmethode zum Holen von Parametern.

        Args:
            name: Parameter-Name
            required: Ob Parameter erforderlich ist
            default: Default-Wert wenn nicht required

        Returns:
            Parameter-Wert

        Raises:
            ValueError: Wenn required Parameter fehlt
        """
        if name not in self.parameter:
            if required:
                raise ValueError(f"Erforderlicher Parameter '{name}' fehlt")
            return default
        return self.parameter[name]


def service(kategorie: str, **metadata):
    """
    Decorator zur automatischen Registrierung von Services.

    Nutze diesen Decorator um Services automatisch in der Registry zu registrieren.

    Args:
        kategorie: Kategorie-Name (z.B. 'dokumente', 'kommunikation', 'verwaltung')
        **metadata: Zusätzliche Metadaten (icon, button_text, button_css_class, erforderliche_rolle)

    Example:
        @service(kategorie='dokumente', icon='file-earmark-pdf', button_text='PDF erstellen')
        class MeinService(BaseService):
            service_id = 'mein_service'
            name = 'Mein Service'
            beschreibung = 'Macht etwas cooles'

            def ausfuehren(self):
                return {'status': 'ok'}
    """
    def decorator(cls):
        # Kategorie setzen
        cls.kategorie = kategorie

        # Metadaten übernehmen
        if 'icon' in metadata:
            cls.icon = metadata['icon']
        if 'button_text' in metadata:
            cls.button_text = metadata['button_text']
        if 'button_css_class' in metadata:
            cls.button_css_class = metadata['button_css_class']
        if 'erforderliche_rolle' in metadata:
            cls.erforderliche_rolle = metadata['erforderliche_rolle']

        # In Registry registrieren
        service_registry.register(cls)

        logger.debug(f"Service-Klasse {cls.__name__} dekoriert und registriert")

        return cls

    return decorator
