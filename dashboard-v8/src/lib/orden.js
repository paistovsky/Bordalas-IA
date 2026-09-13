/* EL ORDEN DEL CUADRO DE OBJETIVOS (13/09/2026)
 *
 * POR QUE AGRUPADO Y NO UNA SOLA LISTA
 *
 *   No hay un orden único porque no hay un solo interés. "Para
 *   el once" se mide en PUNTOS y "para revender" en PRIMA DEL
 *   COMPUTER, y no tenemos el cambio entre las dos unidades.
 *
 *   Ordenar los sesenta por uno solo haría que la mitad de las
 *   filas salieran ordenadas por un criterio que no decide sobre
 *   ellas.
 *
 * EL ORDEN
 *
 *   1. los que ya tienen PUJA PUESTA
 *   2. PARA EL ONCE      con el criterio del TABLÓN
 *   3. PARA REVENDER     con el criterio del CARRIL
 *   4. NO VALE           al final
 *
 * CERO PUNTUACIONES INVENTADAS
 *
 *   El bloque del once conserva el orden en que LLEGA, que ya es
 *   el del tablón —`(decision, escalón, -expected_value,
 *   -our_value)`—.
 *
 *   El de revender se ordena por `acquisition.orden_del_carril`,
 *   una lista de ids que publica la telemetría llamando a
 *   `orden_de_preferencia`, la MISMA función del motor. La
 *   pantalla no reimplementa la tabla de primas medidas: un
 *   dato, un sitio.
 *
 *   Si esa lista no viniera, el bloque conserva su orden de
 *   llegada y no se inventa nada.
 */

export const BLOQUES = [
  { clave: "once", titulo: "PARA EL ONCE" },
  { clave: "revender", titulo: "PARA REVENDER" },
  { clave: "noVale", titulo: "NO VALE" },
  { clave: "sinSaber", titulo: "SIN CLASIFICAR" }
];

export function tienePuja(fila) {
  return Number(fila?.live_bid || 0) > 0;
}

/** A qué bloque va esta fila. Nunca devuelve vacío. */
export function bloqueDe(fila) {
  const via = String(fila?.intent || "").toUpperCase();

  if (via === "SPECULATION") return "revender";

  if (via === "XI_UPGRADE" || via === "KEEP") return "once";

  const decision = String(fila?.decision || "").toUpperCase();

  if (decision === "SIN_VALOR" || decision === "NO_DISPONIBLE") {
    return "noVale";
  }

  return "sinSaber";
}

/**
 * Las filas agrupadas, cada bloque con SU criterio.
 *
 * Devuelve `[{ clave, titulo, filas }]`, con el bloque de puja
 * viva delante. Nunca lanza.
 */
export function agrupado(targets, ordenDelCarril) {
  const filas = Array.isArray(targets) ? targets : [];

  const conPuja = filas.filter(tienePuja);

  const resto = filas.filter((fila) => !tienePuja(fila));

  // EL CRITERIO DEL CARRIL, tal como lo publica el motor.
  const posicion = new Map(
    (Array.isArray(ordenDelCarril) ? ordenDelCarril : []).map(
      (id, indice) => [Number(id), indice]
    )
  );

  const porElCarril = (unas) =>
    [...unas].sort((a, b) => {
      const ia = posicion.has(Number(a.id))
        ? posicion.get(Number(a.id))
        : Number.MAX_SAFE_INTEGER;

      const ib = posicion.has(Number(b.id))
        ? posicion.get(Number(b.id))
        : Number.MAX_SAFE_INTEGER;

      return ia - ib;
    });

  const grupos = BLOQUES.map(({ clave, titulo }) => {
    const suyas = resto.filter((fila) => bloqueDe(fila) === clave);

    return {
      clave,
      titulo,
      // El once y los demás conservan su orden de llegada, que ya
      // es el del tablón. Solo revender se reordena, y con la
      // lista del motor.
      filas: clave === "revender" ? porElCarril(suyas) : suyas
    };
  }).filter((grupo) => grupo.filas.length);

  return conPuja.length
    ? [
        {
          clave: "conPuja",
          titulo: "YA TENEMOS PUJA PUESTA",
          filas: conPuja
        },
        ...grupos
      ]
    : grupos;
}
