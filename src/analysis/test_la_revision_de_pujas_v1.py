"""
La revision de las pujas vivas antes del reset.

QUE SE PRUEBA (29/09/2026)

    1. Fuera de la ventana no retira nada.
    2. En la ventana retira las pujas nuestras por jugadores que Biwenger
       ya marca injured / doubt / sanctioned, y deja las de «ok».
    3. No toca pujas ajenas ni ofertas que nos hacen.
    4. La puja de la orden del gestor no se retira: se avisa.
    5. Apagada, `correr` no crea escritor; encendida manda un cancel_bid
       por puja mala.

    Sin red y sin login.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.actions.la_revision_de_pujas as rev              # noqa: E402


YO = 14175949
ZUBELDIA, BUENO, ROBERTO, AJENO = 8376, 11, 35678, 12


def _foto():
    def puja(oid, pid, desde):
        return {"id": oid, "type": "purchase", "status": "waiting",
                "amount": 1_000_000, "from": desde,
                "requestedPlayers": [{"id": pid}]}
    return {
        "league": {"user": {"id": YO}},
        "market": {"offers": [
            puja(1, ZUBELDIA, {"id": YO}),
            puja(2, BUENO, {"id": YO}),
            puja(3, ROBERTO, {"id": YO}),
            puja(4, AJENO, {"id": 999}),
            puja(5, BUENO, None),
        ]},
        "catalog": {"data": {"players": {
            str(ZUBELDIA): {"status": "doubt"},
            str(BUENO): {"status": "ok"},
            str(ROBERTO): {"status": "injured"},
            str(AJENO): {"status": "injured"},
        }}},
    }


def test_fuera_de_la_ventana_nada() -> None:
    d = rev.decidir(_foto(), en_ventana=False, de_la_orden=set())
    assert d["retirar"] == [] and d["revisadas"] == [], d


def test_retira_la_mala_y_deja_la_buena() -> None:
    d = rev.decidir(_foto(), en_ventana=True, de_la_orden=set())
    assert [r["offer_id"] for r in d["retirar"]] == [1, 3], d
    assert {r["player_id"] for r in d["revisadas"]} == {ZUBELDIA, BUENO, ROBERTO}, d


def test_la_de_la_orden_solo_avisa() -> None:
    d = rev.decidir(_foto(), en_ventana=True, de_la_orden={ROBERTO})
    assert [r["offer_id"] for r in d["retirar"]] == [1], d
    assert [a["player_id"] for a in d["avisos"]] == [ROBERTO], d


def test_correr_apagada_y_encendida() -> None:
    antes = os.environ.get(rev.ENV)
    try:
        os.environ.pop(rev.ENV, None)
        creados = []
        s = rev.correr({"snapshot": _foto()}, 600, escritor_factory=lambda: creados.append(1))
        assert creados == [] and s["motivo"] == "APAGADA", s

        class _Esc:
            def __init__(self):
                self.cancelados = []

            def cancel_bid(self, offer_id, execute=False):
                self.cancelados.append((offer_id, execute))
                return {"sent": True, "success": True}

        os.environ[rev.ENV] = "1"
        esc = _Esc()
        s = rev.correr({"snapshot": _foto()}, 10 * 3600, escritor_factory=lambda: esc)
        assert s["motivo"] == "FUERA_DE_LA_VENTANA" and esc.cancelados == [], s

        s = rev.correr({"snapshot": _foto()}, 600, escritor_factory=lambda: esc)
        assert (1, True) in esc.cancelados, (s, esc.cancelados)
        assert all(o in (1, 3) for o, _ in esc.cancelados), esc.cancelados
    finally:
        if antes is None:
            os.environ.pop(rev.ENV, None)
        else:
            os.environ[rev.ENV] = antes


TESTS = [
    test_fuera_de_la_ventana_nada,
    test_retira_la_mala_y_deja_la_buena,
    test_la_de_la_orden_solo_avisa,
    test_correr_apagada_y_encendida,
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
