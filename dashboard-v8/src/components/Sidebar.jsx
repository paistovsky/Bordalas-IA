import {
  Home,
  ShoppingCart,
  Brain,
  UsersRound,
  Trophy,
  ClipboardList
} from "lucide-react";

const ITEMS = [
  ["home", "INICIO", Home],
  ["market", "MERCADO", ShoppingCart],
  ["brain", "CEREBRO", Brain],
  ["squad", "PLANTILLA", UsersRound],
  ["league", "LIGA", Trophy],
  ["audit", "AUDITORÍA", ClipboardList]
];

export default function Sidebar({ page, setPage, data }) {
  const cycle = data?.cycle || {};
  const last = data?.lastExecution || {};

  return (
    <nav className="sidebar">
      <div className="brand">
        <div className="blogo">B</div>
        <div>
          <b>BORDALÁS IA</b>
          <small>LA INTELIGENCIA DEL FÚTBOL</small>
        </div>
      </div>

      {ITEMS.map(([id, label, Icon]) => (
        <button
          key={id}
          className={page === id ? "on" : ""}
          onClick={() => setPage(id)}
        >
          <Icon size={16} />
          <span>{label}</span>
        </button>
      ))}

      <div className="sidebar-foot">
        <b><span className="dot-ok">●</span> AUTOPILOT LIVE</b>
        {cycle.version || "V10"} · ciclo {data?.meta?.cycle_minutes || 30} min
        <br />
        última escritura:{" "}
        {last.label ? String(last.label).toLowerCase() : "ninguna"}
      </div>
    </nav>
  );
}
