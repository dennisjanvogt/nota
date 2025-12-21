"""
URL-Konfiguration für Sprengel-Verwaltung.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('sprengel/', views.sprengel_liste_view, name='sprengel_liste'),
    path('sprengel/neu/', views.sprengel_erstellen_view, name='sprengel_erstellen'),
    path('sprengel/<str:bezeichnung>/', views.sprengel_detail_view, name='sprengel_detail'),
    path('sprengel/<str:bezeichnung>/bearbeiten/', views.sprengel_bearbeiten_view, name='sprengel_bearbeiten'),
    path('sprengel/<str:bezeichnung>/loeschen/', views.sprengel_loeschen_view, name='sprengel_loeschen'),
]
