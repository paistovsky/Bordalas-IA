"""
El tablon no pierde historia.

DOCTRINA 88 — UN FICHERO REESCRIBIBLE DESDE OTRA MAQUINA ES UNA
CACHE, NO UN LIBRO

    `board_events.json` NO se reconstruye. El tablon se pide de
    1000 en 1000 y una sola peticion no alcanza a cubrir la
    temporada: por eso existe `merge_board_events`, y por eso lo
    que se cae del fichero no vuelve de la API.

EL CASO REAL, MEDIDO EL 19/09/2026

    La copia local llevaba parada desde el 18/09 11:11 (627
    eventos). CI habia seguido acumulando hasta el 19/09 05:05
    (649 eventos). La local es un SUBCONJUNTO estricto: 22
    eventos en git que no estan en local, y CERO al reves.

    Guardar la local encima habria borrado, entre otros:

        f45d62117756d6a7e87b9bfd  transfer  18/09 06:53
            una de las DOS reemisiones de Lunin — justo la prueba
            del descuadre de 420.200

        3d15660bd0c3d1e7813beaab  market    19/09 05:05
            la resolucion de la puja de Maffeo

        + 3 transfer mas, 1 roundStarted y 14 bettingPool

    Y no se habria notado: el fichero va ordenado y con
    `indent=2`, asi que el diff sale como 5.473 lineas insertadas
    y 4.211 borradas. Parece una reescritura. Es una amputacion.

LO QUE SE COMPRUEBA

    1. El tablon ACUMULA: `merge_board_events` es un diccionario
       por `event_id`, union de lo guardado y lo fresco. No
       rederiva nada, asi que los duplicados de Lunin son de
       Biwenger y no nuestros.
    2. Una vuelta con menos eventos de entrada que los ya
       guardados NO puede reducir el fichero: `save_board_history`
       se niega a escribir.
    3. La poda legitima sigue siendo posible: lo anterior al
       `leagueReset` vigente no cuenta como perdida.
    4. El caso real del 19/09 se reproduce: las 22 que faltaban
       frenan el guardado.

LA GUARDIA MUERDE CON EL TABLON VACIO

    Sin eventos guardados no hay historia que perder y todo
    pasaria por vacuidad. Por eso lo primero es exigir que el
    banco traiga tablon.

DE DONDE SALEN LOS NUMEROS

    Fijos, escritos aqui. No se lee `data/` ni
    `diagnostico/status.json`, no se sale a la red y no se mira
    el reloj. El unico fichero que se toca es uno temporal que
    crea y borra esta misma guardia.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")

import src.collectors.board_history_collector as tablon  # noqa: E402
from src.collectors.board_history_collector import (  # noqa: E402
    ElTablonPerderiaHistoria,
    historia_que_se_perderia,
    merge_board_events,
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

RESET_TS = 1786278446          # leagueReset del 09/08, el dia 1

ANTES_DEL_RESET = RESET_TS - 86_400


def ev(event_id, tipo, date):
    return {"event_id": event_id, "type": tipo, "date": date}


# Lo que CI tenia acumulado.
GUARDADOS = [
    ev("aaa", "leagueReset", RESET_TS),
    ev("f45d62117756d6a7e87b9bfd", "transfer", 1789714414),
    ev("62a54356d435e072ddccf042", "transfer", 1789714990),
    ev("3d15660bd0c3d1e7813beaab", "market", 1789794318),
    ev("ddd", "roundStarted", 1789765200),
]

# Lo que trae una maquina parada desde antes: le faltan dos.
VUELTA_VIEJA = [
    ev("aaa", "leagueReset", RESET_TS),
    ev("62a54356d435e072ddccf042", "transfer", 1789714990),
    ev("ddd", "roundStarted", 1789765200),
]


# ================================================================
# 0. EL BANCO NO LLEGA VACIO
# ================================================================

print()
print("0. El tablon no llega vacio")

check(
    "hay tablon guardado",
    len(GUARDADOS) == 5,
    f"(n={len(GUARDADOS)})",
)

check(
    "con el tablon guardado vacio no hay historia que perder",
    historia_que_se_perderia([], VUELTA_VIEJA) == [],
)

check(
    "y con la vuelta vacia se pierde TODO lo guardado",
    len(historia_que_se_perderia(GUARDADOS, [])) == len(GUARDADOS),
    f"({len(historia_que_se_perderia(GUARDADOS, []))})",
)


# ================================================================
# 1. EL TABLON ACUMULA, NO REDERIVA
# ================================================================

print()
print("1. El tablon acumula: la mezcla es union por event_id")

mezclado, anadidos = merge_board_events(
    existing=GUARDADOS,
    fresh=VUELTA_VIEJA,
)

check(
    "mezclar una vuelta pobre no reduce el conjunto",
    len(mezclado) == len(GUARDADOS),
    f"(mezclado={len(mezclado)}, guardado={len(GUARDADOS)})",
)

check(
    "y no anade nada que no viniera",
    anadidos == 0,
    f"(anadidos={anadidos})",
)

# Las dos reemisiones de Lunin sobreviven a la mezcla: son dos
# event_id distintos, asi que el tablon NO las fabrica.
lunin = [
    e["event_id"]
    for e in mezclado
    if e["event_id"].startswith(("f45d6211", "62a54356"))
]

check(
    "las dos emisiones de Lunin son dos event_id distintos",
    len(lunin) == 2,
    f"({lunin})",
)

check(
    "luego el duplicado es de Biwenger, no lo fabricamos aqui",
    len(set(lunin)) == 2,
)


# ================================================================
# 2. UNA VUELTA POBRE NO PUEDE REDUCIR EL FICHERO
# ================================================================

print()
print("2. Una vuelta con menos eventos no reduce el fichero")

perdidos = historia_que_se_perderia(GUARDADOS, VUELTA_VIEJA)

print(f"       perderia: {[p['event_id'][:8] for p in perdidos]}")

check(
    "se detecta lo que se perderia",
    len(perdidos) == 2,
    f"(n={len(perdidos)})",
)

check(
    "y entre ello, la reemision de Lunin",
    any(
        p["event_id"] == "f45d62117756d6a7e87b9bfd"
        for p in perdidos
    ),
)

# El freno de verdad: escribir se aborta.
with tempfile.TemporaryDirectory() as carpeta:

    destino = Path(carpeta) / "board_events.json"

    crudo = Path(carpeta) / "board_latest_raw.json"

    destino.write_text(
        json.dumps(GUARDADOS, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    file_previo = tablon.BOARD_FILE
    raw_previo = tablon.BOARD_RAW_FILE
    dir_previo = tablon.DATA_DIR

    tablon.BOARD_FILE = destino
    tablon.BOARD_RAW_FILE = crudo
    tablon.DATA_DIR = Path(carpeta)

    try:
        frenado = False

        try:
            tablon.save_board_history(
                events=VUELTA_VIEJA,
                raw_events=[],
                reset_ts=RESET_TS,
            )

        except ElTablonPerderiaHistoria as error:
            frenado = True
            motivo = str(error)

        check(
            "guardar una vuelta pobre se ABORTA, no se avisa",
            frenado,
            "<- se escribio igual",
        )

        if frenado:
            check(
                "y el motivo nombra cuantos eventos se perderian",
                "2 evento(s)" in motivo,
                f"({motivo[:90]})",
            )

        en_disco = json.loads(
            destino.read_text(encoding="utf-8")
        )

        check(
            "el fichero sigue entero en disco",
            len(en_disco) == len(GUARDADOS),
            f"(quedaron {len(en_disco)} de {len(GUARDADOS)})",
        )

        # ----------------------------------------------------
        # 3. LA PODA LEGITIMA SIGUE PASANDO
        # ----------------------------------------------------

        print()
        print("3. Lo anterior al reset vigente si puede podarse")

        con_era_vieja = [
            ev("viejo", "transfer", ANTES_DEL_RESET),
            *GUARDADOS,
        ]

        destino.write_text(
            json.dumps(
                con_era_vieja, ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

        podado = False

        try:
            tablon.save_board_history(
                events=GUARDADOS,
                raw_events=[],
                reset_ts=RESET_TS,
            )
            podado = True

        except ElTablonPerderiaHistoria:
            podado = False

        check(
            "podar la era anterior NO se considera perdida",
            podado,
            "<- el freno confundio una poda con una amputacion",
        )

        check(
            "y sin saber el reset, esa misma poda SI frena",
            historia_que_se_perderia(
                con_era_vieja, GUARDADOS, reset_ts=None
            )
            != [],
        )

    finally:
        tablon.BOARD_FILE = file_previo
        tablon.BOARD_RAW_FILE = raw_previo
        tablon.DATA_DIR = dir_previo


# ================================================================
# 4. EL CASO REAL DEL 19/09
# ================================================================

print()
print("4. El caso real: 649 en git contra 627 en local")

GIT = [ev(f"e{i:04d}", "transfer", 1789000000 + i) for i in range(649)]

LOCAL = [e for e in GIT if int(e["event_id"][1:]) < 627]

perdidos_real = historia_que_se_perderia(
    GIT, LOCAL, reset_ts=RESET_TS
)

check(
    "la copia local es un subconjunto estricto",
    len(LOCAL) == 627 and len(GIT) == 649,
    f"(local={len(LOCAL)}, git={len(GIT)})",
)

check(
    "guardarla encima perderia 22 eventos",
    len(perdidos_real) == 22,
    f"(n={len(perdidos_real)})",
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
