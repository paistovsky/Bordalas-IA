"""
El once no se toca para cubrir el deficit.

LA MITAD DE LA REGLA QUE PROTEGE EL MARCADOR

    "...la oferta de mejor prima entre los jugadores que NO estan
    en el once."

    Los puntos son el marcador; la caja es el medio. Vender un
    titular para tapar un agujero de caja cambia lo que se mide
    por lo que se usa para medir.

    Es `A_NO_XI` con un criterio de orden, y por eso la regla no
    necesita un plan aparte: el plan ES la regla.

SIN SABER, SE SUPONE QUE SI ESTA EN EL ONCE

    `_esta_en_el_once` devuelve True cuando no hay marca. Es el
    lado seguro: equivocarse diciendo que no esta cuesta un
    titular; equivocarse diciendo que si cuesta esperar a la
    siguiente oferta. Una oferta sin jugadores tampoco se puede
    juzgar, y no se adivina.

QUE COMPRUEBA ESTA GUARDIA

    1. Ningun titular entra en la seleccion, aunque su oferta sea
       la de MEJOR PRIMA de todas.
    2. Ni aunque sea la unica que cubriria el deficit ella sola.
    3. Sale descartado con el motivo `EN_EL_ONCE`.
    4. Una oferta sin marca de once se trata como titular.
    5. Una oferta con varios jugadores queda fuera si CUALQUIERA
       de ellos es titular.

LA GUARDIA MUERDE SI NO HAY TITULARES CON OFERTA

    Sin un titular con oferta no hay nada que proteger y las
    cinco pasarian por vacuidad. Por eso lo primero es exigir que
    el banco traiga titulares con oferta.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.la_regla_del_deficit import (  # noqa: E402
    _esta_en_el_once,
    el_cobro_que_cierra,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def oferta(offer_id, nombre, importe, prima, en_el_once):
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


DEFICIT = 455_766

# Jutgla es titular Y trae la mejor prima Y cubre el solo.
OFERTAS = [
    oferta(1, "Jutgla", 5_000_000, 12.0, True),
    oferta(2, "Dituro", 2_294_000, 8.0, True),
    oferta(3, "Boyomo", 1_845_800, 4.9, False),
    oferta(4, "Barzic", 144_800, -3.5, False),
]


# ================================================================
# 0. HAY TITULARES CON OFERTA
# ================================================================

print()
print("0. El banco trae titulares con oferta")

titulares = [o for o in OFERTAS if o["in_lineup"]]

check(
    "hay titulares con oferta",
    len(titulares) == 2,
    f"(n={len(titulares)})",
)

check(
    "y uno de ellos trae la MEJOR prima de todas",
    max(OFERTAS, key=lambda o: o["premium_percent"])["in_lineup"]
    is True,
)

check(
    "y cubriria el deficit el solo",
    titulares[0]["amount"] > DEFICIT,
    f"({titulares[0]['amount']:,} vs {DEFICIT:,})",
)


# ================================================================
# 1. NINGUN TITULAR ENTRA
# ================================================================

print()
print("1. Ningun titular entra en la seleccion")

plan = el_cobro_que_cierra(DEFICIT, OFERTAS)

print(f"       elige {nombres(plan)}, total {plan['total']:,}")

check(
    "no entra ningun titular",
    not any(
        o["in_lineup"] for o in plan["seleccionadas"]
    ),
    f"({nombres(plan)})",
)

check(
    "entra el mejor de FUERA del once",
    nombres(plan) == ["Boyomo"],
    f"({nombres(plan)})",
)

check(
    "aunque Jutgla pagaba 12 % y Boyomo 4,9 %",
    plan["seleccionadas"][0]["premium_percent"] == 4.9,
)

check(
    "y aun asi el deficit queda tapado",
    plan["cubre"] is True,
)


# ================================================================
# 2. SALEN CON EL MOTIVO EN_EL_ONCE
# ================================================================

print()
print("2. Los titulares salen con su motivo")

en_el_once = [
    d for d in plan["descartadas"] if d["motivo"] == "EN_EL_ONCE"
]

check(
    "los dos titulares salen como EN_EL_ONCE",
    len(en_el_once) == 2,
    f"({[(d['offer_id'], d['motivo']) for d in plan['descartadas']]})",
)

check(
    "con el motivo escrito",
    all("once no se toca" in d["reason"] for d in en_el_once),
    f"({en_el_once[0]['reason'] if en_el_once else None})",
)


# ================================================================
# 3. SIN MARCA, SE SUPONE TITULAR
# ================================================================

print()
print("3. Sin saberlo, se supone que si esta en el once")

check(
    "una oferta sin marca ninguna cuenta como titular",
    _esta_en_el_once({"amount": 1_000_000}) is True,
)

check(
    "una oferta con jugadores sin marca, tambien",
    _esta_en_el_once(
        {"players": [{"name": "X"}]}
    ) is True,
)

check(
    "una oferta sin jugadores no se puede juzgar: titular",
    _esta_en_el_once({"players": []}) is True,
)

check(
    "y con la marca a False si sale del once",
    _esta_en_el_once(
        {"players": [{"name": "X", "in_lineup": False}]}
    ) is False,
)

sin_marca = [
    {"offer_id": 9, "amount": 9_000_000, "premium_percent": 50.0},
]

plan_ciego = el_cobro_que_cierra(DEFICIT, sin_marca)

check(
    "y por eso una oferta sin marca no se cobra",
    plan_ciego["seleccionadas"] == [],
    f"({plan_ciego['seleccionadas']})",
)


# ================================================================
# 4. BASTA CON QUE UNO DEL LOTE SEA TITULAR
# ================================================================

print()
print("4. Si CUALQUIERA del lote es titular, el lote no entra")

LOTE = [
    {
        "offer_id": 20,
        "amount": 3_000_000,
        "premium_percent": 20.0,
        "players": [
            {"name": "Suplente", "in_lineup": False},
            {"name": "Titular", "in_lineup": True},
        ],
    },
    oferta(21, "Boyomo", 1_845_800, 4.9, False),
]

plan_lote = el_cobro_que_cierra(DEFICIT, LOTE)

check(
    "el lote con un titular dentro no entra",
    20 not in plan_lote["offer_ids"],
    f"({plan_lote['offer_ids']})",
)

check(
    "y se elige el que no toca el once",
    plan_lote["offer_ids"] == {21},
    f"({plan_lote['offer_ids']})",
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
