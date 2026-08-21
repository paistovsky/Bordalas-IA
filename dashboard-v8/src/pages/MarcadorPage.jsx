/**
 * EL MARCADOR: LA NOTA DEL ONCE.
 *
 * QUE PREGUNTA CONTESTA
 *
 *   Pepe juega cada jornada, pero hasta hoy nadie le ponia nota.
 *   Esta pantalla compara dos numeros:
 *
 *     - lo que puntuo el once que alineo
 *     - lo que habria puntuado el MEJOR once posible con esa
 *       misma plantilla, ya sabiendo los resultados
 *
 *   La distancia entre los dos es lo unico que mide el motor de
 *   alineacion solo: sin rivales, sin mercado, sin suerte de
 *   fichaje. Es lo que se puede ganar sin fichar a nadie.
 *
 *     ~90 %  el motor esta terminado, dejar de tocarlo
 *     ~60 %  ahi esta la liga entera
 *
 * POR QUE HAY UN CUADRE
 *
 *   Un marcador que miente es peor que no tener marcador. Si dice
 *   92 % cuando es 61 %, se deja de tocar el motor justo donde
 *   estaba todo por ganar.
 *
 *   Por eso se comprueba que los puntos del once reconstruido
 *   coincidan con los que Biwenger le dio en la clasificacion. Si
 *   no coinciden, la pantalla lo dice en rojo y el numero no
 *   vale.
 *
 * POR QUE HAY JORNADAS QUE NO CUENTAN
 *
 *   La jornada en curso tiene la clasificacion a cero hasta que
 *   cierra, y una jornada sin observacion de la anterior no se
 *   puede medir por diferencia de totales. Ninguna de las dos se
 *   inventa: salen como "no medible" y quedan fuera de la media.
 */

const POSICION = {
  1: "PT",
  2: "DF",
  3: "MC",
  4: "DL"
};

function tonoDeLaNota(nota) {
  if (nota == null) return "";
  if (nota >= 85) return "good";
  if (nota >= 70) return "hot";
  return "bad";
}

export default function MarcadorPage({ data }) {
  const marcador = data.marcador || { available: false };
  const resumen = marcador.resumen || {};
  const jornadas = marcador.jornadas || [];

  const medibles = jornadas.filter((j) => j.medible);
  const ultima = medibles[0];

  if (!marcador.available) {
    return (
      <section className="pan">
        <h2>MARCADOR</h2>
        <div className="sub">La nota del once, jornada a jornada</div>
        <div className="empty">
          {marcador.reason || "El marcador no está disponible."}
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>LA NOTA DEL ONCE</h2>
            <div className="sub">
              Lo que puntuó Pepe contra lo que podía haber puntuado
            </div>
          </div>
          {resumen.cuadra_todo === false && (
            <span className="pill crit">NO CUADRA</span>
          )}
        </div>

        <div className="grid g3">
          <div className={`kpi ${tonoDeLaNota(resumen.eficiencia_media)}`}>
            <div className="l">NOTA DEL ONCE</div>
            <div className="v">
              {resumen.eficiencia_media != null
                ? `${resumen.eficiencia_media} %`
                : "—"}
            </div>
            <div className="s">del máximo posible con su plantilla</div>
          </div>

          <div className="kpi">
            <div className="l">CONTRA LA LIGA</div>
            <div className="v">
              {resumen.diferencia_media != null
                ? `${resumen.diferencia_media > 0 ? "+" : ""}${resumen.diferencia_media}`
                : "—"}
            </div>
            <div className="s">puntos por jornada sobre la media</div>
          </div>

          <div className="kpi">
            <div className="l">JORNADAS QUE CUENTAN</div>
            <div className="v">{resumen.jornadas_fiables ?? 0}</div>
            <div className="s">
              de {resumen.jornadas_observadas ?? 0} anotadas
              {resumen.jornadas_descartadas
                ? ` · ${resumen.jornadas_descartadas} descartada(s) por no cuadrar`
                : ""}
            </div>
          </div>
        </div>

        <div className="strat-rule">
          <b>QUÉ SIGNIFICA ESTO</b>
          <p style={{ marginTop: 6, marginBottom: 0 }}>
            {resumen.veredicto}
          </p>
        </div>

        {resumen.cuadra_todo === false && (
          <div className="alert crit" style={{ marginTop: 11 }}>
            <b>LOS NÚMEROS NO CUADRAN CON BIWENGER.</b> El once que
            hemos reconstruido no suma lo mismo que los puntos que
            Biwenger le dio a Pepe en la clasificación. Hasta que
            coincidan, la nota de arriba no vale.
          </div>
        )}
      </section>

      {ultima && (
        <section className="pan">
          <h2>DÓNDE SE PERDIERON LOS PUNTOS · J{ultima.round_id}</h2>
          <div className="sub">
            {ultima.puntos_perdidos > 0
              ? `${ultima.puntos_perdidos} puntos dejados en el banquillo`
              : "El once fue el mejor posible"}
          </div>

          {ultima.puntos_perdidos > 0 ? (
            <div className="grid g2">
              <div>
                <div className="sub" style={{ marginBottom: 6 }}>
                  DEBIERON JUGAR
                </div>
                {(ultima.detalle?.faltaron || []).map((jugador) => (
                  <div className="kv" key={jugador.id}>
                    <span>
                      <span className="pill">{POSICION[jugador.position]}</span>{" "}
                      {jugador.name}
                    </span>
                    <b className="mono up">{jugador.points}</b>
                  </div>
                ))}
              </div>

              <div>
                <div className="sub" style={{ marginBottom: 6 }}>
                  JUGARON EN SU LUGAR
                </div>
                {(ultima.detalle?.sobraron || []).map((jugador) => (
                  <div className="kv" key={jugador.id}>
                    <span>
                      <span className="pill">{POSICION[jugador.position]}</span>{" "}
                      {jugador.name}
                    </span>
                    <b className="mono down">{jugador.points}</b>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty">
              Nadie en el banquillo puntuó más que los que jugaron.
            </div>
          )}

          <p className="note" style={{ textAlign: "left" }}>
            Con los mismos puntos manda quien jugó: si un suplente
            hizo lo mismo que un titular, no cuenta como fallo.
          </p>
        </section>
      )}

      <section className="pan">
        <h2>JORNADA A JORNADA</h2>
        <div className="sub">Lo alineado, el techo y la diferencia</div>

        {jornadas.length === 0 ? (
          <div className="empty">
            Todavía no se ha anotado ninguna jornada.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>JORNADA</th>
                <th>DIBUJO</th>
                <th className="n">PUNTOS</th>
                <th>TECHO</th>
                <th className="n">MÁXIMO</th>
                <th className="n">NOTA</th>
                <th className="n">PERDIDOS</th>
                <th className="n">VS LIGA</th>
                <th className="n">CUADRA</th>
              </tr>
            </thead>
            <tbody>
              {jornadas.map((jornada) => {
                if (!jornada.medible) {
                  return (
                    <tr key={jornada.round_id}>
                      <td>J{jornada.round_id}</td>
                      <td colSpan={8} className="dim">
                        {jornada.motivo}
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr key={jornada.round_id}>
                    <td>J{jornada.round_id}</td>
                    <td className="mono">{jornada.formacion || "—"}</td>
                    <td className="n mono">{jornada.puntos_once}</td>
                    <td className="mono">{jornada.mejor_formacion}</td>
                    <td className="n mono">{jornada.mejor_puntos}</td>
                    <td className="n">
                      {/* UNA NOTA QUE NO CUADRA NO ES UNA NOTA
                          (21/08/2026)

                          Pintarla en rojo con su porcentaje la
                          hace parecer un mal resultado. No lo
                          es: es un numero invalido, y el ojo
                          tiene que distinguir las dos cosas. */}
                      {jornada.cuadra ? (
                        <span
                          className={
                            jornada.eficiencia >= 85
                              ? "pill ok"
                              : jornada.eficiencia >= 70
                              ? "pill warn"
                              : "pill crit"
                          }
                        >
                          {jornada.eficiencia} %
                        </span>
                      ) : (
                        <span
                          className="dim"
                          title={`Reconstruimos ${jornada.puntos_once} puntos y Biwenger pagó ${jornada.puntos_biwenger}. El once que anotamos no es el que jugó.`}
                        >
                          no cuadra
                        </span>
                      )}
                    </td>
                    <td className="n mono down">
                      {jornada.puntos_perdidos || 0}
                    </td>
                    <td className="n mono">
                      {jornada.diferencia_liga != null
                        ? `${jornada.diferencia_liga > 0 ? "+" : ""}${jornada.diferencia_liga}`
                        : "—"}
                    </td>
                    <td className="n">
                      {jornada.cuadra ? (
                        <span className="pill ok">SÍ</span>
                      ) : (
                        <span className="pill crit">NO</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        <p className="note" style={{ textAlign: "left" }}>
          El techo es el mejor once legal con la plantilla de esa
          jornada, ya sabiendo los resultados. No es lo que Pepe
          podía saber el viernes: es el límite de lo que tenía en
          casa.
        </p>
      </section>
    </>
  );
}
