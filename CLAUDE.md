# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektziel

Notariatskammer-Verwaltungssoftware zur Verwaltung von Notaren, Notar-Anwärtern und Notarstellen durch die Notariatskammer.

## Tech Stack

- **Backend**: Django 5.0 + Django REST Framework
- **Datenbank**: SQLite (Development), PostgreSQL (Production-ready)
- **Frontend**: Django Templates + Bootstrap 5
- **Authentifizierung**: Django's Custom User Model (KammerBenutzer)
- **Sprache**: Vollständig auf Deutsch

## Environment Setup

- Python virtual environment: `venv/`
- Activate venv: `source venv/bin/activate` (Unix/macOS)
- Deactivate venv: `deactivate`
- Install dependencies: `pip install -r requirements.txt`

## Projektstruktur

```
nota/
├── manage.py
├── requirements.txt
├── config/                          # Django-Projekt-Konfiguration
│   ├── settings.py                  # AUTH_USER_MODEL = 'benutzer.KammerBenutzer'
│   ├── urls.py
│   └── wsgi.py
├── apps/                            # Alle Django Apps
│   ├── kern/                        # Gemeinsame Basis-Models (ZeitstempelModel, AktivModel)
│   ├── benutzer/                    # KammerBenutzer Model (Custom User)
│   ├── notarstellen/                # Notarstellen-Verwaltung
│   ├── personen/                    # Notare und Notar-Anwärter
│   ├── workflows/                   # Workflow-System (Bestellungsprozess)
│   ├── aktenzeichen/                # Aktenzeichen-Generierung
│   └── berichte/                    # Export & Reporting
├── templates/
│   └── base.html                    # Bootstrap 5 Basis-Template
├── static/                          # CSS, JS, Bilder
└── media/                           # User uploads
```

## Wichtige Entwicklungskommandos

### Django Basics

```bash
# Development Server starten
python manage.py runserver

# Neue Migrations erstellen
python manage.py makemigrations

# Migrations anwenden
python manage.py migrate

# Superuser erstellen
python manage.py createsuperuser

# Django Shell öffnen
python manage.py shell

# Statische Dateien sammeln (Production)
python manage.py collectstatic
```

### Testing

```bash
# Alle Tests ausführen
python manage.py test

# Tests für eine App
python manage.py test apps.benutzer

# Tests mit Coverage
coverage run --source='.' manage.py test
coverage report
```

## Code-Konventionen

### WICHTIG: Alles auf Deutsch!

- **Model-Felder**: Deutsche Namen (`vorname`, `nachname`, `notarstelle`, `erstellt_am`)
- **Methoden**: Deutsche Namen (`workflow_starten()`, `schritt_abschliessen()`, `aktenzeichen_generieren()`)
- **URLs**: Deutsche Pfade (`/notarstellen/`, `/workflows/instanzen/`)
- **UI-Texte**: Vollständig auf Deutsch
- **Kommentare**: Deutsch
- **verbose_name**: Immer in Meta-Klassen definieren

### Beispiel Model:

```python
class Notarstelle(ZeitstempelModel, AktivModel):
    """Notarstelle/Notariat."""
    notarnummer = models.CharField(max_length=20, unique=True, verbose_name='Notarnummer')
    bezeichnung = models.CharField(max_length=50, verbose_name='Bezeichnung')

    class Meta:
        verbose_name = 'Notarstelle'
        verbose_name_plural = 'Notarstellen'
        ordering = ['notarnummer']
```

## Datenmodell-Übersicht

### Benutzer (apps.benutzer)
- **KammerBenutzer**: Custom User Model für Kammermitarbeiter (rolle, abteilung)

### Notarstellen (apps.notarstellen)
- **Notarstelle**: Notarstellen mit notarnummer, bezeichnung, Adresse

### Personen (apps.personen)
- **PersonBasis**: Abstract Model mit vorname, nachname, titel, email, telefon
- **Notar**: Notar mit notarstelle, bestellt_am
- **NotarAnwaerter**: Notar-Anwärter mit betreuender_notar, zugelassen_am

### Workflows (apps.workflows)
**Definition:**
- **WorkflowTyp**: z.B. "Bestellungsprozess"
- **WorkflowSchritt**: Schritte eines Workflows
- **WorkflowSchrittUebergang**: Erlaubte Übergänge

**Instanzen:**
- **WorkflowInstanz**: Konkrete Workflow-Ausführung
- **WorkflowSchrittInstanz**: Konkrete Schritt-Ausführung
- **WorkflowKommentar**: Kommentare zu Workflows

### Aktenzeichen (apps.aktenzeichen)
- **Nummernsequenz**: Thread-safe Sequenzen pro Jahr/Präfix
- **Aktenzeichen**: Format "BES-2025-0001"

## Wichtige Konzepte

### Custom User Model
- **KRITISCH**: `AUTH_USER_MODEL = 'benutzer.KammerBenutzer'` muss VOR erster Migration gesetzt sein
- Kammermitarbeiter VERWALTEN Notare, sind aber NICHT selbst Notare

### Workflow-System
- Dynamisch konfigurierbar über Django Admin
- State Machine Pattern für Schritt-Übergänge
- Hauptanwendungsfall: Bestellung von Notar-Anwärtern zu Notaren

### Thread-Safety bei Aktenzeichen
- SELECT FOR UPDATE in `naechste_nummer_holen()`
- @transaction.atomic Decorator
- Tests für Concurrent Generation

## Nächste Entwicklungsschritte

### Phase 2: Stammdaten (nächster Schritt)
1. Kern-Models implementieren (ZeitstempelModel, AktivModel)
2. Notarstelle Model + Admin + Views
3. Person-Models (Notar, NotarAnwaerter) + Admin
4. CRUD-Funktionalität
5. URL-Routing

### Phase 3: Aktenzeichen
6. Nummernsequenz und Aktenzeichen Models
7. AktenzeichenService (Thread-safe)
8. Admin + Custom Views

### Phase 4: Workflow-System
9. Workflow Models implementieren
10. Zustandsmaschine (zustandsmaschine.py)
11. WorkflowService (services.py)
12. Custom Views für Workflow-Instanzen

## Admin-Interface

- URL: http://localhost:8000/admin/
- Alle Models sind im Django Admin registriert
- Deutsche Beschriftungen (`verbose_name`)
- Custom Admin-Konfiguration für komplexe Models

## Troubleshooting

### Migration Issues
- Wenn AUTH_USER_MODEL geändert werden muss: Datenbank droppen und neu erstellen
- Bei Migration-Konflikten: `python manage.py migrate --fake-initial`

### Static Files Not Found
- `python manage.py collectstatic` ausführen
- STATICFILES_DIRS und STATIC_ROOT in settings.py prüfen

## Deployment-Hinweise

- SQLite für Development, PostgreSQL für Production
- `DEBUG = False` in Production
- `ALLOWED_HOSTS` konfigurieren
- Statische Dateien mit WhiteNoise oder separatem Server
- Environment Variables für Secrets (SECRET_KEY, DB-Credentials)
