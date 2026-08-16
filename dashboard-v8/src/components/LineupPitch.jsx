import * as Tooltip from "@radix-ui/react-tooltip";
import PlayerAvatar from "./PlayerAvatar";
import { formatMoney, lineupCoords, positionLabel } from "../lib/utils";

function planCandidates(data, player, offer) {
  // Competitive already simulated the XI after selling this exact player.
  // V9.1 telemetry preserves the calculated incoming player objects.
  const direct = Array.isArray(offer?.incoming_players)
    ? offer.incoming_players
    : [];

  if (direct.length) {
    return direct.map((candidate) => ({
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

  // Compatibility fallback.
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

    if (incoming.length) return incoming;
  }

  return [];
}

function PlayerCard({ player, offer, data }) {
  const watched = Boolean(offer);
  const replacements = watched ? planCandidates(data, player, offer) : [];
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

                  <div className="tactical-impact">
                    <div className="tactical-impact-row">
                      <span>AJUSTE TÁCTICO</span>
                      <b>
                        {offer?.formation_before || data?.lineup?.formation || "—"}
                        {" → "}
                        {offer?.formation_after || "—"}
                      </b>
                    </div>

                    <div className="tactical-impact-row">
                      <span>XI DESPUÉS</span>
                      <b>
                        {offer?.post_sale_playable_count != null
                          ? `${offer.post_sale_playable_count}/11`
                          : "—"}
                      </b>
                    </div>

                    <div className="tactical-impact-row">
                      <span>COSTE DEPORTIVO</span>
                      <b className={
                        Number(offer?.lineup_score_loss_percent || 0) > 8
                          ? "impact-danger"
                          : Number(offer?.lineup_score_loss_percent || 0) > 4
                          ? "impact-warning"
                          : "impact-good"
                      }>
                        {offer?.lineup_score_loss_percent != null
                          ? `-${Number(offer.lineup_score_loss_percent).toFixed(1)}%`
                          : "—"}
                      </b>
                    </div>
                  </div>
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

      <div className="pitch-lines" aria-hidden="true">
        <div className="pitch-inner" />
        <div className="pitch-half" />
        <div className="pitch-center" />
        <div className="pitch-spot pitch-spot-center" />

        <div className="pitch-box pitch-box-top" />
        <div className="pitch-box pitch-box-bottom" />
        <div className="pitch-goalarea pitch-goalarea-top" />
        <div className="pitch-goalarea pitch-goalarea-bottom" />

        <div className="pitch-spot pitch-penalty-top" />
        <div className="pitch-spot pitch-penalty-bottom" />
        <div className="pitch-arc pitch-arc-top" />
        <div className="pitch-arc pitch-arc-bottom" />

        <div className="pitch-goal pitch-goal-top" />
        <div className="pitch-goal pitch-goal-bottom" />

        <div className="pitch-corner pitch-corner-tl" />
        <div className="pitch-corner pitch-corner-tr" />
        <div className="pitch-corner pitch-corner-bl" />
        <div className="pitch-corner pitch-corner-br" />
      </div>

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
