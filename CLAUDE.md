# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektziel

Notariatskammer-Verwaltungssoftware zur Verwaltung von Notaren, Notariatskandidatn und Notarstellen durch die Notariatskammer.

## Tech Stack

- **Backend**: Django 5.2.9, Django REST Framework 3.14
- **Python**: 3.12+ (getestet mit 3.14)
- **Datenbank**: SQLite (Development), PostgreSQL-ready
- **Frontend**: Django Templates + Bootstrap 5.3
- **Exports**: openpyxl (Excel), ReportLab (PDF)
- **Authentifizierung**: Custom User Model (`benutzer.KammerBenutzer`)
- **Sprache**: Vollständig auf Deutsch

## Wichtige Entwicklungskommandos

### Setup
```bash
# Virtual environment aktivieren
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Datenbank migrieren
python manage.py migrate

# Superuser erstellen
python manage.py createsuperuser
```

### Custom Management Commands
```bash
# Bestellungsprozess-Workflow anlegen
python manage.py bestellungsprozess_anlegen

# Besetzungsverfahren-Workflow anlegen
python manage.py besetzungsverfahren_anlegen

# Testdaten erstellen (Notarstellen, Notare, Kandidat)
python manage.py testdaten_erstellen

# Notare importieren
python manage.py import_notare

# E-Mail Vorlagen erstellen
python manage.py standard_vorlagen_erstellen

# E-Mail Test versenden
python manage.py test_email

# Workflow-Schritte reparieren (bei Problemen)
python manage.py workflow_schritte_reparieren
```

### Development
```bash
# Development Server
python manage.py runserver

# Django Shell
python manage.py shell

# Tests ausführen
python manage.py test                    # Alle Tests
python manage.py test apps.workflows     # Nur Workflow-Tests
```

### Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Code-Konventionen

### KRITISCH: Alles auf Deutsch!

- **Felder**: `vorname`, `nachname`, `notarstelle`, `erstellt_am`
- **Methoden**: `workflow_starten()`, `schritt_abschliessen()`
- **URLs**: `/notarstellen/`, `/workflows/instanzen/`
- **UI/Kommentare**: Vollständig auf Deutsch
- **verbose_name**: Immer definieren

Beispiel Model:
```python
class Notarstelle(ZeitstempelModel, AktivModel):
    """Notarstelle/Notariat."""
    notarnummer = models.CharField(max_length=20, unique=True, verbose_name='Notarnummer')

    class Meta:
        verbose_name = 'Notarstelle'
        verbose_name_plural = 'Notarstellen'
```

## Architektur-Übersicht

### App-Struktur
```
apps/
├── kern/           # Basis-Models: ZeitstempelModel, AktivModel
├── benutzer/       # Custom User (KammerBenutzer) mit Rollen
├── notarstellen/   # Notarstellen-Verwaltung
├── personen/       # Notare & Notariatskandidat (erbt von PersonBasis)
├── workflows/      # Dynamisches Workflow-System mit State Machine
├── emails/         # E-Mail Templates & Versand (UnverifiedSSLEmailBackend für Dev)
└── berichte/       # Exports (CSV UTF-8 BOM, Excel, PDF)
```

### Basis-Models (apps.kern)
Alle Models erben von:
- **ZeitstempelModel**: Fügt `erstellt_am`, `aktualisiert_am` hinzu
- **AktivModel**: Fügt `ist_aktiv` mit `aktivieren()`/`deaktivieren()` hinzu

### Custom User Model (apps.benutzer)
- **KRITISCH**: `AUTH_USER_MODEL = 'benutzer.KammerBenutzer'` in config/settings.py
- **ACHTUNG**: Muss VOR erster Migration gesetzt sein
- Rollen: Admin, Leitung, Sachbearbeiter
- Kammermitarbeiter VERWALTEN Notare (sind NICHT selbst Notare)

### Workflow-System (apps.workflows)

**Architektur:**
- **WorkflowTyp**: Template/Definition (z.B. "Bestellungsprozess")
- **WorkflowSchritt**: Schritt-Definitionen mit Reihenfolge
- **WorkflowInstanz**: Konkrete Ausführung (status: entwurf → aktiv → archiviert)
- **WorkflowSchrittInstanz**: Konkrete Schritt-Ausführung (status: pending → completed)

**Services (apps/workflows/services.py):**
- `WorkflowService.workflow_erstellen()` - Erstellt Workflow + alle Schritt-Instanzen
- `WorkflowService.workflow_starten()` - Status: entwurf → aktiv
- `WorkflowService.schritt_abschliessen()` - Schritt abschließen, prüft Auto-Archivierung
- `WorkflowService.workflow_archivieren()` - Workflow archivieren

**Wichtig:**
- Vereinfachtes Checklisten-System (keine komplexe State Machine mehr)
- Workflow wird automatisch archiviert wenn alle Schritte completed
- Alle Operationen in @transaction.atomic

### Personen-System (apps.personen)

**Models:**
- **PersonBasis**: Abstract Model (vorname, nachname, titel, email, telefon)
- **Notar**: Erbt von PersonBasis, hat `notarstelle` (ForeignKey)
- **NotarAnwaerter**: Erbt von PersonBasis, hat `betreuender_notar` (ForeignKey)

**Services (apps/personen/services.py):**
- Handling der Bestellung von Kandidaten zu Notaren

### E-Mail System (apps.emails)

**WICHTIG für Development:**
- Backend: `UnverifiedSSLEmailBackend` (SSL-Zertifikate werden nicht validiert)
- Für Production: Auf `django.core.mail.backends.smtp.EmailBackend` wechseln
- Konfiguration via .env (EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, etc.)
- Strato SMTP: `smtp.strato.de:587` mit TLS

**Models:**
- **EmailVorlage**: Templates für E-Mails mit Platzhaltern

### Berichte (apps.berichte)

**Export-Formate:**
- CSV: UTF-8 mit BOM, Semikolon-getrennt
- Excel: XLSX mit Auto-Spaltenbreite
- PDF: Querformat mit ReportLab

## Login & URLs

- Login: `http://localhost:8000/login/`
- Dashboard: `http://localhost:8000/` (nach Login)
- Admin: `http://localhost:8000/admin/`
- Settings: `LOGIN_URL = 'login'`, `LOGIN_REDIRECT_URL = 'dashboard'`

## Troubleshooting

**Migration Issues:**
- AUTH_USER_MODEL ändern erfordert Datenbank-Reset
- `python manage.py migrate --fake-initial` bei Konflikten

**E-Mail Test fehlschlägt:**
- Prüfe .env Datei (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
- Für lokales Testing: `python manage.py test_email`
