import { useState } from "react";
import PitchXI from "../components/PitchXI";
import SquadTable from "../components/SquadTable";
import { formatMoney } from "../lib/utils";

/**
 * PLANTILLA: la mia y la de los seis rivales, con campo.
 *
 * EL CASO (20/08/2026)
 *
 *   "¿Sabes lo que no veo? La plantilla del rival."
 *   "...pero se trata de que me muestre su XI en el campo también."
 *
 *   Estaba entero en el snapshot desde el primer dia:
 *   `standings[].lineup.players` es el once que dejo puesto cada
 *   manager, `discarded` su banquillo y `type` su dibujo. Los
 *   tres juntos son su equipo, y no lo miraba nadie.
 *
 * SE CAMBIA LA PANTALLA ENTERA, NO UNA TABLA
 *
 *   Al pulsar un rival cambia el campo Y la tabla. Enseñar su
 *   plantilla debajo de MI once seria mezclar dos equipos en la
 *   misma pantalla, que es justo la forma de leerla mal.
 *
 *   El unico bloque que no cambia es el suelo por posicion: es
 *   una regla de venta MIA y no significa nada aplicada a otro.
 *   Por eso baja al final y dice de quien habla.
 *
 * FUERA EL PLAN DE BORDALAS
 *
 *   Ocupaba esta columna para resumir la tabla que tenia debajo.
 *   El dueño lo dijo dos veces; la segunda se quito.
 */

function squadValue(players = []) {
  return players.reduce(
    (total, player) => total + Number(player.price || 0),
    0
  );
}

export default function SquadPage({ data }) {
  const lineup = data.lineup || {};
  const guardrail = data.guardrail || {};
  const rivalSquads = data.rivalSquads || { available: false, managers: [] };

  const managers = rivalSquads.managers || [];

  // null = mi equipo. Un user_id = el de ese manager.
  const [viendo, setViendo] = useState(null);

  const managerElegido =
    viendo != null
      ? managers.find((m) => m.user_id === viendo) || null
      : null;

  const rivales = managers.filter((m) => !m.is_current_user);

  const jugadores = managerElegido
    ? managerElegido.players
    : data.roster?.players || [];

  // El campo del rival se arma con la misma forma que el mio para
  // que lo pinte el MISMO componente. Una segunda version del
  // campo seria una version que se queda atras.
  const once = managerElegido
    ? {
        formation: managerElegido.formation,
        players: managerElegido.players.filter((p) => p.is_starter),
        playable: managerElegido.players.filter((p) => p.is_starter).length,
        missing: 0
      }
    : lineup;

  const titulo = managerElegido
    ? `XI DE ${managerElegido.name.toUpperCase()}`
    : "XI TITULAR";

  return (
    <>
      {/* LAS PESTAÑAS, ENCIMA DE TODO */}
      {rivalSquads.available && rivales.length > 0 && (
        <section className="pan" style={{ marginBottom: 11 }}>
          <div className="pan-head">
            <div>
              <h2>PLANTILLAS DE LA LIGA</h2>
              <div className="sub">
                Pulsa un mánager para ver su XI y su plantilla
              </div>
            </div>
          </div>

          <div className="filters" style={{ marginBottom: 0 }}>
            <button
              className={viendo == null ? "on" : ""}
              onClick={() => setViendo(null)}
              type="button"
            >
              LA MÍA
            </button>

            {rivales.map((manager) => (
              <button
                key={manager.user_id}
                className={viendo === manager.user_id ? "on" : ""}
                onClick={() => setViendo(manager.user_id)}
                type="button"
                title={`${manager.squad_size} jugadores · ${manager.formation || "sin dibujo"}`}
              >
                {manager.rank}. {manager.name}
              </button>
            ))}
          </div>
        </section>
      )}

      <div className="grid g23">
        <section className="pan pan-pitch">
          <div className="pan-head">
            <div>
              <h2>{titulo}</h2>
              <div className="sub">
                {once.formation || "—"} · VALOR{" "}
                {formatMoney(squadValue(once.players))} · LA BARRA ES LA
                PROBABILIDAD DE SER TITULAR
              </div>
            </div>
            <span
              className={
                managerElegido
                  ? "pill idle"
                  : Number(lineup.missing || 0)
                  ? "pill crit"
                  : "pill ok"
              }
            >
              {once.playable ?? 0}/11
            </span>
          </div>

          <PitchXI
            lineup={once}
            offers={managerElegido ? [] : data.competitive?.offers || []}
          />

          {managerElegido && (
            <p className="note" style={{ textAlign: "left" }}>
              Es el once que dejó puesto en Biwenger, no el que le
              convendría poner.
            </p>
          )}
        </section>

        <section className="pan">
          <div className="pan-head">
            <div>
              <h2>
                {managerElegido
                  ? `PLANTILLA DE ${managerElegido.name.toUpperCase()}`
                  : "MI PLANTILLA"}
              </h2>
              <div className="sub">
                {jugadores.length} jugadores
                {managerElegido
                  ? ` · ${formatMoney(managerElegido.team_value)}`
                  : ""}
              </div>
            </div>

            {managerElegido && (
              <div className="filters" style={{ marginBottom: 0 }}>
                <button onClick={() => setViendo(null)} type="button">
                  VOLVER A LA MÍA
                </button>
              </div>
            )}
          </div>

          {/* Cuanta de esa plantilla sabemos explicar. Una pantalla
              a medias no puede parecer una pantalla completa. */}
          {managerElegido &&
            managerElegido.with_starter_data < managerElegido.squad_size && (
              <div className="alert warn">
                Tenemos pronóstico de titularidad para{" "}
                {managerElegido.with_starter_data} de{" "}
                {managerElegido.squad_size} jugadores. Los huecos dicen «sin
                dato» en vez de un 0 % que no significaría nada.
              </div>
            )}

          <SquadTable players={jugadores} />

          <p className="note" style={{ textAlign: "left" }}>
            La jerarquía es estructural y aguanta la temporada; el % titular
            es de esta semana y cambia cada viernes.
          </p>
        </section>
      </div>

      {/* EL SUELO ES UNA REGLA MIA.
          Aplicada a la plantilla de otro no significa nada, asi
          que no cambia con las pestañas y lo dice. */}
      <section className="pan">
        <h2>MI PLANTILLA POR POSICIÓN</h2>
        <div className="sub">Cuántos puede vender sin romper el XI</div>
        <div className="poswrap">
          {(guardrail.by_position || []).map((row) => (
            <div
              className={
                row.owned < row.floor
                  ? "poscel crit"
                  : row.below_desired
                  ? "poscel warn"
                  : "poscel"
              }
              key={row.position}
            >
              <b>{row.name.toUpperCase()}</b>
              <span className="big">{row.owned}</span>
              <small>
                suelo {row.floor} · vend. {row.disposable}
              </small>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
