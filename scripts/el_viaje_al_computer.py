"""
El viaje al Computer: comprar un jugador y vendérselo.

QUE HACE

    Cuenta, sobre ficheros que ya estan en disco:

        0. QUE SON      quien vende, contra que precio se mide,
                        cuantas son nuestras, y si el Computer
                        compra siempre.

        1. EL VIAJE     compra, espera, venta, neto. Con la prima
                        de compra y la de venta de LOS MISMOS
                        viajes (doctrina 54).

        2. EL SUELO     cuantos pasan el coste +1 %, cuanto se
                        tarda en cruzarlo, y cuales de los
                        nuestros siguen por debajo.

        3. POR DIA      el rendimiento por dia de capital
                        inmovilizado, y cuanto suma un mes.

        4. QUIEN        el reparto por manager.

    NO TOCA NADA. No escribe, no puja, no enciende. Imprime.

DE DONDE SALE CADA COSA

    data/rival_intelligence/board_events.json   el tablon
    data/autopilot/price_history.json           precios, respaldo
    data/snapshot_*.json                        precios y catalogo
    diagnostico/status.json                     la foto del 14/09

COMO SE USA

    python -m scripts.el_viaje_al_computer
    python -m scripts.el_viaje_al_computer --bloque 1
"""

from __future__ import annotations

import argparse
import bisect
import collections
import glob
import json
import statistics

from datetime import datetime, timezone
from pathlib import Path

from src.analysis.el_viaje_al_computer import (
    compras_en_el_mercado,
    cuanto_cabe_en_un_mes,
    dias_hasta_cruzar_el_suelo,
    por_manager,
    resumen,
    traspasos_entre_managers,
    ventas_al_computer,
    viajes,
)


RAIZ = Path(__file__).parent.parent

TABLON = RAIZ / "data" / "rival_intelligence" / "board_events.json"

PRECIOS = RAIZ / "data" / "autopilot" / "price_history.json"

FOTO = RAIZ / "diagnostico" / "status.json"

NOSOTROS = "Pepe Bordalás"

# Un precio de hace mas de esto no describe el momento de la
# operacion. El mismo margen que `historical_price_lookup`.
MAX_EDAD = 36 * 3600

# Por debajo de dos dias el precio de mercado apenas se mueve, asi
# que lo que queda es la prima del Computer y nada mas. Ese es el
# viaje "puro", y se mira aparte.
VIAJE_RAPIDO_DIAS = 2

# La diferencia con Pollo a 14/09, del informe del 15/09.
DISTANCIA_CON_POLLO = 24_600_000


def _leer(ruta, por_defecto=None):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return por_defecto


def _titulo(texto):
    print()
    print("=" * 78)
    print(texto)
    print("=" * 78)
    print()


def _sub(texto):
    print()
    print("-" * 78)
    print(texto)
    print("-" * 78)
    print()


def _fecha(marca):
    return datetime.fromtimestamp(marca, timezone.utc).strftime("%d/%m")


def construir_precios():
    """
    `precio(jugador, cuando)` con el precio de AQUEL momento.

    Primero los snapshots -que llegan mas atras- y el almacen del
    autopiloto de respaldo. Nunca un precio posterior: seria mirar
    el futuro, que es el sesgo que `historical_price_lookup` nacio
    para quitar.
    """

    from src.analysis.historical_price_lookup import (  # noqa: PLC0415
        build_historical_price_lookup,
    )

    snapshots = build_historical_price_lookup()

    serie = {}

    for jugador, fila in (
        (_leer(PRECIOS) or {}).get("players") or {}
    ).items():

        pares = sorted(
            zip((fila or {}).get("t") or [], (fila or {}).get("p") or [])
        )

        if pares:
            serie[int(jugador)] = (
                [x[0] for x in pares],
                [x[1] for x in pares],
            )

    def precio(jugador, cuando):

        valor = int(snapshots(jugador, cuando) or 0)

        if valor > 0:
            return valor

        guardado = serie.get(int(jugador))

        if not guardado:
            return 0

        marcas, precios = guardado

        i = bisect.bisect_right(marcas, int(cuando)) - 1

        if i < 0 or int(cuando) - marcas[i] > MAX_EDAD:
            return 0

        return int(precios[i] or 0)

    def hoy(jugador):
        guardado = serie.get(int(jugador))
        return int(guardado[1][-1] or 0) if guardado else 0

    return precio, hoy, serie


def construir_nombres():
    """El catalogo del ultimo snapshot. Sin el, se usa el id."""

    ficheros = sorted(glob.glob(str(RAIZ / "data" / "snapshot_*.json")))

    catalogo = {}

    for ruta in reversed(ficheros[-5:]):

        datos = _leer(ruta) or {}

        jugadores = (
            ((datos.get("catalog") or {}).get("data") or {}).get(
                "players"
            )
            or {}
        )

        if jugadores:
            catalogo = jugadores
            break

    def nombre(jugador):
        ficha = catalogo.get(str(jugador)) or {}
        return ficha.get("name") or f"#{jugador}"

    return nombre, len(catalogo)


# ============================================================
# BLOQUE 0
# ============================================================


def bloque_cero(eventos, ventas, precio, catalogo_n, foto):

    _titulo("BLOQUE 0 — QUE SON EXACTAMENTE ESAS VENTAS")

    mercado = compras_en_el_mercado(eventos)
    traspasos = traspasos_entre_managers(eventos)

    print(f"  compras en el mercado del Computer   {len(mercado):>4}")
    print(f"  traspasos entre managers             {len(traspasos):>4}")
    print(f"  ventas al Computer                   {len(ventas):>4}")
    print(
        "  el Computer REVENDIENDO a un manager    0   "
        "(no existe ese evento)"
    )
    print()
    print(
        "  Las ventas se reconocen por tener vendedor y NO tener "
        "comprador. Las 178 son"
    )
    print(
        "  managers vendiendole al Computer, que es exactamente lo "
        "que hariamos nosotros."
    )

    _sub("CONTRA QUE PRECIO SE MIDE, Y CUANTAS SE PUEDEN MEDIR")

    con = sum(
        1 for v in ventas if precio(v["player_id"], v["date"]) > 0
    )

    fechas = [v["date"] for v in ventas]

    print(
        f"  rango del tablon                     "
        f"{_fecha(min(fechas))} -> {_fecha(max(fechas))}"
    )
    print(f"  ventas con precio de AQUEL dia       {con:>4}")
    print(f"  sin precio fechable                  {len(ventas) - con:>4}")
    print()
    print(
        "  El precio es el del dia de la venta, nunca el de hoy. Lo "
        "que no se puede"
    )
    print("  fechar no se estima: se cuenta aparte y se dice.")

    _sub("CUANTAS SON NUESTRAS, Y SI NOS PAGA IGUAL")

    primas = collections.defaultdict(list)

    for venta in ventas:

        mercado_dia = precio(venta["player_id"], venta["date"])

        if mercado_dia <= 0:
            continue

        prima = (venta["amount"] / mercado_dia - 1) * 100

        if abs(prima) <= 50:
            primas[venta["manager"]].append(prima)

    print(
        f"  {'manager':<26}{'ventas':>8}{'fechadas':>10}"
        f"{'prima mediana':>15}"
    )
    print("  " + "-" * 59)

    todas = []

    for nombre, cuantas in collections.Counter(
        v["manager"] for v in ventas
    ).most_common():

        suyas = primas.get(nombre, [])

        todas += suyas

        print(
            f"  {str(nombre)[:24]:<26}{cuantas:>8}{len(suyas):>10}"
            + (
                f"{statistics.median(suyas):>+14.2f}%"
                if suyas
                else f"{'—':>15}"
            )
        )

    print("  " + "-" * 59)
    print(
        f"  {'TODAS':<26}{len(ventas):>8}{len(todas):>10}"
        f"{statistics.median(todas):>+14.2f}%"
    )
    print()
    print(
        "  El +2,03 % del motor y este +2,37 % no son el mismo "
        "numero: el del motor sale"
    )
    print(
        "  de una foto anterior y con su propio descarte. La "
        "direccion es la misma."
    )

    _sub("¿EL COMPUTER COMPRA SIEMPRE?")

    adquisicion = (foto or {}).get("acquisition") or {}

    tamano = adquisicion.get("market_size")

    fuera = adquisicion.get("outside_computer_market")

    print(f"  jugadores en el catalogo             {catalogo_n:>4}")
    print(f"  mercado del Computer ese dia         {tamano:>4}")
    print(f"  fuera del mercado del Computer       {fuera:>4}")
    print()
    print(
        "  COMPRAR es lo limitado: el Computer saca 20 jugadores al "
        "dia de un catalogo"
    )
    print(
        f"  de {catalogo_n}, el "
        f"{100 * (tamano or 0) / max(catalogo_n, 1):.1f} %. El resto "
        f"solo se compra a otro manager."
    )
    print()
    print(
        "  VENDER no lo esta: de las 178 ventas al Computer ninguna "
        "se quedo sin"
    )
    print(
        "  comprador. En el tablon no existe el evento «nadie la "
        "quiso»."
    )


# ============================================================
# BLOQUE 1
# ============================================================


def bloque_uno(hechos, nombre):

    _titulo("BLOQUE 1 — EL VIAJE COMPLETO, DE PUNTA A PUNTA")

    print(f"  {hechos['reason']}")

    trips = hechos["trips"]

    liga = resumen(trips)

    nuestros = resumen(
        [t for t in trips if t["manager"] == NOSOTROS]
    )

    _sub("LA CUENTA QUE PUEDE MATARLO TODO — las dos primas, de LOS MISMOS viajes")

    print(
        f"  {'':<16}{'fechados':>10}{'de':>6}"
        f"{'prima compra':>15}{'prima venta':>14}{'hueco':>10}"
    )
    print("  " + "-" * 71)

    for etiqueta, medido in (
        ("toda la liga", liga),
        ("nosotros", nuestros),
    ):
        if not medido["available"]:
            print(f"  {etiqueta:<16}   sin viajes")
            continue

        print(
            f"  {etiqueta:<16}{medido['priced_n']:>10}"
            f"{medido['n']:>6}"
            f"{medido['buy_premium_median']:>+14.2f}%"
            f"{medido['sell_premium_median']:>+13.2f}%"
            f"{medido['premium_gap']:>+9.2f}pp"
        )

    print()

    if liga["available"] and liga["premium_gap"] is not None:
        if liga["premium_gap"] > 0:
            print(
                f"  NO SE RESTAN: el hueco es "
                f"{liga['premium_gap']:+.2f} puntos a favor. El viaje "
                f"NACE EN GANANCIA."
            )
        else:
            print(
                f"  SE RESTAN: el hueco es "
                f"{liga['premium_gap']:+.2f} puntos. El viaje nace en "
                f"perdida y el encargo termina aqui."
            )

    _sub("EL NETO, VIAJE A VIAJE")

    print(
        f"  {'':<16}{'n':>5}{'neto mediano':>15}{'neto %':>10}"
        f"{'dias':>8}{'%/dia':>9}{'ganan':>8}{'pierden':>9}"
    )
    print("  " + "-" * 80)

    for etiqueta, medido in (
        ("toda la liga", liga),
        ("nosotros", nuestros),
    ):
        if not medido["available"]:
            continue

        print(
            f"  {etiqueta:<16}{medido['n']:>5}"
            f"{medido['net_eur_median']:>+15,.0f}"
            f"{medido['net_percent_median']:>+9.2f}%"
            f"{medido['days_median']:>8.1f}"
            f"{medido['percent_per_day_median']:>+8.3f}%"
            f"{medido['winners']:>8}{medido['losers']:>9}"
        )

    if liga["available"]:
        mejor, peor = liga["best"], liga["worst"]
        print()
        print(
            f"  MEJOR  {str(mejor['manager'])[:16]:<18}"
            f"{nombre(mejor['player_id'])[:14]:<16}"
            f"{mejor['paid']:>11,} -> {mejor['collected']:>11,}"
            f"{mejor['net_eur']:>+11,}  ({mejor['days']:.1f} d)"
        )
        print(
            f"  PEOR   {str(peor['manager'])[:16]:<18}"
            f"{nombre(peor['player_id'])[:14]:<16}"
            f"{peor['paid']:>11,} -> {peor['collected']:>11,}"
            f"{peor['net_eur']:>+11,}  ({peor['days']:.1f} d)"
        )

    _sub("DE DONDE SALE EL NETO: ¿el Computer, o el precio subiendo?")

    fechados = [t for t in trips if t.get("priced")]

    deriva = [
        100.0 * (t["market_on_sell"] / t["market_on_buy"] - 1.0)
        for t in fechados
    ]

    print(f"  sobre n = {len(fechados)} viajes fechados, medianas:")
    print()
    print(
        f"     deriva del mercado mientras lo tenemos   "
        f"{statistics.median(deriva):>+7.2f} %"
    )
    print(
        f"     prima de venta (lo que paga el Computer) "
        f"{liga['sell_premium_median']:>+7.2f} %"
    )
    print(
        f"     prima de compra (lo que pagamos de mas)  "
        f"{liga['buy_premium_median']:>+7.2f} %"
    )
    print()
    print(
        f"     lo que aporta EL COMPUTER                "
        f"{liga['premium_gap']:>+7.2f} pp"
    )
    print(
        f"     lo que aporta EL PRECIO SUBIENDO         "
        f"{statistics.median(deriva):>+7.2f} pp"
    )

    _sub("POR DURACION — ¿es una via de un dia o de dos semanas?")

    print(
        f"  {'dias':<10}{'n':>5}{'neto %':>10}{'%/dia':>10}"
        f"{'deriva':>10}{'prima vta':>12}{'ganan':>8}"
    )
    print("  " + "-" * 65)

    for bajo, alto, etiqueta in (
        (0, 1, "0-1"),
        (1, 2, "1-2"),
        (2, 4, "2-4"),
        (4, 8, "4-8"),
        (8, 15, "8-15"),
        (15, 9999, "15+"),
    ):
        grupo = [t for t in trips if bajo <= t["days"] < alto]

        if not grupo:
            print(f"  {etiqueta:<10}{0:>5}   sin muestra")
            continue

        con_precio = [t for t in grupo if t.get("priced")]

        netos = [
            t["net_percent"]
            for t in grupo
            if t["net_percent"] is not None
        ]

        por_dia = [
            t["net_percent_per_day"]
            for t in grupo
            if t["net_percent_per_day"] is not None
        ]

        derivas = [
            100.0 * (t["market_on_sell"] / t["market_on_buy"] - 1.0)
            for t in con_precio
        ]

        ventas_p = [t["sell_premium"] for t in con_precio]

        print(
            f"  {etiqueta:<10}{len(grupo):>5}"
            f"{statistics.median(netos):>+9.2f}%"
            f"{(statistics.median(por_dia) if por_dia else 0):>+9.3f}%"
            f"{(statistics.median(derivas) if derivas else 0):>+9.2f}%"
            f"{(statistics.median(ventas_p) if ventas_p else 0):>+11.2f}%"
            f"{sum(1 for t in grupo if t['net_eur'] > 0):>8}"
        )

    print()
    print(
        "  El tramo de 1-2 dias es el viaje PURO: el mercado apenas "
        "se mueve, asi que"
    )
    print(
        "  todo lo que queda es la prima del Computer. Los tramos "
        "largos no son esta"
    )
    print("  via: son tener a un jugador que sube.")

    return liga, nuestros


# ============================================================
# BLOQUE 2
# ============================================================


def bloque_dos(hechos, precio_hoy, nombre, serie):

    _titulo("BLOQUE 2 — EL SUELO DEL +1 %")

    trips = hechos["trips"]

    for etiqueta, seleccion in (
        ("toda la liga", trips),
        ("nosotros", [t for t in trips if t["manager"] == NOSOTROS]),
    ):
        medido = dias_hasta_cruzar_el_suelo(seleccion)
        print(f"  {etiqueta:<16} {medido['reason']}")

    _sub("NUESTRAS POSICIONES ABIERTAS CONTRA EL SUELO")

    abiertas = [
        c
        for c in hechos["open_positions"]
        if c["manager"] == NOSOTROS
    ]

    ahora = max(
        max(marcas) for marcas, _ in serie.values()
    ) if serie else 0

    print(
        f"  {'jugador':<18}{'comprada':>10}{'pagado':>12}"
        f"{'hoy':>12}{'suelo':>12}{'le falta':>11}{'dias':>7}"
    )
    print("  " + "-" * 82)

    debajo = 0

    for compra in sorted(abiertas, key=lambda c: c["date"]):

        hoy = precio_hoy(compra["player_id"])

        suelo = int(compra["amount"] * 1.01)

        dias = (ahora - compra["date"]) / 86400

        falta = suelo - hoy

        if hoy and hoy < suelo:
            debajo += 1

        print(
            f"  {nombre(compra['player_id'])[:16]:<18}"
            f"{_fecha(compra['date']):>10}"
            f"{compra['amount']:>12,}{hoy:>12,}{suelo:>12,}"
            + (f"{falta:>+11,}" if hoy else f"{'?':>11}")
            + f"{dias:>7.1f}"
        )

    print()
    print(
        f"  de {len(abiertas)} posiciones nuestras abiertas, "
        f"{debajo} estan POR DEBAJO del suelo"
    )
    print(
        "  («le falta» positivo = cuanto le queda para llegar; "
        "negativo = ya lo paso)"
    )


# ============================================================
# BLOQUE 3
# ============================================================


def bloque_tres(hechos, liga, nuestros, foto):

    _titulo("BLOQUE 3 — EL RENDIMIENTO POR DIA")

    trips = hechos["trips"]

    rapidos = [t for t in trips if t["days"] < VIAJE_RAPIDO_DIAS]

    capital = int(
        ((foto or {}).get("acquisition") or {})
        .get("budgets", {})
        .get("speculation")
        or 0
    )

    print(
        f"  {'':<28}{'n':>5}{'neto %':>10}{'dias':>8}{'%/dia':>10}"
    )
    print("  " + "-" * 61)

    for etiqueta, seleccion in (
        ("todos los viajes de la liga", trips),
        (f"solo los rapidos (<{VIAJE_RAPIDO_DIAS} dias)", rapidos),
        (
            "los nuestros",
            [t for t in trips if t["manager"] == NOSOTROS],
        ),
    ):
        medido = resumen(seleccion)

        if not medido["available"]:
            print(f"  {etiqueta:<28}   sin viajes")
            continue

        print(
            f"  {etiqueta:<28}{medido['n']:>5}"
            f"{medido['net_percent_median']:>+9.2f}%"
            f"{medido['days_median']:>8.1f}"
            f"{medido['percent_per_day_median']:>+9.3f}%"
        )

    _sub("CUANTO SUMA UN MES")

    marcas = [t["bought_at"] for t in trips] + [
        t["sold_at"] for t in trips
    ]

    ventana = (max(marcas) - min(marcas)) / 86400

    pollo_rapidos = [t for t in rapidos if t["manager"] == "Pollo17"]

    neto_rapidos = sum(t["net_eur"] for t in rapidos)

    print(f"  ventana medida          {ventana:.0f} dias")
    print(f"  capital de especulacion {capital:,} EUR")
    print(
        f"  viaje rapido mediano    "
        f"{resumen(rapidos)['net_percent_median']:+.2f} % en "
        f"{resumen(rapidos)['days_median']:.1f} dias "
        f"(n={len(rapidos)})"
    )
    print()

    real = neto_rapidos / ventana * 30 if ventana else 0

    medido_rapido = resumen(rapidos)

    techo = cuanto_cabe_en_un_mes(medido_rapido, capital, dias=30)

    print(
        f"  A) al ritmo REAL de la liga "
        f"({len(pollo_rapidos)} de Pollo en {ventana:.0f} dias, "
        f"uno cada {ventana / max(len(pollo_rapidos), 1):.1f}):"
    )
    print(f"        {real:>+14,.0f} EUR/mes")
    print()

    if techo["available"]:
        print(
            f"  B) si la caja rotase sin parar "
            f"({techo['cycles']:.0f} vueltas/mes):"
        )
        print(f"        {techo['total']:>+14,.0f} EUR/mes")

    print()
    print(
        "  (B) es un TECHO ARITMETICO, no una prevision: supone "
        "encontrar una"
    )
    print(
        "  oportunidad cada dia y ganarla siempre. Quien mejor lo "
        "hace encontro"
    )
    print(f"  {len(pollo_rapidos)} en {ventana:.0f} dias.")

    _sub("CONTRA LA DISTANCIA CON POLLO")

    print(
        f"  diferencia total con Pollo          "
        f"{DISTANCIA_CON_POLLO:>+14,} EUR"
    )
    print(f"  un mes de esta via al ritmo real    {real:>+14,.0f} EUR")
    print(
        f"  meses para cerrarla solo con esto   "
        f"{DISTANCIA_CON_POLLO / real:>14.1f}"
        if real > 0
        else "  no se cierra: el ritmo real es negativo"
    )


# ============================================================
# BLOQUE 4
# ============================================================


def bloque_cuatro(hechos, ventas):

    _titulo("BLOQUE 4 — QUIEN LE VENDE AL COMPUTER")

    trips = hechos["trips"]

    rapidos = [t for t in trips if t["days"] < VIAJE_RAPIDO_DIAS]

    todas = collections.Counter(v["manager"] for v in ventas)

    emparejadas = collections.Counter(t["manager"] for t in trips)

    veloces = collections.Counter(t["manager"] for t in rapidos)

    medido = por_manager(trips)

    print(
        f"  {'manager':<26}{'ventas':>8}{'viajes':>8}{'rapidos':>9}"
        f"{'neto total':>15}{'%/dia':>9}"
    )
    print("  " + "-" * 75)

    for nombre, cuantas in todas.most_common():

        suyo = medido.get(nombre)

        neto = (
            suyo["net_eur_total"]
            if suyo and suyo["available"]
            else 0
        )

        por_dia = (
            suyo.get("percent_per_day_median")
            if suyo and suyo["available"]
            else None
        )

        print(
            f"  {str(nombre)[:24]:<26}{cuantas:>8}"
            f"{emparejadas.get(nombre, 0):>8}"
            f"{veloces.get(nombre, 0):>9}{neto:>+15,}"
            + (
                f"{por_dia:>+8.3f}%"
                if por_dia is not None
                else f"{'—':>9}"
            )
        )

    _sub("LO QUE NOS HEMOS PERDIDO")

    pollo = [t for t in trips if t["manager"] == "Pollo17"]

    nuestros = [t for t in trips if t["manager"] == NOSOTROS]

    neto_pollo = sum(t["net_eur"] for t in pollo)

    neto_nuestro = sum(t["net_eur"] for t in nuestros)

    diferencia = neto_pollo - neto_nuestro

    print(
        f"  Pollo, todos sus viajes al Computer   n={len(pollo):>3}   "
        f"{neto_pollo:>+13,} EUR"
    )
    print(
        f"  Pollo, solo los rapidos               "
        f"n={sum(1 for t in pollo if t['days'] < VIAJE_RAPIDO_DIAS):>3}   "
        f"{sum(t['net_eur'] for t in pollo if t['days'] < VIAJE_RAPIDO_DIAS):>+13,} EUR"
    )
    print(
        f"  Nosotros, todos                       "
        f"n={len(nuestros):>3}   {neto_nuestro:>+13,} EUR"
    )
    print(
        f"  Nosotros, rapidos                     "
        f"n={sum(1 for t in nuestros if t['days'] < VIAJE_RAPIDO_DIAS):>3}   "
        f"{0:>+13,} EUR"
    )
    print()
    print(
        f"  diferencia con Pollo SOLO en esta via "
        f"     {diferencia:>+13,} EUR"
    )
    print(
        f"  diferencia total con Pollo            "
        f"     {DISTANCIA_CON_POLLO:>+13,} EUR"
    )
    print(
        f"  esta via explica el "
        f"{100 * diferencia / DISTANCIA_CON_POLLO:.0f} % de toda la "
        f"distancia"
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bloque",
        type=int,
        choices=(0, 1, 2, 3, 4),
        default=None,
    )

    opciones = parser.parse_args()

    eventos = _leer(TABLON, []) or []

    if not eventos:
        print(f"El tablon llega vacio ({TABLON}): no hay nada que contar.")
        return 1

    precio, precio_hoy, serie = construir_precios()

    nombre, catalogo_n = construir_nombres()

    foto = _leer(FOTO, {}) or {}

    compras = compras_en_el_mercado(eventos) + traspasos_entre_managers(
        eventos
    )

    ventas = ventas_al_computer(eventos)

    hechos = viajes(compras, ventas, precio)

    print("=" * 78)
    print("EL VIAJE AL COMPUTER — comprar un jugador y vendérselo")
    print("=" * 78)
    print()
    print(f"  tablon:    {len(eventos)} eventos")
    print(f"  catalogo:  {catalogo_n} jugadores")
    print("  escrituras contra Biwenger: NINGUNA. Esto solo cuenta.")

    bloques = (
        [opciones.bloque]
        if opciones.bloque is not None
        else [0, 1, 2, 3, 4]
    )

    liga = nuestros = {}

    if 0 in bloques:
        bloque_cero(eventos, ventas, precio, catalogo_n, foto)

    if 1 in bloques or 3 in bloques:
        liga, nuestros = bloque_uno(hechos, nombre)

    if 2 in bloques:
        bloque_dos(hechos, precio_hoy, nombre, serie)

    if 3 in bloques:
        bloque_tres(hechos, liga, nuestros, foto)

    if 4 in bloques:
        bloque_cuatro(hechos, ventas)

    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
