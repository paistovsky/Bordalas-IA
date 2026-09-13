import { formatEuros, positionLabel } from "../lib/utils";

/* QUIÉN MEJORA EL ONCE (13/09/2026, noche)
 *
 *   Los 198 del catálogo que suman sobre nuestro peor titular de
 *   su posición. Sale entero de `todaLaLiga`, filtrando la
 *   etiqueta: ni un cálculo nuevo.
 *
 * LA ÚLTIMA COLUMNA ES LA QUE CONVIERTE LA LISTA EN INFORMACIÓN
 *
 *   Saber que 198 jugadores nos mejorarían no vale de nada si no
 *   se dice a cuántos se puede llegar. Hoy: 127 están libres y
 *   Pepe no los vigila, 66 son de un rival y la compra a
 *   mánagers está cerrada, y los 5 del escaparate no se pujan
 *   porque no hay pronóstico de titularidad.
 *
 *   Ése es el tamaño del punto ciego, y es un número, no una
 *   impresión.
 *
 * ESTO NO DECIDE NADA. Es para mirar.
 */

const POS = { 1: "por", 2: "def", 3: "med", 4: "del" };

const ESCUDO = "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/";

/* SE PUEDE FICHAR HOY: una frase por vía, y ninguna es «sí».
   Las tres razones son distintas y llevan a arreglos distintos,
   así que no se pueden juntar en un «no». */
const SE_PUEDE = {
  libre: [
    "no-vigila",
    "Solo si el Computer lo saca al mercado. Pepe no lo vigila."
  ],
  rival: [
    "no-cerrado",
    "No. La compra a mánagers está cerrada: la tasa de aceptación nunca se ha medido."
  ],
  computer: [
    "no-ciego",
    "Está en el escaparate, pero la vía de fichar está ciega: sin pronóstico de titularidad no se puja."
  ],
  nuestro: ["ya-nuestro", "Ya es nuestro."]
};

function Estado({ status }) {
  const cual = String(status || "").toLowerCase();

  if (cual === "ok") return <span className="ok" title="Disponible">✔</span>;

  if (cual === "injured")
    return <span className="inj" title="Lesionado">✚</span>;

  if (cual === "sanctioned")
    return <i className="card red" title="Sancionado" />;

  if (cual === "doubt") return <span className="dud" title="Duda">?</span>;

  return <span className="unk" title="Sin dato">–</span>;
}

export default function QuienMejoraElOncePanel({ data }) {
  const liga = data.todaLaLiga || {};

  if (!liga.available) {
    return (
      <section className="pan">
        <h2>QUIÉN MEJORA EL ONCE</h2>
        <div className="empty">
          {liga.reason || "No llegó la lista de la liga."}
        </div>
      </section>
    );
  }

  const filas = (liga.players || []).filter(
    (f) => f.etiqueta === "nos mejora"
  );

  /* EL REPARTO SE CUENTA SOBRE LAS FILAS QUE SE PINTAN.
     Un resumen calculado aparte acaba discrepando de la tabla
     que tiene debajo, y entonces no se cree ninguno. */
  const reparto = filas.reduce((acc, f) => {
    acc[f.de_quien] = (acc[f.de_quien] || 0) + 1;
    return acc;
  }, {});

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>QUIÉN MEJORA EL ONCE</h2>
          <p className="sub">
            {filas.length} del catálogo suman sobre nuestro peor
            titular de su posición
          </p>
        </div>
      </div>

      {/* EL TAMAÑO DEL PUNTO CIEGO, arriba y contado. */}
      <p className="reparto">
        <b className="libre">{reparto.libre || 0} libres</b> que
        Pepe no vigila ·{" "}
        <b className="riv">{reparto.rival || 0} de un rival</b>{" "}
        con la compra a mánagers cerrada ·{" "}
        <b className="comp">
          {reparto.computer || 0} en el escaparate
        </b>{" "}
        que no se pujan por falta de pronóstico
      </p>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>QUIÉN</th>
              <th className="ctr">EST.</th>
              <th className="r">PTS</th>
              <th>JUGADOS</th>
              <th className="n">PRECIO</th>
              <th className="n">NOS SUMA</th>
              <th className="r">CALIDAD-PRECIO</th>
              <th>DE QUIÉN ES</th>
              <th>¿SE PUEDE FICHAR HOY?</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => {
              const [clase, frase] =
                SE_PUEDE[fila.de_quien] || [
                  "no-ciego",
                  "No se sabe de quién es."
                ];

              return (
                <tr key={fila.id}>
                  <td className="q">
                    {fila.team_id ? (
                      <img
                        className="esc"
                        src={`${ESCUDO}${fila.team_id}.png`}
                        alt=""
                        onError={(e) => {
                          e.currentTarget.style.visibility = "hidden";
                        }}
                      />
                    ) : null}
                    <span className="nm">{fila.name}</span>{" "}
                    <span className={`pos ${POS[fila.position] || ""}`}>
                      {positionLabel(fila.position)}
                    </span>
                  </td>

                  <td className="es">
                    <Estado status={fila.status} />
                  </td>

                  <td className="pt">{fila.points}</td>

                  <td className="vd">{fila.played}</td>

                  <td className="c">
                    <span className="pr">
                      {formatEuros(fila.price)}
                    </span>
                  </td>

                  {/* NOS SUMA, con la vara debajo: sin decir
                      contra quién se resta, el número no
                      significa nada. */}
                  <td className="dl">
                    <b className="pos-d">+{fila.nos_suma}</b>
                    <br />
                    <span className="ref">
                      sobre {fila.vara_nombre} ({fila.vara_puntos})
                    </span>
                  </td>

                  <td className="ppm">
                    <b className="pos-d">
                      {fila.calidad_precio ?? "—"}
                    </b>
                  </td>

                  <td className="vd">
                    <span className={fila.de_quien === "computer" ? "comp" : fila.de_quien === "rival" ? "riv" : "libre"}>
                      {fila.de_quien === "computer"
                        ? "◆ Computer"
                        : fila.de_quien === "rival"
                        ? "◆ un rival"
                        : "◇ libre"}
                    </span>
                  </td>

                  <td className="pw">
                    <span className={clase}>{frase}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        <b>NOS SUMA</b> son sus puntos menos los del peor titular
        nuestro en su posición, de puntos ya jugados.{" "}
        <b>CALIDAD-PRECIO</b> es lo que suma por cada millón que
        cuesta. Ninguno de estos {filas.length} se puede fichar
        hoy, y las tres razones son distintas: una es que no los
        miramos, otra que la vía está cerrada, y la tercera que
        falta el dato de titularidad.{" "}
        <b>Este cuadro no decide nada.</b>
      </p>
    </section>
  );
}
