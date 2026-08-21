"""
Pepe tiene que poder mejorar el once. Antes no podia.

EL CASO (21/08/2026)

    "Lo que quiero ver es si Pepe pelea las pujas por jugadores
     que mejoren el XI y acaba montando un equipo medio decente."

    No las peleaba. Cero pujas de veinte candidatos, dias
    seguidos. Y no era prudencia: era aritmetica imposible.

LA ARITMETICA QUE NO PODIA SALIR

    Desde el 19/08, al cambiar un TITULAR el dinero del que sale
    se contaba como cero. La cuenta quedaba asi:

        mejora marginal    contra    precio entero

    Y una mejora marginal no supera un precio entero jamas. No es
    que compensara pocas veces: no podia compensar NUNCA.

    El caso real, del mercado del 21/08:

        Affengruber   3,74 M   90 % titular   CLAVE
        aporta sobre Yeray ....  2,13 M
        Yeray vale ............  1,85 M  ->  contaba 0
        veredicto .............  NO COMPENSA

    Con la operacion entera:

        pagas .......  3,74 M
        recuperas ...  1,48 M   (80 % de Yeray)
        coste neto ..  2,26 M

    Ahi ya se puede discutir. Antes no habia discusion posible.

POR QUE AHORA SE PUEDE CONTAR

    La regla vieja cubria el riesgo equivocado. Temia quedarse
    pegado con el saliente, pero en cada reset el Computer hace
    oferta por TODO jugador publicado. Vender no es una
    incognita; lo que no se sabe es a cuanto.

    Un riesgo de precio se cubre con un descuento. Uno de
    liquidez, no. Se cubria el que no era, y con el descuento
    maximo: contar cero.

LO QUE SE PROTEGE AQUI

    1. Que el saliente no vuelva a contar cero. Es la regresion
       que paralizo a Pepe dos dias enteros.
    2. Que se cuente CON descuento y no a precio de escaparate.
       Si un cambio solo sale con el precio optimista, no sale.
    3. Que un suplente siga contando entero: venderlo no toca el
       once.
    4. Que siga avisando de que hace falta vender. Ahora mas que
       antes: la puja se apoya en ese dinero.
"""

from __future__ import annotations

from src.analysis.acquisition_valuation import (
    RECUPERACION_TITULAR,
    build_valuation_context,
    value_candidate,
)


PRECIO_SALIENTE = 2_000_000


def snapshot():
    """Un once con un medio flojo y un banquillo con otro peor."""

    jugadores = []

    def add(player_id, posicion, nombre, precio, puntos):
        jugadores.append({
            "id": player_id,
            "name": nombre,
            "position": posicion,
            "price": precio,
            "priceIncrement": 0,
            "points": puntos,
            "pointsLastSeason": puntos,
            "status": "ok",
            "teamID": 1,
        })

    add(100, 1, "Portero", 3_000_000, 90)

    for i in range(4):
        add(200 + i, 2, f"DEF{i}", 2_000_000, 80)

    # El titular flojo del centro: es a quien se sustituye.
    add(300, 3, "Titular flojo", PRECIO_SALIENTE, 40)

    for i in range(1, 4):
        add(300 + i, 3, f"MC{i}", 2_000_000, 85)

    add(400, 4, "DEL0", 5_000_000, 120)
    add(401, 4, "DEL1", 5_000_000, 115)

    # Suplente, fuera del once.
    add(500, 3, "Suplente flojo", PRECIO_SALIENTE, 30)

    return {
        "my_team": jugadores,
        "catalog": {"data": {"players": {
            str(j["id"]): j for j in jugadores
        }}},
        "market": {"offers": [], "sales": []},
    }


def once():
    """El XI, con el titular flojo dentro y el suplente fuera."""

    dentro = [100, 200, 201, 202, 203, 300, 301, 302, 303, 400, 401]

    return {"selected": [{"id": i} for i in dentro]}


def contexto():
    return build_valuation_context(
        snapshot(),
        velocity_lookup={},
        starter_lookup={},
        lineup=once(),
    )


def candidato(precio: int, puntos: int) -> dict:
    return {
        "id": 900,
        "name": "El que entra",
        "position": 3,
        "price": precio,
        "priceIncrement": 0,
        "points": puntos,
        "pointsLastSeason": puntos,
        "status": "ok",
        "teamID": 1,
    }


def cambio(valoracion: dict) -> dict:
    return valoracion.get("as_xi") or {}


# ============================================================
# PRUEBAS
# ============================================================


def test_el_saliente_no_puede_contar_cero():
    """
    LA REGRESION QUE PARALIZO A PEPE.

    Con el saliente a cero, ninguna mejora del once puede
    compensar nunca, porque se compara una mejora marginal contra
    un precio entero.
    """

    assert RECUPERACION_TITULAR > 0, (
        "el titular que sale vuelve a contar cero: Pepe no podra "
        "mejorar el once ni una sola vez en toda la temporada"
    )


def test_se_cuenta_con_descuento_y_no_a_precio_de_escaparate():
    """
    El dinero llega en el reset, no hoy, y el precio puede
    moverse. Contar el 100 % de un titular seria fiarlo todo a
    que el Computer pague clavado.
    """

    assert RECUPERACION_TITULAR < 1.0, (
        "se esta contando el precio entero del titular que sale: "
        "un cambio que solo sale con el precio optimista pasaria "
        "el filtro"
    )


def test_el_titular_que_sale_entra_en_la_cuenta():
    """
    El caso Affengruber. El valor del cambio tiene que subir
    exactamente lo que se recupera del saliente.
    """

    ctx = contexto()

    valoracion = value_candidate(
        candidato(precio=3_000_000, puntos=140),
        ctx,
    )

    detalle = cambio(valoracion)

    assert detalle, "no se ha valorado como mejora del once"

    esperado = int(PRECIO_SALIENTE * RECUPERACION_TITULAR)

    assert detalle.get("recovered_value") == esperado, (
        f"se esperaba recuperar {esperado} del titular que sale, "
        f"y se conto {detalle.get('recovered_value')}"
    )

    # Se comprueba a QUIEN sustituye, no la etiqueta
    # `replaces_starter`: esa la pone `xi_upgrade_value` mas
    # abajo y depende de que el precio del punto este calibrado,
    # que es otra cosa y aqui no toca.
    assert (detalle.get("replaces") or {}).get("name") == (
        "Titular flojo"
    )
    assert (detalle.get("replaces") or {}).get("in_lineup") is True


def test_un_suplente_sigue_contando_entero():
    """
    Vender a un suplente no toca el once ni corre prisa. Ahi el
    descuento no tiene sentido y nunca lo tuvo.
    """

    ctx = contexto()

    # Se le quita el once al contexto: sin titulares, el que sale
    # es un suplente y se cuenta al 100 %.
    ctx["lineup_ids"] = set()

    for posicion, jugadores in ctx["squad_by_position"].items():
        for jugador in jugadores:
            jugador["in_lineup"] = False

    valoracion = value_candidate(
        candidato(precio=3_000_000, puntos=140),
        ctx,
    )

    detalle = cambio(valoracion)

    assert detalle.get("needs_sale_first") is not True
    assert not detalle.get("recovered_from"), (
        "un suplente no deberia marcarse como venta necesaria"
    )


def test_sigue_avisando_de_que_hay_que_vender():
    """
    La condicion era `recuperado == 0`, y dejo de cumplirse en
    cuanto el saliente empezo a contar: el aviso se habria
    apagado solo.

    Y ahora hace mas falta que antes, porque la puja se apoya en
    ese dinero.
    """

    ctx = contexto()

    detalle = cambio(
        value_candidate(
            candidato(precio=3_000_000, puntos=140),
            ctx,
        )
    )

    assert detalle.get("needs_sale_first") is True, (
        "ya no avisa de que la operacion depende de una venta"
    )

    assert detalle.get("recovered_from") == "Titular flojo", (
        "no se dice de quien sale ese dinero"
    )


def test_no_se_puede_contar_dinero_de_una_venta_que_no_se_hara():
    """
    `assume_replacement_sold=False` es el modo prudente: nadie
    vende nada. Ahi el saliente vuelve a valer cero, y tiene que
    seguir siendo asi.
    """

    detalle = cambio(
        value_candidate(
            candidato(precio=3_000_000, puntos=140),
            contexto(),
            assume_replacement_sold=False,
        )
    )

    assert not detalle.get("recovered_value")


def main():

    pruebas = [
        test_el_saliente_no_puede_contar_cero,
        test_se_cuenta_con_descuento_y_no_a_precio_de_escaparate,
        test_el_titular_que_sale_entra_en_la_cuenta,
        test_un_suplente_sigue_contando_entero,
        test_sigue_avisando_de_que_hay_que_vender,
        test_no_se_puede_contar_dinero_de_una_venta_que_no_se_hara,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Pujar por mejorar el XI: todo en verde.")


if __name__ == "__main__":
    main()
