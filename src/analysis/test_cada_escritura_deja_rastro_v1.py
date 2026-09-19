"""
Cada escritura deja rastro, y su clave es el `event_id`.

LO QUE NO DEJA RASTRO NO SE PUEDE MEDIR

    Al desglosar el desperdicio de escrituras del 19/09, tres
    familias salieron con una raya en vez de un numero:

        aceptar oferta      no escribia libro
        reroll              no escribia libro
        guardar alineacion  no escribia libro

    No es que no repitan: es que no constaba. Poner un cero ahi
    habria sido inventarse una medida. Las otras tres —puja,
    publicar, renovar— se pudieron medir justamente porque
    llevan libro.

    Y una correccion a como lo conte: `vender / salida` SI
    escribe libro (`salida_executor`, linea 171). Lo que pasa es
    que nunca ha corrido, asi que el fichero no existe. "El libro
    no existe" y "no escribe libro" no son lo mismo, y yo los
    junte.

LA CLAVE ES `event_id`, NO LA MARCA DE TIEMPO

    Ya nos mordio dos veces: la reja del tablon llevaba la FECHA
    dentro de la clave, y el libro de pujas era
    `player_id:placed_at`. Las dos veces una operacion se
    convirtio en muchas.

    Aqui la identidad es el `event_id` que devuelve Biwenger, y
    la hora viaja al lado en `at`, donde no manda. Cuando
    Biwenger no devuelve id —guardar una alineacion no lo trae—
    la identidad es la HUELLA DEL CONTENIDO, nunca el reloj.

QUE COMPRUEBA ESTA GUARDIA

    1. Cada familia que hace un POST escribe una entrada.
    2. La entrada lleva la forma de los libros que ya existen:
       `at`, `sent`, `http_status`, `success`.
    3. La clave es el `event_id` de Biwenger cuando lo hay.
    4. Cuando no lo hay, es la huella del contenido: dos envios
       identicos dan la MISMA clave, y uno distinto otra.
    5. La hora NO entra en la clave: dos envios identicos a
       horas distintas siguen dando la misma.
    6. Una escritura fallida tambien deja rastro, con
       `success: False`.

LA GUARDIA MUERDE SI ALGUNA FAMILIA NO ESCRIBE

    Es su unico trabajo: recorre las familias que hacen POST y
    exige una entrada de cada una. Si alguna no escribiera, el
    recuento no cuadra y sale en rojo.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El libro es un fichero temporal que
    crea y borra esta misma guardia. No se lee `data/`, no se
    sale a la red y no se escribe en ningun libro de produccion.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")

from src.actions.el_rastro import (  # noqa: E402
    apuntar_escritura,
    huella,
    identidad_de_la_escritura,
)
from src.analysis.el_cupo_de_las_escrituras import (  # noqa: E402
    LIBROS_POR_FAMILIA,
    escrituras_enviadas,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# Las familias que hacen un POST contra Biwenger.
FAMILIAS_QUE_ESCRIBEN = (
    "puja",
    "publicar",
    "renovar",
    "vender",
    "aceptar",
    "reroll",
    "alineacion",
)


# ================================================================
# 0. TODAS LAS FAMILIAS TIENEN LIBRO DECLARADO
# ================================================================

print()
print("0. Toda familia que escribe tiene libro")

sin_libro = [
    f for f in FAMILIAS_QUE_ESCRIBEN
    if f not in LIBROS_POR_FAMILIA
]

check(
    "ninguna familia se queda sin libro",
    not sin_libro,
    f"({sin_libro})",
)

check(
    "y son siete",
    len(FAMILIAS_QUE_ESCRIBEN) == 7,
    f"({len(FAMILIAS_QUE_ESCRIBEN)})",
)

check(
    "cada una con su fichero, sin compartir",
    len({LIBROS_POR_FAMILIA[f] for f in FAMILIAS_QUE_ESCRIBEN})
    == len(FAMILIAS_QUE_ESCRIBEN),
)


# ================================================================
# 1. CADA FAMILIA ESCRIBE UNA ENTRADA
# ================================================================

print()
print("1. Cada familia que hace un POST escribe una entrada")

RESPUESTA = {
    "sent": True,
    "success": True,
    "http_status": 200,
    "data": {"id": 987654321},
}

with tempfile.TemporaryDirectory() as carpeta:

    escritas = {}

    for familia in FAMILIAS_QUE_ESCRIBEN:

        destino = Path(carpeta) / f"{familia}.jsonl"

        fila = apuntar_escritura(
            familia,
            resultado=RESPUESTA,
            player_id=10030,
            player_name="Maffeo",
            amount=1_664_350,
            contenido={"familia": familia},
            ruta=destino,
            at="2026-09-18T12:00:00+00:00",
        )

        escritas[familia] = (fila, destino)

    check(
        "las siete anotan",
        all(f["anotada"] for f, _ in escritas.values()),
        f"({[k for k, (f, _) in escritas.items() if not f['anotada']]})",
    )

    check(
        "y las siete dejan fichero",
        all(d.exists() for _, d in escritas.values()),
    )

    # Y el contador las ve.
    vistas = {
        familia: escrituras_enviadas(
            familia,
            desde_epoch=0,
            ruta=destino,
        )["cuantas"]
        for familia, (_f, destino) in escritas.items()
    }

    print(f"       {vistas}")

    check(
        "el contador de cupo ve una de cada",
        all(n == 1 for n in vistas.values()),
        f"({vistas})",
    )

    # ------------------------------------------------------
    # 2. LA FORMA ES LA DE LOS LIBROS QUE YA EXISTEN
    # ------------------------------------------------------

    print()
    print("2. La forma es la de los libros que ya existen")

    una, destino = escritas["aceptar"]

    en_disco = json.loads(
        destino.read_text(encoding="utf-8").strip()
    )

    for campo in (
        "at", "sent", "success", "http_status", "event_id",
        "player_id", "amount",
    ):
        check(
            f"lleva `{campo}`",
            campo in en_disco,
            f"({sorted(en_disco)})",
        )

    # ------------------------------------------------------
    # 3. LA CLAVE ES EL event_id DE BIWENGER
    # ------------------------------------------------------

    print()
    print("3. La clave es el event_id de Biwenger cuando lo hay")

    check(
        "se usa el id que devuelve Biwenger",
        en_disco["event_id"] == "987654321",
        f"({en_disco['event_id']})",
    )

    # ------------------------------------------------------
    # 4. SIN ID, LA HUELLA DEL CONTENIDO
    # ------------------------------------------------------

    print()
    print("4. Sin id, la huella del contenido")

    SIN_ID = {"sent": True, "success": True, "http_status": 204}

    ONCE = {
        "player_ids": [1, 2, 3],
        "formation": "4-3-3",
    }

    OTRO_ONCE = {
        "player_ids": [1, 2, 4],
        "formation": "4-3-3",
    }

    a = identidad_de_la_escritura(SIN_ID, ONCE)

    b = identidad_de_la_escritura(SIN_ID, ONCE)

    c = identidad_de_la_escritura(SIN_ID, OTRO_ONCE)

    check(
        "dos envios identicos dan la MISMA clave",
        a == b,
        f"({a} vs {b})",
    )

    check(
        "y uno distinto da otra",
        a != c,
        f"({a} vs {c})",
    )

    check(
        "la huella sale del contenido, no del reloj",
        a == huella(ONCE),
    )

    # ------------------------------------------------------
    # 5. LA HORA NO ENTRA EN LA CLAVE
    # ------------------------------------------------------

    print()
    print("5. La hora NO entra en la clave")

    otro = Path(carpeta) / "alineacion2.jsonl"

    primera = apuntar_escritura(
        "alineacion",
        resultado=SIN_ID,
        contenido=ONCE,
        ruta=otro,
        at="2026-09-18T12:00:00+00:00",
    )

    segunda = apuntar_escritura(
        "alineacion",
        resultado=SIN_ID,
        contenido=ONCE,
        ruta=otro,
        at="2026-09-18T13:00:00+00:00",
    )

    check(
        "dos envios identicos a horas distintas: misma clave",
        primera["event_id"] == segunda["event_id"],
        f"({primera['event_id']} vs {segunda['event_id']})",
    )

    check(
        "y la hora si viaja al lado, distinta",
        primera["at"] != segunda["at"],
    )

    check(
        "las dos filas se anotan: el cupo cuenta ENVIOS",
        escrituras_enviadas(
            "alineacion", desde_epoch=0, ruta=otro
        )["cuantas"]
        == 2,
    )

    # ------------------------------------------------------
    # 6. UNA ESCRITURA FALLIDA TAMBIEN DEJA RASTRO
    # ------------------------------------------------------

    print()
    print("6. Una escritura fallida tambien deja rastro")

    fallo = Path(carpeta) / "fallo.jsonl"

    rota = apuntar_escritura(
        "aceptar",
        resultado={
            "sent": True,
            "success": False,
            "http_status": 500,
        },
        contenido={"offer_id": 1},
        ruta=fallo,
        at="2026-09-18T12:00:00+00:00",
    )

    check(
        "se anota",
        rota["anotada"] is True,
    )

    check(
        "con success en False",
        rota["success"] is False,
        f"({rota})",
    )

    check(
        "y su http, para saber por que fallo",
        rota["http_status"] == 500,
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
