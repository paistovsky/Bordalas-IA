"""
LA TITULARIDAD DEL DIA (19/10/2026). Guardias de
`archivo_diario.archivar_la_titularidad` y de las plantillas enteras
del tablero de FF (`futbolfantasy_provider.CAMPOS_DE_LA_PLANTILLA`).

SINTOMA

    El laboratorio del 19/10 no pudo validar el xP de la J8 y la J9:
    la titularidad de FutbolFantasy solo quedaba guardada para 141 de
    551 jugadores, y el estado de Biwenger de la liga vivia en la
    foto, que caduca.

CAUSA

    El tablero de FF baja las 20 paginas de equipo -con la plantilla
    entera- y solo guardaba a sus objetivos emparejados. El resto se
    leia y se tiraba. Y el tablero se pisa cada vuelta.

LO QUE SE FIJA

    1. El tablero guarda TODAS las filas de cada pagina que lee, y al
       completar conserva las de los equipos que no vuelve a bajar.
    2. Una linea al dia en un libro de git: FF por id de Biwenger (lo
       del tablero y lo que se empareja con el catalogo de su equipo),
       lo que no empareja con su identidad de FF, y el estado de todo
       el catalogo. La segunda vuelta del dia no escribe.
    3. Un tablero de mas de 24 h no se guarda como de hoy; el estado
       si. Se poda a 60 dias, y una linea ilegible no se borra.
    4. Nunca lanza, se apaga con `BORDALAS_SIN_ARCHIVO`, es un libro
       (no lo tapa el `.gitignore`), el ciclo lo llama despues del
       tablero y ninguna ruta de decision lo lee.
    5. El dia empieza en el reset: la vuelta de las 00:07 de Madrid,
       con el catalogo de la cache del reset de ayer, no escribe; la
       primera despues del reset si, y la linea dice de que reset es.
    6. Una linea a medias (caducada, con paginas de FF que fallaron,
       con plantillas que faltan) no congela el dia: una vuelta
       posterior mejor la cambia en su sitio. Una entera no se toca.
    7. Un libro con una linea cortada a mitad de una letra no se lee
       como vacio: se poda, la nueva no se pega a la rota y la vuelta
       siguiente ve que ya esta. Un libro que no se puede abrir no se
       escribe.
    8. Cada plantilla con su hora: la que el tablero arrastra de hace
       30 h (o de ayer) no se guarda como de hoy.

Todo con datos de mentira: la hora se pasa, el libro y el tablero van
a una carpeta temporal y FF no se pide a la red.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.intelligence.futbolfantasy_provider as ff     # noqa: E402

from src.intelligence.archivo_diario import (            # noqa: E402
    DIAS_QUE_SE_GUARDAN, DISABLE_ENV, LIBRO_DE_LA_TITULARIDAD,
    archivar_la_titularidad, el_dia_de_madrid, la_titularidad_de_hoy,
)


AHORA = datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc)   # 12:00 de Madrid


def _archivar(*args, **kwargs):
    """`archivar_la_titularidad` con el archivo encendido: si el `env` de
    quien corre la verja trae `BORDALAS_SIN_ARCHIVO`, aqui no cuenta."""
    apagado = os.environ.pop(DISABLE_ENV, None)
    try:
        return archivar_la_titularidad(*args, **kwargs)
    finally:
        if apagado is not None:
            os.environ[DISABLE_ENV] = apagado


def _pagina(*filas) -> str:
    """Una pagina de equipo de FF con las filas `tipo_lista`."""
    return "<html><body>" + "".join(
        f'<div class="tipo_lista jugador_{i}" data-nombre="{slug}" '
        f'data-probabilidad="{prob}%" data-jerarquia="{jer}" data-estado="0" '
        f'data-sancionado="0" data-valor-biwenger="{valor}">'
        f'<span class="nombre">{nombre}</span></div>'
        for i, (slug, nombre, prob, jer, valor) in enumerate(filas, start=1)
    ) + "</body></html>"


BARCA = _pagina(
    ("fulano", "Fulano", 90, 50, 1_000_000),
    ("mengano-de-tal", "Mengano de Tal", 10, 25, 2_000_000),
    ("zutano", "Zutano", 60, 30, 500_000),
)


def _catalogo() -> dict:
    jugadores = {
        26271: ("Fulano", 1, 1_000_000, "ok"),
        2: ("Mengano", 1, 2_000_000, "injured"),
        3: ("Zutano", 1, 500_000, "doubt"),
        4: ("Perengano", 2, 800_000, "ok"),
    }
    return {"data": {
        "players": {str(p): {"id": p, "name": n, "teamID": t, "price": v, "status": s}
                    for p, (n, t, v, s) in jugadores.items()},
        "teams": {"1": {"id": 1, "name": "Barcelona"}, "2": {"id": 2, "name": "Betis"}},
    }}


def _snapshot(*ids) -> dict:
    catalogo = _catalogo()
    return {
        "timestamp": "2026-10-19T11:55:00",
        "my_team": [{"id": p, "name": catalogo["data"]["players"][str(p)]["name"],
                     "teamID": 1, "price": catalogo["data"]["players"][str(p)]["price"]}
                    for p in ids],
        "catalog": catalogo,
    }


def _tablero(horas=1) -> dict:
    """El tablero de FF de hace `horas`, con un objetivo y las plantillas."""
    return {
        "version": "V12.0",
        "updated_at": (AHORA - timedelta(hours=horas)).isoformat(),
        "matchday": 9,
        "players": [{"player_id": 26271, "player_name": "Fulano", "team": "Barcelona",
                     "scope": "ROSTER", "starter_probability": 90.0, "hierarchy": {"value": 50},
                     "availability": {"code": 0}, "ff": {"slug": "fulano"}}],
        "plantillas": {
            "Barcelona": {"at": AHORA.isoformat(), "players": [
                {"ff_slug": "fulano", "ff_name": "Fulano", "probability": 90.0,
                 "hierarchy_value": 50, "availability_code": 0, "sanctioned": False,
                 "ff_biwenger_value": 1_000_000},
                {"ff_slug": "mengano-de-tal", "ff_name": "Mengano de Tal",
                 "probability": 10.0, "hierarchy_value": 25, "availability_code": 2,
                 "sanctioned": False, "ff_biwenger_value": 2_000_000},
                {"ff_slug": "zutano", "ff_name": "Zutano", "probability": 60.0,
                 "hierarchy_value": 30, "availability_code": 0, "sanctioned": False,
                 "ff_biwenger_value": 500_000},
            ]},
            "Betis": {"at": AHORA.isoformat(), "players": [
                {"ff_slug": "desconocido", "ff_name": "Desconocido", "probability": 70.0,
                 "hierarchy_value": 40, "availability_code": 0, "sanctioned": False,
                 "ff_biwenger_value": 999_000},
            ]},
        },
    }


def _con_ff_de_mentira(funcion, paginas, tablero_previo=None):
    """`refresh_board` sin red y con su tablero en una carpeta temporal.
    Con la lista de objetivos de siempre: `BORDALAS_OBJETIVOS_EL_CATALOGO`
    se quita mientras tanto (una guardia no lee el `env` del workflow)."""
    original = (ff.BOARD_FILE, ff.fetch, ff.load_absences)
    interruptor = os.environ.pop(ff.ENV_EL_CATALOGO, None)
    pedidas = []

    def fetch(session, url):
        pedidas.append(url)
        return paginas.get(url.rsplit("/", 1)[-1], "<html></html>")

    with tempfile.TemporaryDirectory() as carpeta:
        ff.BOARD_FILE = Path(carpeta) / "board.json"
        if tablero_previo is not None:
            ff.BOARD_FILE.write_text(json.dumps(tablero_previo), encoding="utf-8")
        ff.fetch = fetch
        ff.load_absences = lambda session, matchday: ({}, {})
        try:
            return funcion(), pedidas
        finally:
            ff.BOARD_FILE, ff.fetch, ff.load_absences = original
            if interruptor is not None:
                os.environ[ff.ENV_EL_CATALOGO] = interruptor


# ------------------------------------------------------------------
# 1. EL TABLERO GUARDA LAS PLANTILLAS ENTERAS
# ------------------------------------------------------------------

def test_el_tablero_guarda_las_plantillas_enteras():
    tablero, pedidas = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(26271), 9, force=True, session=object()),
        {"barcelona": BARCA})
    assert pedidas == ["https://www.futbolfantasy.com/laliga/equipos/barcelona"], pedidas
    # El objetivo, como siempre; y las tres filas de la pagina, enteras.
    assert [p["player_id"] for p in tablero["players"]] == [26271], tablero["players"]
    filas = tablero["plantillas"]["Barcelona"]["players"]
    assert [f["ff_slug"] for f in filas] == ["fulano", "mengano-de-tal", "zutano"], filas
    assert set(filas[1]) == set(ff.CAMPOS_DE_LA_PLANTILLA), filas[1]
    assert (filas[1]["probability"], filas[1]["ff_biwenger_value"]) == (10.0, 2_000_000)

    # Al completar (misma jornada, fresco, falta un objetivo del Barça) solo
    # se baja el Barça, y la plantilla del Betis de la cache se conserva.
    # El tablero de antes es el que acaba de salir, con el Betis de otra vuelta.
    previo = json.loads(json.dumps(tablero))
    previo["plantillas"]["Betis"] = _tablero()["plantillas"]["Betis"]
    tablero, pedidas = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(26271, 3), 9, session=object()),
        {"barcelona": BARCA}, previo)
    assert tablero["cache"]["status"] == "TOPPED_UP", tablero["cache"]
    assert len(pedidas) == 1 and pedidas[0].endswith("/barcelona"), pedidas
    assert sorted(tablero["plantillas"]) == ["Barcelona", "Betis"], tablero["plantillas"]
    assert tablero["plantillas"]["Betis"] == previo["plantillas"]["Betis"]
    assert sorted(p["player_id"] for p in tablero["players"]) == [3, 26271]


# ------------------------------------------------------------------
# 2. UNA LINEA AL DIA CON TODA LA LIGA
# ------------------------------------------------------------------

def test_una_linea_al_dia_con_toda_la_liga():
    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        r = _archivar(_snapshot(26271), _tablero(), AHORA, libro)
        assert r["written"] and r["day"] == "2026-10-19", r
        lineas = [json.loads(t) for t in libro.read_text(encoding="utf-8").splitlines()]
        assert len(lineas) == 1
        linea = lineas[0]
        # FF: el objetivo del tablero y los dos del Barça que el tablero no
        # emparejo (por el euro y el nombre, contra el catalogo de su equipo).
        assert linea["ff"] == {"26271": [90, 50, 0], "2": [10, 25, 2], "3": [60, 30, 0]}, linea["ff"]
        assert linea["campos_ff"] == ["titular", "jerarquia", "parte"]
        # Lo que no empareja NO se adivina: va con su identidad de FF.
        assert linea["ff_sin_id"] == [["Betis", "desconocido", "Desconocido", 70, 40, 0,
                                       999_000]], linea["ff_sin_id"]
        assert linea["n_ff_leidos"] == 4
        # El estado de Biwenger de TODO el catalogo, tambien el de Perengano.
        assert linea["biwenger"] == {"26271": "ok", "2": "injured", "3": "doubt",
                                     "4": "ok"}, linea["biwenger"]
        assert (linea["ff_jornada"], linea["ff_motivo"]) == (9, None), linea
        assert linea["foto_at"] == "2026-10-19T11:55:00"
        # La segunda vuelta del dia no escribe; la del dia siguiente si.
        r = _archivar(_snapshot(26271), _tablero(), AHORA + timedelta(hours=5), libro)
        assert r["already"] and not r["written"], r
        r = _archivar(_snapshot(26271), _tablero(-23), AHORA + timedelta(days=1),
                                    libro)
        assert r["written"] and r["day"] == "2026-10-20", r
        assert len(libro.read_text(encoding="utf-8").splitlines()) == 2
    # El dia es el de Madrid: las 22:30 UTC del 19/10 son las 00:30 del 20.
    assert el_dia_de_madrid(datetime(2026, 10, 19, 22, 30, tzinfo=timezone.utc)).isoformat() \
        == "2026-10-20"
    assert el_dia_de_madrid(datetime(2026, 12, 19, 22, 30, tzinfo=timezone.utc)).isoformat() \
        == "2026-12-19"


# ------------------------------------------------------------------
# 3. LO CADUCADO NO ES DE HOY, Y LA PODA
# ------------------------------------------------------------------

def test_lo_caducado_no_es_de_hoy_y_se_poda():
    # Un tablero de hace 30 h: FF no se guarda como de hoy; el estado si.
    linea = la_titularidad_de_hoy(_snapshot(26271), _tablero(30), AHORA)
    assert linea["ff"] == {} and linea["ff_sin_id"] == [], linea
    assert linea["ff_motivo"].startswith("CADUCADO"), linea["ff_motivo"]
    assert len(linea["biwenger"]) == 4
    # Un tablero de antes de esto (sin plantillas): solo sus objetivos, y lo dice.
    viejo = {k: v for k, v in _tablero().items() if k != "plantillas"}
    linea = la_titularidad_de_hoy(_snapshot(26271), viejo, AHORA)
    assert linea["ff"] == {"26271": [90, 50, 0]} and linea["ff_motivo"].startswith(
        "SIN_PLANTILLAS"), linea
    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        hoy = AHORA.date()
        libro.write_text(
            json.dumps({"dia": (hoy - timedelta(days=DIAS_QUE_SE_GUARDAN + 1)).isoformat()})
            + "\n" + json.dumps({"dia": (hoy - timedelta(days=DIAS_QUE_SE_GUARDAN)).isoformat()})
            + "\nesto no es json\n", encoding="utf-8")
        r = _archivar(_snapshot(26271), _tablero(), AHORA, libro)
        assert r["written"] and r["removed"] == 1, r
        quedan = libro.read_text(encoding="utf-8").splitlines()
        # El de 61 dias fuera; el de 60 y la linea ilegible se quedan.
        assert len(quedan) == 3 and quedan[1] == "esto no es json", quedan
        assert json.loads(quedan[0])["dia"] == (hoy - timedelta(days=60)).isoformat()
        assert json.loads(quedan[2])["dia"] == hoy.isoformat()


# ------------------------------------------------------------------
# 4. NUNCA LANZA, SE APAGA, ES UN LIBRO Y NADIE DECIDE CON EL
# ------------------------------------------------------------------

def test_nunca_lanza_y_se_apaga():
    import src.intelligence.futbolfantasy_provider as ff

    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        # Sin tablero dado, el modulo lee el de disco. En CI la cache trae
        # el de produccion (143 objetivos) y escribia (20/10 00:07, verja
        # roja): la guardia no puede depender de lo que haya en `data/`.
        tablero_de_disco = ff.BOARD_FILE
        ff.BOARD_FILE = Path(carpeta) / "no_hay_tablero.json"
        try:
            for snapshot, tablero in ((None, None), ("x", 5), ({"catalog": 7}, {"plantillas": "x"}),
                                      ({}, {"updated_at": "ayer", "players": [None, 3]})):
                r = _archivar(snapshot, tablero, AHORA, libro)
                assert isinstance(r, dict) and not r["written"] and r["reason"], r
                linea = la_titularidad_de_hoy(snapshot, tablero, AHORA)
                assert isinstance(linea, dict) and linea["dia"] == "2026-10-19", linea
        finally:
            ff.BOARD_FILE = tablero_de_disco
        # Sin catalogo ni tablero no se escribe nada (ni se crea el libro).
        assert not libro.exists()
        # Una plantilla rota no tumba la linea.
        roto = _tablero()
        roto["plantillas"]["Barcelona"]["players"] = [None, "x", {"ff_slug": None}]
        linea = la_titularidad_de_hoy(_snapshot(26271), roto, AHORA)
        assert linea["ff"]["26271"] == [90, 50, 0] and len(linea["biwenger"]) == 4, linea
        antes = os.environ.get(DISABLE_ENV)
        os.environ[DISABLE_ENV] = "1"
        try:
            r = archivar_la_titularidad(_snapshot(26271), _tablero(), AHORA, libro)
            assert not r["written"] and DISABLE_ENV in r["reason"], r
            assert not libro.exists()
        finally:
            if antes is None:
                os.environ.pop(DISABLE_ENV, None)
            else:
                os.environ[DISABLE_ENV] = antes


def test_es_un_libro_y_el_ciclo_lo_llama():
    import subprocess

    from src.estado.los_libros import rutas

    # (Sin escribir la ruta aqui: una guardia de la verja no nombra el
    # estado, `test_verja_determinista_v1`. La da el modulo.)
    ruta = str(LIBRO_DE_LA_TITULARIDAD).replace("\\", "/")
    assert ruta.endswith("la_titularidad_del_dia.jsonl"), ruta
    assert ruta in rutas(), "la titularidad del dia no esta en LIBROS"
    tapado = subprocess.run(["git", "check-ignore", "-q", "--", ruta], cwd=str(RAIZ),
                            capture_output=True)
    assert tapado.returncode != 0, "el .gitignore tapa la titularidad del dia"
    # El ciclo la escribe DESPUES del tablero de FF de esa vuelta.
    ciclo = (RAIZ / "src" / "autopilot.py").read_text(encoding="utf-8")
    cuerpo = ciclo[ciclo.index("def run_cycle("):]
    assert "archivar_la_titularidad(snapshot)" in cuerpo
    assert cuerpo.index("build_cycle_acquisition_board(") < cuerpo.index(
        "archivar_la_titularidad(snapshot)")
    # Nadie decide con ella.
    for decide in ("src/analysis/decision_orchestrator.py", "src/analysis/acquisition_valuation.py",
                   "src/analysis/candidate_starter_lookup.py", "src/analysis/lineup_engine.py",
                   "src/actions/la_rotacion.py", "src/actions/la_mejora_del_once.py"):
        fichero = RAIZ / decide
        if fichero.exists():
            texto = fichero.read_text(encoding="utf-8")
            for lectura in ("la_titularidad_del_dia", 'get("plantillas")', '["plantillas"]'):
                assert lectura not in texto, (decide, lectura)


# ------------------------------------------------------------------
# 5. EL DIA EMPIEZA EN EL RESET
# ------------------------------------------------------------------

def _tablero_de(cuando, horas=1) -> dict:
    """`_tablero` bajado a `cuando - horas`, con sus plantillas a esa hora."""
    tablero = _tablero()
    hora = (cuando - timedelta(hours=horas)).isoformat()
    tablero["updated_at"] = hora
    for plantilla in tablero["plantillas"].values():
        plantilla["at"] = hora
    return tablero


def test_el_dia_empieza_en_el_reset():
    from src.biwenger import cache_del_reset as cache

    viernes_0715 = datetime(2026, 10, 23, 5, 15, tzinfo=timezone.utc)
    sabado_0007 = datetime(2026, 10, 23, 22, 7, tzinfo=timezone.utc)   # 00:07 de Madrid
    sabado_0715 = datetime(2026, 10, 24, 5, 15, tzinfo=timezone.utc)
    sin_cache = os.environ.pop(cache.DISABLE_ENV, None)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            guardado = Path(carpeta) / "cache.json"
            libro = Path(carpeta) / "titularidad.jsonl"
            # El catalogo que guardo la vuelta de las 07:15 del viernes es
            # el que la cache sirve a la de las 00:07 del sabado (a mas de
            # 12 h del cierre: PREPARATION).
            cache.escribir("catalogo", _catalogo(), path=guardado, ahora=viernes_0715)
            leido = cache.leer("catalogo", path=guardado, ahora=sabado_0007,
                               fase="PREPARATION")
            assert leido["fresco"], leido
            foto = {**_snapshot(26271), "timestamp": "2026-10-24T00:07:30",
                    "catalog": leido["valor"]}
            # Esa vuelta no escribe el sabado: su estado es del viernes.
            r = _archivar(foto, _tablero_de(sabado_0007), sabado_0007, libro)
            assert not r["written"] and not r["already"] and "reset" in r["reason"], r
            assert r["day"] == "2026-10-24" and not libro.exists(), r
            # Y la linea, si se escribiera, diria de que reset es.
            assert la_titularidad_de_hoy(foto, _tablero_de(sabado_0007), sabado_0007)[
                "reset_at"] == "2026-10-23T05:00:00+00:00"
            # La de las 07:15 ya no tira de esa cache: pide el catalogo, y
            # escribe el sabado.
            assert not cache.leer("catalogo", path=guardado, ahora=sabado_0715,
                                  fase="PREPARATION")["fresco"]
            foto = {**_snapshot(26271), "timestamp": "2026-10-24T07:15:30"}
            r = _archivar(foto, _tablero_de(sabado_0715), sabado_0715, libro)
            assert r["written"] and r["day"] == "2026-10-24", r
            linea = json.loads(libro.read_text(encoding="utf-8"))
            assert (linea["dia"], linea["reset_at"]) == (
                "2026-10-24", "2026-10-24T05:00:00+00:00"), linea
            # Las 23:07 del sabado siguen siendo del sabado.
            r = _archivar(foto, _tablero_de(sabado_0715), sabado_0715 + timedelta(hours=16),
                          libro)
            assert r["already"] and r["day"] == "2026-10-24", r
    finally:
        if sin_cache is not None:
            os.environ[cache.DISABLE_ENV] = sin_cache


# ------------------------------------------------------------------
# 6. UNA LINEA A MEDIAS NO CONGELA EL DIA
# ------------------------------------------------------------------

def test_una_linea_a_medias_no_congela_el_dia():
    hoy_0715 = AHORA.replace(hour=5, minute=15)          # 07:15 de Madrid del 19/10
    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        libro.write_text(json.dumps({"dia": "2026-10-18", "x": 1}) + "\n", encoding="utf-8")
        # La primera vuelta del dia trae un tablero de hace 30 h: estado
        # si, FF no.
        r = _archivar(_snapshot(26271), _tablero_de(hoy_0715, 30), hoy_0715, libro)
        assert r["written"] and r["ff"] == 0, r
        # Otra igual de mala no la toca (cada linea escrita es un commit).
        antes = libro.read_bytes()
        r = _archivar(_snapshot(26271), _tablero_de(hoy_0715, 31), hoy_0715
                      + timedelta(hours=1), libro)
        assert r["already"] and not r["written"] and "a medias" in r["reason"], r
        assert libro.read_bytes() == antes
        # La de las 12:00, con el tablero fresco, la cambia EN SU SITIO.
        r = _archivar(_snapshot(26271), _tablero(), AHORA, libro)
        assert r["written"] and r["replaced"] and r["ff"] == 3, r
        lineas = [json.loads(t) for t in libro.read_text(encoding="utf-8").splitlines()]
        assert [l["dia"] for l in lineas] == ["2026-10-18", "2026-10-19"], lineas
        assert lineas[1]["ff_motivo"] is None and len(lineas[1]["ff"]) == 3, lineas[1]
        # Ya entera: una vuelta despues no la toca, ni con un tablero
        # que tambien esta entero.
        antes = libro.read_bytes()
        r = _archivar(_snapshot(26271), _tablero_de(AHORA + timedelta(hours=3)),
                      AHORA + timedelta(hours=3), libro)
        assert r["already"] and not r["written"], r
        assert libro.read_bytes() == antes

    # Lo que el tablero dice de si mismo va a la linea, y lo que falla la
    # deja a medias: una pagina que no se bajo...
    tablero = _tablero()
    tablero["metadata"] = {"errors": ["Betis: TimeoutError: timeout"]}
    tablero["cache"] = {"status": "REFRESHED"}
    linea = la_titularidad_de_hoy(_snapshot(26271), tablero, AHORA)
    assert linea["ff_errores"] == ["Betis: TimeoutError: timeout"], linea
    assert linea["ff_cache"] == "REFRESHED"
    assert linea["ff_motivo"].startswith("ERRORES"), linea["ff_motivo"]
    assert len(linea["ff"]) == 3, linea["ff"]
    # ... o un equipo con objetivos y sin su plantilla.
    tablero = _tablero()
    tablero["players"].append({"player_id": 4, "player_name": "Perengano", "team": "Betis",
                               "starter_probability": 80.0, "hierarchy": {"value": 40},
                               "availability": {"code": 0}, "ff": {"slug": "perengano"}})
    del tablero["plantillas"]["Betis"]
    linea = la_titularidad_de_hoy(_snapshot(26271), tablero, AHORA)
    assert "PLANTILLAS_A_MEDIAS" in linea["ff_motivo"] and "Betis" in linea["ff_motivo"], linea
    assert linea["ff"]["4"] == [80, 40, 0], linea["ff"]
    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        assert _archivar(_snapshot(26271), tablero, AHORA, libro)["written"]
        r = _archivar(_snapshot(26271), _tablero(), AHORA + timedelta(hours=1), libro)
        assert r["written"] and r["replaced"], r
        assert len(libro.read_text(encoding="utf-8").splitlines()) == 1


# ------------------------------------------------------------------
# 7. UN LIBRO ROTO NO SE DUPLICA
# ------------------------------------------------------------------

def test_un_libro_roto_no_se_duplica():
    hoy = AHORA.date()
    viejo = json.dumps({"dia": (hoy - timedelta(days=DIAS_QUE_SE_GUARDAN + 1)).isoformat()})
    truncada = json.dumps({"dia": "2026-10-18", "x": "Muñoz"}, ensure_ascii=False).encode("utf-8")
    # Cortada a mitad de la ñ, sin salto de linea: una escritura que se corto.
    truncada = truncada[:truncada.index("ñ".encode("utf-8")) + 1]
    with tempfile.TemporaryDirectory() as carpeta:
        libro = Path(carpeta) / "titularidad.jsonl"
        libro.write_bytes((viejo + "\n").encode("utf-8") + truncada)
        hechas = [_archivar(_snapshot(26271), _tablero(), AHORA + timedelta(hours=h), libro)
                  for h in (0, 1, 2)]
        assert [(r["written"], r["already"]) for r in hechas] == [
            (True, False), (False, True), (False, True)], hechas
        assert hechas[0]["removed"] == 1, hechas[0]
        lineas = libro.read_bytes().split(b"\n")
        # La de 61 dias, fuera; la rota, tal cual y sola; la de hoy, una.
        assert lineas[0] == truncada and lineas[-1] == b"", lineas
        assert [json.loads(l)["dia"] for l in lineas[1:-1]] == ["2026-10-19"], lineas

        # Sin poda, la nueva va DETRAS de un salto de linea.
        libro.write_bytes(truncada)
        assert _archivar(_snapshot(26271), _tablero(), AHORA, libro)["written"]
        assert _archivar(_snapshot(26271), _tablero(), AHORA + timedelta(hours=1),
                         libro)["already"]
        lineas = libro.read_bytes().split(b"\n")
        assert lineas[0] == truncada and json.loads(lineas[1])["dia"] == "2026-10-19", lineas
        assert len(lineas) == 3 and lineas[2] == b"", lineas

        # Un libro que existe y no se puede abrir: no se escribe.
        carpeta_libro = Path(carpeta) / "es_una_carpeta.jsonl"
        carpeta_libro.mkdir()
        r = _archivar(_snapshot(26271), _tablero(), AHORA, carpeta_libro)
        assert not r["written"] and not r["available"] and "no se puede leer" in r["reason"], r


# ------------------------------------------------------------------
# 8. CADA PLANTILLA CON SU HORA
# ------------------------------------------------------------------

def test_cada_plantilla_con_su_hora():
    betis = {"at": None, "players": [
        {"ff_slug": "perengano", "ff_name": "Perengano", "probability": 80.0,
         "hierarchy_value": 40, "availability_code": 0, "sanctioned": False,
         "ff_biwenger_value": 800_000}]}
    # El tablero es fresco (de hace 1 h: completo), pero la plantilla del
    # Betis la arrastro de hace 30 h. Perengano no es de hoy.
    tablero = _tablero()
    tablero["plantillas"]["Betis"] = {**betis, "at": (AHORA - timedelta(hours=30)).isoformat()}
    tablero["players"].append({"player_id": 4, "player_name": "Perengano", "team": "Betis",
                               "starter_probability": 80.0, "hierarchy": {"value": 40},
                               "availability": {"code": 0}, "ff": {"slug": "perengano"}})
    linea = la_titularidad_de_hoy(_snapshot(26271), tablero, AHORA)
    assert "4" not in linea["ff"] and linea["ff_sin_id"] == [], linea
    assert linea["ff_viejos"] == ["Betis"], linea["ff_viejos"]
    assert linea["ff_at_por_equipo"]["Betis"] == (AHORA - timedelta(hours=30)).isoformat()
    assert linea["ff_at_por_equipo"]["Barcelona"] == AHORA.isoformat()
    assert "PLANTILLAS_VIEJAS" in linea["ff_motivo"], linea["ff_motivo"]
    # Los del Barça, frescos, si.
    assert sorted(linea["ff"]) == ["2", "26271", "3"], linea["ff"]
    # De ayer (las 23:30 de Madrid del 18/10: 12,5 h) tampoco es de hoy.
    tablero["plantillas"]["Betis"]["at"] = datetime(2026, 10, 18, 21, 30,
                                                     tzinfo=timezone.utc).isoformat()
    linea = la_titularidad_de_hoy(_snapshot(26271), tablero, AHORA)
    assert "4" not in linea["ff"] and linea["ff_viejos"] == ["Betis"], linea
    # De esta madrugada (las 00:30 de Madrid del 19/10), si.
    tablero["plantillas"]["Betis"]["at"] = datetime(2026, 10, 18, 22, 30,
                                                     tzinfo=timezone.utc).isoformat()
    linea = la_titularidad_de_hoy(_snapshot(26271), tablero, AHORA)
    assert linea["ff"]["4"] == [80, 40, 0] and linea["ff_viejos"] == [], linea
    assert linea["ff_motivo"] is None, linea["ff_motivo"]


TESTS = [
    test_el_tablero_guarda_las_plantillas_enteras,
    test_una_linea_al_dia_con_toda_la_liga,
    test_lo_caducado_no_es_de_hoy_y_se_poda,
    test_nunca_lanza_y_se_apaga,
    test_es_un_libro_y_el_ciclo_lo_llama,
    test_el_dia_empieza_en_el_reset,
    test_una_linea_a_medias_no_congela_el_dia,
    test_un_libro_roto_no_se_duplica,
    test_cada_plantilla_con_su_hora,
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
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
