"""
LA PROXIMA JORNADA (12/10/2026). Guardias de
`src/analysis/la_proxima_jornada.py` y de los dos relojes que ahora
delegan en él: `los_chollos.horas_a_la_jornada` y
`la_mejora_del_once.jornada_en_curso`.

No lee el calendario de producción ni el reloj: el calendario va aquí
(las horas de verdad de la J5-J7 y la J9-J10, de
`data/calendar/calendar_changes.jsonl`) y `ahora` se pasa siempre.
"""

from __future__ import annotations

import json
import sys
import tempfile

from datetime import datetime, timedelta
from pathlib import Path


RAIZ = Path(__file__).parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.la_proxima_jornada import (     # noqa: E402
    horas_al_proximo_cierre, jornada_en_curso, las_rondas, los_equipos_de,
)


def _j(jornada, *horas):
    partidos = [{"matchday": jornada, "home": f"L{i}", "away": f"V{i}", "kickoff": h}
                for i, h in enumerate(horas)]
    return {"matchday": jornada, "first_kickoff": min(horas), "matches": partidos}


# La J6 de esta temporada: un adelantado (03/09), el grueso (15-17/09) y el
# aplazado Levante-Athletic (21/10, cambio del 17/09).
J6 = _j(6, "2026-09-03T21:00:00+02:00",
        "2026-09-15T19:00:00+02:00", "2026-09-15T20:00:00+02:00",
        "2026-09-15T21:30:00+02:00", "2026-09-16T19:00:00+02:00",
        "2026-09-16T19:00:00+02:00", "2026-09-16T21:30:00+02:00",
        "2026-09-17T19:00:00+02:00", "2026-09-17T21:30:00+02:00",
        "2026-10-21T20:00:00+02:00")
CALENDARIO = {"matchdays": [
    _j(5, "2026-09-11T21:00:00+02:00", "2026-09-12T14:00:00+02:00",
       "2026-09-13T21:00:00+02:00", "2026-09-14T21:00:00+02:00"),
    J6,
    _j(7, "2026-09-18T21:00:00+02:00", "2026-09-19T14:00:00+02:00",
       "2026-09-20T21:00:00+02:00"),
    _j(9, "2026-10-16T21:00:00+02:00", "2026-10-17T14:00:00+02:00",
       "2026-10-18T21:00:00+02:00", "2026-10-19T21:00:00+02:00"),
    _j(10, "2026-10-23T21:00:00+02:00", "2026-10-24T14:00:00+02:00",
       "2026-10-25T21:00:00+01:00", "2026-10-26T21:00:00+01:00"),
]}


def _t(iso):
    return datetime.fromisoformat(iso)


def test_la_j6_son_tres_rondas():
    rondas = las_rondas(CALENDARIO)
    j6 = [(r["inicio"], r["fin"], r["partidos"], r["aparte"])
          for r in rondas if r["jornada"] == 6]
    assert j6 == [
        (_t("2026-09-03T21:00:00+02:00"), _t("2026-09-03T21:00:00+02:00"), 1, True),
        (_t("2026-09-15T19:00:00+02:00"), _t("2026-09-17T21:30:00+02:00"), 8, False),
        (_t("2026-10-21T20:00:00+02:00"), _t("2026-10-21T20:00:00+02:00"), 1, True),
    ], j6
    # Por hora de inicio: el aplazado cae entre la J9 y la J10.
    orden = [(r["jornada"], r["aparte"]) for r in rondas]
    assert orden == [(6, True), (5, False), (6, False), (7, False),
                     (9, False), (6, True), (10, False)], orden
    # Una jornada normal (viernes-lunes) es una sola ronda.
    j10 = [r for r in rondas if r["jornada"] == 10]
    assert len(j10) == 1 and j10[0]["partidos"] == 4


def test_los_aplazados_que_se_juegan_juntos_van_en_una_ronda():
    # La J1: 6 partidos del 15 al 19/08 y 4 aplazados del 25 al 27/08.
    j1 = _j(1, "2026-08-15T19:30:00+02:00", "2026-08-15T21:30:00+02:00",
            "2026-08-16T17:00:00+02:00", "2026-08-16T19:00:00+02:00",
            "2026-08-17T21:00:00+02:00", "2026-08-19T21:00:00+02:00",
            "2026-08-25T21:00:00+02:00", "2026-08-26T21:00:00+02:00",
            "2026-08-27T20:30:00+02:00", "2026-08-27T21:00:00+02:00")
    rondas = las_rondas({"matchdays": [j1]})
    assert [(r["partidos"], r["aparte"]) for r in rondas] == [(6, False), (4, True)]
    assert rondas[1]["inicio"] == _t("2026-08-25T21:00:00+02:00")
    assert rondas[1]["fin"] == _t("2026-08-27T21:00:00+02:00")
    # Sin partidos, el `first_kickoff`; sin `matchdays`, la lista suelta.
    solo = las_rondas({"matchdays": [{"matchday": 3, "first_kickoff": "2026-08-28T19:00:00+02:00"}]})
    assert [(r["inicio"], r["fin"]) for r in solo] == [
        (_t("2026-08-28T19:00:00+02:00"), _t("2026-08-28T19:00:00+02:00"))]
    sueltos = las_rondas({"matches": j1["matches"]})
    assert [(r["partidos"], r["aparte"]) for r in sueltos] == [(6, False), (4, True)]


def test_las_horas_al_proximo_cierre():
    h = lambda iso: horas_al_proximo_cierre(_t(iso), CALENDARIO)   # noqa: E731
    # El 15/09 por la mañana, con la J5 acabada: el cierre es el grueso de
    # la J6 a las 19:00 (antes, con `first_kickoff` = 03/09, era la J7).
    assert h("2026-09-15T10:00:00+02:00") == 9.0
    # Después del adelantado del 03/09, el próximo cierre es la J5.
    assert h("2026-09-04T21:00:00+02:00") == 7 * 24
    # Con la J9 jugada, el aplazado del 21/10 (no la J10).
    assert h("2026-10-20T12:00:00+02:00") == 32.0
    # Empezado el aplazado, la J10.
    assert h("2026-10-21T21:00:00+02:00") == 48.0
    # Justo en el inicio, esa ronda ya ha empezado.
    assert h("2026-10-16T21:00:00+02:00") == 5 * 24 - 1
    # `ahora` sin zona va en UTC.
    assert horas_al_proximo_cierre(datetime(2026, 10, 20, 10, 0), CALENDARIO) == 32.0
    # Sin nada por delante, o sin calendario: None.
    assert h("2026-12-01T12:00:00+01:00") is None
    for malo in ({}, {"matchdays": "x"}, {"matchdays": [{"matches": [{"kickoff": "ayer"}]}]},
                 "/no/existe/calendario.json"):
        assert horas_al_proximo_cierre(_t("2026-10-20T12:00:00+02:00"), malo) is None
    assert horas_al_proximo_cierre(None, CALENDARIO) is None


def test_la_jornada_en_curso():
    e = lambda iso: jornada_en_curso(_t(iso), CALENDARIO)          # noqa: E731
    assert e("2026-09-03T22:00:00+02:00")                 # el adelantado
    assert e("2026-09-04T00:00:00+02:00")                 # hasta 3 h después
    assert not e("2026-09-04T00:01:00+02:00")
    assert not e("2026-09-10T12:00:00+02:00")             # entre rondas
    # El grueso de la J6: antes no contaba (se cortaba a 5 días del 03/09).
    assert e("2026-09-16T12:00:00+02:00")
    assert e("2026-09-18T00:30:00+02:00")
    # El aplazado del 21/10 es una ronda: en curso de 20:00 a 23:00.
    assert not e("2026-10-21T19:59:00+02:00")
    assert e("2026-10-21T20:30:00+02:00")
    assert not e("2026-10-21T23:01:00+02:00")
    # Fin de semana de la J10, con cambio de hora por medio.
    assert e("2026-10-25T12:00:00+01:00")
    assert not e("2026-10-27T12:00:00+01:00")
    # Sin saberlo, True: no se vende.
    for malo in ({}, {"matchdays": []}, "/no/existe/calendario.json", {"matchdays": 7}):
        assert jornada_en_curso(_t("2026-10-20T12:00:00+02:00"), malo) is True
    assert jornada_en_curso(None, CALENDARIO) is True


def test_los_relojes_de_siempre_delegan():
    from src.actions.la_mejora_del_once import jornada_en_curso as de_la_mejora
    from src.actions.los_chollos import horas_a_la_jornada

    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "laliga_calendar.json"
        ruta.write_text(json.dumps(CALENDARIO))
        for iso in ("2026-09-15T10:00:00+02:00", "2026-10-20T12:00:00+02:00",
                    "2026-10-21T21:00:00+02:00"):
            ahora = _t(iso)
            assert horas_a_la_jornada(ahora, ruta) == horas_al_proximo_cierre(ahora, ruta)
            assert horas_a_la_jornada(ahora, str(ruta)) == horas_al_proximo_cierre(ahora, CALENDARIO)
        for iso in ("2026-09-16T12:00:00+02:00", "2026-09-10T12:00:00+02:00",
                    "2026-10-21T20:30:00+02:00"):
            ahora = _t(iso)
            assert de_la_mejora(ahora, ruta) == jornada_en_curso(ahora, CALENDARIO)
        # El 16/09 (grueso de la J6) la mejora ya no vende.
        assert de_la_mejora(_t("2026-09-16T12:00:00+02:00"), ruta) is True
    # Un dict también vale; sin calendario, None y True.
    assert horas_a_la_jornada(_t("2026-10-20T12:00:00+02:00"), CALENDARIO) == 32.0
    assert horas_a_la_jornada(_t("2026-10-20T12:00:00+02:00"), "/no/existe.json") is None
    assert de_la_mejora(_t("2026-10-20T12:00:00+02:00"), "/no/existe.json") is True


def test_los_equipos_de_cada_ronda():
    # Los de la ronda y solo esos (19/10/2026: el freno de la rotacion
    # antes del Levante-Athletic solo vale para los de esos dos).
    j6 = [r for r in las_rondas(CALENDARIO) if r["jornada"] == 6]
    assert los_equipos_de(j6[0], CALENDARIO) == ["L0", "V0"]
    assert los_equipos_de(j6[2], CALENDARIO) == ["L9", "V9"]
    assert len(los_equipos_de(j6[1], CALENDARIO)) == 16
    # Un partido de la ronda sin un nombre, o la jornada sin partidos (solo
    # `first_kickoff`): no se sabe, None; nunca una lista a medias.
    cojo = {"matchdays": [{"matchday": 6, "matches": [
        {"matchday": 6, "home": "Levante UD", "away": None,
         "kickoff": "2026-10-21T20:00:00+02:00"}]}]}
    assert los_equipos_de(las_rondas(cojo)[0], cojo) is None
    solo = {"matchdays": [{"matchday": 3, "first_kickoff": "2026-08-28T19:00:00+02:00"}]}
    assert los_equipos_de(las_rondas(solo)[0], solo) is None
    # Sin `matchdays`, la lista suelta.
    sueltos = {"matches": [{"matchday": 6, "home": "Levante UD", "away": "Athletic Club",
                            "kickoff": "2026-10-21T20:00:00+02:00"}]}
    assert los_equipos_de(las_rondas(sueltos)[0], sueltos) == ["Athletic Club", "Levante UD"]
    for raro in (None, {}, 7, "x"):
        assert los_equipos_de(raro, CALENDARIO) is None
    assert los_equipos_de(j6[2], "/no/existe/calendario.json") is None


def test_nunca_lanza():
    # (Nunca `None`: sería el calendario de producción.)
    raros = (7, "", [], {"matchdays": [None, 3, {"matches": None}]},
             {"matchdays": [{"matchday": 1, "matches": [{"kickoff": None}, "x"]}]})
    for raro in raros:
        assert las_rondas(raro) == []
        assert horas_al_proximo_cierre(_t("2026-10-20T12:00:00+02:00"), raro) is None
        assert jornada_en_curso(_t("2026-10-20T12:00:00+02:00"), raro) is True
    # Una hora sin zona en el calendario se toma como de Madrid.
    r = las_rondas({"matchdays": [_j(9, "2026-10-16T21:00:00")]})
    assert r[0]["inicio"] - _t("2026-10-16T19:00:00+00:00") == timedelta(0)


TESTS = [test_la_j6_son_tres_rondas, test_los_aplazados_que_se_juegan_juntos_van_en_una_ronda,
         test_las_horas_al_proximo_cierre, test_la_jornada_en_curso,
         test_los_relojes_de_siempre_delegan, test_los_equipos_de_cada_ronda,
         test_nunca_lanza]


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
