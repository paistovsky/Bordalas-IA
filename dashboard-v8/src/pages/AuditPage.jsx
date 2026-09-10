import { useMemo, useState } from "react";
import AhoraPanel from "../components/AhoraPanel";
import BidOutcomesPanel from "../components/BidOutcomesPanel";
import CobrarPanel from "../components/CobrarPanel";
import ConcentrationPanel from "../components/ConcentrationPanel";
import DineroPanel from "../components/DineroPanel";
import ElOncePanel from "../components/ElOncePanel";
import PressPanel from "../components/PressPanel";
import RacePanel from "../components/RacePanel";
import ScoutPanel from "../components/ScoutPanel";
import VentanaPanel from "../components/VentanaPanel";
import { ago, formatMoney } from "../lib/utils";

/* LO QUE BAJO DE INICIO EL 10/09/2026
 *
 * Inicio se quedo en la tira de estado y cuatro paneles. Todo lo
 * que estaba alli y no cabia en esos cuatro esta AQUI, entero y
 * leyendo los mismos datos:
 *
 *   AhoraPanel     lo que esta en rojo ahora
 *   DineroPanel    el dinero al detalle
 *   VentanaPanel   la ventana del reset: que pujo y que renovo
 *   CobrarPanel    las ofertas que se pueden cobrar
 *   ElOncePanel    los puntos que se quedaron en el banquillo
 *   Objetivos      a por quien va Bordalas
 *
 * Ni uno se ha borrado. La DEUDA MAXIMA, que era la unica
 * pregunta del dinero que hay que contestar en diez segundos,
 * subio a la tira con su desglose: saldo, comprometido, credito.
 */

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
          {/* LA FECHA ABSOLUTA NO BASTA.
              «16/8/2026, 18:56» hay que restarlo mentalmente para
              saber si es de ahora; «hace 26 h» no. Este cuadro
              enseñó durante más de un día una escritura de la
              antevíspera bajo un título que dice «este». */}
          <div className="sub">
            {cycle.version || "—"} ·{" "}
            {cycle.timestamp
              ? `${ago(cycle.timestamp)} · ${new Date(cycle.timestamp).toLocaleString("es-ES")}`
              : "sin marca de tiempo"}
          </div>
        </div>
        <span className={escribio ? "pill ok" : "pill idle"}>
          {escribio ? "HA ESCRITO" : "SOLO HA MIRADO"}
        </span>
      </div>

      {/* Este fichero solo se reescribe cuando el motor con
          permiso de escritura ejecuta. El observador que regenera
          la pantalla corre mucho más a menudo, así que puede
          quedarse congelado sin que nada más lo parezca. */}
      {cycle.stale && (
        <div className="alert warn" style={{ marginTop: 9 }}>
          Esto NO es de este ciclo. La última ejecución con permiso de
          escritura fue {ago(cycle.timestamp)}: desde entonces el
          dashboard se ha seguido refrescando, pero Pepe no ha escrito
          nada en Biwenger.
        </div>
      )}

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

/* A POR QUIEN VA BORDALAS. Venia de la portada el 10/09: dice
   lo que pujaria y por que ese importe, que es material de
   verificacion, no una decision que tomar hoy. */
function Objetivos({ data }) {
  const board = data.acquisition || {};

  const filas = (board.targets || [])
    .filter((t) => Number(t.bid || 0) > 0)
    .slice(0, 5);

  if (!filas.length) {
    return (
      <section className="pan">
        <h2>A POR QUIÉN VA PEPE</h2>
        <div className="sub">
          Ningún objetivo con puja propuesta ahora mismo.
        </div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>A POR QUIÉN VA PEPE</h2>
          <div className="sub">
            lo que pujaría, y por qué ese importe
          </div>
        </div>
      </div>
      <table className="tbl">
        <tbody>
          {filas.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td className="num">{formatMoney(t.bid)}</td>
              <td className="num sub">
                vale {formatMoney(t.market_price)}
              </td>
              <td className="sub">{t.decision}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
      {/* LO QUE BAJO DE INICIO. Va primero porque `AhoraPanel`
          sigue siendo lo que exige una decision hoy: solo que
          Inicio ya no es su sitio. */}
      <AhoraPanel data={data} />

      <div className="grid g2">
        <DineroPanel data={data} />
        <VentanaPanel data={data} />
      </div>

      <CobrarPanel data={data} />

      <ElOncePanel data={data} />

      <Objetivos data={data} />

      <CyclePanel
        cycle={data.cycle || {}}
        last={data.lastExecution || {}}
        competitive={data.competitive || {}}
        consistency={data.consistency || {}}
      />

      {/* EL LIBRO DE PUJAS (05/09/2026)
          Se escribe desde el 03/09 y no lo enseñaba nadie. Va en
          AUDITORIA porque es exactamente eso: lo que Pepe hizo al
          pujar, no lo que pensaba pujar. */}
      <BidOutcomesPanel data={data} />

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

      {/* ================================================
          LO QUE BAJO DE LA PORTADA EL 10/09/2026

          Nada se ha borrado. Todo esto contesta POR QUE en vez
          de QUE, y ninguno pide una decision hoy:

            LA CARRERA        como va la temporada. Termometro.
            CONCENTRACION     como esta repartida la plantilla.
            EL OJEADOR        lo que otras webs creen que vale
                              un jugador: es una ENTRADA de la
                              valoracion, no una decision. Si
                              alguna vez contradice al precio,
                              lo que hay que mirar es la
                              valoracion, y esta aqui al lado.
            LA PRENSA         partes medicos y convocatorias. Ya
                              esta DENTRO de la probabilidad de
                              ser titular que pinta el XI de la
                              portada; aqui se ve el material en
                              crudo del que sale. Cuando dice
                              algo que cambia una decision, sube
                              solo: al XI como "0 % sin motivo"
                              y a la tira roja si tumba a un
                              titular.
          ================================================ */}

      {/* PLANTILLA POR POSICION. Estaba en la portada y no
          pedia ninguna decision: dice como esta repartida la
          plantilla, no que hacer con ella. Se conserva entero. */}
      {data.guardrail?.available && (
        <section className="pan">
          <h2>PLANTILLA POR POSICIÓN</h2>
          <div className="sub">Tengo / suelo para alinear / vendibles</div>
          <div className="poswrap">
            {(data.guardrail.by_position || []).map((row) => (
              <div
                className={
                  row.owned < row.floor
                    ? "poscel crit"
                    : row.below_desired
                    ? "poscel warn"
                    : "poscel"
                }
                key={row.position}
              >
                <b>{row.name.toUpperCase()}</b>
                <span className="big">{row.owned}</span>
                <small>
                  suelo {row.floor} · vend. {row.disposable}
                </small>
              </div>
            ))}
          </div>
          {data.guardrail.goalkeeper_warning && (
            <div className="alert warn" style={{ marginTop: 9, marginBottom: 0 }}>
              🧤 {data.guardrail.goalkeeper_warning}
            </div>
          )}
        </section>
      )}

      <RacePanel data={data} />
      <ConcentrationPanel data={data} />
      <ScoutPanel data={data} />
      <PressPanel data={data} />
    </>
  );
}
