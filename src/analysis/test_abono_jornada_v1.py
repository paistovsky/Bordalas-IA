"""
El abono de la jornada, en el libro de los siete.

EL CASO (20/08/2026)

    Al cerrar la jornada 1, Biwenger abono dinero a todo el
    mundo. El dueño lo trajo:

        "Por cierto, hay abonos, eso no sé si te lo dije."

    Son 30.000 EUR por punto, exactos. Se comprobo en las siete
    filas de la jornada 1:

        42 -> 1.260.000    31 -> 930.000    29 -> 870.000
        21 ->   630.000    14 -> 420.000    10 -> 300.000

    El libro de `rival_intelligence_engine` -saldo inicial,
    ingresos, gastos, saldo- se construye sumando compras y
    ventas del tablon. El abono no estaba.

POR QUE IMPORTA MAS EN LOS RIVALES

    Nuestro saldo lo dice Biwenger y se puede cuadrar. El de
    ellos NO: en esta liga `settings.balance` esta en `hidden`.
    Ese libro es la unica estimacion que hay y **nada lo
    corrige**.

    Sin el abono, el saldo estimado de cada rival se aleja de la
    realidad hasta 1,26 M cada jornada. En cinco jornadas, el
    modelo de "cuanto puede pujar" no vale nada.

LO QUE SE PROTEGE AQUI

    1. Que el precio del punto no se toque sin querer.
    2. Que sea una REEXPRESION y no un asiento que se suma. Los
       puntos son provisionales y se ajustan; sumando, cada
       correccion duplicaria el ingreso.
    3. Que entre en el libro de TODOS, no solo en el nuestro.
    4. Que NO se cuele en el plan de solvencia. El abono llega
       despues de cerrar la jornada; para decidir solo cuenta el
       dinero que hay en la cuenta.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.rival_intelligence_engine import (
    EUROS_POR_PUNTO,
    apply_matchday_bonus,
    matchday_bonus,
)


# La jornada 1 de verdad, tal y como la enseño Biwenger.
JORNADA_1 = [
    ("Mex", 42, 1_260_000),
    ("DiosMande a Rodri al Palancas", 31, 930_000),
    ("Pepe Bordalás", 29, 870_000),
    ("Luismi_Haz", 29, 870_000),
    ("Pollo17", 21, 630_000),
    ("Prinzipote", 14, 420_000),
    ("Manzagool", 10, 300_000),
]


def libro():
    """Un libro como el que sale del tablon, sin abonos."""

    managers = {}

    for indice, (nombre, puntos, _) in enumerate(
        JORNADA_1, start=1
    ):
        managers[indice] = {
            "user_id": indice,
            "name": nombre,
            "points": puntos,
            "initial_balance": 23_300_000,
            "income": 1_000_000,
            "expenses": 5_000_000,
            "balance": 19_300_000,
            "transactions": [{"type": "market"}],
        }

    return managers


# ============================================================
# PRUEBAS
# ============================================================


def test_el_precio_del_punto():
    """
    Treinta mil euros. Si alguien lo mueve, toda la contabilidad
    de la liga se mueve con el.
    """

    assert EUROS_POR_PUNTO == 30_000


def test_las_siete_filas_de_la_jornada_1():
    """
    El caso real, entero. Si la formula deja de reproducir estos
    siete numeros, es que ya no describe el juego.
    """

    for nombre, puntos, esperado in JORNADA_1:
        assert matchday_bonus(puntos) == esperado, (
            f"{nombre}: {puntos} puntos deberian abonar "
            f"{esperado}, no {matchday_bonus(puntos)}"
        )


def test_jugar_mal_no_cuesta_dinero():
    """
    Un jugador puede restar puntos, asi que un manager podria
    quedar en negativo. Biwenger no cobra por eso, y un abono
    negativo le quitaria dinero a alguien sin motivo.
    """

    assert matchday_bonus(-5) == 0
    assert matchday_bonus(0) == 0


def test_entra_en_el_libro_de_todos():
    """
    El dueño lo pidio asi: "que se registre como ingreso a los
    rivales tambien". Un abono que solo se apunta en el libro
    propio deja el de los otros seis igual de roto que antes.
    """

    managers = libro()

    apply_matchday_bonus(managers)

    for indice, (nombre, puntos, esperado) in enumerate(
        JORNADA_1, start=1
    ):
        manager = managers[indice]

        assert manager["matchday_bonus"] == esperado, nombre

        assert manager["income"] == 1_000_000 + esperado, (
            f"{nombre}: el abono no ha entrado en ingresos"
        )

        assert manager["balance"] == 19_300_000 + esperado, (
            f"{nombre}: el abono no ha movido el saldo"
        )


def test_se_reexpresa_y_no_se_acumula():
    """
    EL CANDADO QUE IMPORTA.

    Los puntos son PROVISIONALES mientras haya partidos
    aplazados. Cuando se ajusten, el abono tiene que ajustarse
    con ellos, no sumarse otra vez encima.

    Aqui se simula el ajuste: los mismos managers, con los puntos
    corregidos, y el libro reconstruido desde el tablon como hace
    el ciclo de verdad.
    """

    primero = libro()
    apply_matchday_bonus(primero)

    saldo_con_29 = primero[3]["balance"]

    # Se juega el aplazado y Pepe pasa de 29 a 34.
    segundo = libro()
    segundo[3]["points"] = 34
    apply_matchday_bonus(segundo)

    assert segundo[3]["matchday_bonus"] == 34 * 30_000

    assert segundo[3]["balance"] == saldo_con_29 + 5 * 30_000, (
        "el ajuste de puntos no se ha reexpresado: el saldo "
        "arrastra el abono viejo"
    )


def test_el_abono_no_toca_los_movimientos_del_tablon():
    """
    `transactions` son hechos observados uno a uno. El abono es
    una derivacion de los puntos, y mezclarlo ahi haria que la
    auditoria del tablon dejase de cuadrar contra lo que de
    verdad paso.
    """

    managers = libro()

    apply_matchday_bonus(managers)

    for manager in managers.values():
        assert len(manager["transactions"]) == 1, (
            "el abono se ha colado como movimiento del tablon"
        )

    # Pero tiene que poder auditarse: de donde sale el numero.
    assert managers[3]["matchday_bonus_points"] == 29
    assert managers[3]["matchday_bonus_rate"] == 30_000


def test_el_abono_no_entra_en_el_plan_de_solvencia():
    """
    "Los puntos siempre se dan tras terminar la jornada. No se
     puede contar con ellos para estar en positivo al inicio de
     la siguiente."

    Contarlo como caja haria a Pepe menos agresivo vendiendo
    justo cuando mas falta hace. El plan de deuda solo cuenta el
    dinero que esta en la cuenta.
    """

    fuente = (
        Path(__file__).parent
        / "safe_debt_portfolio_engine.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nombres = [nodo.module or ""]
        else:
            continue

        for nombre in nombres:
            assert "rival_intelligence_engine" not in nombre, (
                "el plan de deuda ha empezado a mirar el libro "
                "de abonos: eso es dinero que todavia no ha "
                "llegado"
            )

    assert "matchday_bonus" not in fuente
    assert "EUROS_POR_PUNTO" not in fuente



# ============================================================
# LO QUE EL ABONO SIGNIFICA AL FICHAR
# ============================================================


def test_un_fichaje_se_paga_solo_por_debajo_de_30k_el_punto():
    """
    LA VARA QUE FALTABA (21/08/2026)

        Hasta hoy la unica referencia era "lo que pide el mercado
        por un punto" -22.058 EUR de mediana-. Eso dice si algo
        esta CARO COMPARADO CON OTROS, no si merece la pena.

        El abono si: si un fichaje cuesta menos de 30.000 EUR por
        punto que de verdad va a sumar, el abono solo ya lo
        cubre. Lo que sobra es beneficio, y encima queda el
        jugador para revenderlo.

        Un punto es un punto: da igual en que jornada llegue,
        paga lo mismo. Por eso las dos cifras son comparables sin
        inventar horizontes.
    """

    from src.analysis.acquisition_board import _se_paga_solo

    # El precio de mercado tipico esta por debajo del abono: la
    # mayoria de fichajes razonables se pagan solos.
    assert _se_paga_solo(22_058) is True
    assert _se_paga_solo(29_999) is True

    assert _se_paga_solo(30_000) is False
    assert _se_paga_solo(37_500) is False


def test_sin_coste_por_punto_no_se_contesta():
    """
    Ausencia de dato != dato. Un `False` aqui se leeria como "no
    se paga", cuando la verdad es que no se sabe.
    """

    from src.analysis.acquisition_board import _se_paga_solo

    assert _se_paga_solo(None) is None
    assert _se_paga_solo(0) is None
    assert _se_paga_solo(-100) is None
    assert _se_paga_solo("cualquier cosa") is None


def test_el_precio_del_punto_vive_en_un_solo_sitio():
    """
    Si Biwenger cambia el abono, tiene que cambiar en un sitio y
    valer para todo. Dos constantes iguales acaban siendo dos
    constantes distintas.
    """

    from src.analysis import acquisition_board
    from src.analysis import rival_intelligence_engine

    assert (
        acquisition_board.EUROS_POR_PUNTO
        is rival_intelligence_engine.EUROS_POR_PUNTO
        or acquisition_board.EUROS_POR_PUNTO
        == rival_intelligence_engine.EUROS_POR_PUNTO
    )

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert "from src.analysis.rival_intelligence_engine import" in fuente, (
        "el tablero de fichajes se ha hecho su propia copia del "
        "precio del punto"
    )



def main():

    pruebas = [
        test_el_precio_del_punto,
        test_las_siete_filas_de_la_jornada_1,
        test_jugar_mal_no_cuesta_dinero,
        test_entra_en_el_libro_de_todos,
        test_se_reexpresa_y_no_se_acumula,
        test_el_abono_no_toca_los_movimientos_del_tablon,
        test_el_abono_no_entra_en_el_plan_de_solvencia,
        test_un_fichaje_se_paga_solo_por_debajo_de_30k_el_punto,
        test_sin_coste_por_punto_no_se_contesta,
        test_el_precio_del_punto_vive_en_un_solo_sitio,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Abono de la jornada: todo en verde.")


if __name__ == "__main__":
    main()
