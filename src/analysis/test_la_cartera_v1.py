"""
LA CARTERA (16/10/2026). Guardias de `BORDALAS_LA_CARTERA` en
`src/actions/la_ronda_de_la_manana.py`.

    1. Puja para ganar: precio + la prima de su tramo, terminada en 9.900.
    2. Aguanta lo que sube; el primer día que no sube, vende.
    3. Cerca de la jornada no compra (como siempre).
    4. Como mucho `MAXIMO_EN_PLANTILLA`; la prima no saca del tope.
    5. A los managers, lo que piden + 1 %; sin cartera, todo como antes.
    6. Nace apagada.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.la_ronda_de_la_manana as ronda      # noqa: E402

from src.actions.la_ronda_de_la_manana import (       # noqa: E402
    decidir, el_suelo_de_la_cartera, la_puja, la_puja_de_la_cartera,
)


def _f(precio=1_000_000, sube=40_000, estado="ok", puntos=30, partidos=6):
    return {"price": precio, "priceIncrement": sube, "status": estado,
            "points": puntos, "playedHome": partidos // 2,
            "playedAway": partidos - partidos // 2}


def _d(**k):
    base = dict(
        mercado={}, fichas={}, nuestras_pujas={}, plantilla=set(),
        ofertas_del_computer={}, en_venta=set(), maximo_de_puja=20_000_000,
        minutos_al_reset=127, horas_jornada=100, libro={}, cartera=True,
        saldo=5_000_000,
    )
    base.update(k)
    return decidir(**base)


def _por(a, accion):
    return {x["player_id"]: x for x in a if x["accion"] == accion}


def test_puja_para_ganar_terminada_en_9000():
    # Por debajo de 1 M, +12 %; de 1 a 3 M, +4 %; por encima, +1 %.
    assert la_puja_de_la_cartera(900_000, 40_000) == 1_009_900
    assert la_puja_de_la_cartera(2_000_000, 80_000) == 2_089_900
    assert la_puja_de_la_cartera(4_690_000, 10_000) == 4_739_900
    # La subida del día no cambia la prima.
    assert la_puja_de_la_cartera(2_000_000, 10_000) == 2_089_900
    # Termina en 9.900 y nunca por debajo de precio + 1 %.
    for precio, sube in ((1_234_567, 20_000), (450_000, 40_000), (9_870_000, 50_000)):
        p = la_puja_de_la_cartera(precio, sube)
        assert p % 10_000 == 9_900 and p >= la_puja(precio), (precio, sube, p)
    # Con basura, la de siempre.
    assert la_puja_de_la_cartera("x", None) == la_puja(0)
    assert la_puja_de_la_cartera(1_000_000, "x") == la_puja_de_la_cartera(1_000_000, 0)


def test_el_suelo_de_la_cartera():
    assert el_suelo_de_la_cartera(1_000_000, 10_000, 1_200_000) is None
    # El primer día que no sube (0 o baja): desde el 97 % de su valor.
    assert el_suelo_de_la_cartera(1_000_000, 0, 1_200_000) == 1_164_000
    assert el_suelo_de_la_cartera(1_000_000, -10_000, 1_200_000) == 1_164_000
    assert el_suelo_de_la_cartera(1_000_000, -10_000, 0) is None
    # Sin saber si sube (ni dato ni basura): se aguanta.
    assert el_suelo_de_la_cartera(1_000_000, None, 1_200_000) is None
    assert el_suelo_de_la_cartera("x", "y", "z") is None


def test_aguanta_lo_que_sube_y_vende_lo_que_se_para_o_baja():
    fichas = {1: _f(1_300_000, sube=40_000), 2: _f(1_300_000, sube=0),
              3: _f(900_000, sube=-20_000), 4: _f(1_300_000, sube=0),
              5: _f(1_300_000, sube=30_000)}
    ofertas = {1: {"offer_id": 11, "amount": 1_500_000},
               2: {"offer_id": 12, "amount": 1_300_000},
               3: {"offer_id": 13, "amount": 880_000},
               4: {"offer_id": 14, "amount": 1_000_000}}
    a = _d(libro={"1": 1_000_000, "2": 1_000_000, "3": 1_000_000, "4": 1_100_000, "5": 1_000_000},
           plantilla={1, 2, 3, 4, 5}, fichas=fichas, ofertas_del_computer=ofertas,
           en_venta={1, 2, 3, 4})
    cobra = _por(a, "ACEPTAR_OFERTA_DEL_COMPUTER")
    # 1 sube: se aguanta aunque la oferta deje +50 %.
    assert 1 not in cobra, a
    # 2 se para y le ofrecen su valor: se vende; a 4 le ofrecen el 77 %: no.
    assert 2 in cobra and 4 not in cobra, a
    # 3 baja: se vende desde el 97 % de su valor (873.000), aunque pierda.
    assert 3 in cobra and cobra[3]["suelo"] == 873_000, a
    # 5 sube y no está publicado: se publica (para tener la oferta).
    assert _por(a, "PONER_A_LA_VENTA").get(5), a
    # Con la jornada en curso no se cobra nada.
    a = _d(libro={"2": 1_000_000}, plantilla={2}, fichas=fichas,
           ofertas_del_computer=ofertas, en_venta={2}, en_curso=True)
    assert not _por(a, "ACEPTAR_OFERTA_DEL_COMPUTER"), a
    # Sin cartera, la de siempre: el que sube se cobra con beneficio.
    a = _d(libro={"1": 1_000_000}, plantilla={1}, fichas=fichas,
           ofertas_del_computer=ofertas, en_venta={1}, cartera=False)
    assert 1 in _por(a, "ACEPTAR_OFERTA_DEL_COMPUTER"), a


def test_cerca_de_la_jornada_no_compra_y_lejos_si_con_deuda():
    mercado = {1: 1_000_000, 2: 1_000_000, 3: 1_000_000}
    fichas = {1: _f(1_000_000, sube=50_000), 2: _f(1_000_000, sube=45_000),
              3: _f(1_000_000, sube=40_000)}
    # A 30 h, ni con cartera ni sin ella.
    assert not _por(_d(mercado=mercado, fichas=fichas, horas_jornada=30), "PUJAR")
    assert not _por(_d(mercado=mercado, fichas=fichas, horas_jornada=30, cartera=False), "PUJAR")
    # Lejos de la jornada, con deuda (maximumBid manda): los tres.
    a = _d(mercado=mercado, fichas=fichas, horas_jornada=100, maximo_de_puja=5_000_000)
    assert sorted(_por(a, "PUJAR")) == [1, 2, 3], a


def test_el_tope_de_la_cartera():
    # 2,9 M: a + 4 % (3.019.900) se pasaria de 3 M; cabe a + 1 % (2.929.000),
    # asi que se puja el tope.
    a = _por(_d(mercado={1: 2_900_000}, fichas={1: _f(2_900_000, sube=40_000)}), "PUJAR")
    assert a[1]["importe"] == ronda.TOPE_POR_VIAJE, a
    # 4,69 M: ni con la cartera ni sin ella (pasa del tope de 3 M).
    for cartera in (True, False):
        assert not _por(_d(mercado={1: 4_690_000}, fichas={1: _f(4_690_000, sube=30_000)},
                           cartera=cartera), "PUJAR")


def test_el_colchon():
    mercado = {1: 1_000_000, 2: 1_000_000, 3: 1_000_000}
    fichas = {p: _f(1_000_000, sube=40_000) for p in mercado}
    # Saldo 300.000, sin pujas: cada una (1.049.900) cuesta de colchón
    # 1.049.900 - 0,92 x 1.000.000 = 129.900; caben dos.
    a = _d(mercado=mercado, fichas=fichas, saldo=300_000)
    assert len(_por(a, "PUJAR")) == 2, a
    # Hoy (16/10): saldo 486.683; vivas Cardona 919.000 (de otro) y
    # Freeman 2.012.000 (de la ronda, vale 2.000.000): colchón -604.317.
    fichas[9] = _f(2_000_000, sube=80_000)
    a = _d(mercado=mercado, fichas=fichas, saldo=486_683, libro={"9": 2_012_000},
           nuestras_pujas={9: {"offer_id": 1, "amount": 2_012_000},
                           8: {"offer_id": 2, "amount": 919_000}})
    assert not _por(a, "PUJAR"), a
    # Lo que la ronda ya tiene cuenta al 92 %: con Freeman dentro y sin
    # pujas, el colchón es 486.683 + 1.840.000.
    a = _d(mercado=mercado, fichas=fichas, saldo=486_683 - 2_012_000, libro={"9": 2_012_000},
           plantilla={9})
    assert len(_por(a, "PUJAR")) == 2, a
    # Sin saldo, la cartera no compra.
    assert not _por(_d(mercado=mercado, fichas=fichas, saldo=None), "PUJAR")


def test_la_prima_solo_lejos_de_la_jornada():
    mercado = {1: 1_000_000}
    fichas = {1: _f(1_000_000, sube=40_000)}
    assert _por(_d(mercado=mercado, fichas=fichas, horas_jornada=70), "PUJAR")[1]["importe"] == 1_049_900
    assert _por(_d(mercado=mercado, fichas=fichas, horas_jornada=50), "PUJAR")[1]["importe"] == la_puja(1_000_000)


def test_como_mucho_veinte():
    mercado = {1: 1_000_000, 2: 1_000_000, 3: 1_000_000}
    fichas = {p: _f(1_000_000, sube=40_000) for p in mercado}
    plantilla = set(range(100, 118))                       # 18
    a = _d(mercado=mercado, fichas=fichas, plantilla=plantilla,
           nuestras_pujas={200: {"offer_id": 1, "amount": 1}})
    assert len(_por(a, "PUJAR")) == ronda.MAXIMO_EN_PLANTILLA - 19, a
    a = _d(mercado=mercado, fichas=fichas, plantilla=set(range(100, 120)))
    assert not _por(a, "PUJAR"), a


def test_a_los_managers_lo_que_piden_y_sin_cartera_como_antes():
    mercado = {1: 1_000_000, 2: 1_000_000}
    fichas = {1: _f(1_000_000, sube=40_000), 2: _f(1_000_000, sube=40_000)}
    a = _por(_d(mercado=mercado, fichas=fichas, de_managers=frozenset({2})), "PUJAR")
    assert a[1]["importe"] == la_puja_de_la_cartera(1_000_000, 40_000), a
    assert a[2]["importe"] == la_puja(1_000_000), a
    a = _por(_d(mercado=mercado, fichas=fichas, cartera=False), "PUJAR")
    assert a[1]["importe"] == a[2]["importe"] == la_puja(1_000_000), a


def test_en_rojo_el_cierre_vende_lo_de_la_cartera_que_no_puede_adoptar():
    # El cierre en rojo (-4 M) con F3 (12), de la ronda, en su once y sin
    # estar en el once escrito: sin la cartera, «su libro lo sigue
    # vendiendo»; con ella nadie lo venderia, asi que el once se hace sin
    # el y pasa a candidato.
    import src.analysis.test_el_cierre_de_la_jornada_v1 as c
    escrito = (c.ONCE - {12}) | {11}
    d = c._d(inventario={12}, once_escrito=escrito)
    assert 12 in d["once"]["ids"] and 12 not in [x["id"] for x in d["candidatos"]], d
    d = c._d(inventario={12}, once_escrito=escrito, cartera=True)
    assert 12 not in d["once"]["ids"] and d["once"].get("sin_la_cartera"), d["once"]
    assert 12 in [x["id"] for x in d["candidatos"]], d["candidatos"]
    # FALTA aunque se venda todo el banquillo, con F3 (12) de la cartera
    # alineado en el once escrito: sin la cartera nadie lo vende; con ella,
    # es el ultimo recurso.
    rojo = dict(saldo=0, pujas={500: {"offer_id": 9, "amount": 20_000_000}},
                inventario={12}, once_escrito=c.ONCE)
    d = c._d(**rojo)
    assert d["motivo"] == "FALTA" and 12 not in d["vender"], d
    d = c._d(cartera=True, **rojo)
    assert d.get("ultimo_recurso") == [12] and 12 in d["vender"], d
    assert 12 not in d["titulares_que_no_se_venden"], d
    # En positivo, con la cartera, se adopta como siempre.
    d = c._d(saldo=10_000_000, inventario={12}, once_escrito=c.ONCE, cartera=True)
    assert d["adoptar"] == [12] and not d["once"].get("sin_la_cartera"), d


def test_la_mejora_cuenta_entera_la_puja_de_la_cartera():
    from src.actions.la_mejora_del_once import lo_de_esta_vuelta
    v10 = {"ronda": {"hechas": [{"accion": "PUJAR", "player_id": 7, "importe": 1_009_900,
                                 "exito": True}]},
           "chollos": {"hechas": [{"accion": "PUJAR", "player_id": 8, "importe": 500_000,
                                   "exito": True}]}}
    assert lo_de_esta_vuelta(v10)["solas"] == {7, 8}
    assert lo_de_esta_vuelta(v10, cartera=True)["solas"] == {8}
    assert lo_de_esta_vuelta(v10, cartera=True)["pujas"] == {7: 1_009_900, 8: 500_000}


def test_el_motor_viejo_no_vende_lo_que_aguanta():
    import json
    import tempfile
    viejo = os.environ.pop(ronda.ENV_CARTERA, None)
    try:
        with tempfile.TemporaryDirectory() as d:
            libro = Path(d) / "la_ronda.json"
            libro.write_text(json.dumps({"123": 1_009_900, "x": 5}))
            assert ronda.los_que_aguanta(libro) == set()
            os.environ[ronda.ENV_CARTERA] = "1"
            assert ronda.los_que_aguanta(libro) == {123}
            assert ronda.los_que_aguanta(Path(d) / "no_existe.json") == set()
        # Las dos puertas del motor viejo que aceptan ofertas lo miran (y,
        # desde el 17/10, tambien a los que rota la rotacion).
        texto = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text()
        assert texto.count("_conservados() | _aguanta()") == 2
        assert texto.count("_conservados() | _aguanta() | _rota()") == 2
    finally:
        os.environ.pop(ronda.ENV_CARTERA, None)
        if viejo is not None:
            os.environ[ronda.ENV_CARTERA] = viejo


def test_nace_apagada():
    viejo = os.environ.pop(ronda.ENV_CARTERA, None)
    try:
        assert ronda.la_cartera_activa() is False
        os.environ[ronda.ENV_CARTERA] = "1"
        assert ronda.la_cartera_activa() is True
    finally:
        os.environ.pop(ronda.ENV_CARTERA, None)
        if viejo is not None:
            os.environ[ronda.ENV_CARTERA] = viejo


TESTS = [
    test_puja_para_ganar_terminada_en_9000,
    test_el_suelo_de_la_cartera,
    test_aguanta_lo_que_sube_y_vende_lo_que_se_para_o_baja,
    test_cerca_de_la_jornada_no_compra_y_lejos_si_con_deuda,
    test_el_tope_de_la_cartera,
    test_el_colchon,
    test_la_prima_solo_lejos_de_la_jornada,
    test_como_mucho_veinte,
    test_a_los_managers_lo_que_piden_y_sin_cartera_como_antes,
    test_en_rojo_el_cierre_vende_lo_de_la_cartera_que_no_puede_adoptar,
    test_la_mejora_cuenta_entera_la_puja_de_la_cartera,
    test_el_motor_viejo_no_vende_lo_que_aguanta,
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
