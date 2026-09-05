"""
"Vacio" y "de otra jornada" no son lo mismo.

SINTOMA

    `lineup_engine` decia siempre lo mismo cuando no habia
    pronosticos:

        "El tablero de FutbolFantasy esta vacio: se alinea sin
         pronostico."

    El 10/09/2026 se leyo esa frase y se concluyo que la fuente
    estaba caida. Se escribio en un informe. Era falso: el
    tablero tenia 64 jugadores dentro y lo que pasaba es que era
    de la jornada 2 y el calendario iba por la 5.

CAUSA

    `board_from_single_source` ya devolvia `rejected`,
    `rejection_reason`, `matchday` y `expected_matchday`. La rama
    de "sin jugadores" tiraba el diccionario entero y lo
    sustituia por uno nuevo con la frase fija.

    Los datos estaban. Se perdian en el ultimo metro, otra vez.

CONSECUENCIA

    Las dos causas llevan a sitios distintos:

        de otra jornada  ->  el guardarrail funcionando. Se
                             arregla refrescando el tablero.
        vacio de verdad  ->  la fuente no devolvio nada. Se
                             arregla mirando por que.

    Un mensaje que confunde las dos hace perder el tiempo en la
    direccion equivocada, y ya lo hizo una vez.
"""

from __future__ import annotations

from src.analysis import lineup_engine


def _sin_cache():
    lineup_engine._MULTISOURCE_STARTER_CACHE.clear()


def _con_tablero(tablero, funcion):
    """
    Suplanta la fuente del tablero y la deja como estaba.
    """

    original = lineup_engine.board_from_single_source

    lineup_engine.board_from_single_source = lambda: tablero
    _sin_cache()

    try:
        return funcion()

    finally:
        lineup_engine.board_from_single_source = original
        _sin_cache()


def _tablero(**extra) -> dict:
    base = {
        "version": "V12.0_SINGLE_SOURCE",
        "source": "FUTBOLFANTASY",
        "cache": {"status": "REJECTED_WRONG_MATCHDAY"},
        "matchday": 2,
        "updated_at": "2026-08-17T18:32:30+00:00",
        "rejected": False,
        "rejection_reason": None,
        "expected_matchday": None,
        "players": [],
    }
    base.update(extra)
    return base


def test_de_otra_jornada_no_se_llama_vacio() -> None:
    """
    El caso exacto que costo el diagnostico falso del 10/09.
    """

    tablero = _tablero(
        rejected=True,
        expected_matchday=5,
        rejection_reason=(
            "El tablero es de la jornada 2 y estamos en la 5: "
            "sin pronosticos hasta que se refresque."
        ),
    )

    salida = _con_tablero(
        tablero,
        lambda: lineup_engine.build_starter_intelligence_for_snapshot(
            {"marca": "solo para la cache"}
        ),
    )

    assert salida["version"] == "V12.0_REJECTED_MATCHDAY", (
        f"un tablero rechazado por jornada se sigue etiquetando "
        f"como {salida['version']}"
    )

    assert "vacio" not in salida["error"].lower(), (
        f"se sigue diciendo que esta vacio: {salida['error']}"
    )

    assert "jornada" in salida["error"].lower(), (
        f"el motivo no menciona la jornada: {salida['error']}"
    )


def test_los_sellos_sobreviven_al_rechazo() -> None:
    """
    De que jornada era el tablero y cual se esperaba. Sin esos dos
    numeros el aviso no es accionable: no se sabe si falta un
    refresco de horas o de semanas.
    """

    tablero = _tablero(
        rejected=True,
        expected_matchday=5,
        rejection_reason="El tablero es de la jornada 2 y estamos en la 5.",
    )

    salida = _con_tablero(
        tablero,
        lambda: lineup_engine.build_starter_intelligence_for_snapshot(
            {"marca": 2}
        ),
    )

    assert salida["matchday"] == 2
    assert salida["expected_matchday"] == 5
    assert salida["rejected"] is True
    assert salida["rejection_reason"]
    assert salida["updated_at"], (
        "se pierde cuando se genero el tablero rechazado"
    )


def test_vacio_de_verdad_sigue_diciendo_que_esta_vacio() -> None:
    """
    Y la otra mitad: si la fuente no devuelve nada, el mensaje
    tiene que seguir siendo el de siempre. Arreglar un mensaje
    rompiendo el otro no seria un arreglo.
    """

    salida = _con_tablero(
        _tablero(matchday=5, expected_matchday=5),
        lambda: lineup_engine.build_starter_intelligence_for_snapshot(
            {"marca": 3}
        ),
    )

    assert salida["version"] == "V12.0_EMPTY"
    assert "vacio" in salida["error"].lower()
    assert salida["rejected"] is False


def test_un_tablero_con_jugadores_no_se_toca() -> None:
    tablero = _tablero(
        players=[{"player_id": 1, "starter_probability": 90.0}],
    )

    salida = _con_tablero(
        tablero,
        lambda: lineup_engine.build_starter_intelligence_for_snapshot(
            {"marca": 4}
        ),
    )

    assert salida["version"] == "V12.0_SINGLE_SOURCE"
    assert salida.get("error") is None
    assert len(salida["players"]) == 1


def test_si_la_fuente_revienta_se_dice_que_reventó() -> None:
    """
    Tercera causa, tercer mensaje. Un fallo de la fuente no puede
    disfrazarse ni de vacio ni de jornada vieja.
    """

    original = lineup_engine.board_from_single_source

    def revienta():
        raise RuntimeError("la fuente no contesta")

    lineup_engine.board_from_single_source = revienta
    _sin_cache()

    try:
        salida = lineup_engine.build_starter_intelligence_for_snapshot(
            {"marca": 5}
        )

    finally:
        lineup_engine.board_from_single_source = original
        _sin_cache()

    assert salida["version"] == "V12.0_FALLBACK"
    assert "RuntimeError" in salida["error"]


TESTS = [
    test_de_otra_jornada_no_se_llama_vacio,
    test_los_sellos_sobreviven_al_rechazo,
    test_vacio_de_verdad_sigue_diciendo_que_esta_vacio,
    test_un_tablero_con_jugadores_no_se_toca,
    test_si_la_fuente_revienta_se_dice_que_reventó,
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
    print(f"MOTIVO DEL TABLERO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
