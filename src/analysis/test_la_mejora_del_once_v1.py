"""
LA MEJORA DEL ONCE (12/10/2026). Guardias de
`src/actions/la_mejora_del_once.py`.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.la_mejora_del_once import (     # noqa: E402
    correr, decidir, la_caja,
)


# Nuestro once (posición 3 = medio, 4 = delantero) y la liga.
ONCE = [
    {"id": 10, "name": "Flojo", "position": 4, "starter_probability": 60, "price": 2_700_000},
    {"id": 11, "name": "Caro", "position": 3, "starter_probability": 80, "price": 4_900_000},
    {"id": 12, "name": "Yamal", "position": 4, "starter_probability": 90, "price": 25_000_000},
    {"id": 13, "name": "Protegido", "position": 3, "starter_probability": 50, "price": 1_000_000},
]
LIGA = {
    10: {"tasa": 3.75, "price": 2_700_000, "de_quien": "nuestro", "position": 4},
    11: {"tasa": 4.5, "price": 4_900_000, "de_quien": "nuestro", "position": 3},
    12: {"tasa": 11.0, "price": 25_000_000, "de_quien": "nuestro", "position": 4},
    13: {"tasa": 1.0, "price": 1_000_000, "de_quien": "nuestro", "position": 3},
    20: {"tasa": 5.7, "status": "ok", "price": 3_700_000, "de_quien": "computer", "position": 4},
    21: {"tasa": 3.8, "status": "ok", "price": 1_100_000, "de_quien": "computer", "position": 3},
    22: {"tasa": 9.0, "status": "injured", "price": 1_000_000, "de_quien": "computer", "position": 4},
    23: {"tasa": 9.0, "status": "ok", "price": 1_000_000, "de_quien": "computer", "position": 4},
}


def _c(pid, prob=70, jugados=6):
    l = LIGA[pid]
    return {"id": pid, "name": f"c{pid}", "position": l["position"], "price": l["price"],
            "points": int(l["tasa"] * jugados), "played": jugados, "starter_probability": prob}


def _foto(**k):
    f = {"plantilla": {10, 11, 12, 13}, "nuestras_pujas": {}, "ofertas_del_computer": {},
         "en_venta": set(), "saldo": 500_000, "maximo_de_puja": 14_000_000, "mercado": {}}
    f.update(k)
    return f


def _d(**k):
    base = dict(once=ONCE, liga=LIGA, escaparate=[_c(20)], foto=_foto(), libro={},
                intocables={"yamal"}, protegidos={13}, caja=500_000, horas_jornada=100)
    base.update(k)
    return decidir(**base)


def _pujas(d):
    return [(a["player_id"], a.get("sale")) for a in d["acciones"] if a["accion"] == "PUJAR"]


def test_mejora_con_deuda_y_sin_tocar_intocables():
    # 20 por Flojo: 5,7x0,7 = 3,99 contra 3,75x0,6 = 2,25 (+1,74). Caja:
    # 500.000 + 2.565.000 - 3.737.000 = -672.000: vale, con deuda (>= -1 M
    # a más de 64 h). Yamal no sale nunca aunque sea de su posición.
    d = _d()
    assert _pujas(d) == [(20, 10)], d
    assert d["plan"]["caja_despues"] == 500_000 + int(2_700_000 * 0.95) - 3_737_000
    # A menos de 64 h, sin deuda: ya no llega.
    assert _pujas(_d(horas_jornada=50)) == []
    # Lesionados fuera; y si el bueno es más barato, gana el bueno.
    d = _d(escaparate=[_c(20), _c(22), _c(23)])
    assert _pujas(d) == [(23, 10)], d


def test_cambia_caro_por_barato_para_fichar_mejor():
    # Sin caja para 20, pero 21 por Caro da 3,5 M y pierde 0,94: la
    # combinación suma +0,80 y deja la caja en positivo.
    d = _d(escaparate=[_c(20), _c(21)], caja=-1_500_000)
    assert sorted(_pujas(d)) == [(20, 10), (21, 11)], d
    # Pero no se vende caro por barato por gusto.
    assert _pujas(_d(escaparate=[_c(21)])) == []


def test_en_rojo_vende_caro_y_ficha_barato_desde_las_88_horas():
    k = dict(escaparate=[_c(21)], caja=-3_000_000)
    assert _pujas(_d(**k, horas_jornada=100)) == []        # puede entrar el premio
    d = _d(**k, horas_jornada=80)
    assert _pujas(d) == [(21, 11)] and d["plan"]["deficit"], d
    # Ni el Protegido (13) ni Yamal salen nunca para cuadrar la caja.
    assert all(a.get("sale") not in (12, 13) for a in d["acciones"])


def test_solo_en_su_hora():
    assert _pujas(_d(puede_escribir=False)) == []
    assert _pujas(_d(horas_jornada=39)) == []
    assert _pujas(_d(horas_jornada=None)) == []
    assert _pujas(_d(ya_pujados={20})) == []                # ya pujado esta vuelta
    assert _pujas(_d(pendientes={20})) == []                # lo ficha la orden
    assert _pujas(_d(foto=_foto(nuestras_pujas={20: {"offer_id": 1, "amount": 1}}))) == []
    # Se puja lo que PIDE el Computer + 1 %, no su valor.
    d = _d(foto=_foto(mercado={20: 3_500_000}))
    assert [a["importe"] for a in d["acciones"]] == [3_535_000]
    # Y si no está en el mercado de la foto, no.
    assert _pujas(_d(foto=_foto(mercado={99: 1}))) == []


def test_el_que_sale_solo_se_vende_con_el_relevo_dentro():
    libro = {"20": {"sale": 10, "suelo": 2_430_000}}
    ofertas = {10: {"offer_id": 7, "amount": 2_500_000}}
    # Relevo con puja viva: no se vende, y el que sale no se cambia por otro.
    d = _d(libro=libro, foto=_foto(nuestras_pujas={20: {"offer_id": 1, "amount": 1}},
                                   ofertas_del_computer=ofertas), escaparate=[_c(23)])
    assert [a["accion"] for a in d["acciones"]] == [] and d["soltar"] == []
    # Relevo dentro: se acepta desde el suelo; por debajo, se publica.
    f = _foto(plantilla={10, 11, 12, 13, 20}, ofertas_del_computer=ofertas)
    d = _d(libro=libro, foto=f, escaparate=[])
    assert [(a["accion"], a["player_id"]) for a in d["acciones"]] == [("ACEPTAR_OFERTA_DEL_COMPUTER", 10)]
    f = _foto(plantilla={10, 11, 12, 13, 20},
              ofertas_del_computer={10: {"offer_id": 7, "amount": 2_000_000}})
    d = _d(libro=libro, foto=f, escaparate=[])
    assert [(a["accion"], a["player_id"]) for a in d["acciones"]] == [("PONER_A_LA_VENTA", 10)]
    # A menos de 20 h y en rojo, la que haya.
    d = _d(libro=libro, foto={**f, "saldo": -1, "en_venta": {10}}, escaparate=[], horas_jornada=10)
    assert [a["accion"] for a in d["acciones"]] == ["ACEPTAR_OFERTA_DEL_COMPUTER"]
    # Con la jornada jugándose, no se vende a nadie.
    d = _d(libro=libro, foto=_foto(plantilla={10, 11, 12, 13, 20}, ofertas_del_computer=ofertas),
           escaparate=[], en_curso=True)
    assert d["acciones"] == []
    # Puja perdida: el que iba a salir se queda.
    assert _d(libro=libro, escaparate=[])["soltar"] == ["20"]


def test_se_queda_lo_que_compro_la_ronda_si_mejora_el_once():
    f = _foto(plantilla={10, 11, 12, 13, 23})
    once = ONCE + [{"id": 23, "name": "c23", "position": 4, "starter_probability": 70}]
    d = _d(foto=f, once=once, escaparate=[], inventario={23})
    assert [(c["entra"], c["sale"]) for c in d["adoptar"]] == [(23, 10)], d
    assert _pujas(d) == []


def test_la_caja():
    f = _foto(saldo=1_000_000, nuestras_pujas={1: {"amount": 3_000_000}, 2: {"amount": 1_000_000}})
    assert la_caja(f) == -3_000_000
    # La de la ronda se revende sola: solo cuenta lo que se puede perder.
    assert la_caja(f, se_venden_solos={2}, ventas_pendientes=500_000) == -1_570_000


def test_nace_apagada_y_nunca_lanza():
    os.environ.pop("BORDALAS_LA_MEJORA_DEL_ONCE", None)
    assert correr(status={}, snapshot={}, v10={})["motivo"] == "APAGADA"
    os.environ["BORDALAS_LA_MEJORA_DEL_ONCE"] = "1"
    try:
        r = correr(status={"lineup": None}, snapshot={"market": None}, v10={},
                   libro_ruta=os.devnull + ".no")
        assert r["motivo"] in {"NADA_QUE_HACER"} or r["motivo"].startswith("ERROR"), r
    finally:
        os.environ.pop("BORDALAS_LA_MEJORA_DEL_ONCE", None)


TESTS = [test_mejora_con_deuda_y_sin_tocar_intocables,
         test_cambia_caro_por_barato_para_fichar_mejor,
         test_en_rojo_vende_caro_y_ficha_barato_desde_las_88_horas,
         test_solo_en_su_hora, test_el_que_sale_solo_se_vende_con_el_relevo_dentro,
         test_se_queda_lo_que_compro_la_ronda_si_mejora_el_once, test_la_caja,
         test_nace_apagada_y_nunca_lanza]


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
