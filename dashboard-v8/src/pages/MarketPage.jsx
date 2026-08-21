import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

/* POR QUE UN "CLAVE" SALE SIN VALOR (21/08/2026)
 *
 *   "Ya veo a Sergio Herrera. Me dice clave y sin valorar. ¿Por?"
 *
 *   SIN VALOR no quiere decir que el jugador sea malo: quiere
 *   decir que no vale NADA PARA NOSOTROS, casi siempre porque esa
 *   posicion ya esta cubierta mejor de lo que el la cubriria.
 *
 *   El motivo se calculaba y viajaba en `xi_decision`, y solo se
 *   veia pasando el raton por la fila. Un motivo que hay que
 *   cazar con el raton es un motivo que nadie lee.
 */
const MOTIVO_DEL_ONCE = {
  MEJORA_INSUFICIENTE: "no mejora lo bastante el XI",
  NO_SE_TOCA_UN_DIOS: "no se toca a un Dios",
  PIERDE_TITULARIDAD: "jugaría menos que el que sale",
  NO_MEJORA_TITULARIDAD: "no mejora la titularidad",
  NO_MEJORA_JERARQUIA: "no mejora la jerarquía",
  SIN_PRONOSTICO: "sin pronóstico de titular",
  SIN_HUECO: "no hay hueco en su posición"
};

const DECISION = {
  BID: ["ok", "PUJAR"],
  NO_COMPENSA: ["warn", "NO COMPENSA"],
  NO_DISPONIBLE: ["crit", "NO DISPONIBLE"],
  SIN_VALOR: ["idle", "SIN VALOR"],

  // Dinero nuestro puesto fuera del mercado del Computer. Se
  // enseña porque es nuestro; no se persigue porque Pepe no
  // compra en las listas de los rivales.
  PUJA_FUERA_DEL_COMPUTER: ["live", "FUERA DEL COMPUTER"]
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

/**
 * La jerarquia, que es el dato que aguanta.
 *
 * El % dice quien juega ESTE sabado y cambia cada semana. La
 * jerarquia dice que ES un jugador en su equipo y dura toda la
 * temporada. Se ficha para meses, asi que esta columna pesa mas
 * que la de al lado aunque ocupe menos.
 *
 * El escalon de arriba -Dios- se pinta distinto porque no es un
 * Clave mejor: es el fichaje franquicia, otra categoria.
 */
const HIERARCHY_TONE = {
  DIOS: "me",
  CLAVE: "ok",
  IMPORTANTE: "ok",
  ROTACIÓN: "warn",
  ROTACION: "warn",
  REVULSIVO: "idle",
  RESERVA: "idle",
  DESCARTE: "crit"
};

function Hierarchy({ label }) {
  if (!label) return <span className="dim">—</span>;

  const tone = HIERARCHY_TONE[String(label).toUpperCase()] || "idle";

  return <span className={`pill ${tone}`}>{String(label).toUpperCase()}</span>;
}

/**
 * Sin dato no es lo mismo que disponible: solo se dice algo
 * cuando hay algo que decir.
 */
function estadoFisico(target) {
  const estado = target.availability;

  if (!estado || estado === "DISPONIBLE") return null;

  const fuera = target.absence?.matchdays_out;

  if (fuera) {
    return `${estado} · se pierde ${fuera} jornada${fuera === 1 ? "" : "s"}`;
  }

  return estado;
}

/* LESION Y SANCION SON DOS COSAS (19/08/2026)
 *
 * Iban las dos en una linea gris debajo de la jerarquia, y solo
 * sobrevivia la mas larga. Pero decidir con ellas es distinto:
 * un ligamento roto es motivo de venta, dos partidos de sancion
 * no lo son. Ahora cada una tiene su columna y su detalle.
 *
 * `merge_absences` guarda las dos fichas enteras desde hoy. Lo
 * que se lee aqui ya venia de FutbolFantasy y se tiraba por el
 * camino: el tipo de lesion, el pronostico en palabras, si la
 * roja fue directa o por acumulacion, cuantos partidos van
 * cumplidos.
 */

function jornadas(n) {
  if (n == null) return null;
  if (n === 0) return "vuelve ya";
  return `${n} jornada${n === 1 ? "" : "s"}`;
}

function Lesion({ absence, availability }) {
  const parte = absence?.injury;

  if (!parte) {
    // Tocado sin parte detallado: se dice, no se calla.
    if (availability === "DUDA") {
      return <span className="pill warn">DUDA</span>;
    }
    return <span className="dim">—</span>;
  }

  const fuera = jornadas(parte.matchdays_out);

  const grave =
    Number(parte.matchdays_out || 0) >= 4 ||
    parte.severity_label === "GRAVE";

  return (
    <div>
      <span className={grave ? "pill crit" : "pill warn"}>
        {parte.detail || "LESIONADO"}
      </span>

      {(parte.prognosis || fuera) && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {[parte.prognosis, fuera].filter(Boolean).join(" · ")}
        </div>
      )}
    </div>
  );
}

function Sancion({ absence }) {
  const parte = absence?.suspension;

  if (!parte) return <span className="dim">—</span>;

  const partidos =
    parte.matches_total != null
      ? `${parte.matches_served ?? 0} de ${parte.matches_total} cumplidos`
      : jornadas(parte.matchdays_out);

  return (
    <div>
      <span className="pill crit">{parte.detail || "SANCIONADO"}</span>

      {partidos && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {partidos}
          {parte.basis === "SUPUESTO" ? " · estimado" : ""}
        </div>
      )}
    </div>
  );
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

  /* EL BOLSILLO QUE MANDA AQUI (21/08/2026)
   *
   *   Este panel enseñaba el presupuesto de ESPECULAR: 15 % de la
   *   caja y 60 % del margen de deuda. Debajo de una tabla de
   *   fichajes.
   *
   *   Esa misma noche Pepe puso una puja de 2,08 M -con el de
   *   fichar, que es el que decide- y este panel seguia diciendo
   *   "Libre 0 €" porque 2,08 M ya se pasaba del techo de
   *   apostar. El numero de al lado contradecia lo que el bot
   *   acababa de hacer.
   *
   *   Manda el de fichar. El de especular se queda debajo, con su
   *   nombre puesto. */
  const fichajes = exposure.acquisition || {};
  const hayFichajes = Boolean(fichajes.available);

  const bolsillo = hayFichajes ? fichajes : exposure;

  const cash = Number(bolsillo.cash_budget || 0);
  const debt = Number(bolsillo.debt_budget || 0);
  const committed = Number(exposure.committed_total || 0);

  /* El bruto, no el autorizado.
   *
   *   El denominador era `total_budget`, que ya viene con lo
   *   comprometido descontado, y ademas se pintaba lo
   *   comprometido como un tramo mas. La barra sumaba mas del
   *   100 % y salia llena siempre. */
  const bruto = Math.max(cash + debt, 1);

  const ancho = (valor) =>
    `${Math.min((Math.max(valor, 0) / bruto) * 100, 100)}%`;

  const libre = Number(
    bolsillo.available_budget ?? Math.max(bruto - committed, 0)
  );

  return (
    <section className="pan">
      <h2>CAJA</h2>
      <div className="sub">
        {hayFichajes
          ? "De dónde sale lo que puede gastar en fichar"
          : "De dónde sale lo que puede gastar"}
      </div>

      <div className="bar">
        <i style={{ width: ancho(cash), background: "#22c55e" }} />
        <i style={{ width: ancho(debt), background: "#3b82f6" }} />
      </div>
      <div className="legend">
        <span style={{ color: "#22c55e" }}>caja {formatMoney(cash)}</span>
        <span style={{ color: "#3b82f6" }}>
          deuda segura {formatMoney(debt)}
        </span>
      </div>

      <div className="kv" style={{ marginTop: 8 }}>
        <span>Pujas vivas</span><b className="mono">{exposure.operation_count || 0}</b>
      </div>
      <div className="kv">
        <span>Comprometido</span>
        <b className="mono">{formatEuros(committed)}</b>
      </div>
      <div className="kv">
        <span>Libre para fichar</span>
        <b className="mono up">{formatEuros(libre)}</b>
      </div>

      {hayFichajes && (
        <>
          <div className="kv">
            <span>Libre para especular</span>
            <b className="mono">
              {formatEuros(exposure.available_budget)}
            </b>
          </div>

          {fichajes.capped_by_biwenger && (
            <div className="kv">
              <span>Techo de Biwenger</span>
              <b className="mono">
                {formatEuros(fichajes.maximum_bid)}
              </b>
            </div>
          )}
        </>
      )}
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

  /* UN TOPE QUE NO SE ANUNCIA ES UNA MENTIRA POR OMISION
     (21/08/2026)

     La cabecera decia "20 VALORADOS" y la tabla enseñaba doce.
     Los otros ocho estaban valorados y ordenados, y se caian en
     la ultima linea antes de la pantalla. El dueño lo descubrio
     comparando el mercado de Biwenger a mano.

     Ahora caben todos; pero si algun dia vuelve a recortar, se
     dice. */
  const recortados = Number(acquisition.hidden || 0);

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
            {acquisition.shown != null
              ? `${acquisition.shown} en la tabla · `
              : ""}
            {pointsMarket?.calibrated
              ? `un punto cuesta ${formatEuros(pointsMarket.rate_median)} y abona 30.000 €`
              : "un punto abona 30.000 €"}
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
            <th>EQUIPO</th>
            <th className="n">MERCADO</th>
            <th className="n">TIT.</th>
            <th>JERARQUÍA</th>
            <th>LESIÓN</th>
            <th>SANCIÓN</th>
            <th className="n">VALE PARA NOSOTROS</th>
            <th className="n">SE PAGA SOLO</th>
            <th>VENDE</th>
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
                /* TODO EL PORQUE, EN UN SOLO SITIO (21/08/2026)
                   Las letras pequeñas debajo de cada etiqueta
                   convertian la tabla en una pared de gris. El
                   detalle vive aqui, en el recuadro que sale al
                   pasar el raton por la fila. */
                title={
                  [
                    MOTIVO_DEL_ONCE[target.xi_decision],
                    estadoFisico(target),
                    target.xi_reason,
                    target.reason
                  ]
                    .filter(Boolean)
                    .join("  —  ") || undefined
                }
              >
                <td>{target.name}</td>
                <td className="dim">{positionLabel(target.position)}</td>
                <td className="dim">{target.team || "—"}</td>
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

                {/* Lo estructural, al lado de lo semanal. Un
                    Reserva al 70 % esta semana sigue siendo un
                    Reserva, y esta columna es la que lo dice.

                    La linea de estado fisico que colgaba de aqui
                    se ha ido a sus dos columnas propias. */}
                <td>
                  <Hierarchy label={target.hierarchy} />
                </td>

                <td>
                  <Lesion
                    absence={target.absence}
                    availability={target.availability}
                  />
                </td>

                <td>
                  <Sancion absence={target.absence} />
                </td>

                <td className="n">{formatEuros(target.our_value)}</td>

                {/* LO QUE EL FICHAJE DEVUELVE EN CAJA (21/08/2026)

                    Biwenger abona 30.000 € por punto al cerrar
                    cada jornada. La columna MERCADO dice si algo
                    está caro comparado con otros; ésta dice si se
                    paga solo.

                    Un punto es un punto: da igual en qué jornada
                    llegue, paga lo mismo. Por eso el coste por
                    punto y el abono son comparables sin inventar
                    horizontes. */}
                <td className="n">
                  {target.pays_for_itself == null ? (
                    <span className="dim">—</span>
                  ) : target.pays_for_itself ? (
                    <span
                      className="pill ok"
                      title={`Cuesta ${formatEuros(target.cost_per_point)} por punto y cada punto abona 30.000 €. Devuelve ${formatEuros(target.abono_return)} solo en abonos.`}
                    >
                      SÍ · {formatEuros(target.abono_return)}
                    </span>
                  ) : (
                    <span
                      className="dim"
                      title={`Cuesta ${formatEuros(target.cost_per_point)} por punto y cada punto abona 30.000 €.`}
                    >
                      no
                    </span>
                  )}
                </td>

                {/* A QUIÉN SE LE COMPRA, CON NOMBRE.
                    "Un rival" no informa de nada: de cada mánager
                    se sabe cuánto suele pagar, así que saber si es
                    Prinzipote o Pollo17 cambia lo que esperas que
                    pase con la puja. */}
                <td className={target.seller_kind === "MANAGER" ? "rival" : "dim"}>
                  {target.seller_name || "Computer"}
                </td>

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

      {recortados > 0 && (
        <div className="alert warn">
          Esta tabla enseña {acquisition.shown} de{" "}
          {acquisition.valued} jugadores valorados.{" "}
          <b>{recortados} se quedan fuera</b> por el tope de la lista, no
          porque Pepe no los haya mirado.
        </div>
      )}

      {sinPronostico && (
        <div className="alert warn" style={{ marginTop: 10 }}>
          Ningún candidato del mercado tiene pronóstico de titularidad, así que
          la regla del once bloquea las {cobertura.blocked_by_starter_rule ?? 0}{" "}
          mejoras que había. No es que no haya chollos: es que falta el dato
          para juzgarlos. Revisa el refresco de FutbolFantasy.
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
