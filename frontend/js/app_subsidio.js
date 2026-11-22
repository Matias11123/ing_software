/** Consulta de subsidios por RUT contra la API Django. */

const API_BASE =
  window.location.protocol === "file:"
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const formulario = document.getElementById("formSubsidio");
const $ = (id) => document.getElementById(id);

function mostrarMensaje(texto, clase) {
  const contenedor = $("mensajeSubsidio");
  if (!contenedor) return;
  contenedor.className = `alert alert-${clase}`;
  contenedor.textContent = texto;
  contenedor.classList.remove("d-none");
}

function agregarFila(cuerpo, subsidio) {
  const fila = document.createElement("tr");
  [subsidio.id_tramite, subsidio.estado, `$${subsidio.monto}`].forEach((texto) => {
    const celda = document.createElement("td");
    celda.textContent = texto;
    fila.appendChild(celda);
  });
  cuerpo.appendChild(fila);
}

if (formulario) {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const rut = ($("rutSubsidio")?.value || "").trim();
    const cuerpo = $("cuerpoSubsidios");
    if (cuerpo) cuerpo.innerHTML = "";
    if (!rut) {
      mostrarMensaje("Ingrese el RUT del trabajador.", "warning");
      return;
    }

    const boton = $("btnConsultar");
    if (boton) boton.disabled = true;

    try {
      const respuesta = await fetch(
        `${API_BASE}/api/subsidios/?rut=${encodeURIComponent(rut)}`
      );
      const datos = await respuesta.json();
      if (!respuesta.ok) throw new Error(datos.error || "No se pudo consultar.");

      datos.subsidios.forEach((subsidio) => agregarFila(cuerpo, subsidio));
      mostrarMensaje(
        `Se encontraron ${datos.subsidios.length} trámite(s) para ${datos.rut}.`,
        "success"
      );
    } catch (error) {
      mostrarMensaje(error.message || "No se pudo consultar el subsidio.", "danger");
    } finally {
      if (boton) boton.disabled = false;
    }
  });
}
