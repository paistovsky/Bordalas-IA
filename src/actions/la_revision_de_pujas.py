"""
LA REVISION DE LAS PUJAS VIVAS ANTES DEL RESET (29/09/2026)

POR QUE EXISTE

    Las reglas de compra (¿va a jugar?, la rampa, NO_DISPONIBLE) miran
    al jugador CUANDO SE PUJA. Nadie vuelve a mirarlo despues. Caso
    Zubeldia (laboratorio E6): Pepe pujo el 28/09 a las 07:19; FF publico
    «sigue al margen» a las 14:59; Biwenger lo paso a «doubt» el 29/09
    DESPUES del reset en que Pepe lo gano (1.363.592). La puja estuvo
    viva ~16 h con la noticia ya fuera.

QUE HACE

    En la ventana del reset (los mismos 135 min de la subasta), mira
    cada puja nuestra viva y, si Biwenger ya marca al jugador como
    lesionado, en duda o sancionado, la retira (`cancel_bid`).

QUE NO HACE

    No retira las pujas de la orden del gestor (`fichar`): esas las
    decide el gestor; si su jugador se tuerce, lo dice en voz alta y no
    toca. Fuera de la ventana no hace nada. No lee nada nuevo: usa el
    estado del catalogo que ya trae la foto de la vuelta.

    Nace APAGADA: `BORDALAS_REVISA_LAS_PUJAS_VIVAS`. Nunca lanza.
"""

from __future__ import annotations

import os


ENV = "BORDALAS_REVISA_LAS_PUJAS_VIVAS"

# Estados de Biwenger que hacen que una puja ya no pase.
MALOS = frozenset({"injured", "doubt", "sanctioned"})


def activa(interruptor: str = ENV) -> bool:
    try:
        return str(
            os.environ.get(interruptor, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def _int(valor):
    try:
        if valor is None or isinstance(valor, bool):
            return None
        return int(valor)
    except (TypeError, ValueError):
        return None


def _pid(x):
    return _int(x.get("id")) if isinstance(x, dict) else _int(x)


def pujas_vivas(snapshot: dict | None) -> list:
    """Nuestras pujas vivas: [{offer_id, player_id, amount}]."""

    s = snapshot or {}
    yo = _pid((s.get("league") or {}).get("user"))
    salida = []

    if yo is None:
        return salida

    for o in ((s.get("market") or {}).get("offers") or []):
        if str(o.get("status", "waiting")) != "waiting":
            continue
        if str(o.get("type", "purchase")) != "purchase":
            continue
        if _pid(o.get("from")) != yo:
            continue
        jugadores = o.get("requestedPlayers") or []
        if len(jugadores) != 1:
            continue
        salida.append({
            "offer_id": _int(o.get("id")),
            "player_id": _pid(jugadores[0]),
            "amount": _int(o.get("amount")),
        })

    return salida


def estado(snapshot: dict | None, player_id: int) -> str | None:
    catalogo = (
        ((snapshot or {}).get("catalog") or {}).get("data") or {}
    ).get("players") or {}
    jugador = catalogo.get(str(player_id)) or catalogo.get(player_id) or {}
    valor = jugador.get("status")
    return str(valor).lower() if valor is not None else None


def decidir(snapshot: dict | None, en_ventana: bool, de_la_orden: set) -> dict:
    """Que pujas retirar. Pura."""

    salida = {"en_ventana": bool(en_ventana), "revisadas": [], "retirar": [],
              "avisos": []}

    if not en_ventana:
        return salida

    for p in pujas_vivas(snapshot):
        st = estado(snapshot, p["player_id"])
        fila = {**p, "estado": st}
        salida["revisadas"].append(fila)

        if st not in MALOS:
            continue

        if p["player_id"] in de_la_orden:
            salida["avisos"].append({**fila, "motivo": "ES_DE_LA_ORDEN"})
            continue

        if p["offer_id"]:
            salida["retirar"].append(fila)

    return salida


def correr(cycle: dict | None, seconds_to_reset, escritor_factory=None) -> dict:
    """La revision, en esta vuelta. Nunca lanza."""

    salida = {"activa": activa(), "motivo": None, "retiradas": []}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.analysis.la_subasta import ventana_abierta

        en_ventana = bool(ventana_abierta(seconds_to_reset).get("abierta"))

        try:
            from src.actions.la_orden_del_gestor import (
                activa as _orden_activa, leer_la_orden,
            )
            orden = leer_la_orden() if _orden_activa() else None
            de_la_orden = {
                _int(f.get("player_id"))
                for f in ((orden or {}).get("fichar") or [])
            }
        except Exception:                           # noqa: BLE001
            de_la_orden = set()

        plan = decidir((cycle or {}).get("snapshot"), en_ventana, de_la_orden)
        salida.update(plan)

        if not en_ventana:
            salida["motivo"] = "FUERA_DE_LA_VENTANA"
            return salida

        if not plan["retirar"]:
            salida["motivo"] = "TODAS_PASAN"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        escritor = escritor_factory()

        for fila in plan["retirar"]:
            try:
                r = escritor.cancel_bid(offer_id=fila["offer_id"], execute=True)
                salida["retiradas"].append({
                    **fila, "enviada": bool((r or {}).get("sent")),
                    "exito": (r or {}).get("success"),
                })
            except Exception as error:              # noqa: BLE001
                salida["retiradas"].append({
                    **fila, "enviada": False,
                    "error": f"{type(error).__name__}: {error}",
                })

        salida["motivo"] = "REVISADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida
