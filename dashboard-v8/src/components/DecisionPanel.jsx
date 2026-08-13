import bordalasCalm from "../assets/bordalas-calm.jpg";
import bordalasWatch from "../assets/bordalas-watch.jpg";
import bordalasAlert from "../assets/bordalas-alert.jpg";
import bordalasCritical from "../assets/bordalas-critical.jpg";
import { Gauge, Target, Shield, WalletCards } from "lucide-react";
import { Card, CardHeader, CardTitle } from "./ui/Card";
import { formatMoney } from "../lib/utils";

function decisionPortrait(data) {
  const level = String(data?.now?.level || "").toUpperCase();
  const pressure = Number(data?.summary?.lineup_pressure || 0);
  const hours = Number(data?.summary?.hours_to_deadline || 999);

  if (level === "ACTION" || pressure >= 75 || hours <= 2) {
    return ["critical", bordalasCritical];
  }
  if (level === "SOLVENCY" || pressure >= 50 || hours <= 6) {
    return ["alert", bordalasAlert];
  }
  if (level === "WAIT" || pressure >= 20) {
    return ["watch", bordalasWatch];
  }
  return ["calm", bordalasCalm];
}

export default function DecisionPanel({ data }) {
  const { now, summary } = data;
  const deficit = Math.max(0, -Number(summary.balance || 0));
  const [portraitState, portrait] = decisionPortrait(data);

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
        <div className={`decision-manager state-${portraitState}`}>
          <img src={portrait} alt="Bordalás" />
          <span className="decision-state-dot" />
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
