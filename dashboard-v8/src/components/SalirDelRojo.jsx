import Tarjeta from "./Tarjeta";
import { cuando, millones, saldo as saldoDe } from "../lib/lectura";

/* CÓMO SALIMOS DEL ROJO (30/09/2026)
 *
 * El dueño lo pidió así: «esto tengo que verlo en la estrategia».
 * La hoja de ruta que el gestor escribe en la orden
 * (`orden.hoja_de_ruta`): el objetivo, y cada paso con su fecha y su
 * estado (hecho / en marcha / pendiente / solo si hace falta), más el
 * saldo de hoy y los viajes cortos en marcha. Sin hoja de ruta, no se
 * pinta.
 */

const ESTADO = {
  hecho: { txt: "HECHO", cls: "on" },
  "en marcha": { txt: "EN MARCHA", cls: "marcha" },
  pendiente: { txt: "PENDIENTE", cls: "" },
  "solo si hace falta": { txt: "SI HACE FALTA", cls: "" }
};

export default function SalirDelRojo({ data }) {
  const ahora = new Date();
  const hoja = data?.orden?.hoja_de_ruta;
  if (!hoja || !Array.isArray(hoja.pasos) || hoja.pasos.length === 0) return null;

  const s = saldoDe(data);
  const saldo = s == null ? NaN : Number(s);
  const viajes = data?.orden?.viajes || {};
  const candidatos = (viajes.candidatos || []).filter((c) => c && c.nombre);
  const pasos = [...hoja.pasos].sort(
    (a, b) => new Date(a.fecha || 0) - new Date(b.fecha || 0)
  );

  return (
    <Tarjeta
      titulo={(hoja.titulo || "Cómo salimos del rojo").toUpperCase()}
      pregunta={hoja.objetivo || "¿Cómo volvemos a saldo positivo antes de la jornada?"}
      className="c2-rojo"
      pill={
        Number.isFinite(saldo) ? (
          <span className={`c2-pill ${saldo >= 0 ? "on" : ""}`}>
            SALDO {millones(saldo)}
          </span>
        ) : null
      }
    >
      <ul className="c2-filas c2-ruta">
        {pasos.map((p, i) => {
          const e = ESTADO[p.estado] || { txt: String(p.estado || "").toUpperCase(), cls: "" };
          return (
            <li key={i} className={p.estado === "hecho" ? "hecho" : ""}>
              <span>
                {p.que}
                <small>{p.fecha ? cuando(new Date(p.fecha), ahora) : ""}</small>
              </span>
              <b className={`c2-pill ${e.cls}`}>{e.txt}</b>
            </li>
          );
        })}
      </ul>

      <div className="c2-bloque">
        <div className="c2-bloque-t">Viajes cortos en marcha</div>
        {candidatos.length ? (
          <ul className="c2-filas">
            {candidatos.map((c) => (
              <li key={c.nombre}>
                <span>
                  {c.nombre}
                  <small>Se revende al Computer en cuanto ofrezca más de lo pagado.</small>
                </span>
                <b>{millones(c.puja)}</b>
              </li>
            ))}
          </ul>
        ) : (
          <p className="c2-pie">
            Todavía ninguno: el gestor los elige cada mañana con el mercado nuevo
            (máx. {millones(viajes.tope_por_viaje)} por viaje y {millones(viajes.tope_total)} en total).
          </p>
        )}
      </div>
    </Tarjeta>
  );
}
