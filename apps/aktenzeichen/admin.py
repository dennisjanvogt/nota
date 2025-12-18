"""
Admin-Konfiguration für Aktenzeichen.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Nummernsequenz, Aktenzeichen


@admin.register(Nummernsequenz)
class NummernsequenzAdmin(admin.ModelAdmin):
    """Admin für Nummernsequenzen."""

    list_display = [
        'praefix',
        'jahr',
        'aktuelle_nummer',
        'vorschau_naechste',
        'anzahl_aktenzeichen',
    ]
    list_filter = ['jahr', 'praefix']
    search_fields = ['jahr']
    ordering = ['-jahr', 'praefix']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    fieldsets = (
        ('Sequenz-Daten', {
            'fields': ('jahr', 'praefix', 'aktuelle_nummer')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def vorschau_naechste(self, obj):
        """Zeigt Vorschau der nächsten Nummer."""
        naechste = obj.vorschau_naechste_nummer()
        nummer_str = str(naechste).zfill(4)
        vollstaendig = f"{obj.praefix}-{obj.jahr}-{nummer_str}"
        return format_html(
            '<code style="background: #f0f0f0; padding: 2px 4px;">{}</code>',
            vollstaendig
        )
    vorschau_naechste.short_description = 'Nächste Nummer'

    def anzahl_aktenzeichen(self, obj):
        """Zeigt Anzahl der generierten Aktenzeichen."""
        return obj.aktenzeichen.count()
    anzahl_aktenzeichen.short_description = 'Generierte AZ'


@admin.register(Aktenzeichen)
class AktenzeichenAdmin(admin.ModelAdmin):
    """Admin für Aktenzeichen."""

    list_display = [
        'vollstaendige_nummer_display',
        'kategorie',
        'jahr',
        'kurze_beschreibung',
        'erstellt_am',
    ]
    list_filter = ['kategorie', 'jahr', 'sequenz__praefix']
    search_fields = ['vollstaendige_nummer', 'beschreibung']
    ordering = ['-jahr', '-laufnummer']
    readonly_fields = [
        'vollstaendige_nummer',
        'laufnummer',
        'erstellt_am',
        'aktualisiert_am'
    ]
    date_hierarchy = 'erstellt_am'

    fieldsets = (
        ('Aktenzeichen', {
            'fields': ('vollstaendige_nummer', 'sequenz', 'laufnummer', 'jahr')
        }),
        ('Details', {
            'fields': ('kategorie', 'beschreibung')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def vollstaendige_nummer_display(self, obj):
        """Zeigt Aktenzeichen formatiert an."""
        return format_html(
            '<strong style="font-family: monospace; font-size: 14px;">{}</strong>',
            obj.vollstaendige_nummer
        )
    vollstaendige_nummer_display.short_description = 'Aktenzeichen'

    def kurze_beschreibung(self, obj):
        """Zeigt gekürzte Beschreibung."""
        if obj.beschreibung:
            max_length = 50
            if len(obj.beschreibung) > max_length:
                return obj.beschreibung[:max_length] + '...'
            return obj.beschreibung
        return '-'
    kurze_beschreibung.short_description = 'Beschreibung'

    def has_add_permission(self, request):
        """
        Aktenzeichen sollten nicht manuell erstellt werden.
        Nur über den AktenzeichenService!
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """Aktenzeichen sollten nicht gelöscht werden."""
        return request.user.is_superuser  # Nur Superuser dürfen löschen
