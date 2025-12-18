"""
Admin-Konfiguration für E-Mail-Vorlagen.
"""
from django.contrib import admin
from .models import EmailVorlage, GesendeteEmail


@admin.register(EmailVorlage)
class EmailVorlageAdmin(admin.ModelAdmin):
    list_display = ['name', 'kategorie', 'standard_empfaenger', 'ist_aktiv', 'aktualisiert_am']
    list_filter = ['kategorie', 'ist_aktiv']
    search_fields = ['name', 'betreff', 'standard_empfaenger']
    fieldsets = (
        ('Grunddaten', {
            'fields': ('name', 'kategorie', 'ist_aktiv')
        }),
        ('E-Mail-Inhalt', {
            'fields': ('betreff', 'nachricht')
        }),
        ('Empfänger', {
            'fields': ('standard_empfaenger', 'cc_empfaenger')
        }),
    )


@admin.register(GesendeteEmail)
class GesendeteEmailAdmin(admin.ModelAdmin):
    list_display = ['betreff', 'empfaenger', 'gesendet_von', 'erfolgreich', 'gesendet_am']
    list_filter = ['erfolgreich', 'gesendet_am', 'vorlage']
    search_fields = ['betreff', 'empfaenger', 'nachricht']
    readonly_fields = ['gesendet_am']
    fieldsets = (
        ('E-Mail-Daten', {
            'fields': ('vorlage', 'betreff', 'empfaenger', 'cc_empfaenger', 'nachricht')
        }),
        ('Versand-Info', {
            'fields': ('gesendet_von', 'notar', 'anwaerter', 'erfolgreich', 'fehler', 'gesendet_am')
        }),
    )
