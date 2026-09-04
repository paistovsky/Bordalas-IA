import { formatMoney } from "../lib/utils";

/**
 * EN QUE CARRERA VA PEPE (05/09/2026)
 *
 *   Pepe no sabia que iba cuarto. Nada en el codigo leia la
 *   clasificacion: pujaria igual siendo primero con veinte de
 *   ventaja que ultimo a cuarenta.
 *
 *   Este panel no cambia eso —el motor sigue decidiendo igual—
 *   pero pone el marcador delante: puesto, distancia, lo que
 *   queda de temporada, cuanto hay que sacarle al lider cada
 *   jornada, y la brecha de plantilla contra los seis.
 *
 * POR QUE EL RITMO Y NO SOLO LA DISTANCIA
 *
 *   "A 13 puntos" no dice nada sin saber cuanta temporada queda.
 *   Trece puntos en la jornada 4 y trece en la 35 son la misma
 *   distancia y no son el mismo problema.
 *
 * LA COLUMNA DE PLANTILLA ES LA BRECHA DE VERDAD
 *
 *   47,7 M contra 69 M. Es lo que explica por que arriba pueden
 *   pujar por lo que Pepe no puede, y estaba repartida en dos
 *   tablas distintas sin que nadie las restara.
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

/** Un porcentaje pequeño con la precisión que le hace falta. */
function porcentaje(share) {
  if (share == null) return null;
  const n = Number(share) * 100;
  if (!Number.isFinite(n)) return null;
  return `${n < 1 ? n.toFixed(2) : n.toFixed(1)} %`.replace(".", ",");
}

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
  const exigencia = porcentaje(race.required_pace_share);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA CARRERA</h2>
          <div className="sub">
            Dónde va Pepe y cuánto le queda por recuperar
          </div>
        </div>
        <span className={tono}>{etiqueta}</span>
      </div>

      {/* La frase primero. Es lo que se lee de un vistazo. */}
      <div className="godnote" style={{ marginBottom: 10 }}>
        {race.headline}
      </div>

      <div className="poswrap" style={{ marginBottom: 10 }}>
        <div className="poscel">
          <b>PUESTO</b>
          <span className="big">{race.position ?? "—"}º</span>
          <small>{race.points} puntos</small>
        </div>

        <div className="poscel">
          <b>AL LÍDER</b>
          <span className="big">
            {race.is_leader ? `+${race.points_ahead ?? 0}` : race.points_behind}
          </span>
          <small>{race.leader_name || "—"}</small>
        </div>

        <div className="poscel">
          <b>QUEDAN</b>
          <span className="big">{race.matchdays_remaining ?? "—"}</span>
          <small>
            de {race.matchdays_total} · {race.matchdays_played ?? "?"} jugadas
          </small>
        </div>

        <div className="poscel">
          <b>RITMO</b>
          <span className="big">
            {race.required_pace != null
              ? String(race.required_pace.toFixed(2)).replace(".", ",")
              : "—"}
          </span>
          <small>
            {exigencia ? `${exigencia} de una jornada` : "por jornada"}
          </small>
        </div>

        <div className="poscel">
          <b>PLANTILLA</b>
          <span className="big">{formatMoney(race.team_value)}</span>
          <small>
            {race.value_gap_to_leader != null
              ? `${formatMoney(Math.abs(race.value_gap_to_leader))} ${
                  race.value_gap_to_leader > 0 ? "menos" : "más"
                } que el líder`
              : "sin comparación"}
          </small>
        </div>
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
