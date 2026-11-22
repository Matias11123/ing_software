"""Endpoints HTTP para denuncias contingentes, subsidios y monitor de red."""

import json
import re

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Denuncia, MonitorRed, Subsidio
from .utils import normalizar_rut, parsear_fecha


def _cuerpo_json(request):
    try:
        return json.loads(request.body.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "El cuerpo de la petición debe ser JSON válido."


@csrf_exempt
@require_http_methods(["POST"])
def registrar_denuncia(request):
    """Registra una denuncia recibida mientras la red central está caída."""
    data, error = _cuerpo_json(request)
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)

    obligatorios = [
        "rut_trabajador",
        "nombre_trabajador",
        "empresa",
        "tipo",
        "fecha_suceso",
        "descripcion",
    ]
    faltantes = [campo for campo in obligatorios if not str(data.get(campo, "")).strip()]
    if faltantes:
        return JsonResponse(
            {"ok": False, "error": "Faltan campos obligatorios.", "faltantes": faltantes},
            status=400,
        )

    tipo = str(data["tipo"]).upper()
    if tipo not in (Denuncia.TIPO_DIAT, Denuncia.TIPO_DIEP):
        return JsonResponse(
            {"ok": False, "error": "El tipo debe ser DIAT o DIEP."}, status=400
        )

    try:
        fecha_suceso = parsear_fecha(data["fecha_suceso"])
    except (ValueError, TypeError):
        return JsonResponse(
            {"ok": False, "error": "fecha_suceso debe estar en formato ISO-8601."},
            status=400,
        )

    estado = str(data.get("estado", Denuncia.ESTADO_PENDIENTE)).upper()
    if estado not in (Denuncia.ESTADO_PENDIENTE, Denuncia.ESTADO_SINCRONIZADO):
        estado = Denuncia.ESTADO_PENDIENTE

    id_local = str(data.get("id_local", "")).strip() or None
    if id_local:
        existente = Denuncia.objects.filter(id_local=id_local).first()
        if existente:
            return JsonResponse(
                {
                    "ok": True,
                    "ya_existia": True,
                    "id": existente.id,
                    "estado": existente.estado,
                },
                status=200,
            )

    denuncia = Denuncia.objects.create(
        id_local=id_local,
        firebase_id=str(data.get("firebase_id", "")).strip(),
        rut_empresa=normalizar_rut(data.get("rut_empresa", "")),
        empresa=str(data["empresa"]).strip(),
        rut_trabajador=normalizar_rut(data["rut_trabajador"]),
        nombre_trabajador=str(data["nombre_trabajador"]).strip(),
        cargo=str(data.get("cargo", "")).strip(),
        tipo=tipo,
        fecha_suceso=fecha_suceso,
        lugar=str(data.get("lugar", "")).strip(),
        descripcion=str(data["descripcion"]).strip(),
        estado=estado,
    )

    MonitorRed.objects.create(
        estado=MonitorRed.ESTADO_DEGRADADO,
        detalle=f"Denuncia local #{denuncia.id} recibida por el modo contingente.",
    )

    return JsonResponse(
        {
            "ok": True,
            "ya_existia": False,
            "id": denuncia.id,
            "id_local": denuncia.id_local,
            "rut_trabajador": denuncia.rut_trabajador,
            "estado": denuncia.estado,
            "creado_en": denuncia.creado_en.isoformat(),
        },
        status=201,
    )


@require_http_methods(["GET"])
def consultar_subsidio(request):
    """Consulta el estado de los subsidios asociados al RUT del trabajador."""
    rut = request.GET.get("rut") or request.GET.get("rut_trabajador") or ""
    normalizado = normalizar_rut(rut)
    if not re.fullmatch(r"\d{7,8}-[0-9K]", normalizado):
        return JsonResponse(
            {"ok": False, "error": "Debe indicar un RUT válido (Ej.: 19876543-2)."},
            status=400,
        )

    subsidios = Subsidio.objects.filter(rut_trabajador=normalizado).order_by("id_tramite")
    resultados = [
        {
            "id_tramite": subsidio.id_tramite,
            "estado": subsidio.estado,
            "monto": str(subsidio.monto),
            "fecha_actualizacion": subsidio.fecha_actualizacion.isoformat(),
        }
        for subsidio in subsidios
    ]

    if not resultados:
        return JsonResponse(
            {
                "ok": False,
                "error": "No existen subsidios registrados para ese RUT.",
                "rut": normalizado,
                "subsidios": [],
            },
            status=404,
        )

    return JsonResponse(
        {"ok": True, "rut": normalizado, "subsidios": resultados}, status=200
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def estado_red(request):
    """Devuelve el último estado de red y permite al navegador reportar el suyo."""
    if request.method == "POST":
        data, error = _cuerpo_json(request)
        if error:
            return JsonResponse({"ok": False, "error": error}, status=400)

        estado = str(data.get("estado", MonitorRed.ESTADO_ONLINE)).upper()
        if estado not in dict(MonitorRed.ESTADO_CHOICES):
            estado = MonitorRed.ESTADO_DEGRADADO

        registro = MonitorRed.objects.create(
            estado=estado, detalle=str(data.get("detalle", "Reporte del navegador."))
        )
        return JsonResponse(
            {
                "ok": True,
                "estado": registro.estado,
                "verificada_en": registro.verificada_en.isoformat(),
            },
            status=201,
        )

    ultimo = MonitorRed.objects.order_by("-verificada_en").first()
    return JsonResponse(
        {
            "ok": True,
            "estado": ultimo.estado if ultimo else MonitorRed.ESTADO_DEGRADADO,
            "detalle": ultimo.detalle if ultimo else "Sin reportes de red todavía.",
            "verificada_en": (
                ultimo.verificada_en.isoformat()
                if ultimo
                else timezone.now().isoformat()
            ),
        },
        status=200,
    )
