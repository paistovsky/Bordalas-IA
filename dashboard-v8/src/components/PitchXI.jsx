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

/**
 * Verde, ambar, rojo.
 *
 * Los cortes NO son inventados aqui: son los mismos que usa el
 * consenso multifuente para votar (>=67 titular, <=40 suplente).
 * Si la pantalla pintase con otros umbrales, un jugador podria
 * salir verde y estar contado como suplente en la decision.
 *
 * Cuando el consenso viene dado, manda el consenso: ha mirado
 * tres fuentes y esto solo mira un numero.
 */
function confidenceClass(value, consensus) {
  const veredicto = String(consensus || "").toUpperCase();

  if (veredicto === "STARTER" || veredicto === "STARTER_LEAN") return "ok";
  if (veredicto === "BENCH" || veredicto === "BENCH_LEAN") return "crit";
  if (veredicto === "UNCERTAIN") return "warn";

  const n = Number(value || 0);
  if (n >= 67) return "ok";
  if (n > 40) return "warn";
  return "crit";
}

/**
 * Los mismos tonos que la tabla de OBJETIVOS, a proposito: un
 * Clave tiene que verse igual en el campo que en el mercado.
 */
const HIERARCHY_TONE = {
  DIOS: "me",
  CLAVE: "ok",
  IMPORTANTE: "ok",
  ROTACIÓN: "warn",
  ROTACION: "warn",
  REVULSIVO: "idle",
  RESERVA: "idle",
  DESCARTE: "crit"
};

const CONSENSUS_LABEL = {
  STARTER: "titular",
  STARTER_LEAN: "titular?",
  UNCERTAIN: "duda",
  BENCH_LEAN: "suplente?",
  BENCH: "suplente"
};

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

  const raw =
    player.starter_probability ??
    player.jp_confidence ??
    player.start_probability ??
    null;

  const confidence = hasConfidence(raw) ? Number(raw) : null;
  const consensus = player.starter_consensus || null;
  const tone = confidenceClass(confidence, consensus);

  // De cuantas fuentes sale. Un 92 % de una sola fuente y un
  // 92 % de tres no valen lo mismo, y el campo lo dice.
  const coverage = Number(player.starter_source_coverage || 0);

  // Ausencia de dato no es dato: si no viene, no se pinta un 0.
  const value =
    player.weekly_expected_value == null ||
    Number.isNaN(Number(player.weekly_expected_value))
      ? null
      : Number(player.weekly_expected_value);

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

      {/* EL ESCUDO NO BASTA.
          Obliga a reconocer veinte escudos diminutos para saber
          de quien juega cada uno. El nombre del equipo se lee. */}
      <div className="pteam">{player.team_name || ""}</div>

      {/* La jerarquia: que ES en su equipo, no si juega el
          sabado. Es lo que decide si se ficha o se vende, asi
          que tiene que estar donde se mira la plantilla. */}
      {player.hierarchy && (
        <div className="phier">
          {/* CORREGIDA A MANO (22/08/2026)
            *
            *   FF tenía a Mangala como Rotación siendo titular
            *   fijo del Getafe, y con esa etiqueta el plan de
            *   deuda lo eligió para venderlo "sin coste
            *   deportivo" siendo el que más puntos llevaba.
            *
            *   Una jerarquía tocada a mano que se pinte igual que
            *   una de FF es una mentira silenciosa. El asterisco
            *   y el motivo son lo que la convierten en una
            *   corrección. */}
          <span
            className={`pill ${
              HIERARCHY_TONE[String(player.hierarchy).toUpperCase()] || "idle"
            }`}
            title={
              player.hierarchy_source === "MANUAL"
                ? `Corregida a mano: FF dice ${
                    player.hierarchy_override?.hierarchy_before ||
                    "otra cosa"
                  }. ${
                    player.hierarchy_override?.motivo || ""
                  } (caduca ${
                    player.hierarchy_override?.caduca || "?"
                  })`
                : undefined
            }
          >
            {String(player.hierarchy).toUpperCase()}
            {player.hierarchy_source === "MANUAL" ? " ✎" : ""}
          </span>
        </div>
      )}

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
            className={tone}
            style={{ width: `${Math.max(Math.min(confidence, 100), 0)}%` }}
          />
        )}
      </div>

      <div className="pfoot">
        <span
          className={confidence == null ? "dim" : `tit ${tone}`}
          title={
            confidence == null
              ? "La fuente externa no ha respondido en esta generación."
              : `${CONSENSUS_LABEL[consensus] || "sin consenso"} · ` +
                (coverage
                  ? `${coverage} fuente${coverage === 1 ? "" : "s"}`
                  : "cobertura desconocida")
          }
        >
          {confidence != null ? `tit. ${confidence}%` : "sin dato"}
          {confidence != null && coverage === 1 ? "*" : ""}
        </span>
        {/* POR QUE ESTE Y NO OTRO.
            El porcentaje solo no explica el once: un Dios al 60 %
            entra por delante de un Revulsivo al 70 %. Este es el
            número con el que se ordena de verdad —jerarquía y
            porcentaje juntos—, para que la suplencia de alguien
            se pueda auditar sin abrir un log. */}
        {value != null && (
          <span className="pev" title="Valor de la semana: jerarquía × pronóstico. Es lo que ordena el once.">
            {value.toFixed(2)}
          </span>
        )}
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
