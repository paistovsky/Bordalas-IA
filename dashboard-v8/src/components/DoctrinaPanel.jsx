import { formatMoney } from "../lib/utils";

/**
 * LA DOCTRINA (20/09/2026)
 *
 *   Dieciocho reglas en docs/DOCTRINA.md: los consejos básicos de
 *   Biwenger, un vídeo de trucos transcrito entero y la forma
 *   medida de jugar de Pollo. "Eso es lo que quiero que haga
 *   Pepe."
 *
 * LO QUE ESTE PANEL ENSEÑA DE VERDAD
 *
 *   No la lista de decisiones que citan una regla. La OTRA: las
 *   que Pepe toma por un motivo que nadie ha escrito nunca. Ésas
 *   son las que hay que descubrir, y por eso van en rojo y
 *   primero.
 *
 *   Y el embudo: de veinte objetivos, dónde muere cada uno. La
 *   regla 9 dice que la vía de comprar lo que sube "está
 *   construida y casi nunca dispara"; esto contesta por qué.
 *
 * NO DECIDE NADA
 */

const POSICION = { 1: "PT", 2: "DF", 3: "MC", 4: "DL" };

const coma = (n, d = 1) =>
  n == null ? "—" : String(Number(n).toFixed(d)).replace(".", ",");

export default function DoctrinaPanel({ data }) {
  const doctrina = data.doctrina || { available: false };

  if (!doctrina.available) {
    return (
      <section className="pan">
        <h2>LA DOCTRINA</h2>
        <div className="empty">
          {doctrina.reason || "Sin lectura de la doctrina."}
        </div>
      </section>
    );
  }

  const citas = doctrina.citations || { available: false };
  const embudo = doctrina.funnel || { available: false };
  const asc = doctrina.promoted || { available: false };
  const enVenta = doctrina.promoted_on_sale || { available: false };
  const grande = doctrina.big_asset || { available: false };

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA DOCTRINA</h2>
          <div className="sub">
            {citas.available
              ? `${citas.rules} reglas · versión ${citas.version}`
              : "docs/DOCTRINA.md"}
          </div>
        </div>
        <span className="pill idle">NO DECIDE</span>
      </div>

      {/* ============================================================
          REGLA 17 — LAS QUE NO CITAN NINGUNA REGLA
          ============================================================ */}
      {citas.available && (
        <>
          <div className="kv">
            <span>Decisiones que citan una regla</span>
            <b className="mono">
              {citas.cited} de {citas.decisions} ({coma(citas.cited_percent)} %)
            </b>
          </div>

          {(citas.without_rule || []).length > 0 && (
            <>
              <div className="sub" style={{ marginTop: 8 }}>
                LAS QUE NO CITAN NINGUNA — DECISIONES QUE NADIE HA ESCRITO
              </div>
              <table>
                <thead>
                  <tr>
                    <th>DECISIÓN</th>
                    <th className="n">VECES</th>
                    <th>DÓNDE</th>
                    <th>POR QUÉ NO ENCAJA</th>
                  </tr>
                </thead>
                <tbody>
                  {citas.without_rule.map((h) => (
                    <tr key={h.decision}>
                      <td className="down">{h.decision}</td>
                      <td className="n">{h.count}</td>
                      <td className="dim">{(h.where || []).join(", ")}</td>
                      <td className="dim">{h.why}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          <div className="sub" style={{ marginTop: 8 }}>
            LAS QUE SÍ
          </div>
          <table>
            <thead>
              <tr>
                <th className="n">REGLA</th>
                <th>TÍTULO</th>
                <th className="n">VECES</th>
                <th>ESTADO</th>
              </tr>
            </thead>
            <tbody>
              {(citas.by_rule || []).map((f) => (
                <tr key={f.rule}>
                  <td className="n">{f.rule}</td>
                  <td>{f.title}</td>
                  <td className="n">{f.count}</td>
                  <td className="dim">{f.state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* ============================================================
          EL EMBUDO — DÓNDE MUERE CADA OBJETIVO
          ============================================================ */}
      {embudo.available && (
        <>
          <div className="sub" style={{ marginTop: 12 }}>
            EL EMBUDO DEL MERCADO
          </div>

          <div className={embudo.alive ? "alert" : "alert warn"}>
            {embudo.reason}
          </div>

          <table>
            <thead>
              <tr>
                <th>CAUSA DE MUERTE</th>
                <th className="n">N</th>
                <th className="n">%</th>
                <th>QUÉ ES</th>
              </tr>
            </thead>
            <tbody>
              {(embudo.deaths || [])
                .filter((m) => m.count > 0)
                .map((m) => (
                  <tr key={m.cause}>
                    <td className={m.cause === "VIVE" ? "up" : "down"}>
                      {m.cause}
                    </td>
                    <td className="n">{m.count}</td>
                    <td className="n">{coma(m.percent)} %</td>
                    <td className="dim">{m.what}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </>
      )}

      {/* ============================================================
          REGLA 8 — RECIÉN ASCENDIDOS
          ============================================================ */}
      {asc.available && (
        <>
          <div className="kv" style={{ marginTop: 12 }}>
            <span>Recién ascendidos</span>
            <b className="mono">{(asc.teams || []).join(" · ")}</b>
          </div>
          <p className="note" style={{ textAlign: "left" }}>
            {asc.reason} <b>Método:</b> {asc.method}
          </p>

          {enVenta.available && enVenta.count > 0 && (
            <table>
              <thead>
                <tr>
                  <th>EN EL MERCADO HOY</th>
                  <th className="n">POS</th>
                  <th className="n">PRECIO</th>
                  <th className="n">TITULARIDAD</th>
                  <th className="n">RITMO</th>
                  <th>DECISIÓN</th>
                </tr>
              </thead>
              <tbody>
                {enVenta.rows.map((f) => (
                  <tr key={f.id}>
                    <td>
                      {f.name}
                      {f.cheap && (
                        <span className="pill ok" style={{ marginLeft: 6 }}>
                          BARATO
                        </span>
                      )}
                    </td>
                    <td className="n dim">{POSICION[f.position] || "?"}</td>
                    <td className="n">{formatMoney(f.price)}</td>
                    <td className="n">
                      {f.starter_probability == null
                        ? "—"
                        : `${f.starter_probability} %`}
                    </td>
                    <td
                      className={`n ${
                        (f.rate_percent_per_day || 0) > 0 ? "up" : "down"
                      }`}
                    >
                      {coma(f.rate_percent_per_day, 2)} %
                    </td>
                    <td className="dim">{f.decision}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {/* ============================================================
          REGLA 15 — EL ACTIVO QUE PESA DEMASIADO
          ============================================================ */}
      {grande.available && (
        <>
          <div className="sub" style={{ marginTop: 12 }}>
            {String(grande.player).toUpperCase()} — LAS DOS COLUMNAS
          </div>

          <div className={grande.over_limit ? "alert warn" : "alert"}>
            {grande.reason}
          </div>

          <table>
            <thead>
              <tr>
                <th>TENERLO</th>
                <th className="n"></th>
                <th>VENDERLO</th>
                <th className="n"></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Puntos por jornada, medidos</td>
                <td className="n">
                  <b>{coma(grande.keep.points_per_matchday, 2)}</b>
                </td>
                <td>Libera</td>
                <td className="n">{formatMoney(grande.sell.frees)}</td>
              </tr>
              <tr>
                <td>% de los puntos / % del dinero</td>
                <td className="n">
                  {coma(grande.keep.points_share)} % /{" "}
                  {coma(grande.keep.value_share, 2)} %
                </td>
                <td>Entran al once</td>
                <td className="n">{grande.sell.would_enter_xi}</td>
              </tr>
              <tr>
                <td>€ por punto/jornada (él / el resto)</td>
                <td className="n">
                  {formatMoney(grande.keep.euros_per_point)} /{" "}
                  {formatMoney(grande.keep.rest_euros_per_point)}
                </td>
                <td>Puntos netos por jornada</td>
                <td
                  className={`n ${
                    grande.sell.net_points_per_matchday > 0 ? "up" : "down"
                  }`}
                >
                  <b>{coma(grande.sell.net_points_per_matchday, 2)}</b>
                </td>
              </tr>
              <tr>
                <td>Sube al día</td>
                <td className="n">{coma(grande.keep.daily_percent, 3)} %</td>
                <td>Concentración después</td>
                <td className="n">{coma(grande.sell.new_max_share, 2)} %</td>
              </tr>
            </tbody>
          </table>

          <p className="note" style={{ textAlign: "left" }}>
            <b>{grande.keep.warning}</b> {grande.sell.warning}{" "}
            <b>Sin recomendación: decide el dueño.</b>
          </p>
        </>
      )}
    </section>
  );
}
