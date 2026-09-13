import { useEffect, useState } from "react";
import { formatEuros, positionLabel } from "../lib/utils";

/* LO NUESTRO A LA VENTA (13/09/2026)
 *
 * QUÉ VA A HACER PEPE CON CADA PUBLICACIÓN.
 *
 *   Hasta hoy la pantalla decía "16 publicados" y nada más.
 *   Diecisiete jugadores en plantilla, dieciséis en el
 *   escaparate y catorce con una oferta del Computer encima de
 *   la mesa — y ni una sola de esas decisiones a la vista.
 *
 * LA REGLA DE ESTE CUADRO
 *
 *   LA ETIQUETA NO LA DECIDE LA PANTALLA. LA DECIDE EL MOTOR Y
 *   LA PANTALLA LA TRADUCE. Aquí no hay ni un umbral: la
 *   traducción vive en `lo_nuestro_a_la_venta.py` y esto sólo
 *   pinta lo que llega.
 *
 *   Si para una fila no hay decisión publicada, pone «sin
 *   decidir» y el pie dice cuántas salieron así.
 *
 * ESTO NO DECIDE NADA. No se vende ni se acepta nada desde aquí.
 */

const POS = { 1: "por", 2: "def", 3: "med", 4: "del" };

const ESCUDO = "https://cdn.biwenger.com/cdn-cgi/image/f=avif/i/t/";

/* El tono de cada decisión. Sale de lo que dice el motor, no de
   lo bonita que quede la fila. */
const TONO = {
  "aceptar y cobrar": "d-cobra",
  "pedir otra oferta": "d-reroll",
  "buena, la conservamos": "d-buena",
  "guardar para tapar deuda": "d-deuda",
  "esperar mejor oferta": "d-espera",
  "no se vende nunca": "d-nunca",
  "sin decidir": "d-nada"
};

/* Igual que en los otros dos cuadros: Biwenger dice `sanctioned`
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

/* CADA OFERTA CON SU RELOJ.
 *
 *   Las horas llegan por fila y cada oferta tiene la suya: hoy
 *   hay ofertas a 33,5 h y otras a 9,5 h. Poner el reloj del
 *   reset a todas era dar el mismo número a dos cosas distintas.
 *
 *   Sin horas NO se pinta un cero: un 0,0 se lee como «vence
 *   ya», que es lo contrario de «no se sabe». */
function CaducaEn({ horas, caducada }) {
  /* EL ORIGEN SE FIJA AL LLEGAR EL DATO, y el reloj cuenta
     desde ahí. La primera versión restaba `ahora - ahora`, que
     es cero siempre: el contador se veía bien y no corría. */
  const [origen, setOrigen] = useState(() => Date.now());

  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    setOrigen(Date.now());
    setAhora(Date.now());
  }, [horas]);

  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  if (horas == null) return <span className="unk">sin dato</span>;

  if (caducada || horas <= 0)
    return <span className="cd urg">caducada</span>;

  const restan = Math.max(
    0,
    Math.round(Number(horas) * 3600 - (ahora - origen) / 1000)
  );

  const hh = String(Math.floor(restan / 3600)).padStart(2, "0");
  const mm = String(Math.floor((restan % 3600) / 60)).padStart(2, "0");
  const ss = String(restan % 60).padStart(2, "0");

  return (
    <span className={restan < 3600 ? "cd urg" : "cd"}>
      {hh}:{mm}:{ss}
    </span>
  );
}

export default function LoNuestroALaVentaPanel({ data }) {
  const venta = data.loNuestroALaVenta || {};

  const aviso = venta.comprado_sin_publicar || {};

  if (!venta.available) {
    return (
      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>LO NUESTRO A LA VENTA</h2>
            <p className="sub">qué va a hacer Pepe con cada uno</p>
          </div>
        </div>

        {/* EL AVISO SE PINTA IGUAL AUNQUE NO HAYA CUADRO: un
            jugador comprado para revender y sin publicar es justo
            el caso en que puede no haber ni una fila. */}
        {aviso.hay ? <Aviso aviso={aviso} /> : null}

        <p className="note">
          {venta.reason || "No llegó lo que tenemos publicado."}
        </p>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LO NUESTRO A LA VENTA</h2>
          <p className="sub">
            {venta.publicados} publicados · {venta.con_oferta} con
            oferta · qué va a hacer Pepe con cada uno
          </p>
        </div>
      </div>

      {aviso.hay ? <Aviso aviso={aviso} /> : null}

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>QUIÉN</th>
              <th className="ctr">EST.</th>
              <th className="r">PTS</th>
              <th className="n">VALE</th>
              <th className="n">NOS OFRECEN</th>
              <th>LA OFERTA CADUCA EN</th>
              <th>QUÉ VA A HACER</th>
              <th>POR QUÉ</th>
            </tr>
          </thead>
          <tbody>
            {(venta.players || []).map((fila) => (
              <tr key={fila.id} className={fila.decidido ? "" : "hi"}>
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
                  </span>{" "}
                  {fila.titular == null ? null : fila.titular ? (
                    <span className="tit-si">TITULAR</span>
                  ) : (
                    <span className="tit-no">banquillo</span>
                  )}
                </td>

                <td className="es">
                  <Estado status={fila.status} />
                </td>

                <td className="pt">{fila.points}</td>

                <td className="c">
                  <span className="pr">{formatEuros(fila.vale)}</span>
                </td>

                {/* NOS OFRECEN, con la prima al lado. Sin prima
                    calculada NO se pinta un 0,0 %: se dice. */}
                <td className="c">
                  {fila.nos_ofrecen == null ? (
                    <span className="unk">sin oferta</span>
                  ) : (
                    <>
                      <span className="pr">
                        {formatEuros(fila.nos_ofrecen)}
                      </span>{" "}
                      {fila.prima == null ? (
                        <span className="unk">prima sin medir</span>
                      ) : (
                        <span
                          className={
                            fila.prima > 0
                              ? "up"
                              : fila.prima < 0
                              ? "down"
                              : "flat"
                          }
                        >
                          {fila.prima > 0 ? "+" : ""}
                          {fila.prima} %
                        </span>
                      )}
                    </>
                  )}
                </td>

                <td>
                  <CaducaEn
                    horas={fila.oferta_caduca_en}
                    caducada={fila.oferta_caducada}
                  />
                </td>

                {/* QUÉ VA A HACER: traducido del motor, nunca
                    decidido aquí. */}
                <td className="ac">
                  <span className={TONO[fila.que_va_a_hacer] || "d-nada"}>
                    {fila.que_va_a_hacer}
                  </span>
                </td>

                <td className="pw">{fila.por_que}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        {venta.sin_decidir > 0 ? (
          <b className="mal">
            {venta.sin_decidir} publicación(es) sin decisión del
            motor: salen como «sin decidir» y arriba del todo.{" "}
          </b>
        ) : null}
        {venta.sin_traducir && venta.sin_traducir.length ? (
          <b className="mal">
            El motor publica {venta.sin_traducir.join(", ")}, que
            esta pantalla todavía no sabe decir en cristiano: se
            enseña en crudo.{" "}
          </b>
        ) : null}
        <b>La etiqueta la decide el motor</b>, no esta pantalla:
        aquí sólo se traduce lo que él publica. Aquí no se vende ni
        se acepta nada.{" "}
        {venta.renovacion ? (
          <>
            <b>Renovaciones:</b> {venta.renovacion}
          </>
        ) : (
          <b className="mal">
            Renovaciones: no llegó el plan, así que no se sabe si
            algún listado caduca sin renovar.
          </b>
        )}
      </p>
    </section>
  );
}

/* COMPRADO PARA REVENDER Y TODAVÍA SIN PUBLICAR.
 *
 *   Mientras no esté en el escaparate, el Computer no le hace
 *   ninguna oferta: el viaje está parado y no se nota en ningún
 *   sitio.
 *
 *   LO ENCIENDE EL HECHO, NO LA INTENCIÓN (regla 37): si no hay
 *   ninguno, este cartel no existe. Un aviso fijo se deja de leer
 *   a los dos días y entonces ya no avisa de nada. */
function Aviso({ aviso }) {
  return (
    <p className="aviso-ambar">
      <b>Comprado para revender y todavía sin poner a la venta:</b>{" "}
      {aviso.players.join(", ")}. Mientras no esté publicado, el
      Computer no le hace ninguna oferta.
    </p>
  );
}
