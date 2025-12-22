"""
Views für Notarstellen-Verwaltung.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import Notarstelle
from .forms import NotarstelleForm


@login_required
def notarstellen_liste_view(request):
    """Liste aller Notarstellen."""
    # Such- und Filterparameter
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    bundesland_filter = request.GET.get('bundesland', '')

    # Basis-Queryset
    notarstellen = Notarstelle.objects.annotate(
        anzahl_notare=Count('notare', filter=Q(notare__ist_aktiv=True))
    ).order_by('bezeichnung')

    # Suche
    if search:
        notarstellen = notarstellen.filter(
            Q(bezeichnung__icontains=search) |
            Q(name__icontains=search) |
            Q(stadt__icontains=search)
        )

    # Status-Filter
    if status_filter == 'aktiv':
        notarstellen = notarstellen.filter(ist_aktiv=True)
    elif status_filter == 'inaktiv':
        notarstellen = notarstellen.filter(ist_aktiv=False)

    # Bundesland-Filter
    if bundesland_filter:
        notarstellen = notarstellen.filter(bundesland=bundesland_filter)

    # Statistiken
    stats = {
        'total': Notarstelle.objects.count(),
        'aktiv': Notarstelle.objects.filter(ist_aktiv=True).count(),
        'besetzt': Notarstelle.objects.filter(
            notare__ist_aktiv=True,
            notare__ende_datum__isnull=True
        ).distinct().count(),
    }

    # Bundesländer für Filter
    bundeslaender = Notarstelle.objects.values_list('bundesland', flat=True).distinct().order_by('bundesland')

    context = {
        'notarstellen': notarstellen,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'bundesland_filter': bundesland_filter,
        'bundeslaender': bundeslaender,
    }

    return render(request, 'notarstellen/notarstellen_liste.html', context)


@login_required
def notarstelle_detail_view(request, bezeichnung):
    """Detail-Ansicht einer Notarstelle."""
    notarstelle = get_object_or_404(Notarstelle, bezeichnung=bezeichnung)

    # Notare und Kandidat dieser Notarstelle
    notare = notarstelle.notare.filter(ist_aktiv=True).order_by('nachname', 'vorname')
    anwaerter = notarstelle.anwaerter.filter(ist_aktiv=True).order_by('nachname', 'vorname')

    context = {
        'notarstelle': notarstelle,
        'notare': notare,
        'anwaerter': anwaerter,
    }

    return render(request, 'notarstellen/notarstelle_detail.html', context)


@login_required
def notarstelle_erstellen_view(request):
    """Erstellen einer neuen Notarstelle."""
    if request.method == 'POST':
        form = NotarstelleForm(request.POST)
        if form.is_valid():
            notarstelle = form.save()
            messages.success(request, f'Notarstelle "{notarstelle.name}" wurde erfolgreich erstellt.')
            return redirect('notarstelle_detail', bezeichnung=notarstelle.bezeichnung)
    else:
        # Automatische Bezeichnung-Generierung
        form = NotarstelleForm(initial={'bezeichnung': Notarstelle.generate_next_id()})

    context = {
        'form': form,
        'title': 'Neue Notarstelle',
        'submit_text': 'Erstellen',
    }
    return render(request, 'notarstellen/notarstelle_form.html', context)


@login_required
def notarstelle_bearbeiten_view(request, bezeichnung):
    """Bearbeiten einer Notarstelle."""
    notarstelle = get_object_or_404(Notarstelle, bezeichnung=bezeichnung)

    if request.method == 'POST':
        form = NotarstelleForm(request.POST, instance=notarstelle)
        if form.is_valid():
            notarstelle = form.save()
            messages.success(request, f'Notarstelle "{notarstelle.name}" wurde erfolgreich aktualisiert.')
            return redirect('notarstelle_detail', bezeichnung=notarstelle.bezeichnung)
    else:
        form = NotarstelleForm(instance=notarstelle)

    context = {
        'form': form,
        'notarstelle': notarstelle,
        'title': f'Notarstelle bearbeiten: {notarstelle.name}',
        'submit_text': 'Speichern',
    }
    return render(request, 'notarstellen/notarstelle_form.html', context)


@login_required
def notarstelle_loeschen_view(request, bezeichnung):
    """Löschen einer Notarstelle."""
    notarstelle = get_object_or_404(Notarstelle, bezeichnung=bezeichnung)

    if request.method == 'POST':
        name = notarstelle.name
        notarstelle.delete()
        messages.success(request, f'Notarstelle "{name}" wurde gelöscht.')
        return redirect('notarstellen_liste')

    context = {
        'notarstelle': notarstelle,
    }
    return render(request, 'notarstellen/notarstelle_loeschen.html', context)
