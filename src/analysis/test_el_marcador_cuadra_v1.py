"""
El marcador cuadra con Biwenger: cada ronda, con el once que la jugo.

EL SINTOMA (28/10/2026)

    `marcador.json` llevaba nueve jornadas cerradas y medibles y
    CERO fiables: `eficiencia_media: null`. En la J10 el once del
    cuaderno sumaba 49 y Biwenger le pago 39 a Pepe. La bitacora
    del 24/10: «guarda mi_once desplazado una jornada».

LA CAUSA, MEDIDA EN EL LIBRO DEL 28/10

    `observar()` guarda bajo `rounds.data.round.id`, que va un
    pitido por detras (Biwenger lo pasa en el pitido de la
    siguiente y la vuelta lo lee de la cache del reset). La ultima
    escritura de la ronda R cae la mañana DESPUES del pitido de la
    siguiente, y el once sale de `user_lineup`: con
    `lineupRoundChanges: 0`, a esa hora ya es el de la siguiente.

        entrada   su mi_once            puntos en la ronda
        4906      el de la J9 (4907)    49 en la J9  (Biwenger 49)
        4907      el de la J6 parte 3   56 en la J9  (Biwenger 49)
        5176      el de la J10 (4908)   39 en la J10 (Biwenger 39)
        4908      el de la J11          no jugo la J10

    Y el 49 del cuaderno en la J10 es otra cosa: el once era el
    bueno, pero su ventana (cierre J9 -> cierre J10) lleva dentro
    la J6 aplazada del 21-22/10, donde Unai Lopez y Olasagasti
    hicieron 5 cada uno. 49 = 39 + 10.

LO QUE VIGILAN ESTAS GUARDIAS

    1. El libro, tal cual, reproduce el desplazamiento.
    2. El tablon da lo que pago cada ronda; en una partida, la
       resta del acumulado.
    3. Cada ronda lleva el once que la jugo, no el de su entrada.
    4. El marcador cuadra en la J9 y la J10 y dice por que no en
       las demas.
    5. Una ronda sin `roundFinished` no cuadra ni descuadra.
    6. La ventana con una aplazada dentro no es una nota.
    7. La escritura: bajo la ronda en juego, once bloqueado al
       pitido, y la ronda anterior no se ensucia.
    8. Un once grabado tras el pitido no es el bloqueado.

REGLA 23, DOCTRINA 24

    Todo entra por la puerta: el libro se escribe en un directorio
    temporal y se aparta el real; el tablon, los onces y las fotos
    de cierre son copias recortadas de los de produccion. Ninguna
    depende de un `BORDALAS_*` ni del reloj: las horas llevan su
    zona escrita.
"""

from __future__ import annotations

import copy
import json
import tempfile

from datetime import datetime, timezone
from pathlib import Path

from src.analysis import marcador as M


PEPE = 14175949
MANZAGOOL = 14176382


# ============================================================
# EL TABLON (recortado: Pepe y un rival)
# ============================================================


def _ronda(tipo, fecha, round_id, nombre, part=None, resultados=None):

    ronda = {"id": round_id, "name": nombre}

    if part is not None:
        ronda["part"] = part

    contenido = {"round": ronda}

    if resultados is not None:
        contenido["results"] = [
            {"user": {"id": user_id}, "points": puntos}
            for user_id, puntos in resultados.items()
        ]

    return {"type": tipo, "date": fecha, "content": contenido}


EVENTOS = [
    _ronda("roundStarted", 1789491600, 5125, "Jornada 6 (aplazada)", 2),
    _ronda("roundFinished", 1789720501, 5125, "Jornada 6 (aplazada)", 2,
           {MANZAGOOL: 49, PEPE: 29}),
    _ronda("roundStarted", 1791572400, 4906, "Jornada 8"),
    # La J8 no tiene `roundFinished`: nadie la cobro.
    _ronda("roundStarted", 1792177200, 4907, "Jornada 9"),
    _ronda("roundFinished", 1792508749, 4907, "Jornada 9", None,
           {MANZAGOOL: 52, PEPE: 49}),
    _ronda("roundStarted", 1792605600, 5176, "Jornada 6 (aplazada)", 3),
    # Acumulado de la J6: 29 de la parte 2 + 11 de esta.
    _ronda("roundFinished", 1792681402, 5176, "Jornada 6 (aplazada)", 3,
           {MANZAGOOL: 52, PEPE: 40}),
    _ronda("roundStarted", 1792782000, 4908, "Jornada 10"),
    _ronda("roundFinished", 1793117171, 4908, "Jornada 10", None,
           {MANZAGOOL: 57, PEPE: 39}),
]

# La J11, para la escritura: pita el 30/10 a las 21:00 de Madrid.
PITIDO_J11 = 1793390400
J11 = 4909

EVENTOS_CON_J11 = EVENTOS + [
    _ronda("roundStarted", PITIDO_J11, J11, "Jornada 11"),
]


def _calendario(eventos) -> dict:
    """Lo que da `calendario_de_jornadas` con el tablon encendido,
    escrito a mano para no depender del interruptor."""

    salida = {}

    for round_id, fila in M.cierres_del_tablon(eventos).items():
        salida[round_id] = {
            "round_id": round_id,
            "nombre": fila["nombre"],
            "part": fila["part"],
            "primer_partido": fila["empieza"].isoformat(),
            "fuente": "EVENTOS_DEL_TABLON",
        }

    return salida


# ============================================================
# EL LIBRO DEL 28/10 (las cuatro ultimas entradas)
# ============================================================

ONCE_J9 = [38433, 1760, 1599, 5678, 19862, 29661, 14800, 1969, 26271, 35678, 25777]
ONCE_J6_P3 = [38433, 1760, 1599, 30493, 19862, 29661, 14800, 1969, 26271, 35678, 25777]
ONCE_J10 = [38433, 1760, 1844, 1599, 30493, 29661, 14800, 1969, 26271, 35678, 12494]
ONCE_J11 = [38433, 1760, 28115, 1844, 30493, 29661, 14800, 1969, 26271, 35678, 12494]

NOMBRES = {
    "1599": "Jonny", "1760": "Chust", "1844": "Gayà", "1969": "Unai López",
    "5678": "Diego Rico", "12494": "Boyé", "14800": "Pablo Ibáñez",
    "19862": "Expósito", "25777": "Luismi Cruz", "26271": "Yamal",
    "28115": "Kike Salas", "29661": "Olasagasti", "30493": "Sergi Cardona",
    "35678": "Roberto Fernández", "38433": "Gulácsi",
}

POSICION = {
    1599: 2, 1760: 2, 1844: 2, 1969: 3, 5678: 2, 12494: 4, 14800: 3,
    19862: 3, 25777: 4, 26271: 4, 28115: 2, 29661: 3, 30493: 2,
    35678: 4, 38433: 1,
}


def _entrada(round_id, datos_de, escrito_en, formacion, once, totales,
             pepe, manzagool):

    return {
        "round_id": round_id,
        "visto": escrito_en,
        "datos_de": datos_de,
        "escrito_en": escrito_en,
        "clasificacion": [
            {"user_id": PEPE, "name": "Pepe Bordalás", "points": pepe},
            {"user_id": MANZAGOOL, "name": "Manzagool", "points": manzagool},
        ],
        "mi_user_id": PEPE,
        "mi_once": {"formation": formacion, "players": list(once)},
        "plantilla": [
            {"id": int(pid), "name": NOMBRES[pid], "position": POSICION[int(pid)]}
            for pid in totales
        ],
        "totales": dict(totales),
        "once_alternativo": None,
        "nombres": {pid: NOMBRES[pid] for pid in totales},
    }


LIBRO = {
    "version": 1,
    "updated_at": "2026-10-28T20:10:59.812854",
    "jornadas": {
        "4906": _entrada(
            4906, "2026-10-17T04:52:54.535594+00:00", "2026-10-17T04:53:00.995006",
            "3-4-3", ONCE_J9,
            {"1599": 25, "1760": 29, "1969": 29, "5678": 6, "14800": 36,
             "19862": 39, "25777": 40, "26271": 94, "29661": 39, "35678": 62,
             "38433": 22},
            323, 253,
        ),
        "4907": _entrada(
            4907, "2026-10-22T04:56:54.780662+00:00", "2026-10-22T04:57:10.652538",
            "3-4-3", ONCE_J6_P3,
            {"1599": 27, "1760": 37, "1969": 34, "14800": 40, "19862": 42,
             "25777": 42, "26271": 109, "29661": 42, "30493": 14, "35678": 64,
             "38433": 26},
            372, 305,
        ),
        "5176": _entrada(
            5176, "2026-10-24T04:52:49.636461+00:00", "2026-10-24T04:53:10.731537",
            "4-3-3", ONCE_J10,
            {"1599": 27, "1760": 37, "1844": 23, "1969": 34, "12494": 58,
             "14800": 40, "26271": 109, "29661": 47, "30493": 14, "35678": 64,
             "38433": 26},
            383, 308,
        ),
        "4908": _entrada(
            4908, "2026-10-28T20:10:24.313845+00:00", "2026-10-28T20:10:59.812854",
            "4-3-3", ONCE_J11,
            {"1760": 41, "1844": 27, "1969": 39, "12494": 61, "14800": 44,
             "26271": 112, "28115": 35, "29661": 50, "30493": 22, "35678": 66,
             "38433": 29},
            422, 365,
        ),
    },
}


# Las fotos de cierre de LaLiga (`puntos_por_jornada.jsonl`), con
# los quince que aparecen: {id: [puntos, jugados]}.
FOTOS_DE_CIERRE = [
    {"jornada": 8, "cerrada_en": "2026-10-12T23:00:00+02:00", "players": {
        "1599": [25, 7], "1760": [29, 8], "1844": [20, 6], "1969": [29, 7],
        "5678": [6, 2], "12494": [52, 7], "14800": [36, 8], "19862": [39, 8],
        "25777": [40, 8], "26271": [94, 8], "28115": [19, 5], "29661": [33, 6],
        "30493": [7, 4], "35678": [62, 8], "38433": [22, 4]}},
    {"jornada": 9, "cerrada_en": "2026-10-19T23:00:00+02:00", "players": {
        "1599": [27, 8], "1760": [37, 9], "1844": [23, 7], "1969": [29, 7],
        "5678": [6, 2], "12494": [58, 8], "14800": [40, 9], "19862": [42, 9],
        "25777": [42, 9], "26271": [109, 9], "28115": [28, 7], "29661": [42, 8],
        "30493": [14, 5], "35678": [64, 9], "38433": [26, 5]}},
    {"jornada": 10, "cerrada_en": "2026-10-26T23:00:00+01:00", "players": {
        "1599": [27, 8], "1760": [41, 10], "1844": [27, 8], "1969": [39, 9],
        "5678": [6, 2], "12494": [61, 9], "14800": [44, 10], "19862": [55, 10],
        "25777": [44, 10], "26271": [112, 10], "28115": [28, 7], "29661": [50, 10],
        "30493": [22, 6], "35678": [66, 10], "38433": [29, 6]}},
]

# El libro de onces congelados antes del pitido. Su `round_id` va
# tan retrasado como el del marcador: manda `matchday`.
ONCES_CONGELADOS = [
    {"round_id": 4906, "matchday": 9, "formation": "3-4-3",
     "players": list(ONCE_J9),
     "anotado_en": "2026-10-16T18:09:23.064495+00:00",
     "guardado_en": "2026-10-14T05:18:04+00:00"},
    {"round_id": 5176, "matchday": 10, "formation": "4-3-3",
     "players": list(ONCE_J10),
     "anotado_en": "2026-10-23T18:09:54.168263+00:00",
     "guardado_en": "2026-10-23T06:10:29+00:00"},
]


class libro_temporal:
    """Aparta el libro real y deja en su sitio el que se le de."""

    def __init__(self, libro=None):
        self._libro = libro

    def __enter__(self):
        self._directorio = tempfile.TemporaryDirectory()
        self._state, self._file = M.STATE_DIRECTORY, M.LEDGER_FILE

        M.STATE_DIRECTORY = Path(self._directorio.name)
        M.LEDGER_FILE = M.STATE_DIRECTORY / "marcador.json"

        if self._libro is not None:
            M.LEDGER_FILE.write_text(
                json.dumps(self._libro, ensure_ascii=False),
                encoding="utf-8",
            )

        return M.LEDGER_FILE

    def __exit__(self, *_):
        M.STATE_DIRECTORY, M.LEDGER_FILE = self._state, self._file
        self._directorio.cleanup()


def _marcador(libro=None, eventos=EVENTOS, **extra):

    with libro_temporal(copy.deepcopy(libro or LIBRO)):
        return M.marcador(
            _calendario(eventos),
            eventos=eventos,
            onces_congelados=extra.get("onces", ONCES_CONGELADOS),
            fotos_de_cierre=extra.get("fotos", FOTOS_DE_CIERRE),
        )


def _filas(salida) -> dict:
    return {f["round_id"]: f for f in salida["jornadas"]}


def _suma(previa, actual, once) -> int:
    fotos = {f["jornada"]: f["players"] for f in FOTOS_DE_CIERRE}
    return sum(
        fotos[actual][str(p)][0] - fotos[previa][str(p)][0]
        for p in once
    )


# ============================================================
# 1. EL LIBRO REPRODUCE EL DESPLAZAMIENTO
# ============================================================


def test_el_libro_guarda_el_once_de_la_siguiente() -> None:
    """
    Sin el arreglo, la entrada de cada ronda guarda el once de la
    que va despues. Se mide contra el libro de onces congelados
    antes del pitido y contra lo que pago Biwenger.
    """

    jornadas = LIBRO["jornadas"]
    congelado = {o["matchday"]: o["players"] for o in ONCES_CONGELADOS}

    # La entrada 4906 (J8) guarda el once congelado de la J9...
    assert jornadas["4906"]["mi_once"]["players"] == congelado[9]

    # ...y la 5176 (J6 parte 3) el de la J10.
    assert jornadas["5176"]["mi_once"]["players"] == congelado[10]

    # Con los puntos de la J9: el once de SU entrada (4907) no da
    # lo que pago Biwenger; el de la entrada anterior, si.
    assert _suma(8, 9, jornadas["4907"]["mi_once"]["players"]) == 56
    assert _suma(8, 9, jornadas["4906"]["mi_once"]["players"]) == 49

    pagado = M.cierres_del_tablon(EVENTOS)[4907]["puntos"][PEPE]

    assert pagado == 49, pagado


# ============================================================
# 2. LO QUE PAGO CADA RONDA, DEL TABLON
# ============================================================


def test_el_tablon_da_lo_que_pago_cada_ronda() -> None:

    cierres = M.cierres_del_tablon(EVENTOS)

    assert cierres[4907]["puntos"][PEPE] == 49, cierres[4907]
    assert cierres[4908]["puntos"][PEPE] == 39, cierres[4908]

    # LA PARTE 3 DE LA J6: el tablon da el acumulado de la jornada
    # (40) y la ronda vale la resta contra la parte 2 (29).
    assert cierres[5176]["acumulado"][PEPE] == 40, cierres[5176]
    assert cierres[5176]["puntos"][PEPE] == 11, cierres[5176]
    assert cierres[5176]["puntos"][MANZAGOOL] == 3, cierres[5176]

    # La J8 empezo y nunca cerro: sin `roundFinished` no hay pago.
    assert cierres[4906]["empieza"] is not None, cierres[4906]
    assert cierres[4906]["termina"] is None, cierres[4906]
    assert cierres[4906]["puntos"] is None, cierres[4906]

    # Y con basura no lanza.
    assert M.cierres_del_tablon([None, 3, {"type": "roundStarted"}]) == {}


# ============================================================
# 3. CADA RONDA, CON EL ONCE QUE LA JUGO
# ============================================================


def test_cada_ronda_lleva_el_once_que_jugo() -> None:

    onces = M.el_once_de_cada_ronda(
        list(LIBRO["jornadas"].values()),
        calendario=_calendario(EVENTOS),
        cierres=M.cierres_del_tablon(EVENTOS),
        congelados=ONCES_CONGELADOS,
    )

    # La J9 (4907) jugo con el once que se vio en la entrada 4906.
    assert onces[4907]["players"] == ONCE_J9, onces[4907]
    assert onces[4907]["de_la_entrada"] == 4906, onces[4907]
    assert onces[4907]["fuente"] == M.ONCE_VISTO_EN_OTRA_ENTRADA
    assert onces[4907]["congelado_coincide"] is True, onces[4907]

    # La J10 (4908), con el de la entrada 5176.
    assert onces[4908]["players"] == ONCE_J10, onces[4908]
    assert onces[4908]["de_la_entrada"] == 5176, onces[4908]
    assert onces[4908]["congelado_coincide"] is True, onces[4908]

    # La J6 parte 3 (5176), con el que se vio en la 4907.
    assert onces[5176]["players"] == ONCE_J6_P3, onces[5176]

    # El once que hoy guarda la 4908 es el de la J11: la J10 ya
    # habia cerrado cuando se vio, y no se le asigna a nadie.
    assert all(
        o["players"] != ONCE_J11 for o in onces.values()
    ), onces


# ============================================================
# 4. EL MARCADOR CUADRA, Y DICE POR QUE NO CUANDO NO
# ============================================================


def test_el_marcador_cuadra_con_biwenger() -> None:

    salida = _marcador()
    filas = _filas(salida)

    j9, j10, j6p3 = filas[4907], filas[4908], filas[5176]

    # LA J9: el once bueno, los puntos del cierre de LaLiga.
    assert j9["medible"] is True, j9
    assert j9["once"] == ONCE_J9, j9
    assert j9["once_desplazado"] is True, j9
    assert j9["puntos_fuente"] == M.PUNTOS_DEL_CIERRE, j9
    assert j9["puntos_once"] == 49, j9
    assert j9["puntos_biwenger"] == 49, j9
    assert j9["puntos_biwenger_fuente"] == M.VERDAD_DEL_TABLON, j9
    assert j9["cuadra"] is True, j9

    # LA J10: era «en curso» por ser la ultima del libro; el
    # tablon dice que cerro. Su ventana de cierre lleva la J6
    # aplazada dentro, asi que va por la resta de observaciones,
    # y Jonny (vendido) no jugo: cero cierto.
    assert j10["medible"] is True, j10
    assert j10["once"] == ONCE_J10, j10
    assert j10["puntos_fuente"] == M.PUNTOS_DE_LA_RESTA, j10
    assert "5176" in str(j10["puntos_cierre_motivo"]), j10
    assert j10["sin_partido"] == [1599], j10
    assert j10["puntos_once"] == 39, j10
    assert j10["puntos_biwenger"] == 39, j10
    assert j10["cuadra"] is True, j10

    # LA J6 PARTE 3: excepcion escrita, y sin cuadre falso. Dos
    # del once se vendieron antes de la foto.
    assert j6p3["puntos_biwenger"] == 11, j6p3
    assert j6p3["cuadra"] is None, j6p3
    assert "aplazada" in (j6p3["excepcion"] or ""), j6p3
    assert j6p3["cuadra_motivo"], j6p3

    resumen = salida["resumen"]

    assert resumen["jornadas_fiables"] == 2, resumen
    assert resumen["eficiencia_media"] is not None, resumen
    assert resumen["verdad"] == M.VERDAD_DEL_TABLON, resumen
    assert resumen["jornadas_con_once_desplazado"] >= 3, resumen

    # LA LIGA, RONDA A RONDA: J9 49 contra 52, J10 39 contra 57.
    assert j9["media_rivales"] == 52, j9
    assert j10["diferencia_liga"] == -18, j10


# ============================================================
# 5. SIN CIERRE EN EL TABLON NO HAY CUADRE
# ============================================================


def test_sin_cierre_en_el_tablon_no_hay_cuadre() -> None:

    sin_j9 = [
        e for e in EVENTOS
        if not (
            e["type"] == "roundFinished"
            and e["content"]["round"]["id"] == 4907
        )
    ]

    j9 = _filas(_marcador(eventos=sin_j9))[4907]

    assert j9["medible"] is True, j9
    assert j9["puntos_biwenger"] is None, j9
    assert j9["cuadra"] is None, j9
    assert "roundFinished" in (j9["cuadra_motivo"] or ""), j9
    assert j9["diferencia_liga"] is None, j9


# ============================================================
# 6. UNA VENTANA CON OTRA RONDA DENTRO NO ES UNA NOTA
# ============================================================


def test_la_ventana_con_una_aplazada_dentro_no_es_nota() -> None:

    from src.analysis.el_cuaderno import el_cuaderno

    pitidos = M._pitidos(_calendario(EVENTOS), M.cierres_del_tablon(EVENTOS))
    nombres = M._nombres_de_ronda(_calendario(EVENTOS), M.cierres_del_tablon(EVENTOS))

    limpia = M.puntos_de_cierre(FOTOS_DE_CIERRE, 4907, pitidos, nombres)
    sucia = M.puntos_de_cierre(FOTOS_DE_CIERRE, 4908, pitidos, nombres)

    assert limpia["limpia"] is True, limpia
    assert sucia["limpia"] is False, sucia
    assert "5176" in sucia["motivo"], sucia

    # Sin el tablon, el cuaderno de siempre: 49 en la J10.
    viejo = {
        n["jornada"]: n
        for n in el_cuaderno(FOTOS_DE_CIERRE, ONCES_CONGELADOS)["jornadas"]
    }

    assert viejo[10]["puntos_once"] == 49, viejo[10]

    # Con el tablon: la J10 no es nota (49 = 39 + 10 de la J6
    # aplazada) y la J9 cuadra.
    cuaderno = el_cuaderno(
        FOTOS_DE_CIERRE, ONCES_CONGELADOS,
        eventos=EVENTOS, mi_user_id=PEPE,
    )

    notas = {n["jornada"]: n for n in cuaderno["jornadas"]}

    assert notas[10]["medible"] is False, notas[10]
    assert notas[10]["puntos_once"] is None, notas[10]
    assert notas[10]["puntos_mezclados"] == 49, notas[10]
    assert notas[10]["puntos_biwenger"] == 39, notas[10]
    assert "5176" in notas[10]["motivo"], notas[10]

    assert notas[9]["medible"] is True, notas[9]
    assert notas[9]["puntos_once"] == 49, notas[9]
    assert notas[9]["cuadra"] is True, notas[9]


# ============================================================
# 7. LA ESCRITURA: BAJO LA RONDA EN JUEGO, ONCE BLOQUEADO
# ============================================================


def _foto(cuando, round_id, once, guardado, totales):

    return {
        "timestamp": cuando,
        "rounds": {"data": {
            "round": {"id": round_id},
            "league": {"standings": [
                {"id": PEPE, "name": "Pepe Bordalás", "points": 422},
                {"id": MANZAGOOL, "name": "Manzagool", "points": 365},
            ]},
        }},
        "user_lineup": {"data": {"lineup": {
            "type": "4-3-3",
            "date": guardado,
            "players": [{"id": p, "name": NOMBRES[str(p)]} for p in once],
        }}},
        "my_team": [
            {"id": int(pid), "name": NOMBRES[pid],
             "position": POSICION[int(pid)], "points": puntos}
            for pid, puntos in totales.items()
        ],
        "catalog": {"data": {"players": {}}},
    }


def _libro_de_la_j10() -> dict:
    """El libro del 28/10 sin las entradas de antes de la J6 p3."""

    libro = copy.deepcopy(LIBRO)

    for vieja in ("4906", "4907"):
        libro["jornadas"].pop(vieja)

    return libro


TOTALES_J10 = dict(LIBRO["jornadas"]["4908"]["totales"])

# Grabado el 29/10, antes del pitido de la J11.
GUARDADO_ANTES = int(datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc).timestamp())

# Grabado el 31/10, con la J11 ya empezada: es para la J12.
GUARDADO_DESPUES = int(datetime(2026, 10, 31, 6, 0, tzinfo=timezone.utc).timestamp())

ONCE_J12 = [38433, 1760, 1844, 30493, 12494, 29661, 14800, 1969, 26271, 35678, 28115]


def test_la_foto_se_anota_bajo_la_ronda_en_juego() -> None:

    with libro_temporal(_libro_de_la_j10()):

        # A. 30/10 20:10 en Madrid: la J11 no ha pitado. Va a la
        # 4908, que es una entrada de antes y se escribe como
        # siempre.
        a = M.observar(
            _foto("2026-10-30T20:10:00+01:00", 4908, ONCE_J11,
                  GUARDADO_ANTES, TOTALES_J10),
            current_user_id=PEPE,
            eventos=EVENTOS_CON_J11,
        )

        assert a["round_id"] == 4908, a

        libro = M.cargar_ledger()["jornadas"]

        assert str(J11) not in libro, libro.keys()
        assert "escritura" not in libro["4908"], libro["4908"]

        # B. 21:10: la J11 ya pito y `round.id` sigue en 4908 (la
        # cache). Se anota bajo la J11, con su once bloqueado.
        en_juego = {**TOTALES_J10, "26271": 115}

        b = M.observar(
            _foto("2026-10-30T21:10:00+01:00", 4908, ONCE_J11,
                  GUARDADO_ANTES, en_juego),
            current_user_id=PEPE,
            eventos=EVENTOS_CON_J11,
        )

        assert b["round_id"] == J11, b
        assert b["clave"] == M.CLAVE_RONDA_EN_JUEGO, b
        assert b["once_bloqueado"] is True, b

        libro = M.cargar_ledger()["jornadas"]
        nueva = libro[str(J11)]

        assert nueva["escritura"] == M.ESCRITURA_POR_LA_RONDA_EN_JUEGO, nueva
        assert nueva["ronda_de_biwenger"] == 4908, nueva
        assert nueva["mi_once"]["players"] == ONCE_J11, nueva
        assert nueva["mi_once"]["regla"] == M.REGLA_PRIMERA_VISTA, nueva

        # La J10 NO se ensucia con el primer partido de la J11.
        assert libro["4908"]["totales"] == TOTALES_J10, libro["4908"]

        M.anotar_once_alternativo(J11, {"formation": "4-3-3", "players": ONCE_J11})

        # C. 31/10 06:52: el dueño ya toco el once para la J12 y
        # la cache sigue diciendo 4908. El de la J11 no se toca.
        c = M.observar(
            _foto("2026-10-31T06:52:00+01:00", 4908, ONCE_J12,
                  GUARDADO_DESPUES, {**en_juego, "26271": 118}),
            current_user_id=PEPE,
            eventos=EVENTOS_CON_J11,
        )

        assert c["round_id"] == J11, c

        tarde = M.anotar_once_alternativo(
            J11, {"formation": "4-3-3", "players": ONCE_J12}
        )

        assert tarde["anotado"] is False, tarde

        # D. Sin tablon (se cayo) y con la cache ya en la J11.
        M.observar(
            _foto("2026-10-31T07:52:00+01:00", J11, ONCE_J12,
                  GUARDADO_DESPUES, {**en_juego, "26271": 118}),
            current_user_id=PEPE,
        )

        libro = M.cargar_ledger()["jornadas"]

        assert libro[str(J11)]["mi_once"]["players"] == ONCE_J11, libro[str(J11)]

        # El que hay puesto ahora no se pierde: va aparte.
        assert libro[str(J11)]["once_editable"]["players"] == ONCE_J12

        assert libro[str(J11)]["totales"]["26271"] == 118, libro[str(J11)]
        assert libro[str(J11)]["once_alternativo"]["players"] == ONCE_J11
        assert libro["4908"]["totales"] == TOTALES_J10, libro["4908"]

        salida = M.marcador(
            _calendario(EVENTOS_CON_J11),
            eventos=EVENTOS_CON_J11,
            onces_congelados=ONCES_CONGELADOS,
            fotos_de_cierre=FOTOS_DE_CIERRE,
        )

    filas = _filas(salida)

    # La J10 sigue cuadrando con su once, y la J11 esta en curso.
    assert filas[4908]["once"] == ONCE_J10, filas[4908]
    assert filas[4908]["cuadra"] is True, filas[4908]
    assert filas[J11]["medible"] is False, filas[J11]
    assert "en curso" in filas[J11]["motivo"], filas[J11]


# ============================================================
# 8. UN ONCE GRABADO TRAS EL PITIDO NO ES EL BLOQUEADO
# ============================================================


def test_un_once_grabado_tras_el_pitido_no_es_el_bloqueado() -> None:

    libro = _libro_de_la_j10()

    libro["jornadas"][str(J11)] = {
        **copy.deepcopy(libro["jornadas"]["4908"]),
        "round_id": J11,
        "escritura": M.ESCRITURA_POR_LA_RONDA_EN_JUEGO,
        "datos_de": "2026-10-31T06:52:00+01:00",
        "escrito_en": "2026-10-31T06:52:30",
        "mi_once": {
            "formation": "4-3-3",
            "players": list(ONCE_J12),
            "guardado": datetime.fromtimestamp(
                GUARDADO_DESPUES, timezone.utc
            ).isoformat(),
            "regla": M.REGLA_PRIMERA_VISTA,
            "visto_en": "2026-10-31T06:52:00+01:00",
        },
    }

    onces = M.el_once_de_cada_ronda(
        list(libro["jornadas"].values()),
        calendario=_calendario(EVENTOS_CON_J11),
        cierres=M.cierres_del_tablon(EVENTOS_CON_J11),
    )

    assert J11 not in onces, onces[J11]

    # Con el congelado de la J11 delante, es ese el que vale.
    congelado = {
        "round_id": 4908, "matchday": 11, "formation": "4-3-3",
        "players": list(ONCE_J11),
        "anotado_en": "2026-10-30T19:09:00+00:00",
        "guardado_en": "2026-10-29T09:00:00+00:00",
    }

    onces = M.el_once_de_cada_ronda(
        list(libro["jornadas"].values()),
        calendario=_calendario(EVENTOS_CON_J11),
        cierres=M.cierres_del_tablon(EVENTOS_CON_J11),
        congelados=[congelado],
    )

    assert onces[J11]["players"] == ONCE_J11, onces[J11]
    assert onces[J11]["fuente"] == M.ONCE_CONGELADO, onces[J11]


TESTS = [
    test_el_libro_guarda_el_once_de_la_siguiente,
    test_el_tablon_da_lo_que_pago_cada_ronda,
    test_cada_ronda_lleva_el_once_que_jugo,
    test_el_marcador_cuadra_con_biwenger,
    test_sin_cierre_en_el_tablon_no_hay_cuadre,
    test_la_ventana_con_una_aplazada_dentro_no_es_nota,
    test_la_foto_se_anota_bajo_la_ronda_en_juego,
    test_un_once_grabado_tras_el_pitido_no_es_el_bloqueado,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL MARCADOR CUADRA V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
