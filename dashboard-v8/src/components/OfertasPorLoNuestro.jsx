import Tarjeta, { SinDato } from "./Tarjeta";
import { millones } from "../lib/lectura";

/* LO QUE NOS OFRECEN (30/09/2026)
 *
 * Por cuáles de los nuestros que están a la venta hay oferta del
 * Computer, cuánto, y qué va a hacer Pepe con ella (la frase ya
 * viene en castellano en `loNuestroALaVenta.que_va_a_hacer`).
 */

export default function OfertasPorLoNuestro({ data }) {
  const venta = data.loNuestroALaVenta || {};

  if (!venta.available) {
    return (
      <Tarjeta titulo="LO QUE NOS OFRECEN" pregunta="¿Cuánto dan por los nuestros?">
        <SinDato>Esta foto no trae nuestras publicaciones.</SinDato>
      </Tarjeta>
    );
  }

  const jugadores = venta.players || [];
  const conOferta = jugadores
    .filter((p) => Number(p.nos_ofrecen) > 0)
    .sort((a, b) => Number(b.prima ?? -999) - Number(a.prima ?? -999));
  const sinOferta = jugadores.length - conOferta.length;

  const Fila = ({ p }) => {
    const prima = p.prima == null ? null : Number(p.prima);
    return (
      <li>
        <span>
          {p.name}
          <small>
            {prima == null
              ? ""
              : `${prima > 0 ? "+" : ""}${prima.toLocaleString("es-ES")} % sobre su precio · `}
            {p.que_va_a_hacer || "sin decidir"}
          </small>
        </span>
        <b className={prima > 0 ? "sube" : ""}>{millones(p.nos_ofrecen)}</b>
      </li>
    );
  };

  return (
    <Tarjeta
      titulo="LO QUE NOS OFRECEN"
      pregunta="¿Cuánto dan por los nuestros que están a la venta?"
      pill={<span className="c2-pill">{conOferta.length} ofertas</span>}
    >
      {!conOferta.length ? (
        <SinDato>
          {jugadores.length
            ? `Tenemos ${jugadores.length} a la venta y ninguno tiene oferta ahora mismo.`
            : "No tenemos a nadie a la venta."}
        </SinDato>
      ) : (
        <>
          <ul className="c2-filas">
            {conOferta.slice(0, 6).map((p) => <Fila key={p.id || p.name} p={p} />)}
          </ul>
          {conOferta.length > 6 && (
            <details className="c2-mas">
              <summary>Ver las otras {conOferta.length - 6}</summary>
              <ul className="c2-filas">
                {conOferta.slice(6).map((p) => <Fila key={p.id || p.name} p={p} />)}
              </ul>
            </details>
          )}
          {sinOferta > 0 && (
            <p className="c2-pie">Otros {sinOferta} están a la venta sin oferta.</p>
          )}
        </>
      )}
    </Tarjeta>
  );
}
