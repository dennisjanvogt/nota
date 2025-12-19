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

    # Schritt-Aktionen
    path('schritte/<int:schritt_id>/abschliessen/', views.schritt_abschliessen_view, name='schritt_abschliessen'),

    # Workflow-Aktionen
    path('workflows/<int:workflow_id>/starten/', views.workflow_starten_view, name='workflow_starten'),

    # Template-Verwaltung
    path('templates/', views.workflow_template_liste_view, name='workflow_template_liste'),
    path('templates/neu/', views.workflow_template_erstellen_view, name='workflow_template_erstellen'),
    path('templates/<int:template_id>/', views.workflow_template_detail_view, name='workflow_template_detail'),
    path('templates/<int:template_id>/bearbeiten/', views.workflow_template_bearbeiten_view, name='workflow_template_bearbeiten'),
    path('templates/<int:template_id>/loeschen/', views.workflow_template_loeschen_view, name='workflow_template_loeschen'),
]
