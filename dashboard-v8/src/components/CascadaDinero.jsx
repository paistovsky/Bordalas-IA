import Tarjeta, { SinDato } from "./Tarjeta";
import {
  cierreDeJornada,
  cuando,
  esNuestro,
  laOrden,
  millones,
  porVenir,
  pujasDelReset,
  pujasVivas,
  saldo
} from "../lib/lectura";

/* EL DINERO HASTA LA JORNADA (30/09/2026)
 *
 * Una cascada: el saldo de ahora, lo que se va si se ganan las
 * pujas, lo que entra si se venden los de la orden al suelo, y
 * cómo quedaría el saldo antes de que cierre la jornada.
 *
 * Todo sale de datos publicados: el saldo de la foto, nuestras
 * pujas vivas, las que el ciclo lanzará en el reset y los suelos
 * de la orden. Es el peor caso de las pujas (se ganan todas) y el
 * mínimo de las ventas (al suelo): se dice así en la tarjeta.
 */

export default function CascadaDinero({ data }) {
  const ahora = new Date();
  const s = saldo(data);

  if (s == null) {
    return (
      <Tarjeta titulo="EL DINERO HASTA LA JORNADA" pregunta="¿Llegamos con el saldo en positivo?">
        <SinDato>Esta foto no trae el saldo.</SinDato>
      </Tarjeta>
    );
  }

  const orden = laOrden(data, ahora);
  const vivas = pujasVivas(data);
  const reset = pujasDelReset(data, orden);
  const ventas = orden?.viva
    ? orden.vender.filter(
        (v) =>
          esNuestro(data, v.nombre) &&
          !(v.ultimo_recurso && v.desdeFecha && porVenir(v.desdeFecha, ahora)) &&
          Number(v.suelo) > 0
      )
    : [];

  const pasos = [{ que: "Saldo ahora", importe: s, tipo: "base" }];

  const totalVivas = vivas.reduce((a, p) => a + p.importe, 0);
  if (totalVivas > 0) {
    pasos.push({
      que: `Pujas puestas (${vivas.length}), si se ganan`,
      importe: -totalVivas,
      tipo: "sale"
    });
  }

  const totalReset = reset.reduce((a, b) => a + Number(b.bid || 0), 0);
  if (totalReset > 0) {
    pasos.push({
      que: `Pujas del reset (${reset.length}), si se ganan`,
      importe: -totalReset,
      tipo: "sale"
    });
  }

  const totalVentas = ventas.reduce((a, v) => a + Number(v.suelo || 0), 0);
  if (totalVentas > 0) {
    pasos.push({
      que: `Ventas de la orden (${ventas.length}), al suelo`,
      importe: totalVentas,
      tipo: "entra"
    });
  }

  const final = pasos.reduce((a, p) => a + p.importe, 0);
  const cierre = cierreDeJornada(data, ahora);
  const tope = Math.max(...pasos.map((p) => Math.abs(p.importe)), Math.abs(final), 1);

  return (
    <Tarjeta
      titulo="EL DINERO HASTA LA JORNADA"
      pregunta="¿Llegamos con el saldo en positivo?"
    >
      <ul className="c2-cascada">
        {pasos.map((p) => (
          <li key={p.que} className={p.tipo}>
            <span className="c2-cascada-que">{p.que}</span>
            <span className="c2-cascada-barra">
              <i style={{ width: `${Math.max(3, (Math.abs(p.importe) / tope) * 100)}%` }} />
            </span>
            <b>{p.tipo === "entra" ? "+" : ""}{millones(p.importe)}</b>
          </li>
        ))}
      </ul>

      <div className="c2-cascada-final">
        <span>
          Saldo antes de la jornada
          {cierre ? <small>cierra {cuando(cierre, ahora)}</small> : null}
        </span>
        <b className={final >= 0 ? "bien" : ""}>{millones(final)}</b>
      </div>

      <p className="c2-pie">
        {pasos.length === 1
          ? "No hay pujas ni ventas pendientes: el saldo es el que hay."
          : final >= 0
          ? "Aunque se ganen todas las pujas, el saldo queda en positivo."
          : "Si se ganan todas las pujas y sólo se vende al suelo, faltaría dinero: harían falta más ventas."}
      </p>
    </Tarjeta>
  );
}
