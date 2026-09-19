"""
El deficit vence a la reserva, y tambien a la buena oferta.

LA REGLA, DECIDIDA POR EL DUENO EL 19/09/2026

    Si hay deficit, se acepta la oferta de mejor prima entre los
    jugadores que NO estan en el once, y solo hasta volver a
    positivo. Ni un euro mas.

    No hay reloj, no hay ventana de seis horas, no hay espera.

LOS DOS FRENOS, Y POR QUE HACEN FALTA LOS DOS

    Medido el 19/09 con el caso real (saldo -455.766):

        Barzic, Oriol Rey    HOLD_SOLVENCY_RESERVED
        Boyomo, Pablo Duran  KEEP_GOOD_OFFER

    El primero solo cedia por RELOJ: las dos puertas de
    `analyze_computer_offer` a <= 6,0 h, y el deficit no entraba
    en esa decision. El segundo ni siquiera miraba la solvencia.

    Levantar solo la reserva no desbloquea nada: Boyomo y Pablo
    Duran seguirian retenidos por calidad. Por eso la regla pasa
    por delante de los dos.

QUE COMPRUEBA ESTA GUARDIA

    1. Con deficit vivo y TODAS las ofertas marcadas
       SOLVENCY_RESERVED, el motor acepta al menos una.
    2. Y es la de mejor prima de fuera del once.
    3. El mismo caso con todas en KEEP_GOOD_OFFER -sin reserva
       ninguna- tambien cede.
    4. Sin presion de reloj: lo que abre la puerta es el
       deficit, no la caducidad.
    5. Apagado el interruptor, el comportamiento es el de
       siempre y los dos frenos siguen mandando.

LA GUARDIA MUERDE CON LA LISTA DE OFERTAS VACIA

    Sin ofertas no hay nada que aceptar y todo pasaria por
    vacuidad. Por eso lo primero es exigir que el banco traiga
    ofertas, y que con la lista vacia el plan lo diga en vez de
    devolver un plan vacio que parezca bueno.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados del caso del 19/09. No se lee
    `diagnostico/status.json` ni `data/`, no se sale a la red y
    no se escribe en ningun libro. Las caducidades son fechas
    fijas y lejanas (ano 2100) y la presion de cierre entra por
    parametro.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.computer_offer_reroll_engine import (  # noqa: E402
    ACCEPT_BEFORE_DEADLINE_HOURS,
    analyze_computer_offer,
)
from src.analysis.la_regla_del_deficit import (  # noqa: E402
    REGLA_ENV,
    el_cobro_que_cierra,
    regla_activa,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def con_regla(valor):
    if valor:
        os.environ[REGLA_ENV] = valor
    else:
        os.environ.pop(REGLA_ENV, None)


# ================================================================
# EL BANCO: EL CASO DEL 19/09
# ================================================================

SALDO = -455_766

DEFICIT = 455_766

LEJOS = "2100-01-01T00:00:00+00:00"

SIN_PRISA = 480.0          # el hours_to_solvency_deadline real


def oferta(offer_id, nombre, importe, prima, en_el_once):
    return {
        "offer_id": offer_id,
        "amount": importe,
        "premium_percent": prima,
        "in_lineup": en_el_once,
        "expires_at": LEJOS,
        "until": LEJOS,
        "player_ids": [offer_id],
        "players": [
            {
                "name": nombre,
                "in_lineup": en_el_once,
                "franchise_score": 0.0,
                "strategic_score": 0.0,
            }
        ],
    }


# Las cuatro de la foto. Barzic y Oriol Rey estaban reservados;
# Boyomo y Pablo Duran retenidos por KEEP_GOOD_OFFER.
OFERTAS = [
    oferta(1, "Barzic", 144_800, -3.5, False),
    oferta(2, "Oriol Rey", 1_199_400, 0.8, False),
    oferta(3, "Pablo Duran", 362_700, 0.8, False),
    oferta(4, "Boyomo", 1_845_800, 4.9, False),
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

TODAS = {o["offer_id"] for o in OFERTAS}


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. La lista de ofertas no llega vacia")

check(
    "el banco trae cuatro ofertas",
    len(OFERTAS) == 4,
    f"(n={len(OFERTAS)})",
)

vacio = el_cobro_que_cierra(DEFICIT, [])

check(
    "con la lista vacia no hay plan",
    vacio["available"] is False and not vacio["seleccionadas"],
)

check(
    "y lo dice en vez de devolver un plan vacio que parezca bueno",
    "vacia" in (vacio["reason"] or ""),
    f"({vacio['reason']})",
)

check(
    "sin deficit no se cobra nada",
    el_cobro_que_cierra(0, OFERTAS)["seleccionadas"] == [],
)


# ================================================================
# 1. EL PLAN: MEJOR PRIMA PRIMERO, Y SOLO HASTA POSITIVO
# ================================================================

print()
print("1. El plan de cobro")

plan = el_cobro_que_cierra(DEFICIT, OFERTAS)

nombres = [
    o["players"][0]["name"] for o in plan["seleccionadas"]
]

print(f"       elige: {nombres}  total {plan['total']:,}")
print(f"       {plan['reason']}")

check(
    "el plan cubre el deficit",
    plan["cubre"] is True,
    f"(total {plan['total']}, deficit {DEFICIT})",
)

check(
    "elige la de MEJOR PRIMA primero",
    nombres[0] == "Boyomo",
    f"(eligio {nombres})",
)

check(
    "y con una basta: no se cobra de mas",
    len(plan["seleccionadas"]) == 1,
    f"(eligio {len(plan['seleccionadas'])})",
)


# ================================================================
# 2. CON TODO RESERVADO, EL MOTOR ACEPTA AL MENOS UNA
# ================================================================

print()
print("2. Con deficit vivo y TODO reservado")


def decidir(o, reservadas, cobro):
    return analyze_computer_offer(
        offer=o,
        solvency=SOLVENCIA,
        reserved_offer_ids=reservadas,
        history=HISTORIAL,
        hours_to_deadline=SIN_PRISA,
        cobro_por_deficit=cobro,
    )


con_regla("1")

try:
    check(
        "la regla esta encendida",
        regla_activa() is True,
    )

    con_reserva = {
        o["offer_id"]: decidir(
            o, TODAS, plan["offer_ids"]
        )["action"]
        for o in OFERTAS
    }

    print(f"       {con_reserva}")

    aceptadas = [
        oid
        for oid, accion in con_reserva.items()
        if accion == "ACCEPT_BEFORE_EXPIRY"
    ]

    check(
        "el motor acepta al menos una",
        len(aceptadas) >= 1,
        f"({con_reserva})",
    )

    check(
        "y es la de mejor prima de fuera del once (Boyomo)",
        aceptadas == [4],
        f"(acepto {aceptadas})",
    )

    check(
        "las demas siguen retenidas: no se cobra de mas",
        len(aceptadas) == 1,
        f"(acepto {len(aceptadas)})",
    )

    # ------------------------------------------------------
    # 3. Y SIN RESERVA NINGUNA, TAMBIEN CEDE
    # ------------------------------------------------------

    print()
    print("3. El otro freno: sin reserva, KEEP_GOOD_OFFER")

    sin_reserva = {
        o["offer_id"]: decidir(
            o, set(), plan["offer_ids"]
        )["action"]
        for o in OFERTAS
    }

    print(f"       {sin_reserva}")

    check(
        "tambien acepta la elegida sin estar reservada",
        sin_reserva[4] == "ACCEPT_BEFORE_EXPIRY",
        f"({sin_reserva})",
    )

    # ------------------------------------------------------
    # 4. LO QUE ABRE LA PUERTA ES EL DEFICIT, NO EL RELOJ
    # ------------------------------------------------------

    print()
    print("4. Lo que abre la puerta es el deficit, no el reloj")

    check(
        "el cierre esta lejisimos",
        SIN_PRISA > ACCEPT_BEFORE_DEADLINE_HOURS * 10,
        f"({SIN_PRISA} h contra {ACCEPT_BEFORE_DEADLINE_HOURS})",
    )

    # Sin plan de cobro y con el mismo reloj lejano: nadie cede.
    sin_plan = {
        o["offer_id"]: decidir(o, TODAS, set())["action"]
        for o in OFERTAS
    }

    check(
        "sin plan de cobro, con el mismo reloj, no cede nadie",
        all(
            a != "ACCEPT_BEFORE_EXPIRY"
            for a in sin_plan.values()
        ),
        f"({sin_plan})",
    )

finally:
    con_regla(None)


# ================================================================
# 5. APAGADO, EL COMPORTAMIENTO ES EL DE SIEMPRE
# ================================================================

print()
print("5. Apagado reproduce produccion")

check(
    "con el interruptor apagado la regla no esta activa",
    regla_activa() is False,
)

apagado = {
    o["offer_id"]: analyze_computer_offer(
        offer=o,
        solvency=SOLVENCIA,
        reserved_offer_ids=TODAS,
        history=HISTORIAL,
        hours_to_deadline=SIN_PRISA,
    )["action"]
    for o in OFERTAS
}

print(f"       {apagado}")

check(
    "sin pasar el plan, las cuatro siguen retenidas",
    all(
        a == "KEEP_SOLVENCY_RESERVED" for a in apagado.values()
    ),
    f"({apagado})",
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
