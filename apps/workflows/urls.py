"""
URL-Konfiguration für Workflow-System.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Workflow-Listen & CRUD
    path('workflows/', views.workflow_liste_view, name='workflow_liste'),
    path('workflows/neu/', views.workflow_erstellen_view, name='workflow_erstellen'),
    path('workflows/<int:workflow_id>/', views.workflow_detail_view, name='workflow_detail'),
    path('workflows/<int:workflow_id>/bearbeiten/', views.workflow_bearbeiten_view, name='workflow_bearbeiten'),
    path('workflows/<int:workflow_id>/loeschen/', views.workflow_loeschen_view, name='workflow_loeschen'),

    # Meine Aufgaben
    path('aufgaben/', views.meine_aufgaben_view, name='meine_aufgaben'),

    # Schritt-Aktionen
    path('schritte/<int:schritt_id>/abschliessen/', views.schritt_abschliessen_view, name='schritt_abschliessen'),
    path('schritte/<int:schritt_id>/zuweisen/', views.schritt_zuweisen_view, name='schritt_zuweisen'),

    # Workflow-Aktionen
    path('workflows/<int:workflow_id>/starten/', views.workflow_starten_view, name='workflow_starten'),
    path('workflows/<int:workflow_id>/kommentar/', views.kommentar_hinzufuegen_view, name='kommentar_hinzufuegen'),
    path('workflows/<int:workflow_id>/abbrechen/', views.workflow_abbrechen_view, name='workflow_abbrechen'),

    # Besetzungsverfahren-spezifische Aktionen
    path('workflows/<int:workflow_id>/bewerber-auswaehlen/', views.bewerber_auswaehlen_view, name='bewerber_auswaehlen'),
    path('workflows/<int:workflow_id>/ranking-festlegen/', views.ranking_festlegen_view, name='ranking_festlegen'),
    path('workflows/<int:workflow_id>/bestellung-durchfuehren/', views.bestellung_durchfuehren_view, name='bestellung_durchfuehren'),
]
