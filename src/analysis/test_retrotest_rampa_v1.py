"""
Un retrotest con celdas rellenadas a ojo es peor que no tenerlo.

SINTOMA

    De este retrotest cuelgan tres decisiones: si la via TENER se
    enciende, con que horizonte, y si el liston del 3 % se queda
    o se cambia. Si la tabla miente, mienten las tres.

CAUSA

    La tentacion de una tabla es rellenarla. Con una ventana
    corta, los horizontes de 5, 7 y 10 no se pueden medir —y el
    tramo de racha "mas de 7 dias" tampoco existe—, pero la tabla
    tiene esas casillas y quedan feas vacias.

CONSECUENCIA

    Una mediana de cuatro operaciones parece un dato y no lo es.
    Peor: parece un dato QUE APOYA lo que uno queria hacer.

# ============================================================
# LO QUE CAMBIO EL 17/09/2026, CON PRODUCCION CAIDA
# ============================================================

SEGUNDO SINTOMA

    Esta guardia iba verde en el disco del dueño (82/82) y roja
    en GitHub Actions. Produccion parada desde las 11:00.

SEGUNDA CAUSA

    Leia el almacen REAL, `data/autopilot/price_history.json`.
    En local tiene seis dias; en la cache de Actions tiene los
    que lleve produccion acumulados —la cache se restaura ANTES
    de correr la verja—.

    Reproducido a mano con el mismo codigo:

        almacen de  6 dias  ->  las doce en verde
        almacen de 25 dias  ->  tres en rojo

            "el horizonte de 7 dias tiene 3034 operaciones"
            "el tramo 2-4 % rinde 1,96 %: por debajo del 3 %"
            "comprar a alguien que cae ya no pierde dinero"

    Ninguna de las tres era un fallo del codigo. Eran tres
    afirmaciones sobre el MERCADO, y el mercado de la cache no es
    el del disco.

CONSECUENCIA DE LA SEGUNDA

    La verja dejo de ser una verja. Su unica promesa —verde aqui
    es verde alli— se rompio, y con ella el ciclo de produccion.

LO QUE SE HIZO

    El almacen de esta guardia es ahora un fixture construido en
    el propio repositorio: siempre los mismos 300 jugadores y los
    mismos seis dias. No se lee `data/` en ninguna linea.

    Las dos afirmaciones que eran conclusiones de mercado
    —"TENER paga en el tramo de arriba", "quien cae vuelve a
    caer"— siguen aqui, pero comprobando que el CODIGO las lee
    bien de una tabla conocida. Medir el mercado es trabajo del
    informe, no de la verja.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.hold_backtest import (
    MIN_SAMPLE,
    backtest,
    best_horizon,
    daily_rate,
    streak,
)
from src.analysis.price_store_fixture import almacen_de_mentira


def _resultado():
    """
    El retrotest sobre el almacen inventado.

    Antes esto leia `data/autopilot/price_history.json` y
    devolvia `None` si no existia. Esa era la puerta por la que
    entro el mercado en la verja.
    """

    with almacen_de_mentira() as almacen:
        return backtest(almacen)


# ============================================================
# 1. LO QUE NO SE PUEDE MEDIR SALE VACIO
# ============================================================


def test_las_celdas_sin_muestra_se_marcan_como_vacias() -> None:
    resultado = _resultado()

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

    EL FIXTURE TIENE SEIS DIAS A PROPOSITO

        Con el almacen real esta comprobacion decia lo contrario
        segun el dia: con 25 dias de cache, el horizonte de 7
        tenia 3.034 operaciones y la guardia caia. La ventana es
        ahora una constante del fixture, no del mercado.
    """

    resultado = _resultado()

    assert resultado["window"]["days"] < 7, (
        "el fixture ha dejado de tener la ventana corta que hace "
        "medibles estas dos comprobaciones"
    )

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
    saber de que fechas habla la tabla.
    """

    resultado = _resultado()

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
# 3. LA TABLA SE LEE BIEN
# ============================================================
#
# QUE SE COMPRUEBA AQUI Y QUE NO
#
#     Antes: "el tramo 2-4 % rinde mas del 3 % en produccion".
#     Eso es una medicion del mercado y cambiaba sola.
#
#     Ahora: "dado un almacen donde el tramo 2-4 % sube al 3 %
#     diario, el retrotest lo lee y lo coloca donde toca". Eso es
#     una propiedad del codigo y no cambia nunca.
#
#     Si lo que se quiere saber es si el mercado paga, esta en el
#     informe de la noche, que se recalcula con datos de verdad.


def test_el_retrotest_lee_el_tramo_de_arriba_donde_esta() -> None:
    """
    En el fixture, el tramo 2-4 % sube al 3 % diario. A tres dias
    eso son nueve y pico por ciento, y el retrotest tiene que
    encontrarlo en su celda y no en otra.
    """

    resultado = _resultado()

    celda = resultado["cells"]["2-4 %|1 dia|3"]

    assert celda["enough"], (
        f"la celda del tramo bueno se ha quedado sin muestra "
        f"({celda['n']} operaciones) con un fixture que la llena "
        f"a proposito"
    )

    assert celda["median"] > 0.03
    assert celda["loss_rate"] < 0.20


def test_a_mas_tasa_mas_rendimiento() -> None:
    """
    LO QUE DESTAPO PARTIR EL TRAMO

        Con el tramo abierto por arriba, Gorosabel (4,849 %/dia) y
        Roro Riquelme (1,666 %/dia) aterrizaban los dos en el
        mismo 1,80 %. Tres veces la tasa, el mismo valor.

    Aqui se comprueba que los cortes estan puestos donde dicen:
    tres grupos que suben al 1,5 %, al 3 % y al 6 % diario tienen
    que caer en tres tramos distintos y en ese orden. Si algun
    dia uno se cuela en el tramo del otro, los cortes estan mal.
    """

    resultado = _resultado()

    medianas = []

    for tramo in ("1-2 %", "2-4 %", "> 4 %"):

        celda = resultado["cells"][f"{tramo}|1 dia|3"]

        assert celda["enough"], (
            f"el tramo {tramo} se ha quedado sin muestra en el "
            f"fixture"
        )

        medianas.append((tramo, celda["median"]))

    for (tramo_a, a), (tramo_b, b) in zip(medianas, medianas[1:]):
        assert b > a, (
            f"{tramo_b} rinde {b * 100:.2f} % y {tramo_a} rinde "
            f"{a * 100:.2f} %: mas tasa deberia rendir mas"
        )


def test_quien_cae_se_clasifica_como_que_cae() -> None:
    """
    Sostiene el tramo nuevo de la cola de ventas y el freno de
    compra en rampa bajista.

    El fixture tiene 120 jugadores que bajan todos los dias. Si
    el retrotest los pone en cualquier tramo que no sea CAE, o
    les saca una mediana positiva, esta clasificando al reves.
    """

    resultado = _resultado()

    celda = resultado["cells"]["CAE|1 dia|1"]

    assert celda["enough"]

    assert celda["median"] < 0, (
        "comprar a alguien que cae ya no pierde dinero: hay que "
        "revisar el freno"
    )
    assert celda["loss_rate"] > 0.80, (
        f"solo el {celda['loss_rate'] * 100:.0f} % de las compras "
        f"en rampa bajista pierden"
    )


def test_el_horizonte_elegido_es_el_que_maximiza_la_mediana() -> None:
    """
    Y no el que da el numero mas bonito.
    """

    resultado = _resultado()

    elegido = best_horizon(resultado)

    assert elegido is not None

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
    test_el_retrotest_lee_el_tramo_de_arriba_donde_esta,
    test_a_mas_tasa_mas_rendimiento,
    test_quien_cae_se_clasifica_como_que_cae,
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

        # UN FALLO QUE NO ES UNA ASERCION TAMBIEN ES UN FALLO
        #
        #     Con la cache corta esta guardia reventaba con un
        #     KeyError que `main` no atrapaba: salia un traceback
        #     suelto en vez de una linea de rojo. Un error que no
        #     se sabe leer tarda el doble en arreglarse.
        except Exception as exc:                    # noqa: BLE001
            fallos += 1
            print(
                f"ROMPE {test.__name__}: "
                f"{type(exc).__name__}: {exc}"
            )

    print("=" * 60)
    print(f"RETROTEST DE LA RAMPA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
