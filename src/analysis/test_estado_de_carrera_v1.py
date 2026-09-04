"""
El marcador de la temporada: bien calculado, y sin mandar.

SINTOMA

    Pepe no sabe que va cuarto. Nada en el codigo lee la
    clasificacion para decidir: pujaria igual siendo primero con
    veinte de ventaja que ultimo a cuarenta.

CAUSA

    No existia. Toda la maquinaria esta bien construida y juega a
    ciegas sobre el resultado.

CONSECUENCIA

    Esta guardia protege dos cosas, y la segunda es la que de
    verdad importa esta noche:

      1. Que las cuentas esten bien. Un marcador que miente es
         peor que no tener marcador.

      2. Que SIGA SIENDO UN OBSERVADOR. En cuanto un motor lo
         importe, deja de ser un termometro y pasa a decidir
         cuanto se puja, y eso no se hace de noche y sin el
         dueño delante.
"""

from __future__ import annotations

import ast

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.race_state import (
    build_race_state,
    count_finished_matchdays,
)


AHORA = datetime(2026, 9, 5, 2, 0, tzinfo=timezone.utc)


# ============================================================
# LA FOTO DE PRODUCCION DEL 04/09/2026
# ============================================================


def _managers() -> list:
    crudos = [
        (1, "Pollo17", 146, 69_410_000, False),
        (2, "Mex", 141, 52_310_000, False),
        (3, "Luismi_Haz", 136, 68_790_000, False),
        (4, "Pepe Bordalás", 133, 47_720_000, True),
        (5, "DiosMande", 109, 47_000_000, False),
        (6, "Prinzipote", 106, 54_210_000, False),
        (7, "Manzagool", 79, 51_020_000, False),
    ]

    return [
        {
            "user_id": 1000 + rank,
            "name": nombre,
            "rank": rank,
            "points": puntos,
            "team_value": valor,
            "squad_size": 14 if yo else 16,
            "is_current_user": yo,
        }
        for rank, nombre, puntos, valor, yo in crudos
    ]


def _squads(managers=None) -> dict:
    return {
        "available": True,
        "managers": managers if managers is not None else _managers(),
    }


def _calendario(jornadas: int = 38, jugadas: int = 3) -> dict:
    """
    Un calendario donde `jugadas` jornadas ya terminaron.

    Con aritmetica de fechas de verdad: la primera version de
    este fixture componia las cadenas a mano y generaba
    "2026-08-46", que `fromisoformat` rechaza en silencio. La
    jornada se descartaba y el test media otra cosa.
    """

    return {
        "matchdays": [
            {
                "matchday": n,
                "matches": [
                    {
                        "kickoff": (
                            (
                                AHORA
                                - timedelta(days=7 * (jugadas - n + 1))
                                if n <= jugadas
                                else AHORA
                                + timedelta(days=7 * (n - jugadas))
                            ).isoformat()
                        )
                    }
                ],
            }
            for n in range(1, jornadas + 1)
        ]
    }


# ============================================================
# 1. LAS CUENTAS
# ============================================================


def test_el_puesto_y_la_distancia() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    assert r["available"] is True
    assert r["position"] == 4, "va cuarto"
    assert r["points"] == 133, "con 133 puntos"
    assert r["leader_name"] == "Pollo17", "y el lider es Pollo17"
    assert r["leader_points"] == 146
    assert r["points_behind"] == 13, "a trece puntos"
    assert r["is_leader"] is False


def test_las_jornadas_que_quedan() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    assert r["matchdays_total"] == 38, "la temporada son 38"
    assert r["matchdays_played"] == 3, "tres terminadas"
    assert r["matchdays_remaining"] == 35, "y 35 por jugar"


def test_una_jornada_a_medias_no_cuenta_como_jugada() -> None:
    """
    Sus puntos todavia se estan repartiendo. Contarla adelantaria
    la temporada una jornada y encogeria el ritmo necesario.
    """

    calendario = {
        "matchdays": [
            {"matchday": 1, "matches": [
                {"kickoff": "2026-08-15T19:00:00+00:00"},
            ]},
            {"matchday": 2, "matches": [
                {"kickoff": "2026-09-04T19:00:00+00:00"},   # terminado
                {"kickoff": "2026-09-06T19:00:00+00:00"},   # sin jugar
            ]},
        ]
    }

    jugadas, total = count_finished_matchdays(calendario, now=AHORA)

    assert jugadas == 1, "la 2 esta a medias: no cuenta"
    assert total == 2


def test_el_ritmo_necesario() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    # 13 puntos / 35 jornadas
    assert abs(r["required_pace"] - 13 / 35) < 0.001, (
        "distancia entre jornadas restantes, sin mas misterio"
    )


def test_la_exigencia_mide_contra_una_jornada_normal() -> None:
    """
    0,37 puntos sueltos no significan nada. Contra los 44 que
    Pepe saca por jornada, son un 0,8 %.
    """

    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    assert abs(r["points_per_matchday"] - 133 / 3) < 0.01, (
        "puntos entre jornadas jugadas"
    )
    assert abs(
        r["required_pace_share"] - (13 / 35) / (133 / 3)
    ) < 0.0001
    assert r["urgency"] == "COMODA", (
        "menos de un 1 % de una jornada: la distancia es ruido, y "
        "decir otra cosa seria dramatizar un numero pequeño"
    )


def test_la_brecha_de_plantilla() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    assert r["team_value"] == 47_720_000
    assert r["leader_team_value"] == 69_410_000
    assert r["value_gap_to_leader"] == 21_690_000, (
        "21,69 M por debajo del lider: la brecha de verdad"
    )
    assert r["league_average_value"] == round(
        sum(m["team_value"] for m in _managers()) / 7
    )


def test_la_frase_que_lee_el_dueño() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    frase = r["headline"]

    assert "4º" in frase, "el puesto"
    assert "13 puntos" in frase, "la distancia"
    assert "35 jornadas" in frase, "lo que queda"
    assert "0,37" in frase, "el ritmo, con coma decimal: lo lee una persona"
    assert "21,7 M menos" in frase, "y la brecha de plantilla"


# ============================================================
# 2. LOS CASOS FEOS
# ============================================================

def test_con_todos_a_cero_no_hay_carrera() -> None:
    """
    SALIO CON DATOS DE VERDAD (05/09/2026).

    Con el snapshot local del 17/08 -temporada sin empezar, los
    siete a cero- la frase salia "Vas 7º, a 0 puntos" con
    urgencia LIDER: dos cosas contradictorias en el mismo
    renglon. `max()` con empate devuelve el primero de la lista,
    y ahi nos coronaba.
    """

    managers = _managers()
    for m in managers:
        m["points"] = 0

    r = build_race_state(
        _squads(managers), calendar=_calendario(), now=AHORA
    )

    assert r["season_started"] is False, "nadie ha puntuado"
    assert r["is_leader"] is False, (
        "ir empatado a cero con seis mas no es ir primero"
    )
    assert r["urgency"] == "SIN_DATOS", (
        "decir COMODA aqui seria tranquilizar por falta de datos"
    )
    assert "no ha empezado" in r["headline"]


def test_empatado_a_puntos_no_es_ir_primero() -> None:
    managers = _managers()
    for m in managers:
        m["is_current_user"] = m["name"] == "Pollo17"
    # Mex iguala al lider.
    for m in managers:
        if m["name"] == "Mex":
            m["points"] = 146

    r = build_race_state(
        _squads(managers), calendar=_calendario(), now=AHORA
    )

    assert r["is_leader"] is False, (
        "empatado arriba no es ir por delante"
    )
    assert r["points_ahead"] is None, "y no hay ventaja que contar"


def test_la_frase_esta_bien_puntuada() -> None:
    """
    El `.replace(".", ",")` de la coma decimal se comia tambien
    el punto que separaba las dos frases: salia "0,00 por
    jornada, Tu plantilla vale...".
    """

    frase = build_race_state(
        _squads(), calendar=_calendario(), now=AHORA
    )["headline"]

    assert ", Tu plantilla" not in frase, (
        f"punto convertido en coma: {frase}"
    )
    assert ". Tu plantilla" in frase, frase
    assert frase.endswith("."), frase




def test_ir_primero_no_es_ir_a_menos_cero() -> None:
    managers = _managers()
    for m in managers:
        m["is_current_user"] = m["name"] == "Pollo17"

    r = build_race_state(
        _squads(managers), calendar=_calendario(), now=AHORA
    )

    assert r["is_leader"] is True
    assert r["points_behind"] == 0, "el lider no va por detras de nadie"
    assert r["points_ahead"] == 5, "y le saca 5 al segundo"
    assert r["urgency"] == "LIDER"
    assert "Vas 1º" in r["headline"]


def test_sin_calendario_no_se_inventa_el_ritmo() -> None:
    """
    Ausencia de dato != dato. Un ritmo calculado sobre 38
    jornadas fijas seria un numero con pinta de medida.
    """

    r = build_race_state(_squads(), calendar={}, now=AHORA)

    assert r["available"] is True, "el puesto y la distancia si se saben"
    assert r["points_behind"] == 13
    assert r["matchdays_remaining"] is None, "las jornadas no"
    assert r["required_pace"] is None, "ni el ritmo"
    assert r["urgency"] == "SIN_DATOS", "y no se clasifica a ciegas"
    assert r["calendar_available"] is False
    assert r["calendar_reason"], "se dice por que falta"
    assert "sin calendario" in r["headline"].lower()


def test_sin_clasificacion_se_dice_que_no_hay() -> None:
    r = build_race_state({"available": True, "managers": []})

    assert r["available"] is False
    assert r["reason"], "y con motivo"


def test_sin_saber_quienes_somos_no_hay_carrera() -> None:
    managers = _managers()
    for m in managers:
        m["is_current_user"] = False

    r = build_race_state(_squads(managers))

    assert r["available"] is False, (
        "medir la distancia de otro y llamarla nuestra seria peor "
        "que no medirla"
    )


def test_el_lider_es_el_de_mas_puntos_no_el_primero_de_la_lista() -> None:
    """`rank` viene de fuera. Los puntos los contamos nosotros."""

    managers = _managers()
    managers[0]["points"] = 10          # el "rank 1" va ultimo de verdad

    r = build_race_state(
        _squads(managers), calendar=_calendario(), now=AHORA
    )

    assert r["leader_name"] == "Mex", f"salio {r['leader_name']}"
    assert r["points_behind"] == 141 - 133


def test_no_quedan_jornadas() -> None:
    r = build_race_state(
        _squads(),
        calendar=_calendario(jornadas=38, jugadas=38),
        now=AHORA,
    )

    assert r["matchdays_remaining"] == 0
    assert r["required_pace"] is None, "no se divide entre cero"
    assert r["urgency"] == "FUERA_DE_ALCANCE", (
        "sin jornadas por delante no hay nada que recuperar"
    )


def test_nunca_lanza() -> None:
    """Un termometro roto no puede tumbar la telemetria."""

    for basura in (None, {}, {"managers": None}, {"managers": "no"},
                   {"managers": [None, 3, "x"]}):
        r = build_race_state(basura)
        assert isinstance(r, dict), f"revento con {basura!r}"
        assert "available" in r


# ============================================================
# 3. QUE SIGA SIN MANDAR
# ============================================================


MOTORES = [
    "src/analysis/acquisition_valuation.py",
    "src/analysis/speculation_engine.py",
    "src/analysis/rival_bid_model.py",
    "src/analysis/acquisition_budget.py",
    "src/analysis/decision_orchestrator.py",
    "src/analysis/lineup_engine.py",
    "src/analysis/offer_decision_engine.py",
    "src/analysis/sales_analyzer.py",
    "src/autopilot.py",
    "src/v10_full_autonomous_live.py",
]


def test_ningun_motor_lee_el_marcador() -> None:
    """
    LA GUARDIA QUE DE VERDAD IMPORTA.

    En cuanto un motor importe esto, el marcador deja de ser un
    termometro y pasa a decidir cuanto se puja. Ese cambio se
    toma con el dueño delante, no de madrugada.
    """

    culpables = []

    for ruta in MOTORES:

        fichero = Path(ruta)

        if not fichero.exists():
            continue

        if "race_state" in fichero.read_text(encoding="utf-8"):
            culpables.append(ruta)

    assert not culpables, (
        f"el estado de carrera ha entrado en una ruta de decision: "
        f"{culpables}. Es FASE OBSERVADOR: se calcula, se pinta, y "
        f"no manda."
    )


def test_el_marcador_no_importa_motores() -> None:
    """
    Y al reves: si empieza a tirar de los motores, deja de ser
    barato y empieza a poder tumbarlos.
    """

    arbol = ast.parse(
        Path("src/analysis/race_state.py").read_text(encoding="utf-8")
    )

    modulos = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulos.append(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)

    for modulo in modulos:
        assert not modulo.startswith("src."), (
            f"el marcador importa {modulo}: solo tiene que leer "
            f"numeros, no arrastrar el sistema"
        )


def test_el_dashboard_lo_publica() -> None:
    """Calcularlo y no publicarlo lo dejaria en un fichero muerto."""

    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert "build_race_state" in fuente, (
        "el dashboard ha dejado de construir el estado de carrera"
    )
    assert '"race": race' in fuente, (
        "el estado de carrera no llega a `status.json`"
    )


def test_se_declara_observador_en_el_propio_json() -> None:
    r = build_race_state(_squads(), calendar=_calendario(), now=AHORA)

    assert r["observer_only"] is True, (
        "quien abra el JSON tiene que ver que esto no manda, sin "
        "ir a leer el codigo"
    )


TESTS = [
    test_el_puesto_y_la_distancia,
    test_las_jornadas_que_quedan,
    test_una_jornada_a_medias_no_cuenta_como_jugada,
    test_el_ritmo_necesario,
    test_la_exigencia_mide_contra_una_jornada_normal,
    test_la_brecha_de_plantilla,
    test_la_frase_que_lee_el_dueño,
    test_ir_primero_no_es_ir_a_menos_cero,
    test_con_todos_a_cero_no_hay_carrera,
    test_empatado_a_puntos_no_es_ir_primero,
    test_la_frase_esta_bien_puntuada,
    test_sin_calendario_no_se_inventa_el_ritmo,
    test_sin_clasificacion_se_dice_que_no_hay,
    test_sin_saber_quienes_somos_no_hay_carrera,
    test_el_lider_es_el_de_mas_puntos_no_el_primero_de_la_lista,
    test_no_quedan_jornadas,
    test_nunca_lanza,
    test_ningun_motor_lee_el_marcador,
    test_el_marcador_no_importa_motores,
    test_el_dashboard_lo_publica,
    test_se_declara_observador_en_el_propio_json,
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
    print(f"ESTADO DE CARRERA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
