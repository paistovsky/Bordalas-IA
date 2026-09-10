import { formatMoney } from "../lib/utils";

/* ¿HAY ALGO QUE EXIJA QUE YO HAGA ALGO AHORA? (10/09/2026)
 *
 * La tira de arriba del todo, y la unica pregunta que no puede
 * necesitar scroll.
 *
 * DOS COSAS QUE LA HACEN UTIL Y NO DECORATIVA
 *
 *   1. Si no hay nada, LO DICE. Una tira que solo aparece
 *      cuando hay problemas es indistinguible de una tira
 *      rota: el dueno no sabe si esta en verde o si el panel
 *      ha dejado de pintarse.
 *
 *   2. Solo entra lo ACCIONABLE. "El mercado esta caro" no es
 *      una alarma; "hay 8,9 M que tapar y ninguna oferta de
 *      banquillo llega" si. Si no hay nada que el dueno pueda
 *      hacer, no va aqui: va a Auditoria.
 *
 * NO CALCULA NADA. Lee lo que ya viene publicado y lo ordena.
 */

function urgencias(data) {
  const avisos = [];

  const reloj = data.solvencyClock || {};
  const lineup = data.lineup || {};
  const renovacion = data.renovacion || {};
  const ventana = renovacion.ventana || {};
  const silencio = data.silencio || {};
  const consistency = data.consistency || {};

  // 1. DINERO QUE NO LLEGA. Lo primero siempre.
  if (reloj.available && Number(reloj.deficit || 0) > 0) {
    const plan = reloj.two_world_plan || {};
    const tapa = plan.if_won || {};

    avisos.push({
      tone: "crit",
      what: `FALTAN ${formatMoney(reloj.deficit)}`,
      why:
        reloj.state === "DEUDA_CONTINGENTE"
          ? `Si se gana la puja el saldo queda en ${formatMoney(
              reloj.effective_balance
            )}. ${
              tapa.covered === false
                ? "NO hay plan que lo tape sin tocar a un titular."
                : "Se tapa con ofertas de gente que no juega."
            }`
          : reloj.reason_text
    });
  }

  // 2. EL ONCE INCOMPLETO. Cuesta puntos hoy.
  if (Number(lineup.missing || 0) > 0) {
    avisos.push({
      tone: "crit",
      what: `EL XI ESTÁ A ${lineup.playable ?? 0}/11`,
      why: "Faltan jugadores por alinear."
    });
  }

  // 3. LA VENTANA QUE NO SE ABRE. Es la alarma que no se veia:
  //    "FUERA_DE_VENTANA" es la misma frase que sale el resto
  //    del dia.
  if (ventana.red) {
    avisos.push({
      tone: "crit",
      what: ventana.ever
        ? `${Math.round(ventana.hours_since)} H SIN ENTRAR EN LA VENTANA`
        : "LA VENTANA NO SE HA ABIERTO NUNCA",
      why: "Se abre una vez al día. Algo que la dispara no funciona."
    });
  }

  // 4. LISTADOS QUE SE MUEREN Y NO LOS SALVA LA VENTANA.
  const enRiesgo = renovacion.at_risk || [];

  if (enRiesgo.length) {
    avisos.push({
      tone: "warn",
      what: `${enRiesgo.length} LISTADO(S) CADUCAN ANTES DE LA VENTANA`,
      why: enRiesgo
        .slice(0, 4)
        .map((x) => `${x.name} (${Number(x.listing_hours_to_expiry).toFixed(1)} h)`)
        .join(" · ")
    });
  }

  // 5. LA PANTALLA NO SE CREE A SI MISMA.
  if (consistency.available && consistency.ok === false) {
    avisos.push({
      tone: "crit",
      what: "LA PANTALLA NO CUADRA CONSIGO MISMA",
      why: "No decidas mirando esto hasta arreglarlo."
    });
  }

  // 6. ZONA DE SILENCIO con trabajo pendiente. Informativo: no
  //    hay que hacer nada, pero explica por que Pepe esta
  //    quieto.
  const bloqueado = silencio.blocked || {};

  if (bloqueado.blocked && (bloqueado.actions || []).length) {
    avisos.push({
      tone: "warn",
      what: "ZONA DE SILENCIO",
      why: bloqueado.reason
    });
  }

  return avisos;
}

export default function AhoraPanel({ data }) {
  const avisos = urgencias(data);

  // "NO HAY NADA" Y "NO SE PUEDE SABER" NO SON LO MISMO
  //
  //   Si el reloj de solvencia no viene, esta tira diria
  //   "NADA QUE HACER AHORA" con el mismo aplomo que cuando de
  //   verdad no hay nada. Seria una mentira tranquilizadora, y
  //   es exactamente el fallo que esta tira existe para evitar.
  const reloj = data.solvencyClock || {};
  const lineup = data.lineup || {};

  const puedeSaber =
    reloj.available === true || lineup.players?.length > 0;

  if (!avisos.length && !puedeSaber) {
    return (
      <section className="pan ahora">
        <div className="empty">
          NO SE PUEDE SABER si hay algo urgente: falta el reloj de
          solvencia en esta vuelta. {reloj.reason || ""}
        </div>
      </section>
    );
  }

  if (!avisos.length) {
    return (
      <section className="pan ahora ahora-ok">
        <div className="ahora-line">
          <span className="pill ok">NADA QUE HACER AHORA</span>
          <span className="ahora-why">
            Sin déficit, el XI completo y la ventana al día.
          </span>
        </div>
      </section>
    );
  }

  return (
    <section className="pan ahora ahora-bad">
      {avisos.map((aviso, i) => (
        <div className="ahora-line" key={i}>
          <span className={`pill ${aviso.tone}`}>{aviso.what}</span>
          <span className="ahora-why">{aviso.why}</span>
        </div>
      ))}
    </section>
  );
}
