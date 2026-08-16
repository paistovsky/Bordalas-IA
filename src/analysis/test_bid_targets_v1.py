"""
A quien se puede pujar y con que techo.

DOS DEFECTOS DEL MISMO MOTOR, DETECTADOS EL 16/08/2026

1. EL TECHO ERA LA MAGNITUD EQUIVOCADA

    budget_limit = int(balance * 0.45)

   Con el saldo real -239.968 EUR- eso daba 107.985. El jugador
   mas barato del mercado costaba 150.000, asi que los veinte
   salian como DEMASIADO CARO.

   En Biwenger la capacidad de gasto no es la caja: es maximumBid,
   que el juego calcula ya con el limite de deuda dentro. Medir
   contra el saldo era medir contra otra cosa.

   Antes: 0 pujables de 53. Despues: 10.

2. SE RECOMENDABA COMPRAR JUGADORES PROPIOS

   El motor evaluaba a 13 de los 15 de la plantilla como objetivos
   de compra. Jutgla salia PUJAR a 5.170.000 EUR.

   Los otros doce se libraban solo porque su score no llegaba a
   55. No habia ninguna comprobacion de propiedad: era suerte.

   Aguas abajo hay guardias, pero para entonces el jugador ya
   ocupa un puesto en el ranking y puede haber desplazado a un
   objetivo real.

Ejecutar:
    python -m src.analysis.test_bid_targets_v1
"""

from src.analysis.bid_engine import (
    calculate_bid_recommendations,
)


# Cifras reales del 16/08/2026.
SALDO_REAL = 239_968
MAXIMUM_BID_REAL = 12_414_968
TECHO_VIEJO = int(SALDO_REAL * 0.45)   # 107.985

TENAGLIA = 41100
JUTGLA = 7011
YAMAL = 26271


class RecomendacionesFalsas:
    """
    `generate_recommendations` tira de red y de varios motores.
    Aqui solo se prueba la capa de decision de bid_engine, asi que
    se sustituye por una lista fija.
    """

    def __init__(self, jugadores):
        self.jugadores = jugadores
        self.original = None

    def __enter__(self):
        import src.analysis.bid_engine as motor

        self.original = motor.generate_recommendations
        motor.generate_recommendations = (
            lambda snapshot: [dict(j) for j in self.jugadores]
        )
        return self

    def __exit__(self, *args):
        import src.analysis.bid_engine as motor

        motor.generate_recommendations = self.original
        return False


def candidato(
    player_id: int,
    nombre: str,
    precio: int,
    score: int = 60,
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "market_price": precio,
        "player_price": precio,
        "final_score": score,
        "price_increment": 0,
    }


def snapshot(
    my_team: list | None = None,
    balance: int = SALDO_REAL,
    maximum_bid: int = MAXIMUM_BID_REAL,
) -> dict:
    return {
        "my_team": my_team or [],
        "market": {
            "status": {
                "balance": balance,
                "maximumBid": maximum_bid,
            },
        },
    }


def recomendar(jugadores, snap, **kwargs):
    with RecomendacionesFalsas(jugadores):
        return calculate_bid_recommendations(snap, **kwargs)


def por_nombre(resultados, nombre):
    for item in resultados:
        if item.get("name") == nombre:
            return item
    raise AssertionError(f"{nombre} no aparece en el resultado.")


# ============================================================
# EL TECHO
# ============================================================

def test_el_escenario_real_ya_no_veta_a_todos() -> None:
    """
    Los precios reales del mercado del Computer del 16/08.
    """
    mercado = [
        candidato(1, "Tenaglia", 3_270_000),
        candidato(2, "Leo Roman", 4_930_000),
        candidato(3, "Oluwaseyi", 420_000),
        candidato(4, "Toni Martinez", 6_600_000, score=95),
    ]

    resultado = recomendar(mercado, snapshot())

    pujables = [
        item for item in resultado
        if item["action"] == "PUJAR"
    ]

    assert len(pujables) == 4, (
        f"Con maximumBid de {MAXIMUM_BID_REAL:,} los cuatro caben. "
        f"Salieron {len(pujables)}."
    )

    print("  OK  los cuatro objetivos reales son pujables")


def test_reproduce_el_veto_del_techo_viejo() -> None:
    """
    Deja constancia de lo que hacia el 45 % del saldo. Se pasa el
    techo antiguo a mano para poder compararlo.
    """
    mercado = [
        candidato(1, "Tenaglia", 3_270_000),
        candidato(3, "Oluwaseyi", 420_000),
    ]

    resultado = recomendar(
        mercado,
        snapshot(),
        budget_limit=TECHO_VIEJO,
    )

    caros = [
        item for item in resultado
        if item["action"] == "DEMASIADO CARO"
    ]

    assert len(caros) == 2, (
        f"Con el techo viejo de {TECHO_VIEJO:,} ninguno deberia "
        f"caber. Salieron {len(caros)} vetados."
    )

    print(
        f"  OK  reproducido: con {TECHO_VIEJO:,} EUR de techo no "
        f"cabia nadie".replace(",", ".")
    )


def test_maximum_bid_sigue_siendo_el_limite() -> None:
    """
    Quitar el veto no puede convertirse en pujar por encima de lo
    que Biwenger permite.
    """
    mercado = [
        candidato(1, "Budimir", 11_940_000, score=75),
    ]

    resultado = recomendar(mercado, snapshot())

    budimir = por_nombre(resultado, "Budimir")

    assert budimir["suggested_bid"] > MAXIMUM_BID_REAL
    assert budimir["action"] == "DEMASIADO CARO", (
        "Una puja por encima de maximumBid no es ejecutable."
    )

    print("  OK  por encima de maximumBid sigue siendo DEMASIADO CARO")


def test_se_puede_pasar_un_techo_mas_ajustado() -> None:
    mercado = [
        candidato(1, "Tenaglia", 3_270_000),
        candidato(3, "Oluwaseyi", 420_000),
    ]

    resultado = recomendar(
        mercado,
        snapshot(),
        budget_limit=1_000_000,
    )

    assert por_nombre(resultado, "Oluwaseyi")["action"] == "PUJAR"
    assert (
        por_nombre(resultado, "Tenaglia")["action"]
        == "DEMASIADO CARO"
    )

    print("  OK  quien llama puede imponer un techo mas ajustado")


# ============================================================
# JUGADORES PROPIOS
# ============================================================

def test_no_se_puja_por_un_jugador_propio() -> None:
    """
    El caso exacto: Jutgla es nuestro y salia PUJAR a 5,17 M.
    """
    mercado = [
        candidato(JUTGLA, "Jutgla", 4_830_000, score=75),
        candidato(TENAGLIA, "Tenaglia", 3_270_000),
    ]

    resultado = recomendar(
        mercado,
        snapshot(my_team=[{"id": JUTGLA, "name": "Jutgla"}]),
    )

    jutgla = por_nombre(resultado, "Jutgla")

    assert jutgla["action"] == "YA ES NUESTRO", (
        f"REGRESION: se recomendo comprar a un jugador propio "
        f"({jutgla['action']})."
    )
    assert jutgla["suggested_bid"] == 0
    assert jutgla["own_player"] is True

    print("  OK  un jugador propio no es objetivo de compra")


def test_los_ajenos_no_se_ven_afectados() -> None:
    mercado = [
        candidato(JUTGLA, "Jutgla", 4_830_000, score=75),
        candidato(TENAGLIA, "Tenaglia", 3_270_000),
    ]

    resultado = recomendar(
        mercado,
        snapshot(my_team=[{"id": JUTGLA}]),
    )

    tenaglia = por_nombre(resultado, "Tenaglia")

    assert tenaglia["action"] == "PUJAR"
    assert tenaglia["own_player"] is False

    print("  OK  filtrar los propios no toca a los demas")


def test_un_propio_caro_tampoco_pasa() -> None:
    """
    Yamal salia DEMASIADO CARO, que suena a bloqueo pero no lo es:
    lo bloqueaba el precio, no la propiedad. Si manana bajara de
    precio, volveria a colarse.
    """
    mercado = [
        candidato(YAMAL, "Yamal", 33_480_000, score=65),
    ]

    resultado = recomendar(
        mercado,
        snapshot(
            my_team=[{"id": YAMAL}],
            maximum_bid=99_000_000,
        ),
    )

    yamal = por_nombre(resultado, "Yamal")

    assert yamal["action"] == "YA ES NUESTRO", (
        "Con presupuesto de sobra, un jugador propio seguiria "
        "colandose si el unico freno fuese el precio."
    )

    print("  OK  un propio se bloquea por propiedad, no por precio")


def test_la_plantilla_entera_queda_marcada() -> None:
    plantilla = [
        {"id": indice} for indice in range(100, 115)
    ]

    mercado = [
        candidato(indice, f"Propio {indice}", 500_000)
        for indice in range(100, 115)
    ] + [
        candidato(TENAGLIA, "Tenaglia", 3_270_000),
    ]

    resultado = recomendar(
        mercado,
        snapshot(my_team=plantilla),
    )

    nuestros = [
        item for item in resultado
        if item["action"] == "YA ES NUESTRO"
    ]

    assert len(nuestros) == 15
    assert por_nombre(resultado, "Tenaglia")["action"] == "PUJAR"

    print("  OK  los 15 de la plantilla quedan marcados")


# ============================================================
# ROBUSTEZ
# ============================================================

def test_una_plantilla_ilegible_no_rompe_el_motor() -> None:
    """
    Si my_team viene sucio, lo peor seria dejar de recomendar
    nada. Se ignoran las entradas malas y se sigue.
    """
    mercado = [
        candidato(TENAGLIA, "Tenaglia", 3_270_000),
    ]

    for plantilla in (
        None,
        [],
        [{"sin_id": 1}],
        [{"id": None}],
        [{"id": "texto"}],
    ):
        resultado = recomendar(
            mercado,
            snapshot(my_team=plantilla),
        )

        assert (
            por_nombre(resultado, "Tenaglia")["action"] == "PUJAR"
        )

    print("  OK  una plantilla ilegible no bloquea las compras")


def test_score_bajo_sigue_siendo_no_pujar() -> None:
    mercado = [
        candidato(1, "Flojo", 500_000, score=40),
    ]

    resultado = recomendar(mercado, snapshot())

    assert por_nombre(resultado, "Flojo")["action"] == "NO PUJAR"
    assert por_nombre(resultado, "Flojo")["suggested_bid"] == 0

    print("  OK  un score bajo sigue descartando al jugador")


# ============================================================

TESTS = [
    test_el_escenario_real_ya_no_veta_a_todos,
    test_reproduce_el_veto_del_techo_viejo,
    test_maximum_bid_sigue_siendo_el_limite,
    test_se_puede_pasar_un_techo_mas_ajustado,
    test_no_se_puja_por_un_jugador_propio,
    test_los_ajenos_no_se_ven_afectados,
    test_un_propio_caro_tampoco_pasa,
    test_la_plantilla_entera_queda_marcada,
    test_una_plantilla_ilegible_no_rompe_el_motor,
    test_score_bajo_sigue_siendo_no_pujar,
]


def main() -> None:
    print("=" * 60)
    print(" OBJETIVOS DE PUJA Y TECHO")
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
