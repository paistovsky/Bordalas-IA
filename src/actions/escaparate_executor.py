"""
El escaparate: al recien comprado se le pone precio y se publica.

QUE FALTABA

    La mitad que COBRA -`salida_del_viaje`- llevaba un dia
    escrita y apagada porque no habia nada que cobrar. Un viaje
    que no esta en venta no recibe ofertas, asi que nunca podia
    empezar a cerrarse.

    Esto es la puerta de entrada: al GANAR una puja de la
    rendija, el jugador se marca VIAJE y se lista EN LA MISMA
    VUELTA.

POR QUE EN LA MISMA VUELTA Y NO EN LA SIGUIENTE

    Una publicacion vive 48 h y el mercado se resuelve a las
    07:00. Cada vuelta que un viaje pasa sin listar es una tanda
    de ofertas que no llega. Con el ciclo horario, esperar a la
    vuelta siguiente es tirar una hora de escaparate de las 48.

EL PRECIO

        pedir = valor de mercado x 1,15

    Es la misma regla de renovar. Alli va envuelta en un
    `max(precio_actual, valor x 1,15)` porque renovar NUNCA puede
    bajar un precio puesto a proposito -la leccion de Yamal, que
    habria pasado de 32,16 M a 24,75 M-. Aqui el `max()` se
    resuelve solo: un recien comprado no tiene precio anterior
    que proteger.

EL COSTE NO SE RECONSTRUYE

    Sale de `owner.price` de la API, que cuadra con el tablon al
    euro en 9 de 9 comparables. El libro de viajes solo guarda
    QUIEN es un viaje; cuanto costo se pregunta.

APAGADO

    `en_vivo=False` es el defecto, como en las otras dos rutas
    que escriben.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


LIBRO = Path("data") / "trading" / "libro_de_escaparate.jsonl"

# La misma que renovar. No es un umbral nuevo: es el mismo, y si
# algun dia se mueve se mueve en los dos sitios a la vez.
from src.analysis.renovar_ofertas import (                # noqa: E402
    PRIMA_DE_LA_PETICION,
)


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def apuntar(fila: dict, ruta: Path | None = None) -> bool:
    destino = ruta or LIBRO

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)

        with destino.open("a", encoding="utf-8") as fichero:
            fichero.write(
                json.dumps(fila, ensure_ascii=False) + "\n"
            )

        return True

    except Exception:                               # noqa: BLE001
        return False


def precio_de_escaparate(valor_de_mercado) -> int:
    """
    Lo que se pide por un recien comprado.

    Sin valor de mercado NO se inventa un precio: se devuelve 0 y
    quien llama se abstiene. Publicar a un precio deducido de la
    nada es peor que no publicar.
    """

    valor = safe_int(valor_de_mercado)

    if valor <= 0:
        return 0

    return int(round(valor * PRIMA_DE_LA_PETICION))


def que_publicar(
    ganadas: list | None,
    plantilla: list | None = None,
    ya_listados: list | None = None,
) -> dict:
    """
    Que pujas ganadas hay que marcar y listar. Forma fija.

    `ganadas` son las operaciones de la rendija que el reset ha
    resuelto a nuestro favor. `plantilla` da el precio de mercado
    y el coste.
    """

    vacio = {
        "available": False,
        "publicar": [],
        "saltados": [],
        "reason": None,
    }

    try:
        filas = [
            g for g in (ganadas or []) if isinstance(g, dict)
        ]

        if not filas:
            return {
                **vacio,
                "available": True,
                "reason": (
                    "Ninguna puja de la rendija ganada en este "
                    "reset."
                ),
            }

        por_id = {
            safe_int(f.get("id")): f
            for f in (plantilla or [])
            if isinstance(f, dict)
        }

        en_venta = {
            safe_int(x.get("player_id") or x.get("id"))
            for x in (ya_listados or [])
            if isinstance(x, dict)
        }

        publicar = []

        saltados = []

        def _saltar(fila, motivo):
            saltados.append(
                {
                    "player_id": safe_int(fila.get("player_id")),
                    "name": fila.get("name"),
                    "reason": motivo,
                }
            )

        for fila in filas:

            pid = safe_int(fila.get("player_id"))

            if pid <= 0:
                _saltar(fila, "Sin `player_id`.")
                continue

            ficha = por_id.get(pid) or {}

            nombre = (
                fila.get("name") or ficha.get("name") or pid
            )

            # NO ESTA EN PLANTILLA: la puja no se gano, o el
            # reset aun no la ha resuelto. No se marca nada.
            if not ficha:
                _saltar(
                    fila,
                    (
                        f"{nombre} no esta en la plantilla: la "
                        f"puja no se ha resuelto a nuestro favor."
                    ),
                )
                continue

            if pid in en_venta:
                _saltar(
                    fila,
                    f"{nombre} ya esta publicado.",
                )
                continue

            precio = precio_de_escaparate(ficha.get("price"))

            if precio <= 0:
                _saltar(
                    fila,
                    (
                        f"{nombre} no tiene valor de mercado: no "
                        f"se publica a un precio inventado."
                    ),
                )
                continue

            publicar.append(
                {
                    "player_id": pid,
                    "name": ficha.get("name") or fila.get("name"),
                    "position": safe_int(ficha.get("position")),
                    "market_price": safe_int(ficha.get("price")),
                    "listed_price": precio,
                    "cost": safe_int(
                        ficha.get("acquisition_cost")
                        or ficha.get("owner_price")
                    ),
                }
            )

        return {
            "available": True,
            "publicar": publicar,
            "saltados": saltados,
            "reason": (
                f"{len(publicar)} para publicar"
                + (
                    f", {len(saltados)} saltados"
                    if saltados
                    else ""
                )
                + "."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo preparar el escaparate: "
                f"{type(error).__name__}: {error}"
            ),
        }


def publicar(
    filas: list | None,
    escritor=None,
    en_vivo: bool = False,
    ruta_del_libro: Path | None = None,
    ruta_de_viajes: Path | None = None,
) -> dict:
    """
    Marca VIAJE y lista. Nunca lanza.

    EL ORDEN IMPORTA: primero se marca, luego se lista.

        Si se listara primero y el marcado fallara, quedaria un
        jugador en venta al que la ruta del viaje no reconoce:
        lo juzgaria el motor de ofertas de siempre, con la
        pregunta equivocada.

        Marcando primero, el peor caso es un viaje marcado y sin
        listar — y de eso hay guardia que lo saca en ROJO en la
        portada.
    """

    from src.analysis import libro_de_viajes

    salida = {
        "available": False,
        "executed": False,
        "listed": [],
        "failed": [],
        "reason": None,
    }

    pendientes = [
        f for f in (filas or []) if isinstance(f, dict)
    ]

    if not pendientes:
        return {
            **salida,
            "available": True,
            "reason": "Nada que publicar.",
        }

    if escritor is None:
        from src.biwenger.write_client import (
            BiwengerWriteClient,
        )

        escritor = BiwengerWriteClient()

    listados = []

    fallidos = []

    for fila in pendientes:

        pid = safe_int(fila.get("player_id"))

        precio = safe_int(fila.get("listed_price"))

        if pid <= 0 or precio <= 0:
            fallidos.append(
                {
                    "name": fila.get("name"),
                    "error": "Sin id o sin precio no se publica.",
                }
            )
            continue

        marca = libro_de_viajes.abrir(
            player_id=pid,
            name=fila.get("name"),
            position=fila.get("position"),
            ruta=ruta_de_viajes,
        )

        if not marca.get("available"):
            fallidos.append(
                {
                    "name": fila.get("name"),
                    "error": (
                        f"No se pudo marcar VIAJE: "
                        f"{marca.get('reason')}"
                    ),
                }
            )
            continue

        try:
            # LA UNICA ESCRITURA DE ESTE FICHERO.
            resultado = escritor.list_player_for_sale(
                player_id=pid,
                price=precio,
                execute=bool(en_vivo),
            )

            anotacion = {
                "at": _ahora(),
                "player_id": pid,
                "player_name": fila.get("name"),
                "market_price": safe_int(fila.get("market_price")),
                "listed_price": precio,
                "cost": safe_int(fila.get("cost")),
                "margen": PRIMA_DE_LA_PETICION,
                "live": bool(en_vivo),
                "sent": bool(resultado.get("sent")),
                "success": resultado.get("success"),
                "http_status": resultado.get("http_status"),
                "response": resultado.get("response"),
            }

            apuntar(anotacion, ruta_del_libro)

            # Enviada no es hecha: la leccion de Jonny, del 10/09.
            if en_vivo and resultado.get("success") is False:
                fallidos.append(
                    {
                        "name": fila.get("name"),
                        "error": (
                            f"Biwenger contesto "
                            f"{resultado.get('http_status')}"
                        ),
                    }
                )
                continue

            listados.append(anotacion)

        except Exception as error:                  # noqa: BLE001
            fallidos.append(
                {
                    "name": fila.get("name"),
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    return {
        "available": True,
        "executed": bool(en_vivo and listados),
        "listed": listados,
        "failed": fallidos,
        "reason": (
            f"{len(listados)} publicado(s) "
            + (
                "EN VIVO"
                if en_vivo
                else "preparados y NO enviados"
            )
            + (
                f", {len(fallidos)} fallidos"
                if fallidos
                else ""
            )
            + "."
        ),
    }


# ============================================================
# LA GUARDIA CLAVE, EN FORMA DE DATO
# ============================================================


def viajes_sin_listar(
    viajes: list | None,
    listados: list | None,
) -> dict:
    """
    Un jugador marcado VIAJE que termina el ciclo SIN LISTAR.

    Es el estado que no puede existir: comprado para revender, y
    en el escaparate no esta. Sale en ROJO en la portada con
    nombre y hora, porque cada vuelta asi es escaparate tirado y
    nadie lo notaria de otro modo.
    """

    try:
        en_venta = {
            safe_int(x.get("player_id") or x.get("id"))
            for x in (listados or [])
            if isinstance(x, dict)
        }

        huerfanos = [
            {
                "player_id": safe_int(v.get("player_id")),
                "name": v.get("name"),
                "opened_at": v.get("opened_at"),
                "cost": safe_int(v.get("cost")),
            }
            for v in (viajes or [])
            if isinstance(v, dict)
            and safe_int(v.get("player_id")) not in en_venta
        ]

        return {
            "available": True,
            "ok": not huerfanos,
            "players": huerfanos,
            "reason": (
                "Todos los viajes abiertos estan publicados."
                if not huerfanos
                else (
                    "VIAJES SIN LISTAR: "
                    + " · ".join(
                        f"{h['name'] or h['player_id']}"
                        f" (desde {str(h['opened_at'])[:16]})"
                        for h in huerfanos
                    )
                    + ". Comprados para revender y no estan en "
                    "venta: cada vuelta asi es escaparate tirado."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "ok": None,
            "players": [],
            "reason": (
                f"No se pudo comprobar el escaparate: "
                f"{type(error).__name__}: {error}"
            ),
        }
