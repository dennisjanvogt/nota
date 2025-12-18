"""
URL-Konfiguration für Notarstellen-Verwaltung.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.notarstellen_liste_view, name='notarstellen_liste'),
    path('neu/', views.notarstelle_erstellen_view, name='notarstelle_erstellen'),
    path('<int:notarstelle_id>/', views.notarstelle_detail_view, name='notarstelle_detail'),
    path('<int:notarstelle_id>/bearbeiten/', views.notarstelle_bearbeiten_view, name='notarstelle_bearbeiten'),
    path('<int:notarstelle_id>/loeschen/', views.notarstelle_loeschen_view, name='notarstelle_loeschen'),
]
