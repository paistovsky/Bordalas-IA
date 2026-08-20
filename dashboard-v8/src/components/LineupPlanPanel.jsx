/**
 * EL PLAN DE BORDALAS: las once elecciones, no la lista.
 *
 * POR QUE SE REHIZO (20/08/2026)
 *
 *   "El plan de Bordalás no me convence. La info es inútil."
 *
 *   Tenia razon. El panel contaba la titularidad media del once,
 *   el valor del once, los tres de mas valor esperado y los tres
 *   de mas jerarquia. Cuatro agregados de una tabla que estaba
 *   justo debajo —y que desde hoy trae jerarquia, porcentaje,
 *   lesion y sancion jugador a jugador—.
 *
 *   Un panel que resume lo que ya se ve entero no informa:
 *   ocupa.
 *
 * QUE CUENTA AHORA
 *
 *   Lo unico que la tabla no puede contar: LA DECISION.
 *
 *   El once no es una lista de once nombres, son once
 *   elecciones, y de esas solo dos o tres estuvieron reñidas.
 *   Esas son las discutibles —"¿no compensa meter al delantero
 *   del Elche en vez de a Bigas?"— y para discutirlas hace falta
 *   ver al que entro y al que se quedo, con su numero al lado.
 *
 *   El cambio se plantea dentro de la posicion porque ahi
 *   siempre es legal: cualquier titular se puede cambiar por un
 *   suplente de su misma posicion sin tocar el dibujo.
 *
 * LO QUE NO HACE
 *
 *   No recalcula nada. `weekly_expected_value` es la funcion con
 *   la que el motor ordena el once; aqui solo se lee.
 */

const POSICIONES = { 1: "POR", 2: "DEF", 3: "MC", 4: "DEL" };

function porPosicion(players = []) {
  const cuenta = { 1: 0, 2: 0, 3: 0, 4: 0 };

  players.forEach((p) => {
    const pos = Number(p.position);
    if (cuenta[pos] != null) cuenta[pos] += 1;
  });

  return cuenta;
}

/* El nombre del sistema sale de contar, no de un campo: asi no
   puede desfasarse respecto a los jugadores que se pintan. */
function sistema(cuenta) {
  return `${cuenta[2]}-${cuenta[3]}-${cuenta[4]}`;
}

function formaDelEquipo(cuenta) {
  const def = cuenta[2];
  const del = cuenta[4];

  if (def >= 5 && del <= 2) {
    return "Repliegue: mayoría atrás y el peso ofensivo en pocas botas.";
  }

  if (del >= 3) {
    return "Apuesta ofensiva: tres arriba buscando goles.";
  }

  if (cuenta[3] >= 4) {
    return "Control por dentro: el centro del campo manda.";
  }

  return "Reparto equilibrado entre líneas.";
}

function partido(jugador) {
  const match = jugador?.next_match;

  if (!match || !match.rival) return null;

  return `${match.away ? "fuera" : "en casa"} vs ${match.rival}`;
}

function Ficha({ jugador, tono }) {
  return (
    <div>
      <b className={tono}>{jugador.name}</b>{" "}
      <span className="mono dim">
        {jugador.weekly_expected_value != null
          ? jugador.weekly_expected_value.toFixed(3)
          : "—"}
      </span>
      <div className="dim" style={{ fontSize: 10 }}>
        {[
          jugador.hierarchy,
          jugador.starter_probability != null
            ? `${Math.round(jugador.starter_probability)}% titular`
            : "sin pronóstico",
          partido(jugador)
        ]
          .filter(Boolean)
          .join(" · ")}
      </div>
    </div>
  );
}

export default function LineupPlanPanel({ lineup, debate }) {
  const players = lineup?.players || [];

  if (players.length === 0) {
    return (
      <section className="pan">
        <h2>EL PLAN DE BORDALÁS</h2>
        <div className="empty">Sin XI calculado en este ciclo.</div>
      </section>
    );
  }

  const cuenta = porPosicion(players);

  const duelos = debate?.duelos || [];
  const reñidos = duelos.filter((d) => d.discutible);
  const riesgo = debate?.riesgo || [];
  const sinDato = debate?.sin_dato || [];

  const fuera = lineup?.mandatory_hierarchy?.ruled_out || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>EL PLAN DE BORDALÁS</h2>
          <div className="sub">LAS ELECCIONES QUE ESTUVIERON REÑIDAS</div>
        </div>
        <span className={lineup.missing ? "pill crit" : "pill ok"}>
          {lineup.playable ?? 0}/11
        </span>
      </div>

      <div className="planbox">
        <div className="planbox-system">{sistema(cuenta)}</div>
        <div className="planbox-shape">{formaDelEquipo(cuenta)}</div>
      </div>

      <p className="note" style={{ textAlign: "left", marginTop: 8 }}>
        El dibujo no se elige antes: sale de coger a los once con más
        valor esperado y ver en qué formación caben.
      </p>

      {/* LA PARTE QUE IMPORTA */}
      <div className="planwhy">
        <b>
          {reñidos.length > 0
            ? "DECISIONES AJUSTADAS"
            : "NINGUNA DECISIÓN AJUSTADA"}
        </b>

        {duelos.length === 0 ? (
          <p className="dim" style={{ fontSize: 11, marginTop: 6 }}>
            No hay suplentes con pronóstico en ninguna posición, así que
            no había nada que elegir.
          </p>
        ) : (
          <ul>
            {(reñidos.length > 0 ? reñidos : duelos.slice(0, 1)).map(
              (duelo) => (
                <li key={duelo.position} style={{ marginBottom: 8 }}>
                  <div className="dim" style={{ fontSize: 10 }}>
                    {duelo.position_name.toUpperCase()} · margen{" "}
                    <b className={duelo.margen < 0 ? "down" : ""}>
                      {duelo.margen.toFixed(3)}
                    </b>
                  </div>
                  <Ficha jugador={duelo.entra} tono="up" />
                  <div className="dim" style={{ fontSize: 10, margin: "2px 0" }}>
                    por delante de
                  </div>
                  <Ficha jugador={duelo.se_queda} tono="down" />
                </li>
              )
            )}
          </ul>
        )}

        {reñidos.length === 0 && duelos.length > 0 && (
          <p className="dim" style={{ fontSize: 11, marginTop: 4 }}>
            El titular más justo saca {duelos[0].margen.toFixed(3)} al mejor
            suplente de su posición. No estaba cerca.
          </p>
        )}
      </div>

      {riesgo.length > 0 && (
        <div className="planwhy">
          <b>LO QUE PUEDE SALIR MAL</b>
          <ul>
            {riesgo.slice(0, 4).map((jugador) => (
              <li key={jugador.id}>
                <b>{jugador.name}</b>{" "}
                <span className="dim">
                  ({POSICIONES[jugador.position] || "?"}
                  {jugador.starter_probability != null
                    ? ` · solo ${Math.round(jugador.starter_probability)}% de salir`
                    : ""}
                  {jugador.availability &&
                  jugador.availability !== "DISPONIBLE"
                    ? ` · ${jugador.availability}`
                    : ""}
                  )
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sin dato no es dato: si a alguien del once le falta el
          pronostico, esa eleccion se tomo a ciegas y hay que
          decirlo. */}
      {sinDato.length > 0 && (
        <div className="planwhy">
          <b>ELEGIDOS SIN PRONÓSTICO</b>
          <ul>
            {sinDato.map((jugador) => (
              <li key={jugador.id}>
                <b>{jugador.name}</b>{" "}
                <span className="dim">
                  ({POSICIONES[jugador.position] || "?"}) — entró por valor y
                  puntos, no por quién va a jugar
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Un Dios fuera del once es la excepcion a la regla del
          dueño y no puede pasar en silencio. */}
      {fuera.length > 0 && (
        <div className="alert" style={{ marginTop: 10, marginBottom: 0 }}>
          FUERA DEL ONCE:{" "}
          {fuera
            .map((god) => `${god.name} (${god.reason || "sin motivo"})`)
            .join(" · ")}
        </div>
      )}

      <p className="note" style={{ textAlign: "left" }}>
        El número es el valor esperado de la semana, de 0 a 1: lo que
        puntúa su escalón en el equipo × lo probable que es que salga de
        inicio. El motor desempata además por rival, campo y penaltis, y
        eso no cabe en esta cifra.
      </p>
    </section>
  );
}
