import { Card, CardHeader, CardTitle } from "../components/ui/Card";

export default function LeaguePage({ data }) {
  return (
    <div className="page-stack">
      <Card>
        <CardHeader><CardTitle>LALIGA EA SPORTS · CLASIFICACIÓN COMPLETA</CardTitle></CardHeader>
        <div className="league-table-wrap">
          <table className="league-table">
            <thead>
              <tr>
                <th>POS</th><th>EQUIPO</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>PTS</th>
              </tr>
            </thead>
            <tbody>
              {(data.laliga.standings || []).map((row) => (
                <tr key={row.rank}>
                  <td>{row.rank}</td>
                  <td>
                    <div className="league-team">
                      {row.logo && <img src={row.logo} alt="" />}
                      <strong>{row.team}</strong>
                    </div>
                  </td>
                  <td>{row.played}</td><td>{row.win}</td><td>{row.draw}</td><td>{row.lose}</td>
                  <td>{row.goals_for}</td><td>{row.goals_against}</td><td>{row.goals_diff}</td><td><strong>{row.points}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
