"""
EL INTERRUPTOR DE LA VIA TENER.

SINTOMA (17/09/2026, produccion caida)

    En la verja habia dos aserciones de mercado:

        "el tramo 2-4 % rinde mas del 3 % a tres dias"
        "comprar a alguien que cae pierde el 80 % de las veces"

    Las dos eran ciertas. Ninguna era una propiedad del codigo.
    Con el almacen de la cache de Actions -25 dias en vez de
    seis- el primer tramo rendia un 1,96 % y la verja se ponia
    roja. Ciclo de produccion parado desde las 11:00.

CAUSA

    La pregunta estaba bien; el sitio estaba mal. Una verja
    compara codigo. Preguntarle por el mercado hace que el
    despliegue se caiga cuando cambia el mercado, que es
    exactamente cuando MENOS hay que parar el despliegue.

CONSECUENCIA DE HABERLO QUITADO SIN MAS

    Se habria perdido la pregunta, que es de las importantes: si
    el tramo que sostiene la via TENER deja de rendir el liston,
    la via se apoya en una conclusion de agosto.

LO QUE VIGILA ESTE FICHERO

    Que la pregunta siga viva en su sitio nuevo: en cada ciclo,
    contra el almacen de produccion, apagando la via en vez de
    parar el despliegue.

    Y todo con fixture. Estas comprobaciones no vuelven a
    preguntarle nada al mercado: le dan una tabla conocida y
    miran que el interruptor haga lo que dice.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.hold_switch import (
    MAX_TENER_LOSS_RATE,
    MIN_TENER_YIELD,
    bucket_backing,
    route_state,
)
from src.analysis.hold_value import hold_value


def _calibracion(tramos: dict) -> dict:
    """Una calibracion inventada, con los tramos que se le digan."""

    return {
        "available": True,
        "max_streak": 2,
        "by_rate_bucket": {
            nombre: {
                "calibrated": datos is not None,
                "band": "1 dia",
                "max_streak": 2,
                "median": (datos or {}).get("median"),
                "loss_rate": (datos or {}).get("loss_rate"),
                "n": (datos or {}).get("n", 0),
            }
            for nombre, datos in tramos.items()
        },
    }


# ============================================================
# 1. EL LISTON ES EL DE LA VIA, Y ES UNO SOLO
# ============================================================


def test_el_liston_no_se_copia_se_importa() -> None:
    """
    LA REGLA DEL 13/09

        "El bolsillo, el liston y el valor salen todos de la
         misma via."

    Dos treses en dos ficheros se separan el dia que alguien mueve
    uno. Este tiene que ser EL MISMO objeto que el de la puja.
    """

    from src.analysis.rival_bid_model import RENDIMIENTO_MINIMO_DEL_CAPITAL

    assert MIN_TENER_YIELD == RENDIMIENTO_MINIMO_DEL_CAPITAL == 0.03

    fuente = Path(
        "src/analysis/hold_switch.py"
    ).read_text(encoding="utf-8")

    assert "RENDIMIENTO_MINIMO_DEL_CAPITAL" in fuente, (
        "el liston se ha copiado en vez de importarse"
    )


# ============================================================
# 2. UN TRAMO MEDIDO Y FLOJO APAGA
# ============================================================


def test_un_tramo_por_debajo_del_liston_apaga_la_via() -> None:
    """
    La asercion que se mudo de la verja, en su sitio nuevo.
    """

    calibracion = _calibracion({
        "2-4 %": {"median": 0.0196, "loss_rate": 0.10, "n": 40},
    })

    tramo = bucket_backing(calibracion, "2-4 %")

    assert tramo["measured"] is True
    assert tramo["backed"] is False
    assert "liston" in tramo["reason"]
    assert "1.96" in tramo["reason"]


def test_un_tramo_que_rinde_pero_pierde_demasiado_apaga() -> None:
    """
    La segunda mitad de la asercion. Un tramo puede rendir de
    mediana y perder la mitad de las veces; eso no es una via, es
    una moneda.
    """

    calibracion = _calibracion({
        "2-4 %": {
            "median": 0.09,
            "loss_rate": MAX_TENER_LOSS_RATE + 0.15,
            "n": 40,
        },
    })

    tramo = bucket_backing(calibracion, "2-4 %")

    assert tramo["backed"] is False
    assert "pierde" in tramo["reason"]


def test_un_tramo_que_rinde_respalda() -> None:
    calibracion = _calibracion({
        "2-4 %": {"median": 0.0314, "loss_rate": 0.17, "n": 41},
    })

    tramo = bucket_backing(calibracion, "2-4 %")

    assert tramo["backed"] is True
    assert tramo["margin"] == round(0.0314 - MIN_TENER_YIELD, 4)


# ============================================================
# 3. SIN MUESTRA NO SE APAGA NADA
# ============================================================


def test_un_tramo_sin_muestra_no_es_un_tramo_malo() -> None:
    """
    Ausencia de dato != dato.

    `backed` es None, que no es False. Apagar una via por no
    haberla mirado seria el mismo error que valorarla sin mirarla,
    del otro lado.
    """

    calibracion = _calibracion({"0-0,25 %": None})

    tramo = bucket_backing(calibracion, "0-0,25 %")

    assert tramo["backed"] is None
    assert tramo["measured"] is False
    assert "no se puede decir" in tramo["reason"]


def test_sin_retrotest_la_via_no_se_apaga_pero_se_dice() -> None:
    estado = route_state(
        {"available": False, "reason": "sin almacen"},
        horizon_days=3,
    )

    assert estado["available"] is False
    assert estado["on"] is None
    assert estado["reason"]


# ============================================================
# 4. Y ESO LLEGA AL VALOR
# ============================================================


def test_la_via_no_da_valor_sin_respaldo() -> None:
    """
    EL INTERRUPTOR, DE VERDAD

        No basta con pintarlo en el tablero. Si el tramo de este
        jugador esta medido y no llega al liston, `hold_value`
        tiene que devolver cero y decir por que.
    """

    flojo = _calibracion({
        "1-2 %": {"median": 0.018, "loss_rate": 0.10, "n": 58},
    })

    salida = hold_value(
        4_240_000,
        1.666,
        trend_days=50,
        sources=3,
        calibration_override=flojo,
    )

    assert salida["value"] == 0
    assert salida["decision"] == "SIN_RESPALDO"
    assert "liston" in salida["reason"]


def test_la_via_si_da_valor_con_respaldo() -> None:
    bueno = _calibracion({
        "> 4 %": {"median": 0.2115, "loss_rate": 0.03, "n": 35},
    })

    salida = hold_value(
        420_000,
        4.849,
        trend_days=4,
        sources=3,
        calibration_override=bueno,
    )

    assert salida["value"] > 0
    assert salida["decision"] != "SIN_RESPALDO"


def test_un_tramo_sin_muestra_sigue_valorando() -> None:
    """
    Si no se ha medido, la via trabaja como trabajaba: no se
    apaga por falta de datos.
    """

    sin_medir = _calibracion({"0,25-0,5 %": None})

    salida = hold_value(
        15_350_000,
        0.305,
        trend_days=8,
        sources=3,
        calibration_override=sin_medir,
    )

    assert salida["decision"] != "SIN_RESPALDO"


# ============================================================
# 5. LA LINEA DEL TABLERO
# ============================================================


def test_el_tablero_dice_cual_va_mas_justo() -> None:
    """
    El aviso tiene que llegar ANTES de que se apague. Si el tramo
    que la sostiene va a catorce centesimas del liston, eso hay
    que verlo, no enterarse el dia que cae.
    """

    calibracion = _calibracion({
        "CAE": {"median": -0.0396, "loss_rate": 0.93, "n": 114},
        "1-2 %": {"median": 0.018, "loss_rate": 0.10, "n": 58},
        "2-4 %": {"median": 0.0314, "loss_rate": 0.17, "n": 41},
        "> 4 %": {"median": 0.2115, "loss_rate": 0.03, "n": 35},
        "0-0,25 %": None,
    })

    estado = route_state(calibracion, horizon_days=3)

    assert estado["on"] is True
    assert estado["backing"] == ["2-4 %", "> 4 %"]
    assert "1-2 %" in estado["switched_off"]
    assert "0-0,25 %" in estado["unmeasured"]

    assert estado["closest"]["bucket"] == "2-4 %", (
        "el que va mas justo no es el que menos margen tiene"
    )

    assert "se apaga sola" in estado["reason"]


def test_el_tramo_que_cae_no_cuenta_como_respaldo() -> None:
    """
    CAE es el tramo de los que bajan. La via no compra ahi, asi
    que su rendimiento negativo no puede leerse como "la via esta
    apagada": se mide y se enseña, pero no decide.
    """

    calibracion = _calibracion({
        "CAE": {"median": -0.0396, "loss_rate": 0.93, "n": 114},
        "> 4 %": {"median": 0.2115, "loss_rate": 0.03, "n": 35},
    })

    estado = route_state(calibracion, horizon_days=3)

    assert estado["on"] is True
    assert "CAE" not in estado["switched_off"]
    assert "CAE" not in estado["backing"]

    # Pero sigue publicandose, que era la otra asercion mudada.
    assert any(
        t["bucket"] == "CAE" for t in estado["buckets"]
    )


def test_con_todos_los_tramos_flojos_la_via_se_apaga_entera() -> None:
    calibracion = _calibracion({
        "1-2 %": {"median": 0.005, "loss_rate": 0.30, "n": 58},
        "2-4 %": {"median": 0.0196, "loss_rate": 0.17, "n": 41},
    })

    estado = route_state(calibracion, horizon_days=3)

    assert estado["on"] is False
    assert estado["backing"] == []
    assert "APAGADA" in estado["reason"]
    assert estado["closest"] is None


# ============================================================
# 6. NI LEE ESTADO NI REVIENTA
# ============================================================


def test_el_interruptor_no_lee_el_almacen() -> None:
    """
    La guardia que se estrena esta noche vale para toda la verja,
    pero esta pieza merece la suya: nacio de una caida causada
    justamente por leer el almacen desde una comprobacion.
    """

    estado_dir = "dat" + "a"

    arbol = ast.parse(
        Path("src/analysis/hold_switch.py").read_text(
            encoding="utf-8"
        )
    )

    for nodo in ast.walk(arbol):
        if (
            isinstance(nodo, ast.Constant)
            and isinstance(nodo.value, str)
            and (estado_dir + "/") in nodo.value
        ):
            raise AssertionError(
                f"hold_switch lee {nodo.value!r}: el interruptor "
                f"recibe la calibracion, no va a buscarla"
            )


def test_nada_de_esto_lanza() -> None:
    for basura in (None, {}, {"by_rate_bucket": None}):
        assert isinstance(bucket_backing(basura, "2-4 %"), dict)
        assert isinstance(route_state(basura), dict)


TESTS = [
    test_el_liston_no_se_copia_se_importa,
    test_un_tramo_por_debajo_del_liston_apaga_la_via,
    test_un_tramo_que_rinde_pero_pierde_demasiado_apaga,
    test_un_tramo_que_rinde_respalda,
    test_un_tramo_sin_muestra_no_es_un_tramo_malo,
    test_sin_retrotest_la_via_no_se_apaga_pero_se_dice,
    test_la_via_no_da_valor_sin_respaldo,
    test_la_via_si_da_valor_con_respaldo,
    test_un_tramo_sin_muestra_sigue_valorando,
    test_el_tablero_dice_cual_va_mas_justo,
    test_el_tramo_que_cae_no_cuenta_como_respaldo,
    test_con_todos_los_tramos_flojos_la_via_se_apaga_entera,
    test_el_interruptor_no_lee_el_almacen,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL INTERRUPTOR DE TENER V1")
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
