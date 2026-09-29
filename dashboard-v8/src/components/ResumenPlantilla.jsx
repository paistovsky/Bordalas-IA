import { POSICIONES, SIN_DATO, euros, num, variacion } from "../lib/resumen";

/* PLANTILLA: ¿QUIÉN JUEGA Y CÓMO ESTÁ CADA UNO? (30/09/2026)
 *
 * Arriba, en UNA línea, los problemas: lesionados, dudas,
 * sancionados y huecos del once. Debajo, la plantilla por
 * posición: si es del once, su probabilidad de ser titular, cómo
 * está, los puntos, lo que vale y hacia dónde va su precio.
 *
 * La probabilidad sale de la misma cadena que las fichas del once
 * (`starter_probability ?? jp_confidence`); sin ella se escribe
 * «sin dato», nunca un 0 %.
 */

function estadoDe(p) {
  const parte = p.absence || {};
  if (parte.injury) {
    const n = parte.injury.matchdays_out;
    return {
      clase: "lesion",
      texto: `Lesionado${n != null ? ` · ${n} jorn.` : ""}`
    };
  }
  if (parte.suspension) return { clase: "sancion", texto: "Sancionado" };
  if (
    String(p.availability || "").toUpperCase() === "DUDA" ||
    String(p.status || "").toLowerCase() === "doubt"
  ) {
    return { clase: "duda", texto: "Duda" };
  }
  if (String(p.status || "").toLowerCase() === "injured") {
    return { clase: "lesion", texto: "Lesionado" };
  }
  return { clase: "ok", texto: "Bien" };
}

export default function ResumenPlantilla({ data }) {
  const lineup = data.lineup || {};
  const delOnce = new Map((lineup.players || []).map((p) => [p.id, p]));
  const plantilla = data.roster?.players || lineup.players || [];

  const filas = plantilla.map((p) => {
    const once = delOnce.get(p.id) || {};
    const prob =
      num(p.starter_probability) ??
      num(once.starter_probability) ??
      num(p.jp_confidence) ??
      num(once.jp_confidence);
    return {
      ...p,
      enElOnce: delOnce.has(p.id),
      prob: prob != null && prob > 0 ? prob : null,
      estado: estadoDe({ ...once, ...p, absence: p.absence || once.absence })
    };
  });

  const lesionados = filas.filter((f) => f.estado.clase === "lesion").length;
  const dudas = filas.filter((f) => f.estado.clase === "duda").length;
  const sancionados = filas.filter((f) => f.estado.clase === "sancion").length;
  const huecos = Number(lineup.missing || 0);

  const problemas = [
    lesionados ? `${lesionados} lesionado${lesionados === 1 ? "" : "s"}` : null,
    dudas ? `${dudas} duda${dudas === 1 ? "" : "s"}` : null,
    sancionados ? `${sancionados} sancionado${sancionados === 1 ? "" : "s"}` : null,
    huecos ? `${huecos} hueco${huecos === 1 ? "" : "s"} en el once` : null
  ].filter(Boolean);

  return (
    <div className="resumen">
      <section className="pan rs-card">
        <div className="rs-duo">
          <div>
            <div className="rs-lbl">Jugadores</div>
            <div className="rs-big">{plantilla.length || SIN_DATO}</div>
          </div>
          <div>
            <div className="rs-lbl">El once</div>
            <div className="rs-big">
              {lineup.playable ?? 0}/11
            </div>
            <div className="rs-lbl">{lineup.formation || ""}</div>
          </div>
        </div>
        <p className="rs-frase">
          {problemas.length
            ? problemas.join(" · ") + "."
            : "Todos disponibles y el once completo."}
        </p>
      </section>

      {POSICIONES.map(([pos, nombre]) => {
        const aqui = filas
          .filter((f) => Number(f.position) === pos)
          .sort((a, b) => Number(b.enElOnce) - Number(a.enElOnce) || Number(b.points || 0) - Number(a.points || 0));
        if (!aqui.length) return null;
        return (
          <section className="pan rs-card" key={pos}>
            <h2>{nombre.toUpperCase()}</h2>
            <ul className="rs-jugadores">
              {aqui.map((f) => (
                <li key={f.id || f.name}>
                  <div className="rs-j-nombre">
                    <b>{f.name}</b>
                    {f.enElOnce && <span className="rs-xi">XI</span>}
                    <small className={`rs-estado ${f.estado.clase}`}>{f.estado.texto}</small>
                  </div>
                  <div className="rs-j-datos">
                    <span>
                      {f.prob != null ? `titular ${Math.round(f.prob)} %` : "titular: sin dato"}
                    </span>
                    <span>{num(f.points) ?? 0} pts</span>
                    <span>
                      {euros(f.price)}{" "}
                      <small className={Number(f.price_increment || 0) > 0 ? "up" : Number(f.price_increment || 0) < 0 ? "down" : "dim"}>
                        {variacion(f.price_increment)}
                      </small>
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
