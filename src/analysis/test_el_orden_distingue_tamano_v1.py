"""
El orden de la cesta tiene que distinguir el tamaño.

EL HALLAZGO (20/09/2026)

    `_por_euro` = `expected_value / bid`. En modo cartera:

        expected_value ≈ precio x (prima - IMPORTE_DE_CARTERA)

    El precio esta arriba y abajo, asi que se cancela. Medido
    sobre los candidatos REALES de dos dias -n=18 y n=16, con
    precios que van de 150.000 a 7.100.000-, el ratio sale
    constante hasta el quinto decimal:

        150.000    ->  0.020841
        3.000.000  ->  0.020848
        24.900.000 ->  0.020848

    DOCTRINA 97. Un criterio de orden que no depende de lo que
    ordena es una constante disfrazada.

LO QUE SALVA EL ORDEN HOY, Y NO ES EL RATIO

    `elegir_la_cesta` ordena por `-round(_por_euro(c, True), 4)`
    y desempata por `bid` ASCENDENTE. Lo que separa de verdad es
    `win_odds`, y esta MEDIDO que sube con el precio:

        < 1.500.000            0,46   (n=24)
        1.500.000 - 3.000.000  0,61   (n=18)
        >= 3.000.000           0,78   (n=32)

    Asi que el orden efectivo pone primero a los CAROS, por tres
    escalones bien separados:

        >= 3 M    0,020848 x 0,78 = 0,0163
        1,5-3 M   0,020847 x 0,61 = 0,0127
        < 1,5 M   0,020841 x 0,46 = 0,0096

    El desempate por el mas barato solo actua DENTRO de un
    escalon, que es donde el ratio si empata de verdad.

LO QUE VIGILA ESTA GUARDIA

    Que dos candidatos con el mismo rendimiento por euro y
    tamaños muy distintos NO salgan empatados en el orden de la
    cesta. Hoy no salen; si alguien quita la pelea del criterio,
    salen, y entonces la cesta vuelve a elegir por sorteo.

    Y deja escrito, con sus numeros, lo que HOY no distingue:
    dentro de un mismo escalon de `win_odds` el ratio empata y
    manda el mas barato. Eso es una decision del 11/09 con su
    motivo -"pujar bajo por muchos"- y esta guardia no la
    discute: la fija, para que mover el orden sea un acto
    consciente y no un efecto lateral.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj:
    todo son candidatos construidos aqui. Y si la muestra no
    abarca varios tamaños, la guardia FALLA en vez de pasar: un
    orden comprobado con todos los precios iguales no se ha
    comprobado.
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104, 20/09/2026)
#
#     Medido: con `BORDALAS_CESTA_SOLO_EL_SUELO` puesto en el
#     entorno, esta guardia se caia — y una guardia roja para el
#     paso «Validate optimized production cycle», o sea para EL
#     CICLO. Es lo que paso la noche del 20/09 con
#     `BORDALAS_OBJETIVOS_EL_CATALOGO`.
#
#     Este caso mide el comportamiento POR DEFECTO, asi que el
#     interruptor se apaga aqui. El comportamiento con el puesto
#     lo mide su propia guardia, que lo enciende y lo apaga ella.
os.environ.pop("BORDALAS_CESTA_SOLO_EL_SUELO", None)

from src.analysis.la_subasta import (
    IMPORTE_DE_CARTERA,
    _por_euro,
    candidatos_en_modo_cartera,
    elegir_la_cesta,
    probabilidad_de_llevarselo,
    puja_de_cartera,
)


# La prima mediana que el Computer paga al recomprar, medida.
# Aqui es un dato de entrada, no un umbral: se le pasa.
PRIMA = 0.0234


# Precios que cubren los tres escalones de `win_odds` medidos.
# Si alguien los iguala, la guardia se queda sin nada que mirar y
# lo dice.
PRECIOS = (
    150_000,
    240_000,
    1_430_000,
    1_620_000,
    2_590_000,
    3_040_000,
    6_910_000,
)


def _candidatos(precios=PRECIOS) -> list:
    return [
        {
            "id": 1000 + i,
            "name": f"P{precio}",
            "market_price": precio,
            "team_id": 100 + i,
        }
        for i, precio in enumerate(precios)
    ]


def _con_odds(precios=PRECIOS) -> list:
    """Los candidatos con puja, ganancia y probabilidad puestas."""

    listos = candidatos_en_modo_cartera(_candidatos(precios), PRIMA)

    for candidato in listos:
        suya = probabilidad_de_llevarselo(
            candidato.get("market_price"),
            candidato.get("rate_percent_per_day"),
        )
        candidato["win_odds"] = suya["probabilidad"]

    return listos


# ============================================================
# 1. LA MUESTRA TIENE QUE ABARCAR TAMAÑOS
# ============================================================


def test_sin_tamanos_distintos_no_se_comprueba_nada() -> None:
    """
    Doctrina 24, aplicada a esta guardia.

    Un orden comprobado con siete candidatos del mismo precio no
    se ha comprobado: cualquier criterio los deja empatados y
    todo pasa.
    """

    assert len(set(PRECIOS)) >= 3, (
        f"la muestra tiene {len(set(PRECIOS))} precio(s) "
        f"distinto(s): con menos de tres no se puede ver si el "
        f"orden distingue el tamaño"
    )

    assert max(PRECIOS) / min(PRECIOS) >= 10, (
        f"el precio mayor solo es "
        f"{max(PRECIOS) / min(PRECIOS):.1f} veces el menor: la "
        f"muestra no abarca tamaños de verdad"
    )

    # Y el caso que el dueño pidio explicitamente: si todos
    # valiesen lo mismo, esto tiene que saltar.
    iguales = _con_odds((1_000_000,) * 5)

    claves = {
        round(_por_euro(c, True), 4) for c in iguales
    }

    assert len(claves) == 1, (
        "con todos los candidatos al mismo precio el orden "
        "deberia empatar; si no, la guardia esta midiendo otra "
        "cosa"
    )


# ============================================================
# 2. EL RATIO SOLO NO DISTINGUE. QUEDA ESCRITO.
# ============================================================


def test_el_ratio_por_euro_no_depende_del_tamano() -> None:
    """
    El hallazgo, fijado. Si alguien hace que el ratio SI dependa
    del precio -por ejemplo usando la prima medida por tramo en
    vez de una sola-, esta prueba salta y hay que venir a leer la
    cabecera antes de cambiarla.
    """

    listos = _con_odds()

    ratios = {round(_por_euro(c), 4) for c in listos}

    assert len(ratios) == 1, (
        f"el rendimiento por euro ya distingue el tamaño "
        f"({sorted(ratios)}). Es lo que hay que querer, pero no "
        f"es lo que habia: lee la cabecera y actualiza el orden "
        f"a proposito"
    )

    # Y la cuenta que lo explica, por si el dia que salte alguien
    # quiere ver por que: la ganancia es proporcional al precio.
    for candidato in listos:
        precio = candidato["market_price"]
        esperado = int(precio * (1 + PRIMA)) - puja_de_cartera(
            precio, IMPORTE_DE_CARTERA
        )

        assert candidato["expected_value"] == max(0, esperado), (
            f"la ganancia de {candidato['name']} no sale de "
            f"precio x (1 + prima) - puja"
        )


# ============================================================
# 3. EL ORDEN, ENTERO, SI DISTINGUE
# ============================================================


def test_el_orden_distingue_tamano() -> None:
    """
    LA PRUEBA QUE DA NOMBRE AL FICHERO.

    Dos candidatos con el mismo ratio y precios muy distintos no
    pueden salir empatados en el orden de la cesta.
    """

    listos = _con_odds()

    def clave(candidato):
        return round(_por_euro(candidato, True), 4)

    barato = min(listos, key=lambda c: c["market_price"])
    caro = max(listos, key=lambda c: c["market_price"])

    assert round(_por_euro(barato), 4) == round(
        _por_euro(caro), 4
    ), "el caso ya no es el que esta guardia vino a vigilar"

    assert clave(barato) != clave(caro), (
        f"{barato['name']} ({barato['market_price']:,}) y "
        f"{caro['name']} ({caro['market_price']:,}) salen "
        f"EMPATADOS en el orden de la cesta: el criterio no "
        f"depende de lo que ordena y el reparto pasa a decidirlo "
        f"el desempate (doctrina 97)"
    )

    assert clave(caro) > clave(barato), (
        f"el orden pone por delante al de "
        f"{barato['market_price']:,}: con el mismo rendimiento "
        f"por euro, quien se lleva mas veces la subasta tiene "
        f"que ir primero"
    )


def test_la_pelea_es_lo_unico_que_separa_hoy() -> None:
    """
    Si se quita la pelea del criterio, la cesta vuelve a elegir
    por sorteo. Queda dicho aqui para que nadie la quite pensando
    que simplifica.
    """

    listos = _con_odds()

    sin_pelea = {round(_por_euro(c, False), 4) for c in listos}
    con_pelea = {round(_por_euro(c, True), 4) for c in listos}

    assert len(sin_pelea) == 1, (
        "sin la pelea ya hay mas de un rendimiento: el orden ha "
        "cambiado y esta cabecera se ha quedado vieja"
    )

    assert len(con_pelea) >= 3, (
        f"con la pelea solo hay {len(con_pelea)} valor(es) "
        f"distinto(s) en {len(listos)} candidatos de siete "
        f"tamaños: el orden ha dejado de distinguir"
    )


def test_dentro_del_escalon_manda_el_mas_barato() -> None:
    """
    LO QUE HOY NO DISTINGUE, FIJADO CON SU FECHA.

    Dos candidatos del MISMO escalon de `win_odds` empatan en el
    ratio, y entonces gana el que consume menos capacidad. Es
    decision del 11/09/2026, con su motivo escrito en
    `elegir_la_cesta`: "pujar bajo por muchos".

    Esta guardia no la discute. La fija, para que moverla sea un
    acto consciente.
    """

    # Los dos del escalon de abajo: 0,46 los dos.
    listos = _con_odds((150_000, 1_430_000))

    assert len({c["win_odds"] for c in listos}) == 1, (
        "los dos precios ya no caen en el mismo escalon de "
        "`win_odds`: elige otros dos"
    )

    cesta = elegir_la_cesta(
        listos,
        presupuesto=10_000_000,
        fichas_libres=1,
        caja_libre=10_000_000,
    )

    assert cesta["elegidos"], cesta.get("reason")

    elegido = cesta["elegidos"][0]

    assert elegido["market_price"] == 150_000, (
        f"dentro del mismo escalon la cesta se lleva a "
        f"{elegido['name']}: el desempate por capacidad "
        f"consumida ha cambiado, y eso es una decision del "
        f"dueño (11/09/2026)"
    )


def main() -> int:

    pruebas = [
        test_sin_tamanos_distintos_no_se_comprueba_nada,
        test_el_ratio_por_euro_no_depende_del_tamano,
        test_el_orden_distingue_tamano,
        test_la_pelea_es_lo_unico_que_separa_hoy,
        test_dentro_del_escalon_manda_el_mas_barato,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL ORDEN DISTINGUE TAMAÑO V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
