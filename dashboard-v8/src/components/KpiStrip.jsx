import { formatMoney } from "../lib/utils";

/**
 * Tira de estado. Seis numeros y de donde salen.
 *
 * El ultimo era "Objetivos hoy 0/20" y con tres pujas vivas en
 * Biwenger seguia diciendo 0. Contaba cuantos candidatos pasan el
 * filtro AHORA, que baja a cero justo despues de pujar por ellos:
 * el numero se apagaba precisamente cuando Pepe acababa de actuar.
 *
 * Lo primero que hay que ver es lo que hay puesto. Lo que se
 * podria pujar va debajo, cuando no hay nada puesto.
 */

function Kpi({ label, value, sub, tone = "" }) {
  return (
    <div className={tone ? `kpi ${tone}` : "kpi"}>
      <div className="l">{label}</div>
      <div className="v">{value}</div>
      <div className="s">{sub}</div>
    </div>
  );
}

export default function KpiStrip({ data }) {
  const summary = data.summary || {};
  const exposure = data.exposure || {};
  const clock = data.marketClock || {};
  const lineup = data.lineup || {};
  const acquisition = data.acquisition || {};

  // El bolsillo de fichar. Otro numero, otra cosa.
  const fichajes = exposure.acquisition || {};

  const balance = Number(summary.balance || 0);
  const hoursReset = Number(clock.hours_to_reset || 0);

  return (
    <div className="strip">
      <Kpi
        label="Saldo"
        value={formatMoney(balance)}
        sub={`puja máx. ${formatMoney(summary.maximum_bid)}`}
        tone={balance < 0 ? "bad" : ""}
      />
      {/* PUEDE GASTAR EN QUE (21/08/2026)
        *
        *   Enseñaba el presupuesto de ESPECULAR y ponia "0 €" la
        *   misma noche en que Pepe puso una puja de 2,08 M para
        *   mejorar el once. El numero de cabecera desmentia al
        *   bot.
        *
        *   Manda el de fichar, que es con el que se decide
        *   comprar. El de especular va en el subtitulo. */}
      <Kpi
        label="Puede gastar"
        value={formatMoney(
          fichajes.available
            ? fichajes.available_budget
            : exposure.available_budget
        )}
        sub={
          fichajes.available
            ? `fichar · especular ${formatMoney(
                exposure.available_budget
              )}`
            : exposure.mode
            ? String(exposure.mode).replaceAll("_", " ").toLowerCase()
            : "sin presupuesto"
        }
        tone={
          Number(
            (fichajes.available
              ? fichajes.available_budget
              : exposure.available_budget) || 0
          ) > 0
            ? "good"
            : "bad"
        }
      />
      <Kpi
        label="Reset del mercado"
        value={clock.available ? `${hoursReset.toFixed(1)}h` : "—"}
        sub={clock.available ? `${clock.next_reset_local} · se resuelven las pujas` : "sin deducir"}
        tone={clock.available && hoursReset < 3 ? "hot" : ""}
      />
      <Kpi
        label="Cierre de jornada"
        value={summary.hours_to_deadline != null ? `${Number(summary.hours_to_deadline).toFixed(1)}h` : "—"}
        sub={`jornada ${summary.target_matchday ?? "—"} · ${summary.phase || "—"}`}
        tone={Number(summary.hours_to_deadline || 999) < 6 ? "hot" : ""}
      />
      <Kpi
        label="XI"
        value={`${lineup.playable ?? 0}/11`}
        sub={`${lineup.formation || "—"} · riesgo ${String(summary.lineup_risk || "—").toLowerCase()}`}
        tone={Number(lineup.missing || 0) > 0 ? "bad" : ""}
      />
      <Kpi
        label="Pujas puestas"
        value={`${exposure.operation_count ?? 0}`}
        sub={
          Number(exposure.operation_count || 0) > 0
            ? `${formatMoney(exposure.committed_total)} comprometidos`
            : `${acquisition.actionable ?? acquisition.biddable ?? 0} por pujar de ${acquisition.market_size ?? 0}`
        }
        tone={Number(exposure.operation_count || 0) > 0 ? "good" : ""}
      />
    </div>
  );
}
