"""
EL COMPARADOR DE CAMBIOS (30/09/2026). Guardias de
`src/analysis/el_comparador_de_cambios.py`.
"""

from __future__ import annotations

import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.el_comparador_de_cambios import comparar       # noqa: E402


def _f(id_, nombre, pos, precio, puntos, jugados, quien, **extra):
    return {"id": id_, "name": nombre, "position": pos, "price": precio,
            "points": puntos, "played": jugados, "de_quien": quien, **extra}


FILAS = [
    _f(1, "Jutglà", 4, 2_980_000, 14, 7, "nuestro"),
    _f(2, "Yamal", 4, 20_000_000, 40, 7, "nuestro"),
    _f(3, "Chust", 2, 3_000_000, 12, 7, "nuestro"),
    _f(10, "Akhomach", 4, 3_170_000, 23, 6, "computer"),
    _f(11, "Barato", 2, 900_000, 11, 6, "computer"),
    _f(12, "Lesionado", 4, 1_000_000, 40, 6, "computer", status="injured"),
    _f(13, "Nuevo", 4, 1_000_000, 10, 1, "computer"),
    _f(14, "Malo", 2, 2_000_000, 2, 6, "computer"),
    _f(15, "DeRival", 4, 1_000_000, 40, 7, "rival"),
]


def test_puntos_y_caja():
    r = comparar(FILAS, saldo=-1_214_616)
    assert r["ok"]
    por = {c["ficha"]: c for c in r["cambios"]}

    # Akhomach sube puntos contra Jutglà (3,83 vs 2,0) y cuesta 0,19 M.
    a = por["Akhomach"]
    assert a["vende"] == "Jutglà" and a["puntos"] > 0 and a["caja"] == -190_000
    assert not a["gana_las_dos"]

    # El barato por Chust: casi los mismos puntos y +2,1 M de caja.
    b = por["Barato"]
    assert b["vende"] == "Chust" and b["caja"] == 2_100_000
    assert b["saca_del_rojo"]

    # Nunca Yamal; ni lesionados, ni sin partidos, ni de rival, ni los
    # que bajan puntos sin dar caja.
    assert all(c["vende"] != "Yamal" for c in r["cambios"])
    assert not {"Lesionado", "Nuevo", "DeRival", "Malo"} & set(por)


def test_protegidos_no_se_venden():
    r = comparar(FILAS, protegidos={1})
    assert all(c["vende"] != "Jutglà" for c in r["cambios"])


def test_nunca_lanza():
    assert comparar(None)["ok"]
    assert comparar([{"de_quien": "computer", "played": "x"}])["ok"]


TESTS = [test_puntos_y_caja, test_protegidos_no_se_venden, test_nunca_lanza]


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
