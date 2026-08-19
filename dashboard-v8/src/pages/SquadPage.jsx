import PitchXI from "../components/PitchXI";
import LineupPlanPanel from "../components/LineupPlanPanel";
import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

export default function SquadPage({ data }) {
  const lineup = data.lineup || {};
  const starters = data.roster?.starters || lineup.players || [];
  const substitutes = data.roster?.substitutes || [];
  const guardrail = data.guardrail || {};

  const rows = [
    ...starters.map((player) => ({ ...player, starter: true })),
    ...substitutes.map((player) => ({ ...player, starter: false }))
  ];

  return (
    <div className="grid g21">
      <section className="pan pan-pitch">
        <div className="pan-head">
          <div>
            <h2>XI TITULAR</h2>
            <div className="sub">{lineup.formation || "—"} · {lineup.playable ?? 0}/11</div>
          </div>
        </div>
        <PitchXI lineup={lineup} offers={data.competitive?.offers || []} />
      </section>

      <div className="stack">
        <LineupPlanPanel lineup={lineup} guardrail={guardrail} />

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
                <small>suelo {row.floor} · vend. {row.disposable}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="pan">
          <div className="pan-head">
            <div>
              <h2>PLANTILLA</h2>
              <div className="sub">{rows.length} jugadores</div>
            </div>
          </div>

          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th>JUGADOR</th>
                  <th></th>
                  <th className="n">VALOR</th>
                  <th className="n">CAMBIO</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((player) => {
                  const increment = Number(player.price_increment || 0);
                  return (
                    <tr key={player.id}>
                      <td>{player.name}</td>
                      <td className="dim">{positionLabel(player.position)}</td>
                      <td className="n">{formatEuros(player.price)}</td>
                      <td className={increment > 0 ? "n up" : increment < 0 ? "n down" : "n flat"}>
                        {increment > 0 ? "▲" : increment < 0 ? "▼" : "—"}{" "}
                        {increment ? formatMoney(Math.abs(increment)) : ""}
                      </td>
                      <td>
                        <span className={player.starter ? "pill ok" : "pill idle"}>
                          {player.starter ? "TITULAR" : "SUPLENTE"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
