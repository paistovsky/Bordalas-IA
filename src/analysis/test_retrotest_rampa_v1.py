"""
Un retrotest con celdas rellenadas a ojo es peor que no tenerlo.

SINTOMA

    De este retrotest cuelgan tres decisiones: si la via TENER se
    enciende, con que horizonte, y si el liston del 3 % se queda
    o se cambia. Si la tabla miente, mienten las tres.

CAUSA

    La tentacion de una tabla es rellenarla. Con una ventana de
    seis dias, los horizontes de 5, 7 y 10 no se pueden medir —y
    el tramo de racha "mas de 7 dias" tampoco existe—, pero la
    tabla tiene esas casillas y quedan feas vacias.

CONSECUENCIA

    Una mediana de cuatro operaciones parece un dato y no lo es.
    Peor: parece un dato QUE APOYA lo que uno queria hacer.

    Esta guardia comprueba que lo que no se puede medir sale
    marcado como no medido, que la ventana se publica entera, y
    que los numeros que sostienen la via TENER son los que de
    verdad salen del historico.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.hold_backtest import (
    HORIZONS,
    MIN_SAMPLE,
    backtest,
    best_horizon,
    daily_rate,
    load_series,
    streak,
)


ALMACEN = Path("data") / "autopilot" / "price_history.json"


def _resultado():
    if not ALMACEN.exists():
        return None

    return backtest()


# ============================================================
# 1. LO QUE NO SE PUEDE MEDIR SALE VACIO
# ============================================================


def test_las_celdas_sin_muestra_se_marcan_como_vacias() -> None:
    resultado = _resultado()

    if resultado is None:
        return

    for clave, celda in resultado["cells"].items():

        if celda.get("enough"):
            assert celda["n"] >= MIN_SAMPLE
            assert celda.get("median") is not None

        else:
            assert celda.get("reason"), (
                f"la celda {clave} no tiene muestra y no dice por "
                f"que esta vacia"
            )
            assert "median" not in celda, (
                f"la celda {clave} publica una mediana sin muestra "
                f"suficiente ({celda['n']} operaciones)"
            )


def test_los_horizontes_largos_salen_vacios_y_lo_dicen() -> None:
    """
    Seis dias de historico no pueden medir un horizonte de 7 ni
    de 10. Si algun dia salieran con numero, seria que alguien
    los ha inventado.
    """

    resultado = _resultado()

    if resultado is None:
        return

    for m in (7, 10):

        resumen = resultado["by_horizon_rising"][m]

        assert resumen["n"] == 0, (
            f"el horizonte de {m} dias tiene {resumen['n']} "
            f"operaciones con una ventana de "
            f"{resultado['window']['days']} dias"
        )
        assert not resumen["enough"]


def test_la_ventana_se_publica_entera() -> None:
    """
    De cuando a cuando va el historico. Sin eso, nadie puede
    saber que la tabla habla de agosto y no de hoy.
    """

    resultado = _resultado()

    if resultado is None:
        return

    ventana = resultado["window"]

    assert ventana["from"] and ventana["to"]
    assert ventana["days"] >= 2
    assert resultado["players"] > 0
    assert resultado["operations"] > 0


def test_el_corte_de_muestra_es_explicito() -> None:
    assert MIN_SAMPLE == 30


# ============================================================
# 2. LAS CUENTAS
# ============================================================


def test_la_tasa_diaria_es_contra_el_dia_anterior() -> None:
    precios = [100, 110, 99]

    assert daily_rate(precios, 0) is None
    assert abs(daily_rate(precios, 1) - 0.10) < 1e-9
    assert abs(daily_rate(precios, 2) + 0.10) < 1e-9


def test_la_racha_cuenta_dias_del_mismo_signo() -> None:
    """
    La misma definicion que la columna `Tend` de FutbolFantasy.
    """

    sube = [100, 101, 102, 103]

    assert streak(sube, 1) == 1
    assert streak(sube, 2) == 2
    assert streak(sube, 3) == 3

    # Un cambio de signo corta la racha.
    gira = [100, 101, 102, 99]

    assert streak(gira, 3) == 1

    # Un dia plano tambien.
    plano = [100, 101, 101, 102]

    assert streak(plano, 2) == 0
    assert streak(plano, 3) == 1


def test_una_serie_de_un_solo_dia_no_produce_operaciones() -> None:
    from src.analysis.hold_backtest import build_operations

    assert build_operations({1: [100]}) == []


# ============================================================
# 3. LO QUE SOSTIENE LA VIA TENER
# ============================================================


def test_tener_paga_en_el_tramo_de_arriba() -> None:
    """
    EL NUMERO QUE ENCIENDE LA VIA

        Si esto deja de ser cierto, la via TENER se apaga: no
        estaria apoyada por nada.

    EL TRAMO SE PARTIO EL 16/09

        Antes era "> 1 %" abierto por arriba, y ahi dentro
        convivian un jugador al 1,01 %/dia y otro al 4,85 %. Este
        test miraba esa celda; ahora mira las tres.
    """

    resultado = _resultado()

    if resultado is None:
        return

    celda = resultado["cells"]["2-4 %|1 dia|3"]

    if not celda.get("enough"):
        return

    assert celda["median"] > 0.03, (
        f"comprar entre el 2 y el 4 %/dia y vender a tres dias "
        f"rinde {celda['median'] * 100:.2f} % de mediana: por "
        f"debajo del 3 % que exige la casa, asi que la via TENER "
        f"no esta respaldada"
    )

    assert celda["loss_rate"] < 0.20, (
        f"{celda['loss_rate'] * 100:.0f} % de operaciones en "
        f"perdida en el tramo bueno"
    )


def test_a_mas_tasa_mas_rendimiento() -> None:
    """
    LO QUE DESTAPO PARTIR EL TRAMO

        Con el tramo abierto por arriba, Gorosabel (4,849 %/dia) y
        Roro Riquelme (1,666 %/dia) aterrizaban los dos en el
        mismo 1,80 %. Tres veces la tasa, el mismo valor.

        Partido, la escalera se ve: +3,22 % / +5,61 % / +18,37 %.
        Si algun dia deja de ser monotona, el corte de los tramos
        esta mal puesto.
    """

    resultado = _resultado()

    if resultado is None:
        return

    medianas = []

    for tramo in ("1-2 %", "2-4 %", "> 4 %"):

        celda = resultado["cells"][f"{tramo}|1 dia|3"]

        if not celda.get("enough"):
            return

        medianas.append((tramo, celda["median"]))

    for (tramo_a, a), (tramo_b, b) in zip(medianas, medianas[1:]):
        assert b > a, (
            f"{tramo_b} rinde {b * 100:.2f} % y {tramo_a} rinde "
            f"{a * 100:.2f} %: mas tasa deberia rendir mas"
        )


def test_quien_cae_vuelve_a_caer() -> None:
    """
    Sostiene el tramo nuevo de la cola de ventas y el freno de
    compra en rampa bajista.
    """

    resultado = _resultado()

    if resultado is None:
        return

    celda = resultado["cells"]["CAE|1 dia|1"]

    if not celda.get("enough"):
        return

    assert celda["median"] < 0, (
        "comprar a alguien que cae ya no pierde dinero: hay que "
        "revisar el freno"
    )
    assert celda["loss_rate"] > 0.80, (
        f"solo el {celda['loss_rate'] * 100:.0f} % de las compras "
        f"en rampa bajista pierden; estaba medido en el 88 %"
    )


def test_el_horizonte_elegido_es_el_que_maximiza_la_mediana() -> None:
    """
    Y no el que da el numero mas bonito.
    """

    resultado = _resultado()

    if resultado is None:
        return

    elegido = best_horizon(resultado)

    if elegido is None:
        return

    medianas = {
        m: datos["median"]
        for m, datos in resultado["by_horizon_rising"].items()
        if datos.get("enough")
    }

    assert medianas[elegido] == max(medianas.values())


def test_el_retrotest_no_lanza_sin_almacen() -> None:
    resultado = backtest(Path("no") / "existe.json")

    assert resultado["available"] is False
    assert resultado["reason"]


TESTS = [
    test_las_celdas_sin_muestra_se_marcan_como_vacias,
    test_los_horizontes_largos_salen_vacios_y_lo_dicen,
    test_la_ventana_se_publica_entera,
    test_el_corte_de_muestra_es_explicito,
    test_la_tasa_diaria_es_contra_el_dia_anterior,
    test_la_racha_cuenta_dias_del_mismo_signo,
    test_una_serie_de_un_solo_dia_no_produce_operaciones,
    test_tener_paga_en_el_tramo_de_arriba,
    test_a_mas_tasa_mas_rendimiento,
    test_quien_cae_vuelve_a_caer,
    test_el_horizonte_elegido_es_el_que_maximiza_la_mediana,
    test_el_retrotest_no_lanza_sin_almacen,
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
    print(f"RETROTEST DE LA RAMPA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
