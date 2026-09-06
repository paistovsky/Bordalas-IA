"""
El marcador de los rivales: ¿acertaron comprando?

LA PREGUNTA (16/09/2026)

    Cuatro noches construyendo una maquina de valorar cada vez
    mejor. Cada noche la maquina concluye, con razon medida, que
    no hay que comprar nada. Mientras tanto Pollo compro siete
    jugadores por 21.198.020 EUR y va primero.

    Una de estas dos frases es verdad:

        A) Pepe tiene razon y Pollo esta tirando el dinero.
        B) El modelo es demasiado exigente y se esta perdiendo un
           mercado que si paga.

    Y se puede saber cual, porque esas compras tienen precio
    pagado y precio de mercado hoy.

LO QUE ESTE MODULO NO HACE

    No decide nada. Cuenta lo que paso: lo que se pago, lo que
    vale hoy, y cuantos dias han pasado.

    Y publica los DIAS, en primera fila, porque sin ellos el
    numero engaña: tres de las siete compras de Pollo son de esta
    misma mañana y su resultado no es un veredicto sobre la
    tesis, es la prima que pago sobre el mercado.

LA OTRA MITAD, QUE CASI SE NOS ESCAPA

    Pollo tambien VENDE. El 06/09 solto a Vinicius Jr por
    17.633.400 y el 04/09 a Foyth por 3.626.400: 21.259.800 EUR
    de ventas contra 21.198.020 de compras.

    O sea que no esta desplegando caja parada: esta ROTANDO. La
    lectura de "Pollo tiene ocho fichas mas y nosotros el dinero
    quieto" no sobrevive a mirarle las ventas.
"""

from __future__ import annotations

import statistics

from datetime import datetime


BUY = "BUY_FROM_COMPUTER"
SELL = "SELL_TO_COMPUTER"
TRANSFER = "USER_TRANSFER"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _prices_by_name(status: dict) -> dict:
    """
    El precio de HOY de cada jugador que este en alguna plantilla
    de la liga.

    Un jugador vendido al Computer desaparece de todas, asi que
    de esos no hay precio y se dice: `None` no es cero.
    """

    precios = {}

    for manager in (
        (status.get("rival_squads") or {}).get("managers") or []
    ):
        for jugador in (manager.get("players") or []):

            nombre = jugador.get("name")

            if nombre and safe_int(jugador.get("price")) > 0:
                precios[nombre] = {
                    "price": safe_int(jugador.get("price")),
                    "price_increment": safe_int(
                        jugador.get("price_increment")
                    ),
                    "owner": manager.get("name"),
                }

    return precios


def _feed(status: dict) -> list:
    return (
        (status.get("league_center") or {}).get("market_feed") or []
    )


def _dedupe(movimientos: list) -> list:
    """
    El tablon repite entradas.

    Se vio el 16/09: Mikel Rodriguez aparece TRES veces vendido
    por Luismi el mismo dia por el mismo importe, y Ayoze dos.
    Contarlas como ventas distintas triplicaria el marcador.
    """

    vistos = set()
    limpios = []

    for movimiento in movimientos:

        clave = (
            movimiento.get("type"),
            movimiento.get("player_id"),
            movimiento.get("amount"),
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        limpios.append(movimiento)

    return limpios


def manager_scoreboard(
    status: dict | None,
    manager: str,
    *,
    now: datetime | None = None,
) -> dict:
    """
    Lo que compro y vendio un manager, y como le ha ido.

    Nunca lanza.
    """

    try:
        estado = status or {}

        momento = now or datetime.fromisoformat(
            (estado.get("meta") or {}).get("generated_at")
            or datetime.now().isoformat()
        )

        precios = _prices_by_name(estado)

        compras = []
        ventas = []

        for movimiento in _dedupe(_feed(estado)):

            nombre = movimiento.get("player_name")
            importe = safe_int(movimiento.get("amount"))
            marca = movimiento.get("timestamp")

            if not nombre or importe <= 0 or not marca:
                continue

            dias = (
                momento - datetime.fromtimestamp(marca)
            ).total_seconds() / 86400.0

            fila = {
                "player": nombre,
                "amount": importe,
                "days": round(dias, 2),
                "at": datetime.fromtimestamp(marca).isoformat(),
            }

            if (
                movimiento.get("type") == BUY
                and manager in str(movimiento.get("buyer"))
            ):
                hoy = precios.get(nombre)

                fila.update(
                    {
                        "price_today": (
                            hoy["price"] if hoy else None
                        ),
                        "price_increment": (
                            hoy["price_increment"] if hoy else None
                        ),
                        "pnl": (
                            hoy["price"] - importe if hoy else None
                        ),
                        "pnl_percent": (
                            round(
                                (hoy["price"] - importe)
                                / importe
                                * 100,
                                2,
                            )
                            if hoy
                            else None
                        ),
                    }
                )

                compras.append(fila)

            elif (
                movimiento.get("type") in (SELL, TRANSFER)
                and manager in str(movimiento.get("seller"))
            ):
                hoy = precios.get(nombre)

                # Vendio bien si lo que cobro es MAS de lo que
                # vale hoy: se ahorro la caida.
                fila.update(
                    {
                        "price_today": (
                            hoy["price"] if hoy else None
                        ),
                        "avoided": (
                            importe - hoy["price"] if hoy else None
                        ),
                        "avoided_percent": (
                            round(
                                (importe - hoy["price"])
                                / importe
                                * 100,
                                2,
                            )
                            if hoy
                            else None
                        ),
                        "unmeasurable_reason": (
                            None
                            if hoy
                            else (
                                "Vendido al Computer: ya no esta en "
                                "ninguna plantilla de la liga, asi "
                                "que no hay precio de hoy con el "
                                "que compararlo."
                            )
                        ),
                    }
                )

                ventas.append(fila)

        medibles = [c for c in compras if c["pnl"] is not None]

        pagado = sum(c["amount"] for c in medibles)
        hoy_total = sum(c["price_today"] for c in medibles)

        subiendo = sum(
            1
            for c in medibles
            if (c.get("price_increment") or 0) > 0
        )

        return {
            "available": bool(compras or ventas),
            "manager": manager,

            "buys": sorted(compras, key=lambda c: -c["amount"]),
            "sells": sorted(ventas, key=lambda v: -v["amount"]),

            "bought_total": pagado,
            "worth_today": hoy_total,
            "pnl": hoy_total - pagado,
            "pnl_percent": (
                round((hoy_total - pagado) / pagado * 100, 2)
                if pagado
                else None
            ),

            "sold_total": sum(v["amount"] for v in ventas),

            "buys_measurable": len(medibles),
            "buys_total": len(compras),
            "rising_today": subiendo,

            # LO QUE MAS IMPORTA DE ESTA TABLA
            #
            #     Sin los dias, un -0,13 % parece un veredicto. Con
            #     ellos se ve que tres de las siete compras son de
            #     hace cinco horas.
            "median_days": (
                round(statistics.median([c["days"] for c in medibles]), 2)
                if medibles
                else None
            ),
            "min_days": (
                round(min(c["days"] for c in medibles), 2)
                if medibles
                else None
            ),
            "max_days": (
                round(max(c["days"] for c in medibles), 2)
                if medibles
                else None
            ),

            "reason": None,
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "manager": manager,
            "buys": [],
            "sells": [],
            "reason": (
                f"No se pudo montar el marcador: "
                f"{type(error).__name__}: {error}"
            ),
        }


def value_versus_points(status: dict | None) -> dict:
    """
    ¿Tener mas plantilla da mas puntos EN ESTA LIGA?

    La pregunta que hay debajo de las cuatro ultimas noches. Con
    siete managers no se puede contestar con seguridad, y decir
    eso es parte de la respuesta.

    El valor critico de r para n=7 con p<0,05 es 0,754. Por
    debajo, la correlacion no distingue de casualidad.
    """

    try:
        managers = [
            m
            for m in ((status or {}).get("race") or {}).get(
                "managers"
            )
            or []
            if safe_int(m.get("team_value")) > 0
        ]

        if len(managers) < 3:
            return {
                "available": False,
                "reason": "Menos de tres managers con plantilla.",
            }

        puntos = [safe_int(m.get("points")) for m in managers]
        valor = [safe_int(m.get("team_value")) for m in managers]
        fichas = [safe_int(m.get("squad_size")) for m in managers]

        def correlacion(xs, ys):
            mx = statistics.fmean(xs)
            my = statistics.fmean(ys)

            numerador = sum(
                (x - mx) * (y - my) for x, y in zip(xs, ys)
            )

            denominador = (
                sum((x - mx) ** 2 for x in xs)
                * sum((y - my) ** 2 for y in ys)
            ) ** 0.5

            return numerador / denominador if denominador else 0.0

        r_valor = correlacion(valor, puntos)
        r_fichas = correlacion(fichas, puntos)

        # Valor critico de Pearson, dos colas, p<0,05.
        CRITICOS = {
            3: 0.997, 4: 0.950, 5: 0.878, 6: 0.811, 7: 0.754,
            8: 0.707, 9: 0.666, 10: 0.632,
        }

        critico = CRITICOS.get(len(managers), 0.6)

        return {
            "available": True,
            "managers": len(managers),

            "r_value_points": round(r_valor, 3),
            "r_squad_size_points": round(r_fichas, 3),

            "critical_r": critico,
            "significant": bool(abs(r_valor) >= critico),

            "reason": (
                f"r = {r_valor:+.3f} entre valor de plantilla y "
                f"puntos, sobre {len(managers)} managers. Para que "
                f"eso distinga de casualidad con esta muestra hace "
                f"falta {critico:.3f}."
                + (
                    " Lo alcanza."
                    if abs(r_valor) >= critico
                    else " No lo alcanza: con esta liga y esta "
                    "muestra, tener mas plantilla NO predice mas "
                    "puntos."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo correlacionar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def build_scoreboard(
    status: dict | None,
    managers=("Pollo17", "Luismi_Haz"),
) -> dict:
    """
    El bloque entero para el dashboard.
    """

    try:
        marcadores = {
            nombre: manager_scoreboard(status, nombre)
            for nombre in managers
        }

        return {
            "available": any(
                m.get("available") for m in marcadores.values()
            ),
            "observer_only": True,
            "managers": marcadores,
            "value_versus_points": value_versus_points(status),
            "caveat": (
                "Los dias importan mas que el porcentaje. Una "
                "compra de hace cinco horas no dice nada de la "
                "tesis: dice la prima que se pago."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "managers": {},
            "reason": (
                f"{type(error).__name__}: {error}"
            ),
        }
