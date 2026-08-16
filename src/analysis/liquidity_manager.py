from itertools import combinations

from src.analysis.lineup_engine import (
    build_lineup,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sale_price_engine import (
    calculate_sale_price,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.analysis.strategic_target_engine import (
    build_strategic_target_board,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================


FRANCHISE_PROTECTION_THRESHOLD = 70

# Para jugadores que estratégicamente NO queremos vender,
# los publicamos igualmente por liquidez, pero con un precio
# público alto.
PROTECTED_LISTING_MULTIPLIER = 1.50

# Jugadores normales que tampoco son candidatos claros
# de venta.
NORMAL_LISTING_MULTIPLIER = 1.20

ROUND_STEP = 10_000


# ============================================================
# UTILIDADES
# ============================================================


def round_price(
    value: int,
    step: int = ROUND_STEP,
) -> int:

    if value <= 0:
        return 0

    return (
        (
            value
            + step
            - 1
        )
        // step
    ) * step


def get_my_team_lookup(
    snapshot: dict,
) -> dict[int, dict]:

    return {
        int(
            player[
                "id"
            ]
        ):
            player

        for player
        in snapshot.get(
            "my_team",
            []
        )
    }


# ============================================================
# JUGADORES YA PUBLICADOS
# ============================================================


def get_currently_listed_players(
    snapshot: dict,
) -> dict[int, dict]:
    """
    Detecta qué jugadores de NUESTRA plantilla
    aparecen actualmente en market.sales.

    Como un jugador de nuestra plantilla no puede estar
    simultáneamente publicado por otro propietario,
    basta cruzar player_id con my_team.
    """

    team = (
        get_my_team_lookup(
            snapshot
        )
    )

    listed = {}

    sales = (
        snapshot
        .get(
            "market",
            {}
        )
        .get(
            "sales",
            []
        )
        or []
    )

    for sale in sales:

        player_data = (
            sale.get(
                "player",
                {}
            )
            or {}
        )

        player_id = (
            player_data.get(
                "id"
            )
        )

        if player_id is None:
            continue

        player_id = int(
            player_id
        )

        if player_id not in team:
            continue

        listed[
            player_id
        ] = {
            "player_id":
                player_id,

            "price":
                int(
                    sale.get(
                        "price",
                        0,
                    )
                    or 0
                ),

            "date":
                sale.get(
                    "date"
                ),

            "until":
                sale.get(
                    "until"
                ),

            "raw":
                sale,
        }

    return listed


# ============================================================
# STRATEGIC LOOKUP
# ============================================================


def build_strategic_lookup(
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


# ============================================================
# PROTECCIÓN
# ============================================================


def classify_liquidity_protection(
    player: dict,
    sale_analysis: dict,
    strategic: dict,
    selected_ids: set[int],
) -> dict:

    player_id = int(
        player[
            "id"
        ]
    )

    franchise_score = float(
        strategic.get(
            "franchise_score",
            0,
        )
        or 0
    )

    strategic_score = float(
        strategic.get(
            "strategic_score",
            0,
        )
        or 0
    )

    sale_score = float(
        sale_analysis.get(
            "sale_score",
            0,
        )
        or 0
    )

    in_lineup = (
        player_id
        in selected_ids
    )

    reasons = []

    protection_score = 0.0

    # ========================================================
    # FRANCHISE
    # ========================================================

    if (
        franchise_score
        >= FRANCHISE_PROTECTION_THRESHOLD
    ):

        protection_score += 100

        reasons.append(
            "Jugador Franchise"
        )

    # ========================================================
    # XI
    # ========================================================

    if in_lineup:

        protection_score += 35

        reasons.append(
            "Forma parte del XI óptimo"
        )

    # ========================================================
    # STRATEGIC
    # ========================================================

    protection_score += (
        strategic_score
        * 0.30
    )

    # ========================================================
    # SALE SCORE
    # ========================================================

    # Cuanto más vendible lo considera Sales Analyzer,
    # menor protección.
    protection_score -= (
        sale_score
        * 0.45
    )

    protection_score = max(
        protection_score,
        0,
    )

    # ========================================================
    # CLASIFICACIÓN
    # ========================================================

    if (
        franchise_score
        >= FRANCHISE_PROTECTION_THRESHOLD
    ):

        protection = (
            "NEVER_AUTO_SELL"
        )

    elif protection_score >= 50:

        protection = (
            "PROTECTED"
        )

    elif sale_score >= 60:

        protection = (
            "SELLABLE"
        )

    elif sale_score >= 40:

        protection = (
            "CONDITIONAL"
        )

    else:

        protection = (
            "NORMAL"
        )

    return {
        "protection":
            protection,

        "protection_score":
            round(
                protection_score,
                2,
            ),

        "franchise_score":
            franchise_score,

        "strategic_score":
            strategic_score,

        "in_lineup":
            in_lineup,

        "reasons":
            reasons,
    }


# ============================================================
# PRECIO DE PUBLICACIÓN
# ============================================================


def calculate_liquidity_listing_price(
    player: dict,
    sale_analysis: dict,
    protection: dict,
) -> dict:
    """
    IMPORTANTE:

    Publicar != vender.

    Para jugadores que ya eran candidatos a venta,
    reutilizamos Sale Price Engine.

    Para jugadores importantes, los publicamos con prima
    elevada únicamente para mantener abierta la posibilidad
    de recibir ofertas.
    """

    market_value = int(
        player.get(
            "price",
            0,
        )
        or 0
    )

    if market_value <= 0:

        return {
            "price":
                0,

            "strategy":
                "INVALID_PRICE",
        }

    sale_pricing = (
        calculate_sale_price(
            sale_analysis
        )
    )

    protection_class = (
        protection[
            "protection"
        ]
    )

    # ========================================================
    # VENTA REAL
    # ========================================================

    if sale_pricing.get(
        "should_list",
        False,
    ):

        recommended = (
            sale_pricing.get(
                "recommended_price"
            )
        )

        if recommended:

            return {
                "price":
                    int(
                        recommended
                    ),

                "strategy":
                    sale_pricing.get(
                        "strategy",
                        "SALE_ENGINE",
                    ),

                "sale_engine":
                    True,
            }

    # ========================================================
    # FRANCHISE / PROTECTED
    # ========================================================

    if protection_class in {
        "NEVER_AUTO_SELL",
        "PROTECTED",
    }:

        price = round_price(
            int(
                market_value
                * PROTECTED_LISTING_MULTIPLIER
            )
        )

        return {
            "price":
                price,

            "strategy":
                "LIQUIDITY_ONLY_PROTECTED",

            "sale_engine":
                False,
        }

    # ========================================================
    # RESTO
    # ========================================================

    price = round_price(
        int(
            market_value
            * NORMAL_LISTING_MULTIPLIER
        )
    )

    return {
        "price":
            price,

        "strategy":
            "LIQUIDITY_ONLY",

        "sale_engine":
            False,
    }


# ============================================================
# BOARD DE PLANTILLA
# ============================================================


def build_liquidity_roster_board(
    snapshot: dict,
) -> list[dict]:

    team = (
        snapshot.get(
            "my_team",
            []
        )
    )

    lineup = (
        build_lineup(
            snapshot
        )
    )

    selected_ids = {
        int(
            player[
                "id"
            ]
        )

        for player
        in lineup.get(
            "selected",
            []
        )
    }

    sales = (
        analyze_sales(
            snapshot
        )
    )

    sale_lookup = {
        int(
            player[
                "id"
            ]
        ):
            player

        for player
        in sales
    }

    strategic_lookup = (
        build_strategic_lookup(
            snapshot
        )
    )

    listed_lookup = (
        get_currently_listed_players(
            snapshot
        )
    )

    results = []

    for player in team:

        player_id = int(
            player[
                "id"
            ]
        )

        sale_analysis = (
            sale_lookup.get(
                player_id,
                {
                    "id":
                        player_id,

                    "name":
                        player.get(
                            "name"
                        ),

                    "price":
                        player.get(
                            "price",
                            0,
                        ),

                    "sale_score":
                        0,

                    "in_lineup":
                        (
                            player_id
                            in selected_ids
                        ),
                },
            )
        )

        strategic = (
            strategic_lookup.get(
                player_id,
                {}
            )
        )

        protection = (
            classify_liquidity_protection(
                player=
                    player,

                sale_analysis=
                    sale_analysis,

                strategic=
                    strategic,

                selected_ids=
                    selected_ids,
            )
        )

        pricing = (
            calculate_liquidity_listing_price(
                player=
                    player,

                sale_analysis=
                    sale_analysis,

                protection=
                    protection,
            )
        )

        current_listing = (
            listed_lookup.get(
                player_id
            )
        )

        currently_listed = (
            current_listing
            is not None
        )

        results.append(
            {
                "id":
                    player_id,

                "name":
                    player.get(
                        "name"
                    ),

                "position":
                    player.get(
                        "position"
                    ),

                "market_value":
                    int(
                        player.get(
                            "price",
                            0,
                        )
                        or 0
                    ),

                "price_increment":
                    int(
                        player.get(
                            "priceIncrement",
                            0,
                        )
                        or 0
                    ),

                "sale_score":
                    float(
                        sale_analysis.get(
                            "sale_score",
                            0,
                        )
                        or 0
                    ),

                "sale_recommendation":
                    sale_analysis.get(
                        "recommendation"
                    ),

                **protection,

                "listing_price":
                    pricing[
                        "price"
                    ],

                "listing_strategy":
                    pricing[
                        "strategy"
                    ],

                "currently_listed":
                    currently_listed,

                "current_listing":
                    current_listing,

                "listing_action":
                    (
                        "NO_ACTION"
                        if currently_listed
                        else "LIST_FOR_LIQUIDITY"
                    ),
            }
        )

    return results


# ============================================================
# OFERTAS RECIBIDAS
# ============================================================


def build_incoming_offer_candidates(
    snapshot: dict,
    roster_board: list[dict],
) -> list[dict]:

    board = (
        build_offer_board(
            snapshot
        )
    )

    roster_lookup = {
        int(
            player[
                "id"
            ]
        ):
            player

        for player
        in roster_board
    }

    results = []

    for offer in board.get(
        "incoming",
        []
    ):

        if offer.get(
            "status"
        ) != "waiting":

            continue

        player_ids = (
            offer.get(
                "player_ids",
                []
            )
            or []
        )

        # En compraventa normal debería ser uno.
        for player_id in player_ids:

            player_id = int(
                player_id
            )

            roster = (
                roster_lookup.get(
                    player_id
                )
            )

            if roster is None:
                continue

            amount = int(
                offer.get(
                    "amount",
                    0,
                )
                or 0
            )

            if amount <= 0:
                continue

            market_value = int(
                roster[
                    "market_value"
                ]
            )

            delta = (
                amount
                - market_value
            )

            if market_value > 0:

                delta_percent = (
                    delta
                    / market_value
                ) * 100

            else:

                delta_percent = 0.0

            protection = (
                roster[
                    "protection"
                ]
            )

            # =================================================
            # COSTE DE VENTA
            # =================================================

            if protection == (
                "NEVER_AUTO_SELL"
            ):

                sell_damage = 10_000.0

            else:

                sell_damage = (
                    roster[
                        "protection_score"
                    ]
                    + max(
                        100
                        - roster[
                            "sale_score"
                        ],
                        0,
                    )
                    * 0.30
                )

            # Más dinero por menos daño es mejor.
            efficiency = (
                amount
                / max(
                    sell_damage,
                    1,
                )
            )

            results.append(
                {
                    "offer_id":
                        offer.get(
                            "offer_id",
                            offer.get(
                                "id"
                            ),
                        ),

                    "player_id":
                        player_id,

                    "player_name":
                        roster[
                            "name"
                        ],

                    "amount":
                        amount,

                    "market_value":
                        market_value,

                    "delta":
                        delta,

                    "delta_percent":
                        round(
                            delta_percent,
                            2,
                        ),

                    "sale_score":
                        roster[
                            "sale_score"
                        ],

                    "protection":
                        protection,

                    "protection_score":
                        roster[
                            "protection_score"
                        ],

                    "sell_damage":
                        round(
                            sell_damage,
                            2,
                        ),

                    "efficiency":
                        round(
                            efficiency,
                            2,
                        ),

                    "raw_offer":
                        offer,
                }
            )

    results.sort(
        key=lambda item: (
            item[
                "protection"
            ]
            == "NEVER_AUTO_SELL",

            item[
                "sell_damage"
            ],

            -item[
                "amount"
            ],
        )
    )

    return results


# ============================================================
# PLAN DE RECUPERACIÓN
# ============================================================


def build_recovery_plan(
    balance: int,
    offers: list[dict],
    guardrail: dict | None = None,
) -> dict:

    if balance >= 0:

        return {
            "needed":
                False,

            "deficit":
                0,

            "possible":
                True,

            "selected":
                [],

            "recovered":
                0,

            "excess":
                0,

            "reason":
                "El saldo actual no es negativo.",

            "guardrail_applied":
                guardrail is not None,

            "rejected_by_guardrail":
                [],
        }

    deficit = abs(
        int(
            balance
        )
    )

    # Nunca usamos Franchise automáticamente.
    eligible = [
        offer

        for offer in offers

        if offer[
            "protection"
        ]
        != "NEVER_AUTO_SELL"
    ]

    best = None

    rejected_by_guardrail = []

    # La plantilla es pequeña; combinations es perfectamente
    # razonable y nos permite encontrar la combinación exacta.
    for count in range(
        1,
        len(
            eligible
        )
        + 1,
    ):

        for combo in combinations(
            eligible,
            count,
        ):

            # Dos ofertas por el mismo jugador no son dos ventas.
            # Sumarlas inflaba lo recuperado y hacia pasar planes
            # que no recaudaban lo que decian.
            ids_combo = [
                int(item.get("player_id") or 0)
                for item in combo
            ]

            if len(set(ids_combo)) != len(ids_combo):
                continue

            # Guardarrail posicional.
            #
            # Antes el unico filtro era descartar franchise, asi
            # que vender a los dos porteros en el mismo ciclo era
            # una combinacion legal para este bucle. Cada venta
            # por separado pasaba todos los controles; el problema
            # solo aparece mirandolas juntas, que es justo lo que
            # hace validate_sale_set.
            if guardrail is not None:

                veredicto = validate_sale_set(
                    guardrail,
                    ids_combo,
                )

                if not veredicto.get("ok"):
                    rejected_by_guardrail.append(
                        {
                            "player_ids": ids_combo,
                            "reason": veredicto.get("reason"),
                        }
                    )
                    continue

            recovered = sum(
                item[
                    "amount"
                ]

                for item
                in combo
            )

            if recovered < deficit:
                continue

            damage = sum(
                item[
                    "sell_damage"
                ]

                for item
                in combo
            )

            excess = (
                recovered
                - deficit
            )

            # Priorizamos:
            # 1. menor daño
            # 2. menos jugadores
            # 3. menor exceso innecesario
            key = (
                damage,
                count,
                excess,
            )

            if (
                best is None
                or key
                < best[
                    "key"
                ]
            ):

                best = {
                    "key":
                        key,

                    "selected":
                        list(
                            combo
                        ),

                    "recovered":
                        recovered,

                    "damage":
                        damage,

                    "excess":
                        excess,
                }

    if best is None:

        potential = sum(
            item[
                "amount"
            ]

            for item
            in eligible
        )

        return {
            "needed":
                True,

            "deficit":
                deficit,

            "possible":
                False,

            "selected":
                [],

            "recovered":
                0,

            "potential":
                potential,

            "excess":
                0,

            "reason": (
                "Las ofertas recibidas disponibles "
                "no cubren todavía el déficit."
                + (
                    f" Se descartaron "
                    f"{len(rejected_by_guardrail)} combinaciones "
                    f"por dejar una posicion sin cubrir."
                    if rejected_by_guardrail
                    else ""
                )
            ),

            "guardrail_applied":
                guardrail is not None,

            "rejected_by_guardrail":
                rejected_by_guardrail,
        }

    return {
        "needed":
            True,

        "deficit":
            deficit,

        "possible":
            True,

        "selected":
            best[
                "selected"
            ],

        "recovered":
            best[
                "recovered"
            ],

        "damage":
            round(
                best[
                    "damage"
                ],
                2,
            ),

        "excess":
            best[
                "excess"
            ],

        "reason": (
            "Existe una combinación de ofertas "
            "capaz de recuperar solvencia sin dejar "
            "ninguna posición por debajo del mínimo."
        ),

        "guardrail_applied":
            guardrail is not None,

        "rejected_by_guardrail":
            rejected_by_guardrail,
    }


# ============================================================
# ESTADO GLOBAL DE LIQUIDEZ
# ============================================================


def build_liquidity_state(
    snapshot: dict,
) -> dict:

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    roster = (
        build_liquidity_roster_board(
            snapshot
        )
    )

    incoming = (
        build_incoming_offer_candidates(
            snapshot=
                snapshot,

            roster_board=
                roster,
        )
    )

    # El guardarrail se construye del mismo roster que ya
    # tenemos, asi que no cuesta nada, y se pasa al plan de
    # recuperacion para que no pueda elegir una combinacion que
    # deje una posicion sin cubrir.
    guardrail = (
        build_position_guardrail(
            roster
        )
    )

    recovery = (
        build_recovery_plan(
            balance=
                solvency[
                    "balance"
                ],

            offers=
                incoming,

            guardrail=
                guardrail,
        )
    )

    to_list = [
        player

        for player in roster

        if player[
            "listing_action"
        ]
        == "LIST_FOR_LIQUIDITY"
    ]

    listed = [
        player

        for player in roster

        if player[
            "currently_listed"
        ]
    ]

    protected = [
        player

        for player in roster

        if player[
            "protection"
        ]
        in {
            "NEVER_AUTO_SELL",
            "PROTECTED",
        }
    ]

    return {
        "balance":
            solvency[
                "balance"
            ],

        "solvency":
            solvency,

        "roster":
            roster,

        "listed":
            listed,

        "to_list":
            to_list,

        "protected":
            protected,

        "incoming_offers":
            incoming,

        "recovery":
            recovery,

        "position_guardrail":
            guardrail,

        "listing_count":
            len(
                listed
            ),

        "to_list_count":
            len(
                to_list
            ),

        "incoming_offer_count":
            len(
                incoming
            ),
    }