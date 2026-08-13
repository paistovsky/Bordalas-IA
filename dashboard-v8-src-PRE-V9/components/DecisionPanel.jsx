import { Gauge, Target, Shield, WalletCards } from "lucide-react";
import { Card, CardHeader, CardTitle } from "./ui/Card";
import { formatMoney } from "../lib/utils";

export default function DecisionPanel({ data }) {
  const { now, summary, competitive } = data;
  const deficit = Math.max(0, -Number(summary.balance || 0));

  const rows = [
    ["ESTRATEGIA ACTUAL", deficit > 0 ? "Recuperar solvencia" : "Conservar ventaja", Target],
    ["RIESGO XI", summary.lineup_risk || "BAJO", Shield],
    ["OBJETIVO DE CAJA", deficit ? formatMoney(deficit) : "POSITIVO", WalletCards],
    ["PRESIÓN", Number(summary.hours_to_deadline || 0) < 6 ? "ALTA" : "BAJA", Gauge]
  ];

  return (
    <Card className="decision-panel">
      <CardHeader>
        <CardTitle>DECISIÓN DE BORDALÁS</CardTitle>
      </CardHeader>

      <div className="decision-body">
        <div className="decision-manager">
          <div className="manager-silhouette">B</div>
        </div>
        <div className="decision-message">
          <strong>{now.title || "Sin acción necesaria"}</strong>
          <p>{String(now.detail || "Bordalás está observando el mercado.").replaceAll("Pepe", "Bordalás")}</p>
        </div>
      </div>

      <div className="decision-stats">
        {rows.map(([label, value, Icon]) => (
          <div key={label} className="decision-stat">
            <Icon size={16} />
            <div>
              <span>{label}</span>
              <b>{value}</b>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
