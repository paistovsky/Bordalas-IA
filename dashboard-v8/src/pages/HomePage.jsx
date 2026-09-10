import PitchXI from "../components/PitchXI";
import PosiblesCambiosPanel from "../components/PosiblesCambiosPanel";
import StandingsIntelPanel from "../components/StandingsIntelPanel";
import TimelinePanel from "../components/TimelinePanel";
import { formatMoney } from "../lib/utils";

/* INICIO: LA TIRA Y CUATRO PANELES (10/09/2026)
 *
 * Arriba, la tira de estado -que vive en `KpiStrip`- con las dos
 * cuentas atras corriendo. Debajo, cuatro paneles y solo cuatro:
 *
 *   1. EL XI PARA LA JORNADA      quien juega
 *   2. CLASIFICACION E INTELIGENCIA  como vamos y quien aprieta
 *   3. CRONOLOGIA DE BORDALAS     que hizo y que hara
 *   4. POSIBLES CAMBIOS           quien esta fuera, y por que
 *
 * LO QUE SE FUE, Y NO SE BORRO
 *
 *   AhoraPanel, DineroPanel, VentanaPanel, CobrarPanel,
 *   ElOncePanel y los objetivos estaban aqui y ahora viven en
 *   Auditoria. Ni un panel se ha borrado: se han movido, y
 *   siguen leyendo exactamente los mismos datos.
 *
 *   El dinero ya no necesita panel propio en la portada porque
 *   la DEUDA MAXIMA subio a la tira, con su desglose debajo:
 *   saldo, comprometido y credito.
 *
 * LA REGLA QUE EVITA QUE ESTO SE VUELVA A LLENAR
 *
 *   Cualquier panel que se pida para VERIFICAR algo nace en
 *   Auditoria. A la portada solo sube lo que hace falta para
 *   decidir. Esta escrita en la doctrina.
 */

function squadValue(players = []) {
  return players.reduce(
    (total, player) => total + Number(player.price || 0),
    0
  );
}

export default function HomePage({ data }) {
  const lineup = data.lineup || {};
  const mandatory = lineup.mandatory_hierarchy || {};

  return (
    <>
      {/* 1. EL XI, y 2. cómo vamos, a su lado. */}
      <div className="grid g23">
        <section className="pan pan-pitch">
          <div className="pan-head">
            <div>
              <h2>XI PARA LA JORNADA</h2>
              <div className="sub">
                {lineup.formation || "—"} · VALOR{" "}
                {formatMoney(squadValue(lineup.players))} · LA BARRA ES
                LA PROBABILIDAD DE SER TITULAR
              </div>
            </div>
            <span
              className={
                Number(lineup.missing || 0) ? "pill crit" : "pill ok"
              }
            >
              {lineup.playable ?? 0}/11
            </span>
          </div>

          {/* UN DIOS QUE FALTA TIENE QUE EXPLICARSE.
              La regla es que juegan siempre; la unica excepcion
              es el 0 % motivado. Asi que cuando uno no esta, el
              motivo va aqui arriba y no en un log. */}
          {(mandatory.ruled_out || []).length > 0 && (
            <div className="godnote crit">
              FUERA DEL XI:{" "}
              {mandatory.ruled_out
                .map((god) => `${god.name} (${god.reason || "sin motivo"})`)
                .join(" · ")}
            </div>
          )}

          {/* Un Dios al 0 % que nadie explica. Juega igual —un
              dato suelto no es una baja— pero se canta, porque o
              FF sabe algo que no vemos o el dato está viejo. */}
          {(mandatory.unexplained || []).length > 0 && (
            <div className="godnote warn">
              0 % SIN MOTIVO, JUEGA IGUAL:{" "}
              {mandatory.unexplained.map((god) => god.name).join(" · ")}
            </div>
          )}

          <PitchXI
            lineup={lineup}
            offers={data.competitive?.offers || []}
          />
        </section>

        <div className="stack">
          {/* 2. ¿VAMOS GANANDO? */}
          <StandingsIntelPanel data={data} />

          {/* 3. ¿QUÉ HIZO Y QUÉ HARÁ? */}
          <TimelinePanel data={data} />
        </div>
      </div>

      {/* 4. QUIÉN ESTÁ FUERA DEL XI, Y POR QUÉ. */}
      <PosiblesCambiosPanel data={data} />
    </>
  );
}
