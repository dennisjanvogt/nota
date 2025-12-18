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
    WorkflowSchrittUebergang,
    WorkflowInstanz,
    WorkflowSchrittInstanz,
    WorkflowKommentar
)


class WorkflowSchrittInline(admin.TabularInline):
    """Inline für Workflow-Schritte in WorkflowTyp."""
    model = WorkflowSchritt
    extra = 0
    fields = ['reihenfolge', 'name', 'beschreibung', 'geschaetzte_dauer_tage',
              'standard_zustaendige_rolle', 'ist_optional']
    ordering = ['reihenfolge']


class WorkflowSchrittUebergangInline(admin.TabularInline):
    """Inline für Übergänge in WorkflowSchritt."""
    model = WorkflowSchrittUebergang
    fk_name = 'von_schritt'
    extra = 0
    fields = ['zu_schritt', 'bedingung']


@admin.register(WorkflowTyp)
class WorkflowTypAdmin(admin.ModelAdmin):
    """Admin für Workflow-Typen."""

    list_display = [
        'name',
        'schritte_anzahl',
        'instanzen_anzahl',
        'ist_aktiv',
        'erfordert_sequentielle_abarbeitung',
        'erstellt_am'
    ]
    list_filter = ['ist_aktiv', 'erlaube_parallele_schritte', 'erfordert_sequentielle_abarbeitung']
    search_fields = ['name', 'beschreibung']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    inlines = [WorkflowSchrittInline]

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('name', 'beschreibung', 'ist_aktiv')
        }),
        ('Workflow-Konfiguration', {
            'fields': ('erlaube_parallele_schritte', 'erfordert_sequentielle_abarbeitung')
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
        'standard_zustaendige_rolle',
        'geschaetzte_dauer_tage',
        'ist_optional'
    ]
    list_filter = ['workflow_typ', 'standard_zustaendige_rolle', 'ist_optional']
    search_fields = ['name', 'beschreibung']
    ordering = ['workflow_typ', 'reihenfolge']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    inlines = [WorkflowSchrittUebergangInline]

    fieldsets = (
        ('Workflow-Zuordnung', {
            'fields': ('workflow_typ', 'reihenfolge')
        }),
        ('Schritt-Details', {
            'fields': ('name', 'beschreibung', 'geschaetzte_dauer_tage',
                      'standard_zustaendige_rolle', 'ist_optional')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkflowSchrittUebergang)
class WorkflowSchrittUebergangAdmin(admin.ModelAdmin):
    """Admin für Workflow-Schritt-Übergänge."""

    list_display = [
        'workflow_typ_display',
        'von_schritt',
        'pfeil',
        'zu_schritt',
        'bedingung'
    ]
    list_filter = ['von_schritt__workflow_typ']
    search_fields = ['von_schritt__name', 'zu_schritt__name', 'bedingung']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']

    fieldsets = (
        ('Übergang', {
            'fields': ('von_schritt', 'zu_schritt', 'bedingung')
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def workflow_typ_display(self, obj):
        """Zeigt den Workflow-Typ des Übergangs."""
        return obj.von_schritt.workflow_typ.name
    workflow_typ_display.short_description = 'Workflow-Typ'

    def pfeil(self, obj):
        """Zeigt einen Pfeil für den Übergang."""
        return '→'
    pfeil.short_description = ''


class WorkflowSchrittInstanzInline(admin.TabularInline):
    """Inline für Schritt-Instanzen in Workflow-Instanz."""
    model = WorkflowSchrittInstanz
    extra = 0
    readonly_fields = ['workflow_schritt', 'status', 'zugewiesen_an',
                       'gestartet_am', 'abgeschlossen_am']
    fields = ['workflow_schritt', 'status', 'zugewiesen_an', 'faellig_am', 'notizen']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """Schritte können nicht manuell hinzugefügt werden."""
        return False


class WorkflowKommentarInline(admin.TabularInline):
    """Inline für Kommentare in Workflow-Instanz."""
    model = WorkflowKommentar
    extra = 1
    readonly_fields = ['benutzer', 'erstellt_am']
    fields = ['benutzer', 'schritt_instanz', 'kommentar', 'erstellt_am']

    def save_model(self, request, obj, form, change):
        """Setzt den Benutzer automatisch auf den aktuellen Benutzer."""
        if not obj.pk:
            obj.benutzer = request.user
        super().save_model(request, obj, form, change)


@admin.register(WorkflowInstanz)
class WorkflowInstanzAdmin(admin.ModelAdmin):
    """Admin für Workflow-Instanzen."""

    list_display = [
        'name',
        'workflow_typ',
        'status_display',
        'fortschritt',
        'aktenzeichen',
        'betroffene_person',
        'erstellt_von',
        'erstellt_am'
    ]
    list_filter = ['status', 'workflow_typ', 'erstellt_am']
    search_fields = ['name', 'aktenzeichen__vollstaendige_nummer',
                     'betroffene_person__vorname', 'betroffene_person__nachname']
    readonly_fields = ['erstellt_am', 'aktualisiert_am', 'gestartet_am',
                       'abgeschlossen_am', 'fortschritt_anzeige']
    date_hierarchy = 'erstellt_am'
    inlines = [WorkflowSchrittInstanzInline, WorkflowKommentarInline]

    fieldsets = (
        ('Workflow-Informationen', {
            'fields': ('workflow_typ', 'name', 'status', 'fortschritt_anzeige')
        }),
        ('Zuordnungen', {
            'fields': ('erstellt_von', 'aktenzeichen', 'betroffene_person')
        }),
        ('Termine', {
            'fields': ('faellig_am', 'gestartet_am', 'abgeschlossen_am')
        }),
        ('Notizen', {
            'fields': ('notizen',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):
        """Zeigt Status mit farbiger Badge."""
        farben = {
            'entwurf': '#6c757d',
            'aktiv': '#0d6efd',
            'abgeschlossen': '#198754',
            'abgebrochen': '#dc3545',
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

    def fortschritt_anzeige(self, obj):
        """Zeigt ausführliche Fortschrittsanzeige."""
        prozent = obj.fortschritt_prozent()
        alle_schritte = obj.schritt_instanzen.count()
        abgeschlossen = obj.schritt_instanzen.filter(status='abgeschlossen').count()

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
        'status_display',
        'zugewiesen_an',
        'faellig_am',
        'gestartet_am',
        'abgeschlossen_am'
    ]
    list_filter = ['status', 'workflow_schritt__workflow_typ', 'zugewiesen_an']
    search_fields = ['workflow_instanz__name', 'workflow_schritt__name',
                     'zugewiesen_an__username']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    date_hierarchy = 'gestartet_am'

    fieldsets = (
        ('Zuordnung', {
            'fields': ('workflow_instanz', 'workflow_schritt', 'zugewiesen_an')
        }),
        ('Status', {
            'fields': ('status', 'notizen')
        }),
        ('Zeitstempel', {
            'fields': ('faellig_am', 'gestartet_am', 'abgeschlossen_am',
                      'erstellt_am', 'aktualisiert_am')
        }),
    )

    def status_display(self, obj):
        """Zeigt Status mit farbiger Badge."""
        farben = {
            'ausstehend': '#6c757d',
            'in_bearbeitung': '#ffc107',
            'abgeschlossen': '#198754',
            'uebersprungen': '#0dcaf0',
            'fehlgeschlagen': '#dc3545',
        }
        farbe = farben.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            farbe,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(WorkflowKommentar)
class WorkflowKommentarAdmin(admin.ModelAdmin):
    """Admin für Workflow-Kommentare."""

    list_display = [
        'workflow_instanz',
        'benutzer',
        'kurzer_kommentar',
        'schritt_instanz',
        'erstellt_am'
    ]
    list_filter = ['workflow_instanz__workflow_typ', 'benutzer', 'erstellt_am']
    search_fields = ['workflow_instanz__name', 'benutzer__username', 'kommentar']
    readonly_fields = ['erstellt_am', 'aktualisiert_am']
    date_hierarchy = 'erstellt_am'

    fieldsets = (
        ('Zuordnung', {
            'fields': ('workflow_instanz', 'schritt_instanz', 'benutzer')
        }),
        ('Kommentar', {
            'fields': ('kommentar',)
        }),
        ('Zeitstempel', {
            'fields': ('erstellt_am', 'aktualisiert_am'),
            'classes': ('collapse',)
        }),
    )

    def kurzer_kommentar(self, obj):
        """Zeigt gekürzten Kommentar."""
        max_length = 100
        if len(obj.kommentar) > max_length:
            return obj.kommentar[:max_length] + '...'
        return obj.kommentar
    kurzer_kommentar.short_description = 'Kommentar'
