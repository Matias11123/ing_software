import re
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .models import UsuarioApp

def validar_contrasena_segura(password):
    """Verifica: mín 8 caracteres, mayúscula, minúscula, número y símbolo."""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe incluir al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe incluir al menos una letra minúscula."
    if not re.search(r"[0-9]", password):
        return False, "La contraseña debe incluir al menos un número."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=/\\[\];']", password):
        return False, "La contraseña debe incluir al menos un símbolo especial (ej: @, #, $, !)."
    return True, ""

def vista_registro(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            error = "Todos los campos son obligatorios."
        elif password != confirm_password:
            error = "Las contraseñas no coinciden."
        elif UsuarioApp.objects.filter(username=username).exists():
            error = "El nombre de usuario ya está registrado."
        elif UsuarioApp.objects.filter(email=email).exists():
            error = "El correo electrónico ya está registrado."
        else:
            es_valida, mensaje_error = validar_contrasena_segura(password)
            if not es_valida:
                error = mensaje_error
            else:
                # Guardamos en nuestra tabla propia con contraseña encriptada
                nuevo_usuario = UsuarioApp.objects.create(
                    username=username,
                    email=email,
                    password_hash=make_password(password)
                )
                request.session["usuario_id"] = nuevo_usuario.id
                request.session["usuario_nombre"] = nuevo_usuario.username
                return redirect("dashboard")

    return render(request, "core_achs/registro.html", {"error": error})

def vista_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        try:
            usuario = UsuarioApp.objects.get(username=username)

            # 1. Verificar si la cuenta ya está bloqueada
            if usuario.bloqueado:
                error = "CUENTA BLOQUEADA: Superaste los 3 intentos fallidos. Contacta al administrador."
            else:
                # 2. Verificar contraseña manualmente
                if check_password(password, usuario.password_hash):
                    # Éxito: reiniciamos contador y creamos sesión propia
                    usuario.intentos_fallidos = 0
                    usuario.save()
                    request.session["usuario_id"] = usuario.id
                    request.session["usuario_nombre"] = usuario.username
                    return redirect("dashboard")
                else:
                    # Fallo: sumamos intento y bloqueamos si llega a 3
                    usuario.intentos_fallidos += 1
                    if usuario.intentos_fallidos >= 3:
                        usuario.bloqueado = True
                        usuario.save()
                        error = "Contraseña incorrecta. Has alcanzado 3 intentos fallidos: tu cuenta ha sido BLOQUEADA."
                    else:
                        usuario.save()
                        restantes = 3 - usuario.intentos_fallidos
                        error = f"Contraseña incorrecta. Te quedan {restantes} intento(s) antes del bloqueo."

        except UsuarioApp.DoesNotExist:
            error = "El usuario ingresado no existe en la base de datos."

    return render(request, "core_achs/login.html", {"error": error})

def vista_dashboard(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return redirect("login")

    usuario = UsuarioApp.objects.get(id=usuario_id)
    return render(request, "core_achs/dashboard.html", {"usuario": usuario})

def vista_logout(request):
    request.session.flush()
    return redirect("login")