/**
 * LA VARA CON LA QUE SE ELIGE EL ONCE (18/09/2026)
 *
 *   Con la misma marca de la vara, un medio entregaba 8,51
 *   puntos por jornada y un defensa 5,82. El motor los trataba
 *   como iguales y alineaba defensas: salía 5-4-1, con un
 *   lateral de 0 puntos titular y dos delanteros sentados.
 *
 *   Ocho puntos en una jornada, cuando la temporada se decide
 *   por trece.
 *
 * ESTO SÍ DECIDE
 *
 *   No es un termómetro. Los factores están puestos y eligen el
 *   once de verdad. Por eso el panel enseña tres cosas que
 *   normalmente no se enseñan:
 *
 *     - de cuántas fichas sale cada factor, pegado al número;
 *     - el once que sale ahora, al lado del que salía antes;
 *     - la línea exacta para apagarlo.
 *
 * LA MUESTRA ES CORTA Y SE DICE
 *
 *   Tres jornadas. El factor del delantero se apoya en 18
 *   fichas. Eso viaja con el número en vez de quedarse en un
 *   informe que nadie relee.
 */

const POSICION = { 1: "PT", 2: "DF", 3: "MC", 4: "DL" };

const coma = (n, d = 3) =>
  n == null ? "—" : String(Number(n).toFixed(d)).replace(".", ",");

export default function VaraPanel({ data }) {
  const vara = data.vara || { available: false };

  if (!vara.available) {
    return (
      <section className="pan">
        <h2>LA VARA DEL ONCE</h2>
        <div className="empty">
          {vara.reason || "Sin medición de la vara."}
        </div>
      </section>
    );
  }

  const onces = vara.lineups || { available: false };

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA VARA DEL ONCE</h2>
          <div className="sub">
            Lo que entrega cada línea con la misma marca
          </div>
        </div>
        <span className={vara.active ? "pill ok" : "pill idle"}>
          {vara.active ? "FACTORES PUESTOS" : "VARA PLANA"}
        </span>
      </div>

      <div className={vara.active ? "alert" : "alert warn"}>
        {vara.reason}
      </div>

      {/* CADA FACTOR, CON SU MUESTRA AL LADO */}
      <table>
        <thead>
          <tr>
            <th>LÍNEA</th>
            <th className="n">FACTOR</th>
            <th className="n">MEDIDO</th>
            <th className="n">FICHAS</th>
            <th className="n">OBSERVACIONES</th>
            <th>NOTA</th>
          </tr>
        </thead>
        <tbody>
          {(vara.rows || []).map((f) => (
            <tr key={f.position}>
              <td>{f.name}</td>
              <td
                className={`n ${
                  f.factor > 1 ? "up" : f.factor < 1 ? "down" : "dim"
                }`}
              >
                <b>×{coma(f.factor)}</b>
              </td>
              <td className="n dim">×{coma(f.measured_factor)}</td>
              <td className="n">{f.players}</td>
              <td className="n dim">{f.observations}</td>
              <td className={f.applied ? "dim" : "down"}>
                {f.applied ? f.note || "" : "no se aplica"}
                {!f.applied && f.note ? ` · ${f.note}` : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* EL ONCE DE HOY, CON LA VARA NUEVA Y CON LA VIEJA */}
      {onces.available && (
        <>
          <div className="sub" style={{ marginTop: 12 }}>
            EL ONCE DE HOY, CON LAS DOS VARAS
          </div>

          <div className="kv">
            <span>Dibujo</span>
            <b className="mono">
              {onces.old.formation} → {onces.new.formation}
              {!onces.changed && " (sin cambios)"}
            </b>
          </div>

          {onces.changed && (
            <table>
              <thead>
                <tr>
                  <th>CAMBIO</th>
                  <th>JUGADOR</th>
                  <th className="n">POS</th>
                  <th className="n">TITULARIDAD</th>
                  <th className="n">PUNTOS</th>
                </tr>
              </thead>
              <tbody>
                {(onces.in || []).map((j) => (
                  <tr key={`in-${j.id}`}>
                    <td className="up">entra</td>
                    <td>{j.name}</td>
                    <td className="n dim">
                      {POSICION[j.position] || "?"}
                    </td>
                    <td className="n">
                      {j.starter_probability == null
                        ? "—"
                        : `${j.starter_probability} %`}
                    </td>
                    <td className="n">{j.points}</td>
                  </tr>
                ))}
                {(onces.out || []).map((j) => (
                  <tr key={`out-${j.id}`}>
                    <td className="down">sale</td>
                    <td>{j.name}</td>
                    <td className="n dim">
                      {POSICION[j.position] || "?"}
                    </td>
                    <td className="n">
                      {j.starter_probability == null
                        ? "—"
                        : `${j.starter_probability} %`}
                    </td>
                    <td className="n">{j.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <p className="note" style={{ textAlign: "left" }}>
            {onces.caveat}
          </p>
        </>
      )}

      {/* LA LÍNEA PARA APAGARLO, COPIABLE */}
      <div className="kv">
        <span>Para volver a la vara de antes</span>
        <b className="mono">{vara.disable_with}</b>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        Medido sobre {vara.window?.matchdays} jornadas y{" "}
        {vara.window?.players} fichas de las {vara.window?.squads}{" "}
        plantillas de la liga. <b>Muestra corta:</b> se aplicó igual
        porque la temporada corre, y por eso cada jornada se publican
        los puntos del once que alineamos, los del que habría elegido
        la vara vieja y los del mejor once posible.
      </p>
    </section>
  );
}
