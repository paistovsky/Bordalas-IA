import { Lesion, Sancion } from "./AbsenceCells";
import { formatEuros, formatMoney, positionLabel } from "../lib/utils";

/**
 * UNA PLANTILLA, LA MIA O LA DE CUALQUIER RIVAL.
 *
 * EL CASO (20/08/2026)
 *
 *   "¿Sabes lo que no veo? La plantilla del rival."
 *
 *   Y la propia tampoco se veia del todo. La tabla enseñaba
 *   nombre, posicion, valor y titular o suplente. La jerarquia,
 *   el porcentaje de salir de inicio y el parte de lesion o
 *   sancion se calculaban en cada ciclo y solo llegaban al XI
 *   -once de dieciseis- y a la tabla del mercado.
 *
 * LA MISMA TABLA PARA TODOS
 *
 *   Es el mismo componente para mi plantilla y para las seis de
 *   los rivales, a proposito: comparar exige que las dos cosas
 *   se cuenten igual. Si un dia una columna cambia, cambia en
 *   las siete.
 *
 * LO QUE SIGNIFICAN LAS DOS SEÑALES
 *
 *   JERARQUIA es estructural: que es ese jugador en su equipo, y
 *   aguanta la temporada.
 *   % TITULAR es de esta semana y cambia cada viernes.
 *
 *   No miden lo mismo y por eso van en columnas distintas. Un
 *   Rotacion al 90 % juega este sabado; un Clave al 50 % es
 *   mejor jugador.
 */

const ORDEN_JERARQUIA = {
  DIOS: 6,
  CLAVE: 5,
  IMPORTANTE: 4,
  ROTACION: 3,
  "ROTACIÓN": 3,
  REVULSIVO: 2,
  RESERVA: 1,
  DESCARTE: 0
};

function tonoJerarquia(label) {
  const orden = ORDEN_JERARQUIA[String(label || "").toUpperCase()];

  if (orden == null) return "pill idle";
  if (orden >= 5) return "pill ok";
  if (orden >= 3) return "pill";
  return "pill idle";
}

function Titularidad({ value }) {
  // Un 0 % y "no lo sabemos" no son lo mismo. El 16/08 el
  // dashboard pinto once barras vacias porque la fuente habia
  // fallado, y parecia que el equipo no jugaba.
  if (value == null) {
    return <span className="dim">sin dato</span>;
  }

  const n = Math.round(Number(value));

  return (
    <span className={n >= 67 ? "up" : n >= 40 ? "" : "down"}>
      {n}%
    </span>
  );
}

export default function SquadTable({ players = [], showStarterColumn = true }) {
  if (players.length === 0) {
    return <div className="empty">Sin jugadores que enseñar.</div>;
  }

  // Once columnas no caben en media pantalla. Antes que quitar
  // datos, se deja rodar en horizontal: el dueño pidio MAS
  // informacion, no menos.
  return (
    <div className="scroll" style={{ overflowX: "auto" }}>
      <table>
        <thead>
          <tr>
            <th>JUGADOR</th>
            <th>POS</th>
            <th>EQUIPO</th>
            <th>JERARQUÍA</th>
            <th className="n">% TITULAR</th>
            <th className="n">PUNTOS</th>
            <th>LESIÓN</th>
            <th>SANCIÓN</th>
            <th className="n">VALOR</th>
            <th className="n">CAMBIO</th>
            {showStarterColumn && <th></th>}
          </tr>
        </thead>
        <tbody>
          {players.map((player) => {
            const increment = Number(player.price_increment || 0);

            return (
              <tr key={player.id}>
                <td>{player.name}</td>
                <td className="dim">{positionLabel(player.position)}</td>
                <td className="dim">{player.team_name || "—"}</td>
                <td>
                  {player.hierarchy ? (
                    <span className={tonoJerarquia(player.hierarchy)}>
                      {player.hierarchy}
                    </span>
                  ) : (
                    <span className="dim">sin dato</span>
                  )}
                </td>
                <td className="n">
                  <Titularidad value={player.starter_probability} />
                </td>
                <td className="n mono">{player.points ?? 0}</td>
                <td>
                  <Lesion
                    absence={player.absence}
                    availability={player.availability}
                  />
                </td>
                <td>
                  <Sancion absence={player.absence} />
                </td>
                <td className="n">{formatEuros(player.price)}</td>
                <td
                  className={
                    increment > 0
                      ? "n up"
                      : increment < 0
                      ? "n down"
                      : "n flat"
                  }
                >
                  {increment > 0 ? "▲" : increment < 0 ? "▼" : "—"}{" "}
                  {increment ? formatMoney(Math.abs(increment)) : ""}
                </td>
                {showStarterColumn && (
                  <td>
                    <span
                      className={
                        player.is_starter ? "pill ok" : "pill idle"
                      }
                    >
                      {player.is_starter ? "TITULAR" : "SUPLENTE"}
                    </span>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
