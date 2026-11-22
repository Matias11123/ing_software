"""Registro de los modelos en el sitio de administración de Django."""

from django.contrib import admin

from .models import Denuncia, MonitorRed, Subsidio

admin.site.register(Denuncia)
admin.site.register(Subsidio)
admin.site.register(MonitorRed)
