# Notariatskammer Verwaltungssystem

Ein umfassendes Django-basiertes Verwaltungssystem für die Notariatskammer zur Verwaltung von Notaren, Notariatskandidatn, Notarstellen und Workflows.

## 📋 Inhaltsverzeichnis

- [Überblick](#überblick)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Konfiguration](#konfiguration)
- [Verwendung](#verwendung)
- [Architektur](#architektur)
- [Tests](#tests)
- [Deployment](#deployment)

## 🎯 Überblick

Das Notariatskammer Verwaltungssystem ist eine webbasierte Anwendung zur effizienten Verwaltung aller Aufgaben einer Notariatskammer. Das System ermöglicht die Verwaltung von Stammdaten (Notare, Notariatskandidat, Notarstellen), die Durchführung von Workflows (z.B. Bestellungsprozesse) sowie die Generierung und Verwaltung von Aktenzeichen.

### Hauptfunktionen

- **Stammdatenverwaltung**: Notare, Notariatskandidat, Notarstellen
- **Workflow-System**: Dynamische, konfigurierbare Workflows mit State Machine
- **Aktenzeichen-Generierung**: Thread-safe Generierung eindeutiger Aktenzeichen
- **Berichte & Exports**: CSV, Excel und PDF-Exports
- **Benutzer-Management**: Rollenbaiserte Zugriffskontrolle für Kammermitarbeiter
- **Dashboard**: Übersichtliche Darstellung aller wichtigen Informationen

## ✨ Features

### 1. Stammdaten-Verwaltung

#### Notarstellen
- Verwaltung von Notarstellen mit vollständigen Kontaktdaten
- Notarnummer, Bezeichnung, Adresse
- Status-Tracking (aktiv/inaktiv)
- Besetzungs-Tracking

#### Notare
- Vollständige Personalverwaltung
- Zuordnung zu Notarstellen
- Bestellungsdatum und Tätigkeitszeitraum
- Historie (war vorher Kandidat)

#### Notariatskandidat
- Verwaltung von Notariatskandidatn
- Zuordnung zu betreuenden Notaren
- Zulassungsdatum und geplante Bestellung
- Automatische Überführung bei Bestellung

### 2. Workflow-System

#### Dynamische Workflows
- Konfigurierbare Workflow-Typen im Admin
- Flexible Schritt-Definitionen
- Optionale und Pflicht-Schritte
- Geschätzte Dauer pro Schritt
- Rollen-basierte Zuständigkeiten

#### Bestellungsprozess
- Vordefinierter 8-Schritte-Prozess
- Von Antragsprüfung bis Benachrichtigung
- Automatische Aktenzeichen-Generierung
- Schritt-Tracking mit Status
- Zuweisung an Kammermitarbeiter
- Kommentar-Funktion

#### State Machine
- Automatische Übergänge zwischen Schritten
- Validierung von Übergängen
- Automatischer Workflow-Abschluss
- Abbruch-Funktion mit Begründung

### 3. Aktenzeichen-System

#### Thread-Safe Generierung
- Format: PREFIX-JAHR-LAUFNUMMER (z.B. BES-2025-0001)
- SELECT FOR UPDATE für Parallelität
- Transaktions-sichere Nummernvergabe
- Separate Sequenzen pro Präfix und Jahr

#### Kategorien
- BES: Bestellung
- ZUL: Zulassung
- AUF: Aufsicht
- ALL: Allgemein

### 4. Berichte & Exports

#### Export-Formate
- **CSV**: UTF-8 mit BOM, Semikolon-getrennt
- **Excel**: Formatierte XLSX mit Auto-Breite
- **PDF**: Professionelles Layout im Querformat

#### Verfügbare Berichte
- Notare-Liste (mit Notarstellen)
- Notariatskandidat-Liste (mit betreuenden Notaren)
- Notarstellen-Liste (mit Kontaktdaten)
- Workflow-Liste (mit Status und Fortschritt)
- Aktenzeichen-Liste (mit Kategorien)

#### Features
- Deutsche Spaltennamen
- Automatische Datums-Formatierung
- Boolean-Werte als Ja/Nein
- Verschachtelte Felder (z.B. notarstelle__name)

### 5. Dashboard

#### Statistiken
- Anzahl Notare (aktiv)
- Anzahl Notariatskandidat (aktiv)
- Anzahl Notarstellen
- Anzahl aktive Workflows

#### Meine Aufgaben
- Top 5 zugewiesene Workflow-Schritte
- Fälligkeitsdatum-Anzeige
- Direkter Zugriff auf Workflows

#### Offene Workflows
- Top 10 aktive Workflows
- Fortschrittsbalken
- Aktenzeichen-Anzeige

#### Letzte Aktenzeichen
- 5 zuletzt generierte Aktenzeichen
- Kategorie und Beschreibung
- Zeitstempel

### 6. Benutzer-Management

#### Rollen
- **Admin**: Voller Zugriff auf alle Funktionen
- **Leitung**: Genehmigungen und Freigaben
- **Sachbearbeiter**: Tägliche Verwaltungsaufgaben

#### Authentifizierung
- Django's eingebautes Auth-System
- Login/Logout-Funktionalität
- Passwort-Änderung
- Session-Management

## 🛠️ Tech Stack

### Backend
- **Django 5.2.9**: Web Framework
- **Django REST Framework**: API (für zukünftige Erweiterungen)
- **Python 3.12+**: Programmiersprache (getestet mit Python 3.14)
- **SQLite**: Datenbank (Development)
- **PostgreSQL-ready**: Production-ready

### Frontend
- **Bootstrap 5.3**: UI Framework
- **Bootstrap Icons**: Icon-Set
- **Django Templates**: Template Engine

### Export-Bibliotheken
- **openpyxl**: Excel-Export (XLSX)
- **ReportLab**: PDF-Generierung
- **Python CSV**: CSV-Export

### Testing
- **Django TestCase**: Unit Tests
- **Django TransactionTestCase**: Thread-Safety Tests
- **22 Tests für Workflows**: Vollständige Test-Abdeckung

## 🚀 Installation

### Voraussetzungen

- Python 3.14 oder höher
- pip (Python Package Manager)
- Virtualenv (empfohlen)

### Schritt-für-Schritt Installation

1. **Repository klonen**
```bash
git clone <repository-url>
cd nota
```

2. **Virtuelle Umgebung erstellen und aktivieren**
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. **Dependencies installieren**
```bash
pip install -r requirements.txt
```

4. **Datenbank migrieren**
```bash
python manage.py migrate
```

5. **Superuser erstellen**
```bash
python manage.py createsuperuser
```

6. **Bestellungsprozess-Workflow anlegen**
```bash
python manage.py bestellungsprozess_anlegen
```

7. **Testdaten erstellen (optional)**
```bash
python manage.py testdaten_erstellen
```

8. **Server starten**
```bash
python manage.py runserver
```

9. **Anwendung öffnen**
```
http://localhost:8000
```

## ⚙️ Konfiguration

### Wichtige Settings (config/settings.py)

```python
# Custom User Model (KRITISCH!)
AUTH_USER_MODEL = 'benutzer.KammerBenutzer'

# Sprache und Zeitzone
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True

# Login/Logout
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

### Datenbank für Production

Für Production PostgreSQL verwenden:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'notariatskammer_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📖 Verwendung

### 1. Anmeldung

- URL: `http://localhost:8000/login/`
- Standarduser: `admin` / `admin` (nach Erstinstallation ändern!)

### 2. Dashboard

Nach der Anmeldung sehen Sie das Dashboard mit:
- Statistiken (Notare, Kandidat, Notarstellen, Workflows)
- Ihre zugewiesenen Aufgaben
- Offene Workflows
- Letzte Aktenzeichen

### 3. Stammdaten verwalten

**Notarstellen**:
- Navigation: Stammdaten → Notarstellen
- Funktionen: Anlegen, Bearbeiten, Löschen, Filtern

**Notare**:
- Navigation: Stammdaten → Notare
- Funktionen: Anlegen, Bearbeiten, Notarstelle zuweisen

**Notariatskandidat**:
- Navigation: Stammdaten → Notariatskandidat
- Funktionen: Anlegen, Bearbeiten, betreuenden Notar zuweisen

### 4. Workflow starten

**Im Django Admin**:
1. Workflows → Workflow-Instanzen → Hinzufügen
2. Workflow-Typ auswählen (z.B. "Bestellungsprozess")
3. Name eingeben
4. Betroffene Person auswählen (Notariatskandidat)
5. Optional: Aktenzeichen wird automatisch generiert
6. Speichern

**Workflow automatisch starten**:
```python
from apps.workflows.services import WorkflowService
from apps.personen.models import NotarAnwaerter
from django.contrib.auth import get_user_model

KammerBenutzer = get_user_model()

anwaerter = NotarAnwaerter.objects.get(id=1)
benutzer = KammerBenutzer.objects.get(username='admin')

workflow = WorkflowService.bestellungsprozess_starten(
    notar_anwaerter=anwaerter,
    erstellt_von=benutzer
)
```

### 5. Workflow bearbeiten

**Schritt zuweisen**:
1. Workflow-Detail öffnen
2. Bei ausstehendem Schritt auf "Zuweisen" klicken
3. Benutzer auswählen
4. Bestätigen

**Schritt abschließen**:
1. Workflow-Detail öffnen
2. Bei aktivem Schritt auf "Abschließen" klicken
3. Optional: Notizen hinzufügen
4. Bestätigen
5. Nächster Schritt wird automatisch aktiviert

**Kommentar hinzufügen**:
1. Workflow-Detail öffnen
2. Kommentar im Textfeld eingeben
3. "Kommentar hinzufügen" klicken

### 6. Berichte exportieren

1. Navigation: Berichte
2. Bericht auswählen (z.B. "Notare")
3. Format wählen: CSV, Excel oder PDF
4. Datei wird automatisch heruntergeladen

## 🏗️ Architektur

### Projekt-Struktur

```
nota/
├── apps/
│   ├── kern/              # Basis-Models (ZeitstempelModel, AktivModel)
│   ├── benutzer/          # Custom User Model (KammerBenutzer)
│   ├── notarstellen/      # Notarstellen-Verwaltung
│   ├── personen/          # Notare und Notariatskandidat
│   ├── workflows/         # Workflow-System (Models, Services, State Machine)
│   ├── aktenzeichen/      # Aktenzeichen-Generierung
│   └── berichte/          # Export-Funktionen
├── config/                # Django-Konfiguration
├── templates/             # HTML-Templates
│   ├── base.html          # Basis-Template
│   ├── login.html         # Login-Seite
│   ├── workflows/         # Workflow-Templates
│   └── berichte/          # Berichte-Templates
├── static/                # Statische Dateien
├── manage.py              # Django Management
└── requirements.txt       # Python Dependencies
```

### Layer-Architektur

```
┌─────────────────────────────────┐
│        Templates (UI)           │
├─────────────────────────────────┤
│        Views (HTTP)             │
├─────────────────────────────────┤
│     Services (Business Logic)   │
├─────────────────────────────────┤
│    State Machine (Workflows)    │
├─────────────────────────────────┤
│       Models (Data)             │
├─────────────────────────────────┤
│      Database (SQLite/PG)       │
└─────────────────────────────────┘
```

### Workflow-Architektur

**WorkflowTyp** (Template):
- Definiert Workflow-Typ (z.B. "Bestellungsprozess")
- Enthält Schritte mit Reihenfolge
- Konfigurierbar im Admin

**WorkflowInstanz** (Execution):
- Konkrete Ausführung eines Workflows
- Status: entwurf → aktiv → abgeschlossen/abgebrochen
- Verknüpft mit Aktenzeichen und Person

**WorkflowZustandsmaschine**:
- Verwaltet Übergänge zwischen Schritten
- Validiert Aktionen
- Aktiviert nächsten Schritt automatisch

**WorkflowService**:
- High-Level API für Workflows
- Transaction-safe Operationen
- Integration mit Aktenzeichen-System

### Aktenzeichen Thread-Safety

```python
@transaction.atomic
def naechste_nummer_holen(self):
    # SELECT FOR UPDATE verhindert Race Conditions
    sequenz = Nummernsequenz.objects.select_for_update().get(pk=self.pk)
    sequenz.aktuelle_nummer += 1
    sequenz.save()
    return sequenz.aktuelle_nummer
```

## 🧪 Tests

### Tests ausführen

**Alle Tests**:
```bash
python manage.py test
```

**Workflow-Tests**:
```bash
python manage.py test apps.workflows
```

**Aktenzeichen-Tests**:
```bash
python manage.py test apps.aktenzeichen
```

### Test-Abdeckung

- **Workflow-System**: 22 Tests (alle bestanden)
- **Models**: Tests für alle Modelle
- **Services**: Tests für Business Logic
- **State Machine**: Tests für Übergänge
- **Thread-Safety**: Tests für parallele Nummern-Generierung

### Wichtige Tests

**Thread-Safety (Aktenzeichen)**:
```python
def test_concurrent_generation(self):
    """Test: Parallele Generierung erzeugt eindeutige Nummern."""
    # 10 Threads generieren parallel Aktenzeichen
    # Alle Nummern müssen eindeutig sein!
```

**Workflow-Abschluss**:
```python
def test_workflow_abschluss(self):
    """Test: Workflow wird automatisch abgeschlossen."""
    # Alle Schritte abschließen
    # Workflow-Status muss automatisch auf 'abgeschlossen' wechseln
```

## 🚢 Deployment

### Production Checklist

- [ ] `DEBUG = False` in settings.py
- [ ] `SECRET_KEY` aus Umgebungsvariable laden
- [ ] PostgreSQL-Datenbank konfigurieren
- [ ] `ALLOWED_HOSTS` setzen
- [ ] Static Files sammeln: `python manage.py collectstatic`
- [ ] HTTPS konfigurieren
- [ ] Gunicorn oder uWSGI als WSGI-Server
- [ ] Nginx als Reverse Proxy
- [ ] Backup-Strategie implementieren

### Production Settings

```python
# settings.py (Production)
import os

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ['your-domain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': '5432',
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Gunicorn starten

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Nginx-Konfiguration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/nota/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 Lizenz

Dieses Projekt ist für die interne Verwendung der Notariatskammer bestimmt.

## 🤝 Support

Bei Fragen oder Problemen wenden Sie sich bitte an das Entwicklungsteam.

---

**Entwickelt mit Django 5.0 und ❤️ für die Notariatskammer**
