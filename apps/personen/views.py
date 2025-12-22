"""
Views für Personen-Verwaltung (Notare und Notariatskandidat).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from .models import Notar, NotarAnwaerter
from apps.notarstellen.models import Notarstelle
from .forms import NotarForm, NotarAnwaerterForm


@login_required
def notare_liste_view(request):
    """Liste aller Notare."""
    # Such- und Filterparameter
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    notarstelle_filter = request.GET.get('notarstelle', '')

    # Basis-Queryset
    notare = Notar.objects.select_related('notarstelle', 'notarstelle__sprengel').order_by('nachname', 'vorname')

    # Suche
    if search:
        notare = notare.filter(
            Q(vorname__icontains=search) |
            Q(nachname__icontains=search) |
            Q(notar_id__icontains=search) |
            Q(email__icontains=search)
        )

    # Status-Filter
    if status_filter == 'aktiv':
        notare = notare.filter(ist_aktiv=True, ende_datum__isnull=True)
    elif status_filter == 'inaktiv':
        notare = notare.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

    # Notarstellen-Filter
    if notarstelle_filter:
        notare = notare.filter(notarstelle_id=notarstelle_filter)

    # Statistiken
    stats = {
        'total': Notar.objects.count(),
        'aktiv': Notar.objects.filter(ist_aktiv=True, ende_datum__isnull=True).count(),
        'inaktiv': Notar.objects.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False)).count(),
    }

    # Notarstellen für Filter-Dropdown
    notarstellen = Notarstelle.objects.filter(ist_aktiv=True).order_by('name')

    context = {
        'notare': notare,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'notarstelle_filter': notarstelle_filter,
        'notarstellen': notarstellen,
    }

    return render(request, 'personen/notare_liste.html', context)


@login_required
def notar_detail_view(request, notar_id):
    """Detail-Ansicht eines Notars."""
    notar = get_object_or_404(
        Notar.objects.select_related('notarstelle', 'notarstelle__sprengel'),
        notar_id=notar_id
    )

    # Workflows des Notars (falls er vorher Kandidat war)
    workflows = []
    if notar.war_vorher_anwaerter:
        from apps.workflows.models import WorkflowInstanz
        # Versuche Workflows zu finden, die mit diesem Notar verknüpft sind
        workflows = WorkflowInstanz.objects.filter(
            betroffene_notare=notar
        ).order_by('-erstellt_am')[:5]

    context = {
        'notar': notar,
        'workflows': workflows,
    }

    return render(request, 'personen/notar_detail.html', context)


@login_required
def anwaerter_liste_view(request):
    """Liste aller Notariatskandidat."""
    # Such- und Filterparameter
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    betreuender_notar_filter = request.GET.get('betreuender_notar', '')

    # Basis-Queryset
    anwaerter = NotarAnwaerter.objects.select_related(
        'betreuender_notar',
        'notarstelle',
        'notarstelle__sprengel'
    ).order_by('nachname', 'vorname')

    # Suche
    if search:
        anwaerter = anwaerter.filter(
            Q(vorname__icontains=search) |
            Q(nachname__icontains=search) |
            Q(anwaerter_id__icontains=search) |
            Q(email__icontains=search)
        )

    # Status-Filter
    if status_filter == 'aktiv':
        anwaerter = anwaerter.filter(ist_aktiv=True, ende_datum__isnull=True)
    elif status_filter == 'inaktiv':
        anwaerter = anwaerter.filter(Q(ist_aktiv=False) | Q(ende_datum__isnull=False))

    # Betreuender Notar Filter
    if betreuender_notar_filter:
        anwaerter = anwaerter.filter(betreuender_notar_id=betreuender_notar_filter)

    # Statistiken
    stats = {
        'total': NotarAnwaerter.objects.count(),
        'aktiv': NotarAnwaerter.objects.filter(ist_aktiv=True, ende_datum__isnull=True).count(),
        'mit_betreuung': NotarAnwaerter.objects.filter(betreuender_notar__isnull=False).count(),
    }

    # Betreuende Notare für Filter
    betreuende_notare = Notar.objects.filter(ist_aktiv=True).order_by('nachname', 'vorname')

    context = {
        'anwaerter': anwaerter,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'betreuender_notar_filter': betreuender_notar_filter,
        'betreuende_notare': betreuende_notare,
    }

    return render(request, 'personen/anwaerter_liste.html', context)


@login_required
def anwaerter_detail_view(request, anwaerter_id):
    """Detail-Ansicht eines Notariatskandidats."""
    anwaerter = get_object_or_404(
        NotarAnwaerter.objects.select_related('betreuender_notar', 'notarstelle', 'notarstelle__sprengel'),
        anwaerter_id=anwaerter_id
    )

    # Workflows des Anwärters
    from apps.workflows.models import WorkflowInstanz
    workflows = WorkflowInstanz.objects.filter(
        betroffene_kandidaten=anwaerter
    ).select_related('workflow_typ', 'erstellt_von').order_by('-erstellt_am')

    context = {
        'anwaerter': anwaerter,
        'workflows': workflows,
    }

    return render(request, 'personen/anwaerter_detail.html', context)


# ===== CRUD Views für Notare =====

@login_required
def notar_erstellen_view(request):
    """Erstellen eines neuen Notars."""
    if request.method == 'POST':
        form = NotarForm(request.POST)
        if form.is_valid():
            notar = form.save()
            messages.success(request, f'Notar "{notar.get_voller_name()}" wurde erfolgreich erstellt.')
            return redirect('notar_detail', notar_id=notar.notar_id)
    else:
        # Automatische ID-Generierung
        form = NotarForm(initial={'notar_id': Notar.generate_next_id()})

    context = {
        'form': form,
        'title': 'Neuer Notar',
        'submit_text': 'Erstellen',
    }
    return render(request, 'personen/notar_form.html', context)


@login_required
def notar_bearbeiten_view(request, notar_id):
    """Bearbeiten eines Notars."""
    notar = get_object_or_404(Notar, notar_id=notar_id)

    if request.method == 'POST':
        form = NotarForm(request.POST, instance=notar)
        if form.is_valid():
            notar = form.save()
            messages.success(request, f'Notar "{notar.get_voller_name()}" wurde erfolgreich aktualisiert.')
            return redirect('notar_detail', notar_id=notar.notar_id)
    else:
        form = NotarForm(instance=notar)

    context = {
        'form': form,
        'notar': notar,
        'title': f'Notar bearbeiten: {notar.get_voller_name()}',
        'submit_text': 'Speichern',
    }
    return render(request, 'personen/notar_form.html', context)


@login_required
def notar_loeschen_view(request, notar_id):
    """Löschen eines Notars."""
    notar = get_object_or_404(Notar, notar_id=notar_id)

    if request.method == 'POST':
        name = notar.get_voller_name()
        notar.delete()
        messages.success(request, f'Notar "{name}" wurde gelöscht.')
        return redirect('notare_liste')

    context = {
        'notar': notar,
    }
    return render(request, 'personen/notar_loeschen.html', context)


# ===== CRUD Views für Notariatskandidat =====

@login_required
def anwaerter_erstellen_view(request):
    """Erstellen eines neuen Notariatskandidats."""
    if request.method == 'POST':
        form = NotarAnwaerterForm(request.POST)
        if form.is_valid():
            anwaerter = form.save()
            messages.success(request, f'Notariatskandidat "{anwaerter.get_voller_name()}" wurde erfolgreich erstellt.')
            return redirect('anwaerter_detail', anwaerter_id=anwaerter.anwaerter_id)
    else:
        # Automatisch die nächste ID generieren
        next_id = NotarAnwaerter.generate_next_id()
        form = NotarAnwaerterForm(initial={'anwaerter_id': next_id})

    context = {
        'form': form,
        'title': 'Neuer Notariatskandidat',
        'submit_text': 'Erstellen',
    }
    return render(request, 'personen/anwaerter_form.html', context)


@login_required
def anwaerter_bearbeiten_view(request, anwaerter_id):
    """Bearbeiten eines Notariatskandidats."""
    anwaerter = get_object_or_404(NotarAnwaerter, anwaerter_id=anwaerter_id)

    if request.method == 'POST':
        form = NotarAnwaerterForm(request.POST, instance=anwaerter)
        if form.is_valid():
            anwaerter = form.save()
            messages.success(request, f'Notariatskandidat "{anwaerter.get_voller_name()}" wurde erfolgreich aktualisiert.')
            return redirect('anwaerter_detail', anwaerter_id=anwaerter.anwaerter_id)
    else:
        form = NotarAnwaerterForm(instance=anwaerter)

    context = {
        'form': form,
        'anwaerter': anwaerter,
        'title': f'Notariatskandidat bearbeiten: {anwaerter.get_voller_name()}',
        'submit_text': 'Speichern',
    }
    return render(request, 'personen/anwaerter_form.html', context)


@login_required
def anwaerter_loeschen_view(request, anwaerter_id):
    """Löschen eines Notariatskandidats."""
    anwaerter = get_object_or_404(NotarAnwaerter, anwaerter_id=anwaerter_id)

    if request.method == 'POST':
        name = anwaerter.get_voller_name()
        anwaerter.delete()
        messages.success(request, f'Notariatskandidat "{name}" wurde gelöscht.')
        return redirect('anwaerter_liste')

    context = {
        'anwaerter': anwaerter,
    }
    return render(request, 'personen/anwaerter_loeschen.html', context)


@login_required
def anwaerter_zu_notar_view(request, anwaerter_id):
    """Wandelt einen Notariatskandidat in einen Notar um."""
    anwaerter = get_object_or_404(NotarAnwaerter, anwaerter_id=anwaerter_id)

    if request.method == 'POST':
        # Generiere neue Notar-ID
        import re
        letzte_notar = Notar.objects.filter(
            notar_id__startswith='NOT-'
        ).order_by('-notar_id').first()

        if letzte_notar and letzte_notar.notar_id:
            match = re.search(r'NOT-(\d+)', letzte_notar.notar_id)
            if match:
                nummer = int(match.group(1)) + 1
            else:
                nummer = 1
        else:
            nummer = 1

        neue_notar_id = f'NOT-{nummer:03d}'

        # Erstelle neuen Notar aus Kandidaten-Daten
        notar = Notar.objects.create(
            notar_id=neue_notar_id,
            vorname=anwaerter.vorname,
            nachname=anwaerter.nachname,
            titel=anwaerter.titel,
            email=anwaerter.email,
            telefon=anwaerter.telefon,
            notarstelle=anwaerter.notarstelle,
            bestellt_am=request.POST.get('bestellt_am'),
            beginn_datum=anwaerter.beginn_datum,
            war_vorher_anwaerter=True,
            ist_aktiv=True,
            notiz=f'Umgewandelt von Kandidat {anwaerter.anwaerter_id}\n\n{anwaerter.notiz or ""}'
        )

        # Deaktiviere den Kandidat
        anwaerter.ist_aktiv = False
        anwaerter.save()

        messages.success(
            request,
            f'{anwaerter.get_voller_name()} wurde erfolgreich zum Notar ernannt (ID: {notar.notar_id}).'
        )
        return redirect('notar_detail', notar_id=notar.notar_id)

    context = {
        'anwaerter': anwaerter,
    }
    return render(request, 'personen/anwaerter_zu_notar.html', context)


# ===== Notar-Vergleich =====

@login_required
def notare_vergleichen_view(request):
    """Vergleichsansicht für bis zu 3 Notare."""
    # Notar-IDs aus GET-Parametern holen
    notar_ids = request.GET.getlist('notare')

    # Maximal 3 Notare erlauben
    if len(notar_ids) > 3:
        messages.warning(request, 'Sie können maximal 3 Notare gleichzeitig vergleichen.')
        notar_ids = notar_ids[:3]

    if len(notar_ids) < 2:
        messages.error(request, 'Bitte wählen Sie mindestens 2 Notare zum Vergleichen aus.')
        return redirect('notare_liste')

    # Notare laden
    notare = Notar.objects.filter(notar_id__in=notar_ids).select_related('notarstelle')

    # PDF-Export
    if request.GET.get('format') == 'pdf':
        return notare_vergleich_pdf_export(notare)

    context = {
        'notare': notare,
    }

    return render(request, 'personen/notare_vergleich.html', context)


def notare_vergleich_pdf_export(notare):
    """Exportiert den Notar-Vergleich als PDF."""
    from django.http import HttpResponse
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO

    # PDF-Buffer
    buffer = BytesIO()

    # PDF im Querformat erstellen
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    # Container für PDF-Elemente
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#9EBDD5'),
        spaceAfter=20,
    )

    # Titel
    elements.append(Paragraph('Notar-Vergleich', title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Style für kleine Texte
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )

    # Vergleichstabelle erstellen
    data = []

    # Header
    header = ['Eigenschaft'] + [notar.get_voller_name() for notar in notare]
    data.append(header)

    # Datenzeilen mit Paragraph-Wrapping für lange Texte
    rows = [
        ('Notar-ID', [notar.notar_id for notar in notare]),
        ('Titel', [notar.titel or '—' for notar in notare]),
        ('E-Mail', [Paragraph(notar.email or '—', small_style) for notar in notare]),
        ('Telefon', [notar.telefon or '—' for notar in notare]),
        ('Notarstelle', [Paragraph(notar.notarstelle.name, small_style) for notar in notare]),
        ('Ort', [notar.notarstelle.stadt for notar in notare]),
        ('Bestellt am', [notar.bestellt_am.strftime('%d.%m.%Y') if notar.bestellt_am else '—' for notar in notare]),
        ('Beginn', [notar.beginn_datum.strftime('%d.%m.%Y') if notar.beginn_datum else '—' for notar in notare]),
        ('Ende', [notar.ende_datum.strftime('%d.%m.%Y') if notar.ende_datum else '—' for notar in notare]),
        ('Status', ['Aktiv' if notar.ist_aktiv and not notar.ende_datum else 'Inaktiv' for notar in notare]),
        ('War Kandidat', ['Ja' if notar.war_vorher_anwaerter else 'Nein' for notar in notare]),
    ]

    for label, values in rows:
        data.append([label] + values)

    # Tabelle erstellen - mehr Platz für Daten-Spalten
    col_width = (landscape(A4)[0] - 2*cm - 4.5*cm) / len(notare)  # Verfügbarer Platz gleichmäßig verteilen
    table = Table(data, colWidths=[4.5*cm] + [col_width] * len(notare))

    # Tabellen-Style
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9EBDD5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),

        # Erste Spalte (Labels)
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F5F5F7')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, -1), 9),

        # Daten
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),

        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#9EBDD5')),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))

    elements.append(table)

    # Fußnote
    elements.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
    )
    from django.utils import timezone as tz
    elements.append(Paragraph(
        f'Erstellt am: {tz.now().strftime("%d.%m.%Y %H:%M")} | Notariatskammer Verwaltung',
        footer_style
    ))

    # PDF generieren
    doc.build(elements)

    # Response
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="notar_vergleich.pdf"'
    response.write(pdf)

    return response


@login_required
def anwaerter_vergleichen_view(request):
    """Kandidat nebeneinander vergleichen."""
    anwaerter_ids = request.GET.getlist('anwaerter')

    if not anwaerter_ids:
        messages.warning(request, 'Bitte wählen Sie mindestens 2 Kandidat zum Vergleichen aus.')
        return redirect('anwaerter_liste')

    if len(anwaerter_ids) > 3:
        messages.warning(request, 'Sie können maximal 3 Kandidat gleichzeitig vergleichen.')
        return redirect('anwaerter_liste')

    # Kandidat laden
    anwaerter = NotarAnwaerter.objects.filter(anwaerter_id__in=anwaerter_ids).select_related(
        'notarstelle', 'betreuender_notar'
    )

    if anwaerter.count() != len(anwaerter_ids):
        messages.error(request, 'Einige der ausgewählten Kandidat wurden nicht gefunden.')
        return redirect('anwaerter_liste')

    # PDF Export?
    if request.GET.get('format') == 'pdf':
        return anwaerter_vergleich_pdf_export(request, anwaerter)

    context = {
        'anwaerter': anwaerter,
    }
    return render(request, 'personen/anwaerter_vergleich.html', context)


def anwaerter_vergleich_pdf_export(request, anwaerter):
    """Kandidaten-Vergleich als PDF exportieren."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                           leftMargin=1.5*cm, rightMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Titel
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#9EBDD5'),
        spaceAfter=20,
    )
    elements.append(Paragraph('Kandidaten-Vergleich', title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Style für kleine Texte
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )

    # Tabellendaten vorbereiten
    data = []

    # Header
    header = ['Eigenschaft'] + [anw.get_voller_name() for anw in anwaerter]
    data.append(header)

    # Datenzeilen mit Paragraph-Wrapping für lange Texte
    rows = [
        ('Kandidaten-ID', [anw.anwaerter_id for anw in anwaerter]),
        ('Titel', [anw.titel or '—' for anw in anwaerter]),
        ('E-Mail', [Paragraph(anw.email or '—', small_style) for anw in anwaerter]),
        ('Telefon', [anw.telefon or '—' for anw in anwaerter]),
        ('Notarstelle', [Paragraph(anw.notarstelle.name, small_style) for anw in anwaerter]),
        ('Ort', [anw.notarstelle.stadt for anw in anwaerter]),
        ('Betreuender Notar', [Paragraph(anw.betreuender_notar.get_voller_name(), small_style) if anw.betreuender_notar else '—' for anw in anwaerter]),
        ('Zugelassen am', [anw.zugelassen_am.strftime('%d.%m.%Y') if anw.zugelassen_am else '—' for anw in anwaerter]),
        ('Beginn', [anw.beginn_datum.strftime('%d.%m.%Y') if anw.beginn_datum else '—' for anw in anwaerter]),
        ('Ende', [anw.ende_datum.strftime('%d.%m.%Y') if anw.ende_datum else '—' for anw in anwaerter]),
        ('Status', ['Aktiv' if anw.ist_aktiv and not anw.ende_datum else 'Inaktiv' for anw in anwaerter]),
    ]

    for label, values in rows:
        data.append([label] + values)

    # Tabelle erstellen - mehr Platz für Daten-Spalten
    col_width = (landscape(A4)[0] - 2*cm - 4.5*cm) / len(anwaerter)  # Verfügbarer Platz gleichmäßig verteilen
    table = Table(data, colWidths=[4.5*cm] + [col_width] * len(anwaerter))

    # Tabellenstil
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9EBDD5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),

        # Erste Spalte (Labels)
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F5F5F7')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, -1), 9),

        # Daten
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (1, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#FAFAFA')]),

        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#9EBDD5')),

        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))

    elements.append(table)

    # Fußnote
    elements.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
    )
    from django.utils import timezone as tz
    elements.append(Paragraph(
        f'Erstellt am: {tz.now().strftime("%d.%m.%Y %H:%M")} | Notariatskammer Verwaltung',
        footer_style
    ))

    # PDF generieren
    doc.build(elements)

    # Response
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="anwaerter_vergleich.pdf"'
    response.write(pdf)

    return response


# ===== AI Agent für Lebenslauf-Analyse =====

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import base64
import re
import os
import requests

@login_required
@require_http_methods(["POST"])
def ai_extract_cv_data(request):
    """
    Extrahiert Daten aus einem Lebenslauf-PDF mittels OpenRouter AI.

    Erwartet: PDF-Datei als multipart/form-data
    Gibt zurück: JSON mit extrahierten Feldern
    """
    try:
        # PDF-Datei aus Request holen
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'Keine PDF-Datei hochgeladen'}, status=400)

        pdf_file = request.FILES['pdf_file']

        # PDF zu Base64 konvertieren
        pdf_content = pdf_file.read()
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        api_url = "https://openrouter.ai/api/v1/chat/completions"
        api_key = os.environ.get('OPENROUTER_API_KEY')

        if not api_key:
            return JsonResponse({
                'error': 'OpenRouter API-Key nicht konfiguriert',
                'message': 'Bitte OPENROUTER_API_KEY in .env Datei setzen'
            }, status=500)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Notariatskammer Verwaltung - CV Extraktion",
        }

        # Prompt für die AI
        prompt = """Analysiere diesen Lebenslauf und extrahiere die folgenden Informationen im JSON-Format:

{
  "titel": "Akademischer Titel (z.B. Dr., Mag., Prof. Dr.)",
  "vorname": "Vorname",
  "nachname": "Nachname",
  "email": "E-Mail-Adresse",
  "telefon": "Telefonnummer",
  "zugelassen_am": "Datum der Zulassung als Notariatskandidat (Format: YYYY-MM-DD)",
  "beginn_datum": "Beginn der Tätigkeit (Format: YYYY-MM-DD)"
}

Wichtig:
- Gib NUR das JSON-Objekt zurück, keine zusätzlichen Erklärungen
- Falls eine Information nicht gefunden wurde, setze den Wert auf null
- Datumsangaben immer im Format YYYY-MM-DD
- Telefonnummer im Format: +43 ... (österreichisches Format)
"""

        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ]
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            error_details = response.text
            try:
                error_json = response.json()
                error_message = error_json.get('error', {}).get('message', error_details)
            except:
                error_message = error_details

            return JsonResponse({
                'error': f'OpenRouter API Fehler: {response.status_code}',
                'message': error_message,
                'details': error_details[:500]  # Nur ersten 500 Zeichen
            }, status=500)

        result = response.json()

        # AI-Antwort extrahieren
        ai_response = result['choices'][0]['message']['content']

        # JSON aus der Antwort extrahieren
        # Manchmal gibt die AI zusätzlichen Text zurück, also suchen wir nach dem JSON-Block
        json_match = re.search(r'\{[\s\S]*\}', ai_response)

        if json_match:
            extracted_data = json.loads(json_match.group())
        else:
            extracted_data = json.loads(ai_response)

        return JsonResponse({
            'success': True,
            'data': extracted_data
        })

    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': 'Fehler beim Parsen der AI-Antwort',
            'details': str(e),
            'raw_response': ai_response if 'ai_response' in locals() else None
        }, status=500)
    except requests.RequestException as e:
        return JsonResponse({
            'error': 'Fehler bei der Kommunikation mit OpenRouter',
            'details': str(e)
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': 'Unerwarteter Fehler',
            'details': str(e)
        }, status=500)
