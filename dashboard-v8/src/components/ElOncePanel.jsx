import { formatMoney } from "../lib/utils";

/**
 * EL ONCE (17/09/2026)
 *
 *   Cuatro noches empujando hacia "sube patrimonio o no ganamos".
 *   El árbitro tumbó la tesis: el valor de plantilla no explica
 *   los puntos en esta liga.
 *
 *   Lo que gana son los puntos, y los puntos los marcan once
 *   jugadores. La distancia al líder son 13 puntos en 35
 *   jornadas: cuatro décimas por jornada. Si el once deja más
 *   que eso sentado, la liga está aquí y no en el mercado.
 *
 * LA ADVERTENCIA VA PEGADA A LA CIFRA
 *
 *   La brecha de plantilla se recalcula sola y ya dice lo que
 *   toca. Lo que faltaba era que, al lado, pusiera que esa cifra
 *   no predice los puntos. Que nadie —empezando por quien pide
 *   los encargos— vuelva a montar una estrategia encima de ella.
 *
 * NO DECIDE NADA
 */

const POSICION = { 1: "PT", 2: "DF", 3: "MC", 4: "DL" };

const coma = (n, d = 2) =>
  n == null ? "—" : String(Number(n).toFixed(d)).replace(".", ",");

export default function ElOncePanel({ data }) {
  const once = data.once || { available: false };

  if (!once.available) {
    return (
      <section className="pan">
        <h2>EL ONCE</h2>
        <div className="empty">
          {once.reason || "Sin medición del once."}
        </div>
      </section>
    );
  }

  const banquillo = once.bench || { available: false };
  const sesgo = once.position_bias || { available: false };
  const rival = once.rival || { available: false };
  const aviso = once.value_warning || { available: false };

  const cuentan = banquillo.jornadas_que_cuentan || 0;

  /* La cifra grande: la estricta si la hay, y si no la
     indicativa, que es la única evidencia que existe. Nunca las
     dos mezcladas. */
  const sentados = cuentan
    ? banquillo.puntos_perdidos_por_jornada
    : banquillo.puntos_perdidos_casi_por_jornada;

  const estricta = cuentan > 0;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>PUNTOS EN EL BANQUILLO</h2>
          <div className="sub">
            Lo que costó no alinear el mejor once posible
          </div>
        </div>
        <span className="pill idle">NO DECIDE</span>
      </div>

      {/* LA ALARMA MAS IMPORTANTE DEL TABLERO, SI CRECE */}
      <div className="kv">
        <span>Puntos sentados por jornada</span>
        <b className={sentados ? "mono down" : "mono"}>
          {sentados == null ? "sin medir" : coma(sentados)}
          {!estricta && sentados != null && " (indicativo)"}
        </b>
      </div>

      <div className="kv">
        <span>Lo que hace falta para alcanzar al líder</span>
        <b className="mono">
          {coma(banquillo.ritmo_necesario, 3)} por jornada ·{" "}
          {banquillo.distancia_al_lider ?? "—"} puntos de distancia
        </b>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        {banquillo.veredicto}
      </p>

      {/* JORNADA A JORNADA, CON EL MOTIVO DE LA QUE NO CUENTA.
          Media medición honesta vale; una entera inventada, no. */}
      <table>
        <thead>
          <tr>
            <th>JORNADA</th>
            <th className="n">ALINEÓ</th>
            <th className="n">PODÍA</th>
            <th className="n">SENTADOS</th>
            <th className="n">%</th>
            <th>ESTADO</th>
          </tr>
        </thead>
        <tbody>
          {(banquillo.jornadas || []).map((j) => (
            <tr key={j.round_id}>
              <td className="dim">J{j.round_id}</td>
              <td className="n">
                {j.puntos_once ?? "—"}
                {j.formacion && (
                  <span className="dim"> {j.formacion}</span>
                )}
              </td>
              <td className="n">
                {j.mejor_puntos ?? "—"}
                {j.mejor_formacion && (
                  <span className="dim"> {j.mejor_formacion}</span>
                )}
              </td>
              <td className={j.puntos_perdidos ? "n down" : "n"}>
                {j.puntos_perdidos ?? "—"}
              </td>
              <td className="n dim">
                {j.eficiencia == null ? "—" : `${coma(j.eficiencia, 1)} %`}
              </td>
              <td className={j.cuenta ? "up" : "dim"}>
                {j.cuenta
                  ? "cuenta"
                  : j.casi
                  ? `casi (${coma(j.descuadre_percent, 1)} % de descuadre)`
                  : j.motivo}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* QUIEN DEBIO JUGAR: UN NOMBRE SE CORRIGE, UN PORCENTAJE NO */}
      {(banquillo.jornadas || [])
        .filter((j) => (j.cuenta || j.casi) && j.debieron_jugar?.length)
        .map((j) => (
          <div className="kv" key={`fallo-${j.round_id}`}>
            <span>J{j.round_id} · debieron jugar</span>
            <b className="mono">
              {j.debieron_jugar
                .map((p) => `${p.name} (${POSICION[p.position] || "?"}, ${p.points})`)
                .join(", ")}
              {" — en su lugar jugaron "}
              {j.jugaron_y_no_debian
                .map((p) => `${p.name} (${POSICION[p.position] || "?"}, ${p.points})`)
                .join(", ")}
            </b>
          </div>
        ))}

      {/* ============================================================
          LA VARA CON LA QUE SE ORDENA EL ONCE
          ============================================================ */}
      {sesgo.available && (
        <>
          <div className="sub" style={{ marginTop: 12 }}>
            ¿LA VARA MIDE IGUAL EN LAS CUATRO POSICIONES?
          </div>

          <table>
            <thead>
              <tr>
                <th>POSICIÓN</th>
                <th className="n">N</th>
                <th className="n">VALOR MEDIO</th>
                <th className="n">PTS/JORNADA</th>
                <th className="n">PTS POR VALOR</th>
                <th className="n">FACTOR QUE HARÍA FALTA</th>
              </tr>
            </thead>
            <tbody>
              {(sesgo.rows || []).map((f) => (
                <tr key={f.position}>
                  <td>{f.name}</td>
                  <td className="n">{f.n}</td>
                  <td className="n dim">{coma(f.expected_mean, 3)}</td>
                  <td className="n">{coma(f.points_per_matchday_mean)}</td>
                  <td className="n">
                    <b>{coma(f.points_per_expected)}</b>
                  </td>
                  <td className="n">
                    {f.enough ? (
                      <span
                        className={
                          f.proposed_factor > 1.05
                            ? "up"
                            : f.proposed_factor < 0.95
                            ? "down"
                            : "dim"
                        }
                      >
                        ×{coma(f.proposed_factor, 3)}
                      </span>
                    ) : (
                      <span className="dim">
                        muestra corta (n&lt;{sesgo.minimum_sample})
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* EL CASO EXACTO DEL DUEÑO: MISMO PORCENTAJE, OTRA POSICION */}
          {sesgo.tie_band?.gap_percent != null && (
            <div className="kv">
              <span>
                Con {coma(sesgo.tie_band.from, 0)}-
                {coma(sesgo.tie_band.to, 0)} % de titularidad
              </span>
              <b className="mono">
                {sesgo.tie_band.rows
                  .map(
                    (f) =>
                      `${f.name} ${coma(f.points_per_matchday_mean)} (n=${f.n})`
                  )
                  .join(" · ")}
                {" — un delantero entrega un "}
                {coma(sesgo.tie_band.gap_percent, 1)} % más que un defensa
              </b>
            </div>
          )}

          <p className="note" style={{ textAlign: "left" }}>
            <b>{sesgo.reason}</b> {sesgo.caveat}{" "}
            <b>Ningún factor está aplicado:</b> el motor sigue ordenando
            el once exactamente igual que ayer.
          </p>
        </>
      )}

      {/* ============================================================
          EL EQUIPO QUE HABIA QUE MIRAR
          ============================================================ */}
      {rival.available && (
        <>
          <div className="sub" style={{ marginTop: 12 }}>
            {rival.rival.name.toUpperCase()} CONTRA NOSOTROS
          </div>

          <table>
            <thead>
              <tr>
                <th></th>
                <th className="n">PTS</th>
                <th className="n">FICHAS</th>
                <th className="n">PLANTILLA</th>
                <th>DIBUJO</th>
                <th className="n">DE MEDIO ARRIBA</th>
                <th className="n">TITULARES FIJOS</th>
              </tr>
            </thead>
            <tbody>
              {[rival.rival, rival.us].map((x) => (
                <tr key={x.name} className={x === rival.us ? "me" : ""}>
                  <td>
                    {x.rank}º {x.name}
                  </td>
                  <td className="n">{x.points}</td>
                  <td className="n">{x.squad_size}</td>
                  <td className="n">{formatMoney(x.team_value)}</td>
                  <td className="mono">{x.formation || "—"}</td>
                  <td className="n">{x.attacking_half}</td>
                  <td className="n">
                    {x.nailed_starters} de {x.nailed_starters_of}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ textAlign: "left" }}>
            {rival.reason} {rival.caveat}
          </p>
        </>
      )}

      {/* ============================================================
          LA ADVERTENCIA, PEGADA A LA CIFRA QUE LA NECESITA
          ============================================================ */}
      {aviso.available && (
        <div className={aviso.significant ? "alert" : "alert warn"}>
          <b>El valor de plantilla no predice los puntos en esta liga.</b>{" "}
          {aviso.reason}
        </div>
      )}
    </section>
  );
}
