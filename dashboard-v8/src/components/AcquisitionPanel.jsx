import { useState } from "react";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";
import PlayerAvatar from "./PlayerAvatar";
import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

/**
 * Qué quiere fichar Bordalás y por qué.
 *
 * Cada objetivo lleva su cuenta: lo que vale para nosotros en
 * euros, cuánto pujaría, con qué probabilidad de ganar y qué
 * valor esperado deja. Si no puja, también dice por qué.
 */

const DECISION_TONE = {
  BID: "success",
  NO_COMPENSA: "warning",
  NO_DISPONIBLE: "danger",
  SIN_VALOR: "default"
};

const DECISION_LABEL = {
  BID: "PUJAR",
  NO_COMPENSA: "NO COMPENSA",
  NO_DISPONIBLE: "NO DISPONIBLE",
  SIN_VALOR: "SIN VALOR"
};

const INTENT_LABEL = {
  XI_UPGRADE: "MEJORA EL XI",
  SPECULATION: "ESPECULACIÓN"
};

function TargetRow({ target }) {
  const decision = String(target.decision || "").toUpperCase();
  const bids = decision === "BID";
  const probability = Math.round(Number(target.win_probability || 0) * 100);

  return (
    <Tooltip.Root delayDuration={120}>
      <Tooltip.Trigger asChild>
        <div className={bids ? "target-row biddable" : "target-row"}>
          <PlayerAvatar player={target} className="target-avatar" />

          <div className="target-name">
            <strong>{target.name}</strong>
            <span>
              {positionLabel(target.position)} · {formatMoney(target.market_price)}
              {target.replaces ? ` · sale ${target.replaces}` : ""}
            </span>
          </div>

          <div className="target-value">
            <b>{formatMoney(target.our_value)}</b>
            <span>vale para nosotros</span>
          </div>

          <div className="target-bid">
            {bids ? (
              <>
                <b className="impact-good">{formatMoney(target.bid)}</b>
                <span>{probability}% de ganar</span>
              </>
            ) : (
              <>
                <b className="target-nobid">—</b>
                <span>no puja</span>
              </>
            )}
          </div>

          <Badge tone={DECISION_TONE[decision] || "default"}>
            {DECISION_LABEL[decision] || decision}
          </Badge>
        </div>
      </Tooltip.Trigger>

      <Tooltip.Portal>
        <Tooltip.Content className="tooltip-card target-tooltip" sideOffset={10} collisionPadding={16}>
          <div className="tooltip-player-head">
            <PlayerAvatar player={target} className="tooltip-avatar" />
            <div>
              <strong>{target.name}</strong>
              <small>
                {INTENT_LABEL[target.intent] || "SIN INTENCIÓN"}
                {target.points_last_season != null
                  ? ` · ${target.points_last_season} pts la pasada`
                  : ""}
              </small>
            </div>
          </div>

          <div className="tooltip-grid">
            <span>Precio</span><b>{formatMoney(target.market_price)}</b>
            <span>Vale para nosotros</span><b>{formatMoney(target.our_value)}</b>
            {Number(target.bid) > 0 && (
              <>
                <span>Puja óptima</span><b>{formatMoney(target.bid)}</b>
                <span>Probabilidad</span><b>{probability}%</b>
                <span>Valor esperado</span><b>{formatMoney(target.expected_value)}</b>
              </>
            )}
          </div>

          <p className="target-reason">{target.reason}</p>

          {Boolean((target.bid_reasons || []).length) && (
            <ul className="target-reason-list">
              {target.bid_reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          )}

          <Tooltip.Arrow className="tooltip-arrow" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

function RivalTable({ rivals }) {
  const sorted = [...rivals].sort(
    (a, b) => Number(b.participation || 0) - Number(a.participation || 0)
  );

  return (
    <div className="rival-model">
      <div className="rival-model-head">
        <span>RIVAL</span>
        <span>PUJA</span>
        <span>PUEDE PAGAR</span>
      </div>

      {sorted.map((rival) => {
        const percent = Math.round(Number(rival.participation || 0) * 100);
        return (
          <div className="rival-model-row" key={rival.name}>
            <strong title={rival.name}>{rival.name}</strong>
            <div className="rival-bar">
              <div
                className={rival.never_bids ? "rival-bar-fill never" : "rival-bar-fill"}
                style={{ width: `${Math.max(percent, rival.never_bids ? 100 : 2)}%` }}
              />
              <em>{rival.never_bids ? "nunca" : `${percent}%`}</em>
            </div>
            <b>{formatMoney(rival.capacity)}</b>
          </div>
        );
      })}
    </div>
  );
}

export default function AcquisitionPanel({ data, full = false }) {
  const acquisition = data.acquisition || {};
  const pointsMarket = data.pointsMarket || {};
  const [showAll, setShowAll] = useState(false);

  if (!acquisition.available) {
    return (
      <Card>
        <CardHeader><CardTitle>OBJETIVOS DE FICHAJE</CardTitle></CardHeader>
        <div className="empty-state">
          Bordalás no ha valorado el mercado en este ciclo.
        </div>
      </Card>
    );
  }

  const targets = acquisition.targets || [];
  const biddable = targets.filter((t) => t.decision === "BID");
  const visible = showAll || full ? targets : biddable.length ? biddable : targets.slice(0, 4);
  const premium = acquisition.premium_model || {};

  return (
    <Card className="acquisition-card">
      <CardHeader>
        <div>
          <CardTitle>OBJETIVOS DE FICHAJE</CardTitle>
          <p className="section-subtitle">
            {acquisition.market_size} EN EL MERCADO · {acquisition.biddable} PUJABLES
            {pointsMarket.calibrated
              ? ` · UN PUNTO CUESTA ${formatEuros(pointsMarket.rate_median)}`
              : ""}
          </p>
        </div>
        <Badge tone={acquisition.biddable ? "success" : "warning"}>
          {acquisition.biddable ? `${acquisition.biddable} CON PUJA` : "NADA QUE PUJAR"}
        </Badge>
      </CardHeader>

      <div className="target-list">
        {visible.length ? (
          visible.map((target) => <TargetRow key={target.id} target={target} />)
        ) : (
          <div className="empty-state">Ningún jugador supera el filtro.</div>
        )}
      </div>

      {!full && targets.length > visible.length && (
        <button className="ghost-button wide" onClick={() => setShowAll(true)}>
          VER LOS {targets.length} VALORADOS →
        </button>
      )}

      {full && (
        <>
          <div className="model-block">
            <div className="model-block-head">
              <strong>QUIÉN PUJA DE VERDAD</strong>
              <Badge tone={acquisition.ledger_trusted ? "success" : "warning"}>
                COBERTURA {Math.round(Number(acquisition.data_coverage || 0) * 100)}%
              </Badge>
            </div>
            <RivalTable rivals={acquisition.rivals || []} />
            <p className="model-note">
              Poder pagar no es ir a pujar. La participación está medida sobre
              subastas reales, no estimada por el dinero que tiene cada uno.
            </p>
          </div>

          <div className="model-block">
            <div className="model-block-head">
              <strong>CURVA DE PRIMAS</strong>
              <Badge tone={premium.calibrated ? "success" : "warning"}>
                {premium.calibrated ? "CALIBRADA" : "POR DEFECTO"}
              </Badge>
            </div>
            <p className="model-note">{premium.reason}</p>
            <div className="premium-curve">
              {(premium.curve || []).map(([ratio, probability]) => (
                <div className="premium-step" key={ratio}>
                  <em>×{Number(ratio).toFixed(2)}</em>
                  <div className="premium-bar">
                    <div
                      className="premium-bar-fill"
                      style={{ height: `${Math.max(Number(probability) * 100 * 2, 3)}%` }}
                    />
                  </div>
                  <span>{Math.round(Number(probability) * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </Card>
  );
}
