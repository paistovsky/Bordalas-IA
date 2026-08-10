import argparse

from src.actions.action_plan import build_action_plan
from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)
from src.collectors.league_collector import (
    collect_league_snapshot,
)


POSITION_NAMES = {
    1: "POR",
    2: "DEF",
    3: "MC",
    4: "DEL",
}


def print_separator() -> None:
    print("-" * 80)


def print_header(
    text: str,
) -> None:

    print()
    print("=" * 80)
    print(text)
    print("=" * 80)


def run_dry_run(
    refresh: bool = True,
) -> None:

    print_header(
        "                BORDALÁS IA - ACTION ENGINE"
    )

    print()
    print("MODO: DRY-RUN")
    print(
        "No se modificará nada en Biwenger."
    )

    # ==================================================
    # ACTUALIZAR DATOS
    # ==================================================

    if refresh:

        print()
        print(
            "Actualizando datos antes de decidir..."
        )
        print()

        collect_league_snapshot()

    # ==================================================
    # SNAPSHOT
    # ==================================================

    snapshot_file = (
        get_latest_snapshot()
    )

    snapshot = load_snapshot(
        snapshot_file
    )

    print()
    print(
        f"Snapshot: {snapshot_file}"
    )

    # ==================================================
    # GENERAR PLAN
    # ==================================================

    print()
    print(
        "Construyendo plan ejecutable..."
    )

    plan = build_action_plan(
        snapshot
    )

    # ==================================================
    # PUJAS
    # ==================================================

    print_header(
        "PUJAS QUE BORDALÁS IA REALIZARÍA"
    )

    if not plan["bids"]:

        print()
        print("Ninguna.")

    else:

        for index, bid in enumerate(
            plan["bids"],
            start=1,
        ):

            print()
            print(
                f"{index}. "
                f"{bid['player_name']}"
            )

            print(
                f"   Player ID: "
                f"{bid['player_id']}"
            )

            print(
                f"   Puja:      "
                f"{bid['amount']:,} €"
            )

            print(
                f"   Score:     "
                f"{bid['score']}/100"
            )

            print(
                f"   Riesgo:    "
                f"{bid['external_risk']}"
            )

            print_separator()

    # ==================================================
    # VENTAS NECESARIAS
    # ==================================================

    print_header(
        "VENTAS OBLIGATORIAS"
    )

    if not plan[
        "mandatory_sales"
    ]:

        print()
        print("Ninguna.")

    else:

        for sale in plan[
            "mandatory_sales"
        ]:

            print()
            print(
                sale[
                    "player_name"
                ]
            )

            print(
                f"   Player ID: "
                f"{sale['player_id']}"
            )

            print(
                f"   Valor:     "
                f"{sale['estimated_value']:,} €"
            )

            print(
                f"   Sale score:"
                f" "
                f"{sale['sale_score']}/100"
            )

            print_separator()

    # ==================================================
    # VENTAS OPCIONALES
    # ==================================================

    print_header(
        "VENTAS OPCIONALES SEGURAS"
    )

    if not plan[
        "optional_sales"
    ]:

        print()
        print("Ninguna.")

    else:

        for sale in plan[
            "optional_sales"
        ]:

            print()
            print(
                sale[
                    "player_name"
                ]
            )

            print(
                f"   Player ID: "
                f"{sale['player_id']}"
            )

            print(
                f"   Valor:     "
                f"{sale['estimated_value']:,} €"
            )

            print(
                f"   Sale score:"
                f" "
                f"{sale['sale_score']}/100"
            )

            if sale[
                "reasons"
            ]:

                print(
                    "   Motivos:"
                )

                for reason in sale[
                    "reasons"
                ]:

                    print(
                        f"     - {reason}"
                    )

            print_separator()

    # ==================================================
    # ALINEACIÓN
    # ==================================================

    print_header(
        "ALINEACIÓN QUE GUARDARÍA"
    )

    for player in plan[
        "lineup"
    ]:

        position = (
            POSITION_NAMES.get(
                player[
                    "position"
                ],
                "?",
            )
        )

        game_status = (
            "PARTIDO"
            if player[
                "has_game"
            ]
            else "SIN PARTIDO"
        )

        print(
            f"{position:<4}"
            f"{player['player_name']:<24}"
            f"{game_status}"
        )

    # ==================================================
    # ECONOMÍA
    # ==================================================

    print_header(
        "ECONOMÍA DEL PLAN"
    )

    economy = plan[
        "economy"
    ]

    print()
    print(
        f"Saldo actual:       "
        f"{economy['current_balance']:>12,} €"
    )

    print(
        f"Pujas totales:      "
        f"{economy['purchase_cost']:>12,} €"
    )

    print(
        f"Saldo proyectado:   "
        f"{economy['projected_balance']:>12,} €"
    )

    # ==================================================
    # RESUMEN
    # ==================================================

    print_header(
        "RESUMEN DEL DRY-RUN"
    )

    summary = plan[
        "summary"
    ]

    print()
    print(
        f"Pujas:              "
        f"{summary['bid_count']}"
    )

    print(
        f"Ventas obligatorias:"
        f" "
        f"{summary['mandatory_sale_count']}"
    )

    print(
        f"Ventas opcionales:  "
        f"{summary['optional_sale_count']}"
    )

    print(
        f"Jugadores alineados:"
        f" "
        f"{summary['lineup_count']}"
    )

    print()
    print(
        "NO SE HA REALIZADO NINGUNA "
        "OPERACIÓN EN BIWENGER."
    )

    print_header(
        "               FIN DEL DRY-RUN"
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Bordalás IA Action Engine"
        )
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help=(
            "Usa el último snapshot "
            "sin consultar Biwenger."
        ),
    )

    args = parser.parse_args()

    run_dry_run(
        refresh=not args.no_refresh
    )


if __name__ == "__main__":
    main()