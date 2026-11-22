/** Estado de red del panel: consulta y reporta conectividad al backend. */

const API_BASE =
  window.location.protocol === "file:"
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const $ = (id) => document.getElementById(id);

function pintarEstado(estado, detalle) {
  const estados = {
    ONLINE: ["bg-success", "En línea"],
    DEGRADADO: ["bg-warning text-dark", "Inestable / Contingencia"],
    OFFLINE: ["bg-danger", "Sin conexión"],
  };
  const [clase, texto] = estados[estado] || ["bg-secondary", "Desconocido"];

  const insignia = $("estadoRed");
  if (insignia) {
    insignia.className = `badge ${clase}`;
    insignia.textContent = texto;
  }

  const motor = $("estadoMotor");
  if (motor) {
    motor.className = "badge bg-success";
    motor.textContent = "Activo (Guardado Offline)";
  }

  const detalleElemento = $("detalleRed");
  if (detalleElemento) detalleElemento.textContent = detalle || "";
}

async function actualizarRed() {
  if (!navigator.onLine) {
    pintarEstado(
      "OFFLINE",
      "El navegador está sin conexión; las denuncias se guardan en el dispositivo."
    );
    return;
  }

  try {
    await fetch(`${API_BASE}/api/monitor-red/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        estado: "ONLINE",
        detalle: "Reporte automático del navegador.",
      }),
    });
  } catch {
    // El reporte es informativo; no bloquea la consulta posterior.
  }

  try {
    const respuesta = await fetch(`${API_BASE}/api/monitor-red/`);
    const datos = await respuesta.json();
    pintarEstado(datos.estado, datos.detalle);
  } catch {
    pintarEstado("OFFLINE", "No se pudo consultar el monitor de red.");
  }
}

window.addEventListener("online", actualizarRed);
window.addEventListener("offline", () =>
  pintarEstado("OFFLINE", "El navegador perdió conexión; se activó el modo contingente.")
);

actualizarRed();
