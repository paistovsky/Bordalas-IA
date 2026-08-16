import { formatMoney } from "../lib/utils";

/**
 * LO QUE VA A HACER PEPE.
 *
 * En la maqueta original este panel llevaba texto escrito a
 * mano y eso confundio: parecia medido y no lo estaba. Aqui
 * cada paso sale de un campo concreto de status.json y se dice
 * de donde. Si un tramo no se puede derivar, no se pinta.
 */

function resetLabel(clock) {
  if (!clock?.available) return "PRÓXIMO RESET";
  const hours = Number(clock.hours_to_reset || 0);
  return `EN ${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m · ${clock.next_reset_local || ""}`;
}

export default function TimelinePanel({ data }) {
  const clock = data.marketClock || {};
  const next = data.nextAction || {};
  const acquisition = data.acquisition || {};
  const exposure = data.exposure || {};
  const listings = data.listings || {};
  const summary = data.summary || {};
  const backoff = data.backoff || {};

  const bids = (acquisition.targets || []).filter((t) => t.decision === "BID");
  const live = Number(exposure.operation_count || 0);
  const steps = [];

  // 1. Lo que el ciclo ejecuta ahora mismo.
  if (next.action) {
    steps.push({
      state: "now",
      when: "AHORA · ESTE CICLO",
      what: next.label || next.action,
      why: next.reason
    });
  }

  // 2. Pujas pendientes antes del reset: se resuelven ahi o se pierden.
  if (bids.length) {
    const best = bids[0];
    steps.push({
      state: "next",
      when: `ANTES DEL RESET · ${resetLabel(clock)}`,
      what:
        bids.length === 1
          ? `Pujar por ${best.name} — ${formatMoney(best.bid)}`
          : `Pujar por ${bids.length} jugadores — desde ${formatMoney(best.bid)}`,
      why:
        `El mercado Computer se resetea una vez al día: lo que no se puja hoy ` +
        `se pierde. Disponible ${formatMoney(exposure.available_budget)}.`
    });
  }

  // 3. Que pasa en el reset con lo que ya esta en marcha.
  if (clock.available) {
    const publicadas = Number(listings.listing_count || 0);
    steps.push({
      state: "",
      when: `EN EL RESET · ${clock.next_reset_local || "—"}`,
      what:
        live > 0
          ? `Se resuelven ${live} puja(s) viva(s) y llegan ofertas nuevas`
          : "Llegan ofertas nuevas del Computer y se refresca el mercado",
      why:
        `${publicadas} jugador(es) nuestro(s) publicado(s): cada uno recibe una ` +
        `oferta del Computer en el reset.` +
        (live > 0 ? ` Comprometido ahora: ${formatMoney(exposure.committed_total)}.` : "")
    });
  }

  // 4. El otro reloj: el cierre de jornada.
  if (summary.hours_to_deadline != null) {
    const hours = Number(summary.hours_to_deadline);
    steps.push({
      state: "",
      when: `CIERRE DE JORNADA · EN ${Math.floor(hours)}h`,
      what: "Cerrar el XI y el saldo",
      why:
        `Última hora para operar en la jornada ${summary.target_matchday ?? "—"}. ` +
        `XI ${data.lineup?.playable ?? 0}/11 · riesgo ${summary.lineup_risk || "—"}.`
    });
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LO QUE VA A HACER PEPE</h2>
          <div className="sub">Línea temporal · derivada de la telemetría</div>
        </div>
        {Number(backoff.blocked_count || 0) > 0 && (
          <span className="pill warn">{backoff.blocked_count} EN ESPERA</span>
        )}
      </div>

      {steps.length ? (
        <div className="tl">
          {steps.map((step, index) => (
            <div className={`tli ${step.state}`} key={index}>
              <div className="when">{step.when}</div>
              <div className="what">{step.what}</div>
              {step.why && <div className="why">{step.why}</div>}
            </div>
          ))}
        </div>
      ) : (
        <div className="empty">
          No hay ningún paso que derivar de este ciclo.
        </div>
      )}

      {(backoff.blocked || []).map((item, index) => (
        <div className="alert warn" key={index} style={{ marginTop: 10, marginBottom: 0 }}>
          <b>{String(item.action || "").replaceAll("_", " ")}</b> apartada:{" "}
          {item.consecutive_failures === 1
            ? "ha fallado 1 vez"
            : `ha fallado ${item.consecutive_failures} veces seguidas`}
          {item.last_http_status ? ` (HTTP ${item.last_http_status})` : ""}. Se
          reintenta en {Math.max(Math.floor(Number(item.seconds_remaining || 0) / 60), 1)} min.
        </div>
      ))}
    </section>
  );
}
