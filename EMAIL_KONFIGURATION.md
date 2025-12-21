# E-Mail-System - Konfigurationsanleitung

## Was wurde implementiert

### 1. Datenmodelle
- **EmailVorlage**: Speichert E-Mail-Vorlagen mit Platzhaltern
  - Name, Kategorie (Strafregister, Bestellung, Zulassung, etc.)
  - Betreff und Nachricht mit Platzhaltern
  - Standard-Empfänger und CC-Empfänger
  - Aktiv/Inaktiv Status

- **GesendeteEmail**: Protokolliert alle gesendeten E-Mails
  - Verknüpfung zur verwendeten Vorlage
  - Empfänger, Betreff, Nachricht
  - Verknüpfung zu Notar oder Kandidat
  - Erfolgsstatus und Fehlerprotokollierung

### 2. Funktionen
- ✅ E-Mail-Vorlagen verwalten (CRUD)
- ✅ E-Mails basierend auf Vorlagen generieren
- ✅ Platzhalter automatisch ersetzen: `{vorname}`, `{nachname}`, `{titel}`, `{notar_id}`, `{anwaerter_id}`, `{notarstelle}`
- ✅ Standard-Empfänger konfigurierbar
- ✅ Vor dem Senden können E-Mails noch bearbeitet werden
- ✅ Alle gesendeten E-Mails werden protokolliert
- ✅ Verknüpfung zu Notar/Kandidat für einfache Nachverfolgung

### 3. URLs
- `/emails/vorlagen/` - Liste aller E-Mail-Vorlagen
- `/emails/vorlagen/neu/` - Neue Vorlage erstellen
- `/emails/vorlagen/<id>/` - Vorlagen-Details
- `/emails/vorlagen/<id>/bearbeiten/` - Vorlage bearbeiten
- `/emails/vorlagen/<id>/senden/` - E-Mail basierend auf Vorlage senden
- `/emails/gesendet/` - Liste aller gesendeten E-Mails

## E-Mail-Konfiguration erforderlich

### Option 1: Gmail (für Entwicklung/Testing)

Fügen Sie folgende Einstellungen zu `config/settings.py` hinzu:

```python
# E-Mail Konfiguration - Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ihre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'ihr-app-passwort'  # NICHT das normale Passwort!
DEFAULT_FROM_EMAIL = 'ihre-email@gmail.com'
```

**Wichtig für Gmail:**
1. Gehen Sie zu https://myaccount.google.com/apppasswords
2. Erstellen Sie ein App-Passwort für "Mail"
3. Verwenden Sie dieses App-Passwort (NICHT Ihr normales Gmail-Passwort)

### Option 2: Österreichische Behörden-E-Mail (Produktion)

Wenn Sie einen SMTP-Server der österreichischen Behörden verwenden:

```python
# E-Mail Konfiguration - Behörden-Server
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.justiz.gv.at'  # Ihr SMTP-Server
EMAIL_PORT = 587  # Oder 25, 465 je nach Server
EMAIL_USE_TLS = True  # Oder EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'ihr-benutzername'
EMAIL_HOST_PASSWORD = 'ihr-passwort'
DEFAULT_FROM_EMAIL = 'notariatskammer@justiz.gv.at'
```

### Option 3: Lokale Entwicklung (Konsolen-Ausgabe)

Für Tests ohne echten E-Mail-Versand:

```python
# E-Mail Konfiguration - Konsolen-Ausgabe (Development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'notariatskammer@example.com'
```

E-Mails werden dann nur in der Konsole ausgegeben, nicht wirklich versendet.

### Option 4: SendGrid / Mailgun (Cloud-Service)

Falls Sie einen professionellen E-Mail-Service verwenden möchten:

**SendGrid:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'IHR-SENDGRID-API-KEY'
DEFAULT_FROM_EMAIL = 'notariatskammer@example.com'
```

## Umgebungsvariablen (Empfohlen für Produktion)

Erstellen Sie eine `.env` Datei im Projektverzeichnis:

```env
EMAIL_HOST=smtp.justiz.gv.at
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ihr-benutzername
EMAIL_HOST_PASSWORD=ihr-passwort
DEFAULT_FROM_EMAIL=notariatskammer@justiz.gv.at
```

Und laden Sie diese in `settings.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
```

Installieren Sie dafür: `pip install python-dotenv`

## Beispiel-Vorlagen erstellen

Nach der Konfiguration können Sie E-Mail-Vorlagen im Admin-Bereich oder über die Oberfläche erstellen:

### Beispiel: Strafregisterauszug

**Name:** Anfrage Strafregisterauszug
**Kategorie:** Strafregister
**Betreff:** Anfrage Strafregisterauszug - {nachname}
**Nachricht:**
```
Sehr geehrte Damen und Herren,

hiermit ersuche ich um Übermittlung eines Strafregisterauszugs für:

{titel} {vorname} {nachname}
{notar_id}
Notarstelle: {notarstelle}

Mit freundlichen Grüßen
Notariatskammer
```

**Standard-Empfänger:** strafregister@justiz.gv.at

## Verwendung

1. **Vorlage erstellen:** Gehen Sie zu "E-Mail-Vorlagen" → "Neue Vorlage"
2. **E-Mail senden:**
   - Von der Notar-/Kandidaten-Detailseite
   - Wählen Sie die gewünschte Vorlage
   - Platzhalter werden automatisch ersetzt
   - Passen Sie bei Bedarf Empfänger oder Text an
   - Klicken Sie auf "Senden"
3. **Protokoll ansehen:** "Gesendete E-Mails" zeigt alle versendeten E-Mails

## Nächste Schritte

1. Konfigurieren Sie Ihre E-Mail-Einstellungen in `settings.py`
2. Testen Sie den E-Mail-Versand mit der Konsolen-Ausgabe
3. Erstellen Sie Ihre Standard-Vorlagen
4. Wechseln Sie zum echten SMTP-Server für Produktion
