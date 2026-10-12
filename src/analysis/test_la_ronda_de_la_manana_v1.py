"""
LA RONDA DE LA MAÑANA (12/10/2026). Guardias de
`src/actions/la_ronda_de_la_manana.py`.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.la_ronda_de_la_manana import (     # noqa: E402
    correr, decidir, la_puja,
)


def _f(precio=1_000_000, sube=20_000, estado="ok", puntos=30, partidos=6):
    return {"price": precio, "priceIncrement": sube, "status": estado,
            "points": puntos, "playedHome": partidos // 2,
            "playedAway": partidos - partidos // 2}


def _d(**k):
    base = dict(
        mercado={}, fichas={}, nuestras_pujas={}, plantilla=set(),
        ofertas_del_computer={}, en_venta=set(), maximo_de_puja=20_000_000,
        minutos_al_reset=127, horas_jornada=100, libro={},
    )
    base.update(k)
    return decidir(**base)


def _pujas(a):
    return [(x["player_id"], x["importe"]) for x in a if x["accion"] == "PUJAR"]


def test_solo_puja_por_quien_sube_esta_bien_y_juega():
    a = _d(mercado={1: 1_000_000, 2: 1_000_000, 3: 1_000_000, 4: 1_000_000,
                    5: 1_000_000, 6: 2_000_000},
           fichas={1: _f(), 2: _f(sube=0), 3: _f(estado="doubt"),
                   4: _f(partidos=2, puntos=20), 5: _f(puntos=12),
                   6: _f(precio=2_000_000, sube=100_000)})
    # 6 sube un 5 %, 1 un 2 %: primero 6. Puja = precio + 1 % a miles.
    assert _pujas(a) == [(6, 2_020_000), (1, 1_010_000)]
    assert la_puja(1_234_567) == 1_247_000
    # Sin ficha (sin noticias), no.
    assert _d(mercado={9: 1_000_000}) == []


def test_nunca_pasa_de_los_topes():
    f = {i: _f(precio=2_500_000, sube=10_000 + i) for i in range(1, 6)}
    m = {i: 2_500_000 for i in range(1, 6)}
    # Más de 3 M por jugador: nada.
    assert _d(mercado={7: 3_000_000}, fichas={7: _f(precio=3_000_000)}) == []
    # Toda la deuda (el dueño, 12/10): con 20 M de puja caben los cinco.
    assert len(_pujas(_d(mercado=m, fichas=f))) == 5
    # Con 8 M de puja (7 M usables): caben dos de 2,525 M.
    assert len(_pujas(_d(mercado=m, fichas=f, maximo_de_puja=8_000_000))) == 2
    # `maximumBid` - 1 M de reserva: con 3,6 M de puja, solo uno.
    assert len(_pujas(_d(mercado=m, fichas=f, maximo_de_puja=3_600_000))) == 1
    for a in _d(mercado=m, fichas=f):
        assert a["importe"] <= 3_000_000


def test_solo_en_la_ultima_vuelta_y_lejos_de_la_jornada():
    # En CADA vuelta (el dueño, 12/10), salvo zona de silencio y jornada cerca.
    k = dict(mercado={1: 1_000_000}, fichas={1: _f()})
    assert _d(**k)
    assert _d(**k, minutos_al_reset=600)                  # media tarde
    assert _d(**k, minutos_al_reset=None)
    assert _d(**k, puede_escribir=False) == []            # zona de silencio
    assert _d(**k, horas_jornada=39) == []                # menos de 40 h
    assert _d(**k, horas_jornada=None) == []              # sin calendario
    assert _d(**k, horas_jornada=40)


def _salida(**k):
    base = dict(plantilla={1}, libro={"1": 1_000_000}, minutos_al_reset=500,
                fichas={1: _f(precio=1_050_000)})
    base.update(k)
    return _d(**base)


def _oferta(importe):
    return {1: {"offer_id": 7, "amount": importe}}


def test_vende_con_beneficio_o_lo_publica():
    a = _salida(ofertas_del_computer=_oferta(1_010_000))
    assert a[0]["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"
    a = _salida(ofertas_del_computer=_oferta(1_009_999))
    assert a == [{"accion": "PONER_A_LA_VENTA", "player_id": 1,
                  "precio": 1_050_000, "ronda": True}]
    # Ya publicado y sin oferta buena: nada.
    assert _salida(en_venta={1}, ofertas_del_computer=_oferta(1_000_000)) == []


def test_el_primer_dia_que_baja_y_la_liquidacion():
    baja = {1: _f(precio=990_000, sube=-5_000)}
    assert _salida(fichas=baja, ofertas_del_computer=_oferta(980_000))[0][
        "accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"
    assert _salida(fichas=baja, en_venta={1},
                   ofertas_del_computer=_oferta(979_999)) == []
    # A menos de 36 h: hasta un 7 % por debajo.
    assert _salida(horas_jornada=35, ofertas_del_computer=_oferta(930_000))[0][
        "accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"
    assert _salida(horas_jornada=35, en_venta={1},
                   ofertas_del_computer=_oferta(929_999)) == []
    # A menos de 20 h: lo que ofrezca.
    assert _salida(horas_jornada=19, ofertas_del_computer=_oferta(500_000))[0][
        "accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"


def test_no_toca_protegidos_ni_a_quien_no_compro():
    f = {1: _f(), 2: _f()}
    o = {1: {"offer_id": 7, "amount": 9_000_000}, 2: {"offer_id": 8, "amount": 9_000_000}}
    # 2 es nuestro pero no es de la ronda: ni se vende ni se publica.
    a = _d(plantilla={1, 2}, libro={"1": 1_000_000}, fichas=f,
           ofertas_del_computer=o, minutos_al_reset=500)
    assert [x["player_id"] for x in a] == [1]
    # Protegido por el gestor: ni se vende ni se puja por él.
    assert _d(plantilla={1}, libro={"1": 1_000_000}, fichas=f,
              ofertas_del_computer=o, protegidos={1}, minutos_al_reset=500) == []
    assert _d(mercado={2: 1_000_000}, fichas=f, protegidos={2}) == []
    # Ni a rivales (no están en `mercado`) ni a quien ya pujamos.
    assert _d(mercado={2: 1_000_000}, fichas=f,
              nuestras_pujas={2: {"offer_id": 1, "amount": 1_010_000}}) == []


def test_nace_apagada_y_nunca_lanza():
    os.environ.pop("BORDALAS_LA_RONDA_DE_LA_MANANA", None)
    assert correr({}, 10)["motivo"] == "APAGADA"
    os.environ["BORDALAS_LA_RONDA_DE_LA_MANANA"] = "1"
    try:
        for cycle in ({"snapshot": None}, None, {"snapshot": {"catalog": 7}}):
            r = correr(cycle, 10)
            assert r["motivo"] in {"NADA_QUE_HACER"} or r["motivo"].startswith("ERROR")
        assert decidir(mercado={1: 0}, fichas={1: {"status": "ok", "priceIncrement": "x"}},
                       nuestras_pujas={}, plantilla=set(), ofertas_del_computer={},
                       en_venta=set(), maximo_de_puja=None, minutos_al_reset=127,
                       horas_jornada=100, libro={"x": "y"}) == []
    finally:
        os.environ.pop("BORDALAS_LA_RONDA_DE_LA_MANANA", None)


TESTS = [test_solo_puja_por_quien_sube_esta_bien_y_juega, test_nunca_pasa_de_los_topes,
         test_solo_en_la_ultima_vuelta_y_lejos_de_la_jornada,
         test_vende_con_beneficio_o_lo_publica, test_el_primer_dia_que_baja_y_la_liquidacion,
         test_no_toca_protegidos_ni_a_quien_no_compro, test_nace_apagada_y_nunca_lanza]


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
