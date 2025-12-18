"""
Views für Aktenzeichen-Verwaltung.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Aktenzeichen, Nummernsequenz
from .forms import AktenzeichenForm


@login_required
def aktenzeichen_liste_view(request):
    """Liste aller Aktenzeichen."""
    # Such- und Filterparameter
    search = request.GET.get('search', '')
    kategorie_filter = request.GET.get('kategorie', '')
    jahr_filter = request.GET.get('jahr', '')

    # Basis-Queryset
    aktenzeichen = Aktenzeichen.objects.select_related('sequenz').order_by('-jahr', '-laufnummer')

    # Suche
    if search:
        aktenzeichen = aktenzeichen.filter(
            Q(vollstaendige_nummer__icontains=search) |
            Q(beschreibung__icontains=search)
        )

    # Kategorie-Filter
    if kategorie_filter:
        aktenzeichen = aktenzeichen.filter(kategorie=kategorie_filter)

    # Jahr-Filter
    if jahr_filter:
        aktenzeichen = aktenzeichen.filter(jahr=jahr_filter)

    # Statistiken
    stats = {
        'total': Aktenzeichen.objects.count(),
        'dieses_jahr': Aktenzeichen.objects.filter(
            jahr__year=Aktenzeichen.objects.first().jahr if Aktenzeichen.objects.exists() else 0
        ).count() if Aktenzeichen.objects.exists() else 0,
    }

    # Kategorien für Filter
    kategorien = Aktenzeichen.KATEGORIE_CHOICES

    # Jahre für Filter (alle Jahre mit Aktenzeichen)
    jahre = Aktenzeichen.objects.values_list('jahr', flat=True).distinct().order_by('-jahr')

    context = {
        'aktenzeichen': aktenzeichen,
        'stats': stats,
        'search': search,
        'kategorie_filter': kategorie_filter,
        'jahr_filter': jahr_filter,
        'kategorien': kategorien,
        'jahre': jahre,
    }

    return render(request, 'aktenzeichen/aktenzeichen_liste.html', context)


@login_required
def aktenzeichen_detail_view(request, aktenzeichen_id):
    """Detail-Ansicht eines Aktenzeichens."""
    aktenzeichen = get_object_or_404(
        Aktenzeichen.objects.select_related('sequenz'),
        id=aktenzeichen_id
    )

    # Zugehöriger Workflow (falls vorhanden)
    workflow = None
    try:
        if hasattr(aktenzeichen, 'workflow'):
            workflow = aktenzeichen.workflow
    except:
        pass

    context = {
        'aktenzeichen': aktenzeichen,
        'workflow': workflow,
    }

    return render(request, 'aktenzeichen/aktenzeichen_detail.html', context)


@login_required
def aktenzeichen_erstellen_view(request):
    """Erstellen eines neuen Aktenzeichens."""
    if request.method == 'POST':
        form = AktenzeichenForm(request.POST)
        if form.is_valid():
            aktenzeichen = form.save()
            messages.success(
                request,
                f'Aktenzeichen "{aktenzeichen.vollstaendige_nummer}" wurde erfolgreich erstellt.'
            )
            return redirect('aktenzeichen_detail', aktenzeichen_id=aktenzeichen.id)
    else:
        form = AktenzeichenForm()

    # Vorschau der nächsten Nummer für jede Kategorie
    from django.utils import timezone
    aktuelles_jahr = timezone.now().year
    vorschau = {}

    kategorie_praefix_map = {
        'Bestellung': 'BES',
        'Zulassung': 'ZUL',
        'Aufsicht': 'AUF',
        'Allgemein': 'ALL',
    }

    for kategorie, praefix in kategorie_praefix_map.items():
        try:
            sequenz = Nummernsequenz.objects.get(jahr=aktuelles_jahr, praefix=praefix)
            naechste = sequenz.vorschau_naechste_nummer()
            vorschau[kategorie] = f"{praefix}-{aktuelles_jahr}-{str(naechste).zfill(4)}"
        except Nummernsequenz.DoesNotExist:
            vorschau[kategorie] = f"{praefix}-{aktuelles_jahr}-0001"

    context = {
        'form': form,
        'title': 'Neues Aktenzeichen',
        'submit_text': 'Erstellen',
        'vorschau': vorschau,
    }
    return render(request, 'aktenzeichen/aktenzeichen_form.html', context)


@login_required
def aktenzeichen_bearbeiten_view(request, aktenzeichen_id):
    """Bearbeiten eines Aktenzeichens (nur Beschreibung)."""
    aktenzeichen = get_object_or_404(Aktenzeichen, id=aktenzeichen_id)

    if request.method == 'POST':
        # Nur Beschreibung kann bearbeitet werden
        beschreibung = request.POST.get('beschreibung', '')
        aktenzeichen.beschreibung = beschreibung
        aktenzeichen.save()
        messages.success(
            request,
            f'Aktenzeichen "{aktenzeichen.vollstaendige_nummer}" wurde erfolgreich aktualisiert.'
        )
        return redirect('aktenzeichen_detail', aktenzeichen_id=aktenzeichen.id)

    context = {
        'aktenzeichen': aktenzeichen,
        'title': f'Aktenzeichen bearbeiten: {aktenzeichen.vollstaendige_nummer}',
        'submit_text': 'Speichern',
    }
    return render(request, 'aktenzeichen/aktenzeichen_bearbeiten.html', context)


@login_required
def aktenzeichen_loeschen_view(request, aktenzeichen_id):
    """Löschen eines Aktenzeichens."""
    aktenzeichen = get_object_or_404(Aktenzeichen, id=aktenzeichen_id)

    if request.method == 'POST':
        nummer = aktenzeichen.vollstaendige_nummer
        try:
            aktenzeichen.delete()
            messages.success(request, f'Aktenzeichen "{nummer}" wurde gelöscht.')
            return redirect('aktenzeichen_liste')
        except Exception as e:
            messages.error(
                request,
                f'Fehler beim Löschen: {str(e)}. Das Aktenzeichen ist möglicherweise mit einem Workflow verknüpft.'
            )
            return redirect('aktenzeichen_detail', aktenzeichen_id=aktenzeichen_id)

    context = {
        'aktenzeichen': aktenzeichen,
    }
    return render(request, 'aktenzeichen/aktenzeichen_loeschen.html', context)
