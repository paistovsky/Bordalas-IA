import argparse

from src.actions.franchise_executor import (
    build_next_franchise_action,
    execute_single_franchise_action,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.collectors.league_collector import (
    collect_league_snapshot,
)


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


# ======================================================
# SNAPSHOT
# ======================================================


def get_snapshot(
    refresh: bool,
) -> tuple[
    str,
    dict,
]:

    if refresh:

        print()
        print(
            "Actualizando Biwenger..."
        )

        print()

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


# ======================================================
# MOSTRAR ACCIÓN
# ======================================================


def print_action(
    action: dict,
) -> None:

    print()
    print("=" * 90)
    print(
        "             BORDALÁS IA - LIVE FRANCHISE"
    )
    print("=" * 90)

    validation = (
        action.get(
            "validation",
            {},
        )
        or {}
    )

    print()
    print(
        f"Validación: "
        f"{validation.get('status')}"
    )

    print(
        validation.get(
            "reason",
            "",
        )
    )

    print()

    action_name = (
        action[
            "action"
        ]
    )

    if action_name == "CANCEL_BID":

        print(
            "SIGUIENTE OPERACIÓN"
        )

        print(
            "-" * 90
        )

        print()
        print(
            "CANCELAR PUJA"
        )

        print()

        print(
            f"Jugador:      "
            f"{action['player_name']}"
        )

        print(
            f"Player ID:    "
            f"{action['player_id']}"
        )

        print(
            f"Offer ID:     "
            f"{action['offer_id']}"
        )

        print(
            f"Importe:      "
            f"{money(action['amount'])}"
        )

        print(
            f"Puja máxima:  "
            f"{money(action['maximum_bid'])}"
        )

        print(
            f"Objetivo:     "
            f"{money(action['target_bid'])}"
        )

        print(
            f"Falta liberar:"
            f" {money(action['required_unlock'])}"
        )

    elif action_name == "PLACE_FRANCHISE_BID":

        target = (
            action[
                "target"
            ]
        )

        print(
            "SIGUIENTE OPERACIÓN"
        )

        print(
            "-" * 90
        )

        print()
        print(
            "PUJAR POR FRANCHISE"
        )

        print()

        print(
            f"Jugador:      "
            f"{target['name']}"
        )

        print(
            f"Player ID:    "
            f"{target['id']}"
        )

        print(
            f"Puja:         "
            f"{money(action['amount'])}"
        )

        print(
            f"Puja máxima:  "
            f"{money(action['maximum_bid'])}"
        )

        print(
            f"Saldo teórico:"
            f" {money(action['projected_balance'])}"
        )

        print(
            f"Deuda:        "
            f"{money(action['projected_debt'])}"
        )

        print(
            f"Liquidez:     "
            f"{money(action['recoverable_cash'])}"
        )

    elif action_name == "ABORT":

        print(
            "ABORTAR"
        )

        print()

        print(
            validation.get(
                "reason",
                "",
            )
        )

    else:

        print(
            f"Acción: "
            f"{action_name}"
        )

    print()
    print("=" * 90)


# ======================================================
# MAIN
# ======================================================


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Ejecutor Franchise "
            "de Bordalás IA."
        )
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Ejecuta UNA única "
            "operación real."
        ),
    )

    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help=(
            "Usa el último snapshot "
            "sin consultar Biwenger."
        ),
    )

    args = (
        parser.parse_args()
    )

    (
        snapshot_file,
        snapshot,
    ) = get_snapshot(
        refresh=
            not args.no_refresh
    )

    print()
    print(
        f"Snapshot: "
        f"{snapshot_file}"
    )

    print()
    print(
        "Calculando siguiente acción..."
    )

    action = (
        build_next_franchise_action(
            snapshot
        )
    )

    print_action(
        action
    )

    # ==================================================
    # DRY RUN
    # ==================================================

    if not args.live:

        print()
        print(
            "MODO DRY-RUN"
        )

        print(
            "No se ha modificado Biwenger."
        )

        return

    # ==================================================
    # ACCIÓN NO EJECUTABLE
    # ==================================================

    if action[
        "action"
    ] in {
        "ABORT",
        "WAIT",
    }:

        print()
        print(
            "No existe una operación "
            "autorizada para ejecutar."
        )

        return

    # ==================================================
    # CONFIRMACIÓN
    # ==================================================

    print()
    print(
        "*** MODO LIVE ***"
    )

    print()

    print(
        "Se ejecutará exactamente UNA "
        "operación real."
    )

    print()

    print(
        "Después será obligatorio "
        "refrescar y recalcular."
    )

    print()

    print(
        "Escribe EJECUTAR para continuar:"
    )

    answer = input(
        "> "
    ).strip()

    if answer != "EJECUTAR":

        print()
        print(
            "Operación cancelada."
        )

        return

    # ==================================================
    # EJECUCIÓN
    # ==================================================

    result = (
        execute_single_franchise_action(
            snapshot=
                snapshot,

            execute=True,
        )
    )

    print()
    print("=" * 90)
    print(
        "RESULTADO"
    )
    print("=" * 90)

    print()

    print(
        f"Acción:    "
        f"{result['action']}"
    )

    print(
        f"Estado:    "
        f"{result['status']}"
    )

    print(
        f"Ejecutada: "
        f"{'SÍ' if result['executed'] else 'NO'}"
    )

    print(
        f"Éxito:     "
        f"{'SÍ' if result['success'] else 'NO'}"
    )

    write_result = (
        result.get(
            "write_result"
        )
    )

    if write_result:

        print(
            f"HTTP:      "
            f"{write_result.get('http_status')}"
        )

    print()

    if result[
        "success"
    ]:

        print(
            "OPERACIÓN COMPLETADA."
        )

        print()

        print(
            "IMPORTANTE:"
        )

        print(
            "No ejecutes una segunda operación "
            "utilizando este snapshot."
        )

        print()

        print(
            "Vuelve a lanzar live_franchise."
        )

        print(
            "Bordalás refrescará Biwenger "
            "y recalculará el siguiente paso."
        )

    else:

        print(
            "La operación no se completó "
            "correctamente."
        )

        print(
            "No se debe continuar con el "
            "siguiente paso."
        )

    print()
    print("=" * 90)


if __name__ == "__main__":
    main()