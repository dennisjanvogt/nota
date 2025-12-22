"""
E-Mail-Service für das Versenden von E-Mails mit Anhängen.
"""
from typing import List, Optional, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
import logging

from apps.emails.models import EmailVorlage, GesendeteEmail
from apps.services.models import Dokument

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailService:
    """
    Service zum Versenden von E-Mails mit Anhängen.

    Kümmert sich um:
    - Platzhalter-Ersetzung in Vorlagen
    - Anhängen von Dokumenten
    - Versand
    - Protokollierung
    """

    @staticmethod
    def _render_html_email(betreff: str, nachricht: str) -> str:
        """
        Rendert eine E-Mail als HTML mit Branding.

        Args:
            betreff: E-Mail-Betreff
            nachricht: E-Mail-Nachricht (Plain Text)

        Returns:
            HTML-String der E-Mail
        """
        # Logo URL - kann in settings konfiguriert werden
        logo_url = getattr(
            settings,
            'EMAIL_LOGO_URL',
            'https://www.notar.at/fileadmin/templates/images/logo.png'
        )

        context = {
            'betreff': betreff,
            'nachricht': nachricht,
            'logo_url': logo_url,
        }

        return render_to_string('emails/email_template.html', context)

    @staticmethod
    def email_mit_anhaengen_senden(
        vorlage: EmailVorlage,
        empfaenger_liste: List[str],
        dokument_ids: List[int],
        benutzer: User,
        kontext: Optional[Dict[str, Any]] = None,
        service_ausfuehrung=None
    ) -> Dict[str, Any]:
        """
        Sendet E-Mails mit Anhängen basierend auf einer Vorlage.

        Args:
            vorlage: Die zu verwendende E-Mail-Vorlage
            empfaenger_liste: Liste von E-Mail-Adressen
            dokument_ids: Liste von Dokument-IDs die angehängt werden sollen
            benutzer: Der ausführende Benutzer
            kontext: Dictionary mit Platzhalter-Werten (optional)
            service_ausfuehrung: Verknüpfte ServiceAusfuehrung (optional)

        Returns:
            Dictionary mit Ergebnis: {
                'anzahl_empfaenger': int,
                'anzahl_dokumente': int,
                'email_ids': List[int],
                'erfolgreich': bool,
                'fehler': List[str]
            }

        Raises:
            ValueError: Wenn Vorlage oder Dokumente nicht gefunden
        """
        if not kontext:
            kontext = {}

        # Dokumente laden
        dokumente = Dokument.objects.filter(id__in=dokument_ids)
        if len(dokumente) != len(dokument_ids):
            gefundene_ids = set(dokumente.values_list('id', flat=True))
            fehlende_ids = set(dokument_ids) - gefundene_ids
            raise ValueError(f"Dokumente nicht gefunden: {fehlende_ids}")

        # Platzhalter im Betreff und Nachricht ersetzen
        betreff = EmailService._ersetze_platzhalter(vorlage.betreff, kontext)
        nachricht = EmailService._ersetze_platzhalter(vorlage.nachricht, kontext)

        ergebnis = {
            'anzahl_empfaenger': len(empfaenger_liste),
            'anzahl_dokumente': len(dokumente),
            'email_ids': [],
            'erfolgreich': True,
            'fehler': []
        }

        # Für jeden Empfänger E-Mail erstellen und senden
        for empfaenger in empfaenger_liste:
            try:
                # HTML-Version der E-Mail erstellen
                html_content = EmailService._render_html_email(betreff, nachricht)

                # E-Mail erstellen mit Plain Text und HTML
                email = EmailMultiAlternatives(
                    subject=betreff,
                    body=nachricht,  # Plain text version als Fallback
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[empfaenger],
                )

                # HTML-Alternative hinzufügen
                email.attach_alternative(html_content, "text/html")

                # CC-Empfänger hinzufügen
                if vorlage.cc_empfaenger:
                    cc_liste = [e.strip() for e in vorlage.cc_empfaenger.split(',')]
                    email.cc = cc_liste

                # Dokumente anhängen
                for dokument in dokumente:
                    if dokument.datei:
                        email.attach_file(dokument.datei.path)
                        logger.debug(f"Datei angehängt: {dokument.dateiname}")

                # E-Mail senden
                email.send()

                # In Datenbank protokollieren
                gesendete_email = GesendeteEmail.objects.create(
                    vorlage=vorlage,
                    gesendet_von=benutzer,
                    empfaenger=empfaenger,
                    cc_empfaenger=vorlage.cc_empfaenger,
                    betreff=betreff,
                    nachricht=nachricht,
                    service_ausfuehrung=service_ausfuehrung,
                    erfolgreich=True
                )

                # Anhänge verknüpfen
                gesendete_email.anhaenge.set(dokumente)

                ergebnis['email_ids'].append(gesendete_email.id)

                logger.info(f"E-Mail erfolgreich gesendet an {empfaenger}")

            except Exception as e:
                ergebnis['erfolgreich'] = False
                fehler_msg = f"Fehler beim Senden an {empfaenger}: {str(e)}"
                ergebnis['fehler'].append(fehler_msg)

                # Auch Fehler protokollieren
                GesendeteEmail.objects.create(
                    vorlage=vorlage,
                    gesendet_von=benutzer,
                    empfaenger=empfaenger,
                    cc_empfaenger=vorlage.cc_empfaenger,
                    betreff=betreff,
                    nachricht=nachricht,
                    service_ausfuehrung=service_ausfuehrung,
                    erfolgreich=False,
                    fehler=str(e)
                )

                logger.error(fehler_msg, exc_info=True)

        return ergebnis

    @staticmethod
    def _ersetze_platzhalter(text: str, kontext: Dict[str, Any]) -> str:
        """
        Ersetzt Platzhalter im Text durch Werte aus dem Kontext.

        Unterstützte Platzhalter:
        - {vorname}, {nachname}, {titel}
        - {notar_id}, {anwaerter_id}
        - {notarstelle}
        - {email}
        - Alle weiteren Schlüssel aus kontext

        Args:
            text: Text mit Platzhaltern
            kontext: Dictionary mit Platzhalter-Werten

        Returns:
            Text mit ersetzten Platzhaltern
        """
        ergebnis = text

        for key, value in kontext.items():
            placeholder = '{' + key + '}'
            if placeholder in ergebnis:
                ergebnis = ergebnis.replace(placeholder, str(value))

        return ergebnis

    @staticmethod
    def email_einfach_senden(
        empfaenger: str,
        betreff: str,
        nachricht: str,
        benutzer: User,
        cc_empfaenger: Optional[List[str]] = None,
        dokument_ids: Optional[List[int]] = None,
        service_ausfuehrung=None
    ) -> GesendeteEmail:
        """
        Sendet eine einfache E-Mail ohne Vorlage.

        Args:
            empfaenger: E-Mail-Adresse des Empfängers
            betreff: E-Mail-Betreff
            nachricht: E-Mail-Text
            benutzer: Der ausführende Benutzer
            cc_empfaenger: Liste von CC-Empfängern (optional)
            dokument_ids: Liste von Dokument-IDs zum Anhängen (optional)
            service_ausfuehrung: Verknüpfte ServiceAusfuehrung (optional)

        Returns:
            GesendeteEmail-Instanz

        Raises:
            Exception: Bei Versandfehlern
        """
        # HTML-Version der E-Mail erstellen
        html_content = EmailService._render_html_email(betreff, nachricht)

        # E-Mail erstellen mit Plain Text und HTML
        email = EmailMultiAlternatives(
            subject=betreff,
            body=nachricht,  # Plain text version als Fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[empfaenger],
        )

        # HTML-Alternative hinzufügen
        email.attach_alternative(html_content, "text/html")

        # CC-Empfänger hinzufügen
        if cc_empfaenger:
            email.cc = cc_empfaenger
            cc_string = ', '.join(cc_empfaenger)
        else:
            cc_string = ''

        # Dokumente anhängen
        dokumente = []
        if dokument_ids:
            dokumente = Dokument.objects.filter(id__in=dokument_ids)
            for dokument in dokumente:
                if dokument.datei:
                    email.attach_file(dokument.datei.path)

        try:
            # E-Mail senden
            email.send()

            # In Datenbank protokollieren
            gesendete_email = GesendeteEmail.objects.create(
                gesendet_von=benutzer,
                empfaenger=empfaenger,
                cc_empfaenger=cc_string,
                betreff=betreff,
                nachricht=nachricht,
                service_ausfuehrung=service_ausfuehrung,
                erfolgreich=True
            )

            # Anhänge verknüpfen
            if dokumente:
                gesendete_email.anhaenge.set(dokumente)

            logger.info(f"E-Mail erfolgreich gesendet an {empfaenger}")
            return gesendete_email

        except Exception as e:
            # Fehler protokollieren
            gesendete_email = GesendeteEmail.objects.create(
                gesendet_von=benutzer,
                empfaenger=empfaenger,
                cc_empfaenger=cc_string,
                betreff=betreff,
                nachricht=nachricht,
                service_ausfuehrung=service_ausfuehrung,
                erfolgreich=False,
                fehler=str(e)
            )

            logger.error(f"Fehler beim Senden an {empfaenger}: {e}", exc_info=True)
            raise
