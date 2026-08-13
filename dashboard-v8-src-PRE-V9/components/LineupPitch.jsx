import * as Tooltip from "@radix-ui/react-tooltip";
import PlayerAvatar from "./PlayerAvatar";
import { formatMoney, lineupCoords, positionLabel } from "../lib/utils";

function PlayerCard({ player, offer }) {
  const watched = Boolean(offer);

  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <article
          className={watched ? "pitch-player watched" : "pitch-player"}
          style={{ left: `${player.x}%`, top: `${player.y}%` }}
        >
          <PlayerAvatar player={player} />
          <div className="pitch-player-info">
            <div className="player-topline">
              <span className="shirt-number">{player.number || positionLabel(player.position)}</span>
              <strong>{player.name}</strong>
            </div>
            <div className="player-finance">
              <span>{formatMoney(player.price)}</span>
              <b>{player.jp_confidence ? `${player.jp_confidence}%` : "—"}</b>
            </div>
          </div>
        </article>
      </Tooltip.Trigger>

      <Tooltip.Portal>
        <Tooltip.Content className="tooltip-card" sideOffset={10}>
          <strong>{player.name}</strong>
          <div className="tooltip-grid">
            <span>Valor</span><b>{formatMoney(player.price)}</b>
            <span>Titularidad</span><b>{player.jp_confidence ? `${player.jp_confidence}%` : "—"}</b>
            {offer && <>
              <span>Oferta rival</span><b>{formatMoney(offer.amount)}</b>
              <span>Precio Bordalás</span><b>{formatMoney(offer.authoritative_counter_amount || offer.strategic_sell_price)}</b>
            </>}
          </div>
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export default function LineupPitch({ lineup, offers = [], large = false }) {
  const offersByPlayer = new Map(
    offers.map((offer) => [Number(offer.player_id), offer])
  );
  const players = lineupCoords(lineup.players || []);

  return (
    <div className={large ? "football-pitch large" : "football-pitch"}>
      <div className="pitch-inner" />
      <div className="pitch-half" />
      <div className="pitch-center" />
      <div className="pitch-box pitch-box-top" />
      <div className="pitch-box pitch-box-bottom" />
      {players.map((player) => (
        <PlayerCard
          key={player.id}
          player={player}
          offer={offersByPlayer.get(Number(player.id))}
        />
      ))}
    </div>
  );
}
