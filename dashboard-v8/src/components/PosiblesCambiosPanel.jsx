import { formatMoney } from "../lib/utils";
import { tonoDe } from "../lib/tono";

/* POSIBLES CAMBIOS (10/09/2026)
 *
 * Quien esta en el banquillo, POR QUE, y que le pasaria al once
 * si entrara.
 *
 * EL MOTIVO NO SE INVENTA AQUI
 *
 *   El motor de alineacion ya compara a todos para elegir once:
 *   descarta al que no puede jugar, luego al que esta en duda, y
 *   de los que quedan se queda con el que mas puntua en cada
 *   posicion. `banquillo_con_motivo` le saca ESE motivo -el que
 *   uso- y lo publica en `lineup.bench`.
 *
 *   Este fichero solo pinta. Si algun dia el motor cambia de
 *   criterio, el panel cambia solo: no hay una segunda opinion
 *   que mantener al dia.
 *
 * LA COLUMNA DE LA DERECHA
 *
 *   La distancia contra el peor titular de su misma posicion,
 *   que es exactamente contra quien tendria que ganar para
 *   entrar. En VERDE cuando el once ganaria con el dentro: eso
 *   solo pasa cuando lo que le falta no es nivel, es poder
 *   jugar. Un suplente mejor que el titular al que no dejan
 *   jugar es justo lo que hay que ver de un vistazo.
 */

const POSICION = {
  1: "POR",
  2: "DEF",
  3: "MED",
  4: "DEL"
};

// El tono lo da el corte que no paso, no el nombre del jugador.
const TONO = {
  NO_DISPONIBLE: "pill crit",
  NO_JUEGA_SU_EQUIPO: "pill crit",
  EN_DUDA: "pill warn",
  POSICION_CUBIERTA: "pill idle",
  PUNTUA_MENOS: "pill idle"
};

function Delta({ fila }) {
  const valor = fila.weekly_value_delta;

  if (valor == null || !fila.compared_to) {
    return <span className="sub">—</span>;
  }

  const gana = valor > 0;

  return (
    <span className={gana ? "num ok" : "num sub"}>
      {gana ? "+" : ""}
      {valor.toFixed(2)} vs {fila.compared_to}
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

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>POSIBLES CAMBIOS</h2>
          <div className="sub">
            quién está fuera del XI y por qué · a la derecha, lo
            que ganaría o perdería el once si entrara
          </div>
        </div>
        <span className="pill idle">{bench.length}</span>
      </div>

      <table className="tbl">
        <tbody>
          {bench.map((fila) => (
            <tr key={fila.id}>
              <td className="sub">
                {POSICION[fila.position] || "—"}
              </td>

              <td>{fila.name}</td>

              <td>
                <span className={tonoDe(TONO, fila.reason).tono}>
                  {fila.reason_text}
                </span>
              </td>

              <td className="num sub">
                {formatMoney(fila.price)}
              </td>

              <td className="num">
                <Delta fila={fila} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
