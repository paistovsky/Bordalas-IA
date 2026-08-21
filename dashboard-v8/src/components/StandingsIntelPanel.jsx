import { formatMoney } from "../lib/utils";

/**
 * Clasificacion con inteligencia del rival.
 *
 * Tres numeros por manager y cada uno responde a algo distinto:
 *
 *   CAJA  - el dinero que tiene ahora mismo. Puede ser negativo:
 *           Biwenger deja operar en rojo.
 *   TOPE  - lo maximo que puede pujar hoy = caja + margen de
 *           deuda. El ratio de deuda no es una suposicion: se
 *           calibra contra el maximumBid oficial de Pepe, que
 *           Biwenger si nos da exacto.
 *   PUJA  - cuantas veces puja de verdad, medido sobre el
 *           historial del tablon.
 *
 * Poder pagar y ponerse a pujar son cosas distintas. Confundir
 * las dos fue lo que rompio el primer modelo PvP: con siete
 * rivales solventes, los 53 jugadores del mercado tenian seis
 * competidores y la ruta de puja ajustada no se activaba nunca.
 */

const THREAT = {
  HIGH: "pill crit",
  MEDIUM: "pill warn",
  LOW: "pill idle",
  NONE: "pill idle"
};

export default function StandingsIntelPanel({ data }) {
  const standings = data.competition?.standings || [];
  const rivals = data.acquisition?.rivals || [];
  const managers = data.rivalIntel?.managers || [];
  const calibration = data.rivalIntel?.maximum_bid_calibration || {};

  const byName = new Map(rivals.map((rival) => [rival.name, rival]));
  const intelByName = new Map(managers.map((manager) => [manager.name, manager]));

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>CLASIFICACIÓN E INTELIGENCIA</h2>
          <div className="sub">{data.competition?.name || "Liga"}</div>
        </div>
        {calibration.available && (
          <span className="pill ok">
            DEUDA ×{Number(calibration.ratio || 0).toFixed(2)}
          </span>
        )}
      </div>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>MÁNAGER</th>
            <th className="n">PTS</th>
            <th className="n">CAJA</th>
            <th className="n">PLANTILLA</th>
            <th className="n">PATRIMONIO</th>
            <th className="n">TOPE</th>
            <th className="n">PUJA</th>
            <th className="n">MÁX. VISTO</th>
            <th className="n">AMENAZA</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row) => {
            const rival = byName.get(row.name);
            const intel = intelByName.get(row.name);
            const balance = intel?.balance;
            const cap = intel?.maximum_bid ?? rival?.capacity;
            const percent =
              rival && !rival.never_bids
                ? Math.round(Number(rival.participation || 0) * 100)
                : null;

            return (
              <tr key={row.user_id} className={row.is_current_user ? "me" : ""}>
                <td className="dim">{row.rank}º</td>
                <td>
                  {row.name}
                  {row.is_current_user && (
                    <span className="pill me" style={{ marginLeft: 6 }}>TÚ</span>
                  )}
                </td>
                <td className="n">{row.points}</td>
                {/* LA CAJA YA LLEVA LOS ABONOS DENTRO
                    (21/08/2026)

                    Se pregunto dos veces si estaban sumados, y
                    con razon: una columna de ABONOS en otra
                    tabla hace pensar que van aparte. Van dentro,
                    y ahora la propia celda lo dice. */}
                <td
                  className={Number(balance) < 0 ? "n down" : "n"}
                  title={
                    intel?.matchday_bonus
                      ? `Incluye ${formatMoney(intel.matchday_bonus)} de abonos (${row.points} puntos x 30.000 €).`
                      : "Sin abonos todavía en este libro."
                  }
                >
                  {balance != null ? formatMoney(balance) : "—"}
                </td>

                {/* PLANTILLA y PATRIMONIO viajaban desde hace
                    tiempo en la telemetria y no se pintaban.
                    Sin ellos la tabla decia quien tiene dinero
                    hoy, pero no quien es rico: un manager con la
                    caja a cero y 60 M en jugadores no es pobre,
                    es liquido cuando quiere. */}
                <td className="n dim" title={
                  intel?.roster_count != null
                    ? `${intel.roster_count} jugadores`
                    : undefined
                }>
                  {intel?.roster_value
                    ? formatMoney(intel.roster_value)
                    : "—"}
                </td>

                <td className="n strong">
                  {intel?.net_worth != null
                    ? formatMoney(intel.net_worth)
                    : "—"}
                </td>

                <td className="n">{cap != null ? formatMoney(cap) : "—"}</td>
                <td className="n">
                  {rival?.never_bids ? (
                    <span className="pill idle">NUNCA</span>
                  ) : percent != null ? (
                    <span
                      className={
                        percent >= 40 ? "pill crit" : percent >= 15 ? "pill warn" : "pill idle"
                      }
                    >
                      {percent}%
                    </span>
                  ) : (
                    <span className="dim">—</span>
                  )}
                </td>

                {/* Lo mas alto que se le ha visto pagar de
                    verdad. El tope dice lo que PODRIA; esto dice
                    hasta donde ha llegado. */}
                <td className="n dim" title={
                  intel?.lost_bids != null
                    ? `${intel.lost_bids} puja(s) perdida(s) registradas`
                    : undefined
                }>
                  {intel?.max_observed_bid
                    ? formatMoney(intel.max_observed_bid)
                    : "—"}
                </td>

                <td className="n">
                  {intel?.threat_level ? (
                    <span className={THREAT[intel.threat_level] || "pill idle"}>
                      {intel.threat_level}
                      {intel.threat_score != null
                        ? ` ${Math.round(Number(intel.threat_score))}`
                        : ""}
                    </span>
                  ) : (
                    <span className="dim">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left", marginTop: 9 }}>
        CAJA = dinero ahora (puede ir en rojo), <b>abonos incluidos</b> —30.000 €
        por punto, pasa el ratón para ver cuántos—. PLANTILLA = lo que valen sus
        jugadores (pasa el ratón para ver cuántos tiene). PATRIMONIO = caja +
        plantilla, o sea lo que vale el equipo entero. TOPE = caja + margen de
        deuda, con el ratio calibrado contra el maximumBid oficial de Pepe. PUJA =
        veces que ese mánager puja de verdad, medida sobre el tablón. MÁX.
        VISTO = lo más alto que se le ha visto pagar (pasa el ratón para ver
        sus pujas perdidas). AMENAZA combina las cuatro. Lo que tienen
        publicado en venta <b>no</b> suma al tope: en el reset las pujas se
        resuelven antes de que el Computer haga ofertas.
      </p>
    </section>
  );
}
