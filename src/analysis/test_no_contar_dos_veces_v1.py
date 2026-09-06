"""
El mismo euro no se cuenta dos veces.

SINTOMA

    La via TENER del 14/09 vale la RAMPA: lo que sube el precio
    mientras se tiene al jugador. La via del Computer vale la
    PRIMA DE REVENTA: lo que el Computer paga por encima del
    precio de mercado.

    Y la prima se mide contra el precio de mercado DE ESE
    MOMENTO. Si el precio esta subiendo, parte de esa prima ya es
    la rampa.

CAUSA

    Es la tentacion obvia al escribir la cuarta via: "vale la
    rampa MAS la prima, asi que sumamos". Con Amatucci saldria

        3.670.000 + 120.889 (rampa) + 63.124 (prima)

    y los 63.124 estarian contando otra vez euros que ya estan
    dentro de los 120.889.

CONSECUENCIA

    Una via inflada gana el `max()` contra las otras tres y se
    lleva el turno del ciclo. Y como el liston de rendimiento se
    calcula sobre ese valor inflado, ademas lo pasa.

    Es el mismo patron que ya costo dos noches: el valor de una
    via medido con la vara de otra.

    Esta guardia la pidio el encargo por su nombre.
"""

from __future__ import annotations

import ast
import inspect

from pathlib import Path

from src.analysis import hold_value as modulo
from src.analysis.hold_value import (
    DEFAULT_HORIZON_DAYS,
    MARGIN,
    MIN_DAILY_RATE,
    ROUTE,
    hold_value,
)


FUENTE = Path("src/analysis/hold_value.py")


# Amatucci, con los numeros de la foto de produccion del 06/09.
PRECIO = 3_670_000
TASA = 1.098
RACHA = 19


# ============================================================
# 1. LA RAMPA NO LLEVA PRIMA DENTRO
# ============================================================


def test_la_via_tener_no_importa_la_prima_de_reventa() -> None:
    """
    Ni el modulo del premium ni la funcion de reventa entran
    aqui. Se comprueba con `ast`, no leyendo prosa: ya nos ha
    mordido tres veces confiar en que el comentario dijera la
    verdad.
    """

    arbol = ast.parse(FUENTE.read_text(encoding="utf-8"))

    prohibidos = (
        "computer_resale_value",
        "computer_premium",
        "premium_confidence",
        "resale_premium",
        "speculation_value",
    )

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"la via TENER importa {prohibido}: la rampa "
                    f"y la prima estarian contando el mismo euro"
                )

        if isinstance(nodo, ast.Call):

            nombre = getattr(nodo.func, "id", None) or getattr(
                nodo.func, "attr", None
            )

            assert nombre not in prohibidos, (
                f"la via TENER llama a {nombre}"
            )


def test_la_ganancia_es_solo_la_rampa() -> None:
    """
    Precio x tasa diaria x horizonte. Ni un euro mas.
    """

    salida = hold_value(
        PRECIO,
        rate_percent_per_day=TASA,
        trend_days=RACHA,
        sources=3,
    )

    esperada = int(PRECIO * (TASA / 100.0) * DEFAULT_HORIZON_DAYS)

    assert salida["raw_gain"] == esperada, (
        f"la ganancia bruta son {salida['raw_gain']:,} y la rampa "
        f"sola son {esperada:,}: hay algo mas sumado"
    )


def test_el_valor_no_pasa_del_precio_mas_la_rampa() -> None:
    """
    El techo aritmetico de esta via. Si alguna vez lo pasa, es
    que se le ha sumado algo de otra.
    """

    for precio, tasa, racha in (
        (3_670_000, 1.098, 19),
        (4_240_000, 1.666, 50),
        (420_000, 4.849, 4),
        (15_350_000, 0.305, 8),
    ):
        salida = hold_value(
            precio,
            rate_percent_per_day=tasa,
            trend_days=racha,
            sources=3,
        )

        techo = precio + int(
            precio * (tasa / 100.0) * DEFAULT_HORIZON_DAYS
        )

        assert salida["value"] <= techo, (
            f"{precio:,} a {tasa} %/dia sale valorado en "
            f"{salida['value']:,}, por encima de precio + rampa "
            f"({techo:,})"
        )


# ============================================================
# 2. LA CONFIANZA VA SOBRE LA GANANCIA
# ============================================================


def test_la_confianza_descuenta_la_ganancia_no_el_capital() -> None:
    """
    LA LECCION DEL 09/09, QUE COSTO UNA NOCHE

        Descontando el capital, cualquier confianza por debajo de
        1 dejaba el maximo POR DEBAJO del propio precio y apagaba
        la via entera.

        El principal no esta en riesgo: si la apuesta falla
        sigues teniendo un jugador que vale aproximadamente lo
        que pagaste.
    """

    salida = hold_value(
        PRECIO,
        rate_percent_per_day=TASA,
        trend_days=RACHA,
        sources=3,
    )

    assert salida["value"] > PRECIO, (
        "la via sale por debajo del precio: se esta descontando "
        "el capital y no la ganancia"
    )

    # Y el descuento tiene que notarse en la ganancia.
    confianza = salida["confidence"]

    esperado = PRECIO + int(
        salida["raw_gain"] * confianza * (1 - MARGIN)
    )

    assert abs(salida["value"] - esperado) <= 1, (
        f"{salida['value']:,} no es precio + ganancia x "
        f"confianza x (1 - margen) = {esperado:,}"
    )


def test_una_racha_larga_vale_menos_que_una_corta() -> None:
    """
    Lo midio el 07/09 y lo confirma el retrotest del 14/09: la
    continuacion hace pico el segundo dia y cae el tercero. Si
    esta via premiara las rachas largas, iria contra sus propios
    numeros.
    """

    corta = hold_value(PRECIO, TASA, trend_days=2, sources=3)
    larga = hold_value(PRECIO, TASA, trend_days=19, sources=3)

    assert corta["value"] > larga["value"], (
        f"una racha de 2 dias vale {corta['value']:,} y una de 19 "
        f"vale {larga['value']:,}: la via premia aguantar, que es "
        f"lo contrario de lo medido"
    )


# ============================================================
# 3. LOS CORTES SALEN DEL RETROTEST
# ============================================================


def test_no_se_compra_en_rampa_bajista() -> None:
    """
    En el retrotest, comprar a alguien que cae y venderlo tres
    dias despues pierde el 95 % de las veces.
    """

    salida = hold_value(PRECIO, rate_percent_per_day=-1.376,
                        trend_days=3, sources=3)

    assert salida["value"] == 0
    assert salida["decision"] == "CAE"
    assert "95 %" in salida["reason"]


def test_por_debajo_del_cuarto_de_punto_no_hay_operacion() -> None:
    """
    El tramo 0-0,25 % no tiene ni muestra suficiente en el
    retrotest, y el de al lado rinde +0,41 % a tres dias con un
    22 % de operaciones en perdida.
    """

    assert MIN_DAILY_RATE == 0.0025

    flojo = hold_value(PRECIO, rate_percent_per_day=0.2,
                       trend_days=1, sources=3)

    assert flojo["value"] == 0
    assert flojo["decision"] == "RITMO_INSUFICIENTE"


def test_sin_ritmo_no_se_valora_a_ciegas() -> None:
    salida = hold_value(PRECIO, rate_percent_per_day=None)

    assert salida["value"] == 0
    assert salida["decision"] == "SIN_RITMO"


def test_el_horizonte_sale_del_retrotest_y_no_de_una_intuicion() -> None:
    """
    Tres dias, y el motivo escrito en el modulo: en m=4 la
    muestra baja de 474 a 242 y la tasa de perdida sube del
    15,2 % al 17,4 %.
    """

    assert DEFAULT_HORIZON_DAYS == 3

    fuente = FUENTE.read_text(encoding="utf-8")

    assert "retrotest" in fuente.lower()
    assert "474" in fuente and "242" in fuente, (
        "el horizonte no lleva al lado la muestra que lo justifica"
    )


# ============================================================
# 4. ES UNA OPERACION DE CARTERA
# ============================================================


def test_la_via_tener_va_al_bolsillo_de_especular() -> None:
    """
    No es un fichaje para el once. La regla del 13/09 -el
    bolsillo, el liston y el valor de la misma via- se respeta
    sin excepcion.
    """

    salida = hold_value(PRECIO, TASA, trend_days=RACHA, sources=3)

    assert salida["intent"] == "SPECULATION"
    assert salida["route"] == ROUTE == "HOLD"


def test_la_clasificacion_la_pone_del_lado_del_comercio() -> None:
    from src.analysis.deployment import TRADE, classify_operation

    clase = classify_operation(
        None,
        None,
        None,
        None,
        as_hold={"route": "HOLD", "value": 3_740_538},
        price=PRECIO,
    )

    assert clase["operation_class"] == TRADE
    assert clase["route"] == "HOLD"
    assert clase["decision_value"] == 3_740_538


def test_la_via_no_lanza_con_basura() -> None:
    for entrada in (
        (0, 1.0),
        (None, None),
        ("no soy un precio", "yo tampoco"),
        (PRECIO, float("nan")),
    ):
        salida = hold_value(*entrada)

        assert isinstance(salida, dict)
        assert "value" in salida


TESTS = [
    test_la_via_tener_no_importa_la_prima_de_reventa,
    test_la_ganancia_es_solo_la_rampa,
    test_el_valor_no_pasa_del_precio_mas_la_rampa,
    test_la_confianza_descuenta_la_ganancia_no_el_capital,
    test_una_racha_larga_vale_menos_que_una_corta,
    test_no_se_compra_en_rampa_bajista,
    test_por_debajo_del_cuarto_de_punto_no_hay_operacion,
    test_sin_ritmo_no_se_valora_a_ciegas,
    test_el_horizonte_sale_del_retrotest_y_no_de_una_intuicion,
    test_la_via_tener_va_al_bolsillo_de_especular,
    test_la_clasificacion_la_pone_del_lado_del_comercio,
    test_la_via_no_lanza_con_basura,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"NO CONTAR DOS VECES V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
