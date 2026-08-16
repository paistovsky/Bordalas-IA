from src.analysis.portfolio_optimizer import (
    optimize_portfolio,
)

from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

from src.analysis.sales_analyzer import (
    analyze_sales,
)


MIN_SALE_SCORE = 40


def build_roster_plan(
    snapshot: dict,
) -> dict:

    purchase_plan = (
        optimize_portfolio(
            snapshot
        )
    )

    sales = analyze_sales(
        snapshot
    )

    selected_purchases = (
        purchase_plan[
            "selected"
        ]
    )

    purchase_cost = (
        purchase_plan[
            "total_cost"
        ]
    )

    balance = (
        purchase_plan[
            "balance"
        ]
    )

    cash_reserve = (
        purchase_plan[
            "cash_reserve"
        ]
    )

    # --------------------------------------------------
    # ¿NECESITAMOS VENDER PARA FINANCIAR?
    # --------------------------------------------------

    minimum_cash_after_purchases = (
        balance
        - purchase_cost
    )

    liquidity_shortfall = max(
        cash_reserve
        - minimum_cash_after_purchases,
        0,
    )

    recommended_sales = []
    optional_sales = []

    # --------------------------------------------------
    # GUARDARRAIL POSICIONAL
    # --------------------------------------------------
    #
    # Este bucle recorria las ventas ordenadas por sale_score y
    # acumulaba hasta cubrir el deficit, sin mirar de que posicion
    # era cada una. Con un deficit grande podia vaciar la porteria
    # o dejar la defensa en dos.
    #
    # El 16/08/2026 el plan salia legal -vendia un portero de dos-
    # pero por suerte: nada lo comprobaba.
    #
    # validate_sale_set mira el CONJUNTO, asi que hay que
    # preguntarle por la lista completa cada vez que se anade una
    # venta, no por la venta suelta.

    guardrail = build_position_guardrail(
        snapshot.get("my_team")
    )

    blocked_by_guardrail = []

    def sale_fits(candidate: dict, current: list) -> bool:

        tentative = [
            item["id"] for item in current
        ] + [candidate["id"]]

        verdict = validate_sale_set(
            guardrail,
            tentative,
        )

        if not verdict.get("ok"):
            blocked_by_guardrail.append(
                {
                    "id": candidate.get("id"),
                    "name": candidate.get("name"),
                    "reason": verdict.get("reason"),
                }
            )
            return False

        return True

    # --------------------------------------------------
    # VENTAS POR NECESIDAD DE LIQUIDEZ
    # --------------------------------------------------

    recovered = 0

    if liquidity_shortfall > 0:

        for player in sales:

            if (
                player["sale_score"]
                < MIN_SALE_SCORE
            ):
                continue

            if not sale_fits(
                player,
                recommended_sales,
            ):
                continue

            recommended_sales.append(
                player
            )

            recovered += (
                player["price"]
            )

            if (
                recovered
                >= liquidity_shortfall
            ):
                break

    # --------------------------------------------------
    # VENTAS OPCIONALES POR MEJORA DE PLANTILLA
    # --------------------------------------------------

    selected_sale_ids = {
        player["id"]
        for player
        in recommended_sales
    }

    for player in sales:

        if (
            player["id"]
            in selected_sale_ids
        ):
            continue

        if (
            player["sale_score"]
            < MIN_SALE_SCORE
        ):
            continue

        # Las opcionales se ejecutarian ADEMAS de las necesarias,
        # asi que se validan contra las dos listas juntas.
        if not sale_fits(
            player,
            recommended_sales + optional_sales,
        ):
            continue

        optional_sales.append(
            player
        )

    projected_balance = (
        balance
        - purchase_cost
        + sum(
            player["price"]
            for player
            in recommended_sales
        )
    )

    return {
        "balance":
            balance,

        "cash_reserve":
            cash_reserve,

        "selected_purchases":
            selected_purchases,

        "purchase_cost":
            purchase_cost,

        "liquidity_shortfall":
            liquidity_shortfall,

        "recommended_sales":
            recommended_sales,

        "optional_sales":
            optional_sales,

        "projected_balance":
            projected_balance,

        "position_guardrail":
            guardrail,

        "blocked_by_guardrail":
            blocked_by_guardrail,
    }