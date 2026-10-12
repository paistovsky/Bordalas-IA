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
    7. LAS GUARDIAS (12/10/2026): a menos de 40 h de la jornada (o sin
       calendario) no se pone ni se sube la puja de `fichar`; el que sale
       no se vende si su relevo no esta 'ok' en el catalogo; con una
       jornada jugandose no se acepta ninguna oferta del Computer. Y
       `correr` las pasa de verdad (calendario y catalogo de prueba, con
       la hora puesta a mano).

    Sin red, sin login y sin disco de produccion.
"""

from __future__ import annotations

import json
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



# La misma orden sin fecha de caducidad cercana, para las guardias que
# usan el reloj real (el cliente de escritura y la pantalla).
VIVA = {**ORDEN, "caduca": "2099-01-01T00:00:00+00:00"}

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
            {**VIVA, "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}]}
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
        # Con el reloj REAL (plan_desde_el_estado no recibe la hora): una
        # orden de prueba que caducaba el 09/10 15:00 paro la verja ese dia.
        ruta.write_text(__import__("json").dumps(VIVA), encoding="utf-8")
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


def test_subir_la_puja() -> None:
    # maximumBid ya descuenta la puja viva (8,95 M): 5,46 M libres.
    a = _decide(nuestras_pujas={ROBERTO: {"offer_id": 9, "amount": 8_000_000}},
                maximo_de_puja=5_458_784)
    assert _tipos(a) == [("PUJAR", ROBERTO)], a
    assert a[0]["sustituye"]["offer_id"] == 9, a

    class _Esc:
        def __init__(self, admite_dos):
            self.admite_dos, self.log, self.vivas = admite_dos, [], {9}

        def place_bid(self, player_id, amount, execute=False):
            ok = self.admite_dos or not self.vivas
            self.log.append(("place", amount, ok))
            return {"sent": True, "success": ok}

        def cancel_bid(self, offer_id, execute=False):
            self.log.append(("cancel", offer_id))
            self.vivas.discard(offer_id)
            return {"sent": True, "success": True}

    e = _Esc(admite_dos=True)
    orden_mod.ejecutar(a, e)
    assert e.log == [("place", 8_800_000, True), ("cancel", 9)], e.log

    e = _Esc(admite_dos=False)
    h = orden_mod.ejecutar(a, e)
    assert e.log == [("place", 8_800_000, False), ("cancel", 9),
                     ("place", 8_800_000, True)], e.log
    assert h[0]["exito"] is True, h


def test_se_vende_solo_con_el_relevo_dentro() -> None:
    ORIOL, UNAI = 77, 88
    orden = {**ORDEN, "vender_si_ficha": {"si_esta": ROBERTO, "jugadores": [
        {"player_id": UNAI, "nombre": "Unai", "suelo": 2_700_000, "si_esta": ORIOL},
    ]}}
    base = dict(mercado={}, nuestras_pujas={}, ofertas_del_computer={
        UNAI: {"offer_id": 5, "amount": 2_865_000}}, en_venta={UNAI},
        precios={UNAI: 2_770_000}, maximo_de_puja=14_000_000)
    a = orden_mod.decidir(orden, plantilla={ROBERTO, UNAI}, **base)
    assert a == [], "sin el relevo dentro no se vende"
    a = orden_mod.decidir(orden, plantilla={ROBERTO, UNAI, ORIOL}, **base)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", UNAI)], a


def test_los_viajes_cortos() -> None:
    SUBE, OTRO = 501, 502
    orden = {**ORDEN, "vender_si_ficha": {}, "fichar": [], "viajes": {
        "hasta": "2026-10-07T07:00:00+02:00", "tope_por_viaje": 2_000_000,
        "tope_total": 3_000_000, "candidatos": [
            {"player_id": SUBE, "nombre": "Sube", "puja": 1_900_000},
            {"player_id": OTRO, "nombre": "Otro", "puja": 1_500_000},
        ]}}
    base = dict(nuestras_pujas={}, ofertas_del_computer={}, en_venta=set(),
                precios={SUBE: 1_950_000}, maximo_de_puja=12_000_000)
    lunes = datetime(2026, 10, 1, 8, tzinfo=timezone.utc)
    a = orden_mod.decidir(orden, mercado={SUBE: 1, OTRO: 1}, plantilla=set(),
                          ahora=lunes, **base)
    assert _tipos(a) == [("PUJAR", SUBE)], ("el tope total deja solo uno", a)

    a = orden_mod.decidir(orden, mercado={}, plantilla={SUBE}, ahora=lunes, **base)
    assert _tipos(a) == [("PONER_A_LA_VENTA", SUBE)], a

    b = {**base, "en_venta": {SUBE},
         "ofertas_del_computer": {SUBE: {"offer_id": 3, "amount": 1_900_000}}}
    a = orden_mod.decidir(orden, mercado={}, plantilla={SUBE}, ahora=lunes, **b)
    assert a == [], "a coste todavia no se vende"
    b["ofertas_del_computer"] = {SUBE: {"offer_id": 3, "amount": 1_950_000}}
    a = orden_mod.decidir(orden, mercado={}, plantilla={SUBE}, ahora=lunes, **b)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", SUBE)], a

    tarde = datetime(2026, 10, 7, 8, tzinfo=timezone.utc)
    b["ofertas_del_computer"] = {SUBE: {"offer_id": 3, "amount": 1_820_000}}
    a = orden_mod.decidir(orden, mercado={}, plantilla={SUBE}, ahora=tarde, **b)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", SUBE)], a
    a = orden_mod.decidir(orden, mercado={OTRO: 1}, plantilla=set(), ahora=tarde, **base)
    assert a == [], "pasada la fecha no se compra"


def test_la_llave_de_yamal() -> None:
    YAMAL = 26271
    venta = {"si_esta": ROBERTO, "jugadores": [
        {"player_id": YAMAL, "nombre": "Yamal", "suelo": 15_000_000}]}
    orden = {**ORDEN, "vender_si_ficha": venta}
    assert orden_mod.validar(orden, AHORA) == "NOMBRA_A_UN_INTOCABLE"
    corta = {**orden, "yamal_por_lesion": {"motivo": "esguince", "baja_estimada_dias": 14}}
    assert orden_mod.validar(corta, AHORA) == "NOMBRA_A_UN_INTOCABLE"
    sin_motivo = {**orden, "yamal_por_lesion": {"baja_estimada_dias": 60}}
    assert orden_mod.validar(sin_motivo, AHORA) == "NOMBRA_A_UN_INTOCABLE"
    larga = {**orden, "yamal_por_lesion": {"motivo": "cruzado", "baja_estimada_dias": 180}}
    assert orden_mod.validar(larga, AHORA) is None
    base = dict(mercado={}, nuestras_pujas={}, ofertas_del_computer={
        YAMAL: {"offer_id": 9, "amount": 16_000_000}}, en_venta={YAMAL},
        precios={YAMAL: 20_000_000}, maximo_de_puja=0)
    a = orden_mod.decidir(orden, plantilla={ROBERTO, YAMAL}, **base)
    assert a == [], "sin la llave no se toca a Yamal"
    a = orden_mod.decidir(larga, plantilla={ROBERTO, YAMAL}, **base)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", YAMAL)], a


def test_varios_cambios_cada_uno_con_su_relevo() -> None:
    A, B, X, Y = 501, 502, 601, 602
    orden = {**ORDEN, "fichar": [], "vender_si_ficha": {"jugadores": [
        {"player_id": X, "nombre": "X", "suelo": 100, "si_esta": A},
        {"player_id": Y, "nombre": "Y", "suelo": 100, "si_esta": B}]}}
    base = dict(mercado={}, nuestras_pujas={}, ofertas_del_computer={
        X: {"offer_id": 1, "amount": 200}, Y: {"offer_id": 2, "amount": 200}},
        en_venta={X, Y}, precios={}, maximo_de_puja=0)
    a = orden_mod.decidir(orden, plantilla={X, Y, A}, **base)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", X)], a
    a = orden_mod.decidir(orden, plantilla={X, Y}, **base)
    assert a == [], "sin ningun relevo dentro no se vende nada"


# ============================================================
# LAS GUARDIAS (12/10/2026)
# ============================================================
#
#     Los ids de la orden del 12/10 (Ivan Romero por Jutgla, Gerard
#     Martin por Diego Rico), escritos aqui: no se lee la de config/.

IVAN, GERARD, RICO = 17937, 34111, 5678
YO = 14175949


def test_el_reloj_no_deja_fichar_tarde() -> None:
    a = _decide(horas_jornada=40.2)
    assert _tipos(a) == [("PUJAR", ROBERTO)], a

    for horas in (39.9, 14.0, 0.5, None):
        a = _decide(horas_jornada=horas)
        assert _tipos(a) == [("NADA", ROBERTO)], (horas, a)
        assert a[0]["guardia"] == "EL_RELOJ" and a[0]["motivo"], a

    # Subirla tampoco; y la viva se deja como esta (ni se cancela).
    viva = {ROBERTO: {"offer_id": 9, "amount": 8_000_000}}
    a = _decide(nuestras_pujas=viva, maximo_de_puja=6_000_000, horas_jornada=30.0)
    assert _tipos(a) == [("NADA", ROBERTO)], a

    # Con la puja viva ya a su importe, ni aviso.
    a = _decide(nuestras_pujas={ROBERTO: {"offer_id": 9, "amount": 8_800_000}},
                horas_jornada=30.0)
    assert a == [], a

    # El reloj no toca `no_pujar`: la puja vetada se sigue retirando.
    a = _decide(nuestras_pujas={LEJEUNE: {"offer_id": 44, "amount": 3_664_371}},
                horas_jornada=10.0)
    assert ("CANCELAR_PUJA", LEJEUNE) in _tipos(a), a
    assert ("PUJAR", ROBERTO) not in _tipos(a), a

    # Sin pasarla (como antes de la guardia), no se mira.
    assert _tipos(_decide()) == [("PUJAR", ROBERTO)]


def test_el_relevo_tiene_que_estar_sano() -> None:
    plantilla = {ROBERTO, JUTGLA, BLANCO, YAMAL}
    ofertas = {JUTGLA: {"offer_id": 71, "amount": 3_050_000}}

    for parte in ({ROBERTO: "doubt"}, {ROBERTO: "injured"},
                  {ROBERTO: "sanctioned"}, {ROBERTO: None}, {}):
        a = _decide(plantilla=plantilla, mercado={},
                    ofertas_del_computer=ofertas, estados=parte)
        assert sorted(_tipos(a)) == sorted([("NADA", JUTGLA), ("NADA", BLANCO)]), (parte, a)
        assert all(x["guardia"] == "EL_PARTE_DEL_RELEVO" and x["relevo"] == ROBERTO
                   and x["motivo"] for x in a), a

    a = _decide(plantilla=plantilla, mercado={}, ofertas_del_computer=ofertas,
                estados={ROBERTO: "ok"})
    assert sorted(_tipos(a)) == sorted([
        ("ACEPTAR_OFERTA_DEL_COMPUTER", JUTGLA), ("PONER_A_LA_VENTA", BLANCO),
    ]), a

    # Cada uno con su relevo (la orden del 12/10): Ivan lesionado deja a
    # Jutgla; Gerard sano deja vender a Diego Rico.
    orden = {**ORDEN, "fichar": [], "vender_si_ficha": {"jugadores": [
        {"player_id": JUTGLA, "nombre": "Jutgla", "suelo": 2_466_000, "si_esta": IVAN},
        {"player_id": RICO, "nombre": "Diego Rico", "suelo": 470_000, "si_esta": GERARD},
    ]}}
    base = dict(mercado={}, nuestras_pujas={}, ofertas_del_computer={
        JUTGLA: {"offer_id": 1, "amount": 2_600_000},
        RICO: {"offer_id": 2, "amount": 500_000}},
        en_venta={JUTGLA, RICO}, precios={}, maximo_de_puja=0)
    a = orden_mod.decidir(orden, plantilla={JUTGLA, RICO, IVAN, GERARD},
                          estados={IVAN: "injured", GERARD: "ok"}, **base)
    assert _tipos(a) == [("NADA", JUTGLA), ("ACEPTAR_OFERTA_DEL_COMPUTER", RICO)], a
    assert a[0]["relevo"] == IVAN and a[0]["estado_del_relevo"] == "injured", a

    # Sin el relevo dentro manda la regla de siempre: ni venta ni aviso.
    a = orden_mod.decidir(orden, plantilla={JUTGLA, RICO, GERARD},
                          estados={IVAN: "ok", GERARD: "ok"}, **base)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", RICO)], a


def test_no_se_cobra_con_la_jornada_jugandose() -> None:
    plantilla = {ROBERTO, JUTGLA, BLANCO, YAMAL}
    ofertas = {JUTGLA: {"offer_id": 71, "amount": 3_050_000}}

    a = _decide(plantilla=plantilla, mercado={}, ofertas_del_computer=ofertas,
                en_curso=True)
    assert sorted(_tipos(a)) == sorted([
        ("NADA", JUTGLA), ("PONER_A_LA_VENTA", BLANCO),
    ]), ("publicar si; cobrar no", a)
    assert [x["guardia"] for x in a if x["accion"] == "NADA"] == ["JORNADA_EN_CURSO"], a

    a = _decide(plantilla=plantilla, mercado={}, ofertas_del_computer=ofertas,
                en_curso=False)
    assert ("ACEPTAR_OFERTA_DEL_COMPUTER", JUTGLA) in _tipos(a), a

    # Tampoco la venta de un viaje.
    SUBE = 501
    orden = {**ORDEN, "vender_si_ficha": {}, "fichar": [], "viajes": {
        "hasta": "2026-10-20T07:00:00+02:00", "tope_por_viaje": 2_000_000,
        "tope_total": 3_000_000,
        "candidatos": [{"player_id": SUBE, "nombre": "Sube", "puja": 1_900_000}]}}
    base = dict(mercado={}, nuestras_pujas={}, plantilla={SUBE}, en_venta={SUBE},
                ofertas_del_computer={SUBE: {"offer_id": 3, "amount": 1_950_000}},
                precios={SUBE: 1_950_000}, maximo_de_puja=0,
                ahora=datetime(2026, 10, 17, 10, tzinfo=timezone.utc))
    a = orden_mod.decidir(orden, en_curso=True, **base)
    assert _tipos(a) == [("NADA", SUBE)], a
    a = orden_mod.decidir(orden, en_curso=False, **base)
    assert _tipos(a) == [("ACEPTAR_OFERTA_DEL_COMPUTER", SUBE)], a


# El calendario de prueba: la J9 empieza el viernes 16/10 a las 21:00 y
# la cierra el Rayo el lunes 19/10 a las 21:00.
CALENDARIO_J9 = {"matchdays": [{
    "matchday": 9,
    "first_kickoff": "2026-10-16T21:00:00+02:00",
    "matches": [
        {"kickoff": "2026-10-16T21:00:00+02:00"},
        {"kickoff": "2026-10-18T18:30:00+02:00"},
        {"kickoff": "2026-10-19T21:00:00+02:00"},
    ],
}]}


def _la_foto(*, ivan_dentro: bool, parte_de_ivan) -> dict:
    """Una vuelta con Jutgla publicado y la oferta del Computer por el."""

    equipo = [{"id": JUTGLA, "price": 2_570_000}]
    ventas = [{"player": {"id": JUTGLA}, "price": 2_570_000, "user": {"id": YO}}]
    if ivan_dentro:
        equipo.append({"id": IVAN, "price": 3_740_000})
    else:
        ventas.append({"player": {"id": IVAN}, "price": 3_740_000, "user": None})
    return {
        "league": {"user": {"id": YO}},
        "my_team": equipo,
        "catalog": {"data": {"players": {
            str(IVAN): {"price": 3_740_000, "status": parte_de_ivan},
            str(JUTGLA): {"price": 2_570_000, "status": "ok"},
        }}},
        "market": {
            "status": {"balance": 659_783, "maximumBid": 12_000_000},
            "sales": ventas,
            "offers": [{"id": 81, "status": "waiting", "amount": 2_600_000,
                        "from": None, "requestedPlayers": [{"id": JUTGLA}]}],
        },
    }


class _Escritor:
    def __init__(self):
        self.log = []

    def place_bid(self, player_id, amount, execute=False):
        self.log.append(("place", player_id, amount))
        return {"sent": True, "success": True}

    def cancel_bid(self, offer_id, execute=False):
        self.log.append(("cancel", offer_id))
        return {"sent": True, "success": True}

    def accept_offer(self, offer_id, execute=False):
        self.log.append(("accept", offer_id))
        return {"sent": True, "success": True}

    def list_player_for_sale(self, player_id, price, execute=False):
        self.log.append(("list", player_id, price))
        return {"sent": True, "success": True}


def test_correr_pasa_las_guardias() -> None:
    orden = {
        "caduca": "2026-11-30T23:59:00+01:00",
        "fichar": [{"player_id": IVAN, "nombre": "Ivan Romero", "puja": 3_777_000}],
        "vender_si_ficha": {"jugadores": [
            {"player_id": JUTGLA, "nombre": "Jutgla", "suelo": 2_466_000, "si_esta": IVAN},
        ]},
    }
    def madrid(dia, hora):                          # octubre, antes del 25: UTC+2
        return datetime(2026, 10, dia, hora - 2, tzinfo=timezone.utc)

    antes = os.environ.get(orden_mod.ENV)
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(json.dumps(orden), encoding="utf-8")
        calendario = Path(tmp) / "calendario.json"
        calendario.write_text(json.dumps(CALENDARIO_J9), encoding="utf-8")

        def vuelta(ahora, cal=calendario, **foto):
            escritores = []

            def fabrica():
                escritores.append(_Escritor())
                return escritores[-1]

            s = orden_mod.correr({"snapshot": _la_foto(**foto)}, escritor_factory=fabrica,
                                 ruta=ruta, ahora=ahora, calendario=cal)
            return s, (escritores[0].log if escritores else None)

        try:
            os.environ[orden_mod.ENV] = "1"

            # Martes 13/10 08:00: a 85 h de la J9, se puja por Ivan.
            s, log = vuelta(madrid(13, 8), ivan_dentro=False, parte_de_ivan="ok")
            assert log == [("place", IVAN, 3_777_000)], (s, log)
            assert 84 < s["reloj"]["horas_jornada"] < 86, s["reloj"]
            assert s["reloj"]["en_curso"] is False, s["reloj"]

            # Jueves 15/10 08:00: a 37 h. Ni se puja ni se crea escritor.
            s, log = vuelta(madrid(15, 8), ivan_dentro=False, parte_de_ivan="ok")
            assert log is None and s["motivo"] == "NADA_QUE_HACER", (s, log)
            assert [a["guardia"] for a in s["acciones"]] == ["EL_RELOJ"], s

            # Miercoles 14/10: Ivan ya es nuestro pero en duda. Jutgla se queda.
            s, log = vuelta(madrid(14, 8), ivan_dentro=True, parte_de_ivan="doubt")
            assert log is None and s["motivo"] == "NADA_QUE_HACER", (s, log)
            assert [a["guardia"] for a in s["acciones"]] == ["EL_PARTE_DEL_RELEVO"], s

            # Sano: se cobra la oferta por Jutgla.
            s, log = vuelta(madrid(14, 8), ivan_dentro=True, parte_de_ivan="ok")
            assert log == [("accept", 81)], (s, log)

            # Sabado 17/10, con la J9 jugandose: no se cobra.
            s, log = vuelta(madrid(17, 12), ivan_dentro=True, parte_de_ivan="ok")
            assert log is None and s["reloj"]["en_curso"] is True, (s, log)
            assert [a["guardia"] for a in s["acciones"]] == ["JORNADA_EN_CURSO"], s

            # Martes 20/10 08:00, acabada la J9: se cobra.
            s, log = vuelta(madrid(20, 8), ivan_dentro=True, parte_de_ivan="ok")
            assert log == [("accept", 81)], (s, log)

            # Sin calendario: ni se puja ni se cobra.
            s, log = vuelta(madrid(13, 8), cal=Path(tmp) / "no_existe.json",
                            ivan_dentro=False, parte_de_ivan="ok")
            assert log is None and s["reloj"] == {"horas_jornada": None,
                                                  "en_curso": True}, (s, log)
        finally:
            if antes is None:
                os.environ.pop(orden_mod.ENV, None)
            else:
                os.environ[orden_mod.ENV] = antes


def test_el_reloj_y_el_parte_nunca_lanzan() -> None:
    r = orden_mod.el_reloj(AHORA, "/no/existe/calendario.json")
    assert r == {"horas_jornada": None, "en_curso": True}, r
    assert orden_mod.leer_los_estados(None) == {}
    assert orden_mod.leer_los_estados({"catalog": {"data": {"players": []}}}) == {}
    assert orden_mod.leer_los_estados({"catalog": "roto"}) == {}
    f = {"catalog": {"data": {"players": {str(IVAN): {"status": "doubt"}, "x": {}}}}}
    assert orden_mod.leer_los_estados(f) == {IVAN: "doubt"}


TESTS = [
    test_el_reloj_no_deja_fichar_tarde,
    test_el_relevo_tiene_que_estar_sano,
    test_no_se_cobra_con_la_jornada_jugandose,
    test_correr_pasa_las_guardias,
    test_el_reloj_y_el_parte_nunca_lanzan,
    test_varios_cambios_cada_uno_con_su_relevo,
    test_la_llave_de_yamal,
    test_los_viajes_cortos,
    test_se_vende_solo_con_el_relevo_dentro,
    test_subir_la_puja,
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
