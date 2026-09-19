"""
No se escribe dos veces la misma operacion.

EL CASO, MEDIDO EL 19/09/2026

    Sobre los libros de escrituras reales -los que llevan `sent`
    y `http_status`, o sea lo que de verdad salio contra
    Biwenger-:

        familia               escrituras  operaciones  desperdicio
        puja                       16          4          75,0 %
        publicar                   16          1          93,8 %
        renovar publicacion        11          9          18,2 %

    Maffeo, nueve pujas en 8,9 h, cada una con su id de Biwenger
    distinto. Trent, DIECISEIS publicaciones al mismo precio en
    8,1 h, todas HTTP 204.

    Con una escritura por vuelta eso no es ruido: es que Pepe
    opera a una accion cada cuatro horas en vez de una por hora.

EL FALLO, CON NOMBRE

    No es que nadie sepa que hay una puja viva. `acquisition_board`
    LO CALCULA por fila -`has_live_bid`, `live_bid`-, lo publica
    en `targets`, lo usa para ordenar (las filas con puja viva se
    mandan al final) y lo descuenta de `actionable`.

    Y ademas las METE A PROPOSITO en `targets`, para que la
    pantalla pueda ensenar nuestro propio dinero.

    El carril recibe esas mismas filas y las filtra por tres
    cosas -`market_price >= suelo`, `status == "ok"`,
    `not outside_computer_market`- y por ninguna mas. El campo
    viaja intacto hasta la linea de la escritura y nadie lo mira.

    Asi que no es "pregunta y le contestan tarde": es que EN EL
    CAMINO DE ESCRITURA NO SE PREGUNTA. La respuesta ya venia
    dentro de la fila.

Y EL SEGUNDO FALLO, QUE ESTABA DEBAJO

    `has_live_bid` sale de `puja_viva`, que se llena de
    `exposicion["operations"]`. Si la exposicion no esta
    disponible, ese diccionario queda VACIO y todas las filas
    salen `has_live_bid: False`.

    O sea: "no hay pujas vivas" y "no he podido mirar" se
    escriben igual. Un fallo de lectura se lee como permiso.

    Por eso esta guardia distingue las dos cosas y, cuando no
    puede mirar, NO DEJA ESCRIBIR. Ausencia de dato no es dato.

DOCTRINA 84: `players_with_live_bid()` YA EXISTE

    Vive en `decision_orchestrator` desde que se escribio para
    esto mismo, y nunca la llamo nadie desde el camino de
    escritura. Aqui se USA, no se reescribe. Lo unico que se
    anade es el detalle -que oferta y por cuanto- porque el
    motivo tiene que nombrar a quien decidio (doctrina 87).

ENTREGADA APAGADA

    `BORDALAS_NO_REPETIR_LA_ESCRITURA`. Apagada, el
    comportamiento es el de siempre.
"""

from __future__ import annotations

import os


GUARDIA_ENV = "BORDALAS_NO_REPETIR_LA_ESCRITURA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def guardia_activa() -> bool:
    """
    Si la guardia esta encendida. Forma fija, nunca lanza.
    """

    return str(
        os.environ.get(GUARDIA_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def lo_que_ya_esta_puesto(speculation: dict | None) -> dict:
    """
    Por que jugadores tenemos YA una escritura viva, y cual.

    Se apoya en `players_with_live_bid()` para el conjunto
    -doctrina 84, ya existia- y recorre las mismas operaciones
    para quedarse con el detalle que hace falta para explicar un
    freno: la oferta y su importe.

    LA DIFERENCIA ENTRE "NO HAY" Y "NO SE SABE"

        `available: False` significa que no se ha podido mirar.
        Quien llame NO debe escribir en ese caso. Es lo contrario
        de lo que hace hoy el tablero, donde una exposicion
        ausente produce un diccionario vacio que se lee como "via
        libre".

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "por_jugador": {},
        "cuantos": 0,
        "reason": None,
    }

    try:
        datos = speculation if isinstance(speculation, dict) else {}

        exposicion = datos.get("bid_exposure")

        if not isinstance(exposicion, dict):
            return {
                **vacio,
                "reason": (
                    "No viaja `bid_exposure`: no se puede saber "
                    "que tenemos puesto, y sin saberlo no se "
                    "escribe."
                ),
            }

        if not exposicion.get("available"):
            return {
                **vacio,
                "reason": (
                    "La exposicion de pujas no esta disponible"
                    + (
                        f" ({exposicion.get('reason')})"
                        if exposicion.get("reason")
                        else ""
                    )
                    + ": no se sabe que tenemos puesto. Un fallo "
                    "de lectura no es via libre."
                ),
            }

        # DOCTRINA 84: el conjunto sale de la que ya existe.
        from src.analysis.decision_orchestrator import (
            players_with_live_bid,
        )

        ocupados = players_with_live_bid(datos)

        detalle = {}

        for operacion in (exposicion.get("operations") or []):

            if not isinstance(operacion, dict):
                continue

            for jugador in (operacion.get("player_ids") or []):

                pid = safe_int(jugador)

                if pid <= 0:
                    continue

                detalle[pid] = {
                    "offer_id": operacion.get("offer_id"),
                    "amount": safe_int(operacion.get("amount")),
                    "status": operacion.get("status"),
                    "created": operacion.get("created"),
                }

        # Lo que diga `players_with_live_bid` manda: si ella ve un
        # jugador y aqui no hay detalle, sigue ocupado.
        for pid in ocupados:
            detalle.setdefault(
                safe_int(pid),
                {
                    "offer_id": None,
                    "amount": 0,
                    "status": None,
                    "created": None,
                },
            )

        return {
            "available": True,
            "por_jugador": detalle,
            "cuantos": len(detalle),
            "reason": (
                f"Tenemos {len(detalle)} operacion(es) viva(s)."
                if detalle
                else "No tenemos ninguna operacion viva."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar que tenemos puesto: "
                f"{type(error).__name__}: {error}"
            ),
        }


def filtrar_los_repetidos(
    candidatos: list | None,
    speculation: dict | None,
    *,
    clave_id: str = "player_id",
    clave_nombre: str = "name",
) -> dict:
    """
    Separa los que se pueden escribir de los que ya estan puestos.

    EL MOTIVO NOMBRA AL QUE DECIDIO (doctrina 87)

        Cada frenado sale con el jugador Y el id de la operacion
        viva que lo paro. Un "ya estaba puesto" sin decir cual no
        se puede comprobar, y el dia que este mal nadie lo vera.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "escribibles": [],
        "frenados": [],
        "reason": None,
    }

    try:
        filas = [
            c for c in (candidatos or []) if isinstance(c, dict)
        ]

        puestas = lo_que_ya_esta_puesto(speculation)

        if not puestas["available"]:
            # NO SE SABE: no se escribe nada. El lado seguro de
            # no poder mirar es no tocar el mercado.
            return {
                "available": False,
                "escribibles": [],
                "frenados": [
                    {
                        "player_id": safe_int(c.get(clave_id)),
                        "name": c.get(clave_nombre),
                        "offer_id": None,
                        "amount": 0,
                        "motivo": "NO_SE_SABE",
                        "reason": puestas["reason"],
                    }
                    for c in filas
                ],
                "reason": puestas["reason"],
            }

        por_jugador = puestas["por_jugador"]

        escribibles = []

        frenados = []

        for candidato in filas:

            pid = safe_int(candidato.get(clave_id))

            viva = por_jugador.get(pid)

            if not viva:
                escribibles.append(candidato)
                continue

            nombre = candidato.get(clave_nombre) or pid

            importe = viva.get("amount") or 0

            frenados.append({
                "player_id": pid,
                "name": candidato.get(clave_nombre),
                "offer_id": viva.get("offer_id"),
                "amount": importe,
                "motivo": "YA_ESTA_PUESTA",
                "reason": (
                    f"Ya hay una operacion viva por {nombre}: "
                    f"oferta {viva.get('offer_id') or 'sin id'}"
                    + (
                        f" por {importe:,} EUR".replace(",", ".")
                        if importe
                        else ""
                    )
                    + ". No se escribe otra."
                ),
            })

        return {
            "available": True,
            "escribibles": escribibles,
            "frenados": frenados,
            "reason": (
                f"{len(escribibles)} para escribir, "
                f"{len(frenados)} frenada(s) por estar ya puesta(s)."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo filtrar: "
                f"{type(error).__name__}: {error}"
            ),
        }
