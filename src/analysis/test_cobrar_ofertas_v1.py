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



def test_la_tierra_de_nadie_se_resuelve():
    """
    Ni se cobra ni se cambia: eso ya no puede pasar.

    EL CASO

        Alvaro Fidalgo, 75 sobre 100 en venta, suplente. El
        Computer ofrecio 977.400 EUR, un +1,8 %. La pantalla dijo
        "Conservar buena oferta" y ahi se quedo con 33 horas por
        delante para caducar.

        Dos motores con dos definiciones de "buena":

            reroll:    prima >= 0 %  -> no la cambies
            decision:  prima >= 3 %  -> se puede cobrar

        Entre 0 y 3 la oferta era demasiado buena para pedir otra
        y demasiado floja para cobrarla. De las doce ofertas de
        aquel dia, OCHO caian ahi.
    """

    from src.analysis.offer_decision_engine import (
        LAST_CALL_HOURS,
        MAX_REROLLS_PER_PLAYER,
        resolve_dead_zone,
    )

    def caso(**kw):
        base = dict(
            premium_percent=1.8,
            sale_score=75,
            hours_to_expiry=33.5,
            rerolls_used=0,
            max_rerolls=MAX_REROLLS_PER_PLAYER,
            reroll_safe=True,
        )
        base.update(kw)
        return resolve_dead_zone(**base)

    # Con margen se persigue una mejor.
    accion, motivo = caso()

    assert accion == "REROLL_CANDIDATE"
    assert motivo

    # Sin tiempo se cobra: caducar da cero.
    assert caso(
        hours_to_expiry=LAST_CALL_HOURS - 1
    )[0] == "ACCEPT_NOW"

    # Sin rerolls tambien.
    assert caso(
        rerolls_used=MAX_REROLLS_PER_PLAYER
    )[0] == "ACCEPT_NOW"

    # Y si rerollear dejaria la caja sin cubrir, se cobra lo que
    # hay en vez de arriesgarla.
    assert caso(reroll_safe=False)[0] == "ACCEPT_NOW"

    # LO QUE NO TOCA ESTA RAMA
    #
    # Por debajo de mercado no se cobra ni corriendo: vender bajo
    # mercado no es cobrar, es regalar. De eso se encarga el
    # motor de reroll.
    assert caso(premium_percent=-1.2)[0] is None

    # Un jugador que no sobra se queda quieto: no hay prisa por
    # deshacerse de quien no molesta.
    assert caso(sale_score=0)[0] is None

    # Y una prima ya cobrable la coge `sale_is_worth_it`, no
    # esta rama.
    assert caso(premium_percent=4.4)[0] is None


def test_la_banda_esta_cableada():
    """
    Que la rama del Computer la consulte de verdad.
    """

    import inspect

    from src.analysis import offer_decision_engine

    fuente = inspect.getsource(
        offer_decision_engine.decide_incoming_offer
    )

    assert "resolve_dead_zone(" in fuente, (
        "la tierra de nadie ha vuelto: una oferta entre 0 y 3 % "
        "se quedara mirando hasta caducar"
    )

    # Y que se le pase el plazo de verdad, no un None perpetuo:
    # sin horas no hay ultima llamada y todo vuelve a caducar.
    assert "parse_hours_to_expiry(offer)" in fuente, (
        "no se le esta pasando cuanto queda para que caduque"
    )



def test_la_prima_llega_de_verdad():
    """
    La clave que lee el motor tiene que existir en la oferta.

    EL CASO (18/08/2026, la misma tarde)

        Con el orden de las ramas ya arreglado, Alvaro Fidalgo
        -75 de 100 en venta, prima real +1,8 %- seguia saliendo
        como "Conservar buena oferta".

        No era el orden. `decide_incoming_offer` leia

            offer.get("delta_percent", 0.0)

        y esa clave NO EXISTE: `build_offer_board` la llama
        `premium_percent`. La prima de toda oferta valia 0,0
        desde siempre, `classify_offer_quality(0.0)` devolvia
        FAIR para todas, y las dos reglas que exigen prima BUENA
        o EXCELENTE no podian dispararse jamas.

        Es el mismo patron que `lineup.get("score")` cuando la
        clave se llama `lineup_score`. Una clave que no existe
        devuelve el valor por defecto y nadie se entera.

    QUE SE COMPRUEBA

        Que la clave que el motor lee este de verdad entre las
        que produce el generador de ofertas. Comparar nombres de
        claves es lo unico que caza esta familia de fallo.
    """

    import ast
    import inspect

    from src.analysis import offer_analyzer, offer_decision_engine

    # 1. Que el motor lea `premium_percent`.
    fuente = inspect.getsource(
        offer_decision_engine.decide_incoming_offer
    )

    assert 'offer.get(\n            "premium_percent"' in fuente or (
        '"premium_percent"' in fuente
    ), (
        "el motor ha dejado de leer premium_percent: la prima "
        "vuelve a valer cero para todas las ofertas"
    )

    # 2. Y que el generador la escriba con ese nombre.
    generador = inspect.getsource(offer_analyzer)

    assert '"premium_percent"' in generador, (
        "el generador de ofertas ya no produce premium_percent: "
        "el motor leera una clave inexistente"
    )

    # 3. Que una prima de verdad no acabe en FAIR.
    #
    #    Es la prueba de humo del fallo: si la lectura vuelve a
    #    romperse, toda prima se clasificara como FAIR.
    from src.analysis.offer_decision_engine import (
        classify_offer_quality,
    )

    assert classify_offer_quality(4.4) == "GOOD"
    assert classify_offer_quality(8.5) == "EXCELLENT"
    assert classify_offer_quality(-1.2) == "BELOW_MARKET"

    # 4. Y el caso completo: una oferta con prima buena por
    #    alguien que sobra tiene que poder cobrarse.
    from src.analysis.offer_decision_engine import sale_is_worth_it

    assert sale_is_worth_it(
        quality=classify_offer_quality(4.4),
        sale_score=75,
        in_lineup=False,
    )[0], (
        "con prima +4,4 % y 75 de venta no se cobra: la prima no "
        "esta llegando"
    )


def test_alguien_tiene_que_cobrarla():
    """
    La quinta pared: la decision se calculaba y se tiraba.

    `build_global_decision` calculaba `actionable` -las ofertas
    que hay que aceptar- y solo la usaba para CONTAR cuantas hay
    dentro de un texto. La accion emitida era MONITOR_OFFERS, con
    `executable: False` y `executor: None`.

    El executor `ACCEPT_RECOVERY_OFFER` seguia intacto y ya no se
    lo pedia nadie: se apago el camino viejo cuando Offer
    Decision Engine V2 paso a ser la unica autoridad, y no se
    encendio el nuevo.
    """

    from src.analysis.decision_orchestrator import (
        offers_to_collect,
    )

    fidalgo = {
        "decision": "ACCEPT_NOW",
        "offer_id": 4001,
        "player_name": "Alvaro Fidalgo",
        "premium_percent": 4.4,
        "sale_score": 75,
    }

    agujero = {
        "decision": "ACCEPT_FOR_SOLVENCY",
        "offer_id": 4002,
        "player_name": "Suplente cualquiera",
        "premium_percent": 0.3,
        "sale_score": 55,
    }

    otra_buena = {
        "decision": "ACCEPT_NOW",
        "offer_id": 4003,
        "player_name": "Otro que sobra",
        "premium_percent": 2.0,
        "sale_score": 62,
    }

    cola = offers_to_collect([fidalgo, agujero, otra_buena])

    assert len(cola) == 3

    assert cola[0] is agujero, (
        "tapar el agujero va primero: ahi el dinero hace falta, "
        "no solo compensa"
    )

    assert cola[1] is fidalgo, (
        "entre dos ventas aprobadas se cobra antes la que mas "
        "prima deja"
    )


def test_lo_que_no_se_puede_cobrar_no_se_propone():
    """
    Proponer una oferta imposible cuesta el ciclo entero.

    Solo se ejecuta una accion cada media hora. Si la elegida se
    cae en el executor por no tener `offer_id`, no se cobra nada
    y no hay segundo intento hasta el ciclo siguiente.
    """

    from src.analysis.decision_orchestrator import (
        offers_to_collect,
    )

    assert offers_to_collect([]) == []
    assert offers_to_collect(None) == []

    sin_id = {
        "decision": "ACCEPT_NOW",
        "offer_id": None,
        "premium_percent": 9.0,
    }

    protegido = {
        "decision": "ACCEPT_NOW",
        "offer_id": 4004,
        "protection": "NEVER_AUTO_SELL",
        "premium_percent": 12.0,
    }

    solo_reroll = {
        "decision": "REROLL_CANDIDATE",
        "offer_id": 4005,
        "premium_percent": 8.0,
    }

    assert offers_to_collect(
        [sin_id, protegido, solo_reroll]
    ) == [], (
        "se esta proponiendo cobrar algo que el executor va a "
        "rechazar, y ese ciclo se pierde"
    )


def test_no_se_vende_al_ultimo_portero():
    """
    Cobrar bien una oferta que te deja sin poder alinear.

    EL CASO (18/08/2026, primera cola real)

        La primera vez que Pepe eligio solo a quien cobrar, la
        cola salio asi:

            ACCEPT_NOW  Alvaro Fidalgo  +4,4 %  venta 75
            ACCEPT_NOW  Bayindir        +0,8 %  venta 60

        Bayindir es portero. Con dos porteros venderlo esta bien
        -por eso la puntuacion le da 60-, pero nadie estaba
        comprobando que hubiera dos.

        La puntuacion de venta mira el exceso de plantilla solo
        para SUMAR: "hay margen en esta posicion", +15. No resta
        cuando no hay margen. Es un premio, no un freno, y hasta
        hoy no hacia falta que lo fuera porque no vendia solo.

        El camino de aceptar por caducidad si consulta el
        guardarrail de posiciones. El de cobrar, recien abierto,
        no consultaba nada.
    """

    from src.analysis.decision_orchestrator import (
        offers_to_collect,
        position_floor_lookup,
    )

    bayindir = {
        "decision": "ACCEPT_NOW",
        "offer_id": 5001,
        "player_id": 700,
        "player_name": "Bayindir",
        "premium_percent": 0.8,
    }

    fidalgo = {
        "decision": "ACCEPT_NOW",
        "offer_id": 5002,
        "player_id": 800,
        "player_name": "Alvaro Fidalgo",
        "premium_percent": 4.4,
    }

    # Dos porteros: se puede soltar uno.
    con_recambio = position_floor_lookup(
        {
            "my_team": [
                {"id": 700, "position": 1},
                {"id": 701, "position": 1},
                {"id": 800, "position": 3},
                {"id": 801, "position": 3},
                {"id": 802, "position": 3},
                {"id": 803, "position": 3},
            ]
        }
    )

    cola = offers_to_collect(
        [bayindir, fidalgo],
        position_floor=con_recambio,
    )

    assert len(cola) == 2
    assert cola[0] is fidalgo

    # Un solo portero: esa oferta ya no se propone.
    sin_recambio = position_floor_lookup(
        {
            "my_team": [
                {"id": 700, "position": 1},
                {"id": 800, "position": 3},
                {"id": 801, "position": 3},
                {"id": 802, "position": 3},
                {"id": 803, "position": 3},
            ]
        }
    )

    cola = offers_to_collect(
        [bayindir, fidalgo],
        position_floor=sin_recambio,
    )

    assert [item["player_name"] for item in cola] == [
        "Alvaro Fidalgo"
    ], (
        "se esta cobrando por el ultimo portero: el domingo no "
        "hay a quien alinear"
    )

    # AUSENCIA DE DATO NO ES DATO
    #
    # Con plantilla conocida, una oferta por alguien que no esta
    # en ella no se da por segura. Sin plantilla ninguna no se
    # bloquea nada, porque entonces el freno seria el bug.
    desconocido = {
        "decision": "ACCEPT_NOW",
        "offer_id": 5003,
        "player_id": 999,
        "premium_percent": 7.0,
    }

    assert offers_to_collect(
        [desconocido],
        position_floor=sin_recambio,
    ) == []

    assert len(
        offers_to_collect([desconocido], position_floor={})
    ) == 1


def test_el_gatillo_esta_conectado():
    """
    Que la cola exista no basta: hay que emitir la accion.

    Estructural a proposito. El fallo no fue una cuenta mal
    hecha, fue un cable suelto entre dos piezas correctas, y eso
    solo se ve mirando quien llama a quien.
    """

    import inspect

    from src.analysis import decision_orchestrator
    from src.actions.autopilot_executor import (
        HARD_SAFETY_ALLOWED_ACTIONS,
    )

    # La version sin cache es la que lleva la logica. Desde el
    # 19/08/2026 `build_global_decision` es una envoltura que
    # recuerda la ultima decision mientras el snapshot no cambie.
    fuente = inspect.getsource(
        decision_orchestrator.build_global_decision_uncached
    )

    assert "offers_to_collect(" in fuente, (
        "el orchestrator ha dejado de calcular que oferta cobrar"
    )

    assert '"ACCEPT_RECOVERY_OFFER"' in fuente, (
        "vuelve a emitirse solo MONITOR_OFFERS: la decision se "
        "calcula y se tira"
    )

    # Y que el executor siga aceptando esa accion, incluso con la
    # caja en rojo, que es justo cuando cobrar hace falta.
    assert (
        "ACCEPT_RECOVERY_OFFER" in HARD_SAFETY_ALLOWED_ACTIONS
    )

    # El executor lee `data.offer`. Si el orchestrator cambia el
    # nombre de la clave, la accion sale como INVALID_DECISION.
    assert '"offer":' in fuente, (
        "el executor busca decision['data']['offer'] y ya no se "
        "esta poniendo ahi"
    )


def main():

    pruebas = [
        test_la_regla_cobra_lo_que_sobra,
        test_no_se_regala_nada,
        test_las_doce_ofertas_reales,
        test_el_computer_llega_a_la_regla,
        test_una_sola_regla_para_los_dos_caminos,
        test_la_tierra_de_nadie_se_resuelve,
        test_la_banda_esta_cableada,
        test_la_prima_llega_de_verdad,
        test_alguien_tiene_que_cobrarla,
        test_lo_que_no_se_puede_cobrar_no_se_propone,
        test_no_se_vende_al_ultimo_portero,
        test_el_gatillo_esta_conectado,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Cobrar ofertas: todo en verde.")


if __name__ == "__main__":
    main()
