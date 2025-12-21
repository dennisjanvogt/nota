"""
App-Konfiguration für das Service-System.
"""
from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """Konfiguration für die Services-App."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.services'
    verbose_name = 'Service-System'

    def ready(self):
        """
        Wird beim App-Start aufgerufen.

        Importiert alle Service-Module, damit der @service Decorator
        sie in der Registry registriert.
        """
        # Services importieren (nur wenn Django vollständig gestartet ist)
        try:
            # Verhindert Importe während Migrations
            import django
            if django.VERSION >= (3, 2):
                from django.conf import settings
                if settings.configured:
                    import apps.services.services  # noqa
        except Exception:
            # Bei Fehlern während des Starts nicht crashen
            pass
