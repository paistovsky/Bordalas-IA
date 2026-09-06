"""
La porteria nunca se queda a uno.

LA REGLA 3, Y POR QUE NO EXISTIA

    Tenemos UN portero. Si Dituro se lesiona, descansa o ve dos
    amarillas, salimos con diez y esa jornada esta perdida.

    No habia ninguna regla que lo impidiera: simplemente no se le
    ocurrio a nadie. Es el tipo de agujero que solo aparece
    cuando alguien pregunta "¿y esto quien lo cubre?".

EL AJUSTE A NUESTRA LIGA, QUE NO ES DESOBEDECER

    El video pide "los dos porteros del mismo club" -Courtois y
    Lunin- y lo justifica por la escasez en ligas de 18
    managers. La nuestra tiene siete y hay porteros de sobra.

    Asi que lo innegociable es NO QUEDARSE NUNCA CON UNO. Los dos
    del mismo club se publica como opcion cuando exista y quepa,
    pero no es regla: son dos fichas para una plaza.

LO QUE ESTE MODULO HACE Y NO HACE

    Dice si la porteria esta descubierta, cual es el mejor
    segundo portero alcanzable hoy con la caja que hay, y cual se
    abriria vendiendo al primero de la cola de ventas.

    No compra. Publica y decide el dueño.

Y LO QUE SOBREVIVE DE LOS INTOCABLES

    La lista de intocables se derogo el 21/09, pero el portero
    titular sigue sin poder venderse. Eso nunca fue una lista de
    nombres: es la misma barandilla que esta regla, mirada desde
    el otro lado.
"""

from __future__ import annotations


PORTERO = 1


# Con menos de esto la porteria esta descubierta. No es una
# preferencia: es que el once no se puede rellenar.
MINIMO_PORTEROS = 2


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _vacio(motivo: str) -> dict:
    return {
        "available": False,
        "keepers": 0,
        "uncovered": None,
        "minimum": MINIMO_PORTEROS,
        "best_now": None,
        "best_after_sale": None,
        "same_club_option": None,
        "options": [],
        "priority": None,
        "reason": motivo,
    }


def estado_de_la_porteria(
    roster: list | None,
    targets: list | None,
    cash: int = 0,
    sale_queue: list | None = None,
) -> dict:
    """
    ¿Esta cubierta la porteria, y con que se cubriria hoy?

    Nunca lanza. Forma fija. No compra nada.
    """

    try:
        plantilla = [
            p for p in (roster or []) if isinstance(p, dict)
        ]

        if not plantilla:
            return _vacio(
                "Sin plantilla: no se puede saber cuantos "
                "porteros hay."
            )

        porteros = [
            p
            for p in plantilla
            if safe_int(p.get("position")) == PORTERO
        ]

        descubierta = len(porteros) < MINIMO_PORTEROS

        # Los clubes de nuestros porteros, para la opcion del
        # video: titular y suplente del mismo equipo.
        clubes = {
            str(p.get("team_name") or p.get("team"))
            for p in porteros
        }

        candidatos = []

        for objetivo in (targets or []):

            if safe_int(objetivo.get("position")) != PORTERO:
                continue

            precio = safe_int(objetivo.get("market_price"))

            candidatos.append({
                "id": safe_int(objetivo.get("id")),
                "name": objetivo.get("name"),
                "team": objetivo.get("team"),
                "price": precio,
                "starter_probability": safe_float(
                    objetivo.get("starter_probability")
                ),
                "fits_now": bool(precio and precio <= cash),
                "leaves": cash - precio if precio else None,
                "same_club": bool(
                    str(objetivo.get("team")) in clubes
                ),
            })

        # Mejor = el mas probable de jugar; a igualdad, el mas
        # barato. Un segundo portero que tampoco juega no cubre
        # gran cosa, pero evita salir con diez.
        candidatos.sort(
            key=lambda c: (
                -(c["starter_probability"] or 0),
                c["price"],
            )
        )

        alcanzables = [c for c in candidatos if c["fits_now"]]

        mejor_ahora = alcanzables[0] if alcanzables else None

        # Lo que se abriria vendiendo al primero de la cola.
        primero = None

        for fila in (sale_queue or []):
            if isinstance(fila, dict) and safe_int(
                fila.get("price")
            ):
                primero = fila
                break

        caja_tras_venta = cash + safe_int(
            (primero or {}).get("price")
        )

        tras_venta = [
            c
            for c in candidatos
            if c["price"] and c["price"] <= caja_tras_venta
        ]

        mejor_tras_venta = tras_venta[0] if tras_venta else None

        mismo_club = next(
            (c for c in candidatos if c["same_club"]),
            None,
        )

        return {
            "available": True,
            "keepers": len(porteros),
            "uncovered": descubierta,
            "minimum": MINIMO_PORTEROS,

            "best_now": mejor_ahora,
            "best_after_sale": (
                {
                    **mejor_tras_venta,
                    "selling": (primero or {}).get("name"),
                    "raises": safe_int(
                        (primero or {}).get("price")
                    ),
                }
                if mejor_tras_venta and primero
                else None
            ),
            "same_club_option": mismo_club,

            "options": candidatos,

            # LA REGLA: si la porteria esta descubierta, el
            # segundo portero sube al principio de la cola, por
            # encima de cualquier operacion de cartera.
            "priority": (
                "PRIMERA"
                if descubierta
                else "NORMAL"
            ),

            "reason": _reason(
                len(porteros),
                descubierta,
                mejor_ahora,
                mejor_tras_venta,
                primero,
                cash,
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo mirar la porteria: "
            f"{type(error).__name__}: {error}"
        )


def _reason(
    cuantos,
    descubierta,
    mejor,
    tras_venta,
    primero,
    cash,
) -> str:

    if not descubierta:
        return (
            f"{cuantos} porteros en plantilla: la porteria esta "
            f"cubierta."
        )

    frase = (
        f"UN SOLO PORTERO. Si no juega, se sale con diez y esa "
        f"jornada esta perdida. Fichar el segundo va por delante "
        f"de cualquier operacion de cartera."
    )

    if mejor:
        euros = f"{mejor['price']:,}".replace(",", ".")
        resto = f"{mejor['leaves']:,}".replace(",", ".")

        frase += (
            f" Hoy cabe {mejor['name']} por {euros} EUR, dejando "
            f"{resto}."
        )

        if (mejor["starter_probability"] or 0) < 50:
            frase += (
                f" Aviso: titularidad "
                f"{mejor['starter_probability']} %, o sea tercer "
                f"portero. Cubre el salir con diez, no la jornada."
            )

    elif tras_venta and primero:
        euros = f"{tras_venta['price']:,}".replace(",", ".")

        frase += (
            f" Con la caja de hoy no cabe ninguno; vendiendo a "
            f"{primero.get('name')} si cabria "
            f"{tras_venta['name']} por {euros} EUR."
        )

    else:
        disponible = f"{cash:,}".replace(",", ".")

        frase += (
            f" Y hoy no hay ningun portero alcanzable con "
            f"{disponible} EUR: no es una decision, es una "
            f"restriccion."
        )

    return frase
