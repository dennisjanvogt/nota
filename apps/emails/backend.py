"""
Custom E-Mail Backend für Development ohne SSL-Verifikation.
ACHTUNG: Nur für Development verwenden! In Produktion Standard-Backend nutzen.
"""
import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class UnverifiedSSLEmailBackend(SMTPBackend):
    """
    E-Mail Backend, das SSL-Zertifikate nicht verifiziert.
    Nur für Development/Testing verwenden!
    """

    def open(self):
        """Öffnet Verbindung zum SMTP-Server ohne SSL-Verifikation."""
        if self.connection:
            return False

        connection_params = {
            'timeout': self.timeout,
        }

        if self.use_ssl:
            connection_params['context'] = ssl._create_unverified_context()

        try:
            self.connection = self.connection_class(
                self.host,
                self.port,
                **connection_params
            )

            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls(context=ssl._create_unverified_context())
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception:
            if not self.fail_silently:
                raise
