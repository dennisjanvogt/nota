"""
Admin-Konfiguration für Benutzer-App.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import KammerBenutzer


@admin.register(KammerBenutzer)
class KammerBenutzerAdmin(BaseUserAdmin):
    """Admin für Kammermitarbeiter."""

    list_display = ['username', 'email', 'get_full_name', 'rolle', 'abteilung', 'is_active']
    list_filter = ['rolle', 'abteilung', 'is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Kammer-spezifische Felder', {
            'fields': ('rolle', 'abteilung', 'telefon'),
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Kammer-spezifische Felder', {
            'fields': ('rolle', 'abteilung', 'telefon'),
        }),
    )
