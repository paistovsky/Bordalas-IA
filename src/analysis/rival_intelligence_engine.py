from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json


DEFAULT_INITIAL_BALANCE = 23_300_000

KNOWN_NON_ECONOMIC_TYPES = {
    "adminText",
    "leagueReset",
    "leagueSettings",
    "playerMovements",
    "userJoin",
    "userName",
}


# ============================================================
# UTILIDADES
# ============================================================


def safe_int(
    value,
    default: int = 0,
) -> int:

    try:
        return int(
            value
            or 0
        )

    except (
        TypeError,
        ValueError,
    ):
        return default


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def build_player_catalog_index(
    catalog: dict,
) -> dict[int, dict]:

    raw = (
        catalog
        .get(
            "data",
            {},
        )
        .get(
            "players",
            {},
        )
        or {}
    )

    iterable = (
        raw.values()
        if isinstance(
            raw,
            dict,
        )
        else raw
    )

    result = {}

    for player in iterable:

        try:
            result[
                int(
                    player[
                        "id"
                    ]
                )
            ] = player

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return result


def build_profile_index(
    profiles: list[dict],
) -> dict[int, dict]:

    result = {}

    for profile in profiles:

        user_id = safe_int(
            profile.get(
                "id"
            )
        )

        if user_id > 0:
            result[
                user_id
            ] = profile

    return result


def player_name(
    player_id: int,
    catalog_index: dict[int, dict],
) -> str:

    player = (
        catalog_index.get(
            int(
                player_id
            ),
            {},
        )
        or {}
    )

    return (
        player.get(
            "name"
        )
        or
        f"Player {player_id}"
    )


def player_market_value(
    player_id: int,
    catalog_index: dict[int, dict],
) -> int:

    player = (
        catalog_index.get(
            int(
                player_id
            ),
            {},
        )
        or {}
    )

    return safe_int(
        player.get(
            "price"
        )
    )


# ============================================================
# MANAGER BASE
# ============================================================


def initialize_manager(
    user: dict,
    initial_balance: int,
    profile: dict | None,
) -> dict:

    profile = (
        profile
        or {}
    )

    return {
        "user_id":
            safe_int(
                user.get(
                    "id"
                )
            ),

        "name":
            (
                profile.get(
                    "name"
                )
                or
                user.get(
                    "name",
                    "?",
                )
            ),

        "points":
            safe_int(
                profile.get(
                    "points"
                )
            ),

        "join_date":
            profile.get(
                "joinDate"
            ),

        "last_access":
            profile.get(
                "lastAccess"
            ),

        "initial_balance":
            initial_balance,

        "income":
            0,

        "expenses":
            0,

        "balance":
            initial_balance,

        "market_buys":
            0,

        "sales_to_computer":
            0,

        "user_to_user_buys":
            0,

        "user_to_user_sales":
            0,

        "won_auctions":
            0,

        "lost_bids":
            0,

        "lost_bid_amount_total":
            0,

        "max_lost_bid":
            0,

        "max_winning_bid":
            0,

        "transactions":
            [],

        "lost_bid_history":
            [],

        "roster":
            [],

        "roster_count":
            0,

        "roster_value":
            0,

        "roster_price_increment":
            0,

        "roster_points":
            0,

        "acquisition_cost_known":
            0,

        "acquisition_cost_known_count":
            0,
    }


def add_income(
    manager: dict,
    amount: int,
    transaction: dict,
) -> None:

    manager[
        "income"
    ] += amount

    manager[
        "balance"
    ] += amount

    manager[
        "transactions"
    ].append(
        {
            **transaction,
            "delta":
                amount,
        }
    )


def add_expense(
    manager: dict,
    amount: int,
    transaction: dict,
) -> None:

    manager[
        "expenses"
    ] += amount

    manager[
        "balance"
    ] -= amount

    manager[
        "transactions"
    ].append(
        {
            **transaction,
            "delta":
                -amount,
        }
    )


# ============================================================
# PLANTILLAS RIVALES
# ============================================================


def enrich_rosters(
    managers: dict[int, dict],
    profile_index: dict[int, dict],
    catalog_index: dict[int, dict],
) -> None:

    for (
        user_id,
        manager,
    ) in managers.items():

        profile = (
            profile_index.get(
                user_id,
                {},
            )
            or {}
        )

        raw_players = (
            profile.get(
                "players",
                [],
            )
            or []
        )

        roster = []

        for item in raw_players:

            player_id = safe_int(
                item.get(
                    "id"
                )
            )

            if player_id <= 0:
                continue

            catalog_player = (
                catalog_index.get(
                    player_id,
                    {},
                )
                or {}
            )

            owner = (
                item.get(
                    "owner",
                    {},
                )
                or {}
            )

            acquisition_price = (
                owner.get(
                    "price"
                )
            )

            if acquisition_price is not None:

                acquisition_price = (
                    safe_int(
                        acquisition_price
                    )
                )

            record = {
                "id":
                    player_id,

                "name":
                    (
                        catalog_player.get(
                            "name"
                        )
                        or
                        f"Player {player_id}"
                    ),

                "position":
                    catalog_player.get(
                        "position"
                    ),

                "team_id":
                    catalog_player.get(
                        "teamID"
                    ),

                "value":
                    safe_int(
                        catalog_player.get(
                            "price"
                        )
                    ),

                "price_increment":
                    safe_int(
                        catalog_player.get(
                            "priceIncrement"
                        )
                    ),

                "points":
                    safe_int(
                        catalog_player.get(
                            "points"
                        )
                    ),

                "status":
                    catalog_player.get(
                        "status"
                    ),

                "owner_since":
                    owner.get(
                        "date"
                    ),

                "acquisition_price":
                    acquisition_price,
            }

            roster.append(
                record
            )

        manager[
            "roster"
        ] = roster

        manager[
            "roster_count"
        ] = len(
            roster
        )

        manager[
            "roster_value"
        ] = sum(
            item[
                "value"
            ]
            for item
            in roster
        )

        manager[
            "roster_price_increment"
        ] = sum(
            item[
                "price_increment"
            ]
            for item
            in roster
        )

        manager[
            "roster_points"
        ] = sum(
            item[
                "points"
            ]
            for item
            in roster
        )

        known = [
            item[
                "acquisition_price"
            ]
            for item
            in roster
            if item[
                "acquisition_price"
            ]
            is not None
        ]

        manager[
            "acquisition_cost_known"
        ] = sum(
            known
        )

        manager[
            "acquisition_cost_known_count"
        ] = len(
            known
        )

        manager[
            "top_assets"
        ] = [
            {
                "id":
                    item[
                        "id"
                    ],

                "name":
                    item[
                        "name"
                    ],

                "value":
                    item[
                        "value"
                    ],

                "price_increment":
                    item[
                        "price_increment"
                    ],
            }

            for item
            in sorted(
                roster,
                key=lambda item:
                    item[
                        "value"
                    ],
                reverse=True,
            )[
                :5
            ]
        ]


# ============================================================
# PUJA MAXIMA RIVAL
# ============================================================


def calibrate_debt_ratio(
    *,
    managers: dict[int, dict],
    current_user_id: int | None,
    own_balance: int | None,
    own_maximum_bid: int | None,
) -> dict:
    """
    No hardcodeamos la regla de deuda de Biwenger.

    La calibramos con Pepe:
        headroom = maximumBid oficial - saldo oficial

        ratio = headroom / valor actual plantilla Pepe

    Como la regla es de liga, aplicamos el mismo ratio
    a los rivales.
    """

    if (
        current_user_id is None
        or
        current_user_id not in managers
    ):

        return {
            "available":
                False,

            "ratio":
                None,

            "reason":
                "No se conoce manager actual.",
        }

    own_manager = (
        managers[
            current_user_id
        ]
    )

    roster_value = safe_int(
        own_manager.get(
            "roster_value"
        )
    )

    if (
        own_balance is None
        or
        own_maximum_bid is None
        or
        roster_value <= 0
    ):

        return {
            "available":
                False,

            "ratio":
                None,

            "reason":
                (
                    "Faltan saldo, maximumBid o "
                    "valor de plantilla de Pepe."
                ),
        }

    headroom = (
        int(
            own_maximum_bid
        )
        -
        int(
            own_balance
        )
    )

    ratio = (
        headroom
        /
        roster_value
    )

    # Protección contra respuestas anómalas.
    if ratio < 0:

        return {
            "available":
                False,

            "ratio":
                None,

            "reason":
                "Headroom negativo inesperado.",
        }

    return {
        "available":
            True,

        "ratio":
            float(
                ratio
            ),

        "headroom":
            int(
                headroom
            ),

        "own_roster_value":
            roster_value,

        "own_balance":
            int(
                own_balance
            ),

        "own_maximum_bid":
            int(
                own_maximum_bid
            ),

        "reason":
            (
                "Ratio de deuda calibrado dinámicamente "
                "con maximumBid oficial de Pepe."
            ),
    }


def apply_market_power(
    managers: dict[int, dict],
    calibration: dict,
) -> None:

    available = bool(
        calibration.get(
            "available",
            False,
        )
    )

    ratio = (
        calibration.get(
            "ratio"
        )
        if available
        else None
    )

    for manager in managers.values():

        balance = safe_int(
            manager.get(
                "balance"
            )
        )

        roster_value = safe_int(
            manager.get(
                "roster_value"
            )
        )

        manager[
            "net_worth"
        ] = (
            balance
            +
            roster_value
        )

        if (
            available
            and
            ratio is not None
        ):

            estimated_headroom = round(
                roster_value
                *
                float(
                    ratio
                )
            )

            estimated_max_bid = max(
                0,
                balance
                +
                estimated_headroom,
            )

            manager[
                "maximum_bid"
            ] = (
                estimated_max_bid
            )

            manager[
                "maximum_bid_headroom"
            ] = (
                estimated_headroom
            )

            manager[
                "maximum_bid_source"
            ] = (
                "CALIBRATED_FROM_PEPE"
            )

        else:

            manager[
                "maximum_bid"
            ] = max(
                0,
                balance,
            )

            manager[
                "maximum_bid_headroom"
            ] = 0

            manager[
                "maximum_bid_source"
            ] = (
                "CASH_ONLY_FALLBACK"
            )


# ============================================================
# RANKING / THREAT
# ============================================================


def normalized(
    value: float,
    values: list[float],
) -> float | None:

    if not values:
        return None

    minimum = min(
        values
    )

    maximum = max(
        values
    )

    if maximum == minimum:
        return None

    return (
        (
            value
            -
            minimum
        )
        /
        (
            maximum
            -
            minimum
        )
    ) * 100.0


def build_points_rank(
    managers: dict[int, dict],
) -> None:
    """
    Ranking por puntos, con empate real.
    No pretende sustituir desempates internos de Biwenger.
    """

    unique_points = sorted(
        {
            safe_int(
                manager.get(
                    "points"
                )
            )
            for manager
            in managers.values()
        },
        reverse=True,
    )

    rank_map = {
        points:
            index
        for (
            index,
            points,
        )
        in enumerate(
            unique_points,
            start=1,
        )
    }

    all_equal = (
        len(
            unique_points
        )
        <= 1
    )

    for manager in managers.values():

        manager[
            "points_rank"
        ] = (
            None
            if all_equal
            else
            rank_map.get(
                safe_int(
                    manager.get(
                        "points"
                    )
                )
            )
        )

        manager[
            "ranking_status"
        ] = (
            "ALL_TIED"
            if all_equal
            else
            "POINTS_DERIVED"
        )


def apply_threat_scores(
    managers: dict[int, dict],
    current_user_id: int | None,
) -> None:
    """
    V2:
    Threat Score relativo dentro de ESTA liga.

    Señales:
      - puntos (35) si ya discriminan,
      - valor plantilla (25),
      - puja máxima (20),
      - actividad mercado (10),
      - agresividad de pujas (10).

    Si una señal no discrimina (ej. todos 0 puntos),
    se elimina y el resto se renormaliza.
    """

    manager_list = list(
        managers.values()
    )

    points_values = [
        float(
            safe_int(
                item.get(
                    "points"
                )
            )
        )
        for item
        in manager_list
    ]

    roster_values = [
        float(
            safe_int(
                item.get(
                    "roster_value"
                )
            )
        )
        for item
        in manager_list
    ]

    max_bid_values = [
        float(
            safe_int(
                item.get(
                    "maximum_bid"
                )
            )
        )
        for item
        in manager_list
    ]

    activity_values = [
        float(
            safe_int(
                item.get(
                    "activity_count"
                )
            )
        )
        for item
        in manager_list
    ]

    bid_values = [
        float(
            max(
                safe_int(
                    item.get(
                        "max_lost_bid"
                    )
                ),
                safe_int(
                    item.get(
                        "max_winning_bid"
                    )
                ),
            )
        )
        for item
        in manager_list
    ]

    for manager in manager_list:

        components = []

        def add_component(
            key: str,
            value: float,
            values: list[float],
            weight: float,
        ) -> None:

            score = (
                normalized(
                    value,
                    values,
                )
            )

            if score is None:
                return

            components.append(
                {
                    "key":
                        key,

                    "score":
                        score,

                    "weight":
                        weight,
                }
            )

        add_component(
            "points",
            float(
                safe_int(
                    manager.get(
                        "points"
                    )
                )
            ),
            points_values,
            35.0,
        )

        add_component(
            "roster_value",
            float(
                safe_int(
                    manager.get(
                        "roster_value"
                    )
                )
            ),
            roster_values,
            25.0,
        )

        add_component(
            "maximum_bid",
            float(
                safe_int(
                    manager.get(
                        "maximum_bid"
                    )
                )
            ),
            max_bid_values,
            20.0,
        )

        add_component(
            "activity",
            float(
                safe_int(
                    manager.get(
                        "activity_count"
                    )
                )
            ),
            activity_values,
            10.0,
        )

        add_component(
            "bid_aggression",
            float(
                max(
                    safe_int(
                        manager.get(
                            "max_lost_bid"
                        )
                    ),
                    safe_int(
                        manager.get(
                            "max_winning_bid"
                        )
                    ),
                )
            ),
            bid_values,
            10.0,
        )

        total_weight = sum(
            item[
                "weight"
            ]
            for item
            in components
        )

        if total_weight <= 0:

            threat = 0.0

        else:

            threat = sum(
                (
                    item[
                        "score"
                    ]
                    *
                    item[
                        "weight"
                    ]
                )
                for item
                in components
            ) / total_weight

        threat = round(
            clamp(
                threat
            ),
            1,
        )

        manager[
            "threat_score"
        ] = (
            None
            if (
                current_user_id is not None
                and
                manager[
                    "user_id"
                ]
                == current_user_id
            )
            else threat
        )

        manager[
            "threat_components"
        ] = components

        if threat >= 80:

            level = (
                "VERY_HIGH"
            )

        elif threat >= 60:

            level = "HIGH"

        elif threat >= 40:

            level = "MEDIUM"

        elif threat >= 20:

            level = "LOW"

        else:

            level = "VERY_LOW"

        manager[
            "threat_level"
        ] = (
            "US"
            if (
                current_user_id is not None
                and
                manager[
                    "user_id"
                ]
                == current_user_id
            )
            else level
        )


# ============================================================
# BUILD
# ============================================================


def build_rival_intelligence(
    *,
    events: list[dict],
    users: list[dict],
    profiles: list[dict],
    catalog: dict,
    current_user_id: int | None,
    own_finances: dict | None = None,
    own_balance: int | None = None,
    own_maximum_bid: int | None = None,
) -> dict:

    own_finances = (
        own_finances
        or {}
    )

    initial_balance = safe_int(
        own_finances.get(
            "initialBalance"
        ),
        DEFAULT_INITIAL_BALANCE,
    )

    profile_index = (
        build_profile_index(
            profiles
        )
    )

    managers = {
        safe_int(
            user.get(
                "id"
            )
        ):
            initialize_manager(
                user=
                    user,

                initial_balance=
                    initial_balance,

                profile=
                    profile_index.get(
                        safe_int(
                            user.get(
                                "id"
                            )
                        )
                    ),
            )

        for user
        in users

        if safe_int(
            user.get(
                "id"
            )
        ) > 0
    }

    catalog_index = (
        build_player_catalog_index(
            catalog
        )
    )

    event_type_counts = (
        Counter()
    )

    unknown_types = (
        Counter()
    )

    economic_operations = 0
    competitive_bids = 0

    # --------------------------------------------------------
    # LEDGER + BIDS
    # --------------------------------------------------------

    for event in sorted(
        events,
        key=lambda item:
            safe_int(
                item.get(
                    "date"
                )
            ),
    ):

        event_type = str(
            event.get(
                "type"
            )
            or ""
        )

        event_type_counts[
            event_type
        ] += 1

        content = (
            event.get(
                "content"
            )
        )

        event_date = safe_int(
            event.get(
                "date"
            )
        )

        if event_type == "market":

            if not isinstance(
                content,
                list,
            ):
                continue

            for operation in content:

                buyer = (
                    operation.get(
                        "to",
                        {},
                    )
                    or {}
                )

                buyer_id = safe_int(
                    buyer.get(
                        "id"
                    )
                )

                amount = safe_int(
                    operation.get(
                        "amount"
                    )
                )

                player_id = safe_int(
                    operation.get(
                        "player"
                    )
                )

                if (
                    buyer_id
                    in managers
                    and
                    amount > 0
                ):

                    add_expense(
                        managers[
                            buyer_id
                        ],
                        amount,
                        {
                            "date":
                                event_date,

                            "kind":
                                "BUY_FROM_COMPUTER",

                            "player_id":
                                player_id,

                            "player_name":
                                player_name(
                                    player_id,
                                    catalog_index,
                                ),

                            "amount":
                                amount,
                        },
                    )

                    managers[
                        buyer_id
                    ][
                        "market_buys"
                    ] += 1

                    managers[
                        buyer_id
                    ][
                        "won_auctions"
                    ] += 1

                    managers[
                        buyer_id
                    ][
                        "max_winning_bid"
                    ] = max(
                        managers[
                            buyer_id
                        ][
                            "max_winning_bid"
                        ],
                        amount,
                    )

                    economic_operations += 1

                for bid in (
                    operation.get(
                        "bids",
                        [],
                    )
                    or []
                ):

                    bidder = (
                        bid.get(
                            "user",
                            {},
                        )
                        or {}
                    )

                    bidder_id = safe_int(
                        bidder.get(
                            "id"
                        )
                    )

                    bid_amount = safe_int(
                        bid.get(
                            "amount"
                        )
                    )

                    if (
                        bidder_id
                        not in managers
                        or
                        bid_amount <= 0
                    ):
                        continue

                    competitive_bids += 1

                    manager = (
                        managers[
                            bidder_id
                        ]
                    )

                    manager[
                        "lost_bids"
                    ] += 1

                    manager[
                        "lost_bid_amount_total"
                    ] += bid_amount

                    manager[
                        "max_lost_bid"
                    ] = max(
                        manager[
                            "max_lost_bid"
                        ],
                        bid_amount,
                    )

                    manager[
                        "lost_bid_history"
                    ].append(
                        {
                            "date":
                                event_date,

                            "player_id":
                                player_id,

                            "player_name":
                                player_name(
                                    player_id,
                                    catalog_index,
                                ),

                            "amount":
                                bid_amount,

                            "winning_amount":
                                amount,

                            "winner_id":
                                buyer_id,

                            "winner_name":
                                buyer.get(
                                    "name"
                                ),
                        }
                    )

        elif event_type == "transfer":

            if not isinstance(
                content,
                list,
            ):
                continue

            for operation in content:

                seller = (
                    operation.get(
                        "from",
                        {},
                    )
                    or {}
                )

                buyer = (
                    operation.get(
                        "to",
                        {},
                    )
                    or {}
                )

                seller_id = safe_int(
                    seller.get(
                        "id"
                    )
                )

                buyer_id = safe_int(
                    buyer.get(
                        "id"
                    )
                )

                amount = safe_int(
                    operation.get(
                        "amount"
                    )
                )

                player_id = safe_int(
                    operation.get(
                        "player"
                    )
                )

                if amount <= 0:
                    continue

                if seller_id in managers:

                    add_income(
                        managers[
                            seller_id
                        ],
                        amount,
                        {
                            "date":
                                event_date,

                            "kind":
                                (
                                    "SELL_TO_USER"
                                    if buyer_id
                                    in managers
                                    else
                                    "SELL_TO_COMPUTER"
                                ),

                            "player_id":
                                player_id,

                            "player_name":
                                player_name(
                                    player_id,
                                    catalog_index,
                                ),

                            "amount":
                                amount,

                            "counterparty_id":
                                (
                                    buyer_id
                                    if buyer_id > 0
                                    else None
                                ),

                            "counterparty_name":
                                buyer.get(
                                    "name"
                                ),
                        },
                    )

                    if buyer_id in managers:

                        managers[
                            seller_id
                        ][
                            "user_to_user_sales"
                        ] += 1

                    else:

                        managers[
                            seller_id
                        ][
                            "sales_to_computer"
                        ] += 1

                    economic_operations += 1

                if buyer_id in managers:

                    add_expense(
                        managers[
                            buyer_id
                        ],
                        amount,
                        {
                            "date":
                                event_date,

                            "kind":
                                "BUY_FROM_USER",

                            "player_id":
                                player_id,

                            "player_name":
                                player_name(
                                    player_id,
                                    catalog_index,
                                ),

                            "amount":
                                amount,

                            "counterparty_id":
                                seller_id,

                            "counterparty_name":
                                seller.get(
                                    "name"
                                ),
                        },
                    )

                    managers[
                        buyer_id
                    ][
                        "user_to_user_buys"
                    ] += 1

                    economic_operations += 1

        elif (
            event_type
            not in
            KNOWN_NON_ECONOMIC_TYPES
        ):

            unknown_types[
                event_type
            ] += 1

    # --------------------------------------------------------
    # ROSTERS
    # --------------------------------------------------------

    enrich_rosters(
        managers=
            managers,

        profile_index=
            profile_index,

        catalog_index=
            catalog_index,
    )

    # --------------------------------------------------------
    # COMPORTAMIENTO
    # --------------------------------------------------------

    for manager in managers.values():

        lost_bids = (
            manager[
                "lost_bids"
            ]
        )

        manager[
            "avg_lost_bid"
        ] = (
            round(
                manager[
                    "lost_bid_amount_total"
                ]
                /
                lost_bids
            )
            if lost_bids
            else 0
        )

        manager[
            "max_observed_bid"
        ] = max(
            manager[
                "max_lost_bid"
            ],
            manager[
                "max_winning_bid"
            ],
        )

        activity_count = (
            manager[
                "market_buys"
            ]
            +
            manager[
                "sales_to_computer"
            ]
            +
            manager[
                "user_to_user_buys"
            ]
            +
            manager[
                "user_to_user_sales"
            ]
            +
            manager[
                "lost_bids"
            ]
        )

        manager[
            "activity_count"
        ] = activity_count

        if activity_count >= 10:
            activity = "VERY_HIGH"

        elif activity_count >= 6:
            activity = "HIGH"

        elif activity_count >= 3:
            activity = "MEDIUM"

        elif activity_count >= 1:
            activity = "LOW"

        else:
            activity = "NONE"

        manager[
            "market_activity"
        ] = activity

        if (
            manager[
                "market_buys"
            ] >= 3
            or
            manager[
                "lost_bids"
            ] >= 5
        ):

            profile = "AGGRESSIVE"

        elif (
            (
                manager[
                    "sales_to_computer"
                ]
                +
                manager[
                    "user_to_user_sales"
                ]
            )
            >= 3
            and
            manager[
                "market_buys"
            ] <= 1
        ):

            profile = "SELLER"

        elif activity_count == 0:

            profile = "INACTIVE"

        else:

            profile = "BALANCED"

        manager[
            "profile"
        ] = profile

    # --------------------------------------------------------
    # VALIDACION CONTABLE PEPE
    # --------------------------------------------------------

    validation = {
        "available":
            False,

        "exact":
            False,

        "official_balance":
            None,

        "ledger_balance":
            None,

        "difference":
            None,
    }

    if (
        current_user_id is not None
        and
        current_user_id
        in managers
        and
        own_finances
    ):

        official_initial = safe_int(
            own_finances.get(
                "initialBalance"
            )
        )

        official_earnings = safe_int(
            (
                own_finances.get(
                    "earnings",
                    {},
                )
                or {}
            ).get(
                "total"
            )
        )

        official_expenses = safe_int(
            (
                own_finances.get(
                    "expenses",
                    {},
                )
                or {}
            ).get(
                "total"
            )
        )

        official_balance = (
            official_initial
            +
            official_earnings
            -
            official_expenses
        )

        ledger_balance = (
            managers[
                current_user_id
            ][
                "balance"
            ]
        )

        difference = (
            ledger_balance
            -
            official_balance
        )

        validation = {
            "available":
                True,

            "exact":
                difference
                == 0,

            "official_initial_balance":
                official_initial,

            "official_earnings":
                official_earnings,

            "official_expenses":
                official_expenses,

            "official_balance":
                official_balance,

            "ledger_balance":
                ledger_balance,

            "difference":
                difference,
        }

    # --------------------------------------------------------
    # MARKET POWER
    # --------------------------------------------------------

    calibration = (
        calibrate_debt_ratio(
            managers=
                managers,

            current_user_id=
                current_user_id,

            own_balance=
                own_balance,

            own_maximum_bid=
                own_maximum_bid,
        )
    )

    apply_market_power(
        managers=
            managers,

        calibration=
            calibration,
    )

    build_points_rank(
        managers
    )

    apply_threat_scores(
        managers=
            managers,

        current_user_id=
            current_user_id,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    ledger_status = (
        "EXACT"
        if (
            validation.get(
                "exact",
                False,
            )
            and
            not unknown_types
        )
        else
        "REVIEW_REQUIRED"
    )

    ordered_managers = sorted(
        managers.values(),
        key=lambda item: (
            (
                item.get(
                    "points_rank"
                )
                is None
            ),
            item.get(
                "points_rank"
            )
            or 999,
            -safe_int(
                item.get(
                    "roster_value"
                )
            ),
        ),
    )

    return {
        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "initial_balance":
            initial_balance,

        "ledger_status":
            ledger_status,

        "event_type_counts":
            dict(
                event_type_counts
            ),

        "unknown_types":
            dict(
                unknown_types
            ),

        "economic_operations":
            economic_operations,

        "competitive_bids":
            competitive_bids,

        "validation":
            validation,

        "maximum_bid_calibration":
            calibration,

        "managers":
            ordered_managers,
    }


def save_rival_intelligence(
    intelligence: dict,
    path: str | Path = (
        Path("data")
        /
        "rival_intelligence"
        /
        "rival_intelligence.json"
    ),
) -> None:

    path = Path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            intelligence,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
