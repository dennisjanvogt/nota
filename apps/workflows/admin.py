"""
Admin-Konfiguration für Workflow-System.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    WorkflowTyp,
    WorkflowSchritt,
    WorkflowInstanz,
    WorkflowSchrittInstanz
)


class WorkflowSchrittInline(admin.TabularInline):
    """Inline für Workflow-Schritte in WorkflowTyp."""
    model = WorkflowSchritt
    extra = 0
    fields = ['reihenfolge', 'name', 'beschreibung', 'ist_optional', 'service', 'email_vorlage']
    ordering = ['reihenfolge']


@admin.register(WorkflowTyp)
class WorkflowTypAdmin(admin.ModelAdmin):
    """Admin für Workflow-Typen."""

    list_display = [
        'name',
        'kuerzel',
        'schritte_anzahl',
        'instanzen_anzahl',
        'ist_aktiv',
        'erstellt_am'
    ]
    list_filter = ['ist_aktiv']
    search_fields = ['name', 'beschreibung', 'kuerzel']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    inlines = [WorkflowSchrittInline]

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('name', 'kuerzel', 'beschreibung', 'ist_aktiv')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def instanzen_anzahl(self, obj):
        """Zeigt Anzahl der Workflow-Instanzen."""
        anzahl = obj.instanzen.count()
        return format_html(
            '<strong>{}</strong>',
            anzahl
        )
    instanzen_anzahl.short_description = 'Instanzen'


@admin.register(WorkflowSchritt)
class WorkflowSchrittAdmin(admin.ModelAdmin):
    """Admin für Workflow-Schritte."""

    list_display = [
        'workflow_typ',
        'reihenfolge',
        'name',
        'ist_optional',
        'service_anzeige',
        'email_vorlage_anzeige'
    ]
    list_filter = ['workflow_typ', 'ist_optional', 'service']
    search_fields = ['name', 'beschreibung']
    ordering = ['workflow_typ', 'reihenfolge']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    inlines = []

    fieldsets = (
        ('Workflow-Zuordnung', {
            'fields': ('workflow_typ', 'reihenfolge')
        }),
        ('Schritt-Details', {
            'fields': ('name', 'beschreibung', 'ist_optional')
        }),
        ('Service-Integration', {
            'fields': ('service', 'email_vorlage'),
            'description': 'Verknüpfung mit Services und E-Mail-Vorlagen'
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def service_anzeige(self, obj):
        """Zeigt den verknüpften Service."""
        if obj.service:
            return format_html(
                '<i class="bi bi-{}"></i> {}',
                obj.service.icon,
                obj.service.name
            )
        return '-'
    service_anzeige.short_description = 'Service'

    def email_vorlage_anzeige(self, obj):
        """Zeigt die E-Mail-Vorlage."""
        if obj.email_vorlage:
            return obj.email_vorlage.name
        return '-'
    email_vorlage_anzeige.short_description = 'E-Mail-Vorlage'


class WorkflowSchrittInstanzInline(admin.TabularInline):
    """Inline für Schritt-Instanzen in Workflow-Instanz."""
    model = WorkflowSchrittInstanz
    extra = 0
    readonly_fields = ['workflow_schritt', 'status']
    fields = ['workflow_schritt', 'status', 'notizen']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Schritte können nicht manuell hinzugefügt werden."""
        return False



@admin.register(WorkflowInstanz)
class WorkflowInstanzAdmin(admin.ModelAdmin):
    """Admin für Workflow-Instanzen."""

    list_display = [
        'kennung',
        'name',
        'workflow_typ',
        'status_display',
        'fortschritt',
        'betroffene_personen_anzeige',
        'erstellt_von',
        'erstellt_am'
    ]
    list_filter = ['status', 'workflow_typ', 'erstellt_am']
    search_fields = ['name', 'kennung']
    readonly_fields = ['kennung', 'jahr', 'laufende_nummer', 'erstellt_am', 'aktualisiert_am', 'archiviert_am', 'fortschritt_anzeige']
    date_hierarchy = 'erstellt_am'
    inlines = [WorkflowSchrittInstanzInline]

    fieldsets = (
        ('Workflow-Informationen', {
            'fields': ('workflow_typ', 'name', 'status', 'fortschritt_anzeige')
        }),
        ('Kennungssystem', {
            'fields': ('kennung', 'jahr', 'laufende_nummer'),
            'classes': ('collapse',),
            'description': 'Automatisch generierte Kennung'
        }),
        ('Zuordnungen', {
            'fields': ('erstellt_von', 'betroffene_notare', 'betroffene_kandidaten')
        }),
        ('Notizen', {
            'fields': ('notizen',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am', 'archiviert_am'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Zeigt Status mit farbiger Badge."""
        farben = {
            'entwurf': '#6c757d',
            'aktiv': '#0d6efd',
            'archiviert': '#198754',
        }
        farbe = farben.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            farbe,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def fortschritt(self, obj):
        """Zeigt Fortschrittsbalken."""
        prozent = obj.fortschritt_prozent()
        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background: #0d6efd; color: white; text-align: center; '
            'padding: 2px; font-size: 10px; font-weight: bold;">{}</div>'
            '</div>',
            prozent,
            f'{prozent}%' if prozent > 0 else ''
        )
    fortschritt.short_description = 'Fortschritt'

    def betroffene_personen_anzeige(self, obj):
        """Zeigt alle betroffenen Personen (Notare + Kandidaten)."""
        personen = []
        for notar in obj.betroffene_notare.all():
            personen.append(f'🟠 {notar.get_voller_name()}')
        for kandidat in obj.betroffene_kandidaten.all():
            personen.append(f'🔵 {kandidat.get_voller_name()}')
        if not personen:
            return '-'
        return format_html('<br>'.join(personen))
    betroffene_personen_anzeige.short_description = 'Betroffene Personen'

    def fortschritt_anzeige(self, obj):
        """Zeigt ausführliche Fortschrittsanzeige."""
        prozent = obj.fortschritt_prozent()
        alle_schritte = obj.schritt_instanzen.count()
        abgeschlossen = obj.schritt_instanzen.filter(status='completed').count()

        return format_html(
            '<div style="margin-bottom: 10px;">'
            '<div style="width: 100%; background: #e9ecef; border-radius: 5px; overflow: hidden; height: 30px;">'
            '<div style="width: {}%; background: #0d6efd; color: white; text-align: center; '
            'line-height: 30px; font-weight: bold; transition: width 0.3s;">{}</div>'
            '</div>'
            '<div style="margin-top: 5px; color: #6c757d; font-size: 12px;">'
            '{} von {} Schritten abgeschlossen'
            '</div>'
            '</div>',
            prozent,
            f'{prozent}%',
            abgeschlossen,
            alle_schritte
        )
    fortschritt_anzeige.short_description = 'Fortschritt'


@admin.register(WorkflowSchrittInstanz)
class WorkflowSchrittInstanzAdmin(admin.ModelAdmin):
    """Admin für Workflow-Schritt-Instanzen."""

    list_display = [
        'workflow_instanz',
        'workflow_schritt',
        'status_display'
    ]
    list_filter = ['status', 'workflow_schritt__workflow_typ']
    search_fields = ['workflow_instanz__name', 'workflow_schritt__name']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    fieldsets = (
        ('Zuordnung', {
            'fields': ('workflow_instanz', 'workflow_schritt')
        }),
        ('Status', {
            'fields': ('status', 'notizen')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am')
        }),
    )

    def status_display(self, obj):
        """Zeigt Status mit farbiger Badge."""
        farben = {
            'pending': '#6c757d',
            'completed': '#198754',
        }
        farbe = farben.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            farbe,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


