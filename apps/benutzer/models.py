"""
Benutzer-Models für die Notariatskammer-Verwaltung.

Kammermitarbeiter sind Mitarbeiter der Notariatskammer, die die Software nutzen.
Sie VERWALTEN Notare und Notarstellen, sind aber NICHT selbst Notare.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class KammerBenutzer(AbstractUser):
    """
    Erweitertes Benutzer-Model für Kammermitarbeiter.

    Repräsentiert einen Mitarbeiter der Notariatskammer, der die Verwaltungssoftware nutzt.
    """

    ROLLEN = [
        ('admin', 'Administrator'),
        ('sachbearbeiter', 'Sachbearbeiter'),
        ('leitung', 'Leitung'),
    ]

    rolle = models.CharField(
        max_length=20,
        choices=ROLLEN,
        default='sachbearbeiter',
        verbose_name='Rolle'
    )

    abteilung = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Abteilung',
        help_text='z.B. "Zulassungen", "Aufsicht", "Allgemein"'
    )

    telefon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Telefon'
    )

    class Meta:
        verbose_name = 'Kammermitarbeiter'
        verbose_name_plural = 'Kammermitarbeiter'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rolle_display()})"

    def ist_admin(self):
        """Prüft ob Benutzer Admin ist."""
        return self.rolle == 'admin' or self.is_superuser

    def ist_leitung(self):
        """Prüft ob Benutzer zur Leitung gehört."""
        return self.rolle == 'leitung' or self.ist_admin()
