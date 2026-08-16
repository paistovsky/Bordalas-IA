import { formatMoney, positionLabel } from "../lib/utils";

/**
 * El XI sobre un campo pintado.
 *
 * Las lineas van en su propio contenedor, sin eventos de raton
 * y por detras de las fichas: dibujan area grande, area pequena,
 * punto de penalti, el semicirculo recortado por la linea del
 * area, circulo y punto centrales, porterias y corners.
 */

function PitchLines() {
  return (
    <div className="pitch-lines" aria-hidden="true">
      <div className="pl-inner" />
      <div className="pl-half" />
      <div className="pl-center" />
      <div className="pl-spot pl-spot-center" />

      <div className="pl-box pl-box-top" />
      <div className="pl-box pl-box-bottom" />
      <div className="pl-goalarea pl-goalarea-top" />
      <div className="pl-goalarea pl-goalarea-bottom" />

      <div className="pl-spot pl-pen-top" />
      <div className="pl-spot pl-pen-bottom" />
      <div className="pl-arc pl-arc-top" />
      <div className="pl-arc pl-arc-bottom" />

      <div className="pl-goal pl-goal-top" />
      <div className="pl-goal pl-goal-bottom" />

      <div className="pl-corner pl-corner-tl" />
      <div className="pl-corner pl-corner-tr" />
      <div className="pl-corner pl-corner-bl" />
      <div className="pl-corner pl-corner-br" />
    </div>
  );
}

function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

function confidenceClass(value) {
  const n = Number(value || 0);
  if (n >= 70) return "";
  if (n >= 40) return "warn";
  return "crit";
}

/**
 * Sin dato no es cero.
 *
 * Pintar "tit. 0 %" cuando la fuente externa falla hace creer
 * que el once no juega. Se dice que no se sabe.
 */
function hasConfidence(value) {
  return value != null && Number(value) > 0;
}

function PlayerCard({ player, watched }) {
  const photo =
    player.photo_url ||
    (player.id
      ? `https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/p/${player.id}.png`
      : null);

  const crest = player.team_id
    ? `https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/${player.team_id}.png`
    : null;

  const raw = player.jp_confidence ?? player.start_probability ?? null;
  const confidence = hasConfidence(raw) ? Number(raw) : null;
  const increment = Number(player.price_increment || 0);

  return (
    <article className={watched ? "pcard watched" : "pcard"} title={player.name}>
      <div className="phead">
        {photo ? (
          <img
            className="pface"
            src={photo}
            alt={player.name}
            onError={(event) => {
              event.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="pface ini">{initials(player.name)}</div>
        )}
        {crest && <img className="pcrest" src={crest} alt="" />}
      </div>

      <div className="pname">{player.name}</div>

      <div className="prow">
        <span className="pval">{formatMoney(player.price)}</span>
        <span className={increment > 0 ? "up" : increment < 0 ? "down" : "flat"}>
          {increment > 0 ? "▲" : increment < 0 ? "▼" : "—"}
          {increment ? formatMoney(Math.abs(increment)) : ""}
        </span>
      </div>

      <div className={confidence == null ? "pbar unknown" : "pbar"}>
        {confidence != null && (
          <i
            className={confidenceClass(confidence)}
            style={{ width: `${Math.max(Math.min(confidence, 100), 0)}%` }}
          />
        )}
      </div>

      <div className="pfoot">
        <span className={confidence == null ? "dim" : ""}>
          {confidence != null ? `tit. ${confidence}%` : "sin dato"}
        </span>
        <span className="pts">
          {player.points != null ? `${player.points} pt` : "—"}
        </span>
      </div>
    </article>
  );
}

export default function PitchXI({ lineup = {}, offers = [], compact = false }) {
  const players = lineup.players || [];
  const watchedIds = new Set(offers.map((offer) => Number(offer.player_id)));

  // De arriba abajo: delanteros primero, portero al fondo.
  const lines = [4, 3, 2, 1].map((position) =>
    players.filter((player) => Number(player.position) === position)
  );

  return (
    <div className={compact ? "pitch compact" : "pitch"}>
      <PitchLines />

      {lines.map((line, index) => (
        <div className="pline" key={index}>
          {line.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              watched={watchedIds.has(Number(player.id))}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
