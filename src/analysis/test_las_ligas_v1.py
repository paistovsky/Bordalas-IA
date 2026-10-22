"""
LAS LIGAS (22/10/2026). Guardias de `src/biwenger/client.py`
(`select_league`, `la_liga_que_juega`).

    El dueño se apuntó sin querer a una segunda liga ('Reto el clásico').
    Pepe elegía la PRIMERA de la cuenta: si Biwenger la ponía delante,
    pujaba y vendía en la liga equivocada.

    1. Juega la liga de `config/las_ligas.json` (El Chiringuito), esté
       donde esté en la lista de la cuenta.
    2. `BIWENGER_LEAGUE_ID` manda (para cambiar de liga sin tocar código).
    3. Si la liga no está en la cuenta, se para: nunca juega en otra.
    4. Las cabeceras X-League y X-User son las de esa liga.

Con una cuenta de mentira: ni red ni credenciales.
"""

from __future__ import annotations

import json
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import requests                                          # noqa: E402

import src.biwenger.client as C                           # noqa: E402


CHIRINGUITO = {"id": 2165477, "name": "El Chiringuito", "user": {"id": 14175949}}
RETO = {"id": 9999999, "name": "Reto el clásico", "user": {"id": 777}}


def _cliente(ligas):
    c = object.__new__(C.BiwengerClient)
    c.session = requests.Session()
    c.get_account = lambda: {"leagues": ligas, "dailyStreak": 1}
    return c


def test_juega_el_chiringuito_aunque_no_sea_la_primera():
    for ligas in ([RETO, CHIRINGUITO], [CHIRINGUITO, RETO], [CHIRINGUITO]):
        c = _cliente(ligas)
        liga = c.select_league()
        assert liga["id"] == 2165477 and c.league_id == 2165477 and c.user_id == 14175949, ligas
        assert c.session.headers["X-League"] == "2165477"
        assert c.session.headers["X-User"] == "14175949"
        assert {"id": 2165477, "name": "El Chiringuito"} in c.leagues


def test_sin_la_liga_se_para():
    for ligas in ([RETO], [RETO, {"id": "x"}], [None, RETO]):
        c = _cliente(ligas)
        try:
            c.select_league()
        except RuntimeError as error:
            assert "no esta en la cuenta" in str(error)
        else:
            raise AssertionError(f"jugaria en otra liga: {ligas}")
    try:
        _cliente([]).select_league()
    except RuntimeError:
        pass
    else:
        raise AssertionError("sin ligas no se para")


def test_el_entorno_manda_y_la_config_vale():
    assert C.la_liga_que_juega(entorno={}) == 2165477
    assert C.la_liga_que_juega(entorno={"BIWENGER_LEAGUE_ID": "9999999"}) == 9999999
    assert C.la_liga_que_juega(entorno={"BIWENGER_LEAGUE_ID": " x "}) == 2165477
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = Path(carpeta) / "las_ligas.json"
        ruta.write_text(json.dumps({"activa": 9999999}))
        assert C.la_liga_que_juega(ruta=ruta, entorno={}) == 9999999
        ruta.write_text("basura")
        assert C.la_liga_que_juega(ruta=ruta, entorno={}) == 2165477
        ruta.write_text(json.dumps({"activa": True}))
        assert C.la_liga_que_juega(ruta=ruta, entorno={}) == 2165477
    assert C.la_liga_que_juega(ruta="/no/existe.json", entorno={}) == 2165477
    # La del repo: El Chiringuito.
    assert json.loads(C.LAS_LIGAS.read_text())["activa"] == 2165477


TESTS = [
    test_juega_el_chiringuito_aunque_no_sea_la_primera,
    test_sin_la_liga_se_para,
    test_el_entorno_manda_y_la_config_vale,
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
