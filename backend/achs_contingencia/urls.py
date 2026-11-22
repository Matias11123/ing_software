"""Rutas HTTP del proyecto: panel, formularios, API y archivos del frontend."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="inicio"),
    path("diat_form.html", TemplateView.as_view(template_name="diat_form.html"), name="diat"),
    path("subsidio.html", TemplateView.as_view(template_name="subsidio.html"), name="subsidio"),
    path("api/", include("contingencia.urls")),
    path("admin/", admin.site.urls),
    re_path(r"^(?P<path>(?:css|js)/.*)$", serve, {"document_root": settings.FRONTEND_DIR}),
    
    # Agregamos un prefijo "usuarios/" para que no choque con la raíz:
    path("usuarios/", include('core_achs.urls')),
]