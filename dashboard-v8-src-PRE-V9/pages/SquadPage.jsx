import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import LineupPitch from "../components/LineupPitch";
import PlayerAvatar from "../components/PlayerAvatar";
import { formatMoney, positionLabel } from "../lib/utils";

export default function SquadPage({ data }) {
  return (
    <div className="page-stack">
      <Card>
        <CardHeader><CardTitle>PLANTILLA · XI TITULAR</CardTitle></CardHeader>
        <LineupPitch lineup={data.lineup} offers={data.competitive.offers} large />
      </Card>
      <Card>
        <CardHeader><CardTitle>JUGADORES</CardTitle></CardHeader>
        <div className="squad-table">
          {(data.lineup.players || []).map((player) => (
            <div className="squad-table-row" key={player.id}>
              <PlayerAvatar player={player} className="table-avatar" />
              <strong>{player.name}</strong>
              <span>{positionLabel(player.position)}</span>
              <span>{formatMoney(player.price)}</span>
              <span>{player.jp_confidence ? `${player.jp_confidence}% titular` : "—"}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
