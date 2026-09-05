import { formatMoney } from "../lib/utils";

/**
 * EL OJEADOR (06/09/2026)
 *
 *   Pepe no distingue a un jugador de otro por precio: le da a
 *   Bardeli —que subió un 6 % ayer—, a André Almeida —un 17 %— y
 *   a Nico Guillén —que bajó un 2 %— exactamente el mismo 0,17 %
 *   de rendimiento esperado.
 *
 *   Este panel trae lo que tres webs dicen del precio de cada
 *   jugador, con quién lo dijo pegado al dato.
 *
 * LO QUE NO ES, Y VA ESCRITO ARRIBA
 *
 *   Un pronóstico. Las tres webs publican movimiento OBSERVADO:
 *   sus propias páginas se llaman "subidas y bajadas". Ninguna
 *   publica un porcentaje de confianza.
 *
 *   Se dice en pantalla porque dentro de dos meses nadie se va a
 *   acordar, y "el sistema predijo que subiría" es una frase muy
 *   fácil de decir sobre un dato que solo miraba hacia atrás.
 */

const ACUERDO = {
  UNANIMOUS: ["pill ok", "TODAS"],
  MAJORITY: ["pill warn", "MAYORÍA"],
  SPLIT: ["pill crit", "SIN ACUERDO"],
  SINGLE: ["pill idle", "UNA SOLA"],
  NONE: ["pill idle", "—"]
};

const DIRECCION = {
  UP: ["up", "▲"],
  DOWN: ["down", "▼"],
  FLAT: ["dim", "="]
};

function Direccion({ value, percent }) {
  const [tono, flecha] = DIRECCION[value] || DIRECCION.FLAT;

  return (
    <span className={tono}>
      {flecha}
      {percent != null && (
        <> {String(Number(percent).toFixed(2)).replace(".", ",")} %</>
      )}
    </span>
  );
}

export default function ScoutPanel({ data }) {
  const scout = data.scout || { available: false };

  if (!scout.available) {
    return (
      <section className="pan">
        <h2>EL OJEADOR</h2>
        <div className="empty">
          {scout.reason || "Todavía no hay informe del ojeador."}
        </div>
      </section>
    );
  }

  const fuentes = Object.entries(scout.sources || {});
  const acuerdos = scout.agreement_counts || {};
  const libro = scout.accuracy || { available: false };
  const estudio = scout.divergence || { available: false, horizons: {} };

  return (
    <>
      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>EL OJEADOR</h2>
            <div className="sub">
              Lo que dicen las webs del precio de cada jugador
            </div>
          </div>
          <span className={scout.sources_ok ? "pill ok" : "pill crit"}>
            {scout.sources_ok}/{scout.sources_total} FUENTES
          </span>
        </div>

        {/* Lo primero, y sin letra pequeña. */}
        <div className="alert warn">
          <b>Esto no manda todavía.</b> {scout.caveat}
        </div>

        <table>
          <thead>
            <tr>
              <th>FUENTE</th>
              <th className="n">TRAE</th>
              <th className="n">EMPAREJA</th>
              <th className="n">SIN EMPAREJAR</th>
              <th>ESTADO</th>
            </tr>
          </thead>
          <tbody>
            {fuentes.map(([nombre, fuente]) => (
              <tr key={nombre}>
                <td>{nombre.replaceAll("_", " ")}</td>
                <td className="n dim">{fuente.records || 0}</td>
                <td className="n strong">{fuente.players || 0}</td>
                <td className="n dim">{fuente.unmatched || 0}</td>
                <td>
                  {fuente.ok ? (
                    <span className="pill ok">OK</span>
                  ) : (
                    <span className="pill idle" title={fuente.error}>
                      FUERA
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* El motivo de la que falta, entero y a la vista. Una
            fuente que desaparece se lee como una que nadie pensó. */}
        {fuentes
          .filter(([, fuente]) => !fuente.ok && fuente.error)
          .map(([nombre, fuente]) => (
            <p className="note" style={{ textAlign: "left" }} key={nombre}>
              <b>{nombre.replaceAll("_", " ")}:</b> {fuente.error}
            </p>
          ))}

        <div className="kv" style={{ marginTop: 8 }}>
          <span>Jugadores con señal</span>
          <b className="mono">{scout.players_count}</b>
        </div>
        <div className="kv">
          <span>De acuerdo las tres</span>
          <b className="mono up">{acuerdos.UNANIMOUS || 0}</b>
        </div>
        <div className="kv">
          <span>Solo lo dice una</span>
          <b className="mono">{acuerdos.SINGLE || 0}</b>
        </div>
        <div className="kv">
          <span>Sin emparejar (no se usan)</span>
          <b className="mono down">{scout.unmatched_count}</b>
        </div>
        <div className="kv">
          <span>Filas del tablero con veredicto</span>
          <b className="mono">
            {scout.targets_with_verdict} de {scout.targets_total}
          </b>
        </div>
      </section>

      {/* DONDE SE CONTRADICEN.
          Es lo primero que hay que mirar: el precio subió pero la
          gente está vendiendo, o las fuentes no coinciden. */}
      {(scout.disagreements || []).length > 0 && (
        <section className="pan" style={{ marginTop: 11 }}>
          <div className="pan-head">
            <div>
              <h2>DONDE NO CUADRA</h2>
              <div className="sub">
                El movimiento del precio y la demanda apuntan a lados
                distintos
              </div>
            </div>
            <span className="pill warn">{scout.disagreements_count}</span>
          </div>

          <table>
            <thead>
              <tr>
                <th>JUGADOR</th>
                <th className="n">PRECIO</th>
                <th className="n">DEMANDA 24 H</th>
                <th>QUÉ PASA</th>
              </tr>
            </thead>
            <tbody>
              {scout.disagreements.map((fila) => (
                <tr key={fila.player_id}>
                  <td>{fila.player_name}</td>
                  <td className="n">
                    <Direccion value={fila.price_direction} />
                  </td>
                  <td className="n">
                    <Direccion
                      value={fila.demand_direction}
                      percent={fila.demand_pressure}
                    />
                  </td>
                  <td className="dim">{fila.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* LOS QUE MAS SE MUEVEN */}
      <section className="pan" style={{ marginTop: 11 }}>
        <div className="pan-head">
          <div>
            <h2>LO QUE MÁS SE MUEVE</h2>
            <div className="sub">
              Ordenado por tamaño del movimiento, suba o baje
            </div>
          </div>
        </div>

        <table>
          <thead>
            <tr>
              <th>JUGADOR</th>
              <th className="n">PRECIO</th>
              <th className="n">MOVIMIENTO</th>
              <th className="n">RACHA</th>
              <th>ACUERDO</th>
            </tr>
          </thead>
          <tbody>
            {(scout.highlights || []).map((fila) => {
              const [tono, etiqueta] =
                ACUERDO[fila.agreement] || ACUERDO.NONE;

              return (
                <tr key={fila.player_id}>
                  <td>{fila.player_name}</td>
                  <td className="n">{formatMoney(fila.market_price)}</td>
                  <td className="n">
                    <Direccion
                      value={fila.direction}
                      percent={fila.magnitude_percent}
                    />
                  </td>
                  <td className="n dim">
                    {fila.trend_days
                      ? `${Math.abs(fila.trend_days)} d`
                      : "—"}
                  </td>
                  <td>
                    <span className={tono} title={`${fila.sources_agreeing} de ${fila.sources_total}`}>
                      {etiqueta}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {/* EL LIBRO DE ACIERTO.
          Ninguna fuente entra por prestigio: FF puntúa 0.3365 de
          Brier en pronósticos de titular, peor que apostar 50 %
          fijo. Se enseña desde el primer día, aunque esté vacío. */}
      <section className="pan" style={{ marginTop: 11 }}>
        <div className="pan-head">
          <div>
            <h2>¿A CUÁL HACERLE CASO?</h2>
            <div className="sub">
              Acierto medido por fuente, contra el precio real
            </div>
          </div>
          <span className={libro.available ? "pill ok" : "pill idle"}>
            {libro.decided_total || 0} CERRADAS
          </span>
        </div>

        {!libro.available ? (
          <div className="empty">
            {libro.reason ||
              "Todavía no ha vencido ninguna predicción."}
            <div className="dim" style={{ marginTop: 6 }}>
              {libro.recorded_total || 0} apuntadas, esperando a que
              pase su horizonte. No es un 0 % de acierto: es que aún
              no ha jugado esta mano.
            </div>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>FUENTE</th>
                <th className="n">APUNTADAS</th>
                <th className="n">CERRADAS</th>
                <th className="n">ACIERTO</th>
                <th className="n">ERROR DE TAMAÑO</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(libro.sources || {}).map((fuente) => (
                <tr key={fuente.source}>
                  <td>{fuente.source.replaceAll("_", " ")}</td>
                  <td className="n dim">{fuente.recorded}</td>
                  <td className="n">{fuente.decided}</td>
                  <td className="n strong">
                    {fuente.hit_rate != null
                      ? `${Math.round(fuente.hit_rate * 100)} %`
                      : "—"}
                  </td>
                  <td className="n dim">
                    {fuente.mean_magnitude_error_percent != null
                      ? `${fuente.mean_magnitude_error_percent} pp`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>


      {/* EL ESTUDIO DE LA DIVERGENCIA (07/09/2026)
          La hipotesis: que cuando el precio y la demanda apuntan
          a lados distintos, pase algo despues. NO ESTA MEDIDA.
          El libro empieza a guardarla hoy, y hasta que haya
          muestra de los DOS grupos esto no dice nada. */}
      <section className="pan" style={{ marginTop: 11 }}>
        <div className="pan-head">
          <div>
            <h2>PRECIO CONTRA DEMANDA</h2>
            <div className="sub">
              Hipótesis en estudio: ¿anticipa algo que el precio baje
              mientras la gente compra?
            </div>
          </div>
          <span className={estudio.divergent_total ? "pill warn" : "pill idle"}>
            {estudio.divergent_total || 0} HOY
          </span>
        </div>

        <div className="alert warn">
          <b>Hipótesis sin comprobar.</b> {estudio.caveat}
        </div>

        <div className="kv">
          <span>Observaciones apuntadas</span>
          <b className="mono">{estudio.recorded_total || 0}</b>
        </div>
        <div className="kv">
          <span>Ya cerradas (7 días)</span>
          <b className="mono">{estudio.closed_total || 0}</b>
        </div>

        <table style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>HORIZONTE</th>
              <th className="n">DIVERGENTES</th>
              <th className="n">RINDEN</th>
              <th className="n">CONTROL</th>
              <th className="n">RINDE</th>
              <th className="n">DIFERENCIA</th>
            </tr>
          </thead>
          <tbody>
            {Object.values(estudio.horizons || {}).map((h) => (
              <tr key={h.horizon_days}>
                <td>{h.horizon_days} días</td>
                <td className="n dim">{h.divergent_n}</td>
                <td className="n">
                  {h.divergent_mean_return_percent != null
                    ? `${h.divergent_mean_return_percent} %`
                    : "—"}
                </td>
                <td className="n dim">{h.control_n}</td>
                <td className="n">
                  {h.control_mean_return_percent != null
                    ? `${h.control_mean_return_percent} %`
                    : "—"}
                </td>
                <td className="n strong">
                  {/* La diferencia contra el control es TODO el
                      resultado: que un divergente suba no dice
                      nada si ese dia subieron todos. Y no se
                      pinta mientras no haya muestra. */}
                  {h.enough_sample && h.difference_percent != null ? (
                    <span
                      className={h.difference_percent > 0 ? "up" : "down"}
                    >
                      {h.difference_percent > 0 ? "+" : ""}
                      {h.difference_percent} pp
                    </span>
                  ) : (
                    <span className="dim" title={h.reason}>
                      sin muestra
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <p className="note" style={{ textAlign: "left" }}>
          La demanda la publica <b>solo Comuniate</b> (compras 24 h
          menos ventas): es una medida, no un consenso. Y el precio de
          Biwenger tiene mucho momento —el 83,8 % de los jugadores no
          cambia de dirección en seis días—, así que una divergencia es
          una apuesta a que una rampa se gira.
        </p>
      </section>

      {/* LOS QUE NO SE PUDIERON IDENTIFICAR.
          Se publican a propósito: un emparejamiento que no se hizo
          y no se cuenta es un agujero invisible. */}
      {(scout.unmatched || []).length > 0 && (
        <section className="pan" style={{ marginTop: 11 }}>
          <div className="pan-head">
            <div>
              <h2>SIN EMPAREJAR</h2>
              <div className="sub">
                No se usan: un emparejamiento equivocado mete la
                predicción de otro en la ficha de uno tuyo
              </div>
            </div>
            <span className="pill idle">{scout.unmatched_count}</span>
          </div>

          <table>
            <thead>
              <tr>
                <th>FUENTE</th>
                <th>NOMBRE</th>
                <th className="n">DICE VALER</th>
                <th>POR QUÉ NO</th>
              </tr>
            </thead>
            <tbody>
              {scout.unmatched.map((fila, indice) => (
                <tr key={`${fila.source}-${fila.name}-${indice}`}>
                  <td className="dim">
                    {String(fila.source || "").replaceAll("_", " ")}
                  </td>
                  <td>{fila.name}</td>
                  <td className="n dim">
                    {fila.market_value
                      ? formatMoney(fila.market_value)
                      : "—"}
                  </td>
                  <td className="dim">{fila.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="note" style={{ textAlign: "left" }}>
            Se enseñan los primeros {scout.unmatched.length} de{" "}
            {scout.unmatched_count}.
          </p>
        </section>
      )}
    </>
  );
}
