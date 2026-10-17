"""
LA PUERTA, A PRECIO DE MERCADO (16/10/2026). Guardias de
`BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO` en
`src/actions/la_ronda_de_la_manana.py` (con la foto y el `ejecutar` de
`src/actions/la_orden_del_gestor.py`).

    1. La foto separa lo que venden los managers (lo que piden y quién).
    2. Solo entran los que piden su valor (como mucho + 2 % desde el 17/10).
    3. La puja va a nombre del vendedor; la del Computer, como siempre.
    4. Con la puerta, la ronda puja por el del manager; sin ella, no.
    5. Nace apagada.
"""

from __future__ import annotations

import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.la_ronda_de_la_manana as ronda      # noqa: E402
import src.analysis.la_proxima_jornada as proxima       # noqa: E402

from src.actions.la_orden_del_gestor import ejecutar, leer_la_foto   # noqa: E402


YO = 14175949
MANZAGOOL = 14176382
NUNEZ, FREEMAN, CARO, DEL_COMPUTER = 900001, 900002, 900003, 900004


def _ficha(precio, sube=40_000, estado="ok", puntos=20, partidos=4):
    return {"price": precio, "priceIncrement": sube, "status": estado,
            "points": puntos, "playedHome": partidos // 2,
            "playedAway": partidos - partidos // 2}


def _snapshot():
    return {
        "league": {"user": {"id": YO}},
        "market": {
            "sales": [
                {"player": {"id": DEL_COMPUTER}, "price": 2_000_000, "user": None},
                {"player": {"id": NUNEZ}, "price": 1_080_000, "user": {"id": MANZAGOOL}},
                {"player": {"id": CARO}, "price": 1_400_000, "user": {"id": MANZAGOOL}},
                {"player": {"id": 1}, "price": 5, "user": {"id": YO}},
            ],
            "offers": [],
            "status": {"maximumBid": 14_000_000, "balance": 486_683},
        },
        "my_team": [{"id": 1, "price": 5}],
        "catalog": {"data": {"players": {
            str(NUNEZ): _ficha(1_070_000),
            str(CARO): _ficha(1_200_000),
            str(DEL_COMPUTER): _ficha(2_000_000, sube=0),
        }}},
    }


def test_la_foto_separa_lo_que_venden_los_managers():
    f = leer_la_foto(_snapshot(), YO)
    assert f["mercado"] == {DEL_COMPUTER: 2_000_000}, f["mercado"]
    assert f["en_venta"] == {1}, f["en_venta"]
    assert f["de_managers"] == {
        NUNEZ: {"precio": 1_080_000, "vendedor": MANZAGOOL},
        CARO: {"precio": 1_400_000, "vendedor": MANZAGOOL},
    }, f["de_managers"]
    # Sin foto, vacío y sin lanzar.
    assert leer_la_foto(None, YO)["de_managers"] == {}


def test_solo_entran_los_que_piden_su_valor():
    fichas = {1: {"price": 1_000_000}, 2: {"price": 1_000_000}, 3: {"price": 1_000_000},
              4: {}, 5: {"price": 1_000_000}, 6: {"price": 1_000_000}}
    de = {
        1: {"precio": 1_000_000, "vendedor": 7},     # su valor: entra
        2: {"precio": 1_020_000, "vendedor": 7},     # +2 %: entra
        3: {"precio": 1_021_000, "vendedor": 7},     # +2,1 %: fuera
        4: {"precio": 900_000, "vendedor": 7},       # sin valor: fuera
        5: {"precio": 900_000, "vendedor": None},    # sin vendedor: fuera
        6: {"precio": 900_000, "vendedor": 7},       # vetado: fuera
    }
    piden, vendedores = ronda.los_de_managers(de, fichas, veto={6})
    assert piden == {1: 1_000_000, 2: 1_020_000}, piden
    assert vendedores == {1: 7, 2: 7}, vendedores
    assert ronda.los_de_managers("basura", None) == ({}, {})
    assert ronda.los_de_managers({1: "x"}, fichas) == ({}, {})


class _Escritor:
    """Como el de verdad: `seller_user_id` es opcional."""

    def __init__(self):
        self.pujas = []

    def place_bid(self, player_id, amount, execute=False, seller_user_id=None):
        self.pujas.append((player_id, amount, seller_user_id))
        return {"sent": True, "success": True, "http_status": 200}


class _EscritorViejo:
    """Los dobles de otras guardias no conocen `seller_user_id`."""

    def __init__(self):
        self.pujas = []

    def place_bid(self, player_id, amount, execute=False):
        self.pujas.append((player_id, amount))
        return {"sent": True, "success": True, "http_status": 200}


def test_la_puja_va_a_nombre_del_vendedor():
    e = _Escritor()
    h = ejecutar([
        {"accion": "PUJAR", "player_id": NUNEZ, "importe": 1_091_000, "vendedor": MANZAGOOL},
        {"accion": "PUJAR", "player_id": DEL_COMPUTER, "importe": 2_020_000},
    ], e)
    assert e.pujas == [(NUNEZ, 1_091_000, MANZAGOOL), (DEL_COMPUTER, 2_020_000, None)], e.pujas
    assert all(x["exito"] for x in h), h
    # La del Computer no le pasa nada nuevo a un escritor que no lo conoce.
    v = _EscritorViejo()
    h = ejecutar([{"accion": "PUJAR", "player_id": DEL_COMPUTER, "importe": 2_020_000}], v)
    assert v.pujas == [(DEL_COMPUTER, 2_020_000)] and h[0]["exito"], (v.pujas, h)


def _correr(puerta: bool):
    entorno = {k: os.environ.get(k) for k in (ronda.ENV, ronda.ENV_PUERTA)}
    viejos = (ronda.horas_a_la_jornada, ronda._puede_escribir, proxima.jornada_en_curso)
    e = _Escritor()
    try:
        os.environ[ronda.ENV] = "1"
        if puerta:
            os.environ[ronda.ENV_PUERTA] = "1"
        else:
            os.environ.pop(ronda.ENV_PUERTA, None)
        ronda.horas_a_la_jornada = lambda ahora: 100.0
        ronda._puede_escribir = lambda ahora: True
        proxima.jornada_en_curso = lambda ahora, ruta=None: False
        with tempfile.TemporaryDirectory() as d:
            r = ronda.correr({"snapshot": _snapshot()}, 120,
                             escritor_factory=lambda: e,
                             libro_ruta=Path(d) / "la_ronda.json")
            puerta = Path(d) / "la_puerta.jsonl"
            r["_puerta"] = (puerta.read_text().splitlines() if puerta.exists() else [])
        return r, e
    finally:
        ronda.horas_a_la_jornada, ronda._puede_escribir, proxima.jornada_en_curso = viejos
        for k, v in entorno.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_con_la_puerta_puja_por_el_del_manager_y_sin_ella_no():
    r, e = _correr(puerta=False)
    assert r["motivo"] == "NADA_QUE_HACER", r
    assert e.pujas == [], e.pujas
    assert "puerta" not in r, r

    r, e = _correr(puerta=True)
    assert r["motivo"] == "EJECUTADA", r
    # Núñez pide su valor + 0,9 % y sube +3,7 %: se puja a precio + 1 %,
    # a nombre de Manzagool. El caro (+16,7 %) no entra.
    assert e.pujas == [(NUNEZ, ronda.la_puja(1_080_000), MANZAGOOL)], e.pujas
    assert r["puerta"] == {"abierta": True, "a_precio_de_mercado": [NUNEZ]}, r["puerta"]
    assert r["acciones"][0]["vendedor"] == MANZAGOOL, r["acciones"]
    # Y la oferta queda apuntada en el libro de la puerta (en la carpeta
    # del libro de la ronda: nunca en el de verdad).
    import json as _json
    assert r["puerta_apuntadas"] == 1 and len(r["_puerta"]) == 1, r
    fila = _json.loads(r["_puerta"][0])
    assert (fila["player_id"], fila["vendedor"], fila["pide"], fila["oferta"]) == (
        NUNEZ, MANZAGOOL, 1_080_000, ronda.la_puja(1_080_000)), fila


def test_nace_apagada():
    viejo = os.environ.pop(ronda.ENV_PUERTA, None)
    try:
        assert ronda.la_puerta_abierta() is False
        os.environ[ronda.ENV_PUERTA] = "1"
        assert ronda.la_puerta_abierta() is True
    finally:
        os.environ.pop(ronda.ENV_PUERTA, None)
        if viejo is not None:
            os.environ[ronda.ENV_PUERTA] = viejo


TESTS = [
    test_la_foto_separa_lo_que_venden_los_managers,
    test_solo_entran_los_que_piden_su_valor,
    test_la_puja_va_a_nombre_del_vendedor,
    test_con_la_puerta_puja_por_el_del_manager_y_sin_ella_no,
    test_nace_apagada,
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
