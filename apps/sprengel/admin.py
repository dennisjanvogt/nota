"""
Admin-Konfiguration für Sprengel.
"""
from django.contrib import admin
from .models import Sprengel


@admin.register(Sprengel)
class SprengelAdmin(admin.ModelAdmin):
    """Admin-Interface für Sprengel."""

    list_display = [
        'name',
        'gerichtsbezirk',
        'bundesland',
        'anzahl_notarstellen',
        'ist_aktiv',
        'aktualisiert_am',
    ]

    list_filter = [
        'bundesland',
        'ist_aktiv',
    ]

    search_fields = [
        'bezeichnung',
        'name',
        'gerichtsbezirk',
    ]

    readonly_fields = [
        'erstellt_am',
        'aktualisiert_am',
        'anzahl_notarstellen',
        'anzahl_aktive_notarstellen',
    ]

    fieldsets = (
        ('Grunddaten', {
            'fields': ('bezeichnung', 'name', 'gerichtsbezirk', 'bundesland')
        }),
        ('Details', {
            'fields': ('beschreibung', 'ist_aktiv')
        }),
        ('Statistik', {
            'fields': ('anzahl_notarstellen', 'anzahl_aktive_notarstellen'),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Bezeichnung wird nach Erstellung read-only."""
        if obj:  # Bearbeiten
            return self.readonly_fields + ('bezeichnung',)
        return self.readonly_fields
