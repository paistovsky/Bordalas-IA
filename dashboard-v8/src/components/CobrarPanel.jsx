import { formatMoney } from "../lib/utils";

/* ¿QUE PUEDO COBRAR AHORA Y POR CUANTO? (10/09/2026)
 *
 * Y la columna que lo cambia todo: CUALES DE ESOS SON TITULARES.
 *
 * POR QUE ESA COLUMNA
 *
 *   Es la diferencia entre tapar un agujero gratis y taparlo con
 *   puntos. El 10/09 habia 29 M en ofertas vivas y solo 2,1 M
 *   eran de gente que no juega: el numero grande decia que
 *   sobraba dinero y el numero que importaba decia lo contrario.
 *
 *   Un titular no es liquidez mientras no decidas que lo es.
 *
 * NO CALCULA NADA: lee las ofertas ya publicadas y les pone al
 * lado si el jugador esta en el once.
 */

export default function CobrarPanel({ data }) {
  const ofertas = data.offers || [];
  const roster = data.roster || {};

  const titulares = new Set(
    (roster.players || [])
      .filter((p) => p.is_starter)
      .map((p) => String(p.name))
  );

  const vivas = ofertas
    .filter((o) => !o.expired && Number(o.amount || 0) > 0)
    .map((o) => {
      const nombre = String(
        o.player_name || (o.players || [])[0] || ""
      );

      return {
        nombre,
        amount: Number(o.amount || 0),
        premium: o.premium_percent,
        hours: o.hours_to_expiry,
        protegido: o.protection === "NEVER_AUTO_SELL",
        titular: titulares.has(nombre),
        action: o.action_label || o.action
      };
    })
    .sort((a, b) => b.amount - a.amount);

  const cobrables = vivas.filter((v) => !v.protegido);

  const delBanquillo = cobrables.filter((v) => !v.titular);

  const suma = (filas) =>
    filas.reduce((total, f) => total + f.amount, 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>QUÉ PUEDO COBRAR AHORA</h2>
          <div className="sub">
            {formatMoney(suma(cobrables))} en total ·{" "}
            <b>{formatMoney(suma(delBanquillo))} sin tocar el once</b>
          </div>
        </div>
        <span className="pill">{cobrables.length} ofertas</span>
      </div>

      <table className="tbl">
        <thead>
          <tr>
            <th>Jugador</th>
            <th className="num">Ofrecen</th>
            <th className="num">Prima</th>
            <th className="num">Caduca</th>
            <th>Cuesta</th>
          </tr>
        </thead>
        <tbody>
          {vivas.map((v) => (
            <tr key={v.nombre} className={v.titular ? "row-warn" : ""}>
              <td>{v.nombre}</td>
              <td className="num">{formatMoney(v.amount)}</td>
              <td className="num sub">
                {v.premium != null ? `${v.premium} %` : "—"}
              </td>
              <td className="num sub">
                {v.hours != null ? `${Number(v.hours).toFixed(0)} h` : "—"}
              </td>
              <td className={v.titular ? "warn" : "sub"}>
                {v.protegido
                  ? "NO SE VENDE"
                  : v.titular
                  ? "TITULAR: cuesta puntos"
                  : "banquillo: gratis"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
