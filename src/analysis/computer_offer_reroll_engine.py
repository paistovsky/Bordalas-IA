from __future__ import annotations

import json

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from src.analysis.solvency_engine import (
    SAFE_LIQUIDITY_BUFFER,
    build_solvency_state,
    get_expected_haircut,
)


# ============================================================
# CONFIGURACION
# ============================================================

STATE_DIRECTORY = (
    Path("data")
    / "autopilot"
)

STATE_FILE = (
    STATE_DIRECTORY
    / "computer_offer_history.json"
)

# Una oferta necesaria para solvencia que esta cerca de caducar
# debe convertirse en dinero antes de perderla.
ACCEPT_BEFORE_EXPIRY_HOURS = 6.0

# Con la jornada encima, una oferta reservada para solvencia
# debe convertirse en dinero aunque todavia no caduque.
#
# Sin esta regla la unica presion era la caducidad de la propia
# oferta, que es independiente del calendario: se podia llegar
# al cierre de jornada en negativo con ofertas buenas sin tocar.
ACCEPT_BEFORE_DEADLINE_HOURS = 6.0

# Tope de rechazos por jugador.
#
# Sin tope el motor podia rechazar 970.000, luego 960.000, luego
# 950.000... sin recordar que ya habia rechazado algo mejor, y
# acabar aceptando una oferta peor que la primera o perdiendolas
# todas por caducidad.
MAX_REROLLS_PER_PLAYER = 3

# Umbrales deliberadamente prudentes.
#
# No asumimos una distribucion concreta de las ofertas Computer.
# Un descuento claro respecto a valor de mercado puede justificar
# estudiar reroll SIEMPRE que el safety gate lo permita.
REROLL_CANDIDATE_PREMIUM_PERCENT = -2.0

# Una oferta a valor de mercado o mejor se conserva por defecto.
GOOD_OFFER_PREMIUM_PERCENT = 0.0


# ============================================================
# UTILIDADES
# ============================================================


def parse_datetime(
    value,
) -> datetime | None:

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):

        result = value

    elif isinstance(
        value,
        (int, float),
    ):

        try:

            result = (
                datetime.fromtimestamp(
                    float(
                        value
                    ),
                    tz=timezone.utc,
                )
            )

        except (
            OSError,
            OverflowError,
            ValueError,
        ):

            return None

    elif isinstance(
        value,
        str,
    ):

        clean = (
            value.strip()
        )

        if not clean:
            return None

        if clean.isdigit():

            return parse_datetime(
                int(
                    clean
                )
            )

        try:

            result = (
                datetime.fromisoformat(
                    clean.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

        except ValueError:

            return None

    else:

        return None

    if result.tzinfo is None:

        result = (
            result.replace(
                tzinfo=timezone.utc,
            )
        )

    return result.astimezone(
        timezone.utc
    )


def now_utc() -> datetime:

    return datetime.now(
        timezone.utc
    )


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


# ============================================================
# HISTORIAL
# ============================================================


def ensure_state_directory() -> None:

    STATE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )


def load_offer_history() -> dict:

    if not STATE_FILE.exists():

        return {
            "players":
                {},
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8-sig",
        ) as file:

            data = (
                json.load(
                    file
                )
            )

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                "Root invalido."
            )

        data.setdefault(
            "players",
            {},
        )

        return data

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ):

        return {
            "players":
                {},
        }


def save_offer_history(
    history: dict,
) -> None:

    ensure_state_directory()

    temporary = (
        STATE_FILE.with_suffix(
            ".json.tmp"
        )
    )

    with open(
        temporary,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary.replace(
        STATE_FILE
    )


def update_seen_offer_history(
    history: dict,
    offer: dict,
) -> dict:

    player_ids = (
        offer.get(
            "player_ids",
            [],
        )
        or []
    )

    if len(
        player_ids
    ) != 1:

        return {
            "reroll_count":
                0,

            "best_offer_seen":
                None,
        }

    player_id = int(
        player_ids[
            0
        ]
    )

    key = str(
        player_id
    )

    players = (
        history.setdefault(
            "players",
            {},
        )
    )

    state = (
        players.setdefault(
            key,
            {
                "reroll_count":
                    0,

                "best_offer_seen":
                    0,

                "offers":
                    [],
            },
        )
    )

    offer_id = (
        offer.get(
            "offer_id"
        )
    )

    amount = safe_int(
        offer.get(
            "amount"
        )
    )

    seen_ids = {
        str(
            item.get(
                "offer_id"
            )
        )

        for item in state.get(
            "offers",
            [],
        )

        if item.get(
            "offer_id"
        )
        is not None
    }

    if (
        offer_id is not None
        and
        str(
            offer_id
        )
        not in seen_ids
    ):

        state.setdefault(
            "offers",
            [],
        ).append(
            {
                "offer_id":
                    offer_id,

                "amount":
                    amount,

                "seen_at":
                    now_utc().isoformat(),
            }
        )

    state[
        "best_offer_seen"
    ] = max(
        safe_int(
            state.get(
                "best_offer_seen"
            )
        ),
        amount,
    )

    return {
        "reroll_count":
            safe_int(
                state.get(
                    "reroll_count"
                )
            ),

        "best_offer_seen":
            safe_int(
                state.get(
                    "best_offer_seen"
                )
            ),
    }


def record_reroll(
    player_id: int,
    offer_id=None,
    amount=None,
) -> None:
    """
    Registra un rechazo real de oferta Computer.

    Persiste tambien best_offer_seen. update_seen_offer_history
    lo calcula al construir el tablero, pero ese tablero corre
    siempre con persist_history=False, de modo que el maximo
    historico nunca llegaba al disco y la memoria del motor era
    inservible: podia rechazar 970.000 y luego aceptar 950.000
    sin enterarse.
    """

    history = (
        load_offer_history()
    )

    state = (
        history
        .setdefault(
            "players",
            {},
        )
        .setdefault(
            str(
                int(
                    player_id
                )
            ),
            {
                "reroll_count":
                    0,

                "best_offer_seen":
                    0,

                "offers":
                    [],
            },
        )
    )

    state[
        "reroll_count"
    ] = (
        safe_int(
            state.get(
                "reroll_count"
            )
        )
        + 1
    )

    if amount is not None:

        # La mejor oferta que hemos TIRADO. Es la referencia
        # honesta: best_offer_seen incluye la que estas mirando
        # ahora mismo y no sirve para decidir sobre ella.
        state[
            "best_offer_rejected"
        ] = max(
            safe_int(
                state.get(
                    "best_offer_rejected"
                )
            ),
            safe_int(amount),
        )

    state[
        "last_rerolled_offer_id"
    ] = offer_id

    state[
        "last_rerolled_at"
    ] = (
        now_utc().isoformat()
    )

    save_offer_history(
        history
    )


# ============================================================
# SAFETY DE REROLL
# ============================================================


def get_next_replacement_cycle(
    solvency: dict,
) -> dict | None:

    cycles = (
        solvency.get(
            "computer_cycles",
            {},
        )
        or {}
    )

    new_listing_cycles = (
        cycles.get(
            "new_listing_cycles",
            [],
        )
        or []
    )

    if not new_listing_cycles:
        return None

    return new_listing_cycles[
        0
    ]


def calculate_replacement_expected_liquidity(
    offer: dict,
    solvency: dict,
) -> dict:

    replacement_cycle = (
        get_next_replacement_cycle(
            solvency
        )
    )

    if replacement_cycle is None:

        return {
            "possible":
                False,

            "expected_liquidity":
                0,

            "haircut":
                0.0,

            "cycle":
                None,

            "reason": (
                "No queda ningun ciclo Computer seguro "
                "para una nueva publicacion antes del T-15."
            ),
        }

    cycles = (
        solvency.get(
            "computer_cycles",
            {},
        )
        or {}
    )

    safe_cycles_remaining = safe_int(
        cycles.get(
            "safe_cycles_remaining"
        )
    )

    haircut = (
        get_expected_haircut(
            safe_cycles_remaining
        )
    )

    market_value = safe_int(
        offer.get(
            "market_value"
        )
    )

    expected = int(
        market_value
        * haircut
    )

    return {
        "possible":
            expected > 0,

        "expected_liquidity":
            expected,

        "haircut":
            haircut,

        "cycle":
            replacement_cycle,

        "reason": (
            "Existe al menos un ciclo Computer seguro "
            "despues de volver a publicar."
        ),
    }


def simulate_guarantee_after_reroll(
    offer: dict,
    solvency: dict,
) -> dict:

    guarantee = (
        solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    replacement = (
        calculate_replacement_expected_liquidity(
            offer=
                offer,

            solvency=
                solvency,
        )
    )

    current_recovery = safe_int(
        guarantee.get(
            "guaranteed_recovery"
        )
    )

    required_recovery = safe_int(
        guarantee.get(
            "required_recovery"
        )
    )

    offer_amount = safe_int(
        offer.get(
            "amount"
        )
    )

    replacement_expected = safe_int(
        replacement.get(
            "expected_liquidity"
        )
    )

    projected_recovery = (
        current_recovery
        - offer_amount
        + replacement_expected
    )

    projected_surplus = (
        projected_recovery
        - required_recovery
    )

    guaranteed_after = bool(
        replacement.get(
            "possible",
            False,
        )
        and
        projected_surplus >= 0
    )

    return {
        "guaranteed_after_reroll":
            guaranteed_after,

        "current_guaranteed_recovery":
            current_recovery,

        "required_recovery":
            required_recovery,

        "current_offer_removed":
            offer_amount,

        "replacement_expected_liquidity":
            replacement_expected,

        "projected_recovery":
            projected_recovery,

        "projected_surplus":
            projected_surplus,

        "replacement":
            replacement,
    }


# ============================================================
# CLASIFICACION
# ============================================================


def classify_offer_quality(
    offer: dict,
) -> dict:

    premium = float(
        offer.get(
            "premium_percent",
            0,
        )
        or 0
    )

    if premium >= GOOD_OFFER_PREMIUM_PERCENT:

        quality = (
            "GOOD_OR_BETTER"
        )

    elif (
        premium
        <= REROLL_CANDIDATE_PREMIUM_PERCENT
    ):

        quality = (
            "WEAK"
        )

    else:

        quality = (
            "FAIR"
        )

    return {
        "quality":
            quality,

        "premium_percent":
            premium,
    }


def calculate_hours_to_expiry(
    offer: dict,
) -> float | None:

    expiry = (
        offer.get(
            "expires_at"
        )
    )

    if expiry is None:

        expiry = (
            offer.get(
                "until"
            )
        )

    parsed = (
        parse_datetime(
            expiry
        )
    )

    if parsed is None:

        return None

    return max(
        (
            parsed
            - now_utc()
        ).total_seconds()
        / 3600,
        0.0,
    )


def reroll_block_reason(
    history_state: dict,
    amount: int,
) -> tuple[str, str] | None:
    """
    Decide si el historial desaconseja rechazar esta oferta.

    Dos frenos, complementarios:

    MEMORIA - se compara contra la mejor oferta que hemos
    RECHAZADO, no contra la mejor que hemos visto.

    La diferencia importa. best_offer_seen se actualiza al ver
    la oferta actual, asi que compararse con el bloquearia
    siempre el primer reroll: la oferta que estas evaluando ya
    es, por definicion, la mejor vista.

    Contra lo rechazado la regla si dice algo: si la oferta
    actual no mejora lo que ya tiramos, el reroll ha fracasado
    -tuvimos algo igual o mejor y lo dejamos ir-, y seguir
    rechazando es la espiral descendente. Solo si la hemos
    mejorado tiene sentido plantearse otro intento.

    TOPE - por si las ofertas oscilan al alza y la memoria sola
    no converge.

    Devuelve (accion, motivo) o None si se puede rerollear.
    """

    rerolls = safe_int(
        history_state.get(
            "reroll_count"
        )
    )

    if rerolls >= MAX_REROLLS_PER_PLAYER:

        return (
            "KEEP_REROLL_CAP_REACHED",
            f"Ya se han rechazado {rerolls} ofertas por este "
            f"jugador (tope {MAX_REROLLS_PER_PLAYER}). "
            f"Seguir rechazando arriesga acabar peor.",
        )

    rechazado = safe_int(
        history_state.get(
            "best_offer_rejected"
        )
    )

    if (
        rechazado > 0
        and
        safe_int(amount) <= rechazado
    ):

        return (
            "KEEP_NO_IMPROVEMENT",
            f"La oferta ({safe_int(amount)}) no mejora la mejor "
            f"que ya rechazamos por este jugador ({rechazado}). "
            f"El reroll no esta funcionando: seguir rechazando "
            f"es bajar en espiral.",
        )

    return None


def analyze_computer_offer(
    offer: dict,
    solvency: dict,
    reserved_offer_ids: set,
    history: dict,
    hours_to_deadline: float | None = None,
) -> dict:

    offer_id = (
        offer.get(
            "offer_id"
        )
    )

    reserved = (
        offer_id
        in reserved_offer_ids
    )

    quality = (
        classify_offer_quality(
            offer
        )
    )

    hours_to_expiry = (
        calculate_hours_to_expiry(
            offer
        )
    )

    simulation = (
        simulate_guarantee_after_reroll(
            offer=
                offer,

            solvency=
                solvency,
        )
    )

    reroll_safe = bool(
        simulation[
            "guaranteed_after_reroll"
        ]
    )

    replacement_possible = bool(
        simulation[
            "replacement"
        ][
            "possible"
        ]
    )

    player_ids = (
        offer.get(
            "player_ids",
            [],
        )
        or []
    )

    player_id = (
        int(
            player_ids[
                0
            ]
        )
        if len(
            player_ids
        )
        == 1
        else None
    )

    history_state = (
        update_seen_offer_history(
            history=
                history,

            offer=
                offer,
        )
    )

    franchise_protected = bool(
        offer.get(
            "franchise_protected",
            False,
        )
    )

    # ========================================================
    # DECISION
    # ========================================================

    if franchise_protected:

        action = (
            "KEEP_PROTECTED"
        )

        can_reroll = (
            False
        )

        reason = (
            "Jugador protegido/Franchise. "
            "El motor de reroll no autoriza tocar la oferta."
        )

    elif reserved:

        # Una oferta reservada para solvencia NUNCA puede caer
        # a las ramas de calidad de abajo: si lo hace acaba en
        # KEEP_GOOD_OFFER o REROLL_CANDIDATE y la reserva se
        # pierde en silencio.
        #
        # Antes esta rama exigia ademas "not reroll_safe", asi
        # que toda oferta reservada y rerolleable se escapaba
        # y no se cobraba jamas.

        expiry_pressure = bool(
            hours_to_expiry
            is not None
            and
            hours_to_expiry
            <= ACCEPT_BEFORE_EXPIRY_HOURS
        )

        deadline_pressure = bool(
            hours_to_deadline
            is not None
            and
            hours_to_deadline
            <= ACCEPT_BEFORE_DEADLINE_HOURS
        )

        if (
            expiry_pressure
            or
            deadline_pressure
        ):

            action = (
                "ACCEPT_BEFORE_EXPIRY"
            )

            can_reroll = (
                False
            )

            motivo = (
                "proxima a caducar"
                if expiry_pressure
                else "con el cierre de jornada encima"
            )

            reason = (
                "Oferta SOLVENCY_RESERVED, necesaria para "
                f"garantizar T-15, y {motivo}. "
                "Se convierte en dinero antes de perderla."
            )

        elif (
            quality[
                "quality"
            ]
            == "WEAK"
            and
            replacement_possible
            and
            reroll_safe
            and
            reroll_block_reason(
                history_state,
                offer.get("amount"),
            )
            is None
        ):

            action = (
                "REROLL_CANDIDATE"
            )

            can_reroll = (
                True
            )

            reason = (
                "Oferta SOLVENCY_RESERVED pero claramente por "
                "debajo de mercado, sin presion de caducidad "
                "ni de jornada. Existe ciclo de reemplazo "
                "seguro que mantiene SOLVENCY_GUARANTEE."
            )

        else:

            action = (
                "KEEP_SOLVENCY_RESERVED"
            )

            can_reroll = (
                False
            )

            reason = (
                "Oferta SOLVENCY_RESERVED. Rechazarla haria "
                "que la garantia T-15 dejase de estar cubierta "
                "incluso contando una nueva oferta futura "
                "con haircut conservador."
            )

    elif (
        quality[
            "quality"
        ]
        == "WEAK"
        and
        replacement_possible
        and
        reroll_safe
        and
        reroll_block_reason(
            history_state,
            offer.get("amount"),
        )
        is not None
    ):

        # El historial desaconseja seguir rechazando.
        (
            action,
            reason,
        ) = reroll_block_reason(
            history_state,
            offer.get("amount"),
        )

        can_reroll = (
            False
        )

    elif (
        quality[
            "quality"
        ]
        == "WEAK"
        and
        replacement_possible
        and
        reroll_safe
    ):

        action = (
            "REROLL_CANDIDATE"
        )

        can_reroll = (
            True
        )

        reason = (
            "Oferta claramente por debajo del valor de mercado "
            "y existe otro ciclo Computer seguro. "
            "La simulacion mantiene SOLVENCY_GUARANTEE."
        )

    elif (
        quality[
            "quality"
        ]
        == "GOOD_OR_BETTER"
    ):

        action = (
            "KEEP_GOOD_OFFER"
        )

        can_reroll = (
            False
        )

        reason = (
            "Oferta a valor de mercado o mejor. "
            "Se conserva como opcion de liquidez."
        )

    else:

        action = (
            "KEEP_OFFER"
        )

        can_reroll = (
            False
        )

        reason = (
            "La mejora potencial de un reroll no justifica "
            "perder una oferta vigente con la informacion actual."
        )

    return {
        **offer,

        "player_id":
            player_id,

        "solvency_reserved":
            reserved,

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

        "quality":
            quality[
                "quality"
            ],

        "reroll_safe":
            reroll_safe,

        "can_reroll":
            can_reroll,

        "replacement_cycle_available":
            replacement_possible,

        "simulation":
            simulation,

        "action":
            action,

        "reason":
            reason,

        "reroll_count":
            history_state[
                "reroll_count"
            ],

        "best_offer_seen":
            history_state[
                "best_offer_seen"
            ],
    }


# ============================================================
# BOARD
# ============================================================


def build_computer_offer_reroll_board(
    snapshot: dict,
    persist_history: bool = False,
    hours_to_deadline: float | None = None,
) -> dict:

    solvency = (
        build_solvency_state(
            snapshot
        )
    )

    secured = (
        solvency.get(
            "secured_liquidity",
            {},
        )
        or {}
    )

    computer_offers = (
        secured.get(
            "all_computer_offers",
            [],
        )
        or []
    )

    reservations = (
        solvency.get(
            "solvency_reservations",
            {},
        )
        or {}
    )

    reserved_offer_ids = set(
        reservations.get(
            "reserved_offer_ids",
            [],
        )
        or []
    )

    # Presion de calendario.
    #
    # build_solvency_state ya calcula los segundos que faltan
    # para el cierre real de jornada, asi que no hace falta
    # cablear nada desde los llamadores: todos heredan la regla.
    if hours_to_deadline is None:

        seconds_to_deadline = (
            solvency.get(
                "seconds_to_deadline"
            )
        )

        if seconds_to_deadline is not None:

            hours_to_deadline = (
                float(
                    seconds_to_deadline
                )
                / 3600.0
            )

    history = (
        load_offer_history()
    )

    analyzed = [
        analyze_computer_offer(
            offer=
                offer,

            solvency=
                solvency,

            reserved_offer_ids=
                reserved_offer_ids,

            history=
                history,

            hours_to_deadline=
                hours_to_deadline,
        )

        for offer
        in computer_offers
    ]

    if persist_history:

        save_offer_history(
            history
        )

    reroll_candidates = [
        offer

        for offer in analyzed

        if offer[
            "action"
        ]
        == "REROLL_CANDIDATE"
    ]

    accept_before_expiry = [
        offer

        for offer in analyzed

        if offer[
            "action"
        ]
        == "ACCEPT_BEFORE_EXPIRY"
    ]

    protected = [
        offer

        for offer in analyzed

        if offer.get(
            "solvency_reserved",
            False,
        )
    ]

    return {
        "solvency":
            solvency,

        "offers":
            analyzed,

        "offer_count":
            len(
                analyzed
            ),

        "reroll_candidates":
            reroll_candidates,

        "accept_before_expiry":
            accept_before_expiry,

        "solvency_reserved":
            protected,

        "state_file":
            str(
                STATE_FILE
            ),

        "history_persisted":
            persist_history,
    }


# ============================================================
# LIVE REVALIDATION
# ============================================================


def find_offer_by_id(
    board: dict,
    offer_id: int,
) -> dict | None:
    """
    Busca una oferta Computer concreta dentro del board actual.
    """
    try:
        offer_id = int(offer_id)
    except (TypeError, ValueError):
        return None

    for offer in board.get(
        "offers",
        [],
    ) or []:

        current_id = offer.get(
            "offer_id"
        )

        try:
            current_id = int(current_id)
        except (TypeError, ValueError):
            continue

        if current_id == offer_id:
            return offer

    return None


def revalidate_reroll_offer(
    snapshot: dict,
    offer_id: int,
) -> dict:
    """
    Recalcula todo el Reroll Engine con un snapshot fresco y
    devuelve una autorizacion estricta.

    Esta funcion NO escribe en Biwenger.
    """
    board = build_computer_offer_reroll_board(
        snapshot=snapshot,
        persist_history=False,
    )

    offer = find_offer_by_id(
        board=board,
        offer_id=offer_id,
    )

    if offer is None:
        return {
            "authorized": False,
            "status": "OFFER_NOT_FOUND",
            "reason": (
                "La oferta ya no existe en el snapshot fresco."
            ),
            "offer": None,
            "board": board,
        }

    if offer.get("action") != "REROLL_CANDIDATE":
        return {
            "authorized": False,
            "status": "REROLL_NO_LONGER_RECOMMENDED",
            "reason": (
                "El snapshot fresco ya no clasifica la oferta "
                "como REROLL_CANDIDATE."
            ),
            "offer": offer,
            "board": board,
        }

    if not offer.get("reroll_safe", False):
        return {
            "authorized": False,
            "status": "SOLVENCY_GATE_BLOCK",
            "reason": (
                "La simulacion fresca no mantiene la garantia T-15."
            ),
            "offer": offer,
            "board": board,
        }

    if not offer.get(
        "replacement_cycle_available",
        False,
    ):
        return {
            "authorized": False,
            "status": "NO_SAFE_COMPUTER_CYCLE",
            "reason": (
                "No queda otro ciclo Computer seguro para el reroll."
            ),
            "offer": offer,
            "board": board,
        }

    simulation = (
        offer.get(
            "simulation",
            {},
        )
        or {}
    )

    if not simulation.get(
        "guaranteed_after_reroll",
        False,
    ):
        return {
            "authorized": False,
            "status": "GUARANTEE_BLOCK",
            "reason": (
                "SOLVENCY_GUARANTEE no queda cubierta tras el reroll."
            ),
            "offer": offer,
            "board": board,
        }

    return {
        "authorized": True,
        "status": "AUTHORIZED",
        "reason": (
            "Oferta revalidada con snapshot fresco: "
            "reroll seguro y otro ciclo Computer disponible."
        ),
        "offer": offer,
        "board": board,
    }
