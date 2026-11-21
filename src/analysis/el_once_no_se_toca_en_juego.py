"""
EL ONCE NO SE TOCA EN JUEGO (21/11/2026)

LO QUE PASO (laboratorio del sab 21/11)

    La vuelta de las 07:15 del sabado 21/11 (#3098), con la J13 en juego
    (vie 20/11 21:00 - lun 23/11 21:00), hizo SAVE_LINEUP «para la
    Jornada 14»: el Lineup Monitor vio a Remiro (recien ganado) mejor
    que Gulacsi y guardo el once. Biwenger lo aplico a la J13, la que se
    estaba jugando: Remiro entro por Gulacsi. Esta vez no costo puntos
    (ninguno de los dos habia jugado), pero la regla de la casa es «el
    once no se cambia empezada la ronda».

    Por que paso: el calendario (`calendar_state`) desbloquea el trabajo
    de la J+1 dos horas despues del primer partido, y desde ahi la fase
    es la de la J14 (NORMAL, nada bloqueado). Para el mercado eso esta
    bien; para el once no, porque el once que se guarda a mitad de ronda
    vale para los partidos que quedan de ESA ronda. El orquestador solo
    miraba `operations_locked` y el ejecutor, que haya 11 alineables.
    La rotacion, la mejora y el parte ya miraban `jornada_en_curso`; el
    monitor viejo no.

QUE HACE, ENCENDIDO

    1. EL PLAN (`decision_orchestrator`, CAMBIO RELEVANTE DEL XI): con
       una ronda en juego no se propone SAVE_LINEUP; la vuelta se la
       queda la siguiente accion.
    2. EL EJECUTOR (`autopilot_executor`, GUARDAR XI): defensa en
       profundidad. Si aun asi llega un SAVE_LINEUP con la ronda en
       juego, no se escribe: status ROUND_IN_PROGRESS, sin escritura
       (`write_performed: False`, nadie pierde su turno) y sin castigo.

    «En juego» es lo de siempre (`la_proxima_jornada.jornada_en_curso`):
    del primer partido de una ronda a 3 h despues del ultimo, rondas «a
    lo Biwenger» (los adelantados y aplazados son rondas aparte).
    Terminada la J13 (lun 23/11 ~24:00), el monitor guarda el once de la
    J14 como siempre.

QUE NO HACE

    Si el calendario no se puede leer o no tiene rondas, NO bloquea: el
    monitor sigue como antes (un once viejo antes de una jornada cuesta
    mas que el raro cambio a mitad de ronda). Es lo contrario de
    `jornada_en_curso`, que sin calendario dice «en curso» para no
    vender. No toca la rotacion, la mejora ni el parte (ya lo miraban),
    ni el mercado: solo el once del monitor viejo.

    Nace APAGADO: `ENV`.
"""

import os
from datetime import datetime, timezone


ENV = "BORDALAS_EL_ONCE_NO_SE_TOCA_EN_JUEGO"
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})   # = el_paso_0.ENCENDIDO


def activo() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in ENCENDIDO
    except Exception:                               # noqa: BLE001
        return False


def en_juego(ahora=None, calendario=None):
    """
    La ronda en juego ahora, como «J13 (20/11 21:00 - 23/11 21:00)», o
    None si no hay ninguna o no se sabe (calendario ilegible o sin
    rondas). No lee el interruptor. Nunca lanza.
    """

    try:
        from src.analysis.la_proxima_jornada import MARGEN_FINAL, las_rondas, _ahora

        ahora = _ahora(datetime.now(timezone.utc) if ahora is None else ahora)
        for r in las_rondas(calendario):
            if r["inicio"] <= ahora <= r["fin"] + MARGEN_FINAL:
                return (f"J{r['jornada']} ({r['inicio']:%d/%m %H:%M} - "
                        f"{r['fin']:%d/%m %H:%M})")
        return None
    except Exception:                               # noqa: BLE001
        return None


def por_que_no_se_guarda(ahora=None, calendario=None):
    """
    None si el once se puede guardar. Si no (interruptor encendido y una
    ronda en juego), el motivo. Nunca lanza.
    """

    try:
        if not activo():
            return None
        ronda = en_juego(ahora, calendario)
        if not ronda:
            return None
        return (f"EL_ONCE_NO_SE_TOCA_EN_JUEGO: la {ronda} se esta jugando; "
                "el once guardado ahora valdria para los partidos que quedan "
                "de esa ronda. Se guarda al terminar.")
    except Exception:                               # noqa: BLE001
        return None
