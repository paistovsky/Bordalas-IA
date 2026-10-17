"""
LA PUJA EN 9.900 (17/10/2026). Guardias de `BORDALAS_LA_PUJA_EN_9900` en
`src/actions/la_mejora_del_once.py` y de `en_9900` en
`src/actions/la_ronda_de_la_manana.py`.

    1. `en_9900`: el primer importe que termina en 9.900 y no baja.
    2. Con el interruptor, la puja del que entra en el once termina en
       9.900 y la caja del cambio la cuenta; apagado, como antes.
    3. Nace apagado.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.la_mejora_del_once as mejora                     # noqa: E402
import src.analysis.test_la_mejora_del_once_v1 as base              # noqa: E402

from src.actions.la_ronda_de_la_manana import en_9900                # noqa: E402


def test_en_9900():
    # El ejemplo del laboratorio: 3.252.000 -> 3.259.900 (no 3.252.000).
    assert en_9900(3_252_000) == 3_259_900
    assert en_9900(3_259_900) == 3_259_900
    assert en_9900(3_259_950) == 3_269_900
    assert en_9900(1_010_000) == 1_019_900
    assert en_9900(0) == 9_900
    assert en_9900("x") == "x"


def test_la_mejora_puja_en_9900():
    d = base._d()
    puja = next(a for a in d["acciones"] if a["accion"] == "PUJAR")
    assert puja["importe"] == mejora.la_puja(3_700_000) == 3_737_000, puja
    d = base._d(en_9900=True)
    puja = next(a for a in d["acciones"] if a["accion"] == "PUJAR")
    assert puja["importe"] == 3_739_900, puja
    assert d["plan"]["caja_despues"] == 500_000 + int(2_700_000 * 0.95) - 3_739_900, d["plan"]


def test_nace_apagado():
    viejo = os.environ.pop(mejora.ENV_PUJA_EN_9900, None)
    try:
        assert mejora.la_puja_en_9900_activa() is False
        os.environ[mejora.ENV_PUJA_EN_9900] = "1"
        assert mejora.la_puja_en_9900_activa() is True
    finally:
        os.environ.pop(mejora.ENV_PUJA_EN_9900, None)
        if viejo is not None:
            os.environ[mejora.ENV_PUJA_EN_9900] = viejo


TESTS = [test_en_9900, test_la_mejora_puja_en_9900, test_nace_apagado]


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
