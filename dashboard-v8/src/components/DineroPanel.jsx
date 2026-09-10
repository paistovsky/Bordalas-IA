import { formatMoney } from "../lib/utils";

/* CUANTO DINERO HAY Y CUANTO DEBO DE VERDAD (10/09/2026)
 *
 * Tres numeros por separado, nunca refundidos en uno:
 *
 *     saldo                 lo que hay en la cuenta
 *     pujas comprometidas   lo que sale SI se gana
 *     saldo efectivo        el peor caso
 *
 * POR QUE POR SEPARADO. El 10/09 el dueno pujo 12,2 M a mano y
 * la pantalla siguio diciendo "Saldo positivo (3.315.383). El
 * plazo no aprieta" durante horas: leia `balance`, y una puja
 * viva no mueve el balance -baja `maximumBid`-.
 *
 * Un solo numero "neto" habria tapado el problema igual. Son
 * tres porque son tres cosas.
 *
 * Y DOS RELOJES, TAMBIEN POR SEPARADO
 *
 *     el minuto en que arranca la jornada   <- la regla de Biwenger
 *     T-6h                                  <- nuestra prudencia
 *
 * Confundirlos tiene los dos errores dentro: vender con seis
 * horas de margen creyendo que es obligatorio, y llegar al
 * minuto cero creyendo que quedaban seis.
 */

function horas(valor) {
  const n = Number(valor);
  if (!Number.isFinite(n)) return "—";
  if (n <= 0) return "AHORA";
  if (n < 1) return `${Math.round(n * 60)} min`;
  return `${n.toFixed(1)} h`;
}

export default function DineroPanel({ data }) {
  const reloj = data.solvencyClock || {};
  const pujas = data.pujasDelDueno || {};
  const summary = data.summary || {};

  const comprometido = Number(
    reloj.committed_bids ?? pujas.committed ?? 0
  );

  const saldo = Number(reloj.balance ?? summary.balance ?? 0);

  const efectivo = Number(reloj.effective_balance ?? saldo);

  const alPlazo = reloj.hours_to_solvency_deadline;

  const alaJornada = reloj.hours_to_deadline;

  // SI NO HAY DATO, SE DICE. El dinero es lo ultimo que puede
  // desaparecer en silencio: sin este panel el dueno no sabe si
  // esta en verde o si el reloj ha dejado de calcularse.
  if (!reloj.available && !pujas.available && !summary.balance) {
    return (
      <section className="pan">
        <h2>EL DINERO, DE VERDAD</h2>
        <div className="empty">
          Sin datos de solvencia en esta vuelta.{" "}
          {reloj.reason || pujas.reason || ""}
        </div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL DINERO, DE VERDAD</h2>
          <div className="sub">
            {reloj.state_label || "—"}
            {pujas.source ? ` · vía ${pujas.source}` : ""}
          </div>
        </div>
        <span className={efectivo < 0 ? "pill crit" : "pill ok"}>
          {efectivo < 0 ? "DEBE" : "EN VERDE"}
        </span>
      </div>

      <div className="dinero">
        <div className="dinero-cel">
          <small>SALDO</small>
          <b className={saldo < 0 ? "bad" : ""}>{formatMoney(saldo)}</b>
        </div>

        <div className="dinero-cel">
          <small>PUJAS COMPROMETIDAS</small>
          <b className={comprometido ? "warn" : ""}>
            {comprometido ? `− ${formatMoney(comprometido)}` : "ninguna"}
          </b>
        </div>

        <div className="dinero-cel dinero-total">
          <small>SALDO EFECTIVO · PEOR CASO</small>
          <b className={efectivo < 0 ? "bad" : ""}>{formatMoney(efectivo)}</b>
        </div>
      </div>

      <div className="dinero-relojes">
        <div>
          <small>ARRANCA LA JORNADA</small>
          <b className={Number(alaJornada) < 6 ? "bad" : ""}>
            {horas(alaJornada)}
          </b>
          <span className="sub">la línea de Biwenger</span>
        </div>
        <div>
          <small>T−6 H</small>
          <b className={Number(alPlazo) <= 0 ? "bad" : ""}>{horas(alPlazo)}</b>
          <span className="sub">nuestra prudencia, no su norma</span>
        </div>
      </div>

      {/* EL PLAN DE LOS DOS MUNDOS. Solo aparece cuando hay algo
          comprometido: el resto del dia no hay dos mundos que
          planificar. */}
      {reloj.two_world_plan?.available && (
        <div
          className={
            reloj.two_world_plan.if_won?.covered
              ? "alert ok"
              : "alert crit"
          }
          style={{ marginBottom: 0 }}
        >
          {reloj.two_world_plan.reason}
        </div>
      )}
    </section>
  );
}
