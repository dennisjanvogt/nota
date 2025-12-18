"""
URL-Konfiguration für E-Mail-System.
"""
from django.urls import path
from . import views

urlpatterns = [
    # E-Mail-Vorlagen
    path('vorlagen/', views.vorlagen_liste_view, name='vorlagen_liste'),
    path('vorlagen/<int:vorlage_id>/', views.vorlage_detail_view, name='vorlage_detail'),
    path('vorlagen/neu/', views.vorlage_erstellen_view, name='vorlage_erstellen'),
    path('vorlagen/<int:vorlage_id>/bearbeiten/', views.vorlage_bearbeiten_view, name='vorlage_bearbeiten'),
    path('vorlagen/<int:vorlage_id>/loeschen/', views.vorlage_loeschen_view, name='vorlage_loeschen'),

    # E-Mail versenden
    path('vorlagen/<int:vorlage_id>/senden/', views.email_vorbereiten_view, name='email_vorbereiten'),

    # Gesendete E-Mails
    path('gesendet/', views.gesendete_emails_view, name='gesendete_emails'),
]
