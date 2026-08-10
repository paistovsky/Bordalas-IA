from src.analysis.computer_offer_reroll_engine import (
    record_reroll,
    revalidate_reroll_offer,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)

from src.analysis.lineup_monitor import (
    save_lineup_monitor_state,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


HARD_SAFETY_ALLOWED_ACTIONS = {
    "LIST_FOR_LIQUIDITY",
    "ACCEPT_RECOVERY_OFFER",
    "SAVE_LINEUP",
}

# Reroll nunca se autoriza dentro de Hard Safety.
REROLL_ACTION = "REROLL_COMPUTER_OFFER"


def refresh_snapshot_for_write_revalidation() -> tuple[str, dict]:
    """
    Read-before-write obligatorio para operaciones delicadas.

    Refresca Biwenger y carga un snapshot nuevo justo antes
    de decidir si se permite la escritura.
    """
    collect_league_snapshot()

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(
        snapshot_file
    )

    return (
        snapshot_file,
        snapshot,
    )


def build_noop_result(
    decision: dict,
    status: str,
    reason: str,
    success: bool = True,
) -> dict:

    return {
        "action":
            decision.get(
                "action"
            ),

        "status":
            status,

        "reason":
            reason,

        "write_performed":
            False,

        "success":
            success,

        "http_status":
            None,

        "response":
            None,
    }


def validate_temporal_write_gate(
    decision: dict,
) -> dict | None:
    """
    Segunda barrera independiente del Orchestrator.

    Si por un bug llegase una decision ejecutable durante
    ROUND_LOCKED o ROUND_TRANSITION_LOCK, el executor se
    niega a escribir.

    En HARD_SAFETY solo se permiten acciones destinadas a:
    - generar liquidez;
    - recuperar saldo;
    - guardar el XI.
    """

    gate = (
        decision.get(
            "temporal_gate",
            {},
        )
        or {}
    )

    action = (
        decision.get(
            "action"
        )
    )

    phase = str(
        gate.get(
            "phase",
            "UNKNOWN",
        )
    )

    if gate.get(
        "operations_locked",
        False,
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "TEMPORAL_LOCK",

            reason=(
                f"Escritura bloqueada por fase temporal "
                f"{phase}."
            ),

            success=
                True,
        )

    if (
        gate.get(
            "hard_safety_mode",
            False,
        )
        and
        action
        not in HARD_SAFETY_ALLOWED_ACTIONS
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "HARD_SAFETY_BLOCK",

            reason=(
                f"La accion {action} no esta autorizada "
                "durante HARD_SAFETY."
            ),

            success=
                True,
        )

    return None


def execute_autopilot_decision(
    decision: dict,
    execute: bool = False,
) -> dict:
    """
    Ejecuta como maximo UNA escritura real.

    Acciones LIVE soportadas:
    - LIST_FOR_LIQUIDITY
    - ACCEPT_RECOVERY_OFFER
    - SAVE_LINEUP

    El flujo Franchise existente permanece fuera hasta
    integrarlo explicitamente.
    """

    action = (
        decision.get(
            "action"
        )
    )

    # --------------------------------------------------------
    # BARRERA TEMPORAL INDEPENDIENTE
    # --------------------------------------------------------

    temporal_block = (
        validate_temporal_write_gate(
            decision
        )
    )

    if temporal_block is not None:

        return temporal_block

    # --------------------------------------------------------
    # DECISION NO EJECUTABLE
    # --------------------------------------------------------

    if not decision.get(
        "executable",
        False,
    ):

        return build_noop_result(
            decision=
                decision,

            status=
                "NOT_EXECUTABLE",

            reason=(
                "La decision global no requiere "
                "una escritura."
            ),
        )

    # --------------------------------------------------------
    # OBSERVER
    # --------------------------------------------------------

    if not execute:

        return build_noop_result(
            decision=
                decision,

            status=
                "DRY_RUN",

            reason=(
                "Observer: no se ha modificado Biwenger."
            ),
        )

    # ========================================================
    # PUBLICAR PARA LIQUIDEZ
    # ========================================================

    if action == "LIST_FOR_LIQUIDITY":

        player = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "player"
            )
        )

        if not player:

            return {
                "action":
                    action,

                "status":
                    "INVALID_DECISION",

                "reason":
                    "Falta el jugador a publicar.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        player_id = int(
            player[
                "id"
            ]
        )

        price = int(
            player[
                "listing_price"
            ]
        )

        if price <= 0:

            return {
                "action":
                    action,

                "status":
                    "INVALID_PRICE",

                "reason":
                    "El precio de publicacion no es valido.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.list_player_for_sale(
                player_id=
                    player_id,

                price=
                    price,

                execute=
                    True,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "LISTED"
                    if result.get(
                        "success"
                    )
                    else "FAILED"
                ),

            "reason":
                (
                    f"Publicacion de "
                    f"{player.get('name')}."
                ),

            "write_performed":
                True,

            "success":
                bool(
                    result.get(
                        "success",
                        False,
                    )
                ),

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "player":
                player,
        }

    # ========================================================
    # ACEPTAR OFERTA PARA SOLVENCIA
    # ========================================================

    if action == "ACCEPT_RECOVERY_OFFER":

        offer = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "offer"
            )
        )

        if not offer:

            return {
                "action":
                    action,

                "status":
                    "INVALID_DECISION",

                "reason":
                    "Falta la oferta de recuperacion.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        if (
            offer.get(
                "protection"
            )
            == "NEVER_AUTO_SELL"
        ):

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_PROTECTED_PLAYER",

                "reason": (
                    "La oferta pertenece a un jugador "
                    "NEVER_AUTO_SELL."
                ),

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        offer_id = (
            offer.get(
                "offer_id"
            )
        )

        if offer_id is None:

            return {
                "action":
                    action,

                "status":
                    "INVALID_OFFER_ID",

                "reason":
                    "La oferta no tiene offer_id.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.accept_offer(
                offer_id=
                    int(
                        offer_id
                    ),

                execute=
                    True,
            )
        )

        return {
            "action":
                action,

            "status":
                (
                    "OFFER_ACCEPTED"
                    if result.get(
                        "success"
                    )
                    else "FAILED"
                ),

            "reason": (
                "Oferta aceptada para "
                f"{offer.get('player_name')}."
            ),

            "write_performed":
                True,

            "success":
                bool(
                    result.get(
                        "success",
                        False,
                    )
                ),

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "offer":
                offer,
        }

    # ========================================================
    # REROLL COMPUTER OFFER
    # ========================================================

    if action == REROLL_ACTION:

        data = (
            decision.get(
                "data",
                {},
            )
            or {}
        )

        requested_offer = (
            data.get(
                "offer",
                {},
            )
            or {}
        )

        offer_id = (
            requested_offer.get(
                "offer_id"
            )
        )

        if offer_id is None:

            return build_noop_result(
                decision=decision,
                status="INVALID_OFFER_ID",
                reason=(
                    "Reroll bloqueado: la decision no contiene "
                    "un offer_id valido."
                ),
                success=False,
            )

        # ----------------------------------------------------
        # READ-BEFORE-WRITE
        # ----------------------------------------------------

        try:

            (
                fresh_snapshot_file,
                fresh_snapshot,
            ) = (
                refresh_snapshot_for_write_revalidation()
            )

        except Exception as error:

            return build_noop_result(
                decision=decision,
                status="REVALIDATION_REFRESH_FAILED",
                reason=(
                    "No se pudo obtener un snapshot fresco antes "
                    f"del reroll: {type(error).__name__}: {error}"
                ),
                success=False,
            )

        validation = (
            revalidate_reroll_offer(
                snapshot=
                    fresh_snapshot,

                offer_id=
                    int(
                        offer_id
                    ),
            )
        )

        if not validation.get(
            "authorized",
            False,
        ):

            return {
                **build_noop_result(
                    decision=decision,
                    status=validation.get(
                        "status",
                        "REROLL_BLOCKED",
                    ),
                    reason=validation.get(
                        "reason",
                        "Reroll bloqueado por Safety Gate.",
                    ),
                    success=True,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,

                "revalidation":
                    validation,
            }

        fresh_offer = (
            validation.get(
                "offer",
                {},
            )
            or {}
        )

        player_ids = (
            fresh_offer.get(
                "player_ids",
                [],
            )
            or []
        )

        if len(player_ids) != 1:

            return {
                **build_noop_result(
                    decision=decision,
                    status="INVALID_REROLL_PLAYER",
                    reason=(
                        "Reroll bloqueado: la oferta fresca no "
                        "contiene exactamente un jugador."
                    ),
                    success=False,
                ),

                "revalidation_snapshot":
                    fresh_snapshot_file,
            }

        player_id = int(
            player_ids[
                0
            ]
        )

        # ----------------------------------------------------
        # UNICA ESCRITURA REAL DEL CICLO
        # ----------------------------------------------------

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.reject_offer(
                offer_id=
                    int(
                        offer_id
                    ),

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        if success:

            record_reroll(
                player_id=
                    player_id,

                offer_id=
                    int(
                        offer_id
                    ),
            )

        return {
            "action":
                action,

            "status":
                (
                    "OFFER_REROLLED"
                    if success
                    else "FAILED"
                ),

            "reason":
                (
                    "Oferta Computer rechazada tras revalidacion "
                    "fresca. El jugador permanece publicado y "
                    "esperara un nuevo ciclo Computer."
                    if success
                    else
                    "Biwenger no confirmo el rechazo de la oferta."
                ),

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "offer":
                fresh_offer,

            "player_id":
                player_id,

            "revalidation_snapshot":
                fresh_snapshot_file,

            "revalidation":
                validation,
        }

    # ========================================================
    # GUARDAR XI
    # ========================================================

    if action == "SAVE_LINEUP":

        monitor = (
            (
                decision.get(
                    "data",
                    {},
                )
                or {}
            )
            .get(
                "lineup_monitor",
                {},
            )
            or {}
        )

        lineup = (
            monitor.get(
                "lineup",
                {},
            )
            or {}
        )

        selected = (
            lineup.get(
                "selected",
                [],
            )
            or []
        )

        if len(
            selected
        ) != 11:

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_INCOMPLETE_LINEUP",

                "reason":
                    "El XI no contiene exactamente 11 jugadores.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        if int(
            lineup.get(
                "playable_count",
                0,
            )
            or 0
        ) < 11:

            return {
                "action":
                    action,

                "status":
                    "BLOCKED_INVALID_LINEUP",

                "reason": (
                    "El XI contiene 11 nombres, pero no "
                    "11 jugadores validos para la jornada."
                ),

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        player_ids = [
            int(
                player[
                    "id"
                ]
            )

            for player in selected
        ]

        formation = (
            lineup.get(
                "formation_name"
            )
        )

        if not formation:

            return {
                "action":
                    action,

                "status":
                    "INVALID_FORMATION",

                "reason":
                    "La formacion no esta disponible.",

                "write_performed":
                    False,

                "success":
                    False,

                "http_status":
                    None,

                "response":
                    None,
            }

        writer = (
            BiwengerWriteClient()
        )

        result = (
            writer.save_lineup(
                player_ids=
                    player_ids,

                formation=
                    formation,

                reserve_ids=
                    [],

                execute=
                    True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        if success:

            save_lineup_monitor_state(
                lineup
            )

        return {
            "action":
                action,

            "status":
                (
                    "LINEUP_SAVED"
                    if success
                    else "FAILED"
                ),

            "reason":
                "Actualizacion del XI recomendado.",

            "write_performed":
                True,

            "success":
                success,

            "http_status":
                result.get(
                    "http_status"
                ),

            "response":
                result.get(
                    "response"
                ),

            "formation":
                formation,

            "player_ids":
                player_ids,
        }

    return {
        "action":
            action,

        "status":
            "UNSUPPORTED_AUTOPILOT_ACTION",

        "reason": (
            "Esta accion aun no tiene executor LIVE "
            "dentro del Autopilot v3."
        ),

        "write_performed":
            False,

        "success":
            False,

        "http_status":
            None,

        "response":
            None,
    }
