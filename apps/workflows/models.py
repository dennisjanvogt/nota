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
        ('entwurf', 'Entwurf'),
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
        default='entwurf',
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




