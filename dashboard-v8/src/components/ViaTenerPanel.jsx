/**
 * ¿SIGUE HABIENDO ALGO DEBAJO DE LA VIA TENER? (17/09/2026)
 *
 *   La vía se apoya en un tramo del retrotest. Si ese tramo deja
 *   de rendir el listón, la vía no está midiendo nada: está
 *   repitiendo una conclusión de agosto.
 *
 *   Esta línea dice cuál la sostiene hoy, cuál va más justo y
 *   cuánto le sobra. El aviso llega ANTES de que se apague.
 *
 * "SIN MUESTRA" NO ES "MALO"
 *
 *   Un tramo sin medir sale aparte, en gris. Ausencia de dato no
 *   es dato, y confundirlos aquí sería apagar una vía por no
 *   haberla mirado.
 */
export default function ViaTenerPanel({ data }) {
  const estado = data.holdRoute || { available: false };

  if (!estado.available) {
    return (
      <section className="pan">
        <h2>VÍA TENER</h2>
        <div className="empty">
          {estado.reason || "Sin retrotest con el que comprobarla."}
        </div>
      </section>
    );
  }

  const pct = (v) =>
    v == null ? "—" : `${String((v * 100).toFixed(2)).replace(".", ",")} %`;

  const cerca = estado.closest;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>VÍA TENER</h2>
          <div className="sub">El tramo que la sostiene, medido en cada ciclo</div>
        </div>
        <span className={estado.on ? "pill ok" : "pill crit"}>
          {estado.on ? "ENCENDIDA" : "APAGADA"}
        </span>
      </div>

      <div className={estado.on ? "alert" : "alert crit"}>
        <b>{estado.on ? "Vía TENER encendida" : "VÍA TENER APAGADA"}:</b>{" "}
        {estado.reason}
      </div>

      <table>
        <thead>
          <tr>
            <th>TRAMO DE TASA</th>
            <th className="n">N</th>
            <th className="n">RINDE A {estado.horizon_days} DÍAS</th>
            <th className="n">EN PÉRDIDA</th>
            <th className="n">SOBRE EL LISTÓN</th>
            <th>ESTADO</th>
          </tr>
        </thead>
        <tbody>
          {(estado.buckets || []).map((t) => (
            <tr key={t.bucket} className={cerca && t.bucket === cerca.bucket ? "me" : ""}>
              <td>{t.bucket}</td>
              <td className="n dim">{t.n ?? "—"}</td>
              <td className="n">{pct(t.median)}</td>
              <td className="n">{pct(t.loss_rate)}</td>
              <td className={`n ${t.margin > 0 ? "up" : t.margin < 0 ? "down" : ""}`}>
                {t.margin == null
                  ? "—"
                  : `${t.margin > 0 ? "+" : "−"}${String(
                      (Math.abs(t.margin) * 100).toFixed(2)
                    ).replace(".", ",")}`}
              </td>
              <td className={t.backed ? "up" : t.measured ? "down" : "dim"}>
                {t.bucket === "CAE"
                  ? "no se compra ahí"
                  : t.backed
                  ? "respalda"
                  : t.measured
                  ? "apagado"
                  : "sin muestra"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
