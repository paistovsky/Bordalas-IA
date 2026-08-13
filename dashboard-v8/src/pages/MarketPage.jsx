import { useState } from "react";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import NegotiationsPanel from "../components/NegotiationsPanel";
import SolvencyPanel from "../components/SolvencyPanel";
import SpeculationPanel from "../components/SpeculationPanel";
import { formatMoney } from "../lib/utils";

const TABS = [
  ["overview", "VISIÓN GENERAL"],
  ["computer", "COMPUTER"],
  ["rivals", "RIVALES"],
  ["solvency", "SOLVENCIA"]
];

function ComputerOffers({ data }) {
  return (
    <Card className="market-box">
      <CardHeader>
        <CardTitle>OFERTAS DE COMPUTER</CardTitle>
        <Badge tone="success">{data.offers.length} ACTIVAS</Badge>
      </CardHeader>

      <div className="market-scroll">
        {data.offers.length ? (
          data.offers.map((offer, index) => (
            <div className="market-offer-row" key={index}>
              <div>
                <strong>{(offer.players || []).join(", ") || "Oferta"}</strong>
                <small>{offer.action_label || "Analizada por Bordalás"}</small>
              </div>
              <b>{formatMoney(offer.amount)}</b>
            </div>
          ))
        ) : (
          <div className="empty-state">Sin ofertas nuevas de Computer.</div>
        )}
      </div>
    </Card>
  );
}

function Listings({ data }) {
  const players = data.listings.renew_required || [];

  return (
    <Card className="market-box">
      <CardHeader>
        <CardTitle>JUGADORES EN VENTA</CardTitle>
        <Badge>{players.length} PUBLICADOS</Badge>
      </CardHeader>

      <div className="market-scroll">
        {players.length ? (
          players.map((player) => (
            <div className="market-offer-row" key={player.id || player.name}>
              <div>
                <strong>{player.name}</strong>
                <small>Caduca en {player.hours_to_expiry ?? "—"}h</small>
              </div>
              <b>{formatMoney(player.listed_price)}</b>
            </div>
          ))
        ) : (
          <div className="empty-state">No hay publicaciones críticas.</div>
        )}
      </div>
    </Card>
  );
}

export default function MarketPage({ data }) {
  const [tab, setTab] = useState("overview");

  return (
    <div className="page-stack market-page-v94">
      <div className="market-tabs">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            className={tab === id ? "market-tab active" : "market-tab"}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <>
          <div className="market-dual-layout">
            <div className="market-left-column">
              <ComputerOffers data={data} />
              <Listings data={data} />
              <SpeculationPanel data={data} />
            </div>

            <div className="market-right-column">
              <NegotiationsPanel data={data} />
            </div>
          </div>

          <SolvencyPanel data={data} />
        </>
      )}

      {tab === "computer" && (
        <div className="market-dual-layout">
          <div className="market-left-column">
            <ComputerOffers data={data} />
          </div>
          <div className="market-right-column">
            <Listings data={data} />
          </div>
        </div>
      )}

      {tab === "rivals" && <NegotiationsPanel data={data} />}
      {tab === "solvency" && <SolvencyPanel data={data} />}
    </div>
  );
}
