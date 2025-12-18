"""
URL-Konfiguration für Aktenzeichen-Verwaltung.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Aktenzeichen - Liste & Detail
    path('', views.aktenzeichen_liste_view, name='aktenzeichen_liste'),
    path('neu/', views.aktenzeichen_erstellen_view, name='aktenzeichen_erstellen'),
    path('<int:aktenzeichen_id>/', views.aktenzeichen_detail_view, name='aktenzeichen_detail'),
    path('<int:aktenzeichen_id>/bearbeiten/', views.aktenzeichen_bearbeiten_view, name='aktenzeichen_bearbeiten'),
    path('<int:aktenzeichen_id>/loeschen/', views.aktenzeichen_loeschen_view, name='aktenzeichen_loeschen'),
]
