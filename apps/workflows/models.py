"""
Models für Workflow-System.

Dynamisches Workflow-System für Kammer-Prozesse wie Bestellungsprozess.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.kern.models import ZeitstempelModel
from apps.personen.models import NotarAnwaerter


class WorkflowTyp(ZeitstempelModel):
    """
    Definition eines Workflow-Typs (Template).

    Beispiel: "Bestellung Notar-Anwärter zum Notar"
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Name',
        help_text='Name des Workflow-Typs'
    )
    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung',
        help_text='Detaillierte Beschreibung des Workflows'
    )
    ist_aktiv = models.BooleanField(
        default=True,
        verbose_name='Ist aktiv',
        help_text='Kann dieser Workflow-Typ für neue Instanzen verwendet werden?'
    )
    erlaube_parallele_schritte = models.BooleanField(
        default=False,
        verbose_name='Erlaube parallele Schritte',
        help_text='Können mehrere Schritte gleichzeitig aktiv sein?'
    )
    erfordert_sequentielle_abarbeitung = models.BooleanField(
        default=True,
        verbose_name='Erfordert sequentielle Abarbeitung',
        help_text='Müssen Schritte in fester Reihenfolge abgearbeitet werden?'
    )

    class Meta:
        verbose_name = 'Workflow-Typ'
        verbose_name_plural = 'Workflow-Typen'
        ordering = ['name']

    def __str__(self):
        return self.name

    def schritte_anzahl(self):
        """Anzahl der Schritte in diesem Workflow-Typ."""
        return self.schritte.count()


class WorkflowSchritt(ZeitstempelModel):
    """
    Ein Schritt innerhalb eines Workflow-Typs.

    Beispiel: "Antrag prüfen", "Dokumente anfordern", "Präsidium vorlegen"
    """

    ROLLEN_CHOICES = [
        ('sachbearbeiter', 'Sachbearbeiter'),
        ('leitung', 'Leitung'),
        ('admin', 'Administrator'),
    ]

    workflow_typ = models.ForeignKey(
        WorkflowTyp,
        on_delete=models.CASCADE,
        related_name='schritte',
        verbose_name='Workflow-Typ'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='Name des Schritts'
    )
    beschreibung = models.TextField(
        blank=True,
        verbose_name='Beschreibung',
        help_text='Was muss in diesem Schritt gemacht werden?'
    )
    reihenfolge = models.PositiveIntegerField(
        verbose_name='Reihenfolge',
        help_text='Position in der Schritt-Sequenz'
    )
    geschaetzte_dauer_tage = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Geschätzte Dauer (Tage)',
        help_text='Wie lange dauert dieser Schritt üblicherweise?'
    )
    standard_zustaendige_rolle = models.CharField(
        max_length=20,
        choices=ROLLEN_CHOICES,
        default='sachbearbeiter',
        verbose_name='Standard-zuständige Rolle',
        help_text='Welche Rolle ist üblicherweise für diesen Schritt zuständig?'
    )
    ist_optional = models.BooleanField(
        default=False,
        verbose_name='Ist optional',
        help_text='Kann dieser Schritt übersprungen werden?'
    )

    class Meta:
        verbose_name = 'Workflow-Schritt'
        verbose_name_plural = 'Workflow-Schritte'
        ordering = ['workflow_typ', 'reihenfolge']
        unique_together = [['workflow_typ', 'reihenfolge']]

    def __str__(self):
        return f"{self.workflow_typ.name} - Schritt {self.reihenfolge}: {self.name}"


class WorkflowSchrittUebergang(ZeitstempelModel):
    """
    Definiert erlaubte Übergänge zwischen Workflow-Schritten.

    Optional - wenn keine Übergänge definiert sind, wird die Reihenfolge verwendet.
    """

    von_schritt = models.ForeignKey(
        WorkflowSchritt,
        on_delete=models.CASCADE,
        related_name='uebergaenge_von',
        verbose_name='Von Schritt'
    )
    zu_schritt = models.ForeignKey(
        WorkflowSchritt,
        on_delete=models.CASCADE,
        related_name='uebergaenge_zu',
        verbose_name='Zu Schritt'
    )
    bedingung = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Bedingung',
        help_text='Optionale Bedingung für diesen Übergang'
    )

    class Meta:
        verbose_name = 'Workflow-Schritt-Übergang'
        verbose_name_plural = 'Workflow-Schritt-Übergänge'
        unique_together = [['von_schritt', 'zu_schritt']]

    def __str__(self):
        return f"{self.von_schritt.name} → {self.zu_schritt.name}"

    def clean(self):
        """Validierung: Übergänge müssen innerhalb desselben Workflow-Typs sein."""
        super().clean()
        if self.von_schritt.workflow_typ != self.zu_schritt.workflow_typ:
            raise ValidationError(
                'Übergänge müssen innerhalb desselben Workflow-Typs sein!'
            )


class WorkflowInstanz(ZeitstempelModel):
    """
    Konkrete Ausführung eines Workflows.

    Beispiel: "Bestellung Max Mustermann" (basierend auf Workflow-Typ "Bestellungsprozess")
    """

    STATUS_CHOICES = [
        ('entwurf', 'Entwurf'),
        ('aktiv', 'Aktiv'),
        ('abgeschlossen', 'Abgeschlossen'),
        ('abgebrochen', 'Abgebrochen'),
    ]

    workflow_typ = models.ForeignKey(
        WorkflowTyp,
        on_delete=models.PROTECT,
        related_name='instanzen',
        verbose_name='Workflow-Typ'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Name',
        help_text='Beschreibender Name für diese Workflow-Instanz'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='entwurf',
        verbose_name='Status'
    )
    erstellt_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='erstellte_workflows',
        verbose_name='Erstellt von'
    )
    gestartet_am = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Gestartet am'
    )
    abgeschlossen_am = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Abgeschlossen am'
    )
    faellig_am = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fällig am',
        help_text='Bis wann sollte dieser Workflow abgeschlossen sein?'
    )
    aktenzeichen = models.OneToOneField(
        'aktenzeichen.Aktenzeichen',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='workflow',
        verbose_name='Aktenzeichen'
    )
    betroffene_person = models.ForeignKey(
        NotarAnwaerter,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='workflows',
        verbose_name='Betroffene Person',
        help_text='Notar-Anwärter, der betroffen ist (z.B. bei Bestellungsprozess)'
    )
    notizen = models.TextField(
        blank=True,
        verbose_name='Notizen'
    )

    class Meta:
        verbose_name = 'Workflow-Instanz'
        verbose_name_plural = 'Workflow-Instanzen'
        ordering = ['-erstellt_am']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def fortschritt_prozent(self):
        """Berechnet den Fortschritt in Prozent."""
        alle_schritte = self.schritt_instanzen.count()
        if alle_schritte == 0:
            return 0
        abgeschlossene_schritte = self.schritt_instanzen.filter(
            status='abgeschlossen'
        ).count()
        return int((abgeschlossene_schritte / alle_schritte) * 100)

    def aktuelle_schritte(self):
        """Liefert alle aktuell aktiven Schritte."""
        return self.schritt_instanzen.filter(status='in_bearbeitung')


class WorkflowSchrittInstanz(ZeitstempelModel):
    """
    Konkrete Ausführung eines Workflow-Schritts.
    """

    STATUS_CHOICES = [
        ('ausstehend', 'Ausstehend'),
        ('in_bearbeitung', 'In Bearbeitung'),
        ('abgeschlossen', 'Abgeschlossen'),
        ('uebersprungen', 'Übersprungen'),
        ('fehlgeschlagen', 'Fehlgeschlagen'),
    ]

    workflow_instanz = models.ForeignKey(
        WorkflowInstanz,
        on_delete=models.CASCADE,
        related_name='schritt_instanzen',
        verbose_name='Workflow-Instanz'
    )
    workflow_schritt = models.ForeignKey(
        WorkflowSchritt,
        on_delete=models.PROTECT,
        related_name='instanzen',
        verbose_name='Workflow-Schritt'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ausstehend',
        verbose_name='Status'
    )
    zugewiesen_an = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zugewiesene_schritte',
        verbose_name='Zugewiesen an'
    )
    gestartet_am = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Gestartet am'
    )
    abgeschlossen_am = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Abgeschlossen am'
    )
    faellig_am = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fällig am'
    )
    notizen = models.TextField(
        blank=True,
        verbose_name='Notizen'
    )

    class Meta:
        verbose_name = 'Workflow-Schritt-Instanz'
        verbose_name_plural = 'Workflow-Schritt-Instanzen'
        ordering = ['workflow_schritt__reihenfolge']
        unique_together = [['workflow_instanz', 'workflow_schritt']]

    def __str__(self):
        return f"{self.workflow_instanz.name} - {self.workflow_schritt.name} ({self.get_status_display()})"


class WorkflowKommentar(ZeitstempelModel):
    """
    Kommentare zu Workflows und Workflow-Schritten.
    """

    workflow_instanz = models.ForeignKey(
        WorkflowInstanz,
        on_delete=models.CASCADE,
        related_name='kommentare',
        verbose_name='Workflow-Instanz'
    )
    schritt_instanz = models.ForeignKey(
        WorkflowSchrittInstanz,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='kommentare',
        verbose_name='Schritt-Instanz',
        help_text='Optional: Bezieht sich der Kommentar auf einen bestimmten Schritt?'
    )
    benutzer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='workflow_kommentare',
        verbose_name='Benutzer'
    )
    kommentar = models.TextField(
        verbose_name='Kommentar'
    )

    class Meta:
        verbose_name = 'Workflow-Kommentar'
        verbose_name_plural = 'Workflow-Kommentare'
        ordering = ['-erstellt_am']

    def __str__(self):
        return f"Kommentar von {self.benutzer.username} am {self.erstellt_am.strftime('%d.%m.%Y %H:%M')}"
