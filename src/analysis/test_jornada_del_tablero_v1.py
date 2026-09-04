"""
El tablero rancio tiene que ser de ESTA jornada.

SINTOMA

    Un tablero de titularidad de la jornada 3 podia alimentar la
    jornada 4 y salir en verde en el panel de consistencia.

CAUSA

    `refresh_board` comprueba `matchday` en la via HIT -y bien-,
    pero las dos vias de respaldo no lo hacian:

      1. snapshot sin plantilla ni mercado
      2. scrapeo sin un solo jugador emparejado

    Las dos devolvian el tablero anterior tal cual. Y el auditor
    de consistencia lo daba por bueno contando jugadores, que es
    justo lo que un tablero de otra jornada tambien cumple: trae
    sus 59 cabezas.

CONSECUENCIA

    Es el fallo del 16/08/2026 entrando por la puerta de al lado,
    y aquel costo alinear a gente que no jugaba. Un pronostico de
    otra jornada no es un dato viejo: es la respuesta a otra
    pregunta, y se parece demasiado a un dato bueno.

    Esta guardia protege las tres piezas: el respaldo rechaza, el
    auditor lo ve, y la via HIT sigue exigiendo la jornada.
"""

from __future__ import annotations

import json
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path

import src.intelligence.futbolfantasy_provider as ff

from src.telemetry.dashboard_consistency import (
    build_consistency_report,
)


AHORA = datetime.now(timezone.utc)


def _tablero(matchday: int, edad_minutos: int = 5) -> dict:
    """Un tablero anterior con un jugador dentro."""
    return {
        "version": "V12.0",
        "updated_at": (
            AHORA - timedelta(minutes=edad_minutos)
        ).isoformat(),
        "matchday": matchday,
        "metadata": {"matched": 1, "targets": 1},
        "teams": {},
        "players": [
            {
                "player_id": 26271,
                "player_name": "Fulano",
                "team": "Barcelona",
                "scope": "ROSTER",
                "starter_probability": 88.0,
                "consensus": "STARTER",
                "source": "FUTBOLFANTASY",
                "availability": {"code": 0, "label": "DISPONIBLE"},
                "match": {"method": "SLUG", "confidence": "ALTA"},
                "ff": {"slug": "fulano"},
            }
        ],
        "cache": {"status": "REFRESHED"},
    }


def _snapshot_con_objetivo() -> dict:
    return {
        "my_team": [
            {"id": 26271, "name": "Fulano", "teamID": 1, "price": 1_000_000}
        ],
        "catalog": {
            "data": {
                "players": {
                    "26271": {
                        "name": "Fulano",
                        "teamID": 1,
                        "price": 1_000_000,
                    }
                },
                "teams": {"1": {"id": 1, "name": "Barcelona"}},
            }
        },
    }


# ============================================================
# LA REGLA, AISLADA
# ============================================================


def test_el_respaldo_de_esta_jornada_si_se_sirve() -> None:
    r = ff.stale_fallback(_tablero(4), 4, 1800, "FF no contesto.")
    assert (r["cache"]["status"] == "STALE_FALLBACK"), (
        "el tablero de hoy sigue valiendo aunque sea de hace un rato"
    )
    assert len(r["players"]) == 1, "y con sus jugadores dentro"


def test_el_respaldo_de_otra_jornada_no_se_sirve() -> None:
    r = ff.stale_fallback(_tablero(3), 4, 1800, "FF no contesto.")
    assert r["cache"]["status"] == "STALE_WRONG_MATCHDAY", (
        "un tablero de la 3 no responde por la 4"
    )
    assert r["players"] == [], (
        "y no se sirven sus jugadores: eso es lo que costo el 16/08"
    )
    assert "jornada 3" in r["cache"]["error"], "se dice de que jornada era"
    assert "4" in r["cache"]["error"], "y en cual estamos"


def test_el_rechazo_conserva_la_jornada_real_del_tablero() -> None:
    """Escribir aqui la jornada de hoy seria disfrazarlo de bueno."""
    r = ff.stale_fallback(_tablero(3), 4, 1800, "FF no contesto.")
    assert r["matchday"] == 3, "la jornada que dice el tablero es la suya"
    assert r["requested_matchday"] == 4, "y aparte, la que se pedia"


def test_un_tablero_sin_jornada_no_se_da_por_bueno() -> None:
    sin_jornada = _tablero(4)
    sin_jornada["matchday"] = None
    r = ff.stale_fallback(sin_jornada, 4, 1800, "FF no contesto.")
    assert r["cache"]["status"] == "STALE_WRONG_MATCHDAY", (
        "sin jornada no se sabe de que jornada es: no vale"
    )


def test_el_tipo_no_decide_una_jornada() -> None:
    """Un "4" de JSON y un 4 de Python son la misma jornada."""
    texto = _tablero(4)
    texto["matchday"] = "4"
    r = ff.stale_fallback(texto, 4, 1800, "FF no contesto.")
    assert r["cache"]["status"] == "STALE_FALLBACK", (
        "rechazar por el tipo tiraria un tablero bueno"
    )


# ============================================================
# LAS DOS VIAS DE RESPALDO, DE VERDAD
# ============================================================


def _con_tablero_en_disco(tablero: dict, funcion):
    original = ff.BOARD_FILE
    with tempfile.TemporaryDirectory() as carpeta:
        ff.BOARD_FILE = Path(carpeta) / "board.json"
        ff.BOARD_FILE.write_text(
            json.dumps(tablero, ensure_ascii=False), encoding="utf-8"
        )
        try:
            return funcion()
        finally:
            ff.BOARD_FILE = original


def test_via_sin_objetivos_rechaza_otra_jornada() -> None:
    """Snapshot sin plantilla ni mercado, y cache de la jornada de antes."""
    r = _con_tablero_en_disco(
        _tablero(3),
        lambda: ff.refresh_board({}, 4),
    )
    assert r["cache"]["status"] == "STALE_WRONG_MATCHDAY", (
        r["cache"]["status"]
    )
    assert r["players"] == [], "sin jugadores de la semana pasada"


def test_via_sin_objetivos_conserva_la_jornada_buena() -> None:
    r = _con_tablero_en_disco(
        _tablero(4),
        lambda: ff.refresh_board({}, 4),
    )
    assert r["cache"]["status"] == "STALE_FALLBACK", r["cache"]["status"]
    assert len(r["players"]) == 1, (
        "un snapshot roto no puede tirar el tablero bueno de hoy"
    )


def test_via_scrapeo_en_blanco_rechaza_otra_jornada() -> None:
    """FF contesta, no empareja a nadie, y la cache es de otra jornada."""

    fetch_original = ff.fetch
    absences_original = ff.load_absences

    ff.fetch = lambda session, url: (_ for _ in ()).throw(
        RuntimeError("FF caido")
    )
    ff.load_absences = lambda session, matchday: ({}, {})

    try:
        r = _con_tablero_en_disco(
            _tablero(3),
            lambda: ff.refresh_board(_snapshot_con_objetivo(), 4),
        )
    finally:
        ff.fetch = fetch_original
        ff.load_absences = absences_original

    assert r["cache"]["status"] == "STALE_WRONG_MATCHDAY", (
        r["cache"]["status"]
    )
    assert r["players"] == [], "no se rellena la 4 con el pronostico de la 3"


def test_via_scrapeo_en_blanco_conserva_la_jornada_buena() -> None:
    fetch_original = ff.fetch
    absences_original = ff.load_absences

    ff.fetch = lambda session, url: (_ for _ in ()).throw(
        RuntimeError("FF caido")
    )
    ff.load_absences = lambda session, matchday: ({}, {})

    try:
        r = _con_tablero_en_disco(
            # Caducado a proposito: si estuviera fresco saldria HIT
            # y no se probaria el respaldo.
            _tablero(4, edad_minutos=60 * 24),
            lambda: ff.refresh_board(_snapshot_con_objetivo(), 4),
        )
    finally:
        ff.fetch = fetch_original
        ff.load_absences = absences_original

    assert r["cache"]["status"] == "STALE_FALLBACK", r["cache"]["status"]
    assert len(r["players"]) == 1, (
        "que FF se caiga no puede borrar el tablero bueno de hoy"
    )


def test_la_via_hit_sigue_exigiendo_la_jornada() -> None:
    """Lo que ya funcionaba y no se puede haber roto."""
    r = _con_tablero_en_disco(
        _tablero(3),
        lambda: ff.refresh_board({}, 4),
    )
    assert r["cache"]["status"] != "HIT", (
        "un tablero fresco de otra jornada nunca es un HIT"
    )


# ============================================================
# Y QUE EL AUDITOR LO VEA
# ============================================================


def _informe(jornada_hoy, jornada_tablero) -> dict:
    dashboard = {
        "summary": {"target_matchday": jornada_hoy},
        "lineup": {
            "starter_board_matchday": jornada_tablero,
            "starter_board_players": 59,
            "starter_cache_status": "STALE_FALLBACK",
            "starter_board_updated_at": "2026-08-30T10:00:00+00:00",
            "starter_data_total": 11,
            "starter_data_players": 11,
        },
    }
    informe = build_consistency_report(dashboard, {}, None)
    return next(
        c
        for c in informe["checks"]
        if c["key"] == "starter_board_matchday"
    )


def test_el_auditor_ve_la_jornada_cambiada() -> None:
    fila = _informe(4, 3)
    assert fila["ok"] is False, (
        "59 jugadores de la jornada 3 cuadran contando cabezas, "
        "y por eso hay que mirar la jornada"
    )
    assert fila["source"] == "CALENDARIO", (
        "este numero no sale de Biwenger, y el panel no puede decir "
        "que si"
    )
    assert "jornada 3" in fila["found_label"], "se dice cual encontro"


def test_el_auditor_pasa_con_la_jornada_correcta() -> None:
    assert _informe(4, 4)["ok"] is True, (
        "un tablero de la jornada que se juega no es un fallo"
    )


def test_el_auditor_no_se_traga_un_tablero_ausente() -> None:
    assert _informe(4, None)["ok"] is False, (
        "sin tablero no hay pronostico, y eso tambien se dice"
    )


def test_el_auditor_nunca_lanza() -> None:
    """Un panel que revienta deja al dueño sin ojos."""
    informe = build_consistency_report({}, {}, None)
    assert isinstance(informe, dict), "devuelve informe hasta con todo vacio"
    assert any(
        c["key"] == "starter_board_matchday" for c in informe["checks"]
    ), "y la fila de la jornada esta siempre"


TESTS = [
    test_el_respaldo_de_esta_jornada_si_se_sirve,
    test_el_respaldo_de_otra_jornada_no_se_sirve,
    test_el_rechazo_conserva_la_jornada_real_del_tablero,
    test_un_tablero_sin_jornada_no_se_da_por_bueno,
    test_el_tipo_no_decide_una_jornada,
    test_via_sin_objetivos_rechaza_otra_jornada,
    test_via_sin_objetivos_conserva_la_jornada_buena,
    test_via_scrapeo_en_blanco_rechaza_otra_jornada,
    test_via_scrapeo_en_blanco_conserva_la_jornada_buena,
    test_la_via_hit_sigue_exigiendo_la_jornada,
    test_el_auditor_ve_la_jornada_cambiada,
    test_el_auditor_pasa_con_la_jornada_correcta,
    test_el_auditor_no_se_traga_un_tablero_ausente,
    test_el_auditor_nunca_lanza,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"JORNADA DEL TABLERO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
