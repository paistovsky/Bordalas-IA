import { formatEuros } from "../lib/utils";

/* LOS RIVALES (13/09/2026, noche)
 *
 *   La clasificación dice el puesto y los puntos. No dice lo
 *   único que explica la diferencia entre dos mánagers con los
 *   mismos puntos: cuánto les cuesta hacerlos.
 *
 * LOS PUESTOS VIENEN CONTADOS
 *
 *   «Somos segundos en puntos por millón» lo calcula
 *   `los_rivales.py` ordenando y buscándose. Aquí no se escribe
 *   ninguna posición: el dueño puso «primeros» a mano en la
 *   primera versión de la previa y éramos segundos.
 *
 * Y EL RATIO SE LEE CON EL TAMAÑO DE PLANTILLA AL LADO
 *
 *   Álvaro Retamosa saca 3,94 por millón con nueve fichas y
 *   24,9 M. No es mejor gestión: es que ha liquidado casi todo.
 *   Sin las fichas al lado, ese número miente.
 */

const AVATAR = "https://cdn.biwenger.com/";

export default function LosRivalesPanel({ data }) {
  const bloque = data.losRivales || {};

  if (!bloque.available) {
    return (
      <section className="pan">
        <h2>LOS RIVALES</h2>
        <div className="empty">
          {bloque.reason || "No llegó la clasificación."}
        </div>
      </section>
    );
  }

  const managers = bloque.managers || [];

  const lectura = bloque.lectura || {};

  const mejor = lectura.mejor_por_millon;

  /* La barrita se escala contra el mejor de la tabla, no contra
     un tope inventado: así el más alto llena y el resto se leen
     en relación a él. */
  const techo = Math.max(
    ...managers.map((m) => m.puntos_por_millon || 0),
    0.01
  );

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LOS RIVALES</h2>
          <p className="sub">
            {managers.length} mánagers · puntos, plantilla y lo
            que sacan por millón
          </p>
        </div>
      </div>

      {/* LA LECTURA, CON LOS PUESTOS CONTADOS. */}
      {lectura.available ? (
        <p className="reparto">
          Somos <b>{lectura.por_puntos}º de {lectura.total}</b> por
          puntos,{" "}
          <b>
            {lectura.por_plantilla == null
              ? "sin dato"
              : `${lectura.por_plantilla}º`}
          </b>{" "}
          por tamaño de plantilla y{" "}
          <b>
            {lectura.por_millon == null
              ? "sin dato"
              : `${lectura.por_millon}º`}
          </b>{" "}
          por puntos por millón.
          {mejor && !mejor.es_nuestro ? (
            <>
              {" "}
              Por encima está <b>{mejor.name}</b> con{" "}
              <b>{mejor.puntos_por_millon}</b>, que saca más
              porque tiene {mejor.fichas} fichas y{" "}
              {formatEuros(mejor.roster_value)} de plantilla:{" "}
              <b>un ratio alto con plantilla mínima no es
              eficiencia</b>.
            </>
          ) : null}
        </p>
      ) : (
        <p className="reparto">
          <b className="mal">{lectura.reason}</b>
        </p>
      )}

      {bloque.sin_plantilla && bloque.sin_plantilla.length ? (
        <p className="aviso-ambar">
          <b>
            {bloque.sin_plantilla.length} mánager(s) sin plantilla
            cruzada:
          </b>{" "}
          {bloque.sin_plantilla.join(", ")}. Sus fichas salen sin
          dato.
        </p>
      ) : null}

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th className="ctr">#</th>
              <th>MÁNAGER</th>
              <th className="r">PUNTOS</th>
              <th className="r">A NUESTRO NIVEL</th>
              <th className="n">PLANTILLA</th>
              <th className="r">FICHAS</th>
              <th className="n">CAJA</th>
              <th className="n">PATRIMONIO</th>
              <th>PUNTOS POR MILLÓN</th>
            </tr>
          </thead>
          <tbody>
            {managers.map((m) => (
              <tr key={m.user_id || m.name} className={m.is_us ? "hi" : ""}>
                <td className="es">{m.rank ?? "—"}</td>

                <td className="q">
                  {m.icon ? (
                    <img
                      className="esc"
                      src={`${AVATAR}${m.icon}`}
                      alt=""
                      onError={(e) => {
                        e.currentTarget.style.visibility = "hidden";
                      }}
                    />
                  ) : null}
                  <span className="nm">{m.name}</span>{" "}
                  {m.is_us ? (
                    <span className="tit-si">NOSOTROS</span>
                  ) : null}
                </td>

                <td className="pt">{m.points}</td>

                {/* A NUESTRO NIVEL: la diferencia en puntos.
                    Nuestra propia fila pone un guion, no un
                    cero: «cero de diferencia contigo mismo» no
                    es un dato. */}
                <td className="ppm">
                  {m.is_us ? (
                    <span className="unk">—</span>
                  ) : m.vs_nosotros == null ? (
                    <span className="unk">sin dato</span>
                  ) : (
                    <b className={m.vs_nosotros > 0 ? "neg-d" : "pos-d"}>
                      {m.vs_nosotros > 0 ? "+" : ""}
                      {m.vs_nosotros}
                    </b>
                  )}
                </td>

                <td className="c">
                  <span className="pr">
                    {formatEuros(m.roster_value)}
                  </span>
                </td>

                {/* FICHAS: `null` es «no se pudo cruzar», que no
                    es lo mismo que cero. */}
                <td className="ppm">
                  {m.fichas == null ? (
                    <span className="unk">sin dato</span>
                  ) : (
                    m.fichas
                  )}
                </td>

                <td className="c">
                  <span className={m.balance < 0 ? "down" : "up"}>
                    {formatEuros(m.balance)}
                  </span>
                </td>

                <td className="c">
                  <span className="pr">
                    {formatEuros(m.net_worth)}
                  </span>
                </td>

                <td className="ti">
                  {m.puntos_por_millon == null ? (
                    <span className="unk">sin dato</span>
                  ) : (
                    <div className="titw">
                      <span className="titn t-hi">
                        {m.puntos_por_millon}
                      </span>
                      <i className="bar">
                        <b
                          className="t-hi"
                          style={{
                            width: `${Math.min(
                              100,
                              Math.round(
                                (m.puntos_por_millon / techo) * 100
                              )
                            )}%`
                          }}
                        />
                      </i>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        <b>PUNTOS POR MILLÓN</b> son sus puntos entre el valor de
        su plantilla, en millones. La barra se escala contra el
        más alto de la tabla, no contra un tope inventado.{" "}
        <b>
          Léelo siempre con la columna de FICHAS al lado
        </b>
        : un ratio alto con la plantilla vacía dice que alguien ha
        vendido, no que gestione mejor.{" "}
        <b>Los puestos van contados</b>, no escritos.
      </p>
    </section>
  );
}
