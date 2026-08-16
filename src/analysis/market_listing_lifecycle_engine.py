from __future__ import annotations

from datetime import datetime

from src.analysis.computer_cycle_engine import (
    MADRID_TZ,
    build_computer_cycle_state,
    parse_datetime_value,
)

from src.analysis.deadline_engine import (
    build_deadline_state,
)


# ============================================================
# CONFIGURACION
# ============================================================

# Si una publicacion no llega viva hasta el final del siguiente
# ciclo Computer, debe renovarse.
#
# La renovacion usa el mismo POST /market que LIST_FOR_SALE.
RENEW_ACTION = "RENEW_MARKET_LISTING"

# Si quedan menos de estas horas de vida, se marca ademas como
# caducidad cercana para telemetria/alertas.
EXPIRY_WARNING_HOURS = 12.0

# Una publicacion que caduca dentro de estas horas es URGENTE:
# hay que renovarla ya o la perdemos.
#
# Por encima de este margen la renovacion sigue siendo
# necesaria, pero no compite con acciones irreversibles como
# pujar: el mercado Computer se resetea una vez al dia y una
# puja no realizada se pierde para siempre, mientras que una
# publicacion tiene decenas de ciclos por delante para
# renovarse.
#
# Sin esta distincion el ciclo -que ejecuta UNA accion por
# vuelta- se dedicaba a renovar anuncios con 14 horas de vida
# por delante mientras habia seis objetivos pujables sin tocar.
RENEW_URGENT_HOURS = 3.0


# ============================================================
# HELPERS
# ============================================================


def resolve_renewal_price(
    listed_price,
    market_value,
) -> dict:
    """
    Precio con el que se vuelve a publicar un jugador.

    Observado en produccion: una publicacion por DEBAJO del
    valor de mercado actual es rechazada por Biwenger con
    HTTP 400. Ocurre cuando el precio del jugador sube despues
    de haberlo publicado.

    La correccion solo puede SUBIR el precio, nunca bajarlo:
    pedir mas dinero por un jugador que queremos vender no nos
    perjudica en ningun escenario.
    """

    publicado = int(
        listed_price
        or 0
    )

    valor = int(
        market_value
        or 0
    )

    precio = max(
        publicado,
        valor,
    )

    return {
        "listed_price":
            publicado,

        "market_value":
            valor,

        "renewal_price":
            precio,

        "price_raised":
            bool(
                precio
                > publicado
            ),
    }


def get_my_team_lookup(
    snapshot: dict,
) -> dict[int, dict]:
    return {
        int(player["id"]): player
        for player in snapshot.get(
            "my_team",
            [],
        )
        if player.get("id") is not None
    }


def get_current_listings(
    snapshot: dict,
) -> dict[int, dict]:
    """
    Todas las publicaciones de jugadores de NUESTRA plantilla.

    Es generico:
    - liquidez
    - especulacion
    - reroll
    - venta tactica
    - cualquier otro motivo

    El lifecycle de la publicacion no depende del motivo.
    """
    team = get_my_team_lookup(
        snapshot
    )

    result = {}

    sales = (
        snapshot.get(
            "market",
            {},
        ).get(
            "sales",
            [],
        )
        or []
    )

    for sale in sales:

        player_data = (
            sale.get(
                "player",
                {},
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

        result[player_id] = {
            "player_id":
                player_id,

            "player":
                team[
                    player_id
                ],

            "listed_price":
                int(
                    sale.get(
                        "price",
                        0,
                    )
                    or 0
                ),

            "listed_at_raw":
                sale.get(
                    "date"
                ),

            "until_raw":
                sale.get(
                    "until"
                ),

            "listed_at":
                parse_datetime_value(
                    sale.get(
                        "date"
                    )
                ),

            "expires_at":
                parse_datetime_value(
                    sale.get(
                        "until"
                    )
                ),

            "raw":
                sale,
        }

    return result


def hours_between(
    later: datetime | None,
    earlier: datetime | None,
) -> float | None:

    if (
        later is None
        or earlier is None
    ):
        return None

    return (
        later
        - earlier
    ).total_seconds() / 3600


def get_next_future_computer_cycle(
    cycle_state: dict,
) -> dict | None:
    """
    Primer ciclo Computer cuyo final aun no ha pasado.

    build_computer_cycle_state ya filtra ciclos utiles respecto
    al deadline real de la jornada.
    """
    cycles = (
        cycle_state.get(
            "safe_cycles",
            [],
        )
        or []
    )

    if not cycles:
        return None

    return cycles[0]


# ============================================================
# ANALISIS INDIVIDUAL
# ============================================================


def analyze_listing_lifecycle(
    listing: dict,
    cycle_state: dict,
    now: datetime | None = None,
) -> dict:

    now = (
        now
        or cycle_state.get(
            "now"
        )
        or datetime.now(
            MADRID_TZ
        )
    )

    if now.tzinfo is None:
        now = now.replace(
            tzinfo=MADRID_TZ
        )

    now = now.astimezone(
        MADRID_TZ
    )

    listed_at = (
        listing.get(
            "listed_at"
        )
    )

    expires_at = (
        listing.get(
            "expires_at"
        )
    )

    listing_duration_hours = (
        hours_between(
            expires_at,
            listed_at,
        )
    )

    hours_to_expiry = (
        hours_between(
            expires_at,
            now,
        )
    )

    if hours_to_expiry is not None:
        hours_to_expiry = max(
            hours_to_expiry,
            0.0,
        )

    next_cycle = (
        get_next_future_computer_cycle(
            cycle_state
        )
    )

    next_cycle_start = (
        next_cycle.get(
            "cycle_start"
        )
        if next_cycle
        else None
    )

    next_cycle_end = (
        next_cycle.get(
            "cycle_end"
        )
        if next_cycle
        else None
    )

    safe_liquidity_at = (
        next_cycle.get(
            "safe_liquidity_at"
        )
        if next_cycle
        else None
    )

    survives_next_cycle_start = bool(
        expires_at is not None
        and
        next_cycle_start is not None
        and
        expires_at
        >= next_cycle_start
    )

    survives_next_cycle_end = bool(
        expires_at is not None
        and
        next_cycle_end is not None
        and
        expires_at
        >= next_cycle_end
    )

    survives_safe_liquidity_at = bool(
        expires_at is not None
        and
        safe_liquidity_at is not None
        and
        expires_at
        >= safe_liquidity_at
    )

    expiry_warning = bool(
        hours_to_expiry is not None
        and
        hours_to_expiry
        <= EXPIRY_WARNING_HOURS
    )

    # ========================================================
    # DECISION
    # ========================================================

    renew_urgent = False

    if expires_at is None:

        action = (
            "LISTING_EXPIRY_UNKNOWN"
        )

        renew_required = (
            False
        )

        reason = (
            "La publicacion existe, pero no conocemos "
            "su fecha de caducidad."
        )

    elif next_cycle is None:

        action = (
            "NO_FUTURE_COMPUTER_CYCLE"
        )

        renew_required = (
            False
        )

        reason = (
            "No queda ningun ciclo Computer util antes "
            "del deadline real de la jornada."
        )

    elif not survives_next_cycle_end:

        action = (
            RENEW_ACTION
        )

        renew_required = (
            True
        )

        reason = (
            "La publicacion caduca antes de terminar el "
            "siguiente ciclo Computer y debe renovarse "
            "si queremos mantenerla disponible."
        )

        if (
            hours_to_expiry is not None
            and
            hours_to_expiry
            <= RENEW_URGENT_HOURS
        ):
            renew_urgent = True

            reason = (
                f"{reason} Quedan "
                f"{round(hours_to_expiry, 2)} h de vida: "
                "es urgente."
            )

    else:

        action = (
            "KEEP_LISTING"
        )

        renew_required = (
            False
        )

        reason = (
            "La publicacion sigue vigente durante todo "
            "el siguiente ciclo Computer."
        )

    player = (
        listing.get(
            "player",
            {},
        )
        or {}
    )

    return {
        "player_id":
            listing.get(
                "player_id"
            ),

        "name":
            player.get(
                "name"
            ),

        "listed_price":
            listing.get(
                "listed_price"
            ),

        "listed_at":
            listed_at,

        "expires_at":
            expires_at,

        "listing_duration_hours":
            (
                round(
                    listing_duration_hours,
                    2,
                )
                if listing_duration_hours
                is not None
                else None
            ),

        "hours_to_expiry":
            (
                round(
                    hours_to_expiry,
                    2,
                )
                if hours_to_expiry
                is not None
                else None
            ),

        "expiry_warning":
            expiry_warning,

        "next_computer_cycle":
            next_cycle,

        "survives_next_cycle_start":
            survives_next_cycle_start,

        "survives_next_cycle_end":
            survives_next_cycle_end,

        "survives_safe_liquidity_at":
            survives_safe_liquidity_at,

        "renew_required":
            renew_required,

        "renew_urgent":
            renew_urgent,

        "renew_urgent_hours":
            RENEW_URGENT_HOURS,

        "action":
            action,

        "reason":
            reason,

        "listing":
            listing,
    }


# ============================================================
# BOARD GLOBAL
# ============================================================


def build_market_listing_lifecycle_board(
    snapshot: dict,
    now: datetime | None = None,
) -> dict:

    deadline = (
        build_deadline_state(
            snapshot
        )
    )

    cycle_state = (
        build_computer_cycle_state(
            deadline=
                deadline,

            now=
                now,
        )
    )

    listings = (
        get_current_listings(
            snapshot
        )
    )

    players = [
        analyze_listing_lifecycle(
            listing=
                listing,

            cycle_state=
                cycle_state,

            now=
                now,
        )

        for listing
        in listings.values()
    ]

    players.sort(
        key=lambda player: (
            player.get(
                "expires_at"
            )
            or datetime.max.replace(
                tzinfo=MADRID_TZ
            )
        )
    )

    renew_required = [
        player

        for player in players

        if player.get(
            "renew_required",
            False,
        )
    ]

    renew_urgent = [
        player

        for player in renew_required

        if player.get(
            "renew_urgent",
            False,
        )
    ]

    expiry_warnings = [
        player

        for player in players

        if player.get(
            "expiry_warning",
            False,
        )
    ]

    healthy = [
        player

        for player in players

        if player.get(
            "action"
        )
        == "KEEP_LISTING"
    ]

    return {
        "deadline":
            deadline,

        "computer_cycles":
            cycle_state,

        "players":
            players,

        "listing_count":
            len(
                players
            ),

        "renew_required":
            renew_required,

        "renew_required_count":
            len(
                renew_required
            ),

        "renew_urgent":
            renew_urgent,

        "renew_urgent_count":
            len(
                renew_urgent
            ),

        "expiry_warnings":
            expiry_warnings,

        "expiry_warning_count":
            len(
                expiry_warnings
            ),

        "healthy":
            healthy,

        "healthy_count":
            len(
                healthy
            ),
    }
