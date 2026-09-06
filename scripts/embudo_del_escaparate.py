"""
El escaparate por causa de muerte, y que pasaria sin el tope.

LA PREGUNTA (27/09/2026)

    "Cuantos pasan ya el liston de rendimiento, y de esos
     cuantos mueren por el tope por operacion? El tope llevaba
     semanas bloqueando cero porque nadie llegaba hasta el. Si
     ahora bloquea al primero bueno, es otra conversacion."

POR QUE NO BASTA CON CONTAR DECISIONES

    Las puertas de `optimal_bid` se cruzan EN ORDEN:

        1. NO_COMPENSA            valor <= precio
        2. SUPERA_PRESUPUESTO     min(valor, bolsillo) <= precio
        3. ...busqueda de puja...
        4. RENDIMIENTO_INSUFICIENTE   rinde menos del 3 %

    El tope se mira ANTES que el rendimiento. Asi que un
    `SUPERA_PRESUPUESTO` no significa "pasaba el liston y el
    dinero lo mato": significa "no llegamos a preguntarselo".

    Contar los SUPERA_PRESUPUESTO como "bloqueados por el tope"
    seria exactamente la familia de fallos de este proyecto: un
    dato correcto contestando una pregunta que no era la suya.

COMO SE CONTESTA DE VERDAD

    Corriendo `optimal_bid` DOS veces por jugador -la misma
    funcion de produccion, no una copia-:

        con el bolsillo real     -> lo que Pepe decide hoy
        con el bolsillo infinito -> lo que decidiria si el
                                    dinero no fuese el limite

    La diferencia entre las dos es, exactamente, lo que cuesta
    el tope. Y quien muere en las dos, moriria igual.

DE DONDE SALEN LOS DATOS

    De `diagnostico/status.json`, que es lo que produccion
    publica de si misma: precio, valor, intencion y el modelo de
    puja calibrado. Ni una llamada a Biwenger.

NO ENCIENDE NADA

    Calcula y publica. No compra, no vende y no mueve ningun
    liston.

COMO SE USA

    python -m scripts.embudo_del_escaparate
"""

from __future__ import annotations

import json

from pathlib import Path

from src.analysis.rival_bid_model import (
    MIN_SPECULATION_YIELD,
    optimal_bid,
)


ESTADO = (
    Path(__file__).parent.parent / "diagnostico" / "status.json"
)


# El orden en que se cruzan las puertas, para poder contar el
# embudo como un embudo y no como una lista de motivos.
PUERTAS = (
    ("NO_DISPONIBLE", "lesionado o en duda"),
    ("SIN_VALOR", "no vale por ninguna via"),
    ("NO_COMPENSA", "cuesta mas de lo que vale para nosotros"),
    ("SUPERA_PRESUPUESTO", "no cabe en el bolsillo"),
    ("RENDIMIENTO_INSUFICIENTE", "rinde menos del liston"),
    ("BID", "se puja"),
)


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def margen_maximo(precio, valor):
    """
    El techo del rendimiento posible, en porcentaje.

    `expected_value` nunca puede pasar de `valor - puja`, y la
    puja nunca baja del precio. Asi que ningun jugador puede
    rendir mas de `(valor - precio) / precio` por mucho
    presupuesto que se le eche.

    Es el numero que decide si el tope es la causa de muerte o
    solo el primer sitio donde se murio.
    """

    try:
        precio = int(precio or 0)
        valor = int(valor or 0)

        if precio <= 0:
            return None

        return 100 * (valor - precio) / precio

    except (TypeError, ValueError):
        return None


def sin_el_tope(fila: dict, modelo: dict) -> dict:
    """
    Que decidiria `optimal_bid` con el bolsillo infinito.

    Forma fija. Nunca lanza: si no se puede recalcular, lo dice
    en vez de inventarse una decision.
    """

    try:
        plan = optimal_bid(
            price=int(fila.get("market_price") or 0),
            value=int(fila.get("our_value") or 0),
            model=modelo,
            available_budget=None,
            intent=fila.get("intent"),
        )

        return {
            "available": True,
            "decision": plan.get("decision"),
            "bid": plan.get("bid"),
            "expected_value": plan.get("expected_value"),
            "reason": plan.get("reason"),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "decision": None,
            "bid": None,
            "expected_value": None,
            "reason": f"{type(error).__name__}: {error}",
        }


def main() -> None:

    estado = json.loads(ESTADO.read_text(encoding="utf-8"))

    tablero = estado.get("acquisition") or {}

    filas = tablero.get("targets") or []

    modelo = tablero.get("premium_model") or {}

    print()
    print("=" * 78)
    print("EL ESCAPARATE DEL COMPUTER, POR CAUSA DE MUERTE")
    print("=" * 78)
    print(
        f"  Publicado por produccion: "
        f"{(estado.get('meta') or {}).get('generated_at')}"
    )
    print(f"  Jugadores: {len(filas)}")
    print(
        f"  Bolsillo de especular: "
        f"{euros((tablero.get('budgets') or {}).get('speculation'))}"
        f" EUR"
    )

    print()
    print(
        f"  {'CAUSA':<28}{'CUANTOS':>9}   QUE SIGNIFICA"
    )
    print("  " + "-" * 74)

    for nombre, significa in PUERTAS:

        cuantos = sum(
            1 for f in filas if f.get("decision") == nombre
        )

        print(f"  {nombre:<28}{cuantos:>9}   {significa}")

    otros = [
        f
        for f in filas
        if f.get("decision")
        not in {n for n, _ in PUERTAS}
    ]

    if otros:
        print(
            f"  {'(otros)':<28}{len(otros):>9}   "
            f"{sorted({str(f.get('decision')) for f in otros})}"
        )

    # ==========================================================
    # LOS QUE LLEGAN AL TOPE
    # ==========================================================

    en_el_tope = [
        f
        for f in filas
        if f.get("decision") == "SUPERA_PRESUPUESTO"
    ]

    print()
    print("=" * 78)
    print("LOS QUE LLEGAN AL TOPE, Y SI EL TOPE ES SU CAUSA DE MUERTE")
    print("=" * 78)

    if not en_el_tope:
        print()
        print(
            "  Ninguno llega al tope. Mueren todos antes, asi que "
            "el tope\n  sigue sin bloquear nada."
        )
        return

    print()
    print(
        f"  {'JUGADOR':<18}{'PRECIO':>12}{'VALOR':>12}"
        f"{'MARGEN':>9}{'LISTON':>8}  SIN EL TOPE"
    )
    print("  " + "-" * 76)

    culpa_del_tope = 0
    moririan_igual = 0

    for fila in sorted(
        en_el_tope,
        key=lambda f: -(
            margen_maximo(
                f.get("market_price"), f.get("our_value")
            )
            or -99
        ),
    ):

        margen = margen_maximo(
            fila.get("market_price"), fila.get("our_value")
        )

        libre = sin_el_tope(fila, modelo)

        if libre.get("decision") == "BID":
            culpa_del_tope += 1
        else:
            moririan_igual += 1

        print(
            f"  {str(fila.get('name'))[:18]:<18}"
            f"{euros(fila.get('market_price')):>12}"
            f"{euros(fila.get('our_value')):>12}"
            f"{(f'{margen:+.2f} %' if margen is not None else '—'):>9}"
            f"{100 * MIN_SPECULATION_YIELD:>7.0f} %  "
            f"{libre.get('decision')}"
        )

    print()
    print(
        f"  Mueren POR EL TOPE (sin el, se pujaria): "
        f"{culpa_del_tope}"
    )
    print(
        f"  Moririan igual (el tope solo llego antes): "
        f"{moririan_igual}"
    )

    print()
    print(
        "  MARGEN es (valor - precio) / precio: el techo de lo "
        "que puede\n  rendir la operacion. Ninguna puja puede "
        "rendir mas que eso,\n  porque la puja nunca baja del "
        "precio."
    )


if __name__ == "__main__":
    main()
