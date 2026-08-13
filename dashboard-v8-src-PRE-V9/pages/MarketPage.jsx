import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { formatMoney } from "../lib/utils";
import SolvencyPanel from "../components/SolvencyPanel";
import SpeculationPanel from "../components/SpeculationPanel";

export default function MarketPage({ data }) {
  return (
    <div className="page-stack">
      <div className="three-column">
        <Card>
          <CardHeader><CardTitle>OFERTAS COMPUTER</CardTitle></CardHeader>
          <div className="simple-list">
            {data.offers.length
              ? data.offers.slice(0, 10).map((offer, index) => (
                  <div className="simple-row" key={index}>
                    <strong>{(offer.players || []).join(", ")}</strong>
                    <span>{formatMoney(offer.amount)}</span>
                    <small>{offer.action_label || "—"}</small>
                  </div>
                ))
              : <div className="empty-state">Sin ofertas nuevas.</div>}
          </div>
        </Card>

        <Card>
          <CardHeader><CardTitle>JUGADORES EN VENTA</CardTitle></CardHeader>
          <div className="simple-list">
            {(data.listings.renew_required || []).slice(0, 10).map((player) => (
              <div className="simple-row" key={player.id || player.name}>
                <strong>{player.name}</strong>
                <span>{formatMoney(player.listed_price)}</span>
                <small>{player.hours_to_expiry}h</small>
              </div>
            ))}
          </div>
        </Card>

        <SpeculationPanel data={data} />
      </div>

      <SolvencyPanel data={data} />
    </div>
  );
}
