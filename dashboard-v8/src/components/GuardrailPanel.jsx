import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";

/**
 * Guardarraíl posicional.
 *
 * El suelo sale de las formaciones jugables, no de una opinión:
 * con 1-3-3-1 no se puede bajar de un portero, tres defensas,
 * tres centrocampistas y un delantero. Vender por debajo del
 * suelo deja el XI incompleto y eso no lo arregla ninguna
 * plusvalía.
 */

export default function GuardrailPanel({ data }) {
  const guardrail = data.guardrail || {};
  const rows = guardrail.by_position || [];

  const atFloor = rows.filter((row) => row.at_floor);

  if (!guardrail.available) {
    return (
      <Card>
        <CardHeader><CardTitle>GUARDARRAÍL POSICIONAL</CardTitle></CardHeader>
        <div className="empty-state">Sin datos de plantilla por posición.</div>
      </Card>
    );
  }

  return (
    <Card className="guardrail-card">
      <CardHeader>
        <div>
          <CardTitle>GUARDARRAÍL POSICIONAL</CardTitle>
          <p className="section-subtitle">
            CUÁNTOS PUEDE VENDER BORDALÁS SIN ROMPER EL XI
          </p>
        </div>
        <Badge tone={atFloor.length ? "warning" : "success"}>
          {atFloor.length ? `${atFloor.length} EN EL SUELO` : "TODAS CON MARGEN"}
        </Badge>
      </CardHeader>

      <div className="guardrail-table">
        <div className="guardrail-head">
          <span>POSICIÓN</span>
          <span>TENGO</span>
          <span>SUELO</span>
          <span>VENDIBLES</span>
        </div>

        {rows.map((row) => (
          <div
            className={row.at_floor ? "guardrail-row at-floor" : "guardrail-row"}
            key={row.position}
          >
            <strong>{row.name}</strong>
            <b>{row.owned}</b>
            <span>{row.floor}</span>
            <em className={row.disposable > 0 ? "impact-good" : "impact-danger"}>
              {row.disposable}
            </em>
          </div>
        ))}
      </div>

      {guardrail.goalkeeper_warning && (
        <div className="guardrail-warning">
          🧤 {guardrail.goalkeeper_warning}
        </div>
      )}

      {Boolean((guardrail.positions_to_replenish || []).length) && (
        <div className="guardrail-warning">
          Reponer: {guardrail.positions_to_replenish.join(", ")}
        </div>
      )}
    </Card>
  );
}
