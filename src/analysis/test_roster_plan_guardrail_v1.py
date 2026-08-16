"""
El plan de plantilla y el guardarrail posicional.

QUE FALTABA
    `build_roster_plan` decide que vender para financiar los
    fichajes del dia. Recorria las ventas ordenadas por sale_score
    y acumulaba hasta cubrir el deficit, sin mirar de que posicion
    era cada una.

    Con un deficit grande podia vaciar la porteria o dejar la
    defensa en dos.

    El 16/08/2026 el plan salia legal -vendia un portero de dos-
    pero por suerte: nada lo comprobaba. Y ese dia el deficit era
    de 9,4 millones, asi que el bucle tenia motivos de sobra para
    seguir vendiendo.

POR QUE NO BASTA MIRAR CADA VENTA
    Vender un portero de dos es legitimo. Vender los dos, no. El
    guardarrail valida el CONJUNTO acumulado, asi que hay que
    preguntarle por la lista completa cada vez que se anade una
    venta.

Ejecutar:
    python -m src.analysis.test_roster_plan_guardrail_v1
"""

import src.analysis.roster_planner as planificador

from src.analysis.roster_planner import (
    build_roster_plan,
)


DITURO = 4587
BAYINDIR = 8123
JONNY = 1599
SUAZO = 9910
YERAY = 2044
RINCON = 6620
MANGALA = 21400
OLASA = 5521
JAVI = 4404
YAMAL = 26271


PLANTILLA = [
    {"id": DITURO, "name": "Dituro", "position": 1},
    {"id": BAYINDIR, "name": "Bayindir", "position": 1},
    {"id": JONNY, "name": "Jonny Castro", "position": 2},
    {"id": SUAZO, "name": "Gabriel Suazo", "position": 2},
    {"id": YERAY, "name": "Yeray", "position": 2},
    {"id": RINCON, "name": "Hugo Rincon", "position": 2},
    {"id": MANGALA, "name": "Mangala", "position": 3},
    {"id": OLASA, "name": "Olasagasti", "position": 3},
    {"id": JAVI, "name": "Javi Hernandez", "position": 3},
    {"id": YAMAL, "name": "Yamal", "position": 4},
]


class SinRed:
    """
    `optimize_portfolio` y `analyze_sales` tiran de red. Aqui solo
    se prueba la seleccion de ventas.
    """

    def __init__(self, compras, coste, ventas, balance=239_968):
        self.compras = compras
        self.coste = coste
        self.ventas = ventas
        self.balance = balance
        self.previos = {}

    def __enter__(self):
        self.previos["portfolio"] = planificador.optimize_portfolio
        self.previos["sales"] = planificador.analyze_sales

        planificador.optimize_portfolio = lambda snapshot: {
            "selected": self.compras,
            "total_cost": self.coste,
            "balance": self.balance,
            "cash_reserve": 0,
        }
        planificador.analyze_sales = (
            lambda snapshot: [dict(v) for v in self.ventas]
        )
        return self

    def __exit__(self, *args):
        planificador.optimize_portfolio = self.previos["portfolio"]
        planificador.analyze_sales = self.previos["sales"]
        return False


def venta(
    player_id: int,
    nombre: str,
    precio: int,
    score: int = 70,
) -> dict:
    return {
        "id": player_id,
        "name": nombre,
        "price": precio,
        "sale_score": score,
    }


def snapshot() -> dict:
    return {
        "my_team": [dict(j) for j in PLANTILLA],
        "market": {
            "status": {
                "balance": 239_968,
                "maximumBid": 12_414_968,
            },
        },
    }


def planificar(ventas, coste=9_000_000):
    with SinRed(
        compras=[{"name": "Toni Martinez", "suggested_bid": coste}],
        coste=coste,
        ventas=ventas,
    ):
        return build_roster_plan(snapshot())


def vendidos(plan) -> set:
    return {
        item["id"]
        for item in (
            plan["recommended_sales"]
            + plan["optional_sales"]
        )
    }


# ============================================================
# LA PORTERIA
# ============================================================

def test_no_se_venden_los_dos_porteros_para_financiar() -> None:
    """
    Deficit grande y los dos porteros arriba de la lista de
    ventas. Sin guardarrail, el bucle se los llevaba por delante.
    """
    plan = planificar([
        venta(DITURO, "Dituro", 3_530_000, score=90),
        venta(BAYINDIR, "Bayindir", 670_000, score=85),
        venta(JAVI, "Javi Hernandez", 310_000, score=80),
    ])

    salen = vendidos(plan)

    assert not {DITURO, BAYINDIR}.issubset(salen), (
        "REGRESION: el plan vende los dos porteros y deja la "
        "plantilla sin porteria."
    )
    assert plan["blocked_by_guardrail"], (
        "Deberia quedar constancia de la venta que se bloqueo."
    )

    print("  OK  no se venden los dos porteros")


def test_vender_un_portero_de_dos_si_se_permite() -> None:
    """
    El guardarrail no puede convertirse en un freno de mano.
    """
    plan = planificar([
        venta(BAYINDIR, "Bayindir", 670_000, score=85),
        venta(JAVI, "Javi Hernandez", 310_000, score=80),
    ])

    assert BAYINDIR in vendidos(plan), (
        "Con dos porteros, vender el suplente es legitimo."
    )

    print("  OK  vender el suplente sigue permitido")


def test_con_un_solo_portero_no_se_vende() -> None:
    plan_completo = planificar([
        venta(DITURO, "Dituro", 3_530_000, score=90),
    ])

    # Dituro es el unico que queda si Bayindir ya no esta.
    with SinRed(
        compras=[],
        coste=9_000_000,
        ventas=[venta(DITURO, "Dituro", 3_530_000, score=90)],
    ):
        snap = snapshot()
        snap["my_team"] = [
            j for j in snap["my_team"]
            if j["id"] != BAYINDIR
        ]
        plan = build_roster_plan(snap)

    assert DITURO not in vendidos(plan), (
        "Con un solo portero, venderlo deja la plantilla a cero."
    )

    print("  OK  el ultimo portero no entra en el plan de ventas")


# ============================================================
# LAS DEMAS POSICIONES
# ============================================================

def test_no_se_vacia_el_centro_del_campo() -> None:
    """
    Tres centrocampistas y el suelo es tres: no se puede vender
    ninguno.
    """
    plan = planificar([
        venta(MANGALA, "Mangala", 2_770_000, score=90),
        venta(OLASA, "Olasagasti", 2_740_000, score=85),
        venta(JAVI, "Javi Hernandez", 310_000, score=80),
        venta(RINCON, "Hugo Rincon", 670_000, score=75),
    ])

    salen = vendidos(plan)

    assert MANGALA not in salen
    assert OLASA not in salen
    assert JAVI not in salen, (
        "Con tres medios y suelo de tres, no cabe vender ninguno."
    )

    print("  OK  con el centro justo no se vende ningun medio")


def test_se_venden_los_defensas_que_sobran_y_no_mas() -> None:
    """
    Cuatro defensas, suelo tres: cabe uno.
    """
    plan = planificar([
        venta(RINCON, "Hugo Rincon", 670_000, score=90),
        venta(YERAY, "Yeray", 1_960_000, score=85),
        venta(SUAZO, "Gabriel Suazo", 1_730_000, score=80),
    ])

    defensas = {RINCON, YERAY, SUAZO}
    vendidos_defensa = vendidos(plan) & defensas

    assert len(vendidos_defensa) == 1, (
        f"Con 4 defensas y suelo 3 solo cabe vender 1. El plan "
        f"vende {len(vendidos_defensa)}."
    )

    print("  OK  de cuatro defensas se vende exactamente uno")


def test_el_bloqueo_deja_su_motivo() -> None:
    plan = planificar([
        venta(DITURO, "Dituro", 3_530_000, score=90),
        venta(BAYINDIR, "Bayindir", 670_000, score=85),
    ])

    bloqueos = plan["blocked_by_guardrail"]

    assert bloqueos
    assert all(item.get("reason") for item in bloqueos), (
        "Un bloqueo sin motivo es imposible de auditar."
    )
    assert any(
        "portero" in (item.get("reason") or "").lower()
        for item in bloqueos
    )

    print(
        f"  OK  el bloqueo explica por que: "
        f"{bloqueos[0]['reason']}"
    )


def test_las_ventas_opcionales_tambien_cuentan() -> None:
    """
    Las opcionales se ejecutarian ADEMAS de las necesarias. Si se
    validaran por separado, entre las dos listas podrian vaciar
    una posicion.
    """
    plan = planificar(
        [
            venta(BAYINDIR, "Bayindir", 670_000, score=90),
            venta(DITURO, "Dituro", 3_530_000, score=85),
        ],
        coste=100_000,
    )

    salen = vendidos(plan)

    assert not {DITURO, BAYINDIR}.issubset(salen), (
        "REGRESION: una lista vendio un portero y la otra el "
        "segundo."
    )

    print("  OK  necesarias y opcionales se validan juntas")


def test_sin_deficit_no_se_vende_por_liquidez() -> None:
    plan = planificar(
        [venta(BAYINDIR, "Bayindir", 670_000, score=90)],
        coste=0,
    )

    assert not plan["recommended_sales"], (
        "Sin deficit no hay ventas necesarias."
    )

    print("  OK  sin deficit no hay ventas por liquidez")


# ============================================================

TESTS = [
    test_no_se_venden_los_dos_porteros_para_financiar,
    test_vender_un_portero_de_dos_si_se_permite,
    test_con_un_solo_portero_no_se_vende,
    test_no_se_vacia_el_centro_del_campo,
    test_se_venden_los_defensas_que_sobran_y_no_mas,
    test_el_bloqueo_deja_su_motivo,
    test_las_ventas_opcionales_tambien_cuentan,
    test_sin_deficit_no_se_vende_por_liquidez,
]


def main() -> None:
    print("=" * 60)
    print(" PLAN DE PLANTILLA Y GUARDARRAIL")
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
