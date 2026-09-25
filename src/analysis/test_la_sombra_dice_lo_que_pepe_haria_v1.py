"""
La lista de la noche dice lo que Pepe HARIA, no una imitacion.

QUE VIGILA (25/09/2026)

    El 25/09 la lista decia "Lejeune, pujaria 3.674.989" y la
    decision real era SUPERA_PRESUPUESTO: la sombra reconstruia la
    decision por su cuenta y mezclaba el bolsillo de una via con el
    valor de otra. Un aviso que miente es peor que no tener aviso.

        1. Lo que la decision real descarta por presupuesto NO sale
           como puja. MUERDE SI EL CASO NO TRAE NINGUNO: se fabrica
           con `optimal_bid` de verdad y se exige que diga
           SUPERA_PRESUPUESTO antes de mirar la lista.
        1b. Lo que ya tiene puja nuestra viva no es una puja nueva:
           `decision_orchestrator` lo aparta, y la sombra tambien.
        2. El caso del 25/09: con Lejeune y Antonio Blanco fuera
           por presupuesto, la ventana sin cesta y el carril sin a
           quien, la lista dice "no pujaria por nadie".
        3. La ventana del reset ES `plan_del_reset`: la sombra no le
           añade ni le quita nada, solo le pone la hora.
        4. La lista no hace ninguna cuenta de puja: ni valora, ni
           elige via, ni busca bolsillo.
        5. Dice lo que no cubre, en vez de callarlo.
        6. Ni disco, ni red, ni reloj.

NO MIRA EL MUNDO

    Las fichas son de mentira y estan aqui escritas. No toca
    `os.environ`: la comparacion con `plan_del_reset` se hace con el
    entorno que haya, el mismo para los dos lados.
"""

from __future__ import annotations

import ast
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.la_lista_de_la_noche import (               # noqa: E402
    BUY_V10,
    CARRIL,
    TABLERO,
    VENTANA,
    en_la_ventana,
    la_lista,
)
from src.analysis.rival_bid_model import optimal_bid          # noqa: E402


EL_MODULO = RAIZ / "src" / "analysis" / "la_lista_de_la_noche.py"


def _fila(nombre, decision, precio, puja=0, **extra) -> dict:
    base = {
        "id": abs(hash(nombre)) % 100000,
        "name": nombre,
        "market_price": precio,
        "decision": decision,
        "bid": puja,
        "intent": "XI_UPGRADE",
        "deployment": {"route": "XI_UPGRADE"},
        "budget_applied": 2_208_580,
        "seller_id": None,
    }
    base.update(extra)
    return base


def _fuera_por_presupuesto(nombre, precio, valor, bolsillo) -> dict:
    """Una fila con la decision que da `optimal_bid` de verdad."""

    plan = optimal_bid(
        price=precio,
        value=valor,
        model={},
        available_budget=bolsillo,
        intent="XI_UPGRADE",
        route="XI_UPGRADE",
    )

    return _fila(
        nombre, plan.get("decision"), precio,
        puja=int(plan.get("bid") or 0),
        budget_applied=bolsillo,
        reason=plan.get("reason"),
    )


VENTANA_SIN_CESTA = {
    "available": True,
    "bids": [],
    "blocked_by": "SIN_CESTA",
    "reason": "Ninguna puja: 4 candidato(s) y ninguno pasa.",
}

CARRIL_SIN_NADIE = {
    "ultima_vuelta": "2026-09-25T17:12:10+00:00",
    "ultima_decision": "El carril podia pujar y no hay a quien.",
}


# ============================================================
# 1. LA QUE PIDIO EL ENCARGO
# ============================================================


def test_la_sombra_dice_lo_que_pepe_haria() -> None:

    fuera = _fuera_por_presupuesto(
        "Caro", precio=3_560_000, valor=3_922_963, bolsillo=2_208_580
    )

    assert fuera["decision"] == "SUPERA_PRESUPUESTO", (
        f"el caso no trae ningun candidato descartado por presupuesto "
        f"(salio {fuera['decision']}): esta guardia no mediria nada"
    )

    pujable = _fila("Barato", "BID", 1_000_000, puja=1_050_000)

    lista = la_lista(
        {"targets": [fuera, pujable]}, VENTANA_SIN_CESTA, CARRIL_SIN_NADIE
    )

    nombres = [f["jugador"] for f in lista["filas"]]

    assert "Caro" not in nombres, (
        "la sombra ofrece como puja a uno que la decision real "
        "descarta por presupuesto"
    )
    assert nombres == ["Barato"]
    assert lista["filas"][0]["lo_que_pujaria"] == 1_050_000
    assert lista["filas"][0]["camino"] == TABLERO


def test_la_que_ya_tiene_puja_viva_no_se_repite() -> None:
    """
    El 18/09 el tablero dejaba a Maffeo en BID con 1.664.350 nuestros
    ya vivos, y `decision_orchestrator` lo aparta por
    `players_with_live_bid`. La sombra hace lo mismo: no lo ofrece
    como puja nueva, y lo enseña como lo que es.

    MUERDE SI EL CASO NO TRAE NINGUNO EN BID CON PUJA VIVA.
    """

    maffeo = _fila(
        "Maffeo", "BID", 1_660_000, puja=1_758_779,
        has_live_bid=True, live_bid=1_664_350,
    )

    assert maffeo["decision"] == "BID" and maffeo["has_live_bid"], (
        "el caso no trae ningun BID con puja viva: no probaria nada"
    )

    lista = la_lista(
        {"targets": [maffeo, _fila("Cabrera", "BID", 3_040_000, puja=3_134_660)]},
        VENTANA_SIN_CESTA,
        CARRIL_SIN_NADIE,
    )

    assert [f["jugador"] for f in lista["filas"]] == ["Cabrera"]
    assert lista["caminos"][TABLERO]["ya_vivas"] == [
        {"jugador": "Maffeo", "precio_de_mercado": 1_660_000, "puja_viva": 1_664_350}
    ]


# ============================================================
# 2. EL CASO DEL 25/09
# ============================================================


def test_el_25_09_no_puja_por_nadie() -> None:

    lejeune = _fuera_por_presupuesto(
        "Lejeune", precio=3_560_000, valor=3_922_963, bolsillo=2_208_580
    )
    blanco = _fuera_por_presupuesto(
        "Antonio Blanco", precio=3_230_000, valor=3_761_633,
        bolsillo=2_208_580,
    )

    assert {lejeune["decision"], blanco["decision"]} == {"SUPERA_PRESUPUESTO"}

    lista = la_lista(
        {"targets": [lejeune, blanco, _fila("Otro", "NO_COMPENSA", 3_440_000)]},
        VENTANA_SIN_CESTA,
        CARRIL_SIN_NADIE,
    )

    assert lista["available"]
    assert lista["n"] == 0
    assert lista["filas"] == []
    assert lista["reason"].startswith("Esta noche no pujaria por nadie."), (
        f"la lista del 25/09 dice: {lista['reason']}"
    )


# ============================================================
# 3. LA VENTANA ES `plan_del_reset`, CON LA HORA PUESTA
# ============================================================


def _lectura() -> dict:
    return {
        "candidatos": [
            {
                "id": 1,
                "name": "Uno",
                "market_price": 1_000_000,
                "team_id": 1,
                "seller_id": None,
                "rate_percent_per_day": 1.0,
                "starter_probability": 80.0,
                "hierarchy_value": 50,
                "availability": "DISPONIBLE",
                "intent": "SPECULATION",
                "route": "COMPUTER_RESALE",
                "expected_points": 100,
            },
        ],
        "prima_de_reventa": 0.02,
        "presupuesto": 5_000_000,
        "fichas_libres": 3,
        "caja_libre": 10_000_000,
        "seconds_to_reset": 40_000,
        "solvency_clock": {"state": "SIN_DEUDA", "deficit": 0},
        "plantilla": [],
        "bloqueo_temporal": None,
        "max_por_club": 3,
    }


def test_la_ventana_es_plan_del_reset_con_la_hora_puesta() -> None:
    """
    La sombra no añade ni quita nada a `plan_del_reset`: solo le
    dice que esta dentro de la ventana. Se compara la respuesta
    ENTERA, motivo incluido, con el mismo entorno a los dos lados.
    """

    from src.analysis.la_subasta import (
        MAX_PUJAS_PRIMER_DIA,
        VENTANA_MINUTOS,
        plan_del_reset,
    )

    lectura = _lectura()

    assert lectura["seconds_to_reset"] > VENTANA_MINUTOS * 60, (
        "el caso ya esta dentro de la ventana: no probaria que la "
        "sombra le pone la hora"
    )

    sombra = en_la_ventana(lectura)

    directa = plan_del_reset(
        **{**lectura, "seconds_to_reset": VENTANA_MINUTOS * 60 // 2},
        ya_pujados=None,
        en_vivo=False,
        max_pujas=MAX_PUJAS_PRIMER_DIA,
    )

    assert sombra["available"] is True
    assert sombra == directa

    # Y no se ha tocado lo que recibio.
    assert lectura["seconds_to_reset"] == 40_000


def test_una_ventana_con_candado_no_da_pujas() -> None:
    """Si la ventana esta cerrada por algo que no es la hora, no hay puja."""

    lista = la_lista(
        {"targets": []},
        {
            "available": True,
            "bids": [{"id": 1, "name": "Uno", "market_price": 1, "bid": 2}],
            "blocked_by": "SOLVENCIA",
            "reason": "El reloj de solvencia manda.",
        },
        CARRIL_SIN_NADIE,
    )

    assert lista["n"] == 0
    assert lista["caminos"][VENTANA]["blocked_by"] == "SOLVENCIA"

    # Y `SIN_LIVE` no es un candado: es la propia sombra.
    lista = la_lista(
        {"targets": []},
        {
            "available": True,
            "bids": [{"id": 1, "name": "Uno", "market_price": 150_000, "bid": 150_376}],
            "blocked_by": "SIN_LIVE",
            "reason": "1 puja. NO se ejecuta: falta el modo en vivo.",
        },
        CARRIL_SIN_NADIE,
    )

    assert lista["n"] == 1
    assert lista["filas"][0]["camino"] == VENTANA
    assert lista["caminos"][VENTANA]["blocked_by"] is None


# ============================================================
# 4. NI UNA CUENTA DE PUJA PROPIA
# ============================================================


def _nombres_del_codigo() -> set:
    arbol = ast.parse(EL_MODULO.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name):
            nombres.add(nodo.id)
        elif isinstance(nodo, ast.Attribute):
            nombres.add(nodo.attr)
        elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
            if isinstance(nodo, ast.ImportFrom):
                nombres.add(str(nodo.module or ""))
            for alias in nodo.names:
                nombres.add(alias.name)
    return nombres


def test_la_sombra_no_reconstruye_la_decision() -> None:
    """
    Se mira el CODIGO, no la prosa: la cabecera cuenta la historia
    y nombra cosas a proposito.
    """

    RECONSTRUIR = {
        "optimal_bid",
        "value_candidate",
        "xi_upgrade_value",
        "budget_for_intent",
        "classify_operation",
        "MONEDA_DE_LA_LIGA",
        "tarifa_del_punto",
    }

    culpables = sorted(RECONSTRUIR & _nombres_del_codigo())

    assert not culpables, (
        f"la lista de la noche vuelve a hacer cuentas por su cuenta: "
        f"{culpables}"
    )


# ============================================================
# 5. LO QUE NO CUBRE, DICHO
# ============================================================


def test_dice_lo_que_no_cubre() -> None:

    lista = la_lista({"targets": []}, VENTANA_SIN_CESTA, CARRIL_SIN_NADIE)

    assert set(lista["no_cubierto"]) == {CARRIL, BUY_V10}
    assert lista["caminos"][CARRIL]["cubierto"] is False
    assert lista["caminos"][BUY_V10]["cubierto"] is False
    assert lista["caminos"][CARRIL]["ultima_decision"] == (
        CARRIL_SIN_NADIE["ultima_decision"]
    )
    assert "no se pueden preguntar en seco" in lista["reason"]


# ============================================================
# 6. NI DISCO, NI RED, NI RELOJ
# ============================================================


def test_la_sombra_no_toca_ni_disco_ni_red() -> None:

    PROHIBIDO = {
        "open",
        "requests",
        "urlopen",
        "socket",
        "now",
        "utcnow",
        "time",
        "write_text",
        "write_bytes",
        "BiwengerWriteClient",
        "place_bid",
        "execute_bid",
        "correr",
    }

    culpables = sorted(PROHIBIDO & _nombres_del_codigo())

    assert not culpables, (
        f"la lista de la noche toca lo que no debe: {culpables}"
    )


TESTS = [
    test_la_sombra_dice_lo_que_pepe_haria,
    test_la_que_ya_tiene_puja_viva_no_se_repite,
    test_el_25_09_no_puja_por_nadie,
    test_la_ventana_es_plan_del_reset_con_la_hora_puesta,
    test_una_ventana_con_candado_no_da_pujas,
    test_la_sombra_no_reconstruye_la_decision,
    test_dice_lo_que_no_cubre,
    test_la_sombra_no_toca_ni_disco_ni_red,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA SOMBRA DICE LO QUE PEPE HARIA V1")
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
