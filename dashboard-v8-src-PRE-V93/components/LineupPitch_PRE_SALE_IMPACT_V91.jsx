import * as Tooltip from "@radix-ui/react-tooltip";
import PlayerAvatar from "./PlayerAvatar";
import { formatMoney, lineupCoords, positionLabel } from "../lib/utils";

function planCandidates(data, player) {
  const portfolio = data?.competitive?.portfolio || {};
  const plans = [
    portfolio.strategic,
    portfolio.current,
    portfolio.recommended,
    data?.raw?.competitive_portfolio?.strategic,
    data?.raw?.competitive_portfolio?.current,
    data?.raw?.competitive_portfolio?.recommended,
    data?.raw?.recommended
  ].filter(Boolean);

  const playerId = Number(player?.id);

  for (const plan of plans) {
    const soldIds = (plan.player_ids || []).map(Number);
    if (!soldIds.includes(playerId)) continue;

    const incoming = Array.isArray(plan.incoming_players)
      ? plan.incoming_players
      : [];

    // Prefer a replacement compatible with the outgoing player's position.
    const samePosition = incoming.filter(
      (candidate) => Number(candidate.position) === Number(player.position)
    );

    const pool = samePosition.length ? samePosition : incoming;
    if (!pool.length) return [];

    return pool.map((candidate) => ({
      ...candidate,
      price: candidate.price || candidate.market_value || candidate.value || 0,
      jp_confidence:
        candidate.jp_confidence ??
        candidate.confidence ??
        candidate.start_probability ??
        null,
      photo_url:
        candidate.photo_url ||
        (candidate.id
          ? `https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/p/${candidate.id}.png`
          : null)
    }));
  }

  return [];
}

function PlayerCard({ player, offer, data }) {
  const watched = Boolean(offer);
  const replacements = watched ? planCandidates(data, player) : [];
  const replacement = replacements[0] || null;

  return (
    <Tooltip.Root delayDuration={120}>
      <Tooltip.Trigger asChild>
        <article
          className={watched ? "pitch-player watched" : "pitch-player"}
          style={{ left: `${player.x}%`, top: `${player.y}%` }}
        >
          <PlayerAvatar player={player} />
          <div className="pitch-player-info">
            <div className="player-topline">
              <span className="shirt-number">
                {player.number || positionLabel(player.position)}
              </span>
              <strong title={player.name}>{player.name}</strong>
            </div>
            <div className="player-finance">
              <span>{formatMoney(player.price)}</span>
              <b>{player.jp_confidence ? `${player.jp_confidence}%` : "—"}</b>
            </div>
          </div>
        </article>
      </Tooltip.Trigger>

      <Tooltip.Portal>
        <Tooltip.Content
          className="tooltip-card player-impact-tooltip"
          sideOffset={12}
          collisionPadding={18}
        >
          <div className="tooltip-player-head">
            <PlayerAvatar player={player} className="tooltip-avatar" />
            <div>
              <strong>{player.name}</strong>
              <small>{positionLabel(player.position)} · {formatMoney(player.price)}</small>
            </div>
          </div>

          <div className="tooltip-grid">
            <span>Valor</span><b>{formatMoney(player.price)}</b>
            <span>Titularidad</span>
            <b>{player.jp_confidence ? `${player.jp_confidence}%` : "—"}</b>
            {offer && <>
              <span>Oferta rival</span><b>{formatMoney(offer.amount)}</b>
              <span>Precio Bordalás</span>
              <b>{formatMoney(
                offer.authoritative_counter_amount ||
                offer.strategic_sell_price
              )}</b>
            </>}
          </div>

          {watched && (
            <div className="replacement-block">
              <span className="replacement-kicker">
                SI SALE {String(player.name || "").toUpperCase()}
              </span>

              {replacement ? (
                <>
                  <strong className="replacement-title">
                    Entra en su lugar
                  </strong>
                  <div className="replacement-player">
                    <PlayerAvatar
                      player={replacement}
                      className="replacement-avatar"
                    />
                    <div>
                      <b>{replacement.name}</b>
                      <small>
                        {positionLabel(replacement.position)}
                        {replacement.price
                          ? ` · ${formatMoney(replacement.price)}`
                          : ""}
                      </small>
                    </div>
                    {replacement.jp_confidence != null && (
                      <em>{replacement.jp_confidence}%</em>
                    )}
                  </div>
                  {replacements.length > 1 && (
                    <small className="replacement-note">
                      Alternativas calculadas: {replacements.map(p => p.name).join(", ")}
                    </small>
                  )}
                </>
              ) : (
                <small className="replacement-note">
                  Bordalás mantiene el XI cubierto, pero la telemetría actual
                  no identifica un sustituto nominal para esta venta.
                </small>
              )}
            </div>
          )}

          <Tooltip.Arrow className="tooltip-arrow" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export default function LineupPitch({
  lineup,
  offers = [],
  data,
  large = false
}) {
  const offersByPlayer = new Map(
    offers.map((offer) => [Number(offer.player_id), offer])
  );
  const players = lineupCoords(lineup.players || []);

  return (
    <div className={large ? "football-pitch large" : "football-pitch"}>
      <div className="pitch-vignette" />
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
          data={data}
        />
      ))}
    </div>
  );
}
