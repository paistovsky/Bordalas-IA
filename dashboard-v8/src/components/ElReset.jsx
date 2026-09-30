import Tarjeta, { SinDato } from "./Tarjeta";
import { cuando, laOrden, millones, porcentaje, pujasDelReset, pujasVivas, resetDeLaFoto } from "../lib/lectura";

/* EL PRÓXIMO RESET (30/09/2026)
 *
 * El mercado del Computer se renueva una vez al día. Aquí: cuándo,
 * qué pujas nuestras se resuelven, qué va a pujar Pepe en la
 * ventana (el plan REAL de la subasta, sin los que la orden
 * prohíbe) y cómo le ha ido pujando hasta hoy.
 */

export default function ElReset({ data }) {
  const ahora = new Date();
  const reset = resetDeLaFoto(data, ahora);
  const orden = laOrden(data, ahora);
  const vivas = pujasVivas(data);
  const plan = pujasDelReset(data, orden);
  const libro = data.subasta?.outcomes_all || {};
  const ganadas = Number(libro.won || 0);
  const perdidas = Number(libro.lost || 0);
  const resueltas = ganadas + perdidas;

  return (
    <Tarjeta
      titulo="EL PRÓXIMO RESET"
      pregunta="¿Qué se juega Pepe cuando se renueve el mercado?"
      pill={reset ? <span className="c2-pill">{cuando(reset, ahora)}</span> : null}
    >
      {!reset ? (
        <SinDato>
          El reset que trae esta foto ya ha pasado. El siguiente sale en la próxima vuelta de Pepe.
        </SinDato>
      ) : (
        <>
          <div className="c2-bloque">
            <div className="c2-bloque-t">Se resuelven</div>
            {vivas.length ? (
              <ul className="c2-filas">
                {vivas.map((p, i) => (
                  <li key={`${p.nombre}${i}`}>
                    <span>
                      {p.nombre || "Un jugador"}
                      {p.precio ? <small>vale {millones(p.precio)}</small> : null}
                    </span>
                    <b>{millones(p.importe)}</b>
                  </li>
                ))}
              </ul>
            ) : (
              <SinDato>No tenemos ninguna puja puesta.</SinDato>
            )}
          </div>

          <div className="c2-bloque">
            <div className="c2-bloque-t">Pepe pujará en la ventana</div>
            {plan.length ? (
              <ul className="c2-filas">
                {plan.map((b) => (
                  <li key={b.id || b.name}>
                    <span>
                      {b.name}
                      {b.market_price ? <small>vale {millones(b.market_price)}</small> : null}
                    </span>
                    <b>{millones(b.bid)}</b>
                  </li>
                ))}
              </ul>
            ) : (
              <SinDato>No tiene pujas nuevas preparadas para este reset.</SinDato>
            )}
          </div>
        </>
      )}

      {resueltas > 0 && (
        <p className="c2-pie">
          Hasta hoy: {ganadas} pujas ganadas de {resueltas} resueltas
          {porcentaje((ganadas / resueltas) * 100) != null ? ` (${porcentaje((ganadas / resueltas) * 100)} %)` : ""}.
        </p>
      )}
    </Tarjeta>
  );
}
