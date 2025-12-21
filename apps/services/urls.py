"""
URL-Konfiguration für das Service-System.
"""
from django.urls import path
from apps.services import views

urlpatterns = [
    # Service-Katalog
    path('', views.service_katalog_view, name='service_katalog'),

    # Service-Historie
    path('historie/', views.service_historie_view, name='service_historie'),

    # Service ausführen
    path('<str:service_id>/ausfuehren/', views.service_ausfuehren_view, name='service_ausfuehren'),

    # Service-Ausführung Details
    path('ausfuehrung/<int:ausfuehrung_id>/', views.service_ausfuehrung_detail_view, name='service_ausfuehrung_detail'),
]
