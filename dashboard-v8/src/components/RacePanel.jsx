import { formatMoney } from "../lib/utils";

/**
 * EN QUE CARRERA VA PEPE (05/09/2026)
 *
 *   Pepe no sabia que iba cuarto. Nada en el codigo leia la
 *   clasificacion: pujaria igual siendo primero con veinte de
 *   ventaja que ultimo a cuarenta.
 *
 *   Este panel no cambia eso —el motor sigue decidiendo igual—
 *   pero pone el marcador delante.
 *
 * MENOS CAJA Y MAS LINEA (05/09/2026, tarde)
 *
 *   El dueño: "me ha metido un cuadro 'La Carrera' que no me
 *   gusta nada. Al menos, que lo baje abajo, que esta
 *   descuadrado."
 *
 *   Lo de descuadrado era literal y tenia una causa exacta:
 *   `.poswrap` es `repeat(4, 1fr)` en la hoja de estilos y aqui
 *   habia CINCO `.poscel`. El quinto caia solo a una segunda
 *   fila y dejaba media fila vacia. Encima el titular iba en un
 *   `.godnote` sin modificador, y esa clase solo tiene fondo y
 *   borde en sus variantes `.crit` y `.warn`: quedaba un bloque
 *   de texto en negrita flotando.
 *
 *   Los cinco cajones decian lo mismo que la frase que ya
 *   calcula el backend. Asi que se quedan la frase y la tabla,
 *   que es el dato que no esta en ningun otro sitio: la brecha
 *   de plantilla contra los seis rivales.
 *
 * POR QUE EL RITMO Y NO SOLO LA DISTANCIA
 *
 *   "A 13 puntos" no dice nada sin saber cuanta temporada queda.
 *   Trece puntos en la jornada 4 y trece en la 35 son la misma
 *   distancia y no son el mismo problema.
 */

const URGENCIA = {
  LIDER: ["pill ok", "VAS PRIMERO"],
  COMODA: ["pill ok", "DISTANCIA CORTA"],
  EXIGENTE: ["pill warn", "EXIGENTE"],
  DIFICIL: ["pill warn", "DIFÍCIL"],
  MUY_DIFICIL: ["pill crit", "MUY DIFÍCIL"],
  FUERA_DE_ALCANCE: ["pill crit", "FUERA DE ALCANCE"],
  SIN_DATOS: ["pill idle", "SIN DATOS"]
};

function diferencia(valor, formato) {
  const n = Number(valor || 0);
  if (n === 0) return <span className="dim">—</span>;
  return (
    <span className={n > 0 ? "down" : "up"}>
      {n > 0 ? "+" : "−"}
      {formato(Math.abs(n))}
    </span>
  );
}

export default function RacePanel({ data }) {
  const race = data.race || { available: false };

  if (!race.available) {
    return (
      <section className="pan">
        <h2>LA CARRERA</h2>
        <div className="empty">
          {race.reason || "Sin clasificación disponible."}
        </div>
      </section>
    );
  }

  const [tono, etiqueta] = URGENCIA[race.urgency] || URGENCIA.SIN_DATOS;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA CARRERA</h2>

          {/* La frase, y ya. Es lo que se lee de un vistazo y es
              la misma que calcula el backend: no se rearma aqui
              con cinco cajones para decir lo mismo. */}
          <div className="sub" style={{ textTransform: "none" }}>
            {race.headline}
          </div>
        </div>
        <span className={tono}>{etiqueta}</span>
      </div>

      {/* Ausencia de dato != dato: si no hay calendario no hay
          ritmo, y se dice en vez de enseñar un hueco mudo. */}
      {race.calendar_available === false && (
        <div className="alert warn">{race.calendar_reason}</div>
      )}

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>MÁNAGER</th>
            <th className="n">PTS</th>
            <th className="n">VS MÍ</th>
            <th className="n">PLANTILLA</th>
            <th className="n">VS MÍ</th>
            <th className="n">FICHAS</th>
          </tr>
        </thead>
        <tbody>
          {(race.managers || []).map((manager) => (
            <tr
              key={manager.user_id || manager.name}
              className={manager.is_current_user ? "me" : ""}
            >
              <td className="dim">{manager.rank ?? "—"}º</td>
              <td>
                {manager.name}
                {manager.is_current_user && (
                  <span className="pill me" style={{ marginLeft: 6 }}>
                    TÚ
                  </span>
                )}
                {manager.is_leader && !manager.is_current_user && (
                  <span className="pill ok" style={{ marginLeft: 6 }}>
                    LÍDER
                  </span>
                )}
              </td>
              <td className="n">{manager.points}</td>
              <td className="n">
                {manager.is_current_user ? (
                  <span className="dim">—</span>
                ) : (
                  diferencia(manager.points_vs_us, (n) => n)
                )}
              </td>
              <td className="n">{formatMoney(manager.team_value)}</td>
              <td className="n">
                {manager.is_current_user ? (
                  <span className="dim">—</span>
                ) : (
                  diferencia(manager.value_vs_us, formatMoney)
                )}
              </td>
              <td className="n dim">{manager.squad_size || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="note" style={{ textAlign: "left" }}>
        Esto es un termómetro: Pepe <b>no</b> lo usa para decidir. Puja
        igual fuese primero o último.
      </p>
    </section>
  );
}
