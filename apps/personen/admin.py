"""
Admin-Konfiguration für Personen (Notare und Notar-Anwärter).
"""
from django.contrib import admin
from .models import Notar, NotarAnwaerter


@admin.register(Notar)
class NotarAdmin(admin.ModelAdmin):
    """Admin für Notare."""

    list_display = [
        'notar_id',
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

    def ist_aktiv_beschaeftigt(self, obj):
        """Zeigt ob Notar aktiv beschäftigt ist."""
        return obj.ist_aktiv_beschaeftigt()
    ist_aktiv_beschaeftigt.short_description = 'Aktiv'
    ist_aktiv_beschaeftigt.boolean = True

    def anzahl_betreute_anwaerter(self, obj):
        """Zeigt Anzahl der betreuten Anwärter."""
        return obj.anzahl_betreute_anwaerter()
    anzahl_betreute_anwaerter.short_description = 'Betreute Anwärter'


@admin.register(NotarAnwaerter)
class NotarAnwaerterAdmin(admin.ModelAdmin):
    """Admin für Notar-Anwärter."""

    list_display = [
        'anwaerter_id',
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
        ('Anwärter-Daten', {
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

    def ist_aktiv_beschaeftigt(self, obj):
        """Zeigt ob Anwärter aktiv ist."""
        return obj.ist_aktiv_beschaeftigt()
    ist_aktiv_beschaeftigt.short_description = 'Aktiv'
    ist_aktiv_beschaeftigt.boolean = True

    def dauer_in_monaten(self, obj):
        """Zeigt Dauer der Anwärterzeit."""
        monate = obj.dauer_in_monaten()
        return f"{monate} Monate"
    dauer_in_monaten.short_description = 'Dauer'
