/**
 * Lógica del formulario DIAT/DIEP en modo contingente.
 *
 * Flujo de guardado:
 * 1) La denuncia se escribe de inmediato en localStorage (copia de respaldo).
 * 2) Si Firebase está configurado, se envía a Firestore con persistencia
 *    IndexedDB: el SDK encola la escritura cuando no hay conexión.
 * 3) Cuando hay red, se replica en la API Django para consolidar el dato.
 */

import { inicializarFirebase, getPersistenceMode } from "./firebase_config.js";

const CLAVE_COLA = "achs_contingencia_denuncias_v1";
const API_BASE =
  window.location.protocol === "file:"
    ? "http://127.0.0.1:8000"
    : window.location.origin;
const promesaFirebase = inicializarFirebase();
const formulario = document.getElementById("diatForm");

let firebaseActivo = false;

const $ = (id) => document.getElementById(id);

function leerCola() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_COLA) || "[]");
  } catch {
    return [];
  }
}

function escribirCola(cola) {
  localStorage.setItem(CLAVE_COLA, JSON.stringify(cola));
}

function actualizarRegistro(idLocal, cambios) {
  const cola = leerCola().map((registro) =>
    registro.id_local === idLocal ? { ...registro, ...cambios } : registro
  );
  escribirCola(cola);
}

function normalizarRut(rut) {
  const limpio = String(rut || "").replace(/[^0-9kK]/g, "").toUpperCase();
  if (limpio.length < 2) return limpio;
  return `${parseInt(limpio.slice(0, -1), 10)}-${limpio.slice(-1)}`;
}

function generarIdLocal() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `diat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function valor(id) {
  return ($(id)?.value || "").trim();
}

function construirPayload() {
  const fechaLocal = valor("fechaSiniestro");
  let fechaIso = new Date().toISOString();
  if (fechaLocal) {
    const fecha = new Date(fechaLocal);
    if (!Number.isNaN(fecha.getTime())) fechaIso = fecha.toISOString();
  }

  return {
    id_local: generarIdLocal(),
    rut_empresa: normalizarRut(valor("rutEmpresa")),
    empresa: valor("nombreEmpresa"),
    rut_trabajador: normalizarRut(valor("rutTrabajador")),
    nombre_trabajador: valor("nombreTrabajador"),
    cargo: valor("cargoTrabajador"),
    tipo: valor("tipoDenuncia"),
    fecha_suceso: fechaIso,
    lugar: valor("lugarSiniestro"),
    descripcion: valor("descripcionSiniestro"),
    estado: "PENDIENTE",
    creado_local: new Date().toISOString(),
  };
}

function estaCompleto(registro) {
  const remotoConfirmado = firebaseActivo ? registro.firebase_confirmado : true;
  return Boolean(registro.django_id) && remotoConfirmado;
}

function mostrarMensaje(texto, clase = "info") {
  const contenedor = $("mensajeDiat");
  if (!contenedor) return;
  contenedor.className = `alert alert-${clase}`;
  contenedor.textContent = texto;
  contenedor.classList.remove("d-none");
}

function actualizarIndicadores() {
  const pendientes = leerCola().filter((registro) => !estaCompleto(registro)).length;
  const contador = $("contadorPendientes");
  if (contador) contador.textContent = String(pendientes);

  const detalle = $("detallePersistencia");
  if (detalle) {
    const etiquetas = {
      indexeddb: "Firestore + IndexedDB (offline)",
      multitab: "Firestore en memoria (varias pestañas)",
      localstorage: "LocalStorage (Firebase no configurado)",
    };
    const modo = getPersistenceMode();
    detalle.textContent = `${etiquetas[modo] || modo} · ${
      navigator.onLine ? "en línea" : "sin conexión"
    }`;
  }
}

async function guardarEnFirebase(payload, idLocal) {
  const { db, firestore } = await promesaFirebase;
  if (!db || !firestore) return null;

  const referencia = await firestore.addDoc(
    firestore.collection(db, "denuncias"),
    {
      ...payload,
      estado: "PENDIENTE",
      creado_en_firestore: firestore.serverTimestamp(),
    }
  );

  actualizarRegistro(idLocal, { firebase_id: referencia.id });

  // Con metadata.hasPendingWrites sabemos si el dato sigue en la cola local.
  firestore.onSnapshot(
    referencia,
    { includeMetadataChanges: true },
    (instantanea) => {
      if (instantanea.metadata.hasPendingWrites) return;
      const registro = leerCola().find((item) => item.id_local === idLocal);
      if (!registro || registro.firebase_confirmado) return;

      actualizarRegistro(idLocal, {
        firebase_confirmado: true,
        estado: "SINCRONIZADO",
        sincronizado_en: new Date().toISOString(),
      });
      firestore
        .updateDoc(referencia, { estado: "SINCRONIZADO" })
        .catch(() => {});
      actualizarIndicadores();
    },
    (error) => console.warn("No se pudo observar la escritura en Firestore.", error)
  );

  return referencia.id;
}

async function enviarADjango(registro) {
  if (!registro || !navigator.onLine) return false;

  try {
    const respuesta = await fetch(`${API_BASE}/api/denuncias/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...registro.payload,
        firebase_id: registro.firebase_id || "",
      }),
    });
    if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
    const datos = await respuesta.json();
    actualizarRegistro(registro.id_local, {
      django_id: datos.id,
      estado_servidor: datos.estado,
    });
    return true;
  } catch (error) {
    console.warn("Django no disponible; la denuncia permanece en la cola local.", error);
    return false;
  }
}

async function procesarCola() {
  if (!navigator.onLine) {
    actualizarIndicadores();
    return;
  }

  const pendientes = leerCola().filter((registro) => !estaCompleto(registro));
  for (const registro of pendientes) {
    await enviarADjango(registro);
  }
  actualizarIndicadores();
}

if (formulario) {
  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    if (!formulario.reportValidity()) return;

    const boton = $("btnGuardar");
    if (boton) {
      boton.disabled = true;
      boton.textContent = "Guardando...";
    }

    const payload = construirPayload();
    const registro = {
      id_local: payload.id_local,
      creado_local: payload.creado_local,
      payload,
      firebase_id: "",
      django_id: null,
      estado: "PENDIENTE",
      firebase_confirmado: false,
    };

    escribirCola([...leerCola(), registro]);
    actualizarIndicadores();
    mostrarMensaje(
      "Denuncia guardada en el dispositivo. Enviando a los servicios remotos...",
      "info"
    );

    try {
      await guardarEnFirebase(payload, registro.id_local);
    } catch (error) {
      console.warn("Firestore no disponible; se mantiene solo la copia local.", error);
    }

    const guardado = leerCola().find((item) => item.id_local === registro.id_local);
    await enviarADjango(guardado);

    formulario.reset();
    mostrarMensaje(
      "Denuncia registrada. Puedes revisar el estado de sincronización al final del formulario.",
      "success"
    );
    actualizarIndicadores();

    if (boton) {
      boton.disabled = false;
      boton.textContent = "Registrar Denuncia Contingente";
    }
  });
}

promesaFirebase.then(({ db }) => {
  firebaseActivo = Boolean(db);
  actualizarIndicadores();
});

window.addEventListener("online", procesarCola);
window.addEventListener("offline", actualizarIndicadores);

actualizarIndicadores();
procesarCola();
