import { formatMoney } from "../lib/utils";

/* PUJAS EN VIVO (13/09/2026)
 *
 * LO QUE ESTA PASANDO AHORA, ANTES DE LO QUE VA A PASAR.
 *
 *   Las pujas vivas salian como un PASO dentro de la cronología
 *   -"se resuelven N puja(s) viva(s)"-, mezcladas con lo que el
 *   bot hará mañana. Lo primero que se lee tiene que ser lo que
 *   está en juego ahora mismo.
 *
 * DE DONDE SALE
 *
 *   De `acquisition.targets`, filas con `has_live_bid`. Es
 *   dinero YA comprometido en Biwenger, no lo que el motor
 *   pujaría: son dos números distintos y la pantalla los mezcló
 *   una vez.
 *
 * Y SI NO HAY NINGUNA, SE DICE
 *
 *   "Ninguna puja viva" no es un hueco en blanco. Un panel vacío
 *   se lee como "va bien"; aquí significa que no hay nada
 *   comprometido, que es un hecho y no una ausencia de datos.
 */

export default function PujasVivasPanel({ data }) {
  const acquisition = data.acquisition || {};

  const vivas = (acquisition.targets || []).filter(
    (target) => Number(target.live_bid || 0) > 0
  );

  const total = vivas.reduce(
    (suma, target) => suma + Number(target.live_bid || 0),
    0
  );

  const reloj = data.marketClock || {};

  const horas = Number(reloj.hours_to_reset || 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>PUJAS EN VIVO</h2>
          <div className="sub">
            dinero ya comprometido en Biwenger · se resuelve en
            el reset
          </div>
        </div>
        <span className={vivas.length ? "pill ok" : "pill idle"}>
          {vivas.length
            ? `${vivas.length} · ${formatMoney(total)}`
            : "NINGUNA"}
        </span>
      </div>

      {!vivas.length ? (
        <div className="sub">
          No hay ninguna puja puesta ahora mismo. No es que falte
          el dato: es que no hay dinero comprometido.
        </div>
      ) : (
        <>
          <div className="scroll-x">
            <table className="tbl">
              <thead>
                <tr>
                  <th>JUGADOR</th>
                  <th className="n">PUJAMOS</th>
                  <th className="n">PRECIO</th>
                  <th>A QUIÉN</th>
                </tr>
              </thead>
              <tbody>
                {vivas.map((target) => (
                  <tr key={target.id || target.name}>
                    <td>{target.name}</td>
                    <td className="n">
                      <b>{formatMoney(target.live_bid)}</b>
                    </td>
                    <td className="n sub">
                      {formatMoney(target.market_price)}
                    </td>
                    <td className="sub">
                      {target.seller_name || "Computer"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="note" style={{ textAlign: "left" }}>
            {reloj.available
              ? `Se resuelven en el reset, dentro de ${Math.floor(
                  horas
                )} h ${Math.round((horas % 1) * 60)} min.`
              : "Se resuelven en el próximo reset."}{" "}
            Hasta entonces el dinero está apartado y no se puede
            gastar en otra cosa.
          </p>
        </>
      )}
    </section>
  );
}
