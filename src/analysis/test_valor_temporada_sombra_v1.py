"""
La valoracion a temporada: bien calculada, al lado, y sin mandar.

SINTOMA

    Todo se valora a tres dias (`DEFAULT_SPECULATION_HORIZON = 3`)
    o a un ciclo. Exposito -Clave, 90 % titular, 196 puntos
    esperados- se rechaza porque "como especulacion rinde un
    0,59 % y se exige al menos un 3 %". Ni siquiera se esta
    mirando el futbol.

CAUSA

    Tres dias es el horizonte correcto para una reventa y el
    equivocado para un fichaje. Un jugador que da 6 puntos por
    jornada durante 30 jornadas vale 180 puntos; lo que valga su
    reventa el jueves es otra cosa.

CONSECUENCIA

    Esta guardia protege cuatro cosas:

      1. Que la cuenta este bien y no cuente dos veces los
         ajustes que `expected_points` ya trae dentro.
      2. Que sin alguno de los tres datos NO se invente un valor.
      3. Que el numero salga acompañado de sus dos puntos flacos:
         un candidato sin pronostico y uno que FF da suplente
         valen mucho menos de lo que parece a temporada.
      4. Que siga siendo SOMBRA. Ni sustituye a la valoracion
         vieja, ni la toca, ni la lee ningun motor.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.season_horizon_shadow import (
    SEASON_MATCHDAYS,
    annotate_rows,
    build_season_horizon_shadow,
    season_value,
)


TARIFA = 21_758          # el precio del punto medido, 04/09/2026


def _fila(**campos) -> dict:
    base = {
        "id": 1,
        "name": "Fulano",
        "market_price": 1_000_000,
        "our_value": 1_010_000,
        "expected_points": 76,          # dos puntos por jornada
        "starter_probability": 85.0,
        "starter_consensus": "STARTER",
        "intent": "SPECULATION",
    }
    base.update(campos)
    return base


# ============================================================
# 1. LA CUENTA
# ============================================================


def test_la_cuenta_es_puntos_por_jornada_por_lo_que_queda() -> None:
    r = season_value(76, 35, TARIFA, market_price=1_000_000)

    assert r["available"] is True
    assert r["points_per_matchday"] == 2.0, (
        "76 puntos de temporada entre 38 jornadas son 2 por jornada"
    )
    assert r["season_points_remaining"] == 70.0, "2 x 35"
    assert r["season_value"] == round(70.0 * TARIFA), (
        "y esos 70 puntos a precio de mercado"
    )


def test_los_puntos_son_de_temporada_completa() -> None:
    """
    `expected_points` sale de `pointsLastSeason`: 38 jornadas. Si
    se tratara como puntos por jornada, el valor saldria 38 veces
    mas grande.
    """

    assert SEASON_MATCHDAYS == 38

    r = season_value(38, 38, TARIFA)

    assert r["points_per_matchday"] == 1.0
    assert r["season_points_remaining"] == 38.0, (
        "con la temporada entera por delante, valen lo que valen"
    )


def test_menos_jornadas_valen_menos() -> None:
    mucho = season_value(76, 35, TARIFA)["season_value"]
    poco = season_value(76, 5, TARIFA)["season_value"]

    assert poco < mucho, "el mismo jugador vale menos en abril"
    assert abs(poco - mucho * 5 / 35) < 2, "y baja en proporcion"


def test_el_coste_por_punto() -> None:
    r = season_value(76, 35, TARIFA, market_price=1_400_000)

    assert r["cost_per_point"] == round(1_400_000 / 70.0), (
        "lo que cuesta cada punto que queda por dar"
    )
    assert r["beats_market_rate"] is True, (
        "20.000 por punto contra 21.758 que paga el mercado: es "
        "negocio, y se dice"
    )


def test_caro_por_punto_no_es_negocio() -> None:
    r = season_value(76, 35, TARIFA, market_price=3_000_000)

    assert r["cost_per_point"] > TARIFA
    assert r["beats_market_rate"] is False


def test_no_se_aplican_dos_veces_los_ajustes() -> None:
    """
    EL ERROR FACIL.

    `expected_points` YA viene multiplicado por jerarquia,
    probabilidad de titular y ausencias. Volver a escalarlo aqui
    penalizaria dos veces al mismo jugador.

    Se comprueba por donde de verdad se puede romper: la cuenta
    depende SOLO de los puntos que se le pasan, sean del jugador
    que sean.
    """

    a = season_value(100, 35, TARIFA)["season_value"]
    b = season_value(50, 35, TARIFA)["season_value"]

    assert a == 2 * b, (
        "el valor es lineal en los puntos esperados: si aqui se "
        "aplicase otro factor, dejaria de serlo"
    )


# ============================================================
# 2. SIN DATOS NO SE INVENTA UN VALOR
# ============================================================


def test_sin_jornadas_restantes_no_hay_valor() -> None:
    r = season_value(76, None, TARIFA)

    assert r["available"] is False
    assert r["season_value"] is None
    assert "jornadas restantes" in r["reason"]


def test_sin_precio_del_punto_no_hay_valor() -> None:
    r = season_value(76, 35, 0)

    assert r["season_value"] is None
    assert "precio del punto" in r["reason"]


def test_sin_puntos_esperados_no_hay_valor() -> None:
    r = season_value(0, 35, TARIFA)

    assert r["season_value"] is None
    assert "puntos esperados" in r["reason"]


def test_no_se_divide_entre_cero_jornadas() -> None:
    r = season_value(76, 0, TARIFA, market_price=1_000_000)

    assert r["season_value"] == 0, "sin jornadas por delante no da nada"
    assert r["cost_per_point"] is None, "y no se divide entre cero"


# ============================================================
# 3. EL NUMERO SALE CON SUS PEROS
# ============================================================


def test_sin_pronostico_se_avisa() -> None:
    """
    El caso Gustavo Puerta: 156 esperados = 156 en bruto, sin un
    solo descuento por titularidad. El valor de temporada hereda
    ese agujero y tiene que decirlo.
    """

    fila = annotate_rows(
        [_fila(starter_probability=None, starter_consensus=None)],
        35,
        TARIFA,
    )[0]

    assert fila["season_horizon"]["starter_known"] is False
    assert "mejor caso" in fila["season_horizon"]["caveat"], (
        "un valor sin descuento por titularidad es el mejor caso, "
        "no el esperado, y quien lo lea tiene que saberlo"
    )


def test_un_suplente_barato_sale_marcado() -> None:
    """
    Los tres 'chollos por punto' de la foto del 04/09 -Calero,
    Ruben Sanchez, Jon Pacheco- son los tres BENCH. El pronostico
    semanal pesa 0,15, asi que conservan casi todos sus puntos.
    """

    fila = annotate_rows(
        [_fila(starter_probability=0.0, starter_consensus="BENCH")],
        35,
        TARIFA,
    )[0]

    assert fila["season_horizon"]["starter_known"] is True
    assert "suplente" in fila["season_horizon"]["caveat"]
    assert "0,15" in fila["season_horizon"]["caveat"], (
        "y se dice por que conserva los puntos, no solo que los "
        "conserva"
    )


def test_un_titular_no_lleva_pero() -> None:
    fila = annotate_rows([_fila()], 35, TARIFA)[0]

    assert fila["season_horizon"]["caveat"] is None, (
        "poner un pero a todo es no poner ninguno"
    )


# ============================================================
# 4. ES SOMBRA: NI SUSTITUYE, NI TOCA, NI MANDA
# ============================================================


def test_no_se_toca_la_fila_original() -> None:
    original = _fila()
    copia = dict(original)

    annotate_rows([original], 35, TARIFA)

    assert original == copia, (
        "el tablero que decide tiene que seguir siendo bit a bit "
        "el mismo"
    )


def test_la_valoracion_vieja_viaja_al_lado() -> None:
    fila = annotate_rows([_fila(our_value=1_010_000)], 35, TARIFA)[0]

    assert fila["our_value"] == 1_010_000, "la de siempre, intacta"
    assert fila["season_horizon"]["current_value"] == 1_010_000, (
        "y repetida dentro, para poder comparar sin restar a mano"
    )
    assert fila["season_horizon"]["difference"] == (
        fila["season_horizon"]["season_value"] - 1_010_000
    )


def test_no_se_ha_tocado_la_valoracion_de_verdad() -> None:
    """
    Un campo nuevo en `acquisition_valuation.py` habria sido mas
    corto y habria metido la sombra dentro de la ruta que decide.
    """

    fuente = Path("src/analysis/acquisition_valuation.py").read_text(
        encoding="utf-8"
    )

    assert "season_horizon" not in fuente, (
        "la valoracion a temporada ha entrado en la valoracion que "
        "decide"
    )
    assert "DEFAULT_SPECULATION_HORIZON = 3" in fuente, (
        "el horizonte de la valoracion vieja ha cambiado: eso es "
        "cambiar decisiones, y esta noche no tocaba"
    )


MOTORES = [
    "src/analysis/acquisition_valuation.py",
    "src/analysis/acquisition_board.py",
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


def test_ningun_motor_lee_la_sombra() -> None:
    culpables = [
        ruta
        for ruta in MOTORES
        if Path(ruta).exists()
        and "season_horizon_shadow" in Path(ruta).read_text(
            encoding="utf-8"
        )
    ]

    assert not culpables, (
        f"la valoracion a temporada ha entrado en una ruta de "
        f"decision: {culpables}. Es una segunda opinion escrita al "
        f"margen, no un motor."
    )


def test_la_sombra_no_arrastra_el_sistema() -> None:
    arbol = ast.parse(
        Path("src/analysis/season_horizon_shadow.py").read_text(
            encoding="utf-8"
        )
    )

    modulos = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulos.append(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)

    for modulo in modulos:
        assert not modulo.startswith("src."), (
            f"la sombra importa {modulo}: solo tiene que hacer una "
            f"multiplicacion sobre filas ya calculadas"
        )


def test_el_dashboard_lo_publica() -> None:
    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert '"season_horizon": season_horizon' in fuente, (
        "la valoracion a temporada no llega a `status.json`"
    )

    # Y con sus tres entradas ya calculadas: si se construyera
    # antes que `acquisition` o `points_market`, el try/except se
    # lo tragaria en silencio y el bloque saldria vacio para
    # siempre.
    assert fuente.index("acquisition = build_acquisition_board(") < fuente.index(
        "season_horizon = build_season_horizon_shadow("
    ), "se construye antes de tener el tablero"
    assert fuente.index("points_market = calibrate_points_market(") < fuente.index(
        "season_horizon = build_season_horizon_shadow("
    ), "se construye antes de tener el precio del punto"


def test_se_declara_observador_en_el_propio_json() -> None:
    r = build_season_horizon_shadow(
        {"targets": [_fila()]},
        {"matchdays_remaining": 35},
        {"rate_median": TARIFA},
    )

    assert r["observer_only"] is True
    assert r["available"] is True
    assert r["candidates_valued"] == 1


def test_nunca_lanza() -> None:
    for basura in (None, {}, {"targets": None}, {"targets": "no"},
                   {"targets": [None, 3]}):
        r = build_season_horizon_shadow(basura, None, None)
        assert isinstance(r, dict), f"revento con {basura!r}"
        assert r["available"] is False
        assert r["reason"], "y dice por que no hay nada"


TESTS = [
    test_la_cuenta_es_puntos_por_jornada_por_lo_que_queda,
    test_los_puntos_son_de_temporada_completa,
    test_menos_jornadas_valen_menos,
    test_el_coste_por_punto,
    test_caro_por_punto_no_es_negocio,
    test_no_se_aplican_dos_veces_los_ajustes,
    test_sin_jornadas_restantes_no_hay_valor,
    test_sin_precio_del_punto_no_hay_valor,
    test_sin_puntos_esperados_no_hay_valor,
    test_no_se_divide_entre_cero_jornadas,
    test_sin_pronostico_se_avisa,
    test_un_suplente_barato_sale_marcado,
    test_un_titular_no_lleva_pero,
    test_no_se_toca_la_fila_original,
    test_la_valoracion_vieja_viaja_al_lado,
    test_no_se_ha_tocado_la_valoracion_de_verdad,
    test_ningun_motor_lee_la_sombra,
    test_la_sombra_no_arrastra_el_sistema,
    test_el_dashboard_lo_publica,
    test_se_declara_observador_en_el_propio_json,
    test_nunca_lanza,
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
    print(f"VALOR TEMPORADA SOMBRA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
