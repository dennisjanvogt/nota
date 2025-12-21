"""
URL-Konfiguration für Personen-Verwaltung.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Notare - Liste & Detail
    path('notare/', views.notare_liste_view, name='notare_liste'),
    path('notare/neu/', views.notar_erstellen_view, name='notar_erstellen'),
    path('notare/vergleichen/', views.notare_vergleichen_view, name='notare_vergleichen'),
    path('notare/<str:notar_id>/', views.notar_detail_view, name='notar_detail'),
    path('notare/<str:notar_id>/bearbeiten/', views.notar_bearbeiten_view, name='notar_bearbeiten'),
    path('notare/<str:notar_id>/loeschen/', views.notar_loeschen_view, name='notar_loeschen'),

    # Notariatskandidat - Liste & Detail
    path('anwaerter/', views.anwaerter_liste_view, name='anwaerter_liste'),
    path('anwaerter/neu/', views.anwaerter_erstellen_view, name='anwaerter_erstellen'),
    path('anwaerter/vergleichen/', views.anwaerter_vergleichen_view, name='anwaerter_vergleichen'),
    path('anwaerter/<str:anwaerter_id>/', views.anwaerter_detail_view, name='anwaerter_detail'),
    path('anwaerter/<str:anwaerter_id>/bearbeiten/', views.anwaerter_bearbeiten_view, name='anwaerter_bearbeiten'),
    path('anwaerter/<str:anwaerter_id>/loeschen/', views.anwaerter_loeschen_view, name='anwaerter_loeschen'),
    path('anwaerter/<str:anwaerter_id>/zu-notar/', views.anwaerter_zu_notar_view, name='anwaerter_zu_notar'),
]
