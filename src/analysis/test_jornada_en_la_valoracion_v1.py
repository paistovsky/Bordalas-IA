"""
La otra mitad del guardarrail: el tablero de otra jornada tampoco
llega a la valoracion. Y se dice por que.

SINTOMA

    El 04/09 se tapo la mitad: el proveedor dejo de SERVIR un
    tablero de otra jornada cuando FutbolFantasy falla. Pero
    `candidate_starter_lookup` lee el fichero del disco por su
    cuenta -es por donde pasan el XI, el tablero de fichajes, el
    plan de deuda y la pantalla- y nunca miraba la jornada.

CAUSA

    El propio `board_stamps` lo tenia escrito: "`matchday` es el
    guardarrail contra usar datos de una jornada en otra, que es
    justo el fallo del 16/08/2026". Lo cargaba en la ficha de
    cada jugador. No lo aplicaba.

CONSECUENCIA

    Es el fallo del 16/08 llegando hasta donde se decide, no solo
    hasta donde se pinta.

    Ahora no se sirve: el lookup sale vacio y Pepe se queda
    quieto. Esta guardia protege las dos mitades de eso, y la
    segunda importa tanto como la primera:

      1. que un tablero de otra jornada no alimente nada;
      2. que el motivo salga en pantalla. Quedarse quieto esta
         bien; quedarse quieto en silencio dejaria al dueño dias
         preguntandose que le pasa a Pepe.

    Y una tercera, la que evita el remedio peor que la
    enfermedad: sin saber en que jornada estamos NO se rechaza
    nada. Rechazar contra una expectativa que no tenemos seria
    inventarse un motivo, y dejaria a Pepe quieto por nada.
"""

from __future__ import annotations

import json
import tempfile

from pathlib import Path

import src.analysis.candidate_starter_lookup as lookup_mod

from src.analysis.candidate_starter_lookup import (
    board_rejection,
    build_starter_lookup,
    set_expected_matchday,
)


def _tablero(matchday, jugadores: int = 3) -> dict:
    return {
        "version": "V12.0",
        "updated_at": "2026-09-05T10:00:00+00:00",
        "matchday": matchday,
        "players": [
            {
                "player_id": 100 + i,
                "player_name": f"Jugador {i}",
                "starter_probability": 88.0,
                "consensus": "STARTER",
                "source_coverage": 1,
                "source": "FUTBOLFANTASY",
                "scope": "ROSTER",
                "team": "Barcelona",
                "hierarchy": {"value": 5, "label": "Clave"},
                "availability": {"label": "DISPONIBLE", "can_play": True},
            }
            for i in range(jugadores)
        ],
        "cache": {"status": "REFRESHED", "error": None},
    }


def _sin_expectativa(funcion):
    """Deja la expectativa como estaba: es estado de modulo."""
    previa = lookup_mod.expected_matchday()
    try:
        return funcion()
    finally:
        set_expected_matchday(previa)


# ============================================================
# 1. NO ALIMENTA NADA
# ============================================================


def test_el_tablero_de_otra_jornada_no_da_pronosticos() -> None:
    def caso():
        set_expected_matchday(4)
        return build_starter_lookup(_tablero(3))

    assert _sin_expectativa(caso) == {}, (
        "un tablero de la 3 no puede dar pronosticos para la 4"
    )


def test_el_tablero_de_esta_jornada_si() -> None:
    def caso():
        set_expected_matchday(4)
        return build_starter_lookup(_tablero(4))

    resultado = _sin_expectativa(caso)

    assert len(resultado) == 3, "el tablero bueno sigue sirviendo"
    assert resultado[100]["probability"] == 88.0, "y con su probabilidad"


def test_un_tablero_sin_jornada_tampoco_pasa() -> None:
    def caso():
        set_expected_matchday(4)
        return build_starter_lookup(_tablero(None))

    assert _sin_expectativa(caso) == {}, (
        "sin jornada no se sabe de que jornada es: no vale"
    )


def test_el_tipo_no_decide_una_jornada() -> None:
    """Un "4" de JSON y un 4 de Python son la misma jornada."""

    def caso():
        set_expected_matchday(4)
        return build_starter_lookup(_tablero("4"))

    assert len(_sin_expectativa(caso)) == 3, (
        "rechazar por el tipo dejaria a Pepe quieto con un tablero bueno"
    )


# ============================================================
# 2. SE DICE POR QUE
# ============================================================


def test_el_motivo_nombra_las_dos_jornadas() -> None:
    def caso():
        set_expected_matchday(4)
        return board_rejection(_tablero(3))

    rechazo = _sin_expectativa(caso)

    assert rechazo is not None, "hay rechazo"
    assert "jornada 3" in rechazo["reason"], "de que jornada es"
    assert "la 4" in rechazo["reason"], "y en cual estamos"
    assert rechazo["board_matchday"] == 3
    assert rechazo["expected_matchday"] == 4


def test_el_motivo_llega_a_los_sellos_del_tablero() -> None:
    """
    `board_stamps()` es por donde el dashboard lee el estado del
    tablero. Si el motivo no sale por ahi, no sale por ningun
    sitio.
    """

    original = lookup_mod.BOARD_FILE

    def caso():
        with tempfile.TemporaryDirectory() as carpeta:
            lookup_mod.BOARD_FILE = Path(carpeta) / "board.json"
            lookup_mod.BOARD_FILE.write_text(
                json.dumps(_tablero(3)), encoding="utf-8"
            )
            set_expected_matchday(4)
            return lookup_mod.board_stamps()

    try:
        sellos = _sin_expectativa(caso)
    finally:
        lookup_mod.BOARD_FILE = original

    assert sellos["rejected"] is True, "la bandera, explicita"
    assert "jornada 3" in (sellos["rejection_reason"] or ""), (
        "y el motivo con palabras"
    )
    assert sellos["cache"]["status"] == "REJECTED_WRONG_MATCHDAY", (
        "el estado de cache lo dice tambien"
    )
    assert "jornada 3" in (sellos["cache"]["error"] or ""), (
        "y por el campo `error`, que es el que ya pinta la pantalla "
        "como `starter_source_error`"
    )
    assert sellos["matchday"] == 3, (
        "la jornada que se publica es la del tablero, no la de hoy: "
        "escribir la de hoy seria disfrazarlo de bueno"
    )


def test_el_tablero_bueno_no_inventa_un_rechazo() -> None:
    original = lookup_mod.BOARD_FILE

    def caso():
        with tempfile.TemporaryDirectory() as carpeta:
            lookup_mod.BOARD_FILE = Path(carpeta) / "board.json"
            lookup_mod.BOARD_FILE.write_text(
                json.dumps(_tablero(4)), encoding="utf-8"
            )
            set_expected_matchday(4)
            return lookup_mod.board_stamps()

    try:
        sellos = _sin_expectativa(caso)
    finally:
        lookup_mod.BOARD_FILE = original

    assert sellos["rejected"] is False, "no hay nada que rechazar"
    assert sellos["rejection_reason"] is None, "ni motivo que inventar"


# ============================================================
# 3. SIN SABER LA JORNADA, NO SE ROMPE NADA
# ============================================================


def test_sin_expectativa_se_comporta_como_siempre() -> None:
    """
    El remedio peor que la enfermedad: rechazar contra una
    expectativa que no tenemos dejaria a Pepe quieto por nada.
    """

    def caso():
        set_expected_matchday(None)
        return build_starter_lookup(_tablero(3))

    assert len(_sin_expectativa(caso)) == 3, (
        "sin saber en que jornada estamos no se rechaza nada"
    )
    assert _sin_expectativa(
        lambda: (set_expected_matchday(None), board_rejection(_tablero(3)))[1]
    ) is None, "y no se inventa un motivo"


def test_una_jornada_ilegible_no_fija_expectativa() -> None:
    def caso():
        set_expected_matchday("jornada cuatro")
        return lookup_mod.expected_matchday()

    assert _sin_expectativa(caso) is None, (
        "una jornada que no es un numero es no saberla"
    )


def test_sin_tablero_no_hay_rechazo_que_dar() -> None:
    def caso():
        set_expected_matchday(4)
        return (
            board_rejection(None),
            board_rejection({}),
        )

    assert _sin_expectativa(caso) == (None, None), (
        "no hay tablero no es tener el tablero equivocado, y la "
        "pantalla ya dice lo primero por otro sitio"
    )


# ============================================================
# 4. LOS DOS PROCESOS FIJAN LA JORNADA
# ============================================================


def test_la_cache_suelta_al_cambiar_de_jornada() -> None:
    """
    El tablero se queda rancio mientras el calendario avanza. Si
    la cache no soltara, la jornada nueva se contestaria con la
    respuesta de la vieja.
    """

    original = lookup_mod.BOARD_FILE

    def caso():
        with tempfile.TemporaryDirectory() as carpeta:
            lookup_mod.BOARD_FILE = Path(carpeta) / "board.json"
            lookup_mod.BOARD_FILE.write_text(
                json.dumps(_tablero(3)), encoding="utf-8"
            )

            set_expected_matchday(3)
            antes = len(lookup_mod.get_starter_lookup())

            # El fichero no cambia. Solo avanza el calendario.
            set_expected_matchday(4)
            despues = len(lookup_mod.get_starter_lookup())

            return antes, despues

    try:
        antes, despues = _sin_expectativa(caso)
    finally:
        lookup_mod.BOARD_FILE = original
        lookup_mod.reset_starter_lookup_cache()

    assert antes == 3, "en su jornada servia"
    assert despues == 0, "y al avanzar el calendario deja de servir"


def test_el_ciclo_fija_la_jornada() -> None:
    """
    Arreglar el lookup y no decirle nunca en que jornada estamos
    lo dejaria apagado para siempre.
    """

    fuente = Path("src/autopilot.py").read_text(encoding="utf-8")

    assert "set_expected_matchday(jornada)" in fuente, (
        "el ciclo ha dejado de decirle al lookup contra que jornada "
        "validar el tablero"
    )


def test_la_telemetria_fija_la_jornada() -> None:
    """
    Y si solo la fijase el ciclo, el dashboard pintaria el
    pronostico de la semana pasada mientras el ciclo esta quieto.
    Dos pantallas contando cosas distintas del mismo tablero.
    """

    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert "set_expected_matchday(" in fuente, (
        "la telemetria ha dejado de validar la jornada"
    )
    assert fuente.index("set_expected_matchday(") < fuente.index(
        "result = build_global_decision(snapshot)"
    ), (
        "la jornada se fija DESPUES de recalcular: ese recalculo ya "
        "usa el lookup, asi que llegaria tarde"
    )


def test_el_motivo_sale_en_el_bloque_del_once() -> None:
    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert '"starter_board_rejected"' in fuente, (
        "la bandera de tablero rechazado no llega al dashboard"
    )
    assert '"starter_board_rejection_reason"' in fuente, (
        "el motivo no llega al dashboard: Pepe se quedaria quieto "
        "en silencio"
    )


TESTS = [
    test_el_tablero_de_otra_jornada_no_da_pronosticos,
    test_el_tablero_de_esta_jornada_si,
    test_un_tablero_sin_jornada_tampoco_pasa,
    test_el_tipo_no_decide_una_jornada,
    test_el_motivo_nombra_las_dos_jornadas,
    test_el_motivo_llega_a_los_sellos_del_tablero,
    test_el_tablero_bueno_no_inventa_un_rechazo,
    test_sin_expectativa_se_comporta_como_siempre,
    test_una_jornada_ilegible_no_fija_expectativa,
    test_sin_tablero_no_hay_rechazo_que_dar,
    test_la_cache_suelta_al_cambiar_de_jornada,
    test_el_ciclo_fija_la_jornada,
    test_la_telemetria_fija_la_jornada,
    test_el_motivo_sale_en_el_bloque_del_once,
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
    print(f"JORNADA EN LA VALORACION V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
