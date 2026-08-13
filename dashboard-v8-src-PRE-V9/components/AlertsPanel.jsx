import { Card, CardHeader, CardTitle } from "./ui/Card";
import { CircleAlert, CircleCheck, Clock3 } from "lucide-react";
import { formatMoney } from "../lib/utils";

export default function AlertsPanel({ data }) {
  const { summary, lineup, competitive } = data;
  const active = competitive.offers || [];
  const recent = competitive.recentClosed || [];

  const alerts = [];
  if (recent[0]) {
    alerts.push(["danger", CircleAlert, "OFERTA RETIRADA", `${recent[0].rival_name} retiró su oferta por ${recent[0].player_name}.`]);
  }
  if (active[0]) {
    alerts.push(["warning", CircleAlert, "OFERTA ACTIVA", `${active[0].rival_name} ofrece ${formatMoney(active[0].amount)} por ${active[0].player_name}.`]);
  }
  alerts.push(["success", CircleCheck, "XI COMPLETO", `${lineup.playable || 0}/11 jugadores disponibles para la jornada.`]);
  alerts.push(["info", Clock3, "DEADLINE", `Quedan ${Number(summary.hours_to_deadline || 0).toFixed(1)}h para el cierre.`]);

  return (
    <Card>
      <CardHeader><CardTitle>ALERTAS IMPORTANTES</CardTitle></CardHeader>
      <div className="alerts-list">
        {alerts.map(([tone, Icon, title, copy]) => (
          <div key={title} className="alert-row">
            <div className={`alert-icon alert-${tone}`}><Icon size={15} /></div>
            <strong className={`tone-${tone}`}>{title}</strong>
            <span>{copy}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
