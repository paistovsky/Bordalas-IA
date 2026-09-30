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


# ============================================================
# LAS REGLAS ENCENDIDAS, EN UNA LINEA CADA UNA (30/09/2026)
# ============================================================
#
#     Para la pagina ESTRATEGIA del panel: que interruptores de
#     produccion estan encendidos (leidos del YAML de produccion, no de
#     una copia) y que hace cada uno, en palabras del dueno. Uno sin
#     frase sale con su nombre tecnico: nunca se esconde.

QUE_HACE = {
    "BORDALAS_COBRA_LA_RACHA":
        "Cobra solo los 250.000 € de la racha diaria cuando llega a 5.",
    "BORDALAS_COMPRA_SOLO_SI_SUBE":
        "Para revender, solo compra jugadores cuyo precio está subiendo.",
    "BORDALAS_EL_ONCE_UNA_VEZ":
        "Calcula el mejor once una vez por vuelta y lo recuerda (más rápido).",
    "BORDALAS_JORNADAS_POR_SU_FECHA":
        "Cuenta las jornadas por la fecha de los partidos, no por Biwenger.",
    "BORDALAS_LA_MONEDA_DE_LA_LIGA":
        "Usa el dinero real de la liga (saldo y reparto) en sus cuentas.",
    "BORDALAS_LA_ORDEN_DEL_GESTOR":
        "Cumple las órdenes concretas del gestor (hoy: ir a por Roberto "
        "Fernández y vender para pagarlo, sin tocar el once).",
    "BORDALAS_REJA_CON_TOLERANCIA":
        "No cuenta dos veces las ventas que Biwenger repite en el tablón "
        "(así la caja de los rivales cuadra).",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA":
        "En la subasta de las 07:00 solo compra para revender a quien va a jugar.",
    "BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL":
        "Durante el día, lo mismo: solo compra para revender a quien va a jugar.",
    "BORDALAS_REVISA_LAS_PUJAS_VIVAS":
        "Antes de las 07:00 retira las pujas por jugadores que se han lesionado.",
    "BORDALAS_SOLVENCIA_POR_SU_PLAZO":
        "Vigila que el saldo esté en positivo antes de que empiece la jornada.",
}


def las_reglas_encendidas() -> dict:
    """`{"ok", "reglas": [{"nombre", "que_hace"}], "n"}`. Nunca lanza."""

    try:
        from src.analysis.los_interruptores_de_produccion import (
            los_de_produccion,
        )

        prod = los_de_produccion()
        reglas = [
            {"nombre": n, "que_hace": QUE_HACE.get(n) or n}
            for n in prod.get("interruptores") or []
            if n != "BORDALAS_ENSAYO"
        ]
        return {"ok": bool(prod.get("ok")), "reglas": reglas, "n": len(reglas)}

    except Exception as error:                      # noqa: BLE001
        return {"ok": False, "reglas": [], "n": 0,
                "error": f"{type(error).__name__}: {error}"}


# ============================================================
# LA ORDEN DEL GESTOR, PARA EL PANEL (30/09/2026)
# ============================================================

def la_orden_para_el_panel() -> dict:
    """
    La orden viva en frases: a por quien va Pepe, a quien vende para
    pagarlo, a quien protege. `{"viva", "motivo", "caduca", "fichar",
    "vender", "proteger", "conservar", "no_pujar"}`. Nunca lanza.
    """

    try:
        from datetime import datetime, timezone

        from src.actions.la_orden_del_gestor import (
            activa, leer_la_orden, validar,
        )

        orden = leer_la_orden()
        invalida = validar(orden, datetime.now(timezone.utc)) if orden else "SIN_ORDEN"
        venta = (orden or {}).get("vender_si_ficha") or {}

        def nombres(lista):
            return [x.get("nombre") for x in lista or [] if x.get("nombre")]

        return {
            "viva": bool(activa() and not invalida),
            "estado": "VIVA" if activa() and not invalida else (invalida or "APAGADA"),
            "caduca": (orden or {}).get("caduca"),
            "fichar": [
                {"nombre": f.get("nombre"), "puja": f.get("puja")}
                for f in (orden or {}).get("fichar") or []
            ],
            "vender": [
                {
                    "nombre": j.get("nombre"),
                    "suelo": j.get("suelo"),
                    "ultimo_recurso": bool(j.get("desde")),
                    "desde": j.get("desde"),
                }
                for j in venta.get("jugadores") or []
            ],
            "proteger": nombres((orden or {}).get("proteger")),
            "conservar": nombres((orden or {}).get("conservar")),
            "no_pujar": nombres((orden or {}).get("no_pujar")),
        }

    except Exception as error:                      # noqa: BLE001
        return {"viva": False, "estado": f"ERROR: {type(error).__name__}"}
