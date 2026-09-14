"""
El orden del tiempo: `round_id` no es el calendario.

EL FALLO (14/09/2026)

    El marcador ordenaba las jornadas por `round_id` y daba por
    hecho que ese orden era el del tiempo. Esta liga lo desmiente
    sola: la jornada 6 viene PARTIDA EN DOS IDS.

        round 4903  Jornada 5              10 partidos  13-14/09
        round 4904  Jornada 6               1 partido      03/09
        round 5125  Jornada 6 (aplazada)   19 partidos  15-17/09

    Y la lista que publica Biwenger tampoco viene ordenada por
    id: 4904 aparece entre 4901 y 4902.

    Ordenando por id, la "previa" de 4904 era 4903 —una foto
    tomada DIEZ DIAS DESPUES—, la resta de totales acumulados iba
    al reves y salian once jugadores en negativo. De ahi el
    `mejor_puntos: -55` que llego a la pantalla: un "mejor once
    posible" que no puede existir.

LAS TRES CAPAS, Y HACEN FALTA LAS TRES

    1. EL ORDEN arregla la causa: la clave es la hora del primer
       partido, no el id.

    2. LA CONTIGUIDAD arregla lo que el orden no puede: aunque
       ordenes bien, si faltan jornadas en medio la resta cubre
       varias juntas y se publica como si fuera una.

    3. EL INVARIANTE es la red: una diferencia de acumulados no
       puede ser negativa. Si lo es, las fotos estan al reves y
       se dice, en vez de publicar el numero.

REGLA 23

    Ninguna lee estado de produccion: el ledger va a un
    directorio temporal y el calendario se construye aqui.

REGLA 24

    Ninguna pasa con las manos vacias. Una lista vacia haria
    verde cualquiera de las tres sin probar nada.

DOCTRINA 50

    Ninguna mira el reloj del sistema: todas las horas van
    escritas.
"""

from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.analysis import marcador as M


# ============================================================
# EL CALENDARIO DE VERDAD DE ESTA LIGA
# ============================================================
#
# Copiado de la foto del 13/09/2026, con los nombres tal y como
# los publica Biwenger. Es el caso que rompio el motor, no un
# ejemplo inventado: la jornada 6 partida en dos y una de sus
# mitades jugada antes que la jornada 4.

JORNADAS_DE_BIWENGER = [
    {"id": 4899, "name": "Jornada 1"},
    {"id": 4900, "name": "Jornada 2"},
    {"id": 4901, "name": "Jornada 3"},
    {"id": 4904, "name": "Jornada 6"},
    {"id": 4902, "name": "Jornada 4"},
    {"id": 4903, "name": "Jornada 5"},
    {"id": 5125, "name": "Jornada 6 (aplazada)"},
]

# El partido adelantado de la jornada 6 —Real Sociedad-Celta, el
# 3 de septiembre— y los primeros de las otras dos que se ven.
PARTIDOS = [
    {"round": {"id": 4904}, "date": 1788462000},   # 03/09 19:00
    {"round": {"id": 4903}, "date": 1789300800},   # 13/09 12:00
    {"round": {"id": 5125}, "date": 1789491600},   # 15/09 17:00
]

# El respaldo, por NUMERO de jornada, como lo da el calendario de
# LaLiga. Las jornadas viejas solo tienen esto.
KICKOFF_DE_LALIGA = {
    1: "2026-08-15T19:30:00+02:00",
    2: "2026-08-20T21:00:00+02:00",
    3: "2026-08-28T19:00:00+02:00",
    4: "2026-09-04T21:00:00+02:00",
    5: "2026-09-13T14:00:00+02:00",
    6: "2026-09-15T19:00:00+02:00",
}


def _calendario() -> dict:
    return M.calendario_de_jornadas(
        JORNADAS_DE_BIWENGER,
        partidos=PARTIDOS,
        kickoff_por_jornada=KICKOFF_DE_LALIGA,
    )


# ============================================================
# UTILIDAD: un ledger de mentira en un directorio temporal
# ============================================================


class ledger_temporal:
    """Aparta el fichero real mientras dura la prueba.

    Ninguna de estas guardias puede tocar
    `data/intelligence/marcador.json`: es estado de produccion y
    una prueba que lo escriba deja de ser una prueba.
    """

    def __enter__(self):
        self._directorio = tempfile.TemporaryDirectory()

        self._state = M.STATE_DIRECTORY
        self._file = M.LEDGER_FILE

        M.STATE_DIRECTORY = Path(self._directorio.name)
        M.LEDGER_FILE = M.STATE_DIRECTORY / "marcador.json"

        return M.LEDGER_FILE

    def __exit__(self, *_):
        M.STATE_DIRECTORY = self._state
        M.LEDGER_FILE = self._file
        self._directorio.cleanup()


def _jornada(
    round_id: int,
    totales: dict,
    puntos_de_liga: int = 0,
) -> dict:
    """Una observacion con lo justo para que el motor la mida."""

    once = sorted(totales)[:11]

    return {
        "round_id": round_id,
        "visto": f"2026-09-{round_id % 28 + 1:02d}T12:00:00",
        "mi_user_id": 14175949,
        "clasificacion": [
            {
                "user_id": 14175949,
                "name": "Pepe",
                "points": puntos_de_liga,
            },
            {
                "user_id": 14154203,
                "name": "Prinzipote",
                "points": puntos_de_liga,
            },
        ],
        "mi_once": {"formation": "4-4-2", "players": once},
        "plantilla": [
            {
                "id": int(pid),
                "name": f"Jugador {pid}",
                # 1 portero, 4 defensas, 4 medios, 2 delanteros.
                "position": (
                    1 if i == 0
                    else 2 if i <= 4
                    else 3 if i <= 8
                    else 4
                ),
            }
            for i, pid in enumerate(sorted(totales))
        ],
        "totales": dict(totales),
        "nombres": {
            str(pid): f"Jugador {pid}" for pid in totales
        },
    }


def _escribir(ruta: Path, jornadas: list) -> None:

    ruta.parent.mkdir(parents=True, exist_ok=True)

    ruta.write_text(
        json.dumps(
            {
                "version": 1,
                "updated_at": "2026-09-14T20:00:00",
                "jornadas": {
                    str(j["round_id"]): j for j in jornadas
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# 1. EL ORDEN NO ES EL ID
# ============================================================


def test_el_orden_no_es_el_id() -> None:
    """La previa de cada jornada es la correcta EN EL TIEMPO.

    Con la jornada 6 de verdad —un partido el 03/09 y el resto en
    un id mayor— el orden por `round_id` y el orden por
    calendario NO COINCIDEN. Esta guardia fija el segundo.
    """

    calendario = _calendario()

    # REGLA 24: sin calendario esto no probaria nada.
    assert calendario, "el calendario llego vacio"

    assert len(calendario) == len(JORNADAS_DE_BIWENGER), (
        f"faltan jornadas en el calendario: "
        f"{len(calendario)} de {len(JORNADAS_DE_BIWENGER)}"
    )

    # LA HORA DE VERDAD GANA AL RESPALDO. El partido adelantado de
    # la jornada 6 es del 03/09, no del 15/09 que dice LaLiga.
    assert (
        calendario[4904]["fuente"] == "PARTIDOS_DE_LA_JORNADA"
    ), calendario[4904]

    assert calendario[4904]["primer_partido"].startswith(
        "2026-09-03"
    ), calendario[4904]

    # Y una jornada vieja, sin partidos ya a la vista, se coloca
    # con el respaldo — dicho, no disimulado.
    assert (
        calendario[4900]["fuente"] == "CALENDARIO_DE_LALIGA"
    ), calendario[4900]

    # LAS DOS MITADES DE LA JORNADA 6 CAEN DONDE TOCA, y no en el
    # mismo sitio: 4904 el 03/09 y 5125 el 15/09.
    assert (
        calendario[4904]["primer_partido"]
        < calendario[5125]["primer_partido"]
    ), (calendario[4904], calendario[5125])

    assert calendario[4904]["numero"] == 6, calendario[4904]
    assert calendario[5125]["numero"] == 6, calendario[5125]

    # EL ORDEN. Se le pasan las jornadas en el orden del id, que
    # es el que usaba el motor roto.
    observadas = [
        {"round_id": rid}
        for rid in sorted(
            j["id"] for j in JORNADAS_DE_BIWENGER
        )
    ]

    colocadas = M.orden_en_el_tiempo(observadas, calendario)

    # REGLA 24: si no se coloco ninguna, no se ha probado nada.
    assert colocadas["ordenadas"], (
        "no se coloco ninguna jornada en el tiempo"
    )

    assert not colocadas["sin_hora"], colocadas["sin_hora"]

    salida = [item["round_id"] for item in colocadas["ordenadas"]]

    entrada = [j["round_id"] for j in observadas]

    # EL PUNTO DE TODO: los dos ordenes son DISTINTOS. Si algun
    # dia coincidieran, esta guardia habria dejado de probar el
    # fallo que existe.
    assert salida != entrada, (
        f"el orden del calendario ha salido igual que el del id "
        f"({salida}): esta prueba ya no prueba nada"
    )

    assert salida == [
        4899,   # J1   15/08
        4900,   # J2   20/08
        4901,   # J3   28/08
        4904,   # J6   03/09  <- el adelantado, ANTES que la J4
        4902,   # J4   04/09
        4903,   # J5   13/09
        5125,   # J6   15/09
    ], salida

    # Y LA PREVIA DE CADA UNA, dicho en la forma en que lo usa el
    # motor: la de 4902 es 4904, no 4901.
    previa = {
        salida[i]: salida[i - 1]
        for i in range(1, len(salida))
    }

    assert previa[4902] == 4904, previa

    assert previa[4903] == 4902, previa

    assert previa[5125] == 4903, previa


# ============================================================
# 2. UNA JORNADA CON HUECO NO SE MIDE
# ============================================================


def test_una_jornada_con_hueco_no_se_mide() -> None:
    """Si faltan jornadas en medio, no hay nota. Y se dice cual.

    Aunque el orden sea el bueno, con `{4899, 4902}` en el libro
    la resta de totales cubre la 2, la 3 y el adelantado de la 6.
    Publicar eso como "la jornada 4" es inventarse una nota.
    """

    calendario = _calendario()

    # REGLA 24.
    assert calendario, "el calendario llego vacio"

    # LO QUE FALTA EN MEDIO, antes de tocar el ledger.
    faltan = M.jornadas_en_medio(
        calendario[4899]["primer_partido"],
        calendario[4902]["primer_partido"],
        calendario,
    )

    assert faltan, (
        "no se vio ningun hueco entre la jornada 1 y la 4"
    )

    assert sorted(f["round_id"] for f in faltan) == [
        4900,   # J2
        4901,   # J3
        4904,   # J6 adelantada, que cae el 03/09
    ], faltan

    # Y AHORA EL MOTOR ENTERO.
    with ledger_temporal() as libro:

        _escribir(
            libro,
            [
                _jornada(
                    4899,
                    {str(100 + i): 2 for i in range(16)},
                    puntos_de_liga=30,
                ),
                _jornada(
                    4902,
                    {str(100 + i): 9 for i in range(16)},
                    puntos_de_liga=140,
                ),
                # La tercera solo esta para que la 4902 cuente
                # como cerrada: sin sucesora no se mide ninguna.
                _jornada(
                    4903,
                    {str(100 + i): 12 for i in range(16)},
                    puntos_de_liga=180,
                ),
            ],
        )

        datos = M.marcador(calendario)

    filas = {f["round_id"]: f for f in datos["jornadas"]}

    # REGLA 24: sin filas no se ha medido nada.
    assert filas, "el marcador no devolvio ninguna jornada"

    cuarta = filas[4902]

    assert not cuarta["medible"], (
        f"la jornada 4 se midio con tres jornadas de hueco: "
        f"{cuarta}"
    )

    # EL MOTIVO, ESCRITO. Un `medible: false` sin motivo obliga a
    # abrir el codigo para saber que falta.
    assert cuarta.get("motivo"), cuarta

    assert "en medio" in cuarta["motivo"], cuarta["motivo"]

    # Y QUE FALTA, EN DATOS. La pantalla no tiene que reparsear
    # la frase para pintar los nombres.
    assert sorted(
        f["round_id"] for f in cuarta["jornadas_que_faltan"]
    ) == [4900, 4901, 4904], cuarta["jornadas_que_faltan"]

    # NO SE LE PONE NOTA IGUALMENTE. Ni eficiencia, ni puntos, ni
    # cuadre: una jornada no medible no trae numeros.
    for campo in (
        "eficiencia",
        "puntos_once",
        "mejor_puntos",
        "puntos_biwenger",
        "descuadre",
    ):
        assert cuarta.get(campo) is None, (campo, cuarta)

    # Y NO ENSUCIA LA MEDIA.
    assert datos["resumen"]["jornadas_con_hueco"] >= 1, (
        datos["resumen"]
    )

    assert 4902 not in [
        f["round_id"]
        for f in datos["jornadas"]
        if f.get("medible")
    ], datos["jornadas"]


# ============================================================
# 3. UNA DIFERENCIA NEGATIVA NO SE PUBLICA
# ============================================================


def test_una_diferencia_negativa_no_se_publica() -> None:
    """Dos fotos al reves dan un motivo, no un numero.

    Es la red que faltaba el dia del `-55`. Un jugador no pierde
    puntos de temporada: si la resta sale negativa, la foto que
    se esta usando de previa se tomo despues.
    """

    # LA RESTA, A PELO. Once jugadores que "pierden" 5 puntos.
    antes = {str(100 + i): 30 for i in range(11)}
    ahora = {str(100 + i): 25 for i in range(11)}

    # REGLA 24: sin diferencias que mirar esto seria verde vacio.
    assert antes and ahora, "las fotos llegaron vacias"

    diferencias = [
        ahora[pid] - antes[pid] for pid in ahora
    ]

    assert diferencias, "no salio ninguna diferencia"

    assert any(d < 0 for d in diferencias), (
        f"esta prueba necesita alguna diferencia negativa y no "
        f"hay ninguna: {diferencias}"
    )

    puntos, motivo = M._puntos_de_la_jornada(
        {"round_id": 4904, "totales": ahora},
        {"round_id": 4903, "totales": antes},
    )

    assert puntos is None, (
        f"se publicaron puntos de una resta invertida: {puntos}"
    )

    assert motivo, "no se dijo por que no se mide"

    assert "negativos" in motivo, motivo

    assert "al reves" in motivo, motivo

    # EL NUMERO EXACTO QUE SE PUBLICO EN PANTALLA. Con once
    # jugadores a -5 y un 4-4-2 obligado, el techo salia -55.
    #
    # Se comprueba que `mejor_once` SIGUE devolviendo -55 con esa
    # entrada —no se ha tocado, y no habia que tocarlo: el fallo
    # no estaba ahi— y que el motor ya no llega a preguntarselo.
    posiciones = {
        pid: (1 if i == 0 else 2 if i <= 4 else 3 if i <= 8 else 4)
        for i, pid in enumerate(sorted(ahora))
    }

    techo = M.mejor_once(
        {pid: -5 for pid in ahora},
        posiciones,
        alineados=list(ahora),
        formacion_usada="4-4-2",
    )

    assert techo["points"] == -55, techo

    # Y AHORA EL MOTOR ENTERO: con las dos fotos al reves, la
    # jornada sale sin medir y el -55 no aparece por ningun lado.
    with ledger_temporal() as libro:

        _escribir(
            libro,
            [
                _jornada(4899, {str(100 + i): 2 for i in range(16)}),
                _jornada(4903, {str(100 + i): 30 for i in range(16)}),
                _jornada(4904, {str(100 + i): 25 for i in range(16)}),
                _jornada(5125, {str(100 + i): 40 for i in range(16)}),
            ],
        )

        # Un calendario que pone 4904 DESPUES de 4903, que es
        # justo lo que hacia el orden por id.
        al_reves = _calendario()

        al_reves[4904] = {
            **al_reves[4904],
            "primer_partido": "2026-09-14T19:00:00+00:00",
        }

        datos = M.marcador(al_reves)

    filas = {f["round_id"]: f for f in datos["jornadas"]}

    assert filas, "el marcador no devolvio ninguna jornada"

    sexta = filas[4904]

    assert not sexta["medible"], sexta

    assert sexta.get("motivo"), sexta

    # NINGUNA JORNADA PUBLICA UN TECHO NEGATIVO. Es el invariante
    # dicho en la forma en que se veia el fallo.
    for fila in datos["jornadas"]:

        techo_publicado = fila.get("mejor_puntos")

        assert (
            techo_publicado is None or techo_publicado >= 0
        ), (
            f"la jornada {fila['round_id']} publica un mejor "
            f"once de {techo_publicado} puntos, que no existe"
        )
