import { useMemo, useState } from "react";

const FILTERS = [
  ["all", "TODO"],
  ["writes", "ESCRITURAS"],
  ["market", "MERCADO"],
  ["lineup", "XI"],
  ["competitive", "RIVALES"]
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
  const backoff = data.backoff || {};

  const rows = useMemo(() => {
    if (filter === "all") return data.activity;
    return data.activity.filter((item) => category(item) === filter);
  }, [data.activity, filter]);

  return (
    <>
      {Boolean((backoff.blocked || []).length) && (
        <section className="pan">
          <div className="pan-head">
            <div>
              <h2>ACCIONES EN ESPERA</h2>
              <div className="sub">Apartadas porque su escritura falla</div>
            </div>
            <span className="pill warn">{backoff.blocked.length}</span>
          </div>

          {backoff.blocked.map((item, index) => (
            <div className="kv" key={index}>
              <span>
                <b>{String(item.action || "").replaceAll("_", " ")}</b>{" "}
                <span className="dim">
                  {item.consecutive_failures === 1
                    ? "ha fallado 1 vez"
                    : `ha fallado ${item.consecutive_failures} veces seguidas`}
                  {item.last_http_status ? ` · HTTP ${item.last_http_status}` : ""}
                </span>
              </span>
              <b className="mono">
                {Math.max(Math.floor(Number(item.seconds_remaining || 0) / 60), 1)} min
              </b>
            </div>
          ))}

          <p className="note" style={{ textAlign: "left" }}>
            Se reintentan solas. Mientras tanto el ciclo sigue con lo siguiente
            en la cola en vez de reintentar lo mismo cada media hora.
          </p>
        </section>
      )}

      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>AUDITORÍA DE BORDALÁS</h2>
            <div className="sub">Últimos {data.activity.length} registros publicados</div>
          </div>
        </div>

        <div className="filters">
          {FILTERS.map(([id, label]) => (
            <button
              key={id}
              className={filter === id ? "on" : ""}
              onClick={() => setFilter(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="scroll">
          {rows.map((item, index) => (
            <div className="arow" key={index}>
              <span className="ts">
                {item.timestamp
                  ? new Date(item.timestamp).toLocaleString("es-ES", {
                      day: "2-digit",
                      month: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit"
                    })
                  : "—"}
              </span>
              <span className="what">
                {String(item.label || item.action || "—").replaceAll("Pepe", "Bordalás")}
              </span>
              <span className="tag">
                {item.status ? String(item.status).replaceAll("_", " ") : item.phase || ""}
              </span>
              <span className={item.write_performed ? "pill ok" : "pill idle"}>
                {item.write_performed
                  ? item.verified_post_action
                    ? "VERIFICADA"
                    : "ESCRITA"
                  : "observa"}
              </span>
            </div>
          ))}
          {!rows.length && <div className="empty">No hay registros para este filtro.</div>}
        </div>
      </section>
    </>
  );
}
