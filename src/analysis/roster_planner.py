from src.analysis.portfolio_optimizer import (
    optimize_portfolio,
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
            >= MIN_SALE_SCORE
        ):
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
    }