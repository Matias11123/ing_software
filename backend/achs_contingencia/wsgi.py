"""Servidor WSGI para despliegue local o de producción."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "achs_contingencia.settings")

application = get_wsgi_application()
