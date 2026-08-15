"""
Regresion de los defectos 4 y 6 de la auditoria del 15/08/2026.

DEFECTO 6 - CANCEL_COUNTER sin ejecutor
    dynamic_counteroffer_repricing_v107 emite CANCEL_COUNTER con
    prioridad 100, por encima de RAISE_COUNTER (90), cuando un
    jugador pasa a NEVER_SELL: mantener viva una contraoferta que
    el rival puede aceptar deja de ser seguro.

    Esa accion no la consumia nadie. _best_raise filtraba solo
    RAISE_COUNTER, y BiwengerWriteClient.cancel_bid no tenia un
    solo llamante en el repositorio. El rival podia aceptar
    nuestra contraoferta viva y perdiamos un jugador marcado como
    no vendible.

DEFECTO 4 - escrituras V10 sin barrera temporal
    El bloque de acciones autonomas de v10_full_autonomous_live
    escribia sin pasar por ningun gate de fase. Solo el ejecutor
    legacy respetaba operations_locked. Un ciclo que arranca en
    NORMAL y termina 90 segundos despues ya bloqueado podia
    escribir igualmente.

Ejecutar:
    python -m src.analysis.test_v10_write_gates_v1
"""

# HEALTH_CHECK: SAFE
# Solo inspecciona codigo fuente y estructuras en memoria.
# No instancia BiwengerWriteClient ni realiza ninguna escritura.

import inspect

from src.v10_full_autonomous_live import (
    _best_cancel,
    _best_raise,
    _temporal_block,
    run_full_autonomous_cycle,
)


# ============================================================
# DEFECTO 6
# ============================================================

def _item(
    action: str,
    counter_offer_id: int = 777,
    incoming_offer_id: int = 555,
    priority: int = 100,
) -> dict:
    return {
        "action": action,
        "priority": priority,
        "counter_offer_id": counter_offer_id,
        "incoming_offer_id": incoming_offer_id,
        "recommended_counter": 5_000_000,
        "player_name": "Jugador",
        "urgency_score": 1.0,
    }


def test_selecciona_cancel_counter() -> None:
    board = {
        "actions": [
            _item("CANCEL_COUNTER"),
        ],
    }

    elegido = _best_cancel(board)

    assert elegido is not None, (
        "REGRESION: CANCEL_COUNTER vuelve a no tener consumidor."
    )
    assert elegido["counter_offer_id"] == 777

    print("  OK  CANCEL_COUNTER se selecciona")


def test_cancela_nuestra_contraoferta_no_la_del_rival() -> None:
    """
    counter_offer_id es NUESTRA contraoferta.
    incoming_offer_id es la oferta del rival. Confundirlas
    borraria la oferta equivocada.
    """
    board = {
        "actions": [
            _item(
                "CANCEL_COUNTER",
                counter_offer_id=777,
                incoming_offer_id=555,
            ),
        ],
    }

    elegido = _best_cancel(board)

    assert elegido["counter_offer_id"] != elegido["incoming_offer_id"]

    fuente = inspect.getsource(run_full_autonomous_cycle)

    assert 'cancel_candidate["counter_offer_id"]' in fuente, (
        "REGRESION: la cancelacion no usa counter_offer_id. "
        "Estaria borrando la oferta del rival."
    )

    print("  OK  cancela counter_offer_id, no incoming_offer_id")


def test_sin_id_valido_no_cancela() -> None:
    for valor in (0, None, -1):
        board = {
            "actions": [
                _item("CANCEL_COUNTER", counter_offer_id=valor),
            ],
        }

        assert _best_cancel(board) is None, (
            f"REGRESION: con counter_offer_id={valor} se intenta "
            f"cancelar igualmente."
        )

    print("  OK  sin id valido no se cancela nada")


def test_no_confunde_con_otras_acciones() -> None:
    board = {
        "actions": [
            _item("RAISE_COUNTER"),
            _item("KEEP_COUNTER"),
            _item("REVIEW_BLOCK"),
        ],
    }

    assert _best_cancel(board) is None, (
        "REGRESION: _best_cancel selecciona acciones que no son "
        "CANCEL_COUNTER."
    )

    assert _best_raise(
        {"actions": [_item("CANCEL_COUNTER")]}
    ) is None, (
        "REGRESION: _best_raise selecciona un CANCEL_COUNTER."
    )

    print("  OK  cada selector coge solo lo suyo")


def test_cancel_tiene_prioridad_sobre_raise() -> None:
    fuente = inspect.getsource(run_full_autonomous_cycle)

    pos_cancel = fuente.find("if cancel_candidate:")
    pos_raise = fuente.find("elif counter_candidate:")

    assert pos_cancel != -1, (
        "REGRESION: ya no se ejecuta CANCEL_COUNTER."
    )
    assert pos_raise != -1
    assert pos_cancel < pos_raise, (
        "REGRESION: RAISE_COUNTER se evalua antes que "
        "CANCEL_COUNTER. El motor le da prioridad 100 frente a 90."
    )

    print("  OK  CANCEL se evalua antes que RAISE")


# ============================================================
# DEFECTO 4
# ============================================================

def _ciclo(operations_locked: bool, phase: str) -> dict:
    return {
        "result": {
            "state": {
                "operations_locked": operations_locked,
                "phase": phase,
            },
        },
    }


def test_gate_detecta_bloqueo() -> None:
    assert _temporal_block(
        _ciclo(True, "ROUND_TRANSITION_LOCK")
    ) == "ROUND_TRANSITION_LOCK"

    assert _temporal_block(
        _ciclo(True, "HARD_SAFETY")
    ) == "HARD_SAFETY"

    print("  OK  detecta la fase bloqueada")


def test_gate_deja_pasar_en_normal() -> None:
    assert _temporal_block(_ciclo(False, "NORMAL")) is None

    print("  OK  en fase NORMAL no bloquea")


def test_gate_tolera_ciclo_incompleto() -> None:
    for ciclo in ({}, {"result": {}}, {"result": {"state": {}}}):
        assert _temporal_block(ciclo) is None, (
            "Un ciclo sin estado no deberia bloquear por si solo."
        )

    print("  OK  un ciclo incompleto no revienta el gate")


def test_las_escrituras_v10_respetan_el_gate() -> None:
    fuente = inspect.getsource(run_full_autonomous_cycle)

    assert "temporal_block = _temporal_block(cycle)" in fuente, (
        "REGRESION: el ciclo V10 ya no calcula la barrera "
        "temporal."
    )

    assert "if not write_used and not temporal_block:" in fuente, (
        "REGRESION: el bloque de escrituras autonomas V10 ya no "
        "comprueba la barrera temporal. Podria contraofertar o "
        "vender con la jornada bloqueada."
    )

    print("  OK  el bloque de escrituras V10 respeta la fase")


def test_write_used_refleja_exito_real() -> None:
    """
    Antes RAISE_COUNTER hacia write_used = True sin mirar si la
    escritura habia salido bien.
    """
    fuente = inspect.getsource(run_full_autonomous_cycle)

    assert 'action_taken = "RAISE_COUNTER"' in fuente

    trozo = fuente[
        fuente.find("elif counter_candidate:"):
        fuente.find('action_taken = "RAISE_COUNTER"')
    ]

    assert 'action_result.get("success")' in trozo, (
        "REGRESION: RAISE_COUNTER vuelve a marcar write_used "
        "sin comprobar el exito real de la escritura."
    )

    print("  OK  write_used depende del exito real")


# ============================================================

TESTS = [
    test_selecciona_cancel_counter,
    test_cancela_nuestra_contraoferta_no_la_del_rival,
    test_sin_id_valido_no_cancela,
    test_no_confunde_con_otras_acciones,
    test_cancel_tiene_prioridad_sobre_raise,
    test_gate_detecta_bloqueo,
    test_gate_deja_pasar_en_normal,
    test_gate_tolera_ciclo_incompleto,
    test_las_escrituras_v10_respetan_el_gate,
    test_write_used_refleja_exito_real,
]


def main() -> None:
    print("=" * 60)
    print(" GATES DE ESCRITURA V10 (defectos 4 y 6)")
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
