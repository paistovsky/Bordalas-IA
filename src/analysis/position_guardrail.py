"""
Guardarrail posicional.

POR QUE EXISTE
    Bordalas IA sabe cuanto vale cada jugador y cuanto duele
    venderlo, pero no sabia contar por posiciones.

    `build_recovery_plan` recorre TODAS las combinaciones de
    ofertas entrantes buscando la que recupere solvencia con el
    menor dano, y el unico filtro que aplica es descartar a los
    franchise. Con la plantilla del 16/08/2026 -2 porteros, 6
    defensas, 5 centrocampistas, 2 delanteros- una de esas
    combinaciones legales era vender a Dituro y a Bayindir en el
    mismo ciclo.

    Plantilla sin porteros. Y como dice el dueno del equipo, en el
    mercado no salen porteros titulares todos los dias.

    Cada venta por separado pasaba todos los controles. El
    problema solo existe cuando se miran juntas, y no habia nada
    que las mirara juntas.

QUE HACE
    1. Cuenta la plantilla por posicion.
    2. Calcula el suelo de cada posicion: el minimo para poder
       alinear un once legal en alguna formacion.
    3. Ordena a los jugadores de cada posicion por prioridad de
       permanencia y bloquea a los que ocupan el suelo. Los que
       sobran son vendibles.
    4. Valida CONJUNTOS de ventas, no ventas sueltas. Dos ventas
       inocentes por separado pueden dejar una posicion vacia.

QUE NO HACE
    No bloquea publicar. Publicar a toda la plantilla cada dia es
    justo lo que genera las ofertas del Computer, que son la
    liquidez. El guardarrail actua al ACEPTAR, no al publicar.
"""

from __future__ import annotations

from src.analysis.position_policy import (
    POSITION_NAMES,
    get_primary_position,
)


# Formaciones que admite Biwenger, como (POR, DEF, MED, DEL).
FORMATIONS = (
    (1, 5, 4, 1),
    (1, 5, 3, 2),
    (1, 4, 5, 1),
    (1, 4, 4, 2),
    (1, 4, 3, 3),
    (1, 3, 5, 2),
    (1, 3, 4, 3),
)


def _derive_floor() -> dict:
    """
    Suelo por posicion: lo minimo que exige la formacion menos
    exigente. Por debajo de esto no hay once que alinear.

    Se deriva de FORMATIONS en vez de escribirse a mano para que
    anadir una formacion no deje el suelo desactualizado.
    """

    suelo = {}

    for indice, posicion in enumerate((1, 2, 3, 4)):
        suelo[posicion] = min(
            formacion[indice]
            for formacion in FORMATIONS
        )

    return suelo


# Suelo estrategico, por encima del que exige la formacion.
#
# La formacion menos exigente (5-4-1, 4-5-1) admite un solo
# delantero, pero jugar con uno no es la estrategia: esta liga
# se gana con 4-4-2 o 4-3-3 porque los delanteros meten goles y
# son los que mas puntuan -por eso son tambien los mas caros-.
#
# Quedarse en un delantero es legal y perdedor. El suelo de
# venta sube a 2 aunque Pepe luego alinee tres.
#
# Esto NO toca FORMATIONS: el motor de alineacion sigue pudiendo
# elegir cualquier formacion legal. Lo unico que cambia es
# cuantos se pueden vender.
STRATEGIC_FLOOR = {
    4: 2,   # delantero
}


def _apply_strategic_floor(suelo: dict) -> dict:
    """
    El suelo real es el mayor de los dos: el que exige la
    formacion y el que exige la estrategia.
    """

    return {
        posicion: max(
            minimo,
            STRATEGIC_FLOOR.get(
                posicion,
                0,
            ),
        )
        for posicion, minimo in suelo.items()
    }


POSITION_FLOOR = _apply_strategic_floor(
    _derive_floor()
)   # {1: 1, 2: 3, 3: 3, 4: 2}

# Colchon comodo. Por debajo no se bloquea nada, pero se avisa:
# la posicion esta al limite y conviene reponerla.
POSITION_DESIRED = {
    1: 2,   # portero
    2: 4,
    3: 4,
    4: 2,
}

# El portero merece trato aparte. No por la formacion -con uno
# basta- sino porque reponerlo es dificil: no salen porteros
# titulares al mercado todos los dias.
GOALKEEPER = 1


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _keep_priority(player: dict) -> tuple:
    """
    A quien conservamos primero dentro de una posicion.

    Orden: titular del XI, luego mas protegido, luego mas caro.
    El id al final solo para que el resultado sea siempre el
    mismo ante empates.
    """

    return (
        0 if player.get("in_lineup") else 1,
        -float(player.get("protection_score") or 0),
        -safe_int(
            player.get("market_value")
            if player.get("market_value") is not None
            else player.get("price")
        ),
        safe_int(player.get("id")),
    )


def build_position_guardrail(
    roster_board: list,
    lineup_ids=None,
) -> dict:
    """
    Estado posicional de la plantilla.

    Acepta dos formas de plantilla:

    - El roster de liquidity_manager, con in_lineup,
      protection_score y market_value. Es la buena: permite
      ordenar bien a quien conservar.
    - El `my_team` crudo del snapshot, que solo trae id, position
      y price. Suficiente para contar y bloquear, que es lo que
      de verdad importa.

    `lineup_ids` es opcional y solo mejora el orden de
    permanencia cuando la plantilla no trae in_lineup.
    """

    titulares = {
        safe_int(pid)
        for pid in (lineup_ids or [])
    }

    jugadores = []

    for item in (roster_board or []):

        if not isinstance(item, dict):
            continue

        if titulares and "in_lineup" not in item:
            item = {
                **item,
                "in_lineup": safe_int(item.get("id")) in titulares,
            }

        jugadores.append(item)

    por_posicion = {}
    sin_posicion = []

    for jugador in jugadores:

        posicion = get_primary_position(jugador)

        if posicion is None:
            sin_posicion.append(safe_int(jugador.get("id")))
            continue

        por_posicion.setdefault(posicion, []).append(jugador)

    detalle = {}
    bloqueados = {}
    vendibles = set()

    for posicion in (1, 2, 3, 4):

        plantel = sorted(
            por_posicion.get(posicion, []),
            key=_keep_priority,
        )

        suelo = POSITION_FLOOR[posicion]

        # Los primeros del orden ocupan el suelo y no se tocan.
        # El resto puede venderse.
        intocables = plantel[:suelo]
        sobrantes = plantel[suelo:]

        for jugador in intocables:
            bloqueados[safe_int(jugador.get("id"))] = (
                f"Sin el no quedan {suelo} "
                f"{POSITION_NAMES[posicion].lower()}s para alinear "
                f"un once legal."
            )

        for jugador in sobrantes:
            vendibles.add(safe_int(jugador.get("id")))

        detalle[posicion] = {
            "position": posicion,
            "position_name": POSITION_NAMES[posicion],
            "owned": len(plantel),
            "floor": suelo,
            "desired": POSITION_DESIRED[posicion],
            "disposable": len(sobrantes),
            "at_floor": len(plantel) <= suelo,
            "below_desired": len(plantel) < POSITION_DESIRED[posicion],
            "locked_ids": [
                safe_int(j.get("id")) for j in intocables
            ],
            "disposable_ids": [
                safe_int(j.get("id")) for j in sobrantes
            ],
        }

    # Posiciones que hay que reponer cuando aparezca algo. No
    # bloquean nada; alimentan el lado comprador.
    a_reponer = [
        posicion
        for posicion in (1, 2, 3, 4)
        if detalle[posicion]["below_desired"]
    ]

    portero = detalle[GOALKEEPER]

    aviso_portero = None

    if portero["owned"] == 0:
        aviso_portero = (
            "PLANTILLA SIN PORTERO. No se puede alinear. "
            "Fichar uno es la prioridad absoluta."
        )

    elif portero["owned"] <= portero["floor"]:
        aviso_portero = (
            "Queda un solo portero y es intocable. Reponer en "
            "cuanto salga uno titular: no aparecen todos los dias."
        )

    return {
        "available": True,
        "by_position": detalle,
        "locked_ids": bloqueados,
        "disposable_ids": sorted(vendibles),
        "positions_to_replenish": a_reponer,
        "goalkeeper_warning": aviso_portero,
        "players_without_position": sin_posicion,
        "squad_size": len(jugadores),
    }


def validate_sale_set(
    guardrail: dict,
    player_ids,
) -> dict:
    """
    Valida un CONJUNTO de ventas a la vez.

    Aqui esta el motivo de todo el modulo. Preguntar "puedo vender
    a Dituro?" da que si, y "puedo vender a Bayindir?" tambien.
    Preguntar "puedo vender a los dos?" tiene que dar que no.
    """

    if not guardrail or not guardrail.get("available"):
        return {
            "ok": True,
            "guardrail_applied": False,
            "violations": [],
            "reason": (
                "Sin guardarrail posicional: no se comprobo nada."
            ),
        }

    a_vender = {
        safe_int(pid)
        for pid in (player_ids or [])
    }

    if not a_vender:
        return {
            "ok": True,
            "guardrail_applied": True,
            "violations": [],
            "reason": "No hay ventas que validar.",
        }

    violaciones = []

    for posicion, datos in (
        guardrail.get("by_position") or {}
    ).items():

        de_esta_posicion = a_vender.intersection(
            set(datos["locked_ids"])
            | set(datos["disposable_ids"])
        )

        if not de_esta_posicion:
            continue

        restantes = datos["owned"] - len(de_esta_posicion)

        if restantes < datos["floor"]:
            violaciones.append(
                {
                    "position": posicion,
                    "position_name": datos["position_name"],
                    "owned": datos["owned"],
                    "selling": len(de_esta_posicion),
                    "would_remain": restantes,
                    "floor": datos["floor"],
                    "player_ids": sorted(de_esta_posicion),
                    "reason": (
                        f"Quedarian {restantes} "
                        f"{datos['position_name'].lower()}s y hacen "
                        f"falta {datos['floor']} para alinear."
                    ),
                }
            )

    if violaciones:
        return {
            "ok": False,
            "guardrail_applied": True,
            "violations": violaciones,
            "status": "BLOCK_POSITION_FLOOR",
            "reason": "; ".join(
                v["reason"] for v in violaciones
            ),
        }

    return {
        "ok": True,
        "guardrail_applied": True,
        "violations": [],
        "reason": (
            "El conjunto de ventas deja todas las posiciones "
            "por encima del suelo."
        ),
    }


def print_position_guardrail(
    guardrail: dict,
) -> None:

    print()
    print("-" * 70)
    print("GUARDARRAIL POSICIONAL")
    print("-" * 70)

    if not guardrail or not guardrail.get("available"):
        print("  No disponible.")
        return

    print(
        f"  {'POSICION':<16}{'TENGO':>7}{'SUELO':>7}"
        f"{'VENDIBLES':>11}"
    )

    for posicion in (1, 2, 3, 4):

        datos = guardrail["by_position"][posicion]

        marca = ""

        if datos["at_floor"]:
            marca = "  <- al limite"

        elif datos["below_desired"]:
            marca = "  <- conviene reponer"

        print(
            f"  {datos['position_name']:<16}"
            f"{datos['owned']:>7}"
            f"{datos['floor']:>7}"
            f"{datos['disposable']:>11}"
            f"{marca}"
        )

    if guardrail.get("goalkeeper_warning"):
        print()
        print(f"  PORTERIA: {guardrail['goalkeeper_warning']}")

    if guardrail.get("players_without_position"):
        print()
        print(
            f"  Sin posicion valida: "
            f"{guardrail['players_without_position']}"
        )
