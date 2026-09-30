import Tarjeta, { SinDato } from "./Tarjeta";
import { catalogo, clave, conSigno, laOrden, millones, plantilla, porcentaje, porVenir, posicionLarga } from "../lib/lectura";

/* LA PLANTILLA, LÍNEA A LÍNEA (30/09/2026)
 *
 * Porteros, defensas, medios y delanteros. De cada uno: si está en
 * el once, la probabilidad de ser titular (barra), cómo está
 * (lesión, duda, sanción), puntos y media por partido, y si su
 * precio sube o baja hoy. Si la orden del gestor lo vende o lo
 * protege, se dice.
 *
 * La probabilidad de titular sale del once (`lineup.players`) y,
 * si no está, de la plantilla (`roster`). Sin dato: «sin dato».
 */

const ESTADO = {
  injured: "Lesionado",
  doubt: "Duda",
  sanctioned: "Sancionado",
  discarded: "Descartado"
};

export default function PlantillaPorLineas({ data }) {
  const jugadores = plantilla(data);

  if (!jugadores.length) {
    return (
      <Tarjeta titulo="LA PLANTILLA, LÍNEA A LÍNEA" pregunta="¿Cómo está cada uno?">
        <SinDato>Esta foto no trae la plantilla.</SinDato>
      </Tarjeta>
    );
  }

  const delOnce = new Map((data.lineup?.players || []).map((p) => [Number(p.id), p]));
  const cat = catalogo(data);
  const orden = laOrden(data);
  const ahora = new Date();
  const ultimoRecurso = new Set(
    (orden?.viva ? orden.vender : [])
      .filter((v) => v.ultimo_recurso && v.desdeFecha && porVenir(v.desdeFecha, ahora))
      .map((v) => clave(v.nombre))
  );
  const seVende = new Set(
    (orden?.viva ? orden.vender : []).map((v) => clave(v.nombre)).filter((k) => !ultimoRecurso.has(k))
  );
  const seProtege = new Set((orden?.viva ? [...orden.proteger, ...orden.conservar] : []).map(clave));

  const lineas = [1, 2, 3, 4].map((pos) => ({
    pos,
    jugadores: jugadores
      .filter((p) => Number(p.position) === pos)
      .sort(
        (a, b) =>
          Number(Boolean(b.is_starter)) - Number(Boolean(a.is_starter)) ||
          Number(b.points || 0) - Number(a.points || 0)
      )
  }));

  return (
    <Tarjeta
      titulo="LA PLANTILLA, LÍNEA A LÍNEA"
      pregunta="¿Quién juega, cómo está y cómo va su precio?"
      pill={<span className="c2-pill">{jugadores.length} jugadores</span>}
    >
      {lineas.map(({ pos, jugadores: js }) =>
        js.length ? (
          <div className="c2-linea" key={pos}>
            <div className="c2-bloque-t">{posicionLarga(pos)} · {js.length}</div>
            <ul className="c2-squad">
              {js.map((p) => {
                const once = delOnce.get(Number(p.id)) || {};
                const prob = porcentaje(once.starter_probability ?? p.starter_probability);
                const estado = ESTADO[String(p.status || once.status || "").toLowerCase()];
                const ficha = cat.get(Number(p.id));
                const jugados = Number(ficha?.played || 0);
                const media = jugados ? (Number(p.points || 0) / jugados).toLocaleString("es-ES", { maximumFractionDigits: 1 }) : null;
                const d = Number(p.price_increment || 0);
                const k = clave(p.name);
                return (
                  <li key={p.id || p.name}>
                    <div className="c2-sq-arriba">
                      <b>{p.name}</b>
                      {p.is_starter && <span className="c2-xi">XI</span>}
                      {seVende.has(k) && <span className="c2-marca">a la venta</span>}
                      {ultimoRecurso.has(k) && <span className="c2-marca">último recurso</span>}
                      {!seVende.has(k) && !ultimoRecurso.has(k) && seProtege.has(k) && <span className="c2-marca">no se toca</span>}
                      <span className="c2-sq-pts">{p.points ?? "—"} pts</span>
                    </div>
                    <div className="c2-sq-barra" aria-label={prob == null ? "sin dato de titularidad" : `${prob} % de ser titular`}>
                      <i style={{ width: `${prob ?? 0}%` }} />
                    </div>
                    <div className="c2-sq-abajo">
                      <span>{prob == null ? "titular: sin dato" : `${prob} % titular`}</span>
                      {estado && <span className="c2-sq-estado">{estado}</span>}
                      {media && <span>{media} por partido</span>}
                      <span className={d > 0 ? "sube" : d < 0 ? "baja" : ""}>
                        {millones(p.price)} {d ? `(${conSigno(d)})` : ""}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null
      )}
    </Tarjeta>
  );
}
