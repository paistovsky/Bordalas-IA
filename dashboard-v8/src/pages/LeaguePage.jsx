import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { formatMoney } from "../lib/utils";

export default function LeaguePage({ data }) {
  const competition = data.competition || {};
  const standings = competition.standings || [];

  return (
    <div className="page-stack">
      <Card>
        <CardHeader>
          <div>
            <CardTitle>BIWENGER · CLASIFICACIÓN DE LA COMPETICIÓN</CardTitle>
            <p className="section-subtitle">{competition.name || "COMPETICIÓN"}</p>
          </div>
        </CardHeader>

        <div className="league-table-wrap">
          <table className="league-table competition-table">
            <thead>
              <tr>
                <th>POS</th>
                <th>MÁNAGER</th>
                <th>PTS</th>
                <th>VALOR PLANTILLA</th>
                <th>VARIACIÓN</th>
              </tr>
            </thead>
            <tbody>
              {standings.map((row) => (
                <tr
                  key={`${row.rank}-${row.user_id || row.name}`}
                  className={row.is_current_user ? "is-current-user" : ""}
                >
                  <td><strong>{row.rank}º</strong></td>
                  <td><strong>{row.name}</strong>{row.is_current_user && <small className="you-badge">PEPE</small>}</td>
                  <td><strong>{row.points} pts</strong></td>
                  <td>{formatMoney(row.team_value)}</td>
                  <td className={Number(row.team_value_inc) >= 0 ? "success-text" : "danger-text"}>
                    {Number(row.team_value_inc) >= 0 ? "+" : ""}{formatMoney(row.team_value_inc)}
                  </td>
                </tr>
              ))}
              {!standings.length && (
                <tr><td colSpan="5" className="empty-state">Clasificación Biwenger aún no disponible.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
