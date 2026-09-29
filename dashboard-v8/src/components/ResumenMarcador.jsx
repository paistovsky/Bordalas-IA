import { SIN_DATO, num } from "../lib/resumen";

/* MARCADOR: ¿ACIERTA PEPE CON EL ONCE? (30/09/2026)
 *
 * Jornada a jornada, en una frase: los puntos que sacó el once
 * contra los que podía sacar con la misma plantilla bien puesta.
 *
 * Una jornada sin nota se dice como tal -el once anotado no es el
 * que jugó, o no se anotó-: una nota inventada se usaría para
 * decidir. El número de jornada no viene en status.json: se
 * identifica por el día en que se anotó el once.
 */

function fecha(iso) {
  const m = String(iso || "").match(/^\d{4}-(\d{2})-(\d{2})/);
  return m ? `${m[2]}/${m[1]}` : null;
}

export default function ResumenMarcador({ data }) {
  const marcador = data.marcador || {};
  const resumen = marcador.resumen || {};
  // De la más reciente a la más vieja, por el día en que se anotó
  // (el número de ronda de Biwenger no va en orden).
  const jornadas = [...(marcador.jornadas || [])].sort((a, b) =>
    String(b.escrito_en || "").localeCompare(String(a.escrito_en || ""))
  );
  const buenas = jornadas.filter((j) => j.medible && j.cuadra);

  // La media la da el motor, o no hay media: si él la deja vacía
  // es a propósito -una media de jornadas que no cuadran no mide
  // nada- y aquí no se recalcula por su cuenta.
  const media = num(resumen.eficiencia_media);

  return (
    <div className="resumen">
      <section className="pan rs-card">
        <div className="rs-duo">
          <div>
            <div className="rs-lbl">Nota media del once</div>
            <div className="rs-big">{media != null ? `${media} %` : "sin nota"}</div>
            <div className="rs-lbl">de lo máximo posible con su plantilla</div>
          </div>
          <div>
            <div className="rs-lbl">Jornadas con nota</div>
            <div className="rs-big">
              {num(resumen.jornadas_fiables) ?? buenas.length}
              <small className="rs-de"> de {jornadas.length}</small>
            </div>
          </div>
        </div>
        {!buenas.length && (
          <p className="rs-frase">
            Todavía no hay ninguna jornada con nota fiable: el once
            anotado no coincide con el que jugó, o no se anotó.
          </p>
        )}
      </section>

      <section className="pan rs-card">
        <h2>JORNADA A JORNADA</h2>
        {!jornadas.length ? (
          <p className="rs-frase dim">{SIN_DATO}.</p>
        ) : (
          <ul className="rs-lista">
            {jornadas.map((j) => {
              const cuando = fecha(j.escrito_en);
              const nombre = cuando ? `Jornada anotada el ${cuando}` : `Jornada ${j.round_id}`;
              let frase;
              let nota = "—";
              if (!j.medible) {
                frase = "Sin nota: no se anotó qué once jugó.";
              } else if (!j.cuadra) {
                frase = "Sin nota: el once anotado no es el que jugó.";
              } else {
                frase = `Sacó ${j.puntos_once ?? j.puntos_biwenger} de ${j.mejor_puntos} posibles.`;
                nota = `${j.eficiencia} %`;
              }
              return (
                <li key={j.round_id}>
                  <span>
                    {nombre}
                    <small>{frase}</small>
                  </span>
                  <b>{nota}</b>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
