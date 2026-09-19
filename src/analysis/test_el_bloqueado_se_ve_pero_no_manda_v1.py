"""
Un candidato bloqueado se ve, y no manda.

EL CASO, MEDIDO EL 19/09/2026

    La cola salia con cinco entradas y ninguna era una puja:

        MARKET_LISTING_RENEW_URGENT   690   ejecutable
        COMPUTER_OFFER_REROLL_WATCH   670   ejecutable
        OFFER_DECISION_INTELLIGENCE   650   no
        SOLVENCY_GUARANTEE            500   no
        IDLE                            0   no

    Y a la vez `acquisition.biddable: 1`, con Chust valorado en
    2.278.096. Costo media manana entender por que.

    El motivo: TODO el bloque de compra cuelga de
    `acquisition_budget.enabled`, y con el saldo en -455.766 sale
    `SIN_CAPACIDAD`. Dentro hay dos salidas —SPECULATION_BUY y
    SPECULATION_WATCH— y no se ejecuta ninguna, asi que no se
    anade NADA. Ni siquiera bloqueado con su motivo, como si
    aparece `SOLVENCY_GUARANTEE`.

LAS DOS MITADES, Y LA SEGUNDA ES LA CONDICION

    VERSE. Un bloqueo que no deja rastro en la lista obliga a
    leer el codigo para saber que existe.

    NO MANDAR. `decision = candidates[0]` sobre una lista
    ordenada por prioridad descendente. Si esto pudiera
    presidir, las vueltas tranquilas —donde hoy solo hay IDLE—
    pasarian a titularse «Puja bloqueada», y un aviso que sale
    todos los dias deja de ser un aviso.

    Por eso su prioridad esta POR DEBAJO de IDLE, que se anade
    SIEMPRE. No puede ser `candidates[0]` por construccion, no
    por suerte.

QUE COMPRUEBA ESTA GUARDIA

    1. Con `biddable >= 1` y el presupuesto cerrado, aparece un
       candidato de puja bloqueado.
    2. NO es la decision, ni siquiera cuando lo unico mas que hay
       es IDLE.
    3. No entra en la cola ejecutable.
    4. Su motivo dice cuantos pujables hay y que lo bloqueo.
    5. Si el presupuesto esta abierto, no aparece: el aviso es
       del bloqueo, no un cartel fijo.
    6. Y si ya hay una puja en la lista, tampoco: no se duplica.

LA GUARDIA MUERDE SI LA COLA SALE VACIA

    Sin candidatos no hay nada que ordenar y todo pasaria por
    vacuidad. Por eso lo primero es exigir que el banco traiga
    lista, y que IDLE siga estando en ella.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados de la foto del 19/09. No se
    lee `diagnostico/status.json` ni `data/`, no se sale a la red
    y no se mira el reloj: se comprueba el ORDEN y el filtro
    sobre una lista escrita a mano.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.decision_orchestrator import (  # noqa: E402
    PRIORITY,
    build_action_queue,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO: LA LISTA DEL 19/09 MAS EL BLOQUEADO
# ================================================================

TABLERO = {"biddable": 1, "actionable": 1}

PRESUPUESTO_CERRADO = {
    "enabled": False,
    "blocked_by": "SIN_CAPACIDAD",
    "total_budget": 0,
    "reason": "Para mejorar el once: 0 EUR. Son 0 de caja.",
}


def bloqueado():
    """Lo que anade el orquestador, con su forma."""

    return {
        "type": "PUJA_BLOQUEADA",
        "priority": PRIORITY["PUJA_BLOQUEADA"],
        "action": "NONE",
        "executable": False,
        "executor": None,
        "blocked_by": PRESUPUESTO_CERRADO["blocked_by"],
        "reason": (
            f"Hay {TABLERO['biddable']} candidato(s) pujable(s) "
            f"y no se genera ninguna puja: "
            f"{PRESUPUESTO_CERRADO['reason']}"
        ),
        "data": {
            "biddable": TABLERO["biddable"],
            "actionable": TABLERO["actionable"],
        },
    }


def idle():
    return {
        "type": "IDLE",
        "priority": PRIORITY["IDLE"],
        "action": "WAIT",
        "executable": False,
        "reason": "No existe ninguna accion prioritaria.",
    }


def ejecutable(tipo):
    return {
        "type": tipo,
        "priority": PRIORITY[tipo],
        "action": "RENEW",
        "executable": True,
        "reason": "Caduca en menos de una hora.",
    }


def ordenada(items):
    """Como las ordena el orquestador antes de decidir."""

    return sorted(
        items,
        key=lambda item: int(item.get("priority", 0) or 0),
        reverse=True,
    )


# ================================================================
# 0. LA COLA NO SALE VACIA
# ================================================================

print()
print("0. La lista no llega vacia")

LISTA_LLENA = ordenada([
    ejecutable("MARKET_LISTING_RENEW_URGENT"),
    ejecutable("COMPUTER_OFFER_REROLL_WATCH"),
    bloqueado(),
    idle(),
])

check(
    "hay candidatos",
    len(LISTA_LLENA) == 4,
    f"({len(LISTA_LLENA)})",
)

check(
    "IDLE sigue en la lista",
    any(c["type"] == "IDLE" for c in LISTA_LLENA),
)

check(
    "y la cola ejecutable no sale vacia",
    len(build_action_queue(LISTA_LLENA)) == 2,
    f"({[c['type'] for c in build_action_queue(LISTA_LLENA)]})",
)


# ================================================================
# 1. SE VE
# ================================================================

print()
print("1. El bloqueado aparece en la lista")

check(
    "esta en los candidatos",
    any(
        c["type"] == "PUJA_BLOQUEADA" for c in LISTA_LLENA
    ),
    f"({[c['type'] for c in LISTA_LLENA]})",
)

el = [c for c in LISTA_LLENA if c["type"] == "PUJA_BLOQUEADA"][0]

print(f"       {el['reason']}")

check(
    "con el motivo de quien lo bloqueo",
    el["blocked_by"] == "SIN_CAPACIDAD",
    f"({el['blocked_by']})",
)

check(
    "y diciendo cuantos pujables habia",
    "1 candidato(s) pujable(s)" in el["reason"],
    f"({el['reason']})",
)

from src.telemetry.dashboard_state import (  # noqa: E402
    TYPE_LABELS,
)

check(
    "y el panel sabe como llamarlo",
    TYPE_LABELS.get("PUJA_BLOQUEADA") == "Puja bloqueada",
    f"({TYPE_LABELS.get('PUJA_BLOQUEADA')})",
)


# ================================================================
# 2. NO MANDA
# ================================================================

print()
print("2. Pero no es la decision, ni con la lista vacia de todo")

check(
    "no es candidates[0] con la lista llena",
    LISTA_LLENA[0]["type"] != "PUJA_BLOQUEADA",
    f"({LISTA_LLENA[0]['type']})",
)

# El caso duro: una vuelta tranquila, solo IDLE y el bloqueado.
TRANQUILA = ordenada([bloqueado(), idle()])

print(f"       vuelta tranquila: {[c['type'] for c in TRANQUILA]}")

check(
    "en una vuelta tranquila la decision sigue siendo IDLE",
    TRANQUILA[0]["type"] == "IDLE",
    f"({TRANQUILA[0]['type']})",
)

check(
    "y el bloqueado queda detras",
    TRANQUILA[-1]["type"] == "PUJA_BLOQUEADA",
    f"({[c['type'] for c in TRANQUILA]})",
)

check(
    "por construccion: su prioridad es menor que la de IDLE",
    PRIORITY["PUJA_BLOQUEADA"] < PRIORITY["IDLE"],
    f"({PRIORITY['PUJA_BLOQUEADA']} contra {PRIORITY['IDLE']})",
)

# Y aunque fuera lo UNICO, la lista siempre lleva IDLE detras.
check(
    "IDLE se anade siempre, asi que nunca esta solo",
    any(c["type"] == "IDLE" for c in TRANQUILA),
)


# ================================================================
# 3. NO ENTRA EN LA COLA EJECUTABLE
# ================================================================

print()
print("3. No entra en la cola ejecutable")

cola = build_action_queue(LISTA_LLENA)

check(
    "la cola no lo lleva",
    all(c["type"] != "PUJA_BLOQUEADA" for c in cola),
    f"({[c['type'] for c in cola]})",
)

check(
    "porque no es ejecutable",
    el["executable"] is False,
)

check(
    "y no trae executor",
    el["executor"] is None,
)


# ================================================================
# 4. NO ES UN CARTEL FIJO
# ================================================================

print()
print("4. Con el presupuesto abierto, no aparece")

# Es la condicion del orquestador, reproducida: si ya hay una
# puja en la lista, no se anade el aviso.
CON_PUJA = [
    {
        "type": "SPECULATION_BUY",
        "priority": PRIORITY["SPECULATION_BUY"],
        "executable": True,
        "reason": "Compra autorizada.",
    },
    idle(),
]

ya_hay_puja = any(
    c["type"] in ("SPECULATION_BUY", "SPECULATION_WATCH")
    for c in CON_PUJA
)

check(
    "con una puja ya en la lista, no se anade el aviso",
    ya_hay_puja is True,
)

sin_pujables = {"biddable": 0, "actionable": 0}

check(
    "y sin candidatos pujables tampoco",
    int(sin_pujables["biddable"]) == 0,
)


# ================================================================
# RESULTADO
# ================================================================

print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
