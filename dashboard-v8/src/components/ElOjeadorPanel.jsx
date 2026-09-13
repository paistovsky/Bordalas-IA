import { formatEuros } from "../lib/utils";

/* EL OJEADOR (13/09/2026, noche)
 *
 *   Tres fuentes de movimiento de precio, y una cuarta apagada
 *   a propósito.
 *
 * JORNADA PERFECTA SALE IGUAL, CON SU MOTIVO
 *
 *   Está descartada porque no publica variación de valor por
 *   jugador: cero tablas y cero filas en toda la página. Eso no
 *   es un fallo que esconder, es una decisión bien tomada —sacar
 *   una dirección de un titular sería inventarse una señal— y
 *   tiene que verse. Una fuente que desaparece de la lista se
 *   confunde con una que nadie intentó.
 *
 * LA ADVERTENCIA LA ESCRIBE EL PROPIO MÓDULO
 *
 *   «Movimiento observado, no pronóstico». Va arriba y entera:
 *   es lo que separa este cuadro de una bola de cristal.
 *
 * ESTO NO DECIDE NADA por sí solo: alimenta la vía de revender.
 */

const ESCUDO = "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/";

const ACUERDO = {
  UNANIMOUS: ["a-todas", "las 3 fuentes"],
  MAJORITY: ["a-dos", "2 de 3"],
  SINGLE: ["a-una", "una sola"]
};

export default function ElOjeadorPanel({ data }) {
  const scout = data.scout || {};

  const sentidos = data.losSentidos || {};

  /* La edad ya viene calculada en `los_sentidos`. No se vuelve a
     restar aquí: dos cuentas de la misma cosa por caminos
     distintos acaban discrepando. */
  const fila = (sentidos.sentidos || []).find(
    (s) => s.sentido === "Ojeador de precios"
  );

  if (!scout.available) {
    return (
      <section className="pan">
        <h2>EL OJEADOR</h2>
        <div className="empty">
          {scout.reason || "No llegó el ojeador."}
        </div>
      </section>
    );
  }

  const fuentes = Object.entries(scout.sources || {});

  const acuerdos = scout.agreement_counts || {};

  const destacados = [...(scout.highlights || [])].sort(
    (a, b) =>
      Math.abs(b.magnitude_percent || 0) -
      Math.abs(a.magnitude_percent || 0)
  );

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL OJEADOR</h2>
          <p className="sub">
            {scout.sources_ok} de {fuentes.length} fuentes vivas ·{" "}
            {scout.players_count} jugadores ·{" "}
            {acuerdos.UNANIMOUS || 0} por unanimidad ·{" "}
            {acuerdos.MAJORITY || 0} por mayoría ·{" "}
            {acuerdos.SINGLE || 0} de una sola fuente
          </p>
        </div>
      </div>

      {/* LA ADVERTENCIA DEL PROPIO MÓDULO, ENTERA. */}
      <p className="aviso-ambar">
        {scout.caveat}{" "}
        <b>
          Fechado en la jornada {scout.matchday}
          {fila && fila.edad && fila.edad.dias != null
            ? `, ${fila.edad.texto}`
            : ""}
          .
        </b>
      </p>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>FUENTE</th>
              <th className="r">JUGADORES</th>
              <th className="r">REGISTROS</th>
              <th className="r">SIN CASAR</th>
              <th className="ctr">ESTADO</th>
              <th>QUÉ APORTA</th>
            </tr>
          </thead>
          <tbody>
            {fuentes.map(([nombre, f]) => (
              <tr key={nombre} className={f.ok ? "" : "hi"}>
                <td className="q">
                  <span className="nm">{nombre}</span>
                </td>
                <td className="pt">{f.players}</td>
                <td className="pt">{f.records}</td>
                <td className="pt">{f.unmatched}</td>
                <td className="es">
                  <span className={f.ok ? "s-vivo" : "s-muerto"}>
                    {f.ok ? "● VIVA" : "○ APAGADA"}
                  </span>
                </td>
                {/* LA NOTA ENTERA, Y EL MOTIVO SI ESTÁ APAGADA.
                    Una fuente descartada a propósito tiene que
                    poder distinguirse de una rota. */}
                <td className="pw">
                  {f.note}
                  {f.error ? (
                    <>
                      <br />
                      <span className="bloquea">{f.error}</span>
                    </>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="sub2">LO QUE MÁS SE MUEVE</h3>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>QUIÉN</th>
              <th className="n">PRECIO</th>
              <th className="ctr">SUBE/BAJA</th>
              <th className="r">CUÁNTO</th>
              <th>ACUERDO</th>
              <th className="r">RACHA</th>
              <th>PRESIÓN DE COMPRA</th>
            </tr>
          </thead>
          <tbody>
            {destacados.map((h) => {
              const [clase, texto] =
                ACUERDO[h.agreement] || ["a-una", "sin dato"];

              const sube = h.direction === "UP";

              return (
                <tr key={h.player_id}>
                  <td className="q">
                    <span className="nm">{h.player_name}</span>
                  </td>

                  <td className="c">
                    <span className="pr">
                      {formatEuros(h.market_price)}
                    </span>
                  </td>

                  <td className="es">
                    <span className={sube ? "up" : "down"}>
                      {sube ? "▲" : "▼"}
                    </span>
                  </td>

                  <td className="ppm">
                    <b className={sube ? "pos-d" : "neg-d"}>
                      {sube ? "+" : ""}
                      {h.magnitude_percent} %
                    </b>
                  </td>

                  <td className="vd">
                    <span className={clase}>{texto}</span>
                  </td>

                  <td className="ppm">
                    {h.trend_days == null ? (
                      <span className="unk">—</span>
                    ) : (
                      `${h.trend_days} d`
                    )}
                  </td>

                  {/* PRESIÓN DE COMPRA: la única señal del
                      ojeador que mira hacia delante. Sin dato no
                      se pinta una barra vacía, que se leería
                      como «cero presión». */}
                  <td className="ti">
                    {h.demand_pressure == null ? (
                      <span className="unk">sin dato</span>
                    ) : (
                      <div className="titw">
                        <span
                          className={`titn ${
                            h.demand_pressure >= 70
                              ? "t-hi"
                              : h.demand_pressure >= 40
                              ? "t-md"
                              : "t-lo"
                          }`}
                        >
                          {h.demand_pressure}
                        </span>
                        <i className="bar">
                          <b
                            className={
                              h.demand_pressure >= 70
                                ? "t-hi"
                                : h.demand_pressure >= 40
                                ? "t-md"
                                : "t-lo"
                            }
                            style={{
                              width: `${Math.min(
                                100,
                                Math.max(0, h.demand_pressure)
                              )}%`
                            }}
                          />
                        </i>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        <b>Movimiento observado, no pronóstico.</b> Las tres
        fuentes vivas copian el cambio del último mercado y
        ninguna publica confianza.{" "}
        <b>PRESIÓN DE COMPRA</b> es la única señal que mira hacia
        delante, y sólo la trae Comuniate.{" "}
        {scout.unmatched_count
          ? `${scout.unmatched_count} registros no se pudieron casar con ningún jugador del catálogo y se descartaron: salen listados en AUDITORÍA.`
          : null}
      </p>
    </section>
  );
}
