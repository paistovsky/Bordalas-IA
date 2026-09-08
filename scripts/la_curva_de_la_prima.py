"""
Cuanto hay que ofrecer, medido sobre las 156 subastas del tablon.

LA PREGUNTA (11/09/2026)

    Si pujas `precio + 1` ganas solo lo que nadie mira. Si pujas
    `precio x 1,03` ganas alguno disputado pero pagas la prima en
    TODOS, incluidos los que habrias ganado por un euro.

    El punto que maximiza el resultado sale de los datos, no de
    una opinion.

LA TRAMPA, ESCRITA ANTES DE MIRAR

    Las 156 son compras que ALGUIEN GANO. Los jugadores por los
    que nadie pujo nunca no aparecen en el tablon.

    Esos son justo los que `precio + 1` se habria llevado, asi
    que la curva SUBESTIMA lo que gana pujar bajo. El sesgo va a
    favor de la conclusion, no en contra — y por eso hay que
    decirlo.

NI UNA LLAMADA A BIWENGER

    Todo del tablon en disco y de `status.json`.

COMO SE USA

    python -m scripts.la_curva_de_la_prima
"""

from __future__ import annotations

import json

from pathlib import Path

from src.analysis.la_subasta import curva_de_la_prima

from scripts.medir_la_subasta import (
    _historico_local,
    cargar,
    precio_del_dia,
    subastas,
)


ESTADO = (
    Path(__file__).parent.parent
    / "diagnostico"
    / "status.json"
)


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def prima_de_reventa() -> tuple:
    """
    Lo que paga el Computer al recomprar, MEDIDO por produccion.

    No se copia el numero: se lee de donde produccion lo publica,
    con su muestra. Si algun dia cambia, cambia aqui solo.
    """

    try:
        estado = json.loads(
            ESTADO.read_text(encoding="utf-8")
        )

        premium = (
            (estado.get("acquisition") or {}).get(
                "computer_premium"
            )
            or {}
        )

        if not premium.get("calibrated"):
            return (None, "El Computer no esta calibrado.")

        return (
            float(premium["median_percent"]) / 100.0,
            (
                f"+{premium['median_percent']} % medido sobre "
                f"{premium['priced']} ventas"
            ),
        )

    except Exception as error:                      # noqa: BLE001
        return (None, f"{type(error).__name__}: {error}")


def main() -> None:

    eventos = cargar()

    if not eventos:
        print("Sin tablon en disco.")
        return

    historico = _historico_local()

    ventas = subastas(eventos)

    # A cada subasta se le pega el precio de mercado de SU dia.
    # Sin precio no entra: una prima sin precio de referencia no
    # es una prima.
    con_precio = []

    for venta in ventas:

        precio = precio_del_dia(
            historico, venta["jugador"], venta["fecha"]
        )

        if precio:
            con_precio.append({**venta, "precio": precio})

    reventa, de_donde = prima_de_reventa()

    print()
    print("=" * 74)
    print("LA CURVA DE LA PRIMA")
    print("=" * 74)
    print()
    print(f"  Subastas del tablon:        {len(ventas)}")
    print(f"  Con precio de referencia:   {len(con_precio)}")
    print(f"  El Computer recompra a:     {de_donde}")

    if reventa is None:
        print("\n  Sin prima de reventa no hay cuenta que hacer.")
        return

    curva = curva_de_la_prima(con_precio, reventa)

    if not curva["available"]:
        print(f"\n  {curva['reason']}")
        return

    print()
    print(
        f"  {'OFRECE':>9}{'GANA':>7}{'%':>7}"
        f"{'PRIMA PAGADA':>15}{'NETO':>15}{'NETO/GANADA':>14}"
    )
    print("  " + "-" * 67)

    for fila in curva["filas"]:

        marca = (
            "  <-- MAXIMO"
            if fila is curva["mejor"]
            else ""
        )

        print(
            f"  {'+' + format(fila['importe_percent'], '.2f') + ' %':>9}"
            f"{fila['ganadas']:>7}"
            f"{fila['ganadas_percent']:>6.0f}%"
            f"{euros(fila['prima_pagada']):>15}"
            f"{euros(fila['neto']):>15}"
            f"{euros(fila['neto_por_ganada']):>14}"
            f"{marca}"
        )

    print()
    print(f"  {curva['reason']}")

    print()
    print("-" * 74)
    print("EL SESGO, QUE VA A FAVOR")
    print("-" * 74)
    print()
    print(
        "  Estas 156 son subastas que ALGUIEN gano. Los jugadores\n"
        "  por los que nadie pujo no dejan rastro en el tablon, y\n"
        "  esos son exactamente los que `precio + 1` se lleva.\n"
        "\n"
        "  Asi que la columna GANA esta por debajo de la realidad\n"
        "  en los importes bajos, y el maximo real esta igual de\n"
        "  abajo o mas. El sesgo empuja hacia pujar bajo, que es\n"
        "  la conclusion: conviene saberlo antes de creersela."
    )

    print()
    print("  Ni una llamada a Biwenger.")


if __name__ == "__main__":
    main()
