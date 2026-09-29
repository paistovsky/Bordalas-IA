"""
La orden del gestor: ejecuta lo escrito, y nada mas.

QUE SE PRUEBA (29/09/2026)

    1. Puja por el fichaje si esta en el mercado y no hay puja nuestra
       igual o mayor; no repite si ya esta; no supera maximumBid.
    2. No vende NADA mientras el fichaje no este en la plantilla.
    3. Con el fichaje dentro: publica a los de la orden, y acepta la
       oferta del Computer solo si llega al suelo.
    4. Una orden que nombra a Yamal no vale; una caducada tampoco.
    5. Cancela nuestra puja viva por los de `no_pujar`.
    6. Apagada, `correr` no crea escritor.

    Sin red, sin login y sin disco de produccion.
"""

from __future__ import annotations

import os
import sys
import tempfile

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.actions.la_orden_del_gestor as orden_mod        # noqa: E402


AHORA = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)

ROBERTO, JUTGLA, BLANCO, LEJEUNE, YAMAL = 35678, 3159, 1612, 2476, 1

ORDEN = {
    "caduca": "2026-10-09T15:00:00+02:00",
    "fichar": [{"player_id": ROBERTO, "nombre": "Roberto", "puja": 8_800_000}],
    "no_pujar": [{"player_id": LEJEUNE, "nombre": "Lejeune"}],
    "vender_si_ficha": {
        "si_esta": ROBERTO,
        "jugadores": [
            {"player_id": JUTGLA, "nombre": "Jutgla", "suelo": 3_000_000},
            {"player_id": BLANCO, "nombre": "Antonio Blanco", "suelo": 3_100_000},
        ],
    },
}


def _decide(**kw):
    base = dict(
        mercado={ROBERTO: 8_380_000},
        nuestras_pujas={},
        plantilla={JUTGLA, BLANCO, YAMAL},
        ofertas_del_computer={},
        en_venta=set(),
        precios={JUTGLA: 3_170_000, BLANCO: 3_320_000},
        maximo_de_puja=14_408_784,
    )
    base.update(kw)
    return orden_mod.decidir(ORDEN, **base)


def _tipos(acciones):
    return [(a["accion"], a["player_id"]) for a in acciones]


def test_puja_por_el_fichaje() -> None:
    a = _decide()
    assert _tipos(a) == [("PUJAR", ROBERTO)], a
    assert a[0]["importe"] == 8_800_000, a


def test_no_repite_ni_supera_el_maximo() -> None:
    a = _decide(nuestras_pujas={ROBERTO: {"offer_id": 9, "amount": 8_800_000}})
    assert a == [], a

    a = _decide(maximo_de_puja=5_000_000)
    assert _tipos(a) == [("NADA", ROBERTO)], a

    a = _decide(mercado={})
    assert a == [], "sin estar en el mercado no se puja"


def test_no_vende_sin_el_fichaje() -> None:
    a = _decide(ofertas_del_computer={JUTGLA: {"offer_id": 5, "amount": 9_000_000}})
    assert not [x for x in a if x["accion"] != "PUJAR"], a


def test_con_el_fichaje_publica_y_cobra_con_suelo() -> None:
    plantilla = {ROBERTO, JUTGLA, BLANCO, YAMAL}

    a = _decide(plantilla=plantilla, mercado={})
    assert sorted(_tipos(a)) == sorted([
        ("PONER_A_LA_VENTA", JUTGLA), ("PONER_A_LA_VENTA", BLANCO),
    ]), a

    a = _decide(
        plantilla=plantilla, mercado={}, en_venta={JUTGLA, BLANCO},
        ofertas_del_computer={
            JUTGLA: {"offer_id": 71, "amount": 3_050_000},
            BLANCO: {"offer_id": 72, "amount": 3_000_000},   # bajo el suelo
        },
    )
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", JUTGLA)], a
    assert a[0]["offer_id"] == 71, a


def test_yamal_y_caducidad() -> None:
    mala = {**ORDEN, "vender_si_ficha": {"si_esta": ROBERTO, "jugadores": [
        {"player_id": YAMAL, "nombre": "Yamal", "suelo": 1}]}}
    assert orden_mod.validar(mala, AHORA) == "NOMBRA_A_UN_INTOCABLE"
    assert orden_mod.validar(ORDEN, AHORA) is None
    tarde = datetime(2026, 10, 10, tzinfo=timezone.utc)
    assert orden_mod.validar(ORDEN, tarde) == "CADUCADA"
    assert orden_mod.validar(None, AHORA) == "SIN_ORDEN"


def test_cancela_la_puja_de_no_pujar() -> None:
    a = _decide(nuestras_pujas={LEJEUNE: {"offer_id": 44, "amount": 3_664_371}})
    assert ("CANCELAR_PUJA", LEJEUNE) in _tipos(a), a


def test_apagada_no_crea_escritor() -> None:
    antes = os.environ.pop(orden_mod.ENV, None)
    try:
        creados = []
        s = orden_mod.correr(
            {"snapshot": {}}, escritor_factory=lambda: creados.append(1),
        )
        assert creados == [] and s["motivo"] == "APAGADA", s
    finally:
        if antes is not None:
            os.environ[orden_mod.ENV] = antes


def test_lee_la_foto_de_la_vuelta() -> None:
    YO = 14175949
    snap = {
        "league": {"user": {"id": YO}},
        "my_team": [{"id": JUTGLA, "price": 3_170_000}, {"id": YAMAL, "price": 1}],
        "market": {
            "status": {"balance": 206_284, "maximumBid": 14_408_784},
            "sales": [
                {"player": {"id": ROBERTO}, "price": 8_380_000, "user": None},
                {"player": {"id": JUTGLA}, "price": 3_170_000, "user": {"id": YO}},
                {"player": {"id": 999}, "price": 5, "user": {"id": 123}},
            ],
            "offers": [
                {"id": 1, "status": "waiting", "amount": 3_664_371,
                 "from": {"id": YO}, "requestedPlayers": [{"id": LEJEUNE}]},
                {"id": 2, "status": "waiting", "amount": 3_100_000,
                 "from": None, "requestedPlayers": [{"id": JUTGLA}]},
                {"id": 3, "status": "rejected", "amount": 9,
                 "from": {"id": YO}, "requestedPlayers": [{"id": 5}]},
            ],
        },
    }
    f = orden_mod.leer_la_foto(snap, YO)
    assert f["mercado"] == {ROBERTO: 8_380_000}, f["mercado"]
    assert f["en_venta"] == {JUTGLA}, f["en_venta"]
    assert f["nuestras_pujas"] == {LEJEUNE: {"offer_id": 1, "amount": 3_664_371}}, f
    assert f["ofertas_del_computer"] == {JUTGLA: {"offer_id": 2, "amount": 3_100_000}}, f
    assert f["plantilla"] == {JUTGLA, YAMAL} and f["maximo_de_puja"] == 14_408_784, f


def test_la_orden_del_repo_vale() -> None:
    o = orden_mod.leer_la_orden(RAIZ / "config" / "la_orden_del_gestor.json")
    assert o is not None, "no se lee config/la_orden_del_gestor.json"
    assert orden_mod.validar(o, AHORA) is None, orden_mod.validar(o, AHORA)


def test_no_se_publica_a_un_protegido() -> None:
    import src.biwenger.write_client as escritura

    cliente = object.__new__(escritura.BiwengerWriteClient)

    class _C:
        BASE_URL = "https://biwenger.invalid/api/v2"

    cliente.client = _C()
    cliente.version, cliente.league_id, cliente.user_id = "0", 1, 2

    antes = os.environ.get(orden_mod.ENV)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(__import__("json").dumps(
            {**ORDEN, "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}]}
        ), encoding="utf-8")
        ruta_antes = orden_mod.RUTA
        orden_mod.RUTA = ruta
        try:
            os.environ[orden_mod.ENV] = "1"
            assert orden_mod.protegidos(ruta, AHORA) == {YAMAL, ROBERTO}
            r = cliente.list_player_for_sale(player_id=YAMAL, price=1, execute=True)
            assert r.get("blocked") == "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR", r
            r = cliente.list_player_for_sale(player_id=JUTGLA, price=1, execute=False)
            assert "blocked" not in r, r

            os.environ.pop(orden_mod.ENV, None)
            r = cliente.list_player_for_sale(player_id=YAMAL, price=1, execute=False)
            assert "blocked" not in r, "apagada no debe proteger"
        finally:
            orden_mod.RUTA = ruta_antes
            if antes is None:
                os.environ.pop(orden_mod.ENV, None)
            else:
                os.environ[orden_mod.ENV] = antes


def test_el_ultimo_recurso() -> None:
    orden = {**ORDEN, "vender_si_ficha": {"si_esta": ROBERTO, "jugadores": [
        {"player_id": JUTGLA, "nombre": "Jutgla", "suelo": 2_900_000,
         "desde": "2026-10-08T07:00:00+02:00", "si_saldo_negativo": True},
    ]}}
    base = dict(
        mercado={}, nuestras_pujas={}, plantilla={ROBERTO, JUTGLA},
        ofertas_del_computer={JUTGLA: {"offer_id": 7, "amount": 2_950_000}},
        en_venta={JUTGLA}, precios={JUTGLA: 3_170_000},
        maximo_de_puja=14_000_000,
    )
    antes = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
    despues = datetime(2026, 10, 8, 12, tzinfo=timezone.utc)

    assert orden_mod.decidir(orden, **base, saldo=-500_000, ahora=antes) == []
    assert orden_mod.decidir(orden, **base, saldo=100_000, ahora=despues) == []
    assert orden_mod.decidir(orden, **base, saldo=None, ahora=despues) == []
    a = orden_mod.decidir(orden, **base, saldo=-500_000, ahora=despues)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", JUTGLA)], a


def test_conservar_cierra_la_venta_de_pepe() -> None:
    antes = os.environ.get(orden_mod.ENV)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(__import__("json").dumps(
            {**ORDEN, "conservar": [{"player_id": JUTGLA, "nombre": "Jutgla"}]}
        ), encoding="utf-8")
        try:
            os.environ[orden_mod.ENV] = "1"
            assert orden_mod.conservados(ruta, AHORA) == {JUTGLA, ROBERTO}
            os.environ.pop(orden_mod.ENV, None)
            assert orden_mod.conservados(ruta, AHORA) == set()
        finally:
            if antes is not None:
                os.environ[orden_mod.ENV] = antes

    fuente = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text(
        encoding="utf-8")
    assert fuente.count("_conservados()") >= 2, (
        "las dos ventas de Pepe (cobrar y antes de caducar) deben mirar "
        "`conservar`"
    )


def test_la_pantalla_tampoco_anuncia_al_vetado() -> None:
    import src.analysis.la_subasta as sub

    plan_falso = {"bids": [{"id": LEJEUNE, "name": "Lejeune"},
                           {"id": 7, "name": "Otro"}], "execute": False}
    antes_env = os.environ.get(orden_mod.ENV)
    reales = (sub.plan_del_reset, sub.lectura_del_estado)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(__import__("json").dumps(ORDEN), encoding="utf-8")
        ruta_antes = orden_mod.RUTA
        orden_mod.RUTA = ruta
        try:
            sub.plan_del_reset = lambda **kw: dict(plan_falso)
            sub.lectura_del_estado = lambda state, snapshot: {}
            os.environ[orden_mod.ENV] = "1"
            ids = [b["id"] for b in sub.plan_desde_el_estado({}, {})["bids"]]
            assert ids == [7], ids
            os.environ.pop(orden_mod.ENV, None)
            ids = [b["id"] for b in sub.plan_desde_el_estado({}, {})["bids"]]
            assert ids == [LEJEUNE, 7], "apagada no debe quitar nada"
        finally:
            sub.plan_del_reset, sub.lectura_del_estado = reales
            orden_mod.RUTA = ruta_antes
            if antes_env is None:
                os.environ.pop(orden_mod.ENV, None)
            else:
                os.environ[orden_mod.ENV] = antes_env


TESTS = [
    test_la_pantalla_tampoco_anuncia_al_vetado,
    test_conservar_cierra_la_venta_de_pepe,
    test_el_ultimo_recurso,
    test_no_se_publica_a_un_protegido,
    test_lee_la_foto_de_la_vuelta,
    test_la_orden_del_repo_vale,
    test_puja_por_el_fichaje,
    test_no_repite_ni_supera_el_maximo,
    test_no_vende_sin_el_fichaje,
    test_con_el_fichaje_publica_y_cobra_con_suelo,
    test_yamal_y_caducidad,
    test_cancela_la_puja_de_no_pujar,
    test_apagada_no_crea_escritor,
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
