import { formatEuros, formatMoney } from "../lib/utils";

/**
 * LA ESTRATEGIA DE PEPE: QUE VA A HACER, EN QUE ORDEN Y CUANDO.
 *
 * QUE FALLABA EN LA PRIMERA VERSION (20/08/2026)
 *
 *   "No me entero bien del plan."
 *
 *   Y tenia razon. Habia tres parrafos de prosa con los numeros
 *   metidos dentro de las frases, y debajo cuatro reglas
 *   generales que son las mismas todos los dias. Eso no es un
 *   plan, es un manifiesto: describe la POSTURA de Pepe, no lo
 *   que va a hacer esta tarde.
 *
 *   Ademas repetia en prosa lo que la tira de arriba ya dice en
 *   numeros grandes: saldo, cierre, reset, pujas.
 *
 * QUE HACE AHORA
 *
 *   Contesta tres preguntas en este orden, y cada una con
 *   nombres propios en vez de cantidades abstractas:
 *
 *     1. Lo siguiente que va a hacer, y por que gana esa y no
 *        otra de la cola.
 *     2. A quien quiere fichar antes de que se cierre el
 *        mercado, con lo que promete cada uno.
 *     3. Que le esta frenando ahora mismo.
 *
 *   La regla general se queda, pero al final y en una linea. Es
 *   contexto, no noticia.
 */

const POSICIONES = { 1: "POR", 2: "DEF", 3: "MC", 4: "DEL" };

function Paso({ n, titulo, tono = "", children }) {
  return (
    <div className="paso">
      <div className={`paso-n ${tono}`}>{n}</div>
      <div className="paso-cuerpo">
        <div className="paso-titulo">{titulo}</div>
        <div className="paso-detalle">{children}</div>
      </div>
    </div>
  );
}

export default function StrategyPanel({ data }) {
  const summary = data.summary || {};
  const lineup = data.lineup || {};
  /* DOS BLOQUES LEIDOS CON EL NOMBRE EQUIVOCADO (21/08/2026)
   *
   *   `data` sale del normalizador, que renombra `points_market`
   *   a `pointsMarket` y `market_clock` a `marketClock`. Aqui se
   *   pedian con el nombre del JSON crudo, asi que los dos
   *   llegaban vacios SIN FALLAR: quedaban en `{}` y la pantalla
   *   se caia a los textos de reserva.
   *
   *   Resultado visible: "Ninguno de los que hay baja de los —
   *   por punto", con un guion donde va el precio, y "el mercado
   *   se resetea una vez al dia" en vez de las horas que faltan.
   *   Tambien desaparecia la etiqueta de EUR/PUNTO de la
   *   cabecera.
   *
   *   Un `|| {}` es comodo y silencia justo esto. */
  const market = data.pointsMarket || {};
  const exposure = data.exposure || {};
  const clock = data.marketClock || {};
  const solvency = data.solvency || {};
  const acquisition = data.acquisition || {};

  const siguiente = data.nextAction || {};
  const cola = data.priorities || [];

  /* Lo que de verdad quiere fichar, con nombre. "Quiere 3
     jugadores" no dice nada; "quiere a Bigas por 2,28 M porque
     suma 15 puntos" si. */
  const objetivos = (acquisition.targets || [])
    .filter(
      (t) => t.decision === "BID" || Number(t.live_bid || 0) > 0
    )
    .slice(0, 4);

  /* Lo que le frena: de la cola, lo que NO puede ejecutar. Es la
     respuesta a "¿y por que no ha hecho tal cosa?". */
  const frenados = cola.filter(
    (item) =>
      !item.executable &&
      item.type !== "IDLE" &&
      item.type !== siguiente.type
  );

  const precioPunto = market.rate_median;
  const horas = Number(summary.hours_to_deadline || 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>LA ESTRATEGIA DE PEPE</h2>
          <div className="sub">QUÉ VA A HACER Y EN QUÉ ORDEN</div>
        </div>
        {precioPunto ? (
          <span className="pill ok">{formatEuros(precioPunto)} / PUNTO</span>
        ) : null}
      </div>

      {/* ---------------------------------------------------
          1. LO SIGUIENTE
          --------------------------------------------------- */}
      <Paso
        n="1"
        tono={siguiente.executable ? "ok" : "idle"}
        titulo={
          siguiente.label
            ? `Ahora: ${siguiente.label.toLowerCase()}`
            : "Ahora: nada que ejecutar"
        }
      >
        {siguiente.reason ||
          "Ninguna acción de la cola es ejecutable en este ciclo."}
        {cola.length > 0 && (
          <div className="paso-cola">
            {cola
              .filter((item) => item.type !== "IDLE")
              .map((item, i) => (
                <span
                  key={i}
                  className={
                    item.type === siguiente.type
                      ? "colita on"
                      : item.executable
                      ? "colita"
                      : "colita off"
                  }
                >
                  {item.label}
                </span>
              ))}
          </div>
        )}
      </Paso>

      {/* ---------------------------------------------------
          2. A QUIEN QUIERE, CON NOMBRE
          --------------------------------------------------- */}
      <Paso
        n="2"
        tono={objetivos.length ? "warn" : "idle"}
        titulo={
          objetivos.length
            ? `Antes del reset quiere ${objetivos.length} jugador(es)`
            : "No hay nadie que valga la pena al precio de hoy"
        }
      >
        {objetivos.length > 0 ? (
          <>
            <div className="paso-fichas">
              {objetivos.map((t) => (
                <div className="ficha" key={t.id}>
                  <b>{t.name}</b>
                  <span className="dim">
                    {POSICIONES[t.position] || "?"} ·{" "}
                    {formatMoney(t.our_bid || t.market_price)}
                    {t.promised_points
                      ? ` · +${t.promised_points} pts`
                      : ""}
                    {t.win_probability != null
                      ? ` · gana ${Math.round(
                          Number(t.win_probability) * 100
                        )} %`
                      : ""}
                  </span>
                  {t.replaces && (
                    <span className="dim">
                      sustituye a {t.replaces}
                      {t.replaces_starter ? " (titular)" : ""}
                    </span>
                  )}
                </div>
              ))}
            </div>
            <div className="paso-nota">
              Quedan{" "}
              <b>
                {clock.hours_to_reset != null
                  ? `${Number(clock.hours_to_reset).toFixed(1)} h`
                  : "—"}
              </b>{" "}
              para el reset y lo que no se puje hoy se pierde. Disponible{" "}
              <b>{formatMoney(exposure.available_budget)}</b>
              {exposure.mode === "DEBT" ? " de margen de deuda" : ""}.
            </div>
          </>
        ) : (
          <>
            El mercado se resetea{" "}
            {clock.hours_to_reset != null
              ? `en ${Number(clock.hours_to_reset).toFixed(1)} h`
              : "una vez al día"}
            . Ninguno de los que hay baja de los{" "}
            {precioPunto ? formatEuros(precioPunto) : "—"} por punto que
            cuesta en el mercado.
          </>
        )}
      </Paso>

      {/* ---------------------------------------------------
          3. QUE LE FRENA
          --------------------------------------------------- */}
      <Paso
        n="3"
        tono={solvency.needed ? "crit" : "idle"}
        /* LA PANTALLA DISCUTIENDO CON LA PANTALLA (21/08/2026)
         *
         *   El titulo decia "Nada le esta frenando" mientras la
         *   columna de al lado listaba tres frenos. Miraba solo
         *   si habia deuda; los frenos no los miraba nadie.
         *
         *   Un panel que se contradice consigo mismo gasta mas
         *   confianza que uno que se equivoca: si no se cree ni
         *   el, por que iba a creerselo el dueño. */
        titulo={
          solvency.needed
            ? `Tiene que sanear ${formatMoney(solvency.deficit)}`
            : frenados.length > 0
            ? `${frenados.length} cosa(s) le están frenando`
            : "Nada le está frenando"
        }
      >
        {solvency.needed ? (
          <>
            Con el saldo en rojo, tapar el agujero manda sobre fichar. Hay{" "}
            <b>{solvency.incoming_offers || 0}</b> oferta(s) sobre la mesa y{" "}
            <b>{solvency.listed || 0}</b> jugador(es) publicados. El plan
            concreto está justo debajo.
          </>
        ) : frenados.length > 0 ? (
          <>
            {frenados.map((f) => f.label).join(", ")} — calculado pero no
            ejecutable en este ciclo.
          </>
        ) : (
          "Puede operar con normalidad."
        )}
      </Paso>

      {/* ---------------------------------------------------
          EL RELOJ, QUE ES LO QUE ORDENA TODO
          --------------------------------------------------- */}
      <div className="paso-reloj">
        <span>
          Cierre de la jornada {summary.target_matchday ?? "—"} en{" "}
          <b>{horas.toFixed(1)} h</b>
        </span>
        <span className="dim">·</span>
        <span>
          Once <b className={lineup.missing ? "down" : "up"}>
            {lineup.playable ?? 0}/11
          </b>
        </span>
        <span className="dim">·</span>
        <span>
          Fase <b>{summary.phase || "—"}</b>
        </span>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        La regla que aplica cada media hora: alinear a los once con más puntos
        esperados —escalón × probabilidad de ser titular, ajustado por rival y
        campo—; fichar solo si el punto sale por debajo de mercado contando lo
        que se recupera del sustituido; cobrar las ofertas buenas por quien no
        juega y no soltar nunca a un Dios; y no bajar del suelo por posición.
        Pepe no tiene un plan de temporada escrito: tiene esa regla, y la suma
        de aplicarla 48 veces al día <b>es</b> la estrategia.
      </p>
    </section>
  );
}
