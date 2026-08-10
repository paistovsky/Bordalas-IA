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
