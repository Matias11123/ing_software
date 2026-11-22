"""Modelos del módulo de contingencia (Ley N° 16.744)."""

from django.db import models

from .utils import normalizar_rut


class Denuncia(models.Model):
    """Denuncia DIAT/DIEP registrada en modo contingente."""

    TIPO_DIAT = "DIAT"
    TIPO_DIEP = "DIEP"
    TIPO_CHOICES = [
        (TIPO_DIAT, "Accidente del trabajo (DIAT)"),
        (TIPO_DIEP, "Enfermedad profesional (DIEP)"),
    ]

    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_SINCRONIZADO = "SINCRONIZADO"
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, "Pendiente de sincronización"),
        (ESTADO_SINCRONIZADO, "Sincronizado"),
    ]

    id_local = models.CharField(max_length=64, unique=True, null=True, blank=True)
    firebase_id = models.CharField(max_length=128, blank=True)
    rut_empresa = models.CharField(max_length=12, blank=True)
    empresa = models.CharField(max_length=150)
    rut_trabajador = models.CharField(max_length=12, db_index=True)
    nombre_trabajador = models.CharField(max_length=150)
    cargo = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=4, choices=TIPO_CHOICES, default=TIPO_DIAT)
    fecha_suceso = models.DateTimeField()
    lugar = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=14, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.tipo} | {self.rut_trabajador} | {self.estado}"

    def save(self, *args, **kwargs):
        self.rut_trabajador = normalizar_rut(self.rut_trabajador)
        self.rut_empresa = normalizar_rut(self.rut_empresa)
        return super().save(*args, **kwargs)


class Subsidio(models.Model):
    """Estado de un trámite de subsidio por incapacidad laboral."""

    id_tramite = models.CharField(max_length=64, unique=True)
    rut_trabajador = models.CharField(max_length=12, db_index=True)
    estado = models.CharField(max_length=60)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id_tramite"]

    def __str__(self):
        return f"{self.id_tramite} | {self.rut_trabajador} | {self.estado}"

    def save(self, *args, **kwargs):
        self.rut_trabajador = normalizar_rut(self.rut_trabajador)
        return super().save(*args, **kwargs)


class MonitorRed(models.Model):
    """Historial de conectividad reportado por el navegador y por el servidor."""

    ESTADO_ONLINE = "ONLINE"
    ESTADO_DEGRADADO = "DEGRADADO"
    ESTADO_OFFLINE = "OFFLINE"
    ESTADO_CHOICES = [
        (ESTADO_ONLINE, "Conectado"),
        (ESTADO_DEGRADADO, "Red central inestable"),
        (ESTADO_OFFLINE, "Sin conexión"),
    ]

    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    detalle = models.TextField(blank=True)
    verificada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-verificada_en"]

    def __str__(self):
        return f"{self.estado} | {self.verificada_en:%d-%m-%Y %H:%M}"
