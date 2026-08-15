"""
Regresion del doble conteo del ledger de rivales.

Detectado el 15/08/2026 al ejecutar test_rival_intelligence_v2.

SINTOMA
    Saldo oficial de Pepe:  239.968 EUR
    Saldo del ledger:   -27.857.464 EUR
    Diferencia:         -28.097.432 EUR

    La diferencia coincidia AL CENTIMO con los gastos oficiales:
    el ledger restaba los gastos dos veces.

CAUSA
    El tablon de Biwenger devuelve la misma operacion bajo dos
    event_id distintos. El fichaje de Yamal por 24.897.600
    aparecia en los eventos 01172994d5b4 y 5748a8232cb8, con la
    misma fecha y el mismo importe.

    Deduplicar por event_id no sirve: son distintos. Habia que
    hacerlo por el contenido economico de la operacion.

    Afectaba a tres compras -Yamal, Jonny Castro y Gabriel
    Suazo-, que sumaban exactamente los 28.097.432 del desfase.

CONSECUENCIA REAL
    De ese saldo sale la estimacion de cuanto puede pujar cada
    rival. Con el ledger descuadrado, tres managers salian con
    puja maxima 0 EUR mientras el mismo informe registraba pujas
    suyas de entre 10 y 22 millones.

Ejecutar:
    python -m src.analysis.test_ledger_dedup_v1
"""

from src.analysis.rival_intelligence_engine import (
    KNOWN_NON_ECONOMIC_TYPES,
    betting_pool_is_economic,
    build_rival_intelligence,
)


PEPE = 14175949
YAMAL = 26271
IMPORTE_YAMAL = 24_897_600
FECHA = 1786338346
INICIAL = 23_300_000


def _usuarios() -> list[dict]:
    return [
        {"id": PEPE, "name": "Pepe Bordalas", "points": 0},
    ]


def _perfiles() -> list[dict]:
    return [
        {
            "id": PEPE,
            "name": "Pepe Bordalas",
            "players": [
                {"id": YAMAL, "owner": {"id": PEPE}},
            ],
        },
    ]


def _catalogo() -> dict:
    return {
        "data": {
            "players": {
                str(YAMAL): {
                    "id": YAMAL,
                    "name": "Yamal",
                    "price": 22_360_000,
                },
            },
        },
    }


def _compra(event_id: str) -> dict:
    """
    Una compra de Yamal. Cambiando el event_id se reproduce
    exactamente lo que hace el tablon real: la misma operacion
    publicada dos veces.
    """
    return {
        "event_id": event_id,
        "date": FECHA,
        "type": "market",
        "content": [
            {
                "player": YAMAL,
                "amount": IMPORTE_YAMAL,
                "to": {"id": PEPE, "name": "Pepe Bordalas"},
                "bids": [],
            },
        ],
    }


def _finanzas() -> dict:
    return {
        "initialBalance": INICIAL,
        "earnings": {"total": 0},
        "expenses": {"total": IMPORTE_YAMAL},
    }


def _construir(eventos: list[dict]) -> dict:
    return build_rival_intelligence(
        events=eventos,
        users=_usuarios(),
        profiles=_perfiles(),
        catalog=_catalogo(),
        current_user_id=PEPE,
        own_finances=_finanzas(),
        own_balance=INICIAL - IMPORTE_YAMAL,
        own_maximum_bid=None,
    )


def _pepe(resultado: dict) -> dict:
    for manager in resultado.get("managers", []):
        if int(manager.get("user_id") or manager.get("id") or 0) == PEPE:
            return manager
    raise AssertionError("Pepe no aparece en el resultado.")


# ============================================================
# EL DUPLICADO
# ============================================================

def test_una_compra_se_cuenta_una_vez() -> None:
    manager = _pepe(
        _construir([_compra("aaa")])
    )

    assert manager["expenses"] == IMPORTE_YAMAL, (
        f"Con un solo evento los gastos deberian ser "
        f"{IMPORTE_YAMAL}, no {manager['expenses']}."
    )

    print(f"  OK  una compra = {IMPORTE_YAMAL:,} EUR".replace(",", "."))


def test_la_misma_compra_duplicada_no_cuenta_dos_veces() -> None:
    """
    El caso exacto: dos event_id distintos, misma operacion.
    """
    manager = _pepe(
        _construir([
            _compra("01172994d5b4"),
            _compra("5748a8232cb8"),
        ])
    )

    assert manager["expenses"] == IMPORTE_YAMAL, (
        f"REGRESION: la compra duplicada se conto dos veces "
        f"({manager['expenses']} en vez de {IMPORTE_YAMAL}). "
        f"Deduplicar por event_id no basta: son distintos."
    )

    print(
        "  OK  dos eventos con la misma operacion cuentan una vez"
    )


def test_el_saldo_cuadra_con_el_duplicado() -> None:
    resultado = _construir([
        _compra("01172994d5b4"),
        _compra("5748a8232cb8"),
    ])

    validacion = resultado.get("validation", {}) or {}

    assert validacion.get("exact") is True, (
        f"REGRESION: el ledger no cuadra. "
        f"diferencia={validacion.get('difference')}"
    )
    assert validacion.get("difference") == 0

    print("  OK  el saldo reconstruido cuadra al euro")


def test_dos_compras_distintas_si_cuentan_las_dos() -> None:
    """
    La deduplicacion no puede tragarse operaciones legitimas.
    """
    otra = _compra("bbb")
    otra["date"] = FECHA + 3600
    otra["content"][0]["amount"] = 1_570_000
    otra["content"][0]["player"] = 1599

    manager = _pepe(
        _construir([_compra("aaa"), otra])
    )

    esperado = IMPORTE_YAMAL + 1_570_000

    assert manager["expenses"] == esperado, (
        f"REGRESION: la deduplicacion se comio una compra "
        f"legitima ({manager['expenses']} en vez de {esperado})."
    )

    print("  OK  dos compras distintas cuentan las dos")


def test_mismo_jugador_dos_fechas_cuenta_dos_veces() -> None:
    """
    Comprar, vender y volver a comprar al mismo jugador es
    legitimo: la huella incluye la fecha.
    """
    segunda = _compra("ccc")
    segunda["date"] = FECHA + 86_400

    manager = _pepe(
        _construir([_compra("aaa"), segunda])
    )

    assert manager["expenses"] == IMPORTE_YAMAL * 2, (
        "Dos compras del mismo jugador en fechas distintas son "
        "operaciones reales y deben contar las dos."
    )

    print("  OK  mismo jugador en fechas distintas cuenta dos veces")


# ============================================================
# TIPOS DE EVENTO NUEVOS
# ============================================================

def test_round_started_no_es_economico() -> None:
    assert "roundStarted" in KNOWN_NON_ECONOMIC_TYPES, (
        "roundStarted solo anuncia la jornada; sin darlo de alta "
        "deja el ledger en REVIEW_REQUIRED para siempre."
    )

    resultado = _construir([
        _compra("aaa"),
        {
            "event_id": "ddd",
            "date": FECHA,
            "type": "roundStarted",
            "content": {"round": {"id": 4899, "name": "Jornada 1"}},
        },
    ])

    assert "roundStarted" not in (
        resultado.get("unknown_types", {}) or {}
    )

    print("  OK  roundStarted no ensucia el ledger")


def test_quiniela_vacia_es_decorativa() -> None:
    contenido = {
        "pool": {
            "id": 626780,
            "credits": {"required": 1, "prizes": True},
            "prizes": [],
            "responses": [],
        },
    }

    assert betting_pool_is_economic(contenido) is False, (
        "Sin premios ni respuestas la quiniela no mueve saldo "
        "de liga: los credits son moneda aparte de Biwenger."
    )

    print("  OK  quiniela sin premios ni respuestas: decorativa")


def test_quiniela_con_reparto_si_se_revisa() -> None:
    """
    Lo importante de no meterla en la lista blanca a ciegas.
    """
    con_premios = {
        "pool": {
            "prizes": [{"user": PEPE, "amount": 500_000}],
            "responses": [],
        },
    }
    con_respuestas = {
        "pool": {
            "prizes": [],
            "responses": [{"user": PEPE}],
        },
    }

    assert betting_pool_is_economic(con_premios) is True
    assert betting_pool_is_economic(con_respuestas) is True

    print(
        "  OK  una quiniela con reparto SI se marca para revisar"
    )


def test_quiniela_vacia_no_deja_el_ledger_en_revision() -> None:
    resultado = _construir([
        _compra("aaa"),
        {
            "event_id": "eee",
            "date": FECHA,
            "type": "bettingPool",
            "content": {
                "pool": {"prizes": [], "responses": []},
            },
        },
    ])

    assert "bettingPool" not in (
        resultado.get("unknown_types", {}) or {}
    ), "Una quiniela vacia no deberia disparar REVIEW_REQUIRED."

    print("  OK  quiniela vacia no dispara revision")


# ============================================================

TESTS = [
    test_una_compra_se_cuenta_una_vez,
    test_la_misma_compra_duplicada_no_cuenta_dos_veces,
    test_el_saldo_cuadra_con_el_duplicado,
    test_dos_compras_distintas_si_cuentan_las_dos,
    test_mismo_jugador_dos_fechas_cuenta_dos_veces,
    test_round_started_no_es_economico,
    test_quiniela_vacia_es_decorativa,
    test_quiniela_con_reparto_si_se_revisa,
    test_quiniela_vacia_no_deja_el_ledger_en_revision,
]


def main() -> None:
    print("=" * 60)
    print(" DOBLE CONTEO DEL LEDGER DE RIVALES")
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
