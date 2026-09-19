"""
Los cupos van por familia, y cada uno cuenta lo suyo.

POR QUE UNO POR FAMILIA Y NO UNO SOLO

    Demanda LEGITIMA por reset, ya sin repeticiones, medida sobre
    n=5 resets con actividad (10/09 -> 18/09):

        renovar    pico 9      cupo 12
        puja       pico 2      cupo  3
        publicar   pico 1      cupo  4

    Un cupo compartido dimensionado para la puja estrangula a
    renovar: el 10/09 a las 10:25 hubo NUEVE renovaciones
    legitimas de NUEVE jugadores distintos. Y dimensionado para
    renovar deja pujar nueve veces, que es otro riesgo entero.

    Las unidades no son comparables: renovar es mantenimiento y
    no compromete un euro; pujar si.

DOCTRINA 93: EL CUPO NO ES EL ARREGLO CONTRA LA REPETICION

    El cupo limita VOLUMEN. La repeticion es IDENTIDAD, y de eso
    se encarga `filtrar_los_repetidos`. Son dos piezas y hacen
    falta las dos.

    Se midio lo que pasa si se confunden: con el cupo viejo de 1
    contando envios se habrian frenado 37 de las 43 escrituras de
    la ventana, y diez de ellas eran renovaciones buenas.

LAS QUE NO LLEVAN NUMERO

    `vender`, `aceptar`, `reroll` y `alineacion` no tienen cupo,
    porque no hay ni una escritura suya medida: sus libros se
    crearon el 19/09. `cupo_de()` devuelve `None`, que NO es
    cero — es que no se ha medido (doctrina 24).

QUE COMPRUEBA ESTA GUARDIA

    1. El cupo de renovar NO lo consume una puja: cada familia
       lleva su contador.
    2. Agotar una familia deja a las otras intactas.
    3. Los tres numeros son los decididos.
    4. Las familias sin medir devuelven `None`, no cero.
    5. La fecha de revision esta escrita en el codigo y se puede
       preguntar sin mirar el reloj del sistema.

LA GUARDIA MUERDE SI LAS TRES COMPARTEN CONTADOR

    Es su caso principal: se llena `puja` hasta el tope y se
    exige que `renovar` siga entera.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. Los libros son ficheros temporales que
    crea y borra esta misma guardia. No se lee `data/`, no se
    sale a la red y no se mira el reloj: el `desde` y el `hoy`
    son marcas escritas a mano.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, ".")

from src.analysis.el_cupo_de_las_escrituras import (  # noqa: E402
    CUPOS_POR_FAMILIA,
    REVISION_DE_LOS_CUPOS,
    cupo_de,
    la_revision_del_cupo,
    puerta_del_cupo,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


RESET = datetime(
    2026, 9, 18, 7, 0, 0, tzinfo=timezone.utc
).timestamp()


def libro(carpeta, nombre, cuantas):
    """Un libro con `cuantas` escrituras enviadas tras el reset."""

    destino = Path(carpeta) / nombre

    destino.write_text(
        "\n".join(
            json.dumps({
                "at": f"2026-09-18T{8 + i:02d}:00:00+00:00",
                "player_id": 1000 + i,
                "sent": True,
                "http_status": 200,
                "success": True,
            })
            for i in range(cuantas)
        ),
        encoding="utf-8",
    )

    return destino


# ================================================================
# 0. LOS TRES NUMEROS SON LOS DECIDIDOS
# ================================================================

print()
print("0. Los cupos decididos")

print(f"       {CUPOS_POR_FAMILIA}")

check(
    "renovar va a 12",
    cupo_de("renovar") == 12,
    f"({cupo_de('renovar')})",
)

check(
    "puja va a 3",
    cupo_de("puja") == 3,
    f"({cupo_de('puja')})",
)

check(
    "publicar va a 4",
    cupo_de("publicar") == 4,
    f"({cupo_de('publicar')})",
)

check(
    "y cada uno cubre su pico medido con holgura",
    cupo_de("renovar") > 9
    and cupo_de("puja") > 2
    and cupo_de("publicar") > 1,
)


# ================================================================
# 1. LAS QUE NO SE HAN MEDIDO NO LLEVAN NUMERO
# ================================================================

print()
print("1. Sin medir no hay cupo, y `None` no es cero")

for familia in ("vender", "aceptar", "reroll", "alineacion"):
    check(
        f"«{familia}» no lleva cupo",
        cupo_de(familia) is None,
        f"({cupo_de(familia)})",
    )


# ================================================================
# 2. CADA FAMILIA, SU CONTADOR
# ================================================================

print()
print("2. El cupo de renovar no lo consume una puja")

with tempfile.TemporaryDirectory() as carpeta:

    # Se AGOTA la puja: tres escrituras contra un cupo de 3.
    pujas = libro(carpeta, "puja.jsonl", 3)

    # Y renovar no ha escrito ni una.
    renovaciones = libro(carpeta, "renovar.jsonl", 0)

    puerta_puja = puerta_del_cupo(
        "puja", cupo_de("puja"),
        desde_epoch=RESET, ruta=pujas,
    )

    puerta_renovar = puerta_del_cupo(
        "renovar", cupo_de("renovar"),
        desde_epoch=RESET, ruta=renovaciones,
    )

    print(f"       puja   : {puerta_puja['reason']}")
    print(f"       renovar: {puerta_renovar['reason']}")

    check(
        "la puja queda agotada",
        puerta_puja["puede"] is False
        and puerta_puja["llevadas"] == 3,
        f"({puerta_puja})",
    )

    check(
        "y renovar sigue con su cupo ENTERO",
        puerta_renovar["puede"] is True
        and puerta_renovar["quedan"] == cupo_de("renovar"),
        f"(quedan {puerta_renovar['quedan']})",
    )

    check(
        "renovar no ha gastado ninguna",
        puerta_renovar["llevadas"] == 0,
        f"({puerta_renovar['llevadas']})",
    )

    # ------------------------------------------------------
    # 3. Y AL REVES
    # ------------------------------------------------------

    print()
    print("3. Y al reves: agotar renovar no toca la puja")

    renovar_lleno = libro(carpeta, "renovar2.jsonl", 12)

    puja_vacia = libro(carpeta, "puja2.jsonl", 0)

    llena = puerta_del_cupo(
        "renovar", cupo_de("renovar"),
        desde_epoch=RESET, ruta=renovar_lleno,
    )

    intacta = puerta_del_cupo(
        "puja", cupo_de("puja"),
        desde_epoch=RESET, ruta=puja_vacia,
    )

    check(
        "renovar queda agotada con sus doce",
        llena["puede"] is False and llena["llevadas"] == 12,
        f"({llena})",
    )

    check(
        "y la puja sigue entera",
        intacta["puede"] is True
        and intacta["quedan"] == cupo_de("puja"),
        f"({intacta})",
    )

    # ------------------------------------------------------
    # 4. NINGUNA COMPARTE FICHERO
    # ------------------------------------------------------

    print()
    print("4. Ninguna familia comparte contador con otra")

    from src.analysis.el_cupo_de_las_escrituras import (
        LIBROS_POR_FAMILIA,
    )

    check(
        "cada familia tiene su propio libro",
        len(set(LIBROS_POR_FAMILIA.values()))
        == len(LIBROS_POR_FAMILIA),
        f"({LIBROS_POR_FAMILIA})",
    )

    check(
        "y las tres con cupo estan entre ellas",
        all(f in LIBROS_POR_FAMILIA for f in CUPOS_POR_FAMILIA),
    )


# ================================================================
# 5. LA FECHA DE REVISION, EN EL CODIGO
# ================================================================

print()
print("5. Los cupos caducan, y la fecha esta escrita")

check(
    "hay fecha de revision",
    REVISION_DE_LOS_CUPOS == "2026-09-26",
    f"({REVISION_DE_LOS_CUPOS})",
)

antes = la_revision_del_cupo("2026-09-20")

despues = la_revision_del_cupo("2026-09-27")

print(f"       el 20/09: {antes['reason'][-60:]}")
print(f"       el 27/09: {despues['reason'][-60:]}")

check(
    "antes de la fecha, no toca",
    antes["toca"] is False and antes["dias"] == 6,
    f"({antes})",
)

check(
    "pasada la fecha, toca",
    despues["toca"] is True,
    f"({despues})",
)

check(
    "y dice el `n` con el que se pusieron",
    antes["n_resets"] == 5 and "10/09-18/09" in antes["ventana"],
    f"({antes['n_resets']}, {antes['ventana']})",
)

sin_fecha = la_revision_del_cupo(None)

check(
    "sin saber que dia es, no se inventa: dice la fecha y para",
    sin_fecha["toca"] is None
    and REVISION_DE_LOS_CUPOS in sin_fecha["reason"],
    f"({sin_fecha})",
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
