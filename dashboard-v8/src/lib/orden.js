/* EL ORDEN DEL CUADRO DE OBJETIVOS (13/09/2026)
 *
 * UNA SOLA LISTA, DE MAYOR A MENOR INTERÉS.
 *
 *   Estuvo agrupada por "para qué" durante una tarde. El dueño
 *   lo vio y prefiere lista corrida: lo que quiere saber no es
 *   de qué tipo es cada fila, sino CUÁNTO LE FALTA A PEPE PARA
 *   ACTUAR.
 *
 * EL ESCALÓN
 *
 *   0  puja puesta                             ya está hecho
 *   1  pujar                                   se hace hoy
 *   2  no compensa · rinde poco · no hay caja   le falta poco
 *   3  lo vende un rival                       puerta cerrada
 *   4  no vale · no disponible                 nada que hacer
 *
 * CERO PUNTUACIONES INVENTADAS
 *
 *   Dentro de cada escalón se conserva EL ORDEN EN QUE LLEGA,
 *   que ya es el del motor —`(decision, escalón de despliegue,
 *   -expected_value, -our_value)`—. La pantalla solo agrupa por
 *   lo que ella misma puede leer de `decision`, que es un dato
 *   publicado, no un cálculo.
 */

/** La acción, en cristiano. Nunca vacía. */
export function accionDe(fila) {
  if (Number(fila?.live_bid || 0) > 0) return "puja puesta";

  const decision = String(fila?.decision || "").toUpperCase();

  switch (decision) {
    case "BID":
      return "pujar";
    case "SUPERA_PRESUPUESTO":
      return "no hay caja";
    case "RENDIMIENTO_INSUFICIENTE":
      return "rinde poco";
    case "MERCADO_DE_RIVAL":
      return "lo vende un rival";
    case "SIN_VALOR":
      return "no vale";
    case "NO_DISPONIBLE":
      return "no disponible";
    default:
      return decision ? "no compensa" : "sin decidir";
  }
}

const ESCALON = {
  "puja puesta": 0,
  pujar: 1,
  "no compensa": 2,
  "rinde poco": 2,
  "no hay caja": 2,
  "lo vende un rival": 3,
  "no vale": 4,
  "no disponible": 4,
  "sin decidir": 4
};

export function escalonDe(fila) {
  const escalon = ESCALON[accionDe(fila)];

  return escalon === undefined ? 4 : escalon;
}

export function tienePuja(fila) {
  return Number(fila?.live_bid || 0) > 0;
}

/** Para qué sirve. Nunca vacío. */
export function paraQueDe(fila) {
  const via = String(fila?.intent || "").toUpperCase();

  if (via === "SPECULATION") return "para revender";

  if (via === "XI_UPGRADE" || via === "KEEP") return "para el once";

  return "—";
}

/**
 * Las filas, en una sola lista y por escalón.
 *
 * `sort` en JavaScript es estable, así que dentro de cada
 * escalón se conserva el orden de llegada — el del motor.
 *
 * Nunca lanza.
 */
export function porInteres(targets) {
  const filas = Array.isArray(targets) ? targets : [];

  return [...filas].sort((a, b) => escalonDe(a) - escalonDe(b));
}
