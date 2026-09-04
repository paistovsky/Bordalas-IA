import { formatEuros, formatMoney } from "../lib/utils";

/**
 * LA SEGUNDA OPINION (05/09/2026)
 *
 *   Pepe valora a tres dias: lo que valga la reventa el jueves.
 *   Es el horizonte correcto para especular y el equivocado para
 *   fichar.
 *
 *   Aqui esta la otra cuenta, al lado: lo que da un jugador de
 *   aqui a la jornada 38. No sustituye a nada —el motor sigue
 *   decidiendo con la vieja— pero deja ver dónde discrepan.
 *
 * LOS PEROS VAN EN LA MISMA FILA
 *
 *   Un valor de temporada se apoya entero en los puntos
 *   esperados, y esos tienen dos agujeros conocidos: un jugador
 *   sin pronostico no lleva descuento, y el pronostico semanal
 *   pesa solo 0,15, asi que un suplente conserva casi todos sus
 *   puntos.
 *
 *   Sin esa marca, los tres candidatos mas "baratos por punto"
 *   parecerian chollos. Son los tres suplentes.
 */

function Ratio({ valor }) {
  if (valor == null) return <span className="dim">—</span>;

  const n = Number(valor);
  const tono = n >= 1.2 ? "up" : n <= 0.8 ? "down" : "";

  return (
    <span className={tono}>×{String(n.toFixed(2)).replace(".", ",")}</span>
  );
}

export default function SeasonHorizonPanel({ data }) {
  const sombra = data.seasonHorizon || { available: false };

  if (!sombra.available) {
    return (
      <section className="pan">
        <h2>A HORIZONTE DE TEMPORADA</h2>
        <div className="empty">
          {sombra.reason || "Sin valoración a temporada disponible."}
        </div>
      </section>
    );
  }

  const filas = sombra.biggest_gaps || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>A HORIZONTE DE TEMPORADA</h2>
          <div className="sub">
            Lo que Pepe valora hoy, contra lo que dan de aquí a la
            jornada 38
          </div>
        </div>
        <span className="pill idle">
          {sombra.matchdays_remaining ?? "?"} JORNADAS
        </span>
      </div>

      <table>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th className="n">PRECIO</th>
            <th className="n">PUNTOS</th>
            <th className="n">PEPE HOY</th>
            <th className="n">A TEMPORADA</th>
            <th className="n">×</th>
            <th className="n">€/PUNTO</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.id || fila.name}>
              <td>
                {fila.name}
                {/* El pero, donde se lee la fila y no en una
                    leyenda al final. */}
                {fila.caveat && (
                  <span
                    className="pill warn"
                    style={{ marginLeft: 6 }}
                    title={fila.caveat}
                  >
                    {fila.starter_known === false ? "SIN DATO" : "SUPLENTE"}
                  </span>
                )}
              </td>
              <td className="n">{formatMoney(fila.market_price)}</td>
              <td className="n dim">{fila.expected_points ?? "—"}</td>
              <td className="n">{formatMoney(fila.current_value)}</td>
              <td className="n strong">{formatMoney(fila.season_value)}</td>
              <td className="n">
                <Ratio
                  valor={
                    fila.current_value
                      ? fila.season_value / fila.current_value
                      : null
                  }
                />
              </td>
              <td
                className={
                  fila.beats_market_rate ? "n up" : "n dim"
                }
                title={
                  sombra.euros_per_point
                    ? `El mercado paga ${formatEuros(sombra.euros_per_point)} por punto.`
                    : undefined
                }
              >
                {fila.cost_per_point != null
                  ? formatEuros(fila.cost_per_point)
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left" }}>
        Segunda opinión escrita al margen: el motor decide{" "}
        <b>solo</b> con la columna «PEPE HOY». El precio del punto es
        el medido en esta liga
        {sombra.euros_per_point
          ? `, ${formatEuros(sombra.euros_per_point)}`
          : ""}
        .
      </p>
    </section>
  );
}
