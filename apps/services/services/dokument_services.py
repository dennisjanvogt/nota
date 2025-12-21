"""
Dokument-Services für PDF-Generierung.

Benötigt: pip install reportlab
"""
from typing import Dict, Any, List
from django.core.files.base import ContentFile
from django.utils import timezone
from decimal import Decimal
import io
import logging

from apps.services.base import BaseService, service
from apps.services.models import Dokument
from apps.personen.models import NotarAnwaerter, Notar
from apps.notarstellen.models import Notarstelle

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab nicht installiert. PDF-Services nicht verfügbar.")


@service(
    kategorie='dokumente',
    icon='file-earmark-pdf',
    button_text='Stammblatt erstellen'
)
class StammblattPDFEinzelnService(BaseService):
    """
    Erstellt ein detailliertes Stammblatt-PDF für einen Notariatskandidat.

    **Parameter:**
    - anwaerter_id: ID des Anwärters (required)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    service_id = 'stammblatt_pdf_einzeln'
    name = 'Stammblatt-PDF erstellen (Einzeln)'
    beschreibung = """
    Erstellt ein detailliertes Stammblatt-PDF für einen Notariatskandidat.

    Das Stammblatt enthält:
    - Persönliche Daten des Anwärters
    - Zugelassen am / Wartezeit
    - Betreuender Notar mit Kontaktdaten
    - Notarstelle
    - Qualifikationen und Ausbildung

    **Parameter:**
    - anwaerter_id: ID des Anwärters
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "ReportLab ist nicht installiert. "
                "Bitte installieren: pip install reportlab"
            )

        anwaerter_id = self.hole_parameter('anwaerter_id', required=True)

        # Prüfen ob Kandidat existiert
        if not NotarAnwaerter.objects.filter(id=anwaerter_id).exists():
            raise ValueError(f"Notariatskandidat mit ID {anwaerter_id} nicht gefunden")

    def ausfuehren(self) -> Dict[str, Any]:
        """Erstellt das Stammblatt-PDF."""
        anwaerter_id = self.hole_parameter('anwaerter_id')
        anwaerter = NotarAnwaerter.objects.select_related(
            'betreuender_notar',
            'betreuender_notar__notarstelle'
        ).get(id=anwaerter_id)

        # PDF erstellen
        pdf_buffer = self._erstelle_stammblatt_pdf(anwaerter)

        # Dateiname generieren
        heute = timezone.now()
        dateiname = f"Stammblatt_{anwaerter.nachname}_{anwaerter.vorname}_{heute.strftime('%Y%m%d')}.pdf"

        # Dokument in DB speichern
        dokument = Dokument.objects.create(
            titel=f"Stammblatt {anwaerter.get_voller_name()}",
            beschreibung=f"Automatisch generiertes Stammblatt für {anwaerter.get_voller_name()}",
            dokument_typ='stammblatt',
            dateiname=dateiname,
            dateityp='application/pdf',
            dateigroesse=len(pdf_buffer.getvalue()),
            generiert_von_service=self._service_ausfuehrung,
            workflow_instanz=self.parameter.get('workflow_instanz'),
            anwaerter=anwaerter,
            tags=f"{anwaerter.nachname}, {anwaerter.vorname}, Stammblatt"
        )

        # PDF-Datei speichern
        dokument.datei.save(
            dateiname,
            ContentFile(pdf_buffer.getvalue()),
            save=True
        )

        logger.info(
            f"Stammblatt-PDF erstellt für {anwaerter.get_voller_name()} "
            f"(Dokument-ID: {dokument.id})"
        )

        return {
            'dokument_id': dokument.id,
            'dateiname': dateiname,
            'anwaerter_id': anwaerter.id,
            'anwaerter_name': anwaerter.get_voller_name(),
            'dateityp': 'application/pdf',
            'dateigroesse_mb': dokument.dateigroesse_mb()
        }

    def _erstelle_stammblatt_pdf(self, anwaerter: NotarAnwaerter) -> io.BytesIO:
        """
        Erstellt das PDF-Dokument für das Stammblatt.

        Args:
            anwaerter: Der Notariatskandidat

        Returns:
            BytesIO-Buffer mit PDF-Inhalt
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )

        # Content-Elemente
        elements = []

        # Titel
        elements.append(Paragraph("Stammblatt Notariatskandidat", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Persönliche Daten
        elements.append(Paragraph("Persönliche Daten", heading_style))

        personal_data = [
            ['Name:', anwaerter.get_voller_name()],
            ['Titel:', anwaerter.titel or '-'],
            ['E-Mail:', anwaerter.email or '-'],
            ['Telefon:', anwaerter.telefon or '-'],
        ]

        personal_table = Table(personal_data, colWidths=[5*cm, 12*cm])
        personal_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(personal_table)
        elements.append(Spacer(1, 0.5*cm))

        # Status & Wartezeit
        elements.append(Paragraph("Status & Wartezeit", heading_style))

        wartezeit_daten = []
        if anwaerter.zugelassen_am:
            wartezeit_daten.append(['Zugelassen am:', anwaerter.zugelassen_am.strftime('%d.%m.%Y')])

            # Wartezeit berechnen
            wartezeit_tage = (timezone.now().date() - anwaerter.zugelassen_am).days
            wartezeit_jahre = wartezeit_tage / 365.25
            wartezeit_daten.append([
                'Wartezeit:',
                f"{wartezeit_jahre:.1f} Jahre ({wartezeit_tage} Tage)"
            ])
        else:
            wartezeit_daten.append(['Zugelassen am:', 'Nicht erfasst'])

        wartezeit_daten.append(['Aktiv:', 'Ja' if anwaerter.ist_aktiv else 'Nein'])

        wartezeit_table = Table(wartezeit_daten, colWidths=[5*cm, 12*cm])
        wartezeit_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(wartezeit_table)
        elements.append(Spacer(1, 0.5*cm))

        # Betreuender Notar
        if anwaerter.betreuender_notar:
            elements.append(Paragraph("Betreuender Notar", heading_style))

            notar = anwaerter.betreuender_notar
            notar_daten = [
                ['Name:', notar.get_voller_name()],
                ['E-Mail:', notar.email or '-'],
                ['Telefon:', notar.telefon or '-'],
            ]

            if notar.notarstelle:
                notar_daten.append(['Notarstelle:', str(notar.notarstelle)])

            notar_table = Table(notar_daten, colWidths=[5*cm, 12*cm])
            notar_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(notar_table)
            elements.append(Spacer(1, 0.5*cm))

        # Notizen
        if anwaerter.notiz:
            elements.append(Paragraph("Notizen", heading_style))
            notiz_text = Paragraph(anwaerter.notiz.replace('\n', '<br/>'), styles['Normal'])
            elements.append(notiz_text)

        # Fußzeile
        elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        footer_text = f"Erstellt am {timezone.now().strftime('%d.%m.%Y um %H:%M Uhr')} | Notariatskammer"
        elements.append(Paragraph(footer_text, footer_style))

        # PDF bauen
        doc.build(elements)
        buffer.seek(0)

        return buffer


@service(
    kategorie='dokumente',
    icon='file-earmark-pdf',
    button_text='Stammblätter erstellen (Masse)'
)
class StammblattPDFMassenService(BaseService):
    """
    Erstellt Stammblatt-PDFs für mehrere Notariatskandidat.

    **Parameter:**
    - anwaerter_ids: Liste von Kandidaten-IDs (required)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    service_id = 'stammblatt_pdf_masse'
    name = 'Stammblatt-PDF erstellen (Masse)'
    beschreibung = """
    Erstellt Stammblatt-PDFs für mehrere Notariatskandidat auf einmal.

    **Parameter:**
    - anwaerter_ids: Liste von Kandidaten-IDs
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "ReportLab ist nicht installiert. "
                "Bitte installieren: pip install reportlab"
            )

        anwaerter_ids = self.hole_parameter('anwaerter_ids', required=True)

        if not isinstance(anwaerter_ids, list):
            raise ValueError("'anwaerter_ids' muss eine Liste sein")

        if len(anwaerter_ids) == 0:
            raise ValueError("'anwaerter_ids' darf nicht leer sein")

    def ausfuehren(self) -> Dict[str, Any]:
        """Erstellt Stammblatt-PDFs für alle Kandidat."""
        anwaerter_ids = self.hole_parameter('anwaerter_ids')
        workflow_instanz = self.parameter.get('workflow_instanz')

        dokument_ids = []
        fehler = []

        for anwaerter_id in anwaerter_ids:
            try:
                # StammblattPDFEinzelnService für jeden Kandidat aufrufen
                einzeln_service = StammblattPDFEinzelnService(
                    benutzer=self.benutzer,
                    anwaerter_id=anwaerter_id,
                    workflow_instanz=workflow_instanz
                )

                # Service direkt ausführen (ohne execute() um doppelte Protokollierung zu vermeiden)
                einzeln_service.validiere_parameter()
                ergebnis = einzeln_service.ausfuehren()

                dokument_ids.append(ergebnis['dokument_id'])

            except Exception as e:
                fehler.append({
                    'anwaerter_id': anwaerter_id,
                    'fehler': str(e)
                })
                logger.error(
                    f"Fehler beim Erstellen von Stammblatt für Kandidat {anwaerter_id}: {e}",
                    exc_info=True
                )

        logger.info(
            f"Stammblatt-Massenerstellung abgeschlossen: "
            f"{len(dokument_ids)} erfolgreich, {len(fehler)} Fehler"
        )

        return {
            'anzahl_dokumente': len(dokument_ids),
            'dokument_ids': dokument_ids,
            'anzahl_fehler': len(fehler),
            'fehler': fehler
        }


@service(
    kategorie='dokumente',
    icon='table',
    button_text='Besetzungsvorschlag erstellen'
)
class BesetzungsvorschlagService(BaseService):
    """
    Erstellt tabellarischen Besetzungsvorschlag mit Top 3 Bewerbern.

    **Parameter:**
    - anwaerter_ids: Liste mit 3 Kandidaten-IDs (sortiert nach Priorität) (required)
    - notarstelle_id: ID der zu besetzenden Notarstelle (required)
    - empfehlung: Empfehlungstext (optional)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    service_id = 'besetzungsvorschlag_erstellen'
    name = 'Besetzungsvorschlag erstellen'
    beschreibung = """
    Erstellt tabellarischen Besetzungsvorschlag mit Top 3 Bewerbern.

    Das Dokument enthält:
    - Übersichtstabelle mit allen 3 Bewerbern
    - Vergleich: Name, Wartezeit, Betreuender Notar
    - Empfehlung der Kammer

    **Parameter:**
    - anwaerter_ids: Liste mit 3 Kandidaten-IDs (sortiert)
    - notarstelle_id: ID der Notarstelle
    - empfehlung: Empfehlungstext (optional)
    """

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "ReportLab ist nicht installiert. "
                "Bitte installieren: pip install reportlab"
            )

        anwaerter_ids = self.hole_parameter('anwaerter_ids', required=True)
        notarstelle_id = self.hole_parameter('notarstelle_id', required=True)

        if not isinstance(anwaerter_ids, list):
            raise ValueError("'anwaerter_ids' muss eine Liste sein")

        if len(anwaerter_ids) != 3:
            raise ValueError("Exakt 3 Kandidaten-IDs erforderlich")

        # Prüfen ob Notarstelle existiert
        if not Notarstelle.objects.filter(pk=notarstelle_id).exists():
            raise ValueError(f"Notarstelle mit ID {notarstelle_id} nicht gefunden")

        # Prüfen ob alle Kandidat existieren
        gefundene = NotarAnwaerter.objects.filter(id__in=anwaerter_ids).count()
        if gefundene != 3:
            raise ValueError(f"Nicht alle Kandidat gefunden: {gefundene}/3")

    def ausfuehren(self) -> Dict[str, Any]:
        """Erstellt den Besetzungsvorschlag."""
        anwaerter_ids = self.hole_parameter('anwaerter_ids')
        notarstelle_id = self.hole_parameter('notarstelle_id')
        empfehlung = self.hole_parameter('empfehlung', required=False, default='')

        # Daten laden (in der Reihenfolge der IDs)
        notarstelle = Notarstelle.objects.get(pk=notarstelle_id)
        anwaerter_dict = {
            a.id: a for a in NotarAnwaerter.objects.filter(id__in=anwaerter_ids).select_related('betreuender_notar')
        }
        anwaerter_liste = [anwaerter_dict[aid] for aid in anwaerter_ids]

        # PDF erstellen
        pdf_buffer = self._erstelle_besetzungsvorschlag_pdf(
            notarstelle,
            anwaerter_liste,
            empfehlung
        )

        # Dateiname generieren
        heute = timezone.now()
        dateiname = f"Besetzungsvorschlag_{notarstelle.bezeichnung}_{heute.strftime('%Y%m%d')}.pdf"

        # Dokument in DB speichern
        dokument = Dokument.objects.create(
            titel=f"Besetzungsvorschlag {notarstelle.bezeichnung}",
            beschreibung=f"Besetzungsvorschlag für {notarstelle} mit 3 Bewerbern",
            dokument_typ='besetzungsvorschlag',
            dateiname=dateiname,
            dateityp='application/pdf',
            dateigroesse=len(pdf_buffer.getvalue()),
            generiert_von_service=self._service_ausfuehrung,
            workflow_instanz=self.parameter.get('workflow_instanz'),
            tags=f"Besetzungsvorschlag, {notarstelle.bezeichnung}"
        )

        # PDF-Datei speichern
        dokument.datei.save(
            dateiname,
            ContentFile(pdf_buffer.getvalue()),
            save=True
        )

        logger.info(
            f"Besetzungsvorschlag erstellt für {notarstelle} "
            f"(Dokument-ID: {dokument.id})"
        )

        return {
            'dokument_id': dokument.id,
            'dateiname': dateiname,
            'notarstelle_id': notarstelle.pk,
            'notarstelle': str(notarstelle),
            'anzahl_bewerber': 3,
            'dateityp': 'application/pdf',
            'dateigroesse_mb': dokument.dateigroesse_mb()
        }

    def _erstelle_besetzungsvorschlag_pdf(
        self,
        notarstelle: Notarstelle,
        anwaerter_liste: List[NotarAnwaerter],
        empfehlung: str
    ) -> io.BytesIO:
        """Erstellt das PDF-Dokument für den Besetzungsvorschlag."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )

        elements = []

        # Titel
        elements.append(Paragraph("Besetzungsvorschlag", title_style))
        elements.append(Spacer(1, 0.5*cm))

        # Notarstelle
        elements.append(Paragraph("Zu besetzende Notarstelle", heading_style))
        notarstelle_daten = [
            ['Bezeichnung:', notarstelle.bezeichnung],
            ['Name:', notarstelle.name],
            ['Ort:', notarstelle.stadt or '-'],
        ]
        notarstelle_table = Table(notarstelle_daten, colWidths=[5*cm, 12*cm])
        notarstelle_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(notarstelle_table)
        elements.append(Spacer(1, 1*cm))

        # Bewerber-Vergleichstabelle
        elements.append(Paragraph("Bewerber im Vergleich", heading_style))

        # Tabellendaten
        table_data = [
            ['Rang', 'Name', 'Wartezeit', 'Betreuender Notar']
        ]

        for idx, anwaerter in enumerate(anwaerter_liste, 1):
            # Wartezeit berechnen
            if anwaerter.zugelassen_am:
                wartezeit_tage = (timezone.now().date() - anwaerter.zugelassen_am).days
                wartezeit_jahre = wartezeit_tage / 365.25
                wartezeit_text = f"{wartezeit_jahre:.1f} Jahre"
            else:
                wartezeit_text = "Nicht erfasst"

            # Betreuender Notar
            notar_text = anwaerter.betreuender_notar.get_voller_name() if anwaerter.betreuender_notar else '-'

            table_data.append([
                str(idx),
                anwaerter.get_voller_name(),
                wartezeit_text,
                notar_text
            ])

        bewerber_table = Table(table_data, colWidths=[2*cm, 5*cm, 4*cm, 6*cm])
        bewerber_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rang zentriert
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # Zebra-Streifen
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            # Rahmen
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(bewerber_table)
        elements.append(Spacer(1, 1*cm))

        # Empfehlung
        if empfehlung:
            elements.append(Paragraph("Empfehlung der Kammer", heading_style))
            empfehlung_para = Paragraph(empfehlung.replace('\n', '<br/>'), styles['Normal'])
            elements.append(empfehlung_para)
            elements.append(Spacer(1, 0.5*cm))

        # Fußzeile
        elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        footer_text = f"Erstellt am {timezone.now().strftime('%d.%m.%Y um %H:%M Uhr')} | Notariatskammer"
        elements.append(Paragraph(footer_text, footer_style))

        # PDF bauen
        doc.build(elements)
        buffer.seek(0)

        return buffer
