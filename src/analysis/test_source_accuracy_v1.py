"""
Libro de aciertos por fuente de titularidad.

Comprueba que la puntuacion Brier hace lo que prometemos:
premia acertar con conviccion, castiga fuerte equivocarse con
conviccion, y deja neutro al que se abstiene.

Ejecutar:
    python -m src.analysis.test_source_accuracy_v1
"""

from src.intelligence.source_accuracy_ledger import (
    NEUTRAL_BRIER,
    brier,
    empty_ledger,
    infer_outcomes,
    record_predictions,
    score_matchday,
    source_weights,
)


# ============================================================
# BRIER
# ============================================================

def test_brier_premia_acertar_con_conviccion() -> None:
    acierto_seguro = brier(92.2, 1)
    fallo_seguro = brier(92.2, 0)
    abstencion = brier(50.0, 1)

    assert acierto_seguro < 0.01, acierto_seguro
    assert fallo_seguro > 0.8, fallo_seguro
    assert abs(abstencion - 0.25) < 0.001

    assert acierto_seguro < abstencion < fallo_seguro, (
        "El orden debe ser: acertar seguro < abstenerse < "
        "fallar seguro."
    )

    print(
        f"  OK  92%->acierto {acierto_seguro:.3f} | "
        f"50% {abstencion:.3f} | 92%->fallo {fallo_seguro:.3f}"
    )


def test_abstenerse_no_es_equivocarse() -> None:
    """
    El motivo de elegir Brier: decir 50% puntua igual juegue o
    no. Si penalizasemos la abstencion, las fuentes tendrian
    incentivo a farolear.
    """
    assert brier(50.0, 1) == brier(50.0, 0)

    print("  OK  decir 50% puntua igual gane o pierda")


# ============================================================
# REGISTRO
# ============================================================

def _board() -> dict:
    return {
        "players": [
            {
                "player_id": 1599,
                "player_name": "Jonny Castro",
                "team": "Alaves",
                "consensus": "UNCERTAIN",
                "starter_probability": 50.0,
                "sources": {
                    "JORNADA_PERFECTA": {"probability": 92.2},
                    "FUTBOLFANTASY": {"probability": 50.0},
                    "ANALITICA_FANTASY": {"probability": 25.0},
                },
            },
            {
                "player_id": 41606,
                "player_name": "Mangala",
                "team": "Everton",
                "consensus": "UNCERTAIN",
                "starter_probability": 50.0,
                "sources": {
                    "JORNADA_PERFECTA": {"probability": 92.2},
                    "FUTBOLFANTASY": {"probability": 50.0},
                    "ANALITICA_FANTASY": {"probability": 50.0},
                },
            },
            {
                "player_id": 26271,
                "player_name": "Yamal",
                "team": "Barcelona",
                "consensus": "STARTER",
                "starter_probability": 92.2,
                "sources": {
                    "JORNADA_PERFECTA": {"probability": 92.2},
                    "FUTBOLFANTASY": {"probability": 90.0},
                    "ANALITICA_FANTASY": {"probability": 90.0},
                },
            },
        ],
    }


def test_la_abstencion_no_se_registra() -> None:
    board = {
        "players": [
            {
                "player_id": 1,
                "player_name": "Sin datos",
                "sources": {
                    "JORNADA_PERFECTA": {"probability": 92.2},
                    "ANALITICA_FANTASY": {"probability": None},
                },
            },
        ],
    }

    ledger = record_predictions(
        board=board,
        matchday=1,
        ledger=empty_ledger(),
    )

    fuentes = (
        ledger["matchdays"]["1"]["predictions"]["1"]["sources"]
    )

    assert "ANALITICA_FANTASY" not in fuentes, (
        "Una fuente sin dato no debe registrarse: si no, se le "
        "puntuaria una prediccion que nunca hizo."
    )
    assert "JORNADA_PERFECTA" in fuentes

    print("  OK  una fuente que se abstiene no queda registrada")


def test_no_se_pisa_una_jornada_ya_puntuada() -> None:
    ledger = record_predictions(
        board=_board(),
        matchday=1,
        ledger=empty_ledger(),
    )
    ledger = score_matchday(
        matchday=1,
        outcomes={"1599": {"played": 1}},
        ledger=ledger,
    )

    antes = ledger["matchdays"]["1"]["per_source"]

    ledger = record_predictions(
        board={"players": []},
        matchday=1,
        ledger=ledger,
    )

    assert ledger["matchdays"]["1"]["per_source"] == antes, (
        "REGRESION: se sobrescribio una jornada ya puntuada."
    )

    print("  OK  una jornada puntuada no se sobrescribe")


# ============================================================
# EL CASO REAL DE ANOCHE
# ============================================================

def test_jornada_1_jp_gana_a_las_otras_dos() -> None:
    """
    Jonny Castro y Mangala salieron de inicio. JP dijo 92%,
    FutbolFantasy 50% y Analitica 25% / 50%.

    JP debe salir claramente mejor.
    """
    ledger = record_predictions(
        board=_board(),
        matchday=1,
        ledger=empty_ledger(),
    )

    ledger = score_matchday(
        matchday=1,
        outcomes={
            "1599": {"played": 1},
            "41606": {"played": 1},
            "26271": {"played": 1},
        },
        ledger=ledger,
    )

    por_fuente = ledger["matchdays"]["1"]["per_source"]

    jp = por_fuente["JORNADA_PERFECTA"]["mean_brier"]
    ff = por_fuente["FUTBOLFANTASY"]["mean_brier"]
    af = por_fuente["ANALITICA_FANTASY"]["mean_brier"]

    assert jp < ff, f"JP {jp} deberia batir a FF {ff}"
    assert jp < af, f"JP {jp} deberia batir a AF {af}"
    assert af > ff, (
        f"Analitica {af} dijo 25% en un titular: debe puntuar "
        f"peor que FutbolFantasy {ff}, que solo se abstuvo."
    )

    print(
        f"  OK  JP {jp:.3f} < FF {ff:.3f} < AF {af:.3f} "
        f"(menor es mejor)"
    )


def test_solo_disputados() -> None:
    """
    Que las tres acierten con Yamal no informa de nada.
    """
    ledger = record_predictions(
        board=_board(),
        matchday=1,
        ledger=empty_ledger(),
    )

    ledger = score_matchday(
        matchday=1,
        outcomes={
            "1599": {"played": 1},
            "41606": {"played": 1},
            "26271": {"played": 1},
        },
        ledger=ledger,
        only_contested=True,
    )

    detalle = ledger["matchdays"]["1"]["detail"]

    assert "26271" not in detalle, (
        "Yamal no es un caso disputado: las tres fuentes "
        "coincidian."
    )
    assert "1599" in detalle

    print(
        f"  OK  con only_contested quedan "
        f"{len(detalle)} casos, sin los unanimes"
    )


# ============================================================
# PESOS
# ============================================================

def test_sin_datos_reparto_equitativo() -> None:
    resumen = source_weights(empty_ledger())
    pesos = list(resumen["weights"].values())

    assert resumen["scored_matchdays"] == 0
    assert all(
        abs(peso - pesos[0]) < 0.0001
        for peso in pesos
    ), f"Sin evidencia los pesos deben ser iguales: {pesos}"

    print("  OK  sin datos, todas las fuentes pesan igual")


def test_una_jornada_apenas_mueve_los_pesos() -> None:
    """
    La cautela principal: no aprenderse el ruido.
    """
    ledger = record_predictions(
        board=_board(),
        matchday=1,
        ledger=empty_ledger(),
    )
    ledger = score_matchday(
        matchday=1,
        outcomes={
            "1599": {"played": 1},
            "41606": {"played": 1},
            "26271": {"played": 1},
        },
        ledger=ledger,
    )

    resumen = source_weights(ledger)
    pesos = resumen["weights"]

    equitativo = 1.0 / 3.0
    desvio = max(
        abs(peso - equitativo)
        for peso in pesos.values()
    )

    assert desvio < 0.08, (
        f"Con una sola jornada los pesos se han movido {desvio:.3f}. "
        f"Demasiado: seria aprenderse el ruido."
    )

    assert (
        pesos["JORNADA_PERFECTA"]
        > pesos["ANALITICA_FANTASY"]
    ), "JP acerto y Analitica fallo: el orden deberia notarse."

    print(
        f"  OK  una jornada mueve los pesos solo {desvio:.4f}, "
        f"pero JP ya va por delante"
    )


def test_muchas_jornadas_si_separan() -> None:
    ledger = empty_ledger()

    for jornada in range(1, 13):
        ledger = record_predictions(
            board=_board(),
            matchday=jornada,
            ledger=ledger,
        )
        ledger = score_matchday(
            matchday=jornada,
            outcomes={
                "1599": {"played": 1},
                "41606": {"played": 1},
                "26271": {"played": 1},
            },
            ledger=ledger,
        )

    resumen = source_weights(ledger)
    pesos = resumen["weights"]

    assert resumen["scored_matchdays"] == 12
    assert (
        pesos["JORNADA_PERFECTA"]
        > pesos["FUTBOLFANTASY"]
        > pesos["ANALITICA_FANTASY"]
    ), f"Con 12 jornadas el orden debe ser claro: {pesos}"

    print(
        f"  OK  con 12 jornadas: JP "
        f"{pesos['JORNADA_PERFECTA']:.3f} > FF "
        f"{pesos['FUTBOLFANTASY']:.3f} > AF "
        f"{pesos['ANALITICA_FANTASY']:.3f}"
    )


# ============================================================
# VERDAD SOBRE EL TERRENO
# ============================================================

def _snapshot(jugadores: list) -> dict:
    return {
        "catalog": {
            "data": {
                "players": jugadores,
            },
        },
    }


def test_infiere_quien_jugo() -> None:
    antes = _snapshot([
        {"id": 1, "playedHome": 0, "playedAway": 0},
        {"id": 2, "playedHome": 3, "playedAway": 2},
    ])
    despues = _snapshot([
        {"id": 1, "playedHome": 1, "playedAway": 0},
        {"id": 2, "playedHome": 3, "playedAway": 2},
    ])

    resultados = infer_outcomes(antes, despues)

    assert resultados["1"]["played"] == 1
    assert resultados["2"]["played"] == 0

    print("  OK  detecta quien sumo partido entre dos fotos")


def test_datos_incoherentes_no_inventan_resultado() -> None:
    antes = _snapshot([{"id": 1, "playedHome": 5, "playedAway": 0}])
    despues = _snapshot([{"id": 1, "playedHome": 2, "playedAway": 0}])

    assert infer_outcomes(antes, despues) == {}, (
        "Si los partidos bajan, algo va mal: mejor no puntuar "
        "que puntuar con basura."
    )

    print("  OK  ante datos incoherentes no se inventa resultado")


# ============================================================

TESTS = [
    test_brier_premia_acertar_con_conviccion,
    test_abstenerse_no_es_equivocarse,
    test_la_abstencion_no_se_registra,
    test_no_se_pisa_una_jornada_ya_puntuada,
    test_jornada_1_jp_gana_a_las_otras_dos,
    test_solo_disputados,
    test_sin_datos_reparto_equitativo,
    test_una_jornada_apenas_mueve_los_pesos,
    test_muchas_jornadas_si_separan,
    test_infiere_quien_jugo,
    test_datos_incoherentes_no_inventan_resultado,
]


def main() -> None:
    print("=" * 60)
    print(" ACIERTO POR FUENTE - BRIER")
    print("=" * 60)

    fallos = 0

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()
        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)
    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)
    print(f" {len(TESTS)}/{len(TESTS)} TESTS OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
