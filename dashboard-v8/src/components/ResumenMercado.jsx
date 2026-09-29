import { SIN_DATO, euros, lineasDe, num, variacion } from "../lib/resumen";

/* MERCADO: ¿QUÉ ESTÁ HACIENDO PEPE CON EL DINERO? (30/09/2026)
 *
 * Cuatro respuestas, en este orden:
 *
 *   1. Por quién está pujando, cuánto y cuándo se sabe.
 *   2. Lo nuestro a la venta, con la mejor oferta que hay.
 *   3. Lo último que ha comprado o vendido.
 *   4. Qué está subiendo en el mercado ahora.
 *
 * Todo sale de status.json. Lo que falta se dice: hoy no se
 * publica cuánto se ganó o perdió en cada venta.
 */

const DE_QUIEN = { libre: "libre", rival: "de un rival", nuestro: "nuestro" };

export default function ResumenMercado({ data }) {
  const summary = data.summary || {};
  const acquisition = data.acquisition || {};
  const reloj = data.marketClock || {};

  const vivas = (acquisition.targets || []).filter(
    (t) => Number(t.live_bid || 0) > 0
  );

  const cuando = reloj.next_reset_local
    ? `el ${String(reloj.next_reset_local).replace(" ", " a las ")}`
    : "en el próximo reset, a las 07:00";

  const venta = data.loNuestroALaVenta || {};
  const conOferta = (venta.players || [])
    .filter((p) => num(p.nos_ofrecen) != null)
    .sort((a, b) => Number(b.nos_ofrecen) - Number(a.nos_ofrecen));

  const nuestras = lineasDe(data.tablon, "Pepe Bordalás");

  const liga = data.todaLaLiga || {};
  const suben = (liga.players || [])
    .filter((p) => Number(p.price_increment || 0) > 0)
    .sort((a, b) => Number(b.price_increment) - Number(a.price_increment))
    .slice(0, 5);

  return (
    <div className="resumen">
      <section className="pan rs-card">
        <div className="rs-duo">
          <div>
            <div className="rs-lbl">En caja</div>
            <div className="rs-big">{euros(summary.balance)}</div>
          </div>
          <div>
            <div className="rs-lbl">Lo máximo que se puede pujar</div>
            <div className="rs-mid">{euros(summary.maximum_bid)}</div>
          </div>
        </div>
      </section>

      <section className="pan rs-card">
        <h2>PUJAS EN JUEGO</h2>
        {!acquisition.available ? (
          <p className="rs-frase dim">Pujas: {SIN_DATO}.</p>
        ) : vivas.length ? (
          <>
            <ul className="rs-lista">
              {vivas.map((t) => (
                <li key={t.id || t.name}>
                  <span>
                    {t.name}
                    <small>{t.seller_name ? `se lo compramos a ${t.seller_name}` : "al mercado"}</small>
                  </span>
                  <b>{euros(t.live_bid)}</b>
                </li>
              ))}
            </ul>
            <p className="rs-frase dim">Se sabe si las ganamos {cuando}.</p>
          </>
        ) : (
          <p className="rs-frase">Ninguna puja puesta ahora mismo.</p>
        )}
      </section>

      <section className="pan rs-card">
        <h2>LO NUESTRO A LA VENTA</h2>
        {!venta.available ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : (
          <>
            <p className="rs-frase">
              <b>{venta.publicados ?? 0}</b> publicados ·{" "}
              <b>{venta.con_oferta ?? conOferta.length}</b> con oferta.
            </p>
            {conOferta.length > 0 && (
              <ul className="rs-lista">
                {conOferta.slice(0, 6).map((p) => (
                  <li key={p.id || p.name}>
                    <span>
                      {p.name}
                      <small>
                        pedimos {euros(p.lo_que_pedimos)}
                        {p.de_quien_es_la_oferta ? ` · oferta de ${p.de_quien_es_la_oferta}` : ""}
                      </small>
                    </span>
                    <b>{euros(p.nos_ofrecen)}</b>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>

      <section className="pan rs-card">
        <h2>LO ÚLTIMO QUE HA HECHO</h2>
        {!data.tablon ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : nuestras.length ? (
          <ul className="rs-lista rs-lineas">
            {nuestras.map((l, i) => (
              <li key={i}>
                <small className="rs-hora">{l.hora}</small>
                <span>{String(l.texto).replace(/^Pepe Bordalás /, "")}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rs-frase">Ni compras ni ventas en las últimas 24 horas.</p>
        )}
        <p className="rs-frase dim">Lo ganado o perdido en cada venta: {SIN_DATO}.</p>
      </section>

      <section className="pan rs-card">
        <h2>LO QUE MÁS SUBE HOY</h2>
        {!liga.available ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : suben.length ? (
          <ul className="rs-lista">
            {suben.map((p) => (
              <li key={p.id || p.name}>
                <span>
                  {p.name}
                  <small>
                    vale {euros(p.price)} · {DE_QUIEN[p.de_quien] || p.de_quien || ""}
                  </small>
                </span>
                <b className="up">{variacion(p.price_increment)}</b>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rs-frase">Hoy no sube nadie.</p>
        )}
      </section>
    </div>
  );
}
