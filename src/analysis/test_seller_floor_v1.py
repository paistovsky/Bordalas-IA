"""
Lo que pide el vendedor no es lo que vale el jugador.

EL CASO REAL

    16/08/2026. Pepe pujo 480.000 EUR por Iker Munoz.
    Pollo17 lo tenia publicado a 1.370.000 EUR.

    Biwenger acepto la puja -HTTP 200- y aparecio como puja viva
    en la app. Pero no puede ganar jamas: esta un 185 % por
    debajo de lo que pide el dueno. Y mientras vive descuenta
    480.000 EUR de la puja maxima.

    El fallo estaba en el executor: tenia la venta fresca
    delante y cogia el precio del CATALOGO en vez del PEDIDO.

    En las ventas del Computer los dos coinciden, por eso paso
    desapercibido. Ese dia habia 20 ventas del Computer y 32 de
    rivales, con primas del -2 % al +185 %.
"""

import sys

sys.path.insert(0, ".")

fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


def efectivo(catalogo, pedido):
    """
    La regla, aislada: cuesta lo que pide quien lo tiene.
    """
    return max(int(catalogo or 0), int(pedido or 0))


print()
print("1. El caso de Iker Muñoz")
print("-" * 60)

check(
    "el precio efectivo es el que pide Pollo17",
    efectivo(480_000, 1_370_000) == 1_370_000,
)

check(
    "pujar el valor de catalogo seria tirar la puja",
    efectivo(480_000, 1_370_000) > 480_000,
)

check(
    "en una venta del Computer no cambia nada",
    efectivo(360_000, 360_000) == 360_000,
)

check(
    "un vendedor que pide menos que el valor no baja el precio",
    efectivo(5_030_000, 5_000_000) == 5_030_000,
)


print()
print("2. El tablero no propone lo que no se puede ganar")
print("-" * 60)

# Se reproduce el filtro del board sin arrancar todo el motor:
# un candidato cuyo dueno pide mas de lo que vale no entra.
VENTAS = [
    {"player": {"id": 1}, "price": 1_370_000, "user": {"name": "Pollo17"}},
    {"player": {"id": 2}, "price": 360_000, "user": None},
    {"player": {"id": 3}, "price": 5_000_000, "user": {"name": "Pollo17"}},
]

CATALOGO = {1: 480_000, 2: 360_000, 3: 5_030_000}

pedidos = {
    int(v["player"]["id"]): int(v["price"])
    for v in VENTAS
}

aceptados = []
rechazados = []

for pid, catalogo in CATALOGO.items():
    pedido = pedidos.get(pid, 0)
    if pedido > catalogo:
        rechazados.append(pid)
    else:
        aceptados.append(pid)

check(
    "Iker Muñoz (piden +185 %) queda fuera",
    1 in rechazados,
    f"rechazados={rechazados}",
)

check(
    "el del Computer entra",
    2 in aceptados,
)

check(
    "el que se vende por debajo de su valor entra",
    3 in aceptados,
)


print()
print("3. El motor real expone los rechazos")
print("-" * 60)

# No se arranca build_speculation_board -necesita red-, pero si
# se comprueba que la clave existe en el contrato publico.
import inspect  # noqa: E402

from src.analysis import speculation_engine  # noqa: E402

fuente = inspect.getsource(speculation_engine.build_speculation_board)

check(
    "el board calcula el precio pedido",
    "asking_price" in fuente,
)

check(
    "y publica los rechazados por suelo del vendedor",
    "rejected_by_seller_floor" in fuente,
)

from src.actions import autopilot_executor  # noqa: E402

fuente_exec = inspect.getsource(autopilot_executor)

check(
    "el executor usa el precio de la venta, no el del catalogo",
    "listed_price" in fuente_exec
    and "SPECULATION_ABOVE_SELLER_FLOOR" in fuente_exec,
)


print()
print("=" * 60)

if fallos:
    print(f"FALLOS: {len(fallos)}")
    for nombre in fallos:
        print(f"  - {nombre}")
    sys.exit(1)

print("TODO OK")
print("=" * 60)
