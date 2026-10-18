"""
EL INFORME DE LA MAÑANA (18/10/2026). Guardias de
`src/intelligence/el_informe_de_la_manana.py`
(`BORDALAS_EL_INFORME_DE_LA_MANANA`, fase 1: solo observa).

    1. Las dos formulas, clavadas a los numeros del laboratorio del
       18/10: el caso Carvajal da SUBE alta (+35) y PUNTUA baja (1,3).
    2. Quien es nuevo se mira contra el mercado del ultimo dia apuntado
       (la linea DIA del libro; si no hay, la valoracion y el
       escaparate), de reset a reset, con el cambio de hora bien puesto.
    3. Una vez por dia de mercado: la segunda vuelta del dia no apunta
       nada; una foto de antes del reset o un mercado vacio, tampoco.
    4. La red que falla deja la señal SIN LEER, no rompe nada: una
       pagina por equipo, tope de paginas, tope de tiempo DE RELOJ
       (tambien dentro de la descarga) y corte tras tres fallos
       seguidos. Una pagina que llega sin ninguna noticia con fecha
       tampoco es una pagina leida. La prensa vieja o no disponible,
       tampoco.
    4b. La ventana de las noticias es la del laboratorio (las 72 h que
       acaban 15 min tras el reset de hoy) y el libro guarda todos los
       titulares con su fecha. El mercado sin renovar no se apunta. La
       cuota de partidos se cuenta contra lo que ha jugado el equipo.
       El cambio de hoy sale del historico si Biwenger no lo trae.
    5. Los titulares se clasifican con las reglas del laboratorio
       (BAJA / DUDA / VUELTA / TITULARIDAD / SANCION / RECOMENDADO /
       ANALISIS) y el HTML solo se lee.
    6. Nace apagado (lo apaga esta guardia, no el entorno) y nunca lanza.
    7. Nunca escribe fuera de su libro, y ninguna ruta de decision lo lee.

Todo con datos de mentira: la hora se pasa siempre, la foto, el
tablero de FF, la prensa y JP son dicts de este fichero, las paginas
de FF salen de un `fetch` de mentira y el libro va a una carpeta
temporal. No se lee el estado de produccion, ni el reloj, ni se sale a
la red.
"""

from __future__ import annotations

import builtins
import json
import os
import sys
import tempfile
import time

from datetime import datetime, timedelta, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.intelligence import el_informe_de_la_manana as M     # noqa: E402
from src.intelligence.el_informe_de_la_manana import (         # noqa: E402
    ENV, activa, clasificar_titular, correr, el_cambio_de_hoy, el_indice,
    el_mercado_anterior, el_parte, el_ultimo_informe, en_la_ventana, la_fecha_de_ff,
    las_noticias_de_los_equipos, leer_las_noticias, los_nuevos, puntuar,
)


UTC = timezone.utc
AHORA = datetime(2026, 10, 18, 5, 20, tzinfo=UTC)       # dom 07:20 Madrid, tras el reset
AYER = datetime(2026, 10, 17, 5, 20, tzinfo=UTC)
FOTO_HOY = "2026-10-18T07:16:00"                        # sin zona: hora de Madrid
FOTO_AYER = "2026-10-17T07:16:00"
YO = 99


# ------------------------------------------------------------------
# EL CATALOGO DE MENTIRA
# ------------------------------------------------------------------
#
#     100  Carvajal   Getafe    defensa  3,2 M +290k, 0 partidos, FF 30 %
#     101  Borja      Celta     delantero 2 M  -20k, 30 pts en 8, FF 80 %, prensa BAJA
#     102  Aspas      Celta     delantero 600k +20k, 20 pts en 5, 'injured', sin FF
#     103  Hugo Duro  Valencia  delantero 1,5 M +15k, 25 pts en 7, FF 65 %, de un manager
#     104  Blanco     R. Madrid estaba ayer y hoy: no es nuevo
#     105  Propio     R. Madrid lo vendemos nosotros: no cuenta
#     110, 111        del Celta, fuera del mercado (solo para el indice)

def _f(pid, nombre, equipo, pos, precio, inc, pts, casa, fuera, estado="ok"):
    return {"id": pid, "name": nombre, "teamID": equipo, "position": pos, "price": precio,
            "priceIncrement": inc, "points": pts, "playedHome": casa, "playedAway": fuera,
            "status": estado}


CATALOGO = {str(f["id"]): f for f in (
    _f(100, "Dani Carvajal", 8, 2, 3_200_000, 290_000, 0, 0, 0),
    _f(101, "Borja Iglesias", 5, 4, 2_000_000, -20_000, 30, 4, 4),
    _f(102, "Iago Aspas", 5, 4, 600_000, 20_000, 20, 3, 2, "injured"),
    _f(103, "Hugo Duro", 10, 4, 1_500_000, 15_000, 25, 4, 3),
    _f(104, "Antonio Blanco", 1, 3, 2_590_000, 10_000, 26, 4, 4),
    _f(105, "Propio", 1, 3, 1_000_000, 0, 10, 4, 4),
    _f(110, "Miguel Román", 5, 3, 1_000_000, 0, 10, 4, 4),
    _f(111, "Jones El-Abdellaoui", 5, 2, 500_000, 0, 5, 2, 2),
)}
EQUIPOS = {"8": {"name": "Getafe"}, "5": {"name": "Celta"}, "10": {"name": "Valencia"},
           "1": {"name": "Real Madrid"}}


def _foto(cuando=FOTO_HOY, computer=None, managers=None, propios=(105,), until=None,
          catalogo=None):
    """`until`: el de los del Computer (epoch), si se quiere; sin el, la
    foto no dice cuando acaba su mercado."""
    computer = {100: 3_200_000, 101: 2_000_000, 102: 600_000, 104: 2_590_000} \
        if computer is None else computer
    managers = {103: (7, 1_800_000)} if managers is None else managers
    hasta = {} if until is None else {"until": int(until)}
    return {
        "timestamp": cuando,
        "league": {"user": {"id": YO}},
        "market": {"sales": (
            [{"player": {"id": p}, "user": None, "price": v, **hasta} for p, v in computer.items()]
            + [{"player": {"id": p}, "user": {"id": u}, "price": v}
               for p, (u, v) in managers.items()]
            + [{"player": {"id": p}, "user": {"id": YO}, "price": 1} for p in propios])},
        "catalog": {"data": {"players": CATALOGO if catalogo is None else catalogo,
                             "teams": EQUIPOS}},
    }


DIA_DE_AYER = {"tipo": "DIA", "dia_de_mercado": "2026-10-17",
               "mercado": {"computer": [104, 120], "managers": [121]}}

TABLERO_FF = {"updated_at": "2026-10-18T05:17:00+00:00", "players": [
    {"player_id": 100, "starter_probability": 30, "minutes": 0,
     "hierarchy": {"value": 25, "label": "Revulsivo"},
     "availability": {"code": 1, "can_play": True}},
    {"player_id": 101, "starter_probability": 80},
    {"player_id": 103, "starter_probability": 65},
]}

PRENSA = {"available": True, "generated_at": "2026-10-18T05:18:00+00:00", "players": {
    "101": {"items": [{"kind": "BAJA", "source": "MARCA", "ambiguous_subject": False,
                       "published_at": "2026-10-17T20:00:00+00:00",
                       "headline": "Borja Iglesias, baja ante el Betis"}]},
    # Sujeto ambiguo: no cuenta.
    "100": {"items": [{"kind": "BAJA", "source": "RELEVO", "ambiguous_subject": True,
                       "published_at": "2026-10-17T20:00:00+00:00"}]},
    # De hace cinco dias: fuera de la ventana.
    "103": {"items": [{"kind": "DUDA", "source": "MARCA", "ambiguous_subject": False,
                       "published_at": "2026-10-13T08:00:00+00:00"}]},
}}

JP = {"updated_at": "2026-10-18T04:00:00+00:00", "players": [
    {"biwenger_remote_id": 100, "price": 3_200_000, "last_markets": {}, "injured": "0",
     "doubt": "0", "tip": "1"}]}


def _noticia(href, titular, dia, hora):
    return (f'<a href="{href}" class="noticia"><div class="info"><div class="date">'
            f'<span class="day">{dia}</span> <span class="time">{hora}</span></div></div>'
            f'<h2 class="titular mb-2">{titular}</h2></a>')


def _pagina(*noticias):
    return ("<html><body><script>window.malo = 1;</script>"
            '<div class="noticias bloque">' + "".join(noticias) + "</div></body></html>")


FF = "https://www.futbolfantasy.com/laliga/noticias/"
# La pagina de un equipo de LaLiga siempre trae noticias: la de un
# equipo sin nada de los nuestros, una con fecha que no nombra a nadie.
PAGINA_SIN_LOS_NUESTROS = _pagina(_noticia(FF + "152099-el-equipo-prepara-el-partido",
                                           "El equipo prepara el partido", "17/10", "09:00"))
PAGINAS = {
    "getafe": _pagina(
        _noticia(FF + "152001-analisis-fantasy-de-carvajal", "Análisis Fantasy de Dani "
                 "Carvajal: ficha si sale", "17/10", "20:00"),
        _noticia(FF + "151700-carvajal-lesion", "Dani Carvajal sufre una lesión en el "
                 "entrenamiento", "12/10", "10:00")),
    "celta": _pagina(
        _noticia(FF + "152010-aspas-vuelve", "Iago Aspas vuelve a entrenar con el grupo",
                 "17/10", "12:00"),
        _noticia(FF + "152011-borja-duda", "Borja Iglesias, duda para el domingo",
                 "16/10", "19:00"),
        _noticia("javascript:alert(1)", "El Celta prepara el partido", "17/10", "18:00")),
}


class _Fetch:
    """Las paginas de FF, de mentira. Cuenta las llamadas."""

    def __init__(self, paginas=None, revienta=("valencia",)):
        self.paginas = PAGINAS if paginas is None else paginas
        self.revienta = set(revienta)
        self.llamadas = []

    def __call__(self, url):
        self.llamadas.append(url)
        slug = url.rsplit("/", 1)[-1]
        if slug in self.revienta or "*" in self.revienta:
            raise ConnectionError("la red se ha caido")
        return self.paginas.get(slug, PAGINA_SIN_LOS_NUESTROS)


def _entorno(**valores):
    """Pone los interruptores (None = quitarlo) y devuelve como estaban."""
    antes = {k: os.environ.get(k) for k in valores}
    for k, v in valores.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return antes


def _libro(carpeta, *lineas):
    ruta = Path(carpeta) / "libros" / "informe.jsonl"
    if lineas:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("".join(json.dumps(x) + "\n" for x in lineas), encoding="utf-8")
    return ruta


def _correr(ruta, **k):
    base = dict(ahora=AHORA, snapshot=_foto(), libro_ruta=ruta, tablero_ff=TABLERO_FF,
                prensa=PRENSA, jp=JP, historico={}, jornadas=8, valoracion=[],
                escaparate=[], fetch=_Fetch())
    base.update(k)
    return correr(**base)


def _filas(ruta):
    return [json.loads(x) for x in Path(ruta).read_text(encoding="utf-8").splitlines() if x.strip()]


def _carvajal(**cambios):
    s = {"precio": 3_200_000, "cambio_hoy_pct": el_cambio_de_hoy(3_200_000, 290_000),
         "vuelta_ff": False, "titular_ff": 30, "jugados": 0, "jornadas": 8, "puntos": 0,
         "posicion": 2, "estado": "ok", "prensa_baja": False}
    s.update(cambios)
    return s


class _Escrituras:
    """Apunta todo lo que se abre para escribir mientras dura."""

    def __enter__(self):
        self.rutas, self.abiertos = [], []
        self._open, self._popen = builtins.open, Path.open
        self._wt, self._wb = Path.write_text, Path.write_bytes
        self._replace, self._rename = os.replace, os.rename
        yo = self

        def _escribe(modo):
            return any(c in str(modo) for c in "wax+")

        def _open(f, *a, **k):
            yo.abiertos.append(str(f))
            if _escribe(k.get("mode") or (a[0] if a else "r")):
                yo.rutas.append(os.path.abspath(str(f)))
            return yo._open(f, *a, **k)

        def _popen(p, *a, **k):
            yo.abiertos.append(str(p))
            if _escribe(k.get("mode") or (a[0] if a else "r")):
                yo.rutas.append(os.path.abspath(str(p)))
            return yo._popen(p, *a, **k)

        def _wt(p, *a, **k):
            yo.rutas.append(os.path.abspath(str(p)))
            return yo._wt(p, *a, **k)

        def _wb(p, *a, **k):
            yo.rutas.append(os.path.abspath(str(p)))
            return yo._wb(p, *a, **k)

        def _replace(a, b, *r, **k):
            yo.rutas.append(os.path.abspath(str(b)))
            return yo._replace(a, b, *r, **k)

        def _rename(a, b, *r, **k):
            yo.rutas.append(os.path.abspath(str(b)))
            return yo._rename(a, b, *r, **k)

        builtins.open, Path.open = _open, _popen
        Path.write_text, Path.write_bytes = _wt, _wb
        os.replace, os.rename = _replace, _rename
        return self

    def __exit__(self, *exc):
        builtins.open, Path.open = self._open, self._popen
        Path.write_text, Path.write_bytes = self._wt, self._wb
        os.replace, os.rename = self._replace, self._rename
        return False


ENCENDIDO = {ENV: "1"}


# ------------------------------------------------------------------
# 1. LAS FORMULAS, CLAVADAS AL LABORATORIO
# ------------------------------------------------------------------

def test_la_formula_esta_clavada_al_laboratorio():
    # VUELTA 2,0 y no 2,5 (18/10, tarde): vuelta a medir con la ventana de
    # las noticias del modulo, la de la primera medida veia el futuro.
    assert (M.SUBE_CONSTANTE, M.SUBE_POR_PUNTO_DE_CAMBIO, M.SUBE_VUELTA, M.SUBE_BARATO) == (
        -1.0, 4.5, 2.0, 3.0)
    assert M.PESOS == "laboratorio-2026-10-18-v2"
    assert (M.CAMBIO_MINIMO, M.CAMBIO_MAXIMO, M.BARATO_POR_DEBAJO_DE) == (-5.0, 8.0, 1_000_000)
    assert (M.PUNTUA_CONSTANTE, M.PUNTUA_K, M.PUNTUA_PRENSA_BAJA,
            M.PUNTUA_ESTADO_NO_OK_SIN_FF) == (0.5, 0.85, -1.0, -1.2)
    assert M.R_POR_POSICION == {1: 5.1, 2: 3.2, 3: 3.5, 4: 3.5} and M.ENCOGIMIENTO == 2
    assert M.VENTANA_HORAS == 72 and M.NOTICIAS_HASTA_MINUTOS_TRAS_EL_RESET == 15

    # CARVAJAL (18/10): 3,2 M, +290k (un +10 %, se cuenta +8), 30 % de
    # titular, 0 partidos, defensa. Sube alta y puntua baja.
    assert abs(el_cambio_de_hoy(3_200_000, 290_000) - 9.9656) < 1e-3
    n = puntuar(_carvajal())
    assert set(n) == {"sube", "puntua", "por_que"}, n
    assert n["sube"] == 35.0 and n["puntua"] == 1.32, n
    assert n["sube"] >= 30 and n["puntua"] < 1.5
    assert any("se cuenta +8,0" in p for p in n["por_que"]), n["por_que"]

    # Un titular que no sube: sube negativa, puntua alta.
    n = puntuar({"precio": 2_500_000, "cambio_hoy_pct": el_cambio_de_hoy(2_500_000, -30_000),
                 "vuelta_ff": False, "titular_ff": 80, "jugados": 8, "jornadas": 8,
                 "puntos": 40, "posicion": 3, "estado": "ok", "prensa_baja": False})
    assert n["sube"] == -6.3 and n["puntua"] == 3.7, n

    # Cada termino pesa lo suyo, ni mas ni menos.
    base = puntuar(_carvajal(cambio_hoy_pct=1.0, precio=1_000_000))
    assert base["sube"] == 3.5, base
    assert puntuar(_carvajal(cambio_hoy_pct=1.0, precio=1_000_000, vuelta_ff=True))["sube"] == 5.5
    assert puntuar(_carvajal(cambio_hoy_pct=1.0, precio=999_999))["sube"] == 6.5
    assert puntuar(_carvajal(cambio_hoy_pct=-12.0))["sube"] == -23.5      # recortado a -5
    assert puntuar(_carvajal(cambio_hoy_pct=40.0))["sube"] == 35.0        # recortado a +8
    assert puntuar(_carvajal(prensa_baja=True))["puntua"] == 0.32
    # Con FF, el estado no resta (ya esta en la titularidad).
    assert puntuar(_carvajal(estado="injured"))["puntua"] == 1.32

    # Sin FF: la cuota de partidos, y el estado que no es 'ok' resta 1,2.
    n = puntuar(_carvajal(titular_ff=None, jugados=5, puntos=20, posicion=4,
                          estado="injured"))
    assert n["puntua"] == 1.35 and any("-1,2" in p for p in n["por_que"]), n
    assert puntuar(_carvajal(titular_ff=None, jugados=5, puntos=20, posicion=4))["puntua"] == 2.55
    # La cuota no pasa de 1 (un aplazado jugado antes de cerrar la jornada).
    assert puntuar(_carvajal(titular_ff=None, jugados=9, jornadas=8, puntos=0,
                             posicion=1))["puntua"] == round(0.5 + 0.85 * 1.0 * (10.2 / 11), 2)
    # La cuota con la jornada a medias: 7 jugados en vivo, 8 jornadas
    # cerradas y su equipo ya jugo la 9.ª -> 7/9, no 7/8.
    assert M.el_denominador(8, 9) == 9 and M.el_denominador(8, 7) == 8
    assert M.el_denominador(None, 9) == 9 and M.el_denominador(8, None) == 8
    assert M.el_denominador(None, None) is None and M.el_denominador("x", 0) is None
    medio = dict(titular_ff=None, jugados=7, puntos=35, posicion=3)
    assert puntuar(_carvajal(jornadas=M.el_denominador(8, 9), **medio))["puntua"] == 3.59
    assert puntuar(_carvajal(jornadas=8, **medio))["puntua"] == 3.97
    # Portero sin partidos: Q es su mediana.
    assert puntuar(_carvajal(posicion=1))["puntua"] == round(0.5 + 0.85 * 0.3 * 5.1, 2)

    # Lo que falta se dice, no se inventa.
    n = puntuar(_carvajal(cambio_hoy_pct=None))
    assert n["sube"] is None and n["puntua"] == 1.32, n
    assert any("sin el cambio" in p for p in n["por_que"])
    n = puntuar(_carvajal(titular_ff=None, jornadas=None))
    assert n["puntua"] is None and any("no hay nota de puntua" in p for p in n["por_que"]), n
    n = puntuar(_carvajal(vuelta_ff=None, prensa_baja=None))
    assert n["sube"] == 35.0 and any("sin leer" in p for p in n["por_que"]), n
    assert any("sin informe de prensa" in p for p in n["por_que"]), n


# ------------------------------------------------------------------
# 2. QUIEN ES NUEVO, DE RESET A RESET
# ------------------------------------------------------------------

def test_los_nuevos_tras_cada_reset():
    assert los_nuevos({1, 2, 3}, {2}) == [1, 3]
    assert los_nuevos({1, 2}, None) == [1, 2]
    assert los_nuevos(["1", 2, None], {"2"}) == [1]

    # La base: la linea DIA mas reciente de ANTES de hoy (no la de hoy).
    propio = [DIA_DE_AYER, {"tipo": "DIA", "dia_de_mercado": "2026-10-16",
                            "mercado": {"computer": [1], "managers": []}},
              {"tipo": "DIA", "dia_de_mercado": "2026-10-18",
               "mercado": {"computer": [9], "managers": []}},
              {"tipo": "JUGADOR", "dia_de_mercado": "2026-10-17", "id": 5}]
    a = el_mercado_anterior(propio, "2026-10-18")
    assert a == {"ids": {104, 120, 121}, "dia": "2026-10-17", "base": "EL_INFORME"}, a
    # Si ayer no hubo vuelta, el ultimo dia apuntado.
    a = el_mercado_anterior(propio, "2026-10-17")
    assert a["dia"] == "2026-10-16" and a["ids"] == {1}, a
    # Sin linea DIA: la valoracion y el escaparate de su ultimo dia, juntos.
    valoracion = [{"dia": "2026-10-17", "id": 104}, {"dia": "2026-10-17", "id": 103},
                  {"dia": "2026-10-16", "id": 77}, {"dia": "2026-10-18", "id": 88}]
    escaparate = [{"dia_de_mercado": "2026-10-17", "players": [{"id": 101}]}]
    a = el_mercado_anterior([], "2026-10-18", valoracion, escaparate)
    assert a == {"ids": {101, 103, 104}, "dia": "2026-10-17",
                 "base": "VALORACION_Y_ESCAPARATE"}, a
    assert el_mercado_anterior([], "2026-10-18", [], [])["base"] == "SIN_DIA_ANTERIOR"

    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta)
            # DIA 1 (17/10): sin nada antes, todos son nuevos y se dice.
            r = _correr(ruta, ahora=AYER, snapshot=_foto(
                FOTO_AYER, computer={104: 2_590_000, 120: 1_000_000}, managers={121: (7, 5)}))
            assert r["motivo"] == "APUNTADO" and r["base"] == "SIN_DIA_ANTERIOR", r
            assert r["nuevos"] == [104, 120, 121], r["nuevos"]
            # DIA 2 (18/10): contra el mercado del 17. El 104 seguia; el 105
            # es nuestro; el 103 lo vende un manager y es nuevo.
            r = _correr(ruta)
            assert r["motivo"] == "APUNTADO" and r["base"] == "EL_INFORME", r
            assert r["nuevos"] == [100, 101, 102, 103], r["nuevos"]
            assert r["dia"]["dia_anterior"] == "2026-10-17"
            vendedores = {f["id"]: f["vendedor"] for f in r["jugadores"]}
            assert vendedores == {100: "COMPUTER", 101: "COMPUTER", 102: "COMPUTER",
                                  103: "MANAGER"}, vendedores
            assert {f["id"]: f["pide"] for f in r["jugadores"]}[103] == 1_800_000
            dias = [f for f in _filas(ruta) if f["tipo"] == "DIA"]
            assert [d["dia_de_mercado"] for d in dias] == ["2026-10-17", "2026-10-18"]
            assert dias[1]["mercado"] == {"computer": [100, 101, 102, 104], "managers": [103]}

        # EL CAMBIO DE HORA (25/10): desde el 26/10 el reset es a las 06:00
        # UTC. A las 05:30 UTC sigue siendo el dia de mercado del 25.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, {"tipo": "DIA", "dia_de_mercado": "2026-10-25",
                                    "mercado": {"computer": [], "managers": []}})
            r = _correr(ruta, ahora=datetime(2026, 10, 26, 5, 30, tzinfo=UTC))
            assert r["dia_de_mercado"] == "2026-10-25" and r["motivo"] == "YA_HECHO_HOY", r
            r = _correr(ruta, ahora=datetime(2026, 10, 26, 6, 20, tzinfo=UTC),
                        snapshot=_foto("2026-10-26T07:16:00"))
            assert r["dia_de_mercado"] == "2026-10-26" and r["motivo"] == "APUNTADO", r
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 3. UNA VEZ POR DIA DE MERCADO
# ------------------------------------------------------------------

def test_una_vez_por_dia_de_mercado():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)

            # Foto de antes del reset (la de ayer, o la de las 07:02): nada.
            for foto in (FOTO_AYER, "2026-10-18T06:55:00", "2026-10-18T07:02:00", None, "x"):
                r = _correr(ruta, snapshot=_foto(foto))
                assert r["motivo"] in {"FOTO_DE_ANTES_DEL_RESET", "SIN_HORA_DE_LA_FOTO"}, r
            # Mercado vacio: nada, y la vuelta siguiente lo intenta.
            r = _correr(ruta, snapshot=_foto(computer={}, managers={}, propios=()))
            assert r["motivo"] == "MERCADO_VACIO", r
            assert len(_filas(ruta)) == 1, "no se apunta nada sin foto buena ni mercado"

            r = _correr(ruta)
            assert r["motivo"] == "APUNTADO" and r["escrito"], r
            foto_del_libro = Path(ruta).read_bytes()

            # La vuelta de las 08:07 y la de las 06:00 del dia siguiente
            # (antes del reset) son del mismo dia de mercado: nada.
            for cuando, foto in ((AHORA + timedelta(hours=1), "2026-10-18T08:08:00"),
                                 (datetime(2026, 10, 19, 4, 0, tzinfo=UTC),
                                  "2026-10-19T06:00:00")):
                fetch = _Fetch()
                r = _correr(ruta, ahora=cuando, snapshot=_foto(foto), fetch=fetch)
                assert r["motivo"] == "YA_HECHO_HOY" and fetch.llamadas == [], r
            assert Path(ruta).read_bytes() == foto_del_libro

            # Tras el reset del 19, otra vez (con la foto del 19).
            r = _correr(ruta, ahora=datetime(2026, 10, 19, 5, 20, tzinfo=UTC),
                        snapshot=_foto("2026-10-19T07:16:00"))
            assert r["motivo"] == "APUNTADO" and r["nuevos"] == [], r
            assert [f["dia_de_mercado"] for f in _filas(ruta) if f["tipo"] == "DIA"] == [
                "2026-10-17", "2026-10-18", "2026-10-19"]
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 4. DE PUNTA A PUNTA, Y LA RED QUE FALLA
# ------------------------------------------------------------------

def test_de_punta_a_punta():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)
            fetch = _Fetch()
            r = _correr(ruta, fetch=fetch)
            assert r["motivo"] == "APUNTADO", r
            # Una pagina por equipo: el Celta una vez para Borja y Aspas.
            assert sorted(u.rsplit("/", 1)[-1] for u in fetch.llamadas) == [
                "celta", "getafe", "valencia"], fetch.llamadas
            assert all(u.startswith("https://www.futbolfantasy.com/laliga/equipos/")
                       for u in fetch.llamadas)

            por_id = {f["id"]: f for f in r["jugadores"]}
            notas = {pid: (f["sube"], f["puntua"]) for pid, f in por_id.items()}
            assert notas == {100: (35.0, 1.32), 101: (-5.5, 2.02), 102: (19.5, 1.35),
                             103: (3.5, 2.46)}, notas

            # Carvajal: el «Analisis Fantasy» se apunta y no pesa; la lesion
            # de hace seis dias, fuera de la ventana... pero en el libro, con
            # su fecha: la fase 1 puede rehacer cualquier ventana.
            c = por_id[100]
            assert [n["tipo"] for n in c["senales"]["noticias_ff"]] == ["ANALISIS"], c
            todas = c["senales"]["noticias_ff_todas"]
            assert [(n["tipo"], n["publicada"]) for n in todas] == [
                ("ANALISIS", "2026-10-17T18:00:00+00:00"),
                ("BAJA", "2026-10-12T08:00:00+00:00")], todas
            assert c["terminos"]["VUELTA"] == 0 and c["senales"]["ff"]["jerarquia"] == "Revulsivo"
            assert c["senales"]["jp"]["nota"] is not None, c["senales"]["jp"]
            assert c["terminos"]["PRENSA_BAJA"] == 0, "la prensa de sujeto ambiguo no cuenta"
            # Aspas: VUELTA en FF, barato, sin FF y lesionado.
            a = por_id[102]
            assert a["terminos"]["VUELTA"] == 1 and a["terminos"]["BARATO"] == 1, a
            assert a["terminos"]["P_fuente"] == "CUOTA" and a["terminos"]["ESTADO_NO_OK"] == 1
            assert "tablero_ff" in a["faltan"]
            # Borja: DUDA de FF (no pesa) y BAJA de MARCA (si pesa), con fecha.
            b = por_id[101]
            assert [n["tipo"] for n in b["senales"]["noticias_ff"]] == ["DUDA"], b
            assert b["terminos"]["PRENSA_BAJA"] == 1 and b["senales"]["prensa"][0]["fuente"] == "MARCA"
            assert b["senales"]["prensa_todas"][0]["publicada"] == "2026-10-17T20:00:00+00:00"
            # Hugo Duro: la DUDA de MARCA de hace cinco dias no esta en la
            # ventana, pero si en el libro.
            assert por_id[103]["terminos"]["PRENSA_BAJA"] == 0
            assert [x["tipo"] for x in por_id[103]["senales"]["prensa_todas"]] == ["DUDA"]
            # Hugo Duro: la pagina del Valencia no se pudo leer. La señal
            # FALTA (no es un cero) y el informe sale igual.
            h = por_id[103]
            assert h["senales"]["noticias_ff"] is None and "noticias_ff" in h["faltan"], h
            assert h["terminos"]["vuelta_leida"] is False
            assert any("sin leer" in p for p in h["por_que"]), h["por_que"]
            assert r["dia"]["noticias"]["sin_leer"] == ["valencia"], r["dia"]["noticias"]
            assert "ConnectionError" in r["dia"]["noticias"]["errores"][0]

            # La cuota: contra lo que ha jugado su equipo (Celta, 8).
            assert a["terminos"]["jornadas"] == 8 and a["senales"]["partidos_del_equipo"] == 8
            assert r["dia"]["ventana_noticias"] == {"desde": "2026-10-15T05:15:00+00:00",
                                                    "hasta": "2026-10-18T05:15:00+00:00"}, r["dia"]
            assert r["dia"]["fuentes"]["prensa_descartada"] is None

            filas = _filas(ruta)
            assert [f["tipo"] for f in filas] == ["DIA", "DIA"] + ["JUGADOR"] * 4, filas
            assert all(f["pesos"] == M.PESOS for f in filas[1:])
            assert filas[1]["observador"] is True and filas[1]["n_nuevos"] == 4

            # El panel: el ultimo dia, de mas a menos SUBE.
            panel = el_ultimo_informe(ruta)
            assert panel["available"] and panel["dia_de_mercado"] == "2026-10-18", panel
            assert [j["id"] for j in panel["jugadores"]] == [100, 102, 103, 101], panel
            assert any("Dani Carvajal" in x for x in el_parte(r))
            assert any("Solo observa" in x for x in el_parte(r))
    finally:
        _entorno(**antes)


def test_la_red_que_falla_no_rompe_nada():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            # Toda la red caida: se apunta igual, con las noticias SIN LEER.
            ruta = _libro(carpeta, DIA_DE_AYER)
            fetch = _Fetch(revienta=("*",))
            r = _correr(ruta, fetch=fetch)
            assert r["motivo"] == "APUNTADO" and len(r["jugadores"]) == 4, r
            assert all(f["senales"]["noticias_ff"] is None for f in r["jugadores"])
            assert {f["id"]: f["sube"] for f in r["jugadores"]}[102] == 17.5   # sin VUELTA
            assert sorted(r["dia"]["noticias"]["sin_leer"]) == ["celta", "getafe", "valencia"]

            # Basura en vez de HTML (200, sin lanzar): se apunta igual, pero
            # la pagina NO esta leida. Ni una noticia con fecha no es «no ha
            # pasado nada»: es que no se entendio. La señal FALTA, no es 0.
            for basura in (None, "", "<html>", 12, b"\x00\xff", "<a class='noticia'>" * 5000,
                           "x" * (M.TAMANO_MAXIMO_HTML + 10),
                           "<html><title>Just a moment...</title></html>",
                           "<html>Please enable cookies</html>",
                           "<html><body>Tu privacidad es importante</body></html>",
                           # Un rediseño: las mismas noticias con otra clase.
                           PAGINAS["celta"].replace('class="noticia"', 'class="news-card"'),
                           # Noticias sin fecha que se entienda («Hoy»).
                           PAGINAS["celta"].replace("17/10", "Hoy").replace("16/10", "Ayer")):
                ruta = _libro(carpeta + f"/b{abs(hash(str(basura)))}", DIA_DE_AYER)
                r = _correr(ruta, fetch=lambda url, b=basura: b)
                assert r["motivo"] == "APUNTADO" and len(r["jugadores"]) == 4, (basura, r)
                for f in r["jugadores"]:
                    assert f["senales"]["noticias_ff"] is None, (basura, f)
                    assert f["senales"]["noticias_ff_todas"] is None, (basura, f)
                    assert "noticias_ff" in f["faltan"] and f["terminos"]["vuelta_leida"] is False
                assert {f["id"]: f["sube"] for f in r["jugadores"]}[102] == 17.5    # sin VUELTA
                n = r["dia"]["noticias"]
                assert n["leidas"] == [] and n["sin_leer"] == ["celta", "getafe", "valencia"], n
                assert all("sin noticias legibles" in e for e in n["errores"]), n

        # Los topes: paginas, tiempo, tres fallos seguidos y slugs raros.
        equipos = {s: {1: "Uno Dos"} for s in ("alaves", "betis", "celta", "elche", "getafe")}
        fetch = _Fetch(revienta=("*",))
        n = las_noticias_de_los_equipos(equipos, AHORA, fetch)
        assert len(fetch.llamadas) == M.FALLOS_SEGUIDOS_PARA_PARAR == 3, fetch.llamadas
        assert len(n["sin_leer"]) == 5 and n["leidos"] == set(), n
        # Tres paginas seguidas que llegan sin noticias (un reto anti-robots
        # para todos) tambien cortan: son fallos.
        llamadas = []
        n = las_noticias_de_los_equipos(
            equipos, AHORA, lambda url: llamadas.append(url) or "<html>Just a moment...</html>")
        assert len(llamadas) == 3 and len(n["sin_leer"]) == 5 and n["leidos"] == set(), n
        # Los fallos tienen que ser SEGUIDOS: una pagina buena pone la cuenta
        # a cero. Con seis equipos y fallos alternos se piden los seis (con
        # cinco no se distingue de «tres fallos en total»: el tercero es el
        # ultimo).
        seis = {s: {1: "Uno Dos"} for s in ("alaves", "betis", "celta", "elche", "getafe", "girona")}
        fetch = _Fetch(revienta=("alaves", "celta", "getafe"))
        n = las_noticias_de_los_equipos(seis, AHORA, fetch)
        assert [u.rsplit("/", 1)[-1] for u in fetch.llamadas] == sorted(seis), fetch.llamadas
        assert n["sin_leer"] == ["alaves", "celta", "getafe"], n
        assert n["leidos"] == {"betis", "elche", "girona"}, n
        fetch = _Fetch()
        n = las_noticias_de_los_equipos(equipos, AHORA, fetch, maximo_paginas=2)
        assert len(fetch.llamadas) == 2 and len(n["sin_leer"]) == 3, n
        assert n["leidos"] == {"alaves", "betis"}, n
        fetch = _Fetch()
        n = las_noticias_de_los_equipos(equipos, AHORA, fetch, segundos=-1)
        assert fetch.llamadas == [] and len(n["sin_leer"]) == 5, n
        # Con tiempo de verdad y un FF lento (0,1 s por pagina, 0,05 s de
        # tope): la primera pagina, y las demas SIN LEER.
        lentas = []

        def _lenta(url):
            lentas.append(url)
            time.sleep(0.1)
            return PAGINA_SIN_LOS_NUESTROS

        n = las_noticias_de_los_equipos(equipos, AHORA, _lenta, segundos=0.05)
        assert len(lentas) == 1 and len(n["sin_leer"]) == 4, n
        fetch = _Fetch()
        n = las_noticias_de_los_equipos({"../../etc": {1: "x"}, "a b": {}}, AHORA, fetch)
        assert fetch.llamadas == [] and len(n["sin_leer"]) == 2, n
        assert M.MAXIMO_DE_PAGINAS <= 20 and M.TIMEOUT_SEGUNDOS <= 15
        assert M.SEGUNDOS_PARA_LAS_NOTICIAS <= 180
    finally:
        _entorno(**antes)


class _Goteo:
    """Una respuesta de FF que gotea: 1 KB cada 0,05 s, sin fin. Nunca
    pasa el tiempo de espera entre bytes de `requests`."""

    def __init__(self, timeout):
        self.timeout = timeout
        self.raw = self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        return None

    def read1(self, n=-1, decode_content=None):
        time.sleep(0.05)
        return b"<p>" + b"x" * 1021


class _Rapida(_Goteo):
    """Una respuesta normal: la pagina entera y se acaba."""

    def __init__(self, timeout, cuerpo, con_read1=True):
        super().__init__(timeout)
        self._cuerpo = [cuerpo[i:i + 70_000] for i in range(0, len(cuerpo), 70_000)]
        if not con_read1:
            self.raw = object()                      # urllib3 sin read1

    def read1(self, n=-1, decode_content=None):
        return self._cuerpo.pop(0) if self._cuerpo else b""

    def iter_content(self, n):
        while self._cuerpo:
            yield self._cuerpo.pop(0)


def test_el_tope_de_tiempo_es_de_reloj():
    """
    `SEGUNDOS_PARA_LAS_NOTICIAS` es un tope de RELOJ para el paso entero,
    tambien DENTRO de una descarga: una pagina que gotea unos pocos KB
    por segundo nunca dispara el tiempo de espera de `requests` (es
    entre bytes) y antes podia tener la vuelta minutos. Se corta y la
    pagina queda SIN LEER. Con un `requests.get` de mentira: no sale a
    la red.
    """
    import importlib

    import requests

    # Su import, antes de medir: que no se coma el tope.
    importlib.import_module("src.intelligence.futbolfantasy_provider")

    original, pedidas = requests.get, []

    def _goteo(url, **k):
        pedidas.append(k)
        return _Goteo(k.get("timeout"))

    url = "https://www.futbolfantasy.com/laliga/equipos/celta"
    try:
        requests.get = _goteo
        # Una pagina sola, con el tope que le pasa quien la pide.
        empezo = time.monotonic()
        try:
            M._bajar(url, hasta=empezo + 0.3)
            raise AssertionError("una pagina que gotea no se corto")
        except TimeoutError:
            pass
        assert time.monotonic() - empezo < 1.0, time.monotonic() - empezo
        # La espera por lectura no pasa de lo que queda (con un suelo).
        assert pedidas[-1]["timeout"] == (0.5, 0.5) and pedidas[-1]["stream"] is True, pedidas
        # Sin tope de quien la pide: el de una pagina sola.
        tope = M.SEGUNDOS_POR_PAGINA
        M.SEGUNDOS_POR_PAGINA = 0.2
        try:
            empezo = time.monotonic()
            try:
                M._bajar(url)
                raise AssertionError("sin tope por pagina")
            except TimeoutError:
                pass
            assert time.monotonic() - empezo < 1.0
        finally:
            M.SEGUNDOS_POR_PAGINA = tope
        assert M.SEGUNDOS_POR_PAGINA <= 30 and M.TIMEOUT_SEGUNDOS <= 15

        # El paso entero: el `fetch` por defecto recibe el tope de reloj.
        # Antes, 3 s de tope y una pagina que goteaba 10 s: 10 s, y LEIDA.
        equipos = {s: {1: "Uno Dos"} for s in ("celta", "getafe", "valencia")}
        empezo = time.monotonic()
        n = las_noticias_de_los_equipos(equipos, AHORA, segundos=0.3)
        assert time.monotonic() - empezo < 1.2, time.monotonic() - empezo
        assert n["paginas"] == 1 and n["leidos"] == set(), n
        assert n["sin_leer"] == ["celta", "getafe", "valencia"], n
        assert "TimeoutError" in n["errores"][0], n["errores"]

        # Y una pagina que llega bien se lee igual (con read1 y sin el).
        for con_read1 in (True, False):
            requests.get = lambda u, con=con_read1, **k: _Rapida(
                k.get("timeout"), PAGINAS["celta"].encode() * 40, con)
            texto = M._bajar(url, hasta=time.monotonic() + 5)
            assert texto == PAGINAS["celta"] * 40, (con_read1, len(texto))
            n = las_noticias_de_los_equipos({"celta": {102: "Iago Aspas"}}, AHORA)
            assert n["leidos"] == {"celta"} and n["por_jugador"][102][0]["tipo"] == "VUELTA", n
    finally:
        requests.get = original

    # Y en el workflow, el paso tiene su propio tope. En la vuelta de
    # verdad, ademas, no la tumba: el paso del panel (Cloudflare) va
    # detras y sin `always()`. En el ensayo todo lo de detras va con
    # `always()` y el candado tiene que poder fallar el paso.
    for nombre, sigue in (("bordalas-live.yml", True), ("bordalas-ensayo.yml", False)):
        yml = (RAIZ / ".github" / "workflows" / nombre).read_text(encoding="utf-8")
        paso = yml[yml.index("- name: El informe de la manana"):]
        paso = paso[:paso.index("- name:", 10)]
        assert "timeout-minutes: 4" in paso, (nombre, paso)
        assert ("continue-on-error: true" in paso) is sigue, (nombre, paso)


def test_la_ventana_de_las_noticias():
    """
    La ventana con la que el laboratorio midio VUELTA y la prensa: las
    72 h que acaban 15 min despues del reset de HOY, a cualquier hora a
    la que corra el informe. La primera medida contaba hasta el reset de
    mañana (lo que el informe no puede saber).
    """
    corte = M.el_corte_de_las_noticias(AHORA)
    assert corte == datetime(2026, 10, 18, 5, 15, tzinfo=UTC), corte
    for cuando in (datetime(2026, 10, 18, 5, 6, tzinfo=UTC), datetime(2026, 10, 18, 7, 0, tzinfo=UTC),
                   datetime(2026, 10, 19, 4, 59, tzinfo=UTC)):
        assert M.el_corte_de_las_noticias(cuando) == corte, cuando
    # Con la hora de invierno, el reset es a las 06:00 UTC.
    assert M.el_corte_de_las_noticias(datetime(2026, 10, 26, 6, 20, tzinfo=UTC)) == datetime(
        2026, 10, 26, 6, 15, tzinfo=UTC)
    # Los bordes, dentro; nada de despues del corte.
    assert en_la_ventana(corte, corte) and en_la_ventana(corte - timedelta(hours=72), corte)
    assert not en_la_ventana(corte + timedelta(minutes=1), corte)
    assert not en_la_ventana(corte - timedelta(hours=72, minutes=1), corte)
    # Los casos del hallazgo: las 13:00 y las 23:30 de Madrid del 18 caian
    # en la ventana del laboratorio y no en la del modulo; las 08:00 del
    # 15 (dia d-3) al reves. Ahora, las dos iguales.
    assert not en_la_ventana("2026-10-18T13:00:00+02:00", corte)
    assert not en_la_ventana("2026-10-18T23:30:00+02:00", corte)
    assert en_la_ventana("2026-10-15T08:00:00+02:00", corte)
    assert not en_la_ventana("2026-10-15T07:14:00+02:00", corte)

    # En la fila: una VUELTA de FF y una BAJA de prensa de despues del
    # corte no cuentan aunque el informe corra a las 09:20 y ya existan;
    # pero se guardan, con su fecha.
    tarde = AHORA + timedelta(hours=2)
    despues = (corte + timedelta(minutes=1)).isoformat()
    antes = (corte - timedelta(minutes=1)).isoformat()
    for publicada, cuenta in ((despues, 0), (antes, 1)):
        informe = {"available": True, "generated_at": tarde.isoformat(), "players": {"102": {
            "items": [{"kind": "BAJA", "source": "MARCA", "ambiguous_subject": False,
                       "published_at": publicada, "headline": "Aspas, baja"}]}}}
        f = M.la_fila(102, dia="2026-10-18", at=tarde, vendedor="COMPUTER", pide=600_000,
                      ficha=CATALOGO["102"], equipo="Celta", ff=None,
                      prensa=M.la_prensa_de(informe, 102, M.el_corte_de_las_noticias(tarde)),
                      jp=None, noticias=[{"tipo": "VUELTA", "titular": "Aspas vuelve",
                                          "publicada": publicada, "url": None}],
                      noticias_leidas=True, jornadas=8, cambio_hist=None)
        assert f["terminos"]["VUELTA"] == cuenta and f["terminos"]["PRENSA_BAJA"] == cuenta, f
        assert [n["publicada"] for n in f["senales"]["noticias_ff_todas"]] == [publicada], f
        assert [n["publicada"] for n in f["senales"]["prensa_todas"]] == [publicada], f
        assert len(f["senales"]["noticias_ff"]) == cuenta

    # De punta a punta, con la primera vuelta del dia a las 09:00: la
    # noticia de las 08:00 ya esta en FF, pero el informe no la cuenta.
    antes_env = _entorno(**ENCENDIDO)
    try:
        for hora, sube in (("08:00", 17.5), ("07:10", 19.5)):
            celta = _pagina(_noticia(FF + "152030-aspas-vuelve", "Iago Aspas vuelve a entrenar "
                                     "con el grupo", "18/10", hora))
            with tempfile.TemporaryDirectory() as carpeta:
                ruta = _libro(carpeta, DIA_DE_AYER)
                r = _correr(ruta, ahora=datetime(2026, 10, 18, 7, 0, tzinfo=UTC),
                            snapshot=_foto("2026-10-18T08:55:00"),
                            fetch=_Fetch(paginas={**PAGINAS, "celta": celta}))
                assert r["motivo"] == "APUNTADO", r
                aspas = {f["id"]: f for f in r["jugadores"]}[102]
                assert aspas["sube"] == sube, (hora, aspas["sube"], aspas["por_que"])
                assert [n["tipo"] for n in aspas["senales"]["noticias_ff_todas"]] == ["VUELTA"]
                assert r["dia"]["ventana_noticias"]["hasta"] == "2026-10-18T05:15:00+00:00"
    finally:
        _entorno(**antes_env)


def test_la_prensa_vieja_no_cuenta():
    """
    Si el refresco de la prensa no trae titulares, `press` conserva el
    informe viejo (STALE_FALLBACK); si el ojeador no pudo trabajar, deja
    uno con `available: False`. Leidos como de hoy daban PRENSA_BAJA = 0
    y «prensa leida». Ahora la señal FALTA y se dice por que.
    """
    vieja = {**PRENSA, "generated_at": "2026-10-14T05:18:00+00:00"}
    caida = {"available": False, "generated_at": "2026-10-18T05:18:00+00:00",
             "reason": "El ojeador de prensa no pudo trabajar", "players": PRENSA["players"]}
    sin_fecha = {k: v for k, v in PRENSA.items() if k != "generated_at"}
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            for i, (informe, motivo) in enumerate(((vieja, "VIEJO"), (caida, "NO_DISPONIBLE"),
                                                   (sin_fecha, "SIN_FECHA"), ([5], "SIN_INFORME"))):
                ruta = _libro(carpeta + f"/{i}", DIA_DE_AYER)
                r = _correr(ruta, prensa=informe)
                assert r["motivo"] == "APUNTADO" and len(r["jugadores"]) == 4, (motivo, r)
                assert r["dia"]["fuentes"]["prensa_descartada"] == motivo, r["dia"]["fuentes"]
                assert any(f"Prensa sin leer ({motivo})" in x for x in el_parte(r)), el_parte(r)
                for f in r["jugadores"]:
                    assert "prensa" in f["faltan"] and f["senales"]["prensa"] is None, (motivo, f)
                    assert f["terminos"]["prensa_leida"] is False and f["terminos"]["PRENSA_BAJA"] == 0
                borja = {f["id"]: f for f in r["jugadores"]}[101]
                assert borja["puntua"] == 3.02, borja                # sin el -1 de MARCA
                assert any("sin informe de prensa" in x for x in borja["por_que"]), borja["por_que"]
    finally:
        _entorno(**antes)
    # El borde: 13 h (la prensa se refresca cada 12 h, y una hora de vuelta).
    assert M.PRENSA_EDAD_MAXIMA_HORAS == 13
    casi = {**PRENSA, "generated_at": (AHORA - timedelta(hours=12, minutes=59)).isoformat()}
    pasada = {**PRENSA, "generated_at": (AHORA - timedelta(hours=13, minutes=1)).isoformat()}
    assert M.la_prensa_vale(casi, AHORA) is None and M.la_prensa_vale(pasada, AHORA) == "VIEJO"
    assert M.la_prensa_vale(PRENSA, AHORA) is None


def test_el_mercado_sin_renovar_no_se_apunta():
    """
    Una foto de despues del reset que aun trae el mercado de ayer (el
    `until` del Computer es el reset que acaba de pasar: `listings_stale`)
    no se apunta. Antes dejaba el dia hecho con `nuevos == []` y los
    nuevos de verdad de esa mañana no se veian nunca.
    """
    from src.analysis.market_clock import build_market_clock

    reset_de_hoy = datetime(2026, 10, 18, 5, 0, tzinfo=UTC).timestamp()
    reset_de_manana = datetime(2026, 10, 19, 5, 0, tzinfo=UTC).timestamp()
    foto_vieja = _foto(computer={104: 2_590_000, 120: 1_000_000}, managers={121: (7, 5)},
                       until=reset_de_hoy)
    foto_nueva = _foto("2026-10-18T08:16:00", until=reset_de_manana)
    a_las_0716 = int(datetime(2026, 10, 18, 5, 16, tzinfo=UTC).timestamp())
    assert build_market_clock(foto_vieja, now_ts=a_las_0716)["listings_stale"] is True
    assert build_market_clock(foto_nueva, now_ts=a_las_0716 + 3600)["listings_stale"] is False
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)
            fetch = _Fetch()
            r = _correr(ruta, snapshot=foto_vieja, fetch=fetch)
            assert r["motivo"] == "MERCADO_SIN_RENOVAR" and not r["escrito"], r
            assert r["until_del_computer"] == "2026-10-18T05:00:00+00:00", r
            assert any("mercado de ayer" in x for x in el_parte(r)), el_parte(r)
            assert fetch.llamadas == [] and len(_filas(ruta)) == 1
            # Tambien con el `until` justo en la hora de la foto.
            r = _correr(ruta, snapshot=_foto(computer={104: 1}, until=a_las_0716))
            assert r["motivo"] == "MERCADO_SIN_RENOVAR", r
            # La vuelta siguiente, con el mercado ya renovado: se apunta.
            r = _correr(ruta, ahora=AHORA + timedelta(hours=1), snapshot=foto_nueva)
            assert r["motivo"] == "APUNTADO" and r["nuevos"] == [100, 101, 102, 103], r
            assert [f["dia_de_mercado"] for f in _filas(ruta) if f["tipo"] == "DIA"] == [
                "2026-10-17", "2026-10-18"]
    finally:
        _entorno(**antes)


def test_la_cuota_y_el_cambio_del_historico():
    """
    1. La cuota sin FF con la jornada a medias: los jugados del catalogo
       van en vivo; el denominador, lo que ha jugado su equipo (del mismo
       catalogo) si pasa de las jornadas cerradas.
    2. Sin `priceIncrement`, el cambio de hoy sale del historico de
       precios (el ultimo de hoy contra el ultimo de ayer), con su signo.
    """
    catalogo = {k: dict(v) for k, v in CATALOGO.items()}
    catalogo["110"]["playedAway"] = 5                # el Celta ya jugo la 9.ª
    del catalogo["100"]["priceIncrement"]
    del catalogo["102"]["priceIncrement"]

    def _t(*a):
        return datetime(*a, tzinfo=UTC).timestamp()

    historico = {"players": {
        "100": {"t": [_t(2026, 10, 17, 5, 30), _t(2026, 10, 18, 5, 10)],
                "p": [3_000_000, 3_240_000]},
        "102": {"t": [_t(2026, 10, 16, 6, 0), _t(2026, 10, 17, 5, 30), _t(2026, 10, 18, 5, 10)],
                "p": [560_000, 580_000, 600_000]},
    }}
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)
            r = _correr(ruta, snapshot=_foto(catalogo=catalogo), historico=historico, jornadas=8)
            assert r["motivo"] == "APUNTADO", r
            por_id = {f["id"]: f for f in r["jugadores"]}

            # 1. Aspas (sin FF): 5 de 9, no 5 de 8.
            a = por_id[102]
            assert a["terminos"]["P_fuente"] == "CUOTA" and a["terminos"]["jornadas"] == 9, a
            assert a["terminos"]["P"] == round(5 / 9, 4), a["terminos"]
            assert a["senales"]["jornadas_cerradas"] == 8 and a["senales"]["partidos_del_equipo"] == 9
            assert a["puntua"] == 1.12, a                     # con 5/8 era 1,35
            assert any("juega 5 de 9" in x for x in a["por_que"]), a["por_que"]
            # Hugo Duro (Valencia, 7 jugados): las 8 cerradas.
            assert por_id[103]["terminos"]["jornadas"] == 8

            # 2. Carvajal: +8 % del historico (3,0 M -> 3,24 M).
            c = por_id[100]
            assert c["senales"]["c_fuente"] == "HISTORICO", c["senales"]
            assert c["terminos"]["cambio_hoy_pct"] == 8.0 and c["sube"] == 35.0, c
            # Aspas: 580k -> 600k, lo mismo que daba `priceIncrement`.
            assert a["senales"]["c_fuente"] == "HISTORICO"
            assert abs(a["terminos"]["cambio_hoy_pct"] - 3.448) < 1e-3 and a["sube"] == 19.5, a
            assert por_id[101]["senales"]["c_fuente"] == "BIWENGER"

        # Sin historico de ese jugador: no hay SUBE, y se dice.
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)
            r = _correr(ruta, snapshot=_foto(catalogo=catalogo), historico={"players": {}})
            c = {f["id"]: f for f in r["jugadores"]}[100]
            assert c["sube"] is None and c["senales"]["c_fuente"] is None, c
            assert "cambio_de_hoy" in c["faltan"]
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 5. LOS TITULARES Y EL HTML
# ------------------------------------------------------------------

def test_clasifica_los_titulares():
    indice = el_indice({1: "Iago Aspas", 2: "Borja Iglesias", 3: "Dani Carvajal",
                        4: "Miguel Román", 5: "Hugo Duro"})
    casos = {
        "Iago Aspas vuelve a entrenar con el grupo": {1: "VUELTA"},
        "Lesión muscular de Borja Iglesias: se pierde el partido": {2: "BAJA"},
        "Borja Iglesias, duda para el domingo": {2: "DUDA"},
        "Carvajal será titular ante el Betis": {3: "TITULARIDAD"},
        "Análisis Fantasy de Dani Carvajal: ¿merece la pena?": {3: "ANALISIS"},
        "Miguel Román, sancionado por acumulación de amarillas": {4: "SANCION"},
        "Ficha a Carvajal si sale en tu mercado": {3: "RECOMENDADO"},
        "Carvajal, recomendado para la jornada": {3: "RECOMENDADO"},
        "El Celta retoma los entrenamientos sin recuperar a Aspas": {1: "BAJA"},
        "Aspas recibe el alta médica": {1: "VUELTA"},
        "Hugo Duro ficha por el Sevilla": {},
        "Aspas habla de su lesión": {},
        "El Celta prepara el partido": {},
        "": {},
    }
    for titular, esperado in casos.items():
        assert clasificar_titular(titular, indice) == esperado, (titular,
                                                                 clasificar_titular(titular, indice))
    # Dos en un titular: cada uno con su trozo.
    assert clasificar_titular("Aspas vuelve y Borja Iglesias se pierde el partido", indice) == {
        1: "VUELTA", 2: "BAJA"}
    # Un apellido que comparten dos del equipo no se adivina.
    doble = el_indice({1: "Iago Aspas", 9: "Pablo Aspas"})
    assert clasificar_titular("Aspas vuelve a entrenar", doble) == {}
    assert clasificar_titular("Iago Aspas vuelve a entrenar", doble) == {1: "VUELTA"}


def test_el_html_solo_se_lee():
    html = PAGINAS["celta"] + _noticia(FF + "1-x", "Aspas " + "muy " * 200, "31/12", "23:59")
    noticias = leer_las_noticias(html, AHORA)
    assert [n["titular"] for n in noticias][:3] == [
        "Iago Aspas vuelve a entrenar con el grupo", "Borja Iglesias, duda para el domingo",
        "El Celta prepara el partido"], noticias
    # Hora de Madrid (CEST) a UTC; el enlace raro se tira.
    assert noticias[0]["publicada"] == "2026-10-17T10:00:00+00:00", noticias[0]
    assert noticias[0]["url"] == FF + "152010-aspas-vuelve"
    assert noticias[2]["url"] is None
    # Titular capado y sin etiquetas; el 31/12 es del año pasado.
    largo = noticias[3]
    assert len(largo["titular"]) == M.LARGO_MAXIMO_TITULAR and "<" not in largo["titular"]
    assert largo["publicada"].startswith("2025-12-31"), largo
    # Repetidas: una vez.
    assert len(leer_las_noticias(PAGINAS["celta"] * 3, AHORA)) == 3
    assert leer_las_noticias("<html></html>", AHORA) == []
    # La ventana de 72 h.
    assert en_la_ventana(AHORA - timedelta(hours=71), AHORA)
    assert not en_la_ventana(AHORA - timedelta(hours=73), AHORA)
    assert not en_la_ventana(None, AHORA) and not en_la_ventana("x", AHORA)
    assert la_fecha_de_ff("17/10", "22:00", AHORA).isoformat() == "2026-10-17T20:00:00+00:00"
    assert la_fecha_de_ff("10/11", "22:00", datetime(2026, 11, 12, tzinfo=UTC)).isoformat() \
        == "2026-11-10T21:00:00+00:00"                                   # CET
    assert la_fecha_de_ff("x", "y", AHORA) is None and la_fecha_de_ff("40/13", "", AHORA) is None


# ------------------------------------------------------------------
# 6. NACE APAGADO Y NUNCA LANZA
# ------------------------------------------------------------------

def test_nace_apagado():
    antes = _entorno(**{ENV: None})
    try:
        assert activa() is False
        # Sin argumentos: vuelve antes de abrir nada.
        with _Escrituras() as e:
            r = correr()
            panel = el_ultimo_informe()
        assert r["motivo"] == "APAGADO" and r["jugadores"] == [] and not r["escrito"], r
        assert panel["available"] is False and panel["activa"] is False, panel
        assert e.abiertos == [] and e.rutas == [], (e.abiertos, e.rutas)
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta)
            fetch = _Fetch()
            r = _correr(ruta, fetch=fetch)
            assert r["motivo"] == "APAGADO" and not ruta.exists() and fetch.llamadas == [], r
        for valor in ("0", "", "no", "false"):
            _entorno(**{ENV: valor})
            assert activa() is False, valor
        for valor in ("1", "true", "si", "yes", " TRUE "):
            _entorno(**{ENV: valor})
            assert activa() is True, valor
    finally:
        _entorno(**antes)
    from src.telemetry.el_tablon import QUE_HACE

    assert "no decide ninguna puja" in QUE_HACE[ENV], QUE_HACE.get(ENV)
    # Y no promete lo que no hace: el panel aun no tiene cuadro para el
    # (`NO_SE_PINTAN`), asi que nadie lo ve en pantalla.
    assert "todavía no lo pinta" in QUE_HACE[ENV], QUE_HACE.get(ENV)
    assert "enseña en el panel" not in QUE_HACE[ENV] and "enseña en el panel" not in M.__doc__
    from src.analysis.test_la_lista_blanca_v1 import NO_SE_PINTAN

    assert "el_informe_de_la_manana" in NO_SE_PINTAN


def test_nunca_lanza_con_basura():
    for basura in (None, "x", 5, [1, 2], {"a": object()}, object(),
                   {"precio": "x", "cambio_hoy_pct": "nan", "titular_ff": 500, "jugados": -3}):
        n = puntuar(basura)
        assert set(n) == {"sube", "puntua", "por_que"}, (basura, n)
        clasificar_titular(basura, basura)
        el_indice(basura)
        leer_las_noticias(basura, AHORA)
        el_mercado_anterior(basura, basura, basura, basura)
        los_nuevos(basura, None)
        el_parte(basura)
        las_noticias_de_los_equipos(basura, AHORA, lambda u: 1 / 0)
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            for basura in ("x", 5, [1, 2], {"timestamp": FOTO_HOY, "market": 5},
                           {"timestamp": FOTO_HOY, "market": {"sales": [5, {"player": "x"}]},
                            "catalog": {"data": {"players": {"100": "x", "y": {}}}}}):
                ruta = _libro(carpeta)
                r = _correr(ruta, snapshot=basura, tablero_ff="x", prensa=5, jp=[1],
                            historico="x", jornadas="x")
                assert isinstance(r, dict) and r["motivo"], r
            # Todo lo de fuera en basura, con la foto buena: se apunta igual.
            ruta = _libro(carpeta + "/2", DIA_DE_AYER)
            r = _correr(ruta, tablero_ff="x", prensa=[5], jp="x", historico=5, jornadas="x",
                        fetch=lambda u: {"a": 1})
            assert r["motivo"] == "APUNTADO" and len(r["jugadores"]) == 4, r
            # Un libro con lineas rotas se lee igual.
            ruta = Path(carpeta) / "roto.jsonl"
            ruta.write_text("{roto\n[1]\n" + json.dumps(DIA_DE_AYER) + "\n", encoding="utf-8")
            r = _correr(ruta)
            assert r["motivo"] == "APUNTADO" and r["base"] == "EL_INFORME", r
            assert el_ultimo_informe(ruta)["available"] is True
            assert el_ultimo_informe(Path(carpeta) / "no-existe.jsonl")["available"] is False
    finally:
        _entorno(**antes)


# ------------------------------------------------------------------
# 7. SOLO SU LIBRO, Y NADIE LO LEE PARA PUJAR
# ------------------------------------------------------------------

def test_nunca_escribe_fuera_de_su_libro():
    antes = _entorno(**ENCENDIDO)
    try:
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = _libro(carpeta, DIA_DE_AYER)
            with _Escrituras() as e:
                r = _correr(ruta)
            assert r["motivo"] == "APUNTADO", r
            assert e.rutas and set(e.rutas) == {os.path.abspath(str(ruta))}, e.rutas
    finally:
        _entorno(**antes)

    # Y el censo del codigo (el de `los_libros`, que solo lee codigo
    # fuente) dice lo mismo: el modulo escribe un unico fichero, y es un
    # libro de la lista. Sobre una copia del modulo solo: el censo del
    # repositorio entero ya lo pasa `test_la_direccion_v1`.
    from src.estado.los_libros import escritos_por_el_codigo, rutas

    with tempfile.TemporaryDirectory() as carpeta:
        copia = Path(carpeta) / "src" / "intelligence" / "el_informe_de_la_manana.py"
        copia.parent.mkdir(parents=True)
        copia.write_text(Path(M.__file__).read_text(encoding="utf-8"), encoding="utf-8")
        escritos = escritos_por_el_codigo(carpeta)
    assert list(escritos) == [str(M.LIBRO).replace(chr(92), "/")], escritos
    assert list(escritos)[0] in rutas(), "el libro tiene que estar en LIBROS"


# Los unicos de src/ que pueden NOMBRAR el informe, y por que. Nombrarlo
# es importarlo o leer su libro por la ruta (`Path("data/intelligence/
# el_informe_de_la_manana.jsonl")` no es un import y lo leia igual).
LOS_QUE_LO_NOMBRAN = {
    # El panel: el unico que lo lee (`el_ultimo_informe`).
    "src/telemetry/dashboard_state.py": "lo importa: el panel",
    # El registro de libros: la ruta, para guardarlo en git. No lo lee.
    "src/estado/los_libros.py": "la ruta del libro, en LIBROS",
    # La guardia de la lista blanca del panel: la clave, sin cuadro.
    "src/analysis/test_la_lista_blanca_v1.py": "la clave en NO_SE_PINTAN",
    # La guardia del reloj: el nombre de ESTA guardia, en su lista de
    # las que pueden mirar el reloj (mide el tope de las noticias).
    "src/analysis/test_el_reloj_de_las_guardias_v1.py": "esta guardia, en PUEDEN_MIRAR_EL_RELOJ",
}


def test_ninguna_decision_lo_lee():
    """Fase 1: lo lee el panel y nadie mas. Ni pujas, ni ventas, ni once."""
    nombran, importan = [], []
    for fichero in sorted((RAIZ / "src").rglob("*.py")):
        if fichero.name in {"el_informe_de_la_manana.py", "test_el_informe_de_la_manana_v1.py"}:
            continue
        texto = fichero.read_text(encoding="utf-8", errors="replace")
        if "el_informe_de_la_manana" in texto:
            nombran.append(fichero.relative_to(RAIZ).as_posix())
        if "intelligence.el_informe_de_la_manana" in texto or "import el_informe_de_la_manana" in texto:
            importan.append(fichero.relative_to(RAIZ).as_posix())
    assert nombran == sorted(LOS_QUE_LO_NOMBRAN), nombran
    assert importan == ["src/telemetry/dashboard_state.py"], importan
    fuente = Path(M.__file__).read_text(encoding="utf-8")
    for prohibido in ("BiwengerWriteClient", "place_bid", "accept_offer", "list_player_for_sale",
                      "escritor_factory", "write_client"):
        assert prohibido not in fuente, prohibido
    # El paso del workflow: despues de la rotacion, antes de guardar los libros,
    # y sin romper la vuelta.
    vivo = (RAIZ / ".github" / "workflows" / "bordalas-live.yml").read_text(encoding="utf-8")
    paso = "python -m src.intelligence.el_informe_de_la_manana || true"
    assert vivo.index("python -m src.actions.la_rotacion") < vivo.index(paso) \
        < vivo.index("guardar_los_libros.py --empujar"), "el paso esta fuera de sitio"
    ensayo = (RAIZ / ".github" / "workflows" / "bordalas-ensayo.yml").read_text(encoding="utf-8")
    assert ensayo.index("python -m src.actions.la_rotacion") < ensayo.index(paso)


TESTS = [
    test_la_formula_esta_clavada_al_laboratorio,
    test_los_nuevos_tras_cada_reset,
    test_una_vez_por_dia_de_mercado,
    test_de_punta_a_punta,
    test_la_red_que_falla_no_rompe_nada,
    test_el_tope_de_tiempo_es_de_reloj,
    test_la_ventana_de_las_noticias,
    test_la_prensa_vieja_no_cuenta,
    test_el_mercado_sin_renovar_no_se_apunta,
    test_la_cuota_y_el_cambio_del_historico,
    test_clasifica_los_titulares,
    test_el_html_solo_se_lee,
    test_nace_apagado,
    test_nunca_lanza_con_basura,
    test_nunca_escribe_fuera_de_su_libro,
    test_ninguna_decision_lo_lee,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
