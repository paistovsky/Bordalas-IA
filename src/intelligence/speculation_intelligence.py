from src.intelligence.external_status import (
    get_external_player_status,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================


MAX_EXTERNAL_BUY_CANDIDATES = 8
MAX_EXTERNAL_WATCHLIST = 5


# ======================================================
# UTILIDADES
# ======================================================


def get_raw_player(
    snapshot: dict,
    player_id: int,
) -> dict | None:
    """
    Recupera el jugador en formato nativo Biwenger.

    Es importante porque external_status / mapper
    trabajan mejor con el jugador original del catálogo
    que con el objeto ya transformado por Strategic
    Target Engine.
    """

    catalog = (
        snapshot
        .get(
            "catalog",
            {}
        )
        .get(
            "data",
            {}
        )
        .get(
            "players",
            {}
        )
    )

    if not isinstance(
        catalog,
        dict,
    ):
        return None

    # En los snapshots el catálogo suele tener
    # las claves como string.
    player = catalog.get(
        str(
            player_id
        )
    )

    if player is not None:
        return player

    # Fallback por si alguna vez las claves son int.
    player = catalog.get(
        player_id
    )

    if player is not None:
        return player

    # Último fallback defensivo.
    for candidate in catalog.values():

        if int(
            candidate.get(
                "id",
                -1,
            )
        ) == int(
            player_id
        ):

            return candidate

    return None


# ======================================================
# SCORE EXTERNO
# ======================================================


def calculate_external_speculation_adjustment(
    external_status: dict,
) -> dict:
    """
    Convierte External Status a una señal utilizable
    por Speculation Engine.

    IMPORTANTE:

    En esta primera versión las fuentes externas
    únicamente pueden:

        - penalizar riesgo
        - generar alertas
        - confirmar que no detectamos riesgo

    NO damos bonus positivo por falta de noticias.
    """

    external_available = bool(
        external_status.get(
            "external_available",
            False,
        )
    )

    risk_score = int(
        external_status.get(
            "risk_score",
            0,
        )
        or 0
    )

    status = (
        external_status.get(
            "status"
        )
        or
        "SIN DATOS EXTERNOS"
    )

    alerts = list(
        external_status.get(
            "alerts",
            []
        )
        or []
    )

    # ==================================================
    # SIN DATOS FIABLES
    # ==================================================

    if not external_available:

        return {
            "score":
                0.0,

            "confidence":
                0,

            "risk_score":
                risk_score,

            "classification":
                "NO_EXTERNAL_DATA",

            "automatic_block":
                False,

            "alerts":
                alerts,

            "status":
                status,
        }

    # ==================================================
    # RIESGO CRÍTICO
    # ==================================================

    if risk_score >= 70:

        return {
            "score":
                -50.0,

            "confidence":
                90,

            "risk_score":
                risk_score,

            "classification":
                "CRITICAL_EXTERNAL_RISK",

            "automatic_block":
                True,

            "alerts":
                alerts,

            "status":
                status,
        }

    # ==================================================
    # RIESGO ALTO
    # ==================================================

    if risk_score >= 60:

        return {
            "score":
                -40.0,

            "confidence":
                85,

            "risk_score":
                risk_score,

            "classification":
                "HIGH_EXTERNAL_RISK",

            "automatic_block":
                True,

            "alerts":
                alerts,

            "status":
                status,
        }

    # ==================================================
    # REVISAR
    # ==================================================

    if risk_score >= 40:

        return {
            "score":
                -20.0,

            "confidence":
                70,

            "risk_score":
                risk_score,

            "classification":
                "EXTERNAL_WARNING",

            "automatic_block":
                False,

            "alerts":
                alerts,

            "status":
                status,
        }

    if risk_score >= 20:

        return {
            "score":
                -10.0,

            "confidence":
                60,

            "risk_score":
                risk_score,

            "classification":
                "MINOR_EXTERNAL_WARNING",

            "automatic_block":
                False,

            "alerts":
                alerts,

            "status":
                status,
        }

    # ==================================================
    # SIN RIESGO DETECTADO
    # ==================================================

    return {
        "score":
            0.0,

        "confidence":
            70,

        "risk_score":
            risk_score,

        "classification":
            "NO_EXTERNAL_RISK_DETECTED",

        "automatic_block":
            False,

        "alerts":
            alerts,

        "status":
            status,
    }


# ======================================================
# ANALIZAR JUGADOR
# ======================================================


def analyze_external_speculation_player(
    snapshot: dict,
    player: dict,
) -> dict:
    """
    Obtiene inteligencia externa para un jugador
    procesado por Speculation Engine.
    """

    player_id = int(
        player[
            "id"
        ]
    )

    raw_player = (
        get_raw_player(
            snapshot,
            player_id,
        )
    )

    if raw_player is None:

        return {
            "player_id":
                player_id,

            "name":
                player.get(
                    "name"
                ),

            "available":
                False,

            "external_status":
                None,

            "signal": {
                "score":
                    0.0,

                "confidence":
                    0,

                "risk_score":
                    0,

                "classification":
                    "PLAYER_NOT_FOUND",

                "automatic_block":
                    False,

                "alerts":
                    [],

                "status":
                    "PLAYER_NOT_FOUND",
            },
        }

    try:

        external_status = (
            get_external_player_status(
                snapshot,
                raw_player,
            )
        )

    except Exception as error:

        return {
            "player_id":
                player_id,

            "name":
                player.get(
                    "name"
                ),

            "available":
                False,

            "external_status":
                None,

            "signal": {
                "score":
                    0.0,

                "confidence":
                    0,

                "risk_score":
                    0,

                "classification":
                    "EXTERNAL_ERROR",

                "automatic_block":
                    False,

                "alerts": [
                    (
                        "Error consultando inteligencia "
                        f"externa: {type(error).__name__}"
                    )
                ],

                "status":
                    "EXTERNAL_ERROR",
            },
        }

    signal = (
        calculate_external_speculation_adjustment(
            external_status
        )
    )

    return {
        "player_id":
            player_id,

        "name":
            player.get(
                "name"
            ),

        "available":
            bool(
                external_status.get(
                    "external_available",
                    False,
                )
            ),

        "external_status":
            external_status,

        "signal":
            signal,
    }


# ======================================================
# SHORTLIST
# ======================================================


def build_external_shortlist(
    speculation_board: dict,
) -> list[dict]:
    """
    Solo analizamos jugadores relevantes.

    Esto evita recorrer 555 jugadores contra
    servicios externos.
    """

    selected = {}

    # ==================================================
    # OBJETIVOS DE COMPRA
    # ==================================================

    for player in (
        speculation_board.get(
            "buy_candidates",
            [],
        )[
            :MAX_EXTERNAL_BUY_CANDIDATES
        ]
    ):

        selected[
            int(
                player[
                    "id"
                ]
            )
        ] = player

    # ==================================================
    # CANDIDATOS A VENTA
    # ==================================================

    for player in speculation_board.get(
        "sell_candidates",
        [],
    ):

        selected[
            int(
                player[
                    "id"
                ]
            )
        ] = player

    # ==================================================
    # WATCHLIST
    # ==================================================

    for player in (
        speculation_board.get(
            "watchlist",
            [],
        )[
            :MAX_EXTERNAL_WATCHLIST
        ]
    ):

        selected[
            int(
                player[
                    "id"
                ]
            )
        ] = player

    # ==================================================
    # FRANCHISE
    # ==================================================

    active_franchise = (
        speculation_board.get(
            "active_franchise_bid"
        )
    )

    if active_franchise:

        player = active_franchise.get(
            "player"
        )

        if player:

            selected[
                int(
                    player[
                        "id"
                    ]
                )
            ] = player

    return list(
        selected.values()
    )


# ======================================================
# BOARD EXTERNO
# ======================================================


def build_external_speculation_board(
    snapshot: dict,
    speculation_board: dict,
) -> dict:

    shortlist = (
        build_external_shortlist(
            speculation_board
        )
    )

    results = []

    for player in shortlist:

        result = (
            analyze_external_speculation_player(
                snapshot=
                    snapshot,

                player=
                    player,
            )
        )

        results.append(
            result
        )

    # ==================================================
    # ÍNDICE
    # ==================================================

    lookup = {
        int(
            item[
                "player_id"
            ]
        ):
            item

        for item in results
    }

    blocked = [
        item

        for item in results

        if item[
            "signal"
        ][
            "automatic_block"
        ]
    ]

    warnings = [
        item

        for item in results

        if (
            not item[
                "signal"
            ][
                "automatic_block"
            ]
            and
            item[
                "signal"
            ][
                "risk_score"
            ]
            > 0
        )
    ]

    clean = [
        item

        for item in results

        if (
            item[
                "signal"
            ][
                "risk_score"
            ]
            == 0
            and
            item[
                "available"
            ]
        )
    ]

    unavailable = [
        item

        for item in results

        if not item[
            "available"
        ]
    ]

    return {
        "shortlist_count":
            len(
                shortlist
            ),

        "results":
            results,

        "lookup":
            lookup,

        "blocked":
            blocked,

        "warnings":
            warnings,

        "clean":
            clean,

        "unavailable":
            unavailable,

        "blocked_count":
            len(
                blocked
            ),

        "warning_count":
            len(
                warnings
            ),

        "clean_count":
            len(
                clean
            ),

        "unavailable_count":
            len(
                unavailable
            ),
    }