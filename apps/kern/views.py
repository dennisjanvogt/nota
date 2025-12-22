from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


@login_required
def dms_platzhalter_view(request):
    """
    DMS - Dokumentenmanagementsystem.

    Zeigt alle durch Services und Berichte erstellten Dokumente.
    """
    from apps.services.models import Dokument

    # Alle Dokumente holen (aus Services und Berichten)
    dokumente = Dokument.objects.select_related(
        'generiert_von_service',
        'generiert_von_service__service',
        'generiert_von_service__ausgefuehrt_von'
    ).order_by('-erstellt_am')

    # Filter anwenden
    suche = request.GET.get('suche', '')
    typ_filter = request.GET.get('typ', '')

    if suche:
        dokumente = dokumente.filter(titel__icontains=suche)

    if typ_filter:
        dokumente = dokumente.filter(dokument_typ=typ_filter)

    # Paginierung
    paginator = Paginator(dokumente, 25)  # 25 pro Seite
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'suche': suche,
        'typ_filter': typ_filter,
    }

    return render(request, 'dms/platzhalter.html', context)
