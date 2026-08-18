"""
Una oferta buena por alguien que sobra se cobra.

LO QUE SE ENCONTRO (auditoria del 18/08/2026)

    Doce ofertas del Computer sobre la mesa, 44,15 millones, con
    el saldo en -1,46. Entre ellas Alvaro Fidalgo: 75 sobre 100
    en puntuacion de venta, suplente, Rotacion, y la mejor prima
    de las doce (+4,4 % sobre su precio).

    Se iba a quedar en plantilla y la oferta iba a caducar.

POR QUE

    El arbol de decision estaba en este orden:

        1. NEVER_AUTO_SELL / franquicia   -> NEVER_SELL
        2. es del COMPUTER                -> solo ACCEPT_FOR_SOLVENCY
        3. prima EXCELENTE y venta >= 45  -> ACCEPT_NOW
        4. prima BUENA y venta >= 60      -> ACCEPT_NOW

    Las dos reglas que si saben decidir con criterio -3 y 4-
    estaban DEBAJO de la rama del Computer, que se las comia
    antes. Solo se aplicaban a ofertas de managers, y no habia
    ninguna.

    Para el Computer el unico camino a aceptar era
    ACCEPT_FOR_SOLVENCY, que exige dos cosas a la vez: oferta
    reservada para tapar un agujero Y menos de seis horas para
    que caduque. Pepe solo vendia al Computer cuando le faltaba
    el dinero y se le acababa el tiempo. Nunca por buen precio.

SIN VETO DE JERARQUIA, A PROPOSITO

    `sale_intent` si veta a los Dios, los Clave y al portero
    titular, porque ahi Pepe vende por iniciativa propia. Aqui
    reacciona a una oferta, y la regla del dueño para eso es
    otra: "Yamal solo se vende si cae por lesion o sancion
    larga". Un Dios roto es justo el caso en que hay que
    venderlo.

    Quien protege aqui es la puntuacion de venta, que ya mira la
    jerarquia.
"""

from __future__ import annotations

from src.analysis.offer_decision_engine import (
    ACCEPT_BENCH_SALE_SCORE,
    ACCEPT_CLEAR_SALE_SCORE,
    classify_offer_quality,
    sale_is_worth_it,
)


def test_la_regla_cobra_lo_que_sobra():
    """
    Prima buena y jugador claramente vendible: se cobra.
    """

    compensa, motivo = sale_is_worth_it(
        quality="GOOD",
        sale_score=ACCEPT_CLEAR_SALE_SCORE,
        in_lineup=False,
    )

    assert compensa
    assert motivo

    # Y tambien si esta en el once: si su puntuacion de venta
    # pasa de 60 es que ya no deberia estar ahi.
    assert sale_is_worth_it(
        quality="GOOD",
        sale_score=ACCEPT_CLEAR_SALE_SCORE,
        in_lineup=True,
    )[0]

    # Un suplente con prima excelente entra con menos exigencia:
    # soltarlo no toca el once.
    assert sale_is_worth_it(
        quality="EXCELLENT",
        sale_score=ACCEPT_BENCH_SALE_SCORE,
        in_lineup=False,
    )[0]

    # Pero ese atajo NO vale para un titular.
    assert not sale_is_worth_it(
        quality="EXCELLENT",
        sale_score=ACCEPT_BENCH_SALE_SCORE,
        in_lineup=True,
    )[0]


def test_no_se_regala_nada():
    """
    Ni por debajo de precio ni por alguien que no sobra.
    """

    # Prima insuficiente, aunque el jugador sobre.
    assert not sale_is_worth_it(
        quality="FAIR",
        sale_score=100,
        in_lineup=False,
    )[0]

    assert not sale_is_worth_it(
        quality="BELOW_MARKET",
        sale_score=100,
        in_lineup=False,
    )[0]

    # Prima buenisima por alguien que no sobra.
    assert not sale_is_worth_it(
        quality="EXCELLENT",
        sale_score=0,
        in_lineup=True,
    )[0]


def test_las_doce_ofertas_reales():
    """
    Sobre los datos del 18/08: se cobra una, y la correcta.

    Es el caso completo, con las primas medidas contra el precio
    de mercado y las puntuaciones que da `sales_analyzer`.
    """

    OFERTAS = [
        # nombre,           prima, venta, en el once
        ("Alvaro Fidalgo",   4.4,   75,   False),
        ("Jutgla",           3.6,    0,   True),
        ("Yamal",            3.4,    0,   True),
        ("Dituro",           2.7,    0,   True),
        ("Ximo Navarro",     2.1,   30,   True),
        ("Yeray",            1.8,   40,   True),
        ("Valentin Gomez",   1.7,   50,   False),
        ("Javi Hernandez",   1.2,   40,   True),
        ("Bayindir",         0.8,   60,   False),
        ("Olasagasti",       0.5,    0,   True),
        ("Mangala",          0.3,   30,   True),
        ("Gabriel Suazo",   -1.2,    0,   True),
    ]

    aceptadas = [
        nombre
        for nombre, prima, venta, once in OFERTAS
        if sale_is_worth_it(
            quality=classify_offer_quality(prima),
            sale_score=venta,
            in_lineup=once,
        )[0]
    ]

    assert aceptadas == ["Alvaro Fidalgo"], (
        f"se esperaba cobrar solo a Fidalgo y se cobra "
        f"{aceptadas}"
    )

    # Lo importante del caso: 23 millones por Yamal no lo mueven.
    assert "Yamal" not in aceptadas

    # Y Bayindir tampoco, aunque sobre: la prima es floja y se
    # puede pedir otra oferta mejor.
    assert "Bayindir" not in aceptadas


def test_el_computer_llega_a_la_regla():
    """
    Que la rama del Computer no se coma la decision otra vez.

    Se comprueba sobre el codigo porque montar el snapshot
    completo -reroll, solvencia, negociaciones- seria un test de
    otra cosa. Lo que hay que impedir es que la rama vuelva a
    terminar sin preguntarse si compensa cobrar.
    """

    import inspect

    from src.analysis import offer_decision_engine

    fuente = inspect.getsource(
        offer_decision_engine.decide_incoming_offer
    )

    computer = fuente.split('counterparty_type == "COMPUTER"')[1]

    # La rama del Computer, hasta que empieza la de managers.
    computer = computer.split("OFERTAS DE OTROS MANAGERS")[0]

    assert "sale_is_worth_it(" in computer, (
        "la rama del Computer ha vuelto a decidir sin preguntar "
        "si la oferta compensa: se repite el caso Fidalgo"
    )

    # Y que no vuelva el doble regimen: la rama tiene que entrar
    # para TODA oferta del Computer, tenga o no entrada de reroll.
    assert (
        'counterparty_type == "COMPUTER"\n        and\n        reroll_offer is not None'
        not in fuente
    ), (
        "ha vuelto el `reroll_offer is not None`: la misma oferta "
        "se juzga con dos varas segun si otro motor opino"
    )


def test_una_sola_regla_para_los_dos_caminos():
    """
    El criterio no puede estar escrito dos veces.

    Estaba: a mano en la rama de managers y en ningun sitio en la
    del Computer. Dos copias divergen; una sola, no.
    """

    import inspect

    from src.analysis import offer_decision_engine

    fuente = inspect.getsource(
        offer_decision_engine.decide_incoming_offer
    )

    # Los umbrales viven en la funcion, no sueltos en las ramas.
    assert "sale_score >= 60" not in fuente, (
        "el corte de 60 ha vuelto a escribirse a mano en una rama"
    )

    assert "sale_score >= 45" not in fuente, (
        "el corte de 45 ha vuelto a escribirse a mano en una rama"
    )

    assert fuente.count("sale_is_worth_it(") >= 2, (
        "solo un camino usa la regla comun"
    )


def main():

    pruebas = [
        test_la_regla_cobra_lo_que_sobra,
        test_no_se_regala_nada,
        test_las_doce_ofertas_reales,
        test_el_computer_llega_a_la_regla,
        test_una_sola_regla_para_los_dos_caminos,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Cobrar ofertas: todo en verde.")


if __name__ == "__main__":
    main()
