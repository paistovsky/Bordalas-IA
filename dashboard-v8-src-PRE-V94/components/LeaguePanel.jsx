import { Card, CardHeader, CardTitle } from "./ui/Card";

export default function LeaguePanel({ data }) {
  const standings = data.laliga.standings || [];
  return (
    <Card>
      <CardHeader><CardTitle>CLASIFICACIÓN</CardTitle></CardHeader>
      <div className="league-mini">
        {standings.slice(0, 5).map((row) => (
          <div key={row.rank} className="league-row">
            <span>{row.rank}º</span>
            <div className="league-team">
              {row.logo && <img src={row.logo} alt="" />}
              <strong>{row.team}</strong>
            </div>
            <b>{row.points} pts</b>
            <small>{Number(row.goals_diff) > 0 ? "+" : ""}{row.goals_diff}</small>
          </div>
        ))}
      </div>
    </Card>
  );
}
