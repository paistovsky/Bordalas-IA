import { formatEuros } from "../lib/utils";

/**
 * EL LIBRO DE PUJAS (05/09/2026)
 *
 *   Se escribe desde el 03/09 y no lo enseñaba nadie. Es lo unico
 *   que contesta a "¿por cuanto nos ganan?", que es la pregunta
 *   que hay que responder antes de tocar la agresividad.
 *
 * POR QUE SE ENSEÑA VACIO
 *
 *   Hoy sale `placed: 0`, porque solo registra las pujas que pone
 *   PEPE y lleva sin comprar nada. Un panel que aparece el dia
 *   que hay datos no se mira nunca: se enseña desde el principio,
 *   diciendo que todavia no hay nada.
 *
 *   Y "todavia no hay nada" es distinto de "0 %". Un 0 % de
 *   victorias se lee como "pierde siempre"; la verdad es que no
 *   ha jugado. Por eso los huecos van con guion y no con ceros.
 */

function Fila({ etiqueta, valor, tono, titulo }) {
  return (
    <div className="kv" title={titulo}>
      <span>{etiqueta}</span>
      <b className={tono ? `mono ${tono}` : "mono"}>{valor}</b>
    </div>
  );
}

export default function BidOutcomesPanel({ data }) {
  const libro = data.bidOutcomes || { available: false };

  const puestas = Number(libro.placed || 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LIBRO DE PUJAS</h2>
          <div className="sub">
            Lo que Pepe puso, y cómo acabó
          </div>
        </div>
        <span className={libro.available ? "pill ok" : "pill idle"}>
          {puestas} PUESTA{puestas === 1 ? "" : "S"}
        </span>
      </div>

      {!libro.available ? (
        <div className="empty">
          Todavía no hay ninguna puja registrada. El libro se apunta
          cuando Pepe puja y se cierra contra el tablón, así que hasta
          la primera puja no hay nada que medir.
          <div className="dim" style={{ marginTop: 6 }}>
            No es un 0 %: es que aún no ha jugado esta mano.
          </div>
        </div>
      ) : (
        <>
          <Fila etiqueta="Puestas" valor={puestas} />
          <Fila etiqueta="Ganadas" valor={libro.won} tono="up" />
          <Fila etiqueta="Perdidas" valor={libro.lost} tono="down" />

          <Fila
            etiqueta="Se gana"
            valor={
              libro.win_rate != null
                ? `${Math.round(Number(libro.win_rate) * 100)} %`
                : "—"
            }
            titulo="Ganadas entre puestas."
          />

          {/* Por cuanto nos ganan. La mediana aguanta un
              atraco suelto; el peor caso dice cuanto puede
              doler. Las dos, o ninguna dice nada. */}
          <Fila
            etiqueta="Nos ganan por (mediana)"
            valor={
              libro.median_lost_margin != null
                ? formatEuros(libro.median_lost_margin)
                : "—"
            }
            tono="down"
            titulo={`Sobre ${libro.lost_with_margin || 0} puja(s) perdidas con importe conocido.`}
          />

          <Fila
            etiqueta="Peor caso"
            valor={
              libro.worst_lost_margin != null
                ? formatEuros(libro.worst_lost_margin)
                : "—"
            }
            tono="down"
          />

          {(Number(libro.pending || 0) > 0 ||
            Number(libro.unknown || 0) > 0) && (
            <div className="dim" style={{ marginTop: 8 }}>
              {libro.pending || 0} sin resolver ·{" "}
              {libro.unknown || 0} sin rastro tras 72 h
            </div>
          )}
        </>
      )}
    </section>
  );
}
