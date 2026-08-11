from __future__ import annotations

import copy

from collections import defaultdict
from datetime import datetime, timedelta

from src.analysis.computer_offer_reroll_engine import (
    now_utc,
    parse_datetime,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)


# ============================================================
# CONFIGURACION
# ============================================================

# Solo determina CUANDO ejecutar una aceptación que ya ha sido
# demostrada necesaria. No decide por sí mismo si vender.
ACCEPT_EXECUTION_MARGIN_HOURS = 6.0

# Ofertas con deadlines prácticamente simultáneos se consideran
# un mismo evento de caducidad.
EXPIRY_CLUSTER_TOLERANCE_MINUTES = 5


# ============================================================
# HELPERS
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


def resolve_offer_id(
    raw_offer: dict,
) -> int | None:

    for key in (
        "id",
        "offer_id",
    ):
        value = raw_offer.get(
            key
        )

        if value is None:
            continue

        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def get_offer_expiry(
    offer: dict,
) -> datetime | None:

    return parse_datetime(
        offer.get(
            "expires_at"
        )
        or offer.get(
            "until"
        )
    )


def get_real_deadline(
    solvency: dict,
) -> datetime | None:

    deadline = (
        solvency.get(
            "deadline",
            {},
        )
        or {}
    )

    return parse_datetime(
        deadline.get(
            "real_deadline"
        )
    )


def get_effective_accept_deadline(
    offer: dict,
    solvency: dict,
) -> datetime | None:
    """
    Hay que haber asegurado el dinero antes de:
    - caducar la oferta, o
    - T-15 real,
    lo que ocurra primero.
    """

    offer_expiry = (
        get_offer_expiry(
            offer
        )
    )

    real_deadline = (
        get_real_deadline(
            solvency
        )
    )

    candidates = [
        value
        for value in (
            offer_expiry,
            real_deadline,
        )
        if value is not None
    ]

    if not candidates:
        return None

    return min(
        candidates
    )


def calculate_hours_until(
    value: datetime | None,
) -> float | None:

    if value is None:
        return None

    return max(
        (
            value
            - now_utc()
        ).total_seconds()
        / 3600,
        0.0,
    )


def remove_offers_from_snapshot(
    snapshot: dict,
    offer_ids: set[int],
) -> tuple[dict, set[int]]:
    """
    Elimina ofertas SOLO de una copia en memoria.
    Nunca escribe en disco ni toca Biwenger.
    """

    simulated = copy.deepcopy(
        snapshot
    )

    market = (
        simulated.get(
            "market",
            {},
        )
        or {}
    )

    offers = (
        market.get(
            "offers",
            [],
        )
        or []
    )

    kept = []
    removed_ids = set()

    for raw_offer in offers:

        current_id = (
            resolve_offer_id(
                raw_offer
            )
        )

        if (
            current_id is not None
            and
            current_id in offer_ids
        ):
            removed_ids.add(
                current_id
            )
            continue

        kept.append(
            raw_offer
        )

    market[
        "offers"
    ] = kept

    simulated[
        "market"
    ] = market

    return (
        simulated,
        removed_ids,
    )


def simulate_offer_loss_set(
    snapshot: dict,
    offer_ids: set[int],
) -> dict:

    simulated, removed_ids = (
        remove_offers_from_snapshot(
            snapshot=
                snapshot,

            offer_ids=
                offer_ids,
        )
    )

    missing = (
        set(
            offer_ids
        )
        - removed_ids
    )

    if missing:

        return {
            "valid":
                False,

            "reason":
                f"No se encontraron ofertas: {sorted(missing)}",

            "removed_ids":
                sorted(
                    removed_ids
                ),

            "guaranteed_after_loss":
                False,

            "solvency_after_loss":
                None,
        }

    solvency_after = (
        build_solvency_state(
            simulated
        )
    )

    guarantee = (
        solvency_after.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    return {
        "valid":
            True,

        "reason":
            "SOLVENCY_GUARANTEE recalculada tras eliminar "
            "simultáneamente el conjunto de ofertas.",

        "removed_ids":
            sorted(
                removed_ids
            ),

        "guaranteed_after_loss":
            bool(
                guarantee.get(
                    "guaranteed",
                    False,
                )
            ),

        "state_after_loss":
            guarantee.get(
                "state"
            ),

        "surplus_after_loss":
            safe_int(
                guarantee.get(
                    "guarantee_surplus"
                )
            ),

        "secured_after_loss":
            safe_int(
                guarantee.get(
                    "secured_liquidity"
                )
            ),

        "expected_after_loss":
            safe_int(
                guarantee.get(
                    "expected_liquidity"
                )
            ),

        "required_recovery":
            safe_int(
                guarantee.get(
                    "required_recovery"
                )
            ),

        "solvency_after_loss":
            solvency_after,
    }


# ============================================================
# CLUSTERS DE CADUCIDAD
# ============================================================


def cluster_offers_by_effective_deadline(
    offers: list[dict],
    solvency: dict,
) -> list[dict]:
    """
    Agrupa ofertas cuyos límites efectivos son prácticamente
    simultáneos. Esto evita el error de analizar individualmente
    tres ofertas que en realidad pueden desaparecer a la vez.
    """

    enriched = []

    for offer in offers:

        offer_id = (
            offer.get(
                "offer_id"
            )
        )

        if offer_id is None:
            continue

        effective_deadline = (
            get_effective_accept_deadline(
                offer=
                    offer,

                solvency=
                    solvency,
            )
        )

        enriched.append(
            {
                "offer":
                    offer,

                "offer_id":
                    int(
                        offer_id
                    ),

                "effective_deadline":
                    effective_deadline,
            }
        )

    enriched.sort(
        key=lambda item: (
            item[
                "effective_deadline"
            ]
            or datetime.max.replace(
                tzinfo=now_utc().tzinfo
            )
        )
    )

    clusters = []
    tolerance = timedelta(
        minutes=
            EXPIRY_CLUSTER_TOLERANCE_MINUTES
    )

    for item in enriched:

        deadline = (
            item[
                "effective_deadline"
            ]
        )

        if not clusters:

            clusters.append(
                {
                    "effective_deadline":
                        deadline,

                    "items":
                        [
                            item
                        ],
                }
            )
            continue

        previous = (
            clusters[
                -1
            ]
        )

        previous_deadline = (
            previous[
                "effective_deadline"
            ]
        )

        same_cluster = bool(
            deadline is not None
            and
            previous_deadline is not None
            and
            abs(
                deadline
                - previous_deadline
            )
            <= tolerance
        )

        if same_cluster:

            previous[
                "items"
            ].append(
                item
            )

        else:

            clusters.append(
                {
                    "effective_deadline":
                        deadline,

                    "items":
                        [
                            item
                        ],
                }
            )

    return clusters


def analyze_expiry_cluster(
    snapshot: dict,
    cluster: dict,
) -> dict:

    items = (
        cluster.get(
            "items",
            [],
        )
        or []
    )

    offer_ids = {
        int(
            item[
                "offer_id"
            ]
        )
        for item in items
    }

    offers = [
        item[
            "offer"
        ]
        for item in items
    ]

    loss = (
        simulate_offer_loss_set(
            snapshot=
                snapshot,

            offer_ids=
                offer_ids,
        )
    )

    effective_deadline = (
        cluster.get(
            "effective_deadline"
        )
    )

    hours = (
        calculate_hours_until(
            effective_deadline
        )
    )

    player_names = []

    for offer in offers:

        players = (
            offer.get(
                "players",
                [],
            )
            or []
        )

        for player in players:
            player_names.append(
                player.get(
                    "name",
                    "?",
                )
            )

    if not loss.get(
        "valid",
        False,
    ):

        action = (
            "EXPIRY_CLUSTER_UNKNOWN"
        )

        critical = (
            True
        )

        urgent = (
            False
        )

        reason = (
            "No se pudo simular con seguridad la pérdida "
            "simultánea del cluster."
        )

    elif loss.get(
        "guaranteed_after_loss",
        False,
    ):

        action = (
            "HOLD_EXPIRY_CLUSTER"
        )

        critical = (
            False
        )

        urgent = (
            False
        )

        reason = (
            "Todas las ofertas del cluster pueden desaparecer "
            "simultáneamente y SOLVENCY_GUARANTEE sigue cubierta."
        )

    else:

        critical = (
            True
        )

        urgent = bool(
            hours is not None
            and
            hours
            <= ACCEPT_EXECUTION_MARGIN_HOURS
        )

        if urgent:

            action = (
                "ACCEPT_CLUSTER_BEFORE_EXPIRY"
            )

            reason = (
                "La pérdida simultánea del cluster rompe "
                "SOLVENCY_GUARANTEE y el límite está dentro "
                "del margen operativo."
            )

        else:

            action = (
                "ACCEPT_CLUSTER_WATCH"
            )

            reason = (
                "La pérdida simultánea del cluster rompe "
                "SOLVENCY_GUARANTEE, pero aún queda tiempo "
                "antes del margen operativo de aceptación."
            )

    return {
        "offer_ids":
            sorted(
                offer_ids
            ),

        "player_names":
            player_names,

        "offer_count":
            len(
                offers
            ),

        "total_amount":
            sum(
                safe_int(
                    offer.get(
                        "amount"
                    )
                )
                for offer in offers
            ),

        "effective_deadline":
            effective_deadline,

        "hours_to_effective_deadline":
            (
                round(
                    hours,
                    2,
                )
                if hours is not None
                else None
            ),

        "critical":
            critical,

        "urgent":
            urgent,

        "action":
            action,

        "reason":
            reason,

        "loss_simulation":
            loss,

        "offers":
            offers,
    }


# ============================================================
# BOARD GLOBAL
# ============================================================


def build_accept_before_expiry_safety_board(
    snapshot: dict,
) -> dict:

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    reservations = (
        solvency.get(
            "solvency_reservations",
            {},
        )
        or {}
    )

    reserved = (
        reservations.get(
            "reserved",
            [],
        )
        or []
    )

    # --------------------------------------------------------
    # ANALISIS INDIVIDUAL
    # --------------------------------------------------------

    individual = []

    for offer in reserved:

        offer_id = (
            offer.get(
                "offer_id"
            )
        )

        if offer_id is None:
            continue

        loss = (
            simulate_offer_loss_set(
                snapshot=
                    snapshot,

                offer_ids={
                    int(
                        offer_id
                    )
                },
            )
        )

        effective_deadline = (
            get_effective_accept_deadline(
                offer=
                    offer,

                solvency=
                    solvency,
            )
        )

        hours = (
            calculate_hours_until(
                effective_deadline
            )
        )

        players = (
            offer.get(
                "players",
                [],
            )
            or []
        )

        name = (
            players[
                0
            ].get(
                "name",
                "?",
            )
            if len(
                players
            )
            == 1
            else " / ".join(
                player.get(
                    "name",
                    "?",
                )
                for player in players
            )
        )

        individual.append(
            {
                "offer_id":
                    int(
                        offer_id
                    ),

                "player_name":
                    name,

                "amount":
                    safe_int(
                        offer.get(
                            "amount"
                        )
                    ),

                "effective_deadline":
                    effective_deadline,

                "hours_to_effective_deadline":
                    (
                        round(
                            hours,
                            2,
                        )
                        if hours is not None
                        else None
                    ),

                "guaranteed_after_individual_loss":
                    bool(
                        loss.get(
                            "guaranteed_after_loss",
                            False,
                        )
                    ),

                "loss_simulation":
                    loss,
            }
        )

    # --------------------------------------------------------
    # ANALISIS POR CLUSTER
    # --------------------------------------------------------

    raw_clusters = (
        cluster_offers_by_effective_deadline(
            offers=
                reserved,

            solvency=
                solvency,
        )
    )

    clusters = [
        analyze_expiry_cluster(
            snapshot=
                snapshot,

            cluster=
                cluster,
        )

        for cluster
        in raw_clusters
    ]

    critical_clusters = [
        cluster
        for cluster in clusters
        if cluster.get(
            "critical",
            False,
        )
    ]

    urgent_clusters = [
        cluster
        for cluster in clusters
        if cluster.get(
            "action"
        )
        == "ACCEPT_CLUSTER_BEFORE_EXPIRY"
    ]

    watch_clusters = [
        cluster
        for cluster in clusters
        if cluster.get(
            "action"
        )
        == "ACCEPT_CLUSTER_WATCH"
    ]

    safe_clusters = [
        cluster
        for cluster in clusters
        if cluster.get(
            "action"
        )
        == "HOLD_EXPIRY_CLUSTER"
    ]

    return {
        "observer_only":
            True,

        "solvency":
            solvency,

        "reserved_count":
            len(
                reserved
            ),

        "individual":
            individual,

        "cluster_count":
            len(
                clusters
            ),

        "clusters":
            clusters,

        "critical_clusters":
            critical_clusters,

        "critical_cluster_count":
            len(
                critical_clusters
            ),

        "urgent_clusters":
            urgent_clusters,

        "urgent_cluster_count":
            len(
                urgent_clusters
            ),

        "watch_clusters":
            watch_clusters,

        "watch_cluster_count":
            len(
                watch_clusters
            ),

        "safe_clusters":
            safe_clusters,

        "safe_cluster_count":
            len(
                safe_clusters
            ),
    }


# ============================================================
# LIVE REVALIDATION
# ============================================================


def find_cluster_by_offer_ids(
    board: dict,
    offer_ids: set[int],
) -> dict | None:
    """
    Busca un cluster exacto por el conjunto de offer_id.
    """

    normalized = {
        int(
            offer_id
        )
        for offer_id in offer_ids
    }

    for cluster in board.get(
        "clusters",
        [],
    ) or []:

        current = {
            int(
                offer_id
            )
            for offer_id in (
                cluster.get(
                    "offer_ids",
                    [],
                )
                or []
            )
        }

        if current == normalized:
            return cluster

    return None


def revalidate_accept_before_expiry_cluster(
    snapshot: dict,
    offer_ids: set[int] | list[int],
) -> dict:
    """
    Recalcula ACCEPT-BEFORE-EXPIRY con un snapshot fresco.

    Esta funcion NO escribe en Biwenger.

    Solo autoriza si:
    - el cluster exacto sigue existiendo;
    - sigue siendo crítico;
    - sigue dentro del margen operativo;
    - perderlo sigue rompiendo SOLVENCY_GUARANTEE;
    - no hay lock temporal.
    """

    try:
        normalized_ids = {
            int(
                offer_id
            )
            for offer_id in offer_ids
        }

    except (
        TypeError,
        ValueError,
    ):

        return {
            "authorized":
                False,

            "status":
                "INVALID_OFFER_IDS",

            "reason":
                "Los offer_id del cluster no son validos.",

            "cluster":
                None,

            "board":
                None,
        }

    if not normalized_ids:

        return {
            "authorized":
                False,

            "status":
                "EMPTY_CLUSTER",

            "reason":
                "No se ha proporcionado ninguna oferta.",

            "cluster":
                None,

            "board":
                None,
        }

    board = (
        build_accept_before_expiry_safety_board(
            snapshot
        )
    )

    solvency = (
        board.get(
            "solvency",
            {},
        )
        or {}
    )

    deadline = (
        solvency.get(
            "deadline",
            {},
        )
        or {}
    )

    if bool(
        deadline.get(
            "operations_locked",
            False,
        )
    ):

        return {
            "authorized":
                False,

            "status":
                "TEMPORAL_LOCK",

            "reason":
                "La jornada esta temporalmente bloqueada.",

            "cluster":
                None,

            "board":
                board,
        }

    cluster = (
        find_cluster_by_offer_ids(
            board=
                board,

            offer_ids=
                normalized_ids,
        )
    )

    if cluster is None:

        return {
            "authorized":
                False,

            "status":
                "CLUSTER_NOT_FOUND",

            "reason": (
                "El cluster exacto ya no existe en el snapshot fresco."
            ),

            "cluster":
                None,

            "board":
                board,
        }

    if cluster.get(
        "action"
    ) != "ACCEPT_CLUSTER_BEFORE_EXPIRY":

        return {
            "authorized":
                False,

            "status":
                "ACCEPT_NO_LONGER_REQUIRED",

            "reason": (
                "El snapshot fresco ya no considera necesario "
                "aceptar este cluster antes de caducar."
            ),

            "cluster":
                cluster,

            "board":
                board,
        }

    if not cluster.get(
        "critical",
        False,
    ):

        return {
            "authorized":
                False,

            "status":
                "CLUSTER_NOT_CRITICAL",

            "reason":
                "El cluster ya no es critico para solvencia.",

            "cluster":
                cluster,

            "board":
                board,
        }

    if not cluster.get(
        "urgent",
        False,
    ):

        return {
            "authorized":
                False,

            "status":
                "CLUSTER_NOT_URGENT",

            "reason":
                "El cluster ya no esta dentro del margen operativo.",

            "cluster":
                cluster,

            "board":
                board,
        }

    hours = (
        cluster.get(
            "hours_to_effective_deadline"
        )
    )

    if (
        hours is None
        or
        float(
            hours
        )
        > ACCEPT_EXECUTION_MARGIN_HOURS
    ):

        return {
            "authorized":
                False,

            "status":
                "OUTSIDE_ACCEPT_WINDOW",

            "reason":
                "La aceptacion queda fuera del margen operativo.",

            "cluster":
                cluster,

            "board":
                board,
        }

    loss = (
        cluster.get(
            "loss_simulation",
            {},
        )
        or {}
    )

    if loss.get(
        "guaranteed_after_loss",
        False,
    ):

        return {
            "authorized":
                False,

            "status":
                "GUARANTEE_STILL_SAFE",

            "reason": (
                "Perder el cluster ya no rompe SOLVENCY_GUARANTEE."
            ),

            "cluster":
                cluster,

            "board":
                board,
        }

    return {
        "authorized":
            True,

        "status":
            "AUTHORIZED",

        "reason": (
            "Cluster revalidado con snapshot fresco: "
            "sigue siendo critico, urgente y necesario "
            "para proteger SOLVENCY_GUARANTEE."
        ),

        "cluster":
            cluster,

        "board":
            board,
    }
