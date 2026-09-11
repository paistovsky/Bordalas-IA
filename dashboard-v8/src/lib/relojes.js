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

/* ============================================================
 * LOS DISPAROS, DEFINIDOS UNA VEZ
 * ============================================================
 *
 * De aqui sale TODO: la cuenta atras, la cadencia que se pinta
 * en el aviso amarillo y en el lateral, y el aviso del cambio de
 * hora. Antes la cadencia estaba escrita a mano en tres sitios
 * -"cada 30", "ciclo 30 min", `cycle_minutes: 30`- y cuando el
 * cron paso a ser HORARIO los tres se quedaron mintiendo
 * mientras la cuenta atras iba bien.
 */

// El cron interno, tal cual esta en `bordalas-live.yml`. En UTC,
// que es lo que usa GitHub Actions.
export const CRON_INTERNO = "7 0-2,7-23 * * *";

const HORAS_INTERNAS = [
  0, 1, 2, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
  21, 22, 23
];

const MINUTO_INTERNO = 7;

/* ============================================================
 * LOS DISPAROS EXTERNOS
 * ============================================================
 *
 * cron-job.org, con la zona puesta en "Europe/Madrid". Sin
 * compensacion ninguna: la hora que se escribe es la hora de
 * Madrid en que ocurre.
 *
 *     45,50 4 * * *   ->   04:45 y 04:50   (ventana del reset)
 *     15 7 * * *      ->   07:15           (tras el reset)
 *
 * LA COMPENSACION QUE HUBO AQUI, Y POR QUE YA NO ESTA
 *
 *   Del 10 al 11/09/2026 estos crones llevaron UNA HORA DE
 *   MENOS escrita a mano. La teoria era que cron-job.org aplica
 *   CET siempre y no sigue el horario de verano, asi que lo
 *   escrito ocurria una hora mas tarde.
 *
 *   ERA FALSA. Se dedujo de UN solo caso -un job que disparo a
 *   una hora que no cuadraba- y el historial del dia siguiente
 *   la desmintio de forma directa:
 *
 *       10/09  job "45,52 6" Europe/Madrid  ->  ciclo 07:52
 *       11/09  job "45,50 3" Europe/Madrid  ->  disparos 03:45
 *                                               y 03:50
 *
 *   El segundo es la medicion buena: Madrid SI se honra, y la
 *   compensacion adelantaba los disparos una hora. La ventana
 *   del reset se abrio con el mercado sin resetear.
 *
 *   Lo del 10/09 probablemente era otra cosa -ese job venia de
 *   antes y pudo tener otra zona configurada- pero no se puede
 *   probar y da igual: la medicion directa manda.
 *
 *   NO SE VUELVA A DEDUCIR ESTO DE UN SOLO CASO. Si algun dia un
 *   disparo llega a una hora rara, eso es UNA observacion, no
 *   una regla. La regla se mide con historial.
 *
 * QUE SE VIGILA AHORA
 *
 *   No el cambio de hora -no hay nada que revertir en octubre-
 *   sino lo que de verdad importa: que un ciclo entre a una hora
 *   que NO es ninguna de las configuradas, sea cual sea el
 *   motivo. Lo hace `avisoDeDisparoFueraDeHora()`.
 */

// Lo que hay puesto, tal cual, para poder enseñarlo.
export const EXTERNOS_ESCRITOS = [
  { madrid: "04:45", cron: "45 4 * * *", que: "ventana del reset" },
  { madrid: "04:50", cron: "50 4 * * *", que: "ventana del reset" },
  { madrid: "07:15", cron: "15 7 * * *", que: "tras el reset" }
];

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
    // SIN LA BASE DE ZONAS NO SE INVENTA UN DESFASE.
    //
    // Aqui ponia `return 120`, el horario de verano europeo,
    // "que es lo que rige diez meses al ano". Y por eso mismo
    // estaba mal: acierta diez meses y falla justo los dos en
    // que el desfase importa, sin decir nada.
    //
    // Es la doctrina 35 y la 36 a la vez: un desfase escrito a
    // mano, y un defecto benigno tapando un "no se sabe". Los
    // que llaman a esto ya saben devolver null.
    return null;
  }
}

/** El instante UTC de una hora de pared de Madrid, ese día. */
function desdeMadrid(base, minutosDelDia, diasDespues = 0) {
  const desfase = desfaseMadrid(base);

  // Sin desfase no hay hora de Madrid que valga. Se lanza para
  // que los `try` de arriba devuelvan su forma de "no se sabe"
  // en vez de colocar una hora inventada.
  if (desfase == null) {
    throw new Error("sin base de zonas no se sabe la hora de Madrid");
  }

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
  const desfaseObjetivo = desfaseMadrid(objetivo);

  if (desfaseObjetivo == null) {
    throw new Error("sin base de zonas no se sabe la hora de Madrid");
  }

  return new Date(
    objetivo.getTime() - desfaseObjetivo * 60000
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

    const desfase = desfaseMadrid(comoUtc);

    if (desfase == null) return null;

    return new Date(
      comoUtc.getTime() - desfase * 60000
    ).toISOString();
  } catch {
    return null;
  }
}

/**
 * "25:31" · "1:04:09" · "—". Sin decimales, nunca.
 *
 * `cuenta()` redondea a minutos por encima de la hora, que para
 * una cuenta atras de cabecera se queda corto: "25m" no dice si
 * quedan veinticinco minutos o veintiseis. Aqui van los segundos
 * siempre.
 */
export function mmss(segundos) {
  if (segundos == null || Number.isNaN(segundos)) return "—";

  const s = Math.max(0, Math.round(segundos));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const seg = s % 60;

  const dos = (n) => String(n).padStart(2, "0");

  return h > 0
    ? `${h}:${dos(m)}:${dos(seg)}`
    : `${m}:${dos(seg)}`;
}

/**
 * Minutos ENTEROS desde una marca de Madrid sin zona.
 *
 * `minutesOld` devuelve fraccion -de ahi el "hace 7.0107 min"
 * que salia en la tira- y ademas lee la marca como hora local,
 * que solo acierta si quien mira esta en Madrid. Doctrina 35.
 */
export function minutosDeLaFoto(texto) {
  const iso = madridNaiveAUTC(texto);

  if (!iso) return null;

  const delta = (Date.now() - new Date(iso).getTime()) / 60000;

  return Number.isFinite(delta)
    ? Math.max(0, Math.floor(delta))
    : null;
}

/**
 * Cada cuanto entra un ciclo, en minutos.
 *
 * NO es una constante escrita a mano: se cuenta sobre los
 * disparos de verdad, los mismos que alimentan la cuenta atras.
 * Se toma el hueco MAS FRECUENTE, no la media, porque el hueco
 * de la madrugada -cinco horas sin cron interno- se llevaria la
 * media a un sitio que no describe ningun ciclo real.
 *
 * Cuando el cron corria cada media hora esto daba 30; con el
 * horario `7 0-2,7-23` da 60. Los textos que lo pintan
 * cambian solos.
 */
export function cadenciaMinutos(ahora = new Date()) {
  try {
    const desde = new Date(ahora.getTime());
    const hasta = new Date(ahora.getTime() + 24 * 3600_000);

    const todos = disparos(desde, hasta);

    if (todos.length < 2) return null;

    const huecos = new Map();

    for (let i = 1; i < todos.length; i += 1) {
      const minutos = Math.round(
        (todos[i] - todos[i - 1]) / 60000
      );
      if (minutos <= 0) continue;
      huecos.set(minutos, (huecos.get(minutos) || 0) + 1);
    }

    let mejor = null;

    for (const [minutos, veces] of huecos) {
      if (!mejor || veces > mejor[1]) mejor = [minutos, veces];
    }

    return mejor ? mejor[0] : null;
  } catch {
    return null;
  }
}

/** "cada hora" · "cada 30 min" · "cada 2 h 15 min". */
export function cadenciaEnPalabras(ahora = new Date()) {
  const m = cadenciaMinutos(ahora);

  if (m == null) return "a intervalos desconocidos";
  if (m === 60) return "cada hora";
  if (m < 60) return `cada ${m} min`;

  const h = Math.floor(m / 60);
  const resto = m % 60;

  return resto
    ? `cada ${h} h ${resto} min`
    : `cada ${h} h`;
}

/**
 * Un ciclo que entro a una hora que no es ninguna de las
 * configuradas. `null` si encaja, o si no se puede saber.
 *
 * QUE SUSTITUYE, Y POR QUE
 *
 *   Aqui habia un `avisoDelCambioDeHora()` que preguntaba a la
 *   base de zonas si Madrid seguia en verano, para avisar de que
 *   el 25 de octubre habia que quitar la compensacion de los
 *   crones externos. Esa compensacion no existe: la teoria que
 *   la justificaba era falsa y el historial la desmintio -esta
 *   contado arriba-. Asi que no hay nada que revertir en
 *   octubre y ese aviso no vigilaba nada.
 *
 *   Lo que si hace falta es esto: que si un disparo llega a una
 *   hora que no es la suya, se vea. SEA CUAL SEA EL MOTIVO —una
 *   zona mal puesta, un cron tocado, un job duplicado—. No se
 *   diagnostica la causa: se enseña la hora a la que entro, la
 *   hora a la que tenia que entrar y la diferencia, y que la
 *   mire una persona.
 *
 * POR QUE NO DICE DE QUE ES CULPA
 *
 *   Porque la ultima vez que se dedujo una causa de un solo caso
 *   costo la primera ventana del reset. Una observacion no es
 *   una medicion.
 */
export function avisoDeDisparoFueraDeHora(ahora, fotoISO) {
  try {
    if (!fotoISO) return null;

    const foto = new Date(fotoISO);

    if (Number.isNaN(foto.getTime())) return null;

    // Todos los disparos que podrian explicar esta foto.
    const desde = new Date(foto.getTime() - 3 * 3600_000);
    const hasta = new Date(foto.getTime() + 3 * 3600_000);

    const todos = disparos(desde, hasta);

    if (!todos.length) return null;

    let cerca = null;

    for (const t of todos) {
      const d = Math.abs(t - foto.getTime());
      if (cerca === null || d < cerca.distancia) {
        cerca = { cuando: t, distancia: d };
      }
    }

    const minutos = Math.round(cerca.distancia / 60000);

    // El ciclo tarda en correr y publicar, y un `schedule` de
    // GitHub se retrasa: por debajo de la gracia no hay nada que
    // mirar.
    if (minutos <= GRACIA_MINUTOS) return null;

    const hhmm = (fecha) =>
      fecha.toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/Madrid"
      });

    return {
      motivo: "DISPARO_FUERA_DE_HORA",
      entro: hhmm(foto),
      esperado: hhmm(cerca.cuando),
      minutos,
      texto:
        `El ciclo entró a las ${hhmm(foto)} y el disparo más ` +
        `cercano que hay configurado es el de las ` +
        `${hhmm(cerca.cuando)}: ${minutos} minutos de ` +
        `diferencia. Puede ser un retraso, una zona mal puesta ` +
        `o un job de más — esto no lo distingue, solo dice que ` +
        `no encaja.`,
      configurados: EXTERNOS_ESCRITOS
    };
  } catch {
    return null;
  }
}
