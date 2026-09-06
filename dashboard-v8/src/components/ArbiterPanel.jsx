import { formatMoney } from "../lib/utils";

/**
 * EL ÁRBITRO (16/09/2026)
 *
 *   Cuatro noches concluyendo que no hay que comprar nada,
 *   mientras Pollo compraba siete jugadores por 21,2 M y iba
 *   primero. Este panel contesta con números en vez de con
 *   intuición.
 *
 * LOS DÍAS MANDAN SOBRE EL PORCENTAJE
 *
 *   Una compra de hace cinco horas no dice nada de la tesis:
 *   dice la prima que se pagó. Por eso los días van al lado de
 *   cada operación y no escondidos.
 *
 * Y SE MIRAN LAS VENTAS
 *
 *   Mirar solo las compras hace parecer a Pollo un acumulador.
 *   Vendió 21,26 M el mismo día que compró 21,20 M: rota, no
 *   despliega caja parada.
 *
 * NO DECIDE NADA
 */
export default function ArbiterPanel({ data }) {
  const a = data.arbiter || { available: false };

  if (!a.available) {
    return (
      <section className="pan">
        <h2>QUIÉN TENÍA RAZÓN</h2>
        <div className="empty">{a.reason || "Sin marcador."}</div>
      </section>
    );
  }

  const h = a.history || {};
  const rb = a.rule_backtest || {};
  const rj = a.rejections || {};
  const vp = a.value_versus_points || {};

  const pct = (v) =>
    v == null ? "—" : `${String(v.toFixed(2)).replace(".", ",")} %`;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>QUIÉN TENÍA RAZÓN</h2>
          <div className="sub">
            El marcador de los rivales y el libro de nuestros rechazos
          </div>
        </div>
        <span className="pill idle">NO DECIDE</span>
      </div>

      {/* LOS DÍAS DE HISTÓRICO, LA LÍNEA QUE FALTABA.
          Toda la discusión de "el almacén son seis días" salió de
          mirar una copia local caducada. */}
      <div className="kv">
        <span>Histórico de precios</span>
        <b className="mono">
          {h.available
            ? `${h.days} días desde ${h.oldest} · ${h.players} jugadores · retención ${h.retention_days} d`
            : h.reason || "sin almacén"}
        </b>
      </div>

      {h.available && (
        <div className="kv">
          <span>Horizontes que se pueden medir</span>
          <b className="mono">
            {(h.measurable_horizons || []).join(", ") || "ninguno"} días
          </b>
        </div>
      )}

      {/* NUESTRA PROPIA REGLA, PUESTA A PRUEBA */}
      {rb.available && rb.accepted?.enough && rb.rejected?.enough && (
        <>
          <div className="sub" style={{ marginTop: 10 }}>
            NUESTRA REGLA, SOBRE {rb.operations} OPERACIONES
          </div>
          <table>
            <thead>
              <tr>
                <th>GRUPO</th>
                <th className="n">N</th>
                <th className="n">MEDIANA</th>
                <th className="n">P25</th>
                <th className="n">EN PÉRDIDA</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Los que Pepe COMPRA</td>
                <td className="n">{rb.accepted.n}</td>
                <td className="n up">{pct(rb.accepted.median * 100)}</td>
                <td className="n">{pct(rb.accepted.p25 * 100)}</td>
                <td className="n">{pct(rb.accepted.loss_rate * 100)}</td>
              </tr>
              <tr>
                <td>Los que Pepe RECHAZA</td>
                <td className="n">{rb.rejected.n}</td>
                <td className="n">{pct(rb.rejected.median * 100)}</td>
                <td className="n down">{pct(rb.rejected.p25 * 100)}</td>
                <td className="n down">
                  {pct(rb.rejected.loss_rate * 100)}
                </td>
              </tr>
            </tbody>
          </table>
        </>
      )}

      {/* EL MARCADOR DE CADA RIVAL */}
      {Object.entries(a.managers || {}).map(([nombre, m]) =>
        !m.available ? null : (
          <div key={nombre} style={{ marginTop: 10 }}>
            <div className="sub">
              {nombre.toUpperCase()} · compró {formatMoney(m.bought_total)}{" "}
              · vendió {formatMoney(m.sold_total)}
            </div>

            <table>
              <thead>
                <tr>
                  <th>JUGADOR</th>
                  <th className="n">PAGÓ</th>
                  <th className="n">VALE HOY</th>
                  <th className="n">GANA</th>
                  <th className="n">DÍAS</th>
                </tr>
              </thead>
              <tbody>
                {(m.buys || []).map((c) => (
                  <tr key={c.player}>
                    <td>{c.player}</td>
                    <td className="n">{formatMoney(c.amount)}</td>
                    <td className="n">
                      {c.price_today != null
                        ? formatMoney(c.price_today)
                        : "—"}
                    </td>
                    <td className={`n ${c.pnl > 0 ? "up" : "down"}`}>
                      {c.pnl != null
                        ? `${c.pnl > 0 ? "+" : "−"}${formatMoney(
                            Math.abs(c.pnl)
                          )} · ${pct(c.pnl_percent)}`
                        : "sin precio hoy"}
                    </td>
                    {/* LOS DÍAS, AL LADO. Sin ellos el porcentaje miente. */}
                    <td className="n dim">{c.days}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="kv">
              <span>Total, tras {m.median_days} días de mediana</span>
              <b className={m.pnl > 0 ? "mono up" : "mono down"}>
                {m.pnl > 0 ? "+" : "−"}
                {formatMoney(Math.abs(m.pnl))} · {pct(m.pnl_percent)} ·{" "}
                {m.rising_today} de {m.buys_measurable} subiendo hoy
              </b>
            </div>
          </div>
        )
      )}

      {/* EL LIBRO DE RECHAZOS */}
      <div className="kv" style={{ marginTop: 10 }}>
        <span>Libro de rechazos</span>
        <b className="mono">
          {rj.closed
            ? `${rj.closed} cerrados de ${rj.recorded} · mediana ${pct(
                rj.median_return_percent
              )} · comprándolos todos ${
                rj.would_have_gained > 0 ? "+" : "−"
              }${formatMoney(Math.abs(rj.would_have_gained || 0))}`
            : rj.reason || "sin apuntar"}
        </b>
      </div>

      {/* LA CORRELACIÓN, CON SU LÍMITE */}
      {vp.available && (
        <p className="note" style={{ textAlign: "left" }}>
          <b>¿Tener más plantilla da más puntos?</b> {vp.reason}
        </p>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        {a.caveat} Y la regla de arriba se calibró sobre estos mismos
        datos, así que mide coherencia interna, no acierto fuera de
        muestra: para eso está el libro de rechazos, que empieza hoy.
      </p>
    </section>
  );
}
