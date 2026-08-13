import { Card, CardHeader, CardTitle } from "./ui/Card";
import { formatMoney } from "../lib/utils";

export default function LeaguePanel({ data }) {
  const competition = data.competition || {};
  const standings = competition.standings || [];
  const current = standings.find((row) => row.is_current_user);

  // Always keep Pepe visible. If he is outside the top 5,
  // show top 4 + his current position.
  let visible = standings.slice(0, 5);
  if (current && Number(current.rank) > 5) {
    visible = [...standings.slice(0, 4), current];
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>CLASIFICACIÓN BIWENGER</CardTitle>
          <p className="section-subtitle competition-name">
            {competition.name || "COMPETICIÓN"}
          </p>
        </div>
      </CardHeader>

      <div className="league-mini competition-mini">
        {visible.length ? visible.map((row) => (
          <div
            key={`${row.rank}-${row.user_id || row.name}`}
            className={`league-row competition-row${row.is_current_user ? " is-current-user" : ""}`}
          >
            <span>{row.rank}º</span>
            <div className="league-team competition-manager">
              <strong>{row.name}</strong>
            </div>
            <b>{row.points} pts</b>
            <small>{formatMoney(row.team_value)}</small>
          </div>
        )) : (
          <div className="empty-state">Clasificación Biwenger aún no disponible.</div>
        )}
      </div>
    </Card>
  );
}
