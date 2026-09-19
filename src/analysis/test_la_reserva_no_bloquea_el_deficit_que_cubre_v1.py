"""
Una reserva que no se puede gastar no es una garantia.

EL CASO, MEDIDO EL 19/09/2026

    Saldo -455.766. La subasta no puja: `blocked_by SOLVENCIA`.
    Y las cuatro ofertas vivas que podrian taparlo:

        Boyomo       1.845.800   KEEP_GOOD_OFFER
        Pablo Duran    362.700   KEEP_GOOD_OFFER
        Barzic         144.800   HOLD_SOLVENCY_RESERVED
        Oriol Rey    1.199.400   HOLD_SOLVENCY_RESERVED

    Barzic y Oriol Rey estan reservados COMO GARANTIA PARA CUBRIR
    ESE DEFICIT, y esa misma reserva es lo que impide usarlos
    para cubrirlo.

DONDE VIVE EL CANDADO

    `calculate_offer_reservations` reserva ofertas hasta tapar la
    deuda: `secured_needed = max(secured_needed, current_debt)`.
    La reserva se DIMENSIONA contra el deficit.

    Y `analyze_computer_offer` solo la levanta por RELOJ:

        expiry_pressure    hours_to_expiry   <= 6.0
        deadline_pressure  hours_to_deadline <= 6.0

    El deficit no es una entrada de esa decision. Ninguna de las
    dos puertas lo mira.

QUE COMPRUEBA ESTA GUARDIA

    1. La reserva se dimensiona contra el deficit que la motivo.
    2. Con el deficit vivo y SIN presion de reloj, NINGUNA de las
       reservadas se puede aceptar: el candado, escrito.
    3. La unica llave es el reloj: con presion de cierre, la
       misma oferta y el mismo deficit SI se aceptan.
    4. LO QUE SE PIDE: con un deficit vivo y todas las ofertas
       reservadas, el motor tiene que poder aceptar al menos una.

    (4) ESTA EN ROJO A PROPOSITO. Es el candado convertido en
    comprobacion. No se arregla aqui: cuando se cobra en deficit
    es politica del dueno, no de una guardia. El dia que se
    decida, esta se pone verde sola.

LA GUARDIA MUERDE CON LA LISTA DE OFERTAS VACIA

    Sin ofertas no hay nada que reservar ni que aceptar, y las
    comprobaciones pasarian por vacuidad. Por eso lo primero es
    exigir que el banco traiga ofertas y que con la lista vacia
    no se reserve nada.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `diagnostico/status.json` ni
    `data/`, no se sale a la red y no se escribe en ningun libro.

    La caducidad se da como fecha FIJA y lejana (ano 2100) para
    las comprobaciones sin presion de reloj: a cualquier hora que
    se corra esto, faltan mas de 6 h. La presion de reloj se
    inyecta por `hours_to_deadline`, que es un parametro, no el
    reloj del sistema.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.computer_offer_reroll_engine import (  # noqa: E402
    ACCEPT_BEFORE_DEADLINE_HOURS,
    ACCEPT_BEFORE_EXPIRY_HOURS,
    analyze_computer_offer,
)
from src.analysis.la_regla_del_deficit import (  # noqa: E402
    el_cobro_que_cierra,
)
from src.analysis.solvency_engine import (  # noqa: E402
    calculate_offer_reservations,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO: EL CASO DEL 19/09, CON SUS CIFRAS
# ================================================================

SALDO = -455_766

DEFICIT = 455_766

# Lejos de cualquier "ahora": no depende del reloj del sistema.
LEJOS = "2100-01-01T00:00:00+00:00"


def oferta(offer_id, nombre, importe, premium, franquicia=0.0):
    return {
        "offer_id": offer_id,
        "amount": importe,
        "premium_percent": premium,
        # Ninguno de los cuatro estaba en el once el 19/09. Sin
        # esta marca la regla del deficit los trata a todos como
        # titulares -el lado seguro- y no cobraria nada.
        "in_lineup": False,
        "expires_at": LEJOS,
        "until": LEJOS,
        "player_ids": [offer_id],
        "players": [
            {
                "name": nombre,
                "in_lineup": False,
                "franchise_score": franquicia,
                "strategic_score": 0.0,
            }
        ],
    }


OFERTAS = [
    oferta(1, "Barzic", 144_800, -3.5),
    oferta(2, "Oriol Rey", 1_199_400, 0.8),
    oferta(3, "Pablo Duran", 362_700, 0.8),
    oferta(4, "Boyomo", 1_845_800, 4.9),
]

GARANTIA = {
    "required_recovery": DEFICIT,
    "expected_liquidity": 0,
    "state": "CUBIERTO",
}

SOLVENCIA = {
    "balance": SALDO,
    "guarantee": GARANTIA,
    "solvency_guarantee": GARANTIA,
    "incoming_offer_liquidity": {"offers": OFERTAS},
}

HISTORIAL = {"offers": {}}


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. La lista de ofertas no llega vacia")

check(
    "el banco trae ofertas",
    len(OFERTAS) == 4,
    f"(n={len(OFERTAS)})",
)

vacia = calculate_offer_reservations(
    balance=SALDO,
    incoming={"offers": []},
    guarantee=GARANTIA,
)

check(
    "con la lista vacia no se reserva nada",
    vacia["reserved_total"] == 0 and not vacia["reserved"],
    f"(total={vacia['reserved_total']})",
)

check(
    "y con la lista vacia la deuda NO queda cubierta",
    vacia["debt_covered_by_secured"] is False,
)


# ================================================================
# 1. LA RESERVA SE DIMENSIONA CONTRA EL DEFICIT
# ================================================================

print()
print("1. La reserva se mide contra el deficit que la motivo")

reserva = calculate_offer_reservations(
    balance=SALDO,
    incoming={"offers": OFERTAS},
    guarantee=GARANTIA,
)

check(
    "el motor reserva por al menos la deuda actual",
    reserva["secured_needed"] >= DEFICIT,
    f"(secured_needed={reserva['secured_needed']}, deuda={DEFICIT})",
)

check(
    "y reserva ofertas de verdad, no liquidez esperada",
    reserva["reserved_total"] >= DEFICIT,
    f"(reservado={reserva['reserved_total']})",
)

RESERVADAS = set(reserva["reserved_offer_ids"])

check(
    "hay al menos una oferta reservada",
    len(RESERVADAS) >= 1,
    f"(ids={sorted(RESERVADAS)})",
)


# ================================================================
# 2. EL CANDADO: SIN RELOJ, NINGUNA RESERVADA SE PUEDE ACEPTAR
# ================================================================

print()
print("2. Con el deficit vivo y sin presion de reloj")


def decidir(o, horas_al_cierre, reservadas):
    return analyze_computer_offer(
        offer=o,
        solvency=SOLVENCIA,
        reserved_offer_ids=reservadas,
        history=HISTORIAL,
        hours_to_deadline=horas_al_cierre,
    )


SIN_PRISA = 480.0  # el `hours_to_solvency_deadline` de la foto

decisiones_sin_prisa = {
    o["offer_id"]: decidir(o, SIN_PRISA, RESERVADAS)["action"]
    for o in OFERTAS
    if o["offer_id"] in RESERVADAS
}

print(f"       reservadas: {decisiones_sin_prisa}")

check(
    "ninguna reservada sale como aceptable",
    all(
        accion != "ACCEPT_BEFORE_EXPIRY"
        for accion in decisiones_sin_prisa.values()
    ),
    f"({decisiones_sin_prisa})",
)

check(
    "todas se quedan retenidas por la reserva",
    all(
        accion == "KEEP_SOLVENCY_RESERVED"
        for accion in decisiones_sin_prisa.values()
    ),
    f"({decisiones_sin_prisa})",
)


# ================================================================
# 3. LA UNICA LLAVE ES EL RELOJ, NO EL DEFICIT
# ================================================================

print()
print("3. La misma oferta y el mismo deficit, con el reloj encima")

CON_PRISA = ACCEPT_BEFORE_DEADLINE_HOURS - 0.5

decisiones_con_prisa = {
    o["offer_id"]: decidir(o, CON_PRISA, RESERVADAS)["action"]
    for o in OFERTAS
    if o["offer_id"] in RESERVADAS
}

print(f"       reservadas: {decisiones_con_prisa}")

check(
    "con el cierre encima SI se aceptan",
    all(
        accion == "ACCEPT_BEFORE_EXPIRY"
        for accion in decisiones_con_prisa.values()
    ),
    f"({decisiones_con_prisa})",
)

check(
    "lo que cambio fue el reloj, no el deficit",
    decisiones_sin_prisa != decisiones_con_prisa
    and SOLVENCIA["balance"] == SALDO,
)

check(
    "las dos puertas son relojes, y valen lo mismo",
    ACCEPT_BEFORE_EXPIRY_HOURS == 6.0
    and ACCEPT_BEFORE_DEADLINE_HOURS == 6.0,
    f"(expiry={ACCEPT_BEFORE_EXPIRY_HOURS}, "
    f"deadline={ACCEPT_BEFORE_DEADLINE_HOURS})",
)


# ================================================================
# 4. EL CANDADO, Y LA LLAVE QUE SE LE PUSO EL 19/09
# ================================================================
#
#     Esta seccion estuvo EN ROJO a proposito hasta que el dueno
#     decidio la regla del cobro en deficit. Ahora comprueba las
#     dos mitades: que el candado sigue cerrado sin la regla, y
#     que la regla lo abre.

print()
print("4. Con deficit vivo y todo reservado, alguna se debe poder cobrar")

TODAS = {o["offer_id"] for o in OFERTAS}

sin_la_regla = {
    o["offer_id"]: decidir(o, SIN_PRISA, TODAS)["action"]
    for o in OFERTAS
}

print(f"       sin la regla: {sin_la_regla}")

reservado_total = sum(o["amount"] for o in OFERTAS)

check(
    "sin la regla, el candado sigue cerrado",
    all(
        accion == "KEEP_SOLVENCY_RESERVED"
        for accion in sin_la_regla.values()
    ),
    f"<- EL CANDADO. Con {DEFICIT:,} de deficit y "
    f"{reservado_total:,} EUR reservados para taparlo, el motor "
    f"no suelta ni un euro mientras no aprieta el reloj.",
)

# Y con la regla: el plan elige, y la reserva cede.
plan = el_cobro_que_cierra(DEFICIT, OFERTAS)

con_la_regla = {
    o["offer_id"]: analyze_computer_offer(
        offer=o,
        solvency=SOLVENCIA,
        reserved_offer_ids=TODAS,
        history=HISTORIAL,
        hours_to_deadline=SIN_PRISA,
        cobro_por_deficit=plan["offer_ids"],
    )["action"]
    for o in OFERTAS
}

print(f"       con la regla: {con_la_regla}")

check(
    "con la regla, al menos una se acepta para tapar el deficit",
    any(
        accion == "ACCEPT_BEFORE_EXPIRY"
        for accion in con_la_regla.values()
    ),
    f"({con_la_regla})",
)

check(
    "y solo una: no se cobra de mas",
    sum(
        1
        for accion in con_la_regla.values()
        if accion == "ACCEPT_BEFORE_EXPIRY"
    )
    == 1,
    f"({con_la_regla})",
)

check(
    "sin que el reloj se haya movido",
    SIN_PRISA == 480.0,
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
