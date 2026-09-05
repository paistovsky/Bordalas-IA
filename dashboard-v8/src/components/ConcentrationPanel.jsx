import { formatMoney } from "../lib/utils";

/**
 * CONCENTRACIÓN DE LA PLANTILLA (10/09/2026)
 *
 *   No existía ningún tope. Yamal son 22,2 M de los 54,0 M de
 *   plantilla: el 41 % en un solo nombre.
 *
 *   Mientras Pepe no compraba eso era una foto. En cuanto empiece
 *   a desplegar caja, cada compra decide si se concentra más o se
 *   reparte.
 *
 * LOS TOPES SALEN DE LA LIGA, NO DE UN NÚMERO REDONDO
 *
 *   Medido sobre las siete plantillas: los tres que van por
 *   delante están entre el 19 % y el 32 % en su mayor jugador.
 *   Los dos más concentrados van sextos y cuartos. Y nadie lleva
 *   cinco jugadores del mismo club; el líder lleva cuatro.
 *
 * AVISA Y ACOTA, NO PROHÍBE
 *
 *   Estar por encima no obliga a vender a nadie. Lo que se acota
 *   es empeorarlo.
 */
export default function ConcentrationPanel({ data }) {
  const c = data.concentration || { available: false };

  if (!c.available) {
    return (
      <section className="pan">
        <h2>CONCENTRACIÓN</h2>
        <div className="empty">
          {c.reason || "Sin plantilla con precios que medir."}
        </div>
      </section>
    );
  }

  const pct = (v) =>
    `${String((Number(v || 0) * 100).toFixed(1)).replace(".", ",")} %`;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>CONCENTRACIÓN</h2>
          <div className="sub">
            Cuánto pesa el más caro y cuántos hay del mismo club
          </div>
        </div>
        <span className={c.breach_count ? "pill warn" : "pill ok"}>
          {c.breach_count || 0} AVISO{c.breach_count === 1 ? "" : "S"}
        </span>
      </div>

      {(c.breaches || []).map((b, i) => (
        <div className="alert warn" key={i}>
          {b.reason}
        </div>
      ))}

      <div className="kv">
        <span>Plantilla</span>
        <b className="mono">
          {formatMoney(c.squad_value)} en {c.squad_size} fichas
        </b>
      </div>
      <div className="kv">
        <span>Tope por jugador</span>
        <b className="mono">{pct(c.limit_player_share)}</b>
      </div>
      <div className="kv">
        <span>Tope por club</span>
        <b className="mono">{c.limit_same_team} jugadores</b>
      </div>

      <table style={{ marginTop: 8 }}>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th className="n">VALOR</th>
            <th className="n">% DE LA PLANTILLA</th>
          </tr>
        </thead>
        <tbody>
          {(c.players || []).map((p) => (
            <tr key={p.id || p.name}>
              <td>{p.name}</td>
              <td className="n">{formatMoney(p.price)}</td>
              <td className={p.over_limit ? "n down" : "n"}>
                {pct(p.share)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left" }}>
        Los tres mánagers que van por delante están entre el 19 % y el
        32 % en su mayor jugador. Esto <b>avisa y acota</b>: no obliga
        a vender a nadie.
      </p>
    </section>
  );
}
