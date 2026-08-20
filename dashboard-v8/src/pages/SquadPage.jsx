import { useState } from "react";
import PitchXI from "../components/PitchXI";
import LineupPlanPanel from "../components/LineupPlanPanel";
import SquadTable from "../components/SquadTable";
import { formatMoney } from "../lib/utils";

/**
 * PLANTILLA: la mia y la de los seis rivales.
 *
 * EL CASO (20/08/2026)
 *
 *   "¿Sabes lo que no veo? La plantilla del rival."
 *
 *   Estaba en el snapshot desde el primer dia:
 *   `standings[].lineup.players` es el once que alineo cada
 *   manager y `discarded` su banquillo. Los dos juntos son su
 *   plantilla entera, y no la miraba nadie.
 *
 * LAS PESTAÑAS
 *
 *   Van encima del campo y en orden de clasificacion. Se pulsa
 *   un nombre y se ve su plantilla con LAS MISMAS COLUMNAS que
 *   la propia, que es lo unico que hace la comparacion honesta.
 *
 *   Cuando se mira a un rival el campo no cambia: el XI de la
 *   izquierda es siempre el de Pepe, porque es el que se puede
 *   tocar. Lo del rival es informacion, no una decision.
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

  // null = mi plantilla. Un user_id = la de ese manager.
  const [viendo, setViendo] = useState(null);

  const mios = data.roster?.players || [];

  const managerElegido =
    viendo != null
      ? managers.find((m) => m.user_id === viendo) || null
      : null;

  const jugadores = managerElegido ? managerElegido.players : mios;

  const rivales = managers.filter((m) => !m.is_current_user);

  return (
    <>
      {/* LAS PESTAÑAS, ENCIMA DE TODO */}
      {rivalSquads.available && rivales.length > 0 && (
        <section className="pan" style={{ marginBottom: 11 }}>
          <div className="pan-head">
            <div>
              <h2>PLANTILLAS DE LA LIGA</h2>
              <div className="sub">
                Pulsa un mánager para ver su plantilla con los mismos datos
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
              <h2>XI TITULAR</h2>
              <div className="sub">
                {lineup.formation || "—"} · VALOR{" "}
                {formatMoney(squadValue(lineup.players))} · LA BARRA ES LA
                PROBABILIDAD DE SER TITULAR
              </div>
            </div>
            <span className={Number(lineup.missing || 0) ? "pill crit" : "pill ok"}>
              {lineup.playable ?? 0}/11
            </span>
          </div>

          <PitchXI
            lineup={lineup}
            offers={data.competitive?.offers || []}
          />
        </section>

        <div className="stack">
          <LineupPlanPanel lineup={lineup} debate={data.lineupDebate} />

          <section className="pan">
            <h2>PLANTILLA POR POSICIÓN</h2>
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
        </div>
      </div>

      {/* LA TABLA, A TODO LO ANCHO: son once columnas */}
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
                ? ` · ${managerElegido.formation || "sin dibujo"} · ${formatMoney(
                    managerElegido.team_value
                  )}`
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
              {managerElegido.squad_size} jugadores de esta plantilla. Los
              huecos dicen «sin dato» en vez de un 0 % que no significaría
              nada.
            </div>
          )}

        <SquadTable players={jugadores} />

        <p className="note" style={{ textAlign: "left" }}>
          {managerElegido
            ? "Titular o suplente es según el once que dejó puesto en Biwenger, no según lo que le convendría poner."
            : "Titular o suplente es según el XI que Pepe alinearía ahora mismo."}{" "}
          La jerarquía es estructural y aguanta la temporada; el % titular es
          de esta semana y cambia cada viernes.
        </p>
      </section>
    </>
  );
}
