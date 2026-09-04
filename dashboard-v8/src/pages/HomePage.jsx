import PitchXI from "../components/PitchXI";
import RacePanel from "../components/RacePanel";
import TimelinePanel from "../components/TimelinePanel";
import StandingsIntelPanel from "../components/StandingsIntelPanel";
import { formatMoney } from "../lib/utils";

/* FICHAJE FRANQUICIA, FUERA DEL INICIO (19/08/2026)
 *
 * El panel ocupaba un tercio de la columna derecha para decir,
 * ciclo tras ciclo, "Pepe no tiene ningun objetivo de franquicia".
 * Un fichaje franquicia es un Yamal o un Mbappe saliendo al
 * mercado, y eso no pasa: los que habia ya estan colocados.
 *
 * El motor SIGUE calculandose en cada ciclo, asi que el dia que
 * aparezca uno el dato estara ahi. Lo unico que se ha quitado es
 * el hueco permanente en la pantalla principal.
 *
 */

function squadValue(players = []) {
  return players.reduce((total, player) => total + Number(player.price || 0), 0);
}

export default function HomePage({ data }) {
  const lineup = data.lineup || {};
  const guardrail = data.guardrail || {};
  const mandatory = lineup.mandatory_hierarchy || {};

  return (
    <>
      {/* LA CARRERA, LO PRIMERO (05/09/2026)
          Pepe no sabia que iba cuarto. Lo primero que se abre
          a mirar es como voy, no que va a pasar en el reset. */}
      <RacePanel data={data} />

      <div className="grid g23">
        <section className="pan pan-pitch">
          <div className="pan-head">
            <div>
              <h2>XI PARA LA JORNADA</h2>
              <div className="sub">
                {lineup.formation || "—"} · VALOR {formatMoney(squadValue(lineup.players))} ·
                LA BARRA ES LA PROBABILIDAD DE SER TITULAR
              </div>
            </div>
            <span className={Number(lineup.missing || 0) ? "pill crit" : "pill ok"}>
              {lineup.playable ?? 0}/11
            </span>
          </div>

          {/* UN DIOS QUE FALTA TIENE QUE EXPLICARSE.
              La regla es que juegan siempre; la unica excepcion
              es el 0 % motivado. Asi que cuando uno no esta, el
              motivo va aqui arriba y no en un log. */}
          {(mandatory.ruled_out || []).length > 0 && (
            <div className="godnote crit">
              FUERA DEL XI:{" "}
              {mandatory.ruled_out
                .map((god) => `${god.name} (${god.reason || "sin motivo"})`)
                .join(" · ")}
            </div>
          )}

          {/* Un Dios al 0 % que nadie explica. Juega igual —un
              dato suelto no es una baja— pero se canta, porque o
              FF sabe algo que no vemos o el dato está viejo. */}
          {(mandatory.unexplained || []).length > 0 && (
            <div className="godnote warn">
              0 % SIN MOTIVO, JUEGA IGUAL:{" "}
              {mandatory.unexplained.map((god) => god.name).join(" · ")}
            </div>
          )}

          <PitchXI lineup={lineup} offers={data.competitive?.offers || []} />
        </section>

        <div className="stack">
          {/* La clasificacion primero: lo que se abre a mirar es
              como voy, no que va a pasar en el reset. */}
          <StandingsIntelPanel data={data} />
          <TimelinePanel data={data} />
        </div>
      </div>

      {guardrail.available && (
        <section className="pan">
          <h2>PLANTILLA POR POSICIÓN</h2>
          <div className="sub">Tengo / suelo para alinear / vendibles</div>
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
                <small>suelo {row.floor} · vend. {row.disposable}</small>
              </div>
            ))}
          </div>
          {guardrail.goalkeeper_warning && (
            <div className="alert warn" style={{ marginTop: 9, marginBottom: 0 }}>
              🧤 {guardrail.goalkeeper_warning}
            </div>
          )}
        </section>
      )}
    </>
  );
}
