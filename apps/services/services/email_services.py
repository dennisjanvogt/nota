"""
E-Mail-Services für automatisierten Versand.
"""
from typing import Dict, Any, List
import logging

from apps.services.base import BaseService, service
from apps.emails.models import EmailVorlage, GesendeteEmail
from apps.emails.services import EmailService
from apps.personen.models import NotarAnwaerter, Notar

logger = logging.getLogger(__name__)


@service(
    kategorie='kommunikation',
    icon='envelope',
    button_text='Strafregisterauszug anfordern'
)
class StrafregisterauszugAnfordernService(BaseService):
    """
    Fordert Strafregisterauszug bei einem Notariatskandidat an.

    **Parameter:**
    - anwaerter_id: ID des Anwärters (required)
    - vorlage_id: ID der E-Mail-Vorlage (optional, default: automatisch nach Kategorie)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    service_id = 'strafregisterauszug_anfordern'
    name = 'Strafregisterauszug anfordern'
    beschreibung = """
    Sendet eine E-Mail an einen Notariatskandidat zur Anforderung des Strafregisterauszugs.

    **Parameter:**
    - anwaerter_id: ID des Anwärters
    - vorlage_id: ID der E-Mail-Vorlage (optional)
    - workflow_instanz: Optional - Workflow-Zuordnung
    """

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        anwaerter_id = self.hole_parameter('anwaerter_id', required=True)

        # Prüfen ob Kandidat existiert
        if not NotarAnwaerter.objects.filter(id=anwaerter_id).exists():
            raise ValueError(f"Notariatskandidat mit ID {anwaerter_id} nicht gefunden")

        # Wenn vorlage_id angegeben, prüfen ob sie existiert
        vorlage_id = self.hole_parameter('vorlage_id', required=False)
        if vorlage_id and not EmailVorlage.objects.filter(id=vorlage_id).exists():
            raise ValueError(f"E-Mail-Vorlage mit ID {vorlage_id} nicht gefunden")

    def ausfuehren(self) -> Dict[str, Any]:
        """Sendet die Strafregisterauszug-Anforderung."""
        anwaerter_id = self.hole_parameter('anwaerter_id')
        vorlage_id = self.hole_parameter('vorlage_id', required=False)

        # Kandidat laden
        anwaerter = NotarAnwaerter.objects.select_related('betreuender_notar').get(
            id=anwaerter_id
        )

        if not anwaerter.email:
            raise ValueError(
                f"Kandidat {anwaerter.get_voller_name()} hat keine E-Mail-Adresse hinterlegt"
            )

        # E-Mail-Vorlage holen
        if vorlage_id:
            vorlage = EmailVorlage.objects.get(id=vorlage_id)
        else:
            # Automatisch Vorlage nach Kategorie holen
            try:
                vorlage = EmailVorlage.objects.filter(
                    kategorie='strafregister',
                    ist_aktiv=True
                ).first()

                if not vorlage:
                    raise EmailVorlage.DoesNotExist()

            except EmailVorlage.DoesNotExist:
                raise ValueError(
                    "Keine aktive E-Mail-Vorlage für Kategorie 'strafregister' gefunden. "
                    "Bitte Vorlage im Admin anlegen."
                )

        # Kontext für Platzhalter erstellen
        kontext = {
            'vorname': anwaerter.vorname,
            'nachname': anwaerter.nachname,
            'titel': anwaerter.titel or '',
            'anwaerter_id': anwaerter.id,
            'email': anwaerter.email,
        }

        if anwaerter.betreuender_notar:
            kontext['notar'] = anwaerter.betreuender_notar.get_voller_name()

        # E-Mail senden
        try:
            gesendete_email = EmailService.email_einfach_senden(
                empfaenger=anwaerter.email,
                betreff=EmailService._ersetze_platzhalter(vorlage.betreff, kontext),
                nachricht=EmailService._ersetze_platzhalter(vorlage.nachricht, kontext),
                benutzer=self.benutzer,
                cc_empfaenger=[e.strip() for e in vorlage.cc_empfaenger.split(',')] if vorlage.cc_empfaenger else None,
                service_ausfuehrung=self._service_ausfuehrung
            )

            # Vorlage nachträglich verknüpfen
            gesendete_email.vorlage = vorlage
            gesendete_email.anwaerter = anwaerter
            gesendete_email.save()

            logger.info(
                f"Strafregisterauszug-Anforderung gesendet an {anwaerter.get_voller_name()} "
                f"({anwaerter.email})"
            )

            return {
                'email_id': gesendete_email.id,
                'empfaenger': anwaerter.email,
                'anwaerter_id': anwaerter.id,
                'anwaerter_name': anwaerter.get_voller_name(),
                'betreff': gesendete_email.betreff,
                'erfolgreich': True
            }

        except Exception as e:
            logger.error(
                f"Fehler beim Senden der Strafregisterauszug-Anforderung: {e}",
                exc_info=True
            )
            raise


@service(
    kategorie='kommunikation',
    icon='envelope-plus',
    button_text='Unterlagen an Referenten senden'
)
class UnterlagenAnReferentenSendenService(BaseService):
    """
    Sendet Unterlagen (Dokumente) an alle Referenten eines Workflows.

    **Parameter:**
    - workflow_instanz: Workflow-Instanz mit Referenten (required)
    - dokument_ids: Liste von Dokument-IDs zum Anhängen (required)
    - vorlage_id: ID der E-Mail-Vorlage (optional)
    - betreff: Eigener Betreff (optional, überschreibt Vorlage)
    - nachricht: Eigene Nachricht (optional, überschreibt Vorlage)
    """

    service_id = 'unterlagen_an_referenten_senden'
    name = 'Unterlagen an Referenten senden'
    beschreibung = """
    Sendet Dokumente an alle Referenten eines Workflows per E-Mail.

    **Parameter:**
    - workflow_instanz: Workflow-Instanz (required)
    - dokument_ids: Liste von Dokument-IDs (required)
    - vorlage_id: E-Mail-Vorlage (optional)
    - betreff: Eigener Betreff (optional)
    - nachricht: Eigene Nachricht (optional)
    """

    def validiere_parameter(self) -> None:
        """Validiert die erforderlichen Parameter."""
        workflow_instanz = self.hole_parameter('workflow_instanz', required=True)
        dokument_ids = self.hole_parameter('dokument_ids', required=True)

        if not workflow_instanz:
            raise ValueError("workflow_instanz ist erforderlich")

        if not isinstance(dokument_ids, list) or len(dokument_ids) == 0:
            raise ValueError("dokument_ids muss eine nicht-leere Liste sein")

        # Prüfen ob Workflow Referenten hat
        if workflow_instanz.referenten.count() == 0:
            raise ValueError(
                f"Workflow '{workflow_instanz.name}' hat keine Referenten zugeordnet"
            )

    def ausfuehren(self) -> Dict[str, Any]:
        """Sendet die Unterlagen an alle Referenten."""
        workflow_instanz = self.hole_parameter('workflow_instanz')
        dokument_ids = self.hole_parameter('dokument_ids')
        vorlage_id = self.hole_parameter('vorlage_id', required=False)
        betreff_override = self.hole_parameter('betreff', required=False)
        nachricht_override = self.hole_parameter('nachricht', required=False)

        # Referenten holen
        referenten = workflow_instanz.referenten.all()
        empfaenger_liste = []

        for referent in referenten:
            if not referent.email:
                logger.warning(
                    f"Referent {referent.get_voller_name()} hat keine E-Mail-Adresse - wird übersprungen"
                )
                continue
            empfaenger_liste.append(referent.email)

        if len(empfaenger_liste) == 0:
            raise ValueError("Keine Referenten mit E-Mail-Adresse gefunden")

        # E-Mail-Vorlage holen (falls angegeben)
        vorlage = None
        if vorlage_id:
            vorlage = EmailVorlage.objects.get(id=vorlage_id)

        # Betreff und Nachricht bestimmen
        if betreff_override and nachricht_override:
            betreff = betreff_override
            nachricht = nachricht_override
        elif vorlage:
            # Kontext für Platzhalter
            kontext = {
                'workflow_name': workflow_instanz.name,
                'workflow_kennung': workflow_instanz.kennung,
            }
            betreff = EmailService._ersetze_platzhalter(vorlage.betreff, kontext)
            nachricht = EmailService._ersetze_platzhalter(vorlage.nachricht, kontext)
        else:
            # Fallback
            betreff = f"Unterlagen: {workflow_instanz.name}"
            nachricht = (
                f"Sehr geehrte Damen und Herren,\n\n"
                f"anbei erhalten Sie die Unterlagen für {workflow_instanz.name} "
                f"(Kennung: {workflow_instanz.kennung}).\n\n"
                f"Mit freundlichen Grüßen\n"
                f"Notariatskammer"
            )

        # E-Mails versenden
        email_ids = []
        fehler = []

        for empfaenger in empfaenger_liste:
            try:
                gesendete_email = EmailService.email_einfach_senden(
                    empfaenger=empfaenger,
                    betreff=betreff,
                    nachricht=nachricht,
                    benutzer=self.benutzer,
                    dokument_ids=dokument_ids,
                    service_ausfuehrung=self._service_ausfuehrung
                )

                # Vorlage nachträglich verknüpfen
                if vorlage:
                    gesendete_email.vorlage = vorlage
                    gesendete_email.save()

                email_ids.append(gesendete_email.id)

                logger.info(f"Unterlagen gesendet an {empfaenger}")

            except Exception as e:
                fehler.append({
                    'empfaenger': empfaenger,
                    'fehler': str(e)
                })
                logger.error(
                    f"Fehler beim Senden an {empfaenger}: {e}",
                    exc_info=True
                )

        logger.info(
            f"Unterlagen an Referenten gesendet: "
            f"{len(email_ids)} erfolgreich, {len(fehler)} Fehler"
        )

        return {
            'anzahl_empfaenger': len(referenten),
            'anzahl_gesendet': len(email_ids),
            'anzahl_dokumente': len(dokument_ids),
            'email_ids': email_ids,
            'anzahl_fehler': len(fehler),
            'fehler': fehler,
            'workflow_id': workflow_instanz.id,
            'workflow_name': workflow_instanz.name
        }
