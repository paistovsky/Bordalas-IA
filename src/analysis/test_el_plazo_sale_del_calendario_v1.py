"""
El plazo sale del calendario.

SINTOMA (23/09/2026)

    La subasta frenaba con esto:

        El reloj de solvencia dice «CUBIERTO» con 1.525.782 EUR de
        deficit. No se puja: el viernes hay que estar en positivo.

    No habia ningun viernes. La jornada 7 se jugo el 18/09 y la 8
    empieza el 09/10 a las 21:00, veintiun dias despues, por el
    paron de selecciones. El propio reloj lo sabia -publicaba
    390,04 h hasta su plazo, sacadas del calendario- y la subasta
    no lo miraba: la frase estaba escrita a mano y la regla
    cerraba con CUALQUIER deficit, sin fecha.

LO QUE SE PROTEGE

    1. Con una jornada cuyo primer partido esta a 16 dias, el
       motivo del freno nombra la fecha del calendario y no dice
       "viernes" ni "esta semana".
    2. El plazo publicado es el cierre del calendario menos
       `SOLVENCY_DEADLINE_HOURS`: el margen no se toca, solo de
       donde sale la fecha.
    3. Sin fecha en el calendario, el freno dice "no lo se" con
       esas palabras, y frena.
    4. Con `BORDALAS_SOLVENCIA_POR_SU_PLAZO` APAGADO -como llega-
       el deficit sigue cerrando, y el motivo dice que hay tiempo.
    5. Con el interruptor puesto, lejos del plazo no frena la
       solvencia; a menos de un ciclo del Computer, si.

LA GUARDIA MUERDE SI EL CASO NO TIENE CALENDARIO

    Si el caso llega sin `real_deadline`, las pruebas 1, 2 y 5 no
    prueban nada. La primera linea de cada una lo exige.

NO LEE EL MUNDO

    Ni `data/`, ni red, ni el reloj del sistema: las horas se pasan
    escritas. El interruptor se quita aqui arriba (doctrina 104) y
    la prueba que lo pone lo deja como estaba.

COMO SE USA

    python -m src.analysis.test_el_plazo_sale_del_calendario_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
os.environ.pop("BORDALAS_SOLVENCIA_POR_SU_PLAZO", None)
os.environ.pop("BORDALAS_SIN_SUBASTA", None)
os.environ.pop("BORDALAS_SIN_REVENTA", None)

from src.analysis.la_subasta import (  # noqa: E402
    SOLVENCIA_POR_SU_PLAZO_ENV,
    plan_del_reset,
)
from src.analysis.solvency_clock import (  # noqa: E402
    COMPUTER_CYCLE_HOURS,
    SOLVENCY_DEADLINE_HOURS,
    build_solvency_clock,
)


# ============================================================
# EL CASO: EL 23/09/2026 A LAS 08:51, COPIADO DE LA FOTO
# ============================================================
#
#     Cierre de la jornada 8 en el calendario: 09/10 20:45 (primer
#     partido 21:00 menos 15 min). A 16 dias y medio.

CIERRE_J8 = "2026-10-09T20:45:00+02:00"

HORAS_AL_CIERRE = 396.04

SALDO = -1_525_782

OFERTAS = [
    {"player_name": "Uno", "amount": 12_000_000, "hours_to_expiry": 30.0},
    {"player_name": "Dos", "amount": 7_096_400, "hours_to_expiry": 30.0},
]


def _reloj(real_deadline=CIERRE_J8, horas=HORAS_AL_CIERRE) -> dict:
    return build_solvency_clock(
        SALDO,
        horas,
        offers=OFERTAS,
        market_clock={"hours_to_reset": 22.0},
        real_deadline=real_deadline,
    )


def _plan(reloj: dict) -> dict:
    """La subasta con todo en verde salvo la solvencia."""

    return plan_del_reset(
        candidatos=[
            {
                "id": 100 + i,
                "name": f"Jugador {i}",
                "market_price": 100_000 + 10_000 * i,
                "team_id": 1 + i,
                "starter_probability": 80.0,
                "hierarchy_value": 60,
            }
            for i in range(4)
        ],
        prima_de_reventa=0.0187,
        presupuesto=2_500_000,
        fichas_libres=6,
        caja_libre=500_000,
        seconds_to_reset=300,
        solvency_clock=reloj,
        plantilla=[],
        bloqueo_temporal=None,
        en_vivo=True,
        max_por_club=4,
    )


def _exige_calendario(reloj: dict) -> None:
    assert reloj.get("real_deadline"), (
        "el caso no tiene calendario: esta prueba no prueba nada"
    )
    assert (reloj.get("solvency_deadline") or {}).get("known"), (
        "el caso trae calendario y el reloj no ha sacado el plazo"
    )


# ============================================================
# 1. A 16 DIAS, EL PLAZO NO ES ESTA SEMANA
# ============================================================

def test_el_plazo_sale_del_calendario() -> None:

    reloj = _reloj()

    _exige_calendario(reloj)

    assert reloj["state"] == "CUBIERTO", reloj["state"]

    plan = _plan(reloj)

    assert plan["blocked_by"] == "SOLVENCIA", plan["blocked_by"]

    motivo = plan["reason"] or ""

    for prohibida in ("viernes", "esta semana", "semanal"):
        assert prohibida not in motivo.lower(), (
            f"a 16 dias del plazo el motivo dice «{prohibida}»: "
            f"{motivo}"
        )

    assert "09/10" in motivo, (
        f"el motivo no nombra la fecha del calendario: {motivo}"
    )
    assert "calendario" in motivo, motivo


# ============================================================
# 2. EL MARGEN NO SE TOCA: SOLO LA FUENTE
# ============================================================

def test_el_plazo_es_el_cierre_menos_el_margen_de_siempre() -> None:

    reloj = _reloj()

    _exige_calendario(reloj)

    assert SOLVENCY_DEADLINE_HOURS == 6.0, (
        f"el margen ha cambiado a {SOLVENCY_DEADLINE_HOURS}: este "
        f"encargo no lo toca"
    )

    plazo = reloj["solvency_deadline"]

    assert plazo["source"] == "CALENDARIO", plazo
    assert plazo["at"].startswith("2026-10-09T14:45"), plazo["at"]

    assert reloj["hours_to_solvency_deadline"] == round(
        HORAS_AL_CIERRE - SOLVENCY_DEADLINE_HOURS, 2
    )


# ============================================================
# 3. SIN FECHA: "NO LO SE", Y FRENA
# ============================================================

def test_sin_calendario_dice_no_lo_se_y_frena() -> None:

    for reloj in (
        _reloj(real_deadline=None, horas=None),
        _reloj(real_deadline=None, horas=HORAS_AL_CIERRE),
        _reloj(real_deadline=CIERRE_J8, horas=None),
    ):
        plazo = reloj["solvency_deadline"]

        assert plazo["known"] is False, plazo
        assert plazo["at"] is None, plazo

        plan = _plan(reloj)

        assert plan["blocked_by"] == "SOLVENCIA", plan["blocked_by"]
        assert "No lo se" in (plan["reason"] or ""), plan["reason"]
        assert "viernes" not in (plan["reason"] or "").lower()


# ============================================================
# 4. APAGADO, COMO LLEGA: SIGUE CERRANDO Y LO DICE
# ============================================================

def test_apagado_el_deficit_sigue_cerrando_y_dice_que_hay_tiempo() -> None:

    assert not os.environ.get(SOLVENCIA_POR_SU_PLAZO_ENV)

    reloj = _reloj()

    _exige_calendario(reloj)

    plan = _plan(reloj)

    assert plan["blocked_by"] == "SOLVENCIA", plan["blocked_by"]
    assert plan["execute"] is False
    assert "Hay tiempo" in plan["reason"], plan["reason"]
    assert SOLVENCIA_POR_SU_PLAZO_ENV in plan["reason"], plan["reason"]


# ============================================================
# 5. ENCENDIDO: LEJOS NO FRENA, CERCA SI
# ============================================================

def test_encendido_lejos_no_frena_y_cerca_si() -> None:

    antes = os.environ.get(SOLVENCIA_POR_SU_PLAZO_ENV)

    try:
        os.environ[SOLVENCIA_POR_SU_PLAZO_ENV] = "1"

        lejos = _reloj()

        _exige_calendario(lejos)

        plan = _plan(lejos)

        assert plan["blocked_by"] != "SOLVENCIA", (
            f"a 16 dias y con el interruptor puesto sigue frenando "
            f"la solvencia: {plan['reason']}"
        )
        assert plan["bids"], (
            "lejos del plazo y con todo en verde no puja: esta "
            "prueba no distingue un freno de otro"
        )

        # Justo por debajo de un ciclo del Computer antes del
        # plazo: ya no da tiempo, y frena.
        cerca = _reloj(
            horas=SOLVENCY_DEADLINE_HOURS + COMPUTER_CYCLE_HOURS - 1
        )

        _exige_calendario(cerca)

        plan = _plan(cerca)

        assert plan["blocked_by"] == "SOLVENCIA", (
            f"a {COMPUTER_CYCLE_HOURS - 1:.0f} h del plazo no frena: "
            f"{plan['reason']}"
        )

        # Y sin fecha, frena aunque este puesto.
        plan = _plan(_reloj(real_deadline=None, horas=None))

        assert plan["blocked_by"] == "SOLVENCIA", plan["reason"]

    finally:
        if antes is None:
            os.environ.pop(SOLVENCIA_POR_SU_PLAZO_ENV, None)
        else:
            os.environ[SOLVENCIA_POR_SU_PLAZO_ENV] = antes


TESTS = [
    test_el_plazo_sale_del_calendario,
    test_el_plazo_es_el_cierre_menos_el_margen_de_siempre,
    test_sin_calendario_dice_no_lo_se_y_frena,
    test_apagado_el_deficit_sigue_cerrando_y_dice_que_hay_tiempo,
    test_encendido_lejos_no_frena_y_cerca_si,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL PLAZO SALE DEL CALENDARIO V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
