"""
LA CARTERA (16/10/2026). Guardias de `BORDALAS_LA_CARTERA` en
`src/actions/la_ronda_de_la_manana.py`.

    1. Puja para ganar: precio + la prima de su subida, terminada en 9.000.
    2. Aguanta lo que sube; vende lo que se para (con beneficio) o baja.
    3. Cerca de la jornada, solo lo que paga la caja.
    4. Como mucho `MAXIMO_EN_PLANTILLA`.
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
        saldo=500_000,
    )
    base.update(k)
    return decidir(**base)


def _por(a, accion):
    return {x["player_id"]: x for x in a if x["accion"] == accion}


def test_puja_para_ganar_terminada_en_9000():
    # +4 % al día: +12 %.
    assert la_puja_de_la_cartera(2_000_000, 80_000) == 2_249_000
    # +2 a 4 %: +9 %; +1 a 2 %: +6 %; menos de +1 %: +3 %.
    assert la_puja_de_la_cartera(2_000_000, 50_000) == 2_189_000
    assert la_puja_de_la_cartera(2_000_000, 30_000) == 2_129_000
    assert la_puja_de_la_cartera(2_000_000, 10_000) == 2_069_000
    # Termina en 9.000 y nunca por debajo de precio + 1 %.
    for precio, sube in ((1_234_567, 20_000), (450_000, 40_000), (9_870_000, 50_000)):
        p = la_puja_de_la_cartera(precio, sube)
        assert p % 10_000 == 9_000 and p >= la_puja(precio), (precio, sube, p)
    # Con basura, la de siempre.
    assert la_puja_de_la_cartera("x", None) == la_puja(0)
    assert la_puja_de_la_cartera(1_000_000, "x") == la_puja_de_la_cartera(1_000_000, 0)


def test_el_suelo_de_la_cartera():
    assert el_suelo_de_la_cartera(1_000_000, 10_000, 1_200_000) is None
    assert el_suelo_de_la_cartera(1_000_000, 0, 1_200_000) == 1_010_000
    assert el_suelo_de_la_cartera(1_000_000, -10_000, 1_200_000) == 1_164_000
    assert el_suelo_de_la_cartera(1_000_000, -10_000, 0) is None
    assert el_suelo_de_la_cartera("x", "y", "z") is None or True   # nunca lanza


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
    # 2 se para con beneficio: se vende; 4 se para sin beneficio: se aguanta.
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


def test_cerca_de_la_jornada_solo_con_caja():
    mercado = {1: 1_000_000, 2: 1_000_000, 3: 1_000_000}
    fichas = {1: _f(1_000_000, sube=50_000), 2: _f(1_000_000, sube=45_000),
              3: _f(1_000_000, sube=40_000)}
    vivas = {9: {"offer_id": 99, "amount": 400_000}}
    # A 30 h, saldo 2.700.000 - 400.000 vivas = 2.300.000: caben dos de
    # 1.129.000 (precio + 12 %) y el tercero ya no.
    a = _d(mercado=mercado, fichas=fichas, nuestras_pujas=vivas, horas_jornada=30,
           saldo=2_700_000)
    assert sorted(_por(a, "PUJAR")) == [1, 2], a
    # Sin caja, nada.
    a = _d(mercado=mercado, fichas=fichas, nuestras_pujas=vivas, horas_jornada=30,
           saldo=300_000)
    assert not _por(a, "PUJAR"), a
    # Sin cartera, a menos de 40 h nada, como siempre.
    a = _d(mercado=mercado, fichas=fichas, horas_jornada=30, saldo=9_000_000, cartera=False)
    assert not _por(a, "PUJAR"), a
    # Lejos de la jornada, con deuda: los tres.
    a = _d(mercado=mercado, fichas=fichas, horas_jornada=100, saldo=-3_000_000)
    assert sorted(_por(a, "PUJAR")) == [1, 2, 3], a


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
    test_cerca_de_la_jornada_solo_con_caja,
    test_como_mucho_veinte,
    test_a_los_managers_lo_que_piden_y_sin_cartera_como_antes,
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
