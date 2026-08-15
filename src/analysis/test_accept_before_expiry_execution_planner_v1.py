from __future__ import annotations

import copy
from datetime import timedelta

from src.analysis.accept_before_expiry_execution_planner import (
    build_accept_before_expiry_execution_plan,
)

from src.analysis.computer_offer_reroll_engine import (
    now_utc,
)

from src.analysis.market_analyzer import (
    get_latest_snapshot,
    load_snapshot,
)

from src.analysis.solvency_engine import (
    SAFE_LIQUIDITY_BUFFER,
    build_solvency_state,
)


TARGET_SURPLUS = 1_000_000
URGENT_EXPIRY_HOURS = 2.0


def safe_int(
    value,
    default: int = 0,
) -> int:
    try:
        return int(
            value
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def resolve_offer_id(
    raw_offer: dict,
) -> int | None:

    for key in (
        "id",
        "offer_id",
    ):
        value = raw_offer.get(
            key
        )

        if value is None:
            continue

        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def set_balance(
    snapshot: dict,
    balance: int,
) -> None:

    snapshot.setdefault(
        "market",
        {},
    ).setdefault(
        "status",
        {},
    )[
        "balance"
    ] = int(
        balance
    )


def set_offer_expiry(
    snapshot: dict,
    offer_ids: set[int],
    hours_from_now: float,
) -> int:

    expiry_ts = int(
        (
            now_utc()
            + timedelta(
                hours=
                    hours_from_now,
            )
        ).timestamp()
    )

    changed = 0

    for raw_offer in (
        snapshot.get(
            "market",
            {},
        ).get(
            "offers",
            [],
        )
        or []
    ):

        offer_id = (
            resolve_offer_id(
                raw_offer
            )
        )

        if (
            offer_id is None
            or
            offer_id not in offer_ids
        ):
            continue

        raw_offer[
            "until"
        ] = expiry_ts

        changed += 1

    return changed


def main() -> None:

    snapshot_file = (
        get_latest_snapshot()
    )

    original = (
        load_snapshot(
            snapshot_file
        )
    )

    original_solvency = (
        build_solvency_state(
            original
        )
    )

    guarantee = (
        original_solvency.get(
            "solvency_guarantee",
            {},
        )
        or {}
    )

    guaranteed_recovery = safe_int(
        guarantee.get(
            "guaranteed_recovery"
        )
    )

    target_debt = (
        guaranteed_recovery
        - SAFE_LIQUIDITY_BUFFER
        - TARGET_SURPLUS
    )

    simulated = (
        copy.deepcopy(
            original
        )
    )

    set_balance(
        simulated,
        -target_debt,
    )

    pressured = (
        build_solvency_state(
            simulated
        )
    )

    reserved_ids = {
        int(
            offer_id
        )
        for offer_id in (
            (
                pressured.get(
                    "solvency_reservations",
                    {},
                )
                or {}
            ).get(
                "reserved_offer_ids",
                [],
            )
            or []
        )
        if offer_id is not None
    }

    changed = (
        set_offer_expiry(
            snapshot=
                simulated,

            offer_ids=
                reserved_ids,

            hours_from_now=
                URGENT_EXPIRY_HOURS,
        )
    )

    plan = (
        build_accept_before_expiry_execution_plan(
            snapshot=
                simulated,

            offer_ids=
                reserved_ids,
        )
    )

    print()
    print("=" * 126)
    print(
        "          BORDALAS IA - ACCEPT BEFORE EXPIRY EXECUTION PLANNER V1 - OBSERVER"
    )
    print("=" * 126)
    print()

    print(
        f"Snapshot:                    "
        f"{snapshot_file}"
    )

    print(
        f"Reservas simuladas:          "
        f"{len(reserved_ids)}"
    )

    print(
        f"Expiries modificados:        "
        f"{changed}"
    )

    print(
        f"Planner status:              "
        f"{plan.get('status')}"
    )

    print(
        f"Ready:                       "
        f"{plan.get('ready')}"
    )

    print()
    print(
        "## CANDIDATOS"
    )
    print()

    for item in (
        plan.get(
            "candidates",
            [],
        )
        or []
    ):

        simulation = (
            item.get(
                "simulation",
                {},
            )
            or {}
        )

        print(
            f"{', '.join(item.get('player_names', [])):<24} "
            f"{item.get('amount', 0):>12,.0f} EUR "
            f"damage={item.get('damage_score'):>8.2f} "
            f"protected={item.get('protected')} "
            f"sufficient={item.get('individually_sufficient')} "
            f"after={simulation.get('state_after')} "
            f"surplus={safe_int(simulation.get('surplus_after')):>12,.0f}"
        )

    print()
    print(
        "## SELECCION"
    )
    print()

    # El plan NO tiene una clave "selected": eso no existe en el
    # planner. Lo que devuelve es selected_offers (todas las que
    # hay que aceptar), first_offer y selected_plan con la
    # simulacion del conjunto.
    selected_offers = (
        plan.get(
            "selected_offers",
            [],
        )
        or []
    )

    selected_plan = (
        plan.get(
            "selected_plan",
            {},
        )
        or {}
    )

    required_accept_count = safe_int(
        plan.get(
            "required_accept_count"
        )
    )

    selected = (
        plan.get(
            "first_offer"
        )
        or {}
    )

    if selected:

        print(
            f"Jugador:                     "
            f"{', '.join(selected.get('player_names', []))}"
        )

        print(
            f"Offer ID:                    "
            f"{selected.get('offer_id')}"
        )

        print(
            f"Importe:                     "
            f"{selected.get('amount', 0):,.0f} EUR"
        )

        print(
            f"Damage score:                "
            f"{selected.get('damage_score')}"
        )

        simulation = (
            selected.get(
                "simulation",
                {},
            )
            or {}
        )

        print(
            f"Estado tras aceptar 1:       "
            f"{simulation.get('state_after')}"
        )

        print(
            f"Surplus tras aceptar 1:      "
            f"{safe_int(simulation.get('surplus_after')):,.0f} EUR"
        )

    else:

        print(
            "NINGUNA OFERTA SELECCIONADA."
        )

    print()
    print(
        "## SAFETY ASSERTIONS"
    )
    print()

    errors = []

    if changed != len(
        reserved_ids
    ):

        errors.append(
            "No se modificaron todas las expiraciones simuladas."
        )

    if plan.get(
        "ready",
        False,
    ):

        # Un plan puede necesitar VARIAS ofertas combinadas. Este
        # test asumia que ready implicaba una unica venta que
        # bastase sola, y por eso cantaba error ante cualquier
        # MULTI_ACCEPT_PLAN_READY, que es un plan perfectamente
        # valido. Tampoco existe "individually_sufficient" en el
        # planner: salia None en todos los candidatos.

        if not selected_offers:
            errors.append(
                "Planner READY sin ninguna oferta seleccionada."
            )

        else:

            if required_accept_count != len(
                selected_offers
            ):
                errors.append(
                    f"required_accept_count="
                    f"{required_accept_count} no coincide con "
                    f"{len(selected_offers)} ofertas "
                    f"seleccionadas."
                )

            protegidas = [
                oferta
                for oferta in selected_offers
                if oferta.get(
                    "protected",
                    False,
                )
            ]

            if protegidas:
                errors.append(
                    f"Planner selecciono "
                    f"{len(protegidas)} jugador(es) protegido(s)."
                )

            # LO QUE DE VERDAD IMPORTA: el conjunto elegido debe
            # mantener SOLVENCY_GUARANTEE. Da igual si es una
            # oferta o cuatro.
            simulation = (
                selected_plan.get(
                    "simulation",
                    {},
                )
                or {}
            )

            if not simulation.get(
                "guaranteed_after",
                False,
            ):
                errors.append(
                    f"El plan de {len(selected_offers)} oferta(s) "
                    f"NO mantiene SOLVENCY_GUARANTEE."
                )

        print()
        print(
            f"Plan listo -> {plan.get('status')}: "
            f"{len(selected_offers)} oferta(s), "
            f"{safe_int(selected_plan.get('total_amount')):,.0f} EUR"
        )

    else:

        # NO se comprueba el NOMBRE del estado.
        #
        # Primero lo intente con una lista de nombres validos y
        # fue un error de diseno: el planner arrastra el veredicto
        # del motor de seguridad, que tiene su propio vocabulario,
        # y en cuanto cambia el mercado aparece un estado que no
        # estaba en la lista. Un test que hay que ampliar cada
        # semana no protege nada, solo molesta.
        #
        # Lo que de verdad importa es el CONTRATO de un plan
        # bloqueado:
        #
        #   1. ready es False
        #   2. dice en que estado esta
        #   3. explica por que
        #   4. y NO arrastra ofertas seleccionadas
        #
        # El punto 4 es el critico: un plan bloqueado que ademas
        # trajese ofertas elegidas seria una trampa para el
        # executor.

        estado = str(
            plan.get(
                "status"
            )
            or ""
        ).strip()

        motivo = str(
            plan.get(
                "reason"
            )
            or ""
        ).strip()

        seleccionadas = (
            plan.get(
                "selected_offers",
                [],
            )
            or []
        )

        if not estado:
            errors.append(
                "Plan bloqueado sin status: imposible "
                "diagnosticar por que no actua."
            )

        if not motivo:
            errors.append(
                f"Plan bloqueado ({estado}) sin reason."
            )

        if seleccionadas:
            errors.append(
                f"PELIGRO: plan bloqueado ({estado}) pero "
                f"arrastra {len(seleccionadas)} ofertas "
                f"seleccionadas. El executor podria tomarlas "
                f"por validas."
            )

        print()
        print(
            f"Plan bloqueado -> {estado}: {motivo}"
        )

    if errors:

        for error in errors:
            print(
                "ERROR:",
                error,
            )

        raise SystemExit(
            "ACCEPT BEFORE EXPIRY EXECUTION PLANNER: FAILED"
        )

    print(
        "# ACCEPT BEFORE EXPIRY EXECUTION PLANNER V1 OBSERVER: OK"
    )

    print("=" * 126)


if __name__ == "__main__":
    main()
