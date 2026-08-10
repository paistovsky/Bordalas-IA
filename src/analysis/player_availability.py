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


def normalize_status(
    status: Any,
) -> str:

    if status is None:
        return "ok"

    return str(status).strip().lower()


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
        }

    # ==================================================
    # FITNESS CON AVISOS
    # ==================================================

    if fitness:

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