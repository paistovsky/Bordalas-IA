import { Card, CardHeader, CardTitle } from "./ui/Card";
import { formatMoney } from "../lib/utils";

function planSignature(plan) {
  return JSON.stringify([
    plan?.player_names || [],
    plan?.total_amount || 0
  ]);
}

function Plan({ title, subtitle, plan, tone }) {
  return (
    <div className={`solvency-plan plan-${tone}`}>
      <div className="plan-copy">
        <span>{title}</span>
        <small className="plan-subtitle">{subtitle}</small>
        <strong>
          {plan
            ? (plan.player_names || []).join(" + ") || "Sin ventas"
            : "Sin alternativa calculada"}
        </strong>

        {plan && (
          <div className="plan-metrics">
            <div><span>INGRESO</span><b>{formatMoney(plan.total_amount)}</b></div>
            <div><span>SALDO POST</span><b>{formatMoney(plan.post_balance)}</b></div>
            <div><span>XI POST</span><b>{plan.playable_count ?? "—"}/11</b></div>
            <div><span>FORMACIÓN</span><b>{plan.formation_after || "—"}</b></div>
          </div>
        )}
      </div>

      <div className="plan-status">
        <b>{plan?.restores_solvency ? "VIABLE" : plan ? "CONTINGENCIA" : "—"}</b>
      </div>
    </div>
  );
}

export default function SolvencyPanel({ data }) {
  // V10.8: raw es la fuente de verdad. Esto evita perder los planes
  // aunque normalizeStatus cambie o una versión antigua quede cacheada.
  const safeDebt =
    data.raw?.solvency?.plans ||
    data.solvency?.plans ||
    {};
  const safeDebtCandidates = [
    safeDebt.a,
    safeDebt.b,
    safeDebt.c
  ].filter(Boolean);

  const portfolio = data.competitive?.portfolio || {};
  const competitiveCandidates = [
    portfolio.strategic || null,
    ...(portfolio.strategic_alternatives || []),
    portfolio.current || null,
    ...(portfolio.current_alternatives || [])
  ].filter(Boolean);

  const candidates = safeDebtCandidates.length
    ? safeDebtCandidates
    : competitiveCandidates;

  const unique = [];
  const seen = new Set();

  for (const plan of candidates) {
    const signature = planSignature(plan);
    if (!seen.has(signature)) {
      seen.add(signature);
      unique.push(plan);
    }
  }

  const A = unique[0] || null;
  const B = unique[1] || null;
  const C = unique[2] || null;

  return (
    <Card className="solvency-card-v93">
      <CardHeader>
        <div>
          <CardTitle>PLAN DE SOLVENCIA</CardTitle>
          <p className="section-subtitle">
            A = preferido · B = alternativa · C = contingencia
          </p>
        </div>
      </CardHeader>

      <div className="solvency-grid-v93">
        <Plan title="PLAN A" subtitle="PREFERIDO" plan={A} tone="a" />
        <Plan title="PLAN B" subtitle="ALTERNATIVA" plan={B} tone="b" />
        <Plan title="PLAN C" subtitle="CONTINGENCIA" plan={C} tone="c" />
      </div>
    </Card>
  );
}
