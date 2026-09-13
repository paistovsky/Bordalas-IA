import { formatEuros, positionLabel } from "../lib/utils";

/* TODOS LOS JUGADORES DE LA LIGA (13/09/2026)
 *
 * LA LISTA DE LA COMPRA, no la caja registradora.
 *
 *   El cuadro de arriba enseña lo que hay HOY en el mercado:
 *   sesenta filas. Éste enseña los 570 del catálogo, ordenados
 *   por lo que nos mejorarían.
 *
 *   Hacía falta porque un jugador libre que el Computer no ha
 *   sacado hoy no existía en ninguna parte: medido, de once
 *   "chollos" publicados sin dueño, CERO menciones en toda la
 *   foto.
 *
 * LA VARA
 *
 *   Sus puntos menos los del PEOR TITULAR nuestro en su
 *   posición. Misma vara para las cuatro, y de puntos YA
 *   JUGADOS, no de un pronóstico.
 *
 * ESTO NO DECIDE NADA. Es una lista para mirar: ninguna puja
 * sale de aquí.
 */

const POS = { 1: "por", 2: "def", 3: "med", 4: "del" };

const ESCUDO = "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/";

const DE_QUIEN = {
  nuestro: ["nos", "◆", "nuestro"],
  computer: ["comp", "◆", "Computer"],
  rival: ["riv", "◆", "Rival"],
  libre: ["libre", "◇", "libre"]
};

const TONO_ETIQUETA = {
  "nos mejora": "i-top",
  "chollo · muchos puntos por euro": "i-chollo",
  "sin interés": "i-nada",
  "no disponible": "i-nada",
  "ya es nuestro": "i-nuestro"
};

/* Igual que en el cuadro de arriba: Biwenger dice `sanctioned`
   y no dice si fue doble amarilla o roja directa. */
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

export default function TodaLaLigaPanel({ data }) {
  const liga = data.todaLaLiga || {};

  const censo = liga.plantillas || {};

  if (!liga.available) {
    return (
      <section className="pan">
        <h2>TODOS LOS JUGADORES DE LA LIGA</h2>
        <div className="empty">
          {liga.reason ||
            "No se ha podido montar la lista de la liga."}
        </div>
      </section>
    );
  }

  const jugados = (fila) => {
    const total = Math.max(fila.played, liga.jornadas || 6);

    const pct = total ? Math.round((fila.played / total) * 100) : 0;

    const tono = pct >= 80 ? "t-hi" : pct >= 50 ? "t-md" : "t-lo";

    return { total, pct, tono };
  };

  return (
    <section className="pan" style={{ marginTop: 11 }}>
      <div className="pan-head">
        <div>
          <h2>TODOS LOS JUGADORES DE LA LIGA</h2>
          <div className="sub">
            {liga.total} del catálogo, por CALIDAD-PRECIO ·
            lo que nos añaden por cada millón que cuestan
          </div>
        </div>
      </div>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>QUIÉN</th>
              <th className="ctr">EST.</th>
              <th className="r">PTS</th>
              <th>JUGADOS</th>
              <th className="n">PRECIO</th>
              <th className="r">PTS/M€</th>
              <th className="n">NOS SUMA</th>
              <th className="r">CALIDAD-PRECIO</th>
              <th>DÓNDE ESTÁ</th>
              <th>INTERÉS</th>
            </tr>
          </thead>
          <tbody>
            {(liga.players || []).map((fila) => {
              const j = jugados(fila);

              const [clase, rombo, texto] =
                DE_QUIEN[fila.de_quien] || DE_QUIEN.libre;

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

                  {/* JUGADOS: la titularidad MEDIDA, no un
                      pronóstico. */}
                  <td className="ti">
                    <div className="titw">
                      <span className={`titn ${j.tono}`}>
                        {fila.played}/{j.total}
                      </span>
                      <i className="bar">
                        <b
                          className={j.tono}
                          style={{ width: `${j.pct}%` }}
                        />
                      </i>
                    </div>
                  </td>

                  <td className="c">
                    <span className="pr">{formatEuros(fila.price)}</span>{" "}
                    <span
                      className={
                        fila.price_increment > 0
                          ? "up"
                          : fila.price_increment < 0
                          ? "down"
                          : "flat"
                      }
                    >
                      {fila.price_increment > 0
                        ? "▲"
                        : fila.price_increment < 0
                        ? "▼"
                        : "="}
                    </span>
                  </td>

                  <td className="ppm">
                    {fila.puntos_por_millon ?? "—"}
                  </td>

                  {/* NOS SUMA: la vara, con nombre debajo. Sin
                      referencia NO se resta y se dice. */}
                  <td className="dl">
                    {fila.nos_suma == null ? (
                      <span className="unk">sin vara</span>
                    ) : (
                      <>
                        <b
                          className={
                            fila.nos_suma > 0 ? "pos-d" : "neg-d"
                          }
                        >
                          {fila.nos_suma > 0 ? "+" : ""}
                          {fila.nos_suma}
                        </b>
                        <br />
                        <span className="ref">
                          sobre {fila.vara_nombre} ({fila.vara_puntos})
                        </span>
                      </>
                    )}
                  </td>

                  {/* CALIDAD-PRECIO: lo que nos añade por cada
                      millón. Es lo que ORDENA el cuadro.

                      Solo tiene sentido cuando nos suma: dividir
                      un negativo entre el precio ordenaría por
                      "cuál nos empeora menos por euro", que no es
                      una pregunta que nadie haga. */}
                  <td className="ppm">
                    {fila.calidad_precio == null ? (
                      <span className="unk">—</span>
                    ) : (
                      <b className="pos-d">{fila.calidad_precio}</b>
                    )}
                  </td>

                  {/* DÓNDE ESTÁ: informativo, y nada más.

                      Estar hoy en el mercado del Computer dejó de
                      ordenar el 13/09 por la noche. Lo que manda
                      es la calidad-precio. */}
                  <td className="vd">
                    <span className={clase}>
                      {rombo} {texto}
                    </span>
                  </td>

                  <td>
                    <span
                      className={TONO_ETIQUETA[fila.etiqueta] || "i-nada"}
                    >
                      {fila.etiqueta}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* EL RECUENTO, que es el número que más importa de toda la
          pantalla: cuántos hay de cada cosa. */}
      <div className="res">
        {Object.entries(liga.recuento || {})
          .sort((a, b) => b[1] - a[1])
          .map(([etiqueta, cuantos]) => (
            <span key={etiqueta} style={{ marginRight: 14 }}>
              {etiqueta} <b>{cuantos}</b>
            </span>
          ))}
      </div>

      {/* EL CENSO DE LAS OCHO PLANTILLAS (13/09/2026).

          Una plantilla que llega a medias no se nota en ninguna
          parte: sus jugadores se cuentan como LIBRES, y un libre
          es alguien a quien se puede fichar. Aquí va la cuenta
          entera, con el descuadre si lo hay. */}
      {censo.equipos && censo.equipos.length ? (
        <p className="note" style={{ textAlign: "left" }}>
          <b>LAS OCHO PLANTILLAS</b>{" "}
          {censo.equipos
            .map((e) => `${e.nombre} ${e.jugadores}`)
            .join(" · ")}{" "}
          = <b>{censo.con_dueño}</b> con dueño +{" "}
          <b>{censo.libres}</b> libres ={" "}
          <b>{censo.total}</b> del catálogo.{" "}
          {censo.vacias && censo.vacias.length ? (
            <b className="mal">
              Llegan vacías: {censo.vacias.join(", ")} — sus
              jugadores se están contando como libres.
            </b>
          ) : censo.cuadra ? (
            <span className="bien">La cuenta cuadra.</span>
          ) : (
            <b className="mal">
              La cuenta NO cuadra: sobran {censo.descuadre}. Hay
              jugadores contados dos veces o fuera del catálogo.
            </b>
          )}
        </p>
      ) : (
        <p className="note" style={{ textAlign: "left" }}>
          <b className="mal">
            Las plantillas no llegaron: no se puede saber cuántos
            de los {liga.total} están libres de verdad.
          </b>
        </p>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        <b>CALIDAD-PRECIO</b> = lo que nos suma dividido entre lo
        que cuesta, en millones. Es lo que ordena el cuadro:{" "}
        <b>estar hoy en el mercado no adelanta a nadie</b>, sólo
        se dice en DÓNDE ESTÁ.{" "}
        <b>NOS SUMA</b> son sus puntos menos los del peor titular
        nuestro en su posición — hoy{" "}
        {Object.entries(liga.vara || {})
          .map(([pos, v]) => `${pos} ${v.name} (${v.points})`)
          .join(" · ")}
        . De puntos ya jugados, no de un pronóstico.{" "}
        <b>
          El corte de «chollo» en {liga.chollo_sin_medir} pts/M€ NO
          está medido
        </b>
        : se puso a ojo y está pendiente de medir. Esta lista no
        decide nada: ninguna puja sale de aquí.
      </p>
    </section>
  );
}
