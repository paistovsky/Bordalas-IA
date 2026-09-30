import {
  Home,
  ListChecks,
  ShoppingCart,
  UsersRound,
  Trophy,
  Wrench
} from "lucide-react";
import { cadenciaEnPalabras } from "../lib/relojes";

// Seis menús (30/09/2026). En el móvil van abajo, como una barra
// de pestañas: seis caben en 390 px sin deslizar.
const ITEMS = [
  ["home", "INICIO", Home],
  ["plan", "EL PLAN", ListChecks],
  ["market", "MERCADO", ShoppingCart],
  ["squad", "PLANTILLA", UsersRound],
  ["league", "LIGA", Trophy],

  // Lo técnico, al final: es para cuando algo huele mal.
  ["taller", "TALLER", Wrench]
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
        {cycle.version || "V10"} · ciclo {cadenciaEnPalabras()}
        <br />
        última escritura:{" "}
        {last.label ? String(last.label).toLowerCase() : "ninguna"}
      </div>
    </nav>
  );
}
