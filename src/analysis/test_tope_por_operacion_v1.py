"""
El tope por operacion, en pantalla y de verdad.

SINTOMA

    El panel de especulacion enseñaba `max_operation: 0` con
    presupuesto abierto. Cero significa "no cabe ni una
    operacion", y el tope real era el 40 % del bolsillo.

CAUSA

    Un nombre de clave. El motor devuelve
    `single_operation_limit` -`speculation_engine.py`, en las dos
    ramas de presupuesto, y `acquisition_budget.py` igual-. El
    lector del dashboard buscaba `max_operation` y, de reserva,
    `max_single_operation`. Ninguna de las dos existe en ningun
    sitio del sistema.

CONSECUENCIA

    La pantalla no enseñaba un numero pequeño: enseñaba lo
    contrario de lo que decia el motor. Y el dueño decide mirando
    la pantalla.

    Esta guardia ata las dos puntas: que el motor siga llamandolo
    `single_operation_limit`, y que el lector lo lea de ahi.
"""

from __future__ import annotations

from src.telemetry.dashboard_state import compact_speculation


def _estado(budget: dict) -> dict:
    return {"speculation": {"budget": budget, "buy_candidates": []}}


def test_el_tope_del_motor_llega_a_la_pantalla() -> None:
    panel = compact_speculation(
        _estado({
            "enabled": True,
            "total_budget": 3_560_000,
            "single_operation_limit": 1_424_000,
        })
    )

    assert panel["max_operation"] == 1_424_000, (
        "el 40 % del bolsillo, no un cero"
    )


def test_un_tope_de_cero_sigue_siendo_cero() -> None:
    """Cuando el motor dice cero de verdad, la pantalla dice cero."""

    panel = compact_speculation(
        _estado({
            "enabled": False,
            "total_budget": 0,
            "single_operation_limit": 0,
            "blocked_by": "HARD_SAFETY",
        })
    )

    assert panel["max_operation"] == 0, "aqui el cero es la verdad"
    assert panel["enabled"] is False, "y el motivo viaja con el"


def test_sin_presupuesto_no_se_inventa_un_tope() -> None:
    panel = compact_speculation({"speculation": {}})

    assert panel["max_operation"] == 0, "sin dato, cero, y no un numero suelto"


def test_los_nombres_viejos_se_siguen_entendiendo() -> None:
    """
    Un estado guardado de antes puede traerlos. Leerlos no cuesta
    nada y perderlos si.
    """

    assert compact_speculation(
        _estado({"max_operation": 900_000})
    )["max_operation"] == 900_000

    assert compact_speculation(
        _estado({"max_single_operation": 800_000})
    )["max_operation"] == 800_000


def test_el_nombre_del_motor_manda_sobre_el_viejo() -> None:
    panel = compact_speculation(
        _estado({
            "single_operation_limit": 1_424_000,
            "max_operation": 0,
        })
    )

    assert panel["max_operation"] == 1_424_000, (
        "si llegan los dos, el bueno es el que escribe el motor"
    )


def test_el_motor_sigue_llamandolo_igual() -> None:
    """
    LA OTRA PUNTA.

    Si el motor le cambia el nombre, el lector vuelve a enseñar
    cero y nadie se entera. Se comprueba contra el motor de
    verdad, no contra una copia del nombre.
    """

    from src.analysis.speculation_engine import (
        calculate_speculation_budget,
    )

    presupuesto = calculate_speculation_budget(
        {
            "market": {
                "status": {
                    "balance": 5_000_000,
                    "maximumBid": 5_006_140,
                }
            },
            "my_team": [],
        },
        {"hard_safety": False, "solvency_needed": False},
        None,
    )

    assert "single_operation_limit" in presupuesto, (
        "el motor ha dejado de publicar el tope por operacion con "
        "el nombre que lee la pantalla"
    )

    panel = compact_speculation(
        {"speculation": {"budget": presupuesto}}
    )

    assert panel["max_operation"] == presupuesto[
        "single_operation_limit"
    ], "lo que calcula el motor es lo que se pinta"


TESTS = [
    test_el_tope_del_motor_llega_a_la_pantalla,
    test_un_tope_de_cero_sigue_siendo_cero,
    test_sin_presupuesto_no_se_inventa_un_tope,
    test_los_nombres_viejos_se_siguen_entendiendo,
    test_el_nombre_del_motor_manda_sobre_el_viejo,
    test_el_motor_sigue_llamandolo_igual,
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
    print(f"TOPE POR OPERACION V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
