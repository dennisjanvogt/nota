"""
Views für Sprengel-Verwaltung.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import Sprengel
from .forms import SprengelForm


@login_required
def sprengel_liste_view(request):
    """Zeigt Liste aller Sprengel."""
    # Filter-Parameter
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    bundesland_filter = request.GET.get('bundesland', '')

    # Basis-Queryset
    sprengel = Sprengel.objects.annotate(
        anzahl_notarstellen_count=Count('notarstellen', filter=Q(notarstellen__ist_aktiv=True))
    ).order_by('bezeichnung')

    # Suche
    if search:
        sprengel = sprengel.filter(
            Q(bezeichnung__icontains=search) |
            Q(name__icontains=search) |
            Q(gerichtsbezirk__icontains=search)
        )

    # Status-Filter
    if status_filter == 'aktiv':
        sprengel = sprengel.filter(ist_aktiv=True)
    elif status_filter == 'inaktiv':
        sprengel = sprengel.filter(ist_aktiv=False)

    # Bundesland-Filter
    if bundesland_filter:
        sprengel = sprengel.filter(bundesland=bundesland_filter)

    # Statistiken
    stats = {
        'total': Sprengel.objects.count(),
        'aktiv': Sprengel.objects.filter(ist_aktiv=True).count(),
        'mit_notarstellen': Sprengel.objects.filter(
            notarstellen__ist_aktiv=True
        ).distinct().count(),
    }

    # Bundesländer für Filter
    bundeslaender = Sprengel.objects.values_list('bundesland', flat=True).distinct().order_by('bundesland')

    context = {
        'sprengel': sprengel,
        'stats': stats,
        'search': search,
        'status_filter': status_filter,
        'bundesland_filter': bundesland_filter,
        'bundeslaender': bundeslaender,
    }

    return render(request, 'sprengel/sprengel_liste.html', context)


@login_required
def sprengel_detail_view(request, bezeichnung):
    """Zeigt Details eines Sprengels."""
    sprengel = get_object_or_404(Sprengel, bezeichnung=bezeichnung)

    # Notarstellen in diesem Sprengel
    notarstellen = sprengel.notarstellen.all().order_by('name')

    context = {
        'sprengel': sprengel,
        'notarstellen': notarstellen,
    }

    return render(request, 'sprengel/sprengel_detail.html', context)


@login_required
def sprengel_erstellen_view(request):
    """Erstellt einen neuen Sprengel."""
    if request.method == 'POST':
        form = SprengelForm(request.POST)
        if form.is_valid():
            sprengel = form.save()
            messages.success(request, f'Sprengel "{sprengel.name}" wurde erfolgreich erstellt.')
            return redirect('sprengel_detail', bezeichnung=sprengel.bezeichnung)
    else:
        # Auto-generiere die nächste ID
        next_id = Sprengel.generate_next_id()
        form = SprengelForm(initial={'bezeichnung': next_id})

    context = {
        'form': form,
        'title': 'Neuer Sprengel',
    }

    return render(request, 'sprengel/sprengel_form.html', context)


@login_required
def sprengel_bearbeiten_view(request, bezeichnung):
    """Bearbeitet einen Sprengel."""
    sprengel = get_object_or_404(Sprengel, bezeichnung=bezeichnung)

    if request.method == 'POST':
        form = SprengelForm(request.POST, instance=sprengel)
        if form.is_valid():
            sprengel = form.save()
            messages.success(request, f'Sprengel "{sprengel.name}" wurde erfolgreich aktualisiert.')
            return redirect('sprengel_detail', bezeichnung=sprengel.bezeichnung)
    else:
        form = SprengelForm(instance=sprengel)

    context = {
        'form': form,
        'sprengel': sprengel,
        'title': 'Sprengel bearbeiten',
    }

    return render(request, 'sprengel/sprengel_form.html', context)


@login_required
def sprengel_loeschen_view(request, bezeichnung):
    """Löscht einen Sprengel."""
    sprengel = get_object_or_404(Sprengel, bezeichnung=bezeichnung)

    # Prüfen, ob Sprengel Notarstellen hat
    if sprengel.notarstellen.exists():
        messages.error(
            request,
            f'Sprengel "{sprengel.name}" kann nicht gelöscht werden, da noch {sprengel.anzahl_notarstellen} Notarstelle(n) zugeordnet sind.'
        )
        return redirect('sprengel_detail', bezeichnung=sprengel.bezeichnung)

    if request.method == 'POST':
        name = sprengel.name
        sprengel.delete()
        messages.success(request, f'Sprengel "{name}" wurde erfolgreich gelöscht.')
        return redirect('sprengel_liste')

    context = {
        'sprengel': sprengel,
    }

    return render(request, 'sprengel/sprengel_loeschen.html', context)
