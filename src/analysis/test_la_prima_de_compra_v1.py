"""
La prima se mide contra el precio DEL DIA, o no se mide.

EL NUMERO QUE RESULTO NO SERLO (15/09/2026)

    "Pagamos un 8 % de mas y cobramos un 2 %: cada viaje nace
    seis puntos bajo el agua."

    El 8 % salia de comparar contra el catalogo de un
    `snapshot_*.json` del mismo dia. Dos agujeros:

    1. Del 18/08 al 09/09 no hay ninguna foto. De nuestras 24
       compras, solo 5 caian en un dia con foto.

    2. Y la foto no es del momento de la compra: las nuestras se
       resuelven a las 07:0x de Madrid y la foto del 13/09 es de
       las 17:17. Para Trent, la foto daba +1,10 % donde nuestro
       propio registro de puja anoto +0,00 %.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Que la referencia sea del DIA de la operacion y de DESPUES
       del cambio de precio, nunca de la vispera ni de otro
       momento del dia.
    2. Que una operacion sin precio del dia se cuente aparte y no
       reciba ninguna referencia estimada.
    3. Que la hora del cambio se MIDA desde la serie, no se
       escriba a mano.
    4. Que ninguna mediana viaje sin su `n`.
    5. DOCTRINA 54: que la resta compra-venta no se haga con
       mitades de periodos distintos.

REGLA 23 / DOCTRINA 50

    Ni disco, ni red, ni reloj. El tablon y la serie de precios
    son fixtures escritos aqui, y todas las fechas son
    constantes.

MADRID ES UTC+2 EN ESTE FIXTURE

    Igual que en el modulo. Los datos reales van del 09/08 al
    15/09/2026, entero dentro del horario de verano. El dia que
    esto tenga que cruzar el ultimo domingo de octubre hara falta
    una zona horaria de verdad, y entonces esta guardia debera
    cambiar con ella.
"""

from __future__ import annotations

from datetime import datetime

from src.analysis.la_prima_de_compra import (
    HORA_DEL_CAMBIO,
    MADRID,
    bajo_el_agua,
    cuando_cambian_los_precios,
    indexar_precios,
    operaciones,
    precio_del_dia,
    primas,
)


ANA = 2001

BENI = 2002

YAMAL = 100

TRENT = 200

HUERFANO = 300


def t(dia: int, hora: int, minuto: int = 0, mes: int = 9) -> int:
    """Un instante de Madrid, en segundos."""

    return int(
        datetime(
            2026, mes, dia, hora, minuto, tzinfo=MADRID
        ).timestamp()
    )


# ============================================================
# LA SERIE DE PRECIOS
# ============================================================

# DOS MUESTRAS AL DIA, como el almacen de verdad: una de
# madrugada con el precio de la vispera y otra a las 07:01 con el
# precio nuevo.
#
#     Y una TERCERA por la tarde el dia 13, que es la hora a la
#     que se toman las fotos. Lleva un precio distinto a
#     proposito: es el que hacia que el 8 % pareciera un 8 %.
PRECIOS = {
    str(YAMAL): {
        "t": [
            t(12, 3), t(12, 7, 1),
            t(13, 3), t(13, 7, 1), t(13, 17, 17),
            t(14, 3), t(14, 7, 1),
        ],
        "p": [
            1_000_000, 1_000_000,
            1_000_000, 2_000_000, 1_800_000,
            2_000_000, 2_100_000,
        ],
    },
    str(TRENT): {
        "t": [t(13, 3), t(13, 7, 1), t(14, 3), t(14, 7, 1)],
        "p": [400_000, 500_000, 500_000, 500_000],
    },
    # UN JUGADOR SIN MUESTRA DESPUES DEL CAMBIO el dia 13: solo
    # de madrugada. No tiene precio del dia, y no se le inventa.
    str(HUERFANO): {
        "t": [t(13, 3), t(14, 7, 1)],
        "p": [900_000, 950_000],
    },
}


def _market(cuando, jugador, quien, importe, pujas=()):
    return {
        "event_id": f"m{cuando}{jugador}",
        "date": cuando,
        "type": "market",
        "content": [
            {
                "player": jugador,
                "to": {"id": quien, "name": str(quien)},
                "amount": importe,
                "bids": [
                    {"user": {"id": u}, "amount": a}
                    for u, a in pujas
                ],
            }
        ],
    }


def _venta(cuando, jugador, quien, importe):
    """`transfer` sin `to`: venta al Computer."""

    return {
        "event_id": f"t{cuando}{jugador}",
        "date": cuando,
        "type": "transfer",
        "content": [
            {
                "player": jugador,
                "from": {"id": quien, "name": str(quien)},
                "amount": importe,
            }
        ],
    }


# EL TABLON.
#
#   ANA compra a Yamal el 13 a las 07:05 por 2.160.000. El precio
#   del dia es 2.000.000 -> +8,00 %. Contra la foto de las 17:17
#   (1.800.000) saldria +20,00 %, que es la clase de numero que
#   hay que impedir.
#
#   ANA compra a Trent el 13 sin que nadie le dispute, por
#   500.000 clavados -> +0,00 %.
#
#   BENI compra a Yamal el 14 por 2.100.000 -> +0,00 %.
#
#   Y ANA vende a Trent al Computer el 14 por 515.000, con el
#   precio del dia en 500.000 -> +3,00 %.
TABLON = [
    _market(t(13, 7, 5), YAMAL, ANA, 2_160_000,
            pujas=((BENI, 2_100_000), (ANA, 2_160_000))),
    _market(t(13, 7, 5), TRENT, ANA, 500_000),
    _market(t(13, 7, 6), HUERFANO, ANA, 1_000_000),
    _market(t(14, 7, 5), YAMAL, BENI, 2_100_000),
    _venta(t(14, 7, 30), TRENT, ANA, 515_000),
]


def _indice():
    return indexar_precios(PRECIOS)


def _fila(salida, quien, jugador):
    for c in salida["managers"][quien]["buys_detail"]:
        if c["player"] == jugador:
            return c

    raise AssertionError(
        f"no esta la compra de {jugador} por {quien}"
    )


# ============================================================
# REGLA 24: EL FIXTURE TIENE QUE TRAER DE TODO
# ============================================================


def test_el_fixture_trae_de_todo() -> None:
    """
    Sin compras disputadas, sin compras limpias, sin una venta al
    Computer y sin una operacion sin referencia, las demas
    guardias se pondrian verdes sin probar su mitad.
    """

    salida = primas(TABLON, _indice())

    assert salida["available"], salida

    ana = salida["managers"][ANA]

    assert ana["buys"]["n"] >= 2, ana["buys"]

    assert ana["disputed"]["n"] >= 1, (
        "el fixture no tiene ninguna compra disputada"
    )

    assert ana["undisputed"]["n"] >= 1, (
        "el fixture no tiene ninguna compra sin rival"
    )

    assert ana["sells_to_computer"]["n"] >= 1, (
        "el fixture no tiene ninguna venta al Computer"
    )

    assert ana["buys_without_reference"] >= 1, (
        "el fixture no tiene ninguna compra sin precio del dia: "
        "la regla de no estimar no se estaria probando"
    )

    print(
        f"  OK  el fixture trae {ana['buys']['n']} compras con "
        f"referencia, {ana['buys_without_reference']} sin ella, "
        f"disputadas y limpias, y una venta"
    )


# ============================================================
# 1. LA REFERENCIA ES DEL DIA, Y DE DESPUES DEL CAMBIO
# ============================================================


def test_la_referencia_es_la_del_dia_de_la_compra() -> None:
    """
    El precio del dia es la PRIMERA muestra de ese dia a partir
    de la hora del cambio. Ni la de madrugada —que trae el precio
    de la vispera— ni la de la tarde.
    """

    indice = _indice()

    # El dia 13 Yamal vale 1.000.000 de madrugada y 2.000.000
    # desde las 07:01. Una compra a las 07:05 se mide contra
    # 2.000.000.
    assert (
        precio_del_dia(indice, YAMAL, t(13, 7, 5)) == 2_000_000
    ), "se esta cogiendo el precio de la vispera"

    # Y una compra mas tarde ESE MISMO DIA, tambien: el precio no
    # vuelve a cambiar hasta el dia siguiente.
    assert (
        precio_del_dia(indice, YAMAL, t(13, 23, 0)) == 2_000_000
    ), "la muestra de la tarde no puede mandar sobre la del dia"

    # La muestra de las 17:17 del dia 13 dice 1.800.000 y es la
    # que tomaria una foto. NO se usa.
    assert (
        precio_del_dia(indice, YAMAL, t(13, 7, 5)) != 1_800_000
    ), (
        "se esta usando el precio de la foto de la tarde: es el "
        "error que hizo del +8 % un +20 %"
    )

    # Y el dia siguiente es otro precio.
    assert (
        precio_del_dia(indice, YAMAL, t(14, 7, 5)) == 2_100_000
    ), "el dia 14 tiene su propio precio"

    print(
        "  OK  la referencia es la primera muestra del dia tras "
        "el cambio, no la de la vispera ni la de la tarde"
    )


def test_sin_muestra_del_dia_no_hay_precio_ni_estimacion() -> None:
    """
    Si ese dia no hay muestra a partir del cambio, NO se coge la
    de la vispera ni se interpola: no hay precio.
    """

    indice = _indice()

    # El huerfano solo tiene muestra de madrugada el dia 13.
    assert precio_del_dia(indice, HUERFANO, t(13, 7, 6)) is None, (
        "se ha inventado un precio del dia con la muestra de "
        "madrugada"
    )

    # Un jugador que no esta en la serie tampoco.
    assert precio_del_dia(indice, 999_999, t(13, 7, 5)) is None

    salida = primas(TABLON, indice)

    ana = salida["managers"][ANA]

    huerfanos = [
        c["player"]
        for c in ana["buys_without_reference_detail"]
    ]

    assert HUERFANO in huerfanos, ana

    for c in ana["buys_without_reference_detail"]:
        assert c["reference"] is None, c
        assert c["premium"] is None, (
            f"a una compra sin precio del dia se le ha puesto "
            f"una prima: {c}"
        )

    for c in ana["buys_detail"]:
        assert c["reference"], c
        assert c["premium"] is not None, c

    print(
        "  OK  sin muestra del dia no hay precio, y esa compra "
        "se cuenta aparte sin prima"
    )


def test_la_hora_del_cambio_se_mide_no_se_escribe() -> None:
    """
    `HORA_DEL_CAMBIO` es una afirmacion sobre Biwenger. Una
    afirmacion sobre el mundo que no se puede recalcular es una
    opinion con cara de constante.
    """

    medido = cuando_cambian_los_precios(_indice())

    assert medido["available"], medido

    # REGLA 24: sin cambios observados esto no probaria nada.
    assert medido["cambios"] >= 3, medido

    assert medido["hora_dominante"] == HORA_DEL_CAMBIO, (
        f"la serie dice que los precios cambian a las "
        f"{medido['hora_dominante']}h y la constante dice "
        f"{HORA_DEL_CAMBIO}h"
    )

    assert medido["parte_en_la_dominante"] >= 0.5, medido

    print(
        f"  OK  la hora del cambio ({HORA_DEL_CAMBIO}h) sale "
        f"medida de {medido['cambios']} cambios"
    )


# ============================================================
# 2. LOS NUMEROS, CON SU n
# ============================================================


def test_ninguna_mediana_viaja_sin_su_n() -> None:
    """
    Regla de la casa: cada numero con su `n`.

    El 8 % que abrio este encargo era una mediana de CINCO
    compras y viajaba sin decirlo. Aqui el `n` va en el mismo
    diccionario que la mediana: no se puede leer una sin la otra.
    """

    salida = primas(TABLON, _indice())

    bloques = []

    for resumen in salida["managers"].values():
        bloques += [
            resumen["buys"],
            resumen["sells_to_computer"],
            resumen["undisputed"],
            resumen["disputed"],
        ]
        for mes in resumen["by_month"].values():
            bloques += [mes["all"], mes["undisputed"], mes["disputed"]]

    bloques.append(salida["computer"])

    assert bloques, "no hay ni un bloque que comprobar"

    for bloque in bloques:

        assert "n" in bloque, bloque

        if bloque["n"]:
            assert bloque["median"] is not None, bloque

        else:
            # UN BLOQUE VACIO NO VALE CERO: vale nada.
            assert bloque["median"] is None, (
                f"un bloque sin muestra publica una mediana: "
                f"{bloque}"
            )
            assert bloque["mean"] is None, bloque

    print(
        f"  OK  los {len(bloques)} bloques llevan su n, y los "
        f"vacios no publican mediana"
    )


def test_la_prima_sale_contra_el_precio_del_dia() -> None:
    """Las cifras exactas, calculadas a mano en el fixture."""

    salida = primas(TABLON, _indice())

    yamal = _fila(salida, ANA, YAMAL)

    assert yamal["reference"] == 2_000_000, yamal

    assert abs(yamal["premium"] - 8.0) < 1e-9, (
        f"Ana pago 2.160.000 sobre 2.000.000: son +8,00 % y "
        f"salen {yamal['premium']:+.4f} %"
    )

    trent = _fila(salida, ANA, TRENT)

    assert trent["premium"] == 0.0, trent

    # La venta al Computer: 515.000 sobre 500.000 = +3,00 %.
    ana = salida["managers"][ANA]

    assert ana["sells_to_computer"]["n"] == 1, ana
    assert abs(ana["sells_to_computer"]["median"] - 3.0) < 1e-9, (
        ana["sells_to_computer"]
    )

    print(
        "  OK  +8,00 % la disputada, +0,00 % la limpia y "
        "+3,00 % la venta, contra el precio del dia"
    )


def test_la_competencia_sale_del_tablon_y_no_se_duplica() -> None:
    """
    Las pujas perdedoras vienen ESCRITAS. Y si el tablon reemite
    la misma subasta, no se cuentan dos veces.
    """

    filas = operaciones(TABLON)

    de_yamal = [
        f
        for f in filas
        if f["player"] == YAMAL and f["buyer"] == ANA
    ]

    assert len(de_yamal) == 1, de_yamal

    # La puja del propio ganador no cuenta como rival.
    assert de_yamal[0]["rivals"] == 1, de_yamal[0]

    assert de_yamal[0]["losers"] == [BENI], de_yamal[0]

    # AHORA EL TABLON REPETIDO, con otro `event_id`.
    reemitido = []

    for evento in TABLON:
        reemitido.append(evento)
        copia = dict(evento)
        copia["event_id"] = f"{evento['event_id']}-bis"
        reemitido.append(copia)

    assert len(operaciones(reemitido)) == len(filas), (
        "una subasta reemitida se esta contando dos veces"
    )

    limpio = primas(TABLON, _indice())
    sucio = primas(reemitido, _indice())

    assert (
        sucio["managers"][ANA]["buys"]["n"]
        == limpio["managers"][ANA]["buys"]["n"]
    ), "el tablon repetido infla las compras"

    print(
        "  OK  la competencia sale escrita del tablon y una "
        "subasta reemitida no la duplica"
    )


# ============================================================
# 3. DOCTRINA 54: NO SE RESTAN PERIODOS DISTINTOS
# ============================================================


def test_no_se_restan_periodos_distintos() -> None:
    """
    "Compramos al +8 % y cobramos el +2 %" restaba una mediana de
    cinco compras contra una prima de venta de otra muestra y
    otros meses. La resta salia -6 puntos y no significaba nada.
    """

    salida = primas(TABLON, _indice())

    ana = salida["managers"][ANA]

    # EN EL MES 09 HAY LAS DOS MITADES: se puede restar.
    entero = bajo_el_agua(ana, "2026-09")

    assert entero["available"] is True, entero

    assert entero["buy"]["n"] and entero["sell"]["n"], entero

    # Compra +4,00 % de mediana (0 y 8) contra venta +3,00 %.
    assert abs(entero["difference"] + 1.0) < 1e-9, entero

    assert "n=" in entero["reason"], entero["reason"]

    # BENI COMPRA Y NO VENDE: la resta NO se hace.
    beni = salida["managers"][BENI]

    imposible = bajo_el_agua(beni)

    assert imposible["available"] is False, (
        "se ha restado una prima de venta que no existe"
    )

    assert "doctrina 54" in imposible["reason"], (
        imposible["reason"]
    )

    assert imposible["difference"] is None, imposible

    # Y UN MES SIN VENTAS TAMPOCO, aunque el manager venda en otro.
    sin_ventas = bajo_el_agua(ana, "2026-08")

    assert sin_ventas["available"] is False, sin_ventas

    assert sin_ventas["difference"] is None, sin_ventas

    print(
        "  OK  la resta solo sale cuando las dos mitades cubren "
        "el mismo periodo; si no, se dice"
    )


# ============================================================
# 4. NO SE PASA CON LAS MANOS VACIAS
# ============================================================


def test_sin_tablon_o_sin_precios_no_hay_prima() -> None:
    """
    Regla 24. Y sin almacen de precios NO se vuelve a la foto:
    se dice que no se puede medir.
    """

    for vacio in ([], None):

        salida = primas(vacio, _indice())

        assert not salida["available"], salida
        assert not salida["managers"], salida
        assert salida["reason"], salida

    sin_precios = primas(TABLON, {})

    assert not sin_precios["available"], sin_precios

    assert "precio del dia" in (sin_precios["reason"] or ""), (
        sin_precios["reason"]
    )

    assert sin_precios["operations"] > 0, (
        "sin precios se pierde ademas la cuenta de operaciones "
        "leidas: entonces no se sabe si habia tablon"
    )

    print(
        "  OK  sin tablon o sin almacen de precios no hay prima, "
        "y se dice cual falta"
    )


TESTS = [
    test_el_fixture_trae_de_todo,
    test_la_referencia_es_la_del_dia_de_la_compra,
    test_sin_muestra_del_dia_no_hay_precio_ni_estimacion,
    test_la_hora_del_cambio_se_mide_no_se_escribe,
    test_ninguna_mediana_viaja_sin_su_n,
    test_la_prima_sale_contra_el_precio_del_dia,
    test_la_competencia_sale_del_tablon_y_no_se_duplica,
    test_no_se_restan_periodos_distintos,
    test_sin_tablon_o_sin_precios_no_hay_prima,
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
        f"LA PRIMA DE COMPRA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
