import { formatMoney } from "../lib/utils";

/**
 * A QUIEN SOLTARIA PEPE SI NADIE LE OBLIGASE
 *
 * Hasta hoy Pepe solo proponia ventas cuando faltaba caja. Este
 * motor dice a quien soltaria por criterio deportivo, aunque la
 * caja aguante: un Reserva que no va a puntuar, un jugador roto
 * hasta enero, uno cuyo precio se cae.
 *
 * Lleva calculandose desde el 17/08/2026 y no salia en ninguna
 * pantalla. El dueño habia pedido que Pepe vendiera "siempre para
 * mejorar el XI o ganar pasta", y esa mitad estaba hecha,
 * guardada y ciega.
 *
 * ES OBSERVACION. No publica, no vende y no toca Biwenger. Para
 * poder decidir si se le da permiso hay que poder ver antes que
 * haria con el.
 *
 * LAS CUATRO LISTAS
 *
 *   Publicaria  - hoy mismo
 *   Vigila      - le falta poco
 *   No puede    - lo soltaria, pero rompe el once
 *   No toca     - lo ha mirado y ha decidido que no
 *
 * Las dos ultimas son las que suelen faltar en pantallas asi, y
 * son justo las que contestan la pregunta que uno acaba
 * haciendose: "¿y por que no ha vendido a este?". Un veto
 * silencioso es indistinguible de un olvido.
 */

const HIERARCHY_TONE = {
  DIOS: "crit",
  CLAVE: "warn",
  IMPORTANTE: "ok",
  ROTACION: "warn",
  ROTACIÓN: "warn",
  REVULSIVO: "idle",
  RESERVA: "idle",
  DESCARTE: "crit"
};

function Fila({ player, tone, note }) {
  const hierarchy = String(player.hierarchy || "").toUpperCase();

  return (
    <div className="saleline">
      <div className="saleline-top">
        <b>{player.name}</b>

        {player.hierarchy && (
          <span className={`pill ${HIERARCHY_TONE[hierarchy] || "idle"}`}>
            {hierarchy}
          </span>
        )}

        <span className="mono dim">{formatMoney(player.price)}</span>

        <span className={`pill ${tone}`}>{player.sale_score}/100</span>
      </div>

      {/* El motivo por el que NO se propone manda sobre los
          motivos por los que si: es la respuesta a la pregunta
          que uno se esta haciendo al mirar la fila. */}
      {note ? (
        <div className="saleline-note">{note}</div>
      ) : (
        (player.reasons || []).length > 0 && (
          <div className="saleline-reasons">
            {player.reasons.join(" · ")}
          </div>
        )
      )}
    </div>
  );
}

function Bloque({ title, sub, players, tone, noteKey }) {
  if (!players || players.length === 0) return null;

  return (
    <div className="saleblock">
      <div className="saleblock-head">
        <b>{title}</b>
        <span className="dim">{sub}</span>
      </div>

      {players.map((player) => (
        <Fila
          key={player.id}
          player={player}
          tone={tone}
          note={noteKey ? player.held_reason : null}
        />
      ))}
    </div>
  );
}

export default function SaleIntentPanel({ intent }) {
  if (!intent || intent.available === false) {
    return (
      <section className="pan">
        <h2>A QUIÉN VENDERÍA PEPE</h2>
        <div className="empty">
          {intent?.reason || "Sin calcular en este ciclo."}
        </div>
      </section>
    );
  }

  const proposals = intent.proposals || [];
  const watch = intent.watch || [];
  const blocked = intent.blocked || [];
  const untouchable = intent.untouchable || [];

  const nadie =
    proposals.length === 0 &&
    watch.length === 0 &&
    blocked.length === 0 &&
    untouchable.length === 0;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>A QUIÉN VENDERÍA PEPE</h2>
          <div className="sub">
            POR CRITERIO DEPORTIVO, NO POR FALTA DE CAJA
          </div>
        </div>

        {proposals.length > 0 && (
          <span className="pill warn">
            {formatMoney(intent.recovers)}
          </span>
        )}
      </div>

      {nadie ? (
        <div className="empty">
          Nadie que soltar: ningún jugador llega a{" "}
          {intent.watch_score} puntos de venta.
        </div>
      ) : (
        <>
          <Bloque
            title="PUBLICARÍA"
            sub={`${intent.propose_score}+ de venta`}
            players={proposals}
            tone="warn"
          />

          <Bloque
            title="VIGILA"
            sub="le falta poco"
            players={watch}
            tone="idle"
          />

          {/* Lo soltaria y no puede: eso no es una decision
              deportiva, es un limite de plantilla, y se lee muy
              distinto. */}
          <Bloque
            title="NO PUEDE"
            sub="rompería el once"
            players={blocked}
            tone="crit"
            noteKey="held_reason"
          />

          <Bloque
            title="NO TOCA"
            sub="mirado y descartado"
            players={untouchable}
            tone="ok"
            noteKey="held_reason"
          />
        </>
      )}

      <p className="note" style={{ textAlign: "left", marginTop: 9 }}>
        Observación pura: Pepe <b>no</b> publica ni vende por esta vía. Es lo
        que haría si se le diera permiso. Aceptar una oferta que ya está sobre
        la mesa es otra cosa y tiene su propio motor.
      </p>
    </section>
  );
}
