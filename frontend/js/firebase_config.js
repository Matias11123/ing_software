/**
 * Inicialización modular de Firebase Firestore.
 *
 * Para conectarlo a un proyecto real, reemplaza los valores "REEMPLAZAR_*"
 * o define window.FIREBASE_CONFIG antes de cargar este módulo. Si no hay
 * credenciales o no hay Internet, el módulo sigue cargando y el formulario
 * funciona con localStorage como mecanismo de contingencia.
 */

const VERSION_FIREBASE = "10.14.1";
const URL_APP = `https://www.gstatic.com/firebasejs/${VERSION_FIREBASE}/firebase-app.js`;
const URL_FIRESTORE = `https://www.gstatic.com/firebasejs/${VERSION_FIREBASE}/firebase-firestore.js`;

const firebaseConfig = {
  apiKey: window.FIREBASE_CONFIG?.apiKey || "REEMPLAZAR_API_KEY",
  authDomain: window.FIREBASE_CONFIG?.authDomain || "REEMPLAZAR_AUTH_DOMAIN",
  projectId: window.FIREBASE_CONFIG?.projectId || "REEMPLAZAR_PROJECT_ID",
  storageBucket: window.FIREBASE_CONFIG?.storageBucket || "REEMPLAZAR_STORAGE_BUCKET",
  messagingSenderId: window.FIREBASE_CONFIG?.messagingSenderId || "REEMPLAZAR_SENDER_ID",
  appId: window.FIREBASE_CONFIG?.appId || "REEMPLAZAR_APP_ID",
};

const isConfigured = !Object.values(firebaseConfig).some((valor) =>
  String(valor).startsWith("REEMPLAZAR")
);

let modoPersistencia = isConfigured ? "indexeddb" : "localstorage";

function getPersistenceMode() {
  return modoPersistencia;
}

// La importación es dinámica para que el formulario siga funcionando sin red.
const inicializarFirebase = (async () => {
  if (!isConfigured) {
    return { db: null, firestore: null, modo: modoPersistencia };
  }

  try {
    const [moduloApp, moduloFirestore] = await Promise.all([
      import(URL_APP),
      import(URL_FIRESTORE),
    ]);

    const app = moduloApp.initializeApp(firebaseConfig);
    const db = moduloFirestore.getFirestore(app);

    // enableIndexedDbPersistence debe ejecutarse antes de cualquier lectura
    // o escritura: así las escrituras quedan encoladas mientras no hay red.
    try {
      await moduloFirestore.enableIndexedDbPersistence(db);
      modoPersistencia = "indexeddb";
    } catch (error) {
      modoPersistencia =
        error?.code === "failed-precondition" ? "multitab" : "localstorage";
      console.warn("Persistencia IndexedDB no disponible:", error);
    }

    return { db, firestore: moduloFirestore, modo: modoPersistencia };
  } catch (error) {
    modoPersistencia = "localstorage";
    console.warn("Firebase no disponible; se usa almacenamiento local.", error);
    return { db: null, firestore: null, modo: modoPersistencia };
  }
})();

export { firebaseConfig, isConfigured, inicializarFirebase, getPersistenceMode };
