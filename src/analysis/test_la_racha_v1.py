"""
La racha diaria: Pepe la cobra cuando llega a cinco, y solo entonces.

QUE SE PRUEBA (28/09/2026)

    1. Apagada, no crea escritor aunque la racha este en 5.
    2. Encendida con racha 0-4 o sin leer (None), tampoco.
    3. Encendida con racha 5, UNA llamada a `redeem_daily_streak` con
       la liga del escritor y execute=True.
    4. La peticion es la del boton de Biwenger: POST
       /account/dailyStreak/redeem con {"league": id}.
    5. Si el escritor revienta, no lanza: lo apunta.

    Sin red y sin login. Pone y quita ella misma el interruptor
    (doctrina 104).
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.actions.la_racha as la_racha                    # noqa: E402
import src.biwenger.write_client as escritura               # noqa: E402


class _Espia:
    league_id = 777

    def __init__(self):
        self.llamadas = []

    def redeem_daily_streak(self, league_id, execute=False):
        self.llamadas.append((league_id, execute))
        return {"operation": "REDEEM_DAILY_STREAK", "sent": True,
                "success": True, "http_status": 200}


class _Fabrica:
    def __init__(self):
        self.creados = []

    def __call__(self):
        e = _Espia()
        self.creados.append(e)
        return e


def _vuelta(racha):
    return {"snapshot": {"daily_streak": racha}}


class _Interruptor:
    def __init__(self, puesto):
        self.puesto = puesto

    def __enter__(self):
        self.antes = os.environ.get(la_racha.ENV)
        if self.puesto:
            os.environ[la_racha.ENV] = "1"
        else:
            os.environ.pop(la_racha.ENV, None)

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(la_racha.ENV, None)
        else:
            os.environ[la_racha.ENV] = self.antes


def test_apagada_no_cobra() -> None:
    with _Interruptor(False):
        f = _Fabrica()
        s = la_racha.cobrar(_vuelta(5), escritor_factory=f)
        assert f.creados == [], "apagada creo un escritor"
        assert s["motivo"] == "APAGADA" and not s["cobrada"], s


def test_encendida_sin_llegar_no_cobra() -> None:
    with _Interruptor(True):
        for racha in (0, 1, 4, None, "x"):
            f = _Fabrica()
            s = la_racha.cobrar(_vuelta(racha), escritor_factory=f)
            assert f.creados == [], f"con racha {racha!r} creo un escritor"
            assert not s["intentado"], s
        f = _Fabrica()
        la_racha.cobrar(None, escritor_factory=f)
        assert f.creados == [], "sin vuelta creo un escritor"


def test_encendida_en_cinco_cobra_una_vez() -> None:
    with _Interruptor(True):
        f = _Fabrica()
        s = la_racha.cobrar(_vuelta(5), escritor_factory=f)
        assert len(f.creados) == 1, f.creados
        assert f.creados[0].llamadas == [(777, True)], f.creados[0].llamadas
        assert s["cobrada"] and s["motivo"] == "COBRADA", s


def test_la_peticion_es_la_del_boton() -> None:
    cliente = object.__new__(escritura.BiwengerWriteClient)

    class _C:
        BASE_URL = "https://biwenger.as.com/api/v2"

    cliente.client = _C()
    cliente.version = "0"
    cliente.league_id = 777
    cliente.user_id = 1

    r = cliente.redeem_daily_streak(league_id=777, execute=False)
    assert r["method"] == "POST", r
    assert r["url"].endswith("/api/v2/account/dailyStreak/redeem"), r["url"]
    assert r["json"] == {"league": 777}, r["json"]
    assert r["sent"] is False, r


def test_si_revienta_no_lanza() -> None:
    def _rota():
        raise RuntimeError("sin red")

    with _Interruptor(True):
        s = la_racha.cobrar(_vuelta(5), escritor_factory=_rota)
        assert s["motivo"].startswith("ERROR"), s
        assert not s["cobrada"], s


TESTS = [
    test_apagada_no_cobra,
    test_encendida_sin_llegar_no_cobra,
    test_encendida_en_cinco_cobra_una_vez,
    test_la_peticion_es_la_del_boton,
    test_si_revienta_no_lanza,
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
