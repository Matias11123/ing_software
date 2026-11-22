"""Configuración de la aplicación de contingencia."""

from django.apps import AppConfig


class ContingenciaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "contingencia"
    verbose_name = "Módulo de Contingencia ACHS"
