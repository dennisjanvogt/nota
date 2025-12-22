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

    Beispiel: "Bestellung Notariatskandidat zum Notar"
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
    kuerzel = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Kürzel',
        help_text='Kürzel für Kennung (z.B. BES, BP, NOT)'
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
    ist_optional = models.BooleanField(
        default=False,
        verbose_name='Ist optional',
        help_text='Kann dieser Schritt übersprungen werden?'
    )

    # Service-Integration
    service = models.ForeignKey(
        'services.ServiceDefinition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_schritte',
        verbose_name='Verknüpfter Service',
        help_text='Service der bei diesem Schritt angeboten wird'
    )

    # E-Mail-Vorlagen-Integration
    email_vorlage = models.ForeignKey(
        'emails.EmailVorlage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_schritte',
        verbose_name='E-Mail-Vorlage',
        help_text='E-Mail-Vorlage die in diesem Schritt verwendet wird'
    )

    class Meta:
        verbose_name = 'Workflow-Schritt'
        verbose_name_plural = 'Workflow-Schritte'
        ordering = ['workflow_typ', 'reihenfolge']
        unique_together = [['workflow_typ', 'reihenfolge']]

    def __str__(self):
        return f"{self.workflow_typ.name} - Schritt {self.reihenfolge}: {self.name}"



class WorkflowInstanz(ZeitstempelModel):
    """
    Konkrete Ausführung eines Workflows.

    Beispiel: "Bestellung Max Mustermann" (basierend auf Workflow-Typ "Bestellungsprozess")
    """

    STATUS_CHOICES = [
        ('aktiv', 'Aktiv'),
        ('archiviert', 'Archiviert'),
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
        default='aktiv',
        verbose_name='Status'
    )
    erstellt_von = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='erstellte_workflows',
        verbose_name='Erstellt von'
    )
    archiviert_am = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Archiviert am'
    )
    fertigstellungsdatum = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fertigstellungsdatum',
        help_text='Geplantes Datum zur Fertigstellung des Workflows'
    )
    # Betroffene Personen (allgemein für alle Workflows)
    betroffene_notare = models.ManyToManyField(
        'personen.Notar',
        blank=True,
        related_name='workflows_als_betroffener',
        verbose_name='Betroffene Notare',
        help_text='Notare, die von diesem Workflow betroffen sind'
    )
    betroffene_kandidaten = models.ManyToManyField(
        'personen.NotarAnwaerter',
        blank=True,
        related_name='workflows_als_betroffener',
        verbose_name='Betroffene Kandidaten',
        help_text='Notariatskandidaten, die von diesem Workflow betroffen sind'
    )
    notizen = models.TextField(
        blank=True,
        verbose_name='Notizen'
    )

    # Kennungssystem
    kennung = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name='Kennung',
        help_text='Eindeutige Kennung (z.B. 2025-BES-001)'
    )
    jahr = models.PositiveIntegerField(
        default=2025,
        verbose_name='Jahr',
        help_text='Jahr für Kennungssystem'
    )
    laufende_nummer = models.PositiveIntegerField(
        default=0,
        verbose_name='Laufende Nummer',
        help_text='Laufende Nummer innerhalb Jahr und Typ'
    )

    # Besetzungsverfahren-spezifisch
    referenten = models.ManyToManyField(
        'personen.Notar',
        blank=True,
        related_name='workflows_als_referent',
        verbose_name='Referenten',
        help_text='Notare die als Referenten am Workflow beteiligt sind'
    )
    bewerber = models.ManyToManyField(
        'personen.NotarAnwaerter',
        blank=True,
        related_name='workflows_als_bewerber',
        verbose_name='Bewerber',
        help_text='Kandidat die sich um die Stelle bewerben'
    )

    class Meta:
        verbose_name = 'Workflow-Instanz'
        verbose_name_plural = 'Workflow-Instanzen'
        ordering = ['-erstellt_am']

    def save(self, *args, **kwargs):
        """Generiert automatisch Kennung beim ersten Speichern."""
        if not self.kennung and self.workflow_typ_id:
            self.kennung = self._generiere_kennung()
        super().save(*args, **kwargs)

    def _generiere_kennung(self):
        """
        Generiert eindeutige Kennung: JAHR-KUERZEL-NUMMER (z.B. 2025-BES-001).

        Die Kennung besteht aus:
        - Jahr (aktuelles Jahr)
        - Kürzel des Workflow-Typs
        - Laufende Nummer (automatisch hochgezählt für Jahr + Typ)
        """
        from django.utils import timezone
        from django.db.models import Max

        # Aktuelles Jahr setzen
        self.jahr = timezone.now().year

        # Kürzel vom WorkflowTyp holen
        kuerzel = self.workflow_typ.kuerzel
        if not kuerzel:
            raise ValidationError(
                f"WorkflowTyp '{self.workflow_typ.name}' hat kein Kürzel. "
                "Bitte zuerst ein Kürzel vergeben."
            )

        # Höchste laufende Nummer für dieses Jahr + Typ ermitteln
        letzte_nummer = WorkflowInstanz.objects.filter(
            workflow_typ=self.workflow_typ,
            jahr=self.jahr
        ).aggregate(max_nummer=Max('laufende_nummer'))['max_nummer'] or 0

        # Neue Nummer generieren
        self.laufende_nummer = letzte_nummer + 1

        # Kennung zusammensetzen (z.B. 2025-BES-001)
        return f"{self.jahr}-{kuerzel}-{self.laufende_nummer:03d}"

    def alle_betroffenen_personen(self):
        """Liefert alle betroffenen Personen (Notare + Kandidaten) als Liste mit Typ."""
        personen = []
        for notar in self.betroffene_notare.all():
            personen.append({
                'typ': 'notar',
                'id': notar.notar_id,
                'name': notar.get_voller_name(),
                'objekt': notar
            })
        for kandidat in self.betroffene_kandidaten.all():
            personen.append({
                'typ': 'kandidat',
                'id': kandidat.anwaerter_id,
                'name': kandidat.get_voller_name(),
                'objekt': kandidat
            })
        return personen

    @property
    def tage_bis_fertigstellung(self):
        """Berechnet Tage bis zum Fertigstellungsdatum."""
        if not self.fertigstellungsdatum:
            return None
        from django.utils import timezone
        heute = timezone.now().date()
        delta = self.fertigstellungsdatum - heute
        return delta.days

    @property
    def ist_ueberfaellig(self):
        """Prüft ob Workflow überfällig ist."""
        tage = self.tage_bis_fertigstellung
        return tage is not None and tage < 0

    @property
    def deadline_status(self):
        """Liefert Status der Deadline: 'ueberfaellig', '1_tag', '5_tage', 'mehr'."""
        tage = self.tage_bis_fertigstellung
        if tage is None:
            return None
        if tage < 0:
            return 'ueberfaellig'
        elif tage <= 1:
            return '1_tag'
        elif tage <= 5:
            return '5_tage'
        else:
            return 'mehr'

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def fortschritt_prozent(self):
        """Berechnet den Fortschritt in Prozent."""
        alle_schritte = self.schritt_instanzen.count()
        if alle_schritte == 0:
            return 0
        abgeschlossene_schritte = self.schritt_instanzen.filter(
            status='completed'
        ).count()
        return int((abgeschlossene_schritte / alle_schritte) * 100)

    def aktuelle_schritte(self):
        """Liefert alle aktuell offenen Schritte."""
        return self.schritt_instanzen.filter(status='pending')


class WorkflowSchrittInstanz(ZeitstempelModel):
    """
    Konkrete Ausführung eines Workflow-Schritts.
    """

    STATUS_CHOICES = [
        ('pending', 'Ausstehend'),
        ('completed', 'Abgeschlossen'),
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
        default='pending',
        verbose_name='Status'
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




