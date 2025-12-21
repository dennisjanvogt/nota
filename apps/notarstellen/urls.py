"""
URL-Konfiguration für Notarstellen-Verwaltung.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('notarstellen/', views.notarstellen_liste_view, name='notarstellen_liste'),
    path('notarstellen/neu/', views.notarstelle_erstellen_view, name='notarstelle_erstellen'),
    path('notarstellen/<str:bezeichnung>/', views.notarstelle_detail_view, name='notarstelle_detail'),
    path('notarstellen/<str:bezeichnung>/bearbeiten/', views.notarstelle_bearbeiten_view, name='notarstelle_bearbeiten'),
    path('notarstellen/<str:bezeichnung>/loeschen/', views.notarstelle_loeschen_view, name='notarstelle_loeschen'),
]
