"""
La curva de primas usa lo observado, y lo dice cuando no puede.

LO QUE SE CREYO EL 19/09 POR LA MANANA, Y ERA FALSO

    Se publico que la curva iba "161 subastas observadas, 0
    usadas". Era un artefacto de la MEDICION, no del sistema:
    `build_bid_model` se llamo sin `price_lookup`, y sin el, el
    bucle que recorre las pujas NO SE EJECUTA:

        if price_lookup is not None:
            for manager in (managers or []):
                ...

    Cero muestras Y cero descartadas a la vez es la firma de eso:
    si de verdad se estuvieran tirando pujas, `discarded_no_price`
    seria mayor que cero.

    En produccion `acquisition_board` SI lo pasa
    (`price_lookup=build_historical_price_lookup()`), y la foto
    del 18/09 16:16:38 lo confirma: `calibrated: True`,
    `samples: 83`.

    Es la doctrina 89 mordiendo a quien la escribio: cuando el
    dato dice que paso algo absurdo, comprueba si paso.

POR ESO ESTA GUARDIA EXISTE

    El modo "sin calibrar" es legitimo y tiene que seguir
    existiendo — con pocas pujas, la curva por defecto es mejor
    que una medida de ruido. Lo que no puede pasar es que se
    entre en ese modo POR NO PASAR UN PARAMETRO y que desde
    fuera se lea igual que "no hay datos".

    Asi que: con pujas medibles en el banco, `samples` no es
    cero. Y cuando se entra en el modo por defecto, el motivo
    tiene que permitir distinguir POR QUE (doctrina 87).

QUE COMPRUEBA ESTA GUARDIA

    1. Con pujas observables y precio de aquel momento, la curva
       se calibra y `samples` no es cero.
    2. Los peldanos salen de la MASA observada, no de 1/7.
    3. Sin `price_lookup` se cae al modo por defecto, y se
       distingue de "habia pujas y no valian": cero muestras con
       cero descartadas.
    4. Ningun peso es negativo, y la curva suma ~1.
    5. Con menos de `MIN_PREMIUM_SAMPLES` se usa la curva por
       defecto y se dice.

LA GUARDIA MUERDE CON EL LIBRO VACIO

    Sin managers no hay pujas que medir y todo pasaria por
    vacuidad. Por eso lo primero es exigir que el banco traiga
    pujas observables.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El `price_lookup` es una funcion de
    este fichero que devuelve un precio fijo por jugador: no se
    lee `data/`, no se sale a la red y no se mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.rival_bid_model import (  # noqa: E402
    DEFAULT_PREMIUM_CURVE,
    MIN_PREMIUM_SAMPLES,
    build_bid_model,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO: PUJAS CON SU PRECIO DE AQUEL MOMENTO
# ================================================================

PRECIO = 1_000_000


def precio_de_entonces(player_id, cuando):
    """Todos valian lo mismo. Fijo, escrito aqui."""

    return PRECIO


# Primas repartidas a proposito por toda la banda, con mas masa
# abajo -que es lo que pasa de verdad: el 41,8 % de las 91 pujas
# medibles del 19/09 caen entre +0 % y +2 %-.
PRIMAS = (
    [1.000] * 10
    + [1.005] * 8
    + [1.012] * 6
    + [1.018] * 6
    + [1.025] * 8
    + [1.040] * 7
    + [1.070] * 5
    + [1.150] * 4
)


def _manager(uid, primas):
    return {
        "user_id": uid,
        "name": f"R{uid}",
        "capacity": 20_000_000,
        "lost_bid_history": [
            {
                "amount": int(round(PRECIO * p)),
                "player_id": 100 + i,
                "date": 1_789_000_000 + i,
            }
            for i, p in enumerate(primas)
        ],
    }


MANAGERS = [_manager(1, PRIMAS)]

INFORME = {"managers": MANAGERS}


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. El libro de pujas observadas no llega vacio")

check(
    "hay pujas observables",
    len(PRIMAS) == 54,
    f"(n={len(PRIMAS)})",
)

check(
    "y son mas que el minimo para calibrar",
    len(PRIMAS) >= MIN_PREMIUM_SAMPLES,
    f"({len(PRIMAS)} contra {MIN_PREMIUM_SAMPLES})",
)

vacio = build_bid_model(
    {"managers": []}, price_lookup=precio_de_entonces
)

check(
    "sin managers no se calibra nada",
    vacio["premium"]["samples"] == 0
    and vacio["premium"]["calibrated"] is False,
    f"({vacio['premium']['samples']})",
)


# ================================================================
# 1. CON PRECIO DE ENTONCES, SE CALIBRA
# ================================================================

print()
print("1. Con pujas medibles, `samples` no es cero")

modelo = build_bid_model(
    INFORME, price_lookup=precio_de_entonces
)

pr = modelo["premium"]

print(f"       samples={pr['samples']} calibrated={pr['calibrated']}")

check(
    "el numero de usadas NO es cero",
    pr["samples"] > 0,
    f"(samples={pr['samples']})",
)

check(
    "usa todas las medibles",
    pr["samples"] == len(PRIMAS),
    f"({pr['samples']} de {len(PRIMAS)})",
)

check(
    "y queda marcada como calibrada",
    pr["calibrated"] is True,
)

check(
    "sin descartar ninguna por falta de precio",
    pr["discarded_no_price"] == 0,
    f"({pr['discarded_no_price']})",
)


# ================================================================
# 2. LOS PELDANOS SALEN DE LA MASA, NO DE 1/7
# ================================================================

print()
print("2. Los pesos salen de la masa observada")

pesos = [p for _f, p in pr["curve"]]

print(f"       {[round(p, 4) for p in pesos]}")

check(
    "no todos los pesos valen 1/7",
    len(set(round(p, 3) for p in pesos)) > 1,
    f"({pesos})",
)

check(
    "y la curva no es la de por defecto",
    [f for f, _ in pr["curve"]]
    != [f for f, _ in DEFAULT_PREMIUM_CURVE],
)


# ================================================================
# 3. SIN `price_lookup` SE DISTINGUE DEL "NO VALIAN"
# ================================================================

print()
print("3. Sin price_lookup, cero muestras Y cero descartadas")

ciego = build_bid_model(INFORME)

pc = ciego["premium"]

print(
    f"       samples={pc['samples']} "
    f"sin_precio={pc['discarded_no_price']} "
    f"imposibles={pc['discarded_impossible']}"
)

check(
    "cae al modo por defecto",
    pc["calibrated"] is False,
)

check(
    "con cero muestras",
    pc["samples"] == 0,
)

check(
    "Y CERO DESCARTADAS: es la firma de que ni se miraron",
    pc["discarded_no_price"] == 0
    and pc["discarded_impossible"] == 0,
    f"({pc['discarded_no_price']}, {pc['discarded_impossible']})",
)

# El contraste: con lookup que no sabe ningun precio, las pujas
# SI se miran y SI se descartan. Los dos casos se distinguen.
def no_sabe(player_id, cuando):
    return 0


sin_precios = build_bid_model(INFORME, price_lookup=no_sabe)

ps = sin_precios["premium"]

check(
    "y con lookup que no sabe, las descartadas SI se cuentan",
    ps["discarded_no_price"] == len(PRIMAS),
    f"({ps['discarded_no_price']})",
)

check(
    "asi que los dos modos por defecto no se confunden",
    pc["discarded_no_price"] != ps["discarded_no_price"],
)


# ================================================================
# 4. NINGUN PESO NEGATIVO
# ================================================================

print()
print("4. Ninguna probabilidad negativa")

check(
    "ningun peso es negativo",
    all(p >= 0 for p in pesos),
    f"({[p for p in pesos if p < 0]})",
)

check(
    "y la curva suma aproximadamente uno",
    abs(sum(pesos) - 1.0) <= 0.001,
    f"(suma {sum(pesos):.4f})",
)


# ================================================================
# 5. CON POCAS PUJAS, LA DE POR DEFECTO, Y SE DICE
# ================================================================

print()
print("5. Con pocas pujas se usa la de por defecto y se dice")

POCAS = {"managers": [_manager(2, [1.01] * 3)]}

flaco = build_bid_model(POCAS, price_lookup=precio_de_entonces)

pf = flaco["premium"]

check(
    "no se calibra con tres pujas",
    pf["calibrated"] is False,
    f"({pf['samples']})",
)

check(
    "y el motivo dice cuantas hacen falta",
    str(MIN_PREMIUM_SAMPLES) in (pf["reason"] or ""),
    f"({pf['reason']})",
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
