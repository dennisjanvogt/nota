"""
URL-Konfiguration für Berichte und Exports.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Berichte-Übersicht
    path('', views.berichte_uebersicht_view, name='berichte_uebersicht'),

    # Filter-Seiten
    path('filter/notare/', views.notare_filter_view, name='filter_notare'),
    path('filter/anwaerter/', views.anwaerter_filter_view, name='filter_anwaerter'),
    path('filter/notarstellen/', views.notarstellen_filter_view, name='filter_notarstellen'),
    path('filter/workflows/', views.workflows_filter_view, name='filter_workflows'),

    # Exports
    path('export/notare/', views.export_notare_view, name='export_notare'),
    path('export/anwaerter/', views.export_anwaerter_view, name='export_anwaerter'),
    path('export/notarstellen/', views.export_notarstellen_view, name='export_notarstellen'),
    path('export/workflows/', views.export_workflows_view, name='export_workflows'),
]
