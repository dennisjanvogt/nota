# CRUD-Funktionalität Status

## ✅ Was wurde erledigt:

### 1. Fehler behoben
- ✅ AttributeError in `notarstelle_detail_view` behoben (line 74)
  - `notaranwaerter_set` → `anwaerter` (korrekter related_name)

### 2. Echte österreichische Daten importiert
- ✅ 30 Notarstellen aus allen Bundesländern
- ✅ 40 Notare mit realistischen Namen
- ✅ 20 Notar-Anwärter
- ✅ Dummy-Daten entfernt

### 3. CRUD-System erstellt für Notarstellen

#### Forms erstellt:
- ✅ `apps/notarstellen/forms.py` - NotarstelleForm
- ✅ `apps/personen/forms.py` - NotarForm, NotarAnwaerterForm

#### Views erstellt (Notarstellen):
- ✅ `notarstelle_erstellen_view` - Neue Notarstelle erstellen
- ✅ `notarstelle_bearbeiten_view` - Notarstelle bearbeiten
- ✅ `notarstelle_loeschen_view` - Notarstelle löschen

#### URLs aktualisiert (Notarstellen):
- ✅ `/notarstellen/neu/` - Erstellen
- ✅ `/notarstellen/<id>/bearbeiten/` - Bearbeiten
- ✅ `/notarstellen/<id>/loeschen/` - Löschen

#### Templates aktualisiert:
- ✅ `notarstellen_liste.html` - Links zeigen jetzt auf eigene CRUD-Seiten statt Django Admin

## 🔄 Noch zu erstellen:

### 1. Templates für Notarstellen CRUD
```
templates/notarstellen/
├── notarstelle_form.html           # TODO - Für Erstellen & Bearbeiten
└── notarstelle_loeschen.html       # TODO - Lösch-Bestätigung
```

### 2. CRUD Views für Notare
```python
# apps/personen/views.py - Hinzufügen:
- notar_erstellen_view()
- notar_bearbeiten_view()
- notar_loeschen_view()
```

### 3. CRUD Views für Notar-Anwärter
```python
# apps/personen/views.py - Hinzufügen:
- anwaerter_erstellen_view()
- anwaerter_bearbeiten_view()
- anwaerter_loeschen_view()
```

### 4. URLs für Notare & Anwärter
```python
# apps/personen/urls.py - Ergänzen:
- /personen/notare/neu/
- /personen/notare/<id>/bearbeiten/
- /personen/notare/<id>/loeschen/
- /personen/anwaerter/neu/
- /personen/anwaerter/<id>/bearbeiten/
- /personen/anwaerter/<id>/loeschen/
```

### 5. Templates aktualisieren
- `notare_liste.html` - Links auf eigene CRUD statt Django Admin
- `anwaerter_liste.html` - Links auf eigene CRUD statt Django Admin

### 6. Form-Templates erstellen
```
templates/personen/
├── notar_form.html                 # TODO
├── notar_loeschen.html             # TODO
├── anwaerter_form.html             # TODO
└── anwaerter_loeschen.html         # TODO
```

## 📝 Nächste Schritte (Priorität):

1. **Notarstellen-Templates erstellen** (Vorlage unten)
2. **Dieselben CRUD-Views für Notare erstellen** (nach gleichem Muster)
3. **Dieselben CRUD-Views für Anwärter erstellen** (nach gleichem Muster)
4. **Alle Liste-Templates aktualisieren** (Links auf eigene Seiten)

## 🎯 Vorlage für Form-Template

Hier ist eine Vorlage für `notarstelle_form.html`:

```html
{% extends 'base_modern.html' %}
{% load static %}

{% block title %}{{ title }} - Notariatskammer{% endblock %}

{% block content %}
<div class="page-header">
    <div class="page-header-top">
        <div>
            <h1 class="page-title">{{ title }}</h1>
        </div>
    </div>
</div>

<div style="max-width: 800px; margin: 0 auto;">
    <div class="card">
        <div class="card-body">
            <form method="post">
                {% csrf_token %}

                <!-- Formular-Felder -->
                {% for field in form %}
                <div class="form-group" style="margin-bottom: var(--spacing-md);">
                    <label class="form-label">{{ field.label }}</label>
                    {{ field }}
                    {% if field.help_text %}
                    <small style="display: block; margin-top: 4px; font-size: 13px; color: var(--text-secondary);">
                        {{ field.help_text }}
                    </small>
                    {% endif %}
                    {% if field.errors %}
                    <div style="color: var(--danger); font-size: 13px; margin-top: 4px;">
                        {{ field.errors }}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}

                <!-- Buttons -->
                <div style="display: flex; justify-content: space-between; gap: var(--spacing-md); margin-top: var(--spacing-lg);">
                    <a href="{% url 'notarstellen_liste' %}" class="btn btn-secondary">
                        <i class="bi bi-arrow-left"></i> Zurück
                    </a>
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check"></i> {{ submit_text }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

## 🎯 Vorlage für Lösch-Bestätigung

Hier ist eine Vorlage für `notarstelle_loeschen.html`:

```html
{% extends 'base_modern.html' %}
{% load static %}

{% block title %}Notarstelle löschen - Notariatskammer{% endblock %}

{% block content %}
<div class="page-header">
    <div class="page-header-top">
        <div>
            <h1 class="page-title">Notarstelle löschen</h1>
        </div>
    </div>
</div>

<div style="max-width: 600px; margin: 0 auto;">
    <div class="card" style="border: 2px solid var(--danger);">
        <div class="card-body">
            <div class="alert alert-warning" style="margin-bottom: var(--spacing-lg);">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Achtung!</strong> Diese Aktion kann nicht rückgängig gemacht werden.
            </div>

            <p style="margin-bottom: var(--spacing-md);">
                Möchten Sie die folgende Notarstelle wirklich löschen?
            </p>

            <div style="padding: var(--spacing-md); background: var(--bg-primary); border-radius: var(--border-radius); margin-bottom: var(--spacing-lg);">
                <div style="font-weight: 600; margin-bottom: 4px;">{{ notarstelle.name }}</div>
                <div style="font-size: 14px; color: var(--text-secondary);">
                    {{ notarstelle.strasse }}, {{ notarstelle.plz }} {{ notarstelle.stadt }}
                </div>
                <div style="font-size: 14px; color: var(--text-secondary);">
                    Notarnummer: {{ notarstelle.notarnummer }}
                </div>
            </div>

            <form method="post">
                {% csrf_token %}
                <div style="display: flex; justify-content: space-between; gap: var(--spacing-md);">
                    <a href="{% url 'notarstelle_detail' notarstelle.id %}" class="btn btn-secondary">
                        <i class="bi bi-arrow-left"></i> Abbrechen
                    </a>
                    <button type="submit" class="btn btn-danger">
                        <i class="bi bi-trash"></i> Endgültig löschen
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

## 💡 Wie weiter?

Die Templates können einfach kopiert und für Notare/Anwärter angepasst werden:
1. `notarstelle_form.html` → `notar_form.html` (nur URL ändern)
2. `notarstelle_loeschen.html` → `notar_loeschen.html` (nur Felder anpassen)

Das Muster für die Views ist identisch, nur Model-Namen ändern!
