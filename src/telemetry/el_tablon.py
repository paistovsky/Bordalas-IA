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
    "BORDALAS_LOS_CHOLLOS":
        "Puja por debajo de su valor por los del Computer que ya valen más de "
        "lo que piden, y los revende en cuanto hay beneficio (detrás de todo).",
    "BORDALAS_LA_RONDA_DE_LA_MANANA":
        "En cada vuelta puja (precio + 1 %) por los del Computer que suben, están "
        "bien y juegan, con toda la deuda, y se los revende al Computer antes de "
        "la jornada.",
    "BORDALAS_LA_PUJA_EN_9900":
        "La puja de la mejora del once termina en 9.900 (gana los empates: ninguna "
        "puja rival de las 186 más altas acaba entre 9.901 y 9.999).",
    "BORDALAS_LA_JORNADA_DE_CADA_PAGINA":
        "La mejora del once no saca a un titular sano ni mete a nadie por una "
        "alineación CONFIRMADA de FF de otra jornada (el 0 % o el 100 % de un "
        "partido ya jugado no es un pronóstico de la siguiente).",
    "BORDALAS_LA_MEJORA_SOLO_SI_SUBE":
        "La mejora del once solo ficha del Computer a quien sube hoy de verdad (la "
        "subida mínima de su tramo); al que baja solo para tapar un hueco "
        "(titular lesionado, sancionado o con menos del 50 % de titularidad).",
    "BORDALAS_LA_CARTERA":
        "La ronda compra a los que suben pujando para ganar (precio + 12 % por "
        "debajo de 1 M y + 4 % de 1 a 3 M, solo a 64 h o más de la jornada) y los "
        "AGUANTA mientras siguen subiendo, como Pollo17; el primer día que no suben "
        "los vende desde el 97 % de su valor, aunque pierda la prima. Cada compra "
        "cabe en el colchón (vendiéndolo todo al 92 % se empieza la jornada en "
        "positivo) y antes de cada jornada el cierre vende solo lo justo.",
    "BORDALAS_LA_PUERTA_A_PRECIO_DE_MERCADO":
        "La ronda también puja por los que venden otros managers, pero solo si "
        "piden su valor (como mucho un 2 % más), suben y juegan; la puja va a "
        "nombre del que lo vende y cada oferta se apunta para medir cuántas aceptan.",
    "BORDALAS_LA_MEJORA_DEL_ONCE":
        "En cada vuelta busca los cambios que más puntos suman al once (con deuda "
        "entre jornadas), puja por el que entra y vende al que sale cuando llega "
        "su relevo; en rojo, cambia caro por barato antes que jugar con 0.",
    "BORDALAS_EL_CALENDARIO_EN_LA_MEJORA":
        "La mejora del once mira las tres próximas jornadas, sin los partidos "
        "aplazados (en casa o fuera, y si el rival es duro: de los seis "
        "primeros de la tabla o de los cuatro con la plantilla más cara) y "
        "encoge a los de pocos partidos; es un desempate: nunca vende a uno "
        "mucho mejor por un calendario.",
    "BORDALAS_COMPRA_SOLO_SI_SUBE":
        "Para revender, solo compra jugadores cuyo precio está subiendo.",
    "BORDALAS_EL_ONCE_UNA_VEZ":
        "Calcula el mejor once una vez por vuelta y lo recuerda (más rápido).",
    "BORDALAS_LA_MEJORA_PUJA_FUERTE":
        "Cuando un fichaje mejora el once, puja más que el precio + 1 %: un 4 % "
        "más por cada punto por jornada que suma (hasta un 12 %), porque un "
        "punto por jornada vale más que lo que se paga de más.",
    "BORDALAS_EL_CIERRE_DE_LA_JORNADA":
        "Desde 64 h antes de cada jornada elige el mejor once con el calendario "
        "y, si la caja no llega a 0, vende a los que sobran (nunca a un titular "
        "del once escrito) hasta quedar en positivo; publica a los que se pueden "
        "vender para que llegue la oferta del Computer.",
    "BORDALAS_EL_MOTOR_VIEJO_SOLO_SI_SUBE":
        "El motor viejo (mejoras del once y especulación del tablero) solo puja por el que sube "
        "de verdad hoy, con la misma vara que la mejora: lo que bajaba el día de "
        "la puja dejó pérdidas.",
    "BORDALAS_UN_SOLO_COLCHON":
        "Con la cartera encendida, lo que puja el motor viejo (mejoras del once y "
        "especulación del tablero) tiene que caber en el mismo colchón que la "
        "ronda: saldo menos todas las pujas vivas más el 92 % de lo de la cartera. "
        "Lo suyo cuenta entero; si no cabe, no puja.",
    "BORDALAS_EL_PARTE_VENDE":
        "Vende a los suplentes que Biwenger da en duda o lesionados (caen un "
        "3-5 % en la semana): los publica a su valor y acepta la oferta del "
        "Computer desde el 95 %. Nunca a uno del once escrito (hacen falta el del "
        "panel y el de Biwenger), ni a un sancionado, ni a un fichaje que todavía "
        "no ha jugado una ronda con nosotros y nunca antes de 7 días (ni a uno sin "
        "fecha de fichaje: con el tablón atrasado, a nadie), ni a Yamal, "
        "ni a los protegidos o `conservar` del gestor, ni a lo que aguanta la "
        "cartera, ni con una ronda jugándose.",
    "BORDALAS_LA_ROTACION":
        "Cambia a uno de la plantilla que lleva dos días sin subir por uno de su "
        "posición que sube en el Computer y puntúa lo mismo o más (como mucho 2 "
        "por semana y entre jornada y jornada, y solo si la caja aguanta). Al que "
        "sale lo vende cuando el otro ya ha llegado, desde el 99 % de su valor, y "
        "si era titular pone al nuevo en su sitio del once. Nunca con una ronda "
        "jugándose.",
    "BORDALAS_EL_INFORME_DE_LA_MANANA":
        "Cada mañana, después del reset, mira a todos los jugadores nuevos del "
        "mercado (del Computer y de los managers) y les pone dos notas: cuánto "
        "puede subir su precio en una semana y cuántos puntos haría en la próxima "
        "jornada (con lo que ha subido hoy, si vale menos de 1 M, si FutbolFantasy "
        "dice que vuelve, su titularidad y la prensa). Solo lo apunta en su libro "
        "y lo deja en los datos del panel, que todavía no lo pinta: todavía no "
        "decide ninguna puja.",
    "BORDALAS_EL_CALENDARIO_EN_EL_ONCE":
        "Al elegir el once mira el partido de la próxima ronda: en casa contra "
        "uno que no es de los de arriba suma; fuera, o contra uno de arriba, "
        "resta un poco (desempata entre parecidos; si su equipo no juega esa "
        "ronda, ni suma ni resta).",
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
            "viajes": {
                "hasta": ((orden or {}).get("viajes") or {}).get("hasta"),
                "tope_por_viaje": ((orden or {}).get("viajes") or {}).get("tope_por_viaje"),
                "tope_total": ((orden or {}).get("viajes") or {}).get("tope_total"),
                "candidatos": [
                    {"nombre": c.get("nombre"), "puja": c.get("puja")}
                    for c in ((orden or {}).get("viajes") or {}).get("candidatos") or []
                ],
            },
            "hoja_de_ruta": (orden or {}).get("hoja_de_ruta"),
        }

    except Exception as error:                      # noqa: BLE001
        return {"viva": False, "estado": f"ERROR: {type(error).__name__}"}
