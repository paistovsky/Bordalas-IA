import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import LineupPitch from "../components/LineupPitch";
import PlayerAvatar from "../components/PlayerAvatar";
import { formatMoney, positionLabel } from "../lib/utils";

function PlayerRow({ player, starter }) {
  return (
    <div className={starter ? "roster-row starter" : "roster-row"}>
      <PlayerAvatar player={player} className="roster-avatar" />
      <div className="roster-name">
        <strong>{player.name}</strong>
        <span>{positionLabel(player.position)} · dorsal {player.number || "—"}</span>
      </div>
      <div className="roster-value">
        <b>{formatMoney(player.price)}</b>
        <span className={Number(player.price_increment) >= 0 ? "price-up" : "price-down"}>
          {Number(player.price_increment) >= 0 ? "▲" : "▼"} {formatMoney(Math.abs(Number(player.price_increment || 0)))}
        </span>
      </div>
      <span className={starter ? "starter-chip" : "bench-chip"}>
        {starter ? "TITULAR" : "SUPLENTE"}
      </span>
    </div>
  );
}

export default function SquadPage({ data }) {
  const starters = data.roster?.starters || data.lineup.players || [];
  const substitutes = data.roster?.substitutes || [];

  return (
    <div className="squad-layout">
      <Card className="squad-pitch-card">
        <CardHeader>
          <div>
            <CardTitle>XI TITULAR</CardTitle>
            <p className="section-subtitle">
              FORMACIÓN {data.lineup.formation || "—"} · XI {data.lineup.playable || 0}/11
            </p>
          </div>
        </CardHeader>
        <LineupPitch
          lineup={data.lineup}
          offers={data.competitive.offers}
          data={data}
        />
      </Card>

      <Card className="roster-card">
        <CardHeader>
          <div>
            <CardTitle>PLANTILLA</CardTitle>
            <p className="section-subtitle">
              {data.roster?.count || starters.length + substitutes.length} jugadores
            </p>
          </div>
        </CardHeader>

        <div className="roster-scroll">
          <div className="roster-section-title">
            TITULARES <span>{starters.length}</span>
          </div>
          {starters.map((player) => (
            <PlayerRow key={`s-${player.id}`} player={player} starter />
          ))}

          <div className="roster-section-title bench-title">
            SUPLENTES <span>{substitutes.length}</span>
          </div>
          {substitutes.length
            ? substitutes.map((player) => (
                <PlayerRow key={`b-${player.id}`} player={player} starter={false} />
              ))
            : <div className="empty-state">La telemetría aún no ha publicado suplentes.</div>
          }
        </div>
      </Card>
    </div>
  );
}
