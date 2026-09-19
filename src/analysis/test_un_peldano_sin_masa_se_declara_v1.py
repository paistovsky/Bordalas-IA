"""
Un peldano sin masa se declara, y no publica una probabilidad.

DOS COSAS DISTINTAS QUE PARECIAN LA MISMA

    n = 0   El peldano esta VACIO. No cayo ni una puja ahi.
    n >= 1  El peldano es FLOJO. Cayeron pocas y el intervalo es
            ancho, pero existen.

    Con la segunda, borrar el peso seria afirmar algo MAS fuerte
    que el dato: diria "ningun rival paga tanto" cuando alguno
    pago. El codigo ya decidia bien ahi —peso observado, marcado
    como flojo— y eso NO se toca.

    Con la primera no hay nada que observar, y sin embargo el
    peldano llevaba peso. Y no uno cualquiera.

EL RESIDUO DEL REDONDEO, HACIENDOSE PASAR POR MEDIDA

    El ultimo peldano absorbia la diferencia para que la curva
    sumase exactamente uno:

        peso = round(1.0 - acumulado, 4)

    Si los seis de arriba redondean hacia arriba, eso sale
    NEGATIVO. Medido en la foto del 18/09 16:16:38, el peldano
    1.2449x publicaba **-0.0001** con n=0.

    Una probabilidad negativa no es un detalle de coma: en
    `win_probability` RESTA de la probabilidad de que un rival
    nos supere, asi que Pepe se cree mas ganador de lo que es y
    puja menos. El sesgo va en la direccion cara.

    Y aun siendo positivo, con n=0 ese numero no es masa
    observada de nada: es el sobrante del redondeo colocado
    donde no cayo ninguna puja.

QUE COMPRUEBA ESTA GUARDIA

    1. Un peldano con n=0 sale con peso CERO.
    2. Y marcado `calibrated: False`.
    3. Ningun peso de la curva es negativo, pase lo que pase con
       el redondeo.
    4. Un peldano FLOJO (1 <= n < minimo) SI conserva su peso
       observado: no se borra lo que se vio.
    5. El aviso dice cuantos peldanos van flojos y con que
       minimo.

LA GUARDIA MUERDE SI TODOS LOS PELDANOS TIENEN MASA

    Si el banco no produce ningun peldano vacio ni flojo, las
    comprobaciones pasarian por vacuidad. Por eso lo primero es
    exigir que haya al menos uno de cada.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El `price_lookup` es una funcion de
    este fichero: no se lee `data/`, no se sale a la red y no se
    mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.rival_bid_model import (  # noqa: E402
    MIN_SAMPLES_PER_RUNG,
    build_bid_model,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


PRECIO = 1_000_000


def precio_de_entonces(player_id, cuando):
    return PRECIO


def modelo_de(primas):
    managers = [{
        "user_id": 1,
        "name": "R1",
        "capacity": 20_000_000,
        "lost_bid_history": [
            {
                "amount": int(round(PRECIO * p)),
                "player_id": 100 + i,
                "date": 1_789_000_000 + i,
            }
            for i, p in enumerate(primas)
        ],
    }]

    return build_bid_model(
        {"managers": managers},
        price_lookup=precio_de_entonces,
    )["premium"]


# ================================================================
# EL BANCO
# ================================================================
#
#     Casi toda la masa amontonada abajo y UNA sola puja muy
#     alta. Con los cortes en cuantiles, eso deja el peldano de
#     arriba vacio (los dos ultimos cortes caen en el mismo
#     factor) y alguno flojo.
PRIMAS = [1.000] * 20 + [1.004] * 18 + [1.010] * 14 + [1.900]

pr = modelo_de(PRIMAS)

peldanos = pr.get("rungs") or pr.get("peldanos") or []


# ================================================================
# 0. HAY PELDANOS SIN MASA Y PELDANOS FLOJOS
# ================================================================

print()
print("0. El banco produce peldanos vacios y flojos")

print(f"       calibrada={pr['calibrated']} samples={pr['samples']}")

for p in peldanos:
    print(
        f"       {p['factor']:.4f}  n={p['n']:<3d} "
        f"peso={p['weight']:<8} calibrado={p['calibrated']}"
    )

vacios = [p for p in peldanos if p["n"] == 0]

flojos = [
    p for p in peldanos
    if 1 <= p["n"] < MIN_SAMPLES_PER_RUNG
]

check(
    "hay al menos un peldano vacio",
    len(vacios) >= 1,
    f"(n={len(vacios)})",
)

check(
    "hay al menos un peldano flojo",
    len(flojos) >= 1,
    f"(n={len(flojos)})",
)

check(
    "y el minimo por peldano esta declarado",
    MIN_SAMPLES_PER_RUNG >= 1,
    f"({MIN_SAMPLES_PER_RUNG})",
)


# ================================================================
# 1. EL VACIO NO PUBLICA PROBABILIDAD
# ================================================================

print()
print("1. Un peldano sin masa pesa cero")

check(
    "todos los peldanos vacios pesan cero",
    all(p["weight"] == 0 for p in vacios),
    f"({[(p['factor'], p['weight']) for p in vacios]})",
)

check(
    "y salen marcados sin calibrar",
    all(p["calibrated"] is False for p in vacios),
    f"({[(p['factor'], p['calibrated']) for p in vacios]})",
)


# ================================================================
# 2. NINGUN PESO NEGATIVO
# ================================================================

print()
print("2. Ninguna probabilidad negativa")

pesos = [p for _f, p in pr["curve"]]

check(
    "ningun peso de la curva es negativo",
    all(p >= 0 for p in pesos),
    f"({[p for p in pesos if p < 0]})",
)

check(
    "ningun peso de los peldanos es negativo",
    all(p["weight"] >= 0 for p in peldanos),
)

check(
    "y la curva sigue sumando aproximadamente uno",
    abs(sum(pesos) - 1.0) <= 0.001,
    f"(suma {sum(pesos):.4f})",
)


# ================================================================
# 3. EL FLOJO CONSERVA LO QUE SE VIO
# ================================================================

print()
print("3. Un peldano flojo NO se borra")

check(
    "los flojos conservan peso mayor que cero",
    all(p["weight"] > 0 for p in flojos),
    f"({[(p['factor'], p['n'], p['weight']) for p in flojos]})",
)

check(
    "pero salen marcados sin calibrar",
    all(p["calibrated"] is False for p in flojos),
)

check(
    "y los que si llegan al minimo salen calibrados",
    all(
        p["calibrated"] is True
        for p in peldanos
        if p["n"] >= MIN_SAMPLES_PER_RUNG
    ),
)


# ================================================================
# 4. EL AVISO LO DICE
# ================================================================

print()
print("4. El aviso dice cuantos y con que minimo")

print(f"       {(pr.get('reason') or '')[:150]}")

check(
    "el motivo avisa de los peldanos flojos",
    "AVISO" in (pr.get("reason") or ""),
    f"({pr.get('reason')})",
)

check(
    "y nombra el minimo por peldano",
    str(MIN_SAMPLES_PER_RUNG) in (pr.get("reason") or ""),
    f"({pr.get('reason')})",
)

check(
    "y la curva entera se declara no del todo calibrada",
    pr.get("fully_calibrated") is False,
    f"({pr.get('fully_calibrated')})",
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
