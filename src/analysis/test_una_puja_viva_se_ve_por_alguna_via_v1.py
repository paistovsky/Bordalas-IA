"""
Una puja viva se ve por alguna via.

EL CASO, CON LAS DOS FOTOS DELANTE

    18/09 12:16:07   se pone la puja por Maffeo, 1.664.350
    18/09 16:16:38   foto
    19/09 05:26:03   la puja se resuelve: GANADA

    Lo que la foto de las 16:16 dijo DE VERDAD (medido sobre
    `diagnostico/status.json` de esa vuelta):

        TABLON      -> 1.664.350   la vio
        RESTA       -> 1.664.350   la vio, al euro
        DIFERENCIA  -> 0           no la vio

    Dos de las tres la vieron. La tercera no, y no por fallar.

POR QUE LA VIA C DICE CERO SIN EQUIVOCARSE

    `por_la_diferencia` mide un INCREMENTO entre dos fotos, no un
    NIVEL. La puja se puso a las 12:16; a las 16:16 ya estaba en
    las dos fotos que se comparan, asi que `maximumBid` no bajo
    entre ellas y el incremento es cero. Correcto.

    El fallo no es el cero: es publicarlo junto a dos niveles
    como si midiera lo mismo. Eso es la doctrina 54 -numerador y
    denominador del mismo periodo- y es lo que produce el
    `disagreement: 1.664.350` de esa foto.

MAXIMUMBID SI DESCUENTA LAS PUJAS VIVAS

    La via B lo prueba al euro con las cifras de la foto:

        4.324.615 + 13.210.000 - 15.870.265 = 1.664.350

    con la linea medida = 0,25 x 52.840.000 de plantilla. El
    `mismatch` salio 0. El panel lo afirmaba y es cierto.

QUE COMPRUEBA ESTA GUARDIA

    1. Con una puja viva, AL MENOS UNA via la reporta.
    2. La via B reconstruye el importe exacto de la foto real.
    3. La via C vale para incrementos, no para niveles: entre dos
       fotos con la puja ya puesta da cero, y eso NO puede
       contarse como "no hay pujas".
    4. Cuando las vias discrepan manda la mas conservadora: la
       que diga que hay MAS dinero comprometido.

LA GUARDIA MUERDE CON EL LIBRO DE PUJAS VACIO

    Sin pujas no hay nada que ver y las cuatro pasarian por
    vacuidad. Por eso lo primero es exigir que el banco traiga
    una puja viva, y que con el tablon vacio la via A diga que no
    ve nada SIN afirmar que no hay nada.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui, copiados de la foto del 18/09 16:16:38.
    No se lee `diagnostico/status.json` ni `data/`, no se sale a
    la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.pujas_del_dueno import (  # noqa: E402
    por_el_tablon,
    por_la_diferencia,
    por_la_resta,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO: LA FOTO DEL 18/09 16:16:38, TAL CUAL
# ================================================================

SALDO = 4_324_615

TOPE = 15_870_265

PLANTILLA = 52_840_000

COMPROMETIDO = 1_664_350          # la puja de Maffeo

MARGEN = 13_210_000               # 0,25 x PLANTILLA

# La foto anterior: la puja YA estaba puesta (12:16 < 15:16), asi
# que `maximumBid` es el mismo y el saldo no se ha movido.
FOTO_ANTES = {
    "balance": SALDO,
    "maximum_bid": TOPE,
    "hours_to_reset": 15.7,
}

FOTO_AHORA = {
    "balance": SALDO,
    "maximum_bid": TOPE,
    "hours_to_reset": 14.7,
}

# Lo que `build_bid_exposure` entrego en esa vuelta.
TABLON_CON_PUJA = {
    "available": True,
    "committed_total": COMPROMETIDO,
    "operation_count": 1,
}

TABLON_VACIO = {
    "available": True,
    "committed_total": 0,
    "operation_count": 0,
}


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. El libro de pujas no llega vacio")

check(
    "hay una puja viva en el banco",
    TABLON_CON_PUJA["operation_count"] == 1
    and TABLON_CON_PUJA["committed_total"] == COMPROMETIDO,
    f"(n={TABLON_CON_PUJA['operation_count']})",
)

vacia = por_el_tablon(TABLON_VACIO)

check(
    "con el tablon vacio la via A reporta cero",
    vacia["committed"] == 0,
)

check(
    "y NO afirma que no haya pujas: dice que no ve ninguna",
    "no prueba que no la haya" in (vacia["reason"] or ""),
    f"({vacia['reason']})",
)


# ================================================================
# 1. CON LA PUJA VIVA, ALGUNA VIA LA VE
# ================================================================

print()
print("1. Con la puja viva, al menos una via la reporta")

a = por_el_tablon(TABLON_CON_PUJA)

b = por_la_resta(
    balance=SALDO,
    maximum_bid=TOPE,
    valor_plantilla=PLANTILLA,
)

c = por_la_diferencia(FOTO_ANTES, FOTO_AHORA)

vias = {"TABLON": a, "RESTA": b, "DIFERENCIA": c}

for nombre, via in vias.items():
    print(f"       {nombre:11s} -> {via.get('committed')}")

check(
    "al menos una via ve la puja",
    any(
        int(via.get("committed") or 0) > 0
        for via in vias.values()
    ),
    f"({[v.get('committed') for v in vias.values()]})",
)

check(
    "y son DOS las que la ven, no una",
    sum(
        1
        for via in vias.values()
        if int(via.get("committed") or 0) == COMPROMETIDO
    )
    == 2,
)


# ================================================================
# 2. LA RESTA RECONSTRUYE EL IMPORTE EXACTO
# ================================================================

print()
print("2. La via B da el importe al euro")

check(
    "la resta reconstruye la puja exacta",
    b["committed"] == COMPROMETIDO,
    f"(dio {b['committed']}, esperado {COMPROMETIDO})",
)

check(
    "con la linea de credito medida, no supuesta",
    b["credit_line"] == MARGEN,
    f"(dio {b['credit_line']}, esperado {MARGEN})",
)

check(
    "y sin descuadre",
    b["mismatch"] == 0,
    f"(mismatch={b['mismatch']})",
)

check(
    "luego maximumBid SI descuenta las pujas vivas",
    SALDO + MARGEN - TOPE == COMPROMETIDO,
    f"({SALDO} + {MARGEN} - {TOPE} = {SALDO + MARGEN - TOPE})",
)


# ================================================================
# 3. LA VIA C MIDE INCREMENTOS, NO NIVELES
# ================================================================

print()
print("3. La via C mide incrementos: su cero no es 'no hay pujas'")

check(
    "entre dos fotos con la puja ya puesta, da cero",
    c["committed"] == 0 and c["delta"] == 0,
    f"(committed={c['committed']}, delta={c['delta']})",
)

check(
    "y lo dice como lo que es: nada NUEVO comprometido",
    "nada nuevo" in (c["reason"] or "").lower(),
    f"({c['reason']})",
)

# El otro lado: cuando SI baja entre dos fotos, la ve.
FOTO_SIN_PUJA = {
    "balance": SALDO,
    "maximum_bid": TOPE + COMPROMETIDO,
    "hours_to_reset": 16.7,
}

c_nueva = por_la_diferencia(FOTO_SIN_PUJA, FOTO_AHORA)

check(
    "y una puja NUEVA entre dos fotos si la ve",
    c_nueva["committed"] == COMPROMETIDO,
    f"(dio {c_nueva['committed']})",
)


# ================================================================
# 4. MANDA LA MAS CONSERVADORA
# ================================================================

print()
print("4. Cuando discrepan manda la que diga que hay MAS comprometido")

mayor = max(
    int(via.get("committed") or 0) for via in vias.values()
)

check(
    "la mas conservadora es la que vio la puja",
    mayor == COMPROMETIDO,
    f"(mayor={mayor})",
)

check(
    "y nunca se publica la optimista",
    mayor != 0,
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
