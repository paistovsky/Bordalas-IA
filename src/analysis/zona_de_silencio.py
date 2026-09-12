"""
La zona de silencio: entre las 05:00 y las 07:00 de Madrid, Pepe
lee y no escribe.

POR QUE EXISTE

    El reset del mercado pasa dentro de esa franja. Escribir
    mientras el Computer esta rehaciendo precios, ofertas y
    subastas es escribir contra un tablero que se esta moviendo:
    una renovacion puede morir sin nacer, una puja puede caer en
    el lado equivocado del corte.

    Biwenger dice que el reset se efectua "entre las 5:00 y las
    7:00 (hora local)". Medido (ver abajo) en esta liga pasa a
    las 07:00 clavadas, pero la franja de silencio se toma
    entera: la letra pequena es de Biwenger y puede cambiar sin
    avisarnos.

LO QUE NO ARREGLA UN CRON

    Los `schedule` de GitHub Actions NO son puntuales. Se
    retrasan minutos u horas cuando hay carga, y a veces se
    saltan. Una vuelta programada a las 02:07 UTC puede acabar
    ejecutandose dentro de la ventana.

    Por eso la barandilla va aqui, en el codigo, y no en el
    reloj: es la unica capa que no depende de que un reloj ajeno
    se porte bien.

LA EXCEPCION, Y POR QUE NO ES UNA TRAMPA

    El trabajo de la ventana -pujar y renovar a las siete menos
    cinco- CAE dentro de la franja a proposito. Si el silencio
    lo tapase tambien, no habria subasta nunca.

    La diferencia no es la hora: es QUIEN dispara.

        · Una vuelta `schedule` esta dentro de la franja SOLO
          por accidente -llego tarde-, y esa no escribe.

        · Una vuelta disparada a proposito -`workflow_dispatch`,
          `repository_dispatch`, o a mano- esta ahi porque
          alguien la puso ahi. Esa si escribe.

    Y si no se sabe quien dispara, se calla. El error caro es
    escribir sin querer.

LA HORA SE CALCULA EN MADRID, CON SU VERANO

    Ni en UTC ni con la hora del contenedor. Se reutiliza
    `market_clock.madrid_offset_hours`, que existe desde el
    16/08/2026 justo por este error: el mismo codigo imprimia
    las 05:00 en el PC y las 07:00 en GitHub Actions.

    Un dato, un nombre: no se copia la regla del horario de
    verano, se importa.

LO MEDIDO (10/09/2026)

    Sobre las 85 fotos de produccion del 11 al 17/08, con los
    sellos de tiempo del propio Biwenger:

        · 57 de 65 ofertas del Computer caducan a las 07:00
          clavadas (hora de Madrid).

        · Las 54 ofertas entrantes NACEN entre las 07:03:27 y
          las 07:09:25. Mediana 07:04. Siete dias seguidos, de
          martes a lunes: no varia con el dia de la semana.

    Asi que el reset se ejecuta a las 07:00 y la tanda nueva
    aparece de tres a nueve minutos despues.

Y SIRVE PARA MEDIR

    Las vueltas que caen dentro de la franja son las que mejor
    pueden ver a que hora pasa el reset DE VERDAD. De cada una
    se guarda si los precios ya habian cambiado. En una semana
    hay hora exacta sin gastar una peticion de mas.

ESTE MODULO NO LEE EL MUNDO

    Ni disco, ni red, ni reloj: el momento y el disparo se le
    pasan. Forma fija. Nunca lanza.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


# ============================================================
# LA FRANJA
# ============================================================
#
#     La de Biwenger es "entre las 5:00 y las 7:00 AM (hora
#     local)". La nuestra empieza QUINCE MINUTOS ANTES, a las
#     04:45, y no es un capricho:
#
#         El 10/09/2026 se amplio la ventana de la subasta a 135
#         minutos -04:45 a 07:00- para que el disparo externo
#         entrara. Con el silencio empezando a las 05:00 quedaban
#         quince minutos, 04:45-05:00, en los que la ventana
#         estaba ABIERTA y el silencio todavia no vigilaba.
#
#         Medido antes de tocarlo: una vuelta `schedule` de
#         GitHub que llegara tarde y cayera a las 04:47 salia
#         "ventana ABIERTA" + "deja escribir", y habria pujado y
#         renovado de verdad sin que nadie la hubiera puesto ahi.
#
#         Los dos numeros van atados. Si alguien vuelve a mover
#         la ventana, esto se mueve con ella.
#
#     En minutos desde medianoche, porque 04:45 no es una hora
#     redonda y comparar solo horas se comeria los 45 minutos.
SILENCIO_DESDE = 4 * 60 + 45

SILENCIO_HASTA = 7 * 60


# Lo medido el 10/09/2026 sobre 7 dias seguidos.
RESET_MEDIDO = "07:00"

TANDA_NUEVA_DESDE = "07:03"

TANDA_NUEVA_HASTA = "07:09"

DIAS_MEDIDOS = 7


# QUIEN DISPARA — RETIRADO EL 12/09/2026 COMO CRITERIO
#
#     Esta lista decidia si una vuelta podia escribir dentro de
#     la ventana del reset: `schedule` era el cron de GitHub, que
#     llega tarde cuando le apetece, y los demas se daban por
#     deliberados.
#
#     DEJO DE FUNCIONAR EL MISMO DIA QUE SE RETIRO EL SCHEDULE.
#     Sin el, TODAS las vueltas entran como `workflow_dispatch`
#     —el latido de cron-job.org incluido— asi que todas caian en
#     esta lista y todas eran "deliberadas". El criterio no es
#     que fuera mas permisivo: es que dejo de distinguir nada.
#
#     Comprobado ese dia:
#
#         05:30 Madrid, dentro de la ventana del reset
#           schedule           escribe False
#           workflow_dispatch  escribe True   <- ahora, todas
#
#     Un latido descolocado a las 05:30 habria escrito con el
#     mercado sin resetear, que es exactamente lo que costo la
#     primera ventana en septiembre.
#
#     LA LISTA SE QUEDA ESCRITA y ya no decide. El nombre del
#     disparo se sigue publicando como `trigger`, porque para
#     mirar un incidente vale; para decidir, no.
DISPAROS_DELIBERADOS_RETIRADOS = frozenset(
    {
        "workflow_dispatch",
        "repository_dispatch",
        "manual",
        "ventana",
    }
)

DISPARO_DEL_CRON = "schedule"


# LO QUE DECIDE AHORA: LA HORA, CONTRA LA DECLARACION
#
#     Un disparo cuenta como DELIBERADO solo si cae en una de las
#     horas declaradas para la ventana —04:45, 04:50, 07:15—
#     dentro del margen de gracia. Cualquier otro es un disparo
#     DESCOLOCADO y no escribe aqui dentro, VENGA POR DONDE
#     VENGA.
#
#     Eso se puede saber sin depender de quien llamo, que es
#     justo lo que se perdio al quitar el `schedule`.
#
#     La declaracion vive en `config/disparos.json` y es la
#     autoridad. Ver `src/analysis/los_disparos.py`.
CLASES_DELIBERADAS = frozenset({"ventana", "tras_el_reset"})


def _es_deliberado(minutos_de_madrid: int) -> dict:
    """
    ¿Tocaba un disparo de la ventana a esta hora? Forma fija.

    SI NO SE SABE, NO ES DELIBERADO. Si la declaracion no se
    pudiera leer, esto devuelve False y la vuelta no escribe
    dentro de la ventana: el lado seguro de no saber la hora a la
    que tocaba entrar es no tocar el mercado mientras se resetea.
    """

    try:
        from src.analysis.los_disparos import que_disparo_toca

        toca = que_disparo_toca(minutos_de_madrid)

        if not toca.get("available"):
            return {
                "deliberado": False,
                "que": None,
                "reason": toca.get("reason"),
            }

        return {
            "deliberado": bool(toca.get("hay"))
            and toca.get("que") in CLASES_DELIBERADAS,
            "que": toca.get("que") if toca.get("hay") else None,
            "reason": toca.get("reason"),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "deliberado": False,
            "que": None,
            "reason": (
                f"No se pudo mirar la declaracion de disparos: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _hora_de_madrid(momento_utc: datetime) -> datetime:
    """
    El mismo desfase que usa el reloj del mercado. Importado, no
    copiado.
    """

    from src.analysis.market_clock import madrid_offset_hours

    if momento_utc.tzinfo is None:
        momento_utc = momento_utc.replace(tzinfo=timezone.utc)

    momento_utc = momento_utc.astimezone(timezone.utc)

    # CON zona horaria: `madrid_offset_hours` compara contra los
    # domingos de cambio, que son aware. Pasarle un naive lanza
    # `TypeError`, y esta funcion acabaria devolviendo silencio
    # siempre -que es el lado seguro, pero tambien seria una
    # averia muda-. Hay guardia.
    return momento_utc + timedelta(
        hours=madrid_offset_hours(momento_utc)
    )


def en_la_franja(momento_utc: datetime) -> bool:
    """
    ¿Estamos entre las 05:00 y las 07:00 de Madrid?

    El limite de arriba NO se incluye: a las 07:00:00 el reset ya
    ha pasado.
    """

    try:
        madrid = _hora_de_madrid(momento_utc)

        minutos = madrid.hour * 60 + madrid.minute

        return SILENCIO_DESDE <= minutos < SILENCIO_HASTA

    except Exception:                               # noqa: BLE001
        # Sin poder calcular la hora, se calla: el error caro es
        # escribir sin querer.
        return True


def permite_escribir(
    momento_utc: datetime,
    disparo: str | None = None,
) -> dict:
    """
    ¿Puede Pepe escribir en Biwenger en este momento?

    Devuelve SIEMPRE la misma forma, con el motivo dicho, para
    que la pantalla pueda ensenar que accion se quedo sin hacer
    y por que.
    """

    vacio = {
        "available": False,
        "allowed": False,
        "in_window": None,
        "madrid_time": None,
        "trigger": disparo,
        "deliberate": False,
        "reason": None,
    }

    try:
        madrid = _hora_de_madrid(momento_utc)

        minutos_de_madrid = madrid.hour * 60 + madrid.minute

        dentro = (
            SILENCIO_DESDE <= minutos_de_madrid < SILENCIO_HASTA
        )

        # LA HORA DECIDE, NO QUIEN LLAMO.
        segun_la_hora = _es_deliberado(minutos_de_madrid)

        deliberado = segun_la_hora["deliberado"]

        base = {
            "available": True,
            "in_window": dentro,
            "madrid_time": madrid.strftime("%H:%M:%S"),
            # Se sigue publicando: para mirar un incidente vale.
            # Para decidir, ya no.
            "trigger": disparo,
            "deliberate": deliberado,
            "declared_shot": segun_la_hora["que"],
            "declared_reason": segun_la_hora["reason"],
            "window": (
                f"{SILENCIO_DESDE // 60:02d}:"
                f"{SILENCIO_DESDE % 60:02d}-"
                f"{SILENCIO_HASTA // 60:02d}:"
                f"{SILENCIO_HASTA % 60:02d}"
            ),
        }

        if not dentro:
            return {
                **base,
                "allowed": True,
                "reason": (
                    f"Son las {base['madrid_time']} de Madrid: "
                    f"fuera de la franja del reset "
                    f"({base['window']}). Se puede escribir."
                ),
            }

        if deliberado:
            return {
                **base,
                "allowed": True,
                "reason": (
                    f"Son las {base['madrid_time']} de Madrid, "
                    f"dentro de la franja del reset, y a esta "
                    f"hora SI toca un disparo declarado "
                    f"(«{segun_la_hora['que']}»): es el trabajo "
                    f"de la ventana."
                ),
            }

        return {
            **base,
            "allowed": False,
            "reason": (
                f"ZONA DE SILENCIO: son las "
                f"{base['madrid_time']} de Madrid y el reset se "
                f"ejecuta en esta franja ({base['window']}). A "
                f"esta hora NO toca ningun disparo declarado de "
                f"la ventana, asi que esta vuelta esta "
                f"DESCOLOCADA venga de donde venga —llega de "
                f"«{disparo or 'origen desconocido'}»—: se lee y "
                f"se publica, no se escribe. "
                f"{segun_la_hora['reason'] or ''}".strip()
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "available": False,
            "allowed": False,
            "in_window": True,
            "reason": (
                f"No se pudo calcular la hora de Madrid, asi que "
                f"no se escribe: {type(error).__name__}: {error}"
            ),
        }


def lo_que_se_quedo_sin_hacer(
    silencio: dict | None,
    acciones: list | None,
) -> dict:
    """
    Que acciones bloqueo el silencio, para que se vean.

    Una barandilla que frena en silencio es indistinguible de
    una averia.
    """

    estado = silencio if isinstance(silencio, dict) else {}

    pendientes = [
        a for a in (acciones if isinstance(acciones, list) else [])
        if a
    ]

    if estado.get("allowed", True):
        return {
            "blocked": False,
            "actions": [],
            "reason": None,
        }

    return {
        "blocked": True,
        "actions": pendientes,
        "reason": (
            (
                f"La zona de silencio dejo sin hacer: "
                f"{', '.join(str(a) for a in pendientes)}."
            )
            if pendientes
            else (
                "La zona de silencio esta activa y no habia "
                "ninguna accion pendiente."
            )
        ),
    }


def observacion_del_reset(
    silencio: dict | None,
    precios_cambiados: bool | None,
    momento_utc: datetime | None = None,
) -> dict:
    """
    La medicion que sale gratis: de cada vuelta dentro de la
    franja, si los precios YA habian cambiado.

    Con una semana de estas hay hora exacta del reset sin gastar
    ni una peticion.
    """

    estado = silencio or {}

    return {
        "in_window": bool(estado.get("in_window")),
        "madrid_time": estado.get("madrid_time"),
        "prices_changed": precios_cambiados,
        "at": (
            momento_utc.isoformat()
            if isinstance(momento_utc, datetime)
            else None
        ),
        "reason": (
            (
                f"A las {estado.get('madrid_time')} de Madrid "
                f"los precios "
                + (
                    "YA habian cambiado."
                    if precios_cambiados
                    else "todavia NO habian cambiado."
                )
            )
            if estado.get("in_window")
            and precios_cambiados is not None
            else None
        ),
    }
