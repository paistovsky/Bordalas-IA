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

  // El margen esperado de cada fila, por id. Se publica aparte
  // porque el filtro vive en Python y aqui solo se pinta.
  const margen = rendija.margen || {};

  // Quien de los que entran se puede pagar de verdad.
  const pagables = rendija.pagables || {};

  const porId = new Map(
    (margen.entran || []).map((x) => [
      x.margen.player_id,
      x.margen
    ])
  );

  const margenDe = (fila) => porId.get(fila.player_id) || null;

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
        {/* EL INDICADOR LO ENCIENDE EL HECHO (doctrina 37).

            Aqui ponia `rendija.en_vivo`, que es la BANDERA del
            modulo. El 12/09 decia EN VIVO sobre codigo que no
            llamaba nadie: la pantalla afirmaba que funcionaba
            porque una constante decia True.

            Ahora lo enciende `ultima_vuelta` — cuando corrio de
            verdad — y si no ha corrido nunca, lo dice. */}
        <span
          className={
            apagado.apagada
              ? "pill crit"
              : !rendija.ultima_vuelta
              ? "pill warn"
              : rendija.en_vivo
              ? "pill ok"
              : "pill idle"
          }
        >
          {apagado.apagada
            ? "CERRADA"
            : !rendija.ultima_vuelta
            ? "NUNCA HA CORRIDO"
            : rendija.en_vivo
            ? "EN VIVO"
            : "APAGADA"}
        </span>
      </div>

      {/* CUANDO CORRIO, Y QUE DECIDIO. Es lo que convierte
          el indicador en un hecho comprobable. */}
      <div className="kv">
        <span>Última vuelta del carril</span>
        <b className="mono">
          {rendija.ultima_vuelta
            ? new Date(rendija.ultima_vuelta).toLocaleString(
                "es-ES",
                {
                  day: "2-digit",
                  month: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit"
                }
              )
            : "nunca"}
        </b>
      </div>

      {rendija.ultima_decision && (
        <p className="note" style={{ textAlign: "left" }}>
          {rendija.ultima_decision}
        </p>
      )}

      {!rendija.ultima_vuelta && (
        <div className="alert warn" style={{ marginTop: 8 }}>
          <b>EL CARRIL NO HA CORRIDO NUNCA.</b> Está armado y
          publicado, pero ningún ciclo lo ha ejecutado todavía.
          Un indicador que se enciende con la intención y no con
          el hecho es exactamente lo que tapó esto durante un
          día.
        </div>
      )}

      {/* LA LINEA QUE SE MIRA CADA DIA.

          Hasta que ponga 1, todo lo del carril es teoria sobre
          codigo que no ha comprado nada. */}
      <div className="kv">
        <span>VIAJES COMPLETADOS</span>
        <b className="mono">
          <span
            className={
              rendija.viajes_completados > 0
                ? "pill ok"
                : "pill warn"
            }
          >
            {rendija.viajes_completados ?? "—"}
          </span>
        </b>
      </div>

      {/* EL SUELO, Y POR QUE ESE Y NO OTRO.

          Igual que el cupo: se pinta lo que dice
          `suelo_de_precio()`, que es su unico sitio. El dia que
          vuelva a 1.000.000 este panel cambia solo. */}
      <div className="kv">
        <span>Suelo de precio</span>
        <b className="mono">
          {rendija.suelo == null
            ? "—"
            : formatMoney(rendija.suelo)}{" "}
          <span
            className={
              rendija.suelo_estado === "NORMAL"
                ? "pill ok"
                : "pill warn"
            }
          >
            {rendija.suelo_estado || "—"}
          </span>
        </b>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        {rendija.suelo_reason}
      </p>

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
                <th className="n">MARGEN</th>
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
                    {/* EL MARGEN ESPERADO, que es el número
                        que decide si el viaje gana dinero. En
                        rojo si no llega al suelo de venta: esa
                        operación espera una oferta que nosotros
                        mismos rechazaríamos. */}
                    <td className="n">
                      {margenDe(f) == null ? (
                        <span className="sub">—</span>
                      ) : (
                        <b
                          className={
                            margenDe(f).llega_al_suelo
                              ? "up"
                              : "down"
                          }
                        >
                          {margenDe(f).margen_percent > 0
                            ? "+"
                            : ""}
                          {margenDe(f).margen_percent.toFixed(2)}%
                          {margenDe(f).supuesto ? " *" : ""}
                        </b>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* QUIEN NO SE PUEDE PAGAR, CON SU NOMBRE.

          El 12/09 el panel decia «8 llegan al suelo, 0 fuera»
          mientras el carril elegia a Cancelo —5.970.000— contra
          un tope por operacion de 843.612. El numero era cierto
          y la conclusion que sugeria, falsa: ni uno de los ocho
          era comprable. Un panel que cuenta candidatos sin
          contar el tope no informa, tranquiliza. */}
      {pagables.no_caben && pagables.no_caben.length > 0 && (
        <div className="alert warn" style={{ marginTop: 8 }}>
          <b>
            {pagables.caben ? pagables.caben.length : 0} de{" "}
            {(pagables.caben ? pagables.caben.length : 0) +
              pagables.no_caben.length}{" "}
            SE PUEDEN PAGAR
          </b>
          {pagables.tope != null && (
            <> · tope por operación {formatMoney(pagables.tope)}</>
          )}
          <div className="sub" style={{ marginTop: 4 }}>
            No caben:{" "}
            {pagables.no_caben
              .map(
                (x) =>
                  `${x.name} (${formatMoney(x.market_price)})`
              )
              .join(" · ")}
          </div>
        </div>
      )}

      <div className="sub" style={{ marginTop: 6 }}>
        {margen.reason}
        {margen.ritmo_supuesto != null && (
          <>
            {" "}· <b>*</b> usa el ritmo supuesto (mediano del
            mercado, {margen.ritmo_supuesto > 0 ? "+" : ""}
            {margen.ritmo_supuesto} %/día), no medido.
          </>
        )}
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        <b>MARGEN</b> = oferta esperada / coste − 1, con la prima
        de reventa de <b>su posición</b> (defensa +3,67 · portero
        +3,26 · medio +2,85 · delantero +1,80). En rojo si no
        llega al suelo de venta: esa operación espera una oferta
        que nosotros mismos rechazaríamos. Quien tiene margen
        negativo <b>no entra en la lista</b>.
      </p>

      <p className="note" style={{ textAlign: "left" }}>
        La columna <b>VIENE</b> no decide nada: la compuerta de ritmo
        se quitó a propósito porque el negocio es el spread, no la
        rampa. Está aquí para ver qué se está comprando de verdad
        mientras pasa — si todos vinieran cayendo, el experimento
        sería «comprar caídos y revender», y eso hay que saberlo
        antes y no después.
      </p>
    </section>
  );
}
