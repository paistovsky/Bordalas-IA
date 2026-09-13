/* EL ORDEN DEL CUADRO DE OBJETIVOS (13/09/2026)
 *
 * LOS QUE YA TIENEN PUJA PUESTA, PRIMEROS.
 *
 *   En el orden del propio tablero van los ULTIMOS: la clave de
 *   ordenación del motor lleva `bool(has_live_bid)` y en Python
 *   `False` va antes que `True`.
 *
 *   Tiene sentido para el motor —con ése ya no hay nada que
 *   hacer— y ninguno para quien mira: lo que está en juego se
 *   lee primero.
 *
 * Y ESTO NO ES UNA PUNTUACIÓN NUEVA.
 *
 *   Es el MISMO orden que llega del motor, con las filas que ya
 *   tienen puja subidas al principio. El resto conserva su
 *   posición exacta. La pantalla no puede tener una opinión
 *   propia sobre a quién pujar: enseñaría una intención que no
 *   es la del bot.
 *
 * Vive aquí y no dentro del JSX para que se pueda probar.
 */

export function conPujaPrimero(targets) {
  const filas = Array.isArray(targets) ? targets : [];

  const tienePuja = (fila) => Number(fila?.live_bid || 0) > 0;

  return [
    ...filas.filter(tienePuja),
    ...filas.filter((fila) => !tienePuja(fila))
  ];
}
