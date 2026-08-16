import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

const DECISION = {
  BID: ["ok", "PUJAR"],
  NO_COMPENSA: ["warn", "NO COMPENSA"],
  NO_DISPONIBLE: ["crit", "NO DISPONIBLE"],
  SIN_VALOR: ["idle", "SIN VALOR"]
};

/**
 * Dos columnas, no una.
 *
 * "PUJAMOS" ensenaba la puja RECOMENDADA y se leia como "tenemos
 * una puja puesta". Con tres pujas vivas en Biwenger por
 * 3.126.002 EUR, la tabla decia "0 CON PUJA" y guiones en toda
 * la columna. El contador de la caja si las veia; esta tabla no
 * recibia el dato.
 *
 * Ahora PUESTO es el hecho -lo que hay comprometido ahora mismo-
 * y PUJARIAMOS es la recomendacion.
 */

// Mismos cortes que el consenso multifuente (>=67 titular,
// <=40 suplente). Si la pantalla usara otros, un candidato
// podria salir verde y estar contado como suplente al decidir.
function STARTER_TONE(probability) {
  if (probability == null) return "dim";
  const n = Number(probability);
  if (n >= 67) return "up";
  if (n > 40) return "warn-text";
  return "down";
}

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

      {/* Un plazo para actuar que estaba en los datos y no se
          pintaba en ninguna parte. Publicar despues del reset
          es publicar un dia tarde. */}
      <div className="kv">
        <span>Hay que publicar antes del reset</span>
        <b className={clock.must_publish_before_reset ? "down" : "dim"}>
          {clock.must_publish_before_reset ? "SÍ" : "no hace falta"}
        </b>
      </div>

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

function TargetsPanel({ acquisition, pointsMarket, exposure = {} }) {
  if (!acquisition?.available) {
    return (
      <section className="pan">
        <h2>OBJETIVOS DE HOY</h2>
        <div className="empty">Bordalás no ha valorado el mercado en este ciclo.</div>
      </section>
    );
  }

  const objetivos = acquisition.targets || [];

  // Contado sobre las filas que se estan pintando, no sobre un
  // resumen aparte. Si la tabla no lo ensena, no cuenta.
  const conPuja = objetivos.filter(
    (t) => Number(t.live_bid || 0) > 0
  );

  const vivas = conPuja.length;
  const comprometido = conPuja.reduce(
    (total, t) => total + Number(t.live_bid || 0),
    0
  );

  const porPujar = objetivos.filter(
    (t) => t.decision === "BID" && !(Number(t.live_bid || 0) > 0)
  ).length;

  // El dashboard tiene que cazarse a si mismo.
  //
  // La caja lee las pujas del snapshot; esta tabla las cruza con
  // el mercado del Computer. Si los dos numeros no coinciden hay
  // dinero comprometido que esta pantalla no esta mostrando, y
  // eso hay que decirlo en vez de ensenar el numero bonito.
  const descuadre =
    exposure?.operation_count != null &&
    Number(exposure.operation_count) !== vivas;

  const cobertura = acquisition.starter_coverage || {};

  // Con cero pronósticos, la regla del once bloquea todas las
  // mejoras y "0 POR PUJAR" parecería que no hay chollos. No es
  // eso: es que falta el dato para poder juzgarlos.
  const sinPronostico =
    Number(cobertura.total || 0) > 0 &&
    Number(cobertura.with_forecast || 0) === 0;

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
            {cobertura.total
              ? ` · ${cobertura.with_forecast}/${cobertura.total} con pronóstico de titular`
              : ""}
          </div>
        </div>
        <div className="pill-row">
          {vivas > 0 && (
            <span className="pill live">
              {vivas} PUJA{vivas === 1 ? "" : "S"} VIVA
              {vivas === 1 ? "" : "S"} · {formatMoney(comprometido)}
            </span>
          )}
          <span className={porPujar ? "pill ok" : "pill idle"}>
            {porPujar} POR PUJAR
          </span>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th></th>
            <th className="n">MERCADO</th>
            <th className="n">TIT.</th>
            <th className="n">VALE PARA NOSOTROS</th>
            <th className="n">PUESTO</th>
            <th className="n">PUJARÍAMOS</th>
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
            const viva = Number(target.live_bid || 0) > 0;

            return (
              <tr
                key={target.id}
                className={viva ? "live" : bids ? "" : "off"}
                title={
                  [target.xi_reason, target.reason]
                    .filter(Boolean)
                    .join("  —  ") || undefined
                }
              >
                <td>{target.name}</td>
                <td className="dim">{positionLabel(target.position)}</td>
                <td className="n">{formatEuros(target.market_price)}</td>

                {/* La respuesta a "¿cómo es eso mejorar el XI?".
                    Un candidato con más puntos que el nuestro
                    puede ser suplente, y hasta ahora eso no se
                    veía en ninguna columna. */}
                <td className={`n ${STARTER_TONE(target.starter_probability)}`}>
                  {target.starter_probability != null
                    ? `${Math.round(Number(target.starter_probability))}%`
                    : <span className="dim">sin dato</span>}
                </td>

                <td className="n">{formatEuros(target.our_value)}</td>
                <td className="n strong">
                  {viva ? formatEuros(target.live_bid) : "—"}
                </td>
                <td className="n">{bids ? formatEuros(target.bid) : "—"}</td>
                <td className="n">
                  {target.win_probability != null
                    ? `${Math.round(target.win_probability * 100)}%`
                    : "—"}
                </td>
                <td className="dim">{target.intent || "—"}</td>
                <td className="dim">{target.replaces || "—"}</td>
                <td>
                  {viva ? (
                    <span className="pill live">PUJA PUESTA</span>
                  ) : (
                    <span className={`pill ${tone}`}>{label}</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {sinPronostico && (
        <div className="alert warn" style={{ marginTop: 10 }}>
          Ningún candidato del mercado tiene pronóstico de titularidad, así que
          la regla del once bloquea las {cobertura.blocked_by_starter_rule ?? 0}{" "}
          mejoras que había. No es que no haya chollos: es que falta el dato
          para juzgarlos. Revisa el refresco de Jornada Perfecta.
        </div>
      )}

      {descuadre && (
        <div className="alert warn" style={{ marginTop: 10 }}>
          La caja dice {exposure.operation_count} puja(s) viva(s) y esta tabla
          encuentra {vivas}. Alguna puja es de un jugador que ya no está en el
          mercado del Computer. No se decide nada con esta tabla hasta que
          cuadren.
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        <b>PUESTO</b> es lo que ya hay comprometido en Biwenger ahora mismo.{" "}
        <b>PUJARÍAMOS</b> es lo que el modelo recomienda si no hubiera puja.
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

      <TargetsPanel
        acquisition={data.acquisition}
        pointsMarket={data.pointsMarket}
        exposure={data.exposure}
      />

      <div style={{ marginTop: 11 }}>
        <OffersPanel offers={data.offers || []} />
      </div>
    </>
  );
}
