"""Cabeceras CORS para permitir consumir la API desde file:// u otro puerto.

En producción se recomienda reemplazar '*' por el dominio autorizado.
"""

from django.http import HttpResponse


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Las peticiones OPTIONS son la preverificación de los navegadores.
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
