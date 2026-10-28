"""
La clasificacion que se pinta es la de Biwenger.

SINTOMA (28/10/2026, noche)

    `status.json` de las 20:11 (run 40751392431), con la J10 ya
    cerrada. Tres cuadros de la pantalla decian:

        losRivales / league_center.fantasy_standings /
        rival_intelligence.managers

            Pepe 383 y TERCERO · Manzagool 308 · Mex 246

    Y Biwenger, en la misma foto (`competition.standings`):

            Pepe 422 y SEGUNDO · Manzagool 365 · Mex 324

    Y el valor de plantilla de Pollo17 en la clasificacion,
    105,74 M, seguia contando a Kubo (vendido el 28/10): su
    plantilla de ahora suma 102,29 M.

LA CAUSA

    Los puntos salian del PERFIL de cada manager, que solo se
    vuelve a pedir cuando ese manager ficha o vende. Cerrar una
    jornada no es un movimiento del tablon. El valor salia de
    `rounds/league`, cacheado desde el reset.

LO QUE SE COMPRUEBA

    Con los numeros de esa foto: puntos y puesto de Biwenger, con
    su hora; valor, la plantilla sumada; sin Biwenger, el perfil y
    se dice; y el libro de rivales que leen los motores, intacto.

REGLA 23

    No lee `data/`, ni la red, ni el reloj: todo entra por
    argumento. El tablero de FutbolFantasy que `squads` miraria se
    sustituye por uno vacio.
"""

from __future__ import annotations

import copy
from pathlib import Path
from unittest.mock import patch


RAIZ = Path(__file__).resolve().parents[2]


NOSOTROS = 14175949
POLLO = 14145555
MANZAGOOL = 14176382
MEX = 14178736

LA_HORA_DE_LA_CLASIFICACION = 1793167272     # 28/10/2026 06:01:12 UTC
LA_HORA_DE_LOS_PERFILES = 1792611000         # 21/10/2026 19:30:00 UTC


# ============================================================
# LA FOTO DEL 28/10, 20:11
# ============================================================


# LO QUE DECIA BIWENGER: `rounds.data.league.standings`, crudo.
CLASIFICACION_CRUDA = [
    {"id": POLLO, "name": "Pollo17", "position": 1, "points": 432,
     "teamValue": 105_740_000, "teamValueInc": 710_000,
     "icon": "icons/13.png"},
    {"id": NOSOTROS, "name": "Pepe Bordalás", "position": 2,
     "points": 422, "teamValue": 58_010_000, "teamValueInc": -60_000,
     "icon": "i/u/14175949.png"},
    {"id": 14156489, "name": "Luismi_Haz", "position": 3,
     "points": 388, "teamValue": 110_960_000, "teamValueInc": 10_000,
     "icon": "icons/11.png"},
    {"id": MANZAGOOL, "name": "Manzagool", "position": 4,
     "points": 365, "teamValue": 65_040_000, "teamValueInc": 310_000,
     "icon": None},
    {"id": 14151726, "name": "DiosMande a Rodri al Palancas",
     "position": 5, "points": 340, "teamValue": 46_550_000,
     "teamValueInc": -50_000, "icon": "i/u/14151726.png"},
    {"id": 14154203, "name": "Prinzipote", "position": 6,
     "points": 338, "teamValue": 52_420_000, "teamValueInc": -90_000,
     "icon": None},
    {"id": MEX, "name": "Mex", "position": 7, "points": 324,
     "teamValue": 48_960_000, "teamValueInc": 240_000, "icon": None},
    {"id": 14456960, "name": "Alvaro Retamosa Sanguino",
     "position": 8, "points": 282, "teamValue": 30_810_000,
     "teamValueInc": -50_000, "icon": None},
]


def _manager(uid, nombre, puntos, saldo, valor, fichas, *, us=False):
    """Una fila de `rival_intelligence.managers`, con los puntos del
    PERFIL, que es lo que el libro tiene."""

    return {
        "user_id": uid,
        "name": nombre,
        "points": puntos,
        "points_rank": None,
        "balance": saldo,
        "roster_count": fichas,
        "roster_value": valor,
        "roster_price_increment": 100_000,
        "net_worth": saldo + valor,
        "maximum_bid": 1_000_000,
        "threat_level": "US" if us else "HIGH",
        "roster": [],
    }


# LO QUE DECIA EL LIBRO DE RIVALES: los puntos del perfil cacheado.
# Pollo17 se movio (vendio a Kubo) y su perfil se refresco: 432 bien.
# Los demas no: puntos de la J9.
MANAGERS = [
    _manager(POLLO, "Pollo17", 432, 12_801_251, 102_290_000, 18),
    _manager(14156489, "Luismi_Haz", 388, -13_546_918,
             110_960_000, 23),
    _manager(NOSOTROS, "Pepe Bordalás", 383, 1_418_975,
             58_010_000, 11, us=True),
    _manager(MANZAGOOL, "Manzagool", 308, 1_706_111, 65_040_000, 13),
    _manager(14154203, "Prinzipote", 299, 3_334_772, 52_420_000, 20),
    _manager(14151726, "DiosMande a Rodri al Palancas", 281,
             3_115_475, 46_550_000, 12),
    _manager(MEX, "Mex", 246, 3_400_800, 48_960_000, 16),
    _manager(14456960, "Alvaro Retamosa Sanguino", 198, 17_725_200,
             30_810_000, 14),
]

PERFILES = [
    {"id": m["user_id"], "points": m["points"],
     "_fetched_at": LA_HORA_DE_LOS_PERFILES}
    for m in MANAGERS
]


def _foto(**cambios) -> dict:
    foto = {
        "timestamp": "2026-10-28T20:10:24",
        "rounds_as_of": LA_HORA_DE_LA_CLASIFICACION,
        "rounds": {"data": {"league": {
            "id": 2165477,
            "name": "El chiringuito",
            "standings": copy.deepcopy(CLASIFICACION_CRUDA),
        }}},
    }
    foto.update(cambios)
    return foto


def _competition(foto=None) -> dict:
    from src.telemetry.dashboard_state import (
        compact_biwenger_competition,
    )
    from src.telemetry.la_clasificacion_de_biwenger import (
        con_el_valor_de_las_plantillas,
    )

    return con_el_valor_de_las_plantillas(
        compact_biwenger_competition(
            snapshot=foto if foto is not None else _foto(),
            current_user_id=NOSOTROS,
        ),
        MANAGERS,
    )


def _tabla(competition) -> dict:
    from src.telemetry.league_center import la_tabla_de_la_liga

    return la_tabla_de_la_liga(
        rival_intelligence={"managers": copy.deepcopy(MANAGERS)},
        profiles=copy.deepcopy(PERFILES),
        events=[],
        competition=competition,
    )


def _fila(filas, uid) -> dict:
    for fila in filas:
        if fila.get("user_id") == uid:
            return fila

    raise AssertionError(f"no esta {uid} en {filas}")


# ============================================================
# 1. LOS PUNTOS Y EL PUESTO, DE BIWENGER
# ============================================================


def test_la_tabla_lleva_los_puntos_de_biwenger() -> None:
    """
    EL CASO. Con el perfil, Pepe 383 y tercero. Con Biwenger, 422
    y segundo; Manzagool 365, Mex 324.
    """

    # LO QUE SE PINTABA: ordenar por los puntos del perfil.
    antes = sorted(MANAGERS, key=lambda m: -m["points"])

    assert [m["user_id"] for m in antes].index(NOSOTROS) + 1 == 3
    assert _fila(MANAGERS, NOSOTROS)["points"] == 383

    tabla = _tabla(_competition())
    filas = tabla["filas"]

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(filas) == 8, filas

    nosotros = _fila(filas, NOSOTROS)

    assert nosotros["points"] == 422, nosotros
    assert nosotros["rank"] == 2, nosotros
    assert nosotros["is_us"] is True, nosotros
    assert nosotros["profile_points"] == 383, nosotros
    assert nosotros["points_source"] == "BIWENGER", nosotros

    assert _fila(filas, MANZAGOOL)["points"] == 365
    assert _fila(filas, MANZAGOOL)["rank"] == 4
    assert _fila(filas, MEX)["points"] == 324
    assert _fila(filas, MEX)["rank"] == 7

    # El orden de la lista es el puesto.
    assert [f["rank"] for f in filas] == list(range(1, 9)), filas


def test_la_hora_de_la_clasificacion_va_con_ella() -> None:
    """
    `rounds/league` se cachea desde el reset: la hora que vale es
    la de la peticion, no la de la foto.
    """

    competition = _competition()

    assert competition["as_of"] == "2026-10-28T06:01:12+00:00", (
        competition
    )
    assert competition["as_of_source"] == "rounds_as_of"

    tabla = _tabla(competition)

    assert tabla["fuente"]["points_source"] == "BIWENGER", tabla
    assert tabla["fuente"]["as_of"] == competition["as_of"]
    assert tabla["fuente"]["from_biwenger"] == 8
    assert tabla["fuente"]["from_profile"] == 0

    for fila in tabla["filas"]:
        assert fila["points_as_of"] == competition["as_of"], fila

    # UNA FOTO DE ANTES DEL 28/10 no trae la hora de la peticion:
    # se cae a la de la foto, y se dice que es esa.
    vieja = _foto()
    vieja.pop("rounds_as_of")

    sello = _competition(vieja)

    assert sello["as_of"] == "2026-10-28T20:10:24", sello
    assert sello["as_of_source"] == "snapshot.timestamp", sello


# ============================================================
# 2. EL VALOR, LA PLANTILLA SUMADA
# ============================================================


def test_el_valor_de_la_clasificacion_es_la_plantilla_de_ahora() -> None:
    """
    Pollo17: Biwenger 105,74 M con Kubo; su plantilla, 102,29 M.
    """

    competition = _competition()

    pollo = _fila(competition["standings"], POLLO)

    assert pollo["team_value"] == 102_290_000, pollo
    assert pollo["team_value_biwenger"] == 105_740_000, pollo
    assert pollo["team_value_source"] == "PLANTILLA_SUMADA", pollo

    # Los puntos de `competition` no se tocan: ya eran Biwenger.
    assert pollo["points"] == 432

    tabla = _tabla(competition)

    fila = _fila(tabla["filas"], POLLO)

    assert fila["roster_value"] == 102_290_000, fila
    assert fila["team_value_biwenger"] == 105_740_000, fila
    assert fila["net_worth"] == 12_801_251 + 102_290_000, fila


def test_la_ficha_del_rival_suma_lo_que_enseña() -> None:
    """
    La pagina de plantillas ponia 105,74 M encima de una lista que
    sumaba 102,29 M. Con la plantilla entera (la del ledger) manda
    la suma; Kubo esta en el catalogo pero ya no en su plantilla.
    """

    from src.telemetry import squads

    catalogo = {
        "8555": {"name": "Diomande", "price": 14_490_000,
                 "priceIncrement": 210_000, "position": 2},
        "30495": {"name": "Moleiro", "price": 10_330_000,
                  "priceIncrement": 70_000, "position": 3},
        "32440": {"name": "Cubarsí", "price": 8_060_000,
                  "priceIncrement": -70_000, "position": 2},
        "9001": {"name": "El resto", "price": 69_410_000,
                 "priceIncrement": 0, "position": 3},
        "99": {"name": "Kubo", "price": 3_450_000,
               "priceIncrement": 0, "position": 4},
    }

    foto = _foto(catalog={"data": {"players": catalogo}})

    libro = {"managers": [
        {"user_id": POLLO,
         "roster": [{"id": 8555}, {"id": 30495}, {"id": 32440},
                    {"id": 9001}]},
    ]}

    with patch.object(squads, "starter_signal", lambda _pid: {}):
        plantillas = squads.build_rival_squads(
            foto, current_user_id=NOSOTROS, rival_intelligence=libro,
        )

    pollo = _fila(plantillas["managers"], POLLO)

    assert pollo["squad_source"] == "LEDGER", pollo
    assert pollo["squad_size"] == 4, pollo
    assert pollo["team_value"] == 102_290_000, pollo
    assert pollo["team_value"] == sum(
        j["price"] for j in pollo["players"]
    )
    assert pollo["team_value_biwenger"] == 105_740_000, pollo
    assert pollo["team_value_source"] == "PLANTILLA_SUMADA", pollo
    assert pollo["team_value_inc"] == 210_000, pollo

    # SIN PLANTILLA DEL LEDGER no se suma una alineacion vacia: se
    # queda el de Biwenger, y se dice.
    nosotros = _fila(plantillas["managers"], NOSOTROS)

    assert nosotros["team_value"] == 58_010_000, nosotros
    assert nosotros["team_value_source"] == "BIWENGER", nosotros

    # Y los puntos de la ficha ya eran los de Biwenger.
    assert nosotros["points"] == 422, nosotros


# ============================================================
# 3. SIN BIWENGER, EL PERFIL, Y SE DICE
# ============================================================


def test_sin_clasificacion_cae_al_perfil_con_su_hora() -> None:
    """
    Si la foto no trae la clasificacion, se pinta la del perfil
    —no una tabla vacia— y cada fila dice de donde y de cuando.
    """

    competition = _competition(_foto(rounds={"data": {}}))

    assert competition["standings"] == [], competition

    tabla = _tabla(competition)
    filas = tabla["filas"]

    assert len(filas) == 8, filas

    nosotros = _fila(filas, NOSOTROS)

    assert nosotros["points"] == 383, nosotros
    assert nosotros["rank"] == 3, nosotros
    assert nosotros["points_source"] == "PERFIL", nosotros
    assert nosotros["points_as_of"] == "2026-10-21T19:30:00+00:00", (
        nosotros
    )

    fuente = tabla["fuente"]

    assert fuente["points_source"] == "PERFIL", fuente
    assert fuente["as_of"] is None, fuente
    assert fuente["from_profile"] == 8, fuente
    assert "PERFIL" in fuente["reason"], fuente
    assert "points_as_of" in fuente["reason"], fuente

    # Un perfil sin hora (guardado antes del 28/10) no se inventa
    # una: `None`.
    from src.telemetry.league_center import la_tabla_de_la_liga

    sin_hora = _fila(
        la_tabla_de_la_liga(
            rival_intelligence={"managers": copy.deepcopy(MANAGERS)},
            profiles=[{"id": m["user_id"]} for m in MANAGERS],
            events=[],
            competition=None,
        )["filas"],
        MEX,
    )

    assert sin_hora["points_as_of"] is None, sin_hora
    assert sin_hora["points"] == 246, sin_hora


def test_una_averia_no_deja_la_pantalla_sin_tabla() -> None:
    """
    La tabla cuelga de la generacion entera del estado. Si cruzar
    con Biwenger revienta, se pinta la del perfil y se dice por
    que; y las otras dos copias se quedan como venian.
    """

    from src.telemetry.dashboard_state import compact_rivals
    from src.telemetry.la_clasificacion_de_biwenger import (
        con_el_valor_de_las_plantillas,
        con_los_puntos_de_biwenger,
        la_tabla,
    )

    class Rota(dict):
        def get(self, *_args, **_kwargs):
            raise RuntimeError("clasificacion rota")

    rota = Rota(standings=[])

    tabla = la_tabla(
        managers=copy.deepcopy(MANAGERS),
        competition=rota,
        perfiles={},
    )

    assert len(tabla["filas"]) == 8, tabla
    assert tabla["fuente"]["points_source"] == "PERFIL", tabla
    assert "clasificacion rota" in tabla["fuente"]["reason"], tabla
    assert _fila(tabla["filas"], NOSOTROS)["points"] == 383

    compactas = compact_rivals({"managers": MANAGERS}, NOSOTROS)

    assert con_los_puntos_de_biwenger(compactas, rota) == compactas
    assert con_el_valor_de_las_plantillas(rota, MANAGERS) is rota


def test_si_biwenger_no_trae_a_uno_la_tabla_es_mixta() -> None:
    """
    Un manager que Biwenger no trae sale con su perfil y la tabla
    se cuenta por puntos. Y uno que trae Biwenger y el libro no,
    sale igual: sin el, los puestos saltarian un numero.
    """

    foto = _foto()
    crudas = foto["rounds"]["data"]["league"]["standings"]

    # Sin Mex en la clasificacion...
    foto["rounds"]["data"]["league"]["standings"] = [
        f for f in crudas if f["id"] != MEX
    ] + [
        # ...y con uno que el libro no conoce.
        {"id": 999, "name": "Nuevo", "position": 9, "points": 10,
         "teamValue": 20_000_000},
    ]

    tabla = _tabla(_competition(foto))
    filas = tabla["filas"]

    assert len(filas) == 9, filas
    assert tabla["fuente"]["points_source"] == "MIXTA", tabla
    assert _fila(filas, MEX)["points_source"] == "PERFIL"
    assert _fila(filas, MEX)["points"] == 246

    nuevo = _fila(filas, 999)

    assert nuevo["balance"] is None, nuevo
    assert nuevo["roster_value"] == 20_000_000, nuevo

    assert [f["rank"] for f in filas] == list(range(1, 10)), filas
    assert _fila(filas, NOSOTROS)["rank"] == 2


# ============================================================
# 4. LAS OTRAS DOS COPIAS DE LA PANTALLA
# ============================================================


def test_la_inteligencia_de_rivales_de_la_pantalla() -> None:
    """
    `rival_intelligence.managers` del `status.json`: puntos y
    puesto de Biwenger, y al lado los del perfil, que son con los
    que el libro calculo el abono y el tope.
    """

    from src.telemetry.dashboard_state import compact_rivals
    from src.telemetry.la_clasificacion_de_biwenger import (
        con_los_puntos_de_biwenger,
    )

    compactas = compact_rivals({"managers": MANAGERS}, NOSOTROS)
    antes = copy.deepcopy(compactas)

    filas = con_los_puntos_de_biwenger(compactas, _competition())

    # Las que llegan no se tocan.
    assert compactas == antes

    assert len(filas) == 8, filas

    nosotros = _fila(filas, NOSOTROS)

    assert nosotros["points"] == 422, nosotros
    assert nosotros["rank"] == 2, nosotros
    assert nosotros["profile_points"] == 383, nosotros
    assert nosotros["points_source"] == "BIWENGER", nosotros

    assert _fila(filas, MANZAGOOL)["points"] == 365
    assert _fila(filas, MEX)["points"] == 324
    assert _fila(filas, MEX)["rank"] == 7

    # Lo que lee la subasta no cambia.
    assert [f["roster_count"] for f in filas] == [
        f["roster_count"] for f in antes
    ]


def test_los_rivales_cuentan_el_puesto_con_biwenger() -> None:
    """`losRivales` sale de la tabla: segundos en puntos, y la
    diferencia con cada uno con los puntos de Biwenger."""

    from src.analysis.los_rivales import los_rivales

    tabla = _tabla(_competition())

    rivales = los_rivales(clasificacion=tabla["filas"], plantillas={})

    assert rivales["available"] is True, rivales
    assert rivales["lectura"]["por_puntos"] == 2, rivales

    nosotros = rivales["nosotros"]

    assert nosotros["points"] == 422, nosotros
    assert nosotros["rank"] == 2, nosotros
    assert nosotros["points_source"] == "BIWENGER", nosotros

    manzagool = _fila(rivales["managers"], MANZAGOOL)

    assert manzagool["vs_nosotros"] == 365 - 422, manzagool
    assert _fila(rivales["managers"], MEX)["vs_nosotros"] == 324 - 422


# ============================================================
# 5. LO QUE NO SE TOCA
# ============================================================


def test_el_libro_que_leen_los_motores_no_se_toca() -> None:
    """
    SOLO VISTA. El abono, el saldo estimado, el tope de puja y el
    `points_rank` de los motores salen de `rival_intelligence`, y
    eso entra y sale igual.
    """

    from src.telemetry.la_clasificacion_de_biwenger import (
        con_el_valor_de_las_plantillas,
        la_tabla,
    )

    libro = {"managers": copy.deepcopy(MANAGERS)}
    perfiles = {p["id"]: dict(p) for p in PERFILES}

    competition = _competition()
    antes = copy.deepcopy((libro, perfiles, competition))

    la_tabla(
        managers=libro["managers"],
        competition=competition,
        perfiles=perfiles,
    )
    con_el_valor_de_las_plantillas(competition, libro["managers"])

    assert (libro, perfiles, competition) == antes

    # Y ningun motor la importa: solo la telemetria.
    quien = sorted(
        str(ruta.relative_to(RAIZ))
        for ruta in (RAIZ / "src").rglob("*.py")
        if "la_clasificacion_de_biwenger" in ruta.read_text(
            encoding="utf-8", errors="ignore"
        )
        and not ruta.name.startswith("test_")
    )

    assert quien, "nadie la usa: la guardia no mira nada"

    for ruta in quien:
        assert ruta.startswith("src/telemetry/"), (
            f"{ruta} la importa y no es telemetria"
        )

    motor = (
        RAIZ / "src" / "analysis" / "rival_intelligence_engine.py"
    ).read_text(encoding="utf-8")

    assert "la_clasificacion_de_biwenger" not in motor


def test_los_colectores_apuntan_la_hora() -> None:
    """
    La hora de la clasificacion y la del perfil las ponen los
    colectores, sin peticiones nuevas.
    """

    liga = (
        RAIZ / "src" / "collectors" / "league_collector.py"
    ).read_text(encoding="utf-8")

    assert '"rounds_as_of": rounds_as_of' in liga
    assert 'rounds_as_of = guardada.get("guardado_en")' in liga

    tablon = (
        RAIZ / "src" / "collectors" / "board_history_collector.py"
    ).read_text(encoding="utf-8")

    cuerpo = tablon.split("def fetch_user_profiles")[1].split(
        "\ndef "
    )[0]

    assert 'perfil["_fetched_at"]' in cuerpo, cuerpo


TESTS = [
    test_la_tabla_lleva_los_puntos_de_biwenger,
    test_la_hora_de_la_clasificacion_va_con_ella,
    test_el_valor_de_la_clasificacion_es_la_plantilla_de_ahora,
    test_la_ficha_del_rival_suma_lo_que_enseña,
    test_sin_clasificacion_cae_al_perfil_con_su_hora,
    test_una_averia_no_deja_la_pantalla_sin_tabla,
    test_si_biwenger_no_trae_a_uno_la_tabla_es_mixta,
    test_la_inteligencia_de_rivales_de_la_pantalla,
    test_los_rivales_cuentan_el_puesto_con_biwenger,
    test_el_libro_que_leen_los_motores_no_se_toca,
    test_los_colectores_apuntan_la_hora,
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
        f"LA CLASIFICACION DE BIWENGER V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
