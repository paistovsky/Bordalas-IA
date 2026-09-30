"""
El tablon del dia, en frases para el panel (29/09/2026).

    1. Cuenta fichajes, ventas al mercado y entre managers, rachas y
       jornadas, con nombres de jugador del catalogo.
    2. Solo las ultimas 24 h, lo mas nuevo arriba, hora de Madrid.
    3. Ignora porras y movimientos de LaLiga.
    4. Con basura no lanza.
    Sin red y sin disco.
"""

from __future__ import annotations

import sys

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.telemetry.el_tablon import el_tablon_de_hoy          # noqa: E402


AHORA = datetime(2026, 9, 29, 18, 0, tzinfo=timezone.utc)
T = int(AHORA.timestamp())

EVENTOS = [
    {"type": "market", "date": T - 3600, "content": [
        {"player": 1, "to": {"name": "Pollo17"}, "amount": 8_707_000,
         "bids": [{"user": {"name": "X"}}, {"user": {"name": "Y"}}]}]},
    {"type": "transfer", "date": T - 7200, "content": [
        {"player": 2, "from": {"name": "Pepe Bordalás"}, "amount": 150_300}]},
    {"type": "transfer", "date": T - 7300, "content": [
        {"player": 2, "from": {"name": "A"}, "to": {"name": "B"}, "amount": 5}]},
    {"type": "bonus", "date": T - 100, "content": [
        {"user": {"name": "Pollo17"}, "amount": 250_000, "reason": "dailyStreak"}]},
    {"type": "bettingPool", "date": T - 50, "content": {}},
    {"type": "market", "date": T - 3 * 86400, "content": [
        {"player": 1, "to": {"name": "Viejo"}, "amount": 1}]},
    {"type": "roundFinished", "date": T - 60, "content": {
        "round": {"name": "Jornada 7"},
        "results": [{"user": {"name": "L"}, "points": 61},
                    {"user": {"name": "M"}, "points": 59}]}},
]


def test_frases_y_orden() -> None:
    t = el_tablon_de_hoy(EVENTOS, {1: "Moleiro", 2: "Diaby"}, ahora=AHORA)
    textos = [l["texto"] for l in t["lineas"]]
    assert t["n"] == 5, textos
    assert textos[0].startswith("Termina la Jornada 7"), textos
    assert "Pollo17 cobra 250.000 € por la racha diaria." in textos, textos
    assert any("Pollo17 ficha a Moleiro por 8.707.000 €" in x and "2 rivales" in x
               for x in textos), textos
    assert "Pepe Bordalás vende a Diaby al mercado por 150.300 €." in textos, textos
    assert any(x.startswith("A vende a Diaby a B") for x in textos), textos
    assert not any("Viejo" in x for x in textos), "entro uno de hace 3 dias"
    assert t["lineas"][0]["hora"] == "29/09 19:59", t["lineas"][0]


def test_con_basura_no_lanza() -> None:
    for basura in (None, [], {}, [None, 3, {"type": "market", "date": "x"}],
                   [{"type": "market", "date": T, "content": None}]):
        t = el_tablon_de_hoy(basura, None, ahora=AHORA)
        assert isinstance(t["lineas"], list), t


def test_las_reglas_encendidas() -> None:
    from src.telemetry.el_tablon import QUE_HACE, las_reglas_encendidas
    from src.analysis.los_interruptores_de_produccion import los_de_produccion

    r = las_reglas_encendidas()
    prod = los_de_produccion()["interruptores"]
    assert r["ok"] and r["n"] == len(prod), r
    sin_frase = [x for x in prod if x not in QUE_HACE]
    assert not sin_frase, (
        f"interruptores encendidos sin frase para el dueno: {sin_frase}"
    )


def test_la_semana() -> None:
    t = el_tablon_de_hoy(EVENTOS, {1: "Moleiro"}, ahora=AHORA, horas=168)
    assert any("Viejo" in l["texto"] for l in t["lineas"]), t


def test_la_orden_en_el_panel() -> None:
    import os
    from src.telemetry.el_tablon import la_orden_para_el_panel
    antes = os.environ.get("BORDALAS_LA_ORDEN_DEL_GESTOR")
    try:
        os.environ["BORDALAS_LA_ORDEN_DEL_GESTOR"] = "1"
        o = la_orden_para_el_panel()
        assert "estado" in o and isinstance(o.get("fichar"), list), o
        os.environ.pop("BORDALAS_LA_ORDEN_DEL_GESTOR", None)
        assert la_orden_para_el_panel()["viva"] is False
    finally:
        if antes is not None:
            os.environ["BORDALAS_LA_ORDEN_DEL_GESTOR"] = antes


TESTS = [test_la_orden_en_el_panel, test_frases_y_orden, test_con_basura_no_lanza,
         test_las_reglas_encendidas, test_la_semana]


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
