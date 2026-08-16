import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

const DECISION = {
  BID: ["ok", "PUJAR"],
  NO_COMPENSA: ["warn", "NO COMPENSA"],
  NO_DISPONIBLE: ["crit", "NO DISPONIBLE"],
  SIN_VALOR: ["idle", "SIN VALOR"]
};

function ClockPanel({ clock }) {
  if (!clock?.available) {
    return (
      <section className="pan">
        <h2>RELOJ DEL MERCADO</h2>
        <div className="empty">{clock?.reason || "Sin deducir."}</div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>RELOJ DEL MERCADO</h2>
          <div className="sub">Reset Computer · {clock.next_reset_local}</div>
        </div>
        <span className={clock.window_state === "CRITICAL" ? "pill crit" : clock.window_state === "CLOSING" ? "pill warn" : "pill ok"}>
          {clock.window_state}
        </span>
      </div>

      <div className="kv"><span>Quedan</span><b className="mono">{Number(clock.hours_to_reset).toFixed(2)} h</b></div>
      <div className="kv"><span>Jugadores del Computer</span><b className="mono">{clock.computer_listings}</b></div>
      <div className="kv"><span>Se puede pujar</span><b className={clock.bidding_window_open ? "up" : "down"}>{clock.bidding_window_open ? "SÍ" : "NO"}</b></div>
      <div className="kv"><span>Origen del dato</span><span className="tag">{clock.source}</span></div>

      {clock.listings_stale && (
        <div className="alert warn" style={{ marginTop: 9, marginBottom: 0 }}>
          El snapshot es anterior al último reset: puede traer jugadores que ya
          no existen. No se puja sobre datos caducados.
        </div>
      )}
    </section>
  );
}

function CashPanel({ exposure }) {
  if (!exposure?.available) {
    return (
      <section className="pan">
        <h2>CAJA</h2>
        <div className="empty">{exposure?.reason || "Sin presupuesto calculado."}</div>
      </section>
    );
  }

  const total = Number(exposure.total_budget || 1);
  const cash = Number(exposure.cash_budget || 0);
  const debt = Number(exposure.debt_budget || 0);
  const committed = Number(exposure.committed_total || 0);

  return (
    <section className="pan">
      <h2>CAJA</h2>
      <div className="sub">De dónde sale lo que puede gastar</div>

      <div className="bar">
        <i style={{ width: `${(cash / total) * 100}%`, background: "#22c55e" }} />
        <i style={{ width: `${(debt / total) * 100}%`, background: "#3b82f6" }} />
        <i style={{ width: `${(committed / total) * 100}%`, background: "#eab308" }} />
      </div>
      <div className="legend">
        <span style={{ color: "#22c55e" }}>caja {formatMoney(cash)}</span>
        <span style={{ color: "#3b82f6" }}>deuda segura {formatMoney(debt)}</span>
        <span style={{ color: "#eab308" }}>comprometido {formatMoney(committed)}</span>
      </div>

      <div className="kv" style={{ marginTop: 8 }}>
        <span>Pujas vivas</span><b className="mono">{exposure.operation_count || 0}</b>
      </div>
      <div className="kv">
        <span>Libre</span><b className="mono up">{formatEuros(exposure.available_budget)}</b>
      </div>
    </section>
  );
}

function TargetsPanel({ acquisition, pointsMarket }) {
  if (!acquisition?.available) {
    return (
      <section className="pan">
        <h2>OBJETIVOS DE HOY</h2>
        <div className="empty">Bordalás no ha valorado el mercado en este ciclo.</div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>OBJETIVOS DE HOY</h2>
          <div className="sub">
            {acquisition.market_size} valorados ·{" "}
            {pointsMarket?.calibrated
              ? `un punto cuesta ${formatEuros(pointsMarket.rate_median)}`
              : "precio del punto sin calibrar"}
          </div>
        </div>
        <span className={acquisition.biddable ? "pill ok" : "pill idle"}>
          {acquisition.biddable} CON PUJA
        </span>
      </div>

      <table>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th></th>
            <th className="n">MERCADO</th>
            <th className="n">VALE PARA NOSOTROS</th>
            <th className="n">PUJAMOS</th>
            <th className="n">GANAR</th>
            <th>INTENCIÓN</th>
            <th>SUSTITUYE</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {(acquisition.targets || []).map((target) => {
            const [tone, label] = DECISION[target.decision] || ["idle", target.decision];
            const bids = target.decision === "BID";

            return (
              <tr key={target.id} className={bids ? "" : "off"} title={target.reason}>
                <td>{target.name}</td>
                <td className="dim">{positionLabel(target.position)}</td>
                <td className="n">{formatEuros(target.market_price)}</td>
                <td className="n">{formatEuros(target.our_value)}</td>
                <td className="n strong">{bids ? formatEuros(target.bid) : "—"}</td>
                <td className="n">
                  {target.win_probability != null
                    ? `${Math.round(target.win_probability * 100)}%`
                    : "—"}
                </td>
                <td className="dim">{target.intent || "—"}</td>
                <td className="dim">{target.replaces || "—"}</td>
                <td><span className={`pill ${tone}`}>{label}</span></td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left" }}>
        Pasa el ratón por una fila para ver el porqué completo.
      </p>
    </section>
  );
}

function OffersPanel({ offers }) {
  return (
    <section className="pan">
      <h2>OFERTAS RECIBIDAS</h2>
      <div className="sub">Del Computer y de rivales</div>

      {offers.length ? (
        <table>
          <thead>
            <tr>
              <th>JUGADOR</th>
              <th className="n">IMPORTE</th>
              <th className="n">VS VALOR</th>
              <th className="n">EXPIRA</th>
              <th>ACCIÓN</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer, index) => {
              const premium = Number(offer.premium_percent || 0);
              return (
                <tr key={index}>
                  <td>{(offer.players || []).join(", ") || "—"}</td>
                  <td className="n">{formatEuros(offer.amount)}</td>
                  <td className={premium >= 0 ? "n up" : "n down"}>
                    {premium >= 0 ? "+" : ""}{premium.toFixed(1)}%
                  </td>
                  <td className="n dim">
                    {offer.hours_to_expiry != null ? `${offer.hours_to_expiry}h` : "—"}
                  </td>
                  <td className="dim">{offer.action_label || offer.action || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <div className="empty">Sin ofertas activas.</div>
      )}
    </section>
  );
}

function ListingsPanel({ listings }) {
  const rows = listings?.renew_required || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>NUESTRAS PUBLICACIONES</h2>
          <div className="sub">{listings?.listing_count ?? 0} en el mercado</div>
        </div>
        {rows.length ? <span className="pill warn">{rows.length} POR RENOVAR</span> : null}
      </div>

      {rows.length ? (
        <table>
          <thead>
            <tr><th>JUGADOR</th><th className="n">PRECIO</th><th className="n">CADUCA EN</th></tr>
          </thead>
          <tbody>
            {rows.map((player) => (
              <tr key={player.id || player.name}>
                <td>{player.name}</td>
                <td className="n">{formatEuros(player.listed_price)}</td>
                <td className={Number(player.hours_to_expiry) <= 3 ? "n down" : "n dim"}>
                  {player.hours_to_expiry ?? "—"} h
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty">Ninguna publicación necesita renovarse.</div>
      )}
    </section>
  );
}

export default function MarketPage({ data }) {
  return (
    <>
      <div className="grid g3">
        <ClockPanel clock={data.marketClock} />
        <CashPanel exposure={data.exposure} />
        <ListingsPanel listings={data.listings} />
      </div>

      <TargetsPanel acquisition={data.acquisition} pointsMarket={data.pointsMarket} />

      <div style={{ marginTop: 11 }}>
        <OffersPanel offers={data.offers || []} />
      </div>
    </>
  );
}
