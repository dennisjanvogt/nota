"""
Service-Layer für Workflow-Verwaltung.

Der WorkflowService bietet High-Level-Methoden für Workflow-Operationen.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    WorkflowTyp,
    WorkflowInstanz,
    WorkflowSchrittInstanz,
    WorkflowKommentar
)
from .zustandsmaschine import WorkflowZustandsmaschine
from apps.aktenzeichen.services import AktenzeichenService


class WorkflowService:
    """
    Service für Workflow-Verwaltung.

    Bietet High-Level-Methoden für Workflow-Operationen und
    integriert die Zustandsmaschine mit Aktenzeichen-Generierung.
    """

    @staticmethod
    @transaction.atomic
    def workflow_instanz_erstellen(
        workflow_typ_name,
        name,
        erstellt_von,
        betroffene_person=None,
        mit_aktenzeichen=True,
        aktenzeichen_praefix='ALL',
        aktenzeichen_kategorie='Allgemein',
        faellig_am=None,
        notizen=''
    ):
        """
        Erstellt eine neue Workflow-Instanz.

        Args:
            workflow_typ_name (str): Name des Workflow-Typs
            name (str): Name der Workflow-Instanz
            erstellt_von (KammerBenutzer): Benutzer, der den Workflow erstellt
            betroffene_person (NotarAnwaerter, optional): Betroffene Person. Defaults to None.
            mit_aktenzeichen (bool, optional): Aktenzeichen generieren? Defaults to True.
            aktenzeichen_praefix (str, optional): Präfix für Aktenzeichen. Defaults to 'ALL'.
            aktenzeichen_kategorie (str, optional): Kategorie für Aktenzeichen. Defaults to 'Allgemein'.
            faellig_am (date, optional): Fälligkeitsdatum. Defaults to None.
            notizen (str, optional): Notizen. Defaults to ''.

        Returns:
            WorkflowInstanz: Die erstellte Workflow-Instanz

        Raises:
            ValidationError: Wenn Workflow-Typ nicht existiert oder nicht aktiv ist
        """
        # Hole Workflow-Typ
        try:
            workflow_typ = WorkflowTyp.objects.get(name=workflow_typ_name)
        except WorkflowTyp.DoesNotExist:
            raise ValidationError(
                f'Workflow-Typ "{workflow_typ_name}" existiert nicht!'
            )

        if not workflow_typ.ist_aktiv:
            raise ValidationError(
                f'Workflow-Typ "{workflow_typ_name}" ist nicht aktiv!'
            )

        # Generiere optional Aktenzeichen
        aktenzeichen = None
        if mit_aktenzeichen:
            jahr = timezone.now().year
            aktenzeichen = AktenzeichenService.aktenzeichen_generieren(
                praefix=aktenzeichen_praefix,
                kategorie=aktenzeichen_kategorie,
                jahr=jahr,
                beschreibung=f'Workflow: {name}'
            )

        # Erstelle Workflow-Instanz
        workflow_instanz = WorkflowInstanz.objects.create(
            workflow_typ=workflow_typ,
            name=name,
            status='entwurf',
            erstellt_von=erstellt_von,
            aktenzeichen=aktenzeichen,
            betroffene_person=betroffene_person,
            faellig_am=faellig_am,
            notizen=notizen
        )

        return workflow_instanz

    @staticmethod
    @transaction.atomic
    def workflow_starten(workflow_instanz):
        """
        Startet einen Workflow.

        Args:
            workflow_instanz (WorkflowInstanz): Die zu startende Workflow-Instanz

        Returns:
            WorkflowInstanz: Die gestartete Workflow-Instanz

        Raises:
            ValidationError: Wenn Workflow nicht gestartet werden kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(workflow_instanz)
        return zustandsmaschine.workflow_starten()

    @staticmethod
    @transaction.atomic
    def schritt_abschliessen(schritt_instanz, notizen=''):
        """
        Schließt einen Workflow-Schritt ab.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die abzuschließende Schritt-Instanz
            notizen (str, optional): Notizen zum Abschluss. Defaults to ''.

        Returns:
            WorkflowSchrittInstanz: Die nächste aktive Schritt-Instanz (oder None)

        Raises:
            ValidationError: Wenn Schritt nicht abgeschlossen werden kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(schritt_instanz.workflow_instanz)
        return zustandsmaschine.schritt_abschliessen(schritt_instanz, notizen)

    @staticmethod
    @transaction.atomic
    def schritt_zuweisen(schritt_instanz, benutzer):
        """
        Weist einen Schritt einem Benutzer zu.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die zuzuweisende Schritt-Instanz
            benutzer (KammerBenutzer): Der zuständige Benutzer

        Returns:
            WorkflowSchrittInstanz: Die aktualisierte Schritt-Instanz

        Raises:
            ValidationError: Wenn Zuweisung nicht möglich ist
        """
        if schritt_instanz.status not in ['ausstehend', 'in_bearbeitung']:
            raise ValidationError(
                f'Schritt kann nicht zugewiesen werden! '
                f'Status: {schritt_instanz.get_status_display()}'
            )

        schritt_instanz.zugewiesen_an = benutzer
        schritt_instanz.save()

        return schritt_instanz

    @staticmethod
    @transaction.atomic
    def schritt_ueberspringen(schritt_instanz, grund=''):
        """
        Überspringt einen optionalen Schritt.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die zu überspringende Schritt-Instanz
            grund (str, optional): Grund für das Überspringen. Defaults to ''.

        Returns:
            WorkflowSchrittInstanz: Die nächste aktive Schritt-Instanz (oder None)

        Raises:
            ValidationError: Wenn Schritt nicht übersprungen werden kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(schritt_instanz.workflow_instanz)
        return zustandsmaschine.schritt_ueberspringen(schritt_instanz, grund)

    @staticmethod
    @transaction.atomic
    def schritt_fehlschlagen_lassen(schritt_instanz, fehler_beschreibung):
        """
        Markiert einen Schritt als fehlgeschlagen.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die fehlgeschlagene Schritt-Instanz
            fehler_beschreibung (str): Beschreibung des Fehlers

        Raises:
            ValidationError: Wenn Schritt nicht fehlschlagen kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(schritt_instanz.workflow_instanz)
        zustandsmaschine.schritt_fehlschlagen_lassen(schritt_instanz, fehler_beschreibung)

    @staticmethod
    @transaction.atomic
    def schritt_neu_starten(schritt_instanz):
        """
        Startet einen fehlgeschlagenen Schritt neu.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die neu zu startende Schritt-Instanz

        Raises:
            ValidationError: Wenn Schritt nicht neu gestartet werden kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(schritt_instanz.workflow_instanz)
        zustandsmaschine.schritt_neu_starten(schritt_instanz)

    @staticmethod
    @transaction.atomic
    def workflow_abbrechen(workflow_instanz, grund=''):
        """
        Bricht einen Workflow ab.

        Args:
            workflow_instanz (WorkflowInstanz): Die abzubrechende Workflow-Instanz
            grund (str, optional): Grund für den Abbruch. Defaults to ''.

        Raises:
            ValidationError: Wenn Workflow nicht abgebrochen werden kann
        """
        zustandsmaschine = WorkflowZustandsmaschine(workflow_instanz)
        zustandsmaschine.workflow_abbrechen(grund)

    @staticmethod
    @transaction.atomic
    def kommentar_hinzufuegen(
        workflow_instanz,
        benutzer,
        kommentar,
        schritt_instanz=None
    ):
        """
        Fügt einen Kommentar zu einem Workflow hinzu.

        Args:
            workflow_instanz (WorkflowInstanz): Die Workflow-Instanz
            benutzer (KammerBenutzer): Der kommentierende Benutzer
            kommentar (str): Der Kommentar-Text
            schritt_instanz (WorkflowSchrittInstanz, optional): Bezug zu Schritt. Defaults to None.

        Returns:
            WorkflowKommentar: Der erstellte Kommentar
        """
        return WorkflowKommentar.objects.create(
            workflow_instanz=workflow_instanz,
            schritt_instanz=schritt_instanz,
            benutzer=benutzer,
            kommentar=kommentar
        )

    @staticmethod
    def aktuelle_schritte_holen(workflow_instanz):
        """
        Liefert alle aktuell aktiven Schritte eines Workflows.

        Args:
            workflow_instanz (WorkflowInstanz): Die Workflow-Instanz

        Returns:
            QuerySet: Aktive Schritt-Instanzen
        """
        zustandsmaschine = WorkflowZustandsmaschine(workflow_instanz)
        return zustandsmaschine.aktuelle_schritte_holen()

    @staticmethod
    def statistik_holen(workflow_instanz):
        """
        Liefert Statistiken über einen Workflow.

        Args:
            workflow_instanz (WorkflowInstanz): Die Workflow-Instanz

        Returns:
            dict: Statistiken mit Schritt-Zählungen und Fortschritt
        """
        zustandsmaschine = WorkflowZustandsmaschine(workflow_instanz)
        return zustandsmaschine.statistik_holen()

    @staticmethod
    def meine_aufgaben_holen(benutzer):
        """
        Liefert alle offenen Aufgaben (Schritte) für einen Benutzer.

        Args:
            benutzer (KammerBenutzer): Der Benutzer

        Returns:
            QuerySet: Zugewiesene Schritt-Instanzen in Bearbeitung
        """
        return WorkflowSchrittInstanz.objects.filter(
            zugewiesen_an=benutzer,
            status='in_bearbeitung'
        ).select_related(
            'workflow_instanz',
            'workflow_schritt'
        ).order_by('faellig_am', 'erstellt_am')

    @staticmethod
    def offene_workflows_holen():
        """
        Liefert alle offenen (aktiven) Workflows.

        Returns:
            QuerySet: Aktive Workflow-Instanzen
        """
        return WorkflowInstanz.objects.filter(
            status='aktiv'
        ).select_related(
            'workflow_typ',
            'erstellt_von',
            'aktenzeichen'
        ).order_by('-erstellt_am')

    @staticmethod
    def workflow_suchen(suchbegriff):
        """
        Sucht Workflows nach Name oder Aktenzeichen.

        Args:
            suchbegriff (str): Suchbegriff

        Returns:
            QuerySet: Gefundene Workflow-Instanzen
        """
        return WorkflowInstanz.objects.filter(
            name__icontains=suchbegriff
        ) | WorkflowInstanz.objects.filter(
            aktenzeichen__vollstaendige_nummer__icontains=suchbegriff
        )

    @staticmethod
    @transaction.atomic
    def bestellungsprozess_starten(
        notar_anwaerter,
        erstellt_von,
        notarstelle=None,
        faellig_am=None
    ):
        """
        Startet einen Bestellungsprozess für einen Notar-Anwärter.

        Convenience-Methode für den wichtigsten Workflow.

        Args:
            notar_anwaerter (NotarAnwaerter): Der zu bestellende Notar-Anwärter
            erstellt_von (KammerBenutzer): Benutzer, der den Prozess startet
            notarstelle (Notarstelle, optional): Zuzuweisende Notarstelle. Defaults to None.
            faellig_am (date, optional): Fälligkeitsdatum. Defaults to None.

        Returns:
            WorkflowInstanz: Die erstellte und gestartete Workflow-Instanz

        Raises:
            ValidationError: Wenn Bestellungsprozess nicht gestartet werden kann
        """
        # Erstelle Workflow-Name
        name = f'Bestellung {notar_anwaerter.vorname} {notar_anwaerter.nachname}'

        # Erstelle Workflow-Instanz mit Aktenzeichen
        workflow_instanz = WorkflowService.workflow_instanz_erstellen(
            workflow_typ_name='Bestellungsprozess',
            name=name,
            erstellt_von=erstellt_von,
            betroffene_person=notar_anwaerter,
            mit_aktenzeichen=True,
            aktenzeichen_praefix='BES',
            aktenzeichen_kategorie='Bestellung',
            faellig_am=faellig_am,
            notizen=f'Bestellungsprozess für {notar_anwaerter.vorname} {notar_anwaerter.nachname}'
        )

        # Starte Workflow
        workflow_instanz = WorkflowService.workflow_starten(workflow_instanz)

        return workflow_instanz
