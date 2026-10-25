"""
LA JORNADA DE CADA PAGINA (25/10/2026). Guardias de
`BORDALAS_LA_JORNADA_DE_CADA_PAGINA`, en dos sitios:

    `src/intelligence/futbolfantasy_provider.py`  el tablero apunta de
        que jornada era la pagina de FF de la que salio cada ficha;
    `src/actions/la_mejora_del_once.py`  la mejora no abre un hueco
        con una titularidad de otra jornada.

SINTOMA (24/10/2026)

    El panel de las 18:10 tenia a Sergi Cardona al 0 % y a Chust y Unai
    Lopez al 100 % -la "Alineacion confirmada J10" de sus paginas- al
    lado de Jonny al 50 % -el pronostico de la J11-, con el tablero ya
    en la J11. La mejora del once lee un 0 % como un hueco: se salta
    SOLO SI SUBE y puja +1 % por cualquier defensa sano con un 60 %.

CAUSA

    El tablero comprueba su jornada entero, pero cada pagina de equipo
    no: la del que ya jugo sigue en su confirmada (11 al 100 %, el
    resto al 0 %) hasta que FF publica la siguiente, y la del que juega
    el lunes sigue con el pronostico de la jornada anterior.

LO QUE SE FIJA

    1. La jornada de una pagina se lee de tres marcas DENTRO de la
       seccion de la alineacion (cabecera, selector, rotulo de la
       previsibilidad), y las trampas (la pestana del calendario, la
       navegacion, el pie, `tipo`) no se miran nunca.
    2. El caso del 24/10: Cardona y Gulacsi (confirmada J10) marcados,
       Jonny (J11) no; el 0 % sigue siendo 0 %.
    3. Apagado, el tablero es byte a byte el de antes; encendido solo
       AÑADE claves, no cambia ni un numero.
    4. Sin jornada legible no se marca nada, y se dice.
    5. Al completar, cada ficha lleva la marca de su propia bajada.
    6. La mejora no abre un hueco ni pone precio a un cambio con un %
       de otra jornada; el lesionado sigue siendo hueco.
    7. Apagada, la mejora decide lo de siempre (la misma huella).
    8. `correr` lee las marcas del tablero de junto al libro, solo
       encendido; lo dado en `de_fuera` manda.
    9. El lookup de titularidad no cambia: el once, el xP, el cierre,
       las valoraciones y el panel ven los mismos numeros.
   10. Nace apagado, se lee al llamarse y nunca lanza.

Todo con datos de mentira: HTML sintetico (el repositorio no guarda
paginas de FF), sin red, con el reloj parado, y el tablero y los libros
en carpetas temporales. Cada prueba pone y quita el interruptor ella
misma (doctrina 104).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from bs4 import BeautifulSoup                                       # noqa: E402

import src.actions.la_mejora_del_once as mejora                     # noqa: E402
import src.analysis.candidate_starter_lookup as lookup              # noqa: E402
import src.analysis.test_la_mejora_del_once_v1 as base              # noqa: E402
import src.intelligence.futbolfantasy_provider as ff                # noqa: E402


INTERRUPTOR = "BORDALAS_LA_JORNADA_DE_CADA_PAGINA"

# El panel del 24/10 a las 18:10 de Madrid.
AHORA = datetime(2026, 10, 24, 16, 10, tzinfo=timezone.utc)

CARDONA, GULACSI, JONNY = 30493, 38433, 1599


@contextmanager
def _interruptor(valor):
    """El de LA JORNADA DE CADA PAGINA, puesto (o quitado, con None) por
    la prueba misma y devuelto como estaba al salir (doctrina 104)."""
    antes = os.environ.get(INTERRUPTOR)
    try:
        if valor is None:
            os.environ.pop(INTERRUPTOR, None)
        else:
            os.environ[INTERRUPTOR] = valor
        yield
    finally:
        if antes is None:
            os.environ.pop(INTERRUPTOR, None)
        else:
            os.environ[INTERRUPTOR] = antes


class _Reloj(datetime):
    """El reloj del proveedor, parado en `AHORA`: dos tableros del mismo
    dato salen con la misma hora, y la cache tiene la edad que se le da."""

    @classmethod
    def now(cls, tz=None):
        return AHORA if tz is None else AHORA.astimezone(tz)


# ------------------------------------------------------------------
# LAS PAGINAS, COPIANDO EL DOM DE VERDAD
# ------------------------------------------------------------------

def _filas_del_entrenador(jornada) -> str:
    """Las filas del entrenador de una POSIBLE: rotaciones, previsibilidad
    de la jornada y la de la temporada (que no lleva jornada)."""
    def fila(clase, rotulo, ancho, texto):
        return (f'<div class="row coach-metric {clase}">'
                f'<div class="col-5 p-0 text-truncate font-size-12">{rotulo}</div>'
                '<div class="col-7 p-0"><div class="prevision-wrapper">'
                f'<div class="prevision three" style="width:{ancho}%;"></div>'
                f'<div class="porcentaje">{texto}</div></div></div></div>')
    return ('<div class="coach-wrapper">'
            + fila("coach-metric--rotations", f"Rotaciones J{jornada}", 60, "Algunas rotaciones")
            + fila("", f"Previsib. J{jornada}", 44, "Poco previsible")
            + fila("coach-metric--season", "Previsib. Temp.", 58, "79%")
            + '</div>')


def _pagina(jornada, confirmada, filas, cabecera=True, selector=True, previsib=True,
            nav=None, pie=None, tipo=None, con_data_confirmed=True) -> str:
    """
    Una pagina de equipo de FF con la forma de la de verdad:

        la seccion `section.alineacion_wrapper[data-equipo]`, con `past`
        si es confirmada; la cabecera `h2.lineup-title` con
        `.jornada_label` "J" y `.jornada` N; el `select.past-alineaciones`
        con sus `option[data-jornada][data-confirmed]`; el campo; las
        filas `tipo_lista` (como `test_la_titularidad_del_dia_v1._pagina`);
        y, solo en las POSIBLES, las filas del entrenador.

    Y SIEMPRE la trampa 1: `div.tab.checked` con un data-jornada (6) que
    no es el de su rotulo. `cabecera`, `selector` y `previsib`: True (la
    `jornada`), False (no esta) o un numero (otra). `nav`, `pie` y `tipo`
    son las otras trampas. `con_data_confirmed=False`, el selector de
    septiembre.
    """
    def cual(valor):
        if valor is True:
            return jornada
        if valor is False or valor is None:
            return None
        return valor

    j_cabecera, j_selector, j_previsib = cual(cabecera), cual(selector), cual(previsib)
    titulo = "Alineación confirmada" if confirmada else "Posible alineación"
    partes = ["<html><head>"]
    if tipo:
        partes.append(f"<script>var tipo = '{tipo}';</script>")
    partes.append("</head><body>")
    if nav:
        partes.append(f'<nav class="nav-equipo"><a class="nav-link">{nav}</a></nav>')
    partes.append('<div class="tabs-wrapper"><div class="tab checked" data-jornada="6"> '
                  f'J{jornada}</div></div>')
    clases = "mod alineacion_wrapper block-new-only-header" + (" past" if confirmada else "")
    partes.append(f'<section class="{clases}" data-equipo="22" data-prox="22522">')
    cabeza = ('<h2 class="col-12 d-flex flex-row px-0 main title lineup-title">'
              f'<span class="ml-auto posible mt-auto">{titulo}</span>'
              '<span class="pasada ml-auto mt-auto">Alineación confirmada</span>')
    if j_cabecera is not None:
        cabeza += ('<span class="mb-0 mr-auto ml-0 mt-0">'
                   '<span class="jornada_label my-auto ml-1">J</span>'
                   f'<span class="jornada my-auto">{j_cabecera}</span></span>')
    partes.append(cabeza + "</h2>")
    if j_selector is not None:
        confirmado = f' data-confirmed="{1 if confirmada else 0}"' if con_data_confirmed else ""
        anterior = ' data-confirmed="1"' if con_data_confirmed else ""
        partes.append('<select class="past-alineaciones past-alineaciones-btn select_radius">'
                      f'<option value="22522" data-jornada="{j_selector}"{confirmado} selected>'
                      f'J{j_selector}</option>'
                      f'<option value="22511" data-jornada="{j_selector - 1}"{anterior}>'
                      f'J{j_selector - 1}</option></select>')
    campo = "relative campo-wrapper multi-views liga" + (" confirmed" if confirmada else " with-tabs")
    partes.append(f'<div class="{campo}">')
    for i, (slug, nombre, prob, jer, valor, rival) in enumerate(filas, start=1):
        partes.append(
            f'<div class="jugador_{4700 + i} jugador tipo_lista d-none block-new" '
            f'data-nombre="{slug}" data-probabilidad="{prob}%" data-jerarquia="{jer}" '
            f'data-estado="0" data-sancionado="0" data-valor-biwenger="{valor}" '
            f'data-rival="{rival}"><span class="nombre">{nombre}</span></div>')
    partes.append("</div></section>")
    if j_previsib is not None and not confirmada:
        partes.append(_filas_del_entrenador(j_previsib))
    if pie:
        partes.append(f'<footer><a class="footer-link">{pie}</a></footer>')
    partes.append("</body></html>")
    return "".join(partes)


def _pagina_sin_marcas(*filas) -> str:
    """Una pagina sin seccion ni rotulos, como las sinteticas de las demas
    guardias del tablero: no dice de que jornada es."""
    return "<html><body>" + "".join(
        f'<div class="tipo_lista jugador_{i}" data-nombre="{slug}" '
        f'data-probabilidad="{prob}%" data-jerarquia="{jer}" data-estado="0" '
        f'data-sancionado="0" data-valor-biwenger="{valor}">'
        f'<span class="nombre">{nombre}</span></div>'
        for i, (slug, nombre, prob, jer, valor, _) in enumerate(filas, start=1)
    ) + "</body></html>"


FILAS_VILLARREAL = [
    ("sergi-cardona", "Sergi Cardona", 0, 40, 6_100_000, "VAL"),
    ("peter-gulacsi", "Péter Gulácsi", 100, 50, 5_000_000, "VAL"),
    ("juan-foyth", "Juan Foyth", 100, 30, 3_210_000, "VAL"),
]
FILAS_ALAVES = [
    ("jonny", "Jonny", 50, 30, 2_400_000, "ESP"),
    ("antonio-blanco", "Antonio Blanco", 80, 50, 2_540_000, "ESP"),
]

# El 24/10 por la tarde: el Villarreal ya jugo (confirmada de la J10) y
# el Alaves ya tiene su pronostico de la J11.
VILLARREAL_J10 = _pagina(10, True, FILAS_VILLARREAL)
ALAVES_J11 = _pagina(11, False, FILAS_ALAVES)
# El 25/10 por la manana: el Villarreal ya en la J11 (Cardona al 50 %).
VILLARREAL_J11 = _pagina(11, False, [("sergi-cardona", "Sergi Cardona", 50, 40, 6_100_000, "ESP")]
                         + FILAS_VILLARREAL[1:])

PAGINAS = {"villarreal": VILLARREAL_J10, "alaves": ALAVES_J11}


def _snapshot(*ids) -> dict:
    """La foto con `ids` en nuestra plantilla: el catalogo con los tres
    del 24/10 y sus dos equipos."""
    jugadores = {
        CARDONA: ("Sergi Cardona", 1, 6_100_000),
        GULACSI: ("Péter Gulácsi", 1, 5_000_000),
        JONNY: ("Jonny", 2, 2_400_000),
    }
    catalogo = {"data": {
        "players": {str(p): {"id": p, "name": n, "teamID": t, "price": v, "status": "ok"}
                    for p, (n, t, v) in jugadores.items()},
        "teams": {"1": {"id": 1, "name": "Villarreal"}, "2": {"id": 2, "name": "Alavés"}},
    }}
    return {
        "my_team": [{"id": p, "name": jugadores[p][0], "teamID": jugadores[p][1],
                     "price": jugadores[p][2]} for p in ids],
        "catalog": catalogo,
    }


def _con_ff_de_mentira(funcion, paginas, tablero_previo=None, encendido=True):
    """
    `refresh_board` sin red, con el reloj parado en `AHORA` y el tablero
    en una carpeta temporal. Con la lista de objetivos de siempre:
    `BORDALAS_OBJETIVOS_EL_CATALOGO` se quita mientras tanto. Y con LA
    JORNADA DE CADA PAGINA puesta o quitada por la prueba.

    Devuelve (lo que devolvio, lo que quedo escrito en el disco, las
    paginas pedidas).
    """
    original = (ff.BOARD_FILE, ff.fetch, ff.load_absences, ff.datetime)
    catalogo = os.environ.pop(ff.ENV_EL_CATALOGO, None)
    pedidas = []

    def fetch(session, url):
        pedidas.append(url.rsplit("/", 1)[-1])
        return paginas.get(url.rsplit("/", 1)[-1], "<html></html>")

    with tempfile.TemporaryDirectory() as carpeta, _interruptor("1" if encendido else None):
        ff.BOARD_FILE = Path(carpeta) / "board.json"
        if tablero_previo is not None:
            ff.BOARD_FILE.write_text(json.dumps(tablero_previo), encoding="utf-8")
        ff.fetch = fetch
        ff.load_absences = lambda session, matchday: ({}, {})
        ff.datetime = _Reloj
        try:
            tablero = funcion()
            en_disco = (json.loads(ff.BOARD_FILE.read_text(encoding="utf-8"))
                        if ff.BOARD_FILE.exists() else None)
            return tablero, en_disco, pedidas
        finally:
            ff.BOARD_FILE, ff.fetch, ff.load_absences, ff.datetime = original
            if catalogo is not None:
                os.environ[ff.ENV_EL_CATALOGO] = catalogo


def _el_tablero_del_24_10(encendido=True):
    return _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(CARDONA, GULACSI, JONNY), 11, force=True,
                                 session=object()),
        PAGINAS, encendido=encendido)


# Las claves que pone LA JORNADA DE CADA PAGINA, y ninguna mas.
NUEVAS_DE_LA_FICHA = ("ff_page_matchday", "ff_page_lineup", "ff_de_otra_jornada")
NUEVAS_DEL_EQUIPO = ("page_matchday", "page_lineup", "page_matchday_source")
NUEVAS_DE_LA_METADATA = ("pages_other_matchday", "pages_without_matchday",
                         "players_other_matchday")


def _sin_lo_nuevo(tablero) -> dict:
    """El tablero sin EXACTAMENTE las claves nuevas. Con `del`: si alguna
    no esta, revienta (encendido tienen que estar todas)."""
    copia = json.loads(json.dumps(tablero))
    for ficha in copia.get("players") or []:
        for clave in NUEVAS_DE_LA_FICHA:
            del ficha[clave]
    for equipo in (copia.get("teams") or {}).values():
        for clave in NUEVAS_DEL_EQUIPO:
            del equipo[clave]
    for clave in NUEVAS_DE_LA_METADATA:
        del copia["metadata"][clave]
    return copia


def _jornada(html):
    pagina = ff.la_jornada_de_la_pagina(html)
    return (pagina["matchday"], pagina["lineup"], pagina["source"], pagina["agree"])


# ------------------------------------------------------------------
# 1. LA JORNADA DE UNA PAGINA
# ------------------------------------------------------------------

def test_lee_la_jornada_de_la_pagina():
    # (a) "Posible alineacion J11", con su "Previsib. J11".
    assert _jornada(ALAVES_J11) == (11, "POSIBLE", "CABECERA", True), _jornada(ALAVES_J11)
    # La misma respuesta con la sopa ya hecha, y la que da parse_team_page.
    assert ff.la_jornada_de_la_pagina(BeautifulSoup(ALAVES_J11, "html.parser")) == \
        ff.la_jornada_de_la_pagina(ALAVES_J11)
    assert ff.parse_team_page(ALAVES_J11, con_la_jornada=True)["page"] == \
        ff.la_jornada_de_la_pagina(ALAVES_J11)

    # (b) "Alineacion confirmada J10": `past`, data-confirmed=1 y sin las
    # filas del entrenador (por eso su previsibilidad sale None).
    assert _jornada(VILLARREAL_J10) == (10, "CONFIRMADA", "CABECERA", True), \
        _jornada(VILLARREAL_J10)
    assert ff.parse_team_page(VILLARREAL_J10)["team"]["predictability_percent"] is None
    assert ff.parse_team_page(ALAVES_J11)["team"]["predictability_percent"] == 44.0

    # (c) El DOM de septiembre: sin la jornada en la cabecera y el selector
    # sin data-confirmed. La da el selector (con o sin el rotulo).
    septiembre = _pagina(8, False, FILAS_ALAVES, cabecera=False, con_data_confirmed=False)
    assert _jornada(septiembre) == (8, "POSIBLE", "SELECTOR", True), _jornada(septiembre)
    confirmada_de_septiembre = _pagina(8, True, FILAS_ALAVES, cabecera=False,
                                       con_data_confirmed=False)
    assert _jornada(confirmada_de_septiembre) == (8, "CONFIRMADA", "SELECTOR", True), \
        _jornada(confirmada_de_septiembre)

    # (d) Solo el rotulo "Previsib. J9".
    rotulo = _pagina(9, False, FILAS_ALAVES, cabecera=False, selector=False)
    assert _jornada(rotulo) == (9, "POSIBLE", "PREVISIBILIDAD", True), _jornada(rotulo)

    # (e) Sin ninguna marca: no hay jornada (con seccion o sin ella).
    nada = _pagina(10, False, FILAS_ALAVES, cabecera=False, selector=False, previsib=False)
    assert _jornada(nada) == (None, "POSIBLE", None, False), _jornada(nada)
    sin_seccion = _pagina_sin_marcas(*FILAS_ALAVES)
    assert _jornada(sin_seccion) == (None, None, None, False), _jornada(sin_seccion)

    # (f) Las trampas no se miran: la pestana del calendario (6, en todas),
    # la navegacion "Espanyol J10" (su proxima), el pie "Jornada 11" (de
    # toda la web) y `tipo` "previa" en una confirmada. Es la J9.
    trampas = _pagina(9, True, FILAS_VILLARREAL, nav="Espanyol J10",
                      pie="Posibles alineaciones Jornada 11", tipo="previa")
    assert _jornada(trampas) == (9, "CONFIRMADA", "CABECERA", True), _jornada(trampas)
    # Y una pestana sola no es una jornada.
    pestana = '<div class="tab checked" data-jornada="6"> J10</div>'
    assert _jornada(pestana) == (None, None, None, False), _jornada(pestana)

    # (g) Dos marcas que no coinciden no son una jornada.
    choque = _pagina(10, False, FILAS_ALAVES, selector=11, previsib=False)
    assert _jornada(choque) == (None, "POSIBLE", None, False), _jornada(choque)
    choque_del_rotulo = _pagina(10, False, FILAS_ALAVES, previsib=11)
    assert _jornada(choque_del_rotulo)[0] is None, _jornada(choque_del_rotulo)

    # (h) Con basura, todo None y sin lanzar.
    for basura in ("", None, 42, {"a": 1}, b"<p>basura</p>", "<<<>>>", object(),
                   '<section class="alineacion_wrapper" data-equipo="1"><h2 class="lineup-title">'
                   '<span class="jornada">J</span></h2></section>'):
        r = ff.la_jornada_de_la_pagina(basura)
        assert r["matchday"] is None and r["agree"] is False and r["source"] is None, \
            (repr(basura)[:40], r)


# ------------------------------------------------------------------
# 2. EL CASO DEL 24/10
# ------------------------------------------------------------------

def test_la_regresion_del_24_10():
    tablero, en_disco, pedidas = _el_tablero_del_24_10()
    assert sorted(pedidas) == ["alaves", "villarreal"], pedidas
    fichas = {p["player_id"]: p for p in tablero["players"]}
    assert sorted(fichas) == sorted([CARDONA, GULACSI, JONNY]), sorted(fichas)

    # Cardona: el 0 % sigue siendo 0 % (no se toca un numero), pero ahora
    # se sabe de donde sale.
    cardona = fichas[CARDONA]
    assert cardona["starter_probability"] == 0.0 and cardona["consensus"] == "BENCH", cardona
    assert (cardona["ff_page_matchday"], cardona["ff_page_lineup"],
            cardona["ff_de_otra_jornada"]) == (10, "CONFIRMADA", True), cardona
    gulacsi = fichas[GULACSI]
    assert gulacsi["starter_probability"] == 100.0 and gulacsi["ff_de_otra_jornada"] is True, \
        gulacsi
    jonny = fichas[JONNY]
    assert jonny["starter_probability"] == 50.0, jonny
    assert (jonny["ff_page_matchday"], jonny["ff_page_lineup"],
            jonny["ff_de_otra_jornada"]) == (11, "POSIBLE", False), jonny

    meta = tablero["metadata"]
    assert meta["pages_other_matchday"] == ["Villarreal"], meta
    assert meta["players_other_matchday"] == 2, meta
    assert meta["pages_without_matchday"] == [], meta

    villarreal = tablero["teams"]["Villarreal"]
    assert (villarreal["page_matchday"], villarreal["page_lineup"],
            villarreal["page_matchday_source"]) == (10, "CONFIRMADA", "CABECERA"), villarreal
    assert tablero["teams"]["Alavés"]["page_matchday"] == 11, tablero["teams"]

    # Las plantillas, las de siempre.
    assert set(tablero["plantillas"]["Villarreal"]["players"][0]) == \
        set(ff.CAMPOS_DE_LA_PLANTILLA)
    assert en_disco == tablero


def test_apagado_el_tablero_no_cambia_ni_un_byte():
    apagado, en_disco_apagado, _ = _el_tablero_del_24_10(encendido=False)
    encendido, en_disco_encendido, _ = _el_tablero_del_24_10(encendido=True)

    # Apagado, ni una clave nueva en ningun sitio.
    for ficha in apagado["players"]:
        assert not set(ficha) & set(NUEVAS_DE_LA_FICHA), sorted(ficha)
    for equipo in apagado["teams"].values():
        assert not set(equipo) & set(NUEVAS_DEL_EQUIPO), sorted(equipo)
    assert not set(apagado["metadata"]) & set(NUEVAS_DE_LA_METADATA), sorted(apagado["metadata"])

    # parse_team_page y build_player_entry sin lo nuevo: lo de siempre.
    assert set(ff.parse_team_page(VILLARREAL_J10)) == {"players", "team"}
    assert set(ff.parse_team_page(VILLARREAL_J10, con_la_jornada=True)) == \
        {"players", "team", "page"}
    pagina = ff.parse_team_page(VILLARREAL_J10)
    objetivo = {"id": CARDONA, "name": "Sergi Cardona", "scope": "ROSTER", "price": 6_100_000}
    emparejado = {"record": pagina["players"][0], "target": objetivo, "method": "NAME",
                  "score": 1.0, "margin": 1.0}
    assert ff.build_player_entry(emparejado, pagina["team"], "Villarreal") == \
        ff.build_player_entry(emparejado, pagina["team"], "Villarreal", pagina=None, jornada=11)
    assert not set(ff.build_player_entry(emparejado, pagina["team"], "Villarreal")) & \
        set(NUEVAS_DE_LA_FICHA)

    # Encendido solo AÑADE claves: quitandolas, es el apagado entero.
    assert json.dumps(apagado, sort_keys=True) == \
        json.dumps(_sin_lo_nuevo(encendido), sort_keys=True)
    # Y lo escrito es lo devuelto, en los dos.
    assert en_disco_apagado == apagado and en_disco_encendido == encendido


def test_sin_jornada_no_se_marca():
    sin_marca = _pagina_sin_marcas(*FILAS_ALAVES)
    tablero, _, _ = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(JONNY), 11, force=True, session=object()),
        {"alaves": sin_marca})
    jonny = {p["player_id"]: p for p in tablero["players"]}[JONNY]
    assert (jonny["ff_page_matchday"], jonny["ff_page_lineup"],
            jonny["ff_de_otra_jornada"]) == (None, None, False), jonny
    meta = tablero["metadata"]
    assert meta["pages_without_matchday"] == ["Alavés"], meta
    assert meta["pages_other_matchday"] == [] and meta["players_other_matchday"] == 0, meta
    assert tablero["teams"]["Alavés"]["page_matchday"] is None, tablero["teams"]

    # Dos marcas que no coinciden: tampoco se marca, y tambien se dice.
    choque = _pagina(10, False, FILAS_ALAVES, selector=11, previsib=False)
    tablero, _, _ = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(JONNY), 11, force=True, session=object()),
        {"alaves": choque})
    jonny = {p["player_id"]: p for p in tablero["players"]}[JONNY]
    assert jonny["ff_de_otra_jornada"] is False, jonny
    assert tablero["metadata"]["pages_without_matchday"] == ["Alavés"], tablero["metadata"]

    # La ficha suelta: sin saber una de las dos jornadas, no se marca;
    # "10" y 10 son la misma; un aplazado (la J6 en la semana de la J10)
    # si es otra.
    pagina = ff.parse_team_page(ALAVES_J11)
    objetivo = {"id": JONNY, "name": "Jonny", "scope": "ROSTER", "price": 2_400_000}
    emparejado = {"record": pagina["players"][0], "target": objetivo, "method": "NAME",
                  "score": 1.0, "margin": 1.0}

    def marca(de_la_pagina, jornada):
        return ff.build_player_entry(emparejado, pagina["team"], "Alavés",
                                     pagina=de_la_pagina, jornada=jornada)["ff_de_otra_jornada"]

    assert marca({"matchday": 10}, None) is False
    assert marca({}, 11) is False
    assert marca({"matchday": None}, 11) is False
    assert marca("basura", 11) is False
    assert marca({"matchday": 10}, "10") is False
    assert marca({"matchday": 6}, 10) is True
    assert marca({"matchday": 12}, 11) is True


def test_al_completar_cada_ficha_lleva_su_marca():
    # Primera vuelta: solo Cardona, de la confirmada de la J10.
    primero, _, _ = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(CARDONA), 11, force=True, session=object()),
        {"villarreal": VILLARREAL_J10})
    assert primero["players"][0]["ff_de_otra_jornada"] is True, primero["players"]

    # Segunda vuelta, misma jornada y fresca: falta Jonny y solo se baja
    # el Alaves. Aunque la del Villarreal ya este en la J11, no se ha
    # vuelto a bajar: Cardona lleva la marca de SU bajada.
    previo = json.loads(json.dumps(primero))
    segundo, _, pedidas = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(CARDONA, JONNY), 11, session=object()),
        {"villarreal": VILLARREAL_J11, "alaves": ALAVES_J11}, previo)
    assert segundo["cache"]["status"] == "TOPPED_UP", segundo["cache"]
    assert pedidas == ["alaves"], pedidas
    fichas = {p["player_id"]: p for p in segundo["players"]}
    assert fichas[CARDONA]["ff_de_otra_jornada"] is True, fichas[CARDONA]
    assert fichas[JONNY]["ff_de_otra_jornada"] is False, fichas[JONNY]
    # Sale de las FICHAS: el Villarreal ya no esta en `teams`.
    assert "Villarreal" not in segundo["teams"], sorted(segundo["teams"])
    assert segundo["metadata"]["pages_other_matchday"] == ["Villarreal"], segundo["metadata"]
    assert segundo["metadata"]["players_other_matchday"] == 1, segundo["metadata"]

    # Y la cache servida (HIT) deja las marcas como estaban.
    tercero, _, pedidas = _con_ff_de_mentira(
        lambda: ff.refresh_board(_snapshot(CARDONA, JONNY), 11, session=object()),
        {"villarreal": VILLARREAL_J11, "alaves": ALAVES_J11}, json.loads(json.dumps(segundo)))
    assert tercero["cache"]["status"] == "HIT" and pedidas == [], (tercero["cache"], pedidas)
    assert tercero["players"] == segundo["players"]


# ------------------------------------------------------------------
# 3. LA MEJORA DEL ONCE
# ------------------------------------------------------------------

def _once_del_incidente():
    """El once de la guardia de la mejora con Flojo (10) al 0 %: el de una
    confirmada de otra jornada."""
    once = [dict(p) for p in base.ONCE]
    once[0]["starter_probability"] = 0
    return once


def test_la_mejora_no_abre_hueco_con_otra_jornada():
    once = _once_del_incidente()
    otra = frozenset({10})

    # APAGADO, el incidente: el 0 % abre un hueco, SOLO SI SUBE se salta y
    # entra el 20, que no sube.
    apagado = base._d(once=once, solo_si_sube=True)
    assert base._pujas(apagado) == [(20, 10)], apagado["plan"]
    assert "de_otra_jornada" not in apagado["plan"], apagado["plan"]

    # ENCENDIDO: Flojo no sale, y el plan dice por que.
    encendido = base._d(once=once, solo_si_sube=True, de_otra_jornada=otra)
    assert base._pujas(encendido) == [], encendido["plan"]
    assert encendido["plan"]["de_otra_jornada"] == [
        {"id": 10, "nombre": "Flojo", "titularidad": 0}], encendido["plan"]

    # Lo mismo con el % de la plantilla entera (`probabilidades`, el que
    # manda en produccion).
    assert base._pujas(base._d(solo_si_sube=True, probabilidades={10: 0})) == [(20, 10)]
    assert base._pujas(base._d(solo_si_sube=True, probabilidades={10: 0},
                               de_otra_jornada=otra)) == []

    # Sin SOLO SI SUBE: quitar el hueco no bastaria (el 0 % pone el cambio
    # gratis en puntos). Encendido, el 0 % de otra jornada no lo pone.
    assert base._pujas(base._d(once=once)) == [(20, 10)]
    assert base._pujas(base._d(once=once, de_otra_jornada=otra)) == []

    # Un hueco de verdad (lesionado o sancionado) lo sigue siendo: entra
    # aunque no suba, a precio + 1 %.
    for estado in ("injured", "sanctioned"):
        d = base._d(once=once, solo_si_sube=True, estados={10: estado}, de_otra_jornada=otra)
        assert base._pujas(d) == [(20, 10)], (estado, d["plan"])
        puja = next(a for a in d["acciones"] if a["accion"] == "PUJAR")
        assert puja["importe"] == mejora.la_puja(3_700_000), puja
        assert "de_otra_jornada" not in d["plan"], d["plan"]

    # Uno que no es de los nuestros marcado: exactamente lo de siempre.
    for k in (dict(once=once, solo_si_sube=True), dict(once=once), dict()):
        assert base._d(**k, de_otra_jornada=frozenset({999})) == base._d(**k), k


def test_apagado_la_mejora_decide_lo_de_siempre():
    escenarios = base.ESCENARIOS_APAGADO() + [
        base._base(solo_si_sube=True),
        base._base(once=_once_del_incidente(), solo_si_sube=True),
        base._base(puja_fuerte=True),
        base._base(en_9900=True),
        base._base(horas_jornada=30),
        base._en_el_mundo([40], [41], calendario_de_puntos=base._ctx()),
        base._en_el_mundo([40, 44], [41, 43, 45], caja=-2_000_000, horas_jornada=70,
                          calendario_de_puntos=base._ctx()),
    ]
    for k in escenarios:
        antes = mejora.decidir(**k)
        vacio = mejora.decidir(**k, de_otra_jornada=frozenset())
        assert antes == vacio, (antes["plan"], vacio["plan"])
        assert "de_otra_jornada" not in antes["plan"], antes["plan"]
    # La huella de siempre de la guardia de la mejora, pasando el vacio.
    huella = base._huella([mejora.decidir(**k, de_otra_jornada=frozenset())
                           for k in base.ESCENARIOS_APAGADO()])
    assert huella == base.HUELLA_DE_ANTES, huella


def _correr(encendido, tablero=None, de_otra=None):
    """
    `correr` de la mejora con TODO dado: la foto, el panel, la vuelta,
    el reloj y lo que si no se lee de produccion. Los libros y el tablero
    de FF (si se da, con el nombre de `TABLERO_FF`) en un temporal, junto
    al libro de la mejora.

    El incidente del 24/10 con SOLO SI SUBE puesto: nuestro Roberto (40)
    con el 0 % de la plantilla y el Casero (41) del Computer, que no sube.
    """
    status = {
        "todaLaLiga": {"players": list(base.MUNDO.values())},
        "lineup": {"players": [base._nuestro(40, 0)]},
        "roster": {"players": [base._nuestro(40, 0)]},
        "libro_del_escaparate": {"players": [base._del_computer(41)]},
    }
    snapshot = {
        "league": {"user": {"id": 7}},
        "market": {"sales": [{"player": {"id": 41}, "user": None,
                              "price": base.MUNDO[41]["price"]}],
                   "offers": [],
                   "status": {"maximumBid": 14_000_000, "balance": 500_000}},
        "my_team": [{"id": 40, "price": base.MUNDO[40]["price"]}],
        "catalog": {"data": {"players": {}}},
    }
    escritor = base._Escritor()
    interruptores = {
        mejora.ENV: "1", mejora.ENV_CALENDARIO: None, mejora.ENV_PUJA_FUERTE: None,
        mejora.ENV_PUJA_EN_9900: None, mejora.ENV_SOLO_SI_SUBE: "1",
        "BORDALAS_LA_CARTERA": None,
    }
    with tempfile.TemporaryDirectory() as carpeta, base._interruptores(interruptores), \
            _interruptor("1" if encendido else None):
        rutas = {k: os.path.join(carpeta, f"{k}.json") for k in ("mejora", "ronda", "chollos")}
        for ruta in rutas.values():
            Path(ruta).write_text("{}")
        if tablero is not None:
            (Path(carpeta) / mejora.TABLERO_FF.name).write_text(json.dumps(tablero))
        fuera = {"orden": {}, "vetados": set(), "protegidos": set(), "rotando": set(),
                 "libro_ronda": rutas["ronda"], "libro_chollos": rutas["chollos"],
                 "horas_jornada": 100.0, "puede_escribir": True, "en_curso": False}
        if de_otra is not None:
            fuera["de_otra_jornada"] = de_otra
        salida = mejora.correr(status=status, snapshot=snapshot, v10={},
                               escritor_factory=lambda: escritor, ahora=base.AHORA,
                               libro_ruta=rutas["mejora"], calendario={}, de_fuera=fuera)
    return salida, escritor


TABLERO_CON_ROBERTO = {"matchday": 11, "players": [
    {"player_id": 40, "starter_probability": 0.0, "ff_page_matchday": 10,
     "ff_page_lineup": "CONFIRMADA", "ff_de_otra_jornada": True},
    {"player_id": 41, "starter_probability": 80.0, "ff_page_matchday": 11,
     "ff_page_lineup": "POSIBLE", "ff_de_otra_jornada": False},
]}


def test_correr_lee_las_marcas_del_tablero():
    # Las marcas: solo `ff_de_otra_jornada` exactamente True.
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / mejora.TABLERO_FF.name
        ruta.write_text(json.dumps({"matchday": 11, "players": [
            {"player_id": 10, "ff_de_otra_jornada": True},
            {"player_id": 11, "ff_de_otra_jornada": False},
            {"player_id": 12},
            {"player_id": "13", "ff_de_otra_jornada": True},
            {"player_id": 14, "ff_de_otra_jornada": "true"},
            {"player_id": None, "ff_de_otra_jornada": True},
            {"player_id": "basura", "ff_de_otra_jornada": True},
            "basura", 7, None, [],
        ]}))
        assert mejora.las_de_otra_jornada(ruta) == frozenset({10, 13}), \
            mejora.las_de_otra_jornada(ruta)
        assert mejora.las_de_otra_jornada(str(ruta)) == frozenset({10, 13})
        assert mejora.las_de_otra_jornada(Path(carpeta) / "no_esta.json") == frozenset()
        for basura in ("{ no es json", "[]", "3", json.dumps({"players": {"10": {}}}),
                       json.dumps({"players": None}), json.dumps({"players": "texto"})):
            ruta.write_text(basura)
            assert mejora.las_de_otra_jornada(ruta) == frozenset(), basura

    # APAGADO, con el tablero marcando a Roberto: lo de hoy, la puja.
    apagado, escritor = _correr(False, TABLERO_CON_ROBERTO)
    assert escritor.llamadas == [("PUJAR", 41, mejora.la_puja(3_000_000))], \
        (apagado["motivo"], escritor.llamadas, apagado["plan"])
    assert "de_otra_jornada" not in apagado["plan"], apagado["plan"]

    # ENCENDIDO: Roberto no sale, no se escribe nada y el plan lo dice.
    encendido, escritor = _correr(True, TABLERO_CON_ROBERTO)
    assert encendido["motivo"] == "NADA_QUE_HACER" and escritor.llamadas == [], \
        (encendido["motivo"], escritor.llamadas)
    assert encendido["plan"]["de_otra_jornada"] == [
        {"id": 40, "nombre": "Roberto", "titularidad": 0}], encendido["plan"]

    # Lo dado en `de_fuera` manda sobre el fichero: vacio, la puja.
    dado, escritor = _correr(True, TABLERO_CON_ROBERTO, de_otra=[])
    assert [ll[:2] for ll in escritor.llamadas] == [("PUJAR", 41)], dado
    # Y al reves: sin tablero, lo dado.
    dado, escritor = _correr(True, None, de_otra=["40"])
    assert escritor.llamadas == [] and dado["plan"]["de_otra_jornada"][0]["id"] == 40, dado
    # Encendido sin tablero junto al libro: lo de siempre.
    sin_tablero, escritor = _correr(True, None)
    assert [ll[:2] for ll in escritor.llamadas] == [("PUJAR", 41)], sin_tablero


# ------------------------------------------------------------------
# 4. LO QUE NO CAMBIA
# ------------------------------------------------------------------

def test_el_lookup_no_cambia():
    encendido, _, _ = _el_tablero_del_24_10(encendido=True)
    apagado, _, _ = _el_tablero_del_24_10(encendido=False)
    antes = lookup.expected_matchday()
    lookup.set_expected_matchday(11)
    try:
        con_marcas = lookup.build_starter_lookup(json.loads(json.dumps(encendido)))
        sin_marcas = lookup.build_starter_lookup(_sin_lo_nuevo(encendido))
        de_apagado = lookup.build_starter_lookup(apagado)
    finally:
        lookup.set_expected_matchday(antes)
    assert con_marcas and con_marcas == sin_marcas == de_apagado, (con_marcas, sin_marcas)
    assert (con_marcas[CARDONA]["probability"], con_marcas[CARDONA]["consensus"]) == \
        (0.0, "BENCH"), con_marcas[CARDONA]


class _EntornoRoto:
    def get(self, *a, **k):
        raise RuntimeError("el entorno no se puede leer")


def test_nace_apagado():
    assert ff.ENV_LA_JORNADA_DE_CADA_PAGINA == INTERRUPTOR
    assert mejora.ENV_LA_JORNADA_DE_CADA_PAGINA == INTERRUPTOR
    lectores = (ff.la_jornada_de_cada_pagina, mejora.la_jornada_de_cada_pagina_activa)
    with _interruptor(None):
        for lee in lectores:
            assert lee() is False, lee.__name__
    for valor in ("1", "true", "TRUE", "Si", "yes", " si ", "Yes\n"):
        with _interruptor(valor):
            for lee in lectores:
                assert lee() is True, (lee.__name__, valor)
    for valor in ("0", "no", "", "false", "  "):
        with _interruptor(valor):
            for lee in lectores:
                assert lee() is False, (lee.__name__, valor)
    # Al llamarse, no al importarse: cambia dentro de la misma prueba.
    with _interruptor("1"):
        assert all(lee() for lee in lectores)
        os.environ.pop(INTERRUPTOR, None)
        assert not any(lee() for lee in lectores)
    # Nunca lanza.
    real = os.environ
    os.environ = _EntornoRoto()
    try:
        for lee in lectores:
            assert lee() is False, lee.__name__
    finally:
        os.environ = real


TESTS = [
    test_lee_la_jornada_de_la_pagina,
    test_la_regresion_del_24_10,
    test_apagado_el_tablero_no_cambia_ni_un_byte,
    test_sin_jornada_no_se_marca,
    test_al_completar_cada_ficha_lleva_su_marca,
    test_la_mejora_no_abre_hueco_con_otra_jornada,
    test_apagado_la_mejora_decide_lo_de_siempre,
    test_correr_lee_las_marcas_del_tablero,
    test_el_lookup_no_cambia,
    test_nace_apagado,
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
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
