import { positionLabel } from "../lib/utils";

/* EL CALENDARIO (13/09/2026, noche)
 *
 * CONTRA QUIÉN JUEGA CADA UNO DE LOS NUESTROS.
 *
 *   `laliga_calendar.json` lleva vivo desde siempre —380
 *   partidos, refrescado hoy— y no lo miraba nadie: ni una
 *   decisión, ni una pantalla. Era el mejor dato desaprovechado
 *   que teníamos.
 *
 * ESTO NO DECIDE NADA. Ninguna puja y ninguna venta salen de
 * aquí. Primero hay que ver si dice cosas sensatas.
 *
 * LO QUE NO CASA SE DICE
 *
 *   Las fichas del calendario casan con las de la clasificación
 *   por nombre. Hoy casan las veinte. El día que una no case,
 *   sale con su nombre y sin puesto — no desaparece en silencio,
 *   porque una fila que falta no la echa de menos nadie.
 */

const POS = { 1: "por", 2: "def", 3: "med", 4: "del" };

const ESCUDO = "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/";

/* El color del rival por su puesto. El reparto NO está medido y
   el pie del cuadro lo dice. */
const TRAMO = {
  duro: "t-duro",
  normal: "t-normal",
  blando: "t-blando",
  "sin dato": "t-sindato"
};

const VEREDICTO = {
  "tramo blando": "v-blando",
  normal: "v-normal",
  "tramo duro": "v-duro",
  "sin dato": "v-sindato",
  "sin partidos": "v-sindato"
};

function cuando(kickoff) {
  if (!kickoff) return "sin hora";

  const d = new Date(kickoff);

  if (Number.isNaN(d.getTime())) return "sin hora";

  return d.toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export default function ElCalendarioPanel({ data }) {
  const cal = data.elCalendario || {};

  if (!cal.available) {
    return (
      <section className="pan">
        <h2>EL CALENDARIO</h2>
        <div className="empty">
          {cal.reason || "No llegó el calendario de LaLiga."}
        </div>
      </section>
    );
  }

  const equipos = cal.equipos || [];

  const tramos = cal.tramos_sin_medir || {};

  return (
    <section className="pan">
      {/* LO QUE NO CASA, ARRIBA Y CON NOMBRE. */}
      {cal.sin_casar && cal.sin_casar.length ? (
        <p className="aviso-ambar">
          <b>
            {cal.sin_casar.length} ficha(s) del calendario no
            casan con la clasificación:
          </b>{" "}
          {cal.sin_casar.join(", ")}. Sus partidos salen igual,
          pero con el puesto del rival sin dato.
        </p>
      ) : null}

      <div className="pan-head">
        <div>
          <h2>EL CALENDARIO</h2>
          <p className="sub">
            {cal.partidos} partidos · {equipos.length} equipos
            nuestros · de más blando a más duro
          </p>
        </div>
        <span className="pill idle">SOLO MIRAR</span>
      </div>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>EQUIPO</th>
              <th>LOS NUESTROS</th>
              <th>LOS TRES PRÓXIMOS</th>
              <th className="r">PUESTO MEDIO</th>
              <th>QUÉ LE VIENE</th>
            </tr>
          </thead>
          <tbody>
            {equipos.map((eq) => (
              <tr key={eq.team_id}>
                <td className="q">
                  {eq.team_id ? (
                    <img
                      className="esc"
                      src={`${ESCUDO}${eq.team_id}.png`}
                      alt=""
                      onError={(e) => {
                        e.currentTarget.style.visibility = "hidden";
                      }}
                    />
                  ) : null}
                  <span className="nm">
                    {eq.team || "sin casar"}
                  </span>{" "}
                  {eq.puesto ? (
                    <span className="ref">{eq.puesto}º</span>
                  ) : (
                    <span className="unk">sin puesto</span>
                  )}
                </td>

                <td className="pw">
                  {(eq.jugadores || []).map((j) => (
                    <span key={j.id} className="minijug">
                      {j.name}{" "}
                      <span className={`pos ${POS[j.position] || ""}`}>
                        {positionLabel(j.position)}
                      </span>
                    </span>
                  ))}
                </td>

                <td className="partidos">
                  {(eq.proximos || []).length ? (
                    (eq.proximos || []).map((p, i) => (
                      <span
                        key={i}
                        className={`part ${TRAMO[p.tramo] || "t-sindato"}`}
                        title={`Jornada ${p.jornada ?? "?"} · ${cuando(
                          p.kickoff
                        )}`}
                      >
                        {p.en_casa ? "vs" : "@"} {p.rival}
                        {p.rival_puesto ? (
                          <b> {p.rival_puesto}º</b>
                        ) : (
                          <b className="unk"> sin puesto</b>
                        )}
                      </span>
                    ))
                  ) : (
                    <span className="unk">
                      sin partidos por delante
                    </span>
                  )}
                </td>

                <td className="ppm">
                  {eq.media_del_rival == null ? (
                    <span className="unk">—</span>
                  ) : (
                    <b>{eq.media_del_rival}</b>
                  )}
                </td>

                <td className="ac">
                  <span
                    className={VEREDICTO[eq.veredicto] || "v-sindato"}
                  >
                    {eq.veredicto}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        Los tres próximos son <b>por reloj, no por número de
        jornada</b>: en esta liga hay partidos aplazados —la
        jornada 6 tiene uno el 3 de septiembre, antes que toda la
        jornada 5— y ordenar por jornada pondría como «próximo»
        uno ya jugado.{" "}
        <b>
          El reparto de colores (1–{tramos.duro_hasta} duro, hasta{" "}
          {tramos.normal_hasta} normal, el resto blando) NO está
          medido
        </b>
        : son tres grupos de tamaño parecido sobre veinte equipos,
        y no decide nada. <b>Este cuadro no decide nada</b>: es
        para ver si dice cosas sensatas.
      </p>
    </section>
  );
}
