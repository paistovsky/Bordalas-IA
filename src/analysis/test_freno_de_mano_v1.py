"""
El freno de mano: una posicion especulativa que se gira, se
suelta. Y la leccion de Soler, puesta sobre el mecanismo que de
verdad la protege.

POR QUE EXISTE EL FRENO DE MANO

    Es lo que hace aceptable el acelerador. Comprar rachas
    funciona -el que sube sigue subiendo el 85,1 % de las veces-
    pero toda racha se acaba, y sin regla de salida comprar
    rachas es comprar techos tarde o temprano.

    La misma medicion del 07/09 justifica las dos cosas:

        90,7 %  de los que bajaron ayer bajan hoy
         0,5 %  de los que bajaron baten al mercado

LA LECCION DE SOLER, RECOLOCADA

    El 16/08 se pujo por Soler a 5.950.000 con un margen finisimo
    que inmovilizaba el 81 % del presupuesto.
    `test_la_especulacion_de_soler_ya_no_se_puja` lo guarda desde
    entonces.

    Ese test sigue verde despues de este cambio, y hay un motivo
    concreto: llama a `optimal_bid` con precio y valor FIJOS, sin
    pasar por `value_candidate`. La compuerta de esta noche vive
    en la valoracion, asi que no puede tocarlo. Y no se ha
    movido ningun umbral.

    Pero el propio encargo lo dice: la leccion de Soler es de
    CONCENTRACION, no de rendimiento. El test usa el umbral de
    rendimiento solo porque prueba `optimal_bid` aislado, y esa
    funcion no ve el presupuesto.

    Lo que de verdad protege en produccion es el tope por
    operacion, y eso no lo cubria ninguna guardia. Aqui esta.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.speculative_exit import (
    EXIT_SCORE,
    build_speculative_positions,
    evaluate_exit,
)


def _posiciones(*filas) -> dict:
    return build_speculative_positions({"positions": list(filas)})


def _posicion(player_id=10, strategy="SPECULATION", status="OPEN", **extra):
    base = {
        "player_id": player_id,
        "player_name": f"Jugador {player_id}",
        "position_id": f"POS-{player_id}",
        "strategy": strategy,
        "status": status,
        "bid_amount": 1_000_000,
        "entry_price": 1_000_000,
    }
    base.update(extra)
    return base


def _ritmos(**jugadores) -> dict:
    return {
        int(pid): {
            "rate_percent_per_day": tasa,
            "direction": "UP" if tasa > 0 else "DOWN" if tasa < 0 else "FLAT",
            "trend_days": None,
        }
        for pid, tasa in jugadores.items()
    }


# ============================================================
# 1. A QUIEN SE LE APLICA
# ============================================================


def test_una_posicion_especulativa_girada_se_suelta() -> None:
    salida = evaluate_exit(
        10,
        _posiciones(_posicion(10)),
        _ritmos(**{"10": -2.5}),
    )

    assert salida is not None
    assert salida["score"] == EXIT_SCORE
    assert "90,7 %" in salida["reason"], (
        "el motivo tiene que llevar el numero que lo justifica"
    )


def test_una_posicion_que_sigue_subiendo_no_se_toca() -> None:
    assert evaluate_exit(
        10,
        _posiciones(_posicion(10)),
        _ritmos(**{"10": 3.0}),
    ) is None, "no se vende una racha que sigue viva"


def test_un_jugador_del_once_no_es_una_posicion_girada() -> None:
    """
    LA DISTINCION QUE EVITA UN DESASTRE.

    Sin ella, la primera semana mala de precios propondria vender
    media plantilla. Un jugador que se compro por puntos no se
    suelta porque su precio baje.
    """

    assert evaluate_exit(
        99,
        _posiciones(_posicion(10)),      # 99 no es posicion nuestra
        _ritmos(**{"99": -5.0}),
    ) is None


def test_una_puja_pendiente_no_es_una_posicion() -> None:
    """Todavia no es nuestra: no hay nada que soltar."""

    for estado in ("BID_PENDING", "BID_PENDING_UNCONFIRMED", "LOST"):
        assert evaluate_exit(
            10,
            _posiciones(_posicion(10, status=estado)),
            _ritmos(**{"10": -5.0}),
        ) is None, f"{estado} no deberia contar como posicion abierta"


def test_sin_ritmo_observado_tampoco_se_vende() -> None:
    """
    LA SIMETRIA IMPORTA.

    Si sin dato no se compra, sin dato tampoco se vende. Vender a
    ciegas por si acaso es la version cara del mismo error.
    """

    assert evaluate_exit(
        10,
        _posiciones(_posicion(10)),
        {},
    ) is None


def test_sin_libro_de_posiciones_esto_no_hace_nada() -> None:
    assert build_speculative_positions({}) == {}
    assert build_speculative_positions({"positions": None}) == {}
    assert evaluate_exit(10, {}, _ritmos(**{"10": -5.0})) is None


# ============================================================
# 2. COMO ENCAJA CON EL RESTO DE LA PUNTUACION
# ============================================================


def test_los_sesenta_puntos_son_el_corte_de_VENDER() -> None:
    """
    Una posicion girada llega a VENDER por si sola: es el sentido
    de la regla.
    """

    assert EXIT_SCORE == 60


def test_si_ademas_esta_jugando_solo_se_avisa() -> None:
    """
    UNA PROPIEDAD QUE SALE SOLA, Y ES BUENA.

    `analyze_sales` resta 15 por estar en el once, asi que una
    posicion girada que ADEMAS juega se queda en 45: CONSIDERAR
    VENTA, no VENDER.

    No esta programado como caso especial: sale de sumar las dos
    reglas. Si esta dando puntos, no se malvende por una racha de
    precio.
    """

    fuente = Path(
        "src/analysis/speculative_exit.py"
    ).read_text(encoding="utf-8")

    assert "CONSIDERAR VENTA, no VENDER" in fuente, (
        "se ha perdido la nota que explica por que un titular "
        "girado no se malvende"
    )

    # Y que el -15 del once siga estando donde se supone.
    ventas = Path(
        "src/analysis/sales_analyzer.py"
    ).read_text(encoding="utf-8")

    assert "sale_score -= 15" in ventas, (
        "ha desaparecido el descuento por estar en el once, y con "
        "el la propiedad que protege a los titulares"
    )


def test_el_freno_de_mano_esta_enchufado_a_las_ventas() -> None:
    fuente = Path(
        "src/analysis/sales_analyzer.py"
    ).read_text(encoding="utf-8")

    assert "evaluate_exit" in fuente, (
        "la regla de salida no llega a la puntuacion de ventas: "
        "seria un modulo que no mira nadie"
    )
    assert '"speculative_exit"' in fuente, (
        "la fila no publica de donde salen los 60 puntos"
    )


def test_no_vende_por_su_cuenta() -> None:
    """
    Aqui se PUNTUA, no se ejecuta. Pepe no vende por iniciativa
    propia salvo para generar liquidez, y esa decision es del
    dueño:

        "Vender mal no es como comprar mal. Una compra mala
         cuesta dinero y se corrige; una venta mala te deja SIN
         el jugador."
    """

    import ast

    arbol = ast.parse(
        Path("src/analysis/speculative_exit.py").read_text(
            encoding="utf-8"
        )
    )

    modulos = []

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulos.append(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            modulos.extend(a.name for a in nodo.names)

    for modulo in modulos:
        assert "executor" not in modulo and "biwenger" not in modulo, (
            f"la regla de salida importa {modulo}: ha dejado de "
            f"ser una puntuacion"
        )


# ============================================================
# 3. LA LECCION DE SOLER, SOBRE SU MECANISMO DE VERDAD
# ============================================================


SOLER_PRICE = 5_950_000


def test_soler_sigue_cayendo_por_rendimiento_aislado() -> None:
    """
    El test original sigue verde y sigue valiendo. Se repite aqui
    la comprobacion para dejar constancia de que este cambio no
    lo movio.
    """

    from src.analysis.rival_bid_model import optimal_bid

    plan = optimal_bid(
        price=SOLER_PRICE,
        value=5_965_543,
        model={
            "available": True,
            "rivals": [],
            "auctions_observed": 10,
        },
        intent="SPECULATION",
    )

    assert plan["decision"] != "BID"


def test_y_en_produccion_lo_para_la_CONCENTRACION() -> None:
    """
    LA GUARDIA QUE FALTABA.

    La leccion de Soler es de concentracion: 5,95 M inmovilizaban
    el 81 % del presupuesto. El test original usa el umbral de
    rendimiento solo porque prueba `optimal_bid` aislado, y esa
    funcion no ve el presupuesto.

    Lo que de verdad lo para es el tope por operacion, que se
    aplica en el ejecutor. Sobre la foto local -presupuesto de
    especular 3.064.300 y tope por operacion 1.225.720- una
    operacion de 5,95 M es 4,9 veces el tope.
    """

    ejecutor = Path(
        "src/actions/autopilot_executor.py"
    ).read_text(encoding="utf-8")

    assert "single_operation_limit" in ejecutor, (
        "el ejecutor ha dejado de mirar el tope por operacion: es "
        "lo unico que para una concentracion como la de Soler"
    )
    assert "bid_amount > authorised" in ejecutor, (
        "ha desaparecido la comparacion que rechaza una puja por "
        "encima del tope autorizado"
    )

    # Y la cuenta, con numeros reales de una foto con presupuesto
    # abierto: 5,95 M contra un tope de 1,23 M.
    tope = 1_225_720

    assert SOLER_PRICE > tope * 4, (
        "la operacion de Soler ya no sobrepasa el tope por "
        "operacion: revisar de donde salen estos numeros"
    )


def test_la_compuerta_nueva_no_puede_desbloquear_a_soler() -> None:
    """
    Lo que mas importa comprobar: que el acelerador no abra la
    puerta que la concentracion cierra. La compuerta solo sabe
    decir que NO — nunca sube un valor ni toca un presupuesto.
    """

    from src.analysis.market_rate_gate import evaluate

    # Aunque Soler estuviera subiendo con fuerza y con demanda:
    r = evaluate(1, _ritmos(**{"1": 4.0}))

    assert r["allow"] is True, "el ritmo por si solo si abre la via"

    # ...la compuerta no devuelve ningun valor ni presupuesto.
    assert "value" not in r
    assert "budget" not in r
    assert "single_operation_limit" not in r


TESTS = [
    test_una_posicion_especulativa_girada_se_suelta,
    test_una_posicion_que_sigue_subiendo_no_se_toca,
    test_un_jugador_del_once_no_es_una_posicion_girada,
    test_una_puja_pendiente_no_es_una_posicion,
    test_sin_ritmo_observado_tampoco_se_vende,
    test_sin_libro_de_posiciones_esto_no_hace_nada,
    test_los_sesenta_puntos_son_el_corte_de_VENDER,
    test_si_ademas_esta_jugando_solo_se_avisa,
    test_el_freno_de_mano_esta_enchufado_a_las_ventas,
    test_no_vende_por_su_cuenta,
    test_soler_sigue_cayendo_por_rendimiento_aislado,
    test_y_en_produccion_lo_para_la_CONCENTRACION,
    test_la_compuerta_nueva_no_puede_desbloquear_a_soler,
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
    print(f"FRENO DE MANO V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
