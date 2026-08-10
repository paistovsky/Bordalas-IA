from src.actions.franchise_executor import (
    build_next_franchise_action,
)

from src.analysis.offer_analyzer import (
    build_offer_board,
)

from src.analysis.solvency_engine import (
    build_solvency_state,
)

from src.biwenger.write_client import (
    BiwengerWriteClient,
)


# ======================================================
# CONFIGURACIÓN
# ======================================================


MAX_ACTIONS_PER_CYCLE = 5


# ======================================================
# UTILIDADES
# ======================================================


def money(
    value: int | float,
) -> str:

    return (
        f"{value:,.0f} €"
    )


def get_player_from_my_team(
    snapshot: dict,
    player_id: int,
) -> dict | None:

    for player in snapshot.get(
        "my_team",
        [],
    ):

        if int(
            player.get(
                "id",
                -1,
            )
        ) == int(
            player_id
        ):

            return player

    return None


def find_outgoing_offer_for_player(
    snapshot: dict,
    player_id: int,
) -> dict | None:
    """
    Busca una puja saliente activa nuestra
    correspondiente al jugador indicado.
    """

    board = (
        build_offer_board(
            snapshot
        )
    )

    for offer in board.get(
        "outgoing",
        [],
    ):

        if offer.get(
            "status"
        ) != "waiting":

            continue

        player_ids = (
            offer.get(
                "player_ids",
                [],
            )
        )

        if int(
            player_id
        ) in [
            int(item)
            for item in player_ids
        ]:

            return offer

    return None


# ======================================================
# IDENTIFICAR OBJETIVO
# ======================================================


def extract_franchise_target(
    franchise_action: dict,
) -> dict | None:

    impact = (
        franchise_action.get(
            "impact_plan",
            {},
        )
        or {}
    )

    target = (
        impact.get(
            "target"
        )
    )

    if target:
        return target

    target = (
        franchise_action.get(
            "target"
        )
    )

    if target:
        return target

    return None


# ======================================================
# ESTADO FRANCHISE
# ======================================================


def build_franchise_autopilot_state(
    snapshot: dict,
) -> dict:
    """
    Decide qué estado tiene el proceso Franchise
    ANTES de ejecutar ninguna operación.

    Esta función jamás modifica Biwenger.
    """

    next_action = (
        build_next_franchise_action(
            snapshot
        )
    )

    target = (
        extract_franchise_target(
            next_action
        )
    )

    # ==================================================
    # NO HAY OBJETIVO FRANCHISE
    # ==================================================

    if target is None:

        return {
            "state":
                "NO_FRANCHISE",

            "terminal":
                True,

            "should_execute":
                False,

            "target":
                None,

            "next_action":
                next_action,

            "reason":
                (
                    "No existe objetivo Franchise "
                    "activo en el mercado."
                ),
        }

    target_id = int(
        target[
            "id"
        ]
    )

    # ==================================================
    # YA TENEMOS AL JUGADOR
    # ==================================================

    owned = (
        get_player_from_my_team(
            snapshot,
            target_id,
        )
    )

    if owned is not None:

        solvency = (
            build_solvency_state(
                snapshot
            )
        )

        balance = int(
            solvency.get(
                "balance",
                0,
            )
            or 0
        )

        if balance < 0:

            return {
                "state":
                    "POST_FRANCHISE_DEBT",

                "terminal":
                    True,

                "should_execute":
                    False,

                "target":
                    target,

                "owned_player":
                    owned,

                "solvency":
                    solvency,

                "next_action":
                    next_action,

                "reason":
                    (
                        "El jugador Franchise ya está "
                        "en nuestra plantilla y el saldo "
                        "es negativo. Debe activarse el "
                        "plan de saneamiento."
                    ),
            }

        return {
            "state":
                "FRANCHISE_ALREADY_OWNED",

            "terminal":
                True,

            "should_execute":
                False,

            "target":
                target,

            "owned_player":
                owned,

            "solvency":
                solvency,

            "next_action":
                next_action,

            "reason":
                (
                    "El objetivo Franchise ya pertenece "
                    "a nuestra plantilla."
                ),
        }

    # ==================================================
    # ¿YA TENEMOS UNA PUJA ACTIVA?
    # ==================================================

    existing_offer = (
        find_outgoing_offer_for_player(
            snapshot,
            target_id,
        )
    )

    if existing_offer is not None:

        return {
            "state":
                "WAIT_FRANCHISE_RESOLUTION",

            "terminal":
                True,

            "should_execute":
                False,

            "target":
                target,

            "active_offer":
                existing_offer,

            "next_action":
                next_action,

            "reason":
                (
                    "Ya existe una puja activa por el "
                    "objetivo Franchise. No se enviarán "
                    "pujas duplicadas ni se cancelarán "
                    "más operaciones hasta que el mercado "
                    "resuelva esta oferta."
                ),
        }

    # ==================================================
    # MOTOR FRANCHISE NORMAL
    # ==================================================

    action_name = (
        next_action.get(
            "action"
        )
    )

    if action_name == "CANCEL_BID":

        return {
            "state":
                "CANCEL_BID",

            "terminal":
                False,

            "should_execute":
                True,

            "target":
                target,

            "next_action":
                next_action,

            "reason":
                (
                    "Es necesario desbloquear capacidad "
                    "de puja antes de atacar al Franchise."
                ),
        }

    if action_name == "PLACE_FRANCHISE_BID":

        return {
            "state":
                "PLACE_FRANCHISE_BID",

            "terminal":
                False,

            "should_execute":
                True,

            "target":
                target,

            "next_action":
                next_action,

            "reason":
                (
                    "La capacidad de puja y las reglas "
                    "de solvencia permiten atacar al "
                    "objetivo Franchise."
                ),
        }

    if action_name == "ABORT":

        return {
            "state":
                "ABORT",

            "terminal":
                True,

            "should_execute":
                False,

            "target":
                target,

            "next_action":
                next_action,

            "reason":
                (
                    next_action
                    .get(
                        "validation",
                        {},
                    )
                    .get(
                        "reason",
                        "El motor Franchise ha bloqueado la operación.",
                    )
                ),
        }

    return {
        "state":
            "WAIT",

        "terminal":
            True,

        "should_execute":
            False,

        "target":
            target,

        "next_action":
            next_action,

        "reason":
            (
                "El motor no requiere ninguna "
                "operación inmediata."
            ),
    }


# ======================================================
# EJECUTAR UNA ACCIÓN
# ======================================================


def execute_autopilot_action(
    state: dict,
    execute: bool = False,
) -> dict:
    """
    Ejecuta como máximo UNA acción del estado actual.

    No hace refresh.
    El caller debe refrescar después.
    """

    if not state.get(
        "should_execute"
    ):

        return {
            **state,

            "executed":
                False,

            "success":
                True,

            "result":
                None,
        }

    next_action = (
        state[
            "next_action"
        ]
    )

    if not execute:

        return {
            **state,

            "executed":
                False,

            "success":
                True,

            "result":
                {
                    "status":
                        "DRY_RUN",
                },
        }

    writer = (
        BiwengerWriteClient()
    )

    # ==================================================
    # CANCELAR PUJA
    # ==================================================

    if state[
        "state"
    ] == "CANCEL_BID":

        result = (
            writer.cancel_bid(
                offer_id=
                    next_action[
                        "offer_id"
                    ],

                execute=True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            **state,

            "executed":
                True,

            "success":
                success,

            "result":
                result,
        }

    # ==================================================
    # PUJAR POR FRANCHISE
    # ==================================================

    if state[
        "state"
    ] == "PLACE_FRANCHISE_BID":

        target = (
            next_action[
                "target"
            ]
        )

        # Protección adicional anti-duplicado:
        # aunque el caller haya calculado el estado
        # anteriormente, volvemos a comprobar el
        # snapshot que tenemos.
        #
        # El refresh entre acciones será otra capa
        # adicional de seguridad.
        result = (
            writer.place_bid(
                player_id=
                    target[
                        "id"
                    ],

                amount=
                    next_action[
                        "amount"
                    ],

                seller_user_id=
                    None,

                execute=True,
            )
        )

        success = bool(
            result.get(
                "success",
                False,
            )
        )

        return {
            **state,

            "executed":
                True,

            "success":
                success,

            "result":
                result,
        }

    return {
        **state,

        "executed":
            False,

        "success":
            False,

        "result":
            None,

        "reason":
            (
                "Estado ejecutable desconocido."
            ),
    }


# ======================================================
# PRESENTACIÓN
# ======================================================


def print_autopilot_state(
    state: dict,
) -> None:

    print()
    print("=" * 90)
    print(
        "          BORDALÁS IA - FRANCHISE AUTOPILOT"
    )
    print("=" * 90)

    target = (
        state.get(
            "target"
        )
    )

    if target:

        print()
        print(
            f"Objetivo:      "
            f"{target.get('name')}"
        )

        print(
            f"Player ID:     "
            f"{target.get('id')}"
        )

        print(
            f"Franchise:     "
            f"{target.get('franchise_score', 0)}/100"
        )

    print()
    print(
        f"Estado:        "
        f"{state['state']}"
    )

    print(
        f"Terminal:      "
        f"{'SÍ' if state['terminal'] else 'NO'}"
    )

    print(
        f"Ejecutar:      "
        f"{'SÍ' if state['should_execute'] else 'NO'}"
    )

    print()
    print(
        state.get(
            "reason",
            "",
        )
    )

    # ==================================================
    # PUJA FRANCHISE ACTIVA
    # ==================================================

    if (
        state[
            "state"
        ]
        == "WAIT_FRANCHISE_RESOLUTION"
    ):

        offer = (
            state[
                "active_offer"
            ]
        )

        print()
        print(
            "PUJA FRANCHISE ACTIVA"
        )

        print(
            "-" * 90
        )

        print()

        print(
            f"Offer ID:      "
            f"{offer.get('offer_id')}"
        )

        print(
            f"Importe:       "
            f"{money(offer.get('amount', 0))}"
        )

        print(
            f"Estado oferta: "
            f"{offer.get('status')}"
        )

        print(
            f"Válida hasta:  "
            f"{offer.get('until')}"
        )

    # ==================================================
    # CANCELACIÓN
    # ==================================================

    if (
        state[
            "state"
        ]
        == "CANCEL_BID"
    ):

        action = (
            state[
                "next_action"
            ]
        )

        print()
        print(
            "SIGUIENTE CANCELACIÓN"
        )

        print(
            "-" * 90
        )

        print()

        print(
            f"Jugador:       "
            f"{action['player_name']}"
        )

        print(
            f"Offer ID:      "
            f"{action['offer_id']}"
        )

        print(
            f"Importe:       "
            f"{money(action['amount'])}"
        )

    # ==================================================
    # PUJA NUEVA
    # ==================================================

    if (
        state[
            "state"
        ]
        == "PLACE_FRANCHISE_BID"
    ):

        action = (
            state[
                "next_action"
            ]
        )

        print()
        print(
            "PUJA A EJECUTAR"
        )

        print(
            "-" * 90
        )

        print()

        print(
            f"Jugador:       "
            f"{action['target']['name']}"
        )

        print(
            f"Importe:       "
            f"{money(action['amount'])}"
        )

        print(
            f"Puja máxima:   "
            f"{money(action['maximum_bid'])}"
        )

    # ==================================================
    # POST FRANCHISE
    # ==================================================

    if (
        state[
            "state"
        ]
        == "POST_FRANCHISE_DEBT"
    ):

        solvency = (
            state[
                "solvency"
            ]
        )

        print()
        print(
            "POST-FRANCHISE"
        )

        print(
            "-" * 90
        )

        print()

        print(
            f"Saldo:         "
            f"{money(solvency.get('balance', 0))}"
        )

        print(
            f"Liquidez:      "
            f"{money(solvency.get('recoverable_cash', 0))}"
        )

        print(
            f"Riesgo:        "
            f"{solvency.get('risk')}"
        )

    print()
    print("=" * 90)