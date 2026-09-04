import { formatEuros, formatMoney } from "../lib/utils";

/**
 * SI PUDIERA LLENAR UN HUECO (05/09/2026)
 *
 *   Pepe compara cada candidato con UN jugador: el peor titular
 *   de su posicion. No existe "fichar y punto". Tiene 14 fichas y
 *   el mayor de la liga tiene 17.
 *
 *   Esta lista dice a quien ficharia si esa via existiera,
 *   ordenados por lo que dan de aqui a final de temporada. No
 *   ficha a nadie: es una lista al margen.
 *
 * LAS FICHAS LIBRES SON UNA COTA INFERIOR
 *
 *   El tope de plantilla de Biwenger no esta en el codigo ni
 *   comprobado. Se cuenta contra la plantilla mas grande que se
 *   ve en la liga, asi que si Biwenger permite mas, hay mas sitio
 *   del que dice esto. Nunca menos. Y se escribe, en vez de
 *   enseñar un numero redondo que parece exacto.
 */

const BLOQUEO = {
  NO_MEJORA: "no mejora el XI",
  NO_MEJORA_JERARQUIA: "no mejora la jerarquía",
  NO_MEJORA_TITULARIDAD: "no mejora la titularidad",
  PIERDE_TITULARIDAD: "jugaría menos que el que sale",
  SIN_PRONOSTICO: "sin pronóstico de titular",
  INTENT_POR_EUROS: "gana la reventa en el reparto por euros"
};

export default function RosterExpansionPanel({ data }) {
  const via = data.rosterExpansion || { available: false };
  const huecos = via.slots || {};

  if (!via.available) {
    return (
      <section className="pan">
        <h2>SI HUBIERA HUECO</h2>
        <div className="empty">
          {via.reason || "Sin candidatos para ampliar plantilla."}
        </div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>SI HUBIERA HUECO</h2>
          <div className="sub">
            A quién ficharía Pepe para llenar plantilla, si esa vía
            existiera
          </div>
        </div>
        <span className={huecos.free_slots ? "pill warn" : "pill idle"}>
          {huecos.free_slots != null
            ? `${huecos.free_slots} FICHA${huecos.free_slots === 1 ? "" : "S"} LIBRE${huecos.free_slots === 1 ? "" : "S"}`
            : "SIN CONTAR"}
        </span>
      </div>

      {huecos.known ? (
        <div className="kv">
          <span>Plantilla</span>
          <b className="mono">
            {huecos.our_roster_size} · la mayor de la liga tiene{" "}
            {huecos.largest_roster_in_league}
          </b>
        </div>
      ) : (
        <div className="alert warn">{huecos.reason}</div>
      )}

      <table style={{ marginTop: 8 }}>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th className="n">PRECIO</th>
            <th className="n">A TEMPORADA</th>
            <th className="n">€/PUNTO</th>
            <th>HOY NO ENTRA PORQUE</th>
          </tr>
        </thead>
        <tbody>
          {(via.candidates || []).map((candidato) => (
            <tr key={candidato.id || candidato.name}>
              <td>
                {candidato.name}
                {candidato.caveat && (
                  <span
                    className="pill warn"
                    style={{ marginLeft: 6 }}
                    title={candidato.caveat}
                  >
                    {candidato.starter_known === false
                      ? "SIN DATO"
                      : "SUPLENTE"}
                  </span>
                )}
              </td>
              <td className="n">{formatMoney(candidato.market_price)}</td>
              <td className="n strong">
                {formatMoney(candidato.season_value)}
              </td>
              <td className={candidato.beats_market_rate ? "n up" : "n dim"}>
                {candidato.cost_per_point != null
                  ? formatEuros(candidato.cost_per_point)
                  : "—"}
              </td>
              <td className="dim" title={candidato.blocked_reason}>
                {BLOQUEO[candidato.blocked_by] ||
                  String(candidato.blocked_by || "—")
                    .replaceAll("_", " ")
                    .toLowerCase()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="kv" style={{ marginTop: 8 }}>
        <span>Costarían</span>
        <b className="mono">{formatEuros(via.total_cost)}</b>
      </div>
      <div className="kv">
        <span>Sumarían de aquí a final</span>
        <b className="mono up">{via.total_season_points} puntos</b>
      </div>
      {via.acquisition_budget != null && (
        <div className="kv">
          <span>Presupuesto de fichar hoy</span>
          <b className={via.affordable_today ? "mono up" : "mono down"}>
            {formatEuros(via.acquisition_budget)}
          </b>
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        Pepe <b>no</b> puede hacer esto hoy: no existe la operación
        «fichar para llenar un hueco», y esta lista no la crea. De{" "}
        {via.vetoed_total} candidatos que hoy no entran por la vía del
        XI, estos son los que más darían.
      </p>
    </section>
  );
}
