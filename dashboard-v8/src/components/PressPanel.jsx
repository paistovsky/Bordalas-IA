import { formatMoney } from "../lib/utils";

/**
 * LO QUE DICE LA PRENSA (05/09/2026)
 *
 *   Las tres webs de mercado que ya lee Pepe copian el precio de
 *   Biwenger: el 06/09 se midieron cero discrepancias de
 *   dirección en 288 jugadores. Son la misma medida repetida.
 *
 *   La prensa es lo único independiente. Un parte médico, una
 *   convocatoria, un entrenador anunciando rotaciones: eso
 *   todavía no está en ningún precio.
 *
 * DATO Y DEDUCCIÓN, SEPARADOS
 *
 *   El titular, la frase y el enlace son DATO: es lo que publicó
 *   el medio, literal. La clase de noticia y la dirección las
 *   pone el bot con palabras clave, y por eso se marcan.
 *
 * NO DECIDE NADA
 *
 *   Se publica al lado de lo que decide Pepe. Ningún motor lee
 *   este bloque.
 */

const TONO = {
  BAJA: "pill crit",
  DUDA: "pill warn",
  VUELVE: "pill ok",
  ALINEACION: "pill idle",
  FICHAJE: "pill idle"
};

const ETIQUETA = {
  BAJA: "BAJA",
  DUDA: "DUDA",
  VUELVE: "VUELVE",
  ALINEACION: "ONCE",
  FICHAJE: "MERCADO"
};

function cuando(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export default function PressPanel({ data }) {
  const press = data.press || { available: false };

  if (!press.available) {
    return (
      <section className="pan">
        <h2>LO QUE DICE LA PRENSA</h2>
        <div className="empty">
          {press.reason || "Todavía no hay informe de prensa."}
        </div>
      </section>
    );
  }

  const fuentes = Object.entries(press.sources || {});

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LO QUE DICE LA PRENSA</h2>
          <div className="sub">
            {press.headlines} titulares · {press.players_with_signal} jugadores
            con señal de {press.players_mentioned} mencionados
          </div>
        </div>
        <span className="pill idle">NO DECIDE</span>
      </div>

      {press.items_total === 0 ? (
        <div className="empty">
          Ninguna noticia de hoy dice nada de un jugador de Biwenger
          con las tres condiciones de emparejamiento.
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>QUÉ</th>
              <th>JUGADOR</th>
              <th className="n">PRECIO</th>
              <th>LO QUE SE PUBLICÓ</th>
              <th>MEDIO</th>
            </tr>
          </thead>
          <tbody>
            {(press.items || []).map((item, i) => (
              <tr key={`${item.player_id}-${i}`}>
                <td>
                  <span className={TONO[item.kind] || "pill idle"}>
                    {ETIQUETA[item.kind] || item.kind}
                  </span>
                </td>
                <td>{item.player_name}</td>
                <td className="n">{formatMoney(item.market_price)}</td>
                <td>
                  {/* LA CITA LITERAL. Es lo único que permite
                      discutir un fallo dentro de un mes. */}
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noreferrer">
                      {item.quote}
                    </a>
                  ) : (
                    item.quote
                  )}
                </td>
                <td className="dim">
                  {item.source}
                  {cuando(item.published_at) ? (
                    <div style={{ fontSize: 9 }}>
                      {cuando(item.published_at)}
                    </div>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* LOS CANALES, CON EL QUE NO ENTRA Y POR QUÉ.
          Una fuente apagada en silencio es indistinguible de una
          fuente olvidada. */}
      <div style={{ marginTop: 10 }}>
        <div className="sub">CANALES</div>
        {fuentes.map(([nombre, fuente]) => (
          <div className="kv" key={nombre}>
            <span>
              {nombre}{" "}
              {fuente.enabled ? (
                <span className={fuente.ok ? "pill ok" : "pill crit"}>
                  {fuente.ok ? `${fuente.items} titulares` : "no contesta"}
                </span>
              ) : (
                <span className="pill idle">NO ENTRA</span>
              )}
            </span>
            <b className="dim" style={{ fontWeight: 400 }}>
              {fuente.enabled
                ? `${fuente.matched} con jugador · ${fuente.note || ""}`
                : fuente.error}
            </b>
          </div>
        ))}
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        El titular, la frase y el enlace son <b>dato</b>: es lo que
        publicó el medio. La clase de noticia y la dirección son{" "}
        <b>deducción</b> del bot a partir de palabras clave sobre la
        frase citada. {press.confidence_basis} Cuando una frase nombra a
        más de un jugador no se deduce nada: se deja la cita y se dice.
      </p>
    </section>
  );
}
