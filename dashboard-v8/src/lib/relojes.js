/* LOS RELOJES DE LA TIRA (10/09/2026)
 *
 * Dos cuentas atrás en vivo: el próximo ciclo y el reset.
 *
 * DE DÓNDE SALE EL PRÓXIMO CICLO
 *
 *   No de una estimación: del cron real que hay puesto.
 *
 *     interno (GitHub Actions, UTC)   "7 0-2,7-23 * * *"
 *     externo (cron-job.org, Madrid)  04:45 · 04:50 · 07:15
 *
 *   El interno salta UTC 03-06 a propósito, que es la ventana
 *   del reset en las dos estaciones.
 *
 * Y SI NO LLEGA, SE DICE
 *
 *   Los `schedule` de GitHub se retrasan minutos u horas. Si el
 *   último disparo que tocaba es más nuevo que la foto, el ciclo
 *   no ha entrado, y eso es lo que hay que ver: la cuenta atrás
 *   pasa a "debería haber entrado hace X" en vez de quedarse en
 *   cero fingiendo normalidad.
 *
 * LA HORA DE MADRID
 *
 *   Con `Intl`, que trae la base de zonas del navegador. Ni UTC
 *   ni la hora del equipo: es el mismo error que ya nos costó
 *   dos semanas de ventana perdida.
 */

const HORAS_INTERNAS = [
  0, 1, 2, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
  21, 22, 23
];

const MINUTO_INTERNO = 7;

// Hora de Madrid, en minutos desde medianoche.
const EXTERNOS_MADRID = [4 * 60 + 45, 4 * 60 + 50, 7 * 60 + 15];

// El reset del mercado: 07:00 de Madrid, medido sobre siete días
// seguidos (las ofertas caducan a las 07:00 y la tanda nueva
// nace entre las 07:03 y las 07:09).
const RESET_MADRID = 7 * 60;

// Margen para que un ciclo arranque, corra y publique. Por
// debajo de esto no se llama tarde a nadie.
const GRACIA_MINUTOS = 12;

/** Desfase de Madrid respecto a UTC, en minutos, para ese instante. */
export function desfaseMadrid(fecha) {
  try {
    const partes = new Intl.DateTimeFormat("en-US", {
      timeZone: "Europe/Madrid",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    }).formatToParts(fecha);

    const v = {};
    for (const p of partes) v[p.type] = p.value;

    const comoUtc = Date.UTC(
      Number(v.year),
      Number(v.month) - 1,
      Number(v.day),
      Number(v.hour === "24" ? "00" : v.hour),
      Number(v.minute),
      Number(v.second)
    );

    return Math.round((comoUtc - fecha.getTime()) / 60000);
  } catch {
    // Sin `Intl` no se inventa: se usa el horario de verano
    // europeo, que es lo que rige diez meses al año.
    return 120;
  }
}

/** El instante UTC de una hora de pared de Madrid, ese día. */
function desdeMadrid(base, minutosDelDia, diasDespues = 0) {
  const desfase = desfaseMadrid(base);

  const enMadrid = new Date(base.getTime() + desfase * 60000);

  const dia = new Date(
    Date.UTC(
      enMadrid.getUTCFullYear(),
      enMadrid.getUTCMonth(),
      enMadrid.getUTCDate() + diasDespues,
      0,
      0,
      0
    )
  );

  const objetivo = new Date(
    dia.getTime() + minutosDelDia * 60000
  );

  // Se vuelve a UTC con el desfase del propio día objetivo, no
  // con el de hoy: en el cambio de hora no son el mismo.
  return new Date(
    objetivo.getTime() - desfaseMadrid(objetivo) * 60000
  );
}

/** Todos los disparos programados entre dos instantes. */
function disparos(desde, hasta) {
  const lista = [];

  // Internos: UTC puro.
  const cursor = new Date(desde.getTime());
  cursor.setUTCMinutes(0, 0, 0);
  cursor.setUTCHours(cursor.getUTCHours() - 1);

  for (let i = 0; i < 72; i += 1) {
    const h = new Date(cursor.getTime() + i * 3600_000);
    if (!HORAS_INTERNAS.includes(h.getUTCHours())) continue;
    const t = new Date(h.getTime() + MINUTO_INTERNO * 60000);
    if (t >= desde && t <= hasta) lista.push(t);
  }

  // Externos: hora de pared de Madrid.
  for (let d = -1; d <= 2; d += 1) {
    for (const m of EXTERNOS_MADRID) {
      const t = desdeMadrid(desde, m, d);
      if (t >= desde && t <= hasta) lista.push(t);
    }
  }

  return lista.sort((a, b) => a - b);
}

/**
 * El próximo ciclo, y si el anterior llegó.
 *
 * Devuelve siempre la misma forma. Nunca lanza.
 */
export function proximoCiclo(ahora, fotoISO) {
  try {
    const desde = new Date(ahora.getTime() - 6 * 3600_000);
    const hasta = new Date(ahora.getTime() + 6 * 3600_000);

    const todos = disparos(desde, hasta);

    const pasados = todos.filter((t) => t <= ahora);
    const futuros = todos.filter((t) => t > ahora);

    const ultimo = pasados.length
      ? pasados[pasados.length - 1]
      : null;

    const siguiente = futuros.length ? futuros[0] : null;

    // ¿Llegó el último que tocaba? La foto tiene que ser
    // POSTERIOR a él, con margen para que el ciclo corra.
    let tarde = null;

    if (ultimo && fotoISO) {
      const foto = new Date(fotoISO);

      if (!Number.isNaN(foto.getTime())) {
        const limite = new Date(
          ultimo.getTime() + GRACIA_MINUTOS * 60000
        );

        if (foto < ultimo && ahora > limite) {
          tarde = Math.round(
            (ahora - ultimo.getTime()) / 60000
          );
        }
      }
    }

    return {
      next: siguiente,
      seconds: siguiente
        ? Math.max(0, Math.round((siguiente - ahora) / 1000))
        : null,
      lateMinutes: tarde
    };
  } catch {
    return { next: null, seconds: null, lateMinutes: null };
  }
}

/** Segundos hasta el próximo reset de las 07:00 de Madrid. */
export function segundosAlReset(ahora) {
  try {
    for (const d of [0, 1, 2]) {
      const t = desdeMadrid(ahora, RESET_MADRID, d);
      if (t > ahora) {
        return Math.round((t - ahora) / 1000);
      }
    }
    return null;
  } catch {
    return null;
  }
}

/** "1h 23m" · "4m 12s" · "—". Con signo si va en negativo. */
export function cuenta(segundos) {
  if (segundos == null || Number.isNaN(segundos)) return "—";

  const s = Math.abs(Math.round(segundos));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const seg = s % 60;

  if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
  if (m > 0) return `${m}m ${String(seg).padStart(2, "0")}s`;
  return `${seg}s`;
}

/**
 * Una marca de tiempo de Madrid SIN zona -"2026-09-10T09:04:33"-
 * convertida al instante real.
 *
 * El dashboard publica `generated_at` así. Leerlo como si fuera
 * UTC lo adelanta dos horas, y comparar eso con la hora del cron
 * daría "el ciclo llegó" cuando no ha llegado.
 */
export function madridNaiveAUTC(texto) {
  if (!texto) return null;

  try {
    const limpio = String(texto).replace(" ", "T");

    // Si ya trae zona, se respeta.
    if (/[zZ]|[+-]\d{2}:?\d{2}$/.test(limpio)) {
      return new Date(limpio).toISOString();
    }

    const comoUtc = new Date(`${limpio}Z`);

    if (Number.isNaN(comoUtc.getTime())) return null;

    return new Date(
      comoUtc.getTime() - desfaseMadrid(comoUtc) * 60000
    ).toISOString();
  } catch {
    return null;
  }
}
