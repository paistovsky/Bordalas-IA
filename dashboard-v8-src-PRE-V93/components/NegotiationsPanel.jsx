import { Card, CardHeader, CardTitle } from "./ui/Card";
import { Badge } from "./ui/Badge";
import { formatMoney, humanGate, ago } from "../lib/utils";
import PlayerAvatar from "./PlayerAvatar";

function OfferRow({ offer, closed = false }) {
  return (
    <div className={closed ? "negotiation-row closed" : "negotiation-row"}>
      <PlayerAvatar player={offer} className="negotiation-avatar" />
      <div className="negotiation-player">
        <strong>{offer.player_name}</strong>
        <span>→ {offer.rival_name}</span>
      </div>
      <div className="negotiation-metric">
        <span>OFERTA RIVAL</span>
        <b>{formatMoney(offer.amount)}</b>
      </div>
      <div className="negotiation-metric">
        <span>CONTRAOFERTA</span>
        <b>{formatMoney(offer.authoritative_counter_amount || offer.strategic_sell_price)}</b>
      </div>
      <Badge tone={closed ? "danger" : "warning"}>
        {closed ? "RETIRADA POR RIVAL" : humanGate(offer.action_gate)}
      </Badge>
      <small className="negotiation-time">{closed ? ago(offer.closed_at) : ""}</small>
    </div>
  );
}

export default function NegotiationsPanel({ data, compact = false }) {
  const active = data.competitive.offers || [];
  const recent = data.competitive.recentClosed || [];

  return (
    <Card className={compact ? "negotiations compact" : "negotiations"}>
      <CardHeader>
        <CardTitle>NEGOCIACIONES ACTIVAS</CardTitle>
        <Badge tone="success">EN VIVO</Badge>
      </CardHeader>

      <div className="negotiations-list">
        {active.length
          ? active.slice(0, compact ? 3 : 10).map((offer) => (
              <OfferRow key={`a-${offer.player_id}-${offer.rival_name}`} offer={offer} />
            ))
          : <div className="empty-state">No hay negociaciones activas.</div>
        }

        {!compact && recent.length > 0 && (
          <>
            <div className="negotiations-divider">CIERRES RECIENTES · ÚLTIMAS 12H</div>
            {recent.slice(0, 5).map((offer, index) => (
              <OfferRow key={`c-${offer.player_id}-${offer.rival_name}-${index}`} offer={offer} closed />
            ))}
          </>
        )}
      </div>
    </Card>
  );
}
