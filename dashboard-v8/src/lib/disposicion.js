import { useEffect, useState } from "react";

/* MÓVIL O PC (29/09/2026)
 *
 * El dueño mira esto en el teléfono y en el ordenador. Por defecto
 * la pantalla elige sola según el ancho; con el selector de arriba
 * se puede forzar una de las dos, y se recuerda en este navegador.
 *
 * - "auto": móvil si la pantalla mide 760 px o menos.
 * - "movil": el diseño de teléfono, también en el ordenador (una
 *   columna centrada).
 * - "pc": el diseño de ordenador, también en el teléfono. Para que
 *   no haya scroll lateral, el teléfono dibuja la página a 1280 px
 *   de ancho y la encoge, igual que el «ver versión de ordenador»
 *   del navegador.
 *
 * El diseño efectivo se escribe en <html data-layout="...">, y la
 * hoja de estilos cuelga de ese atributo, no de una media query:
 * así el selector manda de verdad.
 *
 * localStorage puede no existir o lanzar (navegación privada,
 * datos bloqueados): todo va en try/catch y sin él vale "auto".
 */

const CLAVE = "bordalas.disposicion";
const CORTE = 760;
const MODOS = ["auto", "movil", "pc"];

function leer() {
  try {
    const v = window.localStorage.getItem(CLAVE);
    return MODOS.includes(v) ? v : "auto";
  } catch {
    return "auto";
  }
}

function guardar(v) {
  try {
    if (v === "auto") window.localStorage.removeItem(CLAVE);
    else window.localStorage.setItem(CLAVE, v);
  } catch {
    /* sin almacenamiento: se queda para esta visita */
  }
}

/* El ancho de verdad del aparato. `screen.width` no cambia cuando
   el modo PC agranda el viewport, así que al volver a "auto" el
   teléfono sigue siendo un teléfono. */
function anchoDelAparato() {
  if (typeof window === "undefined") return 1280;
  const pantalla = window.screen?.width || window.innerWidth;
  return Math.min(window.innerWidth, pantalla);
}

function ponerViewport(ancho) {
  const meta = document.querySelector('meta[name="viewport"]');
  if (!meta) return;
  const quiero = ancho
    ? `width=${ancho}`
    : "width=device-width, initial-scale=1.0";
  if (meta.getAttribute("content") !== quiero) {
    meta.setAttribute("content", quiero);
  }
}

export function useDisposicion() {
  const [modo, setModoEstado] = useState(leer);
  const [ancho, setAncho] = useState(anchoDelAparato);

  useEffect(() => {
    const alCambiar = () => setAncho(anchoDelAparato());
    window.addEventListener("resize", alCambiar);
    return () => window.removeEventListener("resize", alCambiar);
  }, []);

  const automatico = ancho <= CORTE ? "movil" : "pc";
  const efectivo = modo === "auto" ? automatico : modo;

  useEffect(() => {
    document.documentElement.dataset.layout = efectivo;
    // PC forzado en un teléfono: se dibuja a 1280 y se encoge.
    const pantalla = window.screen?.width || 1280;
    ponerViewport(efectivo === "pc" && pantalla <= CORTE ? 1280 : null);
  }, [efectivo]);

  const setModo = (v) => {
    const nuevo = MODOS.includes(v) ? v : "auto";
    guardar(nuevo);
    setModoEstado(nuevo);
  };

  return { modo, efectivo, setModo };
}
