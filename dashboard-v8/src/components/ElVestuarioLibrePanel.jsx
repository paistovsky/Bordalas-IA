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

   POR QUÉ SE ORDENA POR CALIDAD-PRECIO

     Lo pidió el dueño con estas palabras el 13/09: "cuál es el
     que más le interesa por CALIDAD-PRECIO y ese esté el
     primero". NOS SUMA va al lado para poder mirarlo a mano. */

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

  const filas = v.players || [];
  const r = v.recuento || {};
  const cortes = v.cortes || {};

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL VESTUARIO LIBRE</h2>
          <p className="sub">
            Catálogo menos las ocho plantillas. Los {filas.length}{" "}
            primeros por calidad-precio.
          </p>
        </div>
      </div>

      {/* EL TAMAÑO, ARRIBA Y CONTADO. Ningún número escrito a
          mano: todos salen del recuento. */}
      <p className="reparto">
        <b className="libre">{v.libres} libres</b> de{" "}
        {v.total_catalogo} del catálogo · {v.con_dueno} con dueño ·{" "}
        <b>{r.nos_mejoran || 0}</b> nos mejorarían el once ·{" "}
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

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th className="n">#</th>
              <th>QUIÉN</th>
              <th className="ctr">POS</th>
              <th className="n">PTS</th>
              <th className="n">JUG</th>
              <th className="n">PRECIO</th>
              <th className="n">NOS SUMA</th>
              <th className="n">PTS/M€</th>
              <th>MEJORA A</th>
              <th className="ctr">HOY</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((p, i) => (
              <tr key={p.id}>
                <td className="n dim">{i + 1}</td>
                <td>{p.name}</td>
                <td className={`ctr ${POS[p.posicion] || ""}`}>
                  {p.posicion}
                </td>
                <td className="n mono">{p.points}</td>
                <td className="n mono dim">{p.played}</td>
                <td className="n mono">{euros(p.price)}</td>
                <td className="n mono ok">+{p.nos_suma}</td>
                <td className="n mono">{p.calidad_precio}</td>
                <td className="dim">
                  {p.vara_nombre
                    ? `${p.vara_nombre} (${p.vara_puntos})`
                    : "—"}
                </td>
                <td className="ctr">
                  {p.en_el_mercado ? (
                    <span className="comp" title="Hoy está en el escaparate del Computer. Vigilado: pasa por el mismo listón que cualquier otro.">
                      ◆ ESCAPARATE
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

      <p className="note" style={{ textAlign: "left" }}>
        <b>Esta lista no puja.</b> Entran los que nos suman{" "}
        {cortes.nos_suma_minimo}+ contra el peor titular nuestro de
        su posición y han jugado {cortes.partidos_para_juzgar}+
        partidos; los dos cortes están puestos para que la lista se
        pueda mirar, <b>no están calibrados</b>. Un «vigilado» que
        aparezca en el escaparate pasa por el mismo listón que
        cualquier otro: la marca cambia dónde se ve, no si se puja.
      </p>
    </section>
  );
}
