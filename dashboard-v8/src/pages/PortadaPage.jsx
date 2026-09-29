import { minutosDeLaFoto } from "../lib/relojes";

/* LA PORTADA DEL DUEÑO (29/09/2026)
 *
 * «Algo así pero más sencillo.» Lo que el dueño mira en el
 * móvil: pocas tarjetas grandes, cada una con un número o una
 * frase. Nada de tablas ni de jerga.
 *
 *   ARRIBA     Pepe, la hora de la última vuelta y si salió bien
 *   1. LA LIGA     puesto y puntos contra el líder y el de al lado
 *   2. EL DINERO   saldo, lo máximo que se puede pujar, lo apartado
 *   3. EL ONCE     quién juega esta jornada
 *   4. PEPE        lo último que hizo
 *
 * LA REGLA
 *
 *   Todo sale de status.json. Si un dato no viene se escribe
 *   «sin dato» y la tarjeta sigue en pie: nunca un cero ni un
 *   número inventado. Si se duda entre enseñar algo o no, no se
 *   enseña: el detalle vive en las otras pestañas.
 *
 *   Lo que hoy NO publica status.json y aquí sale «sin dato»:
 *     - el once objetivo y los puntos que nos separan de él
 *     - la lista de interruptores BORDALAS_* encendidos
 *     - el resultado (verde/rojo) del workflow de GitHub; el
 *       semáforo se hace con lo que la foto sabe de sí misma
 *
 *   Esta página no decide nada y no escribe nada: solo lee.
 */

const SIN_DATO = "sin dato";

const LINEAS = [
  [1, "Portero"],
  [2, "Defensas"],
  [3, "Medios"],
  [4, "Delanteros"]
];

function numero(v) {
  const n = Number(v);
  return v == null || v === "" || !Number.isFinite(n) ? null : n;
}

/* 4.324.615 -> "4,32 M€": se lee de un golpe en el móvil. */
function millones(v) {
  const n = numero(v);
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

/* Marca de Madrid sin zona ("2026-09-18T16:16:38") -> {dia, hora}.
   Ya es hora de Madrid: se lee tal cual. Si trae zona, se pasa a
   Madrid con el navegador. */
function enMadrid(texto) {
  if (!texto) return null;
  const s = String(texto).replace(" ", "T");
  if (/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) {
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    const p = Object.fromEntries(
      new Intl.DateTimeFormat("es-ES", {
        timeZone: "Europe/Madrid",
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
      })
        .formatToParts(d)
        .map((x) => [x.type, x.value])
    );
    return { dia: `${p.day}/${p.month}`, hora: `${p.hour}:${p.minute}` };
  }
  const m = s.match(/^\d{4}-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  return m ? { dia: `${m[2]}/${m[1]}`, hora: `${m[3]}:${m[4]}` } : null;
}

function haceCuanto(min) {
  if (min == null) return null;
  if (min < 1) return "ahora mismo";
  if (min < 60) return `hace ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 48) return `hace ${h} h`;
  return `hace ${Math.floor(h / 24)} días`;
}

function Tarjeta({ titulo, children }) {
  return (
    <section className="pt-card">
      <h2 className="pt-h">{titulo}</h2>
      {children}
    </section>
  );
}

/* ---------------- ARRIBA: PEPE Y LA ÚLTIMA VUELTA ---------------- */

function LaVuelta({ data }) {
  const generado = data.meta?.generated_at;
  const cuando = enMadrid(generado);
  const min = minutosDeLaFoto(generado);

  // "Verde" = lo que la foto sabe de sí misma: el ciclo terminó
  // bien, la pantalla cuadra con Biwenger, ningún dato caducado y
  // no hace más de tres horas. El workflow de GitHub no viene.
  const problemas = [];
  if (data.cycle?.success === false) problemas.push("El ciclo terminó con error.");
  if (data.consistency?.available && data.consistency.ok === false)
    problemas.push("La pantalla no cuadra con Biwenger.");
  if (data.lineup?.live?.known && data.lineup.live.matches === false)
    problemas.push("El once puesto en Biwenger no es el que quiere Pepe.");
  if (data.alarmaDeLosSentidos?.hay) problemas.push("Pepe tiene un dato caducado.");
  if (min != null && min > 180) problemas.push("Hace más de 3 horas que no hay vuelta.");
  // Los avisos de arriba no salen en la portada: se dice dónde están.
  const verDetalle = problemas.length > 0;

  const sabemos =
    !!cuando && (data.cycle?.success != null || !!data.consistency?.available);
  const verde = sabemos && problemas.length === 0;
  const tono = !sabemos ? "idle" : verde ? "ok" : "crit";

  return (
    <section className={`pt-hero pt-${tono}`}>
      <img
        className="pt-cara"
        src={verde || !sabemos ? "/bordalas-calm.jpg" : "/bordalas-critical.jpg"}
        alt="Pepe Bordalás"
      />
      <div className="pt-hero-txt">
        <div className="pt-lbl">Última vuelta de Pepe</div>
        <div className="pt-big">{cuando ? cuando.hora : SIN_DATO}</div>
        <div className="pt-sub">
          {cuando ? `${cuando.dia} · hora de Madrid` : ""}
          {min != null ? ` · ${haceCuanto(min)}` : ""}
        </div>
        <span className={`pt-semaforo ${tono}`}>
          {!sabemos ? SIN_DATO : verde ? "● TODO EN VERDE" : "● ALGO NO VA"}
        </span>
        {problemas.length > 0 && <p className="pt-frase">{problemas.join(" ")}</p>}
        {verDetalle && (
          <p className="pt-frase dim">El detalle está en la pestaña INICIO.</p>
        )}
      </div>
    </section>
  );
}

/* ---------------- 1. LA LIGA ---------------- */

function LaLiga({ data }) {
  const tabla = [...(data.competition?.standings || [])].sort(
    (a, b) => Number(a.rank) - Number(b.rank)
  );
  const i = tabla.findIndex((f) => f.is_current_user);
  const yo = tabla[i];

  if (!yo) {
    return (
      <Tarjeta titulo="La liga">
        <div className="pt-big">{SIN_DATO}</div>
      </Tarjeta>
    );
  }

  const pts = Number(yo.points || 0);
  const lider = tabla[0];
  const detras = tabla[i + 1];

  const frase = (r, rol) => {
    const dif = pts - Number(r.points || 0);
    if (dif === 0) return `Empatados con ${r.name} (${rol}).`;
    return dif > 0
      ? `Le sacamos ${dif} a ${r.name} (${rol}).`
      : `${r.name} (${rol}) nos saca ${-dif}.`;
  };

  return (
    <Tarjeta titulo="La liga">
      <div className="pt-duo">
        <div>
          <div className="pt-big">{yo.rank}º</div>
          <div className="pt-lbl">de {tabla.length}</div>
        </div>
        <div>
          <div className="pt-big">{pts}</div>
          <div className="pt-lbl">puntos</div>
        </div>
      </div>
      <p className="pt-frase">
        {i === 0 ? "¡Vamos primeros!" : frase(lider, "el líder")}
      </p>
      {detras && <p className="pt-frase dim">{frase(detras, `${detras.rank}º`)}</p>}
    </Tarjeta>
  );
}

/* ---------------- 2. EL DINERO ---------------- */

function ElDinero({ data }) {
  const s = data.summary || {};
  const saldo = numero(s.balance);
  const dueno = data.pujasDelDueno || {};
  const comprometido = dueno.available ? numero(dueno.committed) : null;

  const vivas = (data.acquisition?.targets || []).filter(
    (t) => Number(t.live_bid || 0) > 0
  );

  const reset = data.marketClock?.next_reset_local;
  const cuando = reset
    ? `el ${reset.replace(" ", " a las ")}`
    : "en el próximo reset, a las 07:00";

  return (
    <Tarjeta titulo="El dinero">
      <div className="pt-lbl">En caja</div>
      <div className={`pt-big ${saldo != null && saldo < 0 ? "pt-down" : ""}`}>
        {millones(saldo)}
      </div>

      <div className="pt-duo">
        <div>
          <div className="pt-mid">{millones(s.maximum_bid)}</div>
          <div className="pt-lbl">lo máximo que se puede pujar</div>
        </div>
        <div>
          <div className="pt-mid">{millones(comprometido)}</div>
          <div className="pt-lbl">apartado en pujas</div>
        </div>
      </div>

      {vivas.length > 0 ? (
        <>
          {vivas.map((t) => (
            <p key={t.id || t.name} className="pt-frase">
              Pujamos <b>{millones(t.live_bid)}</b> por <b>{t.name}</b>.
            </p>
          ))}
          <p className="pt-frase dim">Se sabe si lo ganamos {cuando}.</p>
        </>
      ) : (
        <p className="pt-frase dim">
          {data.acquisition?.available
            ? "Ninguna puja puesta ahora mismo."
            : `Pujas: ${SIN_DATO}.`}
        </p>
      )}
    </Tarjeta>
  );
}

/* ---------------- 3. EL ONCE ---------------- */

function ElOnce({ data }) {
  const lineup = data.lineup || {};
  const jugadores = lineup.players || [];
  const jornada = data.summary?.target_matchday;

  return (
    <Tarjeta titulo={jornada != null ? `El once · jornada ${jornada}` : "El once"}>
      {!jugadores.length ? (
        <div className="pt-big">{SIN_DATO}</div>
      ) : (
        <>
          <div className="pt-mid">{lineup.formation || ""}</div>
          <div className="pt-xi">
            {LINEAS.map(([pos, nombre]) => {
              const aqui = jugadores.filter((p) => Number(p.position) === pos);
              if (!aqui.length) return null;
              return (
                <div key={pos} className="pt-linea">
                  <div className="pt-lbl">{nombre}</div>
                  <div>{aqui.map((p) => p.name).join(" · ")}</div>
                </div>
              );
            })}
          </div>
        </>
      )}
      <p className="pt-frase dim">Once objetivo y puntos que faltan: {SIN_DATO}.</p>
    </Tarjeta>
  );
}

/* ---------------- 4. PEPE ---------------- */

const EN_CRISTIANO = {
  LIST_FOR_LIQUIDITY: "Puso un jugador a la venta para hacer caja",
  EXIT_LISTING: "Puso a la venta un jugador que sobra",
  MONITOR_OFFERS: "Miró las ofertas; no hacía falta tocar nada",
  ACCEPT_NOW: "Aceptó una oferta",
  SAVE_LINEUP: "Guardó el once",
  LINEUP: "Cambió el once",
  BUY_SPECULATION: "Pujó por un jugador para revenderlo",
  SPECULATION_BUY: "Pujó por un jugador para revenderlo",
  RENEW_MARKET_LISTING: "Volvió a poner a la venta un jugador",
  IDLE: "Nada: no hacía falta tocar nada"
};

function Pepe({ data }) {
  const ult = data.lastExecution || {};
  const accion = EN_CRISTIANO[ult.action] || ult.label || null;
  const cuando = enMadrid(ult.timestamp);

  return (
    <Tarjeta titulo="Lo último que hizo Pepe">
      <p className="pt-frase grande">{accion ? `${accion}.` : SIN_DATO}</p>
      {accion && (
        <p className="pt-frase dim">
          {ult.reason ? `${ult.reason} ` : ""}
          {cuando ? `El ${cuando.dia} a las ${cuando.hora}.` : ""}
          {ult.success === false ? " No le salió." : ""}
        </p>
      )}
      <p className="pt-frase dim">Interruptores encendidos: {SIN_DATO}.</p>
    </Tarjeta>
  );
}

export default function PortadaPage({ data }) {
  return (
    <div className="portada">
      <LaVuelta data={data} />
      <LaLiga data={data} />
      <ElDinero data={data} />
      <ElOnce data={data} />
      <Pepe data={data} />
    </div>
  );
}
