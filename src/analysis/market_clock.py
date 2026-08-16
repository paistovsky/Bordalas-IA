"""
Reloj del mercado de Biwenger.

POR QUE EXISTE
    Bordalas IA conocia un solo reloj: el deadline de jornada
    (T-15 antes del primer partido). Pero la operativa diaria
    depende de OTRO reloj distinto, el reset del Computer, y el
    sistema no lo veia.

    El 16/08/2026 el mercado cerro a las 07:00 y Pepe siguio
    analizando a Tenaglia durante horas sin saber que la ventana
    de pujas ya se habia cerrado.

QUE PASA EN EL RESET (entre las 05:00 y las 07:00)
    1. Se ejecutan las pujas: quien haya pujado mas alto se lleva
       al jugador. Es una subasta a ciegas y de un solo intento.
    2. El Computer hace una oferta por CADA jugador publicado en
       el mercado. El importe es aleatorio.
    3. Se renueva el mercado: desaparecen los no fichados y entra
       una lista nueva de jugadores libres.

CONSECUENCIAS OPERATIVAS
    - Pujar despues del reset no sirve: hay que hacerlo antes.
    - Publicar jugadores antes del reset es lo que genera las
      ofertas del Computer, que a su vez son la liquidez y el
      margen de deuda. Cada jugador publicado es un boleto mas.
    - Vender para sanear tiene un plazo distinto y mas largo: el
      deadline de jornada.

COMO SE CALCULA
    De los datos, no de una constante. Los jugadores del Computer
    comparten todos el mismo `until`, que es justo el instante del
    proximo reset. Si Biwenger cambia la hora, el reloj la sigue
    sin tocar codigo.

    Verificado contra snapshot real del 16/08/2026: 20 ventas del
    Computer con until identico (1786856400), 33 de rivales con
    until individual a 48 h. Solo las del Computer sirven.

    Solo si no hay jugadores del Computer en el snapshot se
    recurre a la hora habitual como respaldo.

DATO CADUCADO
    Si el `until` del Computer ya paso, el snapshot es anterior al
    corte: el mercado que contiene ya no existe. El reloj apunta
    al reset siguiente y marca listings_stale, porque pujar sobre
    esa lista seria pujar por jugadores que ya no estan.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone


# Hora habitual del reset, solo como respaldo.
FALLBACK_RESET_HOUR_UTC = 5

# Ventanas de aviso, en segundos.
CRITICAL_SECONDS = 60 * 60          # 1 h
CLOSING_SECONDS = 3 * 60 * 60       # 3 h


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def is_computer_sale(sale: dict) -> bool:
    """
    Una venta del Computer no tiene vendedor.

    Las de los rivales llevan `user` con su id, y su `until` es
    individual -48 h desde que la publicaron-, asi que no sirve
    para deducir el reset.
    """

    vendedor = sale.get("user")

    if isinstance(vendedor, dict):
        return vendedor.get("id") is None

    return vendedor is None


def computer_sales(snapshot: dict) -> list:
    mercado = snapshot.get("market") or {}
    ventas = mercado.get("sales") or []

    return [
        venta
        for venta in ventas
        if isinstance(venta, dict)
        and is_computer_sale(venta)
    ]


def computer_reset_epoch(
    snapshot: dict,
) -> tuple[int | None, str]:
    """
    Instante del proximo reset, deducido de los datos.

    Devuelve (epoch, origen).
    """

    expiraciones = [
        safe_int(venta.get("until"))
        for venta in computer_sales(snapshot)
        if safe_int(venta.get("until")) > 0
    ]

    if not expiraciones:
        return (None, "SIN_MERCADO_COMPUTER")

    # Todos los del Computer comparten instante. Se coge el mas
    # repetido por si alguno viene con ruido.
    mas_comun, repeticiones = (
        Counter(expiraciones).most_common(1)[0]
    )

    origen = (
        "COMPUTER_LISTINGS"
        if repeticiones >= 2
        else "COMPUTER_LISTINGS_UNICO"
    )

    return (mas_comun, origen)


def fallback_reset_epoch(
    ahora: datetime,
) -> int:
    """
    Respaldo cuando no hay mercado del Computer que mirar.
    """

    candidato = ahora.replace(
        hour=FALLBACK_RESET_HOUR_UTC,
        minute=0,
        second=0,
        microsecond=0,
    )

    if candidato <= ahora:
        candidato = candidato + timedelta(days=1)

    return int(candidato.timestamp())


def _ultimo_domingo(
    ano: int,
    mes: int,
) -> datetime:
    """
    Ultimo domingo del mes, a las 00:00 UTC.
    """

    if mes == 12:
        primero_siguiente = datetime(
            ano + 1, 1, 1, tzinfo=timezone.utc
        )
    else:
        primero_siguiente = datetime(
            ano, mes + 1, 1, tzinfo=timezone.utc
        )

    ultimo_dia = primero_siguiente - timedelta(days=1)

    # weekday(): lunes 0 ... domingo 6.
    return ultimo_dia - timedelta(
        days=(ultimo_dia.weekday() + 1) % 7
    )


def madrid_offset_hours(
    momento_utc: datetime,
) -> int:
    """
    Desfase de Madrid respecto a UTC: +1 en invierno, +2 en verano.

    Se calcula con la regla europea en vez de con `zoneinfo`
    porque Windows no trae base de datos de zonas horarias. El
    16/08/2026 esto hizo que el reset de las 07:00 se imprimiera
    como 05:00 en el PC y como 07:00 en GitHub Actions: el mismo
    codigo dando dos horas distintas segun donde corriera.

    La regla de la UE es ley y no cambia: el horario de verano
    empieza el ultimo domingo de marzo a la 01:00 UTC y termina
    el ultimo domingo de octubre a la 01:00 UTC.

    Solo vale para la peninsula. Canarias va una hora menos.
    """

    inicio_verano = _ultimo_domingo(
        momento_utc.year, 3
    ).replace(hour=1)

    fin_verano = _ultimo_domingo(
        momento_utc.year, 10
    ).replace(hour=1)

    if inicio_verano <= momento_utc < fin_verano:
        return 2

    return 1


def _hora_local(epoch: int) -> str:
    """
    El usuario piensa en hora de Madrid, no en UTC.
    """

    momento = datetime.fromtimestamp(
        epoch,
        tz=timezone.utc,
    )

    local = momento + timedelta(
        hours=madrid_offset_hours(momento)
    )

    return local.strftime("%d/%m %H:%M")


def build_market_clock(
    snapshot: dict,
    now_ts: int | None = None,
) -> dict:
    """
    Estado del reloj de mercado.

    Nunca lanza: si no puede determinar nada devuelve
    window_state = UNKNOWN y el resto en None. Un fallo del reloj
    no puede detener un ciclo.
    """

    try:
        ahora = (
            datetime.fromtimestamp(
                now_ts,
                tz=timezone.utc,
            )
            if now_ts is not None
            else datetime.now(timezone.utc)
        )

        ahora_ts = int(ahora.timestamp())

        reset, origen = computer_reset_epoch(snapshot)

        if reset is None:
            reset = fallback_reset_epoch(ahora)
            origen = "FALLBACK_DIARIO"

        segundos = reset - ahora_ts

        # Un reset ya pasado significa que el snapshot es de antes
        # del corte. El mercado que trae ya no existe: se renovo.
        caducado = segundos < 0

        while segundos < 0:
            reset = int(
                (
                    datetime.fromtimestamp(
                        reset,
                        tz=timezone.utc,
                    )
                    + timedelta(days=1)
                ).timestamp()
            )
            segundos = reset - ahora_ts

        if segundos <= CRITICAL_SECONDS:
            estado = "CRITICAL"

        elif segundos <= CLOSING_SECONDS:
            estado = "CLOSING_SOON"

        else:
            estado = "OPEN"

        listado = computer_sales(snapshot)

        # Se puede pujar mientras no haya llegado el reset. Lo que
        # invalida la operativa no es la hora, es tener delante un
        # mercado que ya no existe.
        pujas_utiles = not caducado

        if caducado:
            motivo = (
                "Snapshot anterior al ultimo reset: el mercado que "
                "contiene ya se renovo. No se puede pujar sobre "
                f"esta lista. Proximo reset {_hora_local(reset)}."
            )

        else:
            motivo = (
                f"Quedan {segundos // 3600}h "
                f"{(segundos % 3600) // 60}m para el reset "
                f"({_hora_local(reset)} hora de Madrid)."
            )

        return {
            "available": True,
            "next_reset_epoch": reset,
            "next_reset_iso": datetime.fromtimestamp(
                reset,
                tz=timezone.utc,
            ).isoformat(),
            "next_reset_local": _hora_local(reset),
            "seconds_to_reset": segundos,
            "hours_to_reset": round(segundos / 3600.0, 2),
            "window_state": estado,
            "source": origen,
            "listings_stale": caducado,
            "computer_listings": len(listado),
            "bidding_window_open": pujas_utiles,
            "must_publish_before_reset": pujas_utiles,
            "reason": motivo,
        }

    except Exception as error:
        return {
            "available": False,
            "next_reset_epoch": None,
            "next_reset_iso": None,
            "next_reset_local": None,
            "seconds_to_reset": None,
            "hours_to_reset": None,
            "window_state": "UNKNOWN",
            "source": "ERROR",
            "listings_stale": False,
            "computer_listings": 0,
            "bidding_window_open": True,
            "must_publish_before_reset": True,
            "reason": f"{type(error).__name__}: {error}",
        }


def print_market_clock(
    clock: dict,
) -> None:

    print()
    print("-" * 70)
    print("RELOJ DE MERCADO")
    print("-" * 70)

    if not clock.get("available"):
        print(f"  No disponible: {clock.get('reason')}")
        return

    print(
        f"  Proximo reset Computer:  "
        f"{clock.get('next_reset_local')} (Madrid)"
    )
    print(
        f"  Tiempo restante:         "
        f"{clock.get('hours_to_reset')} h"
    )
    print(
        f"  Ventana:                 "
        f"{clock.get('window_state')}"
    )
    print(
        f"  Jugadores del Computer:  "
        f"{clock.get('computer_listings')}"
    )
    print(
        f"  Origen del dato:         "
        f"{clock.get('source')}"
    )
    print(f"  {clock.get('reason')}")

    if clock.get("listings_stale"):
        print()
        print(
            "  AVISO: el mercado de este snapshot ya caduco. Las "
            "pujas sobre esta lista no valen para nada."
        )

    elif clock.get("window_state") == "CRITICAL":
        print()
        print(
            "  AVISO: queda menos de una hora. Las pujas que no "
            "esten puestas se pierden, y lo que no este publicado "
            "no recibira oferta del Computer."
        )
