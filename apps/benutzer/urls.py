"""
URL-Konfiguration für Benutzer-App.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('profil/', views.profil_bearbeiten_view, name='profil_bearbeiten'),
]
