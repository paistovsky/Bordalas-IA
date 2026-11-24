"""
LAS PRIMAS MEDIDAS (24/11/2026). Guardias de `BORDALAS_LAS_PRIMAS_MEDIDAS`
(`src/actions/la_ronda_de_la_manana.py`: `las_primas`,
`la_puja_de_la_cartera`).

QUE SE COMPRUEBA

    1. Nace apagado, se lee en un sitio, tiene frase en el tablon.
    2. Apagado, la puja de la cartera es la de siempre (+12 % / +4 % /
       +1 %, en 9.900), precio a precio, tambien en los bordes de tramo.
    3. Encendido: +6 % por debajo de 1 M y +1 % de 1 M para arriba, en
       9.900, y nunca menos que `la_puja` (precio + 1 %).
    4. El caso de hoy: Espi (1.600.000) apagado 1.669.900; encendido
       1.619.900. Un barato de 500.000: 569.900 apagado, 539.900 encendido.
    5. Con basura no lanza: precio 0, None, texto, negativo -> `la_puja`.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).parents[2]
sys.path.insert(0, str(RAIZ))

from src.actions import la_ronda_de_la_manana as R   # noqa: E402

ENV = "BORDALAS_LAS_PRIMAS_MEDIDAS"


class _Entorno:
    def __init__(self, valor):
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(ENV)
        if self.valor is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.valor

    def __exit__(self, *a):
        if self.antes is None:
            os.environ.pop(ENV, None)
        else:
            os.environ[ENV] = self.antes


def _esperada(precio, prima):
    return max(int(precio * (1 + prima)) // 10_000 * 10_000 + 9_900, R.la_puja(precio))


PRECIOS = (150_000, 400_000, 500_000, 999_999, 1_000_000, 1_600_000, 2_999_999,
           3_000_000, 4_420_000, 8_240_000)


def test_nace_apagado_un_lector_y_su_frase():
    assert R.ENV_PRIMAS_MEDIDAS == ENV
    with _Entorno(None):
        assert R.las_primas_medidas_activas() is False
        assert R.las_primas() is R.PRIMAS_DE_LA_CARTERA
    for v in ("", "0", "off", "no", "2"):
        with _Entorno(v):
            assert R.las_primas_medidas_activas() is False, v
    from src.analysis.el_paso_0 import ENCENDIDO
    for v in ENCENDIDO:
        with _Entorno(v):
            assert R.las_primas_medidas_activas() is True, v
            assert R.las_primas() is R.PRIMAS_MEDIDAS
    lectores = []
    for camino in (RAIZ / "src").rglob("*.py"):
        if camino.name.startswith("test_") or "PRE_" in camino.name or "BACKUP" in camino.name:
            continue
        if ENV in camino.read_text(errors="ignore") and camino.name != "el_tablon.py":
            lectores.append(camino.name)
    assert lectores == ["la_ronda_de_la_manana.py"], lectores
    from src.telemetry.el_tablon import QUE_HACE
    assert ENV in QUE_HACE and len(QUE_HACE[ENV]) > 40


def test_apagado_lo_de_siempre():
    with _Entorno(None):
        for p in PRECIOS:
            prima = 0.12 if p < 1_000_000 else (0.04 if p < 3_000_000 else 0.01)
            assert R.la_puja_de_la_cartera(p) == _esperada(p, prima), p


def test_encendido_las_primas_medidas():
    with _Entorno("1"):
        for p in PRECIOS:
            prima = 0.06 if p < 1_000_000 else 0.01
            puja = R.la_puja_de_la_cartera(p)
            assert puja == _esperada(p, prima), (p, puja)
            assert puja >= R.la_puja(p)
            assert puja % 10_000 == 9_900 or puja == R.la_puja(p)


def test_el_caso_de_hoy():
    with _Entorno(None):
        assert R.la_puja_de_la_cartera(1_600_000) == 1_669_900
        assert R.la_puja_de_la_cartera(500_000) == 569_900
    with _Entorno("1"):
        assert R.la_puja_de_la_cartera(1_600_000) == 1_619_900
        assert R.la_puja_de_la_cartera(500_000) == 539_900
        assert R.la_puja_de_la_cartera(4_420_000) == 4_469_900


def test_nunca_lanza():
    for v in (None, "1"):
        with _Entorno(v):
            for basura in (0, None, "x", -5, [], {}):
                assert R.la_puja_de_la_cartera(basura) == R.la_puja(R._int(basura, 0) or 0)


TESTS = [
    test_nace_apagado_un_lector_y_su_frase,
    test_apagado_lo_de_siempre,
    test_encendido_las_primas_medidas,
    test_el_caso_de_hoy,
    test_nunca_lanza,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"FALLA {test.__name__}: {type(error).__name__}: {error}")
    print("=" * 60)
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
