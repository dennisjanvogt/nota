from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfilBearbeitenForm


@login_required
def profil_bearbeiten_view(request):
    """
    View zur Bearbeitung des eigenen Benutzerprofils.
    """
    if request.method == 'POST':
        form = ProfilBearbeitenForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil wurde erfolgreich aktualisiert.')
            return redirect('profil_bearbeiten')
    else:
        form = ProfilBearbeitenForm(instance=request.user)

    context = {
        'form': form,
        'title': 'Profil bearbeiten',
    }
    return render(request, 'benutzer/profil_bearbeiten.html', context)
