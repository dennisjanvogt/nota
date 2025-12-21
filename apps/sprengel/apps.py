"""
App-Konfiguration für Sprengel-Verwaltung.
"""
from django.apps import AppConfig


class SprengelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sprengel'
    verbose_name = 'Sprengel'
