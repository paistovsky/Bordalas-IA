"""
El acantilado del presupuesto especulativo.

EL FALLO
    `calculate_speculation_budget` tiene dos ramas: saldo negativo
    y saldo positivo. La de saldo negativo usa el margen de deuda
    segura. La de saldo positivo solo miraba la caja.

    Con los numeros reales del 16/08/2026:

        saldo               239.968 EUR
        margen de deuda  10.719.800 EUR

        presupuesto = 239.968 * 0,15 = 35.995 EUR
        -> por debajo del minimo -> BLOCKED / LOW_LIQUIDITY

    Con el mismo margen de deuda y saldo -1 EUR:

        presupuesto = 10.719.800 * 0,60 = 6.431.880 EUR

    Un euro de saldo cambiaba el presupuesto en seis millones y
    medio. Y al reves de como deberia: tener dinero salia peor que
    no tenerlo.

    Es justo el escenario del 16/08. Pepe tenia saldo positivo, un
    margen de deuda enorme, y no pujaba por nada.

POR QUE NO ES DOBLE CONTEO
    additional_debt_headroom = max_total_debt - current_debt, y
    current_debt es max(-saldo, 0). Con saldo positivo la deuda
    actual es cero, asi que caja y margen son dos bolsillos
    distintos. El techo real -maximumBid- se sigue respetando.

LO QUE NO SE RELAJA
    Las condiciones para usar deuda con saldo positivo son
    exactamente las mismas que con saldo negativo: garantia de
    solvencia, ventana de deuda abierta y deuda temporal
    autorizada. La mitad de este fichero verifica eso.

Ejecutar:
    python -m src.analysis.test_speculation_budget_v1
"""

from src.analysis.speculation_engine import (
    MAX_DEBT_SPECULATION_PERCENT,
    MAX_SPECULATION_BUDGET_PERCENT,
    MIN_SPECULATION_BUDGET,
    calculate_speculation_budget,
)


# Numeros reales del 16/08/2026.
SALDO_REAL = 239_968
HEADROOM_REAL = 10_719_800
MAXIMUM_BID_REAL = 25_000_000


def snapshot(
    balance: int,
    maximum_bid: int = MAXIMUM_BID_REAL,
) -> dict:
    return {
        "market": {
            "status": {
                "balance": balance,
                "maximumBid": maximum_bid,
            },
        },
    }


def solvencia(
    headroom: int = HEADROOM_REAL,
    guaranteed: bool = True,
    window_open: bool = True,
    debt_allowed: bool = True,
    hard_safety: bool = False,
) -> dict:
    return {
        "hard_safety": {"active": hard_safety},
        "solvency_guarantee": {
            "guaranteed": guaranteed,
            "state": "GUARANTEED" if guaranteed else "AT_RISK",
        },
        "max_safe_debt": {
            "additional_debt_headroom": headroom,
            "debt_window_open": window_open,
        },
        "temporary_debt": {"allowed": debt_allowed},
    }


def presupuesto(
    balance: int,
    **kwargs,
) -> dict:
    return calculate_speculation_budget(
        snapshot(
            balance,
            kwargs.pop("maximum_bid", MAXIMUM_BID_REAL),
        ),
        solvencia(**kwargs),
        None,
    )


# ============================================================
# EL ACANTILADO
# ============================================================

def test_el_escenario_real_ya_no_bloquea() -> None:
    """
    Los numeros exactos del dia que Pepe no pujo por nada.
    """
    resultado = presupuesto(SALDO_REAL)

    assert resultado["enabled"] is True, (
        f"REGRESION: con {SALDO_REAL:,} de saldo y "
        f"{HEADROOM_REAL:,} de margen de deuda, la especulacion "
        f"quedo bloqueada por {resultado.get('blocked_by')}."
    )
    assert resultado["total_budget"] > 1_000_000, (
        f"El presupuesto salio {resultado['total_budget']:,}, que "
        f"no da para ninguna operacion util."
    )

    print(
        f"  OK  escenario real: presupuesto "
        f"{resultado['total_budget']:,} EUR".replace(",", ".")
    )


def test_un_euro_de_saldo_no_cambia_seis_millones() -> None:
    """
    EL test. Compara los dos lados del acantilado.
    """
    en_deuda = presupuesto(-1)
    en_positivo = presupuesto(1)

    salto = abs(
        en_positivo["total_budget"]
        - en_deuda["total_budget"]
    )

    assert salto < 100_000, (
        f"REGRESION: el acantilado sigue ahi. Con -1 EUR el "
        f"presupuesto es {en_deuda['total_budget']:,} y con +1 EUR "
        f"es {en_positivo['total_budget']:,}. Salto de {salto:,}."
    )

    print(
        f"  OK  cruzar el cero mueve el presupuesto {salto:,} EUR"
        .replace(",", ".")
    )


def test_mas_saldo_nunca_da_menos_presupuesto() -> None:
    """
    Que tener dinero salga peor que no tenerlo es absurdo, y era
    literalmente lo que pasaba.
    """
    saldos = [
        -5_000_000,
        -1_000_000,
        -1,
        0,
        1,
        239_968,
        1_000_000,
        5_000_000,
        12_000_000,
    ]

    anterior = None
    anterior_saldo = None

    for saldo in saldos:

        actual = presupuesto(saldo)["total_budget"]

        if anterior is not None:
            assert actual >= anterior, (
                f"Con {saldo:,} de saldo el presupuesto "
                f"({actual:,}) es MENOR que con "
                f"{anterior_saldo:,} ({anterior:,})."
            )

        anterior = actual
        anterior_saldo = saldo

    print("  OK  el presupuesto nunca baja al subir el saldo")


def test_el_presupuesto_es_caja_mas_deuda() -> None:
    resultado = presupuesto(4_000_000)

    caja_esperada = int(
        4_000_000 * MAX_SPECULATION_BUDGET_PERCENT
    )
    deuda_esperada = int(
        HEADROOM_REAL * MAX_DEBT_SPECULATION_PERCENT
    )

    assert resultado["cash_budget"] == caja_esperada
    assert resultado["debt_budget"] == deuda_esperada
    assert resultado["total_budget"] == (
        caja_esperada + deuda_esperada
    ), (
        "El total deberia ser la suma de los dos bolsillos."
    )
    assert resultado["mode"] == "CASH_AND_DEBT"

    print("  OK  el total es caja + deuda, y se desglosa")


# ============================================================
# LO QUE NO SE PUEDE RELAJAR
# ============================================================

def test_sin_garantia_de_solvencia_no_hay_deuda() -> None:
    """
    La rama de saldo negativo exige SOLVENCY_GUARANTEE. La de
    saldo positivo tiene que exigir lo mismo, o habriamos abierto
    una puerta trasera.
    """
    resultado = presupuesto(
        SALDO_REAL,
        guaranteed=False,
    )

    assert resultado.get("debt_budget", 0) == 0, (
        "REGRESION: se autorizo deuda sin garantia de solvencia."
    )
    assert resultado["enabled"] is False

    print("  OK  sin garantia de solvencia no se toca la deuda")


def test_con_la_ventana_de_deuda_cerrada_no_hay_deuda() -> None:
    resultado = presupuesto(
        SALDO_REAL,
        window_open=False,
    )

    assert resultado.get("debt_budget", 0) == 0, (
        "REGRESION: se autorizo deuda con la ventana cerrada."
    )

    print("  OK  con la ventana cerrada no se toca la deuda")


def test_sin_permiso_temporal_no_hay_deuda() -> None:
    """
    Cerca del deadline la deuda temporal deja de autorizarse. Esa
    puerta tiene que cerrarse tambien con saldo positivo.
    """
    resultado = presupuesto(
        SALDO_REAL,
        debt_allowed=False,
    )

    assert resultado.get("debt_budget", 0) == 0, (
        "REGRESION: se autorizo deuda sin permiso temporal. Cerca "
        "del deadline esto endeuda al equipo sin margen para "
        "sanear."
    )

    print("  OK  sin permiso temporal no se toca la deuda")


def test_el_motivo_de_no_usar_deuda_se_explica() -> None:
    """
    Un bloqueo sin motivo obliga a leer codigo para entenderlo.
    """
    casos = [
        ({"guaranteed": False}, "SOLVENCY_GUARANTEE"),
        ({"window_open": False}, "ventana de deuda"),
        ({"debt_allowed": False}, "ventana temporal"),
        ({"headroom": 0}, "MAX_SAFE_DEBT"),
    ]

    for kwargs, fragmento in casos:
        resultado = presupuesto(SALDO_REAL, **kwargs)

        motivo = resultado.get("debt_unavailable_reason") or ""

        assert fragmento.lower() in motivo.lower(), (
            f"Con {kwargs} se esperaba un motivo que mencionara "
            f"'{fragmento}'. Salio: '{motivo}'"
        )

    print("  OK  cada bloqueo de deuda dice por que")


def test_hard_safety_sigue_bloqueando_todo() -> None:
    resultado = presupuesto(
        10_000_000,
        hard_safety=True,
    )

    assert resultado["enabled"] is False
    assert resultado["blocked_by"] == "HARD_SAFETY"
    assert resultado["total_budget"] == 0

    print("  OK  Hard Safety sigue bloqueando aunque haya caja")


def test_una_puja_franchise_activa_congela_todo() -> None:
    resultado = calculate_speculation_budget(
        snapshot(SALDO_REAL),
        solvencia(),
        {"player": {"name": "Mbappe"}},
    )

    assert resultado["enabled"] is False
    assert resultado["blocked_by"] == "FRANCHISE_ACTIVE_BID"

    print("  OK  una puja franchise activa congela la especulacion")


# ============================================================
# TECHOS
# ============================================================

def test_nunca_se_supera_la_puja_maxima_de_biwenger() -> None:
    """
    maximumBid es el techo real que impone el juego. Da igual lo
    que digan caja y margen.
    """
    resultado = presupuesto(
        8_000_000,
        maximum_bid=900_000,
    )

    assert resultado["total_budget"] <= 900_000, (
        f"El presupuesto {resultado['total_budget']:,} supera la "
        f"puja maxima de 900.000 que permite Biwenger."
    )

    print("  OK  maximumBid sigue siendo el techo")


def test_sin_caja_ni_margen_se_bloquea() -> None:
    resultado = presupuesto(
        50_000,
        headroom=0,
    )

    assert resultado["enabled"] is False
    assert resultado["blocked_by"] == "LOW_LIQUIDITY"
    assert resultado["total_budget"] == 0

    print("  OK  sin caja ni margen se bloquea, como debe")


def test_caja_sola_sigue_funcionando() -> None:
    """
    Sin margen de deuda el comportamiento tiene que ser el de
    antes: caja por su porcentaje y nada mas.
    """
    resultado = presupuesto(
        20_000_000,
        headroom=0,
    )

    assert resultado["enabled"] is True
    assert resultado["mode"] == "CASH"
    assert resultado["total_budget"] == int(
        20_000_000 * MAX_SPECULATION_BUDGET_PERCENT
    )

    print("  OK  con caja y sin margen se comporta como antes")


def test_el_minimo_sigue_vigente() -> None:
    resultado = presupuesto(
        100_000,
        headroom=100_000,
    )

    assert resultado["total_budget"] == 0, (
        f"Un presupuesto por debajo de "
        f"{MIN_SPECULATION_BUDGET:,} no sirve para nada y no "
        f"deberia habilitarse."
    )
    assert resultado["enabled"] is False

    print("  OK  el minimo operativo sigue vigente")


def test_saldo_negativo_no_ha_cambiado() -> None:
    """
    No he tocado esa rama, y este test lo deja fijado.
    """
    resultado = presupuesto(-3_000_000)

    assert resultado["mode"] == "DEBT"
    assert resultado["enabled"] is True
    assert resultado["total_budget"] == int(
        HEADROOM_REAL * MAX_DEBT_SPECULATION_PERCENT
    )

    print("  OK  la rama de saldo negativo sigue igual")


# ============================================================

TESTS = [
    test_el_escenario_real_ya_no_bloquea,
    test_un_euro_de_saldo_no_cambia_seis_millones,
    test_mas_saldo_nunca_da_menos_presupuesto,
    test_el_presupuesto_es_caja_mas_deuda,
    test_sin_garantia_de_solvencia_no_hay_deuda,
    test_con_la_ventana_de_deuda_cerrada_no_hay_deuda,
    test_sin_permiso_temporal_no_hay_deuda,
    test_el_motivo_de_no_usar_deuda_se_explica,
    test_hard_safety_sigue_bloqueando_todo,
    test_una_puja_franchise_activa_congela_todo,
    test_nunca_se_supera_la_puja_maxima_de_biwenger,
    test_sin_caja_ni_margen_se_bloquea,
    test_caja_sola_sigue_funcionando,
    test_el_minimo_sigue_vigente,
    test_saldo_negativo_no_ha_cambiado,
]


def main() -> None:
    print("=" * 60)
    print(" PRESUPUESTO ESPECULATIVO")
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
