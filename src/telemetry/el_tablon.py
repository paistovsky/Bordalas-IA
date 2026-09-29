"""
EL TABLON DEL DIA, EN EL PANEL (29/09/2026)

    El dueno lo pidio asi: «lo que pone en el tablon del dia en
    Biwenger». Pepe ya guarda el tablon de la liga en cada vuelta
    (`data/rival_intelligence/board_events.json`); esto lo traduce a
    frases para el panel. Funcion pura: ni red ni disco. Nunca lanza.

    Se cuenta: fichajes del mercado (quien, a quien, por cuanto, y
    las pujas que perdieron), ventas al Computer y entre managers,
    rachas cobradas, jornadas cerradas, mensajes, encuestas y cambios
    de puntos del admin. No se cuenta: porras, movimientos de LaLiga y
    ajustes de la liga (ruido para el dueno).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


MADRID = ZoneInfo("Europe/Madrid")

IGNORADOS = frozenset({
    "bettingPool", "playerMovements", "leagueSettings", "roundStarted",
    "userName", "adminText",
})


def _euros(n) -> str:
    try:
        return f"{int(n):,}".replace(",", ".") + " €"
    except (TypeError, ValueError):
        return "?"


def _quien(u) -> str:
    return str((u or {}).get("name") or "?") if isinstance(u, dict) else "?"


def _jugador(pid, nombres: dict) -> str:
    try:
        return str(nombres.get(int(pid)) or f"jugador {pid}")
    except (TypeError, ValueError):
        return "?"


def _frases(e: dict, nombres: dict) -> list:
    tipo = e.get("type")
    c = e.get("content")
    out = []

    if tipo == "market":
        for f in c or []:
            j = _jugador(f.get("player"), nombres)
            pujas = f.get("bids") or []
            extra = (
                f" (le ganó la puja a {len(pujas)} rival"
                f"{'es' if len(pujas) != 1 else ''})"
                if pujas else ""
            )
            out.append(
                f"{_quien(f.get('to'))} ficha a {j} por "
                f"{_euros(f.get('amount'))}{extra}."
            )

    elif tipo == "transfer":
        for f in c or []:
            j = _jugador(f.get("player"), nombres)
            if f.get("to"):
                out.append(
                    f"{_quien(f.get('from'))} vende a {j} a "
                    f"{_quien(f.get('to'))} por {_euros(f.get('amount'))}."
                )
            else:
                out.append(
                    f"{_quien(f.get('from'))} vende a {j} al mercado por "
                    f"{_euros(f.get('amount'))}."
                )

    elif tipo == "bonus":
        for f in c or []:
            motivo = (
                "por la racha diaria" if f.get("reason") == "dailyStreak"
                else ""
            )
            out.append(
                f"{_quien(f.get('user'))} cobra {_euros(f.get('amount'))} "
                f"{motivo}".strip() + "."
            )

    elif tipo == "roundFinished":
        ronda = ((c or {}).get("round") or {}).get("name") or "La jornada"
        res = sorted(
            (c or {}).get("results") or [],
            key=lambda r: -(r.get("points") or 0),
        )
        if res:
            top = ", ".join(
                f"{_quien(r.get('user'))} {r.get('points')}" for r in res[:3]
            )
            out.append(f"Termina la {ronda}. Los mejores: {top} puntos.")

    elif tipo == "text":
        titulo = str(e.get("title") or "").strip() or "un mensaje"
        out.append(f"{_quien(e.get('author'))} escribe: «{titulo}».")

    elif tipo == "poll":
        preguntas = (((c or {}).get("poll") or {}).get("questions") or [])
        titulo = (preguntas[0].get("title") if preguntas else None) or "una encuesta"
        out.append(f"{_quien(e.get('author'))} abre una encuesta: «{titulo}».")

    elif tipo == "userPoints":
        for f in c or []:
            out.append(
                f"El admin cambia los puntos de {_quien(f.get('user'))}: "
                f"de {f.get('from')} a {f.get('to')}."
            )

    elif tipo == "userJoin":
        for f in c or []:
            out.append(f"{_quien(f)} entra en la liga.")

    elif tipo == "leagueReset":
        out.append("La liga se reinicia.")

    return out


def el_tablon_de_hoy(
    eventos,
    nombres: dict | None = None,
    ahora: datetime | None = None,
    horas: int = 24,
) -> dict:
    """
    Lo del tablon de las ultimas `horas`, lo mas nuevo arriba:
    `{"desde", "lineas": [{"hora", "tipo", "texto"}], "n"}`.
    """

    salida = {"desde": None, "lineas": [], "n": 0, "horas": horas}

    try:
        ahora = ahora or datetime.now(timezone.utc)
        desde = ahora - timedelta(hours=horas)
        salida["desde"] = desde.astimezone(MADRID).isoformat()
        nombres = nombres or {}

        lista = eventos
        if isinstance(eventos, dict):
            lista = eventos.get("events") or eventos.get("items") or []

        filas = []
        for e in lista or []:
            if not isinstance(e, dict) or e.get("type") in IGNORADOS:
                continue
            try:
                cuando = datetime.fromtimestamp(int(e.get("date")), timezone.utc)
            except (TypeError, ValueError, OverflowError, OSError):
                continue
            if cuando < desde or cuando > ahora + timedelta(minutes=5):
                continue
            for texto in _frases(e, nombres):
                filas.append((cuando, e.get("type"), texto))

        filas.sort(key=lambda f: f[0], reverse=True)
        salida["lineas"] = [
            {
                "hora": c.astimezone(MADRID).strftime("%d/%m %H:%M"),
                "tipo": t,
                "texto": x,
            }
            for c, t, x in filas
        ]
        salida["n"] = len(salida["lineas"])

    except Exception as error:                      # noqa: BLE001
        salida["error"] = f"{type(error).__name__}: {error}"

    return salida
