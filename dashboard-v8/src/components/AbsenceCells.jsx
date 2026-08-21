/**
 * LESION Y SANCION, EN DOS COLUMNAS Y CON EL PARTE.
 *
 * POR QUE VIVEN AQUI
 *
 *   Estas dos celdas nacieron dentro de MarketPage el 19/08. El
 *   20/08 la tabla de PLANTILLA pidio lo mismo, y una segunda
 *   copia habria sido una copia que se desincroniza: el dia que
 *   FutbolFantasy cambie el parte, una pantalla lo cuenta bien y
 *   la otra miente.
 *
 * EL DETALLE NO VIVE EN LA TABLA (21/08/2026)
 *
 *   El pronostico y los partidos cumplidos iban en gris pequeño
 *   debajo de la etiqueta, en todas las filas a la vez. Con
 *   veinte jugadores eso es una pared de letra menuda que tapa
 *   lo unico que se lee de un vistazo: la etiqueta.
 *
 *   Ahora el detalle va en el recuadro que sale al pasar el
 *   raton. Sigue estando; deja de estorbar. `detalle` lo trae de
 *   vuelta a la linea para quien lo quiera.
 *
 * LA REGLA
 *
 *   Un jugador sin parte y disponible sale con una raya, no con
 *   un "OK" verde. Verde significa que sabemos algo bueno; una
 *   raya significa que no hay nada que contar, que es distinto.
 */

function jornadas(n) {
  if (n == null) return null;
  if (n === 0) return "vuelve ya";
  return `${n} jornada${n === 1 ? "" : "s"}`;
}

export function Lesion({ absence, availability, detalle = false }) {
  const parte = absence?.injury;

  if (!parte) {
    // Tocado sin parte detallado: se dice, no se calla.
    if (availability === "DUDA") {
      return <span className="pill warn">DUDA</span>;
    }
    return <span className="dim">—</span>;
  }

  const fuera = jornadas(parte.matchdays_out);

  const grave =
    Number(parte.matchdays_out || 0) >= 4 ||
    parte.severity_label === "GRAVE";

  const pie = [parte.prognosis, fuera].filter(Boolean).join(" · ");

  return (
    <div title={pie || undefined}>
      <span className={grave ? "pill crit" : "pill warn"}>
        {parte.detail || "LESIONADO"}
      </span>

      {detalle && pie && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {pie}
        </div>
      )}
    </div>
  );
}

export function Sancion({ absence, detalle = false }) {
  const parte = absence?.suspension;

  if (!parte) return <span className="dim">—</span>;

  const partidos =
    parte.matches_total != null
      ? `${parte.matches_served ?? 0} de ${parte.matches_total} cumplidos`
      : jornadas(parte.matchdays_out);

  const pie = partidos
    ? `${partidos}${parte.basis === "SUPUESTO" ? " · estimado" : ""}`
    : "";

  return (
    <div title={pie || undefined}>
      <span className="pill crit">{parte.detail || "SANCIONADO"}</span>

      {detalle && pie && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {pie}
        </div>
      )}
    </div>
  );
}
