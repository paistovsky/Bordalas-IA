/* EL VESTUARIO LIBRE — la lista de la compra.

   EL PUNTO CIEGO (14/09/2026)

     Pepe no podía querer a nadie que no estuviera HOY en el
     escaparate. Su universo eran los veinte que el Computer saca
     cada mañana; los 450 libres restantes no existían en ninguna
     parte — ni descartados, ni valorados, ni en ninguna lista.

   ESTO NO PUJA

     Es una lista para MIRAR. Ninguna puja sale de aquí, y el
     módulo que la calcula tiene una guardia que recorre su árbol
     para demostrarlo. «Vigilado» tampoco autoriza nada: cambia
     dónde se ve, no si se puja.

   POR QUÉ POR POSICIÓN Y POR QUÉ POR «NOS SUMA»

     No se puede fichar a un defensa para mejorar la delantera.
     La vara es por posición por construcción, así que las cuatro
     van en cuatro tablas, cada una contra su propia vara.

     Y se ordena por lo que nos SUMA, no por calidad-precio: eso
     divide por el precio y el barato gana siempre — con el orden
     viejo el segundo de la lista era un defensa de 350.000 € que
     nos sumaba +3. El precio se queda de columna. */

const POS = { POR: "por", DEF: "def", MED: "med", DEL: "del" };

function euros(valor) {
  const n = Number(valor || 0);
  return n ? n.toLocaleString("es-ES") : "—";
}

export default function ElVestuarioLibrePanel({ data }) {
  const v = (data && data.elVestuarioLibre) || {};

  if (!v.available) {
    return (
      <section className="pan">
        <div className="pan-head">
          <h2>EL VESTUARIO LIBRE</h2>
        </div>
        <p className="note">{v.reason || "No disponible."}</p>
      </section>
    );
  }

  const porPuesto = v.por_puesto || {};
  const filas = v.players || [];
  const r = v.recuento || {};
  const cortes = v.cortes || {};
  const PUESTOS = ["POR", "DEF", "MED", "DEL"];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL VESTUARIO LIBRE</h2>
          <p className="sub">
            Catálogo menos las ocho plantillas. Los{" "}
            {cortes.por_posicion} mejores de cada puesto, por lo que
            nos suman contra la vara de su posición.
          </p>
        </div>
      </div>

      {/* EL TAMAÑO, ARRIBA Y CONTADO. Ningún número escrito a
          mano: todos salen del recuento. */}
      <p className="reparto">
        <b className="libre">{v.libres} libres</b> de{" "}
        {v.total_catalogo} del catálogo · {v.con_dueno} con dueño ·{" "}
        {/* LA ETIQUETA DICE LO QUE MIDE (15/09/2026)

            Decía «nos mejorarían el once» y NO es eso lo que
            mide: `nos_suma` es la resta pelada de puntos contra
            el peor titular del puesto. No mira el pronóstico de
            titularidad ni aplica ninguna vara más.

            Caso vivo: Álvaro Carreras salía aquí como «nos
            mejora +9 sobre Trent», y en OBJETIVOS como
            «sustituiría a un titular confirmado (100 %) por
            alguien que está a 0 %: el once empeora». Las dos
            frases eran verdad. El dueño lo leyó como que Pepe se
            contradice, y no se contradice: la pantalla usaba una
            etiqueta que el motor no usa para decidir.

            Se cambia la ETIQUETA, no el motor. */}
        <b>{r.nos_mejoran || 0}</b> tienen más puntos en la hoja ·{" "}
        <b>{v.candidatos}</b> pasan el corte
        {r.en_el_mercado_hoy ? (
          <>
            {" "}·{" "}
            <b className="comp">
              {r.en_el_mercado_hoy} de estos {filas.length} están hoy
              en el escaparate
            </b>
          </>
        ) : (
          <> · ninguno de estos {filas.length} está hoy en el escaparate</>
        )}
      </p>

      {PUESTOS.map((puesto) => {
        const grupo = porPuesto[puesto] || [];
        if (!grupo.length) return null;
        const vara = grupo[0];

        return (
          <div key={puesto} className="scroll-y">
            {/* LA VARA DE ESTE PUESTO, EN LA CABECERA. Sin ella
                «nos suma» es un número sin contra qué. */}
            <p className="reparto">
              <b className={POS[puesto] || ""}>{puesto}</b> — más puntos que{" "}
              <b>
                {vara.vara_nombre} ({vara.vara_puntos} pts)
              </b>
              , nuestro peor titular del puesto
            </p>

            <table className="tbl">
              <thead>
                <tr>
                  <th className="n">#</th>
                  <th>QUIÉN</th>
                  <th className="n">PTS</th>
                  <th className="n">JUG</th>
                  <th className="n">PRECIO</th>
                  <th className="n">NOS SUMA</th>
                  <th className="n">PTS/M€</th>
                  <th className="ctr">¿HOY?</th>
                  <th className="ctr">MERCADO</th>
                </tr>
              </thead>
              <tbody>
                {grupo.map((p, i) => (
                  <tr key={p.id}>
                    <td className="n dim">{i + 1}</td>
                    <td>{p.name}</td>
                    <td className="n mono">{p.points}</td>
                    <td className="n mono dim">{p.played}</td>
                    <td className="n mono">{euros(p.price)}</td>
                    <td className="n mono ok">+{p.nos_suma}</td>
                    <td className="n mono dim">{p.calidad_precio}</td>
                    <td className="ctr">
                      {/* SI HOY LLEGARÍAMOS. No filtra a nadie:
                          uno que no podemos pagar puede ser justo
                          a quien hay que vender algo para llegar. */}
                      {p.nos_lo_podemos_permitir === null ? (
                        <span className="dim" title="No se sabe: no llegó la caja de fichar de esta vuelta.">?</span>
                      ) : p.nos_lo_podemos_permitir ? (
                        <span className="ok" title="Cabe en la caja de fichar de esta vuelta.">✔</span>
                      ) : (
                        <span className="dim" title="Hoy no llegamos. No queda descartado: habría que vender algo.">—</span>
                      )}
                    </td>
                    <td className="ctr">
                      {p.en_el_mercado ? (
                        <span className="comp" title="Hoy está en el escaparate. Vigilado: pasa por el mismo listón que cualquier otro.">
                          ◆
                        </span>
                      ) : (
                        <span className="dim">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}

      {/* EL PIE EXPLICA QUE «MÁS PUNTOS» NO ES «MEJORA EL ONCE».
          Lo exige `test_la_etiqueta_dice_lo_que_mide`. */}
      <p className="note" style={{ textAlign: "left" }}>
        <b>
          «Más puntos en la hoja» no es «mejora el once».
        </b>{" "}
        Esta columna es la resta de puntos contra el peor titular
        nuestro de su posición, y nada más:{" "}
        <b>no mira el pronóstico de titularidad</b> ni aplica la
        vara con la que decide el motor. Un jugador puede tener más
        puntos y aun así empeorar el once —si el que sale es
        titular confirmado y el que entra no va a jugar—. Quien
        decide eso es OBJETIVOS, con su <code>xi_decision</code>;
        esta lista es para mirar.{" "}
        <b>Esta lista no puja.</b> Entran los que nos suman{" "}
        {cortes.nos_suma_minimo}+ contra el peor titular nuestro de
        su posición y han jugado {cortes.partidos_para_juzgar}+
        partidos; los dos cortes están puestos para que la lista se
        pueda mirar, <b>no están calibrados</b> — y ya no son ellos
        los que aguantan la lista, sino el orden por NOS SUMA.
        La columna «¿hoy?» dice si cabría en la caja de fichar de
        esta vuelta ({euros(cortes.caja_de_fichar)} €); no descarta
        a nadie. Un «vigilado» que
        aparezca en el escaparate pasa por el mismo listón que
        cualquier otro: la marca cambia dónde se ve, no si se puja.
      </p>
    </section>
  );
}
