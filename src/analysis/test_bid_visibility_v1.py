"""
Todo euro nuestro tiene una fila, y con el nombre de quien vende.

EL CASO QUE LO DESTAPO

    18/08/2026. La propia pantalla levanto la mano:

        Pujas vivas:  Biwenger 2, aqui 1
        Comprometido: Biwenger 2.531.501, aqui 2.068.001

    463.500 EUR nuestros, vivos, sin ninguna fila donde salir.
    El dueño leia el tablero y entendia "solo tengo una puja".

POR QUE PASABA

    Los dos numeros median universos distintos.

    `build_bid_exposure` lee `market.offers`: TODAS nuestras
    ofertas vivas, venda quien venda.

    `build_acquisition_board` recorria `market.sales` y saltaba
    todo lo que no vendiese el Computer:

        if venta.get("seller_user_id") is not None:
            continue

    Asi que una puja por el jugador de otro manager -o una oferta
    directa por uno que ni esta publicado- no tenia fila donde
    aparecer. No era un recorte: ese jugador no entraba en la
    lista.

LA REGLA NUEVA

    El mercado del Computer MAS todo aquello donde ya hay dinero
    nuestro. Lo segundo entra aunque lo venda un rival y aunque no
    este publicado.

    Y entra con NOMBRE. "Un rival" no informa de nada: de cada
    manager se sabe cuanto suele pagar, asi que saber si le pujas
    a Prinzipote o a Pollo17 cambia lo que esperas que pase.

LO QUE NO CAMBIA

    A quien se compra. Esas filas llevan `decision`
    PUJA_FUERA_DEL_COMPUTER, que no es BID, asi que
    `best_acquisition_target` no las elige. Se ven, no se
    persiguen.
"""

from __future__ import annotations

import inspect

from src.analysis.bid_exposure_engine import build_bid_exposure


NOSOTROS = 14175949


def _snapshot(ofertas: list) -> dict:
    return {
        "league": {"user": {"id": NOSOTROS}},
        "market": {
            "status": {"balance": 0},
            "sales": [],
            "offers": ofertas,
        },
        "my_team": [],
    }


def test_la_puja_dice_a_quien():
    """
    Cada puja viva sabe si es al Computer o a quien.
    """

    snapshot = _snapshot(
        [
            {
                "id": 1,
                "amount": 2_068_001,
                "status": "waiting",
                "type": "purchase",
                "from": {"id": NOSOTROS},
                "to": None,
                "requestedPlayers": [100],
            },
            {
                "id": 2,
                "amount": 463_500,
                "status": "waiting",
                "type": "purchase",
                "from": {"id": NOSOTROS},
                "to": {"id": 99, "name": "Prinzipote"},
                "requestedPlayers": [200],
            },
        ]
    )

    exposicion = build_bid_exposure(
        snapshot,
        own_user_id=NOSOTROS,
    )

    assert exposicion["operation_count"] == 2
    assert exposicion["committed_total"] == 2_531_501

    por_jugador = {
        operacion["player_ids"][0]: operacion
        for operacion in exposicion["operations"]
    }

    # Al Computer: no hay manager, y eso es un dato, no un hueco.
    assert por_jugador[100]["counterparty_id"] is None
    assert por_jugador[100]["counterparty_name"] is None

    # A un manager: con nombre y con id.
    assert por_jugador[200]["counterparty_id"] == 99
    assert por_jugador[200]["counterparty_name"] == "Prinzipote"


def test_ninguna_puja_se_queda_sin_fila():
    """
    El tablero mira el mercado del Computer Y donde hay dinero.

    Se comprueba sobre el codigo, no sobre datos: montar un
    snapshot con catalogo, valoracion y modelo de puja completo
    para esto seria un test de otra cosa. Lo que hay que impedir
    es que vuelva el `continue` seco que dejaba las pujas fuera.
    """

    from src.analysis import acquisition_board

    fuente = inspect.getsource(
        acquisition_board.build_acquisition_board
    )

    # 1. Que el filtro por vendedor no vuelva a ser incondicional.
    assert (
        "outside_computer_market" in fuente
    ), (
        "el tablero ha vuelto a ser solo el mercado del "
        "Computer: las pujas a managers se pierden"
    )

    # 2. Que la excepcion sea justo esa -hay puja nuestra- y no
    #    que se cuele el mercado entero de los rivales.
    assert "not in puja_viva" in fuente, (
        "un mercado ajeno solo entra si ya hay dinero nuestro "
        "dentro; si no, esta tabla deja de ser la del Computer"
    )

    # 3. Que esas filas no sean objetivos de compra.
    assert "PUJA_FUERA_DEL_COMPUTER" in fuente

    assert "BID" in fuente


def test_esas_filas_no_se_persiguen():
    """
    Ver una puja no es querer hacerla.

    `best_acquisition_target` elige entre filas con
    `decision == "BID"`. Las filas nuevas llevan otra decision a
    proposito: si algun dia alguien las marcase BID, Pepe se
    pondria a comprar en las listas de los rivales sin que nadie
    lo hubiese decidido.
    """

    from src.analysis.decision_orchestrator import (
        best_acquisition_target,
    )

    tablero = {
        "available": True,
        "targets": [
            {
                "id": 200,
                "name": "El de Prinzipote",
                "decision": "PUJA_FUERA_DEL_COMPUTER",
                "bid": 463_500,
                "live_bid": 463_500,
                "expected_value": 9_999_999,
                "seller_name": "Prinzipote",
            },
        ],
    }

    assert best_acquisition_target(tablero) is None, (
        "Pepe se ha puesto a comprar fuera del mercado del "
        "Computer"
    )


def main():

    pruebas = [
        test_la_puja_dice_a_quien,
        test_ninguna_puja_se_queda_sin_fila,
        test_esas_filas_no_se_persiguen,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Visibilidad de pujas: todo en verde.")


if __name__ == "__main__":
    main()
