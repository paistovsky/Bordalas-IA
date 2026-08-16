import { formatMoney } from "../lib/utils";

/**
 * Tira de estado. Seis numeros y de donde salen.
 */

function Kpi({ label, value, sub, tone = "" }) {
  return (
    <div className={tone ? `kpi ${tone}` : "kpi"}>
      <div className="l">{label}</div>
      <div className="v">{value}</div>
      <div className="s">{sub}</div>
    </div>
  );
}

export default function KpiStrip({ data }) {
  const summary = data.summary || {};
  const exposure = data.exposure || {};
  const clock = data.marketClock || {};
  const lineup = data.lineup || {};
  const acquisition = data.acquisition || {};

  const balance = Number(summary.balance || 0);
  const hoursReset = Number(clock.hours_to_reset || 0);

  return (
    <div className="strip">
      <Kpi
        label="Saldo"
        value={formatMoney(balance)}
        sub={`puja máx. ${formatMoney(summary.maximum_bid)}`}
        tone={balance < 0 ? "bad" : ""}
      />
      <Kpi
        label="Puede gastar"
        value={formatMoney(exposure.available_budget)}
        sub={exposure.mode ? String(exposure.mode).replaceAll("_", " ").toLowerCase() : "sin presupuesto"}
        tone={Number(exposure.available_budget || 0) > 0 ? "good" : "bad"}
      />
      <Kpi
        label="Reset del mercado"
        value={clock.available ? `${hoursReset.toFixed(1)}h` : "—"}
        sub={clock.available ? `${clock.next_reset_local} · se resuelven las pujas` : "sin deducir"}
        tone={clock.available && hoursReset < 3 ? "hot" : ""}
      />
      <Kpi
        label="Cierre de jornada"
        value={summary.hours_to_deadline != null ? `${Number(summary.hours_to_deadline).toFixed(1)}h` : "—"}
        sub={`jornada ${summary.target_matchday ?? "—"} · ${summary.phase || "—"}`}
        tone={Number(summary.hours_to_deadline || 999) < 6 ? "hot" : ""}
      />
      <Kpi
        label="XI"
        value={`${lineup.playable ?? 0}/11`}
        sub={`${lineup.formation || "—"} · riesgo ${String(summary.lineup_risk || "—").toLowerCase()}`}
        tone={Number(lineup.missing || 0) > 0 ? "bad" : ""}
      />
      <Kpi
        label="Objetivos hoy"
        value={`${acquisition.biddable ?? 0}/${acquisition.market_size ?? 0}`}
        sub="del mercado Computer"
        tone={Number(acquisition.biddable || 0) > 0 ? "good" : ""}
      />
    </div>
  );
}
