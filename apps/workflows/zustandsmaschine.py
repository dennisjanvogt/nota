"""
Workflow-Zustandsmaschine.

State Machine für Workflow-Übergänge und Schritt-Verwaltung.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    WorkflowInstanz,
    WorkflowSchrittInstanz,
    WorkflowSchritt
)


class WorkflowZustandsmaschine:
    """
    State Machine für Workflow-Verwaltung.

    Verwaltet Übergänge zwischen Workflow-Schritten und Status-Updates.
    """

    def __init__(self, workflow_instanz):
        """
        Initialisiert die Zustandsmaschine.

        Args:
            workflow_instanz (WorkflowInstanz): Die zu verwaltende Workflow-Instanz
        """
        self.workflow_instanz = workflow_instanz
        self.workflow_typ = workflow_instanz.workflow_typ

    @transaction.atomic
    def workflow_starten(self):
        """
        Startet den Workflow.

        Erstellt alle Schritt-Instanzen und aktiviert den ersten Schritt.

        Returns:
            WorkflowInstanz: Die gestartete Workflow-Instanz

        Raises:
            ValidationError: Wenn Workflow bereits gestartet ist
        """
        if self.workflow_instanz.status != 'entwurf':
            raise ValidationError(
                f'Workflow kann nur im Status "Entwurf" gestartet werden! '
                f'Aktueller Status: {self.workflow_instanz.get_status_display()}'
            )

        # Hole alle Schritte des Workflow-Typs
        schritte = self.workflow_typ.schritte.all().order_by('reihenfolge')

        if not schritte.exists():
            raise ValidationError(
                f'Workflow-Typ "{self.workflow_typ.name}" hat keine Schritte definiert!'
            )

        # Erstelle Schritt-Instanzen für alle Schritte
        for schritt in schritte:
            WorkflowSchrittInstanz.objects.create(
                workflow_instanz=self.workflow_instanz,
                workflow_schritt=schritt,
                status='ausstehend'
            )

        # Aktiviere ersten Schritt
        erster_schritt = self.workflow_instanz.schritt_instanzen.first()
        if erster_schritt:
            erster_schritt.status = 'in_bearbeitung'
            erster_schritt.gestartet_am = timezone.now()
            erster_schritt.save()

        # Update Workflow-Status
        self.workflow_instanz.status = 'aktiv'
        self.workflow_instanz.gestartet_am = timezone.now()
        self.workflow_instanz.save()

        return self.workflow_instanz

    @transaction.atomic
    def schritt_abschliessen(self, schritt_instanz, notizen=''):
        """
        Schließt einen Schritt ab und aktiviert den nächsten.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die abzuschließende Schritt-Instanz
            notizen (str, optional): Notizen zum Abschluss. Defaults to ''.

        Returns:
            WorkflowSchrittInstanz: Die nächste aktive Schritt-Instanz (oder None)

        Raises:
            ValidationError: Wenn Schritt nicht abgeschlossen werden kann
        """
        if schritt_instanz.status not in ['in_bearbeitung', 'ausstehend']:
            raise ValidationError(
                f'Schritt kann nicht abgeschlossen werden! '
                f'Status: {schritt_instanz.get_status_display()}'
            )

        if schritt_instanz.workflow_instanz != self.workflow_instanz:
            raise ValidationError(
                'Schritt gehört nicht zu dieser Workflow-Instanz!'
            )

        # Schritt abschließen
        schritt_instanz.status = 'abgeschlossen'
        schritt_instanz.abgeschlossen_am = timezone.now()
        if notizen:
            schritt_instanz.notizen = notizen
        schritt_instanz.save()

        # Nächsten Schritt ermitteln
        naechster_schritt = self._naechsten_schritt_ermitteln(schritt_instanz)

        # Nächsten Schritt aktivieren (falls vorhanden)
        if naechster_schritt:
            naechster_schritt.status = 'in_bearbeitung'
            naechster_schritt.gestartet_am = timezone.now()
            naechster_schritt.save()
        else:
            # Kein nächster Schritt -> Workflow abschließen prüfen
            self._workflow_abschluss_pruefen()

        return naechster_schritt

    @transaction.atomic
    def schritt_ueberspringen(self, schritt_instanz, grund=''):
        """
        Überspringt einen Schritt (nur bei optionalen Schritten).

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die zu überspringende Schritt-Instanz
            grund (str, optional): Grund für das Überspringen. Defaults to ''.

        Returns:
            WorkflowSchrittInstanz: Die nächste aktive Schritt-Instanz (oder None)

        Raises:
            ValidationError: Wenn Schritt nicht übersprungen werden kann
        """
        if not schritt_instanz.workflow_schritt.ist_optional:
            raise ValidationError(
                f'Schritt "{schritt_instanz.workflow_schritt.name}" ist nicht optional '
                f'und kann nicht übersprungen werden!'
            )

        if schritt_instanz.status not in ['in_bearbeitung', 'ausstehend']:
            raise ValidationError(
                f'Schritt kann nicht übersprungen werden! '
                f'Status: {schritt_instanz.get_status_display()}'
            )

        # Schritt überspringen
        schritt_instanz.status = 'uebersprungen'
        schritt_instanz.abgeschlossen_am = timezone.now()
        if grund:
            schritt_instanz.notizen = f'Übersprungen: {grund}'
        schritt_instanz.save()

        # Nächsten Schritt ermitteln und aktivieren
        naechster_schritt = self._naechsten_schritt_ermitteln(schritt_instanz)
        if naechster_schritt:
            naechster_schritt.status = 'in_bearbeitung'
            naechster_schritt.gestartet_am = timezone.now()
            naechster_schritt.save()
        else:
            self._workflow_abschluss_pruefen()

        return naechster_schritt

    @transaction.atomic
    def schritt_fehlschlagen_lassen(self, schritt_instanz, fehler_beschreibung):
        """
        Markiert einen Schritt als fehlgeschlagen.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die fehlgeschlagene Schritt-Instanz
            fehler_beschreibung (str): Beschreibung des Fehlers

        Raises:
            ValidationError: Wenn Schritt nicht fehlschlagen kann
        """
        if schritt_instanz.status not in ['in_bearbeitung', 'ausstehend']:
            raise ValidationError(
                f'Schritt kann nicht als fehlgeschlagen markiert werden! '
                f'Status: {schritt_instanz.get_status_display()}'
            )

        schritt_instanz.status = 'fehlgeschlagen'
        schritt_instanz.abgeschlossen_am = timezone.now()
        schritt_instanz.notizen = f'Fehlgeschlagen: {fehler_beschreibung}'
        schritt_instanz.save()

        # Workflow bleibt aktiv, Schritt kann neu gestartet werden

    @transaction.atomic
    def schritt_neu_starten(self, schritt_instanz):
        """
        Startet einen fehlgeschlagenen Schritt neu.

        Args:
            schritt_instanz (WorkflowSchrittInstanz): Die neu zu startende Schritt-Instanz

        Raises:
            ValidationError: Wenn Schritt nicht neu gestartet werden kann
        """
        if schritt_instanz.status != 'fehlgeschlagen':
            raise ValidationError(
                'Nur fehlgeschlagene Schritte können neu gestartet werden!'
            )

        schritt_instanz.status = 'in_bearbeitung'
        schritt_instanz.gestartet_am = timezone.now()
        schritt_instanz.abgeschlossen_am = None
        schritt_instanz.save()

    @transaction.atomic
    def workflow_abbrechen(self, grund=''):
        """
        Bricht den Workflow ab.

        Args:
            grund (str, optional): Grund für den Abbruch. Defaults to ''.

        Raises:
            ValidationError: Wenn Workflow nicht abgebrochen werden kann
        """
        if self.workflow_instanz.status == 'abgeschlossen':
            raise ValidationError('Abgeschlossene Workflows können nicht abgebrochen werden!')

        self.workflow_instanz.status = 'abgebrochen'
        self.workflow_instanz.abgeschlossen_am = timezone.now()
        if grund:
            self.workflow_instanz.notizen += f'\n\nAbgebrochen: {grund}'
        self.workflow_instanz.save()

        # Alle laufenden Schritte abbrechen
        self.workflow_instanz.schritt_instanzen.filter(
            status='in_bearbeitung'
        ).update(status='fehlgeschlagen', abgeschlossen_am=timezone.now())

    def aktuelle_schritte_holen(self):
        """
        Liefert alle aktuell aktiven Schritte.

        Returns:
            QuerySet: Aktive Schritt-Instanzen
        """
        return self.workflow_instanz.schritt_instanzen.filter(
            status='in_bearbeitung'
        )

    def uebergang_moeglich(self, von_schritt, zu_schritt):
        """
        Prüft, ob ein Übergang zwischen zwei Schritten möglich ist.

        Args:
            von_schritt (WorkflowSchritt): Start-Schritt
            zu_schritt (WorkflowSchritt): Ziel-Schritt

        Returns:
            bool: True wenn Übergang möglich, sonst False
        """
        # Prüfe explizite Übergänge
        explizite_uebergaenge = von_schritt.uebergaenge_von.filter(
            zu_schritt=zu_schritt
        )
        if explizite_uebergaenge.exists():
            return True

        # Wenn keine expliziten Übergänge definiert sind, verwende Reihenfolge
        if not von_schritt.uebergaenge_von.exists():
            return zu_schritt.reihenfolge == von_schritt.reihenfolge + 1

        return False

    def _naechsten_schritt_ermitteln(self, aktueller_schritt):
        """
        Ermittelt den nächsten Schritt nach dem aktuellen.

        Args:
            aktueller_schritt (WorkflowSchrittInstanz): Der aktuelle Schritt

        Returns:
            WorkflowSchrittInstanz: Der nächste Schritt (oder None)
        """
        workflow_schritt = aktueller_schritt.workflow_schritt

        # Prüfe explizite Übergänge
        explizite_uebergaenge = workflow_schritt.uebergaenge_von.all()
        if explizite_uebergaenge.exists():
            # Nimm den ersten erlaubten Übergang
            naechster_workflow_schritt = explizite_uebergaenge.first().zu_schritt
            return self.workflow_instanz.schritt_instanzen.get(
                workflow_schritt=naechster_workflow_schritt
            )

        # Keine expliziten Übergänge -> verwende Reihenfolge
        naechste_reihenfolge = workflow_schritt.reihenfolge + 1
        try:
            naechster_workflow_schritt = WorkflowSchritt.objects.get(
                workflow_typ=self.workflow_typ,
                reihenfolge=naechste_reihenfolge
            )
            return self.workflow_instanz.schritt_instanzen.get(
                workflow_schritt=naechster_workflow_schritt
            )
        except WorkflowSchritt.DoesNotExist:
            # Kein nächster Schritt vorhanden
            return None

    def _workflow_abschluss_pruefen(self):
        """
        Prüft, ob der Workflow abgeschlossen werden kann.

        Schließt den Workflow ab, wenn alle Schritte abgeschlossen/übersprungen sind.
        """
        alle_schritte = self.workflow_instanz.schritt_instanzen.all()
        abgeschlossene_schritte = alle_schritte.filter(
            status__in=['abgeschlossen', 'uebersprungen']
        )

        if alle_schritte.count() == abgeschlossene_schritte.count():
            # Alle Schritte sind abgeschlossen -> Workflow abschließen
            self.workflow_instanz.status = 'abgeschlossen'
            self.workflow_instanz.abgeschlossen_am = timezone.now()
            self.workflow_instanz.save()

    def statistik_holen(self):
        """
        Liefert Statistiken über den Workflow-Fortschritt.

        Returns:
            dict: Statistiken mit Schritt-Zählungen und Fortschritt
        """
        alle_schritte = self.workflow_instanz.schritt_instanzen.all()

        statistik = {
            'gesamt_schritte': alle_schritte.count(),
            'abgeschlossen': alle_schritte.filter(status='abgeschlossen').count(),
            'in_bearbeitung': alle_schritte.filter(status='in_bearbeitung').count(),
            'ausstehend': alle_schritte.filter(status='ausstehend').count(),
            'uebersprungen': alle_schritte.filter(status='uebersprungen').count(),
            'fehlgeschlagen': alle_schritte.filter(status='fehlgeschlagen').count(),
            'fortschritt_prozent': self.workflow_instanz.fortschritt_prozent()
        }

        return statistik
