/* LO DESCONOCIDO SALE COMO DESCONOCIDO (10/09/2026)
 *
 * Doctrina 36. Un valor por defecto no puede absorber el caso
 * mas importante.
 *
 * EL FALLO QUE ESTO CIERRA
 *
 *   THREAT[intel.threat_level] || "pill idle"
 *
 *   `VERY_HIGH` no estaba en la tabla, asi que la amenaza mas
 *   alta del tablero se pintaba en GRIS, igual que "ninguna". El
 *   caso que mas urgia ver era el unico invisible.
 *
 *   Y no dejaba rastro: sin excepcion, sin registro, sin nada
 *   que buscar despues. La pantalla informaba de calma con la
 *   misma cara con la que informaria de calma verdadera.
 *
 * LA FORMA DEL FALLO ES SIEMPRE LA MISMA
 *
 *   El caso peligroso es el que FALTA de la tabla -el nuevo, el
 *   raro, el que nadie previo- y el defecto lo disfraza del caso
 *   mas comun, que casi siempre es el tranquilo.
 *
 * POR ESO ESTO NO ES UN `||` MEJOR ESCRITO
 *
 *   Devuelve un tono PROPIO -ni benigno ni critico- y ademas
 *   ensena el valor crudo que no supo traducir. Si manana
 *   aparece un `VERY_HIGH` nuevo, se ve que aparecio.
 *
 * DONDE SE USA Y DONDE NO
 *
 *   Solo en rutas que DECIDEN o que PINTAN UNA ALARMA. Una
 *   etiqueta de posicion que cae a "?" esta diciendo la verdad y
 *   se queda como esta.
 */

export const TONO_DESCONOCIDO = "pill unknown";

/**
 * El tono de un estado, y "desconocido" si no está en la tabla.
 *
 * Devuelve siempre `{ tono, etiqueta, conocido }`. Nunca lanza.
 */
export function tonoDe(tabla, valor, etiquetaPorDefecto = null) {
  const clave = valor == null ? "" : String(valor);

  const encontrado =
    clave !== "" && Object.prototype.hasOwnProperty.call(tabla, clave)
      ? tabla[clave]
      : undefined;

  if (encontrado !== undefined) {
    return {
      tono: Array.isArray(encontrado) ? encontrado[0] : encontrado,
      etiqueta: Array.isArray(encontrado)
        ? encontrado[1]
        : etiquetaPorDefecto ?? clave,
      conocido: true
    };
  }

  // NO SE SABE, Y SE DICE.
  //
  // El valor crudo va en la etiqueta a propósito: es la única
  // pista de qué llegó. Un "—" aquí sería el mismo fallo con
  // otro color.
  return {
    tono: TONO_DESCONOCIDO,
    etiqueta: clave === "" ? "sin dato" : clave,
    conocido: false
  };
}
