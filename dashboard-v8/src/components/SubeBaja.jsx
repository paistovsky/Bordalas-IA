import Tarjeta, { SinDato } from "./Tarjeta";
import { conSigno, millones, plantilla } from "../lib/lectura";

/* LO QUE SUBE Y LO QUE BAJA (30/09/2026)
 *
 * El movimiento de precio de hoy (`price_increment`): cuánto ha
 * ganado o perdido nuestra plantilla, y los cinco que más suben y
 * más bajan de toda la liga, con de quién son. Verde para lo que
 * sube; lo que baja, en gris: no es un aviso.
 */

const DE_QUIEN = {
  nuestro: "nuestro",
  rival: "de un rival",
  computer: "en el mercado",
  libre: "libre"
};

function Lista({ filas }) {
  return (
    <ul className="c2-filas c2-compacta">
      {filas.map((p) => {
        const d = Number(p.price_increment || 0);
        return (
          <li key={p.id}>
            <span>
              {p.name}
              <small>{DE_QUIEN[p.de_quien] || "—"} · vale {millones(p.price)}</small>
            </span>
            <b className={d > 0 ? "sube" : "baja"}>{conSigno(d)}</b>
          </li>
        );
      })}
    </ul>
  );
}

export default function SubeBaja({ data }) {
  const liga = data.todaLaLiga || {};
  const todos = (liga.players || []).filter((p) => Number.isFinite(Number(p.price_increment)));

  if (!liga.available || !todos.length) {
    return (
      <Tarjeta titulo="LO QUE SUBE Y LO QUE BAJA" pregunta="¿Cómo se mueven hoy los precios?">
        <SinDato>Esta foto no trae los precios de la liga.</SinDato>
      </Tarjeta>
    );
  }

  const suben = [...todos].filter((p) => Number(p.price_increment) > 0)
    .sort((a, b) => b.price_increment - a.price_increment).slice(0, 5);
  const bajan = [...todos].filter((p) => Number(p.price_increment) < 0)
    .sort((a, b) => a.price_increment - b.price_increment).slice(0, 5);

  const nuestros = plantilla(data);
  const hoy = nuestros.reduce((a, p) => a + Number(p.price_increment || 0), 0);
  const subenNuestros = nuestros.filter((p) => Number(p.price_increment) > 0).length;
  const bajanNuestros = nuestros.filter((p) => Number(p.price_increment) < 0).length;

  return (
    <Tarjeta titulo="LO QUE SUBE Y LO QUE BAJA" pregunta="¿Cómo se mueven hoy los precios?">
      {nuestros.length > 0 && (
        <div className="c2-destacado">
          <span>Nuestra plantilla hoy</span>
          <b className={hoy > 0 ? "sube" : ""}>{conSigno(hoy)}</b>
          <small>
            {subenNuestros} suben · {bajanNuestros} bajan · {nuestros.length - subenNuestros - bajanNuestros} quietos
          </small>
        </div>
      )}

      <div className="c2-dos">
        <div>
          <div className="c2-bloque-t">Los que más suben</div>
          {suben.length ? <Lista filas={suben} /> : <SinDato>Hoy no sube nadie.</SinDato>}
        </div>
        <div>
          <div className="c2-bloque-t">Los que más bajan</div>
          {bajan.length ? <Lista filas={bajan} /> : <SinDato>Hoy no baja nadie.</SinDato>}
        </div>
      </div>
    </Tarjeta>
  );
}
