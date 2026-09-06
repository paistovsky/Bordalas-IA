"""
Cuantos de los mercados de rivales pasarian el liston.

LA PREGUNTA DEL ENCARGO (24/09/2026)

    "De los 27 de rivales, cuantos pasarian el liston si
     pudieramos comprarlos. Ese numero decide si el resto del
     plan merece las noches."

COMO SE CONTESTA, Y POR QUE ASI

    Con el tablero de produccion entero, no con una cuenta
    aparte. La sonda de la noche anterior calculo el ritmo con
    `priceIncrement / precio` -un salto de UN dia, sin racha- y
    dio ocho subidas que resultaron ser lo que le pasa al 42 %
    de la liga cualquier dia. Fue la quinta vez de la familia
    "un dato haciendose pasar por otro".

    Asi que aqui no se calcula nada: se llama a
    `build_acquisition_board` y se lee `would_pass`, que es el
    campo que el propio tablero publica despues de valorar con
    el ritmo del ojeador y su racha.

QUE HACE Y QUE NO

    Solo GET, contra nuestra liga. No puja, no vende, no
    responde ofertas y no escribe nada en disco.

COMO SE USA

    python -m scripts.sonda_mercado_rivales
"""

from __future__ import annotations

from src.analysis.acquisition_board import build_acquisition_board
from src.biwenger.client import BiwengerClient


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def main():

    client = BiwengerClient()

    print("Iniciando sesion...")
    client.login()

    liga = client.select_league()
    yo = ((liga or {}).get("user") or {}).get("id")

    print(f"Mi id: {yo}")

    mercado = client.get_market()
    catalogo = client.get_player_catalog()
    plantilla = client.get_my_team()

    # `get_player_catalog()` devuelve el diccionario de jugadores
    # pelado; el tablero espera la envoltura de Biwenger. Sin
    # esto el catalogo sale vacio y TODAS las filas se caen en
    # silencio -que es como esta sonda dio cero la primera vez-.
    snapshot = {
        "league": liga,
        "market": mercado,
        "catalog": {"data": {"players": catalogo}},
        "my_team": plantilla,
    }

    print(f"Catalogo: {len(catalogo)} jugadores")
    print(f"Ventas en el mercado: {len(mercado.get('sales') or [])}")

    # EL SALDO, PARA QUE EL PRESUPUESTO SEA EL DE VERDAD
    #
    #     Sin el, el tablero valora con un bolsillo inventado y
    #     `would_pass` diria mas o menos de lo que hay.
    saldo = ((mercado.get("status") or {}).get("balance"))

    print(f"Saldo: {euros(saldo)} EUR")

    # El mismo reparto de bolsillos que usa el ciclo.
    from src.analysis.bid_exposure_engine import build_bid_exposure

    exposicion = build_bid_exposure(snapshot, own_user_id=yo)

    print(f"Comprometido: {euros(exposicion.get('committed_total'))} EUR")

    # LOS DOS BOLSILLOS, DE PRODUCCION Y NO DE AQUI
    #
    #     `build_bid_exposure` sola devuelve 0: el reparto en
    #     caja y deuda segura lo hace el motor de especulacion,
    #     que vive mas arriba. Con un bolsillo de cero TODAS las
    #     filas salen SUPERA_PRESUPUESTO y el numero del encargo
    #     seria un cero falso.
    #
    #     Asi que se leen de `diagnostico/status.json`, que es lo
    #     que produccion publica de si misma. Nunca del disco
    #     local, que miente.
    import json

    from pathlib import Path

    estado = json.loads(
        (
            Path(__file__).parent.parent
            / "diagnostico"
            / "status.json"
        ).read_text(encoding="utf-8")
    )

    bolsillos = (estado.get("exposure") or {})

    disponible = bolsillos.get("available_budget")
    para_fichar = (
        bolsillos.get("acquisition") or {}
    ).get("available_budget")

    print(
        f"Generado por produccion: "
        f"{(estado.get('meta') or {}).get('generated_at')}"
    )
    print(f"Bolsillo de especular: {euros(disponible)} EUR")
    print(f"Bolsillo de fichar:    {euros(para_fichar)} EUR")

    tablero = build_acquisition_board(
        snapshot=snapshot,
        rival_intelligence={},
        current_user_id=yo,
        available_budget=disponible or None,
        acquisition_budget=para_fichar or None,
    )

    if not tablero.get("available"):
        print(f"El tablero no esta disponible: {tablero.get('reason')}")
        return

    rivales = tablero.get("rival_market") or {}

    print()
    print("=" * 74)
    print("EL ESCAPARATE, CON SUS DOS MITADES")
    print("=" * 74)
    print(f"  del Computer            {tablero.get('market_size')}")
    print(f"  de managers             {rivales.get('shown')}")
    print(f"  ---------------------------")
    print(f"  universo comprable      {tablero.get('buyable_universe')}")
    print()
    print(f"  vendedores              {', '.join(rivales.get('sellers') or []) or '-'}")
    print(f"  compra cerrada          {rivales.get('buying_closed')}")
    print()
    print(f"  PASARIAN EL LISTON      {rivales.get('would_pass')}")
    print(f"  (del Computer, PUJAR)   {tablero.get('biddable')}")

    filas = [
        f
        for f in (tablero.get("targets") or [])
        if f.get("rival_market")
    ]

    print()
    print("=" * 74)
    print("UNO A UNO, CON EL RITMO DEL OJEADOR Y SU RACHA")
    print("=" * 74)
    print()
    print(
        f"  {'JUGADOR':<22} {'PRECIO':>10} {'PIDEN':>10} "
        f"{'RITMO':>8} {'RACHA':>6}  {'HABRIA SIDO':<22} VENDE"
    )
    print("  " + "-" * 100)

    def ritmo_de(fila):
        bloque = fila.get("market_gate") or {}
        return bloque.get("rate_percent_per_day"), bloque.get(
            "trend_days"
        )

    # Los que pasarian primero: es la respuesta, no un detalle.
    filas.sort(
        key=lambda f: (
            not f.get("would_pass"),
            -(ritmo_de(f)[0] or -99),
        )
    )

    con_ritmo = 0

    for fila in filas:

        ritmo, racha = ritmo_de(fila)

        if ritmo is not None:
            con_ritmo += 1

        print(
            f"  {str(fila.get('name'))[:22]:<22} "
            f"{euros(fila.get('market_price')):>10} "
            f"{euros(fila.get('asking_price')):>10} "
            f"{(f'{ritmo:+.2f}%' if ritmo is not None else '-'):>8} "
            f"{(racha if racha is not None else '-'):>6}  "
            f"{str(fila.get('would_be_decision'))[:22]:<22} "
            f"{fila.get('seller_name')}"
        )

    print()
    print(
        f"  Con ritmo del ojeador: {con_ritmo} de {len(filas)}."
    )

    # POR QUE NO PASA CADA UNO
    #
    #     Un cero sin desglose no se puede interpretar. "Ninguno
    #     vale" y "ninguno cabe en el bolsillo" llevan a planes
    #     opuestos, y la diferencia esta aqui.
    from collections import Counter

    motivos = Counter(
        str(f.get("would_be_decision")) for f in filas
    )

    print()
    print("=" * 74)
    print("POR QUE NO PASA NINGUNO")
    print("=" * 74)

    for motivo, cuantos in motivos.most_common():
        print(f"  {motivo:<28} {cuantos:>3}")

    tope = (
        estado.get("speculation") or {}
    ).get("max_operation")

    caben = [
        f
        for f in filas
        if tope and (f.get("market_price") or 0) <= tope
    ]

    sobre_liston = [
        f
        for f in filas
        if (ritmo_de(f)[0] or 0) >= 3.0
    ]

    print()
    print(f"  Tope por operacion:        {euros(tope)} EUR")
    print(f"  Caben en el tope:          {len(caben)} de {len(filas)}")
    print(f"  Ritmo >= 3 %/dia:          {len(sobre_liston)} de {len(filas)}")
    print(
        f"  Las dos cosas a la vez:    "
        f"{len([f for f in caben if f in sobre_liston])}"
    )

    precios = sorted(
        (f.get("market_price") or 0) for f in filas
    )

    if precios:
        print(
            f"  Precio mediano del rival:  "
            f"{euros(precios[len(precios) // 2])} EUR"
        )

    print()
    print("  Ni una escritura. Ni una puja.")


if __name__ == "__main__":
    main()
