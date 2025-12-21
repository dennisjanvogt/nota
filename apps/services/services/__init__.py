"""
Service-Implementierungen.

Alle Service-Module werden hier importiert,
damit der @service Decorator sie automatisch registriert.
"""

# Import aller Service-Module (wichtig für automatische Registrierung!)
from . import dokument_services
from . import email_services
from . import workflow_services

__all__ = [
    'dokument_services',
    'email_services',
    'workflow_services',
]
