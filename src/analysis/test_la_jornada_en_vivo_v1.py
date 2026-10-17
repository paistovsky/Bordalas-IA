"""
LA JORNADA EN VIVO (17/10/2026). Guardias de `scripts/la_jornada_en_vivo.py`.

    El once que cuenta es el que empezo la jornada (el `mi_once` del
    marcador de antes), no el `lineup` de ahora: el 17/10 el script daba
    12 puntos en vez de 5 porque contaba los 7 de temporada de Sergi
    Cardona, fichado con la J9 empezada, en lugar de Diego Rico.
"""

from __future__ import annotations

import sys

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import scripts.la_jornada_en_vivo as V                 # noqa: E402


ONCE_J9 = [38433, 1760, 1599, 5678, 19862, 29661, 14800, 1969, 26271, 35678, 25777]
ONCE_J10 = [38433, 1760, 1599, 30493, 19862, 29661, 14800, 1969, 26271, 35678, 25777]


def _ficha(pid, equipo="Osasuna", nombre=None):
    return {"id": pid, "name": nombre or str(pid), "team_name": equipo}


def _status():
    plantilla = [_ficha(p) for p in ONCE_J10] + [_ficha(5678, "Osasuna", "Diego Rico")]
    return {"lineup": {"players": [_ficha(p) for p in ONCE_J10]},
            "roster": {"players": plantilla}}


def _marcador(once, totales):
    return {"jornadas": {"4906": {"mi_once": {"formation": "3-4-3", "players": once},
                                  "nombres": {"5678": "Diego Rico"},
                                  "totales": totales}}}


def test_cuenta_el_once_que_empezo_no_el_de_ahora():
    previo = _marcador(ONCE_J9, {"30493": 0, "5678": 6})
    ahora = _marcador(ONCE_J10, {"30493": 7, "5678": 6, "29661": 3})
    calendario = {"matchdays": []}
    r = V.la_jornada(_status(), calendario, datetime(2026, 10, 17, 11, tzinfo=timezone.utc),
                     previo, ahora)
    ids = [f["nombre"] for f in r["filas"]]
    assert "Diego Rico" in ids and "30493" not in ids
    # Los 7 de Cardona no cuentan; los 3 de Olasagasti si.
    assert r["puntos"] == 3


def test_el_que_ya_no_esta_sale_con_su_nombre():
    status = _status()
    status["roster"]["players"] = [p for p in status["roster"]["players"] if p["id"] != 5678]
    once = V.el_once_que_empezo(_marcador(ONCE_J9, {}), status)
    assert len(once) == 11
    rico = [p for p in once if p["id"] == 5678][0]
    assert rico["name"] == "Diego Rico" and rico["team_name"] == "?"


def test_sin_marcador_previo_el_lineup_de_siempre():
    assert V.el_once_que_empezo(None, _status()) is None
    assert V.el_once_que_empezo({"jornadas": {"1": {"mi_once": {"players": [1, 2]}}}}, _status()) is None
    r = V.la_jornada(_status(), {"matchdays": []}, datetime(2026, 10, 17, tzinfo=timezone.utc))
    assert [f["nombre"] for f in r["filas"]] == [str(p) for p in ONCE_J10]


TESTS = [
    test_cuenta_el_once_que_empezo_no_el_de_ahora,
    test_el_que_ya_no_esta_sale_con_su_nombre,
    test_sin_marcador_previo_el_lineup_de_siempre,
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
