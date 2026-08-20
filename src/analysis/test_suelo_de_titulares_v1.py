"""
El suelo se mide en titulares, no en cuerpos.

EL CASO (20/08/2026)

    El dueño tuvo que intervenir a mano. Pepe habia acumulado
    catorce defensas y el plan de deuda proponia vender a Jutgla,
    uno de sus dos delanteros. Lo dijo en una linea:

        "El suelo tiene que ser para TITULARES."

    Y tenia razon. El suelo contaba CUERPOS: "tengo nueve
    defensas". Pero cuatro de esos nueve no juegan ni un minuto
    en su equipo.

    Un jugador que no juega no cubre nada. No da puntos, no tapa
    una baja y no sostiene una posicion. Contarlo hacia que la
    linea pareciera sobrada justo mientras el motor seguia
    comprando defensas.

LOS NUMEROS SON DEL DUEÑO

    Dos delanteros, dos medios, dos defensas y un portero. Es la
    columna vertebral, no la formacion.

LOS DOS SUELOS CONVIVEN

    POSITION_FLOOR   cuerpos, para que exista un once legal
    STARTER_FLOOR    titulares, para que ese once valga algo

    Sin el primero, Pepe podria quedarse con dos defensas en
    total y no poder alinear. Sin el segundo, con nueve defensas
    de los que solo juegan dos.
"""

from __future__ import annotations

from src.analysis.position_guardrail import (
    POSITION_FLOOR,
    STARTER_FLOOR,
    build_position_guardrail,
)


def plantilla():
    """
    La forma real del 20/08: nueve defensas de los que juegan
    cinco, cinco medios de los que juegan tres, dos delanteros que
    juegan los dos, y dos porteros de los que juega uno.
    """

    jugadores = []

    def add(player_id, posicion, nombre, en_el_once):
        jugadores.append({
            "id": player_id,
            "position": posicion,
            "name": nombre,
            "price": 1_000_000,
            "in_lineup": en_el_once,
        })

    for i in range(9):
        add(200 + i, 2, f"DEF{i}", i < 5)

    for i in range(5):
        add(300 + i, 3, f"MC{i}", i < 3)

    add(400, 4, "Jutglà", True)
    add(401, 4, "Yamal", True)

    add(100, 1, "Dituro", True)
    add(101, 1, "Bayindir", False)

    return jugadores


def guardarrail():
    jugadores = plantilla()

    return build_position_guardrail(
        jugadores,
        lineup_ids=[
            j["id"] for j in jugadores if j["in_lineup"]
        ],
    )


def test_los_numeros_del_dueño():
    """
    2 delanteros, 2 medios, 2 defensas, 1 portero.
    """

    assert STARTER_FLOOR == {1: 1, 2: 2, 3: 2, 4: 2}


def test_se_cuentan_los_que_juegan():
    """
    Nueve cuerpos y cinco titulares no son lo mismo, y la
    diferencia tiene que verse.
    """

    g = guardarrail()

    defensas = g["by_position"][2]

    assert defensas["owned"] == 9
    assert defensas["starters"] == 5, (
        "el guardarrail ha vuelto a contar cuerpos: una linea con "
        "suplentes de relleno parecera sobrada"
    )

    assert defensas["counted_on_starters"] is True


def test_los_dos_delanteros_no_se_tocan():
    """
    El caso de Jutgla. Dos delanteros, los dos titulares, suelo
    de dos: no se puede soltar ninguno.
    """

    g = guardarrail()

    vendibles = set(g.get("disposable_ids") or [])

    assert 400 not in vendibles, "Jutglà quedaria vendible"
    assert 401 not in vendibles, "Yamal quedaria vendible"

    assert g["by_position"][4]["disposable"] == 0


def test_el_portero_suplente_si_se_vende():
    """
    Decision explicita del dueño: "vender a Bayindir esta bien,
    no es titular".

    Con un portero titular el suelo se cumple, y el segundo
    portero no cubre nada que de puntos.
    """

    g = guardarrail()

    vendibles = set(g.get("disposable_ids") or [])

    assert 101 in vendibles, (
        "el portero suplente ha dejado de ser vendible: se esta "
        "protegiendo a alguien que no juega"
    )

    assert 100 not in vendibles, "Dituro es el titular, no se toca"


def test_los_defensas_de_sobra_se_sueltan():
    """
    Nueve defensas con cinco titulares y suelo de dos: hay mucho
    que soltar. Un guardarrail que lo bloquea todo con la caja en
    rojo es tan malo como no tenerlo.
    """

    g = guardarrail()

    assert g["by_position"][2]["disposable"] >= 6


def test_sin_once_conocido_no_se_paraliza():
    """
    El `my_team` crudo del snapshot no trae `in_lineup`.

    Si nadie pasa el once, el suelo de titulares no se aplica y
    manda el de cuerpos, como siempre. Menos exacto, pero sigue
    funcionando.
    """

    jugadores = [
        {"id": j["id"], "position": j["position"],
         "name": j["name"], "price": j["price"]}
        for j in plantilla()
    ]

    g = build_position_guardrail(jugadores)

    defensas = g["by_position"][2]

    assert defensas["counted_on_starters"] is False
    assert defensas["starters"] == 0
    assert defensas["disposable"] == 9 - POSITION_FLOOR[2]


def test_el_plan_de_deuda_obedece_al_guardarrail():
    """
    De nada sirve el suelo si el planificador no pregunta.

    Este era el fallo entero: `safe_debt_portfolio_engine`
    validaba "¿sigue habiendo once?" y con un delantero se alinea
    un 5-4-1 legal. La formacion aguantaba; el equipo no.
    """

    from src.analysis.safe_debt_portfolio_engine import (
        build_safe_liquidity_portfolio,
    )

    jugadores = []

    def add(player_id, posicion, nombre, precio):
        jugadores.append({
            "id": player_id,
            "name": nombre,
            "position": posicion,
            "price": precio,
            "points": 100,
            "pointsLastSeason": 100,
            "status": "ok",
        })

    for i in range(9):
        add(200 + i, 2, f"DEF{i}", 1_000_000)

    for i in range(5):
        add(300 + i, 3, f"MC{i}", 1_000_000)

    add(400, 4, "Jutglà", 4_000_000)
    add(401, 4, "Yamal", 20_000_000)
    add(100, 1, "Dituro", 3_000_000)
    add(101, 1, "Bayindir", 640_000)

    snapshot = {
        "my_team": jugadores,
        "catalog": {"data": {"players": {}}},
        "market": {"offers": [], "sales": []},
    }

    incoming = {
        "offers": [
            {
                "offer_id": 1,
                "amount": 4_200_000,
                "player_ids": [400],
                "players": [{"id": 400, "name": "Jutglà"}],
            },
            {
                "offer_id": 9,
                "amount": 640_000,
                "player_ids": [101],
                "players": [{"id": 101, "name": "Bayindir"}],
            },
        ] + [
            {
                "offer_id": 10 + i,
                "amount": 1_100_000,
                "player_ids": [200 + i],
                "players": [{"id": 200 + i, "name": f"DEF{i}"}],
            }
            for i in range(3)
        ]
    }

    cartera = build_safe_liquidity_portfolio(
        snapshot,
        incoming,
        {},
    )

    vendidos = set()

    for clave in ("tier_a", "trading_safe", "tier_b", "tier_c"):
        plan = cartera.get(clave) or {}
        for nombre in (plan.get("player_names") or []):
            vendidos.add(nombre)

    assert "Jutglà" not in vendidos, (
        "el plan de deuda vuelve a proponer vender un delantero "
        "titular de dos"
    )

    assert any(
        n.startswith("DEF") for n in vendidos
    ), (
        "el freno bloquea de mas: con nueve defensas tiene que "
        "poder soltar alguno"
    )


def main():

    pruebas = [
        test_los_numeros_del_dueño,
        test_se_cuentan_los_que_juegan,
        test_los_dos_delanteros_no_se_tocan,
        test_el_portero_suplente_si_se_vende,
        test_los_defensas_de_sobra_se_sueltan,
        test_sin_once_conocido_no_se_paraliza,
        test_el_plan_de_deuda_obedece_al_guardarrail,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Suelo de titulares: todo en verde.")


if __name__ == "__main__":
    main()
