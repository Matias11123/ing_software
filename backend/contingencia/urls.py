"""Rutas de la API REST del módulo de contingencia."""

from django.urls import path

from . import views

urlpatterns = [
    path("denuncias/", views.registrar_denuncia, name="registrar-denuncia"),
    path("subsidios/", views.consultar_subsidio, name="consultar-subsidio"),
    path("monitor-red/", views.estado_red, name="estado-red"),
]
