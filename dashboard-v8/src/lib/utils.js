import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatMoney(value) {
  const n = Number(value || 0);
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${sign}${(abs / 1_000_000).toFixed(2)}M€`;
  if (abs >= 1_000) return `${sign}${Math.round(abs / 1_000)}k€`;
  return `${sign}${abs.toLocaleString("es-ES")}€`;
}

/**
 * Euros exactos.
 *
 * formatMoney redondea (22.589 -> 23k€) y para un precio por
 * punto eso borra justo la precision que hace util el dato.
 */
export function formatEuros(value) {
  const n = Math.round(Number(value || 0));
  return `${n.toLocaleString("es-ES")} €`;
}

export function ago(iso) {
  if (!iso) return "—";
  const delta = (Date.now() - new Date(iso).getTime()) / 60000;
  if (!Number.isFinite(delta)) return "—";
  if (delta < 1) return "ahora";
  if (delta < 60) return `hace ${Math.floor(delta)} min`;
  if (delta < 1440) return `hace ${(delta / 60).toFixed(1)} h`;
  return `hace ${Math.floor(delta / 1440)} d`;
}

/**
 * Minutos desde la ultima generacion, o null.
 *
 * El dashboard solo se regenera al terminar cada ciclo. Entre
 * ciclo y ciclo lo que se ve es una foto, y hay que decirlo: el
 * 16/08/2026 el panel de caja mostraba dos pujas vivas cuando ya
 * habia tres, simplemente porque la foto era de un minuto antes
 * de la tercera.
 */
export function minutesOld(iso) {
  if (!iso) return null;
  const delta = (Date.now() - new Date(iso).getTime()) / 60000;
  return Number.isFinite(delta) ? Math.max(delta, 0) : null;
}

export function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

export function positionLabel(position) {
  return ({ 1: "POR", 2: "DEF", 3: "MC", 4: "DEL" })[Number(position)] || "JUG";
}

export function humanGate(gate) {
  return ({
    NO_ACTION_WAITING_RIVAL: "ESPERANDO RIVAL",
    ALLOW_SINGLE_RESPONSE: "RESPONDER",
    RECALCULATE: "RECALCULAR"
  })[gate] || String(gate || "—").replaceAll("_", " ");
}

export function lineupCoords(players = []) {
  const grouped = { 1: [], 2: [], 3: [], 4: [] };
  players.forEach((player) => (grouped[player.position] || grouped[4]).push(player));
  const output = [];
  [[4, 13], [3, 38], [2, 68], [1, 91]].forEach(([position, y]) => {
    grouped[position].forEach((player, index) => {
      output.push({
        ...player,
        x: ((index + 1) * 100) / (grouped[position].length + 1),
        y
      });
    });
  });
  return output;
}
