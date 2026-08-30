"""
El libro de pujas: que pusimos, y como acabo.

SINTOMA

    El dueño dice que pierde muchas pujas. El sistema no registra
    ninguna: en el ledger, "Pepe Bordalas" tiene lost_bids = 0, y
    nuestro user_id no aparece como perdedor en ninguna de las 48
    subastas del tablon. El autopilot escribe SPECULATION_BID_PLACED y
    ahi se acaba la historia: no hay campo de resultado.

CAUSA

    Poner la puja y saber quien la gano son dos momentos distintos,
    separados por horas. Nadie los estaba cosiendo.

CONSECUENCIA

    Sin ese cosido no se puede calibrar nada. "Perder por un 2 %" y
    "perder por un 40 %" son dos problemas opuestos -uno se arregla
    subiendo un pelo, el otro dice que el jugador no era para
    nosotros- y a ojo no se distinguen. Este libro es la materia
    prima: primero medir, despues decidir.

    No decide nada. Solo apunta.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path("data/trading/bid_outcome_ledger.json")

# El tablon que persiste board_history_collector. Es una LISTA pelada de
# eventos, no un dict con "events": si algun dia cambia, _operaciones
# traga las dos formas.
BOARD_EVENTS_PATH = Path("data/rival_intelligence/board_events.json")

VERSION = "V1.0"

# El tablon de Biwenger solo publica las dos mejores pujas perdedoras
# de cada subasta. Si nuestra puja no sale ahi, sabemos que perdimos
# pero no por cuanto: quedan como LOST sin margen, y se cuentan aparte
# para no ensuciar la media.
PUJAS_PERDEDORAS_PUBLICADAS = 2

# Una puja sin resolver despues de esto se da por perdida de vista. El
# mercado del Computer se resetea a diario; 72 h es de sobra.
HORAS_PARA_CADUCAR = 72


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _libro_vacio() -> dict:
    return {"version": VERSION, "bids": {}}


def load_ledger(path: Path | None = None) -> dict:
    ruta = path or LEDGER_PATH
    try:
        libro = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return _libro_vacio()

    if not isinstance(libro, dict) or "bids" not in libro:
        return _libro_vacio()

    if not isinstance(libro.get("bids"), dict):
        libro["bids"] = {}

    libro.setdefault("version", VERSION)
    return libro


def save_ledger(libro: dict, path: Path | None = None) -> bool:
    """Nunca lanza: perder una anotacion no puede tumbar un ciclo."""
    ruta = path or LEDGER_PATH
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(libro, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def _clave(player_id: int, puesta_en: str) -> str:
    return f"{int(player_id)}:{puesta_en}"


def record_bid(
    player_id: int,
    amount: int,
    *,
    player_name: str | None = None,
    our_value: int | None = None,
    win_probability: float | None = None,
    market_price: int | None = None,
    recommended_bid: int | None = None,
    intent: str | None = None,
    target_source: str | None = None,
    seller_user_id: int | None = None,
    placed_at: str | None = None,
    ledger: dict | None = None,
    path: Path | None = None,
    save: bool = True,
) -> dict:
    """
    Apunta una puja recien colocada, en estado PENDIENTE.

    `our_value` y `win_probability` pueden venir vacios: las pujas del
    respaldo legacy (target_source == "SPECULATION_SCORING") no traen
    fila de adquisicion. Se apuntan igual; simplemente no serviran para
    calibrar la curva.
    """

    libro = ledger if ledger is not None else load_ledger(path)
    puesta_en = placed_at or _ahora()

    libro["bids"][_clave(player_id, puesta_en)] = {
        "player_id": int(player_id),
        "player_name": player_name,
        "amount": int(amount),
        "our_value": int(our_value) if our_value is not None else None,
        "win_probability": (
            float(win_probability) if win_probability is not None else None
        ),
        "market_price": int(market_price) if market_price is not None else None,
        "recommended_bid": (
            int(recommended_bid) if recommended_bid is not None else None
        ),
        "intent": intent,
        "target_source": target_source,
        # None = mercado del Computer; un id = puja a un rival.
        "seller_user_id": seller_user_id,
        "placed_at": puesta_en,
        "outcome": "PENDING",
        "resolved_at": None,
        "winning_amount": None,
        # Cuanto nos gano el ganador. Positivo = nos superaron por eso.
        "margin": None,
        "event_id": None,
    }

    if save:
        save_ledger(libro, path)

    return libro


def _operaciones(board):
    """
    Aplana el tablon a (event_id, fecha_epoch, operacion).

    Acepta la lista pelada que escribe board_history_collector y
    tambien un dict con "events", que es lo que devuelve el colector
    en vivo.
    """

    if isinstance(board, dict):
        eventos = board.get("events") or []
    elif isinstance(board, list):
        eventos = board
    else:
        return

    for evento in eventos:
        if not isinstance(evento, dict):
            continue
        if evento.get("type") not in (None, "market"):
            continue

        event_id = evento.get("event_id") or evento.get("id")
        fecha = evento.get("date")

        for operacion in evento.get("content") or []:
            if isinstance(operacion, dict):
                yield event_id, fecha, operacion


def _epoch(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0


def reconcile(
    board,
    our_user_id: int | None,
    *,
    ledger: dict | None = None,
    path: Path | None = None,
    save: bool = True,
    ahora: str | None = None,
) -> dict:
    """
    Cierra las pujas pendientes contra las subastas ya resueltas.

    Ganamos si el comprador de la operacion somos nosotros. Si no, el
    importe de la operacion es lo que pago el ganador, y la diferencia
    con lo nuestro es por cuanto nos ganaron.
    """

    libro = ledger if ledger is not None else load_ledger(path)

    # Sin saber quienes somos no se puede distinguir ganar de perder, y
    # marcarlo todo como perdido seria peor que no medir: dejaria un
    # libro que miente. Se prefiere no tocar nada.
    if our_user_id is None:
        return libro

    momento = ahora or _ahora()
    limite = _epoch(momento) - HORAS_PARA_CADUCAR * 3600

    ops_por_jugador: dict[int, list] = {}
    for event_id, fecha, operacion in _operaciones(board):
        try:
            pid = int(operacion.get("player"))
        except (TypeError, ValueError):
            continue
        ops_por_jugador.setdefault(pid, []).append((event_id, fecha, operacion))

    for entrada in libro["bids"].values():
        if entrada.get("outcome") != "PENDING":
            continue

        puesta = _epoch(entrada.get("placed_at") or "")
        candidatas = [
            (e, f, o)
            for e, f, o in ops_por_jugador.get(entrada["player_id"], [])
            if not f or not puesta or f >= puesta
        ]

        if not candidatas:
            if puesta and puesta < limite:
                entrada["outcome"] = "UNKNOWN"
                entrada["resolved_at"] = momento
            continue

        event_id, _fecha, operacion = min(
            candidatas, key=lambda c: c[1] or 0
        )

        comprador = (operacion.get("to") or {}).get("id")
        importe = operacion.get("amount")

        entrada["event_id"] = event_id
        entrada["resolved_at"] = momento
        entrada["winning_amount"] = (
            int(importe) if importe is not None else None
        )

        if our_user_id is not None and comprador == our_user_id:
            entrada["outcome"] = "WON"
            entrada["margin"] = 0
        else:
            entrada["outcome"] = "LOST"
            if importe is not None:
                entrada["margin"] = int(importe) - int(entrada["amount"])

    if save:
        save_ledger(libro, path)

    return libro


def summary(ledger: dict | None = None, path: Path | None = None) -> dict:
    """
    El resumen que va al dashboard. Sin datos, dice que no los hay:
    nunca inventa un 0 % que parezca una medida.
    """

    libro = ledger if ledger is not None else load_ledger(path)
    entradas = list(libro.get("bids", {}).values())

    ganadas = [e for e in entradas if e.get("outcome") == "WON"]
    perdidas = [e for e in entradas if e.get("outcome") == "LOST"]
    pendientes = [e for e in entradas if e.get("outcome") == "PENDING"]
    perdidas_de_vista = [e for e in entradas if e.get("outcome") == "UNKNOWN"]

    margenes = sorted(
        e["margin"] for e in perdidas if e.get("margin") is not None
    )

    resueltas = len(ganadas) + len(perdidas)

    return {
        "available": bool(entradas),
        "placed": len(entradas),
        "won": len(ganadas),
        "lost": len(perdidas),
        "pending": len(pendientes),
        "unknown": len(perdidas_de_vista),
        "win_rate": (len(ganadas) / resueltas) if resueltas else None,
        "lost_with_margin": len(margenes),
        "median_lost_margin": (
            margenes[len(margenes) // 2] if margenes else None
        ),
        "mean_lost_margin": (
            int(sum(margenes) / len(margenes)) if margenes else None
        ),
        "worst_lost_margin": (margenes[-1] if margenes else None),
    }


def sync_bid_outcomes(
    our_user_id: int | None,
    *,
    board_path: Path | None = None,
    path: Path | None = None,
) -> dict:
    """
    El enganche del ciclo: cierra pendientes y devuelve el resumen.

    Lee el tablon ya persistido en vez de volver a pedirlo por red: el
    colector lo deja escrito en cada ciclo.

    Blindado a proposito, igual que el libro de fuentes: un fallo
    apuntando jamas puede detener un ciclo de produccion.
    """

    try:
        eventos = json.loads(
            (board_path or BOARD_EVENTS_PATH).read_text(encoding="utf-8")
        )
    except Exception:
        eventos = []

    if our_user_id is None:
        return {
            "available": False,
            "error": "Sin identificar nuestro usuario, no se cierra nada.",
        }

    try:
        libro = reconcile(eventos, our_user_id, path=path)
        return summary(libro)
    except Exception:
        return {"available": False, "error": "El libro de pujas no pudo cerrarse."}
