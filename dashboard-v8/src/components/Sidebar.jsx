import {
  Home,
  ShoppingCart,
  Brain,
  UsersRound,
  Trophy,
  Gauge,
  ClipboardList
} from "lucide-react";

const ITEMS = [
  ["home", "INICIO", Home],
  ["market", "MERCADO", ShoppingCart],
  ["brain", "ESTRATEGIA", Brain],
  ["squad", "PLANTILLA", UsersRound],
  ["league", "LIGA", Trophy],

  // El marcador va antes de AUDITORIA a proposito: auditoria es
  // para cuando algo huele mal, el marcador es para el lunes.
  ["marcador", "MARCADOR", Gauge],

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
          <small>ESTO ES FÚTBOL, PAPÁ</small>
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
