"""
Regresion del defecto 9 de la auditoria del 15/08/2026.

SINTOMA
    competitive_safety_gate comprueba

        protection = str(offer.get("protection") or "")
        ...
        if protection == "NEVER_AUTO_SELL":
            return block("BLOCK_PROTECTED_PLAYER", ...)

    pero las ofertas que llegan a ese gate se construyen en
    autopilot.build_competitive_observer, y ese diccionario no
    incluia la clave "protection". La palabra no aparecia ni una
    sola vez en autopilot.py.

    Resultado: protection era siempre "" y la barrera nunca podia
    dispararse. Un jugador clasificado NEVER_AUTO_SELL podia
    venderse por la ruta competitiva sin que la proteccion
    diseñada para impedirlo llegase a evaluarse.

ARREGLO
    liquidity_manager ya calcula la proteccion por jugador y la
    expone en su roster. Ahora se pasa al observador y viaja con
    cada oferta.

Ejecutar:
    python -m src.analysis.test_protection_gate_v1
"""

import inspect

from src.analysis.competitive_safety_gate import (
    evaluate_competitive_safety_gate,
)
from src.autopilot import build_competitive_observer


# ============================================================
# EL GATE FUNCIONA SI LE LLEGA EL DATO
# ============================================================

def _oferta(protection: str = "") -> dict:
    return {
        "offer_id": 1,
        "player_id": 26271,
        "amount": 22_000_000,
        "protection": protection,
        "decision_authority": "COMPETITIVE",
        "authoritative_decision": "ACCEPT_NOW",
        "negotiation": {
            "action_gate": "RESPOND",
            "should_respond": True,
        },
    }


def test_never_auto_sell_bloquea() -> None:
    resultado = evaluate_competitive_safety_gate(
        offer=_oferta("NEVER_AUTO_SELL"),
        temporal_gate={},
        current_balance=1_000_000,
    )

    assert resultado["status"] == "BLOCK_PROTECTED_PLAYER", (
        f"REGRESION: un jugador NEVER_AUTO_SELL no se bloqueo. "
        f"Devolvio {resultado['status']}."
    )
    assert resultado["authorized"] is False

    print("  OK  NEVER_AUTO_SELL bloquea la venta competitiva")


def test_sin_el_dato_la_barrera_es_invisible() -> None:
    """
    Deja constancia de por que el bug era dificil de ver: con la
    clave ausente el gate sigue su camino como si nada.
    """
    resultado = evaluate_competitive_safety_gate(
        offer=_oferta(""),
        temporal_gate={},
        current_balance=1_000_000,
    )

    assert resultado["status"] != "BLOCK_PROTECTED_PLAYER", (
        "Si sin el dato tambien bloqueara, este test no "
        "demostraria nada."
    )

    print(
        "  OK  sin el dato la barrera no salta: por eso era "
        "invisible"
    )


def test_otras_protecciones_no_bloquean() -> None:
    """
    Solo NEVER_AUTO_SELL es un veto. PROTECTED y CONDITIONAL
    son grados menores y no deben cortar la operacion aqui.
    """
    for nivel in ("PROTECTED", "CONDITIONAL", "SELLABLE", "NORMAL"):
        resultado = evaluate_competitive_safety_gate(
            offer=_oferta(nivel),
            temporal_gate={},
            current_balance=1_000_000,
        )

        assert resultado["status"] != "BLOCK_PROTECTED_PLAYER", (
            f"{nivel} no deberia bloquear como si fuera "
            f"NEVER_AUTO_SELL."
        )

    print("  OK  solo NEVER_AUTO_SELL veta; los demas grados no")


# ============================================================
# EL DATO LLEGA
# ============================================================

def test_el_observador_rellena_protection() -> None:
    fuente = inspect.getsource(
        build_competitive_observer
    )

    assert "protection_lookup" in fuente, (
        "REGRESION: el observador ya no construye el indice de "
        "proteccion."
    )

    assert '"protection":' in fuente, (
        "REGRESION: las ofertas vuelven a salir sin la clave "
        "protection, y el gate no puede bloquear nada."
    )

    print("  OK  el observador rellena protection en cada oferta")


def test_el_observador_acepta_la_liquidez() -> None:
    firma = inspect.signature(
        build_competitive_observer
    )

    assert "liquidity" in firma.parameters, (
        "REGRESION: el observador ya no recibe el estado de "
        "liquidez, que es de donde sale la proteccion."
    )

    print("  OK  el observador recibe el estado de liquidez")


def test_indice_tolera_roster_sucio() -> None:
    """
    Un roster con basura no puede tumbar el ciclo.
    """
    fuente = inspect.getsource(
        build_competitive_observer
    )

    assert "except (KeyError, TypeError, ValueError)" in fuente, (
        "El indice de proteccion debe ignorar entradas mal "
        "formadas en vez de lanzar."
    )

    print("  OK  un roster con entradas sucias no revienta")


# ============================================================

TESTS = [
    test_never_auto_sell_bloquea,
    test_sin_el_dato_la_barrera_es_invisible,
    test_otras_protecciones_no_bloquean,
    test_el_observador_rellena_protection,
    test_el_observador_acepta_la_liquidez,
    test_indice_tolera_roster_sucio,
]


def main() -> None:
    print("=" * 60)
    print(" PROTECCION DE JUGADORES (defecto 9)")
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
