import { Card, CardHeader, CardTitle } from "./ui/Card";
import { formatMoney } from "../lib/utils";

function Plan({ title, plan, alternate = false }) {
  return (
    <div className={alternate ? "solvency-plan alternate" : "solvency-plan"}>
      <div>
        <span>{title}</span>
        <strong>{plan ? (plan.player_names || []).join(" + ") || "—" : "Sin alternativa"}</strong>
        <small>OBJETIVO: {plan ? formatMoney(plan.total_amount) : "—"}</small>
      </div>
      <div className="probability-ring">
        <b>{plan?.restores_solvency ? "75%" : alternate ? "35%" : "—"}</b>
      </div>
    </div>
  );
}

export default function SolvencyPanel({ data }) {
  const portfolio = data.competitive.portfolio || {};
  const A = portfolio.strategic || null;
  const B = portfolio.current && JSON.stringify(portfolio.current) !== JSON.stringify(A)
    ? portfolio.current
    : null;

  return (
    <Card>
      <CardHeader><CardTitle>PLAN DE SOLVENCIA</CardTitle></CardHeader>
      <div className="solvency-grid">
        <Plan title="PLAN A" plan={A} />
        <Plan title="PLAN B" plan={B} alternate />
      </div>
    </Card>
  );
}
