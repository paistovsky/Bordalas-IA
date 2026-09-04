from typing import Any


# Estados que consideramos directamente incompatibles
# con una alineación automática.
BLOCKING_STATUSES = {
    "injured",
    "suspended",
    "sanctioned",
    "out",
}

# Estados que no bloquean automáticamente,
# pero requieren precaución.
WARNING_STATUSES = {
    "doubt",
    "doubtful",
    "questionable",
}

# Estados que Biwenger da por buenos.
HEALTHY_STATUSES = {
    "ok",
    "",
}


# ======================================================
# QUE ES DE VERDAD `fitness`  (04/09/2026)
#
#     No es un parte medico: es el historial por jornada.
#     Un numero son los puntos de esa jornada, `null` es que
#     no hay observacion, y SOLO un texto -"injured",
#     "doubt", "sanctioned", "discarded"- dice que ese dia no
#     jugo, y por que.
#
#     Sobre la foto del 17/08, de 569 jugadores: 205 traen
#     `fitness` no vacio y solo 13 traen un texto dentro. Los
#     otros 192 son puntos.
#
#     Marcar VIGILAR por "fitness no vacio" etiquetaba a los
#     once titulares -Yamal incluido, con `fitness=[4]`, y
#     De la Fuente con `fitness=[4]`- y dejaba la etiqueta sin
#     significado: 205 de 569 jugadores marcados es no marcar
#     ninguno.
# ======================================================


def normalize_status(
    status: Any,
) -> str:

    if status is None:
        return "ok"

    return str(status).strip().lower()


def fitness_signals(
    fitness: Any,
) -> list:
    """
    Los avisos de verdad que trae `fitness`, si trae alguno.

    Un numero son puntos. `null` es una jornada sin dato.
    Solo un texto es una señal.
    """

    if not isinstance(fitness, (list, tuple)):
        return []

    señales = []

    for entrada in fitness:

        # `bool` es subclase de `int`, y un True colado en el
        # array no es un parte de lesion.
        if isinstance(entrada, bool):
            continue

        if isinstance(entrada, (int, float)):
            continue

        if entrada is None:
            continue

        texto = str(entrada).strip().lower()

        if not texto:
            continue

        if texto not in señales:
            señales.append(texto)

    return señales


def analyze_player_availability(
    player: dict,
) -> dict:

    status = normalize_status(
        player.get("status")
    )

    status_info = (
        player.get("statusInfo")
        or ""
    )

    fitness = (
        player.get("fitness")
        or []
    )

    señales = fitness_signals(fitness)

    # ==================================================
    # BLOQUEADO
    # ==================================================

    if status in BLOCKING_STATUSES:

        if status == "injured":
            label = "LESIONADO"

        elif status in {
            "suspended",
            "sanctioned",
        }:
            label = "SANCIONADO"

        else:
            label = "NO DISPONIBLE"

        return {
            "available":
                False,

            "automatic_lineup":
                False,

            "risk":
                100,

            "status":
                status,

            "label":
                label,

            "status_info":
                status_info,

            "fitness":
                fitness,

            "signals":
                señales,
        }

    # ==================================================
    # DUDA
    # ==================================================

    if status in WARNING_STATUSES:

        return {
            "available":
                True,

            "automatic_lineup":
                False,

            "risk":
                60,

            "status":
                status,

            "label":
                "DUDA",

            "status_info":
                status_info,

            "fitness":
                fitness,

            "signals":
                señales,
        }

    # ==================================================
    # VIGILAR: SOLO CON UNA SEÑAL DE VERDAD
    #
    #     Tres cosas cuentan como señal, y ninguna es "tiene
    #     puntos recientes":
    #
    #       1. Un texto dentro de `fitness`: se perdio una
    #          jornada por algo. Brugue sale `status=ok` con
    #          `fitness=["sanctioned"]`, y eso si merece un
    #          vistazo.
    #       2. Un `statusInfo` con texto: Biwenger ha escrito
    #          un parte sobre el.
    #       3. Un `status` que no reconocemos y no es "ok"
    #          -"unknown", "discarded"-. No bloquea, pero
    #          tampoco se pinta en verde.
    # ==================================================

    hay_señal = bool(
        señales
        or str(status_info).strip()
        or status not in HEALTHY_STATUSES
    )

    if hay_señal:

        return {
            "available":
                True,

            "automatic_lineup":
                True,

            "risk":
                20,

            "status":
                status,

            "label":
                "VIGILAR",

            "status_info":
                status_info,

            "fitness":
                fitness,

            "signals":
                señales,
        }

    # ==================================================
    # NORMAL
    # ==================================================

    return {
        "available":
            True,

        "automatic_lineup":
            True,

        "risk":
            0,

        "status":
            status,

        "label":
            "OK",

        "status_info":
            status_info,

        "fitness":
            fitness,

        "signals":
            señales,
    }


def is_player_available(
    player: dict,
) -> bool:

    analysis = (
        analyze_player_availability(
            player
        )
    )

    return analysis[
        "available"
    ]


def can_auto_lineup(
    player: dict,
) -> bool:

    analysis = (
        analyze_player_availability(
            player
        )
    )

    return analysis[
        "automatic_lineup"
    ]
