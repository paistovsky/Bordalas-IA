import { formatMoney } from "../lib/utils";
import { tonoDe } from "../lib/tono";

/* POSIBLES CAMBIOS (10/09/2026)
 *
 * Una fila por suplente, y la fila contesta entera:
 *
 *   quien es · de que equipo · su tit. % · POR QUE esta fuera ·
 *   A QUIEN tendria que quitarle el puesto · cuanto cambia el
 *   once si entra por el
 *
 * EL MOTIVO Y EL RIVAL NO SE INVENTAN AQUI
 *
 *   El motor de alineacion ya compara a todos contra todos para
 *   elegir once: descarta al que no puede jugar, luego al que
 *   esta en duda, y de los que quedan se queda con el que mas
 *   puntua en cada posicion. `banquillo_con_motivo` le saca ESE
 *   motivo y ESE rival -el peor titular de su posicion, que es
 *   justo al que esta mas cerca de quitarle el puesto- y los
 *   publica en `posibles_cambios`.
 *
 *   Este fichero solo pinta. Si el motor cambia de criterio, el
 *   panel cambia solo: no hay una segunda opinion que mantener
 *   al dia.
 *
 * EL ORDEN, Y EL VERDE
 *
 *   Arriba el que menos lejos esta de entrar. Y en VERDE el que
 *   YA mejoraria el once: eso solo puede pasar cuando el motivo
 *   no es puntuar menos, o sea, cuando lo que le falta no es
 *   nivel sino poder jugar. Un suplente mejor que el titular al
 *   que no dejan jugar es exactamente lo que hay que ver de un
 *   vistazo.
 *
 * SIN DATO NO ES CERO
 *
 *   Misma regla que las tarjetas del once: pintar "tit. 0 %"
 *   cuando la fuente externa falla hace creer que no juega, que
 *   es lo contrario de "no se sabe".
 */

const POSICION = {
  1: "POR",
  2: "DEF",
  3: "MED",
  4: "DEL"
};

// El tono lo da el corte del motor que no paso, no el jugador.
const TONO = {
  NO_DISPONIBLE: "pill crit",
  NO_JUEGA_SU_EQUIPO: "pill crit",
  EN_DUDA: "pill warn",
  POSICION_CUBIERTA: "pill idle",
  PUNTUA_MENOS: "pill idle"
};

function escudo(teamId) {
  return teamId
    ? `https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/${teamId}.png`
    : null;
}

/** La misma cadena que `PitchXI`. Sin dato devuelve null. */
function titularidad(fila) {
  const raw = fila.starter_probability ?? fila.jp_confidence ?? null;

  return raw != null && Number(raw) > 0 ? Number(raw) : null;
}

function Titular({ valor }) {
  if (valor == null) {
    return <span className="sub">sin dato</span>;
  }

  return (
    <span className={valor >= 70 ? "up" : valor >= 40 ? "" : "dim"}>
      tit. {Math.round(valor)}%
    </span>
  );
}

export default function PosiblesCambiosPanel({ data }) {
  const bloque = data.posiblesCambios || {};
  const bench = bloque.bench || [];

  // "No hay dato" y "no hay suplentes" son cosas distintas y se
  // dicen distinto. Un panel que se esconde cuando falla es un
  // panel que no se mira nunca.
  const available = Boolean(bloque.available);

  if (!available) {
    return (
      <section className="pan">
        <h2>POSIBLES CAMBIOS</h2>
        <div className="empty">
          El motor no ha publicado el banquillo en esta foto. No
          es que no haya suplentes: es que no se sabe.
        </div>
      </section>
    );
  }

  if (!bench.length) {
    return (
      <section className="pan">
        <h2>POSIBLES CAMBIOS</h2>
        <div className="sub">
          Ningún suplente: los once son toda la plantilla.
        </div>
      </section>
    );
  }

  const mejoran = bench.filter(
    (f) => Number(f.weekly_value_delta || 0) > 0
  ).length;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>POSIBLES CAMBIOS</h2>
          <div className="sub">
            quién está fuera del XI, por qué, y a quién tendría
            que quitarle el puesto · el más cerca de entrar,
            arriba
          </div>
        </div>
        <span className={mejoran ? "pill ok" : "pill idle"}>
          {mejoran
            ? `${mejoran} mejoraría${mejoran > 1 ? "n" : ""} el XI`
            : `${bench.length} en el banquillo`}
        </span>
      </div>

      <div className="scroll-x">
        <table className="tbl">
          <thead>
            <tr>
              <th>JUGADOR</th>
              <th>TIT.</th>
              <th>POR QUÉ ESTÁ FUERA</th>
              <th>LE QUITARÍA EL PUESTO A</th>
              <th className="n">EL XI</th>
            </tr>
          </thead>

          <tbody>
            {bench.map((fila) => {
              const delta = fila.weekly_value_delta;
              const mejora = delta != null && delta > 0;
              const crest = escudo(fila.team_id);
              const crestRival = escudo(fila.compared_to_team_id);

              return (
                <tr key={fila.id} className={mejora ? "row-ok" : ""}>
                  {/* QUIÉN ES: nombre, escudo y posición. */}
                  <td>
                    <span className="who">
                      {crest && (
                        <img
                          className="crest"
                          src={crest}
                          alt=""
                          loading="lazy"
                        />
                      )}
                      <b>{fila.name}</b>
                      <span className="sub">
                        {POSICION[fila.position] || "—"}
                        {fila.team_name ? ` · ${fila.team_name}` : ""}
                      </span>
                    </span>
                  </td>

                  {/* SU PROBABILIDAD DE SER TITULAR, EN SU CLUB. */}
                  <td className="n">
                    <Titular valor={titularidad(fila)} />
                  </td>

                  {/* POR QUÉ, en castellano llano. */}
                  <td>
                    <span className={tonoDe(TONO, fila.reason).tono}>
                      {fila.reason_text}
                    </span>
                  </td>

                  {/* A QUIÉN. El titular concreto al que está
                      más cerca, con nombre y su propio tit. % —
                      sin eso no se puede juzgar el cambio. */}
                  <td>
                    {fila.compared_to ? (
                      <span className="who">
                        {crestRival && (
                          <img
                            className="crest"
                            src={crestRival}
                            alt=""
                            loading="lazy"
                          />
                        )}
                        {fila.compared_to}
                        {fila.compared_to_probability != null && (
                          <span className="sub">
                            {" "}
                            tit.{" "}
                            {Math.round(
                              fila.compared_to_probability
                            )}
                            %
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="sub">
                        no hay titular en su posición
                      </span>
                    )}
                  </td>

                  {/* CUÁNTO SE GANA O SE PIERDE. */}
                  <td className="n">
                    {delta == null ? (
                      <span className="sub">—</span>
                    ) : (
                      <b className={mejora ? "up" : "down"}>
                        {mejora ? "+" : ""}
                        {delta.toFixed(2)}
                      </b>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        «EL XI» es lo que cambiaría el valor esperado de la semana
        si entrara por ese titular — la misma cuenta con la que el
        motor eligió a uno sobre otro. En verde, el que ya lo
        mejoraría: a ese no le falta nivel, le falta jugar.
      </p>
    </section>
  );
}
