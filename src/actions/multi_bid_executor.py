from typing import Any

from src.actions.live_bid_executor import (
    execute_bid,
    find_existing_offer,
    get_sale_for_player,
    get_seller_description,
    get_seller_id,
)
from src.biwenger.write_client import (
    BiwengerWriteClient,
)


def execute_bid_plan(
    bids: list[dict],
    execute: bool = False,
    stop_on_error: bool = True,
) -> dict[str, Any]:
    """
    Ejecuta un plan de pujas de forma secuencial.

    Antes de CADA jugador:
    - refresca mercado
    - comprueba que sigue disponible
    - detecta pujas existentes
    - comprueba vendedor
    - comprueba precio
    - comprueba puja máxima

    Después de cada puja real:
    - execute_bid vuelve a consultar el mercado
    - confirma que la oferta aparece

    En dry-run no modifica Biwenger.
    """

    writer = BiwengerWriteClient()

    results: list[dict] = []

    summary = {
        "total": len(bids),
        "executed": 0,
        "skipped": 0,
        "failed": 0,
        "results": results,
    }

    for index, bid in enumerate(
        bids,
        start=1,
    ):
        player_id = int(
            bid["player_id"]
        )

        player_name = bid.get(
            "player_name",
            f"ID {player_id}",
        )

        amount = int(
            bid["amount"]
        )

        result = {
            "index": index,
            "player_id": player_id,
            "player_name": player_name,
            "amount": amount,
            "status": None,
        }

        # ==============================================
        # MERCADO FRESCO
        # ==============================================

        try:
            market = (
                writer.client.get_market()
            )

            sale = get_sale_for_player(
                market,
                player_id,
            )

            # ==========================================
            # ¿YA HEMOS PUJADO?
            # ==========================================

            existing_offer = (
                find_existing_offer(
                    market,
                    player_id,
                )
            )

            if existing_offer is not None:
                result["status"] = (
                    "ALREADY_BID"
                )

                result["message"] = (
                    "Ya existe una puja activa."
                )

                summary["skipped"] += 1

                continue

            # ==========================================
            # ¿SIGUE EN MERCADO?
            # ==========================================

            if sale is None:
                result["status"] = (
                    "NOT_IN_MARKET"
                )

                result["message"] = (
                    "El jugador ya no está "
                    "en el mercado."
                )

                summary["skipped"] += 1

                continue

            seller_id = get_seller_id(
                sale
            )

            seller_description = (
                get_seller_description(
                    sale
                )
            )

            current_price = int(
                sale.get(
                    "price",
                    0,
                )
            )

            result["seller_id"] = (
                seller_id
            )

            result["seller"] = (
                seller_description
            )

            result["current_price"] = (
                current_price
            )

            # ==========================================
            # EJECUTAR PREFLIGHT + PUJA
            # ==========================================

            execution = execute_bid(
                player_id=player_id,
                amount=amount,
                expected_seller_id=seller_id,
                execute=execute,
            )

            result["details"] = execution

            if not execute:
                result["status"] = (
                    "DRY_RUN_OK"
                )

                result["message"] = (
                    "Preflight correcto."
                )

                continue

            if (
                execution.get("success")
                and
                execution.get(
                    "offer_detected_after"
                )
            ):
                result["status"] = (
                    "EXECUTED"
                )

                result["message"] = (
                    "Puja confirmada."
                )

                summary["executed"] += 1

            else:
                result["status"] = (
                    "FAILED"
                )

                result["message"] = (
                    "La API respondió pero "
                    "la puja no pudo confirmarse."
                )

                summary["failed"] += 1

                if stop_on_error:
                    break

        except Exception as error:
            result["status"] = "ERROR"

            result["message"] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            summary["failed"] += 1

            if stop_on_error:
                break

        finally:
            results.append(
                result
            )

    return summary