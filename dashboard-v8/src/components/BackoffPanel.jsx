import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";

/**
 * Acciones apartadas por fallar.
 *
 * El ciclo ejecuta una sola acción por vuelta. Una que falla
 * siempre se queda con el turno para siempre y deja al resto
 * sin ejecutar. Aquí se ven las que están en espera, para que
 * un fallo persistente no quede escondido detrás de un
 * dashboard en verde.
 *
 * Si no hay ninguna, este panel no se pinta.
 */

function minutes(seconds) {
  return Math.max(Math.floor(Number(seconds || 0) / 60), 1);
}

export default function BackoffPanel({ data }) {
  const backoff = data.backoff || {};
  const blocked = backoff.blocked || [];

  if (!blocked.length) return null;

  return (
    <Card className="backoff-card">
      <CardHeader>
        <CardTitle>ACCIONES EN ESPERA</CardTitle>
        <Badge tone="warning">{blocked.length}</Badge>
      </CardHeader>

      <div className="backoff-list">
        {blocked.map((item, index) => (
          <div className="backoff-row" key={`${item.action}-${item.target_id}-${index}`}>
            <div>
              <strong>{String(item.action || "").replaceAll("_", " ")}</strong>
              <small>
                {item.consecutive_failures === 1
                  ? "ha fallado 1 vez"
                  : `ha fallado ${item.consecutive_failures} veces seguidas`}
                {item.last_http_status ? ` · HTTP ${item.last_http_status}` : ""}
              </small>
            </div>
            <b>{minutes(item.seconds_remaining)} min</b>
          </div>
        ))}
      </div>

      <p className="model-note">
        Se reintentan solas. Mientras tanto el ciclo sigue con lo siguiente en
        la cola en vez de reintentar lo mismo cada media hora.
      </p>
    </Card>
  );
}
