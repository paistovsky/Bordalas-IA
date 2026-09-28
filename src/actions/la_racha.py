"""
LA RACHA DIARIA, COBRADA POR PEPE (28/09/2026)

    Biwenger paga 250.000 EUR a quien entra cinco dias seguidos y
    pulsa «Canjear». Pepe entra cada hora, pero el boton lo pulsaba
    el dueno a mano: los tres canjes de Pepe en el tablon (16/09
    09:12, 21/09 00:53, 26/09 07:22 de Madrid) no caen en ninguna
    vuelta (todas a las :07). Pollo17 lleva siete canjes; Pepe, tres.

    QUE HACE: si la racha que la vuelta ya leyo (`daily_streak` de
    la foto, sin peticion de mas) ha llegado a CINCO, pide el canje
    con `BiwengerWriteClient.redeem_daily_streak`. Si no, nada.

    QUE NO HACE: no consume `write_used` (no es comprar ni vender,
    y no mueve jugadores) ni lee nada nuevo de Biwenger hasta que
    hay algo que cobrar. Si la racha es None (no se pudo leer), no
    hace nada: nunca se cobra a ciegas.

    Nace APAGADA: `BORDALAS_COBRA_LA_RACHA`. Nunca lanza.
"""

from __future__ import annotations

import os


ENV = "BORDALAS_COBRA_LA_RACHA"

# Los pasos de la racha. En la app de Biwenger es `ko`, y el canje
# se ofrece cuando `dailyStreak >= ko`.
PASOS = 5


def activa(interruptor: str = ENV) -> bool:
    try:
        return str(
            os.environ.get(interruptor, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def racha_de_la_vuelta(cycle: dict | None) -> int | None:
    """La racha que ya leyo la vuelta. None si no se sabe."""

    try:
        valor = ((cycle or {}).get("snapshot") or {}).get("daily_streak")

        if valor is None or isinstance(valor, bool):
            return None

        return int(valor)

    except (TypeError, ValueError):
        return None


def cobrar(cycle: dict | None, escritor_factory=None) -> dict:
    """Cobra la racha si toca. Devuelve lo que hizo. Nunca lanza."""

    salida = {
        "activa": activa(),
        "racha": racha_de_la_vuelta(cycle),
        "pasos": PASOS,
        "intentado": False,
        "cobrada": False,
        "motivo": None,
        "resultado": None,
    }

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        if salida["racha"] is None:
            salida["motivo"] = "RACHA_SIN_LEER"
            return salida

        if salida["racha"] < PASOS:
            salida["motivo"] = "AUN_NO_TOCA"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        escritor = escritor_factory()

        salida["intentado"] = True

        resultado = escritor.redeem_daily_streak(
            league_id=escritor.league_id,
            execute=True,
        )

        salida["resultado"] = {
            k: resultado.get(k)
            for k in (
                "operation", "sent", "http_status",
                "success", "success_detail",
            )
        }
        salida["cobrada"] = bool(
            resultado.get("sent") and resultado.get("success")
        )
        salida["motivo"] = (
            "COBRADA" if salida["cobrada"]
            else "NO_ENVIADA" if not resultado.get("sent")
            else "BIWENGER_LA_RECHAZO"
        )

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida
