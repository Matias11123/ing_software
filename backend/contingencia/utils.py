"""Utilidades compartidas por los endpoints de la API."""

import re

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import datetime


def normalizar_rut(rut):
    """Deja un RUT en formato cuerpo-dígito verificador (Ej.: 19876543-2)."""
    if not rut:
        return ""
    limpio = re.sub(r"[^0-9kK]", "", str(rut)).upper()
    if len(limpio) < 2:
        return limpio
    return f"{int(limpio[:-1])}-{limpio[-1]}"


def parsear_fecha(valor):
    """Convierte un ISO-8601 del navegador en un datetime con zona horaria."""
    if not valor:
        raise ValueError("Fecha vacía")

    fecha = parse_datetime(str(valor))
    if fecha is None:
        fecha = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    if timezone.is_naive(fecha):
        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())
    return fecha
