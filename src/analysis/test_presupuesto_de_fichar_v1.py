"""
El dinero de fichar no es el dinero de especular.

EL CASO (21/08/2026)

    "Tengo 1.5M en la cuenta ahora mismo. Que significa eso de
     que supera_presupuesto?"

    Agoumé costaba 2.580.000 EUR. Biwenger dejaba pujar hasta
    13.050.000. El tablero contestaba:

        SUPERA_PRESUPUESTO
        "Cuesta 2.580.000 EUR y solo quedan 1.497.444 sin
         comprometer."

    Ese 1.497.444 no salia de la cuenta ni de Biwenger. Salia de
    aplicar a un fichaje los porcentajes de una apuesta:

        15 % de la caja + 60 % del margen de deuda

    Pepe se limitaba a la novena parte de lo que el juego le
    dejaba gastar, y encima creia estar siendo prudente.

LAS CINCO PAREDES

    Esta fue la quinta regla seguida que, sola, hacia imposible
    mejorar el once:

        1. El titular que sale contaba cero.       (21/08)
        2. Hacia falta un 25 % de margen.
        3. El presupuesto era el de especular.     (esto)
        4. La revalidacion de escritura tambien.   (esto)
        5. La puerta del ciclo pedia permiso para
           apostar antes de dejar fichar.          (esto)

    Cada una parecia prudente por separado.

LO QUE SE PROTEGE AQUI

    1. Que fichar no vuelva a pasar por el porcentaje de apostar.
    2. Que las puertas de solvencia sigan TODAS en su sitio: lo
       que cambia es la cantidad, no las condiciones.
    3. Que el techo de Biwenger siga siendo la ultima palabra.
    4. Que lo ya comprometido se siga descontando, y una sola vez.
    5. Que la eleccion de bolsillo viva en un solo sitio, para que
       el dashboard y el ciclo no puedan contestar distinto.
    6. Que la revalidacion de escritura mire el mismo bolsillo con
       el que se decidio.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.acquisition_budget import (
    ACQUISITION_CASH_PERCENT,
    ACQUISITION_DEBT_PERCENT,
    budget_for_intent,
    calculate_acquisition_budget,
)

from src.analysis.speculation_engine import (
    MAX_DEBT_SPECULATION_PERCENT,
    MAX_SPECULATION_BUDGET_PERCENT,
    calculate_speculation_budget,
)


# El caso real del 21/08/2026.
CAJA = 1_500_000
TECHO_BIWENGER = 13_050_000
MARGEN_DEUDA = 2_250_000

PRECIO_AGOUME = 2_580_000


def snapshot(balance=CAJA, maximum_bid=TECHO_BIWENGER):
    return {
        "market": {
            "status": {
                "balance": balance,
                "maximumBid": maximum_bid,
            }
        }
    }


def solvencia(headroom=MARGEN_DEUDA, **cambios):
    base = {
        "hard_safety": {"active": False},
        "solvency_guarantee": {"guaranteed": True},
        "max_safe_debt": {
            "additional_debt_headroom": headroom,
            "debt_window_open": True,
        },
        "temporary_debt": {"allowed": True},
    }

    base.update(cambios)

    return base


def fichar(**kwargs):
    return calculate_acquisition_budget(
        snapshot=kwargs.pop("snapshot", None) or snapshot(),
        solvency=kwargs.pop("solvency", None) or solvencia(),
        **kwargs,
    )


# ============================================================
# PRUEBAS
# ============================================================


def test_fichar_no_es_apostar():
    """
    LA REGRESION QUE PARALIZO A PEPE.

    Si los porcentajes de fichar vuelven a ser los de especular,
    todo lo demas de este fichero da igual.
    """

    assert ACQUISITION_CASH_PERCENT > MAX_SPECULATION_BUDGET_PERCENT, (
        "el presupuesto de fichar ha vuelto a ser el de apostar: "
        "Pepe no podra pagar un titular"
    )

    assert ACQUISITION_DEBT_PERCENT > MAX_DEBT_SPECULATION_PERCENT


def test_el_caso_agoume():
    """
    El numero de la pantalla, entero.

    Con 1,5 M de caja y 2,25 M de margen de deuda seguro:

        especular ..  1.575.000   ->  NO llega a Agoumé
        fichar ..... 3.750.000   ->  si llega
    """

    especulacion = calculate_speculation_budget(
        snapshot=snapshot(),
        solvency=solvencia(),
        active_franchise_bid=None,
    )

    fichajes = fichar()

    assert especulacion["total_budget"] < PRECIO_AGOUME, (
        "el caso ha dejado de reproducirse: con el presupuesto de "
        "especulacion ya se llegaba a Agoumé"
    )

    assert fichajes["total_budget"] >= PRECIO_AGOUME, (
        f"con {CAJA:,} de caja y {MARGEN_DEUDA:,} de margen "
        f"seguro sigue sin poder pagar {PRECIO_AGOUME:,}"
    )

    assert fichajes["cash_budget"] == CAJA
    assert fichajes["debt_budget"] == MARGEN_DEUDA


def test_el_techo_de_biwenger_es_la_ultima_palabra():
    """
    La unica pared que no es nuestra. Ni el margen de deuda ni el
    dinero que se recupera vendiendo pueden saltarsela.
    """

    presupuesto = fichar(
        snapshot=snapshot(maximum_bid=900_000),
    )

    assert presupuesto["total_budget"] == 900_000
    assert presupuesto["capped_by_biwenger"] is True


def test_el_ochenta_por_ciento_del_saliente_no_se_suma_aparte():
    """
    Lo que se recupera al vender al titular que sale ya esta
    dentro de `maximumBid`: por eso es tan grande comparado con el
    saldo. Sumarlo otra vez seria contarlo dos veces.

    La comprobacion es estructural: el presupuesto no puede
    depender de la valoracion de candidatos.
    """

    fuente = (
        Path(__file__).parent / "acquisition_budget.py"
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
            assert "acquisition_valuation" not in nombre, (
                "el presupuesto ha empezado a mirar lo que se "
                "recupera del saliente: eso ya esta en maximumBid"
            )

    assert "RECUPERACION_TITULAR" not in fuente


# ------------------------------------------------------------
# LAS PUERTAS DE SOLVENCIA SIGUEN TODAS
# ------------------------------------------------------------


def test_hard_safety_sigue_bloqueando():
    presupuesto = fichar(
        solvency=solvencia(hard_safety={"active": True}),
    )

    assert presupuesto["enabled"] is False
    assert presupuesto["blocked_by"] == "HARD_SAFETY"
    assert presupuesto["total_budget"] == 0


def test_una_puja_franchise_viva_sigue_congelandolo_todo():
    presupuesto = fichar(
        active_franchise_bid={"player": {"name": "El caro"}},
    )

    assert presupuesto["enabled"] is False
    assert presupuesto["blocked_by"] == "FRANCHISE_ACTIVE_BID"


def test_la_deuda_exige_exactamente_lo_mismo_que_antes():
    """
    Se ha cambiado el PORCENTAJE, no las condiciones. Si alguna de
    las cuatro se cae, la deuda no se usa: solo queda la caja.
    """

    casos = [
        ("solvency_guarantee", {"guaranteed": False}),
        (
            "max_safe_debt",
            {
                "additional_debt_headroom": MARGEN_DEUDA,
                "debt_window_open": False,
            },
        ),
        ("temporary_debt", {"allowed": False}),
    ]

    for clave, valor in casos:

        presupuesto = fichar(
            solvency=solvencia(**{clave: valor}),
        )

        assert presupuesto["debt_budget"] == 0, (
            f"con {clave} cerrado se sigue contando deuda"
        )

        assert presupuesto["cash_budget"] == CAJA, (
            "la caja no depende de la ventana de deuda"
        )

        assert presupuesto["debt_unavailable_reason"], (
            "se ha quitado la deuda sin decir por que"
        )

    # Y sin margen no hay deuda aunque todo lo demas este abierto.
    assert fichar(solvency=solvencia(headroom=0))["debt_budget"] == 0


def test_sin_caja_y_sin_deuda_no_se_ficha():
    presupuesto = fichar(
        snapshot=snapshot(balance=0, maximum_bid=0),
        solvency=solvencia(headroom=0),
    )

    assert presupuesto["enabled"] is False
    assert presupuesto["total_budget"] == 0


def test_no_hay_minimo_para_fichar():
    """
    MIN_SPECULATION_BUDGET = 150.000 evita micro-apuestas. Pero
    Copete costaba 150.000 y sumaba 32 puntos: un fichaje pequeño
    no es una operacion irrelevante.
    """

    presupuesto = fichar(
        snapshot=snapshot(balance=160_000, maximum_bid=160_000),
        solvency=solvencia(headroom=0),
    )

    assert presupuesto["enabled"] is True
    assert presupuesto["total_budget"] == 160_000


# ------------------------------------------------------------
# LO COMPROMETIDO
# ------------------------------------------------------------


def test_lo_ya_pujado_se_descuenta_una_sola_vez():
    """
    `maximumBid` YA viene con las pujas vivas descontadas -medido
    el 16/08-. Restarlas otra vez sobre el neto las contaria dos
    veces, y esa cuenta no se reescribe aqui: se llama a la que
    ya existe.
    """

    presupuesto = fichar(
        exposure={
            "available": True,
            "committed_total": 500_000,
            "operation_count": 1,
        },
    )

    # bruto 3.750.000 - 500.000 = 3.250.000, por debajo del techo.
    assert presupuesto["available_budget"] == 3_250_000
    assert presupuesto["committed_total"] == 500_000
    assert presupuesto["exposure_applied"] is True

    fuente = (
        Path(__file__).parent / "acquisition_budget.py"
    ).read_text(encoding="utf-8")

    assert "apply_exposure_to_budget" in fuente, (
        "el presupuesto de fichajes se ha hecho su propia copia "
        "de la resta de pujas vivas"
    )


def test_sin_contador_no_se_inventa_disponible():
    presupuesto = fichar()

    assert presupuesto["available_budget"] == (
        presupuesto["total_budget"]
    )
    assert presupuesto["exposure_applied"] is False


# ------------------------------------------------------------
# QUE BOLSILLO SE APLICA A CADA FILA
# ------------------------------------------------------------


def test_cada_via_usa_su_bolsillo():

    assert budget_for_intent(
        "XI_UPGRADE", 1_497_444, 3_750_000
    ) == 3_750_000

    assert budget_for_intent(
        "SPECULATION", 1_497_444, 3_750_000
    ) == 1_497_444


def test_sin_saber_por_que_via_se_aplica_el_mas_estrecho():
    """
    Ausencia de dato != permiso. No saber para que lo queremos no
    es motivo para gastar mas.
    """

    assert budget_for_intent(
        None, 1_497_444, 3_750_000
    ) == 1_497_444


def test_sin_presupuesto_de_fichajes_todo_sigue_como_ayer():
    """
    El respaldo. Si el presupuesto nuevo no llega, se usa el
    viejo: peor, pero nunca sin techo.
    """

    assert budget_for_intent(
        "XI_UPGRADE", 1_497_444, None
    ) == 1_497_444


def test_la_eleccion_de_bolsillo_vive_en_un_solo_sitio():
    """
    El 16/08 el dashboard proponia cuatro pujas y en Biwenger
    habia una, distinta. Dos motores. Si cada uno elige por su
    cuenta con que dinero decide, vuelve a pasar.
    """

    fuente = (
        Path(__file__).parent / "acquisition_board.py"
    ).read_text(encoding="utf-8")

    assert "budget_for_intent" in fuente, (
        "el tablero ha vuelto a elegir el presupuesto por su "
        "cuenta"
    )


# ------------------------------------------------------------
# LA RUTA QUE ESCRIBE
# ------------------------------------------------------------


def test_la_revalidacion_de_escritura_mira_el_mismo_bolsillo():
    """
    Una puja decidida con el presupuesto de fichajes que se
    revalida contra el de especulacion se cae sola, y encima con
    un motivo que no explica nada: SPECULATION_BUDGET_CHANGED.
    """

    fuente = (
        Path(__file__).parents[1]
        / "actions"
        / "autopilot_executor.py"
    ).read_text(encoding="utf-8")

    assert "acquisition_budget" in fuente, (
        "la ruta que escribe en Biwenger sigue revalidando solo "
        "contra el presupuesto de especulacion"
    )

    assert "presupuesto_via" in fuente


def test_el_ciclo_puede_fichar_sin_permiso_para_apostar():
    """
    LA QUINTA PARED.

    La puerta del ciclo era `budget["enabled"] and
    executable_buys`: las dos cosas de especular. Con la caja baja
    el presupuesto de apuestas se apaga entero y el tablero de
    fichajes no llegaba ni a mirarse.
    """

    fuente = (
        Path(__file__).parent / "decision_orchestrator.py"
    ).read_text(encoding="utf-8")

    assert "hay_objetivo_de_fichaje" in fuente, (
        "el ciclo vuelve a exigir presupuesto de especulacion "
        "para dejar fichar"
    )

    # Y el respaldo antiguo no puede reventar con la lista vacia,
    # que a partir de ahora es un caso normal: se entra a comprar
    # sin que el scoring viejo haya propuesto nada.
    arbol = ast.parse(fuente)

    # Solo la funcion donde vive la puerta nueva. Otras funciones
    # comprueban la lista con un `return` temprano y ahi el
    # subindice si es seguro.
    puerta = None

    for nodo in ast.walk(arbol):

        if not isinstance(
            nodo, (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        if "hay_objetivo_de_fichaje" in ast.dump(nodo):
            puerta = nodo
            break

    assert puerta is not None, (
        "no se encuentra la puerta de compra del ciclo"
    )

    arbol = puerta

    protegidos = set()

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.IfExp):
            continue

        if not (
            isinstance(nodo.test, ast.Name)
            and nodo.test.id == "executable_buys"
        ):
            continue

        for hijo in ast.walk(nodo.body):
            protegidos.add(id(hijo))

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Subscript):
            continue

        if not isinstance(nodo.value, ast.Name):
            continue

        if nodo.value.id != "executable_buys":
            continue

        assert id(nodo) in protegidos, (
            "executable_buys[0] sin guardia: ahora se puede "
            "llegar a comprar sin lista antigua, y con la lista "
            "vacia el ciclo entero revienta"
        )


def main():

    pruebas = [
        test_fichar_no_es_apostar,
        test_el_caso_agoume,
        test_el_techo_de_biwenger_es_la_ultima_palabra,
        test_el_ochenta_por_ciento_del_saliente_no_se_suma_aparte,
        test_hard_safety_sigue_bloqueando,
        test_una_puja_franchise_viva_sigue_congelandolo_todo,
        test_la_deuda_exige_exactamente_lo_mismo_que_antes,
        test_sin_caja_y_sin_deuda_no_se_ficha,
        test_no_hay_minimo_para_fichar,
        test_lo_ya_pujado_se_descuenta_una_sola_vez,
        test_sin_contador_no_se_inventa_disponible,
        test_cada_via_usa_su_bolsillo,
        test_sin_saber_por_que_via_se_aplica_el_mas_estrecho,
        test_sin_presupuesto_de_fichajes_todo_sigue_como_ayer,
        test_la_eleccion_de_bolsillo_vive_en_un_solo_sitio,
        test_la_revalidacion_de_escritura_mira_el_mismo_bolsillo,
        test_el_ciclo_puede_fichar_sin_permiso_para_apostar,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Presupuesto de fichar: todo en verde.")


if __name__ == "__main__":
    main()
