"""
El tope de prima depende de la via, y de cual exactamente.

DE QUE CUELGA EL TOPE: DEL `intent`, NO DEL `route`

    En `optimal_bid`:

        if etiqueta == SPECULATION_INTENT:   tope = prima_maxima
        elif etiqueta in INTENTS_DEL_ONCE:   tope = el del once
        else:                                tope = None

    `route` entra en la funcion pero su propio docstring dice que
    "no entra en ninguna cuenta ni abre ni cierra ninguna
    puerta": solo sirve para el motivo. Y `market_gate.route_now`
    vive en el bloque de comparacion marcado "AL LADO Y SIN
    MANDAR".

    Asi que el miedo del encargo -que el `market_gate` reetiquete
    un fichaje del once y con el se mueva el tope- NO se cumple:
    esa etiqueta no decide el tope. La que decide es el `intent`.

LA DIRECCION DE ESTE ARREGLO ES LA CONTRARIA (doctrina 59)

    El encargo lo pedia como una subida de 0,25 % a 1,2525 %.
    Medido: la via del once NO TENIA TOPE. Con el valor real de
    Chust (2.278.096) Pepe ofrecia 1.942.501, un +5,00 %, cuatro
    veces lo que pago el dueno a mano.

    Asi que el tope nuevo BAJA el techo del once. Las dos pujas
    del dueno siguen cabiendo; la de Cabrera (+6,71 %) no.

QUE COMPRUEBA ESTA GUARDIA

    1. Dos candidatos del MISMO precio, uno para el once y otro
       para revender, salen con topes distintos.
    2. El tope del once es el 1,2525 % decidido, y sale del
       producto de sus dos factores, no escrito a mano.
    3. Mover el tope de reventa NO mueve el del once.
    4. El `route` no cambia el tope: el mismo `intent` con dos
       `route` distintos da el mismo techo.
    5. Cabrera no cabe ni con el tope nuevo.

LA GUARDIA MUERDE SI LOS DOS VAN POR LA MISMA VIA

    Si los dos candidatos salieran con el mismo `intent` no
    habria dos vias que comparar y todo pasaria por vacuidad.
    Por eso lo primero es exigir que sean dos vias distintas.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj. El interruptor se pone y se quita aqui dentro.
"""

import os
import sys

sys.path.insert(0, ".")

from src.analysis.rival_bid_model import (  # noqa: E402
    DEFAULT_PREMIUM_CURVE,
    INTENTS_DEL_ONCE,
    PRIMA_MAXIMA_DE_PUJA,
    SPECULATION_INTENT,
    TOPE_DEL_ONCE_ENV,
    TOPE_DE_PRIMA_DEL_ONCE,
    optimal_bid,
    tope_del_once_activo,
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


# EL MODELO, ESCRITO A MANO
#
#     Tres rivales con la participacion medida de los tres que de
#     verdad pujan en esta liga, y la curva de primas POR DEFECTO
#     -que es la que corre hoy: el modelo real trae
#     `calibrated: False` con 0 pujas medibles sobre 161
#     subastas observadas-.
#
#     No se lee `data/`: estos numeros estan copiados aqui.
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

PARA_EL_ONCE = "XI_UPGRADE"

PARA_REVENDER = SPECULATION_INTENT


# ================================================================
# 0. LOS DOS NO VAN POR LA MISMA VIA
# ================================================================

print()
print("0. Los dos candidatos van por vias distintas")

check(
    "el del once y el de reventa tienen intent distinto",
    PARA_EL_ONCE != PARA_REVENDER,
    f"({PARA_EL_ONCE} / {PARA_REVENDER})",
)

check(
    "y la via del once esta declarada como tal",
    PARA_EL_ONCE in INTENTS_DEL_ONCE,
    f"({sorted(INTENTS_DEL_ONCE)})",
)

check(
    "la de reventa NO esta entre las del once",
    PARA_REVENDER not in INTENTS_DEL_ONCE,
)


# ================================================================
# 1. MISMO PRECIO, DOS TOPES DISTINTOS
# ================================================================

print()
print("1. Mismo precio, topes distintos")

techo_once = tope_por_la_prima(PRECIO, TOPE_DE_PRIMA_DEL_ONCE)

techo_reventa = tope_por_la_prima(PRECIO, PRIMA_MAXIMA_DE_PUJA)

print(f"       once    {techo_once:,}  ({100 * TOPE_DE_PRIMA_DEL_ONCE:.4f} %)")
print(f"       reventa {techo_reventa:,}  ({100 * PRIMA_MAXIMA_DE_PUJA:.4f} %)")

check(
    "los dos techos son distintos",
    techo_once != techo_reventa,
    f"({techo_once} vs {techo_reventa})",
)

check(
    "y el del once es el mas alto",
    techo_once > techo_reventa,
)


# ================================================================
# 2. EL TOPE DEL ONCE SALE DE SUS DOS FACTORES
# ================================================================

print()
print("2. El 1,2525 % sale de su producto, no escrito a mano")

SUELO_DE_COBRO = 0.01

esperado = (1 + SUELO_DE_COBRO) * (1 + PRIMA_MAXIMA_DE_PUJA) - 1

check(
    "es (1+1 %) x (1+0,25 %) - 1",
    abs(TOPE_DE_PRIMA_DEL_ONCE - esperado) < 1e-12,
    f"({TOPE_DE_PRIMA_DEL_ONCE} vs {esperado})",
)

check(
    "y vale 1,2525 %",
    round(100 * TOPE_DE_PRIMA_DEL_ONCE, 4) == 1.2525,
    f"({100 * TOPE_DE_PRIMA_DEL_ONCE:.4f} %)",
)


# ================================================================
# 3. EL `route` NO CAMBIA EL TOPE
# ================================================================

print()
print("3. El route no mueve el tope: lo mueve el intent")

con_tope("1")

try:
    por_ruta = {}

    for ruta in ("XI_UPGRADE", "ROSTER_FILL", "PRICE_TREND",
                 "COMPUTER_RESALE", None):

        plan = optimal_bid(
            price=PRECIO,
            value=VALOR,
            model=MODELO,
            available_budget=20_000_000,
            intent=PARA_EL_ONCE,
            route=ruta,
        )

        por_ruta[str(ruta)] = plan.get("bid")

    print(f"       {por_ruta}")

    check(
        "el mismo intent con cinco routes da la misma puja",
        len(set(por_ruta.values())) == 1,
        f"({por_ruta})",
    )

    # Y el contraste: cambiar el INTENT si la mueve.
    como_reventa = optimal_bid(
        price=PRECIO,
        value=VALOR,
        model=MODELO,
        available_budget=20_000_000,
        intent=PARA_REVENDER,
        route="XI_UPGRADE",
    )

    check(
        "el tope aplicado depende del intent, no del route",
        tope_del_once_activo() == TOPE_DE_PRIMA_DEL_ONCE
        and como_reventa.get("bid") is not None,
    )

    # ------------------------------------------------------
    # 4. CABRERA NO CABE NI CON EL TOPE NUEVO
    # ------------------------------------------------------

    print()
    print("4. Cabrera no cabe ni con el tope nuevo")

    CASOS = [
        ("Chust", 1_850_000, 1_871_032, True),
        ("Dmitrovic", 4_740_000, 4_782_000, True),
        ("Cabrera", 2_920_000, 3_116_031, False),
    ]

    for nombre, precio, pujo, deberia in CASOS:

        techo = tope_por_la_prima(precio, TOPE_DE_PRIMA_DEL_ONCE)

        cabe = pujo <= techo

        pct = 100 * (pujo - precio) / precio

        check(
            f"{nombre} ({pct:+.2f} %) "
            f"{'cabe' if deberia else 'NO cabe'}",
            cabe is deberia,
            f"(pujo {pujo:,}, techo {techo:,})",
        )

finally:
    con_tope(None)


# ================================================================
# 5. APAGADO, LA VIA DEL ONCE SIGUE SIN TOPE
# ================================================================

print()
print("5. Apagado reproduce produccion: el once sin tope")

check(
    "con el interruptor apagado no hay tope del once",
    tope_del_once_activo() is None,
)

apagado = optimal_bid(
    price=PRECIO, value=VALOR, model=MODELO,
    available_budget=20_000_000, intent=PARA_EL_ONCE,
)

con_tope("1")

try:
    encendido = optimal_bid(
        price=PRECIO, value=VALOR, model=MODELO,
        available_budget=20_000_000, intent=PARA_EL_ONCE,
    )

finally:
    con_tope(None)

print(
    f"       apagado {apagado.get('bid'):,} "
    f"({100 * (apagado.get('bid') - PRECIO) / PRECIO:+.2f} %)  "
    f"encendido {encendido.get('bid'):,} "
    f"({100 * (encendido.get('bid') - PRECIO) / PRECIO:+.2f} %)"
)

check(
    "encender el tope BAJA la puja, no la sube",
    encendido.get("bid") < apagado.get("bid"),
    f"(apagado {apagado.get('bid')}, encendido {encendido.get('bid')})",
)

check(
    "y apagado se pasa del tope nuevo: por eso hacia falta",
    apagado.get("bid") > techo_once,
    f"(apagado {apagado.get('bid')}, techo {techo_once})",
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
