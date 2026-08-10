from typing import Any

from src.actions.live_sale_executor import (
    execute_sale_listing,
)
from src.analysis.sale_price_engine import (
    calculate_sale_price,
)


def execute_sale_plan(
    sales: list[dict],
    execute: bool = False,
    stop_on_error: bool = True,
) -> dict[str, Any]:
    """
    Procesa publicaciones en mercado una por una.

    Cada jugador pasa por:
    - Sale Price Engine
    - validación de plantilla actual
    - detección de publicación existente
    - publicación
    - comprobación posterior

    Publicar NO significa aceptar una venta.
    """

    results = []

    summary = {
        "total": len(sales),
        "executed": 0,
        "skipped": 0,
        "failed": 0,
        "results": results,
    }

    for index, player in enumerate(
        sales,
        start=1,
    ):
        player_id = player["id"]

        name = player["name"]

        pricing = calculate_sale_price(
            player
        )

        result = {
            "index": index,
            "player_id": player_id,
            "player_name": name,
            "sale_score":
                player["sale_score"],
            "pricing": pricing,
            "status": None,
        }

        # ==============================================
        # SALE PRICE ENGINE BLOQUEA PUBLICACIÓN
        # ==============================================

        if not pricing[
            "should_list"
        ]:
            result["status"] = (
                "NOT_RECOMMENDED"
            )

            result["message"] = (
                "Sale Price Engine "
                "recomienda NO LISTAR."
            )

            summary["skipped"] += 1

            results.append(
                result
            )

            continue

        price = pricing[
            "recommended_price"
        ]

        result[
            "recommended_price"
        ] = price

        # ==============================================
        # PREFLIGHT + EJECUCIÓN
        # ==============================================

        try:
            execution = (
                execute_sale_listing(
                    player_id=
                        player_id,
                    price=
                        price,
                    execute=
                        execute,
                )
            )

            result[
                "execution"
            ] = execution

            execution_status = (
                execution.get(
                    "status"
                )
            )

            if (
                execution_status
                == "ALREADY_LISTED"
            ):
                result["status"] = (
                    "ALREADY_LISTED"
                )

                result["message"] = (
                    "Ya está publicado "
                    "en el mercado."
                )

                summary[
                    "skipped"
                ] += 1

            elif not execute:
                result["status"] = (
                    "DRY_RUN_OK"
                )

                result["message"] = (
                    "Preflight correcto."
                )

            elif (
                execution.get(
                    "success"
                )
                and
                execution.get(
                    "listing_detected_after"
                )
            ):
                result["status"] = (
                    "EXECUTED"
                )

                result["message"] = (
                    "Jugador publicado "
                    "correctamente."
                )

                summary[
                    "executed"
                ] += 1

            else:
                result["status"] = (
                    "FAILED"
                )

                result["message"] = (
                    "No se pudo confirmar "
                    "la publicación."
                )

                summary[
                    "failed"
                ] += 1

                if stop_on_error:
                    results.append(
                        result
                    )
                    break

        except Exception as error:
            result["status"] = "ERROR"

            result["message"] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            summary[
                "failed"
            ] += 1

            if stop_on_error:
                results.append(
                    result
                )
                break

        results.append(
            result
        )

    return summary