"""
Views für E-Mail-Verwaltung.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from .models import EmailVorlage, GesendeteEmail
from .forms import EmailVorlageForm, EmailSendenForm
from apps.personen.models import Notar, NotarAnwaerter


@login_required
def vorlagen_liste_view(request):
    """Liste aller E-Mail-Vorlagen."""
    vorlagen = EmailVorlage.objects.select_related('workflow_typ').order_by('kategorie', 'name')

    context = {
        'vorlagen': vorlagen,
    }
    return render(request, 'emails/vorlagen_liste.html', context)


@login_required
def vorlage_detail_view(request, vorlage_id):
    """Detail einer E-Mail-Vorlage."""
    vorlage = get_object_or_404(EmailVorlage, id=vorlage_id)

    # Letzte gesendete E-Mails mit dieser Vorlage
    gesendete_emails = GesendeteEmail.objects.filter(vorlage=vorlage).order_by('-gesendet_am')[:10]

    context = {
        'vorlage': vorlage,
        'gesendete_emails': gesendete_emails,
    }
    return render(request, 'emails/vorlage_detail.html', context)


@login_required
def vorlage_erstellen_view(request):
    """Neue E-Mail-Vorlage erstellen."""
    if request.method == 'POST':
        form = EmailVorlageForm(request.POST)
        if form.is_valid():
            vorlage = form.save()
            messages.success(request, f'E-Mail-Vorlage "{vorlage.name}" wurde erstellt.')
            return redirect('vorlage_detail', vorlage_id=vorlage.id)
    else:
        form = EmailVorlageForm()

    context = {
        'form': form,
        'title': 'Neue E-Mail-Vorlage',
    }
    return render(request, 'emails/vorlage_form.html', context)


@login_required
def vorlage_bearbeiten_view(request, vorlage_id):
    """E-Mail-Vorlage bearbeiten."""
    vorlage = get_object_or_404(EmailVorlage, id=vorlage_id)

    if request.method == 'POST':
        form = EmailVorlageForm(request.POST, instance=vorlage)
        if form.is_valid():
            vorlage = form.save()
            messages.success(request, f'E-Mail-Vorlage "{vorlage.name}" wurde aktualisiert.')
            return redirect('vorlage_detail', vorlage_id=vorlage.id)
    else:
        form = EmailVorlageForm(instance=vorlage)

    context = {
        'form': form,
        'vorlage': vorlage,
        'title': f'Vorlage bearbeiten: {vorlage.name}',
    }
    return render(request, 'emails/vorlage_form.html', context)


@login_required
def vorlage_loeschen_view(request, vorlage_id):
    """E-Mail-Vorlage löschen."""
    vorlage = get_object_or_404(EmailVorlage, id=vorlage_id)

    if request.method == 'POST':
        name = vorlage.name
        vorlage.delete()
        messages.success(request, f'E-Mail-Vorlage "{name}" wurde gelöscht.')
        return redirect('vorlagen_liste')

    context = {
        'vorlage': vorlage,
    }
    return render(request, 'emails/vorlage_loeschen.html', context)


@login_required
def email_vorbereiten_view(request, vorlage_id):
    """E-Mail basierend auf Vorlage vorbereiten."""
    vorlage = get_object_or_404(EmailVorlage, id=vorlage_id)

    # Alle Notare und Kandidat für Auswahl
    notare = Notar.objects.select_related('notarstelle').filter(ist_aktiv=True).order_by('nachname', 'vorname')
    anwaerter = NotarAnwaerter.objects.select_related('notarstelle').filter(ist_aktiv=True).order_by('nachname', 'vorname')

    if request.method == 'POST':
        form = EmailSendenForm(request.POST)

        # Person aus POST-Daten holen
        notar_id = request.POST.get('notar_id')
        anwaerter_id = request.POST.get('anwaerter_id')

        notar = None
        anwaerter_obj = None

        if notar_id:
            try:
                notar = Notar.objects.get(id=notar_id)
            except Notar.DoesNotExist:
                pass

        if anwaerter_id:
            try:
                anwaerter_obj = NotarAnwaerter.objects.get(id=anwaerter_id)
            except NotarAnwaerter.DoesNotExist:
                pass

        if form.is_valid():
            return email_senden(
                request,
                vorlage,
                form.cleaned_data,
                notar=notar,
                anwaerter=anwaerter_obj
            )
    else:
        form = EmailSendenForm(initial={
            'empfaenger': vorlage.standard_empfaenger,
            'cc': vorlage.cc_empfaenger,
            'betreff': vorlage.betreff,
            'nachricht': vorlage.nachricht,
        })

    context = {
        'form': form,
        'vorlage': vorlage,
        'notare': notare,
        'anwaerter': anwaerter,
    }
    return render(request, 'emails/email_senden.html', context)


def email_senden(request, vorlage, data, notar=None, anwaerter=None):
    """E-Mail tatsächlich versenden."""
    try:
        # E-Mail versenden
        send_mail(
            subject=data['betreff'],
            message=data['nachricht'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[data['empfaenger']],
            fail_silently=False,
        )

        # Protokollieren
        GesendeteEmail.objects.create(
            vorlage=vorlage,
            gesendet_von=request.user,
            empfaenger=data['empfaenger'],
            cc_empfaenger=data['cc_empfaenger'],
            betreff=data['betreff'],
            nachricht=data['nachricht'],
            notar=notar,
            anwaerter=anwaerter,
            erfolgreich=True
        )

        messages.success(
            request,
            f'E-Mail wurde erfolgreich an {data["empfaenger"]} gesendet.'
        )

        # Zurück zur Person-Detailseite
        if notar:
            return redirect('notar_detail', notar_id=notar.notar_id)
        elif anwaerter:
            return redirect('anwaerter_detail', anwaerter_id=anwaerter.anwaerter_id)
        else:
            return redirect('vorlagen_liste')

    except BadHeaderError:
        messages.error(request, 'Ungültige Header-Daten in der E-Mail.')
    except Exception as e:
        # Fehler protokollieren
        GesendeteEmail.objects.create(
            vorlage=vorlage,
            gesendet_von=request.user,
            empfaenger=data['empfaenger'],
            cc_empfaenger=data['cc_empfaenger'],
            betreff=data['betreff'],
            nachricht=data['nachricht'],
            notar=notar,
            anwaerter=anwaerter,
            erfolgreich=False,
            fehler=str(e)
        )
        messages.error(request, f'Fehler beim Versenden der E-Mail: {str(e)}')

    return redirect('email_vorbereiten', vorlage_id=vorlage.id)


@login_required
def gesendete_emails_view(request):
    """Liste aller gesendeten E-Mails."""
    emails = GesendeteEmail.objects.select_related(
        'vorlage', 'gesendet_von', 'notar', 'anwaerter'
    ).order_by('-gesendet_am')

    # Statistiken
    stats = {
        'total': emails.count(),
        'erfolgreich': emails.filter(erfolgreich=True).count(),
        'fehlgeschlagen': emails.filter(erfolgreich=False).count(),
    }

    context = {
        'emails': emails,
        'stats': stats,
    }
    return render(request, 'emails/gesendete_emails.html', context)


@login_required
def gesendete_email_detail_view(request, email_id):
    """Detail-Ansicht einer gesendeten E-Mail."""
    email = get_object_or_404(
        GesendeteEmail.objects.select_related(
            'vorlage', 'gesendet_von', 'notar', 'anwaerter'
        ).prefetch_related('anhaenge'),
        id=email_id
    )

    context = {
        'email': email,
    }
    return render(request, 'emails/gesendete_email_detail.html', context)
