"""
Admin-Konfiguration für Personen (Notare und Notariatskandidaten).
"""
from django.contrib import admin
from .models import Notar, NotarAnwaerter


@admin.register(Notar)
class NotarAdmin(admin.ModelAdmin):
    """Admin für Notare."""

    list_display = [
        'get_voller_name',
        'notarstelle',
        'bestellt_am',
        'anzahl_betreute_anwaerter',
        'ist_aktiv_beschaeftigt',
    ]
    list_filter = ['ist_aktiv', 'notarstelle', 'war_vorher_anwaerter', 'bestellt_am']
    search_fields = ['notar_id', 'vorname', 'nachname', 'email']
    ordering = ['nachname', 'vorname']
    date_hierarchy = 'bestellt_am'

    fieldsets = (
        ('Persönliche Daten', {
            'fields': ('titel', 'vorname', 'nachname', 'email', 'telefon')
        }),
        ('Notar-Daten', {
            'fields': ('notar_id', 'notarstelle', 'bestellt_am', 'war_vorher_anwaerter')
        }),
        ('Zeitraum', {
            'fields': ('beginn_datum', 'ende_datum', 'ist_aktiv')
        }),
        ('Weitere Informationen', {
            'fields': ('notiz',),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    def get_readonly_fields(self, request, obj=None):
        """Macht notar_id read-only nach Erstellung."""
        if obj:  # Bearbeiten
            return self.readonly_fields + ['notar_id']
        return self.readonly_fields

    def ist_aktiv_beschaeftigt(self, obj):
        """Zeigt ob Notar aktiv beschäftigt ist."""
        return obj.ist_aktiv_beschaeftigt()
    ist_aktiv_beschaeftigt.short_description = 'Aktiv'
    ist_aktiv_beschaeftigt.boolean = True

    def anzahl_betreute_anwaerter(self, obj):
        """Zeigt Anzahl der betreuten Kandidaten."""
        return obj.anzahl_betreute_anwaerter()
    anzahl_betreute_anwaerter.short_description = 'Betreute Kandidaten'


@admin.register(NotarAnwaerter)
class NotarAnwaerterAdmin(admin.ModelAdmin):
    """Admin für Notariatskandidaten."""

    list_display = [
        'get_voller_name',
        'betreuender_notar',
        'notarstelle',
        'zugelassen_am',
        'dauer_in_monaten',
        'ist_aktiv_beschaeftigt',
    ]
    list_filter = ['ist_aktiv', 'notarstelle', 'betreuender_notar', 'zugelassen_am']
    search_fields = ['anwaerter_id', 'vorname', 'nachname', 'email']
    ordering = ['nachname', 'vorname']
    date_hierarchy = 'zugelassen_am'

    fieldsets = (
        ('Persönliche Daten', {
            'fields': ('titel', 'vorname', 'nachname', 'email', 'telefon')
        }),
        ('Kandidaten-Daten', {
            'fields': (
                'anwaerter_id',
                'betreuender_notar',
                'notarstelle',
                'zugelassen_am',
                'geplante_bestellung'
            )
        }),
        ('Zeitraum', {
            'fields': ('beginn_datum', 'ende_datum', 'ist_aktiv')
        }),
        ('Weitere Informationen', {
            'fields': ('notiz',),
            'classes': ('collapse',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    def get_readonly_fields(self, request, obj=None):
        """Macht anwaerter_id read-only nach Erstellung."""
        if obj:  # Bearbeiten
            return self.readonly_fields + ['anwaerter_id']
        return self.readonly_fields

    def ist_aktiv_beschaeftigt(self, obj):
        """Zeigt ob Kandidat aktiv ist."""
        return obj.ist_aktiv_beschaeftigt()
    ist_aktiv_beschaeftigt.short_description = 'Aktiv'
    ist_aktiv_beschaeftigt.boolean = True

    def dauer_in_monaten(self, obj):
        """Zeigt Dauer der Kandidatenzeit."""
        monate = obj.dauer_in_monaten()
        return f"{monate} Monate"
    dauer_in_monaten.short_description = 'Dauer'
