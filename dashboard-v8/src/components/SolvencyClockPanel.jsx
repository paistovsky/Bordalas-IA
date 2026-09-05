import { formatMoney } from "../lib/utils";

/**
 * EL RELOJ DE LA SOLVENCIA (12/09/2026)
 *
 *   "No quiero salir de rojo hoy. Con estar en positivo 6 horas
 *    antes del inicio de jornada es suficiente."
 *
 *   La solvencia deja de ser un estado y pasa a ser un plazo.
 *   Lejos del cierre, un déficit es una posición legítima. Cerca,
 *   es una emergencia.
 *
 * LAS DOS VELOCIDADES
 *
 *   Aceptar una oferta que ya está sobre la mesa es inmediato.
 *   Crear liquidez nueva es lento: hace falta un ciclo entero del
 *   Computer, 24 h medidas, para que valore lo publicado y
 *   ofrezca. Y esperar a que un manager compre una publicación no
 *   es un plan: se vio UNO en 67 h de tablón.
 *
 * EL DESEMPATE
 *
 *   Dentro de las 6 h manda la solvencia por encima del HOLD del
 *   motor de ofertas. Fuera, manda el motor de ofertas — que para
 *   eso mira el precio.
 */

const TONO = {
  SIN_DEUDA: "ok",
  CUBIERTO: "ok",
  CUBIERTO_PERO_CADUCA: "warn",
  PUBLICAR: "warn",
  CRITICO: "crit",
  EN_EL_PLAZO: "crit"
};

function horas(valor) {
  if (valor == null) return "—";
  const h = Math.floor(Math.abs(valor));
  const m = Math.round((Math.abs(valor) - h) * 60);
  return `${valor < 0 ? "−" : ""}${h}h ${String(m).padStart(2, "0")}m`;
}

export default function SolvencyClockPanel({ data }) {
  const reloj = data.solvencyClock || { available: false };

  if (!reloj.available) {
    return (
      <section className="pan">
        <h2>RELOJ DE SOLVENCIA</h2>
        <div className="empty">
          {reloj.reason || "Sin plazo que medir."}
        </div>
      </section>
    );
  }

  const venta = reloj.recommended_sale;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>RELOJ DE SOLVENCIA</h2>
          <div className="sub">
            En positivo {reloj.solvency_deadline_hours} h antes del primer
            partido
          </div>
        </div>
        <span className={`pill ${TONO[reloj.state] || "idle"}`}>
          {reloj.state_label}
        </span>
      </div>

      <div className="kv">
        <span>Saldo</span>
        <b className={reloj.deficit > 0 ? "mono down" : "mono up"}>
          {formatMoney(reloj.balance)}
        </b>
      </div>

      <div className="kv">
        <span>Para el plazo (T−{reloj.solvency_deadline_hours}h)</span>
        <b className="mono">{horas(reloj.hours_to_solvency_deadline)}</b>
      </div>

      <div className="kv">
        <span>Para el cierre de jornada</span>
        <b className="mono">{horas(reloj.hours_to_deadline)}</b>
      </div>

      {reloj.deficit > 0 && (
        <div className="kv">
          <span>Cubierto por ofertas vivas</span>
          <b className={reloj.covered ? "mono up" : "mono down"}>
            {formatMoney(reloj.covered_at_deadline)} de{" "}
            {formatMoney(reloj.deficit)}
          </b>
        </div>
      )}

      <div className={`alert ${reloj.state === "CRITICO" || reloj.state === "EN_EL_PLAZO" ? "crit" : "warn"}`}>
        {reloj.reason_text}
      </div>

      {/* EL DESEMPATE, CON SU MOTIVO.
          "se vende a Cepeda pese al HOLD porque quedan 5 h y el
          saldo es −421.792". */}
      {reloj.override_reason && (
        <div className="kv">
          <span>Quién manda</span>
          <b style={{ fontWeight: 400 }}>
            {reloj.solvency_overrides_hold ? (
              <span className="pill crit">SOLVENCIA</span>
            ) : (
              <span className="pill idle">MOTOR DE OFERTAS</span>
            )}{" "}
            {reloj.override_reason}
          </b>
        </div>
      )}

      {venta && (
        <div style={{ marginTop: 8 }}>
          <div className="sub">LA VENTA QUE TAPA EL AGUJERO</div>
          <div className="kv">
            <span>
              {venta.order}. {venta.name}
            </span>
            <b className={venta.covers_deficit ? "mono up" : "mono down"}>
              {formatMoney(venta.amount)}
              {venta.covers_deficit ? "" : " · no llega"}
            </b>
          </div>
          <p className="note" style={{ textAlign: "left" }}>
            {venta.reason}
          </p>
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        Aceptar una oferta puesta es inmediato. Crear liquidez tarda un
        ciclo del Computer ({reloj.computer_cycle_hours} h medidas), y
        esperar a que un mánager compre una publicación no es un plan:
        se vio <b>uno</b> en {reloj.measured?.window_hours} h de tablón
        frente a {reloj.measured?.computer_sales} ventas al Computer.
      </p>
    </section>
  );
}
