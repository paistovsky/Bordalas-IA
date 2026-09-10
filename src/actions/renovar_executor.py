"""
El camino de renovar. Solo renueva. No puede vender.

POR QUE ESTE FICHERO EXISTE Y ES TAN CORTO

    Hasta hoy Pepe no escribia nada contra Biwenger. A partir de
    esta rama si, y lo primero que escribe es una renovacion.

    El endpoint de renovar -POST /market, type "sell"- vive al
    lado del de vender -PUT /offers/{id}-, y se llaman parecido.
    Confundirlos una vez seria vender un titular por accidente el
    dia de la jornada.

    Asi que el camino esta AISLADO a proposito:

        · Este modulo no importa el ejecutor de ventas, ni el de
          ofertas, ni nada que pueda aceptarlas.

        · La UNICA llamada de escritura que hace es
          `list_player_for_sale`. No hay ninguna otra en el
          fichero, y hay una guardia que lo comprueba
          ejecutandolo con un cliente falso que apunta todo lo
          que se le llama.

        · Aunque a `renovar` le llegue una fila manipulada con
          `offer_id`, `accept`, o lo que sea, no hay ninguna
          rama que llegue a una venta: no existe el codigo.

LO QUE RENOVAR ES, EXACTAMENTE

    Volver a listar al jugador al mismo precio. Biwenger mata la
    oferta viva y publica una nueva en el reset siguiente -entre
    las 07:03 y las 07:09, medido-.

    NO mueve dinero. NO ocupa fichas. NO vende.

EL TOPE DE ESCRITURAS ES DURO

    Se corta contando, no confiando. Si la lista trae mas de las
    que se pueden hacer, se hacen las primeras y se dice cuantas
    se quedaron fuera.

CADA RENOVACION, AL LIBRO

    Jugador, importe de la oferta que muere, hora, y que nacio
    despues. Si manana esto sale mal hay que poder reconstruirlo
    sin adivinar.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


LIBRO = Path("data") / "trading" / "libro_de_renovaciones.jsonl"


# El corte duro. Es el mismo numero que decide `renovar_ofertas`,
# importado y no copiado: un dato, un nombre.
def _tope() -> int:
    from src.analysis.renovar_ofertas import TOPE_DE_RENOVACIONES

    return TOPE_DE_RENOVACIONES


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def apuntar(fila: dict, ruta: Path | None = None) -> bool:
    """
    Al libro. Nunca lanza: perder una anotacion no puede tumbar
    un ciclo, pero perder la renovacion si seria grave, asi que
    esto va DESPUES de escribir.
    """

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


def renovar(
    renovaciones: list | None,
    escritor=None,
    en_vivo: bool = False,
    tope: int | None = None,
    ruta_del_libro: Path | None = None,
) -> dict:
    """
    Ejecuta las renovaciones decididas por `que_renovar`.

    `en_vivo=False` -el defecto- no escribe nada: monta la
    peticion y la devuelve. El primer disparo real se mira con el
    dueno delante.

    Nunca lanza: una renovacion que revienta no puede tumbar el
    ciclo.
    """

    salida = {
        "available": False,
        "executed": False,
        "sent": [],
        "failed": [],
        "dropped_by_cap": 0,
        "reason": None,
    }

    filas = [
        f for f in (renovaciones or []) if isinstance(f, dict)
    ]

    if not filas:
        return {
            **salida,
            "available": True,
            "reason": "No hay ninguna renovacion que hacer.",
        }

    limite = safe_int(tope if tope is not None else _tope())

    recortadas = max(0, len(filas) - limite)

    filas = filas[:limite]

    if escritor is None:
        from src.biwenger.write_client import (
            BiwengerWriteClient,
        )

        escritor = BiwengerWriteClient()

    enviadas = []
    fallidas = []

    for fila in filas:

        jugador = safe_int(fila.get("id"))

        precio = safe_int(fila.get("listed_price"))

        if jugador <= 0 or precio <= 0:
            fallidas.append(
                {
                    "name": fila.get("name"),
                    "error": (
                        "Sin id de jugador o sin precio no se "
                        "renueva."
                    ),
                }
            )
            continue

        try:
            # LA UNICA ESCRITURA DE ESTE FICHERO.
            resultado = escritor.list_player_for_sale(
                player_id=jugador,
                price=precio,
                execute=bool(en_vivo),
            )

            anotacion = {
                "at": _ahora(),
                "player_id": jugador,
                "player_name": fila.get("name"),
                "listed_price": precio,

                # La opcion que se mata al renovar.
                "dying_offer": safe_int(fila.get("dying_offer")),
                "dying_offer_hours": fila.get(
                    "dying_offer_hours"
                ),

                # Y lo que nace: no se sabe hasta el reset. Se
                # apunta lo que se espera, medido.
                "new_offer_expected": "07:03-07:09 Madrid",

                "live": bool(en_vivo),
                "sent": bool(resultado.get("sent")),
                "success": resultado.get("success"),
            }

            apuntar(anotacion, ruta_del_libro)

            enviadas.append(anotacion)

        except Exception as error:                  # noqa: BLE001
            fallidas.append(
                {
                    "name": fila.get("name"),
                    "error": (
                        f"{type(error).__name__}: {error}"
                    ),
                }
            )

    return {
        "available": True,
        "executed": bool(en_vivo and enviadas),
        "sent": enviadas,
        "failed": fallidas,
        "dropped_by_cap": recortadas,
        "reason": (
            f"{len(enviadas)} renovacion(es) "
            + ("ENVIADAS" if en_vivo else "preparadas y NO enviadas")
            + (
                f", {len(fallidas)} fallidas"
                if fallidas
                else ""
            )
            + (
                f", {recortadas} fuera por el tope de {limite}"
                if recortadas
                else ""
            )
            + "."
        ),
    }
