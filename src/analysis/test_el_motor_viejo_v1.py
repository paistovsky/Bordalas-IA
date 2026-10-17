"""
EL MOTOR VIEJO (17/10/2026, laboratorio de rivales). Guardias de la rama
BUY_SPECULATION de `src/actions/autopilot_executor.py`.

    1. Los `no_pujar` de la orden tampoco los puja: tras vetar a Manu
       Sanchez volvio a pujar por el cada hora y solo lo paro el colchon.
       El veto va ANTES de refrescar la foto (no cuesta una llamada).
    2. Con `BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE` (nace apagado), solo por
       el que sube de verdad en la foto fresca (la vara de la mejora):
       lo que bajaba el dia de la puja dejo -716.045 desde el 21/08.
    3. Las dos puertas van antes de la unica escritura de la rama.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import src.actions.autopilot_executor as ejecutor        # noqa: E402
import src.actions.la_orden_del_gestor as orden          # noqa: E402
import src.actions.la_ronda_de_la_manana as ronda        # noqa: E402


class _Refresco(Exception):
    pass


def _decision(pid):
    return {"action": ejecutor.SPECULATION_BUY_ACTION, "executable": True,
            "data": {"player": {"id": pid}, "intent": "XI_UPGRADE",
                     "target_source": "ACQUISITION_BOARD"}}


def _con(vetados, decision):
    """Corre la rama con `vetados` y un refresco de la foto que avisa."""
    v, r = orden.vetados, ejecutor.refresh_snapshot_for_write_revalidation
    orden.vetados = lambda *a, **k: set(vetados)

    def refresco():
        raise _Refresco("llego a refrescar")

    ejecutor.refresh_snapshot_for_write_revalidation = refresco
    try:
        return ejecutor.execute_autopilot_decision(decision, execute=True)
    finally:
        orden.vetados, ejecutor.refresh_snapshot_for_write_revalidation = v, r


def test_el_vetado_no_se_puja_ni_se_refresca():
    r = _con({1721}, _decision(1721))
    assert r.get("status") == "SPECULATION_VETADA_POR_LA_ORDEN", r
    # El que no esta vetado sigue su camino (llega al refresco).
    r = _con({1721}, _decision(999))
    assert r.get("status") == "SPECULATION_REVALIDATION_REFRESH_FAILED", r
    # Un id que no vale no se puja, y se dice que no vale (no que esta vetado).
    for malo in ("x", "", "1721.0", float("inf")):
        r = _con(set(), _decision(malo))
        assert r.get("status") == "INVALID_SPECULATION_PLAYER" and r.get("success") is False, (malo, r)


def _foto(sube, precio=1_000_000, lista=False):
    ficha = {"id": 7, "price": precio, "priceIncrement": sube}
    jugadores = [ficha] if lista else {"7": ficha}
    return {"catalog": {"data": {"players": jugadores}}}


def test_sube_en_la_foto():
    # La vara de la mejora: sube y al menos la subida minima de su tramo.
    minima = ronda.la_subida_minima(1_000_000)
    assert ronda.sube_en_la_foto(_foto(minima), 7) is True
    assert ronda.sube_en_la_foto(_foto(minima, lista=True), 7) is True
    assert ronda.sube_en_la_foto(_foto(minima - 1), 7) is False
    assert ronda.sube_en_la_foto(_foto(0), 7) is False
    assert ronda.sube_en_la_foto(_foto(-20_000), 7) is False
    assert ronda.sube_en_la_foto(_foto(None), 7) is False
    assert ronda.sube_en_la_foto(_foto(minima), 8) is False
    assert ronda.sube_en_la_foto(None, 7) is False


def test_la_puerta_de_sube():
    viejo = os.environ.pop(ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE, None)
    minima = ronda.la_subida_minima(1_000_000)
    try:
        # Apagada, deja pasar a todos.
        assert ronda.la_puerta_de_sube(_foto(-20_000), 7) is None
        assert ronda.la_puerta_de_sube(None, 7) is None
        os.environ[ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE] = "1"
        assert ronda.la_puerta_de_sube(_foto(minima), 7) is None
        assert ronda.la_puerta_de_sube(_foto(minima - 1), 7) == "SPECULATION_NO_SUBE"
        assert ronda.la_puerta_de_sube(_foto(-20_000), 7) == "SPECULATION_NO_SUBE"
        assert ronda.la_puerta_de_sube(None, 7) == "SPECULATION_NO_SUBE"
    finally:
        os.environ.pop(ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE, None)
        if viejo is not None:
            os.environ[ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE] = viejo


def test_el_orquestador_ni_elige_al_vetado():
    texto = (RAIZ / "src" / "analysis" / "decision_orchestrator.py").read_text()
    filtro = texto.index("no_se_pujan = set(_vetados())")
    lista = texto.index("if int(player.get(\"id\") or 0) not in no_se_pujan", filtro)
    legacy = texto.index("pendientes_legacy = (", lista)
    mejor = texto.index("exclude_ids=set(ya_pujados) | no_se_pujan", legacy)
    assert filtro < lista < legacy < mejor


def test_las_puertas_antes_de_la_unica_escritura():
    texto = (RAIZ / "src" / "actions" / "autopilot_executor.py").read_text()
    rama = texto.index("if action == SPECULATION_BUY_ACTION:")
    veto = texto.index("SPECULATION_VETADA_POR_LA_ORDEN", rama)
    refresco = texto.index("refresh_snapshot_for_write_revalidation()", rama)
    sube = texto.index("no_sube = la_puerta_de_sube(fresh_snapshot, requested_player_id)", rama)
    colchon = texto.index("if un_solo_colchon_activo():", rama)
    escribe = texto.index("writer.place_bid(", rama)
    assert veto < refresco < sube < colchon < escribe
    assert "if no_sube is not None:\n\n            return {" in texto[sube:colchon]
    assert "status=no_sube," in texto[sube:colchon]


def test_nace_apagado():
    viejo = os.environ.pop(ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE, None)
    try:
        assert ronda.el_motor_viejo_solo_si_sube_activo() is False
        os.environ[ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE] = "1"
        assert ronda.el_motor_viejo_solo_si_sube_activo() is True
    finally:
        os.environ.pop(ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE, None)
        if viejo is not None:
            os.environ[ronda.ENV_MOTOR_VIEJO_SOLO_SI_SUBE] = viejo


TESTS = [
    test_el_vetado_no_se_puja_ni_se_refresca,
    test_sube_en_la_foto,
    test_la_puerta_de_sube,
    test_el_orquestador_ni_elige_al_vetado,
    test_las_puertas_antes_de_la_unica_escritura,
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
