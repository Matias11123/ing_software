"""Servidor ASGI para despliegue local o de producción."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "achs_contingencia.settings")

application = get_asgi_application()
