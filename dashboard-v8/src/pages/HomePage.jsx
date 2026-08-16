import PitchXI from "../components/PitchXI";
import TimelinePanel from "../components/TimelinePanel";
import StandingsIntelPanel from "../components/StandingsIntelPanel";
import { formatMoney } from "../lib/utils";

function squadValue(players = []) {
  return players.reduce((total, player) => total + Number(player.price || 0), 0);
}

export default function HomePage({ data }) {
  const lineup = data.lineup || {};
  const guardrail = data.guardrail || {};

  return (
    <>
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

          <PitchXI lineup={lineup} offers={data.competitive?.offers || []} />
        </section>

        <div className="stack">
          <TimelinePanel data={data} />
          <StandingsIntelPanel data={data} />
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
