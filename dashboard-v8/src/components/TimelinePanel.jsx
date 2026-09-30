import {
  cierreDeJornada,
  clave,
  cuando,
  esNuestro,
  laOrden,
  millones,
  ofertasDelComputer,
  porVenir,
  pujasDelReset,
  pujasVivas,
  resetDeLaFoto,
  saldo
} from "../lib/lectura";

/* LA CRONOLOGÍA, DESDE CERO (30/09/2026)
 *
 * «Está perfecto salvo lo de cronología.» Anunciaba «ANTES DEL
 * RESET: Pujar por Lejeune» mientras la orden del gestor lo
 * prohibía: salía del cuadro de VALORACIÓN (`acquisition.targets`
 * con BID), que no es lo que Pepe va a hacer.
 *
 * Ahora cada paso sale de lo que de verdad va a pasar:
 *
 *   - nuestras pujas vivas (lo mismo que PUJAS EN VIVO), que se
 *     resuelven en el reset;
 *   - el plan de la subasta del reset (`subasta`), que es lo que
 *     el ciclo ejecuta, sin los jugadores que la orden prohíbe;
 *   - la orden del gestor (`orden`): a quién vende y a qué suelo,
 *     el último recurso y cuándo caduca;
 *   - el cierre de la jornada.
 *
 * Lo que ya pasó no sale: una fecha en el pasado es información
 * vieja, y el dueño se quejó de eso. Si no queda nada por venir,
 * se dice en una línea.
 */

export default function TimelinePanel({ data }) {
  const ahora = new Date();
  const orden = laOrden(data, ahora);
  const reset = resetDeLaFoto(data, ahora);
  const cierre = cierreDeJornada(data, ahora);
  const ofertas = ofertasDelComputer(data);
  const fichajesDeLaOrden = new Set((orden?.viva ? orden.fichar : []).map((f) => clave(f.nombre)));

  const conHora = [];
  const mientras = [];

  // 1. Las pujas que ya están puestas se resuelven en el reset.
  if (reset) {
    for (const p of pujasVivas(data)) {
      const deLaOrden = p.nombre && fichajesDeLaOrden.has(clave(p.nombre));
      conHora.push({
        t: reset,
        estado: "now",
        que: p.nombre
          ? `Se resuelve la puja por ${p.nombre} (${millones(p.importe)})`
          : `Se resuelve una puja nuestra de ${millones(p.importe)}`,
        porque: deLaOrden ? "Es el fichaje de la orden del gestor." : null
      });
    }

    // 2. Lo que el ciclo pujará en la ventana del reset.
    for (const b of pujasDelReset(data, orden)) {
      conHora.push({
        t: new Date(reset.getTime() - 60_000),
        estado: "next",
        que: `Pepe pujará por ${b.name} (${millones(b.bid)})`,
        porque: "En la ventana de antes del reset, si nadie lo cambia."
      });
    }
  }

  if (orden?.viva) {
    // 3. Fichajes de la orden que todavía no tienen puja puesta.
    const conPuja = new Set(pujasVivas(data).map((p) => clave(p.nombre)));
    for (const f of orden.fichar) {
      if (esNuestro(data, f.nombre) || conPuja.has(clave(f.nombre))) continue;
      mientras.push({
        que: `Pepe pondrá la puja por ${f.nombre}${f.puja ? ` (${millones(f.puja)})` : ""}`,
        porque: "Lo manda la orden del gestor."
      });
    }

    // 4. Las ventas de la orden, sólo de los que siguen siendo nuestros.
    for (const v of orden.vender) {
      if (!esNuestro(data, v.nombre)) continue;
      const oferta = ofertas.get(clave(v.nombre));
      const hoy = oferta ? ` Hoy ofrece ${millones(oferta)}.` : "";

      if (v.ultimo_recurso && v.desdeFecha && porVenir(v.desdeFecha, ahora)) {
        conHora.push({
          t: v.desdeFecha,
          estado: "",
          que: `Último recurso: si el saldo sigue en negativo, Pepe podrá vender a ${v.nombre} (≥ ${millones(v.suelo)})`,
          porque: `Antes de esa hora no se toca.${hoy}`
        });
        continue;
      }

      mientras.push({
        que: `Pepe venderá a ${v.nombre} si el Computer ofrece ≥ ${millones(v.suelo)}`,
        porque: hoy.trim() || null
      });
    }

    // 5. La orden caduca.
    if (orden.caduca && porVenir(orden.caduca, ahora)) {
      conHora.push({
        t: orden.caduca,
        estado: "",
        que: "Caduca la orden del gestor",
        porque: "Desde entonces Pepe vuelve a decidir solo."
      });
    }
  }

  // 6. El cierre de la jornada.
  if (cierre) {
    const s = saldo(data);
    const jornada = data.summary?.target_matchday;
    conHora.push({
      t: cierre,
      estado: "",
      que: `Cierra la jornada${jornada ? ` ${jornada}` : ""}: el saldo tiene que estar en positivo`,
      porque: s == null ? null : `Saldo en la última vuelta: ${millones(s)}.`
    });
  }

  conHora.sort((a, b) => a.t - b.t);

  const nada = !conHora.length && !mientras.length;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>CRONOLOGÍA</h2>
          <div className="sub">Lo que va a pasar · hora de Madrid</div>
        </div>
      </div>

      {nada ? (
        <div className="crono-vacia">
          No hay nada programado por delante en esta foto.
        </div>
      ) : (
        <>
          {conHora.length > 0 && (
            <div className="tl">
              {conHora.map((paso, i) => (
                <div className={`tli ${paso.estado}`} key={`h${i}`}>
                  <div className="when">{cuando(paso.t, ahora)}</div>
                  <div className="what">{paso.que}</div>
                  {paso.porque && <div className="why">{paso.porque}</div>}
                </div>
              ))}
            </div>
          )}

          {mientras.length > 0 && (
            <>
              <div className="crono-mientras">
                Mientras dure la orden
                {orden?.caduca ? ` (hasta ${cuando(orden.caduca, ahora)})` : ""}
              </div>
              <div className="tl">
                {mientras.map((paso, i) => (
                  <div className="tli" key={`m${i}`}>
                    <div className="what">{paso.que}</div>
                    {paso.porque && <div className="why">{paso.porque}</div>}
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
