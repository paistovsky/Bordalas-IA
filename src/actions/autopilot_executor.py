from src.analysis.lineup_monitor import (
    save_lineup_monitor_state,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def build_noop_result(
    decision: dict,
    status: str,
    reason: str,
) -> dict:

    return {
        "action": decision.get("action"),
        "status": status,
        "reason": reason,
        "write_performed": False,
        "success": True,
        "http_status": None,
        "response": None,
    }


def execute_autopilot_decision(
    decision: dict,
    execute: bool = False,
) -> dict:
    """
    Ejecuta como maximo UNA escritura real.

    Acciones soportadas:
    - LIST_FOR_LIQUIDITY
    - ACCEPT_RECOVERY_OFFER
    - SAVE_LINEUP

    El flujo Franchise existente se mantiene fuera de este
    executor hasta integrarlo explicitamente.
    """

    action = decision.get("action")

    if not decision.get("executable", False):
        return build_noop_result(
            decision=decision,
            status="NOT_EXECUTABLE",
            reason="La decision global no requiere una escritura.",
        )

    if not execute:
        return build_noop_result(
            decision=decision,
            status="DRY_RUN",
            reason="Observer: no se ha modificado Biwenger.",
        )

    if action == "LIST_FOR_LIQUIDITY":
        player = (decision.get("data", {}) or {}).get("player")

        if not player:
            return {
                "action": action,
                "status": "INVALID_DECISION",
                "reason": "Falta el jugador a publicar.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        player_id = int(player["id"])
        price = int(player["listing_price"])

        if price <= 0:
            return {
                "action": action,
                "status": "INVALID_PRICE",
                "reason": "El precio de publicacion no es valido.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        writer = BiwengerWriteClient()
        result = writer.list_player_for_sale(
            player_id=player_id,
            price=price,
            execute=True,
        )

        return {
            "action": action,
            "status": "LISTED" if result.get("success") else "FAILED",
            "reason": f"Publicacion de {player.get('name')}.",
            "write_performed": True,
            "success": bool(result.get("success", False)),
            "http_status": result.get("http_status"),
            "response": result.get("response"),
            "player": player,
        }

    if action == "ACCEPT_RECOVERY_OFFER":
        offer = (decision.get("data", {}) or {}).get("offer")

        if not offer:
            return {
                "action": action,
                "status": "INVALID_DECISION",
                "reason": "Falta la oferta de recuperacion.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        if offer.get("protection") == "NEVER_AUTO_SELL":
            return {
                "action": action,
                "status": "BLOCKED_PROTECTED_PLAYER",
                "reason": "La oferta pertenece a un jugador NEVER_AUTO_SELL.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        offer_id = offer.get("offer_id")

        if offer_id is None:
            return {
                "action": action,
                "status": "INVALID_OFFER_ID",
                "reason": "La oferta no tiene offer_id.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        writer = BiwengerWriteClient()
        result = writer.accept_offer(
            offer_id=int(offer_id),
            execute=True,
        )

        return {
            "action": action,
            "status": "OFFER_ACCEPTED" if result.get("success") else "FAILED",
            "reason": f"Oferta aceptada para {offer.get('player_name')}.",
            "write_performed": True,
            "success": bool(result.get("success", False)),
            "http_status": result.get("http_status"),
            "response": result.get("response"),
            "offer": offer,
        }

    if action == "SAVE_LINEUP":
        monitor = (decision.get("data", {}) or {}).get("lineup_monitor", {}) or {}
        lineup = monitor.get("lineup", {}) or {}
        selected = lineup.get("selected", []) or []

        if len(selected) != 11:
            return {
                "action": action,
                "status": "BLOCKED_INCOMPLETE_LINEUP",
                "reason": "El XI no contiene exactamente 11 jugadores.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        player_ids = [int(player["id"]) for player in selected]
        formation = lineup.get("formation_name")

        if not formation:
            return {
                "action": action,
                "status": "INVALID_FORMATION",
                "reason": "La formacion no esta disponible.",
                "write_performed": False,
                "success": False,
                "http_status": None,
                "response": None,
            }

        writer = BiwengerWriteClient()
        result = writer.save_lineup(
            player_ids=player_ids,
            formation=formation,
            reserve_ids=[],
            execute=True,
        )

        success = bool(result.get("success", False))

        if success:
            save_lineup_monitor_state(lineup)

        return {
            "action": action,
            "status": "LINEUP_SAVED" if success else "FAILED",
            "reason": "Actualizacion del XI recomendado.",
            "write_performed": True,
            "success": success,
            "http_status": result.get("http_status"),
            "response": result.get("response"),
            "formation": formation,
            "player_ids": player_ids,
        }

    return {
        "action": action,
        "status": "UNSUPPORTED_AUTOPILOT_ACTION",
        "reason": (
            "Esta accion aun no tiene executor LIVE "
            "dentro del Autopilot v2."
        ),
        "write_performed": False,
        "success": False,
        "http_status": None,
        "response": None,
    }
