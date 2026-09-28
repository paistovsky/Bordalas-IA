"""
La regla de la rampa: solo se compra para revender lo que SUBE.

LO QUE SE MIDIO (E1 del laboratorio, 28/09/2026)

    Todas las compras reales al Computer de los ocho managers, al
    precio que pagaron y saliendo el primer dia que el precio baja
    (n=191 con precio, 09/08 a 27/09):

        su precio subio el dia antes   n=109  57/73 verdes  +25.701.957
        su precio NO subio             n= 82  24/58 verdes     -567.940

    El precio de Biwenger tiene inercia: si subio hoy, manana sube
    el 92 % de las veces (n=5.338). Pollo17 y Luismi_Haz compran
    lo que sube (50/60 y 35/49). Pepe, 9 de 41.

LO QUE HACIA PEPE (bid_outcome_ledger, al 28/09)

    Las dos vias que compran para revender, mirando el precio de
    Biwenger 24 h antes de cada puja:

        subasta del reset (SUBASTA_CARTERA)  17 de 17 con el precio QUIETO
        carril (RENDIJA)                     14 de 17 BAJANDO, 3 quietos

    Ni una puja para revender a un jugador que subiera. La
    compuerta PRECIO_CAYENDO (market_rate_gate) no lo evita: la
    subasta no la mira, el carril la quito a proposito, y en
    cualquier caso lee el ritmo del ojeador, no el precio de
    Biwenger (doctrina 84: se comprobo antes de construir esto).

LA REGLA

    Un candidato para revender pasa solo si su ultimo cambio de
    precio en Biwenger fue una SUBIDA: `price_increment` > 0, que
    es el `priceIncrement` del catalogo y ya viaja en cada fila del
    tablero. Quieto o bajando, se frena. Sin el dato, se frena: no
    consta que suba (doctrina 103).

    Comprobado el 28/09 contra `price_history.json`: Zubeldia,
    -10.000 en los dos. Del tablero de ese dia, 34 de 67 suben: la
    regla no deja sin candidatos a ninguna via.

    Es la mitad de COMPRA de E1. La de VENTA (vender el primer dia
    que baja) va aparte, con su propio interruptor.

EL INTERRUPTOR

    `BORDALAS_COMPRA_SOLO_SI_SUBE`. Nace APAGADO: sin el, esto no
    frena ni una puja. El mismo interruptor manda en las dos vias,
    subasta del reset y carril, porque la regla es la misma y el
    dinero perdido tambien.

REGLA 23 Y DOCTRINA 50

    Ni disco, ni red, ni reloj: todo sale de la fila del candidato.
"""

from __future__ import annotations


ENV = "BORDALAS_COMPRA_SOLO_SI_SUBE"

SUBE = "SUBE"
QUIETO = "QUIETO"
BAJA = "BAJA"
SIN_DATO = "SIN_DATO"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def activa(interruptor: str = ENV) -> bool:
    """Si la regla manda. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(interruptor, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        # Un interruptor que no se puede leer no frena nada solo.
        return False


def direccion(fila) -> str:
    """Hacia donde fue su ultimo cambio de precio. Nunca lanza."""

    try:
        valor = (fila or {}).get("price_increment")

        if valor is None:
            return SIN_DATO

        valor = int(valor)

        if valor > 0:
            return SUBE

        if valor < 0:
            return BAJA

        return QUIETO

    except Exception:                               # noqa: BLE001
        return SIN_DATO


def mira_si_sube(
    candidatos: list | None,
    interruptor: str = ENV,
) -> dict:
    """
    Parte la lista en los que siguen y los que frena la regla.

    Forma fija. Nunca lanza. Con el interruptor apagado devuelve la
    lista entera en `siguen` y `frenados` vacio: el comportamiento
    de antes, al detalle.
    """

    salida = {
        "available": False,
        "activa": False,
        "siguen": list(candidatos or []),
        "frenados": [],
        "interruptor": interruptor,
        "reason": None,
    }

    try:
        if not activa(interruptor):
            return {
                **salida,
                "available": True,
                "reason": (
                    f"La regla de la rampa esta apagada ({interruptor} "
                    f"sin poner): pasan los {len(candidatos or [])}."
                ),
            }

        siguen = []
        frenados = []

        for fila in (candidatos or []):

            if not isinstance(fila, dict):
                continue

            sentido = direccion(fila)

            if sentido == SUBE:
                siguen.append(fila)
                continue

            frenados.append({
                "id": safe_int(fila.get("id") or fila.get("player_id")),
                "name": fila.get("name") or fila.get("player_name"),
                "direccion": sentido,
                "price_increment": fila.get("price_increment"),
                "reason": (
                    f"Su precio no sube ({sentido}): de los "
                    f"que compraron los ocho managers sin que subiera, "
                    f"24 de 58 viajes en verde y -567.940 en total; "
                    f"de los que subian, 57 de 73 y +25,7 M."
                ),
            })

        return {
            **salida,
            "available": True,
            "activa": True,
            "siguen": siguen,
            "frenados": frenados,
            "reason": (
                f"{interruptor} puesto: {len(frenados)} frenada(s) por "
                f"no subir su precio, {len(siguen)} siguen."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"No se pudo mirar la regla de la rampa: "
                f"{type(error).__name__}: {error}"
            ),
        }
