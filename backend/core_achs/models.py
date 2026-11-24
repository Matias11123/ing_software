# models.py - Módulo ACHS Contingencia (Actualizado con Clases de Usuarios)


from django.db import models

class UsuarioApp(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({'Bloqueado' if self.bloqueado else 'Activo'})"
class Usuario(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=100)

    class Meta:
        abstract = True # Clase abstracta base del diagrama

    def iniciar_sesion(self):
        return f"Usuario {self.correo} ha iniciado sesión."

    def cerrar_sesion(self):
        return "Sesión cerrada."

class Trabajador(Usuario):
    cargo = models.CharField(max_length=100)

    def consultar_subsidio(self):
        return "Consultando estado de subsidio..."

class Empresa(models.Model):
    rut_empresa = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=150)
    mutual_adherida = models.CharField(max_length=100, default="ACHS")

class Prevencionista(Usuario):
    area = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='prevencionistas')

    def declarar_denuncia(self):
        return "Iniciando formulario DIAT/DIEP en modo contingente..."

class MonitorRed(models.Model):
    conectado = models.BooleanField(default=True)
    ultima_verificacion = models.DateTimeField(auto_now=True)

    def verificar_conexion(self):
        return self.conectado

class Denuncia(models.Model):
    TIPO_CHOICES = [
        ('DIAT', 'Accidente del Trabajo'),
        ('DIEP', 'Enfermedad Profesional'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Guardado Localmente (Offline)'),
        ('SINCRONIZADO', 'Enviado a API ACHS'),
    ]

    prevencionista = models.ForeignKey(Prevencionista, on_delete=models.SET_NULL, null=True, blank=True)
    rut_trabajador = models.CharField(max_length=12)
    rut_empresa = models.CharField(max_length=12)
    tipo_denuncia = models.CharField(max_length=4, choices=TIPO_CHOICES, default='DIAT')
    fecha_suceso = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    lugar_accidente = models.CharField(max_length=255, blank=True, null=True)
    estado_envio = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')

    def marcar_sincronizada(self):
        self.estado_envio = 'SINCRONIZADO'
        self.save()

class Subsidio(models.Model):
    denuncia = models.OneToOneField(Denuncia, on_delete=models.CASCADE, related_name='subsidio')
    id_tramite = models.CharField(max_length=20, unique=True)
    estado_tramite = models.CharField(max_length=50, default='En Evaluación')
    fecha_pago_estimada = models.DateField(null=True, blank=True)
    monto_calculado = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def consultar_estado(self):
        return f"Trámite {self.id_tramite}: {self.estado_tramite}"