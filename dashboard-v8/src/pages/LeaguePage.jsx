import StandingsIntelPanel from "../components/StandingsIntelPanel";
import { formatEuros } from "../lib/utils";

export default function LeaguePage({ data }) {
  const audit = data.ledgerAudit || {};

  return (
    <>
      <StandingsIntelPanel data={data} />

      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>LIBRO DE OPERACIONES RIVAL</h2>
            <div className="sub">¿Explicamos la plantilla que tiene hoy cada mánager?</div>
          </div>
          <span className={audit.status === "COMPLETO" ? "pill ok" : "pill warn"}>
            {audit.status || "—"}
          </span>
        </div>

        {audit.available ? (
          <>
            <table>
              <thead>
                <tr>
                  <th>MÁNAGER</th>
                  <th className="n">PLANTILLA</th>
                  <th className="n">DEL SORTEO</th>
                  <th className="n">FICHADOS</th>
                  <th className="n">EXPLICADOS</th>
                  <th className="n">COBERTURA</th>
                </tr>
              </thead>
              <tbody>
                {(audit.by_manager || []).map((manager) => {
                  const coverage = Math.round(Number(manager.coverage || 0) * 100);
                  return (
                    <tr key={manager.name} className={manager.is_us ? "me" : ""}>
                      <td>
                        {manager.name}
                        {manager.is_us && <span className="pill me" style={{ marginLeft: 6 }}>TÚ</span>}
                      </td>
                      <td className="n">{manager.roster_size}</td>
                      <td className="n">{manager.from_initial_draft}</td>
                      <td className="n">{manager.acquired}</td>
                      <td className="n">{manager.explained}</td>
                      <td className="n">
                        <span className={coverage >= 100 ? "pill ok" : "pill warn"}>{coverage}%</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="note" style={{ textAlign: "left" }}>{audit.reason}</p>
          </>
        ) : (
          <div className="empty">{audit.reason || "Sin reconciliación disponible."}</div>
        )}
      </section>

      {data.pointsMarket?.calibrated && (
        <section className="pan">
          <h2>PRECIO DEL PUNTO</h2>
          <div className="sub">Lo que paga el mercado por un punto de la temporada pasada</div>
          <div className="kv"><span>Mediana</span><b className="mono">{formatEuros(data.pointsMarket.rate_median)}</b></div>
          <div className="kv"><span>Barato (p25)</span><b className="mono up">{formatEuros(data.pointsMarket.rate_p25)}</b></div>
          <div className="kv"><span>Caro (p75)</span><b className="mono down">{formatEuros(data.pointsMarket.rate_p75)}</b></div>
          <p className="note" style={{ textAlign: "left" }}>{data.pointsMarket.reason}</p>
        </section>
      )}
    </>
  );
}
