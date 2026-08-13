import { Card, CardHeader, CardTitle } from "../components/ui/Card";

export default function AuditPage({ data }) {
  return (
    <Card>
      <CardHeader><CardTitle>AUDITORÍA DE BORDALÁS</CardTitle></CardHeader>
      <div className="audit-list">
        {data.activity.slice(0, 50).map((item, index) => (
          <div className="audit-item" key={index}>
            <span>{item.timestamp ? new Date(item.timestamp).toLocaleString("es-ES") : "—"}</span>
            <strong>{String(item.label || "").replaceAll("Pepe", "Bordalás")}</strong>
            <b>{item.write_performed ? "HECHO" : "VISTO"}</b>
          </div>
        ))}
      </div>
    </Card>
  );
}
