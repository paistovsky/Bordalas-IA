"""
El presupuesto del optimizador de cartera.

EL MISMO ERROR, EN OTRO SITIO
    `optimize_portfolio` es el motor que elige la mejor
    COMBINACION de fichajes del dia. Es el que soporta la idea de
    "fichar dos o tres atractivos".

    Su presupuesto operativo salia del SALDO menos una reserva del
    20 %. Con el saldo real del 16/08/2026:

        Saldo                    239.968 EUR
        Reserva                   47.993 EUR
        Presupuesto operativo    191.975 EUR

    El candidato mas barato de los diez costaba 440.000, asi que
    la salida era literalmente:

        "No se ha encontrado ninguna combinacion valida."

    Es el mismo fallo que tenia bid_engine: medir contra la caja
    cuando la capacidad de gasto en Biwenger es maximumBid, que ya
    lleva el limite de deuda dentro.

    Aparecio despues de arreglar bid_engine, porque hasta entonces
    no llegaba ni un candidato hasta aqui.

Ejecutar:
    python -m src.analysis.test_portfolio_budget_v1
"""

import src.analysis.portfolio_optimizer as optimizador

from src.analysis.portfolio_optimizer import (
    CASH_RESERVE_PERCENT,
    optimize_portfolio,
)


SALDO_REAL = 239_968
MAXIMUM_BID_REAL = 12_414_968

# Lo que daba el calculo viejo: 239.968 - 20 %.
PRESUPUESTO_VIEJO = 191_975


class SinRed:
    """
    `calculate_intelligent_bids` tira de red. Aqui solo se prueba
    la capa de presupuesto y combinatoria.
    """

    def __init__(self, candidatos):
        self.candidatos = candidatos
        self.previo = None

    def __enter__(self):
        self.previo = optimizador.calculate_intelligent_bids
        optimizador.calculate_intelligent_bids = (
            lambda snapshot, rival_intelligence=None: [
                dict(c) for c in self.candidatos
            ]
        )
        return self

    def __exit__(self, *args):
        optimizador.calculate_intelligent_bids = self.previo
        return False


def candidato(
    player_id: int,
    nombre: str,
    puja: int,
    score: int = 60,
    posicion: int = 3,
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "position": posicion,
        "suggested_bid": puja,
        "action": "PUJAR",
        "final_score": score,
        "intelligent_score": score,
        "external_risk": 0,
        "market_price": puja,
        "player_price": puja,
        "has_current_round_game": True,
        "matchday_need_score": 0,
        "structural_need_score": 0,
        "lineup_need_score": 50,
    }


def snapshot(
    balance: int = SALDO_REAL,
    maximum_bid: int = MAXIMUM_BID_REAL,
) -> dict:
    return {
        "my_team": [],
        "catalog": {"data": {"teams": {}, "players": {}}},
        "market": {
            "sales": [],
            "offers": [],
            "status": {
                "balance": balance,
                "maximumBid": maximum_bid,
            },
        },
    }


def optimizar(candidatos, snap=None, **kwargs):
    with SinRed(candidatos):
        return optimize_portfolio(
            snap or snapshot(),
            **kwargs,
        )


# ============================================================
# EL PRESUPUESTO
# ============================================================

def test_el_presupuesto_sale_de_la_capacidad_no_de_la_caja() -> None:
    resultado = optimizar([
        candidato(1, "Tenaglia", 3_340_000),
    ])

    esperado = MAXIMUM_BID_REAL - int(
        MAXIMUM_BID_REAL * CASH_RESERVE_PERCENT
    )

    assert resultado["available_budget"] == esperado, (
        f"El presupuesto deberia salir de maximumBid "
        f"({esperado:,}) y salio "
        f"{resultado['available_budget']:,}."
    )
    assert resultado["budget_source"] == "MAXIMUM_BID"
    assert resultado["available_budget"] > PRESUPUESTO_VIEJO * 10

    print(
        f"  OK  presupuesto {resultado['available_budget']:,} EUR "
        f"en vez de {PRESUPUESTO_VIEJO:,}".replace(",", ".")
    )


def test_el_escenario_real_ya_encuentra_combinacion() -> None:
    """
    Los diez candidatos reales del 16/08. Antes: ninguna
    combinacion valida.
    """
    reales = [
        candidato(1, "Toni Martinez", 7_190_000, score=95, posicion=4),
        candidato(2, "Sorloth", 5_120_000, score=75, posicion=4),
        candidato(3, "Batalla", 4_270_000, score=65, posicion=1),
        candidato(4, "Oluwaseyi", 440_000, score=65, posicion=4),
        candidato(5, "Tenaglia", 3_340_000, score=60, posicion=2),
    ]

    resultado = optimizar(reales)

    assert resultado["selected"], (
        f"Con {resultado['available_budget']:,} de presupuesto "
        f"deberia caber algo. Sigue sin encontrar combinacion."
    )
    assert resultado["total_cost"] > 0
    assert resultado["total_cost"] <= resultado["available_budget"]

    print(
        f"  OK  encuentra combinacion: "
        f"{[j['name'] for j in resultado['selected']]}"
    )


def test_se_puede_inyectar_el_presupuesto_bueno() -> None:
    """
    El presupuesto correcto es el del motor de especulacion, que
    ya descuenta las pujas vivas. El calculo interno es solo el
    respaldo.
    """
    resultado = optimizar(
        [candidato(1, "Tenaglia", 3_340_000)],
        available_budget=1_000_000,
    )

    assert resultado["available_budget"] == 1_000_000
    assert resultado["budget_source"] == "INYECTADO"
    assert not resultado["selected"], (
        "Con un millon no cabe una puja de 3,34 M."
    )

    print("  OK  el presupuesto inyectado manda sobre el interno")


def test_nunca_se_supera_la_puja_maxima_de_biwenger() -> None:
    """
    Aunque alguien inyecte un presupuesto enorme, Biwenger sigue
    poniendo el techo.
    """
    resultado = optimizar(
        [candidato(1, "Tenaglia", 3_340_000)],
        available_budget=999_000_000,
    )

    assert resultado["available_budget"] <= MAXIMUM_BID_REAL, (
        f"El presupuesto {resultado['available_budget']:,} supera "
        f"maximumBid."
    )

    print("  OK  maximumBid sigue siendo el techo")


def test_reproduce_el_bloqueo_del_presupuesto_viejo() -> None:
    """
    Deja constancia de lo que hacia el calculo anterior.
    """
    resultado = optimizar(
        [
            candidato(1, "Toni Martinez", 7_190_000, score=95),
            candidato(4, "Oluwaseyi", 440_000, score=65),
        ],
        available_budget=PRESUPUESTO_VIEJO,
    )

    assert not resultado["selected"], (
        "Con el presupuesto viejo no cabia nadie: si ahora cabe, "
        "este test ya no reproduce el fallo."
    )

    print(
        f"  OK  reproducido: con {PRESUPUESTO_VIEJO:,} EUR no "
        f"cabia nadie".replace(",", ".")
    )


def test_sin_maximum_bid_se_cae_al_saldo() -> None:
    """
    Si el snapshot llega sin maximumBid, mejor un presupuesto
    conservador que ninguno.
    """
    resultado = optimizar(
        [candidato(1, "Oluwaseyi", 100_000)],
        snap=snapshot(balance=SALDO_REAL, maximum_bid=0),
    )

    assert resultado["budget_source"] == "BALANCE"
    assert resultado["available_budget"] == (
        SALDO_REAL - int(SALDO_REAL * CASH_RESERVE_PERCENT)
    )

    print("  OK  sin maximumBid se usa el saldo como respaldo")


def test_un_presupuesto_negativo_no_se_propaga() -> None:
    resultado = optimizar(
        [candidato(1, "Tenaglia", 3_340_000)],
        available_budget=-5_000_000,
    )

    assert resultado["available_budget"] == 0
    assert not resultado["selected"]

    print("  OK  un presupuesto negativo se queda en cero")


# ============================================================

TESTS = [
    test_el_presupuesto_sale_de_la_capacidad_no_de_la_caja,
    test_el_escenario_real_ya_encuentra_combinacion,
    test_se_puede_inyectar_el_presupuesto_bueno,
    test_nunca_se_supera_la_puja_maxima_de_biwenger,
    test_reproduce_el_bloqueo_del_presupuesto_viejo,
    test_sin_maximum_bid_se_cae_al_saldo,
    test_un_presupuesto_negativo_no_se_propaga,
]


def main() -> None:
    print("=" * 60)
    print(" PRESUPUESTO DEL OPTIMIZADOR DE CARTERA")
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
