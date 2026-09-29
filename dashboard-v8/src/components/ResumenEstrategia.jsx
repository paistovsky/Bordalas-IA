import { SIN_DATO } from "../lib/resumen";

/* ESTRATEGIA: ¿QUÉ REGLAS SIGUE PEPE? (30/09/2026)
 *
 * Una línea por regla, en palabras, con si está encendida. Salen
 * de lo que status.json publica de cada motor:
 *
 *   - vara          elegir el once con pesos por posición
 *   - subasta       pujar en la ventana del reset
 *   - hold_route    comprar para revender sólo donde ha rendido
 *   - silencio      no tocar nada durante el reset
 *   - concentration el tope por jugador y por equipo
 *   - doctrina      las reglas escritas y cuántas decisiones citan
 *
 * Y arriba del todo, LO QUE PEPE TIENE ENCENDIDO: los
 * interruptores de producción (BORDALAS_*) que publica `reglas`,
 * una línea cada uno con lo que hace en cristiano. El nombre
 * técnico va pequeño y gris, debajo. Sin la clave, el cuadro no se
 * pinta (30/09/2026).
 */

function Regla({ on, titulo, detalle }) {
  return (
    <li className={on === true ? "on" : on === false ? "off" : "nd"}>
      <span className="rs-dot" aria-hidden="true" />
      <div>
        <b>{titulo}</b>
        {detalle && <small>{detalle}</small>}
      </div>
      <span className="rs-estado-regla">
        {on === true ? "encendida" : on === false ? "apagada" : SIN_DATO}
      </span>
    </li>
  );
}

const ESTADO_DOCTRINA = {
  entendido: "se cumple",
  "a medias": "se cumple a medias",
  "construido, no dispara": "está hecha pero todavía no actúa"
};

export default function ResumenEstrategia({ data }) {
  const vara = data.vara || {};
  const subasta = data.raw?.subasta || data.subasta || {};
  const tener = data.holdRoute || {};
  const silencio = data.silencio || {};
  const conc = data.concentration || {};
  const citas = data.doctrina?.citations || {};
  const porRegla = citas.by_rule || [];

  const reglas = data.reglas;

  const pct = (x) => `${Math.round(Number(x) * 100)} %`;

  return (
    <div className="resumen">
      {reglas && (
        <section className="pan rs-card">
          <h2>LO QUE PEPE TIENE ENCENDIDO</h2>
          {reglas.ok === false || !(reglas.reglas || []).length ? (
            <p className="rs-frase dim">
              {reglas.ok === false
                ? "Esta vuelta no se pudo leer qué tiene encendido."
                : "No tiene ninguna regla especial encendida."}
            </p>
          ) : (
            <ul className="rs-encendido">
              {reglas.reglas.map((r) => (
                <li key={r.nombre}>
                  <span className="rs-dot" aria-hidden="true" />
                  <div>
                    {r.que_hace || r.nombre}
                    {r.que_hace && <small>{r.nombre}</small>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section className="pan rs-card">
        <h2>SUS MOTORES, AHORA</h2>
        <ul className="rs-reglas">
          <Regla
            on={vara.available ? !!vara.active : null}
            titulo="Elige el once dando a cada posición su peso"
            detalle="Un delantero y un defensa no puntúan igual: se ordenan con su vara."
          />
          <Regla
            on={subasta.available ? subasta.blocked_by !== "INTERRUPTOR" : null}
            titulo="Puja de madrugada, en la ventana del reset"
            detalle={
              subasta.available
                ? subasta.blocked_by === "FUERA_DE_VENTANA"
                  ? "Espera a su hora: sólo puja entre las 04:45 y las 07:00."
                  : subasta.blocked_by
                  ? `Ahora parada: ${String(subasta.blocked_by).replaceAll("_", " ").toLowerCase()}.`
                  : "Puja en la ventana del reset."
                : null
            }
          />
          <Regla
            on={tener.available ? !!tener.on : null}
            titulo="Compra para revender sólo donde ha dado beneficio"
            detalle={
              tener.available
                ? `Mira los últimos ${tener.horizon_days ?? "?"} días y exige que no se pierda en más del ${pct(tener.max_loss_rate ?? 0)} de las operaciones.`
                : null
            }
          />
          <Regla
            on={silencio.available ? true : null}
            titulo={`No toca nada durante el reset (${silencio.window || "04:45-07:00"})`}
            detalle="A esa hora el mercado se rehace y cualquier movimiento sería a ciegas."
          />
          <Regla
            on={conc.available ? true : null}
            titulo="No se juega todo a un jugador ni a un equipo"
            detalle={
              conc.available
                ? `Tope: ${pct(conc.limit_player_share ?? 0)} del valor en un jugador y ${conc.limit_same_team ?? "?"} del mismo equipo.`
                : null
            }
          />
        </ul>
      </section>

      <section className="pan rs-card">
        <h2>LAS REGLAS ESCRITAS</h2>
        {!citas.available ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : (
          <>
            <p className="rs-frase">
              <b>{citas.cited_percent != null ? `${Math.round(citas.cited_percent)} %` : SIN_DATO}</b>{" "}
              de las decisiones de Pepe se apoyan en una regla escrita.
            </p>
            <ul className="rs-lista">
              {porRegla.map((r) => (
                <li key={r.rule}>
                  <span>
                    {r.title}
                    <small>{ESTADO_DOCTRINA[r.state] || r.state}</small>
                  </span>
                  <b>{r.count}</b>
                </li>
              ))}
            </ul>
            <p className="rs-frase dim">El número es cuántas decisiones de hoy la citan.</p>
          </>
        )}
      </section>
    </div>
  );
}
