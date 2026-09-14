/* LOS SENTIDOS DE PEPE (13/09/2026, noche)
 *
 * DE QUÉ SE ENTERA, DE CUÁNDO ES, Y QUÉ DEJA DE DECIDIR CUANDO
 * SE APAGA.
 *
 *   Hoy hay 64 objetivos en el mercado y ni una puja. El tablero
 *   de titulares es de la jornada 2, del 17 de agosto: el motor
 *   lo rechaza —bien hecho— y los 64 candidatos salen con la
 *   misma frase repetida.
 *
 *   Leída fila a fila, esa frase parecía prudencia. Junta y
 *   contada, dice lo que pasa: la vía de fichar está cerrada por
 *   falta de un dato, no por criterio.
 *
 * LAS DOS REGLAS
 *
 *   La edad se CALCULA en `los_sentidos.py`. Aquí no se resta
 *   ninguna fecha ni se escribe ningún número de días.
 *
 *   El «qué bloquea» es la frase del motor, entera. No se
 *   reescribe: la pantalla no tiene autoridad sobre esto.
 *
 * ESTO NO DECIDE NADA. Es un cuadro para mirar.
 */

const TONO = {
  VIVO: "s-vivo",
  VIEJO: "s-viejo",
  MUERTO: "s-muerto"
};

const ROMBO = {
  VIVO: "●",
  VIEJO: "◐",
  MUERTO: "○"
};

export default function LosSentidosPanel({ data }) {
  const bloque = data.losSentidos || {};

  const ciego = bloque.ciego || {};

  if (!bloque.available) {
    return (
      <section className="pan">
        <h2>LOS SENTIDOS DE PEPE</h2>
        <div className="empty">
          {bloque.reason ||
            "No llegó de qué se entera Pepe."}
        </div>
      </section>
    );
  }

  const filas = bloque.sentidos || [];

  const muertos = filas.filter((f) => f.estado === "MUERTO");

  return (
    <section className="pan">
      {/* LA BANDA. LA ENCIENDE EL HECHO, NO LA INTENCIÓN.

          Sale porque el motor ha rechazado el tablero Y hay
          objetivos que contar. Con la lista vacía no sale: «0 de
          0» no es una alarma, es que no ha llegado nada, y un
          aviso que se enciende con la ausencia de datos tapa el
          fallo que tenía que enseñar. */}
      {ciego.hay ? (
        <p className="aviso-ambar">
          <b>
            Hoy Pepe está medio ciego: {ciego.sin_pronostico} de{" "}
            {ciego.objetivos} objetivos salen sin pronóstico de
            titularidad.
          </b>{" "}
          {ciego.reason}{" "}
          <b>
            La vía de fichar está cerrada por falta de un dato, no
            por criterio.
          </b>
        </p>
      ) : null}

      <div className="pan-head">
        <div>
          <h2>LOS SENTIDOS DE PEPE</h2>
          <p className="sub">
            de qué se entera, de cuándo es, y qué deja de decidir
            cuando se apaga
          </p>
        </div>
        {muertos.length ? (
          <span className="pill crit">
            {muertos.length} APAGADO{muertos.length === 1 ? "" : "S"}
          </span>
        ) : (
          <span className="pill ok">LOS OCHO VIVOS</span>
        )}
      </div>

      <div className="scroll-y">
        <table className="tbl">
          <thead>
            <tr>
              <th>EL SENTIDO</th>
              <th>PARA QUÉ SIRVE</th>
              <th>DE CUÁNDO ES</th>
              <th>CUÁNTO PUEDE ENVEJECER</th>
              <th className="ctr">ESTADO</th>
              <th>QUÉ DECIDE HOY — Y QUÉ DEJA SIN DECIDIR</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <tr
                key={fila.sentido}
                className={fila.estado === "MUERTO" ? "hi" : ""}
              >
                <td className="q">
                  <span className="nm">{fila.sentido}</span>
                </td>

                <td className="pw">{fila.para_que}</td>

                {/* DE CUÁNDO ES: lo calcula el módulo. Si no hay
                    marca de tiempo dice «sin dato», nunca un
                    cero: un cero se lee como «de ahora mismo». */}
                <td className="vd">
                  {fila.de_cuando}
                  {fila.edad && fila.edad.zona_supuesta ? (
                    <>
                      <br />
                      <span className="ref">
                        sin zona horaria: se supone UTC
                      </span>
                    </>
                  ) : null}
                </td>

                {/* CUÁNTO PUEDE ENVEJECER, Y POR QUÉ.

                    El tope no se inventa: sale de cada cuánto
                    cambia el dato, y el motivo apunta a la
                    constante del módulo que lo produce. Los que
                    no se pueden derivar salen «sin medir» y lo
                    dicen, en vez de un número redondo. */}
                <td className="vd">
                  {(() => {
                    const tope = fila.edad_maxima || {};

                    if (tope.criterio === "POR_JORNADA")
                      return <b>la jornada de hoy</b>;

                    if (tope.horas != null)
                      return <b>{tope.horas} h</b>;

                    return <span className="ref">sin medir</span>;
                  })()}
                  <br />
                  <span className="ref">
                    {(fila.edad_maxima || {}).motivo}
                  </span>
                </td>

                <td className="es">
                  <span className={TONO[fila.estado] || "s-muerto"}>
                    {ROMBO[fila.estado] || "○"} {fila.estado}
                  </span>
                  {(fila.edad_maxima || {}).caducado ? (
                    <>
                      <br />
                      <span className="bloquea">CADUCADO</span>
                    </>
                  ) : null}
                </td>

                <td className="pw">
                  {fila.que_decide}
                  {/* LA FRASE DEL MOTOR, ENTERA. Es la que
                      explica por qué está apagado, y se copia
                      tal cual. */}
                  {fila.que_bloquea ? (
                    <>
                      <br />
                      <span className="bloquea">
                        {fila.que_bloquea}
                      </span>
                    </>
                  ) : null}
                  {fila.detalle ? (
                    <>
                      <br />
                      <span className="ref">{fila.detalle}</span>
                    </>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        <b>La edad se calcula</b>, no se escribe: sale de restar
        la marca de tiempo de cada fuente a la hora de esta foto.
        Sin marca de tiempo dice «sin dato» y nunca un cero.{" "}
        <b>
          El corte entre VIVO y VIEJO son{" "}
          {bloque.dias_para_viejo_sin_medir} días y NO está medido
        </b>
        : se puso a ojo y está pendiente de medir. Las frases en
        rojo son del motor, copiadas enteras. Este cuadro no
        decide nada.
      </p>
    </section>
  );
}
