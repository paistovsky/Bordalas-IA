"""
El motor PvP conectado al mercado del Computer.

QUE FALTABA
    `calculate_intelligent_bids` ya tenia logica competitiva, pero
    solo se activaba cuando el vendedor era otro manager.

    Los jugadores del Computer no tienen vendedor. Y son justo los
    que se disputan en subasta a ciegas contra toda la liga: el
    16/08/2026 eran 20 de los 53 del mercado. Para esos la puja
    salia de una escalera fija de primas sobre el precio
    -+8/6/4/2 %- que no miraba si alguien podia disputarnoslos.

    Resultado: pagabamos prima cuando nadie competia, y nos
    quedabamos cortos cuando si.

EL TECHO DELIBERADO DE ESTA VERSION
    La puja PvP no puede superar a la que habria hecho la
    escalera. Este cambio solo puede abaratar, nunca encarecer.

    No es timidez: es que sin el motor de mejora del XI no se
    puede distinguir un fichaje para el once de uno para revender,
    y pagar por encima de la escalera solo se justifica en el
    primer caso. Cuando exista, el techo se levanta para esos.

    Medido sobre el mercado real del 16/08 y con los rivales sin
    caja: 749.995 EUR de ahorro en una sola tanda de cinco pujas.

Ejecutar:
    python -m src.analysis.test_pvp_wiring_v1
"""

import src.analysis.intelligent_bid_engine as motor

from src.analysis.intelligent_bid_engine import (
    calculate_intelligent_bids,
)


YO = 14175949
TENAGLIA = 41100
JUTGLA = 7011

PRECIO_TENAGLIA = 3_270_000

# Lo que proponia la escalera fija para Tenaglia: +2 % por score
# 60, redondeado a bloques de 10.000.
ESCALERA_TENAGLIA = 3_340_000


class SinRed:
    """
    `calculate_bid_recommendations` y el chequeo externo tiran de
    red y de media aplicacion. Aqui solo se prueba la capa de
    decision.
    """

    def __init__(self, candidatos):
        self.candidatos = candidatos
        self.previos = {}

    def __enter__(self):
        self.previos["bids"] = motor.calculate_bid_recommendations
        self.previos["externo"] = motor.get_external_player_status

        motor.calculate_bid_recommendations = (
            lambda snapshot: [dict(c) for c in self.candidatos]
        )
        motor.get_external_player_status = (
            lambda snapshot, player: {"external_available": False}
        )
        return self

    def __exit__(self, *args):
        motor.calculate_bid_recommendations = self.previos["bids"]
        motor.get_external_player_status = self.previos["externo"]
        return False


def candidato(
    player_id: int = TENAGLIA,
    nombre: str = "Tenaglia",
    precio: int = PRECIO_TENAGLIA,
    puja: int = ESCALERA_TENAGLIA,
    accion: str = "PUJAR",
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "market_price": precio,
        "player_price": precio,
        "final_score": 60,
        "suggested_bid": puja,
        "action": accion,
        "premium_percent": 2.0,
        "trend_bonus_percent": 0.0,
        "budget_limit": 12_414_968,
        "affordable": True,
        "own_player": False,
    }


def venta_computer(player_id: int = TENAGLIA) -> dict:
    return {
        "player": {"id": player_id},
        "price": PRECIO_TENAGLIA,
        "until": 1786856400,
        "user": None,
    }


def venta_rival(player_id: int, rival_id: int = 999) -> dict:
    return {
        "player": {"id": player_id},
        "price": PRECIO_TENAGLIA,
        "until": 1786910890,
        "user": {"id": rival_id, "name": "Rival"},
    }


def snapshot(ventas: list, my_team: list | None = None) -> dict:
    return {
        "league": {"user": {"id": YO}},
        "my_team": my_team or [],
        "market": {
            "sales": ventas,
            "offers": [],
            "status": {
                "balance": 239_968,
                "maximumBid": 12_414_968,
            },
        },
    }


def rivales(
    maximum_bid: int,
    cuadra: bool = True,
    cuantos: int = 6,
) -> dict:
    return {
        "managers": [
            {
                "user_id": 100 + indice,
                "name": f"Rival {indice}",
                "maximum_bid": maximum_bid,
            }
            for indice in range(cuantos)
        ],
        "validation": {"exact": cuadra},
    }


def evaluar(candidatos, snap, rival_intelligence):
    with SinRed(candidatos):
        return calculate_intelligent_bids(
            snap,
            rival_intelligence=rival_intelligence,
            allow_external_checks=False,
        )


def uno(resultados, nombre="Tenaglia"):
    for item in resultados:
        if item.get("name") == nombre:
            return item
    raise AssertionError(f"{nombre} no aparece.")


# ============================================================
# SIN COMPETENCIA
# ============================================================

def test_sin_rivales_con_caja_se_paga_mercado_mas_uno() -> None:
    """
    El caso que mas dinero ahorra: nadie puede disputarnos al
    jugador y la escalera nos hacia pagar prima igualmente.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            rivales(maximum_bid=200_000),
        )
    )

    assert resultado["suggested_bid"] == PRECIO_TENAGLIA + 1, (
        f"Sin competencia deberia bastar {PRECIO_TENAGLIA + 1:,}. "
        f"Salio {resultado['suggested_bid']:,}."
    )
    assert resultado["legacy_suggested_bid"] == ESCALERA_TENAGLIA
    assert resultado["pvp_saving"] == (
        ESCALERA_TENAGLIA - PRECIO_TENAGLIA - 1
    )

    print(
        f"  OK  se paga {resultado['suggested_bid']:,} en vez de "
        f"{ESCALERA_TENAGLIA:,} (ahorro "
        f"{resultado['pvp_saving']:,})".replace(",", ".")
    )


def test_con_el_ledger_roto_no_se_puja_al_filo() -> None:
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            rivales(maximum_bid=200_000, cuadra=False),
        )
    )

    assert resultado["suggested_bid"] > PRECIO_TENAGLIA + 1, (
        "REGRESION: se pujo al minimo fiandose de un ledger que "
        "no cuadra."
    )
    assert resultado["pvp"]["ledger_trusted"] is False

    print(
        f"  OK  con el ledger roto se deja margen: "
        f"{resultado['suggested_bid']:,}".replace(",", ".")
    )


# ============================================================
# EL TECHO
# ============================================================

def test_nunca_se_paga_mas_que_la_escalera() -> None:
    """
    La garantia de esta version: solo puede abaratar.

    Con rivales ricos el motor PvP querria pagar mas para ganar la
    subasta, pero el techo lo impide y se queda en lo que habria
    pagado antes.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            rivales(maximum_bid=20_000_000),
        )
    )

    assert resultado["suggested_bid"] <= ESCALERA_TENAGLIA, (
        f"REGRESION: se pago {resultado['suggested_bid']:,}, mas "
        f"que la escalera ({ESCALERA_TENAGLIA:,})."
    )
    assert resultado["pvp_saving"] >= 0

    print(
        "  OK  con rivales ricos se paga la escalera, nunca mas"
    )


def test_el_techo_deja_constancia_de_lo_que_haria_falta() -> None:
    """
    Perder una subasta en silencio no ensena nada. Si el techo nos
    deja cortos, tiene que quedar escrito cuanto habria hecho
    falta: es el dato que justificara levantarlo.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            rivales(maximum_bid=20_000_000),
        )
    )

    pvp = resultado["pvp"]

    assert pvp["decision"] == "SUPERA_VALOR_RACIONAL"
    assert pvp["bid_needed"] > ESCALERA_TENAGLIA, (
        "Falta el dato de cuanto habria costado ganar."
    )

    print(
        f"  OK  queda escrito que ganar costaria "
        f"{pvp['bid_needed']:,}".replace(",", ".")
    )


# ============================================================
# A QUIEN SE LE APLICA
# ============================================================

def test_no_se_toca_a_los_vendidos_por_rivales() -> None:
    """
    Un jugador publicado por otro manager no es una subasta a
    ciegas: lo lleva el observer competitivo bilateral, que es
    otra cosa. El PvP no debe pisarlo.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_rival(TENAGLIA)]),
            rivales(maximum_bid=200_000),
        )
    )

    assert resultado["pvp"] is None, (
        "El PvP no debe aplicarse a ventas de rivales."
    )
    assert resultado["suggested_bid"] == ESCALERA_TENAGLIA

    print("  OK  las ventas de rivales las lleva el otro motor")


def test_no_se_toca_a_quien_no_esta_en_el_mercado() -> None:
    """
    Un jugador que no esta publicado no se puede fichar, asi que
    calcularle puja competitiva no tiene sentido.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([]),
            rivales(maximum_bid=200_000),
        )
    )

    assert resultado["pvp"] is None

    print("  OK  sin estar en el mercado no se calcula puja")


def test_no_se_toca_a_quien_no_ibamos_a_pujar() -> None:
    resultado = uno(
        evaluar(
            [
                candidato(
                    accion="NO PUJAR",
                    puja=0,
                )
            ],
            snapshot([venta_computer()]),
            rivales(maximum_bid=200_000),
        )
    )

    assert resultado["pvp"] is None
    assert resultado["suggested_bid"] == 0

    print("  OK  el PvP no crea pujas donde no las habia")


def test_sin_inteligencia_de_rivales_no_se_cambia_nada() -> None:
    """
    Sin datos de rivales no se puede saber quien compite, y
    suponer que nadie seria justo el error caro.
    """
    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            None,
        )
    )

    assert resultado["pvp"] is None
    assert resultado["suggested_bid"] == ESCALERA_TENAGLIA, (
        "Sin datos de rivales hay que mantener el comportamiento "
        "anterior, no pujar el minimo."
    )

    print("  OK  sin datos de rivales no se arriesga el minimo")


def test_pepe_no_cuenta_como_rival_al_pujar() -> None:
    """
    Pepe aparece en el listado de managers. Si se contara, su
    propia caja subiria la puja contra si mismo.
    """
    inteligencia = rivales(maximum_bid=200_000)
    inteligencia["managers"].append(
        {
            "user_id": YO,
            "name": "Pepe Bordalas",
            "maximum_bid": 12_414_968,
        }
    )

    resultado = uno(
        evaluar(
            [candidato()],
            snapshot([venta_computer()]),
            inteligencia,
        )
    )

    assert resultado["suggested_bid"] == PRECIO_TENAGLIA + 1, (
        "REGRESION: Pepe se conto a si mismo como competencia y "
        "subio su propia puja."
    )

    print("  OK  Pepe no puja contra si mismo")


# ============================================================
# CONJUNTO
# ============================================================

def test_varios_jugadores_a_la_vez() -> None:
    candidatos = [
        candidato(TENAGLIA, "Tenaglia", 3_270_000, 3_340_000),
        candidato(2001, "Batalla", 4_050_000, 4_270_000),
        candidato(2002, "Oluwaseyi", 420_000, 440_000),
    ]

    ventas = [
        venta_computer(TENAGLIA),
        venta_computer(2001),
        venta_computer(2002),
    ]

    resultados = evaluar(
        candidatos,
        snapshot(ventas),
        rivales(maximum_bid=200_000),
    )

    ahorro = sum(item["pvp_saving"] for item in resultados)

    assert ahorro == (
        (3_340_000 - 3_270_001)
        + (4_270_000 - 4_050_001)
        + (440_000 - 420_001)
    ), f"El ahorro conjunto no cuadra: {ahorro:,}."

    print(
        f"  OK  tres pujas: {ahorro:,} EUR de ahorro".replace(
            ",", "."
        )
    )


def test_toda_puja_pvp_deja_su_razonamiento() -> None:
    resultados = evaluar(
        [candidato()],
        snapshot([venta_computer()]),
        rivales(maximum_bid=200_000),
    )

    pvp = uno(resultados)["pvp"]

    assert pvp.get("reasons"), "La puja PvP no explica por que."
    assert "competitor_count" in pvp

    print("  OK  la puja PvP viene con su motivo")


# ============================================================

TESTS = [
    test_sin_rivales_con_caja_se_paga_mercado_mas_uno,
    test_con_el_ledger_roto_no_se_puja_al_filo,
    test_nunca_se_paga_mas_que_la_escalera,
    test_el_techo_deja_constancia_de_lo_que_haria_falta,
    test_no_se_toca_a_los_vendidos_por_rivales,
    test_no_se_toca_a_quien_no_esta_en_el_mercado,
    test_no_se_toca_a_quien_no_ibamos_a_pujar,
    test_sin_inteligencia_de_rivales_no_se_cambia_nada,
    test_pepe_no_cuenta_como_rival_al_pujar,
    test_varios_jugadores_a_la_vez,
    test_toda_puja_pvp_deja_su_razonamiento,
]


def main() -> None:
    print("=" * 60)
    print(" PVP CONECTADO AL MERCADO DEL COMPUTER")
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
