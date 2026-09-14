import { formatEuros } from "../lib/utils";

/* LA PUERTA DE LOS MANAGERS (14/09/2026)
 *
 * LA PREGUNTA
 *
 *   49 de los 69 objetivos del día mueren en MERCADO_DE_RIVAL:
 *   el 71 % de la lista. Y el motivo declarado es que la tasa de
 *   aceptación de una oferta a otro mánager NO ESTÁ MEDIDA.
 *
 *   Se podía medir sin escribir nada y sin gastar un euro: los
 *   rivales llevan cinco semanas haciéndose ofertas entre ellos
 *   y el tablón lo publica.
 *
 * LO QUE SALIÓ
 *
 *   8 traspasos de mánager a mánager en 301 eventos del tablón,
 *   contra 166 compras al Computer. Y Pepe está en CUATRO de los
 *   ocho. La puerta no está cerrada, y no es teoría.
 *
 *   La ventana de tres días que se miró primero —17 compras al
 *   Computer, 13 ventas y cero traspasos— no decía nada: en tres
 *   días caben cero traspasos de una vía que se usa cada semana
 *   y pico.
 *
 * ESTE CUADRO NO OFRECE NADA A NADIE. Cuenta lo que ya pasó.
 */

/* EL PRECIO DE ENTONCES, NO EL DE HOY. De los ocho traspasos,
   siete caen en el agujero de snapshots del 17/08 al 10/09 y no
   tienen precio con el que compararse. Se dice, en vez de
   rellenarlos con el precio de hoy. */
function SobreElMercado({ ratio }) {
  if (ratio == null)
    return <span className="unk">sin precio de entonces</span>;

  const pct = Math.round((ratio - 1) * 1000) / 10;

  return (
    <span className={pct > 0 ? "up" : pct < 0 ? "down" : "flat"}>
      {pct > 0 ? "+" : ""}
      {pct} % sobre el mercado
    </span>
  );
}

export default function LaPuertaDeLosManagersPanel({ data }) {
  const puerta = data.laPuertaDeLosManagers || {};

  if (!puerta.available) {
    return (
      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>LA PUERTA DE LOS MÁNAGERS</h2>
            <p className="sub">
              cuántas veces se ha cruzado de verdad
            </p>
          </div>
        </div>

        {/* CERO EVENTOS NO ES CERO TRASPASOS. Sin poder mirar, no
            se concluye: «no se pudo contar» y «en esta liga nadie
            vende» son cosas distintas, y la segunda es la cara. */}
        <p className="note">
          {puerta.reason ||
            "No llegó el tablón: no se puede decir si la puerta se cruza o no."}
        </p>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA PUERTA DE LOS MÁNAGERS</h2>
          <p className="sub">
            {puerta.cuantos} traspaso(s) entre mánagers ·{" "}
            {puerta.compras_al_computer} compras al Computer ·{" "}
            {puerta.eventos_leidos} eventos leídos
          </p>
        </div>

        <span className={puerta.puerta_cerrada ? "pill crit" : "pill ok"}>
          {puerta.puerta_cerrada ? "CERRADA" : "SE CRUZA"}
        </span>
      </div>

      {puerta.cuantos > 0 && (
        <div className="scroll-y">
          <table className="tbl">
            <thead>
              <tr>
                <th>CUÁNDO</th>
                <th>QUIÉN VENDE</th>
                <th>QUIÉN COMPRA</th>
                <th className="n">POR CUÁNTO</th>
                <th>SOBRE EL PRECIO DE ENTONCES</th>
              </tr>
            </thead>
            <tbody>
              {(puerta.traspasos || []).map((t, i) => (
                <tr key={i} className={t.nuestro ? "hi" : ""}>
                  <td className="vd">{t.fecha}</td>
                  <td className="q">
                    <span className="nm">{t.de}</span>
                  </td>
                  <td className="q">
                    <span className="nm">{t.a}</span>
                    {t.nuestro ? (
                      <>
                        {" "}
                        <span className="tit-si">NOSOTROS</span>
                      </>
                    ) : null}
                  </td>
                  <td className="c">
                    <span className="pr">{formatEuros(t.importe)}</span>
                  </td>
                  <td>
                    <SobreElMercado ratio={t.sobre_el_mercado} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        <b>{puerta.reason}</b>{" "}
        {puerta.con_precio_de_mercado != null &&
        puerta.cuantos > puerta.con_precio_de_mercado ? (
          <>
            Sólo {puerta.con_precio_de_mercado} de {puerta.cuantos} se
            pueden comparar con el precio de entonces: los demás caen
            en el hueco de fotos del 17/08 al 10/09.{" "}
          </>
        ) : null}
        Este cuadro <b>no ofrece nada a nadie</b>: cuenta lo que ya
        pasó.
      </p>
    </section>
  );
}
