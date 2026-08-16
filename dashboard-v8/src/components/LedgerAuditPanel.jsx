import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";

/**
 * Auditoría del libro de operaciones rival.
 *
 * La pregunta no es «¿tenemos datos?» sino «¿explican la
 * plantilla que ese manager tiene hoy?». Se reconcilia jugador
 * a jugador: reparto inicial + operaciones registradas contra
 * la plantilla real. Lo que no cuadra sale con nombre y
 * apellidos, porque un hueco aquí es una puja rival que no
 * hemos visto y que envenena el modelo.
 */

const STATUS_TONE = {
  COMPLETO: "success",
  PARCIAL: "warning",
  INSUFICIENTE: "danger"
};

export default function LedgerAuditPanel({ data }) {
  const audit = data.ledgerAudit || {};
  const managers = audit.by_manager || [];

  if (!audit.available) {
    return (
      <Card>
        <CardHeader><CardTitle>LIBRO DE OPERACIONES RIVAL</CardTitle></CardHeader>
        <div className="empty-state">
          {audit.reason || "Sin reconciliación disponible."}
        </div>
      </Card>
    );
  }

  const status = String(audit.status || "").toUpperCase();

  return (
    <Card className="ledger-card">
      <CardHeader>
        <div>
          <CardTitle>LIBRO DE OPERACIONES RIVAL</CardTitle>
          <p className="section-subtitle">
            ¿EXPLICAMOS LA PLANTILLA QUE TIENE HOY CADA MANAGER?
          </p>
        </div>
        <Badge tone={STATUS_TONE[status] || "default"}>{status || "—"}</Badge>
      </CardHeader>

      <div className="ledger-table">
        <div className="ledger-head">
          <span>MANAGER</span>
          <span>PLANTILLA</span>
          <span>DEL SORTEO</span>
          <span>FICHADOS</span>
          <span>EXPLICADOS</span>
          <span>COBERTURA</span>
        </div>

        {managers.map((manager) => {
          const coverage = Math.round(Number(manager.coverage || 0) * 100);
          const gaps = (manager.unexplained || []).length;

          return (
            <div
              className={manager.is_us ? "ledger-row is-us" : "ledger-row"}
              key={manager.name}
            >
              <strong title={manager.name}>
                {manager.name}
                {manager.is_us && <em className="ledger-us">nosotros</em>}
              </strong>
              <span>{manager.roster_size}</span>
              <span>{manager.from_initial_draft}</span>
              <span>{manager.acquired}</span>
              <span>{manager.explained}</span>
              <div className="ledger-coverage">
                <div className="ledger-bar">
                  <div
                    className={coverage >= 100 ? "ledger-bar-fill full" : "ledger-bar-fill"}
                    style={{ width: `${coverage}%` }}
                  />
                </div>
                <b className={gaps ? "impact-warning" : "impact-good"}>{coverage}%</b>
              </div>
            </div>
          );
        })}
      </div>

      {Boolean((audit.managers_with_gaps || []).length) && (
        <div className="ledger-gaps">
          Sin explicar: {audit.managers_with_gaps.join(", ")}. Cada hueco es
          una operación rival que no hemos visto.
        </div>
      )}

      <p className="model-note">{audit.reason}</p>
    </Card>
  );
}
