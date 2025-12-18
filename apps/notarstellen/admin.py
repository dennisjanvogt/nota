"""
Admin-Konfiguration für Notarstellen.
"""
from django.contrib import admin
from .models import Notarstelle


@admin.register(Notarstelle)
class NotarstelleAdmin(admin.ModelAdmin):
    """Admin für Notarstellen."""

    list_display = [
        'notarnummer',
        'bezeichnung',
        'name',
        'stadt',
        'anzahl_notare',
        'anzahl_anwaerter',
        'ist_aktiv'
    ]
    list_filter = ['ist_aktiv', 'bundesland', 'stadt']
    search_fields = ['notarnummer', 'bezeichnung', 'name', 'stadt']
    ordering = ['notarnummer']

    fieldsets = (
        ('Grunddaten', {
            'fields': ('notarnummer', 'bezeichnung', 'name', 'ist_aktiv')
        }),
        ('Adresse', {
            'fields': ('strasse', 'plz', 'stadt', 'bundesland')
        }),
        ('Kontakt', {
            'fields': ('telefon', 'email')
        }),
        ('Weitere Informationen', {
            'fields': ('besetzt_seit', 'notiz'),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    def anzahl_notare(self, obj):
        """Zeigt Anzahl der Notare."""
        return obj.anzahl_notare()
    anzahl_notare.short_description = 'Notare'

    def anzahl_anwaerter(self, obj):
        """Zeigt Anzahl der Anwärter."""
        return obj.anzahl_anwaerter()
    anzahl_anwaerter.short_description = 'Anwärter'
