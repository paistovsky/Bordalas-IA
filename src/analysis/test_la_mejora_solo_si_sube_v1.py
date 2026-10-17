"""
SOLO SI SUBE (17/10/2026). Guardias de `BORDALAS_LA_MEJORA_SOLO_SI_SUBE`
en `src/actions/la_mejora_del_once.py`.

    1. Con el interruptor, el del Computer que no sube hoy (al menos la
       subida mínima de su tramo) no entra en el once.
    2. Salvo para tapar un hueco: el que sale lesionado, sancionado o con
       menos del 50 % de titularidad.
    3. Lo que ya es nuestro (inventario) no se mira.
    4. Apagado, todo como antes. Nace apagado.
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


def _liga(**incrementos):
    liga = {k: dict(v) for k, v in base.LIGA.items()}
    for pid, inc in incrementos.items():
        liga[int(pid[1:])]["price_increment"] = inc
    return liga


def test_sube_de_verdad():
    # 900.000: la mínima es el 3,1 % (27.900).
    assert mejora.sube_de_verdad({"price": 900_000, "price_increment": 28_000})
    assert not mejora.sube_de_verdad({"price": 900_000, "price_increment": 27_000})
    # 3,7 M: max(20.000, 0,5 %) = 20.000.
    assert mejora.sube_de_verdad({"price": 3_700_000, "price_increment": 20_000})
    assert not mejora.sube_de_verdad({"price": 3_700_000, "price_increment": 10_000})
    assert not mejora.sube_de_verdad({"price": 3_700_000, "price_increment": -10_000})
    # El catálogo lo llama `priceIncrement`.
    assert mejora.sube_de_verdad({"price": 3_700_000, "priceIncrement": 30_000})
    # Sin dato o con basura, no; nunca lanza.
    assert not mejora.sube_de_verdad({"price": 3_700_000})
    assert not mejora.sube_de_verdad("basura")
    assert not mejora.sube_de_verdad(None, "x")


def test_solo_entra_el_que_sube():
    # El 20 por Flojo (10) es el cambio de siempre (+1,74 pts).
    assert base._pujas(base._d()) == [(20, 10)]
    # Con el interruptor y sin saber si sube: no entra.
    d = base._d(solo_si_sube=True)
    assert base._pujas(d) == [] and d["plan"]["sin_subir"] >= 1, d["plan"]
    # Sube poco (10.000 en 3,7 M): no. Sube de verdad (30.000): sí.
    assert base._pujas(base._d(liga=_liga(c20=10_000), solo_si_sube=True)) == []
    assert base._pujas(base._d(liga=_liga(c20=30_000), solo_si_sube=True)) == [(20, 10)]
    # Apagado, aunque baje, como antes.
    assert base._pujas(base._d(liga=_liga(c20=-50_000))) == [(20, 10)]


def test_tapa_un_hueco_aunque_no_suba():
    # El que sale lesionado: entra aunque no suba (a precio + 1 %).
    d = base._d(solo_si_sube=True, estados={10: "injured"})
    assert base._pujas(d) == [(20, 10)], d["plan"]
    puja = next(a for a in d["acciones"] if a["accion"] == "PUJAR")
    assert puja["importe"] == mejora.la_puja(3_700_000), puja
    # El que sale con menos del 50 % de titularidad, también.
    once = [dict(p) for p in base.ONCE]
    once[0]["starter_probability"] = 40
    assert base._pujas(base._d(solo_si_sube=True, once=once)) == [(20, 10)]
    # Con el 60 %, no es un hueco.
    assert base._pujas(base._d(solo_si_sube=True)) == []


def test_lo_que_ya_es_nuestro_no_se_mira():
    # El 20 ya es de la ronda (inventario, en la plantilla) y no sube: se
    # adopta igual, porque no se compra nada.
    foto = base._foto(plantilla={10, 11, 12, 13, 20})
    d = base._d(escaparate=[], foto=foto, inventario={20}, solo_si_sube=True,
                probabilidades={20: 70})
    assert any(a.get("player_id") == 20 for a in d.get("adoptar") or []) or \
        any(c.get("entra") == 20 for c in d["plan"]["cambios"]), d


def test_nace_apagado():
    viejo = os.environ.pop(mejora.ENV_SOLO_SI_SUBE, None)
    try:
        assert mejora.la_mejora_solo_si_sube_activa() is False
        os.environ[mejora.ENV_SOLO_SI_SUBE] = "1"
        assert mejora.la_mejora_solo_si_sube_activa() is True
    finally:
        os.environ.pop(mejora.ENV_SOLO_SI_SUBE, None)
        if viejo is not None:
            os.environ[mejora.ENV_SOLO_SI_SUBE] = viejo


TESTS = [
    test_sube_de_verdad,
    test_solo_entra_el_que_sube,
    test_tapa_un_hueco_aunque_no_suba,
    test_lo_que_ya_es_nuestro_no_se_mira,
    test_nace_apagado,
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
