"""
Models für Service-System und Document Management System (DMS).
"""
from django.db import models
from django.conf import settings
from apps.kern.models import ZeitstempelModel, AktivModel


class ServiceKategorie(models.Model):
    """
    Kategorie für Services (z.B. Dokumenten-Management, E-Mail, Berichte).
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Name'
    )
    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Bootstrap Icon',
        help_text='z.B. "file-earmark-pdf", "envelope", "graph-up"'
    )
    reihenfolge = models.PositiveIntegerField(
        default=0,
        verbose_name='Reihenfolge'
    )

    class Meta:
        verbose_name = 'Service-Kategorie'
        verbose_name_plural = 'Service-Kategorien'
        ordering = ['reihenfolge', 'name']

    def __str__(self):
        return self.name


class ServiceDefinition(ZeitstempelModel, AktivModel):
    """
    Definition eines Services - verknüpft Code mit UI und Konfiguration.

    Jeder Service wird im Code registriert und hier in der DB konfiguriert.
    """
    # Identifikation
    service_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Service-ID',
        help_text='Eindeutige ID im Code (z.B. "stammblatt_pdf_einzeln")'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='Benutzerfreundlicher Name'
    )
    beschreibung = models.TextField(
        verbose_name='Beschreibung',
        help_text='Was macht dieser Service? Wann nutzt man ihn?'
    )

    # Kategorisierung
    kategorie = models.ForeignKey(
        ServiceKategorie,
        on_delete=models.PROTECT,
        related_name='services',
        verbose_name='Kategorie'
    )

    # UI-Integration
    icon = models.CharField(
        max_length=50,
        default='tools',
        verbose_name='Bootstrap Icon'
    )
    button_text = models.CharField(
        max_length=100,
        default='Service ausführen',
        verbose_name='Button-Text'
    )
    button_css_class = models.CharField(
        max_length=100,
        default='btn-primary',
        verbose_name='Button CSS-Klasse',
        help_text='z.B. "btn-primary", "btn-success", "btn-warning"'
    )

    # Berechtigungen
    erforderliche_rolle = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Erforderliche Rolle',
        help_text='Leer = alle; sonst z.B. "sachbearbeiter", "leitung"'
    )

    class Meta:
        verbose_name = 'Service-Definition'
        verbose_name_plural = 'Service-Definitionen'
        ordering = ['kategorie', 'name']

    def __str__(self):
        return f"{self.name} ({self.service_id})"

    def kann_benutzer_ausfuehren(self, benutzer):
        """Prüft ob Benutzer den Service ausführen darf."""
        if not self.ist_aktiv:
            return False
        if not self.erforderliche_rolle:
            return True
        return benutzer.rolle == self.erforderliche_rolle


class ServiceAusfuehrung(ZeitstempelModel):
    """
    Protokoll einer Service-Ausführung.

    Jedes Mal wenn ein Service ausgeführt wird, wird hier ein Eintrag erstellt.
    """
    service = models.ForeignKey(
        ServiceDefinition,
        on_delete=models.PROTECT,
        related_name='ausfuehrungen',
        verbose_name='Service'
    )
    ausgefuehrt_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='service_ausfuehrungen',
        verbose_name='Ausgeführt von'
    )

    # Kontext
    workflow_instanz = models.ForeignKey(
        'workflows.WorkflowInstanz',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_ausfuehrungen',
        verbose_name='Workflow-Instanz'
    )
    workflow_schritt = models.ForeignKey(
        'workflows.WorkflowSchrittInstanz',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_ausfuehrungen',
        verbose_name='Workflow-Schritt'
    )

    # Ergebnis
    erfolgreich = models.BooleanField(
        default=True,
        verbose_name='Erfolgreich'
    )
    fehlermeldung = models.TextField(
        blank=True,
        verbose_name='Fehlermeldung'
    )
    ergebnis_daten = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Ergebnis-Daten',
        help_text='JSON mit Rückgabewerten (z.B. generierte Datei-ID)'
    )

    # Performance
    dauer_sekunden = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='Dauer (Sekunden)'
    )

    class Meta:
        verbose_name = 'Service-Ausführung'
        verbose_name_plural = 'Service-Ausführungen'
        ordering = ['-erstellt_am']

    def __str__(self):
        status = "✓" if self.erfolgreich else "✗"
        return f"{status} {self.service.name} - {self.erstellt_am.strftime('%d.%m.%Y %H:%M')}"


class Dokument(ZeitstempelModel):
    """
    DMS - Document Management System.

    Zentrale Verwaltung aller hochgeladenen und generierten Dokumente.
    """
    DOKUMENT_TYP_CHOICES = [
        ('stammblatt', 'Stammblatt'),
        ('strafregisterauszug', 'Strafregisterauszug'),
        ('besetzungsvorschlag', 'Besetzungsvorschlag'),
        ('gutachten', 'Gutachten'),
        ('beschluss', 'Beschluss'),
        ('korrespondenz', 'Korrespondenz'),
        ('sonstiges', 'Sonstiges'),
    ]

    # Metadaten
    titel = models.CharField(
        max_length=200,
        verbose_name='Titel'
    )
    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung'
    )
    dokument_typ = models.CharField(
        max_length=50,
        choices=DOKUMENT_TYP_CHOICES,
        default='sonstiges',
        verbose_name='Dokumenten-Typ'
    )

    # Datei
    datei = models.FileField(
        upload_to='dokumente/%Y/%m/',
        verbose_name='Datei'
    )
    dateiname = models.CharField(
        max_length=255,
        verbose_name='Originaler Dateiname'
    )
    dateityp = models.CharField(
        max_length=50,
        verbose_name='Dateityp',
        help_text='MIME-Type (z.B. "application/pdf")'
    )
    dateigroesse = models.PositiveIntegerField(
        verbose_name='Dateigröße (Bytes)'
    )

    # Herkunft
    hochgeladen_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='hochgeladene_dokumente',
        verbose_name='Hochgeladen von'
    )
    generiert_von_service = models.ForeignKey(
        ServiceAusfuehrung,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generierte_dokumente',
        verbose_name='Generiert von Service'
    )

    # Verknüpfungen
    workflow_instanz = models.ForeignKey(
        'workflows.WorkflowInstanz',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dokumente',
        verbose_name='Workflow-Instanz'
    )
    notar = models.ForeignKey(
        'personen.Notar',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dokumente',
        verbose_name='Notar'
    )
    anwaerter = models.ForeignKey(
        'personen.NotarAnwaerter',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='dokumente',
        verbose_name='Notariatskandidat'
    )

    # Tags für flexible Suche
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Tags',
        help_text='Komma-getrennte Tags für Suche'
    )

    class Meta:
        verbose_name = 'Dokument'
        verbose_name_plural = 'Dokumente'
        ordering = ['-erstellt_am']
        indexes = [
            models.Index(fields=['workflow_instanz', 'dokument_typ']),
            models.Index(fields=['notar', 'dokument_typ']),
            models.Index(fields=['anwaerter', 'dokument_typ']),
        ]

    def __str__(self):
        return f"{self.titel} ({self.get_dokument_typ_display()})"

    def dateigroesse_mb(self):
        """Gibt Dateigröße in MB zurück."""
        return round(self.dateigroesse / (1024 * 1024), 2)
