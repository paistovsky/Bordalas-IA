"""
UN SOLO COLCHÓN (17/10/2026). Guardias de `BORDALAS_UN_SOLO_COLCHON`
(`src/actions/la_ronda_de_la_manana.py` y la rama BUY_SPECULATION de
`src/actions/autopilot_executor.py`).

    El motor viejo pujó 1.778.494 por Manu Sánchez con la caja en
    -432.317: su presupuesto autoriza deuda y no ve las pujas de la
    ronda, los chollos ni la mejora.

    1. El colchón es uno: saldo - todas las pujas + 92 % de lo de la ronda.
    2. Lo del motor viejo cuenta entero; su propia puja vieja no cuenta.
    3. El caso de Manu Sánchez no cabe; con caja, sí.
    4. El executor lo mira antes de escribir.
    5. Nace apagado y sin la cartera no hace nada.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.la_ronda_de_la_manana as ronda      # noqa: E402

from src.actions.la_ronda_de_la_manana import (       # noqa: E402
    cabe_en_el_colchon, el_colchon,
)


YO = 77


def _foto(saldo=-432_317, pujas=None, equipo=None, catalogo=None):
    return {
        "league": {"user": {"id": YO}},
        "market": {
            "status": {"balance": saldo, "maximumBid": 12_064_189},
            "sales": [],
            "offers": [
                {"id": 900 + pid, "from": {"id": YO}, "status": "waiting",
                 "amount": importe, "requestedPlayers": [{"id": pid}]}
                for pid, importe in (pujas or {}).items()
            ],
        },
        "my_team": [{"id": p, "price": v} for p, v in (equipo or {}).items()],
        "catalog": {"data": {"players": {
            str(p): {"id": p, "price": v} for p, v in (catalogo or {}).items()}}},
    }


def _libro(d, contenido):
    ruta = Path(d) / "la_ronda.json"
    ruta.write_text(json.dumps(contenido))
    return ruta


def test_el_colchon_es_uno():
    fichas = {1: {"price": 1_000_000}, 2: {"price": 2_000_000}, 3: {"price": 500_000}}
    pujas = {2: {"amount": 2_100_000}, 9: {"amount": 300_000}}
    # 1 en plantilla y 2 pujado son de la ronda; 3 está en el libro pero ya no es nuestro.
    libro = {"1": 1_009_900, "2": 2_089_900, "3": 509_900}
    colchon = el_colchon(1_000_000, pujas, libro, {1, 5}, fichas)
    assert abs(colchon - (1_000_000 - 2_400_000 + 0.92 * 3_000_000)) < 1
    assert el_colchon(None, pujas, libro, {1}, fichas) is None
    assert el_colchon(0, {}, {}, set(), {}) == 0


def test_manu_sanchez_no_cabe():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d, {})
        r = cabe_en_el_colchon(_foto(), 1721, 1_778_494, libro)
        assert r["cabe"] is False and r["colchon"] == -432_317
        # Con su puja ya viva, la vieja no cuenta: sigue sin caber.
        r = cabe_en_el_colchon(_foto(pujas={1721: 1_778_494}), 1721, 1_778_494, libro)
        assert r["cabe"] is False and r["colchon"] == -432_317


def test_con_caja_cabe_y_cuenta_entera():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d, {"10": 1_009_900})
        # 3 M de saldo, 1 M pujado por otro, 10 de la ronda en plantilla (1 M).
        foto = _foto(saldo=3_000_000, pujas={20: 1_000_000}, equipo={10: 1_000_000})
        r = cabe_en_el_colchon(foto, 1721, 2_900_000, libro)
        assert r["colchon"] == 2_920_000 and r["cabe"] is True
        # Entera: 2.930.000 ya no cabe (la ronda la contaría al 8 %).
        assert cabe_en_el_colchon(foto, 1721, 2_930_000, libro)["cabe"] is False
        # Lo de la ronda con puja viva se cuenta por el catálogo.
        foto = _foto(saldo=3_000_000, pujas={10: 1_100_000}, catalogo={10: 1_000_000})
        assert cabe_en_el_colchon(foto, 1721, 1_800_000, libro)["colchon"] == 2_820_000


def test_con_basura_no_cabe():
    assert cabe_en_el_colchon(None, 1721, 1_000_000)["cabe"] is False
    assert cabe_en_el_colchon({"market": "x"}, 1721, 1_000_000)["cabe"] is False
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d, {})
        foto = _foto(saldo=3_000_000)
        assert cabe_en_el_colchon(foto, 1721, 0, libro)["cabe"] is False
        foto["market"]["status"].pop("balance")
        assert cabe_en_el_colchon(foto, 1721, 1, libro)["cabe"] is False


def test_el_executor_lo_mira_antes_de_escribir():
    texto = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text()
    rama = texto.index("if action == SPECULATION_BUY_ACTION:")
    puerta = texto.index("if un_solo_colchon_activo():", rama)
    escribe = texto.index("writer.place_bid(", puerta)
    assert puerta < escribe
    assert "SPECULATION_SIN_COLCHON" in texto[puerta:escribe]
    # La única escritura de esa rama es la de despues de la puerta.
    assert texto.count("writer.place_bid(") == 1


def test_nace_apagado_y_sin_cartera_no_hace_nada():
    viejos = {k: os.environ.pop(k, None)
              for k in (ronda.ENV_CARTERA, ronda.ENV_UN_SOLO_COLCHON)}
    try:
        assert ronda.un_solo_colchon_activo() is False
        os.environ[ronda.ENV_UN_SOLO_COLCHON] = "1"
        assert ronda.un_solo_colchon_activo() is False
        os.environ[ronda.ENV_CARTERA] = "1"
        assert ronda.un_solo_colchon_activo() is True
        os.environ.pop(ronda.ENV_UN_SOLO_COLCHON)
        assert ronda.un_solo_colchon_activo() is False
    finally:
        for k, v in viejos.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


TESTS = [
    test_el_colchon_es_uno,
    test_manu_sanchez_no_cabe,
    test_con_caja_cabe_y_cuenta_entera,
    test_con_basura_no_cabe,
    test_el_executor_lo_mira_antes_de_escribir,
    test_nace_apagado_y_sin_cartera_no_hace_nada,
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
