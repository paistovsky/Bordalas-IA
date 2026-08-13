import bordalasMethod from "../assets/bordalas-method.jpg";
import {
  Home,
  UsersRound,
  ShoppingCart,
  Trophy,
  ChartNoAxesCombined,
  ClipboardList,
  Settings
} from "lucide-react";

const items = [
  ["home", "INICIO", Home],
  ["squad", "PLANTILLA", UsersRound],
  ["market", "MERCADO", ShoppingCart],
  ["league", "LIGA", Trophy],
  ["analysis", "ANÁLISIS", ChartNoAxesCombined],
  ["audit", "AUDITORÍA", ClipboardList],
  ["settings", "AJUSTES", Settings]
];

const BORDALAS_PHRASES = [
  "Esto es fútbol, papá.",
  "Competir siempre, también contra presupuestos mayores.",
  "El equipo tiene que saber sufrir y saber competir.",
  "Orden, trabajo y máxima exigencia hasta el final.",
  "Primero controlamos el partido; después buscamos dónde hacer daño.",
  "Cada detalle cuenta cuando el objetivo es ganar."
];

function hourlyPhrase() {
  const hour = new Date().getHours();
  return BORDALAS_PHRASES[hour % BORDALAS_PHRASES.length];
}

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
        <img
          className="method-photo"
          src={bordalasMethod}
          alt="Bordalás"
        />
        <div className="method-copy">
          <strong>EL MÉTODO BORDALÁS</strong>
          <div className="method-values">
            <span>✓ Orden</span>
            <span>✓ Solidez</span>
            <span>✓ Trabajo</span>
            <span>✓ Eficiencia</span>
          </div>
          <blockquote>“{hourlyPhrase()}”</blockquote>
          <small>Frase de la hora</small>
        </div>
      </div>
    </aside>
  );
}
