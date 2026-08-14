import { useMemo, useState } from "react";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";

const FILTERS = [
  ["all", "TODO"],
  ["market", "MERCADO"],
  ["lineup", "XI"],
  ["competitive", "COMPETITIVE"],
  ["writes", "ESCRITURAS"]
];

function category(item) {
  const text = `${item.phase || ""} ${item.action || ""} ${item.label || ""}`.toUpperCase();
  if (item.write_performed) return "writes";
  if (text.includes("COMPETITIVE") || text.includes("OFFER")) return "competitive";
  if (text.includes("LINEUP") || text.includes("XI")) return "lineup";
  if (text.includes("MARKET") || text.includes("LISTING") || text.includes("VENTA")) return "market";
  return "other";
}

export default function AuditPage({ data }) {
  const [filter, setFilter] = useState("all");

  const rows = useMemo(() => {
    if (filter === "all") return data.activity;
    return data.activity.filter((item) => category(item) === filter);
  }, [data.activity, filter]);

  return (
    <Card className="audit-card-v93">
      <CardHeader>
        <div>
          <CardTitle>AUDITORÍA DE BORDALÁS</CardTitle>
          <p className="section-subtitle">
            Últimos {data.activity.length} registros publicados
          </p>
        </div>
      </CardHeader>

      <div className="audit-filters">
        {FILTERS.map(([id, label]) => (
          <button
            key={id}
            className={filter === id ? "audit-filter active" : "audit-filter"}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="audit-scroll">
        {rows.map((item, index) => (
          <div className="audit-item audit-item-v93" key={index}>
            <span>
              {item.timestamp
                ? new Date(item.timestamp).toLocaleString("es-ES")
                : "—"}
            </span>
            <strong>
              {String(item.label || "").replaceAll("Pepe", "Bordalás")}
            </strong>
            <small>
              {item.status
                ? String(item.status).replaceAll("_", " ")
                : item.phase || "—"}
            </small>
            <b className={item.write_performed ? "audit-write" : "audit-seen"}>
              {item.write_performed
                ? item.verified_post_action
                  ? "✓ VERIFICADA"
                  : "ESCRITURA"
                : "VISTO"}
            </b>
          </div>
        ))}
        {!rows.length && <div className="empty-state">No hay registros para este filtro.</div>}
      </div>
    </Card>
  );
}
