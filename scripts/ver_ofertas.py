"""
Quien ha pujado a quien, segun Biwenger.

POR QUE EXISTE (23/08/2026)

    El dueño lo vio asi:

        "A Andrés Castrín ya le tengo y dice que está en el
         mercado y que ha pujado por él??"

    En el tablero salia su propio jugador -publicado por el, con
    tres ofertas encima- marcado como PUJA PUESTA por 1.190.038 EUR.

    Y la cuenta cuadra en el sitio equivocado:

        1.190.038  (Castrín, que es SUYO)
        +  424.350  (Oriol Rey, esa si es una puja suya)
        ---------
        1.614.388  -> "2 PUJAS VIVAS · 1.61M comprometidos"

    Biwenger, en la misma pantalla, dice **1 puja** y 14 ofertas.
    Asi que hay una oferta RECIBIDA contandose como puja PUESTA, y
    eso le esta recortando 1,19 M del presupuesto de fichar por un
    dinero que no ha comprometido.

QUE HACE ESTO

    Pide el mercado y enseña, oferta por oferta, quien es `from`,
    quien es `to`, de que tipo es y que jugadores pide. Y al lado,
    que decide el contador de exposicion con cada una.

    En el snapshot del 17/08 las doce ofertas eran todas
    `from: null, to: nosotros` -recibidas- y el contador daba
    cero, correcto. Hoy hay algo con otra forma, y hasta verla no
    se arregla nada: se adivina.

QUE NO HACE

    No enseña credenciales y no escribe nada. Solo lee.

COMO SE USA

    python -m scripts.ver_ofertas
"""

from __future__ import annotations

import json

from src.analysis.bid_exposure_engine import (
    build_bid_exposure,
    get_own_user_id,
)
from src.biwenger.client import BiwengerClient


def quien(bloque, yo):
    """`from` o `to`, en una linea."""

    if bloque is None:
        return "null"

    if isinstance(bloque, dict):
        identificador = bloque.get("id")
        nombre = bloque.get("name")

        etiqueta = "YO" if identificador == yo else "otro"

        return f"{etiqueta} id={identificador} ({nombre})"

    return f"{type(bloque).__name__} {bloque}"


def main():

    client = BiwengerClient()

    print("Iniciando sesión...")
    client.login()
    liga = client.select_league()

    yo = (
        (liga or {}).get("user") or {}
    ).get("id")

    print(f"Mi id: {yo}")

    market = client.get_market()

    ofertas = market.get("offers") or []
    ventas = market.get("sales") or []

    print(f"Ofertas en el mercado: {len(ofertas)}")
    print(f"Ventas publicadas:     {len(ventas)}")

    # Nombres, para poder leer la salida.
    nombres = {}

    for venta in ventas:
        ficha = venta.get("player") or {}
        if ficha.get("id") is not None:
            nombres[int(ficha["id"])] = ficha.get("name")

    print()
    print("=" * 70)
    print("OFERTA POR OFERTA")
    print("=" * 70)

    for oferta in ofertas:

        if not isinstance(oferta, dict):
            continue

        pedidos = []

        for solicitado in (oferta.get("requestedPlayers") or []):
            identificador = (
                solicitado.get("id")
                if isinstance(solicitado, dict)
                else solicitado
            )
            try:
                identificador = int(identificador)
            except (TypeError, ValueError):
                continue

            pedidos.append(
                f"{identificador}"
                + (
                    f" ({nombres[identificador]})"
                    if identificador in nombres
                    else ""
                )
            )

        print()
        print(f"  id      {oferta.get('id')}")
        print(f"  type    {oferta.get('type')}")
        print(f"  status  {oferta.get('status')}")
        print(f"  amount  {int(oferta.get('amount') or 0):,}".replace(",", "."))
        print(f"  from    {quien(oferta.get('from'), yo)}")
        print(f"  to      {quien(oferta.get('to'), yo)}")
        print(f"  pide    {', '.join(pedidos) or '—'}")
        print(f"  claves  {list(oferta.keys())}")

    print()
    print("=" * 70)
    print("QUE CUENTA EL CONTADOR DE EXPOSICION")
    print("=" * 70)

    # El mismo snapshot minimo que usa el ciclo para esto.
    snapshot = {"league": liga, "market": market}

    print(f"  own_user_id deducido: {get_own_user_id(snapshot)}")

    exposicion = build_bid_exposure(snapshot)

    print(
        f"  comprometido: "
        f"{exposicion.get('committed_total', 0):,}".replace(",", ".")
    )
    print(f"  operaciones:  {exposicion.get('operation_count')}")

    for operacion in (exposicion.get("operations") or []):
        print(
            f"    {operacion['amount']:>12,}".replace(",", ".")
            + f"  jugadores={operacion['player_ids']}"
            + f"  contraparte={operacion.get('counterparty_name')}"
        )

    print()
    print("  (Biwenger dice cuantas pujas tienes en la pestaña")
    print("   'puja' de la pantalla de mercado. Si ese numero y")
    print("   'operaciones' no coinciden, ahi esta el fallo.)")


if __name__ == "__main__":
    main()
