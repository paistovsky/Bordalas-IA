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


# ============================================================
# LA PRIMA NO ES UNA CONSTANTE: ES UNA CURVA (20/09/2026)
# ============================================================
#
#     Medido sobre las 194 ventas fechables, la prima SUBE con el
#     precio. Y el modelo metia UNA sola mediana para todos, asi
#     que la ganancia esperada de la cesta salia proporcional al
#     precio y el rendimiento por euro CONSTANTE — doctrina 98:
#     un ratio constante no delata al ratio, delata a su entrada.
#
#     LOS CORTES NO SON NUEVOS, Y ESO ES A PROPOSITO
#
#         1.500.000 y 3.000.000 son `CORTES_DE_PRECIO`, la
#         rejilla que `la_subasta` ya usa para la probabilidad de
#         pelea. Las dos se multiplican en el mismo sitio
#         (`_por_euro`), asi que dos rejillas distintas para el
#         mismo eje serian una arbitrariedad escondida.
#
#         El unico corte nuevo es 6.000.000, y sale de donde
#         estaba el salto: +2,63 % de 3 a 6 M contra +4,26 % por
#         encima. Parte la celda de arriba de la pelea, que es
#         abierta, SOLO para la prima.
#
#     LO QUE LA CURVA NO DICE, Y HAY QUE DECIRLO
#
#         La dispersion DENTRO de cada tramo es mayor que la
#         separacion ENTRE tramos: el rango intercuartilico va de
#         2,9 a 4,2 puntos y las medianas se separan 1,8. La
#         curva describe la mediana, no lo que pasa en una
#         operacion suelta.
CORTES_DE_LA_PRIMA = (1_500_000, 3_000_000, 6_000_000)


ENV_POR_TRAMO = "BORDALAS_PRIMA_POR_TRAMO"


def prima_por_tramo_activa() -> bool:
    """Si la curva manda sobre la mediana unica. Nunca lanza."""

    import os

    return str(
        os.environ.get(ENV_POR_TRAMO, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def _primas_fechadas(events, price_at) -> list:
    """`[(precio_de_entonces, prima)]`. Nunca lanza."""

    salida = []

    for venta in sales_to_computer(events):

        try:
            precio = safe_int(
                price_at(venta["player_id"], venta["date"])
            )

        except Exception:                           # noqa: BLE001
            continue

        if precio <= 0:
            continue

        prima = venta["amount"] / precio - 1.0

        if abs(prima) > MAX_ABSOLUTE_PREMIUM:
            continue

        salida.append((precio, prima))

    return salida


def _etiqueta(desde, hasta) -> str:

    if hasta is None:
        return f"{desde:,}+".replace(",", ".")

    return f"{desde:,}-{hasta:,}".replace(",", ".")


def medir_la_prima_por_tramo(
    events: list[dict] | None = None,
    price_at=None,
    cortes=CORTES_DE_LA_PRIMA,
    min_samples: int = MIN_SAMPLES,
) -> dict:
    """
    La prima y la tasa de acierto, tramo a tramo.

    Forma fija, nunca lanza. Un tramo con menos de `min_samples`
    sale `calibrado: False` y NO trae numero propio: quien lo use
    cae a la mediana global, que es lo que hace la curva de pujas
    con una celda corta.
    """

    vacio = {
        "available": False,
        "calibrated": False,
        "cortes": list(cortes),
        "min_samples": int(min_samples),
        "global_percent": None,
        "global_positive_ratio": None,
        "tramos": [],
        "reason": None,
    }

    try:
        if events is None:
            events = load_board_events()

        if price_at is None:
            from src.analysis.historical_price_lookup import (
                build_historical_price_lookup,
            )

            price_at = build_historical_price_lookup()

        filas = _primas_fechadas(events, price_at)

        if not filas:
            return {
                **vacio,
                "available": True,
                "reason": (
                    "Ninguna venta al Computer se puede fechar "
                    "con el precio de aquel momento. Sin "
                    "denominador no hay prima."
                ),
            }

        todas = [p for _, p in filas]

        global_mediana = statistics.median(todas)

        global_verde = sum(1 for p in todas if p > 0) / len(todas)

        bordes = [0] + list(cortes) + [None]

        tramos = []

        for desde, hasta in zip(bordes, bordes[1:]):

            grupo = [
                p
                for precio, p in filas
                if precio >= desde
                and (hasta is None or precio < hasta)
            ]

            calibrado = len(grupo) >= min_samples

            tramos.append({
                "desde": desde,
                "hasta": hasta,
                "etiqueta": _etiqueta(desde, hasta),
                "n": len(grupo),
                "calibrado": calibrado,

                # SIN MASA NO HAY NUMERO PROPIO (doctrina 24).
                # `None` no es cero: es "cae a la global".
                "median_percent": (
                    round(statistics.median(grupo) * 100, 2)
                    if calibrado
                    else None
                ),
                "positive_ratio": (
                    round(
                        sum(1 for p in grupo if p > 0)
                        / len(grupo),
                        3,
                    )
                    if calibrado
                    else None
                ),
                "reason": (
                    f"{len(grupo)} venta(s) fechadas."
                    if calibrado
                    else (
                        f"Sin calibrar: {len(grupo)} venta(s), "
                        f"hacen falta {min_samples}. Usa la "
                        f"mediana global."
                    )
                ),
            })

        calibrados = [t for t in tramos if t["calibrado"]]

        return {
            **vacio,
            "available": True,
            "calibrated": bool(calibrados),
            "global_percent": round(global_mediana * 100, 2),
            "global_positive_ratio": round(global_verde, 3),
            "tramos": tramos,
            "reason": (
                f"{len(calibrados)} de {len(tramos)} tramo(s) "
                f"calibrado(s) sobre {len(filas)} venta(s) "
                f"fechadas. Mediana global "
                f"{global_mediana * 100:+.2f} %."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": f"{type(error).__name__}: {error}",
        }


def prima_del_tramo(curva: dict | None, precio) -> dict:
    """
    La prima que le toca a ESE precio. Forma fija, nunca lanza.

    `{percent, calibrado, n, etiqueta, reason}`. Si el tramo no
    esta calibrado, devuelve la mediana global y lo dice: un
    numero inventado para un tramo sin masa es peor que no tener
    tramos.
    """

    vacio = {
        "percent": None,
        "calibrado": False,
        "n": 0,
        "etiqueta": None,
        "reason": "No hay curva de primas.",
    }

    try:
        if not curva or not curva.get("available"):
            return vacio

        valor = safe_int(precio)

        if valor <= 0:
            return {
                **vacio,
                "reason": "Sin precio no hay tramo.",
            }

        for tramo in (curva.get("tramos") or []):

            desde = safe_int(tramo.get("desde"))

            hasta = tramo.get("hasta")

            if valor < desde:
                continue

            if hasta is not None and valor >= safe_int(hasta):
                continue

            if tramo.get("calibrado"):
                return {
                    "percent": tramo.get("median_percent"),
                    "calibrado": True,
                    "n": safe_int(tramo.get("n")),
                    "etiqueta": tramo.get("etiqueta"),
                    "reason": (
                        f"Tramo {tramo.get('etiqueta')}: "
                        f"{tramo.get('median_percent'):+.2f} % "
                        f"sobre {tramo.get('n')} venta(s)."
                    ),
                }

            return {
                "percent": curva.get("global_percent"),
                "calibrado": False,
                "n": safe_int(tramo.get("n")),
                "etiqueta": tramo.get("etiqueta"),
                "reason": (
                    f"Tramo {tramo.get('etiqueta')} sin calibrar "
                    f"({tramo.get('n')} venta(s)): se usa la "
                    f"mediana global, "
                    f"{curva.get('global_percent')} %."
                ),
            }

        return {
            **vacio,
            "reason": f"{valor} no cae en ningun tramo.",
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": f"{type(error).__name__}: {error}",
        }


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
