import { formatEuros, formatMoney } from "../lib/utils";

/**
 * LA ESTRATEGIA DE PEPE, A CORTO Y A LARGO.
 *
 * UNA HONESTIDAD POR DELANTE
 *
 *   Pepe no tiene un plan de temporada escrito en ningun sitio.
 *   Tiene una regla que aplica cada media hora, y la suma de esas
 *   aplicaciones ES la estrategia. Este cuadro no inventa un plan:
 *   coge la regla y la cuenta en palabras, con los numeros del
 *   ciclo de ahora mismo.
 *
 *   Por eso cada cifra de aqui sale de un campo publicado y no de
 *   una estimacion escrita a mano. Si mañana cambia el motor,
 *   cambia el cuadro solo. Un panel de estrategia que se escribe
 *   aparte del motor envejece en una semana y miente en dos.
 *
 * LOS TRES HORIZONTES
 *
 *   Hoy      - la jornada que se cierra en unas horas
 *   Mercado  - hasta el proximo reset del Computer
 *   Temporada- donde estamos y de que depende ganar
 */

function Bloque({ eyebrow, title, children }) {
  return (
    <div className="strat">
      <div className="strat-eyebrow">{eyebrow}</div>
      <div className="strat-title">{title}</div>
      <div className="strat-body">{children}</div>
    </div>
  );
}

export default function StrategyPanel({ data }) {
  const summary = data.summary || {};
  const lineup = data.lineup || {};
  const market = data.points_market || {};
  const exposure = data.exposure || {};
  const clock = data.market_clock || {};
  const competition = data.competition || {};
  const solvency = data.solvency || {};
  const acquisition = data.acquisition || {};

  const standings = competition.standings || [];

  const yo = standings.find((row) => row.is_current_user);
  const lider = standings[0];

  /* El valor de plantilla si discrimina desde el minuto uno; los
     puntos, en la jornada 2, valen todos cero. Decir "vas sexto"
     sin decir eso seria enseñar una posicion que no significa
     nada todavia. */
  const porValor = [...standings]
    .filter((row) => row.team_value != null)
    .sort((a, b) => Number(b.team_value) - Number(a.team_value));

  const puestoValor =
    porValor.findIndex((row) => row.is_current_user) + 1;

  const puntosRepartidos = standings.some(
    (row) => Number(row.points || 0) > 0
  );

  const objetivos = acquisition.targets || [];

  const quiere = objetivos.filter(
    (t) => t.decision === "BID" || Number(t.live_bid || 0) > 0
  );

  const precioPunto = market.rate_median;

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA ESTRATEGIA DE PEPE</h2>
          <div className="sub">CÓMO PIENSA GANAR ESTO</div>
        </div>
        {precioPunto ? (
          <span className="pill ok">{formatEuros(precioPunto)} / PUNTO</span>
        ) : null}
      </div>

      <Bloque
        eyebrow="HOY"
        title={
          lineup.missing
            ? `El once está incompleto: ${lineup.missing} hueco(s)`
            : "El once está cerrado"
        }
      >
        Quedan <b>{Number(summary.hours_to_deadline || 0).toFixed(1)} h</b> para
        el cierre de la jornada {summary.target_matchday ?? "—"}. Riesgo del
        once: <b>{summary.lineup_risk || "—"}</b>. Mientras la jornada no
        empiece, cualquier cambio en las alineaciones previstas puede mover el
        once, y por eso se recalcula cada media hora en vez de dejarlo hecho.
      </Bloque>

      <Bloque
        eyebrow="ESTE MERCADO"
        title={
          quiere.length
            ? `Quiere ${quiere.length} jugador(es) antes del reset`
            : "Nada que fichar a este precio"
        }
      >
        El mercado del Computer se resetea{" "}
        {clock.hours_to_reset != null ? (
          <>
            en <b>{Number(clock.hours_to_reset).toFixed(1)} h</b>
          </>
        ) : (
          "una vez al día"
        )}
        , y lo que no se puja hoy se pierde: esos jugadores no vuelven.
        Comprometidos <b>{formatMoney(exposure.committed_total)}</b> en{" "}
        <b>{exposure.operation_count || 0}</b> puja(s) viva(s), y quedan{" "}
        <b>{formatMoney(exposure.available_budget)}</b> por gastar
        {exposure.mode === "DEBT" ? " (de margen de deuda, no de caja)" : ""}.
        {solvency.needed ? (
          <>
            {" "}
            Con el saldo en rojo la prioridad es taparlo:{" "}
            <b>{formatMoney(solvency.deficit)}</b> de déficit contra{" "}
            <b>{solvency.incoming_offers || 0}</b> oferta(s) sobre la mesa.
          </>
        ) : null}
      </Bloque>

      <Bloque
        eyebrow="LA TEMPORADA"
        title={
          puntosRepartidos
            ? `${yo?.rank ?? "—"}º de ${standings.length} · ${
                yo?.points ?? 0
              } puntos`
            : "Todavía no se han repartido puntos"
        }
      >
        {/* Sin puntos repartidos, la clasificacion no dice nada y
            decir "vas sexto" seria hacerle creer al dueño algo que
            no ha pasado. Lo que si discrimina ya es el valor. */}
        {!puntosRepartidos && (
          <>
            La clasificación va toda a cero, así que el puesto no significa nada
            aún. Lo que sí se puede comparar es el equipo:{" "}
          </>
        )}
        Plantilla de <b>{formatMoney(yo?.team_value)}</b>,{" "}
        <b>{puestoValor > 0 ? `${puestoValor}º` : "—"}</b> de{" "}
        {porValor.length} por valor
        {lider && !lider.is_current_user ? (
          <>
            {" "}
            (el más caro es {lider.name === yo?.name ? "el nuestro" : porValor[0]?.name}{" "}
            con {formatMoney(porValor[0]?.team_value)})
          </>
        ) : null}
        .
      </Bloque>

      <div className="strat-rule">
        <b>LA REGLA QUE APLICA CADA MEDIA HORA</b>
        <ol>
          <li>
            Alinear a los once con más puntos esperados esta semana —escalón en
            su equipo × probabilidad de ser titular, ajustado por rival y campo.
          </li>
          <li>
            Fichar solo cuando el punto salga más barato que en el mercado
            {precioPunto ? (
              <>
                {" "}
                (<b>{formatEuros(precioPunto)}</b> de mediana hoy)
              </>
            ) : null}
            , contando lo que se recupera vendiendo al que sustituye.
          </li>
          <li>
            Cobrar las ofertas buenas por quien no juega, y no soltar nunca a un
            Dios salvo lesión o sanción.
          </li>
          <li>
            No quedarse sin poder alinear: hay un suelo por posición que ninguna
            venta puede romper.
          </li>
        </ol>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        Pepe no tiene un plan de temporada escrito: tiene esa regla, y la suma
        de aplicarla 48 veces al día <b>es</b> la estrategia. Este cuadro no la
        inventa, la lee del ciclo de ahora mismo.
      </p>
    </section>
  );
}
