import {
  Home,
  UsersRound,
  ShoppingCart,
  Handshake,
  Trophy,
  ChartNoAxesCombined,
  ClipboardList,
  Settings
} from "lucide-react";

const items = [
  ["home", "INICIO", Home],
  ["squad", "PLANTILLA", UsersRound],
  ["market", "MERCADO", ShoppingCart],
  ["negotiations", "NEGOCIACIONES", Handshake],
  ["league", "LIGA", Trophy],
  ["analysis", "ANÁLISIS", ChartNoAxesCombined],
  ["audit", "AUDITORÍA", ClipboardList],
  ["settings", "AJUSTES", Settings]
];

export default function Sidebar({ page, setPage }) {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-shield">B</div>
        <div>
          <strong>BORDALÁS IA</strong>
          <small>LA INTELIGENCIA DEL FÚTBOL</small>
        </div>
      </div>

      <nav className="sidebar-nav">
        {items.map(([id, label, Icon]) => (
          <button
            key={id}
            className={page === id ? "sidebar-link active" : "sidebar-link"}
            onClick={() => setPage(id)}
          >
            <Icon size={18} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-method">
        <div className="method-title">
          <div className="manager-avatar">B</div>
          <div>
            <strong>EL MÉTODO BORDALÁS</strong>
            <small>AUTOPILOT COMPETITIVO</small>
          </div>
        </div>
        <div className="method-values">
          <span>✓ Orden</span>
          <span>✓ Solidez</span>
          <span>✓ Eficiencia</span>
        </div>
      </div>
    </aside>
  );
}
