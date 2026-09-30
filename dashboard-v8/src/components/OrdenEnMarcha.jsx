import Tarjeta, { SinDato } from "./Tarjeta";
import bordalas from "../assets/bordalas-method.jpg";
import {
  clave,
  cuando,
  esNuestro,
  laOrden,
  millones,
  ofertasDelComputer,
  porVenir,
  pujasVivas
} from "../lib/lectura";

/* LA ORDEN EN MARCHA (30/09/2026)
 *
 * Lo que el gestor le ha mandado a Pepe, y cómo va: a por quién
 * va, a quién vende para pagarlo (y si la oferta de hoy llega al
 * suelo), a quién no toca y por quién no puja. Sale de `orden`.
 *
 * Sin la clave, una línea que lo dice. Con la orden parada, una
 * línea con el motivo: si Pepe no la cumple, no se enseña como si
 * la cumpliera.
 */

export default function OrdenEnMarcha({ data }) {
  const ahora = new Date();
  const orden = laOrden(data, ahora);

  if (!orden) {
    return (
      <Tarjeta titulo="LA ORDEN EN MARCHA" pregunta="¿Qué le ha mandado el gestor a Pepe?">
        <SinDato>Esta foto no trae la orden del gestor.</SinDato>
      </Tarjeta>
    );
  }

  if (!orden.viva) {
    return (
      <Tarjeta
        titulo="LA ORDEN EN MARCHA"
        pregunta="¿Qué le ha mandado el gestor a Pepe?"
        pill={<span className="c2-pill">SIN ORDEN</span>}
      >
        <SinDato>Ahora mismo no hay orden en marcha: {orden.estado}. Pepe decide solo.</SinDato>
      </Tarjeta>
    );
  }

  const vivas = new Map(pujasVivas(data).map((p) => [clave(p.nombre), p.importe]));
  const ofertas = ofertasDelComputer(data);

  return (
    <Tarjeta
      titulo="LA ORDEN EN MARCHA"
      pregunta="¿Qué le ha mandado el gestor a Pepe?"
      className="c2-orden"
      pill={<span className="c2-pill on">EN MARCHA</span>}
    >
      {orden.fichar.length > 0 && (
        <div className="c2-bloque">
          <div className="c2-bloque-t">A por</div>
          {orden.fichar.map((f) => {
            const nuestro = esNuestro(data, f.nombre);
            const puja = vivas.get(clave(f.nombre));
            return (
              <div className="c2-fichaje" key={f.nombre}>
                <img className="c2-avatar" src={bordalas} alt="" />
                <div className="c2-fichaje-txt">
                  <b>{f.nombre}</b>
                  <span>
                    {nuestro
                      ? "Ya es nuestro."
                      : puja
                      ? `Puja puesta: ${millones(puja)}.`
                      : "Todavía sin puja puesta."}
                    {f.puja && !nuestro ? ` La orden dice hasta ${millones(f.puja)}.` : ""}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {orden.vender.length > 0 && (
        <div className="c2-bloque">
          <div className="c2-bloque-t">Para pagarlo, vende</div>
          <ul className="c2-filas">
            {orden.vender.map((v) => {
              const sigue = esNuestro(data, v.nombre);
              const oferta = ofertas.get(clave(v.nombre));
              const espera = v.ultimo_recurso && v.desdeFecha && porVenir(v.desdeFecha, ahora);
              let estado;
              if (!sigue) estado = "Ya no está en la plantilla.";
              else if (espera) estado = `Último recurso: sólo desde ${cuando(v.desdeFecha, ahora)} y si el saldo sigue en negativo.`;
              else if (oferta && oferta >= Number(v.suelo || 0)) estado = `Hoy ofrecen ${millones(oferta)}: llega al suelo.`;
              else if (oferta) estado = `Hoy ofrecen ${millones(oferta)}: todavía no llega.`;
              else estado = "Hoy no hay oferta del Computer.";
              return (
                <li key={v.nombre} className={sigue ? "" : "hecho"}>
                  <span>
                    {v.nombre}
                    <small>{estado}</small>
                  </span>
                  <b>≥ {millones(v.suelo)}</b>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {(orden.proteger.length > 0 || orden.conservar.length > 0) && (
        <div className="c2-bloque">
          <div className="c2-bloque-t">No se tocan</div>
          <div className="c2-chips">
            {[...orden.proteger, ...orden.conservar.filter((n) => !orden.proteger.includes(n))].map((n) => (
              <span className="c2-chip" key={n}>{n}</span>
            ))}
          </div>
        </div>
      )}

      {orden.noPujar.length > 0 && (
        <div className="c2-bloque">
          <div className="c2-bloque-t">Prohibido pujar por</div>
          <div className="c2-chips">
            {orden.noPujar.map((n) => (
              <span className="c2-chip tachado" key={n}>{n}</span>
            ))}
          </div>
        </div>
      )}

      {orden.caduca && (
        <p className="c2-pie">La orden caduca {cuando(orden.caduca, ahora)}.</p>
      )}
    </Tarjeta>
  );
}
