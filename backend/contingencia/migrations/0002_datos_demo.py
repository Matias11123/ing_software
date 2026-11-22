"""Datos mínimos de demostración para probar la consulta de subsidios."""

from django.db import migrations


def cargar_datos(apps, schema_editor):
    Subsidio = apps.get_model("contingencia", "Subsidio")
    MonitorRed = apps.get_model("contingencia", "MonitorRed")

    Subsidio.objects.get_or_create(
        id_tramite="SUB-2026-0001",
        defaults={
            "rut_trabajador": "19876543-2",
            "estado": "En revisión médica",
            "monto": "185000.00",
        },
    )
    Subsidio.objects.get_or_create(
        id_tramite="SUB-2026-0002",
        defaults={
            "rut_trabajador": "11222333-4",
            "estado": "Aprobado - en pago",
            "monto": "240500.00",
        },
    )
    MonitorRed.objects.create(
        estado="DEGRADADO",
        detalle="Red central inestable: modo contingente activado.",
    )


def eliminar_datos(apps, schema_editor):
    Subsidio = apps.get_model("contingencia", "Subsidio")
    MonitorRed = apps.get_model("contingencia", "MonitorRed")
    Subsidio.objects.filter(
        id_tramite__in=["SUB-2026-0001", "SUB-2026-0002"]
    ).delete()
    MonitorRed.objects.filter(
        detalle="Red central inestable: modo contingente activado."
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("contingencia", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_datos, eliminar_datos),
    ]
