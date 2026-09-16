"""
El carril de un día: la regla sale de la medición, no de una constante.

QUE SE PRUEBA AQUI

    1. `test_la_prima_de_compra_lleva_su_mes`
       La prima se publica partida por periodo y cada tramo con su
       `n`, aunque un tramo se quede en n=1. Falla si la lista de
       compras llega vacía.

    2. `test_la_ventana_sale_de_la_curva`
       El plazo de la regla se deriva de la medición, no de una
       constante escrita. Falla si la curva llega vacía.

    3. Que el listón del carril sale de los dos umbrales de la
       casa y se mueve con ellos, en vez de ser un número elegido.

    4. Que el carril sigue APAGADO.

LO QUE ESTAS GUARDIAS SABEN Y LA PRIMERA VERSION NO

    La regla empezó siendo "vender al día siguiente", leída de la
    curva por noches. Esa curva es SELECCION, no reloj: las 167
    ventas aceptadas tienen mediana +2,37 % y las 13 ofertas vivas
    sin aceptar, −0,50 %. La gente vende los días que la oferta es
    buena.

    Por eso `test_la_ventana_sale_de_la_curva` exige que la regla
    NO tenga plazo fijo, y que el número que sí tiene —el precio
    de venta— se derive de los umbrales.

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aquí, con instantes fijos. No se
    abre `data/`, no se llama a `datetime.now()` y el `ahora` de
    `posiciones_atascadas` entra por argumento.
"""

from __future__ import annotations

import statistics

from src.analysis.el_carril_de_un_dia import (
    ENCENDIDO,
    SUELO_DE_COBRO,
    TOPE_DE_COMPRA,
    cuantos_caben,
    esta_encendido,
    liston_del_carril,
    posiciones_atascadas,
    regla_de_compra,
    regla_de_venta,
    tasa_de_exito,
    techo_del_carril,
)


DIA = 86_400

T0 = 1_786_000_000


# ============================================================
# LOS FIXTURES
# ============================================================
#
# Nuestras compras, con su mes. Agosto caro y septiembre barato:
# si los dos tramos fuesen iguales, la guardia del mes no probaría
# nada.
COMPRAS = [
    # agosto: el mecanismo viejo, primas de dos cifras
    {"player": "Bigas", "month": "2026-08", "premium": 10.00},
    {"player": "Zubeldia", "month": "2026-08", "premium": 10.00},
    {"player": "Cepeda", "month": "2026-08", "premium": 0.76},
    # septiembre: el tope de euro exacto funcionando, y dos
    # excepciones que NO son de este carril
    {"player": "Expósito", "month": "2026-09", "premium": -0.06},
    {"player": "Diego Conde", "month": "2026-09", "premium": 0.25},
    {"player": "Fortuño", "month": "2026-09", "premium": 0.25},
    {"player": "Kiko Femenía", "month": "2026-09", "premium": 4.23},
]


# La curva por noches, tal y como salió medida.
CURVA = [
    {"nights": 1, "n": 11, "net_percent": 3.14, "winners": 11},
    {"nights": 2, "n": 6, "net_percent": -4.13, "winners": 2},
    {"nights": 3, "n": 10, "net_percent": -0.75, "winners": 5},
    {"nights": 4, "n": 10, "net_percent": 2.75, "winners": 7},
    {"nights": 5, "n": 9, "net_percent": 0.53, "winners": 6},
]


# Las 13 ofertas vivas del Computer, sin aceptar: la muestra SIN
# sesgo de selección.
OFERTAS_VIVAS = [
    -4.2, -3.3, -3.2, -3.1, -2.4, -1.5, -0.5,
    1.5, 2.0, 3.8, 4.1, 5.0, 10.6,
]

# Las aceptadas, que están seleccionadas por ser buenas.
OFERTAS_ACEPTADAS = [0.15, 1.44, 2.37, 3.11, 4.09, 4.81, 5.92]


def _por_mes(compras):
    """Lo que tiene que hacer quien publique la prima de compra."""

    grupos = {}

    for compra in compras or []:
        grupos.setdefault(compra["month"], []).append(
            compra["premium"]
        )

    return {
        mes: {
            "n": len(primas),
            "median": round(statistics.median(primas), 3),
        }
        for mes, primas in sorted(grupos.items())
    }


def test_el_fixture_trae_de_todo() -> None:
    """
    REGLA 24. Sin dos meses distintos, sin ofertas por debajo y por
    encima del listón y sin una curva con forma, las demás se
    pondrían verdes sin haber probado su mitad.
    """

    meses = {c["month"] for c in COMPRAS}

    assert len(meses) >= 2, (
        f"el fixture de compras tiene un solo mes ({meses}): la "
        f"guardia del mes no probaría nada"
    )

    por_mes = _por_mes(COMPRAS)

    medianas = {v["median"] for v in por_mes.values()}

    assert len(medianas) > 1, (
        f"los meses dan la misma mediana ({medianas}): entonces "
        f"partir por mes no cambia nada"
    )

    liston = liston_del_carril()["floor_percent"]

    assert any(p >= liston for p in OFERTAS_VIVAS), (
        "ninguna oferta viva pasa el listón: la tasa de éxito "
        "saldría cero y no probaría nada"
    )

    assert any(p < liston for p in OFERTAS_VIVAS), (
        "todas las ofertas vivas pasan el listón: entonces el "
        "listón no separa nada"
    )

    assert any(p < 0 for p in OFERTAS_VIVAS), (
        "ninguna oferta viva es negativa: el fixture no refleja lo "
        "medido"
    )

    # La curva tiene que tener forma: si todas las noches dieran lo
    # mismo, no se podría distinguir reloj de selección.
    netos = {c["net_percent"] for c in CURVA}

    assert len(netos) > 1, "la curva del fixture es plana"

    print(
        f"  OK  el fixture trae {len(meses)} meses, una curva de "
        f"{len(CURVA)} tramos y ofertas a los dos lados del listón"
    )


# ============================================================
# 1. LA PRIMA DE COMPRA, POR MES
# ============================================================


def test_la_prima_de_compra_lleva_su_mes() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    La prima de compra se publica PARTIDA POR PERIODO y cada tramo
    con su `n`, aunque un tramo se quede en n=1.

    POR QUE IMPORTA: la mediana de los cinco viajes nuestros daba
    +4,23 %, y de ahí concluí que "lo primero es dejar de pagar de
    más al entrar". Partida por mes:

        agosto       n=3   +10,00 %
        septiembre   n=2    +2,24 %

    Tres de los cinco eran de agosto. El problema de entrada ya
    estaba casi resuelto y la conclusión estaba mal.

    Y FALLA SI LA LISTA DE COMPRAS LLEGA VACIA: sin compras no se
    publica una prima, se dice que no hay.
    """

    por_mes = _por_mes(COMPRAS)

    assert por_mes, "no se ha partido por mes"

    assert len(por_mes) >= 2, (
        f"solo hay {len(por_mes)} periodo(s): sin dos no se puede "
        f"ver si el problema es viejo o sigue vivo"
    )

    # CADA TRAMO CON SU `n` (doctrina 55).
    for mes, datos in por_mes.items():

        assert datos["n"] > 0, f"el tramo {mes} no trae `n`"

        assert datos["median"] is not None, (
            f"el tramo {mes} publica una mediana vacía"
        )

    # UN TRAMO DE n=1 SE DICE, NO SE ESCONDE.
    uno = _por_mes(
        COMPRAS + [{"player": "X", "month": "2026-07", "premium": 9.9}]
    )

    assert uno["2026-07"]["n"] == 1, uno

    assert uno["2026-07"]["median"] == 9.9, (
        "un tramo de n=1 no publica su número: un n=1 dicho es "
        "información; escondido dentro de una mediana es lo que "
        "costó el «ocho por ciento»"
    )

    # Y LA GLOBAL NO PUEDE SUSTITUIR A LAS PARTIDAS.
    global_ = round(
        statistics.median([c["premium"] for c in COMPRAS]), 3
    )

    assert any(
        v["median"] != global_ for v in por_mes.values()
    ), (
        f"todos los meses dan la mediana global ({global_}): "
        f"entonces partir no aporta"
    )

    # ------------------------------------------------------
    # CON LA LISTA VACIA SE FALLA
    # ------------------------------------------------------
    for etiqueta, entrada in (
        ("vacía", []),
        ("None", None),
    ):
        assert _por_mes(entrada) == {}, (
            f"con la lista de compras «{etiqueta}» se ha publicado "
            f"una prima igualmente"
        )

    print(
        f"  OK  {len(por_mes)} periodos con su `n`: "
        + ", ".join(
            f"{m} n={v['n']} {v['median']:+.2f} %"
            for m, v in por_mes.items()
        )
    )


# ============================================================
# 2. LA VENTANA
# ============================================================


def test_la_ventana_sale_de_la_curva() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    El plazo de la regla se deriva de la medición, no de una
    constante escrita.

    Y LA MEDICION DICE QUE NO HAY PLAZO. La curva por noches
    —+3,14 % a una noche, −4,13 % a dos— parece un reloj y no lo
    es: es selección. Las ofertas aceptadas tienen mediana
    +2,37 % y las vivas sin aceptar −0,50 %; la gente vende los
    días que la oferta es buena.

    Así que lo que esta guardia exige es:

        - que la regla de venta NO mire ningún calendario;
        - que el número que sí tiene —el precio de venta— se
          derive de los umbrales de la casa y se mueva con ellos.

    Y FALLA SI LA CURVA LLEGA VACIA.
    """

    assert CURVA, (
        "la curva llega vacía: sin curva no se puede derivar "
        "ninguna regla (regla 24)"
    )

    for tramo in CURVA:
        assert tramo["n"] > 0, f"un tramo de la curva sin `n`: {tramo}"

    # ------------------------------------------------------
    # LA REGLA DE VENTA NO TIENE FECHA
    # ------------------------------------------------------
    #
    #     Con el mismo coste y la misma oferta, la decisión tiene
    #     que ser la misma lleve un día o lleve un mes.
    coste = 1_000_000

    buena = int(coste * 1.02)
    mala = int(coste * 1.004)

    assert regla_de_venta(coste, buena)["sell"] is True, (
        "una oferta que cubre el suelo no se acepta"
    )

    assert regla_de_venta(coste, mala)["sell"] is False, (
        "una oferta que NO cubre el suelo se acepta"
    )

    # La firma no admite ningún día ni ninguna fecha: si alguien
    # añadiera un plazo, esto tendría que cambiar y se vería.
    import inspect  # noqa: PLC0415

    parametros = set(
        inspect.signature(regla_de_venta).parameters
    )

    assert not (
        parametros & {"dias", "days", "plazo", "ventana", "ahora"}
    ), (
        f"la regla de venta ha recuperado un plazo: {parametros}. "
        f"La curva por noches es selección, no reloj."
    )

    # ------------------------------------------------------
    # EL NUMERO QUE SI TIENE SE DERIVA, NO SE ESCRIBE
    # ------------------------------------------------------
    medido = liston_del_carril()

    esperado = (1 + SUELO_DE_COBRO) * (1 + TOPE_DE_COMPRA) - 1

    assert medido["floor_percent"] == round(100 * esperado, 4), (
        f"el listón ({medido['floor_percent']}) no es el producto "
        f"de los dos umbrales ({100 * esperado})"
    )

    # Y SE MUEVE CON ELLOS: ese es el punto entero.
    otro = liston_del_carril(suelo=0.02, tope=0.005)

    assert otro["floor_percent"] > medido["floor_percent"], (
        f"subir los dos umbrales no sube el listón: "
        f"{otro['floor_percent']} contra {medido['floor_percent']}. "
        f"Entonces es una constante escrita, no una derivación."
    )

    mas_bajo = liston_del_carril(suelo=0.0, tope=0.0)

    assert mas_bajo["floor_percent"] == 0.0, (
        f"sin suelo ni tope el listón debería ser cero y es "
        f"{mas_bajo['floor_percent']}"
    )

    # ------------------------------------------------------
    # LA TASA SALE DE LAS OFERTAS SIN SELECCIONAR
    # ------------------------------------------------------
    liston = medido["floor_percent"]

    vivas = tasa_de_exito(OFERTAS_VIVAS, liston)

    aceptadas = tasa_de_exito(OFERTAS_ACEPTADAS, liston)

    assert vivas["available"] and aceptadas["available"]

    assert vivas["rate"] < aceptadas["rate"], (
        f"las ofertas vivas ({vivas['rate']}) no salen peor que "
        f"las aceptadas ({aceptadas['rate']}): entonces no hay "
        f"sesgo de selección que corregir y toda la lectura de la "
        f"curva cambia"
    )

    # Con la lista vacía, no se inventa una tasa.
    for etiqueta, entrada in (("vacía", []), ("None", None)):
        assert not tasa_de_exito(entrada, liston)["available"], (
            f"con ofertas «{etiqueta}» se ha publicado una tasa"
        )
        assert not techo_del_carril(entrada)["available"], (
            f"con ofertas «{etiqueta}» se ha publicado un techo"
        )

    print(
        f"  OK  la regla no tiene plazo; el listón "
        f"{liston:.4f} % sale de los umbrales, y la tasa cae de "
        f"{aceptadas['rate']:.2f} a {vivas['rate']:.2f} al quitar "
        f"el sesgo"
    )


def test_el_liston_no_supera_el_techo_de_la_via() -> None:
    """
    DOCTRINA 60: una vía no puede pasar un listón mayor que su
    techo. El 3 % global contra un techo de 1,5075 % tuvo el
    carril apagado sin que nadie lo supiera.

    Aquí se comprueba con los dos números medidos, y además que la
    comprobación sabría detectar el caso malo.
    """

    liston = liston_del_carril()["floor_percent"]

    techo = techo_del_carril(OFERTAS_VIVAS)

    assert techo["available"], techo["reason"]

    # La cola de arriba es lo que hace viable el carril: la
    # mediana es NEGATIVA y aun así el p75 lo pasa.
    assert techo["median_percent"] < liston, (
        f"la mediana de las ofertas ({techo['median_percent']}) ya "
        f"pasa el listón ({liston}): entonces el carril sería "
        f"trivial y la tasa de éxito no haría falta"
    )

    assert techo["p75"] > liston, (
        f"ni el percentil 75 de las ofertas ({techo['p75']}) llega "
        f"al listón ({liston}): el carril estaría cerrado por "
        f"construcción, como lo estaba con el 3 %"
    )

    # Y el caso malo se detectaría: con el listón del 3 % global,
    # ninguna de las medidas del techo de la vía lo alcanza.
    TECHO_MEDIDO_DE_LA_VIA = 1.5075

    assert 3.0 > TECHO_MEDIDO_DE_LA_VIA, (
        "el 3 % global ya no supera el techo de la vía: si eso "
        "cambia, cambia el motivo entero de este carril"
    )

    assert liston < TECHO_MEDIDO_DE_LA_VIA, (
        f"el listón propuesto ({liston}) supera el techo medido de "
        f"la vía ({TECHO_MEDIDO_DE_LA_VIA}): repetiría el error "
        f"del 3 % (doctrina 60)"
    )

    print(
        f"  OK  listón {liston:.4f} % por debajo del techo "
        f"{TECHO_MEDIDO_DE_LA_VIA} %, y el 3 % global por encima"
    )


# ============================================================
# 3. LA COMPRA
# ============================================================


def test_en_este_carril_se_puja_el_minimo() -> None:
    """
    Toda la ventaja está en la entrada: el neto por mánager ordena
    igual que su prima de compra. Así que se ofrece el mínimo y
    nunca por encima del tope de la casa.
    """

    precio = 2_000_000

    plan = regla_de_compra(precio)

    assert plan["available"], plan["reason"]

    assert plan["bid"] == precio + 1, (
        f"se puja {plan['bid']} sobre un precio de {precio}: en "
        f"este carril se puja el mínimo"
    )

    assert plan["bid"] <= plan["max_bid"], plan

    assert plan["max_bid"] <= int(precio * (1 + TOPE_DE_COMPRA)), (
        "el techo de la puja supera el tope de la casa"
    )

    # Sin precio no se puja.
    for malo in (0, None, -100):
        assert not regla_de_compra(malo)["available"], malo

    print(
        f"  OK  se puja {plan['bid']:,} sobre {precio:,} "
        f"(+{plan['premium_percent']:.6f} %), nunca por encima de "
        f"{plan['max_bid']:,}"
    )


# ============================================================
# 4. EL CAPITAL PARADO
# ============================================================


def test_el_capital_parado_se_cuenta_y_no_se_propone_vender() -> None:
    """
    El encargo lo pidió así: dale el número y calla. Esta función
    cuenta lo que está parado y desde cuándo; no devuelve ninguna
    orden de venta.
    """

    posiciones = [
        # una con oferta buena: no está atascada
        {"player": "A", "cost": 1_000_000, "offer": 1_020_000,
         "bought_at": T0},
        # dos atascadas, una de ellas vieja
        {"player": "B", "cost": 2_000_000, "offer": 1_900_000,
         "bought_at": T0},
        {"player": "Yamal", "cost": 24_897_600, "offer": 20_896_900,
         "bought_at": T0 - 37 * DIA},
        # una sin oferta ninguna
        {"player": "C", "cost": 500_000, "offer": 0,
         "bought_at": T0 - 2 * DIA},
    ]

    medido = posiciones_atascadas(posiciones, ahora=T0 + DIA)

    assert medido["available"], medido["reason"]

    nombres = {p["player"] for p in medido["stuck"]}

    assert "A" not in nombres, (
        "una posición con oferta suficiente se ha contado como "
        "atascada"
    )

    assert {"B", "Yamal", "C"} <= nombres, (
        f"faltan posiciones atascadas: {nombres}"
    )

    assert medido["capital"] == 2_000_000 + 24_897_600 + 500_000, (
        f"el capital parado sale {medido['capital']}"
    )

    # La vieja se marca, la de ayer no.
    marcada = next(
        p for p in medido["stuck"] if p["player"] == "Yamal"
    )

    assert marcada["flagged"] is True, marcada

    assert marcada["days"] >= 37, marcada

    reciente = next(
        p for p in medido["stuck"] if p["player"] == "B"
    )

    assert reciente["flagged"] is False, (
        "una posición de un día se marca como atascada de largo"
    )

    # NO SE PROPONE VENDER: ninguna clave de la salida ordena nada.
    prohibidas = {"sell", "action", "recommend", "vender", "orden"}

    for posicion in medido["stuck"]:
        assert not (set(posicion) & prohibidas), (
            f"la salida trae una orden de venta: {posicion}"
        )

    # Con las manos vacías, no se da un número.
    for etiqueta, entrada in (("vacía", []), ("None", None)):
        assert not posiciones_atascadas(entrada, ahora=T0)[
            "available"
        ], f"con posiciones «{etiqueta}» se ha publicado un capital"

    print(
        f"  OK  {len(medido['stuck'])} posiciones paradas, "
        f"{medido['capital']:,} EUR, {medido['flagged']} marcada(s), "
        f"y ninguna orden de venta"
    )


def test_lo_que_cabe_se_limita_por_el_capital() -> None:
    """
    Aunque la vía se abriera hoy, hay que poder pagarla. Y la
    cuenta es aritmética sobre lo medido, no una previsión.
    """

    medido = cuantos_caben(
        capital_libre=3_780_699,
        coste_tipico=2_410_007,
        tasa=0.46,
        margen_percent=2.12,
        dias=30,
    )

    assert medido["available"], medido["reason"]

    assert medido["slots"] == 1, (
        f"con 3,78 M y posiciones de 2,41 M caben "
        f"{medido['slots']} y debería caber 1"
    )

    # Más capital, más plazas.
    mas = cuantos_caben(
        capital_libre=10_000_000,
        coste_tipico=2_410_007,
        tasa=0.46,
        margen_percent=2.12,
    )

    assert mas["slots"] > medido["slots"], (
        "doblar el capital no abre más plazas"
    )

    assert mas["total"] > medido["total"], (
        "más plazas no dan más dinero"
    )

    # Sin capital, sin coste o sin tasa: no se inventa nada.
    for etiqueta, kwargs in (
        ("sin capital", {"capital_libre": 0, "coste_tipico": 100}),
        ("sin coste", {"capital_libre": 100, "coste_tipico": 0}),
    ):
        sin = cuantos_caben(tasa=0.46, margen_percent=2.0, **kwargs)
        assert not sin["available"], f"«{etiqueta}» ha dado un número"

    # Capital que no llega ni para una posición: se dice.
    corto = cuantos_caben(
        capital_libre=1_000_000,
        coste_tipico=2_410_007,
        tasa=0.46,
        margen_percent=2.12,
    )

    assert corto["slots"] == 0, corto

    assert corto["reason"], corto

    print(
        f"  OK  {medido['slots']} plaza(s) con 3,78 M, "
        f"{medido['cycles']:.1f} vueltas, {medido['total']:+,} EUR"
    )


# ============================================================
# 5. APAGADO
# ============================================================


def test_el_carril_sigue_apagado() -> None:
    """
    Se propone; la luz la da el dueño con las tres tablas delante.
    """

    assert ENCENDIDO is False, (
        "el carril se ha quedado ENCENDIDO: este encargo dice "
        "medir, proponer y dejar apagado"
    )

    assert esta_encendido() is False, (
        "`esta_encendido()` no respeta la constante"
    )

    # Pero la pieza CALCULA: si no, no se podría enseñar la tabla.
    assert liston_del_carril()["available"], (
        "apagado no puede significar que no calcule"
    )

    assert regla_de_compra(1_000_000)["available"], (
        "apagado no puede significar que no calcule"
    )

    print("  OK  la regla está escrita, calcula, y sigue apagada")


TESTS = [
    test_el_fixture_trae_de_todo,
    test_la_prima_de_compra_lleva_su_mes,
    test_la_ventana_sale_de_la_curva,
    test_el_liston_no_supera_el_techo_de_la_via,
    test_en_este_carril_se_puja_el_minimo,
    test_el_capital_parado_se_cuenta_y_no_se_propone_vender,
    test_lo_que_cabe_se_limita_por_el_capital,
    test_el_carril_sigue_apagado,
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
        f"EL CARRIL DE UN DIA V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
