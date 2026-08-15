"""
Regresion del defecto 2 de la auditoria del 15/08/2026.

SINTOMA
    build_competitive_observer() persistia el estado de la
    negociacion en la linea 1039, ANTES de que se intentase
    ninguna escritura (la ejecucion ocurre ~1600 lineas despues) y
    tambien en ciclos de pura observacion.

    Los estados que escribe apply_observer_response son
    terminales:
        ACCEPT_NOW     -> CLOSED
        COUNTER_OFFER  -> WAITING_RIVAL

    y la clave es offer:{offer_id}, la misma para siempre.

    Consecuencia: un solo ciclo en observacion, o un fallo HTTP,
    dejaba la oferta en CLOSED. En el siguiente ciclo el safety
    gate devolvia BLOCK_NEGOTIATION_STATE y la oferta no se
    aceptaba nunca. No existe ningun camino que reabra un CLOSED.

ARREGLO
    El observador ya no guarda: acumula las transiciones en
    pending_negotiation_transitions. confirm_negotiation_transitions()
    persiste UNICAMENTE la de la oferta cuya escritura se ha
    confirmado.

Ejecutar:
    python -m src.analysis.test_negotiation_persistence_v1
"""

import inspect

from src.autopilot import (
    build_competitive_observer,
    confirm_negotiation_transitions,
)


# ============================================================
# UTILIDADES
# ============================================================

def _observador(transiciones: dict) -> dict:
    return {
        "pending_negotiation_transitions": transiciones,
    }


def _transicion(
    clave: str,
    offer_id: int,
    status: str = "CLOSED",
) -> dict:
    return {
        clave: {
            "entry": {
                "status": status,
                "offer_id": offer_id,
            },
            "offer_id": offer_id,
            "player_id": 999,
        },
    }


# ============================================================
# EL OBSERVADOR YA NO PERSISTE
# ============================================================

def test_observador_no_guarda_estado() -> None:
    fuente = inspect.getsource(build_competitive_observer)

    assert "save_negotiation_state(" not in fuente, (
        "REGRESION: build_competitive_observer vuelve a guardar "
        "el estado de negociacion. Eso bloquea ofertas que nunca "
        "se llegaron a escribir."
    )

    assert "pending_negotiation_transitions" in fuente, (
        "REGRESION: el observador ya no acumula transiciones en "
        "espera."
    )

    print("  OK  el observador no persiste, solo deja en espera")


# ============================================================
# SIN ESCRITURA NO SE AVANZA
# ============================================================

def test_sin_escritura_no_persiste() -> None:
    """
    El caso exacto del bug: ciclo en observacion.
    """
    resultado = confirm_negotiation_transitions(
        _observador(_transicion("offer:555", 555)),
        {
            "status": "COMPETITIVE_LIVE_DISABLED",
            "write_performed": False,
            "success": True,
        },
    )

    assert resultado["persisted"] is False, (
        "REGRESION: se persistio el estado sin haber escrito. "
        "La oferta quedaria bloqueada para siempre."
    )

    print(f"  OK  observacion no avanza el estado")


def test_escritura_fallida_no_persiste() -> None:
    """
    Un fallo HTTP tampoco puede cerrar la negociacion.
    """
    resultado = confirm_negotiation_transitions(
        _observador(_transicion("offer:555", 555)),
        {
            "status": "WRITE_FAILED",
            "write_performed": True,
            "success": False,
            "offer_id": 555,
        },
    )

    assert resultado["persisted"] is False, (
        "REGRESION: un fallo de escritura cerro la negociacion."
    )

    print("  OK  escritura fallida no avanza el estado")


def test_gate_bloqueado_no_persiste() -> None:
    resultado = confirm_negotiation_transitions(
        _observador(_transicion("offer:555", 555)),
        {
            "status": "BLOCKED_LEGACY_ALREADY_WROTE",
            "write_performed": False,
            "success": True,
        },
    )

    assert resultado["persisted"] is False

    print("  OK  gate bloqueado no avanza el estado")


# ============================================================
# SOLO LA OFERTA ESCRITA
# ============================================================

def test_solo_avanza_la_oferta_escrita(tmp_ok=True) -> None:
    """
    Con tres transiciones en espera y una sola escritura, no se
    pueden cerrar las otras dos.
    """
    pendientes = {}
    pendientes.update(_transicion("offer:111", 111))
    pendientes.update(_transicion("offer:222", 222))
    pendientes.update(_transicion("offer:333", 333))

    # No tocamos disco: comprobamos la seleccion de claves.
    import src.autopilot as autopilot

    guardado = {}

    original_load = autopilot.load_negotiation_state
    original_save = autopilot.save_negotiation_state

    autopilot.load_negotiation_state = (
        lambda: {"negotiations": {}}
    )
    autopilot.save_negotiation_state = (
        lambda estado: guardado.update(estado)
    )

    try:
        resultado = confirm_negotiation_transitions(
            _observador(pendientes),
            {
                "status": "EXECUTED",
                "write_performed": True,
                "success": True,
                "offer_id": 222,
            },
        )
    finally:
        autopilot.load_negotiation_state = original_load
        autopilot.save_negotiation_state = original_save

    assert resultado["persisted"] is True, (
        f"Deberia haber persistido: {resultado}"
    )

    claves = set(resultado["keys"])

    assert claves == {"offer:222"}, (
        f"REGRESION: se persistieron claves de mas: {claves}. "
        f"Solo se escribio la oferta 222."
    )

    guardadas = set(
        guardado.get("negotiations", {}).keys()
    )

    assert guardadas == {"offer:222"}, (
        f"REGRESION: el estado en disco contiene {guardadas}; "
        f"las ofertas 111 y 333 quedarian bloqueadas sin "
        f"haberse escrito."
    )

    print(
        "  OK  con 3 en espera y 1 escrita, solo avanza esa"
    )


def test_escritura_de_otra_oferta_no_arrastra() -> None:
    resultado = confirm_negotiation_transitions(
        _observador(_transicion("offer:111", 111)),
        {
            "status": "EXECUTED",
            "write_performed": True,
            "success": True,
            "offer_id": 999,
        },
    )

    assert resultado["persisted"] is False, (
        "REGRESION: una escritura de otra oferta arrastro una "
        "transicion que no le correspondia."
    )

    print("  OK  escritura de otra oferta no arrastra estado")


def test_sin_transiciones_no_hace_nada() -> None:
    resultado = confirm_negotiation_transitions(
        _observador({}),
        {
            "write_performed": True,
            "success": True,
            "offer_id": 1,
        },
    )

    assert resultado["persisted"] is False

    print("  OK  sin transiciones en espera no hace nada")


# ============================================================

TESTS = [
    test_observador_no_guarda_estado,
    test_sin_escritura_no_persiste,
    test_escritura_fallida_no_persiste,
    test_gate_bloqueado_no_persiste,
    test_solo_avanza_la_oferta_escrita,
    test_escritura_de_otra_oferta_no_arrastra,
    test_sin_transiciones_no_hace_nada,
]


def main() -> None:
    print("=" * 60)
    print(" PERSISTENCIA DE NEGOCIACION (defecto 2)")
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
