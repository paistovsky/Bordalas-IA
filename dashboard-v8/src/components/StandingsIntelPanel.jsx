import { formatMoney } from "../lib/utils";

/**
 * Clasificacion con inteligencia del rival.
 *
 * La columna que importa no es el patrimonio sino la
 * participacion: cuantas veces puja de verdad cada uno. Poder
 * pagar y ponerse a pujar son cosas distintas, y confundirlas
 * fue justo lo que rompio el primer modelo PvP.
 */

export default function StandingsIntelPanel({ data }) {
  const standings = data.competition?.standings || [];
  const rivals = data.acquisition?.rivals || [];
  const audit = data.ledgerAudit || {};

  const byName = new Map(rivals.map((rival) => [rival.name, rival]));
  const coverage = new Map(
    (audit.by_manager || []).map((manager) => [manager.name, manager.coverage])
  );

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>CLASIFICACIÓN E INTELIGENCIA</h2>
          <div className="sub">{data.competition?.name || "Liga"}</div>
        </div>
        {audit.status && (
          <span className={audit.status === "COMPLETO" ? "pill ok" : "pill warn"}>
            LEDGER {audit.status}
          </span>
        )}
      </div>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>MÁNAGER</th>
            <th className="n">PTS</th>
            <th className="n">PATRIM.</th>
            <th className="n">PUJA</th>
            <th className="n">DATOS</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row) => {
            const rival = byName.get(row.name);
            const cover = coverage.get(row.name);
            const percent =
              rival && !rival.never_bids
                ? Math.round(Number(rival.participation || 0) * 100)
                : null;

            return (
              <tr key={row.user_id} className={row.is_current_user ? "me" : ""}>
                <td className="dim">{row.rank}º</td>
                <td>
                  {row.name}
                  {row.is_current_user && <span className="pill me" style={{ marginLeft: 6 }}>TÚ</span>}
                </td>
                <td className="n">{row.points}</td>
                <td className="n">{formatMoney(row.team_value)}</td>
                <td className="n">
                  {rival?.never_bids ? (
                    <span className="pill idle">NUNCA</span>
                  ) : percent != null ? (
                    <span className={percent >= 40 ? "pill crit" : percent >= 15 ? "pill warn" : "pill idle"}>
                      {percent}%
                    </span>
                  ) : (
                    <span className="dim">—</span>
                  )}
                </td>
                <td className="n">
                  {cover != null ? (
                    <span className={cover >= 1 ? "up" : "down"}>{Math.round(cover * 100)}%</span>
                  ) : (
                    <span className="dim">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left", marginTop: 9 }}>
        PUJA = veces que ese mánager puja de verdad, medida sobre el histórico
        del tablón. DATOS = cuánto de su plantilla actual sabemos explicar.
      </p>
    </section>
  );
}
