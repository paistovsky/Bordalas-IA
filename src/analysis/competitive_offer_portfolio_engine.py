from __future__ import annotations

from copy import deepcopy
from itertools import combinations

from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.recommendation_engine import (
    generate_recommendations,
)


OBSERVER_ONLY = True


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def build_current_lineup(snapshot: dict) -> dict:
    return (
        build_lineup(
            snapshot
        )
        or {}
    )


def get_lineup_player_ids(
    lineup: dict,
) -> set[int]:

    return {
        safe_int(
            item.get(
                "id"
            )
        )
        for item
        in (
            lineup.get(
                "selected",
                [],
            )
            or []
        )
        if safe_int(
            item.get(
                "id"
            )
        ) > 0
    }



def get_selected_lookup(
    lineup: dict,
) -> dict[int, dict]:

    result = {}

    for item in (
        lineup.get(
            "selected",
            [],
        )
        or []
    ):

        player_id = safe_int(
            item.get(
                "id"
            )
        )

        if player_id > 0:

            result[
                player_id
            ] = item

    return result


def get_catalog_player(
    snapshot: dict,
    player_id: int,
) -> dict:

    raw = (
        snapshot.get(
            "catalog",
            {},
        )
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

    player_id = safe_int(
        player_id
    )

    if isinstance(
        raw,
        dict,
    ):

        return (
            raw.get(
                str(
                    player_id
                )
            )
            or
            raw.get(
                player_id
            )
            or {}
        )

    for item in raw:

        if safe_int(
            item.get(
                "id"
            )
        ) == player_id:

            return item

    return {}


def get_player_name(
    snapshot: dict,
    player_id: int,
) -> str:

    for item in (
        snapshot.get(
            "my_team",
            [],
        )
        or []
    ):

        if safe_int(
            item.get(
                "id"
            )
        ) == safe_int(
            player_id
        ):

            if item.get(
                "name"
            ):
                return str(
                    item.get(
                        "name"
                    )
                )

    catalog_player = (
        get_catalog_player(
            snapshot,
            player_id,
        )
    )

    return str(
        catalog_player.get(
            "name"
        )
        or
        f"Player {safe_int(player_id)}"
    )


def extract_player_quality_score(
    *,
    snapshot: dict,
    lineup_item: dict | None,
    player_id: int,
) -> float | None:
    """
    V1.6: usa primero el lineup_score REAL calculado por lineup_engine.

    Importante:
    lineup_score NO es una probabilidad 0..100 ni puntos fantasy esperados.
    Es la unidad interna de utilidad deportiva de Pepe. Precisamente por eso
    no la recortamos a 100: sirve para comparar el XI antes y despues de una
    venta con la misma escala.
    """

    lineup_item = (
        lineup_item
        or {}
    )

    for key in (
        "lineup_score",
        "final_score",
        "score",
    ):

        value = lineup_item.get(
            key
        )

        if value is None:
            continue

        try:
            return round(
                float(
                    value
                ),
                2,
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    catalog_player = (
        get_catalog_player(
            snapshot,
            player_id,
        )
    )

    # Fallback conservador: replicamos solo las señales base estables
    # que usa lineup_engine cuando no tenemos el item preparado.
    last_points = safe_float(
        catalog_player.get(
            "pointsLastSeason"
        )
    )

    price = safe_float(
        catalog_player.get(
            "price"
        )
    )

    if (
        last_points != 0.0
        or
        price != 0.0
    ):

        return round(
            last_points
            +
            price
            /
            1_000_000.0,
            2,
        )

    return None


def build_sporting_opportunity_cost(
    *,
    current_lineup: dict,
    post_lineup: dict,
) -> dict:
    """
    Mide el coste deportivo en la MISMA escala interna de lineup_engine.

    No lo llamamos puntos fantasy esperados: lineup_score es una heuristica
    comparativa. La metrica robusta es cuanto cae el mejor XI reconstruido.
    """

    before_score = safe_float(
        current_lineup.get(
            "lineup_score"
        )
    )

    after_score = safe_float(
        post_lineup.get(
            "lineup_score"
        )
    )

    before_playable = safe_int(
        current_lineup.get(
            "playable_count",
            len(
                current_lineup.get(
                    "selected",
                    [],
                )
                or []
            ),
        )
    )

    after_playable = safe_int(
        post_lineup.get(
            "playable_count",
            len(
                post_lineup.get(
                    "selected",
                    [],
                )
                or []
            ),
        )
    )

    missing = max(
        11
        -
        after_playable,
        0,
    )

    score_loss = max(
        before_score
        -
        after_score,
        0.0,
    )

    loss_percent = (
        score_loss
        /
        abs(
            before_score
        )
        *
        100.0
        if before_score
        else 0.0
    )

    # El ranking debe castigar primero un XI incompleto.
    ranking_cost = (
        score_loss
        +
        missing
        *
        1_000_000.0
    )

    # Señal normalizada para pricing competitivo.
    # Conserva la perdida real del lineup_engine y añade una escala 0..100
    # para que competitive_transaction_engine pueda cobrar ese coste.
    normalized_cost_score = min(
        max(
            loss_percent * 3.0
            +
            missing * 35.0,
            0.0,
        ),
        100.0,
    )

    return {
        "sporting_cost_score":
            round(
                normalized_cost_score,
                1,
            ),

        "lineup_score_before":
            round(
                before_score,
                2,
            ),

        "lineup_score_after":
            round(
                after_score,
                2,
            ),

        "lineup_score_loss":
            round(
                score_loss,
                2,
            ),

        "lineup_score_loss_percent":
            round(
                loss_percent,
                2,
            ),

        "playable_before":
            before_playable,

        "playable_after":
            after_playable,

        "missing":
            missing,

        "lineup_complete":
            missing == 0,

        "ranking_cost":
            round(
                ranking_cost,
                2,
            ),

        "metric":
            "LINEUP_ENGINE_INTERNAL_SCORE",

        "is_expected_fantasy_points":
            False,
    }

def build_replacement_change(
    *,
    snapshot: dict,
    current_lineup: dict,
    post_lineup: dict,
    sold_player_id: int,
) -> dict:

    current_lookup = (
        get_selected_lookup(
            current_lineup
        )
    )

    post_lookup = (
        get_selected_lookup(
            post_lineup
        )
    )

    current_ids = set(
        current_lookup
    )

    post_ids = set(
        post_lookup
    )

    entered_ids = sorted(
        post_ids
        -
        current_ids
    )

    exited_ids = sorted(
        current_ids
        -
        post_ids
    )

    sold_player_id = safe_int(
        sold_player_id
    )

    incoming = []

    for player_id in entered_ids:

        item = (
            post_lookup.get(
                player_id,
                {}
            )
            or {}
        )

        incoming.append(
            {
                "id":
                    player_id,

                "name":
                    get_player_name(
                        snapshot,
                        player_id,
                    ),

                "position":
                    get_player_position(
                        snapshot,
                        player_id,
                    ),

                "quality_score":
                    extract_player_quality_score(
                        snapshot=
                            snapshot,

                        lineup_item=
                            item,

                        player_id=
                            player_id,
                    ),
            }
        )

    outgoing_item = (
        current_lookup.get(
            sold_player_id,
            {}
        )
        or {}
    )

    sold_quality = (
        extract_player_quality_score(
            snapshot=
                snapshot,

            lineup_item=
                outgoing_item,

            player_id=
                sold_player_id,
        )
    )

    incoming_quality = None

    available_scores = [
        safe_float(
            item.get(
                "quality_score"
            )
        )
        for item
        in incoming
        if item.get(
            "quality_score"
        )
        is not None
    ]

    if available_scores:

        incoming_quality = max(
            available_scores
        )

    quality_loss = None

    if (
        sold_quality
        is not None
        and
        incoming_quality
        is not None
    ):

        quality_loss = round(
            max(
                sold_quality
                -
                incoming_quality,
                0.0,
            ),
            1,
        )

    return {
        "sold_player_id":
            sold_player_id,

        "sold_player_name":
            get_player_name(
                snapshot,
                sold_player_id,
            ),

        "entered_player_ids":
            entered_ids,

        "exited_player_ids":
            exited_ids,

        "incoming_players":
            incoming,

        "sold_quality_score":
            sold_quality,

        "incoming_quality_score":
            incoming_quality,

        "quality_loss_score":
            quality_loss,

        "formation_before":
            (
                current_lineup.get(
                    "formation_name"
                )
                or
                current_lineup.get(
                    "formation"
                )
            ),

        "formation_after":
            (
                post_lineup.get(
                    "formation_name"
                )
                or
                post_lineup.get(
                    "formation"
                )
            ),
    }


def get_player_position(
    snapshot: dict,
    player_id: int,
) -> int | None:

    player_id = safe_int(
        player_id
    )

    for item in (
        snapshot.get(
            "my_team",
            [],
        )
        or []
    ):

        if safe_int(
            item.get(
                "id"
            )
        ) == player_id:

            value = item.get(
                "position"
            )

            if value is not None:
                return safe_int(
                    value
                )

    catalog = (
        snapshot.get(
            "catalog",
            {},
        )
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

    player = (
        catalog.get(
            str(
                player_id
            ),
            {},
        )
        or {}
    )

    value = player.get(
        "position"
    )

    if value is None:
        return None

    return safe_int(
        value
    )


def simulate_lineup_without_players(
    snapshot: dict,
    player_ids: set[int] | list[int] | tuple[int, ...],
) -> dict:
    """
    Simula literalmente la plantilla sin esos jugadores y vuelve
    a ejecutar el lineup_engine existente.
    """

    removed_ids = {
        safe_int(
            value
        )
        for value
        in player_ids
        if safe_int(
            value
        ) > 0
    }

    simulated = deepcopy(
        snapshot
    )

    simulated[
        "my_team"
    ] = [
        player
        for player
        in (
            snapshot.get(
                "my_team",
                [],
            )
            or []
        )
        if safe_int(
            player.get(
                "id"
            )
        )
        not in removed_ids
    ]

    lineup = (
        build_lineup(
            simulated
        )
        or {}
    )

    playable_count = safe_int(
        lineup.get(
            "playable_count",
            len(
                lineup.get(
                    "selected",
                    [],
                )
                or []
            ),
        )
    )

    return {
        "removed_player_ids":
            sorted(
                removed_ids
            ),

        "playable_count":
            playable_count,

        "missing":
            max(
                11
                -
                playable_count,
                0,
            ),

        "complete":
            playable_count
            >= 11,

        "formation":
            lineup.get(
                "formation_name"
            ),

        "shortages":
            lineup.get(
                "matchday_shortages",
                {},
            )
            or {},

        "selected_ids":
            sorted(
                get_lineup_player_ids(
                    lineup
                )
            ),

        "lineup":
            lineup,
    }


def build_viable_market_replacements(
    snapshot: dict,
) -> dict[int, list[dict]]:
    """
    Usa Recommendation Engine, no solo presencia bruta en mercado.
    Un candidato >=55 se considera razonablemente util; no significa
    que la compra este garantizada.
    """

    try:
        recommendations = (
            generate_recommendations(
                snapshot
            )
            or []
        )
    except Exception:
        recommendations = []

    result: dict[int, list[dict]] = {
        1: [],
        2: [],
        3: [],
        4: [],
    }

    for player in recommendations:

        position = safe_int(
            player.get(
                "position"
            )
        )

        final_score = safe_float(
            player.get(
                "final_score"
            )
        )

        has_game = bool(
            player.get(
                "has_current_round_game",
                True,
            )
        )

        if (
            position
            not in result
            or
            final_score < 55
            or
            not has_game
        ):
            continue

        result[
            position
        ].append(
            {
                "id":
                    safe_int(
                        player.get(
                            "id"
                        )
                    ),

                "name":
                    player.get(
                        "name"
                    ),

                "position":
                    position,

                "final_score":
                    round(
                        final_score,
                        1,
                    ),

                "market_price":
                    safe_int(
                        player.get(
                            "market_price"
                        )
                    ),

                "status":
                    player.get(
                        "status"
                    ),
            }
        )

    for candidates in result.values():

        candidates.sort(
            key=lambda item:
                item[
                    "final_score"
                ],
            reverse=True,
        )

    return result



def classify_replacement_after_sale(
    *,
    snapshot: dict,
    player_id: int,
    current_lineup: dict | None = None,
    viable_market: dict[int, list[dict]] | None = None,
) -> dict:

    current_lineup = (
        current_lineup
        or
        build_current_lineup(
            snapshot
        )
    )

    current_ids = (
        get_lineup_player_ids(
            current_lineup
        )
    )

    player_id = safe_int(
        player_id
    )

    in_lineup = (
        player_id
        in current_ids
    )

    current_playable_count = safe_int(
        current_lineup.get(
            "playable_count",
            len(
                current_lineup.get(
                    "selected",
                    [],
                )
                or []
            ),
        )
    )

    position = (
        get_player_position(
            snapshot,
            player_id,
        )
    )

    if not in_lineup:

        return {
            "player_id":
                player_id,

            "player_name":
                get_player_name(
                    snapshot,
                    player_id,
                ),

            "in_lineup":
                False,

            "replacement_status":
                "NOT_NEEDED",

            "replacement_source":
                "NONE",

            "pre_sale_playable_count":
                current_playable_count,

            "post_sale_playable_count":
                current_playable_count,

            "post_sale_missing":
                max(
                    11
                    -
                    current_playable_count,
                    0,
                ),

            "position":
                position,

            "formation_before":
                (
                    current_lineup.get(
                        "formation_name"
                    )
                    or
                    current_lineup.get(
                        "formation"
                    )
                ),

            "formation_after":
                (
                    current_lineup.get(
                        "formation_name"
                    )
                    or
                    current_lineup.get(
                        "formation"
                    )
                ),

            "incoming_players":
                [],

            "quality_loss_score":
                0.0,

            "viable_market_candidates":
                [],
        }

    simulation = (
        simulate_lineup_without_players(
            snapshot,
            {
                player_id,
            },
        )
    )

    post_lineup = (
        simulation.get(
            "lineup",
            {},
        )
        or {}
    )

    change = (
        build_replacement_change(
            snapshot=
                snapshot,

            current_lineup=
                current_lineup,

            post_lineup=
                post_lineup,

            sold_player_id=
                player_id,
        )
    )

    sporting = (
        build_sporting_opportunity_cost(
            current_lineup=
                current_lineup,

            post_lineup=
                post_lineup,
        )
    )

    viable_market = (
        viable_market
        or
        build_viable_market_replacements(
            snapshot
        )
    )

    market_candidates = (
        viable_market.get(
            safe_int(
                position
            ),
            [],
        )
        or []
    )

    if simulation[
        "complete"
    ]:

        status = "SECURED_BY_BENCH"
        source = "BENCH"

    elif len(
        market_candidates
    ) >= 2:

        status = "AVAILABLE_ON_MARKET"
        source = "MARKET"

    elif len(
        market_candidates
    ) == 1:

        status = "UNCERTAIN_ON_MARKET"
        source = "MARKET"

    else:

        status = "NONE"
        source = "NONE"

    return {
        "player_id":
            player_id,

        "player_name":
            get_player_name(
                snapshot,
                player_id,
            ),

        "in_lineup":
            True,

        "replacement_status":
            status,

        "replacement_source":
            source,

        "pre_sale_playable_count":
            current_playable_count,

        "post_sale_playable_count":
            simulation[
                "playable_count"
            ],

        "post_sale_missing":
            simulation[
                "missing"
            ],

        "position":
            position,

        "shortages":
            simulation[
                "shortages"
            ],

        "formation_before":
            change.get(
                "formation_before"
            ),

        "formation_after":
            change.get(
                "formation_after"
            ),

        "incoming_players":
            change.get(
                "incoming_players",
                [],
            ),

        "entered_player_ids":
            change.get(
                "entered_player_ids",
                [],
            ),

        "exited_player_ids":
            change.get(
                "exited_player_ids",
                [],
            ),

        "sold_quality_score":
            change.get(
                "sold_quality_score"
            ),

        "incoming_quality_score":
            change.get(
                "incoming_quality_score"
            ),

        "quality_loss_score":
            change.get(
                "quality_loss_score"
            ),

        "sporting_opportunity_cost":
            sporting,

        "lineup_score_before":
            sporting.get(
                "lineup_score_before"
            ),

        "lineup_score_after":
            sporting.get(
                "lineup_score_after"
            ),

        "lineup_score_loss":
            sporting.get(
                "lineup_score_loss"
            ),

        "lineup_score_loss_percent":
            sporting.get(
                "lineup_score_loss_percent"
            ),

        "viable_market_candidates":
            market_candidates[
                :5
            ],
    }



def build_offer_replacement_lookup(
    *,
    snapshot: dict,
    offers: list[dict],
) -> dict[int, dict]:

    current_lineup = (
        build_current_lineup(
            snapshot
        )
    )

    viable_market = (
        build_viable_market_replacements(
            snapshot
        )
    )

    result = {}

    for offer in offers:

        player_id = safe_int(
            offer.get(
                "player_id"
            )
        )

        if player_id <= 0:
            continue

        result[
            player_id
        ] = (
            classify_replacement_after_sale(
                snapshot=
                    snapshot,

                player_id=
                    player_id,

                current_lineup=
                    current_lineup,

                viable_market=
                    viable_market,
            )
        )

    return result


def _build_portfolio_scenario(
    *,
    snapshot: dict,
    manager_decisions: list[dict],
    amount_mode: str,
) -> dict:

    balance = safe_int(
        (
            snapshot.get(
                "market",
                {},
            )
            .get(
                "status",
                {},
            )
            or {}
        ).get(
            "balance"
        )
    )

    combos = []

    current_lineup = (
        build_current_lineup(
            snapshot
        )
    )

    for count in range(
        1,
        len(
            manager_decisions
        )
        + 1,
    ):

        for combo in combinations(
            manager_decisions,
            count,
        ):

            player_ids = {
                safe_int(
                    item.get(
                        "player_id"
                    )
                )
                for item
                in combo
            }

            amount_rows = []

            for item in combo:

                current_amount = safe_int(
                    item.get(
                        "amount"
                    )
                )

                competitive = (
                    item.get(
                        "competitive_observer"
                    )
                    or {}
                )

                strategic_amount = (
                    safe_int(
                        competitive.get(
                            "counter_amount"
                        )
                    )
                    or
                    safe_int(
                        competitive.get(
                            "strategic_sell_price"
                        )
                    )
                    or
                    current_amount
                )

                selected_amount = (
                    strategic_amount
                    if amount_mode
                    ==
                    "STRATEGIC"
                    else current_amount
                )

                amount_rows.append(
                    {
                        "player_id":
                            safe_int(
                                item.get(
                                    "player_id"
                                )
                            ),

                        "player_name":
                            item.get(
                                "player_name"
                            ),

                        "current_amount":
                            current_amount,

                        "strategic_amount":
                            strategic_amount,

                        "selected_amount":
                            selected_amount,
                    }
                )

            total_amount = sum(
                row[
                    "selected_amount"
                ]
                for row
                in amount_rows
            )

            current_total = sum(
                row[
                    "current_amount"
                ]
                for row
                in amount_rows
            )

            strategic_total = sum(
                row[
                    "strategic_amount"
                ]
                for row
                in amount_rows
            )

            simulation = (
                simulate_lineup_without_players(
                    snapshot,
                    player_ids,
                )
            )

            post_balance = (
                balance
                +
                total_amount
            )

            competitive_damage = sum(
                safe_float(
                    (
                        item.get(
                            "competitive_observer"
                        )
                        or {}
                    ).get(
                        "rival_reinforcement_score"
                    )
                )
                for item
                in combo
            )

            market_value_sold = sum(
                safe_int(
                    item.get(
                        "market_value"
                    )
                )
                for item
                in combo
            )

            excess_cash = (
                max(
                    post_balance,
                    0,
                )
                if balance < 0
                else total_amount
            )

            names = [
                str(
                    item.get(
                        "player_name"
                    )
                    or
                    item.get(
                        "player_id"
                    )
                )
                for item
                in combo
            ]

            post_lineup = (
                simulation.get(
                    "lineup",
                    {},
                )
                or {}
            )

            current_selected_ids = (
                get_lineup_player_ids(
                    current_lineup
                )
            )

            post_selected_ids = (
                get_lineup_player_ids(
                    post_lineup
                )
            )

            combo_incoming_ids = sorted(
                post_selected_ids
                -
                current_selected_ids
            )

            combo_incoming_players = [
                {
                    "id":
                        incoming_id,

                    "name":
                        get_player_name(
                            snapshot,
                            incoming_id,
                        ),

                    "position":
                        get_player_position(
                            snapshot,
                            incoming_id,
                        ),
                }

                for incoming_id
                in combo_incoming_ids
            ]

            sporting = (
                build_sporting_opportunity_cost(
                    current_lineup=
                        current_lineup,

                    post_lineup=
                        post_lineup,
                )
            )

            combos.append(
                {
                    "amount_mode":
                        amount_mode,

                    "player_ids":
                        sorted(
                            player_ids
                        ),

                    "player_names":
                        names,

                    "offer_ids":
                        [
                            item.get(
                                "offer_id"
                            )
                            for item
                            in combo
                        ],

                    "sold_count":
                        count,

                    "amounts":
                        amount_rows,

                    "current_total":
                        current_total,

                    "strategic_total":
                        strategic_total,

                    "total_amount":
                        total_amount,

                    "market_value_sold":
                        market_value_sold,

                    "post_balance":
                        post_balance,

                    "restores_solvency":
                        post_balance
                        >= 0,

                    "excess_cash":
                        excess_cash,

                    "playable_count":
                        simulation[
                            "playable_count"
                        ],

                    "missing":
                        simulation[
                            "missing"
                        ],

                    "lineup_complete":
                        simulation[
                            "complete"
                        ],

                    "shortages":
                        simulation[
                            "shortages"
                        ],

                    "formation_before":
                        (
                            current_lineup.get(
                                "formation_name"
                            )
                            or
                            current_lineup.get(
                                "formation"
                            )
                        ),

                    "formation_after":
                        (
                            post_lineup.get(
                                "formation_name"
                            )
                            or
                            post_lineup.get(
                                "formation"
                            )
                        ),

                    "incoming_players":
                        combo_incoming_players,

                    "competitive_damage":
                        round(
                            competitive_damage,
                            1,
                        ),

                    "sporting_opportunity_cost":
                        sporting,

                    "lineup_score_before":
                        sporting.get(
                            "lineup_score_before"
                        ),

                    "lineup_score_after":
                        sporting.get(
                            "lineup_score_after"
                        ),

                    "lineup_score_loss":
                        sporting.get(
                            "lineup_score_loss"
                        ),

                    "lineup_score_loss_percent":
                        sporting.get(
                            "lineup_score_loss_percent"
                        ),

                    "sporting_ranking_cost":
                        sporting.get(
                            "ranking_cost"
                        ),
                }
            )

    combos.sort(
        key=lambda item: (
            not item[
                "restores_solvency"
            ],

            not item[
                "lineup_complete"
            ],

            item.get(
                "sporting_ranking_cost",
                0.0,
            ),

            item[
                "sold_count"
            ],

            item[
                "competitive_damage"
            ],

            item[
                "excess_cash"
            ],

            -item[
                "total_amount"
            ],
        )
    )

    solvency_combinations = [
        item
        for item
        in combos
        if item[
            "restores_solvency"
        ]
    ]

    recommended = (
        solvency_combinations[
            0
        ]
        if solvency_combinations
        else (
            combos[
                0
            ]
            if combos
            else None
        )
    )

    return {
        "amount_mode":
            amount_mode,

        "balance":
            balance,

        "deficit":
            max(
                -balance,
                0,
            ),

        "combinations":
            combos,

        "solvency_combinations":
            solvency_combinations,

        "recommended":
            recommended,
    }


def build_competitive_offer_portfolio(
    *,
    snapshot: dict,
    decisions: list[dict],
) -> dict:
    """
    V1.4 publica dos planes:

    CURRENT:
        liquidez si Pepe aceptase las ofertas rivales actuales.

    STRATEGIC:
        liquidez objetivo si los rivales aceptan las contraofertas
        / precios estrategicos calculados por Competitive Engine.

    CURRENT no autoriza vender barato. Solo mide la salida inmediata.
    """

    manager_decisions = [
        item
        for item
        in (
            decisions
            or []
        )
        if (
            item.get(
                "counterparty_type"
            )
            ==
            "MANAGER"
            and
            safe_int(
                item.get(
                    "amount"
                )
            )
            > 0
            and
            safe_int(
                item.get(
                    "player_id"
                )
            )
            > 0
            and
            item.get(
                "decision"
            )
            !=
            "NEVER_SELL"
        )
    ]

    balance = safe_int(
        (
            snapshot.get(
                "market",
                {},
            )
            .get(
                "status",
                {},
            )
            or {}
        ).get(
            "balance"
        )
    )

    if not manager_decisions:

        return {
            "observer_only":
                OBSERVER_ONLY,

            "balance":
                balance,

            "deficit":
                max(
                    -balance,
                    0,
                ),

            "offer_count":
                0,

            "current":
                {
                    "amount_mode":
                        "CURRENT",

                    "combinations":
                        [],

                    "solvency_combinations":
                        [],

                    "recommended":
                        None,
                },

            "strategic":
                {
                    "amount_mode":
                        "STRATEGIC",

                    "combinations":
                        [],

                    "solvency_combinations":
                        [],

                    "recommended":
                        None,
                },

            "recommended":
                None,
        }

    current = (
        _build_portfolio_scenario(
            snapshot=
                snapshot,

            manager_decisions=
                manager_decisions,

            amount_mode=
                "CURRENT",
        )
    )

    strategic = (
        _build_portfolio_scenario(
            snapshot=
                snapshot,

            manager_decisions=
                manager_decisions,

            amount_mode=
                "STRATEGIC",
        )
    )

    recommended = (
        strategic.get(
            "recommended"
        )
        or
        current.get(
            "recommended"
        )
    )

    return {
        "observer_only":
            OBSERVER_ONLY,

        "balance":
            balance,

        "deficit":
            max(
                -balance,
                0,
            ),

        "offer_count":
            len(
                manager_decisions
            ),

        "current":
            current,

        "strategic":
            strategic,

        # Compatibilidad con V1.3:
        "combinations":
            current.get(
                "combinations",
                [],
            ),

        "solvency_combinations":
            current.get(
                "solvency_combinations",
                [],
            ),

        "recommended":
            recommended,
    }
