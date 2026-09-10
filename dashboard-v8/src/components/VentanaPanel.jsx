import { formatMoney } from "../lib/utils";

/* ¿SE ABRIO LA VENTANA? ¿QUE PUJO Y QUE RENOVO? (10/09/2026)
 *
 * LA PRUEBA QUE TIENE QUE PASAR ESTE PANEL
 *
 *   Manana a las 07:15, el dueno tiene que poder contestar SOLO
 *   MIRANDO AQUI:
 *
 *       ¿gané a Aubameyang?  ¿se abrió la ventana?
 *       ¿qué renovó y a qué precio?
 *
 * POR QUE EXISTE
 *
 *   La ventana no se abrio NUNCA -el cron externo llegaba una
 *   hora tarde- y nadie lo noto en dos semanas, porque
 *   "FUERA_DE_VENTANA" es la misma frase que sale el resto del
 *   dia. Indistinguible de una noche normal.
 *
 *   Por eso lo primero que dice este panel no es que se hizo,
 *   sino CUANDO SE ENTRO POR ULTIMA VEZ. Si pasan 24 h, en rojo.
 */

function cuando(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-ES", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return String(iso).slice(5, 16).replace("T", " ");
  }
}

export default function VentanaPanel({ data }) {
  const renovacion = data.renovacion || {};
  const ventana = renovacion.ventana || {};
  const subasta = data.subasta || {};
  const outcomes = subasta.outcomes || {};
  const todas = subasta.outcomes_all || outcomes;
  const libro = subasta.bids_book || [];

  // SI NO HAY DATO, SE DICE. Un panel que desaparece cuando
  // falla es un panel que no se mira nunca — y este es
  // justamente el que tiene que cantar las ausencias.
  if (!renovacion.available && !subasta.available) {
    return (
      <section className="pan">
        <h2>LA VENTANA DEL RESET</h2>
        <div className="empty">
          Sin datos de la ventana en esta vuelta.{" "}
          {renovacion.reason || subasta.reason || ""}
        </div>
      </section>
    );
  }

  const renovados = renovacion.renewals || [];
  const pujas = subasta.bids || [];

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA VENTANA DEL RESET</h2>
          <div className="sub">
            {ventana.ever
              ? `última entrada ${cuando(ventana.last_at)}`
              : "nunca se ha entrado"}
          </div>
        </div>
        <span className={ventana.red ? "pill crit" : "pill ok"}>
          {ventana.red
            ? ventana.ever
              ? `${Math.round(ventana.hours_since)} H SIN ENTRAR`
              : "NUNCA"
            : `HACE ${Number(ventana.hours_since || 0).toFixed(1)} H`}
        </span>
      </div>

      {/* Lo que dijo la ultima entrada, con sus palabras. */}
      {ventana.reason && (
        <div className={ventana.red ? "alert crit" : "alert ok"}>
          {ventana.reason}
        </div>
      )}

      {/* QUE PUJO */}
      <h3 className="mini">PUJAS</h3>
      {pujas.length ? (
        <table className="tbl">
          <tbody>
            {pujas.map((b) => (
              <tr key={b.id || b.name}>
                <td>{b.name}</td>
                <td className="num">{formatMoney(b.bid)}</td>
                <td className="num sub">
                  {Math.round((b.win_odds || 0) * 100)} % se lo lleva
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="sub">
          {subasta.reason || "Sin pujas en esta ventana."}
        </div>
      )}

      {/* Y COMO ACABARON, CON NOMBRE.
          Es la respuesta literal a "¿gané a Aubameyang?", y por
          eso va con el nombre y no solo con el contador: un "1
          ganada" obliga a ir a buscar a quien, que es justo lo
          que la portada tiene que evitar. */}
      {libro.length > 0 && (
        <table className="tbl" style={{ marginTop: 6 }}>
          <tbody>
            {libro.map((b, i) => (
              <tr key={`${b.name}-${i}`}>
                <td>{b.name}</td>
                <td className="num">{formatMoney(b.amount)}</td>
                <td>
                  <span
                    className={
                      b.outcome === "WON"
                        ? "pill ok"
                        : b.outcome === "LOST"
                        ? "pill crit"
                        : "pill idle"
                    }
                  >
                    {b.outcome === "WON"
                      ? "GANADA"
                      : b.outcome === "LOST"
                      ? "perdida"
                      : b.outcome === "PENDING"
                      ? "se resuelve en el reset"
                      : "sin resolver"}
                  </span>
                </td>
                <td className="num sub">
                  {b.margin
                    ? `nos ganaron por ${formatMoney(b.margin)}`
                    : b.source === "MANUAL_DUENO"
                    ? "a mano"
                    : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {todas.available && (
        <div className="sub" style={{ marginTop: 4 }}>
          LIBRO: {todas.won} ganadas · {todas.lost} perdidas ·{" "}
          {todas.pending} pendientes
          {todas.median_lost_margin
            ? ` · nos ganaron por ${formatMoney(
                todas.median_lost_margin
              )} de mediana`
            : ""}
        </div>
      )}

      {/* QUE RENOVO Y A QUE PRECIO. Con el precio anterior al
          lado: renovar tambien re-precia, y si sube hay que
          poder verlo sin buscarlo. */}
      <h3 className="mini">RENOVACIONES</h3>
      {renovados.length ? (
        <table className="tbl">
          <tbody>
            {renovados.map((r) => (
              <tr key={r.id || r.name}>
                <td>{r.name}</td>
                <td className="num">{formatMoney(r.listed_price)}</td>
                <td className="num sub">
                  {r.precio_anterior &&
                  r.precio_anterior !== r.listed_price
                    ? `subido desde ${formatMoney(r.precio_anterior)}`
                    : "mismo precio"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="sub">
          {renovacion.reason || "Nada que renovar."}
        </div>
      )}
    </section>
  );
}
