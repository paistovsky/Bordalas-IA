import { useEffect, useState } from "react";
import { formatMoney } from "../lib/utils";
import {
  cuenta,
  minutosDeLaFoto,
  segundosAlReset
} from "../lib/relojes";

/* LA TIRA DE ESTADO (10/09/2026)
 *
 * Seis cosas, y una corriendo en vivo.
 *
 * LO QUE SE FUE ARRIBA
 *
 *   "Foto" y "Proximo ciclo" estaban aqui y ahora van en la
 *   pastilla verde de la cabecera, juntas:
 *
 *       foto de hace 6 min · proximo ciclo en 25:31
 *
 *   "Foto" duplicaba esa pastilla, y ademas pintaba
 *   "hace 7.0107 min": `minutesOld` devuelve fraccion y aqui
 *   se imprimia cruda.
 *
 * "DEUDA MÁXIMA" SUSTITUYE A "PUEDE GASTAR"
 *
 *   Es lo que Pepe puede COMPROMETER: el total con el que se
 *   pueden hacer pujas.
 *
 *       deuda máxima = saldo + línea de crédito − pujas vivas
 *
 *   Y ese número YA descuenta lo comprometido. El 10/09 son
 *   3.608.383 y no 15.825.383, porque hay 12.217.000 puestos en
 *   Aubameyang.
 *
 *   Sin el desglose debajo, eso se lee como "se me ha hundido el
 *   saldo" cuando lo que pasa es que hay una puja puesta. Por
 *   eso van los tres números al lado: saldo · comprometido ·
 *   crédito.
 *
 * LAS DOS CUENTAS ATRÁS VAN EN VIVO
 *
 *   Y si el ciclo no llega, LO DICE. Un `schedule` de GitHub se
 *   retrasa cuando le apetece; quedarse en cero fingiendo
 *   normalidad es justo lo que tapó dos semanas de ventana
 *   perdida.
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
  const [ahora, setAhora] = useState(() => new Date());

  // El único sitio de la casa donde el reloj corre solo, y es a
  // propósito: una cuenta atrás congelada no es una cuenta
  // atrás.
  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const summary = data.summary || {};
  const lineup = data.lineup || {};
  const pujas = data.pujasDelDueno || {};
  const reloj = data.solvencyClock || {};
  const meta = data.meta || {};

  // ------------------------------------------------------
  // LA DEUDA MÁXIMA Y SU DESGLOSE
  // ------------------------------------------------------
  const comprometido = Number(
    reloj.committed_bids ?? pujas.committed ?? 0
  );

  const saldo = Number(reloj.balance ?? summary.balance ?? 0);

  const deudaMaxima = Number(summary.maximum_bid || 0);

  // EL CRÉDITO SE DEDUCE DE LOS OTROS TRES, no se lee de otro
  // sitio: así los cuatro números de la tira SIEMPRE cuadran
  // entre sí. Si se leyera aparte, un día no sumarían y el
  // desglose dejaría de explicar nada.
  //
  //     deuda máxima = saldo + crédito − comprometido
  const credito = deudaMaxima + comprometido - saldo;

  // ------------------------------------------------------
  // Y AHÍ ESTÁ EL PROBLEMA
  // ------------------------------------------------------
  //
  // Cuadran SIEMPRE. Incluso si `maximumBid` viniera mal: el
  // crédito absorbería el error entero y los cuatro números
  // seguirían sumando tan tranquilos.
  //
  // Una pantalla que no puede estar equivocada tampoco puede
  // avisar de que lo está.
  //
  // Por eso se contrasta contra la OTRA vía, la que no pasa por
  // `maximumBid`:
  //
  //     línea de crédito = valor de plantilla × 0,25
  //
  // que está medida al euro en 12 de 12 estados. Si las dos no
  // dan lo mismo, una de las dos miente y hay que verlo — no
  // elegir en silencio cuál creer.
  const medido = data.pujasDelDueno?.credito || {};

  const creditoMedido = Number(medido.headroom || 0);

  // Un euro de margen por el redondeo del 0,25 sobre la
  // plantilla. Ni uno más: la medición fue exacta.
  const descuadre =
    medido.available && comprometido
      ? Math.abs(credito - creditoMedido)
      : 0;

  const cuadra = descuadre <= 1;

  // ------------------------------------------------------
  // LOS DOS RELOJES
  // ------------------------------------------------------
  const alReset = segundosAlReset(ahora);

  // La edad de la foto, con su zona puesta (doctrina 35).
  // `minutesOld` la leia como hora LOCAL, asi que el cierre
  // de jornada se descontaba mal para quien no estuviera en
  // Madrid — dos horas de menos, sin avisar.
  const edad = minutosDeLaFoto(meta.generated_at);

  // El cierre de la jornada venía calculado en la foto; se le
  // descuenta lo que ha pasado desde entonces para que no se
  // quede parado.
  const horasCierre = Number(summary.hours_to_deadline);

  const segundosCierre = Number.isFinite(horasCierre)
    ? horasCierre * 3600 - (edad != null ? edad * 60 : 0)
    : null;

  const pendientes = (data.subasta?.bids_book || []).filter(
    (b) => b.outcome === "PENDING"
  ).length;

  return (
    <div className="strip">
      <Kpi
        label="Jornada"
        value={summary.target_matchday ?? "—"}
        sub={summary.phase || ""}
      />

      {/* DEUDA MÁXIMA: lo que se puede comprometer, ya neto.
          Y en ROJO si las dos vías del crédito no coinciden. */}
      <Kpi
        label={cuadra ? "Deuda máxima" : "Deuda máxima NO CUADRA"}
        value={formatMoney(deudaMaxima)}
        sub={
          !cuadra
            ? `crédito ${formatMoney(credito)} por resta, pero ` +
              `${formatMoney(creditoMedido)} por plantilla ` +
              `(${formatMoney(medido.roster_value)} × 0,25): ` +
              `se llevan ${formatMoney(descuadre)}`
            : comprometido
            ? `saldo ${formatMoney(saldo)} · comprometido ${formatMoney(
                comprometido
              )} · crédito ${formatMoney(credito)}`
            : `saldo ${formatMoney(saldo)} · crédito ${formatMoney(
                credito
              )} · sin pujas puestas`
        }
        tone={!cuadra ? "bad" : comprometido ? "warn" : ""}
      />

      {/* RESET — EN VIVO. */}
      <Kpi
        label="Reset"
        value={cuenta(alReset)}
        sub="07:00 de Madrid"
        tone={alReset != null && alReset < 900 ? "warn" : ""}
      />

      <Kpi
        label="Cierre de la jornada"
        value={
          segundosCierre != null && segundosCierre > 0
            ? cuenta(segundosCierre)
            : segundosCierre != null
            ? "EN JUEGO"
            : "—"
        }
        sub="cuando arranca, no el T−6h"
        tone={
          segundosCierre != null && segundosCierre < 6 * 3600
            ? "bad"
            : ""
        }
      />

      <Kpi
        label="XI"
        value={`${lineup.playable ?? 0}/11`}
        sub={lineup.formation || "—"}
        tone={Number(lineup.missing || 0) ? "bad" : ""}
      />

      <Kpi
        label="Pujas puestas"
        value={
          comprometido ? formatMoney(comprometido) : "ninguna"
        }
        sub={
          pendientes
            ? `${pendientes} sin resolver`
            : pujas.source
            ? `vía ${pujas.source}`
            : ""
        }
        tone={comprometido ? "warn" : ""}
      />
    </div>
  );
}
