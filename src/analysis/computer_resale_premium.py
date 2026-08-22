from __future__ import annotations

"""
Cuanto paga el Computer por encima del mercado.

EL CASO (21/08/2026)

    El dueño lo dijo asi:

        "Me deja pujar, hay margen, por que no lo usa? Si lo gano
         a precio de mercado, lo puedo poner mañana y a ver si
         Computer me hace una oferta buena y ganamos unos K's ahi
         con la operacion."

    Se midio en su tablon: 36 ventas al Computer, mediana +2,9 %
    sobre el precio de mercado, 29 de 36 por encima. Gavi +11,2 %,
    Boyé +11,5 %, Sucic +15,1 %, Miguel Rodríguez +18,4 %.

    O sea que tenia razon: hay un diferencial, y es estable.

POR QUE PEPE NO LO VEIA

    `speculation_value` solo sabe ganar dinero de UNA manera: que
    el PRECIO DEL JUGADOR suba. Proyecta el incremento diario a
    tres dias y, si no sube, contesta SIN_REVALORIZACION y vale
    cero.

    Por eso 15 de 20 candidatos salian SIN VALOR el 21/08: no es
    que fueran malos, es que la unica via de reventa que el motor
    conoce estaba cerrada para ellos.

    La segunda via -comprar a mercado y venderle al Computer, que
    paga por encima- no estaba en el codigo. Ni bien ni mal: no
    estaba.

EL DENOMINADOR, QUE ES DONDE ESTA LA TRAMPA

    Aquella mediana de +2,9 % se saco dividiendo entre el precio
    de HOY, no entre el del dia de la venta. Es exactamente el
    sesgo que `historical_price_lookup` nacio para quitar: los
    precios se mueven a diario, asi que una venta vieja sale
    barata o cara segun por donde haya ido el jugador despues.

    Prueba de que importa: con el precio de hoy salian dos
    desastres, -39,9 % y -15,1 %. Con el precio de aquel momento
    no aparecen. No eran ofertas malas: eran jugadores que
    subieron despues.

    Aqui se mide SOLO con el precio de aquel momento. Lo que no se
    puede fechar, no cuenta.

FAIL-CLOSED

    Con pocas muestras limpias esto no se usa para decidir. El
    21/08 habia 3 de las 12 que hacen falta -mediana +2,0 %, las
    tres positivas-, que apunta al mismo sitio pero no es una
    medida.

    `calibrated` en falso significa "no se sabe todavia", no "no
    hay prima". Y mientras siga en falso, no se mueve un euro por
    esta via. Se cura sola conforme el almacen de precios se
    llena.
"""

import json
import statistics

from pathlib import Path


BOARD_FILE = (
    Path("data") / "rival_intelligence" / "board_events.json"
)


# El mismo liston que la curva de primas del modelo de puja. Con
# menos de doce, una racha se disfraza de patron.
MIN_SAMPLES = 12


# Una venta que se aparta un 50 % del mercado no describe la regla
# del Computer: describe un precio mal fechado o un caso raro.
MAX_ABSOLUTE_PREMIUM = 0.50


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def load_board_events(path: Path | str | None = None) -> list[dict]:
    """
    El tablon, tal y como lo dejo el colector. Nunca lanza.
    """

    try:
        ruta = Path(path) if path else BOARD_FILE

        datos = json.loads(ruta.read_text(encoding="utf-8"))

        return datos if isinstance(datos, list) else []

    except Exception:
        return []


def sales_to_computer(events: list[dict]) -> list[dict]:
    """
    Ventas de un manager al Computer.

    Se reconocen por tener vendedor y NO tener comprador: si
    hubiera comprador seria un traspaso entre managers, que se
    pacta y no dice nada de lo que paga el Computer.
    """

    ventas = []
    vistas = set()

    for evento in events or []:

        if evento.get("type") != "transfer":
            continue

        instante = safe_int(evento.get("date"))

        for movimiento in evento.get("content") or []:

            if not isinstance(movimiento, dict):
                continue

            if movimiento.get("to"):
                continue

            if not movimiento.get("from"):
                continue

            jugador = movimiento.get("player")
            importe = safe_int(movimiento.get("amount"))

            if jugador is None or importe <= 0:
                continue

            # El tablon se re-descarga y el mismo hecho puede
            # llegar con dos ids distintos. Un hecho contado dos
            # veces pesa el doble en la mediana.
            firma = (safe_int(jugador), instante, importe)

            if firma in vistas:
                continue

            vistas.add(firma)

            ventas.append(
                {
                    "player_id": safe_int(jugador),
                    "amount": importe,
                    "date": instante,
                    "seller": (movimiento.get("from") or {}).get(
                        "name"
                    ),
                }
            )

    return ventas


def measure_computer_resale_premium(
    events: list[dict] | None = None,
    price_at=None,
    min_samples: int = MIN_SAMPLES,
) -> dict:
    """
    Que prima paga el Computer sobre el precio de mercado.

    `price_at(player_id, cuando)` devuelve el precio de aquel
    momento, o 0 si no se puede fechar. Sin esa funcion no se mide
    nada: usar el precio de hoy es el sesgo que venimos a quitar.

    Nunca lanza.
    """

    try:
        if events is None:
            events = load_board_events()

        if price_at is None:
            from src.analysis.historical_price_lookup import (
                build_historical_price_lookup,
            )

            price_at = build_historical_price_lookup()

        ventas = sales_to_computer(events)

        primas = []
        sin_precio = 0
        descartadas = 0

        for venta in ventas:

            precio = safe_int(
                price_at(venta["player_id"], venta["date"])
            )

            if precio <= 0:
                sin_precio += 1
                continue

            prima = venta["amount"] / precio - 1.0

            if abs(prima) > MAX_ABSOLUTE_PREMIUM:
                descartadas += 1
                continue

            primas.append(prima)

        base = {
            "available": True,
            "sales_seen": len(ventas),
            "priced": len(primas),
            "discarded_no_price": sin_precio,
            "discarded_outlier": descartadas,
            "min_samples": int(min_samples),
        }

        if not primas:
            return {
                **base,
                "calibrated": False,
                "median_percent": None,
                "mean_percent": None,
                "positive_ratio": None,
                "reason": (
                    f"Ninguna de las {len(ventas)} ventas al "
                    f"Computer se puede fechar con el precio de "
                    f"aquel momento. Sin denominador no hay prima."
                ),
            }

        mediana = statistics.median(primas)
        media = statistics.mean(primas)

        positivas = sum(1 for p in primas if p > 0)

        calibrada = len(primas) >= min_samples

        return {
            **base,
            "calibrated": calibrada,
            "median_percent": round(mediana * 100, 2),
            "mean_percent": round(media * 100, 2),
            "positive_ratio": round(positivas / len(primas), 3),
            "reason": (
                (
                    f"El Computer paga una mediana de "
                    f"{mediana * 100:+.1f} % sobre el mercado "
                    f"({positivas} de {len(primas)} por encima)."
                )
                if calibrada
                else (
                    f"Solo {len(primas)} venta(s) fechables; hacen "
                    f"falta {min_samples}. No se usa para decidir. "
                    f"Descartadas: {sin_precio} sin precio de "
                    f"aquel momento, {descartadas} fuera de rango."
                )
            ),
        }

    except Exception as error:
        return {
            "available": False,
            "calibrated": False,
            "median_percent": None,
            "reason": f"{type(error).__name__}: {error}",
        }


def usable_premium(measure: dict | None) -> float | None:
    """
    La prima que se puede usar para decidir, o None.

    Es la puerta: `None` significa "no se sabe", y quien la
    reciba no debe inventarse un cero. Un cero diria "el Computer
    paga justo el mercado", que es una afirmacion, no un hueco.

    Una prima negativa medida tampoco se devuelve: si el Computer
    pagase por debajo, la via no existe y no hay nada que hacer
    con el numero.
    """

    if not measure or not measure.get("calibrated"):
        return None

    mediana = measure.get("median_percent")

    if mediana is None:
        return None

    try:
        valor = float(mediana) / 100.0
    except (TypeError, ValueError):
        return None

    return valor if valor > 0 else None


def print_computer_resale_premium(measure: dict) -> None:

    print()
    print("-" * 70)
    print("LO QUE PAGA EL COMPUTER POR ENCIMA DEL MERCADO")
    print("-" * 70)

    if not measure or not measure.get("available"):
        print(f"  No disponible: {(measure or {}).get('reason')}")
        return

    print(f"  ventas vistas        {measure['sales_seen']:>6}")
    print(f"  fechables            {measure['priced']:>6}")
    print(f"  sin precio           {measure['discarded_no_price']:>6}")
    print(f"  fuera de rango       {measure['discarded_outlier']:>6}")

    if measure.get("median_percent") is not None:
        print(f"  mediana              {measure['median_percent']:>+6.2f} %")
        print(f"  media                {measure['mean_percent']:>+6.2f} %")
        print(f"  por encima           {measure['positive_ratio']:>6.0%}")

    print(f"  calibrada            {measure['calibrated']}")
    print(f"  {measure.get('reason')}")
