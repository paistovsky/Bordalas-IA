/* LECTURA: LO QUE COMPARTEN LOS CUADROS NUEVOS (30/09/2026)
 *
 * Las páginas nuevas (EL PLAN, MERCADO, PLANTILLA, LIGA) y la
 * cronología de INICIO leen los mismos datos de la misma forma.
 * Aquí viven esas lecturas para que no haya dos versiones de
 * "quién es nuestro" o "cuándo es el reset".
 *
 * Regla de la casa: nada de lo que sale de aquí se inventa. Si un
 * dato no está, la función devuelve `null` y el cuadro lo dice o
 * no se pinta.
 */

import { madridNaiveAUTC } from "./relojes";

/* ---------- NÚMEROS ---------- */

/** "9,65 M" · "850 mil €" · "—". Para leer de un vistazo. */
export function millones(valor) {
  if (valor == null || valor === "") return "—";
  const n = Number(valor);
  if (!Number.isFinite(n)) return "—";

  const abs = Math.abs(n);
  const signo = n < 0 ? "−" : "";

  if (abs >= 1_000_000) {
    return `${signo}${(abs / 1_000_000).toLocaleString("es-ES", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })} M`;
  }

  if (abs >= 1_000) {
    return `${signo}${Math.round(abs / 1_000).toLocaleString("es-ES")} mil €`;
  }

  return `${signo}${Math.round(abs).toLocaleString("es-ES")} €`;
}

/** Con signo delante siempre: "+70 mil €", "−1,20 M". */
export function conSigno(valor) {
  const n = Number(valor);
  if (!Number.isFinite(n)) return "—";
  if (n === 0) return "igual";
  return n > 0 ? `+${millones(n)}` : millones(n);
}

export function numero(valor) {
  if (valor == null || valor === "") return null;
  const n = Number(valor);
  return Number.isFinite(n) ? n : null;
}

export function porcentaje(valor) {
  const n = numero(valor);
  return n == null ? null : Math.round(n);
}

/* ---------- NOMBRES ---------- */

/** "Jutglà" y "jutgla" son el mismo jugador. */
export function clave(nombre) {
  return String(nombre || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

const POSICIONES = { 1: "Porteros", 2: "Defensas", 3: "Medios", 4: "Delanteros" };
const POSICION_CORTA = { 1: "POR", 2: "DEF", 3: "MED", 4: "DEL" };

export function posicionLarga(p) {
  return POSICIONES[Number(p)] || "Otros";
}

export function posicionCorta(p) {
  return POSICION_CORTA[Number(p)] || "—";
}

/* ---------- TIEMPO ---------- */

const MADRID = "Europe/Madrid";

function partes(fecha) {
  const f = new Intl.DateTimeFormat("es-ES", {
    timeZone: MADRID,
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(fecha);

  const v = (t) => f.find((p) => p.type === t)?.value || "";
  return { dia: `${v("day")}/${v("month")}`, hora: `${v("hour")}:${v("minute")}` };
}

/** Una fecha con zona, o `null`. Lee también las de Madrid sin zona. */
export function instante(texto) {
  if (!texto) return null;
  if (texto instanceof Date) return Number.isNaN(texto.getTime()) ? null : texto;
  const iso = madridNaiveAUTC(texto);
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "07:00" si es hoy, "mañana 07:00", o "09/10 21:00". Hora de Madrid. */
export function cuando(fecha, ahora = new Date()) {
  if (!fecha) return "—";
  const a = partes(fecha);
  const hoy = partes(ahora).dia;
  const manana = partes(new Date(ahora.getTime() + 86_400_000)).dia;

  if (a.dia === hoy) return `hoy ${a.hora}`;
  if (a.dia === manana) return `mañana ${a.hora}`;
  return `${a.dia} ${a.hora}`;
}

/** "09/10" */
export function dia(fecha) {
  return fecha ? partes(fecha).dia : "—";
}

/** ¿Está por delante de ahora? Lo pasado no se enseña. */
export function porVenir(fecha, ahora = new Date()) {
  return Boolean(fecha) && fecha.getTime() > ahora.getTime();
}

/** El instante de la foto (la última vuelta de Pepe). */
export function instanteDeLaFoto(data) {
  return instante(data?.meta?.generated_at);
}

/** El próximo reset del mercado que trae la foto. `null` si ya pasó o no está. */
export function resetDeLaFoto(data, ahora = new Date()) {
  const reloj = data?.marketClock || {};
  if (!reloj.available) return null;
  const r = instante(reloj.next_reset_iso);
  return porVenir(r, ahora) ? r : null;
}

/** El cierre de la jornada: foto + horas que quedaban. `null` si ya pasó. */
export function cierreDeJornada(data, ahora = new Date()) {
  const horas = numero(data?.summary?.hours_to_deadline);
  const foto = instanteDeLaFoto(data);
  if (horas == null || !foto) return null;
  const c = new Date(foto.getTime() + horas * 3_600_000);
  return porVenir(c, ahora) ? c : null;
}

/* ---------- LO NUESTRO ---------- */

export function plantilla(data) {
  const r = data?.roster || {};
  return Array.isArray(r.players) && r.players.length
    ? r.players
    : [...(r.starters || []), ...(r.substitutes || [])];
}

export function esNuestro(data, nombre) {
  const k = clave(nombre);
  return plantilla(data).some((p) => clave(p.name) === k);
}

/** Saldo de ahora según la foto. `null` si no se publica. */
export function saldo(data) {
  const reloj = data?.solvencyClock || {};
  const s = reloj.balance ?? data?.summary?.balance;
  return numero(s);
}

/** Todos los jugadores de la liga por id (catálogo publicado). */
export function catalogo(data) {
  const mapa = new Map();
  for (const p of data?.todaLaLiga?.players || []) mapa.set(Number(p.id), p);
  return mapa;
}

/**
 * Nuestras pujas vivas: nombre e importe.
 *
 * Primero las del cuadro de objetivos con `live_bid` (lo mismo que
 * lee PUJAS EN VIVO); después las operaciones de `exposure` que no
 * salieran ahí, con el nombre sacado del catálogo.
 */
export function pujasVivas(data) {
  const filas = [];
  const vistos = new Set();

  for (const t of data?.acquisition?.targets || []) {
    const importe = numero(t.live_bid);
    if (importe && importe > 0) {
      filas.push({ id: Number(t.id), nombre: t.name, importe, precio: numero(t.market_price) });
      vistos.add(Number(t.id));
    }
  }

  const cat = catalogo(data);

  for (const op of data?.exposure?.operations || []) {
    const ids = (op.player_ids || []).map(Number);
    if (ids.some((id) => vistos.has(id))) continue;
    const importe = numero(op.amount);
    if (!importe) continue;
    const nombres = ids.map((id) => cat.get(id)?.name).filter(Boolean);
    filas.push({
      id: ids[0],
      nombre: nombres.length ? nombres.join(" + ") : null,
      importe,
      precio: ids.length === 1 ? numero(cat.get(ids[0])?.price) : null
    });
    ids.forEach((id) => vistos.add(id));
  }

  return filas;
}

/** Lo que el Computer ofrece hoy por cada jugador nuestro: Map(clave → importe). */
export function ofertasDelComputer(data) {
  const mapa = new Map();

  for (const p of data?.loNuestroALaVenta?.players || []) {
    const n = numero(p.nos_ofrecen);
    if (n && n > 0) mapa.set(clave(p.name), n);
  }

  for (const o of data?.offers || []) {
    if (String(o.counterparty || "").toUpperCase() !== "COMPUTER") continue;
    if (o.expired) continue;
    const nombres = o.players || [];
    if (nombres.length !== 1) continue;
    const k = clave(nombres[0]);
    if (!mapa.has(k) && numero(o.amount)) mapa.set(k, numero(o.amount));
  }

  return mapa;
}

/* ---------- LA ORDEN DEL GESTOR ---------- */

const ESTADOS = {
  VIVA: "en marcha",
  APAGADA: "escrita, pero Pepe la tiene apagada",
  SIN_ORDEN: "no hay ninguna orden escrita",
  CADUCADA: "caducada",
  SIN_CADUCIDAD: "sin fecha de caducidad, así que Pepe no la cumple",
  NOMBRA_A_UN_INTOCABLE: "nombra a un intocable, así que Pepe no la cumple",
  FICHAJE_MAL_ESCRITO: "el fichaje está mal escrito, así que Pepe no la cumple"
};

/**
 * La orden, leída. `null` si la foto no la publica.
 * `viva` sólo si el motor la da por viva Y no ha caducado.
 */
export function laOrden(data, ahora = new Date()) {
  const o = data?.orden;
  if (!o || typeof o !== "object") return null;

  const caduca = instante(o.caduca);
  const caducada = caduca ? !porVenir(caduca, ahora) : false;
  const estado = String(o.estado || (o.viva ? "VIVA" : "APAGADA"));

  return {
    viva: Boolean(o.viva) && !caducada,
    estado: caducada
      ? ESTADOS.CADUCADA
      : ESTADOS[estado] || (estado.startsWith("ERROR") ? "no se pudo leer" : estado.toLowerCase()),
    caduca,
    fichar: (o.fichar || []).filter((f) => f && f.nombre),
    vender: (o.vender || []).filter((v) => v && v.nombre).map((v) => ({
      ...v,
      desdeFecha: instante(v.desde)
    })),
    proteger: (o.proteger || []).filter(Boolean),
    conservar: (o.conservar || []).filter(Boolean),
    noPujar: (o.no_pujar || []).filter(Boolean)
  };
}

/* ---------- LA SUBASTA DEL RESET ---------- */

/**
 * Las pujas que el ciclo va a lanzar en la ventana del reset.
 *
 * Sólo si de verdad van a pasar: el plan existe y o se ejecuta ya
 * o sólo le falta que se abra la ventana. Si lo frena un
 * interruptor, la solvencia o lo que sea, no se enseña como si
 * fuera a ocurrir. Y nunca por un jugador que la orden prohíbe.
 */
export function pujasDelReset(data, orden) {
  const s = data?.subasta || {};
  if (!s.available) return [];
  const va = s.would_bid || !s.blocked_by || s.blocked_by === "FUERA_DE_VENTANA";
  if (!va) return [];
  const prohibidos = new Set((orden?.noPujar || []).map(clave));
  return (s.bids || [])
    .filter((b) => b && b.name && numero(b.bid) > 0)
    .filter((b) => !prohibidos.has(clave(b.name)));
}

/* ---------- LA LIGA ---------- */

/** Las líneas del tablón de la semana que empiezan por el nombre del mánager. */
export function movimientosDe(data, nombre) {
  const lineas = data?.tablonSemana?.lineas || [];
  const k = clave(nombre);
  if (!k) return [];
  return lineas.filter((l) => clave(l.texto).startsWith(`${k} `));
}
