import AhoraPanel from "../components/AhoraPanel";
import CobrarPanel from "../components/CobrarPanel";
import DineroPanel from "../components/DineroPanel";
import ElOncePanel from "../components/ElOncePanel";
import PitchXI from "../components/PitchXI";
import StandingsIntelPanel from "../components/StandingsIntelPanel";
import TimelinePanel from "../components/TimelinePanel";
import VentanaPanel from "../components/VentanaPanel";
import { formatMoney } from "../lib/utils";

/* LA PORTADA CONTESTA OCHO PREGUNTAS (10/09/2026)
 *
 * Y solo ocho. El orden es el de urgencia, no el de cuanto
 * costo construir cada panel:
 *
 *   1. ¿Algo en ROJO que exija que yo haga algo AHORA?  AhoraPanel
 *   2. ¿Vamos ganando?                       Standings + El Once
 *   3. ¿Cuánto dinero hay y cuánto debo?             DineroPanel
 *   4. ¿Qué hizo y qué hará Pepe?                  TimelinePanel
 *   5. ¿Se abrió la ventana? ¿qué pujó y renovó?  VentanaPanel
 *   6. ¿Qué puedo cobrar y quién es titular?       CobrarPanel
 *   7. ¿Cómo está el once?                             PitchXI
 *   8. ¿A por quién va Pepe?                        (objetivos)
 *
 * LO QUE SE FUE, Y NO SE BORRO
 *
 *   LA CARRERA y PLANTILLA POR POSICION estaban aqui y ahora
 *   viven en Auditoria. Las dos contestan POR QUE -como va la
 *   temporada, como esta repartida la plantilla- y ninguna
 *   pide una decision hoy. Nada se ha perdido: se ha movido.
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

function Objetivos({ data }) {
  const board = data.acquisition || {};

  const filas = (board.targets || [])
    .filter((t) => Number(t.bid || 0) > 0)
    .slice(0, 5);

  if (!filas.length) {
    return (
      <section className="pan">
        <h2>A POR QUIÉN VA PEPE</h2>
        <div className="sub">
          Ningún objetivo con puja propuesta ahora mismo.
        </div>
      </section>
    );
  }

  return (
    <section className="pan">
      <div className="pan-head">
        <div>
          <h2>A POR QUIÉN VA PEPE</h2>
          <div className="sub">
            lo que pujaría, y por qué ese importe
          </div>
        </div>
      </div>
      <table className="tbl">
        <tbody>
          {filas.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td className="num">{formatMoney(t.bid)}</td>
              <td className="num sub">
                vale {formatMoney(t.market_price)}
              </td>
              <td className="sub">{t.decision}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function HomePage({ data }) {
  const lineup = data.lineup || {};
  const mandatory = lineup.mandatory_hierarchy || {};

  return (
    <>
      {/* 1. ¿HAY ALGO EN ROJO? Arriba del todo y sin scroll. */}
      <AhoraPanel data={data} />

      {/* 3. EL DINERO y 5. LA VENTANA, uno al lado del otro:
             son las dos preguntas de las 07:15. */}
      <div className="grid g2">
        <DineroPanel data={data} />
        <VentanaPanel data={data} />
      </div>

      {/* 7. EL ONCE, y 2. cómo vamos, a su lado. */}
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
          {/* 2. ¿VAMOS GANANDO? La clasificación primero. */}
          <StandingsIntelPanel data={data} />

          {/* 4. ¿QUÉ HIZO Y QUÉ HARÁ? */}
          <TimelinePanel data={data} />
        </div>
      </div>

      {/* 6. QUÉ PUEDO COBRAR, con la columna de titular. */}
      <CobrarPanel data={data} />

      {/* 2-bis. LOS PUNTOS QUE DEJAMOS EN EL BANQUILLO.
          "Si esa cifra crece, es la alarma más importante del
          tablero." (dueño, 17/09) */}
      <ElOncePanel data={data} />

      {/* 8. A POR QUIÉN VA PEPE. */}
      <Objetivos data={data} />
    </>
  );
}
