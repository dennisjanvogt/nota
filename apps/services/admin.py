"""
Admin-Interface für das Service-System und DMS.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.services.models import (
    ServiceKategorie,
    ServiceDefinition,
    ServiceAusfuehrung,
    Dokument
)


@admin.register(ServiceKategorie)
class ServiceKategorieAdmin(admin.ModelAdmin):
    """Admin für Service-Kategorien."""
    list_display = ['name', 'icon_preview', 'reihenfolge', 'anzahl_services']
    list_editable = ['reihenfolge']
    search_fields = ['name', 'beschreibung']
    ordering = ['reihenfolge', 'name']

    def icon_preview(self, obj):
        """Zeigt Icon-Vorschau."""
        if obj.icon:
            return format_html(
                '<i class="bi bi-{}"></i> {}',
                obj.icon,
                obj.icon
            )
        return '-'
    icon_preview.short_description = 'Icon'

    def anzahl_services(self, obj):
        """Anzahl Services in dieser Kategorie."""
        return obj.services.count()
    anzahl_services.short_description = 'Anzahl Services'


@admin.register(ServiceDefinition)
class ServiceDefinitionAdmin(admin.ModelAdmin):
    """Admin für Service-Definitionen."""
    list_display = [
        'name',
        'service_id',
        'kategorie',
        'icon_preview',
        'ist_aktiv',
        'erforderliche_rolle',
        'anzahl_ausfuehrungen'
    ]
    list_filter = ['kategorie', 'ist_aktiv', 'erforderliche_rolle']
    search_fields = ['name', 'service_id', 'beschreibung']
    readonly_fields = ['service_id', 'erstellt_am', 'aktualisiert_am']
    ordering = ['kategorie', 'name']

    fieldsets = (
        ('Identifikation', {
            'fields': ('service_id', 'name', 'beschreibung', 'kategorie')
        }),
        ('UI-Integration', {
            'fields': ('icon', 'button_text', 'button_css_class')
        }),
        ('Berechtigungen', {
            'fields': ('ist_aktiv', 'erforderliche_rolle')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def icon_preview(self, obj):
        """Zeigt Icon-Vorschau."""
        if obj.icon:
            return format_html(
                '<i class="bi bi-{}"></i>',
                obj.icon
            )
        return '-'
    icon_preview.short_description = 'Icon'

    def anzahl_ausfuehrungen(self, obj):
        """Anzahl Ausführungen dieses Services."""
        return obj.ausfuehrungen.count()
    anzahl_ausfuehrungen.short_description = 'Ausführungen'


@admin.register(ServiceAusfuehrung)
class ServiceAusfuehrungAdmin(admin.ModelAdmin):
    """Admin für Service-Ausführungen."""
    list_display = [
        'id',
        'service',
        'ausgefuehrt_von',
        'erstellt_am',
        'erfolgreich_icon',
        'dauer_sekunden',
        'workflow_link'
    ]
    list_filter = ['erfolgreich', 'service', 'erstellt_am']
    search_fields = ['service__name', 'ausgefuehrt_von__username', 'fehlermeldung']
    readonly_fields = [
        'service',
        'ausgefuehrt_von',
        'workflow_instanz',
        'workflow_schritt',
        'erstellt_am',
        'erfolgreich',
        'fehlermeldung',
        'ergebnis_daten_formatiert',
        'dauer_sekunden'
    ]
    ordering = ['-erstellt_am']
    date_hierarchy = 'erstellt_am'

    fieldsets = (
        ('Service', {
            'fields': ('service', 'ausgefuehrt_von', 'erstellt_am')
        }),
        ('Kontext', {
            'fields': ('workflow_instanz', 'workflow_schritt')
        }),
        ('Ergebnis', {
            'fields': ('erfolgreich', 'fehlermeldung', 'ergebnis_daten_formatiert', 'dauer_sekunden')
        }),
    )

    def erfolgreich_icon(self, obj):
        """Zeigt Erfolgs-Icon."""
        if obj.erfolgreich:
            return format_html(
                '<span style="color: green; font-size: 18px;">✓</span>'
            )
        return format_html(
            '<span style="color: red; font-size: 18px;">✗</span>'
        )
    erfolgreich_icon.short_description = 'Status'

    def workflow_link(self, obj):
        """Link zum Workflow."""
        if obj.workflow_instanz:
            return format_html(
                '<a href="/admin/workflows/workflowinstanz/{}/change/">{}</a>',
                obj.workflow_instanz.id,
                obj.workflow_instanz
            )
        return '-'
    workflow_link.short_description = 'Workflow'

    def ergebnis_daten_formatiert(self, obj):
        """Formatierte Anzeige der Ergebnis-Daten."""
        if obj.ergebnis_daten:
            import json
            return format_html(
                '<pre style="max-width: 600px; overflow: auto;">{}</pre>',
                json.dumps(obj.ergebnis_daten, indent=2, ensure_ascii=False)
            )
        return '-'
    ergebnis_daten_formatiert.short_description = 'Ergebnis-Daten'


@admin.register(Dokument)
class DokumentAdmin(admin.ModelAdmin):
    """Admin für Dokumente (DMS)."""
    list_display = [
        'titel',
        'dokument_typ',
        'dateiname_kurz',
        'dateigroesse_mb_display',
        'erstellt_am',
        'hochgeladen_von',
        'download_link'
    ]
    list_filter = ['dokument_typ', 'erstellt_am', 'hochgeladen_von']
    search_fields = ['titel', 'beschreibung', 'tags', 'dateiname']
    readonly_fields = [
        'dateiname',
        'dateityp',
        'dateigroesse',
        'dateigroesse_mb_display',
        'hochgeladen_von',
        'generiert_von_service',
        'erstellt_am',
        'aktualisiert_am',
        'download_link'
    ]
    ordering = ['-erstellt_am']
    date_hierarchy = 'erstellt_am'

    fieldsets = (
        ('Metadaten', {
            'fields': ('titel', 'beschreibung', 'dokument_typ', 'tags')
        }),
        ('Datei', {
            'fields': (
                'datei',
                'dateiname',
                'dateityp',
                'dateigroesse',
                'dateigroesse_mb_display',
                'download_link'
            )
        }),
        ('Herkunft', {
            'fields': ('hochgeladen_von', 'generiert_von_service')
        }),
        ('Verknüpfungen', {
            'fields': ('workflow_instanz', 'notar', 'anwaerter')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def dateiname_kurz(self, obj):
        """Gekürzter Dateiname."""
        if len(obj.dateiname) > 30:
            return obj.dateiname[:27] + '...'
        return obj.dateiname
    dateiname_kurz.short_description = 'Dateiname'

    def dateigroesse_mb_display(self, obj):
        """Dateigröße in MB."""
        return f"{obj.dateigroesse_mb()} MB"
    dateigroesse_mb_display.short_description = 'Größe'

    def download_link(self, obj):
        """Download-Link für Datei."""
        if obj.datei:
            return format_html(
                '<a href="{}" target="_blank" class="button">Datei öffnen</a>',
                obj.datei.url
            )
        return '-'
    download_link.short_description = 'Download'
