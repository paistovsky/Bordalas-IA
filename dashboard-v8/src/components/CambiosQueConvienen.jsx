import Tarjeta from "./Tarjeta";
import { millones } from "../lib/lectura";

/* CAMBIOS QUE NOS CONVIENEN (30/09/2026)
 *
 * Lo publica el comparador de cambios (`cambios`): por cada fichaje
 * del Computer que juega, a quién de los nuestros venderíamos, cuántos
 * puntos por partido ganamos o perdemos y cómo queda la caja. No
 * decide nada: el gestor lo convierte en orden.
 */

const POS = { 1: "POR", 2: "DEF", 3: "MED", 4: "DEL" };

function signo(n, dec = 2) {
  const v = Number(n || 0);
  return `${v > 0 ? "+" : ""}${v.toFixed(dec).replace(".", ",")}`;
}

export default function CambiosQueConvienen({ data }) {
  const c = data?.cambios;
  if (!c || !c.ok) return null;
  const filas = c.cambios || [];

  return (
    <Tarjeta
      titulo="CAMBIOS QUE NOS CONVIENEN"
      pregunta="¿A quién vendemos para fichar a quién, en puntos y en caja?"
      pill={<span className="c2-pill">{c.n || 0}</span>}
    >
      {filas.length ? (
        <ul className="c2-filas">
          {filas.map((f) => (
            <li key={`${f.ficha_id}-${f.vende_id}`}>
              <span>
                {POS[f.posicion] || ""} · Entra {f.ficha} ({millones(f.ficha_precio)}),
                sale {f.vende} ({millones(f.vende_precio)})
                <small>
                  {signo(f.puntos)} pts/partido ({f.ficha_tasa} contra {f.vende_tasa})
                  {f.saca_del_rojo ? " · nos saca del rojo" : ""}
                </small>
              </span>
              <b className={`c2-pill ${f.gana_las_dos ? "on" : ""}`}>
                {f.caja >= 0 ? "+" : "−"}{millones(Math.abs(f.caja))}
              </b>
            </li>
          ))}
        </ul>
      ) : (
        <p className="c2-pie">
          Hoy ningún jugador del Computer nos sube puntos o nos da caja sin perderlos.
        </p>
      )}
      <p className="c2-pie">
        En verde, los que suben puntos y además dejan dinero. La venta se cuenta a
        precio de mercado; Yamal y los protegidos no entran.
      </p>
    </Tarjeta>
  );
}
