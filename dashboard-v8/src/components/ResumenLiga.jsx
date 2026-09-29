import {
  SIN_DATO,
  amenazaEnPalabras,
  euros,
  lineasDe,
  porManager,
  recuento
} from "../lib/resumen";

/* LIGA: ¿CÓMO VAN LOS RIVALES? (30/09/2026)
 *
 * La clasificación con lo que importa -puntos, a cuánto están de
 * nosotros y cuánta caja tienen-, quién aprieta más, y lo que ha
 * movido cada uno en el tablón de hoy.
 *
 * La caja de los rivales es una reconstrucción (la liga la tiene
 * oculta); su cuadre se vigila en DIAGNÓSTICO, en AUDITORÍA.
 */

export default function ResumenLiga({ data }) {
  const tabla = [...(data.competition?.standings || [])].sort(
    (a, b) => Number(a.rank) - Number(b.rank)
  );
  const intel = new Map(
    (data.rivalIntel?.managers || []).map((m) => [m.name, m])
  );
  const yo = tabla.find((f) => f.is_current_user);
  const misPuntos = yo ? Number(yo.points || 0) : null;

  const peligro = tabla
    .filter((f) => !f.is_current_user)
    .map((f) => ({ f, m: intel.get(f.name) || {} }))
    .filter(({ m }) => m.threat_score != null)
    .sort((a, b) => Number(b.m.threat_score) - Number(a.m.threat_score))[0];

  return (
    <div className="resumen">
      <section className="pan rs-card">
        <h2>LA CLASIFICACIÓN</h2>
        {!tabla.length ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : (
          <ul className="rs-clasif">
            {tabla.map((f) => {
              const m = intel.get(f.name) || {};
              const dif = misPuntos != null ? Number(f.points || 0) - misPuntos : null;
              return (
                <li key={f.user_id || f.name} className={f.is_current_user ? "nos" : ""}>
                  <span className="rs-pos">{f.rank}º</span>
                  <span className="rs-quien">
                    {f.is_current_user ? "Nosotros" : f.name}
                    <small>
                      {f.is_current_user
                        ? "Pepe Bordalás"
                        : dif == null
                        ? ""
                        : dif > 0
                        ? `nos saca ${dif}`
                        : dif < 0
                        ? `le sacamos ${-dif}`
                        : "empatados"}
                    </small>
                  </span>
                  <span className="rs-pts">
                    {f.points}
                    <small>pts</small>
                  </span>
                  <span className="rs-caja">
                    {m.balance != null ? euros(m.balance) : SIN_DATO}
                    <small>caja</small>
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="pan rs-card">
        <h2>QUIÉN APRIETA MÁS</h2>
        {peligro ? (
          <p className="rs-frase">
            <b>{peligro.f.name}</b>: amenaza {amenazaEnPalabras(peligro.m.threat_level)}.
            Tiene {euros(peligro.m.balance)} en caja y puede pujar hasta{" "}
            {euros(peligro.m.maximum_bid)}.
          </p>
        ) : (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        )}
      </section>

      <section className="pan rs-card">
        <h2>LO QUE HAN MOVIDO HOY</h2>
        {!data.tablon ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : (
          (() => {
            const conMovimientos = tabla
              .filter((f) => !f.is_current_user)
              .map((f) => ({ f, lineas: lineasDe(data.tablon, f.name) }))
              .filter((x) => x.lineas.length);
            return conMovimientos.length ? (
              <ul className="rs-movs">
                {conMovimientos.map(({ f, lineas }) => (
                  <li key={f.name}>
                    <b>{f.name}</b>
                    {lineas.map((l, i) => (
                      <span key={i}>
                        <small className="rs-hora">{l.hora}</small>{" "}
                        {String(l.texto).replace(`${f.name} `, "")}
                      </span>
                    ))}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="rs-frase">Ningún rival ha movido ficha en las últimas 24 horas.</p>
            );
          })()
        )}
      </section>

      {/* LA SEMANA DE CADA RIVAL (30/09/2026). `tablon_semana` es
          el tablón a 168 h. Un plegable por mánager, con cuántos
          fichajes y ventas lleva; sin la clave, no se pinta. */}
      {data.tablonSemana && (
        <section className="pan rs-card">
          <h2>LO QUE HA MOVIDO CADA RIVAL ESTA SEMANA</h2>
          {(() => {
            const rivales = tabla.filter((f) => !f.is_current_user).map((f) => f.name);
            const grupos = porManager(data.tablonSemana, rivales);
            const conAlgo = rivales.filter((n) => grupos.get(n).length);
            if (!conAlgo.length) {
              return (
                <p className="rs-frase">
                  Ningún rival ha movido ficha en los últimos 7 días.
                </p>
              );
            }
            return (
              <div className="rs-semana">
                {rivales.map((n) => {
                  const lineas = grupos.get(n);
                  const { fichajes, ventas } = recuento(lineas);
                  return (
                    <details key={n} className="rs-rival">
                      <summary>
                        <b>{n}</b>
                        <span>
                          {lineas.length
                            ? `${fichajes} fichaje${fichajes === 1 ? "" : "s"} · ${ventas} venta${ventas === 1 ? "" : "s"}`
                            : "nada esta semana"}
                        </span>
                      </summary>
                      {lineas.length > 0 && (
                        <ul>
                          {lineas.map((l, i) => (
                            <li key={i}>
                              <small className="rs-hora">{l.hora}</small>{" "}
                              {String(l.texto).replace(`${n} `, "")}
                            </li>
                          ))}
                        </ul>
                      )}
                    </details>
                  );
                })}
              </div>
            );
          })()}
        </section>
      )}
    </div>
  );
}
