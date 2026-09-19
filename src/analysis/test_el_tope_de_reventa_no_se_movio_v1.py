"""
El tope de la via de reventa sigue en 0,25 % exacto.

POR QUE ESTA GUARDIA EXISTE

    El 19/09 se le dio tope propio a la via del once. Hasta ese
    dia los dos numeros estaban ATADOS a proposito, y el
    comentario lo decia:

        TOPE_DE_PRIMA_DE_FICHAJE = PRIMA_MAXIMA_DE_PUJA
        "NO ES UN NUMERO NUEVO. Es el mismo +0,25 % que
         `optimal_bid` ya aplica a SPECULATION, extendido a la
         via del once. Si alguien lo mueve alli, se mueve aqui."

    Desatarlos es justo lo que se pidio. Y desatar dos numeros
    que estaban juntos abre el fallo de que uno se lleve al otro
    por delante sin que nadie lo vea, que es la clase de cosa que
    solo se nota cuando ya ha costado dinero.

    En reventa el margen ES el negocio: ahi el tope aprieta a
    proposito. El encargo lo dejo por escrito, SIN TOCAR.

QUE COMPRUEBA ESTA GUARDIA

    1. `PRIMA_MAXIMA_DE_PUJA` vale 0,0025 exacto.
    2. El tope que se aplica a SPECULATION es ese y no otro.
    3. El interruptor del once NO mueve la via de reventa, ni
       encendido ni apagado.
    4. Los dos numeros son distintos: si alguien vuelve a
       atarlos, esto se pone rojo.

    Y ademas quedan clavados los otros umbrales que el encargo
    declaro intactos, para que un cambio de los de al lado no se
    cuele: el suelo de cobro (+1 %) y el tope por operacion del
    carril.

LA GUARDIA MUERDE SI EL TOPE CAMBIA

    Es su unico trabajo. Un `PRIMA_MAXIMA_DE_PUJA = 0.005` la
    pone en rojo, que es lo que tiene que pasar.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.el_carril_de_un_dia import (  # noqa: E402
    TOPE_DE_COMPRA,
)
from src.analysis.rival_bid_model import (  # noqa: E402
    DEFAULT_PREMIUM_CURVE,
    PRIMA_MAXIMA_DE_PUJA,
    SPECULATION_INTENT,
    TOPE_DEL_ONCE_ENV,
    TOPE_DE_PRIMA_DEL_ONCE,
    optimal_bid,
    tope_por_la_prima,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def con_tope(valor):
    if valor:
        os.environ[TOPE_DEL_ONCE_ENV] = valor
    else:
        os.environ.pop(TOPE_DEL_ONCE_ENV, None)


def _rival(uid, capacidad, participacion):
    return {
        "user_id": uid,
        "name": f"R{uid}",
        "capacity": capacidad,
        "bids_made": 50,
        "max_observed_bid": 17_000_000,
        "participation": participacion,
        "profile": "AGGRESSIVE",
        "coverage": 1.0,
        "never_bids": False,
    }


MODELO = {
    "available": True,
    "auctions_observed": 161,
    "premium": {
        "curve": list(DEFAULT_PREMIUM_CURVE),
        "calibrated": False,
        "samples": 0,
    },
    "rivals": [
        _rival(1, 24_946_665, 0.7596),
        _rival(2, 20_996_791, 0.6211),
        _rival(3, 13_504_241, 0.2774),
    ],
}

PRECIO = 1_850_000

VALOR = 2_278_096


# ================================================================
# 1. EL NUMERO, EXACTO
# ================================================================

print()
print("1. El tope de reventa vale 0,25 % exacto")

check(
    "PRIMA_MAXIMA_DE_PUJA == 0.0025",
    PRIMA_MAXIMA_DE_PUJA == 0.0025,
    f"({PRIMA_MAXIMA_DE_PUJA})",
)

check(
    "que es 0,2500 %",
    round(100 * PRIMA_MAXIMA_DE_PUJA, 4) == 0.25,
    f"({100 * PRIMA_MAXIMA_DE_PUJA:.4f} %)",
)

check(
    "y el techo que produce sobre el precio de Chust",
    tope_por_la_prima(PRECIO, PRIMA_MAXIMA_DE_PUJA) == 1_854_626,
    f"({tope_por_la_prima(PRECIO, PRIMA_MAXIMA_DE_PUJA):,})",
)


# ================================================================
# 2. ES EL QUE SE APLICA A SPECULATION
# ================================================================

print()
print("2. Es el que se aplica de verdad a la via de reventa")

con_tope(None)

try:
    apagado = optimal_bid(
        price=PRECIO, value=VALOR, model=MODELO,
        available_budget=20_000_000, intent=SPECULATION_INTENT,
    )

    check(
        "la puja de reventa no pasa del techo del 0,25 %",
        apagado.get("bid")
        <= tope_por_la_prima(PRECIO, PRIMA_MAXIMA_DE_PUJA),
        f"({apagado.get('bid'):,})",
    )

    # ------------------------------------------------------
    # 3. EL INTERRUPTOR DEL ONCE NO LA TOCA
    # ------------------------------------------------------

    print()
    print("3. El interruptor del once no mueve la reventa")

    con_tope("1")

    encendido = optimal_bid(
        price=PRECIO, value=VALOR, model=MODELO,
        available_budget=20_000_000, intent=SPECULATION_INTENT,
    )

    print(
        f"       reventa apagado {apagado.get('bid'):,}  "
        f"encendido {encendido.get('bid'):,}"
    )

    check(
        "la puja de reventa es la misma con el once encendido",
        apagado.get("bid") == encendido.get("bid"),
        f"({apagado.get('bid')} vs {encendido.get('bid')})",
    )

    check(
        "y sigue sin pasar del 0,25 %",
        encendido.get("bid")
        <= tope_por_la_prima(PRECIO, PRIMA_MAXIMA_DE_PUJA),
    )

finally:
    con_tope(None)


# ================================================================
# 4. LOS DOS NUMEROS ESTAN DESATADOS
# ================================================================

print()
print("4. Los dos topes son numeros distintos")

check(
    "el del once no es el de reventa",
    TOPE_DE_PRIMA_DEL_ONCE != PRIMA_MAXIMA_DE_PUJA,
    f"({TOPE_DE_PRIMA_DEL_ONCE} vs {PRIMA_MAXIMA_DE_PUJA})",
)

check(
    "y el del once es 5,01 veces el de reventa",
    round(TOPE_DE_PRIMA_DEL_ONCE / PRIMA_MAXIMA_DE_PUJA, 2)
    == 5.01,
    f"(x{TOPE_DE_PRIMA_DEL_ONCE / PRIMA_MAXIMA_DE_PUJA:.2f})",
)


# ================================================================
# 5. LOS DE AL LADO, QUE NO SE TOCARON
# ================================================================

print()
print("5. Los umbrales declarados intactos siguen intactos")

check(
    "el tope de compra del carril sigue en 0,25 %",
    TOPE_DE_COMPRA == 0.0025,
    f"({TOPE_DE_COMPRA})",
)

SUELO_DE_COBRO = 0.01

check(
    "el suelo de cobro sigue en +1 %",
    round(
        (1 + SUELO_DE_COBRO) * (1 + PRIMA_MAXIMA_DE_PUJA) - 1, 6
    )
    == round(TOPE_DE_PRIMA_DEL_ONCE, 6),
    "<- si el suelo se movio, el tope del once ya no es su "
    "producto",
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
