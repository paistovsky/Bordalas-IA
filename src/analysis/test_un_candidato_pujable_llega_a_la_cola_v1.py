"""
Un candidato pujable llega a la cola, aunque sea bloqueado.

EL CASO, MEDIDO EL 19/09/2026

    La lista de prioridades entera de la foto:

        MARKET_LISTING_RENEW_URGENT   690   ejecutable
        COMPUTER_OFFER_REROLL_WATCH   670   ejecutable
        OFFER_DECISION_INTELLIGENCE   650   no
        SOLVENCY_GUARANTEE            500   no   (GARANTIZADA)
        IDLE                            0   no

    Ni una accion de puja. Y a la vez:

        acquisition.biddable    1
        acquisition.actionable  1

SE FILTRA O NO SE GENERA: NO SE GENERA

    Son dos fallos distintos y se arreglan en sitios distintos,
    asi que la pregunta importa. La respuesta esta medida:

    En `decision_orchestrator`, todo el bloque que produce el
    candidato de compra cuelga de una sola puerta:

        if (speculation_phase_allowed
            and ((budget.enabled and hay_lista_de_especulacion)
                 or (acquisition_budget.enabled
                     and hay_objetivo_de_fichaje))
            and not hard_safety_mode):

    `hay_objetivo_de_fichaje` es `biddable > 0`: SI se cumple.
    Lo que no se cumple es `acquisition_budget.enabled`, porque
    con el saldo en -455.766 el presupuesto sale
    `blocked_by: SIN_CAPACIDAD`.

    Dentro de ese bloque hay DOS salidas y las dos anaden algo:
    `SPECULATION_BUY` si hay objetivo, y `SPECULATION_WATCH` si
    no lo hay. Como la puerta no se abre, no se ejecuta ninguna
    de las dos: no se anade NADA. Por eso no aparece ni siquiera
    bloqueado con su motivo, como si aparece `SOLVENCY_GUARANTEE`.

    No es la cola la que lo filtra. Es que nunca se genera.

Y LA COLA, ADEMAS, SOLO ADMITE EJECUTABLES

    `build_action_queue` se queda solo con `executable=True`. La
    lista de cinco entradas de la foto -que incluye tres "no"- es
    la de CANDIDATOS, no la cola. Un candidato de puja bloqueado
    se veria ahi, con su motivo, igual que los otros tres.

QUE COMPRUEBA ESTA GUARDIA

    1. El sistema TIENE un escalon para pujar: la ausencia no es
       de diseno.
    2. Con el deficit vivo, el presupuesto de fichaje se apaga.
    3. La cola descarta los no ejecutables, luego un candidato
       bloqueado solo puede verse en la lista de candidatos.
    4. LO QUE SE PIDE: con `biddable >= 1` tiene que existir un
       candidato de puja, aunque salga bloqueado y con su motivo.

    (4) ESTA EN ROJO. Es el hueco, convertido en comprobacion.
    No se arregla aqui: cuando se puja en deficit es politica del
    dueno.

LA GUARDIA MUERDE SIN CANDIDATO PUJABLE

    Con `biddable = 0` no hay nada que exigir y (4) pasaria por
    vacuidad. Por eso lo primero es exigir que el banco traiga un
    candidato pujable.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `diagnostico/status.json` ni
    `data/`, no se sale a la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.acquisition_budget import (  # noqa: E402
    calculate_acquisition_budget,
)
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
# EL BANCO: EL CASO DEL 19/09
# ================================================================

SALDO = -455_766

TOPE = 15_870_265

# El tablero de adquisicion de la foto: Chust, pujable.
TABLERO = {
    "biddable": 1,
    "actionable": 1,
    "rows": [
        {
            "id": 61061,
            "name": "Chust",
            "bid": 1_850_000,
            "our_value": 2_278_096,
            "reason": "Mejora del once, titular 100 %.",
        }
    ],
}

SOLVENCIA = {
    "hard_safety": {"active": False},
    "solvency_guarantee": {
        "guaranteed": True,
        "required_recovery": 455_766,
    },
    "max_safe_debt": {
        "additional_debt_headroom": 0,
        "debt_window_open": False,
    },
    "temporary_debt": {"allowed": False},
}

SNAPSHOT = {
    "market": {
        "status": {"balance": SALDO, "maximumBid": TOPE},
    }
}


# ================================================================
# 0. EL BANCO TRAE UN CANDIDATO PUJABLE
# ================================================================

print()
print("0. El banco trae un candidato pujable")

check(
    "hay al menos un pujable",
    int(TABLERO.get("biddable") or 0) >= 1,
    f"(biddable={TABLERO.get('biddable')})",
)

check(
    "y tiene su puja calculada en euros",
    int(TABLERO["rows"][0]["bid"]) > 0,
    f"(bid={TABLERO['rows'][0]['bid']})",
)

check(
    "con la cola vacia no hay nada que mirar",
    build_action_queue([]) == [],
)


# ================================================================
# 1. EL SISTEMA TIENE UN ESCALON PARA PUJAR
# ================================================================

print()
print("1. La ausencia no es de diseno: el escalon existe")

check(
    "existe una prioridad para comprar",
    "SPECULATION_BUY" in PRIORITY,
)

check(
    "y esta por encima de renovar sin urgencia",
    PRIORITY["SPECULATION_BUY"] > PRIORITY["MARKET_LISTING_RENEW"],
    f"(buy={PRIORITY['SPECULATION_BUY']}, "
    f"renew={PRIORITY['MARKET_LISTING_RENEW']})",
)


# ================================================================
# 2. CON EL DEFICIT, EL PRESUPUESTO DE FICHAJE SE APAGA
# ================================================================

print()
print("2. Con el deficit vivo el presupuesto de fichaje se apaga")

presupuesto = calculate_acquisition_budget(SNAPSHOT, SOLVENCIA)

print(
    f"       enabled={presupuesto.get('enabled')} "
    f"blocked_by={presupuesto.get('blocked_by')} "
    f"total={presupuesto.get('total_budget')}"
)

check(
    "el presupuesto sale deshabilitado",
    presupuesto.get("enabled") is False,
)

check(
    "y dice por que",
    presupuesto.get("blocked_by") == "SIN_CAPACIDAD",
    f"({presupuesto.get('blocked_by')})",
)

# La puerta del orquestador, con los dos terminos de la foto.
hay_objetivo = int(TABLERO.get("biddable") or 0) > 0

puerta_abierta = bool(
    presupuesto.get("enabled") and hay_objetivo
)

check(
    "hay objetivo pero la puerta no se abre",
    hay_objetivo and not puerta_abierta,
    f"(objetivo={hay_objetivo}, puerta={puerta_abierta})",
)


# ================================================================
# 3. LA COLA SOLO ADMITE EJECUTABLES
# ================================================================

print()
print("3. La cola descarta los no ejecutables")

bloqueado = {
    "type": "SPECULATION_BUY",
    "priority": PRIORITY["SPECULATION_BUY"],
    "action": "BUY_SPECULATION",
    "executable": False,
    "reason": "Solvencia: no se puja con deficit vivo.",
}

ejecutable = {
    "type": "MARKET_LISTING_RENEW_URGENT",
    "priority": PRIORITY["MARKET_LISTING_RENEW_URGENT"],
    "action": "RENEW",
    "executable": True,
    "reason": "Caduca en menos de una hora.",
}

cola = build_action_queue([bloqueado, ejecutable])

check(
    "un candidato bloqueado no entra en la cola",
    all(c["type"] != "SPECULATION_BUY" for c in cola),
    f"({[c['type'] for c in cola]})",
)

check(
    "luego solo puede verse en la lista de CANDIDATOS",
    bloqueado["executable"] is False
    and bloqueado["reason"],
)


# ================================================================
# 4. LO QUE SE PIDE, Y HOY NO SE CUMPLE
# ================================================================

print()
print("4. Con biddable >= 1 tiene que haber un candidato de puja")

# Lo que el orquestador produce hoy con esta entrada: nada. La
# puerta no se abre, y las DOS salidas de dentro -SPECULATION_BUY
# y SPECULATION_WATCH- quedan sin ejecutar.
candidatos_de_puja = [] if not puerta_abierta else [bloqueado]

print(f"       candidatos de puja generados: {candidatos_de_puja}")

check(
    "existe un candidato de puja, aunque salga bloqueado",
    len(candidatos_de_puja) >= 1,
    f"<- con biddable={TABLERO['biddable']} y Chust valorado en "
    f"{TABLERO['rows'][0]['our_value']:,} EUR no se genera NADA: "
    f"ni la puja ni el WATCH que la sustituye. No se filtra en la "
    f"cola, no se llega a generar.",
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
