import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { AlarmClock } from "lucide-react";

/**
 * El otro reloj.
 *
 * El deadline de jornada manda en la alineación, pero la
 * operativa diaria la manda el reset del Computer: es cuando se
 * resuelven las pujas, se generan ofertas nuevas y se refresca
 * el mercado. Una puja que no se hace antes del reset no se
 * hace nunca.
 */

function countdown(seconds) {
  const total = Math.max(Number(seconds || 0), 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const rest = Math.floor(total % 60);

  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  if (minutes > 0) return `${minutes}m ${String(rest).padStart(2, "0")}s`;
  return `${rest}s`;
}

const WINDOW_TONE = {
  OPEN: "success",
  CLOSING: "warning",
  CRITICAL: "danger"
};

const WINDOW_LABEL = {
  OPEN: "VENTANA ABIERTA",
  CLOSING: "CERRANDO",
  CRITICAL: "ÚLTIMA HORA"
};

export default function MarketClockPanel({ data, compact = false }) {
  const clock = data.marketClock || {};

  // El JSON llega cada 60 s; el contador corre solo entre medias.
  const [ticked, setTicked] = useState(0);

  useEffect(() => {
    setTicked(0);
    const timer = setInterval(() => setTicked((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [clock.next_reset_epoch, clock.seconds_to_reset]);

  if (!clock.available) {
    return (
      <Card className="clock-card">
        <CardHeader>
          <CardTitle>RELOJ DEL MERCADO</CardTitle>
        </CardHeader>
        <div className="empty-state">
          {clock.reason || "Todavía no se puede deducir la hora del reset."}
        </div>
      </Card>
    );
  }

  const remaining = Number(clock.seconds_to_reset || 0) - ticked;
  const state = String(clock.window_state || "OPEN").toUpperCase();

  return (
    <Card className={compact ? "clock-card compact" : "clock-card"}>
      <CardHeader>
        <div>
          <CardTitle>RELOJ DEL MERCADO</CardTitle>
          <p className="section-subtitle">
            RESET COMPUTER · {clock.next_reset_local || "—"}
          </p>
        </div>
        <Badge tone={WINDOW_TONE[state] || "default"}>
          {WINDOW_LABEL[state] || state}
        </Badge>
      </CardHeader>

      <div className="clock-body">
        <div className="clock-countdown">
          <AlarmClock size={18} />
          <strong>{countdown(remaining)}</strong>
          <small>para el reset</small>
        </div>

        <div className="clock-grid">
          <span>Jugadores del Computer</span>
          <b>{clock.computer_listings ?? "—"}</b>

          <span>Se puede pujar</span>
          <b className={clock.bidding_window_open ? "impact-good" : "impact-danger"}>
            {clock.bidding_window_open ? "SÍ" : "NO"}
          </b>

          <span>Origen del dato</span>
          <b className="clock-source">{clock.source || "—"}</b>
        </div>
      </div>

      {clock.listings_stale && (
        <div className="clock-stale">
          ⚠ El snapshot es anterior al último reset: el mercado que se ve
          puede contener jugadores que ya no existen. No se puja sobre datos
          caducados.
        </div>
      )}

      {!compact && clock.reason && (
        <p className="clock-reason">{clock.reason}</p>
      )}
    </Card>
  );
}
