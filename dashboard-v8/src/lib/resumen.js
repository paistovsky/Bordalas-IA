/* Ayudantes de las cabeceras de cada página (30/09/2026).
 *
 * Números para leer en el móvil: millones con dos decimales y
 * coma, miles como "mil €". Si el dato no viene, "sin dato": nunca
 * un cero que parezca una medida. */

export const SIN_DATO = "sin dato";

export function num(v) {
  const n = Number(v);
  return v == null || v === "" || !Number.isFinite(n) ? null : n;
}

export function euros(v) {
  const n = num(v);
  if (n == null) return SIN_DATO;
  const abs = Math.abs(n);
  const signo = n < 0 ? "−" : "";
  if (abs >= 1_000_000) {
    return `${signo}${(abs / 1_000_000).toLocaleString("es-ES", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })} M€`;
  }
  if (abs >= 1_000) {
    return `${signo}${Math.round(abs / 1_000).toLocaleString("es-ES")} mil €`;
  }
  return `${signo}${abs.toLocaleString("es-ES")} €`;
}

/* +120 mil € / −35 mil € */
export function variacion(v) {
  const n = num(v);
  if (n == null || n === 0) return "=";
  return `${n > 0 ? "+" : "−"}${euros(Math.abs(n))}`;
}

export const POSICIONES = [
  [1, "Porteros"],
  [2, "Defensas"],
  [3, "Medios"],
  [4, "Delanteros"]
];

/* La amenaza de un rival, en palabras. */
export function amenazaEnPalabras(nivel) {
  return (
    {
      VERY_HIGH: "muy alta",
      HIGH: "alta",
      MEDIUM: "media",
      LOW: "baja",
      VERY_LOW: "muy baja",
      US: "somos nosotros",
      NONE: "ninguna"
    }[String(nivel || "").toUpperCase()] || SIN_DATO
  );
}

/* Las líneas del tablón de un mánager concreto. */
export function lineasDe(tablon, nombre) {
  return ((tablon && tablon.lineas) || []).filter((l) =>
    String(l.texto || "").startsWith(`${nombre} `)
  );
}

/* Las líneas del tablón agrupadas por mánager. El nombre va al
   principio del texto; se prueba primero el nombre más largo para
   que "Pepe" no se quede con las de "Pepe Bordalás". */
export function porManager(tablon, nombres) {
  const orden = [...nombres].sort((a, b) => b.length - a.length);
  const grupos = new Map(nombres.map((n) => [n, []]));
  for (const l of (tablon && tablon.lineas) || []) {
    const texto = String(l.texto || "");
    const quien = orden.find((n) => texto.startsWith(`${n} `));
    if (quien) grupos.get(quien).push(l);
  }
  return grupos;
}

/* Fichajes y ventas de un puñado de líneas. */
export function recuento(lineas) {
  let fichajes = 0;
  let ventas = 0;
  for (const l of lineas) {
    const t = String(l.texto || "");
    if (l.tipo === "market" || / ficha a /.test(t)) fichajes += 1;
    else if (/ vende a /.test(t)) ventas += 1;
  }
  return { fichajes, ventas };
}
