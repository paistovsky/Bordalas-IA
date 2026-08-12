from __future__ import annotations

from typing import Any

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)

from src.analysis.offer_decision_engine import (
    build_offer_decision_board,
)

from src.analysis.negotiation_state_engine import (
    empty_state,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


SUPPORTED_LIVE_ACTIONS = {
    "COUNTER_OFFER",
    "ACCEPT_NOW",
    "ACCEPT_SACRIFICE_LINEUP",
}


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def noop(
    *,
    action: str | None,
    status: str,
    reason: str,
    success: bool = True,
    extra: dict | None = None,
) -> dict:

    return {
        "action":
            action,

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

        **(
            extra
            or {}
        ),
    }


def refresh_snapshot() -> tuple[str, dict]:
    """
    Read-before-write obligatorio.
    """

    collect_league_snapshot()

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = (
        load_snapshot(
            snapshot_file
        )
    )

    return (
        snapshot_file,
        snapshot,
    )


def find_fresh_manager_decision(
    *,
    snapshot: dict,
    offer_id: int,
    rival_intelligence: dict,
) -> dict | None:
    """
    Recalcula la oferta con snapshot fresco.

    Usamos empty_state() deliberadamente para la REVALIDACION:
    la idempotencia ya fue autorizada por el Safety Gate del ciclo.
    Aqui solo queremos confirmar que la oferta sigue existiendo y
    que Competitive sigue llegando a la misma decision economica.
    """

    board = (
        build_offer_decision_board(
            snapshot=
                snapshot,

            rival_intelligence=
                rival_intelligence,

            negotiation_state=
                empty_state(),
        )
    )

    for decision in (
        board.get(
            "decisions",
            [],
        )
        or []
    ):

        if (
            decision.get(
                "counterparty_type"
            )
            !=
            "MANAGER"
        ):
            continue

        if safe_int(
            decision.get(
                "offer_id"
            )
        ) == safe_int(
            offer_id
        ):

            return decision

    return None


def execute_competitive_live_action(
    *,
    selected_offer: dict | None,
    rival_intelligence: dict,
    execute: bool = False,
) -> dict:
    """
    V2.0 Competitive Live Controlado.

    Maximo UNA llamada de escritura por invocacion.

    - Sin selected_offer: no-op.
    - execute=False: DRY RUN.
    - execute=True: snapshot fresco, recalculo Competitive y SOLO entonces
      counter/accept.
    """

    selected_offer = (
        selected_offer
        or {}
    )

    action = str(
        selected_offer.get(
            "authoritative_decision"
        )
        or
        selected_offer.get(
            "competitive_decision"
        )
        or
        ""
    )

    offer_id = safe_int(
        selected_offer.get(
            "offer_id"
        )
    )

    original_amount = safe_int(
        selected_offer.get(
            "amount"
        )
    )

    expected_player_id = safe_int(
        selected_offer.get(
            "player_id"
        )
    )

    expected_rival_id = safe_int(
        selected_offer.get(
            "rival_user_id"
        )
    )

    requested_counter = safe_int(
        selected_offer.get(
            "authoritative_counter_amount"
        )
        or
        selected_offer.get(
            "counter_amount"
        )
    )

    if not selected_offer:

        return noop(
            action=
                None,

            status=
                "NO_COMPETITIVE_ACTION",

            reason=
                "No hay accion competitiva seleccionada.",
        )

    if action not in SUPPORTED_LIVE_ACTIONS:

        return noop(
            action=
                action,

            status=
                "UNSUPPORTED_COMPETITIVE_ACTION",

            reason=
                f"V2.0 no permite ejecutar {action}.",
        )

    if offer_id <= 0:

        return noop(
            action=
                action,

            status=
                "INVALID_OFFER_ID",

            reason=
                "La accion competitiva no contiene offer_id valido.",

            success=
                False,
        )

    if not execute:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_DRY_RUN",

            reason=(
                "V2.0 ha recibido una accion competitiva valida, "
                "pero execute=False."
            ),

            extra={
                "offer_id":
                    offer_id,

                "counter_amount":
                    (
                        requested_counter
                        if action == "COUNTER_OFFER"
                        else None
                    ),
            },
        )

    # =====================================================
    # READ BEFORE WRITE
    # =====================================================

    try:

        (
            fresh_snapshot_file,
            fresh_snapshot,
        ) = refresh_snapshot()

    except Exception as error:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_REVALIDATION_REFRESH_FAILED",

            reason=(
                "No se pudo obtener snapshot fresco: "
                f"{type(error).__name__}: {error}"
            ),

            success=
                False,
        )

    fresh = (
        find_fresh_manager_decision(
            snapshot=
                fresh_snapshot,

            offer_id=
                offer_id,

            rival_intelligence=
                rival_intelligence,
        )
    )

    if fresh is None:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_OFFER_NO_LONGER_EXISTS",

            reason=
                "La oferta ya no existe en el snapshot fresco.",

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,
            },
        )

    fresh_amount = safe_int(
        fresh.get(
            "amount"
        )
    )

    fresh_player_id = safe_int(
        fresh.get(
            "player_id"
        )
    )

    fresh_rival_id = safe_int(
        fresh.get(
            "counterparty_id"
        )
    )

    if fresh_amount != original_amount:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_RIVAL_AMOUNT_CHANGED",

            reason=(
                "El rival ha cambiado el importe durante la revalidacion. "
                "Se aborta para recalcular en el siguiente ciclo."
            ),

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,

                "old_amount":
                    original_amount,

                "fresh_amount":
                    fresh_amount,
            },
        )

    if (
        expected_player_id > 0
        and
        fresh_player_id
        !=
        expected_player_id
    ):

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_PLAYER_MISMATCH",

            reason=
                "La oferta fresca ya no corresponde al mismo jugador.",

            success=
                False,

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,
            },
        )

    if (
        expected_rival_id > 0
        and
        fresh_rival_id
        !=
        expected_rival_id
    ):

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_RIVAL_MISMATCH",

            reason=
                "La oferta fresca ya no corresponde al mismo rival.",

            success=
                False,

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,
            },
        )

    fresh_competitive = (
        fresh.get(
            "competitive_observer",
            {},
        )
        or {}
    )

    fresh_action = str(
        fresh_competitive.get(
            "decision"
        )
        or ""
    )

    fresh_strategic_price = safe_int(
        fresh_competitive.get(
            "strategic_sell_price"
        )
    )

    fresh_counter = safe_int(
        fresh_competitive.get(
            "counter_amount"
        )
    )

    if fresh_action != action:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_DECISION_CHANGED",

            reason=(
                f"Competitive ha cambiado de {action} a {fresh_action} "
                "en el snapshot fresco."
            ),

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,

                "fresh_decision":
                    fresh_action,
            },
        )

    # =====================================================
    # ESCRITURA UNICA
    # =====================================================

    writer = (
        BiwengerWriteClient()
    )

    if action == "COUNTER_OFFER":

        if fresh_counter <= 0:

            return noop(
                action=
                    action,

                status=
                    "INVALID_FRESH_COUNTER",

                reason=
                    "Competitive ya no produce una contraoferta valida.",

                success=
                    False,

                extra={
                    "revalidation_snapshot":
                        fresh_snapshot_file,
                },
            )

        # Siempre usamos el precio FRESCO, no el calculado minutos antes.
        result = (
            writer.counter_offer(
                offer_id=
                    offer_id,

                amount=
                    fresh_counter,

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

        return {
            "action":
                action,

            "status":
                (
                    "COMPETITIVE_COUNTER_SENT"
                    if success
                    else "FAILED"
                ),

            "reason":(
                f"Contraoferta competitiva enviada por "
                f"{fresh_counter:,} EUR tras revalidacion fresca."
                if success
                else
                "Biwenger no confirmo la contraoferta."
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

            "offer_id":
                offer_id,

            "player_id":
                fresh_player_id,

            "rival_user_id":
                fresh_rival_id,

            "counter_amount":
                fresh_counter,

            "strategic_sell_price":
                fresh_strategic_price,

            "revalidation_snapshot":
                fresh_snapshot_file,
        }

    # ACCEPT_NOW / ACCEPT_SACRIFICE_LINEUP
    if fresh_amount < fresh_strategic_price:

        return noop(
            action=
                action,

            status=
                "COMPETITIVE_ACCEPT_BELOW_FRESH_STRATEGIC",

            reason=(
                "La oferta fresca no alcanza el precio estrategico "
                "recalculado; aceptacion bloqueada."
            ),

            extra={
                "revalidation_snapshot":
                    fresh_snapshot_file,

                "fresh_amount":
                    fresh_amount,

                "fresh_strategic_price":
                    fresh_strategic_price,
            },
        )

    result = (
        writer.accept_offer(
            offer_id=
                offer_id,

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

    return {
        "action":
            action,

        "status":
            (
                "COMPETITIVE_OFFER_ACCEPTED"
                if success
                else "FAILED"
            ),

        "reason":(
            "Oferta rival aceptada tras revalidacion Competitive fresca."
            if success
            else
            "Biwenger no confirmo la aceptacion."
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

        "offer_id":
            offer_id,

        "player_id":
            fresh_player_id,

        "rival_user_id":
            fresh_rival_id,

        "accepted_amount":
            fresh_amount,

        "strategic_sell_price":
            fresh_strategic_price,

        "revalidation_snapshot":
            fresh_snapshot_file,
    }
