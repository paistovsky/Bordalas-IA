import Tarjeta, { SinDato } from "./Tarjeta";
import { clave, millones, movimientosDe } from "../lib/lectura";

/* LOS RIVALES, UNO A UNO (30/09/2026)
 *
 * Una carta por mánager: puntos y distancia con nosotros, caja
 * (reconstruida desde el tablón; la nuestra es la real), cuánto
 * puede pujar, lo peligroso que es y lo que ha movido esta semana
 * (`tablon_semana`, sus líneas).
 *
 * La amenaza no va en rojo: cinco puntos, más llenos cuanto más
 * aprieta. El dueño no quiere avisos de colores.
 */

const AMENAZA = {
  VERY_HIGH: [5, "muy peligroso"],
  HIGH: [4, "peligroso"],
  MEDIUM: [3, "a vigilar"],
  LOW: [2, "poco peligroso"],
  VERY_LOW: [1, "inofensivo"]
};

function Amenaza({ nivel }) {
  const a = AMENAZA[String(nivel || "").toUpperCase()];
  if (!a) return null;
  return (
    <span className="c2-amenaza" title={a[1]}>
      {[1, 2, 3, 4, 5].map((i) => (
        <i key={i} className={i <= a[0] ? "on" : ""} />
      ))}
      <small>{a[1]}</small>
    </span>
  );
}

function resumenDeLaSemana(lineas) {
  const fichajes = lineas.filter((l) => / ficha a /.test(l.texto)).length;
  const ventas = lineas.filter((l) => / vende a /.test(l.texto)).length;
  const partes = [];
  if (fichajes) partes.push(`${fichajes} ${fichajes === 1 ? "fichaje" : "fichajes"}`);
  if (ventas) partes.push(`${ventas} ${ventas === 1 ? "venta" : "ventas"}`);
  return partes.length ? partes.join(" · ") : `${lineas.length} movimientos`;
}

export default function LosRivalesEnCartas({ data }) {
  const tabla = [...(data.competition?.standings || [])].sort((a, b) => a.rank - b.rank);

  if (!tabla.length) {
    return (
      <Tarjeta titulo="LOS RIVALES, UNO A UNO" pregunta="¿Quién aprieta y qué ha hecho?">
        <SinDato>Esta foto no trae la clasificación.</SinDato>
      </Tarjeta>
    );
  }

  const intel = new Map((data.rivalIntel?.managers || []).map((m) => [clave(m.name), m]));
  const nos = tabla.find((m) => m.is_current_user);
  const semana = data.tablonSemana;
  const cuadre = data.rivalIntel?.cash_check || {};

  return (
    <Tarjeta titulo="LOS RIVALES, UNO A UNO" pregunta="¿Quién aprieta, con cuánto dinero y qué ha movido esta semana?">
      <div className="c2-rivales">
        {tabla.map((m) => {
          const i = intel.get(clave(m.name)) || {};
          const esNos = Boolean(m.is_current_user);
          const diff = nos ? Number(m.points) - Number(nos.points) : null;
          const lineas = semana ? movimientosDe(data, m.name) : [];
          const caja = esNos ? (data.solvencyClock?.balance ?? data.summary?.balance) : i.balance;
          return (
            <article className={`c2-rival ${esNos ? "es-nos" : ""}`} key={m.user_id || m.name}>
              <div className="c2-rival-arriba">
                <span className="c2-rival-puesto">{m.rank}º</span>
                <b className="c2-rival-nombre">{esNos ? `${m.name} (nosotros)` : m.name}</b>
                <span className="c2-rival-pts">
                  {m.points}
                  <small>pts</small>
                </span>
              </div>

              {!esNos && diff != null && (
                <div className="c2-rival-frase">
                  {diff > 0 ? `Nos saca ${diff} puntos.` : diff < 0 ? `Le sacamos ${-diff} puntos.` : "Empatados a puntos."}
                </div>
              )}

              <dl className="c2-rival-datos">
                <div>
                  <dt>Caja</dt>
                  <dd>{caja == null ? "sin dato" : millones(caja)}</dd>
                </div>
                <div>
                  <dt>Plantilla</dt>
                  <dd>{m.team_value != null ? millones(m.team_value) : "sin dato"}</dd>
                </div>
                {!esNos && (
                  <div>
                    <dt>Puede pujar</dt>
                    <dd>{i.maximum_bid != null ? millones(i.maximum_bid) : "sin dato"}</dd>
                  </div>
                )}
              </dl>

              {!esNos && <Amenaza nivel={i.threat_level} />}

              {semana && (
                lineas.length ? (
                  <details className="c2-rival-semana">
                    <summary>Esta semana: {resumenDeLaSemana(lineas)}</summary>
                    <ul>
                      {lineas.map((l, k) => (
                        <li key={k}>
                          <span>{l.hora}</span> {l.texto.slice(m.name.length).trim()}
                        </li>
                      ))}
                    </ul>
                  </details>
                ) : (
                  <div className="c2-rival-quieto">Esta semana no ha movido nada.</div>
                )
              )}
            </article>
          );
        })}
      </div>

      {cuadre.available && cuadre.ok === false && cuadre.difference != null && (
        <p className="c2-pie">
          La caja de los rivales se reconstruye con el tablón. Hecho con la nuestra, se desvía {millones(Math.abs(cuadre.difference))} de la real.
        </p>
      )}
    </Tarjeta>
  );
}
