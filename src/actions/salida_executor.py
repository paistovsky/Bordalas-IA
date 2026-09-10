"""
El camino que cierra un VIAJE. Solo cobra ofertas. Nada mas.

POR QUE ESTE FICHERO EXISTE Y ES TAN CORTO

    Es la primera ruta de esta casa que VENDE jugadores sola. La
    de renovar solo lista; esta acepta ofertas, y aceptar una
    oferta es irreversible: el jugador se va.

    Por eso esta aislada igual que `renovar_executor`:

        · No importa el motor de ventas de siempre, ni el de
          ofertas, ni el de solvencia.

        · La UNICA llamada de escritura del fichero es
          `accept_offer`. No hay ninguna otra, y hay guardia que
          lo comprueba con un cliente que apunta todo lo que se
          le llama.

        · No decide NADA. Recibe la lista que ya decidio
          `salida_del_viaje.que_cobrar`, con sus cinco
          prohibiciones aplicadas, y ejecuta. Si algun dia hay
          que endurecer una condicion, se endurece alli.

LA MARCA ES EL PERMISO

    Solo se cobra lo que viene con `player_id` y `offer_id` de
    un VIAJE. Un jugador sin marca no llega hasta aqui, porque
    `que_cobrar` solo mira la lista de viajes abiertos — y hay
    una guardia que lo prueba pasandole datos trucados.

APAGADO

    `en_vivo=False` es el defecto. Se enciende el sabado con el
    dueno delante.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


LIBRO = Path("data") / "trading" / "libro_de_salidas.jsonl"


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def apuntar(fila: dict, ruta: Path | None = None) -> bool:
    """Al libro. Nunca lanza."""

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


def cobrar(
    salidas: list | None,
    escritor=None,
    en_vivo: bool = False,
    tope: int | None = None,
    ruta_del_libro: Path | None = None,
) -> dict:
    """
    Cobra las ofertas de los VIAJES que ya decidio `que_cobrar`.

    Nunca lanza: una salida que revienta no puede tumbar el
    ciclo.
    """

    from src.analysis.salida_del_viaje import VENTAS_POR_VUELTA

    salida = {
        "available": False,
        "executed": False,
        "sold": [],
        "failed": [],
        "dropped_by_cap": 0,
        "reason": None,
    }

    filas = [
        f for f in (salidas or []) if isinstance(f, dict)
    ]

    if not filas:
        return {
            **salida,
            "available": True,
            "reason": "No hay ningun viaje que cerrar.",
        }

    limite = safe_int(
        tope if tope is not None else VENTAS_POR_VUELTA
    )

    recortadas = max(0, len(filas) - limite)

    filas = filas[:limite]

    if escritor is None:
        from src.biwenger.write_client import (
            BiwengerWriteClient,
        )

        escritor = BiwengerWriteClient()

    vendidas = []

    fallidas = []

    for fila in filas:

        oferta = safe_int(fila.get("offer_id"))

        if oferta <= 0:
            fallidas.append(
                {
                    "name": fila.get("name"),
                    "error": "Sin offer_id no se cobra nada.",
                }
            )
            continue

        try:
            # LA UNICA ESCRITURA DE ESTE FICHERO.
            resultado = escritor.accept_offer(
                offer_id=oferta,
                execute=bool(en_vivo),
            )

            anotacion = {
                "at": _ahora(),
                "player_id": fila.get("player_id"),
                "player_name": fila.get("name"),
                "offer_id": oferta,
                "cost": safe_int(fila.get("cost")),
                "amount": safe_int(fila.get("amount")),
                "profit": safe_int(fila.get("profit")),
                "yield_percent": fila.get("yield_percent"),
                "loss_cut": bool(fila.get("loss_cut")),
                "live": bool(en_vivo),
                "sent": bool(resultado.get("sent")),
                "success": resultado.get("success"),
                "http_status": resultado.get("http_status"),
                "response": resultado.get("response"),
            }

            apuntar(anotacion, ruta_del_libro)

            # Enviada no es hecha: si Biwenger dice que no, es un
            # fallo. Es la leccion de Jonny, del 10/09.
            if en_vivo and resultado.get("success") is False:
                fallidas.append(
                    {
                        "name": fila.get("name"),
                        "error": (
                            f"Biwenger contesto "
                            f"{resultado.get('http_status')}"
                        ),
                    }
                )
                continue

            vendidas.append(anotacion)

        except Exception as error:                  # noqa: BLE001
            fallidas.append(
                {
                    "name": fila.get("name"),
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    return {
        "available": True,
        "executed": bool(en_vivo and vendidas),
        "sold": vendidas,
        "failed": fallidas,
        "dropped_by_cap": recortadas,
        "reason": (
            f"{len(vendidas)} viaje(s) "
            + ("CERRADOS" if en_vivo else "preparados y NO enviados")
            + (
                f", {len(fallidas)} fallidos"
                if fallidas
                else ""
            )
            + "."
        ),
    }
