import { formatMoney } from "../lib/utils";

/**
 * El plan de franquicia.
 *
 * POR QUE ESTE PANEL EXISTE
 *
 *     `franchise` llevaba desde el principio en status.json y no
 *     lo leia ni un componente. La consola del ciclo si lo
 *     imprime -"Franchise state: ABORT, target: Mbappe"-, asi
 *     que Pepe tenia un plan que el dashboard no contaba.
 *
 *     Es de las cosas mas caras que puede hacer: 25,44 M en un
 *     solo jugador. No puede vivir solo en un log.
 *
 * QUE SIGNIFICA CADA ESTADO
 *
 *     ABORT     lo quiere y hoy no puede. Casi siempre por caja.
 *     HOLD      esperando mejor momento o mejor precio.
 *     PURSUE    va a por el.
 *     DONE      ya es nuestro.
 */

const STATE = {
  PURSUE: ["pill ok", "VA A POR ÉL"],
  HOLD: ["pill warn", "ESPERANDO"],
  ABORT: ["pill crit", "DESCARTADO HOY"],
  DONE: ["pill ok", "CONSEGUIDO"]
};

const EXPLAIN = {
  PURSUE: "Está en la cola: si le llega el turno y la caja aguanta, puja.",
  HOLD: "Lo quiere, pero hoy no es el momento. Sigue vigilándolo.",
  ABORT:
    "Lo quiere y no puede permitírselo ahora mismo. No se hace nada con él " +
    "hasta que cambie la caja o baje el precio.",
  DONE: "Ya está en la plantilla."
};

export default function FranchisePanel({ franchise = {}, exposure = {} }) {
  if (!franchise.target) {
    return (
      <section className="pan">
        <h2>FICHAJE FRANQUICIA</h2>
        <div className="empty">
          Pepe no tiene ningún objetivo de franquicia en este ciclo.
        </div>
      </section>
    );
  }

  const estado = String(franchise.state || "").toUpperCase();
  const [tone, label] = STATE[estado] || ["pill idle", estado || "—"];

  const precio = Number(franchise.price || 0);
  const puedeGastar = Number(exposure.available_budget || 0);
  const falta = precio - puedeGastar;
  const incremento = Number(franchise.price_increment || 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>FICHAJE FRANQUICIA</h2>
          <div className="sub">El jugador que cambiaría la temporada</div>
        </div>
        <span className={tone}>{label}</span>
      </div>

      <div className="kv">
        <span>Objetivo</span>
        <b>{franchise.target}</b>
      </div>

      <div className="kv">
        <span>Precio</span>
        <b className="mono">
          {formatMoney(precio)}{" "}
          <small className={incremento > 0 ? "up" : incremento < 0 ? "down" : "dim"}>
            {incremento > 0 ? "▲" : incremento < 0 ? "▼" : "—"}
            {incremento ? formatMoney(Math.abs(incremento)) : ""}
          </small>
        </b>
      </div>

      {franchise.score != null && (
        <div className="kv">
          <span>Puntuación de franquicia</span>
          <b className="mono">{franchise.score}/100</b>
        </div>
      )}

      {precio > 0 && puedeGastar > 0 && (
        <div className="kv">
          <span>{falta > 0 ? "Le faltan" : "Le sobran"}</span>
          <b className={falta > 0 ? "mono down" : "mono up"}>
            {formatMoney(Math.abs(falta))}
          </b>
        </div>
      )}

      <p className="note" style={{ textAlign: "left", marginTop: 8 }}>
        {EXPLAIN[estado] || "Estado sin descripción."}
      </p>
    </section>
  );
}
