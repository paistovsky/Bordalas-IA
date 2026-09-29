import PitchXI from "../components/PitchXI";
import PujasVivasPanel from "../components/PujasVivasPanel";
import TablonPanel from "../components/TablonPanel";
import StandingsIntelPanel from "../components/StandingsIntelPanel";
import TimelinePanel from "../components/TimelinePanel";
import { formatMoney } from "../lib/utils";

/* INICIO: LA TIRA Y CUATRO PANELES (10/09/2026)
 *
 * Arriba, la tira de estado -que vive en `KpiStrip`- con las dos
 * cuentas atras corriendo. Debajo, cinco paneles:
 *
 *   1. EL XI PARA LA JORNADA      quien juega
 *   2. CLASIFICACION E INTELIGENCIA  como vamos y quien aprieta
 *   3. PUJAS EN VIVO              que esta en juego AHORA
 *   4. CRONOLOGIA DE BORDALAS     que hizo y que hara
 *
 * EL TABLON ARRIBA, POSIBLES CAMBIOS FUERA (29/09/2026)
 *
 *   Encargo del dueño: arriba del todo, EL TABLON DE HOY -lo que
 *   ha pasado en la liga en las ultimas 24 horas, en frases-, y
 *   fuera el panel de POSIBLES CAMBIOS. El componente no se borra.
 *
 *   Las pujas en vivo van ENCIMA de la cronologia: lo primero
 *   que se lee tiene que ser lo que esta pasando ahora, no lo
 *   que va a pasar.
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
      {/* 0. QUÉ HA PASADO HOY EN LA LIGA. Si la telemetría no
          publica `tablon`, no sale nada. */}
      <TablonPanel data={data} />

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

          {/* El Dios fuera del XI y el 0 % sin motivo, mudados a DIAGNÓSTICO (AUDITORÍA), 30/09/2026. */}

          <PitchXI
            lineup={lineup}
            offers={data.competitive?.offers || []}
          />
        </section>

        <div className="stack">
          {/* 2. ¿VAMOS GANANDO? */}
          <StandingsIntelPanel data={data} />

          {/* 3. ¿QUÉ ESTÁ EN JUEGO AHORA MISMO?

              Va ENCIMA de la cronología a propósito: lo primero
              que se lee tiene que ser lo que está pasando, no lo
              que va a pasar. Las pujas vivas salían como un paso
              dentro de la cronología, mezcladas con lo de
              mañana. */}
          <PujasVivasPanel data={data} />

          {/* 4. ¿QUÉ HIZO Y QUÉ HARÁ? */}
          <TimelinePanel data={data} />
        </div>
      </div>

    </>
  );
}
