"""
El viaje al Computer: una sola definicion, y las tres cuentas la usan.

QUE SE PRUEBA AQUI

    1. `test_un_viaje_al_computer_es_comprar_y_venderle`
       La definicion vive en UN solo sitio —`viajes()`— y las tres
       cuentas del informe salen de ella. La guardia lo comprueba
       recalculando a mano lo que deberia dar cada una. Y FALLA si
       la lista de viajes llega vacia.

    2. Que las dos primas —la de compra y la de venta— salen de
       LOS MISMOS viajes (doctrina 54). Ese es el numero que podia
       matar el encargo entero, y medirlo sobre dos muestras
       distintas no es restarlo: es comparar dos cosas.

    3. Que una venta sin compra anterior no se empareja con
       cualquiera: se queda HUERFANA y se cuenta aparte. En el
       tablon de verdad son 84 de 178, casi la mitad.

    4. Que lo que no se puede fechar no se estima.

POR QUE IMPORTA QUE LA DEFINICION SEA UNA SOLA

    El informe compara tres cosas: la liga, los nuestros y el
    rendimiento por dia. Si cada una contara los viajes a su
    manera, las tres columnas no serian comparables y la
    conclusion —que esta via explica el 39 % de la distancia con
    Pollo— seria un artefacto de haber contado distinto.

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    El tablon de esta guardia es un fixture escrito aqui, con
    instantes fijos puestos a mano. No se abre `data/`, no se
    llama a `datetime.now()` y la funcion de precios es una tabla.

DOCTRINA 53 / 55

    Cada agregado de estas pruebas lleva su `n`, y el rendimiento
    lleva su plazo: por DIA de capital inmovilizado, no por viaje.
"""

from __future__ import annotations

import statistics

from src.analysis.el_viaje_al_computer import (
    SEGUNDOS_POR_DIA,
    compras_en_el_mercado,
    cuanto_cabe_en_un_mes,
    dias_hasta_cruzar_el_suelo,
    por_manager,
    resumen,
    traspasos_entre_managers,
    ventas_al_computer,
    viajes,
)


# ============================================================
# EL TABLON DE MENTIRA
# ============================================================
#
# Instantes fijos escritos a mano: el dia 0 es un numero, no
# "hoy". Asi la guardia da lo mismo hoy que dentro de un año.
DIA = SEGUNDOS_POR_DIA

T0 = 1_786_000_000


def _mercado(player, manager, amount, dia, bids=0):
    """Una subasta del Computer que alguien gano."""

    return {
        "type": "market",
        "date": T0 + dia * DIA,
        "content": [
            {
                "player": player,
                "to": {"id": 1, "name": manager},
                "amount": amount,
                "bids": [{"amount": 1}] * bids,
            }
        ],
    }


def _venta(player, manager, amount, dia):
    """Una venta al Computer: con vendedor y SIN comprador."""

    return {
        "type": "transfer",
        "date": T0 + dia * DIA,
        "content": [
            {
                "player": player,
                "from": {"id": 1, "name": manager},
                "amount": amount,
            }
        ],
    }


def _traspaso(player, vende, compra, amount, dia):
    """Entre managers: con vendedor Y comprador."""

    return {
        "type": "transfer",
        "date": T0 + dia * DIA,
        "content": [
            {
                "player": player,
                "from": {"id": 1, "name": vende},
                "to": {"id": 2, "name": compra},
                "amount": amount,
            }
        ],
    }


# UN FIXTURE QUE TRAE DE TODO (regla 24)
#
#     Un viaje rapido que gana, uno lento que pierde, uno que no
#     llega al suelo del +1 %, una venta huerfana, una compra sin
#     vender, un traspaso, un jugador comprado y vendido DOS veces
#     y una operacion que no se puede fechar.
TABLON = [
    # 1. rapido y ganador: +5 % en un dia
    _mercado(100, "Pollo17", 1_000_000, 0, bids=0),
    _venta(100, "Pollo17", 1_050_000, 1),

    # 2. lento y perdedor: -10 % en veinte dias
    _mercado(200, "Manzagool", 2_000_000, 0, bids=2),
    _venta(200, "Manzagool", 1_800_000, 20),

    # 3. gana, pero NO llega al suelo del +1 %
    _mercado(300, "Pollo17", 1_000_000, 2),
    _venta(300, "Pollo17", 1_005_000, 4),

    # 4. el mismo jugador, comprado y vendido DOS veces
    _mercado(400, "Luismi_Haz", 500_000, 1),
    _venta(400, "Luismi_Haz", 530_000, 3),
    _mercado(400, "Luismi_Haz", 540_000, 6),
    _venta(400, "Luismi_Haz", 580_000, 9),

    # 5. adquirido por traspaso y vendido al Computer
    _traspaso(500, "Mex", "Pepe Bordalás", 800_000, 2),
    _venta(500, "Pepe Bordalás", 860_000, 5),

    # 6. venta HUERFANA: no hay compra anterior en el tablon
    _venta(600, "Prinzipote", 300_000, 3),

    # 7. compra que sigue SIN VENDER
    _mercado(700, "Pepe Bordalás", 900_000, 8),

    # 8. sin precio fechable NI a la ida ni a la vuelta (el
    #    jugador 800 no esta en la tabla de precios)
    _mercado(800, "Pollo17", 400_000, 1),
    _venta(800, "Pollo17", 420_000, 2),

    # 9. MEDIO fechable: la compra si, la venta no.
    #
    #     Es el caso que destapo que la guardia de las dos primas
    #     no mordia. Si alguien midiera la prima de compra sobre
    #     "todas las que tengan compra fechada" y la de venta solo
    #     sobre las completas, este viaje entraria en una y no en
    #     la otra — y eso es exactamente la doctrina 54.
    #
    #     Su prima de compra es enorme a proposito (+20 %) para
    #     que mezclar las muestras mueva la mediana de sitio.
    _mercado(900, "Manzagool", 1_200_000, 1),
    _venta(900, "Manzagool", 1_250_000, 4),
]


# Precio de mercado de cada jugador, por dia. Escrito a mano.
PRECIOS = {
    100: {0: 1_000_000, 1: 1_002_000},
    200: {0: 1_950_000, 20: 1_790_000},
    300: {2: 1_000_000, 4: 1_010_000},
    400: {1: 495_000, 3: 520_000, 6: 535_000, 9: 570_000},
    500: {2: 790_000, 5: 850_000},
    700: {8: 900_000},
    # El 900 tiene precio el dia de la COMPRA y no el de la venta.
    900: {1: 1_000_000},
}


def precio_de_aquel_dia(player_id, cuando):
    """
    Nunca mira el futuro y nunca estima: si no consta, es cero.
    """

    dia = round((int(cuando) - T0) / DIA)

    return int((PRECIOS.get(int(player_id)) or {}).get(dia) or 0)


def _tablon():
    compras = compras_en_el_mercado(TABLON) + traspasos_entre_managers(
        TABLON
    )

    return compras, ventas_al_computer(TABLON)


# ============================================================
# REGLA 24
# ============================================================


def test_el_fixture_trae_de_todo() -> None:
    """
    Sin un rapido, un lento, un perdedor, una huerfana, una compra
    sin vender y un jugador repetido, las demas se pondrian verdes
    sin haber probado su mitad.
    """

    compras, ventas = _tablon()

    assert compras, "el fixture no trae compras"
    assert ventas, "el fixture no trae ventas"

    hechos = viajes(compras, ventas, precio_de_aquel_dia)

    trips = hechos["trips"]

    assert any(t["days"] < 2 for t in trips), "falta un viaje rapido"

    assert any(t["days"] > 10 for t in trips), "falta un viaje lento"

    assert any(t["net_eur"] > 0 for t in trips), "faltan ganadores"

    assert any(t["net_eur"] < 0 for t in trips), "faltan perdedores"

    assert any(
        t["net_eur"] > 0 and not t["clears_floor"] for t in trips
    ), (
        "falta un viaje que gane pero NO llegue al suelo del +1 %: "
        "sin el, el suelo no prueba nada"
    )

    assert hechos["orphan_sales"], "falta una venta huerfana"

    assert hechos["open_positions"], "falta una compra sin vender"

    assert any(not t["priced"] for t in trips), (
        "falta una operacion sin precio fechable"
    )

    assert any(t["via"] == "TRASPASO" for t in trips), (
        "falta un jugador adquirido por traspaso"
    )

    repetidos = [t for t in trips if t["player_id"] == 400]

    assert len(repetidos) == 2, (
        f"el jugador comprado y vendido dos veces da "
        f"{len(repetidos)} viaje(s) y tienen que ser 2"
    )

    print(
        f"  OK  el fixture da {len(trips)} viajes con rapido, lento, "
        f"ganador, perdedor, huerfana y repetido"
    )


# ============================================================
# LA DEFINICION, EN UN SOLO SITIO
# ============================================================


def test_un_viaje_al_computer_es_comprar_y_venderle() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    Un VIAJE es comprar un jugador y vendérselo al Computer. La
    definicion vive en `viajes()` y las TRES cuentas del informe
    -la liga, los nuestros y el rendimiento por dia- salen de ahi.

    Aqui se recalcula a mano lo que deberia dar cada una y se
    compara. Si alguna contase los viajes a su manera, las
    columnas del informe no serian comparables.

    Y ESTA GUARDIA FALLA SI LA LISTA DE VIAJES LLEGA VACIA: sin
    viajes no se prueba ninguna definicion.
    """

    compras, ventas = _tablon()

    hechos = viajes(compras, ventas, precio_de_aquel_dia)

    assert hechos["available"], hechos["reason"]

    trips = hechos["trips"]

    assert trips, (
        "la lista de viajes llega vacia: sin viajes esta guardia no "
        "prueba nada (regla 24)"
    )

    # ------------------------------------------------------
    # LA DEFINICION, COMPROBADA PIEZA A PIEZA
    # ------------------------------------------------------
    for viaje in trips:

        assert viaje["sold_at"] >= viaje["bought_at"], (
            f"un viaje se vende ANTES de comprarse: {viaje}"
        )

        assert viaje["net_eur"] == viaje["collected"] - viaje["paid"], (
            f"el neto no es venta - compra: {viaje}"
        )

        esperado = round(
            (viaje["sold_at"] - viaje["bought_at"]) / SEGUNDOS_POR_DIA,
            2,
        )

        assert viaje["days"] == esperado, (
            f"los dias no son la resta de instantes: "
            f"{viaje['days']} contra {esperado}"
        )

        if viaje["paid"]:
            assert viaje["net_percent"] == round(
                100.0 * viaje["net_eur"] / viaje["paid"], 3
            ), f"el neto % no sale del neto y lo pagado: {viaje}"

    # ------------------------------------------------------
    # LAS TRES CUENTAS USAN LA MISMA LISTA
    # ------------------------------------------------------
    liga = resumen(trips)

    nuestros = resumen(
        [t for t in trips if t["manager"] == "Pepe Bordalás"]
    )

    reparto = por_manager(trips)

    # 1. La liga: el `n` y el neto total, recalculados a mano.
    assert liga["n"] == len(trips), (
        f"la cuenta de la liga dice {liga['n']} y hay {len(trips)}"
    )

    assert liga["net_eur_total"] == sum(
        t["net_eur"] for t in trips
    ), "el neto total de la liga no es la suma de los viajes"

    # 2. Los nuestros: un subconjunto de LA MISMA lista.
    mios = [t for t in trips if t["manager"] == "Pepe Bordalás"]

    assert nuestros["n"] == len(mios), (
        f"la cuenta nuestra dice {nuestros['n']} y hay {len(mios)}"
    )

    assert mios, (
        "no hay ni un viaje nuestro en el fixture: entonces la "
        "columna «nosotros» no se prueba"
    )

    # 3. El reparto por manager suma la liga entera: si alguno
    #    contase distinto, la suma no cuadraria.
    assert sum(v["n"] for v in reparto.values()) == liga["n"], (
        f"el reparto por manager suma "
        f"{sum(v['n'] for v in reparto.values())} y la liga tiene "
        f"{liga['n']}: alguien esta contando distinto"
    )

    assert sum(
        v["net_eur_total"] for v in reparto.values()
    ) == liga["net_eur_total"], (
        "el neto por manager no suma el de la liga"
    )

    # 4. El rendimiento por dia sale de los MISMOS viajes, y lleva
    #    su plazo (doctrina 53).
    por_dia = [
        t["net_percent_per_day"]
        for t in trips
        if t["net_percent_per_day"] is not None
    ]

    assert liga["percent_per_day_median"] == round(
        statistics.median(por_dia), 4
    ), "el rendimiento por dia no sale de estos viajes"

    assert liga["percent_per_day_n"] == len(por_dia), (
        "el rendimiento por dia se publica sin su `n` correcto"
    )

    # Y NO es el neto por viaje disfrazado: un viaje de 20 dias y
    # otro de uno no pueden dar el mismo %/dia.
    rapido = next(t for t in trips if t["days"] < 2)
    lento = next(t for t in trips if t["days"] > 10)

    assert (
        rapido["net_percent_per_day"] != rapido["net_percent"]
    ) or rapido["days"] == 1.0, (
        "el %/dia coincide con el % del viaje: no se esta "
        "dividiendo por los dias"
    )

    assert abs(lento["net_percent_per_day"]) < abs(
        lento["net_percent"]
    ), (
        f"el viaje de {lento['days']} dias rinde lo mismo por dia "
        f"que en total: el plazo no entra en la cuenta"
    )

    # ------------------------------------------------------
    # CON LA LISTA VACIA SE FALLA
    # ------------------------------------------------------
    for etiqueta, (c, v) in (
        ("sin compras", ([], ventas)),
        ("sin ventas", (compras, [])),
        ("las dos vacias", ([], [])),
        ("None", (None, None)),
    ):
        vacio = viajes(c, v, precio_de_aquel_dia)

        assert not vacio["available"], (
            f"con «{etiqueta}» se ha dado por buena una lista de "
            f"viajes vacia: no haber mirado nada no es un aprobado"
        )

        assert vacio["trips"] == [], vacio

        assert vacio["reason"], (
            f"con «{etiqueta}» no se dice por que no hay viajes"
        )

        assert not resumen(vacio["trips"])["available"], (
            f"con «{etiqueta}» el resumen publica agregados sobre "
            f"cero viajes"
        )

    print(
        f"  OK  una definicion, {liga['n']} viajes, y las tres "
        f"cuentas cuadran con ella"
    )


def test_las_dos_primas_salen_de_los_mismos_viajes() -> None:
    """
    DOCTRINA 54. La prima de compra y la de venta tienen que salir
    del MISMO conjunto de viajes.

    Comparar «lo que pagamos de mas» con «lo que paga el Computer»
    cuando cada numero viene de operaciones distintas no resta:
    son dos medias de dos cosas. Esa era la cuenta que podia matar
    el encargo entero.
    """

    compras, ventas = _tablon()

    hechos = viajes(compras, ventas, precio_de_aquel_dia)

    medido = resumen(hechos["trips"])

    fechados = [t for t in hechos["trips"] if t["priced"]]

    assert fechados, (
        "ningun viaje del fixture se puede fechar: sin primas no "
        "hay nada que comparar"
    )

    assert medido["priced_n"] == len(fechados), (
        f"las primas se miden sobre {medido['priced_n']} viajes y "
        f"fechados hay {len(fechados)}"
    )

    assert medido["priced_n"] < medido["n"], (
        "todos los viajes estan fechados: entonces esta guardia no "
        "prueba que los no fechables se quedan fuera. Arreglar el "
        "fixture, no la guardia."
    )

    # ------------------------------------------------------
    # EL CASO QUE HACE QUE ESTO MUERDA
    # ------------------------------------------------------
    #
    #     Tiene que haber un viaje con la compra fechada y la
    #     venta NO. Si no lo hubiera, "los viajes con prima de
    #     compra" y "los viajes completos" serian el mismo
    #     conjunto, mezclar las muestras no cambiaria ninguna
    #     mediana, y esta guardia daria verde sin probar nada.
    a_medias = [
        t
        for t in hechos["trips"]
        if not t["priced"] and t["buy_premium"] is not None
    ]

    assert a_medias, (
        "no hay ningun viaje con la compra fechada y la venta sin "
        "fechar: sin ese caso, mezclar las dos muestras no movería "
        "ninguna mediana y esta guardia no probaría nada. Arreglar "
        "el fixture, no la guardia."
    )

    # Y su prima tiene que ser DISTINTA de las de los completos:
    # si cayera en medio, colarla tampoco movería la mediana.
    con_todas = statistics.median(
        [t["buy_premium"] for t in fechados]
        + [t["buy_premium"] for t in a_medias]
    )

    assert round(con_todas, 3) != medido["buy_premium_median"], (
        f"meter los viajes a medias da la misma mediana "
        f"({con_todas}): el fixture no distingue las dos muestras"
    )

    # LAS DOS, DE LA MISMA LISTA.
    assert medido["buy_premium_median"] == round(
        statistics.median(t["buy_premium"] for t in fechados), 3
    ), "la prima de compra no sale de los viajes fechados"

    assert medido["sell_premium_median"] == round(
        statistics.median(t["sell_premium"] for t in fechados), 3
    ), "la prima de venta no sale de los viajes fechados"

    assert medido["premium_gap"] == round(
        medido["sell_premium_median"] - medido["buy_premium_median"],
        3,
    ), "el hueco no es la resta de las dos primas"

    # Y el viaje SIN precio fechable conserva su neto en euros:
    # los dos importes son hechos del tablon, aunque la prima no
    # se pueda medir.
    sin_precio = [t for t in hechos["trips"] if not t["priced"]]

    assert sin_precio, "el fixture no trae ningun viaje sin fechar"

    for viaje in sin_precio:
        assert viaje["net_eur"] == viaje["collected"] - viaje["paid"], (
            "un viaje sin fechar ha perdido su neto en euros"
        )

    print(
        f"  OK  las dos primas sobre los mismos {medido['priced_n']} "
        f"viajes fechados (de {medido['n']}), hueco "
        f"{medido['premium_gap']:+.2f} pp"
    )


def test_una_venta_sin_compra_no_se_empareja_con_cualquiera() -> None:
    """
    En el tablon de verdad hay 84 ventas sin compra anterior de 178
    -jugadores que ya estaban en la plantilla-. Si se emparejaran
    con la compra que hubiera mas a mano, saldrian viajes que
    nunca existieron.
    """

    compras, ventas = _tablon()

    hechos = viajes(compras, ventas, precio_de_aquel_dia)

    huerfanas = hechos["orphan_sales"]

    assert huerfanas, (
        "el fixture no tiene ventas huerfanas: entonces esto no "
        "prueba nada"
    )

    # La del jugador 600 no tiene compra en ningun sitio.
    assert any(v["player_id"] == 600 for v in huerfanas), (
        f"la venta sin compra no esta entre las huerfanas: "
        f"{huerfanas}"
    )

    # Y NO aparece como viaje.
    assert not any(
        t["player_id"] == 600 for t in hechos["trips"]
    ), "una venta sin compra anterior se ha convertido en viaje"

    # Una venta no puede emparejarse con una compra POSTERIOR.
    for viaje in hechos["trips"]:
        assert viaje["bought_at"] <= viaje["sold_at"], viaje

    # Y una compra de OTRO manager no sirve: el jugador 500 lo
    # compra Pepe por traspaso y lo vende Pepe.
    quinientos = [t for t in hechos["trips"] if t["player_id"] == 500]

    assert len(quinientos) == 1, quinientos

    assert quinientos[0]["manager"] == "Pepe Bordalás", (
        "el viaje se ha atribuido al manager equivocado"
    )

    print(
        f"  OK  {len(huerfanas)} venta(s) huerfana(s) contada(s) "
        f"aparte y ninguna convertida en viaje"
    )


def test_el_suelo_del_uno_por_ciento_se_mide_sobre_lo_pagado() -> None:
    """
    Solo vendemos si nos pagan el coste +1 %. El suelo se mide
    sobre lo que PAGAMOS, no sobre el mercado de hoy — que es
    justo lo que lo hace inalcanzable cuando el precio baja.
    """

    compras, ventas = _tablon()

    hechos = viajes(compras, ventas, precio_de_aquel_dia)

    for viaje in hechos["trips"]:
        assert viaje["clears_floor"] == (
            viaje["collected"] >= viaje["paid"] * 1.01
        ), f"el suelo no se mide sobre lo pagado: {viaje}"

    medido = dias_hasta_cruzar_el_suelo(hechos["trips"])

    cruzan = [t for t in hechos["trips"] if t["clears_floor"]]

    assert medido["crossed"] == len(cruzan), medido

    assert medido["did_not_cross"] == len(hechos["trips"]) - len(
        cruzan
    ), medido

    assert 0 < medido["crossed"] < medido["n"], (
        f"o los cruzan todos o ninguno ({medido['crossed']} de "
        f"{medido['n']}): asi no se prueba que el suelo separe"
    )

    # Los dias se miden SOLO sobre los que cruzaron: los que no
    # cruzaron no tienen ese dia y meterlos mezclaria dos cosas.
    assert medido["days_n"] == len(cruzan), (
        f"los dias hasta el suelo se miden sobre "
        f"{medido['days_n']} y cruzaron {len(cruzan)}"
    )

    print(
        f"  OK  {medido['crossed']} de {medido['n']} pasan el suelo, "
        f"medido sobre lo pagado"
    )


def test_un_mes_no_se_proyecta_sin_ritmo() -> None:
    """
    `cuanto_cabe_en_un_mes` es aritmetica sobre lo ya medido, no
    una prevision. Sin dias o sin neto no devuelve un numero:
    devuelve el motivo.
    """

    compras, ventas = _tablon()

    medido = resumen(viajes(compras, ventas, precio_de_aquel_dia)["trips"])

    proyectado = cuanto_cabe_en_un_mes(medido, 1_000_000, dias=30)

    assert proyectado["available"], proyectado["reason"]

    # Las vueltas son los dias entre los dias por viaje.
    assert proyectado["cycles"] == round(
        30 / medido["days_median"], 2
    ), proyectado

    # Y viaja con el `n` del que sale (doctrina 55).
    assert proyectado["n"] == medido["n"], (
        "la proyeccion no dice sobre cuantos viajes esta hecha"
    )

    for etiqueta, entrada in (
        ("sin medicion", None),
        ("vacia", {}),
        ("no disponible", {"available": False}),
        (
            "sin dias",
            {"available": True, "days_median": None,
             "net_percent_median": 3.0},
        ),
        (
            "sin neto",
            {"available": True, "days_median": 2.0,
             "net_percent_median": None},
        ),
        (
            "cero dias",
            {"available": True, "days_median": 0,
             "net_percent_median": 3.0},
        ),
    ):
        sin = cuanto_cabe_en_un_mes(entrada, 1_000_000)

        assert not sin["available"], (
            f"con «{etiqueta}» se ha proyectado un mes igualmente: "
            f"{sin}"
        )

        assert sin["reason"], f"«{etiqueta}» no dice por que no"

    print(
        f"  OK  un mes sale de {proyectado['cycles']} vueltas sobre "
        f"n={proyectado['n']}, y sin ritmo no sale"
    )


def test_una_venta_con_comprador_no_es_una_venta_al_computer() -> None:
    """
    Si hay comprador es un traspaso entre managers: se pacta y no
    dice nada de lo que paga el Computer. Confundirlos meteria
    precios negociados en la mediana.
    """

    ventas = ventas_al_computer(TABLON)

    traspasos = traspasos_entre_managers(TABLON)

    assert traspasos, "el fixture no trae traspasos"

    for traspaso in traspasos:
        assert not any(
            v["player_id"] == traspaso["player_id"]
            and v["date"] == traspaso["date"]
            for v in ventas
        ), (
            f"un traspaso entre managers se ha contado como venta "
            f"al Computer: {traspaso}"
        )

    # Y un traspaso SI cuenta como forma de adquirir al jugador.
    assert all(t["via"] == "TRASPASO" for t in traspasos), traspasos

    # Basura dentro no tumba nada.
    for basura in (None, [], [None], [{"type": "transfer"}], ["x"]):
        assert ventas_al_computer(basura) == [], basura
        assert compras_en_el_mercado(basura) == [], basura
        assert traspasos_entre_managers(basura) == [], basura

    print(
        f"  OK  {len(traspasos)} traspaso(s) fuera de las ventas al "
        f"Computer, y dentro de las adquisiciones"
    )


TESTS = [
    test_el_fixture_trae_de_todo,
    test_un_viaje_al_computer_es_comprar_y_venderle,
    test_las_dos_primas_salen_de_los_mismos_viajes,
    test_una_venta_sin_compra_no_se_empareja_con_cualquiera,
    test_el_suelo_del_uno_por_ciento_se_mide_sobre_lo_pagado,
    test_un_mes_no_se_proyecta_sin_ritmo,
    test_una_venta_con_comprador_no_es_una_venta_al_computer,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL VIAJE AL COMPUTER V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
