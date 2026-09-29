import {
  ArrowRightLeft,
  Coins,
  Flag,
  MessageSquare,
  UserPlus
} from "lucide-react";

/* EL TABLÓN DE HOY (29/09/2026)
 *
 * Lo que ha pasado en la liga en las últimas 24 horas, en frases:
 * quién ficha, quién vende, quién cobra, cuándo acaba la jornada.
 * Sale de `tablon` en status.json:
 *
 *   { desde, horas, n, lineas: [{ hora, tipo, texto }], error? }
 *
 * - Sin la clave, no se pinta nada: no es «no ha pasado nada», es
 *   que la telemetría no lo publicó.
 * - Con n == 0, se dice: «Hoy no ha pasado nada en el tablón.»
 * - Lo más nuevo arriba. Las líneas donde sale Pepe, resaltadas.
 */

const ICONO = {
  market: [UserPlus, "fichaje"],
  transfer: [ArrowRightLeft, "venta"],
  bonus: [Coins, "dinero"],
  roundFinished: [Flag, "jornada"],
  leagueReset: [Flag, "jornada"],
  userPoints: [Flag, "jornada"],
  text: [MessageSquare, "mensaje"],
  poll: [MessageSquare, "mensaje"],
  userJoin: [MessageSquare, "mensaje"]
};

const NOSOTROS = "Pepe Bordalás";

/* "29/09 07:09" -> "0929 0709", para ordenar de más nuevo a más
   viejo. Lo que no se entiende se queda donde venía. */
function clave(hora) {
  const m = String(hora || "").match(/(\d{1,2})\/(\d{1,2})\D+(\d{1,2}):(\d{2})/);
  if (!m) return null;
  const dos = (x) => String(x).padStart(2, "0");
  return `${dos(m[2])}${dos(m[1])}${dos(m[3])}${m[4]}`;
}

export default function TablonPanel({ data }) {
  const tablon = data.tablon;

  if (!tablon || typeof tablon !== "object") return null;

  const lineas = (Array.isArray(tablon.lineas) ? tablon.lineas : [])
    .map((l, i) => ({ ...l, _i: i, _k: clave(l?.hora) }))
    .sort((a, b) =>
      a._k && b._k && a._k !== b._k ? (a._k < b._k ? 1 : -1) : a._i - b._i
    );

  const n = Number.isFinite(Number(tablon.n)) ? Number(tablon.n) : lineas.length;

  return (
    <section className="pan tablon">
      <div className="pan-head">
        <div>
          <h2>EL TABLÓN DE HOY</h2>
          <div className="sub">
            lo que ha pasado en la liga en las últimas {tablon.horas || 24} horas
          </div>
        </div>
        {n > 0 && <span className="pill idle">{n}</span>}
      </div>

      {n === 0 || !lineas.length ? (
        <p className="tablon-vacio">Hoy no ha pasado nada en el tablón.</p>
      ) : (
        <ul className="tablon-lista">
          {lineas.map((l) => {
            const [Icono, que] = ICONO[l.tipo] || [MessageSquare, "mensaje"];
            const nuestra = String(l.texto || "").includes(NOSOTROS);
            return (
              <li key={l._i} className={nuestra ? "nuestra" : undefined}>
                <span className="tablon-hora">{l.hora || "—"}</span>
                <Icono className="tablon-icono" size={15} aria-label={que} />
                <span className="tablon-texto">{l.texto || "sin texto"}</span>
              </li>
            );
          })}
        </ul>
      )}

    </section>
  );
}
