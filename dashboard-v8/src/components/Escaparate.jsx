import Tarjeta, { SinDato } from "./Tarjeta";
import { clave, laOrden, millones, posicionCorta, pujasVivas } from "../lib/lectura";

/* EL ESCAPARATE DE HOY (30/09/2026)
 *
 * Los jugadores que vende el Computer en este reset, con lo que
 * importa para ganar puntos: cuánto vale, cuántos puntos lleva,
 * si su precio sube o baja y si mejoraría nuestro once (lo mide
 * `todaLaLiga` contra el peor titular de su puesto).
 *
 * Primero los que nos mejoran, después los chollos, después el
 * resto. Si ya tenemos puja o la orden prohíbe pujar, se dice.
 */

const ORDEN = { "nos mejora": 0, "chollo · muchos puntos por euro": 1, "sin interés": 2, "no disponible": 3 };

function nota(p, vivas, prohibidos) {
  const k = clave(p.name);
  if (vivas.has(k)) return { txt: `Puja puesta: ${millones(vivas.get(k))}`, cls: "puja" };
  if (prohibidos.has(k)) return { txt: "La orden dice no pujar", cls: "" };
  if (p.etiqueta === "nos mejora" && Number(p.nos_suma) > 0) {
    return {
      txt: `Mejora el once: ${p.nos_suma} pts más que ${p.vara_nombre || "nuestro peor titular"}`,
      cls: "mejora"
    };
  }
  if (p.etiqueta === "chollo · muchos puntos por euro") return { txt: "Muchos puntos por euro", cls: "" };
  if (p.etiqueta === "no disponible") return { txt: "No disponible ahora", cls: "" };
  return { txt: "No mejora nuestro once", cls: "" };
}

function Jugador({ p, vivas, prohibidos }) {
  const n = nota(p, vivas, prohibidos);
  const sube = Number(p.price_increment || 0);
  return (
    <li className={`c2-jug ${n.cls}`}>
      <div className="c2-jug-arriba">
        <span className="c2-pos">{posicionCorta(p.position)}</span>
        <b>{p.name}</b>
        <span className="c2-precio">{millones(p.price)}</span>
      </div>
      <div className="c2-jug-abajo">
        <span>
          {p.points ?? "—"} pts{p.played ? ` en ${p.played} partidos` : ""}
        </span>
        <span className={sube > 0 ? "sube" : sube < 0 ? "baja" : ""}>
          {sube > 0 ? "▲ " : sube < 0 ? "▼ " : ""}
          {sube === 0 ? "precio quieto" : millones(Math.abs(sube))}
        </span>
      </div>
      <div className="c2-jug-nota">{n.txt}</div>
    </li>
  );
}

export default function Escaparate({ data }) {
  const liga = data.todaLaLiga || {};
  const jugadores = (liga.players || []).filter((p) => p.de_quien === "computer");
  const orden = laOrden(data);
  const vivas = new Map(pujasVivas(data).map((p) => [clave(p.nombre), p.importe]));
  const prohibidos = new Set((orden?.viva ? orden.noPujar : []).map(clave));

  if (!liga.available) {
    return (
      <Tarjeta titulo="EL ESCAPARATE DE HOY" pregunta="¿Qué vende hoy el Computer?">
        <SinDato>Esta foto no trae la lista de jugadores de la liga.</SinDato>
      </Tarjeta>
    );
  }

  const ordenados = [...jugadores].sort(
    (a, b) =>
      (ORDEN[a.etiqueta] ?? 2) - (ORDEN[b.etiqueta] ?? 2) ||
      Number(b.nos_suma || 0) - Number(a.nos_suma || 0) ||
      Number(b.points || 0) - Number(a.points || 0)
  );

  const primeros = ordenados.slice(0, 6);
  const resto = ordenados.slice(6);
  const mejoran = jugadores.filter((p) => p.etiqueta === "nos mejora").length;

  return (
    <Tarjeta
      titulo="EL ESCAPARATE DE HOY"
      pregunta="¿Qué vende hoy el Computer, y cuál nos haría ganar puntos?"
      pill={<span className="c2-pill">{jugadores.length} a la venta</span>}
    >
      {!jugadores.length ? (
        <SinDato>El Computer no tiene a nadie a la venta en esta foto.</SinDato>
      ) : (
        <>
          <p className="c2-frase">
            {mejoran
              ? `${mejoran} de ${jugadores.length} mejorarían nuestro once.`
              : "Ninguno mejoraría nuestro once."}
          </p>
          <ul className="c2-jugs">
            {primeros.map((p) => (
              <Jugador key={p.id} p={p} vivas={vivas} prohibidos={prohibidos} />
            ))}
          </ul>
          {resto.length > 0 && (
            <details className="c2-mas">
              <summary>Ver los otros {resto.length}</summary>
              <ul className="c2-jugs">
                {resto.map((p) => (
                  <Jugador key={p.id} p={p} vivas={vivas} prohibidos={prohibidos} />
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </Tarjeta>
  );
}
