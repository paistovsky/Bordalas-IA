"""
Regresion del bloqueo de solvencia observado el 11/08/2026.

Sintoma: el autopiloto registraba durante dias
    balance: -4.651.032   (identico al centimo en cada ciclo)
    recovery_needed: true
    recovery_possible: true
    14 ofertas en mesa, TODAS con solvency_reserved: false
    y accion KEEP_GOOD_OFFER
    computer_accept_before_expiry_count: 0

Causa raiz doble:

1. calculate_offer_reservations() restaba EXPECTED_LIQUIDITY
   (dinero de jugadores listados que nadie habia comprado)
   de required_recovery. Con la plantilla entera listada
   secured_needed caia a 0 y no se reservaba NINGUNA oferta.

2. analyze_computer_offer() solo podia emitir
   ACCEPT_BEFORE_EXPIRY dentro de la rama
   "reserved and not reroll_safe". Sin reservas esa rama era
   inalcanzable y las 14 ofertas caian a KEEP_GOOD_OFFER.

Ejecutar:
    python -m src.analysis.test_solvency_deadlock_v1
"""

from src.analysis.solvency_engine import (
    calculate_offer_reservations,
)

from src.analysis import (
    computer_offer_reroll_engine as reroll,
)


# ============================================================
# ESCENARIO REAL DEL 11/08/2026
# ============================================================

BALANCE = -4_651_032

# Las 14 ofertas Computer que estaban en mesa, con su prima
# real respecto a valor de mercado.
OFERTAS_REALES = [
    (237035185, "Olasagasti", 2_655_600, 2.9),
    (1222723573, "Gustavo Puerta", 3_474_300, 0.7),
    (1408797889, "Alvaro Fidalgo", 1_147_400, 8.2),
    (1408797890, "Etta Eyong", 4_003_700, 1.9),
    (1408797891, "Dituro", 3_529_400, 2.6),
    (1408797892, "Mangala", 3_023_100, 4.6),
    (1408797893, "Yeray", 1_844_600, 1.4),
    (1408797894, "Gabriel Suazo", 1_646_700, 3.6),
    (1408797895, "Jonny Castro", 1_500_900, 0.7),
    (1408797896, "Ximo Navarro", 1_175_100, 2.2),
    (1408797897, "Hugo Rincon", 674_900, 0.7),
    (1408797898, "Rodrygo", 641_700, 0.3),
    (1408797899, "Valentin Gomez", 323_900, -1.8),
]


def construir_incoming() -> dict:
    return {
        "offers": [
            {
                "offer_id": offer_id,
                "amount": amount,
                "premium_percent": premium,
                "player_ids": [offer_id % 100000],
                "players": [
                    {
                        "name": name,
                        "franchise_score": 10,
                        "strategic_score": 10,
                    }
                ],
            }
            for offer_id, name, amount, premium in OFERTAS_REALES
        ],
        "secured_total": sum(
            amount for _, _, amount, _ in OFERTAS_REALES
        ),
    }


def construir_guarantee() -> dict:
    """
    Reproduce el estado que producia el bloqueo: la liquidez
    ESPERADA de los 17 listados tapaba de sobra la deuda.
    """
    return {
        "state": "GUARANTEED",
        "required_recovery": 4_651_032 + 500_000,
        "expected_liquidity": 20_700_000,
        "guaranteed_recovery": 69_263_400,
    }


# ============================================================
# TEST 1 - LA DEUDA REAL SE RESERVA CON DINERO REAL
# ============================================================

def test_reserva_cubre_deuda_real() -> None:

    reservations = calculate_offer_reservations(
        balance=BALANCE,
        incoming=construir_incoming(),
        guarantee=construir_guarantee(),
    )

    reserved_total = reservations["reserved_total"]
    reserved_ids = reservations["reserved_offer_ids"]
    deuda = -BALANCE

    assert reserved_ids, (
        "REGRESION: no se reservo ninguna oferta con saldo "
        "negativo. La liquidez esperada volvio a anular "
        "secured_needed."
    )

    assert reserved_total >= deuda, (
        f"REGRESION: reservado {reserved_total:,} < "
        f"deuda {deuda:,}. La deuda real quedo cubierta con "
        f"liquidez esperada."
    )

    assert reservations["debt_covered_by_secured"] is True

    print(
        f"  OK  reserva real {reserved_total:,} EUR "
        f"sobre deuda {deuda:,} EUR "
        f"({len(reserved_ids)} ofertas)"
    )


def test_sin_deuda_no_reserva() -> None:

    reservations = calculate_offer_reservations(
        balance=3_000_000,
        incoming=construir_incoming(),
        guarantee=construir_guarantee(),
    )

    assert reservations["reserved_offer_ids"] == []
    assert reservations["current_debt"] == 0
    assert reservations["debt_covered_by_secured"] is True

    print("  OK  saldo positivo no reserva nada")


# ============================================================
# TEST 2 - LA RAMA DE ACEPTACION ES ALCANZABLE
# ============================================================

def _analizar(
    reserved: bool,
    premium: float,
    hours_to_expiry,
    hours_to_deadline,
    reroll_safe: bool = True,
) -> dict:
    """
    Aisla analyze_computer_offer de la simulacion pesada:
    lo que se prueba aqui es el arbol de decision.
    """
    original_sim = reroll.simulate_guarantee_after_reroll
    original_exp = reroll.calculate_hours_to_expiry

    reroll.simulate_guarantee_after_reroll = (
        lambda offer, solvency: {
            "guaranteed_after_reroll": reroll_safe,
            "replacement": {"possible": True},
        }
    )
    reroll.calculate_hours_to_expiry = (
        lambda offer: hours_to_expiry
    )

    try:
        return reroll.analyze_computer_offer(
            offer={
                "offer_id": 999,
                "amount": 3_000_000,
                "premium_percent": premium,
                "player_ids": [1],
                "players": [{"name": "Test"}],
            },
            solvency={},
            reserved_offer_ids={999} if reserved else set(),
            history={},
            hours_to_deadline=hours_to_deadline,
        )
    finally:
        reroll.simulate_guarantee_after_reroll = original_sim
        reroll.calculate_hours_to_expiry = original_exp


def test_reservada_y_jornada_encima_se_acepta() -> None:
    """
    El caso exacto que fallaba: oferta buena, reserva activa,
    reroll_safe=True, sin caducidad cercana, pero con la
    jornada a 2 horas.
    """
    result = _analizar(
        reserved=True,
        premium=2.9,
        hours_to_expiry=40.0,
        hours_to_deadline=2.0,
        reroll_safe=True,
    )

    assert result["action"] == "ACCEPT_BEFORE_EXPIRY", (
        f"REGRESION: con la jornada a 2h la accion fue "
        f"{result['action']} en vez de ACCEPT_BEFORE_EXPIRY."
    )

    print("  OK  jornada a 2h fuerza la conversion")


def test_reservada_rerollsafe_no_cae_a_keep_good() -> None:
    """
    Antes del arreglo, reserved=True + reroll_safe=True
    se escapaba de la rama de reserva y terminaba en
    KEEP_GOOD_OFFER, perdiendo la reserva en silencio.
    """
    result = _analizar(
        reserved=True,
        premium=2.9,
        hours_to_expiry=40.0,
        hours_to_deadline=80.0,
        reroll_safe=True,
    )

    assert result["action"] != "KEEP_GOOD_OFFER", (
        "REGRESION: una oferta reservada volvio a caer en "
        "KEEP_GOOD_OFFER y perdio la reserva."
    )
    assert result["action"] == "KEEP_SOLVENCY_RESERVED"

    print("  OK  oferta reservada conserva su estado")


def test_caducidad_sigue_forzando_aceptacion() -> None:
    result = _analizar(
        reserved=True,
        premium=2.9,
        hours_to_expiry=3.0,
        hours_to_deadline=None,
        reroll_safe=False,
    )

    assert result["action"] == "ACCEPT_BEFORE_EXPIRY"

    print("  OK  caducidad proxima sigue forzando aceptacion")


def test_sin_presion_se_permite_reroll_de_debil() -> None:
    """
    La optimizacion legitima no se pierde: una oferta
    reservada pero claramente por debajo de mercado, sin
    presion de tiempo, sigue siendo candidata a reroll.
    """
    result = _analizar(
        reserved=True,
        premium=-5.0,
        hours_to_expiry=40.0,
        hours_to_deadline=80.0,
        reroll_safe=True,
    )

    assert result["action"] == "REROLL_CANDIDATE"
    assert result["can_reroll"] is True

    print("  OK  reroll de oferta debil sigue permitido")


def test_no_reservada_sin_deuda_se_conserva() -> None:
    result = _analizar(
        reserved=False,
        premium=2.9,
        hours_to_expiry=40.0,
        hours_to_deadline=2.0,
        reroll_safe=True,
    )

    assert result["action"] == "KEEP_GOOD_OFFER"

    print("  OK  sin reserva la jornada no fuerza ventas")


# ============================================================
# TEST 3 - CADENA COMPLETA
# ============================================================

def test_cadena_completa_desbloquea() -> None:
    """
    Reserva + decision juntas sobre el escenario del 11/08.
    Debe producir al menos una aceptacion.
    """
    reservations = calculate_offer_reservations(
        balance=BALANCE,
        incoming=construir_incoming(),
        guarantee=construir_guarantee(),
    )

    reserved_ids = set(reservations["reserved_offer_ids"])
    acciones = []

    for offer_id, name, amount, premium in OFERTAS_REALES:
        original_sim = reroll.simulate_guarantee_after_reroll
        original_exp = reroll.calculate_hours_to_expiry

        reroll.simulate_guarantee_after_reroll = (
            lambda offer, solvency: {
                "guaranteed_after_reroll": True,
                "replacement": {"possible": True},
            }
        )
        reroll.calculate_hours_to_expiry = lambda offer: 40.0

        try:
            result = reroll.analyze_computer_offer(
                offer={
                    "offer_id": offer_id,
                    "amount": amount,
                    "premium_percent": premium,
                    "player_ids": [offer_id % 100000],
                    "players": [{"name": name}],
                },
                solvency={},
                reserved_offer_ids=reserved_ids,
                history={},
                hours_to_deadline=1.8,
            )
        finally:
            reroll.simulate_guarantee_after_reroll = original_sim
            reroll.calculate_hours_to_expiry = original_exp

        acciones.append((name, amount, result["action"]))

    aceptadas = [
        (name, amount)
        for name, amount, action in acciones
        if action == "ACCEPT_BEFORE_EXPIRY"
    ]

    total = sum(amount for _, amount in aceptadas)

    assert aceptadas, (
        "REGRESION: la cadena completa no produjo ninguna "
        "aceptacion con la jornada encima."
    )
    assert total >= -BALANCE, (
        f"REGRESION: aceptado {total:,} < deuda {-BALANCE:,}."
    )

    print(
        f"  OK  cadena completa acepta {len(aceptadas)} "
        f"ofertas por {total:,} EUR "
        f"(saldo final {BALANCE + total:+,})"
    )
    for name, amount in aceptadas:
        print(f"        - {name}: {amount:,} EUR")


# ============================================================

TESTS = [
    test_reserva_cubre_deuda_real,
    test_sin_deuda_no_reserva,
    test_reservada_y_jornada_encima_se_acepta,
    test_reservada_rerollsafe_no_cae_a_keep_good,
    test_caducidad_sigue_forzando_aceptacion,
    test_sin_presion_se_permite_reroll_de_debil,
    test_no_reservada_sin_deuda_se_conserva,
    test_cadena_completa_desbloquea,
]


def main() -> None:
    print("=" * 60)
    print(" REGRESION BLOQUEO DE SOLVENCIA (11/08/2026)")
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
