import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { formatMoney } from "../lib/utils";

/**
 * Dinero disponible de verdad.
 *
 * Una puja no descuenta saldo hasta el reset, y el ciclo corre
 * cada 30 minutos: sin contarlas, tres vueltas comprometen tres
 * veces el mismo dinero.
 *
 * Medido el 16/08/2026: Biwenger sí descuenta las pujas vivas
 * de maximumBid (no del balance), así que lo comprometido se
 * resta del presupuesto bruto y el techo se aplica después.
 */

export default function ExposurePanel({ data }) {
  const exposure = data.exposure || {};
  const operations = exposure.operations || [];

  if (!exposure.available) {
    return (
      <Card>
        <CardHeader><CardTitle>CAJA Y PUJAS VIVAS</CardTitle></CardHeader>
        <div className="empty-state">
          {exposure.reason || "Sin presupuesto de especulación calculado."}
        </div>
      </Card>
    );
  }

  const total = Number(exposure.total_budget || 0);
  const committed = Number(exposure.committed_total || 0);
  const available = Number(exposure.available_budget || 0);
  const usedPercent = total > 0 ? Math.min(100, (committed / total) * 100) : 0;

  return (
    <Card className="exposure-card">
      <CardHeader>
        <div>
          <CardTitle>CAJA Y PUJAS VIVAS</CardTitle>
          <p className="section-subtitle">
            MODO {exposure.mode || "—"}
          </p>
        </div>
        <Badge tone={available > 0 ? "success" : "danger"}>
          {available > 0 ? "PUEDE PUJAR" : "SIN MARGEN"}
        </Badge>
      </CardHeader>

      <div className="exposure-figures">
        <div>
          <span>PRESUPUESTO</span>
          <strong>{formatMoney(total)}</strong>
        </div>
        <div>
          <span>COMPROMETIDO</span>
          <strong className={committed > 0 ? "impact-warning" : ""}>
            {formatMoney(committed)}
          </strong>
        </div>
        <div>
          <span>DISPONIBLE</span>
          <strong className="impact-good">{formatMoney(available)}</strong>
        </div>
      </div>

      <div className="exposure-bar">
        <div className="exposure-bar-fill" style={{ width: `${usedPercent}%` }} />
      </div>

      <div className="exposure-split">
        <span>Caja <b>{formatMoney(exposure.cash_budget)}</b></span>
        <span>Deuda segura <b>{formatMoney(exposure.debt_budget)}</b></span>
      </div>

      <div className="exposure-list">
        {operations.length ? (
          operations.map((operation) => (
            <div className="exposure-row" key={operation.offer_id}>
              <div>
                <strong>Puja viva</strong>
                <small>oferta {operation.offer_id}</small>
              </div>
              <b>{formatMoney(operation.amount)}</b>
            </div>
          ))
        ) : (
          <div className="empty-state">Ninguna puja pendiente de resolverse.</div>
        )}
      </div>

      {exposure.blocked_by && (
        <div className="exposure-blocked">Bloqueado por: {exposure.blocked_by}</div>
      )}
    </Card>
  );
}
