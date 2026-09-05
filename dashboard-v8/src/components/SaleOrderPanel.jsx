import { formatMoney } from "../lib/utils";

/**
 * A QUIÉN LE TOCA SALIR (10/09/2026)
 *
 *   En la foto del 05/09 a las 14:03 el saldo estaba en
 *   −421.792 €, la prioridad declarada era "recuperar solvencia",
 *   había doce ofertas sobre la mesa por 45,7 M y el motor de
 *   ofertas contestaba: "0 con signal accionable. Ninguna para
 *   cobrar ahora."
 *
 *   Tres motores hablan de vender y ninguno manda. Esta es la
 *   cola: quién sale primero, quién después y por qué.
 *
 * SE PUEDE PARAR EN CUALQUIER PUNTO
 *
 *   La cola está construida para que vender a los k primeros,
 *   para cualquier k, deje todas las posiciones por encima de su
 *   suelo. No es una lista de sugerencias sueltas.
 *
 * NO VENDE
 *
 *   Observador puro. Esto se calcula y se enseña para que el
 *   dueño pueda leerlo ANTES de que pase.
 */
export default function SaleOrderPanel({ data }) {
  const orden = data.saleOrder || { available: false };

  if (!orden.available) {
    return (
      <section className="pan">
        <h2>ORDEN DE VENTA</h2>
        <div className="empty">
          {orden.reason || "Sin cola de venta calculada."}
        </div>
      </section>
    );
  }

  const cola = orden.queue || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>ORDEN DE VENTA</h2>
          <div className="sub">
            A quién le toca salir cuando haga falta caja
          </div>
        </div>
        <span className="pill idle">NO VENDE</span>
      </div>

      {cola.length === 0 ? (
        <div className="empty">
          Nadie entra en la cola: todos están apartados. Mira la
          lista de abajo para ver por qué.
        </div>
      ) : (
        <>
          <div className="kv">
            <span>Caja en este ciclo</span>
            <b className="mono">
              {formatMoney(orden.cash_one_cycle)}
              {orden.cash_one_cycle_player
                ? ` · ${orden.cash_one_cycle_player}`
                : ""}
            </b>
          </div>
          <div className="kv">
            <span>Sobre la mesa, en ofertas vivas</span>
            <b className="mono">
              {formatMoney(orden.cash_on_the_table)} ·{" "}
              {orden.offers_on_the_table} ofertas
            </b>
          </div>

          <table style={{ marginTop: 8 }}>
            <thead>
              <tr>
                <th>#</th>
                <th>JUGADOR</th>
                <th>MOTIVO</th>
                <th className="n">€/PUNTO</th>
                <th>PRECIO</th>
                <th className="n">ENTRA EN CAJA</th>
              </tr>
            </thead>
            <tbody>
              {cola.map((fila) => (
                <tr key={fila.id} title={fila.reason}>
                  <td className="mono">{fila.order}</td>
                  <td>{fila.name}</td>
                  <td>
                    <span
                      className={
                        fila.tier === "NO_JUEGA" ? "pill warn" : "pill idle"
                      }
                    >
                      {fila.tier_label}
                    </span>
                    {fila.momentum === "CAE" && (
                      <span className="down" style={{ marginLeft: 4 }}>
                        ▼ {formatMoney(Math.abs(fila.price_increment))}/día
                      </span>
                    )}
                    {fila.momentum === "SUBE" && (
                      <span className="up" style={{ marginLeft: 4 }}>
                        ▲ {formatMoney(fila.price_increment)}/día
                      </span>
                    )}
                  </td>
                  <td className="n">
                    {fila.euros_per_point != null ? (
                      formatMoney(fila.euros_per_point)
                    ) : (
                      <span className="dim">sin puntos</span>
                    )}
                  </td>
                  <td className="n">{formatMoney(fila.price)}</td>
                  <td className="n">
                    {fila.cash_kind === "OFERTA_VIVA" ? (
                      <span className="pill ok">
                        {formatMoney(fila.cash_now)} ya
                      </span>
                    ) : (
                      <span className="dim">a mercado</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* LO QUE SE APARTA, CON SU MOTIVO.
          Un tope que recorta en silencio es el problema que este
          repo lleva una semana arreglando. */}
      {(orden.excluded || []).length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div className="sub">NO SE PROPONEN</div>
          {orden.excluded.map((e) => (
            <div className="kv" key={e.id}>
              <span>{e.name}</span>
              <b className="dim" style={{ fontWeight: 400 }}>
                {e.reason}
              </b>
            </div>
          ))}
        </div>
      )}

      {(orden.blocked || []).length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div className="sub">APARTADOS POR EL SUELO DE SU POSICIÓN</div>
          {orden.blocked.map((b) => (
            <div className="kv" key={b.id}>
              <span>{b.name}</span>
              <b className="dim" style={{ fontWeight: 400 }}>
                {b.blocked_reason}
              </b>
            </div>
          ))}
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        Pepe <b>no</b> ejecuta esta cola. Se calcula y se enseña para que
        puedas leerla antes de que haga falta. Se puede parar en
        cualquier punto: vender a los primeros, para cualquier número,
        deja todas las posiciones por encima de su suelo.
      </p>
    </section>
  );
}
