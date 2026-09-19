"""
Ningun peldano reparte por construccion.

LA SOSPECHA, Y ERA BUENA

    La curva del 19/09 salia con cuatro peldanos seguidos de peso
    identico y `n` identico:

        +0,00 %   peso 0,1978   n = 18
        +0,52 %   peso 0,1978   n = 18
        +1,95 %   peso 0,1978   n = 18
        +3,07 %   peso 0,1978   n = 18

    Cuatro dieciochos exactos no parecen mercado. Y no lo son:
    son la REJILLA. Comprobado con aritmetica pura, sin tocar un
    solo dato — solo los cortes y N:

        N= 91  ->  [18, 18, 18, 18, 14, 4, 1]
        N= 94  ->  [18, 19, 19, 19, 14, 4, 1]
        N= 72  ->  [14, 14, 15, 14, 11, 3, 1]

    Los cortes son cuantiles FIJOS -0,05 · 0,20 · 0,40 · 0,60 ·
    0,80 · 0,95 · 0,995- y el recuento de cada banda es la
    distancia entre sus indices. Con N=91 esa distancia vale
    18, 18, 18, 18 para los cuatro primeros. Punto.

Y AUN ASI NO ES EL FALLO DEL 16/09. SON DISTINTOS

    Entonces cada peldano llevaba `1/7` = 0,1429 SIN MIRAR la
    rejilla, asi que el ultimo —que cubre el 0,5 % de arriba— se
    llevaba la misma masa que el primero. Estaba diez veces
    sobrevalorado.

    Ahora los pesos siguen la rejilla de verdad: 0,15 · 0,20 ·
    0,20 · 0,20 · 0,15 · 0,045 · 0,005. Que los cuatro de en
    medio coincidan no es un reparto inventado: es lo que hace un
    resumen por cuantiles.

    DONDE VIVE LA INFORMACION, ENTONCES: en los FACTORES, no en
    los pesos. El peso dice cuanta masa hay en cada banda —y eso
    lo fija la rejilla—; el factor dice DONDE cae esa banda, y
    eso lo fijan las pujas.

QUE COMPRUEBA ESTA GUARDIA

    1. Con una muestra deliberadamente sesgada, los pesos NO
       salen iguales: el reparto responde a los datos.
    2. Con una muestra suave, los pesos reproducen la rejilla —y
       eso es correcto, no un fallo.
    3. Los FACTORES si se mueven con los datos, que es donde esta
       la informacion.
    4. Y no se ha vuelto a 1/7: el ultimo peldano no puede pesar
       lo mismo que el primero.

LA GUARDIA MUERDE CON LA MUESTRA VACIA

    Sin pujas no hay curva que calibrar y todo pasaria por
    vacuidad. Por eso lo primero es exigir que las dos muestras
    traigan bastante para calibrar.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El `price_lookup` es una funcion de
    este fichero: no se lee `data/`, no se sale a la red y no se
    mira el reloj.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.rival_bid_model import (  # noqa: E402
    CORTES_DE_LA_CURVA,
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


PRECIO = 1_000_000


def precio_de_entonces(player_id, cuando):
    return PRECIO


def curva_de(primas):
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
# LAS DOS MUESTRAS
# ================================================================

# SUAVE: primas repartidas sin amontonarse en ningun valor.
SUAVE = [1.0 + i * 0.0009 for i in range(94)]

# SESGADA: casi todo pegado al precio de salida y una cola corta.
# Es la forma que tendria un mercado donde nadie sube la puja.
SESGADA = [1.0] * 70 + [1.0004] * 10 + [1.35 + i * 0.01 for i in range(14)]


# ================================================================
# 0. LAS DOS MUESTRAS TRAEN BASTANTE
# ================================================================

print()
print("0. Las dos muestras traen para calibrar")

check(
    "la suave trae bastante",
    len(SUAVE) >= MIN_PREMIUM_SAMPLES,
    f"({len(SUAVE)})",
)

check(
    "la sesgada tambien",
    len(SESGADA) >= MIN_PREMIUM_SAMPLES,
    f"({len(SESGADA)})",
)

check(
    "y tienen el mismo tamano, para que solo cambie la FORMA",
    len(SUAVE) == len(SESGADA),
    f"({len(SUAVE)} vs {len(SESGADA)})",
)

suave = curva_de(SUAVE)

sesgada = curva_de(SESGADA)

check(
    "las dos se calibran",
    suave["calibrated"] and sesgada["calibrated"],
)


# ================================================================
# 1. CON UNA MUESTRA SESGADA, LOS PESOS NO SALEN IGUALES
# ================================================================

print()
print("1. Con la muestra sesgada los pesos NO son iguales")

pesos_sesgada = [round(p, 4) for _f, p in sesgada["curve"]]

print(f"       {pesos_sesgada}")

check(
    "no todos los pesos valen lo mismo",
    len(set(pesos_sesgada)) > 1,
    f"({pesos_sesgada})",
)

check(
    "hay al menos un peldano que se lleva mucha mas masa",
    max(pesos_sesgada) >= 2 * sorted(pesos_sesgada)[-2],
    f"({sorted(pesos_sesgada, reverse=True)[:3]})",
)

check(
    "y al menos uno vacio, porque el sesgo deja bandas sin nada",
    any(p == 0 for p in pesos_sesgada),
    f"({pesos_sesgada})",
)


# ================================================================
# 2. CON LA SUAVE, LOS PESOS SON LA REJILLA — Y ESTA BIEN
# ================================================================

print()
print("2. Con la suave, los pesos reproducen la rejilla")

pesos_suave = [round(p, 4) for _f, p in suave["curve"]]

print(f"       {pesos_suave}")

# Lo que dice la rejilla, SIN mirar los datos.
N = len(SUAVE)

indices = [
    min(int(c * N), N - 1) for c in CORTES_DE_LA_CURVA
]

por_rejilla = []

for k in range(len(indices)):
    ini = 0 if k == 0 else indices[k]
    fin = indices[k + 1] if k + 1 < len(indices) else N
    por_rejilla.append(fin - ini)

print(f"       rejilla: {por_rejilla}")

check(
    "el peso del primero es el que predice la rejilla",
    abs(pesos_suave[0] - por_rejilla[0] / N) < 0.02,
    f"({pesos_suave[0]} contra {por_rejilla[0] / N:.4f})",
)

check(
    "los cuatro de en medio se parecen entre si",
    max(pesos_suave[1:4]) - min(pesos_suave[1:4]) < 0.02,
    f"({pesos_suave[1:4]})",
)

check(
    "y eso NO lo decide el dato: la rejilla ya lo predecia",
    max(por_rejilla[1:4]) - min(por_rejilla[1:4]) <= 1,
    f"({por_rejilla[1:4]})",
)


# ================================================================
# 3. LOS FACTORES SI SE MUEVEN CON LOS DATOS
# ================================================================

print()
print("3. Donde vive la informacion: en los factores")

factores_suave = [f for f, _p in suave["curve"]]

factores_sesgada = [f for f, _p in sesgada["curve"]]

print(f"       suave  : {[round(f, 4) for f in factores_suave]}")
print(f"       sesgada: {[round(f, 4) for f in factores_sesgada]}")

check(
    "las dos curvas tienen factores distintos",
    factores_suave != factores_sesgada,
)

check(
    "la sesgada amontona sus primeros factores abajo",
    factores_sesgada[3] < factores_suave[3],
    f"({factores_sesgada[3]} contra {factores_suave[3]})",
)


# ================================================================
# 4. NO SE HA VUELTO A 1/7
# ================================================================

print()
print("4. El ultimo peldano no pesa como el primero")

UN_SEPTIMO = round(1 / 7, 4)

check(
    "el ultimo no vale 1/7",
    pesos_suave[-1] != UN_SEPTIMO,
    f"({pesos_suave[-1]} contra {UN_SEPTIMO})",
)

check(
    "y pesa MENOS que el primero: cubre menos cuantil",
    pesos_suave[-1] < pesos_suave[0],
    f"({pesos_suave[-1]} contra {pesos_suave[0]})",
)

check(
    "ningun peso es negativo",
    all(p >= 0 for p in pesos_suave + pesos_sesgada),
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
