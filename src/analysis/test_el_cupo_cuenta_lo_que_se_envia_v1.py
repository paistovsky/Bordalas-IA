"""
El cupo cuenta lo que se envia, no lo que se gana.

EL AGUJERO, CON LA LINEA DELANTE

    `libro_de_viajes.cuantos_en_este_reset`, linea 521:

        if fila.get("state") != ABIERTO:
            continue

    Cuenta viajes ABIERTOS. Un viaje se abre cuando la puja se
    GANA. Asi que entre poner la puja y ganarla, el contador no
    se mueve — y repujar al mismo jugador es gratis.

    Ese numero va a `la_rendija.permiso`, linea 1461:

        quedan_reset = max(0, cupo["cupo"] - operaciones_en_este_reset)

    Medido: nueve escrituras de Maffeo el 18/09 contra un cupo de
    1. El portero no se entero porque estaba contando otra cosa.

    Y el cupo de la vuelta tampoco mordia:
    `escrituras_en_esta_vuelta` vale 0 por defecto y NADIE se lo
    pasa.

DOCTRINA 24, QUE AQUI TAMBIEN APLICA

    Un libro que NO EXISTE si es un cero: esa familia no ha
    escrito nunca. Un libro que existe y NO SE PUEDE LEER no es
    cero: es "no lo se", y con eso no se escribe.

QUE COMPRUEBA ESTA GUARDIA

    1. Dos escrituras seguidas de la misma familia con cupo 1 y
       ninguna ganada: la segunda NO sale.
    2. Y es el CUPO quien la para, no otra puerta.
    3. Una escritura que no llego a enviarse (`sent: False`) no
       gasta cupo.
    4. Lo de antes del reset no cuenta.
    5. Cada familia lleva su propia cuenta: llenar una no vacia
       la otra.
    6. El motivo dice que escritura, contra que cupo y cuantas
       van (doctrina 87).
    7. Un libro ilegible frena; uno inexistente no.

LA GUARDIA MUERDE SI EL CUPO LLEGA A CERO POR OTRA VIA

    Si el cupo saliera agotado sin que ninguna escritura lo
    hubiera gastado, la comprobacion (1) pasaria por vacuidad.
    Por eso lo primero es exigir que con el libro vacio quede
    cupo, y que sea la PRIMERA escritura la que lo gaste.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. El libro es un fichero temporal que
    crea y borra esta misma guardia. No se lee `data/`, no se
    sale a la red y no se mira el reloj del sistema: el `desde`
    es una marca escrita a mano.
"""

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, ".")

from src.analysis.el_cupo_de_las_escrituras import (  # noqa: E402
    CUPO_POR_ENVIOS_ENV,
    LIBROS_POR_FAMILIA,
    cupo_por_envios_activo,
    escrituras_enviadas,
    puerta_del_cupo,
)


fallos = []


def check(nombre, condicion, detalle=""):
    if condicion:
        print(f"  OK   {nombre}")
    else:
        print(f"  FALLA {nombre} {detalle}")
        fallos.append(nombre)


# ================================================================
# EL BANCO
# ================================================================

RESET = datetime(
    2026, 9, 18, 7, 0, 0, tzinfo=timezone.utc
).timestamp()

CUPO = 1


def escritura(hora, jugador, enviada=True):
    return {
        "at": f"2026-09-18T{hora}:00+00:00",
        "player_id": jugador,
        "player_name": f"J{jugador}",
        "amount": 1_000_000,
        "sent": enviada,
        "http_status": 200 if enviada else None,
        "success": enviada,
    }


def libro_con(carpeta, nombre, filas):
    destino = Path(carpeta) / nombre

    destino.write_text(
        "\n".join(
            json.dumps(f, ensure_ascii=False) for f in filas
        ),
        encoding="utf-8",
    )

    return destino


# ================================================================
# 0. CON EL LIBRO VACIO QUEDA CUPO
# ================================================================

print()
print("0. El cupo no llega agotado por otra via")

with tempfile.TemporaryDirectory() as carpeta:

    vacio = libro_con(carpeta, "vacio.jsonl", [])

    puerta = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=vacio
    )

    check(
        "con el libro vacio se puede escribir",
        puerta["puede"] is True,
        f"({puerta['reason']})",
    )

    check(
        "y queda el cupo entero",
        puerta["quedan"] == CUPO and puerta["llevadas"] == 0,
        f"(quedan {puerta['quedan']}, llevadas {puerta['llevadas']})",
    )

    # ------------------------------------------------------
    # 1. LA SEGUNDA NO SALE
    # ------------------------------------------------------

    print()
    print("1. Dos seguidas con cupo 1: la segunda no sale")

    una = libro_con(
        carpeta, "una.jsonl", [escritura("08", 10030)]
    )

    tras_una = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=una
    )

    print(f"       {tras_una['reason']}")

    check(
        "la primera gasta el cupo",
        tras_una["llevadas"] == 1,
        f"({tras_una['llevadas']})",
    )

    check(
        "y la segunda NO sale",
        tras_una["puede"] is False,
        f"({tras_una})",
    )

    check(
        "la para el cupo de la familia, no otra puerta",
        tras_una["blocked_by"] == "CUPO_DE_LA_FAMILIA",
        f"({tras_una['blocked_by']})",
    )

    check(
        "y ninguna se ha ganado: no hay viaje de por medio",
        tras_una["available"] is True,
    )

    # ------------------------------------------------------
    # 2. EL MOTIVO LO DICE ENTERO
    # ------------------------------------------------------

    print()
    print("2. El motivo nombra la familia, el cupo y cuantas van")

    check(
        "dice la familia",
        "puja" in tras_una["reason"],
        f"({tras_una['reason']})",
    )

    check(
        "dice cuantas van",
        "van 1 " in tras_una["reason"],
        f"({tras_una['reason']})",
    )

    check(
        "dice contra que cupo",
        f"cupo de {CUPO}" in tras_una["reason"],
        f"({tras_una['reason']})",
    )

    # ------------------------------------------------------
    # 3. LO QUE NO SE ENVIO NO GASTA
    # ------------------------------------------------------

    print()
    print("3. Una escritura que no salio no gasta cupo")

    fallida = libro_con(
        carpeta,
        "fallida.jsonl",
        [escritura("08", 10030, enviada=False)],
    )

    tras_fallida = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=fallida
    )

    check(
        "no cuenta",
        tras_fallida["llevadas"] == 0,
        f"({tras_fallida['llevadas']})",
    )

    check(
        "y se puede seguir escribiendo",
        tras_fallida["puede"] is True,
    )

    # ------------------------------------------------------
    # 4. LO DE ANTES DEL RESET NO CUENTA
    # ------------------------------------------------------

    print()
    print("4. Lo de antes del reset no cuenta")

    vieja = libro_con(
        carpeta,
        "vieja.jsonl",
        [
            {
                **escritura("08", 10030),
                "at": "2026-09-17T23:00:00+00:00",
            }
        ],
    )

    tras_vieja = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=vieja
    )

    check(
        "una escritura del reset anterior no gasta",
        tras_vieja["llevadas"] == 0
        and tras_vieja["puede"] is True,
        f"({tras_vieja['llevadas']})",
    )

    # ------------------------------------------------------
    # 5. CADA FAMILIA, SU CUENTA
    # ------------------------------------------------------

    print()
    print("5. Llenar una familia no vacia la otra")

    publicar = libro_con(
        carpeta,
        "publicar.jsonl",
        [escritura("08", 1), escritura("09", 2)],
    )

    cupo_publicar = puerta_del_cupo(
        "publicar", CUPO, desde_epoch=RESET, ruta=publicar
    )

    check(
        "publicar tiene su cuenta llena",
        cupo_publicar["llevadas"] == 2
        and cupo_publicar["puede"] is False,
        f"({cupo_publicar['llevadas']})",
    )

    check(
        "y puja sigue con la suya intacta",
        puerta_del_cupo(
            "puja", CUPO, desde_epoch=RESET, ruta=vacio
        )["puede"]
        is True,
    )

    check(
        "las familias declaradas tienen libro propio",
        len(set(LIBROS_POR_FAMILIA.values()))
        == len(LIBROS_POR_FAMILIA),
        f"({LIBROS_POR_FAMILIA})",
    )

    # ------------------------------------------------------
    # 6. NO SABER NO ES CERO
    # ------------------------------------------------------

    print()
    print("6. Un libro ilegible frena; uno inexistente no")

    roto = Path(carpeta) / "roto.jsonl"

    roto.write_text("{esto no es json\n", encoding="utf-8")

    tras_roto = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=roto
    )

    check(
        "un libro ilegible no deja escribir",
        tras_roto["puede"] is False
        and tras_roto["available"] is False,
        f"({tras_roto})",
    )

    check(
        "con un motivo distinto del de cupo agotado",
        tras_roto["blocked_by"] == "CUPO_SIN_SABER",
        f"({tras_roto['blocked_by']})",
    )

    inexistente = Path(carpeta) / "no_existe.jsonl"

    tras_inexistente = puerta_del_cupo(
        "puja", CUPO, desde_epoch=RESET, ruta=inexistente
    )

    check(
        "un libro que no existe SI es un cero",
        tras_inexistente["available"] is True
        and tras_inexistente["puede"] is True,
        f"({tras_inexistente})",
    )

    # Y sin marca desde la que contar, tampoco se sabe.
    sin_marca = escrituras_enviadas("puja", None, ruta=una)

    check(
        "sin marca del reset no se sabe cuantas van",
        sin_marca["available"] is False,
        f"({sin_marca})",
    )


# ================================================================
# 7. EL INTERRUPTOR
# ================================================================

print()
print("7. Apagado por defecto")

check(
    "el cupo por envios esta apagado",
    cupo_por_envios_activo() is False,
)

check(
    "y se llama BORDALAS_CUPO_POR_ENVIOS",
    CUPO_POR_ENVIOS_ENV == "BORDALAS_CUPO_POR_ENVIOS",
    f"({CUPO_POR_ENVIOS_ENV})",
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
