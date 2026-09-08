"""
Lo que se ofrece no puede pasar del punto de equilibrio.

SINTOMA (11/09/2026)

    Pepe pujaba con una prima MEDIANA del 8,51 %, la segunda mas
    alta de la liga. Once compras medibles al Computer, con
    primas de hasta +57,69 %.

CAUSA

    `optimal_bid` maximiza `P(ganar) x (valor - puja)`. Para
    subir `P(ganar)` sube la oferta, y eso es correcto CUANDO
    SOLO SE TIRA UNA VEZ.

    En la subasta del reset no es asi: perder no cuesta -el
    balance no se mueve, solo baja `maximumBid` hasta el reset-,
    hay veinte jugadores cada mañana y el 43 % no tiene rival.
    Con tiros gratis, subir la oferta compra jugadores caros.

CONSECUENCIA — LA CURVA, SOBRE 115 SUBASTAS DEL TABLON

    OFRECE     GANA           NETO
    +0,00 %      30      2.376.870
    +0,25 %      34      2.654.961   <-- MAXIMO
    +0,50 %      35      2.325.829
    +1,00 %      35      1.431.245
    +1,50 %      40        572.873
    +2,00 %      46       -430.126
    +3,00 %      54     -2.940.054
    +5,00 %      61     -8.717.501
    +8,00 %      71    -18.540.551

    Subir del 0,25 % al 8 % compra 37 jugadores mas y cuesta 21
    millones.

    Y cuadra por un camino independiente: el punto de equilibrio
    cae entre el 1,5 % y el 2 %, que es la prima que el Computer
    paga al RECOMPRAR -+1,8 %, medida sobre 107 ventas-. Dos
    mediciones distintas que se encuentran en el mismo numero.

LO QUE SE PROTEGE AQUI

    1. Que la prima maxima siga por debajo del equilibrio.
    2. Que la curva -metida aqui dentro- siga dando el maximo
       donde dice la constante.
    3. Que el tope se pueda quitar para poder enseñar el antes.
    4. Que el tope no impida pujar: nunca por debajo de
       `precio + 1`.

    La curva va como fixture. Ni disco, ni red, ni reloj.
"""

from __future__ import annotations

from src.analysis.rival_bid_model import (
    PRIMA_DE_EQUILIBRIO,
    PRIMA_MAXIMA_DE_PUJA,
    candidate_bids,
    optimal_bid,
    tope_por_la_prima,
)


# ============================================================
# LA CURVA, MEDIDA EL 11/09/2026 SOBRE 115 SUBASTAS
# ============================================================
#
# `(importe, ganadas, neto)`. No se recalcula aqui: es el
# resultado que justifica la constante, guardado para que la
# constante no pueda alejarse de el en silencio.
CURVA = (
    (0.0000, 30, 2_376_870),
    (0.0025, 34, 2_654_961),
    (0.0050, 35, 2_325_829),
    (0.0100, 35, 1_431_245),
    (0.0150, 40, 572_873),
    (0.0200, 46, -430_126),
    (0.0300, 54, -2_940_054),
    (0.0500, 61, -8_717_501),
    (0.0800, 71, -18_540_551),
)


# Un modelo de puja con la curva de primas plana, como la que
# produccion tiene calibrada hoy: siete escenarios con la misma
# probabilidad.
MODELO = {
    "premium": {
        "curve": [
            [1.0, 0.1429],
            [1.0052, 0.1429],
            [1.0259, 0.1429],
            [1.0411, 0.1429],
            [1.0695, 0.1429],
            [1.2027, 0.1429],
            [1.2449, 0.1429],
        ],
        "calibrated": True,
        "samples": 48,
    }
}


# ============================================================
# PRUEBAS
# ============================================================


def test_la_prima_maxima_es_la_que_maximiza_la_curva():
    """
    LA GUARDIA CON LA CURVA DENTRO.

    Si alguien mueve `PRIMA_MAXIMA_DE_PUJA` a un importe que no
    es el maximo de la curva, esto se pone rojo y le enseña la
    tabla.
    """

    mejor = max(CURVA, key=lambda fila: fila[2])

    assert abs(PRIMA_MAXIMA_DE_PUJA - mejor[0]) < 1e-9, (
        "la prima maxima es "
        + str(PRIMA_MAXIMA_DE_PUJA)
        + " y el maximo de la curva esta en "
        + str(mejor[0])
        + " (neto "
        + str(mejor[2])
        + "). Si la curva ha cambiado, rehazla con "
        "scripts/la_curva_de_la_prima.py y actualiza las dos "
        "cosas a la vez."
    )


def test_nunca_por_encima_del_punto_de_equilibrio():
    """
    LA GUARDIA QUE PIDE EL DUEÑO.

    El Computer recompra a +1,8 %. Pujar por encima de eso es
    comprar con perdida garantizada, antes de que el jugador se
    mueva.
    """

    assert PRIMA_MAXIMA_DE_PUJA < PRIMA_DE_EQUILIBRIO, (
        "se puja al "
        + f"{100 * PRIMA_MAXIMA_DE_PUJA:.2f} %"
        + " y el Computer recompra al "
        + f"{100 * PRIMA_DE_EQUILIBRIO:.2f} %"
        + ": cada compra nace en perdidas"
    )


def test_la_curva_cambia_de_signo_en_el_equilibrio():
    """
    Que la curva guardada y la prima de equilibrio cuenten la
    misma historia. Si una de las dos se toca sin la otra, esto
    lo canta.
    """

    for importe, _, neto in CURVA:

        if importe < PRIMA_DE_EQUILIBRIO:
            assert neto > 0, (
                f"la curva dice que ofrecer un {100 * importe:.2f} "
                f"% pierde ({neto}), y eso esta POR DEBAJO del "
                f"equilibrio"
            )

        if importe > PRIMA_DE_EQUILIBRIO:
            assert neto < 0, (
                f"la curva dice que ofrecer un {100 * importe:.2f} "
                f"% gana ({neto}), y eso esta POR ENCIMA del "
                f"equilibrio"
            )


def test_ganar_mas_jugadores_no_es_ganar_mas_dinero():
    """
    La trampa que mide la curva: subir la oferta SIEMPRE gana
    mas subastas, y aun asi pierde dinero. Si alguna vez la
    curva dejara de tener esa forma, habria que rehacer el
    razonamiento entero.
    """

    ganadas = [fila[1] for fila in CURVA]

    assert ganadas == sorted(ganadas), (
        "en la curva, ofrecer mas no siempre gana mas subastas: "
        "el razonamiento no se sostiene"
    )

    assert CURVA[-1][1] > CURVA[1][1], "el +8 % gana mas subastas"

    assert CURVA[-1][2] < CURVA[1][2], (
        "...y aun asi tiene que ganar menos dinero"
    )


def test_no_se_ofrece_por_encima_del_tope():
    """
    El tope se aplica sobre el techo, asi que ningun importe
    candidato puede pasarse.
    """

    precio = 1_000_000

    tope = tope_por_la_prima(precio)

    for importe in candidate_bids(
        precio, 9_000_000, MODELO
    ):
        assert importe <= tope, (
            f"se propone {importe} y el tope es {tope}"
        )


def test_el_tope_no_impide_pujar():
    """
    Nunca por debajo de `precio + 1`: si no, no se podria pujar
    por nadie y el arreglo seria peor que el problema.
    """

    for precio in (10_000, 150_000, 4_550_000, 20_000_000):

        importes = candidate_bids(precio, 99_000_000, MODELO)

        assert importes, f"sin importes para {precio}"

        assert min(importes) >= precio + 1


def test_se_puede_quitar_para_enseñar_el_antes():
    """
    El tablero recalcula SIN tope para poder publicar los dos
    numeros. Un cambio que no se ve es un cambio que nadie
    audita.
    """

    precio = 1_000_000

    con = candidate_bids(precio, 9_000_000, MODELO)

    sin = candidate_bids(
        precio, 9_000_000, MODELO, prima_maxima=None
    )

    assert max(sin) > max(con), (
        "quitar el tope no cambia nada: no se puede enseñar el "
        "antes"
    )


def test_el_tablero_publica_el_antes_y_el_ahorro():
    """
    En cada objetivo: lo que ofreceria sin tope, lo que ofrece
    ahora y la diferencia. Y el acumulado del escaparate entero,
    porque mil euros por jugador no dicen nada y la suma si.
    """

    from pathlib import Path

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    for clave in (
        "bid_sin_tope",
        "ahorro_del_tope",
        "bid_cap",
        "saved_total",
        "bids_capped",
    ):
        assert clave in fuente, (
            f"el tablero no publica «{clave}»"
        )


def test_el_tope_no_cambia_la_forma_de_decidir():
    """
    `optimal_bid` sigue eligiendo igual entre los importes que
    quedan. Lo unico que cambia es hasta donde puede llegar.
    """

    plan = optimal_bid(
        price=1_000_000,
        value=1_300_000,
        model=MODELO,
        available_budget=9_000_000,
        intent="SPECULATION",
    )

    assert plan["decision"] == "BID", plan

    assert plan["bid"] <= tope_por_la_prima(1_000_000)


def test_el_tope_es_de_la_especulacion_y_no_de_todo():
    """
    LA TENSION QUE ME ENSEÑO UNA GUARDIA ROJA (11/09/2026)

    Al topar `optimal_bid` entero se puso roja
    `test_con_rivales_activos_se_sube_hasta_donde_compensa`, que
    dice que con seis rivales activos pujar el minimo es tirar la
    operacion.

    Tiene razon EN SU MUNDO: si solo se puede tirar una vez,
    subir es correcto. La curva mide otra cosa —el mercado diario
    del Computer, con veinte candidatos y perdidas gratis—.

    Asi que el tope se aplica a la ESPECULACION. Comprar al
    jugador que hace falta para el once es un disparo, y el
    margen se paga en puntos, no en reventa.
    """

    precio = 1_000_000

    tope = tope_por_la_prima(precio)

    especulando = optimal_bid(
        price=precio,
        value=1_300_000,
        model=MODELO,
        available_budget=9_000_000,
        intent="SPECULATION",
    )

    assert especulando["bid"] <= tope, (
        "especulando se ofrece "
        + str(especulando["bid"])
        + " y el tope es "
        + str(tope)
    )

    # Sin intencion declarada, el comportamiento de siempre: el
    # tope no puede cambiarle la decision a quien no lo pidio.
    sin_intencion = optimal_bid(
        price=precio,
        value=1_300_000,
        model=MODELO,
        available_budget=9_000_000,
    )

    assert sin_intencion["decision"] in {
        "BID",
        "NO_COMPENSA",
        "SUPERA_PRESUPUESTO",
    }

    # Y con un modelo donde subir SI compensa. Se reutiliza el
    # constructor de la guardia de al lado en vez de inventar
    # uno: un modelo de mentira mal montado da `p=1` en todos
    # los importes y la prueba pasaria sin probar nada. Me paso
    # en el primer intento.
    from src.analysis.test_rival_bid_model_v1 import (
        PRECIO,
        VALOR,
        modelo,
        todos,
    )

    con_rivales = modelo(todos(30_000_000, 20_000_000, 15, 5))

    libre = optimal_bid(PRECIO, VALOR, con_rivales)

    atado = optimal_bid(
        PRECIO, VALOR, con_rivales, intent="SPECULATION"
    )

    assert libre["bid"] > PRECIO + 1, (
        "sin intencion declarada y con seis rivales activos "
        "deberia subir, y ofrece " + str(libre["bid"])
    )

    assert atado["bid"] <= tope_por_la_prima(PRECIO), (
        "especulando se ha pasado del tope: "
        + str(atado["bid"])
    )

    assert atado["bid"] < libre["bid"], (
        "el tope no esta cambiando nada en la especulacion"
    )


def test_nada_de_esto_lanza():

    for precio in (None, 0, -5, "x"):

        assert isinstance(tope_por_la_prima(precio), int)

        assert isinstance(
            candidate_bids(precio, 1_000, MODELO), list
        )

    assert tope_por_la_prima(1_000, None) == 0
    assert tope_por_la_prima(1_000, "x") == 0


def test_estas_guardias_no_leen_el_estado():
    """REGLA 23. Ni disco, ni red, ni reloj."""

    import ast

    from pathlib import Path

    from src.analysis.test_verja_determinista_v1 import (
        _docstrings,
    )

    fuente = Path(__file__).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    fuera = _docstrings(arbol)

    prohibido = "dat" + "a/"

    for nodo in ast.walk(arbol):

        if id(nodo) in fuera:
            continue

        if isinstance(nodo, ast.Constant) and isinstance(
            nodo.value, str
        ):
            assert prohibido not in nodo.value, nodo.value


TESTS = [
    test_la_prima_maxima_es_la_que_maximiza_la_curva,
    test_nunca_por_encima_del_punto_de_equilibrio,
    test_la_curva_cambia_de_signo_en_el_equilibrio,
    test_ganar_mas_jugadores_no_es_ganar_mas_dinero,
    test_no_se_ofrece_por_encima_del_tope,
    test_el_tope_no_impide_pujar,
    test_se_puede_quitar_para_enseñar_el_antes,
    test_el_tablero_publica_el_antes_y_el_ahorro,
    test_el_tope_no_cambia_la_forma_de_decidir,
    test_el_tope_es_de_la_especulacion_y_no_de_todo,
    test_nada_de_esto_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA PRIMA DE PUJA V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
