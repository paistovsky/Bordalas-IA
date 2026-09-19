"""
No se cobra de mas: solo hasta volver a positivo.

LA MITAD DE LA REGLA QUE CUESTA DINERO SI SE OLVIDA

    "...y solo hasta volver a positivo. Ni un euro mas."

    Cada oferta aceptada es un jugador que se va. Cobrar de mas
    para tener colchon es vender plantilla por comodidad, y no se
    nota: la caja sale bien y el once sale peor, que es
    exactamente la clase de coste que nadie va a buscar.

    Por eso el plan se para en cuanto la suma cubre el deficit, y
    lo que queda fuera queda fuera CON SU MOTIVO
    (`YA_ESTA_CUBIERTO`), no en silencio.

EL ORDEN: MEJOR PRIMA PRIMERO

    A igualdad de prima manda el importe mayor, porque cierra el
    agujero con menos jugadores. Las dos cosas empujan al mismo
    sitio: menos gente fuera.

QUE COMPRUEBA ESTA GUARDIA

    1. Si UNA sola oferta ya cubre, se acepta UNA. No dos.
    2. Si hacen falta dos, se aceptan dos y ni una mas.
    3. Lo descartado por estar ya cubierto lo dice con ese
       motivo.
    4. Cuando ninguna combinacion llega, se aceptan todas las de
       fuera del once y se dice que no llega — sin tocar el once.
    5. A igualdad de prima entra antes la de importe mayor.

LA GUARDIA MUERDE SI UNA SOLA CUBRE Y SE ACEPTAN DOS

    Es su caso principal, y es el de la foto del 19/09: Boyomo
    solo (1.845.800) ya tapa los 455.766.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.la_regla_del_deficit import (  # noqa: E402
    el_cobro_que_cierra,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def oferta(offer_id, nombre, importe, prima, en_el_once=False):
    return {
        "offer_id": offer_id,
        "amount": importe,
        "premium_percent": prima,
        "in_lineup": en_el_once,
        "players": [{"name": nombre, "in_lineup": en_el_once}],
    }


def nombres(plan):
    return [
        o["players"][0]["name"] for o in plan["seleccionadas"]
    ]


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. El banco trae ofertas que suman mucho mas")

DEFICIT = 455_766

MUCHAS = [
    oferta(1, "Barzic", 144_800, -3.5),
    oferta(2, "Oriol Rey", 1_199_400, 0.8),
    oferta(3, "Pablo Duran", 362_700, 0.8),
    oferta(4, "Boyomo", 1_845_800, 4.9),
]

suma = sum(o["amount"] for o in MUCHAS)

check(
    "hay cuatro ofertas",
    len(MUCHAS) == 4,
)

check(
    "y suman mucho mas que el deficit",
    suma > DEFICIT * 7,
    f"(suman {suma:,}, deficit {DEFICIT:,})",
)


# ================================================================
# 1. SI UNA CUBRE, SE ACEPTA UNA
# ================================================================

print()
print("1. Si una sola cubre, se acepta una")

plan = el_cobro_que_cierra(DEFICIT, MUCHAS)

print(f"       elige {nombres(plan)}, total {plan['total']:,}")

check(
    "se acepta exactamente una",
    len(plan["seleccionadas"]) == 1,
    f"(acepto {len(plan['seleccionadas'])}: {nombres(plan)})",
)

check(
    "es la de mejor prima",
    nombres(plan) == ["Boyomo"],
    f"({nombres(plan)})",
)

check(
    "y cubre",
    plan["cubre"] is True and plan["total"] >= DEFICIT,
)

check(
    "lo que sobra queda contado",
    plan["sobra"] == plan["total"] - DEFICIT,
    f"(sobra {plan['sobra']})",
)


# ================================================================
# 2. LO DESCARTADO DICE POR QUE
# ================================================================

print()
print("2. Lo que no entra dice por que")

ya_cubierto = [
    d for d in plan["descartadas"]
    if d["motivo"] == "YA_ESTA_CUBIERTO"
]

check(
    "las tres restantes salen como YA_ESTA_CUBIERTO",
    len(ya_cubierto) == 3,
    f"({[(d['offer_id'], d['motivo']) for d in plan['descartadas']]})",
)

check(
    "con un motivo que se entiende sin abrir el codigo",
    all("no se cobra de mas" in d["reason"].lower()
        for d in ya_cubierto),
)


# ================================================================
# 3. SI HACEN FALTA DOS, SE ACEPTAN DOS
# ================================================================

print()
print("3. Si hacen falta dos, dos. Ni una mas")

GRANDE = 2_000_000

plan2 = el_cobro_que_cierra(GRANDE, MUCHAS)

print(f"       elige {nombres(plan2)}, total {plan2['total']:,}")

check(
    "se aceptan dos",
    len(plan2["seleccionadas"]) == 2,
    f"(acepto {len(plan2['seleccionadas'])}: {nombres(plan2)})",
)

check(
    "en orden de prima: Boyomo y luego el siguiente",
    nombres(plan2)[0] == "Boyomo",
    f"({nombres(plan2)})",
)

check(
    "la suma cubre",
    plan2["total"] >= GRANDE,
    f"({plan2['total']} vs {GRANDE})",
)

check(
    "y sin las dos NO cubriria: no sobra ninguna",
    plan2["total"] - plan2["seleccionadas"][-1]["amount"]
    < GRANDE,
)


# ================================================================
# 4. CUANDO NINGUNA COMBINACION LLEGA
# ================================================================

print()
print("4. Cuando no llega, se dice y no se toca el once")

IMPOSIBLE = 50_000_000

CON_TITULAR = [
    *MUCHAS,
    oferta(5, "Jutgla", 40_000_000, 9.9, en_el_once=True),
]

plan3 = el_cobro_que_cierra(IMPOSIBLE, CON_TITULAR)

check(
    "no cubre, y lo dice",
    plan3["cubre"] is False
    and "NO llegan" in plan3["reason"]
    and "no se sale del rojo" in plan3["reason"],
    f"({plan3['reason'][:80]})",
)

check(
    "acepta todas las de fuera del once",
    len(plan3["seleccionadas"]) == 4,
    f"({nombres(plan3)})",
)

check(
    "y el titular sigue fuera aunque su prima sea la mejor",
    "Jutgla" not in nombres(plan3),
    f"({nombres(plan3)})",
)


# ================================================================
# 5. A IGUALDAD DE PRIMA, EL IMPORTE MAYOR
# ================================================================

print()
print("5. A igualdad de prima, el importe mayor")

EMPATE = [
    oferta(10, "Pequeno", 300_000, 1.0),
    oferta(11, "Grande", 900_000, 1.0),
]

plan4 = el_cobro_que_cierra(500_000, EMPATE)

check(
    "entra el de importe mayor",
    nombres(plan4) == ["Grande"],
    f"({nombres(plan4)})",
)

check(
    "y con uno basta",
    len(plan4["seleccionadas"]) == 1,
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
