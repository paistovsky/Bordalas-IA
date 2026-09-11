import { formatMoney } from "../lib/utils";
import { tonoDe } from "../lib/tono";

/* LA RENDIJA (11/09/2026)
 *
 * En que cupo esta el carril, POR QUE, y que esta comprando.
 *
 * EL CUPO NO SE ESCRIBE AQUI
 *
 *   Se pinta lo que dice `cupo_del_reset()`, que es su unico
 *   sitio. Si algun dia sube de 2 a 4, este panel cambia solo y
 *   nadie tiene que acordarse de tocar un numero en la pantalla.
 *
 * EL RITMO, QUE NO DECIDE NADA
 *
 *   La compuerta de ritmo se quito a proposito: el negocio es el
 *   spread -se compra al precio del Computer y se revende por
 *   encima- y para eso da igual hacia donde vaya el precio.
 *
 *   Pero quitarla no es dejar de mirar. El libro en la sombra
 *   decia que lo que se rechazaba era todo PRECIO_CAYENDO; si lo
 *   que compramos tambien lo fuera, el experimento real seria
 *   "comprar caidos y revender", y eso hay que saberlo MIENTRAS
 *   PASA. Por eso esta columna existe y por eso NO filtra.
 */

const POSICION = { 1: "POR", 2: "DEF", 3: "MED", 4: "DEL" };

const DIRECCION = {
  SUBIENDO: ["up", "▲ subiendo"],
  PRECIO_CAYENDO: ["down", "▼ cayendo"],
  PLANO: ["dim", "= plano"],
  SIN_DATO: ["sub", "sin dato"]
};

export default function RendijaPanel({ data }) {
  const rendija = data.rendija || {};

  const available = Boolean(rendija.available);

  if (!available) {
    return (
      <section className="pan">
        <h2>LA RENDIJA</h2>
        <div className="empty">
          {rendija.reason ||
            "No se ha podido leer el estado del carril."}
        </div>
      </section>
    );
  }

  const ritmo = rendija.ritmo || {};
  const apagado = rendija.apagado || {};
  const filas = ritmo.filas || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA RENDIJA</h2>
          <div className="sub">
            el carril de comprar para revender · no compite con
            la acción de la vuelta
          </div>
        </div>
        <span
          className={
            apagado.apagada
              ? "pill crit"
              : rendija.en_vivo
              ? "pill ok"
              : "pill idle"
          }
        >
          {apagado.apagada
            ? "CERRADA"
            : rendija.en_vivo
            ? "EN VIVO"
            : "ARMADA Y APAGADA"}
        </span>
      </div>

      {/* EL CUPO, Y POR QUE ESE Y NO OTRO. */}
      <div className="kv">
        <span>Cupo por ciclo de reset</span>
        <b className="mono">
          {rendija.cupo ?? "—"}{" "}
          <span
            className={
              rendija.cupo_estado === "PLENO"
                ? "pill ok"
                : "pill warn"
            }
          >
            {rendija.cupo_estado || "—"}
          </span>
        </b>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        {rendija.cupo_reason}
      </p>

      {/* SE APAGA SOLA. Sólo cuando hay algo que decir. */}
      {apagado.apagada && (
        <div className="alert crit" style={{ marginTop: 8 }}>
          {apagado.reason}
        </div>
      )}

      {/* QUÉ ESTAMOS COMPRANDO DE VERDAD. */}
      <div className="pan-head" style={{ marginTop: 12 }}>
        <div>
          <h2 style={{ fontSize: 12 }}>
            CÓMO VIENEN LOS CANDIDATOS
          </h2>
          <div className="sub">{ritmo.reason}</div>
        </div>
        {ritmo.todos_cayendo && (
          <span className="pill warn">TODOS CAYENDO</span>
        )}
      </div>

      {!filas.length ? (
        <div className="sub">
          Ningún candidato en el mercado ahora mismo.
        </div>
      ) : (
        <div className="scroll-x">
          <table className="tbl">
            <thead>
              <tr>
                <th>JUGADOR</th>
                <th>POS</th>
                <th className="n">PRECIO</th>
                <th>VIENE</th>
                <th className="n">%/DÍA</th>
                <th className="n">DÍAS</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => {
                const [tono, etiqueta] = (DIRECCION[
                  f.direction
                ] || ["sub", f.direction])[0]
                  ? DIRECCION[f.direction] || [
                      "sub",
                      f.direction
                    ]
                  : ["sub", f.direction];

                return (
                  <tr key={f.player_id}>
                    <td>{f.name}</td>
                    <td className="sub">
                      {POSICION[f.position] || "—"}
                    </td>
                    <td className="n sub">
                      {formatMoney(f.market_price)}
                    </td>
                    <td className={tono}>{etiqueta}</td>
                    <td className="n">
                      {f.rate_percent_per_day == null
                        ? "—"
                        : `${f.rate_percent_per_day > 0 ? "+" : ""}${
                            f.rate_percent_per_day
                          }`}
                    </td>
                    <td className="n sub">
                      {f.trend_days ?? "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        Esta columna <b>no decide nada</b>: la compuerta de ritmo
        se quitó a propósito porque el negocio es el spread, no la
        rampa. Está aquí para ver qué se está comprando de verdad
        mientras pasa — si todos vinieran cayendo, el experimento
        sería «comprar caídos y revender», y eso hay que saberlo
        antes y no después.
      </p>
    </section>
  );
}
