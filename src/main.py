from src.analysis.lineup_engine import build_lineup
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.analysis.transaction_planner import (
    POSITION_NAMES,
    simulate_transactions,
)
from src.collectors.league_collector import (
    collect_league_snapshot,
)


def print_header(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    print_header(
        "                         BORDALÁS IA"
    )

    # ==================================================
    # 1. ACTUALIZAR DATOS
    # ==================================================

    print()
    print("Actualizando datos de Biwenger...")
    print()

    collect_league_snapshot()

    # ==================================================
    # 2. CARGAR SNAPSHOT MÁS RECIENTE
    # ==================================================

    snapshot_file = get_latest_snapshot()
    snapshot = load_snapshot(snapshot_file)

    print()
    print(f"Snapshot utilizado: {snapshot_file}")

    # ==================================================
    # 3. ESTADO ACTUAL DEL XI
    # ==================================================

    lineup = build_lineup(snapshot)

    print_header(
        "                     ESTADO DE LA JORNADA"
    )

    print()
    print(
        f"Jugadores alineables: "
        f"{lineup['total_selected']}/11"
    )

    print(
        f"Con partido:          "
        f"{lineup['playable_count']}/11"
    )

    print(
        f"Sin partido:          "
        f"{lineup['unavailable_count']}/11"
    )

    print()
    print("NECESIDADES URGENTES")
    print("-" * 80)

    shortages_total = 0

    for position_id, missing in (
        lineup["matchday_shortages"].items()
    ):
        shortages_total += missing

        print(
            f"{POSITION_NAMES[position_id]:<18}"
            f"{missing}"
        )

    if shortages_total == 0:
        print()
        print(
            "Puedes presentar un XI completo "
            "con partido."
        )

    else:
        print()
        print(
            f"Faltan {shortages_total} jugadores "
            "con partido para completar el XI."
        )

    # ==================================================
    # 4. PLAN GLOBAL DE OPERACIONES
    # ==================================================

    plan = simulate_transactions(snapshot)

    print_header(
        "                     PLAN DE OPERACIONES"
    )

    # --------------------------------------------------
    # COMPRAS
    # --------------------------------------------------

    print()
    print("COMPRAS RECOMENDADAS")
    print("-" * 80)

    if not plan["purchases"]:
        print("Ninguna.")

    else:
        for player in plan["purchases"]:

            risk = player.get(
                "external_risk",
                0,
            )

            print(
                f"{player['name']:<22}"
                f"{player['suggested_bid']:>12,} €"
                f"   Score "
                f"{player['intelligent_score']:>3}/100"
                f"   Riesgo {risk}"
            )

    # --------------------------------------------------
    # VENTAS NECESARIAS
    # --------------------------------------------------

    print()
    print("VENTAS NECESARIAS")
    print("-" * 80)

    if not plan["mandatory_sales"]:
        print(
            "Ninguna venta necesaria "
            "para financiar las compras."
        )

    else:
        for player in plan["mandatory_sales"]:

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
                f"   Sale score "
                f"{player['sale_score']:>3}/100"
            )

    # --------------------------------------------------
    # VENTAS OPCIONALES
    # --------------------------------------------------

    print()
    print("VENTAS OPCIONALES SEGURAS")
    print("-" * 80)

    if not plan["safe_optional_sales"]:
        print("Ninguna.")

    else:
        for player in plan[
            "safe_optional_sales"
        ]:

            print(
                f"{player['name']:<22}"
                f"{player['price']:>12,} €"
                f"   Sale score "
                f"{player['sale_score']:>3}/100"
            )

            for reason in player["reasons"]:
                print(
                    f"   - {reason}"
                )

    # ==================================================
    # 5. PLANTILLA PROYECTADA
    # ==================================================

    print_header(
        "                    PLANTILLA PROYECTADA"
    )

    print()
    print(
        f"Plantilla actual:       "
        f"{plan['original_count']}"
    )

    print(
        f"Tras compras:           "
        f"{plan['projected_count_before_optional']}"
    )

    print(
        f"Tras ventas opcionales: "
        f"{plan['projected_count_after_optional']}"
    )

    print()
    print("DISTRIBUCIÓN FINAL")
    print("-" * 80)

    for position_id in [
        1,
        2,
        3,
        4,
    ]:

        print(
            f"{POSITION_NAMES[position_id]:<18}"
            f"{plan['final_position_counts'][position_id]}"
        )

    # ==================================================
    # 6. ECONOMÍA
    # ==================================================

    print_header(
        "                         ECONOMÍA"
    )

    current_balance = (
        snapshot["market"]
        ["status"]
        ["balance"]
    )

    purchase_cost = sum(
        player["suggested_bid"]
        for player in plan["purchases"]
    )

    print()
    print(
        f"Saldo actual:             "
        f"{current_balance:>12,} €"
    )

    print(
        f"Coste compras:            "
        f"{purchase_cost:>12,} €"
    )

    print(
        f"Saldo tras compras:       "
        f"{plan['projected_balance_without_optional']:>12,} €"
    )

    print(
        f"Ingresos ventas opcionales:"
        f"{plan['optional_sale_income']:>11,} €"
    )

    print(
        f"SALDO FINAL PROYECTADO:   "
        f"{plan['projected_balance_with_optional']:>12,} €"
    )

    print_header(
        "                 BORDALÁS IA - FIN DEL ANÁLISIS"
    )

    print()


if __name__ == "__main__":
    main()