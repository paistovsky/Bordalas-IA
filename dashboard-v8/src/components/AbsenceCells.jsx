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

export function Lesion({ absence, availability }) {
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

  return (
    <div>
      <span className={grave ? "pill crit" : "pill warn"}>
        {parte.detail || "LESIONADO"}
      </span>

      {(parte.prognosis || fuera) && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {[parte.prognosis, fuera].filter(Boolean).join(" · ")}
        </div>
      )}
    </div>
  );
}

export function Sancion({ absence }) {
  const parte = absence?.suspension;

  if (!parte) return <span className="dim">—</span>;

  const partidos =
    parte.matches_total != null
      ? `${parte.matches_served ?? 0} de ${parte.matches_total} cumplidos`
      : jornadas(parte.matchdays_out);

  return (
    <div>
      <span className="pill crit">{parte.detail || "SANCIONADO"}</span>

      {partidos && (
        <div className="dim" style={{ fontSize: 9, marginTop: 2 }}>
          {partidos}
          {parte.basis === "SUPUESTO" ? " · estimado" : ""}
        </div>
      )}
    </div>
  );
}
