import { formatMoney } from "../lib/utils";

/**
 * COMO PIENSA PEPE TAPAR EL AGUJERO, Y CUANDO.
 *
 * EL CASO (20/08/2026)
 *
 *   "Tenemos -5 M de deuda y no se que planes tiene para
 *    solventar eso ni cuando lo va a hacer."
 *
 *   Los tres planes se calculan enteros en cada ciclo -quien se
 *   vende, por cuanto, con que saldo se queda y cuanto empeora
 *   el once- y no salian en ninguna pantalla. Otra vez el dato
 *   calculado, guardado y ciego.
 *
 * LOS TRES PLANES NO SON ALTERNATIVAS, SON ESCALONES
 *
 *   A  - se tapa sin tocar el once. Es el que se usa siempre que
 *        se pueda.
 *   B1 - hay que tocar el once, pero sigue habiendo once. Cuesta
 *        puntos y se dice cuantos.
 *   C  - emergencia: se rompe el once. Solo si no hay otra.
 *
 *   Que exista un plan C no significa que vaya a pasar: significa
 *   que aunque todo salga mal, la deuda se puede tapar. Ese es el
 *   sentido de calcular los tres.
 *
 * EL CUANDO NO ES UNA FECHA
 *
 *   Pepe no ejecuta "el plan A" de una vez. Cobra oferta a oferta
 *   segun van mereciendo la pena, y la urgencia sube sola con el
 *   reloj de la jornada. Los planes son la PRUEBA de que el
 *   agujero es tapable; la ejecucion va por otro lado.
 */

const FASES = [
  ["NORMAL", "más de 48 h", "Vigila. Estar en rojo es legal."],
  ["PREPARATION", "menos de 48 h", "Prioriza tapar el agujero."],
  ["HIGH_ATTENTION", "menos de 12 h", "Sube por encima del mercado."],
  ["FINALIZATION", "menos de 2 h", "Casi todo lo demás se aparta."],
  ["HARD_SAFETY", "pasado el T-90", "Solo genera liquidez y guarda el XI."]
];

const TIER_TONE = { A: "ok", B1: "warn", B: "warn", C: "crit" };

const TIER_TITULO = {
  A: "PLAN A · sin tocar el once",
  B1: "PLAN B · toca el once, sigue habiendo once",
  B: "PLAN B · toca el once, sigue habiendo once",
  C: "PLAN C · emergencia, se rompe el once"
};

function Plan({ plan }) {
  const tier = String(plan.tier || plan.plan_kind || "").toUpperCase();
  const tono = TIER_TONE[tier] || "idle";
  const perdida = Number(plan.lineup_score_loss_percent || 0);

  /* VERDE, AMARILLO Y ROJO, Y QUE SE VEA (20/08/2026)
     El color iba solo en una pastilla de nueve pixeles. Estos
     tres cuadros se leen de un vistazo o no se leen: el semaforo
     tiene que ser la tarjeta entera. */
  return (
    <div className={`plan2 plan2-${tono}`}>
      <div className="plan2-head">
        <span className={`pill ${tono}`}>{tier}</span>
        <b>{TIER_TITULO[tier] || plan.plan_kind}</b>
      </div>

      <div className="plan2-who">
        {(plan.player_names || []).join(" · ") || "—"}
      </div>

      <div className="kv">
        <span>Entra</span>
        <b className="mono">{formatMoney(plan.total_amount)}</b>
      </div>

      <div className="kv">
        <span>Saldo después</span>
        <b className={Number(plan.post_balance) >= 0 ? "up" : "down"}>
          {formatMoney(plan.post_balance)}
        </b>
      </div>

      <div className="kv">
        <span>Once después</span>
        <b className={plan.lineup_complete ? "" : "down"}>
          {plan.playable_count ?? 0}/11
          {plan.formation_after ? ` · ${plan.formation_after}` : ""}
        </b>
      </div>

      {/* Lo que cuesta en puntos. Un plan que tapa el agujero
          rompiendo el equipo no es gratis, y el precio va aqui y
          no en una nota al pie. */}
      <div className="kv">
        <span>Coste deportivo</span>
        <b className={perdida > 0 ? "down" : "dim"}>
          {perdida > 0 ? `−${perdida.toFixed(1)} %` : "ninguno"}
        </b>
      </div>

      {!plan.restores_solvency && (
        <div className="plan2-warn">No llega a tapar el agujero.</div>
      )}
    </div>
  );
}

export default function SolvencyPlansPanel({ solvency, summary }) {
  const necesita = Boolean(solvency?.needed);
  const planes = solvency?.plans || {};
  const lista = planes.plans || [];

  if (!necesita) {
    return (
      <section className="pan">
        <div className="pan-head">
          <div>
            <h2>PLAN PARA LA DEUDA</h2>
            <div className="sub">CÓMO LA TAPA Y CUÁNDO</div>
          </div>
          <span className="pill ok">SIN DEUDA</span>
        </div>
        <div className="empty">
          El saldo está en positivo: no hay nada que tapar.
        </div>
      </section>
    );
  }

  if (!planes.available || lista.length === 0) {
    return (
      <section className="pan">
        <h2>PLAN PARA LA DEUDA</h2>
        <div className="empty">
          Hay {formatMoney(solvency.deficit)} de déficit y no se ha podido
          calcular ningún plan. Eso es un problema: significa que Pepe no sabe
          cómo taparlo.
        </div>
      </section>
    );
  }

  const fase = summary?.phase;
  const horas = Number(summary?.hours_to_deadline || 0);

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>PLAN PARA LA DEUDA</h2>
          <div className="sub">CÓMO LA TAPA Y CUÁNDO</div>
        </div>
        <span className="pill crit">{formatMoney(solvency.deficit)}</span>
      </div>

      <div className="kv">
        <span>Ofertas sobre la mesa</span>
        <b>{solvency.incoming_offers ?? 0}</b>
      </div>

      <div className="kv">
        <span>Publicados en venta</span>
        <b>
          {solvency.listed ?? 0}
          {solvency.to_list ? ` · faltan ${solvency.to_list}` : ""}
        </b>
      </div>

      {/* Lo que se puede sacar sin romper nada, frente a lo que
          se podria sacar quemando el equipo. La distancia entre
          esos dos numeros es el margen real. */}
      {planes.trading_safe_total != null && (
        <div className="kv">
          <span>Se puede sacar sin romper el once</span>
          <b className="mono">{formatMoney(planes.trading_safe_total)}</b>
        </div>
      )}

      <div className="plan2-list">
        {lista.map((plan, i) => (
          <Plan key={plan.plan_kind || i} plan={plan} />
        ))}
      </div>

      <div className="strat-rule">
        <b>CUÁNDO LO HACE</b>
        <p style={{ margin: "6px 0 8px" }}>
          No hay una hora marcada. Pepe cobra oferta a oferta según van
          mereciendo la pena, y la urgencia sube sola conforme se acerca el
          cierre de la jornada. Los planes son la <b>prueba</b> de que el
          agujero se puede tapar; el cobro va por su cuenta.
        </p>

        <div className="fases">
          {FASES.map(([id, cuando, que]) => (
            <div
              key={id}
              className={id === fase ? "fase on" : "fase"}
            >
              <b>{cuando}</b>
              <span>{que}</span>
            </div>
          ))}
        </div>

        <p style={{ margin: "8px 0 0" }}>
          Ahora mismo: <b>{fase || "—"}</b>, quedan{" "}
          <b>{horas.toFixed(1)} h</b> para el cierre.
        </p>
      </div>

      <p className="note" style={{ textAlign: "left" }}>
        Que exista un plan C no significa que vaya a pasar. Significa que
        aunque todo salga mal, la deuda se puede tapar. Para eso se calculan
        los tres.
      </p>
    </section>
  );
}
