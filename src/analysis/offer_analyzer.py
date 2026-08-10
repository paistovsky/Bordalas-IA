from src.analysis.deadline_engine import (
    build_deadline_state,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ======================================================
# UTILIDADES
# ======================================================


def get_my_user_id(
    snapshot: dict,
) -> int | None:
    """
    Intenta detectar nuestro user ID desde distintas
    estructuras del snapshot.
    """

    league = snapshot.get(
        "league",
        {},
    )

    if isinstance(
        league,
        dict,
    ):

        user = league.get(
            "user",
            {},
        )

        if isinstance(
            user,
            dict,
        ):

            user_id = user.get(
                "id"
            )

            if user_id is not None:
                return int(
                    user_id
                )

    market = snapshot.get(
        "market",
        {},
    )

    for offer in market.get(
        "offers",
        [],
    ):

        from_user = offer.get(
            "from"
        )

        if isinstance(
            from_user,
            dict,
        ):

            # En nuestros snapshots actuales,
            # las pujas salientes contienen nuestro ID.
            user_id = from_user.get(
                "id"
            )

            if user_id is not None:

                # Fallback provisional.
                return int(
                    user_id
                )

    return None


def extract_player_ids(
    offer: dict,
) -> list[int]:

    result = []

    requested = offer.get(
        "requestedPlayers",
        [],
    )

    if isinstance(
        requested,
        list,
    ):

        for item in requested:

            if isinstance(
                item,
                int,
            ):
                result.append(
                    item
                )

            elif isinstance(
                item,
                dict,
            ):

                player_id = item.get(
                    "id"
                )

                if player_id is not None:

                    result.append(
                        int(
                            player_id
                        )
                    )

    player = offer.get(
        "player"
    )

    if isinstance(
        player,
        int,
    ):

        if player not in result:
            result.append(
                player
            )

    elif isinstance(
        player,
        dict,
    ):

        player_id = player.get(
            "id"
        )

        if (
            player_id is not None
            and
            int(
                player_id
            )
            not in result
        ):

            result.append(
                int(
                    player_id
                )
            )

    return result


def get_player_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    board = (
        build_strategic_target_board(
            snapshot,
            limit=None,
            sort_by="strategic",
        )
    )

    return {
        int(
            player[
                "id"
            ]
        ):
            player

        for player in board
    }


# ======================================================
# CLASIFICACIÓN DE DIRECCIÓN
# ======================================================


def classify_offer_direction(
    offer: dict,
    my_user_id: int | None,
) -> str:
    """
    OUTGOING:
    oferta enviada por nosotros.

    INCOMING:
    oferta enviada a nosotros.

    UNKNOWN:
    todavía no conocemos suficiente estructura.
    """

    from_user = offer.get(
        "from"
    )

    to_user = offer.get(
        "to"
    )

    from_id = None
    to_id = None

    if isinstance(
        from_user,
        dict,
    ):

        from_id = from_user.get(
            "id"
        )

    elif isinstance(
        from_user,
        int,
    ):

        from_id = from_user

    if isinstance(
        to_user,
        dict,
    ):

        to_id = to_user.get(
            "id"
        )

    elif isinstance(
        to_user,
        int,
    ):

        to_id = to_user

    if my_user_id is not None:

        if (
            from_id is not None
            and
            int(
                from_id
            )
            == my_user_id
        ):

            return "OUTGOING"

        if (
            to_id is not None
            and
            int(
                to_id
            )
            == my_user_id
        ):

            return "INCOMING"

    return "UNKNOWN"


# ======================================================
# ORIGEN
# ======================================================


def classify_counterparty(
    offer: dict,
    direction: str,
) -> dict:
    """
    Devuelve quién está al otro lado.

    Para OUTGOING:
    miramos 'to'.

    Para INCOMING:
    miramos 'from'.
    """

    if direction == "OUTGOING":

        counterparty = offer.get(
            "to"
        )

    elif direction == "INCOMING":

        counterparty = offer.get(
            "from"
        )

    else:

        return {
            "type":
                "UNKNOWN",

            "id":
                None,

            "name":
                None,
        }

    if counterparty is None:

        return {
            "type":
                "COMPUTER",

            "id":
                None,

            "name":
                "MÁQUINA",
        }

    if isinstance(
        counterparty,
        dict,
    ):

        return {
            "type":
                "MANAGER",

            "id":
                counterparty.get(
                    "id"
                ),

            "name":
                counterparty.get(
                    "name"
                )
                or
                "MANAGER",
        }

    if isinstance(
        counterparty,
        int,
    ):

        return {
            "type":
                "MANAGER",

            "id":
                counterparty,

            "name":
                f"MANAGER {counterparty}",
        }

    return {
        "type":
            "UNKNOWN",

        "id":
            None,

        "name":
            str(
                counterparty
            ),
    }


# ======================================================
# ANÁLISIS ECONÓMICO
# ======================================================


def calculate_offer_premium(
    amount: int,
    market_value: int,
) -> dict:

    difference = (
        amount
        - market_value
    )

    if market_value <= 0:

        percentage = 0.0

    else:

        percentage = (
            difference
            / market_value
        ) * 100

    return {
        "difference":
            difference,

        "percentage":
            round(
                percentage,
                1,
            ),
    }


# ======================================================
# LIQUIDEZ / DEADLINE
# ======================================================


def classify_liquidity_pressure(
    snapshot: dict,
) -> dict:

    deadline = (
        build_deadline_state(
            snapshot
        )
    )

    market = snapshot.get(
        "market",
        {}
    )

    status = market.get(
        "status",
        {}
    )

    balance = int(
        status.get(
            "balance",
            0,
        )
        or 0
    )

    seconds = (
        deadline[
            "calendar"
        ][
            "seconds_to_lineup_lock"
        ]
    )

    if balance >= 0:

        if deadline[
            "hard_safety_mode"
        ]:

            level = (
                "CONTROLAR"
            )

        else:

            level = (
                "BAJA"
            )

    else:

        if seconds is None:

            level = (
                "ALTA"
            )

        elif seconds <= 24 * 3600:

            level = (
                "CRITICA"
            )

        elif seconds <= 48 * 3600:

            level = (
                "MUY_ALTA"
            )

        else:

            level = (
                "MODERADA"
            )

    return {
        "balance":
            balance,

        "level":
            level,

        "seconds_to_deadline":
            seconds,

        "hard_safety_mode":
            deadline[
                "hard_safety_mode"
            ],

        "deadline":
            deadline,
    }


# ======================================================
# ANÁLISIS DE UNA OFERTA
# ======================================================


def analyze_offer(
    offer: dict,
    my_user_id: int | None,
    player_lookup: dict[int, dict],
) -> dict:

    direction = (
        classify_offer_direction(
            offer,
            my_user_id,
        )
    )

    counterparty = (
        classify_counterparty(
            offer,
            direction,
        )
    )

    player_ids = (
        extract_player_ids(
            offer
        )
    )

    players = []

    for player_id in player_ids:

        target = player_lookup.get(
            player_id
        )

        if target is None:

            players.append(
                {
                    "id":
                        player_id,

                    "name":
                        f"Player {player_id}",

                    "price":
                        0,
                }
            )

        else:

            players.append(
                target
            )

    amount = int(
        offer.get(
            "amount",
            0,
        )
        or 0
    )

    market_value = sum(
        int(
            player.get(
                "price",
                0,
            )
            or 0
        )

        for player in players
    )

    premium = (
        calculate_offer_premium(
            amount=
                amount,

            market_value=
                market_value,
        )
    )

    return {
        "offer_id":
            offer.get(
                "id"
            ),

        "status":
            offer.get(
                "status"
            ),

        "type":
            offer.get(
                "type"
            ),

        "amount":
            amount,

        "created":
            offer.get(
                "created"
            ),

        "until":
            offer.get(
                "until"
            ),

        "direction":
            direction,

        "counterparty":
            counterparty,

        "player_ids":
            player_ids,

        "players":
            players,

        "market_value":
            market_value,

        "premium_amount":
            premium[
                "difference"
            ],

        "premium_percent":
            premium[
                "percentage"
            ],

        "raw_offer":
            offer,
    }


# ======================================================
# DECISIÓN PROVISIONAL
# ======================================================


def provisional_incoming_decision(
    offer: dict,
    liquidity: dict,
) -> dict:
    """
    Esta lógica es deliberadamente conservadora.

    Todavía NO sabemos con certeza la estructura
    completa de una oferta recibida en Biwenger.

    Hasta capturar una oferta real:
    NUNCA autorizamos aceptación automática.
    """

    if offer[
        "direction"
    ] != "INCOMING":

        return {
            "decision":
                "NO_APLICA",

            "automatic":
                False,

            "reason":
                "No es una oferta recibida.",
        }

    return {
        "decision":
            "REVISAR_OFERTA",

        "automatic":
            False,

        "reason": (
            "Oferta recibida detectada, pero la aceptación "
            "automática permanece bloqueada hasta validar "
            "la estructura y endpoint reales de Biwenger."
        ),
    }


# ======================================================
# BOARD DE OFERTAS
# ======================================================


def build_offer_board(
    snapshot: dict,
) -> dict:

    my_user_id = (
        get_my_user_id(
            snapshot
        )
    )

    player_lookup = (
        get_player_lookup(
            snapshot
        )
    )

    liquidity = (
        classify_liquidity_pressure(
            snapshot
        )
    )

    raw_offers = (
        snapshot
        .get(
            "market",
            {}
        )
        .get(
            "offers",
            [],
        )
    )

    analyzed = []

    for raw_offer in raw_offers:

        offer = (
            analyze_offer(
                raw_offer,
                my_user_id,
                player_lookup,
            )
        )

        offer[
            "decision"
        ] = (
            provisional_incoming_decision(
                offer,
                liquidity,
            )
        )

        analyzed.append(
            offer
        )

    outgoing = [
        offer
        for offer in analyzed
        if offer[
            "direction"
        ]
        == "OUTGOING"
    ]

    incoming = [
        offer
        for offer in analyzed
        if offer[
            "direction"
        ]
        == "INCOMING"
    ]

    unknown = [
        offer
        for offer in analyzed
        if offer[
            "direction"
        ]
        == "UNKNOWN"
    ]

    return {
        "my_user_id":
            my_user_id,

        "liquidity":
            liquidity,

        "offers":
            analyzed,

        "outgoing":
            outgoing,

        "incoming":
            incoming,

        "unknown":
            unknown,

        "outgoing_count":
            len(
                outgoing
            ),

        "incoming_count":
            len(
                incoming
            ),

        "unknown_count":
            len(
                unknown
            ),
    }


# ======================================================
# EJECUCIÓN DIRECTA OPCIONAL
# ======================================================


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    board = (
        build_offer_board(
            snapshot
        )
    )

    print(
        board
    )


if __name__ == "__main__":
    main()