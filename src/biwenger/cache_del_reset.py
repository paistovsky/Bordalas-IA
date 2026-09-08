"""
Lo que solo cambia en el reset se pide una vez, no cuarenta y ocho.

EL PROBLEMA (07/09/2026)

    El mercado del Computer cambia UNA VEZ AL DIA, a las 07:00
    de Madrid. El ciclo, en cambio, volvia a pedirlo todo cada
    media hora:

        el catalogo entero        48 veces al dia
        la lista de managers      48 veces al dia
        la jornada                48 veces al dia
        los 7 perfiles rivales   336 veces al dia

    Y una plantilla rival solo cambia cuando ese manager ficha o
    vende. Cuantos lo hacen de verdad esta MEDIDO sobre el
    tablon del 04 al 07 de septiembre: 4, 5, 2 y 1 al dia.
    Media 3 de 7.

    Asi que de 336 peticiones diarias de perfiles, 333 preguntan
    por algo que no ha cambiado.

DOS RELOJES DISTINTOS, Y NO SE PUEDEN MEZCLAR

    1. LO QUE CAMBIA EN EL RESET -catalogo, jornada, lista de
       managers-. Vale hasta las 07:00 siguientes y punto.

    2. LO QUE CAMBIA CUANDO ALGUIEN SE MUEVE -las plantillas-.
       No tiene hora: tiene un aviso. El tablon dice quien se ha
       movido y cuesta UNA peticion, asi que se lee el indice
       antes de abrir el libro.

    Cachear lo segundo con el reloj de lo primero nos dejaria
    ciegos media tarde. Por eso son dos mecanismos y no uno.

EL RIESGO QUE SE ACEPTA, ESCRITO

    El catalogo trae el PRECIO -que solo cambia en el reset- y
    tambien el ESTADO: lesionado, duda, sancionado. Eso si puede
    cambiar a media tarde.

    Se acepta porque la titularidad y los partes de baja llegan
    por otra via -el ojeador y la prensa, que no pasan por
    aqui-, asi que un jugador que se lesiona a las 14:00 sigue
    saliendo bloqueado por el pronostico aunque el catalogo
    diga "ok".

    Si algun dia eso deja de ser cierto, la salida es sacar el
    catalogo de `CACHEABLES` y volver a pedirlo cada vuelta: son
    47 peticiones al dia y esta medido.

EL INTERRUPTOR

    `BORDALAS_SIN_CACHE=1` y todo se vuelve a pedir cada vuelta,
    como antes del 07/09.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.market_clock import FALLBACK_RESET_HOUR_UTC


# Donde vive. Es estado del ciclo, como el resto del almacen.
FICHERO = Path("data") / "autopilot" / "cache_biwenger.json"


DISABLE_ENV = "BORDALAS_SIN_CACHE"


# Lo que se guarda entre resets. Cada clave lleva por que se
# puede cachear, para que nadie añada una sin pensarlo.
CACHEABLES = {
    # Los precios solo se mueven en el reset. Ver el riesgo del
    # `status` en la cabecera.
    "catalogo": "precios: cambian en el reset",

    # Quien esta en la liga. No cambia en meses.
    "managers": "quien juega la liga",

    # La jornada en curso. Cambia una vez por semana.
    "jornada": "la jornada, semanal",
}


# ============================================================
# EL CATALOGO NO SE CACHEA EL DIA DE LA JORNADA (08/09/2026)
# ============================================================
#
#     LA PEGA QUE QUEDO ESCRITA AL MONTAR ESTO
#
#         El catalogo trae el PRECIO -que solo cambia en el
#         reset- y tambien el ESTADO: lesionado, dudoso,
#         sancionado. Lo segundo cambia a media tarde.
#
#         Un martes da igual: no se alinea a nadie. El dia de la
#         jornada no: alinear a un lesionado cuesta puntos, y
#         esta liga se decide por cuatro decimas por jornada.
#
#     LA REGLA, Y POR QUE ESTAS FASES
#
#         Se pide fresco mientras la alineacion TODAVIA SE PUEDE
#         ESCRIBIR y el cierre esta cerca:
#
#             HIGH_ATTENTION   T-12 h
#             FINALIZATION     T-2 h
#             HARD_SAFETY      pasado T-90 min
#
#         Y con el calendario roto, tambien: no saber en que
#         fase estamos tiene que costar peticiones, no puntos.
#
#     LO QUE SI SE CACHEA, Y POR QUE
#
#         NORMAL y PREPARATION: quedan mas de 12 h y la
#         alineacion se escribe despues, ya en fresco.
#
#         ROUND_LOCKED y ROUND_TRANSITION_LOCK: la jornada esta
#         en marcha y el once ya no se puede tocar. Un estado
#         viejo no puede estropear una alineacion que esta
#         cerrada.
#
#     EL COSTE, MEDIDO
#
#         Fresco solo en esas tres fases son ~12 h por jornada.
#         Con el cron de 48 vueltas eso son unas 24 peticiones
#         mas por jornada; nunca cachear costaria 47 AL DIA.
#
#         Si algun dia parece poco margen, meter PREPARATION en
#         el conjunto sube a ~48 h por jornada. Es una linea, y
#         el numero esta en el informe.
FASES_SIN_CACHE = frozenset({
    "HIGH_ATTENTION",
    "FINALIZATION",
    "HARD_SAFETY",

    # No saber falla del lado caro.
    "CALENDAR_UNKNOWN",
    "SEASON_COMPLETE_OR_UNKNOWN",
})


# Lo unico que depende de la fase. El resto -jornada, lista de
# managers- no lleva estado de jugador y se cachea siempre.
SENSIBLE_A_LA_FASE = "catalogo"


def fase_del_calendario(ahora=None) -> str:
    """
    En que fase temporal estamos, sin salir a la calle.

    Se lee del calendario dinamico, que ya vive en disco y lo
    usa el ciclo entero. `force=False`: si la copia esta fresca
    no se pide nada, y si no lo esta se habria refrescado igual
    unas lineas mas adelante.

    Nunca lanza. Si no se puede saber, devuelve
    `CALENDAR_UNKNOWN` — que esta en `FASES_SIN_CACHE`, o sea
    que no saber sale por el lado seguro.
    """

    try:
        from src.analysis.matchday_calendar_engine import (
            refresh_dynamic_calendar,
        )

        dinamico = refresh_dynamic_calendar(
            force=False, now=ahora
        )

        return str(
            (dinamico or {}).get("phase")
            or "CALENDAR_UNKNOWN"
        )

    except Exception:                               # noqa: BLE001
        return "CALENDAR_UNKNOWN"


def se_cachea_en_esta_fase(
    clave: str,
    fase: str | None = None,
) -> dict:
    """
    `{cachea, fase, reason}`. Forma fija, nunca lanza.

    `fase` se puede pasar -las guardias lo hacen- o se deduce.
    Ninguna funcion de aqui lee el reloj por su cuenta si le
    dan la hora.
    """

    try:
        if clave != SENSIBLE_A_LA_FASE:
            return {
                "cachea": True,
                "fase": fase,
                "reason": (
                    f"«{clave}» no lleva estado de jugador: la "
                    f"fase no le afecta."
                ),
            }

        if fase is None:
            fase = fase_del_calendario()

        if fase in FASES_SIN_CACHE:
            return {
                "cachea": False,
                "fase": fase,
                "reason": (
                    f"Fase «{fase}»: la alineacion aun se puede "
                    f"escribir y el cierre esta cerca. El "
                    f"catalogo se pide fresco para no alinear a "
                    f"un lesionado."
                ),
            }

        return {
            "cachea": True,
            "fase": fase,
            "reason": (
                f"Fase «{fase}»: queda margen antes del cierre, "
                f"el catalogo de este reset vale."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        # Ante la duda, fresco.
        return {
            "cachea": False,
            "fase": fase,
            "reason": (
                f"No se pudo mirar la fase "
                f"({type(error).__name__}): se pide fresco."
            ),
        }


def _sin_cache() -> bool:
    return str(
        os.environ.get(DISABLE_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def ultimo_reset(ahora: datetime | None = None) -> int:
    """
    El epoch del reset mas reciente.

    Se usa la hora de respaldo del reloj del mercado -importada,
    no copiada- para que no haya dos horas del reset en el
    proyecto. Si algun dia Biwenger la mueve, se mueve en un
    sitio.
    """

    try:
        ahora = ahora or datetime.now(timezone.utc)

        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)

        candidato = ahora.replace(
            hour=FALLBACK_RESET_HOUR_UTC,
            minute=0,
            second=0,
            microsecond=0,
        )

        if candidato > ahora:
            candidato = candidato - timedelta(days=1)

        return int(candidato.timestamp())

    except Exception:                               # noqa: BLE001
        return 0


def _cargar(path: Path | None = None) -> dict:
    try:
        return json.loads(
            (path or FICHERO).read_text(encoding="utf-8")
        )

    except Exception:                               # noqa: BLE001
        return {}


def _guardar(datos: dict, path: Path | None = None) -> None:
    try:
        destino = path or FICHERO

        destino.parent.mkdir(parents=True, exist_ok=True)

        destino.write_text(
            json.dumps(datos), encoding="utf-8"
        )

    except Exception:                               # noqa: BLE001
        pass


def leer(
    clave: str,
    path: Path | None = None,
    ahora: datetime | None = None,
    fase: str | None = None,
) -> dict:
    """
    `{fresco, valor, guardado_en, reason}`.

    Forma fija: las mismas claves haya cache o no. `fresco` es
    lo unico que hay que mirar; `valor` sin `fresco` no vale.
    """

    vacio = {
        "fresco": False,
        "valor": None,
        "guardado_en": None,
        "reason": None,
    }

    try:
        if _sin_cache():
            return {
                **vacio,
                "reason": (
                    f"{DISABLE_ENV} puesto: no se usa cache."
                ),
            }

        if clave not in CACHEABLES:
            return {
                **vacio,
                "reason": (
                    f"«{clave}» no esta en CACHEABLES: se pide."
                ),
            }

        # LA FASE MANDA SOBRE EL RESET (08/09/2026)
        #
        #     El catalogo se cachea desde el reset, salvo el dia
        #     de la jornada. Ver `FASES_SIN_CACHE`.
        por_la_fase = se_cachea_en_esta_fase(clave, fase)

        if not por_la_fase["cachea"]:
            return {**vacio, "reason": por_la_fase["reason"]}

        entrada = (_cargar(path) or {}).get(clave) or {}

        guardado = safe_int(entrada.get("guardado_en"))

        if not guardado or "valor" not in entrada:
            return {**vacio, "reason": "Sin cache guardada."}

        corte = ultimo_reset(ahora)

        if guardado < corte:
            return {
                **vacio,
                "guardado_en": guardado,
                "reason": (
                    "La cache es de antes del ultimo reset: se "
                    "vuelve a pedir."
                ),
            }

        return {
            "fresco": True,
            "valor": entrada["valor"],
            "guardado_en": guardado,
            "reason": None,
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": f"{type(error).__name__}: {error}",
        }


def escribir(
    clave: str,
    valor,
    path: Path | None = None,
    ahora: datetime | None = None,
) -> None:
    """Guarda, si la clave es cacheable. Nunca lanza."""

    try:
        if _sin_cache() or clave not in CACHEABLES:
            return

        datos = _cargar(path)

        datos[clave] = {
            "guardado_en": int(
                (
                    ahora or datetime.now(timezone.utc)
                ).timestamp()
            ),
            "valor": valor,
        }

        _guardar(datos, path)

    except Exception:                               # noqa: BLE001
        pass


# ============================================================
# EL OTRO RELOJ: QUIEN SE HA MOVIDO
# ============================================================


# Los tipos de evento del tablon que significan "esa plantilla
# ya no es la que era". `market` es compra al Computer,
# `transfer` es traspaso entre managers.
MOVIMIENTOS = frozenset({"transfer", "market"})


def _usuarios_del_evento(evento: dict) -> set:
    """
    Los ids de manager que aparecen en un evento del tablon.

    El contenido viene a veces como lista y a veces como
    diccionario, y el manager puede estar en `from` o en `to`.
    Se recogen los dos: en un traspaso cambian DOS plantillas, y
    refrescar solo una dejaria la otra vieja.
    """

    encontrados = set()

    contenido = evento.get("content")

    trozos = (
        contenido
        if isinstance(contenido, list)
        else [contenido]
    )

    for trozo in trozos:

        if not isinstance(trozo, dict):
            continue

        for lado in ("from", "to"):

            quien = trozo.get(lado)

            if isinstance(quien, dict) and quien.get("id"):
                encontrados.add(safe_int(quien.get("id")))

    return encontrados


def managers_que_se_han_movido(
    eventos: list | None,
    desde: int,
) -> set:
    """
    Quien ha fichado o vendido desde `desde` (epoch).

    Nunca lanza. Ante la duda devuelve mas gente, no menos: una
    plantilla refrescada de mas cuesta una peticion; una de
    menos es un dato viejo decidiendo.
    """

    movidos = set()

    try:
        for evento in (eventos or []):

            if not isinstance(evento, dict):
                continue

            if str(evento.get("type")) not in MOVIMIENTOS:
                continue

            if safe_int(evento.get("date")) < safe_int(desde):
                continue

            movidos |= _usuarios_del_evento(evento)

        return movidos

    except Exception:                               # noqa: BLE001
        # Sin poder decidir, que se refresquen todos.
        return set()


def perfiles_a_refrescar(
    users: list | None,
    eventos: list | None,
    cacheados: dict | None,
    desde: int,
) -> dict:
    """
    `{refrescar: [ids], reutilizar: {id: perfil}, reason}`.

    LA REGLA

        Se refresca a quien se ha movido desde la ultima vez, y
        a quien no tengamos guardado. Todo lo demas se reutiliza.

    LA SEGURIDAD

        Con el interruptor puesto, o si algo falla, se refrescan
        TODOS: el comportamiento de antes del 07/09. Una cache
        que se equivoca hacia el lado caro cuesta peticiones;
        hacia el lado barato, decisiones.

    Forma fija. Nunca lanza.
    """

    todos = []

    try:
        for user in (users or []):

            if isinstance(user, dict) and user.get("id"):
                todos.append(safe_int(user.get("id")))

    except Exception:                               # noqa: BLE001
        todos = []

    def _todos(motivo: str) -> dict:
        return {
            "refrescar": list(todos),
            "reutilizar": {},
            "reason": motivo,
        }

    try:
        if _sin_cache():
            return _todos(
                f"{DISABLE_ENV} puesto: se refrescan todos."
            )

        guardados = {
            safe_int(k): v
            for k, v in (cacheados or {}).items()
            if v
        }

        if not guardados:
            return _todos(
                "Sin perfiles guardados: primera vuelta."
            )

        movidos = managers_que_se_han_movido(eventos, desde)

        refrescar = [
            identificador
            for identificador in todos
            if identificador in movidos
            or identificador not in guardados
        ]

        reutilizar = {
            identificador: guardados[identificador]
            for identificador in todos
            if identificador not in refrescar
            and identificador in guardados
        }

        return {
            "refrescar": refrescar,
            "reutilizar": reutilizar,
            "reason": (
                f"{len(refrescar)} de {len(todos)} se han movido "
                f"o no estaban guardados; {len(reutilizar)} se "
                f"reutilizan."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return _todos(
            f"No se pudo decidir ({type(error).__name__}): se "
            f"refrescan todos."
        )
