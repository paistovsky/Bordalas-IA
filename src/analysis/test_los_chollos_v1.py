"""
LOS CHOLLOS DEL PRECIO FIJO (02/10/2026). Guardias de
`src/actions/los_chollos.py`.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.actions.los_chollos import correr, decidir, la_puja     # noqa: E402


def _d(**k):
    base = dict(
        mercado={}, valores={}, estados={}, nuestras_pujas={}, plantilla=set(),
        ofertas_del_computer={}, en_venta=set(), maximo_de_puja=10_000_000,
        saldo=5_000_000, minutos_al_reset=50, horas_jornada=200, libro={},
    )
    base.update(k)
    return decidir(**base)


def test_la_puja_nunca_pasa_del_valor():
    assert la_puja(890_000, 900_000) == 899_000          # caso Moi
    assert la_puja(890_000, 891_000) == 890_500          # hueco pequeño: a mitad
    assert la_puja(900_000, 900_000) is None             # sin hueco, nada
    assert la_puja(900_000, 890_000) is None             # pide más de lo que vale
    for pide, vale in ((1, 3), (100, 5_000), (1_000_000, 1_000_002)):
        p = la_puja(pide, vale)
        assert p is None or pide < p < vale


def test_puja_por_moi_y_no_por_los_demas():
    a = _d(mercado={1: 890_000, 2: 500_000, 3: 300_000, 4: 700_000},
           valores={1: 900_000, 2: 490_000, 3: 320_000, 4: 750_000},
           estados={3: "injured"}, plantilla={4})
    assert [(x["player_id"], x["importe"]) for x in a] == [(1, 899_000)]


def test_solo_en_la_ultima_vuelta():
    k = dict(mercado={1: 890_000}, valores={1: 900_000})
    assert _d(**k, minutos_al_reset=132) == []           # la de las 04:45
    assert _d(**k, minutos_al_reset=None) == []
    assert _d(**k, minutos_al_reset=0) == []
    assert _d(**k, minutos_al_reset=127)                  # la de las 04:50
    # Fuera de las vueltas puestas a proposito (zona de silencio), nada.
    assert _d(**k, minutos_al_reset=40, puede_escribir=False) == []


def test_cerca_de_la_jornada_solo_caja_propia():
    k = dict(mercado={1: 890_000}, valores={1: 900_000}, minutos_al_reset=40)
    # En rojo, con la jornada a 2 días: nada, aunque haya puja de sobra.
    assert _d(**k, saldo=-1, horas_jornada=48) == []
    # Lejos de la jornada, con deuda: sí (va con `maximumBid`).
    assert _d(**k, saldo=-1, horas_jornada=200)
    # Sin calendario se trata como cerca.
    assert _d(**k, saldo=-1, horas_jornada=None) == []
    # La caja descuenta nuestras pujas vivas (las normales van primero).
    assert _d(**k, saldo=1_000_000, horas_jornada=48,
              nuestras_pujas={9: {"offer_id": 1, "amount": 200_000}}) == []


def test_revende_en_cuanto_hay_beneficio():
    a = _d(plantilla={1}, libro={"1": 899_000},
           ofertas_del_computer={1: {"offer_id": 7, "amount": 899_001}},
           minutos_al_reset=500)
    assert a[0]["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER"
    a = _d(plantilla={1}, libro={"1": 899_000}, valores={1: 920_000},
           ofertas_del_computer={1: {"offer_id": 7, "amount": 899_000}},
           minutos_al_reset=500)
    assert a == [{"accion": "PONER_A_LA_VENTA", "player_id": 1,
                  "precio": 920_000, "chollo": True}]
    # Lo que no se compró como chollo no se toca.
    assert _d(plantilla={2}, valores={2: 1}, minutos_al_reset=500) == []


def test_nace_apagada_y_nunca_lanza():
    os.environ.pop("BORDALAS_LOS_CHOLLOS", None)
    assert correr({}, 10)["motivo"] == "APAGADA"
    os.environ["BORDALAS_LOS_CHOLLOS"] = "1"
    try:
        r = correr({"snapshot": None}, 10)
        assert r["motivo"] in {"NADA_QUE_HACER"} or r["motivo"].startswith("ERROR")
    finally:
        os.environ.pop("BORDALAS_LOS_CHOLLOS", None)


TESTS = [test_la_puja_nunca_pasa_del_valor, test_puja_por_moi_y_no_por_los_demas,
         test_solo_en_la_ultima_vuelta, test_cerca_de_la_jornada_solo_caja_propia,
         test_revende_en_cuanto_hay_beneficio, test_nace_apagada_y_nunca_lanza]


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
