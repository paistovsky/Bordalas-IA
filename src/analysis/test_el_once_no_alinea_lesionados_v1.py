"""
El once no alinea lesionados.

EL CASO (26/09/2026)

    Aubameyang, `injured` en el panel de las 08:10, 69 puntos en 7
    partidos, entraba en el once B del once objetivo. Un once ideal
    con un lesionado dentro no es un once ideal.

QUE COMPRUEBA

    0. El caso muerde: hay un lesionado que, por puntos, entraria en
       el once. Si no lo hubiera, "no entra" pasaria por vacuidad.
    1. Con el filtro, ni el lesionado, ni el sancionado, ni el
       descartado, ni el de estado desconocido entran en ningun once.
    2. El `doubt` y el `warned` SI entran en el de la temporada.
    3. Sin el filtro, el lesionado entraria: lo que lo saca es el
       filtro, no el caso.
    4. El plan no compra a un lesionado, aunque sea lo que mas sube.
    5. El 24 % del `doubt` queda mas cerca del lesionado que del sano.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. Ni `data/`, ni red, ni reloj, ni entorno.
"""

import sys

sys.path.insert(0, ".")

from src.analysis.el_once_objetivo import (  # noqa: E402
    FUERA,
    JUEGA_SI_DUDA,
    disponible,
    el_mejor_once,
    el_plan,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def j(i, pos, valor, status="ok", precio=1):
    return {"id": i, "posicion": pos, "valor": valor, "status": status, "precio": precio}


# Un once de 3-4-3 justo, y fuera de el, los que tienen estado.
BASE = (
    [j("p1", 1, 5)]
    + [j(f"d{k}", 2, 3) for k in range(3)]
    + [j(f"m{k}", 3, 4) for k in range(4)]
    + [j(f"a{k}", 4, 2) for k in range(3)]
    + [j("p2", 1, 1), j("d9", 2, 1), j("m9", 3, 1), j("a9", 4, 1)]
)

CON_ESTADO = [
    j("lesionado", 4, 50, "injured"),
    j("sancionado", 3, 40, "sanctioned"),
    j("descartado", 2, 30, "discarded"),
    j("desconocido", 1, 20, "unknown"),
    j("en_duda", 4, 9, "doubt"),
    j("apercibido", 3, 9, "warned"),
]

TODOS = BASE + CON_ESTADO
ESTADO = {x["id"]: x["status"] for x in TODOS}


print()
print("0. El caso muerde")

sin_filtro = el_mejor_once(TODOS, fuera=frozenset())
check(
    "sin filtro, el lesionado entraria por puntos",
    "lesionado" in sin_filtro["ids"],
    f"({sin_filtro['ids']})",
)
check(
    "y es el que mas puntua de todos",
    max(TODOS, key=lambda x: x["valor"])["id"] == "lesionado",
)

print()
print("1. Con el filtro, nadie de FUERA entra")

con_filtro = el_mejor_once(TODOS)
dentro = {ESTADO[i] for i in con_filtro["ids"]}

check("el once sigue lleno", con_filtro["lleno"], f"({con_filtro})")
for estado in ("injured", "sanctioned", "discarded", "unknown"):
    check(f"ningun `{estado}` en el once", estado not in dentro, f"({con_filtro['ids']})")
check(
    "FUERA son exactamente esos cuatro",
    FUERA == frozenset({"injured", "sanctioned", "discarded", "unknown"}),
    f"({sorted(FUERA)})",
)

print()
print("2. El doubt y el warned si entran en el de la temporada")

check("el `doubt` entra", "en_duda" in con_filtro["ids"], f"({con_filtro['ids']})")
check("el `warned` entra", "apercibido" in con_filtro["ids"], f"({con_filtro['ids']})")
check(
    "sin estado cuenta como disponible",
    disponible({"id": 1}) is True and disponible({"status": "injured"}) is False,
)

print()
print("3. Lo que lo saca es el filtro")

check(
    "con filtro y sin filtro, onces distintos",
    set(sin_filtro["ids"]) != set(con_filtro["ids"]),
)

print()
print("4. El plan no compra lesionados")

plan = el_plan(
    BASE,
    [j("lesionado", 4, 50, "injured", precio=100), j("sano", 4, 3, precio=100)],
    {},
    caja=1_000,
    fichas=2,
)
compras = [p["compra"] for p in plan["pasos"]]
check("no compra al lesionado", "lesionado" not in compras, f"({compras})")
check("y si al sano, que tambien sube el once", "sano" in compras, f"({compras})")

print()
print("5. El doubt, medido")

check(
    "juega el 24 %: mas cerca del lesionado (3 %) que del sano (69 %)",
    abs(JUEGA_SI_DUDA - 0.03) < abs(JUEGA_SI_DUDA - 0.69),
    f"({JUEGA_SI_DUDA})",
)

try:
    basura = [el_mejor_once([{"status": None, "posicion": 1, "valor": 1}]), disponible(None)]
    check("nunca lanza", True, f"({basura})")
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
