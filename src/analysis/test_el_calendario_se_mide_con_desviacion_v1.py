"""
El calendario se mide en desviacion sobre la media propia, no en
puntos brutos.

POR QUE (26/09/2026)

    "Los de equipos de arriba, y en casa, puntuan mas" puede ser
    verdad y puede ser solo que los buenos juegan mas en casa, o que
    los buenos estan en equipos que ganan. En puntos brutos las dos
    cosas dan el mismo numero. Restando a cada partido la media de su
    jugador, lo que queda es lo que el contexto le añade A EL.

    Medido el 26/09 sobre 1.819 partidos reconstruidos: en casa
    +0,22 en desviacion; en bruto la diferencia casa-fuera parece el
    doble de lo que es para algunas posiciones.

QUE COMPRUEBA

    0. El caso muerde: en BRUTO da un efecto de casa grande. Si no lo
       diera, un calculo en bruto tambien saldria "cero" y esto no
       distinguiria nada.
    1. En desviacion, ese mismo caso da CERO: un bueno que juega mas
       en casa no fabrica efecto de casa por si solo.
    2. Y un efecto de casa de verdad -el mismo jugador puntua mas en
       casa- SI se ve, con su tamaño exacto.
    3. Cada numero sale con su `n`.
    4. El once: exactamente las siete formaciones de `lineup_engine`,
       y el mejor por valor.
    5. El plan: no vende a perdida, ni con coste desconocido, ni a
       quien no se vende, ni compra sin ficha o sin caja.
    6. Nada lanza con basura.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. Ni `data/`, ni red, ni reloj, ni entorno.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.el_once_objetivo import (  # noqa: E402
    desviacion_por_contexto,
    el_mejor_once,
    el_plan,
    encoger,
    estimar_k,
)
from src.analysis.lineup_engine import FORMATIONS  # noqa: E402


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def partido(jugador, puntos, casa, rival_alto=None, posicion=4):
    return {
        "jugador": jugador,
        "posicion": posicion,
        "puntos": puntos,
        "casa": casa,
        "rival_alto": rival_alto,
    }


# ================================================================
# EL CASO: un bueno que juega mas en casa, un malo que juega mas fuera
# ================================================================
#
#     El bueno puntua 10 SIEMPRE, 3 veces en casa y 1 fuera.
#     El malo puntua 2 SIEMPRE, 1 vez en casa y 3 fuera.
#     Ninguno de los dos puntua mas en casa que fuera.

SIN_EFECTO = (
    [partido("bueno", 10, True) for _ in range(3)]
    + [partido("bueno", 10, False)]
    + [partido("malo", 2, True)]
    + [partido("malo", 2, False) for _ in range(3)]
)

r = desviacion_por_contexto(SIN_EFECTO)
todas = r.get("todas") or {}

print()
print("0. El caso muerde: en bruto parece que en casa se puntua mas")

bruto_casa = todas["casa"]["bruto"]["media"]
bruto_fuera = todas["fuera"]["bruto"]["media"]

check(
    "en bruto, casa 8 y fuera 4",
    bruto_casa == 8.0 and bruto_fuera == 4.0,
    f"(casa {bruto_casa}, fuera {bruto_fuera})",
)

print()
print("1. En desviacion, ese caso da cero")

check(
    "desviacion en casa = 0",
    todas["casa"]["desviacion"]["media"] == 0.0,
    f"({todas['casa']['desviacion']})",
)
check(
    "desviacion fuera = 0",
    todas["fuera"]["desviacion"]["media"] == 0.0,
    f"({todas['fuera']['desviacion']})",
)
check(
    "y la guardia distingue: bruto y desviacion NO dan lo mismo",
    (bruto_casa - bruto_fuera)
    != (todas["casa"]["desviacion"]["media"] - todas["fuera"]["desviacion"]["media"]),
)

print()
print("2. Un efecto de casa de verdad si se ve, con su tamaño")

CON_EFECTO = (
    [partido("uno", 6, True) for _ in range(2)]
    + [partido("uno", 2, False) for _ in range(2)]
)
r2 = desviacion_por_contexto(CON_EFECTO)["todas"]

check(
    "el mismo jugador: +2 en casa, -2 fuera",
    r2["casa"]["desviacion"]["media"] == 2.0
    and r2["fuera"]["desviacion"]["media"] == -2.0,
    f"({r2['casa']['desviacion']}, {r2['fuera']['desviacion']})",
)

con_media = desviacion_por_contexto(CON_EFECTO, medias={"uno": 3.0})["todas"]
check(
    "con la media de la temporada dada, se resta esa",
    con_media["casa"]["desviacion"]["media"] == 3.0,
    f"({con_media['casa']['desviacion']})",
)

print()
print("3. Cada numero con su n, y por posicion")

check(
    "n en casa = 4 partidos, de 2 jugadores",
    todas["casa"]["desviacion"]["n"] == 4 and todas["casa"]["jugadores"] == 2,
    f"({todas['casa']})",
)
check(
    "sale un cuadro por posicion",
    "4" in r and r["4"]["casa"]["desviacion"]["n"] == 4,
    f"({list(r)})",
)
check(
    "partidos sin rival conocido no cuentan como rival bajo",
    todas["rival_bajo"]["desviacion"]["n"] == 0,
    f"({todas['rival_bajo']})",
)


# ================================================================
# 4. EL ONCE
# ================================================================

print()
print("4. El once: las siete formaciones, y el mejor")

formas = {
    tuple(sorted(f.items())) for f in FORMATIONS.values()
}
permitidas = {
    ((1, 1), (2, d), (3, m), (4, a))
    for d in (3, 4, 5) for m in (3, 4, 5) for a in (1, 2, 3)
    if d + m + a == 10
}
check(
    "las de lineup_engine son exactamente 1 POR, 3-5 DEF, 3-5 MED, 1-3 DEL",
    formas == permitidas,
    f"({sorted(formas)})",
)

PLANTILLA = (
    [{"id": "p1", "posicion": 1, "valor": 5, "precio": 1}]
    + [{"id": f"d{i}", "posicion": 2, "valor": 3, "precio": 1} for i in range(5)]
    + [{"id": f"m{i}", "posicion": 3, "valor": 4, "precio": 1} for i in range(5)]
    + [{"id": f"a{i}", "posicion": 4, "valor": v, "precio": 1}
       for i, v in enumerate([9, 8, 7])]
)
once = el_mejor_once(PLANTILLA)
check(
    "con tres delanteros buenos, 3-4-3",
    once["formacion"] == "3-4-3" and once["lleno"],
    f"({once})",
)
check(
    "y la suma es la de esos once",
    once["suma"] == 5 + 3 * 3 + 4 * 4 + 9 + 8 + 7,
    f"({once['suma']})",
)
check(
    "sin portero no hay once",
    el_mejor_once([j for j in PLANTILLA if j["posicion"] != 1])["lleno"] is False,
)


# ================================================================
# 5. EL PLAN
# ================================================================

print()
print("5. El plan respeta caja, fichas, perdidas y protegidos")

MERCADO = [{"id": "nuevo", "posicion": 4, "valor": 20, "precio": 1_000}]

sin_ficha = el_plan(PLANTILLA, MERCADO, {}, caja=10_000, fichas=0)
check("sin ficha y sin ofertas, no compra", sin_ficha["pasos"] == [], f"({sin_ficha})")

sin_caja = el_plan(PLANTILLA, MERCADO, {}, caja=999, fichas=1)
check("sin caja, no compra", sin_caja["pasos"] == [], f"({sin_caja})")

compra = el_plan(PLANTILLA, MERCADO, {}, caja=1_000, fichas=1)
check(
    "con caja y ficha, compra y cuenta una escritura",
    len(compra["pasos"]) == 1 and compra["escrituras"] == 1
    and compra["caja_final"] == 0,
    f"({compra})",
)

# Sin ficha: tiene que vender a un delantero que salga del once.
a_perdida = el_plan(PLANTILLA, MERCADO, {"a2": {"importe": 500, "coste": 900}},
                    caja=1_000, fichas=0)
check("no vende a perdida", a_perdida["pasos"] == [], f"({a_perdida})")

sin_coste = el_plan(PLANTILLA, MERCADO, {"a2": {"importe": 500, "coste": None}},
                    caja=1_000, fichas=0)
check("con coste desconocido no vende", sin_coste["pasos"] == [], f"({sin_coste})")

protegido = el_plan(PLANTILLA, MERCADO, {"a2": {"importe": 500, "coste": 100}},
                    caja=1_000, fichas=0, no_se_vende={"a2"})
check("a quien no se vende, no se vende", protegido["pasos"] == [], f"({protegido})")

bien = el_plan(PLANTILLA, MERCADO, {"a2": {"importe": 500, "coste": 100}},
               caja=600, fichas=0)
check(
    "con oferta sin perdida: vende, compra, y son dos escrituras",
    len(bien["pasos"]) == 1 and bien["pasos"][0]["vende"] == "a2"
    and bien["escrituras"] == 2 and bien["caja_final"] == 100,
    f"({bien})",
)


# ================================================================
# 6. ENCOGER, K, Y BASURA
# ================================================================

print()
print("6. Encoger, k, y nada lanza")

check("encoger: sin partidos, la media", encoger(0, 0, 4.0, 5) == 4.0)
check("encoger: (10 + 2*4) / (2 + 2) = 4.5", encoger(10, 2, 4.0, 2) == 4.5)
check("estimar_k con pocos datos dice que no sabe", estimar_k([{"ppg": 1, "jugados": 1}], 4.0) is None)

try:
    basura = [
        desviacion_por_contexto(None),
        desviacion_por_contexto([{"puntos": "x"}, None, 3]),
        el_mejor_once(None),
        el_mejor_once([{"posicion": "x"}]),
        el_plan(None, None, None, None, None),
        estimar_k(None, None),
    ]
    check("nunca lanza", all(isinstance(b, (dict, type(None))) for b in basura), f"({basura})")
except Exception as error:                          # noqa: BLE001
    check("nunca lanza", False, f"({type(error).__name__}: {error})")


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
