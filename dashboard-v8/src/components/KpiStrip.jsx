import {
  WalletCards,
  UsersRound,
  Clock3,
  ShieldCheck,
  BarChart3
} from "lucide-react";
import { formatMoney } from "../lib/utils";

function Kpi({ icon: Icon, label, value, helper, tone = "neutral" }) {
  return (
    <div className="kpi">
      <div className={`kpi-icon kpi-icon-${tone}`}><Icon size={19} /></div>
      <div className="kpi-copy">
        <span>{label}</span>
        <strong className={`tone-${tone}`}>{value}</strong>
        <small>{helper}</small>
      </div>
    </div>
  );
}

export default function KpiStrip({ data }) {
  const { summary, lineup } = data;
  const mode = summary.operations_locked
    ? "BLOQUEADO"
    : summary.hard_safety
      ? "HARD SAFETY"
      : summary.balance < 0
        ? "SOLVENCIA"
        : "CONTROLADO";
  const modeTone = summary.operations_locked
    ? "danger"
    : summary.hard_safety || summary.balance < 0
      ? "warning"
      : "success";
  return (
    <div className="kpi-strip">
      <Kpi icon={WalletCards} label="SALDO" value={formatMoney(summary.balance)} helper={summary.balance < 0 ? "Déficit" : "Disponible"} tone={summary.balance < 0 ? "danger" : "success"} />
      <Kpi icon={BarChart3} label="VALOR XI" value={formatMoney(lineup.total_value)} helper="Titulares" tone="neutral" />
      <Kpi icon={UsersRound} label="XI COMPLETO" value={`${lineup.playable || 0}/11`} helper="Disponibles" tone={lineup.playable === 11 ? "success" : "danger"} />
      <Kpi icon={Clock3} label="CIERRE MERCADO" value={`${Number(summary.hours_to_deadline || 0).toFixed(1)}h`} helper="Para la jornada" tone="warning" />
      <Kpi icon={ShieldCheck} label="ESTADO" value={mode} helper="Estrategia protegida" tone={modeTone} />
    </div>
  );
}
