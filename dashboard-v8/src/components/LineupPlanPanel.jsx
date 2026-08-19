import { formatMoney } from "../lib/utils";

/**
 * EL PLAN DE BORDALAS: que sistema, por que ese once, que busca.
 *
 * POR QUE HACE FALTA
 *
 *   El campo enseña once caras y una formacion. Lo que no
 *   enseñaba es el razonamiento: por que un 5-3-2 y no un 4-4-2,
 *   por que ese lateral y no el otro, y de donde espera sacar
 *   los puntos.
 *
 *   Todo eso ya estaba calculado. El motor de alineacion elige
 *   por valor esperado semanal -jerarquia por probabilidad de
 *   ser titular- y desde el 18/08 mete tambien el rival y el
 *   campo. Ninguno de esos numeros llegaba a una frase.
 *
 * LO QUE NO HACE
 *
 *   No decide nada ni recalcula: lee lo que el motor ya decidio
 *   y lo cuenta. Si mañana cambia la regla, cambia el texto.
 */

const POSICIONES = { 1: "POR", 2: "DEF", 3: "MC", 4: "DEL" };

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

function porPosicion(players = []) {
  const cuenta = { 1: 0, 2: 0, 3: 0, 4: 0 };

  players.forEach((p) => {
    const pos = Number(p.position);
    if (cuenta[pos] != null) cuenta[pos] += 1;
  });

  return cuenta;
}

/* El nombre del sistema sale de contar, no de un campo: asi no
   puede desfasarse respecto a los jugadores que se pintan. */
function sistema(cuenta) {
  return `${cuenta[2]}-${cuenta[3]}-${cuenta[4]}`;
}

function formaDelEquipo(cuenta) {
  const def = cuenta[2];
  const del = cuenta[4];

  if (def >= 5 && del <= 2) {
    return "Repliegue: mayoria atras y el peso ofensivo en pocas botas.";
  }

  if (del >= 3) {
    return "Apuesta ofensiva: tres arriba buscando goles.";
  }

  if (cuenta[3] >= 4) {
    return "Control por dentro: el centro del campo manda.";
  }

  return "Reparto equilibrado entre lineas.";
}

function partido(player) {
  const match = player.next_match;

  if (!match || !match.rival) return null;

  return `${match.away ? "fuera" : "en casa"} vs ${match.rival}`;
}

export default function LineupPlanPanel({ lineup, guardrail }) {
  const players = lineup?.players || [];

  if (players.length === 0) {
    return (
      <section className="pan">
        <h2>EL PLAN DE BORDALÁS</h2>
        <div className="empty">Sin XI calculado en este ciclo.</div>
      </section>
    );
  }

  const cuenta = porPosicion(players);

  const conProbabilidad = players.filter(
    (p) => p.starter_probability != null
  );

  const probabilidadMedia = conProbabilidad.length
    ? Math.round(
        conProbabilidad.reduce(
          (total, p) => total + Number(p.starter_probability || 0),
          0
        ) / conProbabilidad.length
      )
    : null;

  const seguros = players.filter(
    (p) => Number(p.starter_probability || 0) >= 80
  ).length;

  const dudosos = players
    .filter(
      (p) =>
        p.starter_probability != null &&
        Number(p.starter_probability) < 60
    )
    .sort(
      (a, b) =>
        Number(a.starter_probability) - Number(b.starter_probability)
    );

  /* Los que sostienen la jornada: mas valor esperado. No es el
     mas caro ni el de mas jerarquia, es el que mas puntos se
     espera que traiga ESTA semana. */
  const pilares = [...players]
    .filter((p) => p.weekly_expected_value != null)
    .sort(
      (a, b) =>
        Number(b.weekly_expected_value) - Number(a.weekly_expected_value)
    )
    .slice(0, 3);

  const jerarquias = [...players].sort(
    (a, b) =>
      (ORDEN_JERARQUIA[String(b.hierarchy || "").toUpperCase()] ?? -1) -
      (ORDEN_JERARQUIA[String(a.hierarchy || "").toUpperCase()] ?? -1)
  );

  const columna = jerarquias.slice(0, 3);

  const fuera = lineup?.mandatory_hierarchy?.ruled_out || [];

  const sinDato = players.length - conProbabilidad.length;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL PLAN DE BORDALÁS</h2>
          <div className="sub">POR QUÉ ESTE ONCE Y NO OTRO</div>
        </div>
        <span className={lineup.missing ? "pill crit" : "pill ok"}>
          {lineup.playable ?? 0}/11
        </span>
      </div>

      <div className="planbox">
        <div className="planbox-system">{sistema(cuenta)}</div>
        <div className="planbox-shape">{formaDelEquipo(cuenta)}</div>
      </div>

      <div className="kv">
        <span>Titularidad media del once</span>
        <b className={probabilidadMedia >= 70 ? "up" : "down"}>
          {probabilidadMedia != null ? `${probabilidadMedia}%` : "—"}
        </b>
      </div>

      <div className="kv">
        <span>Titulares seguros (80% o más)</span>
        <b>{seguros} de 11</b>
      </div>

      <div className="kv">
        <span>Valor del once</span>
        <b className="mono">{formatMoney(lineup.total_value)}</b>
      </div>

      {/* Sin dato no es dato: si a alguien le falta el pronostico
          se dice, porque la media de arriba se calcula sin el. */}
      {sinDato > 0 && (
        <div className="kv">
          <span>Sin pronóstico de titular</span>
          <b className="down">{sinDato}</b>
        </div>
      )}

      <div className="planwhy">
        <b>DE DÓNDE ESPERA LOS PUNTOS</b>
        <ul>
          {pilares.map((p) => (
            <li key={p.id}>
              <b>{p.name}</b>{" "}
              <span className="dim">
                ({POSICIONES[p.position] || "?"}
                {p.hierarchy ? ` · ${p.hierarchy}` : ""}
                {p.starter_probability != null
                  ? ` · ${Math.round(p.starter_probability)}% titular`
                  : ""}
                {partido(p) ? ` · ${partido(p)}` : ""})
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="planwhy">
        <b>LA COLUMNA VERTEBRAL</b>
        <ul>
          {columna.map((p) => (
            <li key={p.id}>
              <b>{p.name}</b>{" "}
              <span className="dim">
                {p.hierarchy || "sin escalón"} en {p.team_name || "su equipo"}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {dudosos.length > 0 && (
        <div className="planwhy">
          <b>LO QUE LE PREOCUPA</b>
          <ul>
            {dudosos.slice(0, 3).map((p) => (
              <li key={p.id}>
                <b>{p.name}</b>{" "}
                <span className="dim">
                  solo {Math.round(p.starter_probability)}% de salir
                  {p.availability && p.availability !== "DISPONIBLE"
                    ? ` · ${p.availability}`
                    : ""}
                  {partido(p) ? ` · ${partido(p)}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Un Dios fuera del once es la excepcion a la regla del
          dueño y no puede pasar en silencio. */}
      {fuera.length > 0 && (
        <div className="alert" style={{ marginTop: 10, marginBottom: 0 }}>
          FUERA DEL ONCE:{" "}
          {fuera
            .map((god) => `${god.name} (${god.reason || "sin motivo"})`)
            .join(" · ")}
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        El sistema no se elige antes: sale de coger a los once con más valor
        esperado esta semana y ver en qué formación caben. Valor esperado =
        lo que puntúa su escalón en el equipo × lo probable que es que salga
        de inicio, ajustado por el rival y por si juega en casa.
        {guardrail?.goalkeeper_warning ? ` ${guardrail.goalkeeper_warning}` : ""}
      </p>
    </section>
  );
}
