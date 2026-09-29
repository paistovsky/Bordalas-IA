import { useEffect, useState } from "react";
import { ago, formatMoney, minutesOld } from "../lib/utils";
import {
  avisoDeDisparoFueraDeHora,
  cadenciaEnPalabras,
  cadenciaMinutos,
  madridNaiveAUTC,
  minutosDeLaFoto,
  mmss,
  proximoCiclo
} from "../lib/relojes";

/* DIAGNÓSTICO (30/09/2026)
 *
 * «Los avisos siguen saliendo.» El dueño no quiere avisos en el
 * panel. Ni franjas, ni notas ámbar, ni «Hay N avisos», ni «no
 * cuadra» en mitad de una tabla.
 *
 * LO QUE NO SE HA HECHO: borrarlos. Cada aviso protegía algo que
 * costó un disgusto -la caja de los rivales, el XI de Biwenger,
 * el sentido caducado 27 días, la racha de 250.000-. Así que se
 * han MUDADO aquí, a una sección plegada al final de AUDITORÍA,
 * cerrada por defecto. Mismas condiciones, mismas frases.
 *
 *   - De arriba del todo (antes en App.jsx): la edad de la foto,
 *     la racha, los sentidos, la caja de los rivales, el XI de
 *     Biwenger, el cuadre de la pantalla, la titularidad.
 *   - De INICIO: el Dios fuera del XI, el 0 % sin motivo, las
 *     acciones en espera y el tablón a medias.
 *   - De la tira: la deuda máxima que no cuadra.
 *   - De MERCADO, ESTRATEGIA, PLANTILLA y MARCADOR: los carteles
 *     de dato viejo, dato que falta o cuadro que no cuadra.
 *
 * En el resto del panel sólo queda UNA línea arriba: «Última
 * vuelta de Pepe: HH:MM», en rojo únicamente si Pepe lleva más de
 * tres horas sin vuelta.
 */

function Grupo({ titulo, children }) {
  const hijos = (Array.isArray(children) ? children : [children])
    .flat()
    .filter(Boolean);
  if (!hijos.length) return null;
  return (
    <div className="diag-grupo">
      <h3>{titulo}</h3>
      {hijos}
    </div>
  );
}

export default function Diagnostico({ data, error = "", children = null }) {
  // La pastilla corre: una cuenta atras congelada no es una
  // cuenta atras.
  const [ahora, setAhora] = useState(() => new Date());

  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const edad = minutesOld(data.meta?.generated_at);

  // La cadencia sale del cron de verdad, no de un numero escrito
  // a mano en Python.
  const cicloMin = cadenciaMinutos(ahora);

  const cadencia = cadenciaEnPalabras(ahora);

  const fueraDeHora = avisoDeDisparoFueraDeHora(
    ahora,
    madridNaiveAUTC(data.meta?.generated_at)
  );

  const minutosFoto = minutosDeLaFoto(data.meta?.generated_at);

  const ciclo = proximoCiclo(ahora, madridNaiveAUTC(data.meta?.generated_at));

  const rancio =
    edad != null && cicloMin != null && edad > cicloMin * 1.5;

  /* ---- La tira: la deuda máxima, por sus dos vías. ---- */
  const summary = data.summary || {};
  const pujas = data.pujasDelDueno || {};
  const reloj = data.solvencyClock || {};
  const comprometido = Number(reloj.committed_bids ?? pujas.committed ?? 0);
  const saldo = Number(reloj.balance ?? summary.balance ?? 0);
  const deudaMaxima = Number(summary.maximum_bid || 0);
  const credito = deudaMaxima + comprometido - saldo;
  const medido = pujas.credito || {};
  const creditoMedido = Number(medido.headroom || 0);
  const descuadreDeuda =
    medido.available && comprometido ? Math.abs(credito - creditoMedido) : 0;
  const cuadra = descuadreDeuda <= 1;

  /* ---- INICIO ---- */
  const mandatory = data.lineup?.mandatory_hierarchy || {};
  const backoff = data.backoff || {};
  const tablon = data.tablon;

  /* ---- MERCADO ---- */
  const clock = data.marketClock || {};
  const acquisition = data.acquisition || {};
  const exposure = data.exposure || {};
  const vivas = (acquisition.targets || []).filter(
    (t) => Number(t.live_bid || 0) > 0
  ).length;
  const descuadreMercado =
    !!acquisition.available &&
    exposure?.operation_count != null &&
    Number(exposure.operation_count) !== vivas;
  const cobertura = acquisition.starter_coverage || {};
  const recortados = Number(acquisition.hidden || 0);
  const sinPronostico =
    Number(cobertura.total || 0) > 0 &&
    Number(cobertura.with_forecast || 0) === 0;
  const venta = data.loNuestroALaVenta || {};
  const sinPublicar = venta.comprado_sin_publicar || {};

  /* ---- ESTRATEGIA ---- */
  const ciego = (data.losSentidos || {}).ciego || {};
  const rivales = data.losRivales || {};
  const cal = data.elCalendario || {};

  /* ---- PLANTILLA ---- */
  const cortas = ((data.rivalSquads || {}).managers || []).filter(
    (m) =>
      m.with_starter_data != null &&
      Number(m.with_starter_data) < Number(m.squad_size)
  );

  /* ---- MARCADOR ---- */
  const marcador = data.marcador || {};
  const resumen = marcador.resumen || {};

  return (
    <details className="pan diagnostico">
      <summary>
        <h2>DIAGNÓSTICO</h2>
        <span className="sub">
          lo técnico: edad del dato, cuadres, sentidos y avisos de cada
          página · pulsa para abrir
        </span>
      </summary>

      <div className="diag-cuerpo">
        {children}

        <div className="diag-grupo">
          <h3>La vuelta, los datos y la cabecera</h3>
            <div className="estado-pastillas">
          <span
            className={
              ciclo.lateMinutes
                ? "freshness stale"
                : rancio
                ? "freshness stale"
                : "freshness"
            }
          >
            ● foto de{" "}
            {minutosFoto != null
              ? `hace ${minutosFoto} min`
              : ago(data.meta.generated_at)}
            {" · "}
            {/* Y SI EL CICLO NO LLEGA, LO DICE. Quedarse en cero
                fingiendo normalidad es lo que tapo dos semanas
                de ventana perdida. */}
            {ciclo.lateMinutes
              ? `debería haber entrado hace ${mmss(
                  ciclo.lateMinutes * 60
                )}`
              : `próximo ciclo en ${mmss(ciclo.seconds)}`}
          </span>

          {/* LA RACHA DIARIA (13/09/2026)

              250.000 EUR por entrar cinco días seguidos y pulsar
              canjear. En 34 días medidos, Pollo17 se llevó
              750.000 y nosotros 250.000: medio millón por
              acordarse.

              Se LEE de `account.dailyStreak`, no se estima. Si
              no viene, "SIN MEDIR" — nunca un número inventado:
              un contador que finge saber es peor que no tenerlo,
              porque se confía en él y se pierden los 250.000.

              En ROJO al llegar a 5/5: hay 250.000 esperando a
              que alguien pulse canjear en la app. */}
          <span
            className={
              data.meta?.daily_streak == null
                ? "freshness stale"
                : Number(data.meta.daily_streak) >= 5
                ? "freshness cobrar"
                : "freshness"
            }
          >
            {data.meta?.daily_streak == null
              ? "● RACHA SIN MEDIR"
              : Number(data.meta.daily_streak) >= 5
              ? `● RACHA 5/5 · CANJEA 250.000`
              : `● RACHA ${data.meta.daily_streak}/5`}
          </span>
            </div>

        {/* UN SENTIDO CADUCADO SE GRITA (14/09/2026)

            El tablero de titulares se cayó el 17 de agosto y
            volvió el 14 de septiembre. Las dos veces SOLO. 27
            días con la vía de fichar cerrada por falta de un
            dato, y ni un aviso: su edad estaba calculada y a la
            vista desde el 13/09, dentro de un cuadro de ocho
            filas, y no la miró nadie.

            Va ARRIBA DEL TODO y en todas las páginas, no dentro
            del cuadro de los sentidos: un dato que hay que ir a
            buscar no es un aviso.

            Y dice QUÉ QUEDA BLOQUEADO, no sólo que el dato es
            viejo. «El tablero es de la jornada 2» es un dato;
            «no se puja para mejorar el once» es la razón por la
            que alguien se levanta a mirarlo. */}
        {data.alarmaDeLosSentidos?.hay && (
          <div className="alert crit">
            <b>
              {data.alarmaDeLosSentidos.cuantos === 1
                ? "UN SENTIDO DE PEPE ESTÁ CADUCADO."
                : `${data.alarmaDeLosSentidos.cuantos} SENTIDOS DE PEPE ESTÁN CADUCADOS.`}
            </b>
            {(data.alarmaDeLosSentidos.sentidos || []).map((s, i) => (
              <div key={i} style={{ marginTop: 4 }}>
                {s.texto}{" "}
                <span className="dim">
                  Queda bloqueado: {s.que_queda_bloqueado}
                </span>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="alert warn">
            La última actualización falló ({error}). Se muestra el último estado válido.
          </div>
        )}

        {rancio && !error && (
          <div className="alert warn">
            Estos datos son de hace {Math.round(edad)} minutos y el ciclo corre{" "}
            {cadencia}. Entre ciclo y ciclo lo que ves es una foto: puede
            haber pujas o movimientos que aún no aparecen aquí.
          </div>
        )}

        {/* UN DISPARO A UNA HORA QUE NO ES LA SUYA
            Aqui habia un aviso del cambio de hora, para acordarse
            de quitar en octubre una compensacion que los crones
            externos NO necesitan: la teoria que la justificaba se
            dedujo de un solo caso y era falsa.

            Esto vigila lo que si importa —que el ciclo entre
            cuando toca— y no diagnostica la causa. */}
        {fueraDeHora && (
          <div className="alert warn">
            <b>EL CICLO NO HA ENTRADO A SU HORA.</b>{" "}
            {fueraDeHora.texto}
            <div style={{ marginTop: 4 }} className="dim">
              Configurados:{" "}
              {fueraDeHora.configurados
                .map((d) => `${d.madrid} (${d.que})`)
                .join(" · ")}
            </div>
          </div>
        )}

        {/* COMPRADO PARA REVENDER Y FUERA DEL ESCAPARATE

            NARANJA, NO ROJO (13/09/2026). Esto cuesta un día de
            escaparate, que es poco. El rojo se reserva para lo
            que cuesta puntos o dinero HOY: deuda sin cubrir, XI
            a punto de cerrarse mal, oferta buena caducando.

            Si todo es rojo, el rojo no significa nada.

            Y SIN TITULAR REPETIDO: el motivo ya es una frase
            entera y empieza por el nombre. Ponerle encima
            "VIAJE COMPRADO Y SIN LISTAR" decia lo mismo dos
            veces, y con una palabra —"viaje"— que es jerga
            nuestra y que el dueño no ha usado nunca. */}
        {/* SOLO EN MERCADO (13/09/2026, noche).

            Esta tira de avisos sale en todas las páginas, así
            que el recado de un jugador concreto aparecía también
            en INICIO. INICIO es la portada: lo que se hace con
            un jugador se hace en MERCADO, y el aviso tiene que
            estar donde está la acción.

            Lo demás de esta tira sigue saliendo en todas: un
            ciclo parado o una caja que no cuadra afectan a toda
            la pantalla, no a un cuadro. */}
        {data.rendija?.sin_listar?.ok === false && (
            <div className="alert warn">
              {data.rendija.sin_listar.reason}
            </div>
          )}

        {/* LA CAJA DE LOS RIVALES NO CUADRA (10/09/2026)
            De la caja cuelgan CAJA, PATRIMONIO, TOPE, PUJA,
            MAX. VISTO y AMENAZA: media tabla de Clasificacion.

            No podemos ver el saldo de nadie mas -la liga los
            tiene ocultos- asi que la unica auditoria posible es
            el NUESTRO: si el metodo falla con el que si podemos
            comprobar, los otros seis tampoco valen.

            SOLO SALE SI ESTA ROJA. Cuando cuadra no aparece
            nada: una alarma que no salta no ocupa sitio. Por eso
            se compara contra `false` y no contra un valor falsy:
            un `null` es "no se ha podido comprobar", y eso no es
            una alarma, es la columna diciendo SIN DATO. */}
        {data.rivalIntel?.cash_check?.ok === false && (
          <div className="alert crit">
            <b>LA CAJA DE LOS RIVALES NO CUADRA.</b>{" "}
            {data.rivalIntel.cash_check.reason}
          </div>
        )}

        {/* EL 11/11 EN VERDE MENTIA (20/08/2026)
            Un XI recomendado que no es el que hay puesto en
            Biwenger es el fallo mas caro posible: se juega la
            jornada con otro equipo y la pantalla dice que todo
            va bien. Va arriba y en rojo. */}
        {data.lineup?.live?.known && data.lineup.live.matches === false && (
          <div className="alert crit">
            <b>EL XI DE BIWENGER NO ES ESTE.</b> {data.lineup.live.reason}
            {(data.lineup.live.missing_in_biwenger || []).length > 0 && (
              <div style={{ marginTop: 4 }}>
                Deberían entrar:{" "}
                <b>
                  {data.lineup.live.missing_in_biwenger
                    .map((jugador) => jugador.name || `#${jugador.id}`)
                    .join(", ")}
                </b>
                .
              </div>
            )}
            {/* UN CONSEJO IMPOSIBLE ES PEOR QUE NINGUNO
                (20/08/2026)

                Con la jornada ya cerrada, el aviso seguia
                diciendo "Pepe lo ajustará en el próximo ciclo" y
                "cámbialo a mano". Las dos cosas son falsas:
                `operations_locked` pone a cero la prioridad del
                cambio de XI, y Biwenger tampoco deja tocarlo.

                Un panel que pide algo que no se puede hacer
                gasta la confianza igual que uno que miente. */}
            <div style={{ marginTop: 4 }}>
              {data.summary?.operations_locked ? (
                <>
                  <b>La jornada ya está cerrada.</b> Ni Pepe ni tú podéis
                  cambiarlo: se juega con este once. Queda anotado para el
                  marcador.
                </>
              ) : (
                <>
                  Pepe lo ajustará en el próximo ciclo. Si queda poco para
                  el cierre, cámbialo a mano.
                </>
              )}
            </div>
          </div>
        )}

        {data.lineup?.live?.known === false && (
          <div className="alert warn">
            No se ha podido leer qué XI hay puesto en Biwenger, así que no
            se puede garantizar que sea este. No se da por bueno.
          </div>
        )}

        {data.consistency?.available && !data.consistency.ok && (
          <div className="alert crit">
            <b>ESTA PANTALLA NO CUADRA CON BIWENGER.</b>{" "}
            {data.consistency.summary}
            <ul className="consistency-list">
              {(data.consistency.checks || [])
                .filter((check) => !check.ok)
                .map((check) => (
                  <li key={check.key}>
                    {check.label}:{" "}
                    {check.source === "BIWENGER" ? "Biwenger dice " : ""}
                    <b>{check.expected_label ?? String(check.expected)}</b>
                    {check.source === "BIWENGER" ? ", aquí sale " : " · "}
                    <b>{check.found_label ?? String(check.found)}</b>.{" "}
                    {check.detail}
                  </li>
                ))}
            </ul>
          </div>
        )}

        {data.lineup?.starter_data_total > 0 &&
          !data.lineup?.starter_data_ok && (
          <div className="alert warn">
            Probabilidad de ser titular disponible solo para{" "}
            {data.lineup.starter_data_players} de{" "}
            {data.lineup.starter_data_total} jugadores del XI. Los huecos dicen
            «sin dato» en vez de un 0 % que no significaría nada.

            {/* El POR QUE, no solo el cuantos. "La fuente externa
                no ha respondido" no dice si es que la pagina dio
                un 403, si la cache estaba vacia o si el tablero
                se cayo. Sin eso no se puede arreglar. */}
            <div style={{ marginTop: 6 }}>
              <b>Motivo:</b>{" "}
              {data.lineup.starter_source_error ? (
                <code>{data.lineup.starter_source_error}</code>
              ) : data.lineup.starter_board_players === 0 ? (
                "el tablero multifuente ha salido vacío (0 jugadores). " +
                "Suele significar que no se ha podido leer Jornada Perfecta " +
                "desde donde se generó este dashboard."
              ) : (
                "sin error registrado; el tablero tiene " +
                `${data.lineup.starter_board_players ?? "?"} jugadores.`
              )}
            </div>

            <div className="dim" style={{ marginTop: 4 }}>
              tablero {data.lineup.starter_board_version || "?"} ·{" "}
              caché {data.lineup.starter_cache_status || "?"} ·{" "}
              jornada {data.lineup.starter_board_matchday ?? "?"} ·{" "}
              generado {data.lineup.starter_board_updated_at || "?"}
            </div>

            <div style={{ marginTop: 6 }}>
              El XI que ves arriba está elegido <b>sin</b> ese dato: es el
              mejor por valor y puntos, no por quién va a jugar.
            </div>
          </div>
        )}

        </div>

        <Grupo titulo="Tira de arriba">
          {!cuadra && (
            <div className="alert crit">
              <b>Deuda máxima NO CUADRA.</b> crédito {formatMoney(credito)} por
              resta, pero {formatMoney(creditoMedido)} por plantilla (
              {formatMoney(medido.roster_value)} × 0,25): se llevan{" "}
              {formatMoney(descuadreDeuda)}.
            </div>
          )}
        </Grupo>

        <Grupo titulo="Inicio">
          {(mandatory.ruled_out || []).length > 0 && (
            <div className="godnote crit">
              FUERA DEL XI:{" "}
              {mandatory.ruled_out
                .map((god) => `${god.name} (${god.reason || "sin motivo"})`)
                .join(" · ")}
            </div>
          )}
          {(mandatory.unexplained || []).length > 0 && (
            <div className="godnote warn">
              0 % SIN MOTIVO, JUEGA IGUAL:{" "}
              {mandatory.unexplained.map((god) => god.name).join(" · ")}
            </div>
          )}
          {(backoff.blocked || []).map((item, index) => (
            <div className="alert warn" key={`b${index}`}>
              <b>{String(item.action || "").replaceAll("_", " ")}</b> apartada:{" "}
              {item.consecutive_failures === 1
                ? "ha fallado 1 vez"
                : `ha fallado ${item.consecutive_failures} veces seguidas`}
              {item.last_http_status ? ` (HTTP ${item.last_http_status})` : ""}. Se
              reintenta en{" "}
              {Math.max(Math.floor(Number(item.seconds_remaining || 0) / 60), 1)} min.
            </div>
          ))}
          {tablon && tablon.error && (
            <div className="alert warn">
              No se pudo leer todo el tablón: {tablon.error}
            </div>
          )}
        </Grupo>

        <Grupo titulo="Mercado">
          {clock.listings_stale && (
            <div className="alert warn">
              El snapshot es anterior al último reset: puede traer jugadores que ya
              no existen. No se puja sobre datos caducados.
            </div>
          )}
          {recortados > 0 && (
            <div className="alert warn">
              La tabla de objetivos enseña {acquisition.shown} de{" "}
              {acquisition.valued} jugadores valorados.{" "}
              <b>{recortados} se quedan fuera</b>: el tope viene del motor.
            </div>
          )}
          {sinPronostico && (
            <div className="alert warn">
              Ningún candidato del mercado tiene pronóstico de titularidad, así que
              la regla del once bloquea las {cobertura.blocked_by_starter_rule ?? 0}{" "}
              mejoras que había. Revisa el refresco de FutbolFantasy.
            </div>
          )}
          {descuadreMercado && (
            <div className="alert warn">
              La caja dice {exposure.operation_count} puja(s) viva(s) y la tabla
              de objetivos encuentra {vivas}. No se decide nada con esa tabla
              hasta que cuadren.
            </div>
          )}
          {sinPublicar.hay && (
            <div className="aviso-ambar">
              <b>Comprado para revender y todavía sin poner a la venta:</b>{" "}
              {(sinPublicar.players || []).join(", ")}. Mientras no esté
              publicado, el Computer no le hace ninguna oferta.
            </div>
          )}
        </Grupo>

        <Grupo titulo="Estrategia">
          {ciego.hay && (
            <div className="aviso-ambar">
              <b>
                Hoy Pepe está medio ciego: {ciego.sin_pronostico} de{" "}
                {ciego.objetivos} objetivos salen sin pronóstico de
                titularidad.
              </b>{" "}
              {ciego.reason}{" "}
              <b>
                La vía de fichar está cerrada por falta de un dato, no
                por criterio.
              </b>
            </div>
          )}
          {rivales.sin_plantilla && rivales.sin_plantilla.length > 0 && (
            <div className="aviso-ambar">
              <b>{rivales.sin_plantilla.length} mánager(s) sin plantilla cruzada:</b>{" "}
              {rivales.sin_plantilla.join(", ")}. Sus fichas salen sin dato.
            </div>
          )}
          {cal.sin_casar && cal.sin_casar.length > 0 && (
            <div className="aviso-ambar">
              <b>
                {cal.sin_casar.length} ficha(s) del calendario no casan con la
                clasificación:
              </b>{" "}
              {cal.sin_casar.join(", ")}. Sus partidos salen igual, pero con el
              puesto del rival sin dato.
            </div>
          )}
        </Grupo>

        <Grupo titulo="Plantilla">
          {cortas.map((m) => (
            <div className="alert warn" key={m.user_id}>
              {m.name}: pronóstico de titularidad para {m.with_starter_data} de{" "}
              {m.squad_size} jugadores. Los huecos dicen «sin dato» en vez de un
              0 % que no significaría nada.
            </div>
          ))}
        </Grupo>

        <Grupo titulo="Marcador">
          {resumen.cuadra_todo === false && (
            <div className="alert crit">
              <b>LOS NÚMEROS NO CUADRAN CON BIWENGER.</b> El once que hemos
              reconstruido no suma lo mismo que los puntos que Biwenger le dio a
              Pepe en la clasificación. Hasta que coincidan, la nota del once no
              vale.
            </div>
          )}
          {marcador.el_once_anotado?.available &&
            marcador.el_once_anotado.irrecuperables > 0 && (
              <div className="alert warn">
                <b>
                  {marcador.el_once_anotado.irrecuperables} jornada(s) sin once
                  anotado, irrecuperables.
                </b>{" "}
                {marcador.el_once_anotado.desde
                  ? `La medición empieza en la jornada ${marcador.el_once_anotado.desde}.`
                  : "Todavía no hay ninguna anotada: la medición no ha empezado."}{" "}
                <span className="dim">
                  No se reconstruyen: un once a ojo daría una nota inventada, y
                  esa se usaría para decidir.
                </span>
              </div>
            )}
        </Grupo>
      </div>
    </details>
  );
}
