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

/**
 * Este ciclo, en una línea.
 *
 * `cycle.write_used` y los contadores del motor competitivo
 * estaban en los datos y no los leía nadie. "¿Ha escrito Pepe en
 * esta vuelta y qué?" no debería exigir bajar a la lista de
 * registros y buscarlo.
 */
function CyclePanel({ cycle = {}, last = {}, competitive = {}, consistency = {} }) {
  const escribio = Boolean(cycle.write_used);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>ESTE CICLO</h2>
          <div className="sub">
            {cycle.version || "—"} ·{" "}
            {cycle.timestamp
              ? new Date(cycle.timestamp).toLocaleString("es-ES")
              : "sin marca de tiempo"}
          </div>
        </div>
        <span className={escribio ? "pill ok" : "pill idle"}>
          {escribio ? "HA ESCRITO" : "SOLO HA MIRADO"}
        </span>
      </div>

      {escribio ? (
        <>
          <div className="kv">
            <span>Qué hizo</span>
            <b>{cycle.label || cycle.action || "—"}</b>
          </div>
          <div className="kv">
            <span>Cómo acabó</span>
            <b className={cycle.success ? "up" : "down"}>
              {String(cycle.status || "—").replaceAll("_", " ")}
              {cycle.http_status ? ` · HTTP ${cycle.http_status}` : ""}
            </b>
          </div>
          <div className="kv">
            <span>Comprobado después de escribir</span>
            <b className={cycle.post_write_verified ? "up" : "down"}>
              {cycle.post_write_verified ? "SÍ" : "NO"}
            </b>
          </div>
          {(cycle.reason || last.reason) && (
            <p className="note" style={{ textAlign: "left" }}>
              {cycle.reason || last.reason}
            </p>
          )}
        </>
      ) : (
        <div className="empty">
          Ninguna escritura en esta vuelta. El ciclo permite una como máximo.
        </div>
      )}

      <div className="kv" style={{ marginTop: 8 }}>
        <span>Motor competitivo</span>
        <b className={competitive.live_enabled ? "up" : "dim"}>
          {competitive.status_label ||
            (competitive.live_enabled ? "en vivo" : "solo observa")}
        </b>
      </div>
      <div className="kv">
        <span>Ofertas de mánagers</span>
        <b className="mono">
          {competitive.offer_count ?? 0}
          {competitive.responding_count
            ? ` · ${competitive.responding_count} respondiendo`
            : ""}
          {competitive.waiting_count
            ? ` · ${competitive.waiting_count} en espera`
            : ""}
        </b>
      </div>

      {consistency.available && (
        <div className="kv">
          <span>La pantalla cuadra con Biwenger</span>
          <b className={consistency.ok ? "up" : "down"}>
            {consistency.ok
              ? `SÍ · ${(consistency.checks || []).length} comprobaciones`
              : `NO · ${consistency.failed_count} fallo(s)`}
          </b>
        </div>
      )}
    </section>
  );
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
      <CyclePanel
        cycle={data.cycle || {}}
        last={data.lastExecution || {}}
        competitive={data.competitive || {}}
        consistency={data.consistency || {}}
      />

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
