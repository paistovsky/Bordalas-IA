import { formatEuros, formatMoney } from "../lib/utils";

/**
 * CEREBRO: por que Pepe hace lo que hace.
 *
 * Cuatro columnas que son las cuatro preguntas reales del
 * ciclo: que puede hacer, con que dinero, contra quien, y que
 * le esta frenando.
 */

function Queue({ priorities, next }) {
  return (
    <div className="col">
      <h4>Cola de decisiones</h4>
      {priorities.map((item, index) => {
        const chosen = next?.type === item.type;
        const cls = chosen ? "node take" : item.executable ? "node" : "node drop";

        return (
          <div className={cls} key={index}>
            <div className="t">{item.label}</div>
            <div className="d">{String(item.status || item.action).replaceAll("_", " ")}</div>
            <div className="m">
              prioridad {item.priority} ·{" "}
              {chosen ? "SE EJECUTA" : item.executable ? "ejecutable" : "solo observa"}
            </div>
          </div>
        );
      })}
      {next?.reason && <p className="note" style={{ textAlign: "left" }}>{next.reason}</p>}
    </div>
  );
}

function Money({ exposure, solvency }) {
  return (
    <div className="col">
      <h4>Con qué dinero</h4>
      <div className="node">
        <div className="t">{formatMoney(exposure.available_budget)}</div>
        <div className="d">disponible tras descontar pujas vivas</div>
        <div className="m">
          caja {formatMoney(exposure.cash_budget)} + deuda {formatMoney(exposure.debt_budget)}
        </div>
      </div>
      <div className={Number(exposure.committed_total || 0) > 0 ? "node wait" : "node"}>
        <div className="t">{formatMoney(exposure.committed_total)}</div>
        <div className="d">comprometido en {exposure.operation_count || 0} puja(s) viva(s)</div>
        <div className="m">Biwenger ya lo descuenta de maximumBid</div>
      </div>
      {solvency?.needed != null && (
        <div className={solvency.needed ? "node drop" : "node"}>
          <div className="t">{solvency.needed ? "Hay que sanear" : "Solvencia cubierta"}</div>
          <div className="d">
            {solvency.needed
              ? `déficit ${formatMoney(solvency.deficit)}`
              : "no hace falta vender para llegar al cierre"}
          </div>

          {/* `possible` era el dato que faltaba: hay deficits que
              no se pueden cubrir vendiendo sin romper el XI, y
              eso no es lo mismo que "hay que sanear". */}
          {solvency.needed && (
            <div className="m">
              {solvency.possible
                ? "Se puede cubrir vendiendo sin romper el once."
                : "NO se puede cubrir sin romper el once."}
            </div>
          )}
        </div>
      )}

      {/* De dónde saldría el dinero si hiciera falta. Estaba en
          los datos y no se pintaba en ningún sitio. */}
      <div className="node">
        <div className="t">
          {solvency?.listed ?? 0} publicados
          {Number(solvency?.to_list || 0) > 0
            ? ` · ${solvency.to_list} por publicar`
            : ""}
        </div>
        <div className="d">
          {solvency?.incoming_offers ?? 0} oferta(s) del Computer sobre la mesa
        </div>
        <div className="m">
          Publicar es gratis y reversible: es la vía de liquidez que no
          compromete nada hasta que se acepta.
        </div>
      </div>
    </div>
  );
}

function Rivals({ acquisition }) {
  const rivals = [...(acquisition.rivals || [])].sort(
    (a, b) => Number(b.participation || 0) - Number(a.participation || 0)
  );

  return (
    <div className="col">
      <h4>Contra quién</h4>
      {rivals.map((rival) => {
        const percent = Math.round(Number(rival.participation || 0) * 100);
        return (
          <div className={rival.never_bids ? "node drop" : percent >= 40 ? "node wait" : "node"} key={rival.name}>
            <div className="t">{rival.name}</div>
            <div className="d">
              {rival.never_bids ? "nunca ha pujado" : `puja el ${percent}% de las veces`}
            </div>
            <div className="m">puede pagar {formatMoney(rival.capacity)}</div>
          </div>
        );
      })}
      <p className="note" style={{ textAlign: "left" }}>
        Medido sobre el histórico del tablón, no estimado por su patrimonio.
      </p>
    </div>
  );
}

function Limits({ data }) {
  const limits = [];
  const guardrail = data.guardrail || {};
  const clock = data.marketClock || {};
  const exposure = data.exposure || {};
  const premium = data.acquisition?.premium_model || {};
  const backoff = data.backoff || {};

  (guardrail.by_position || [])
    .filter((row) => row.at_floor)
    .forEach((row) =>
      limits.push({
        tone: "drop",
        title: `${row.name} en el suelo`,
        detail: `Con ${row.owned} no se puede vender ninguno más sin romper el XI.`
      })
    );

  if (exposure.blocked_by) {
    limits.push({
      tone: "drop",
      title: "Presupuesto bloqueado",
      detail: String(exposure.blocked_by).replaceAll("_", " ")
    });
  }

  if (clock.available && !clock.bidding_window_open) {
    limits.push({
      tone: "drop",
      title: "Ventana de pujas cerrada",
      detail: clock.reason
    });
  }

  if (premium.samples != null && !premium.calibrated) {
    limits.push({
      tone: "wait",
      title: "Curva de primas sin calibrar",
      detail: premium.reason
    });
  }

  (backoff.blocked || []).forEach((item) =>
    limits.push({
      tone: "wait",
      title: `${String(item.action).replaceAll("_", " ")} en espera`,
      detail: `Ha fallado ${item.consecutive_failures} vez/veces${
        item.last_http_status ? ` (HTTP ${item.last_http_status})` : ""
      }. Se reintenta sola.`
    })
  );

  if (data.summary?.operations_locked) {
    limits.push({
      tone: "drop",
      title: "Operaciones bloqueadas",
      detail: "La jornada está en marcha: no se opera hasta el unlock."
    });
  }

  return (
    <div className="col">
      <h4>Qué le está frenando</h4>
      {limits.length ? (
        limits.map((limit, index) => (
          <div className={`node ${limit.tone}`} key={index}>
            <div className="t">{limit.title}</div>
            <div className="d">{limit.detail}</div>
          </div>
        ))
      ) : (
        <div className="node take">
          <div className="t">Nada</div>
          <div className="d">
            Ningún guardarraíl está activo: puede operar con normalidad.
          </div>
        </div>
      )}
    </div>
  );
}

export default function BrainPage({ data }) {
  const acquisition = data.acquisition || {};
  const bids = (acquisition.targets || []).filter((t) => t.decision === "BID");

  return (
    <>
      <section className="pan">
        <h2>CÓMO DECIDE PEPE</h2>
        <div className="sub">Una acción por ciclo · gana la primera ejecutable de la cola</div>

        <div className="tree">
          <Queue priorities={data.priorities || []} next={data.nextAction} />
          <Money exposure={data.exposure || {}} solvency={data.solvency || {}} />
          <Rivals acquisition={acquisition} />
          <Limits data={data} />
        </div>
      </section>

      {Boolean(bids.length) && (
        <section className="pan">
          <h2>LA CUENTA DE CADA PUJA</h2>
          <div className="sub">Valor esperado = probabilidad de ganar × (lo que vale − lo que pagamos)</div>

          {bids.map((target) => (
            <div className="node take" key={target.id} style={{ marginBottom: 8 }}>
              <div className="t">
                {target.name} — {formatEuros(target.bid)}{" "}
                <span className="pill ok" style={{ marginLeft: 6 }}>
                  {Math.round(Number(target.win_probability || 0) * 100)}%
                </span>
              </div>
              <div className="d">{target.reason}</div>
              {(target.bid_reasons || []).map((reason, index) => (
                <div className="d" key={index}>· {reason}</div>
              ))}
              <div className="m">
                valor esperado {formatEuros(target.expected_value)} · intención{" "}
                {target.intent || "—"}
                {target.replaces ? ` · sustituye a ${target.replaces}` : ""}
              </div>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
