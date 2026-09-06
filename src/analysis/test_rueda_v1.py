"""
LA RUEDA — cuanto puede dar, y que la frena de verdad.

SINTOMA

    Pepe tiene permiso, dinero y maquina para comerciar, y lleva
    semanas sin fichar. Pollo hizo 52 pujas; Pepe, 1.

LO QUE SE SOSPECHABA Y NO ERA

    El embudo del 20/09 decia que 12 de 20 objetivos morian por
    `NO_MEJORA_EL_ONCE`, y de ahi salio la sospecha de que el
    filtro del once estaba matando la rueda.

    **Era un fallo de etiqueta mio.** `SIN_VALOR` no significa
    "no mejora el once": significa "ninguna via lo quiere". El
    motivo que publica el propio objetivo lo dice entero -once,
    especulacion y reventa- y los doce estaban evaluados por
    todas. Once de los doce estaban CAYENDO.

LO QUE SI FRENA LA RUEDA, MEDIDO

    1. El escaparate. De los 20 de hoy, once caen y solo uno
       -420.000 EUR- esta en el tramo 2-4 %. No hay material.
    2. La prioridad del ciclo. Con saldo negativo,
       EMERGENCY_SOLVENCY vale 1100 y SPECULATION_BUY 400: el
       ciclo, que hace una accion por vuelta, nunca llegaria a
       comprar estando en rojo.

    Guardias con fixture. Ni una lectura de `data/` ni de la red.
"""

from __future__ import annotations

from src.analysis.rueda import (
    DIAS_DEL_MES,
    ESCENARIOS,
    capacidad,
    volumen_contra_margen,
)


# ============================================================
# 1. EL TECHO DE LA RUEDA
# ============================================================


def test_la_rueda_da_un_numero_con_su_rango() -> None:
    """
    "Un numero al mes. Si son doscientos mil, es un
     entretenimiento caro; si son tres millones, es la liga."

    Y el rango, no solo el punto medio: el +4,47 % se midio en
    una semana de agosto.
    """

    salida = capacidad(
        capital=2_497_407,
        slots=8,
        cycle_days=3,
        median_return=0.0447,
        loss_rate=0.05,
        resale_premium=0.0176,
        per_operation_cap=973_594,
    )

    assert salida["available"]
    assert salida["cycles_per_month"] == 10.0

    nombres = [e["name"] for e in salida["scenarios"]]

    assert nombres == [n for n, _ in ESCENARIOS]

    optimista = salida["scenarios"][0]
    pesimista = salida["scenarios"][-1]

    assert optimista["per_month"] > pesimista["per_month"], (
        "el rango no separa el escenario bueno del malo"
    )

    # El pesimista es la cuarta parte del rendimiento, no la
    # cuarta parte del resultado: la prima del Computer no se
    # recorta, porque esa si esta medida sobre 106 ventas.
    assert pesimista["per_month"] > 0


def test_se_dice_que_limita_la_rueda() -> None:
    """
    El numero importa menos que saber donde tocar si se quiere
    que gire mas.
    """

    # Poco capital, muchas fichas: manda el capital.
    poco = capacidad(
        capital=500_000, slots=8, cycle_days=3,
        median_return=0.0447, per_operation_cap=973_594,
    )

    assert poco["binding_limit"] == "CAPITAL"

    # Mucho capital, una ficha con tope: mandan las fichas.
    estrecho = capacidad(
        capital=50_000_000, slots=1, cycle_days=3,
        median_return=0.0447, per_operation_cap=973_594,
    )

    assert estrecho["binding_limit"] == "FICHAS_Y_TOPE"
    assert estrecho["deployable"] == 973_594


def test_sin_capital_o_sin_fichas_la_rueda_no_gira() -> None:
    for capital, fichas, ciclo in (
        (0, 8, 3), (2_000_000, 0, 3), (2_000_000, 8, 0),
    ):
        salida = capacidad(
            capital=capital, slots=fichas, cycle_days=ciclo,
            median_return=0.0447,
        )

        assert salida["available"] is False
        assert salida["scenarios"] == []
        assert salida["reason"]


def test_el_mes_son_treinta_dias_y_esta_escrito() -> None:
    assert DIAS_DEL_MES == 30

    salida = capacidad(
        capital=1_000_000, slots=8, cycle_days=3,
        median_return=0.10,
    )

    # 10 ciclos al mes: el resultado mensual es diez veces el del
    # ciclo, sin redondeos raros por el medio.
    ciclo = salida["scenarios"][0]

    assert abs(
        ciclo["per_month"] - ciclo["per_cycle"] * 10
    ) <= 1


# ============================================================
# 2. VOLUMEN CONTRA MARGEN
# ============================================================


def test_gana_el_tramo_donde_cabe_el_capital_no_el_que_mas_rinde() -> None:
    """
    EL HALLAZGO DEL 23/09

        El tramo `> 4 %` rinde un 18,37 % por operacion y el
        `1-2 %` un 3,22 %. Pero hoy el escaparate no ofrece NI UN
        jugador del primero y si dos del segundo.

        Un tramo que rinde el triple y donde no cabe un euro da
        cero. Por eso la comparacion tiene que llevar dentro
        cuanto capital se puede colocar de verdad.
    """

    salida = volumen_contra_margen(
        [
            {
                "name": "1-2 %", "median": 0.0322,
                "loss_rate": 0.074, "n": 68, "share": 1.0,
            },
            {
                "name": "> 4 %", "median": 0.1837,
                "loss_rate": 0.027, "n": 37, "share": 0.0,
            },
        ],
        capital=2_497_407,
        slots=8,
        resale_premium=0.0176,
    )

    assert salida["available"]
    assert salida["winner"] == "1-2 %", (
        "gana el tramo que mas rinde por operacion, ignorando "
        "que no hay donde colocar el dinero"
    )

    por_nombre = {f["name"]: f for f in salida["rows"]}

    assert por_nombre["> 4 %"]["per_month"] == 0
    assert por_nombre["1-2 %"]["per_month"] > 0


def test_la_comparacion_publica_perdidas_y_capital() -> None:
    """
    "Rendimiento mensual, operaciones en perdida, y capital
     inmovilizado de cada estrategia."
    """

    salida = volumen_contra_margen(
        [
            {
                "name": "fino", "median": 0.0322,
                "loss_rate": 0.074, "n": 68, "share": 1.0,
            },
            {
                "name": "grueso", "median": 0.1837,
                "loss_rate": 0.027, "n": 37, "share": 0.17,
            },
        ],
        capital=2_497_407,
        slots=8,
    )

    for fila in salida["rows"]:
        assert fila["loss_rate_percent"] is not None
        assert fila["capital_used"] > 0
        assert fila["n"] > 0


def test_una_estrategia_sin_muestra_no_entra() -> None:
    salida = volumen_contra_margen(
        [
            {"name": "sin datos", "median": 0.5, "n": 0},
            {
                "name": "medida", "median": 0.03,
                "loss_rate": 0.07, "n": 68, "share": 1.0,
            },
        ],
        capital=1_000_000,
        slots=8,
    )

    assert [f["name"] for f in salida["rows"]] == ["medida"]


def test_sin_estrategias_no_se_compara_nada() -> None:
    for estrategias, capital in (
        (None, 1_000_000), ([], 1_000_000), ([{"n": 1}], 0),
    ):
        salida = volumen_contra_margen(
            estrategias, capital=capital, slots=8
        )

        assert salida["available"] is False
        assert salida["reason"]


# ============================================================
# 3. LO QUE FRENA LA RUEDA, POR SU NOMBRE
# ============================================================


def test_el_saldo_en_rojo_deja_la_caja_en_cero() -> None:
    """
    EL PRIMER FRENO, MEDIDO EN EL CODIGO

        `cash_budget = max(balance, 0) * ACQUISITION_CASH_PERCENT`

        En rojo, la mitad de caja del presupuesto es CERO. Lo
        unico que queda es la deuda segura, y esa depende de que
        SOLVENCY_GUARANTEE aguante.

    No se toca: se señala, como pidio el encargo.
    """

    from pathlib import Path

    fuente = Path(
        "src/analysis/acquisition_budget.py"
    ).read_text(encoding="utf-8")

    assert "max(balance, 0)" in fuente, (
        "la caja ya no se recorta a cero con saldo negativo: si "
        "eso ha cambiado, la cuenta del encargo del 23/09 ya no "
        "vale"
    )


def test_la_solvencia_gana_a_comprar_por_setecientos_puntos() -> None:
    """
    EL SEGUNDO FRENO, Y ES EL QUE HACE INUTIL EL PERMISO

        El ciclo ejecuta UNA accion por vuelta. Con saldo
        negativo:

            EMERGENCY_SOLVENCY   1100
            SPECULATION_BUY       400

        Setecientos puntos de diferencia. Estando en rojo, el
        ciclo se dedicaria a recuperar solvencia y nunca llegaria
        a comprar — que es justo lo contrario de "se puede ir en
        rojo de lunes a jueves".

    Esta guardia NO exige que se arregle. Exige que si alguien lo
    arregla, sea a proposito.
    """

    from src.analysis.decision_orchestrator import PRIORITY

    assert PRIORITY["EMERGENCY_SOLVENCY"] == 1100
    assert PRIORITY["SPECULATION_BUY"] == 400

    assert (
        PRIORITY["EMERGENCY_SOLVENCY"]
        > PRIORITY["SPECULATION_BUY"]
    ), (
        "comprar ha pasado por delante de recuperar solvencia: "
        "eso es un cambio grande y tiene que ser deliberado"
    )


def test_la_ventana_de_deuda_no_mira_el_calendario() -> None:
    """
    `debt_window_open = guaranteed and headroom > 0`.

    No hay puerta de lunes a jueves: la puerta es "puedo
    recuperar antes del plazo". Conviene saberlo antes de buscar
    un calendario que no existe.
    """

    from pathlib import Path

    fuente = Path(
        "src/analysis/solvency_engine.py"
    ).read_text(encoding="utf-8")

    assert "debt_window_open = bool(" in fuente
    assert "additional_debt_headroom > 0" in fuente


# ============================================================
# 4. NI DECIDE NI CAMBIA DE FORMA
# ============================================================


def test_la_rueda_no_compra_ni_vende() -> None:
    import ast

    from pathlib import Path

    arbol = ast.parse(
        Path("src/analysis/rueda.py").read_text(encoding="utf-8")
    )

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, (ast.Import, ast.ImportFrom)):
            continue

        for prohibido in (
            "write_client",
            "BiwengerWriteClient",
            "autopilot_executor",
        ):
            assert prohibido not in ast.dump(nodo), (
                f"rueda.py importa `{prohibido}`"
            )


def test_no_mueve_ningun_liston() -> None:
    """
    "No muevas el 3 %." Se publica el resultado y decide el
    dueño.
    """

    from pathlib import Path

    fuente = Path(
        "src/analysis/rueda.py"
    ).read_text(encoding="utf-8")

    for prohibido in (
        "MIN_SPECULATION_YIELD",
        "MAX_SINGLE",
        "MIN_TENER_YIELD",
    ):
        assert prohibido not in fuente, (
            f"rueda.py toca `{prohibido}`: solo tenia que medir"
        )


def test_la_forma_no_cambia_con_los_datos() -> None:
    lleno = capacidad(
        capital=2_000_000, slots=8, cycle_days=3,
        median_return=0.0447,
    )
    vacio = capacidad(
        capital=0, slots=0, cycle_days=0, median_return=0.0,
    )

    assert set(lleno) - set(vacio) == set(), (
        f"capacidad cambia de forma: faltan "
        f"{sorted(set(lleno) - set(vacio))}"
    )

    lleno = volumen_contra_margen(
        [{"name": "x", "median": 0.03, "n": 10, "share": 1.0}],
        capital=1_000_000, slots=8,
    )
    vacio = volumen_contra_margen(None, capital=0, slots=0)

    assert set(lleno) - set(vacio) == set()


def test_nada_de_esto_lanza() -> None:
    for basura in (None, "x", [], {}):
        assert isinstance(
            capacidad(basura, basura, basura, basura), dict
        )
        assert isinstance(
            volumen_contra_margen(basura, basura, basura), dict
        )


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    for modulo in (
        "src.analysis.test_rueda_v1",
        "src.analysis.rueda",
    ):
        assert not lecturas_de_estado(modulo), (
            f"{modulo} lee estado mutable"
        )


TESTS = [
    test_la_rueda_da_un_numero_con_su_rango,
    test_se_dice_que_limita_la_rueda,
    test_sin_capital_o_sin_fichas_la_rueda_no_gira,
    test_el_mes_son_treinta_dias_y_esta_escrito,
    test_gana_el_tramo_donde_cabe_el_capital_no_el_que_mas_rinde,
    test_la_comparacion_publica_perdidas_y_capital,
    test_una_estrategia_sin_muestra_no_entra,
    test_sin_estrategias_no_se_compara_nada,
    test_el_saldo_en_rojo_deja_la_caja_en_cero,
    test_la_solvencia_gana_a_comprar_por_setecientos_puntos,
    test_la_ventana_de_deuda_no_mira_el_calendario,
    test_la_rueda_no_compra_ni_vende,
    test_no_mueve_ningun_liston,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA RUEDA V1")
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
