"""
En que carrera va Pepe. Solo mirar el marcador.

POR QUE EXISTE

    Pepe no sabe que va cuarto. Nada en el codigo lee la
    clasificacion para decidir: pujaria igual siendo primero con
    veinte de ventaja que ultimo a cuarenta. Toda la maquinaria
    esta bien construida y juega a ciegas sobre el resultado.

    Esto pone el marcador por escrito. Nada mas.

FASE OBSERVADOR

    No decide. No escribe en Biwenger. No entra en ninguna
    valoracion, en ningun umbral y en ningun guardarrail. Ningun
    motor lo importa: se calcula, se publica en el dashboard, y
    ahi acaba su trabajo.

    El dia que alguien quiera condicionar la agresividad al
    puesto, tendra el numero hecho y medido. Hoy no.

QUE MIDE, Y POR QUE ASI

    La pregunta util no es "¿a cuantos puntos vas?" sino
    "¿cuanto mejor que el lider hay que ser, cada jornada, para
    llegar?".

        ritmo necesario = distancia / jornadas restantes

    Sobre la foto del 04/09/2026 -13 puntos de distancia, tres
    jornadas jugadas, 35 por delante- salen 0,37 puntos por
    jornada. Dicho asi parece poquisimo, y ES poquisimo, y eso es
    exactamente lo que hay que ver.

    Pero 0,37 puntos no significan nada sueltos: hay que saber
    contra que. Asi que tambien se mide en proporcion de lo que
    Pepe saca en una jornada normal:

        exigencia = ritmo necesario / puntos por jornada

    0,37 sobre los 44,3 puntos por jornada que lleva sacando es
    un 0,8 %. Necesita ser menos de un 1 % mejor que el lider
    cada jornada. Ese es el numero honesto, y es el que ordena la
    urgencia.

DE DONDE SALE CADA COSA

    Puesto, puntos y valor de plantilla: de `rival_squads`, que
    los saca de la clasificacion de Biwenger.

    Jornadas jugadas: del calendario real de LaLiga
    (`data/calendar/laliga_calendar.json`), contando las que ya
    han terminado del todo. No del `matchday` en curso, que dice
    cual se juega y no cuantas se han jugado.

AUSENCIA DE DATO != DATO

    Sin calendario no hay jornadas restantes, y sin jornadas
    restantes no hay ritmo necesario: van None y se dice por que.
    Un ritmo inventado sobre 38 jornadas fijas seria un numero
    con pinta de medida.
"""

from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


CALENDAR_FILE = (
    Path("data")
    / "calendar"
    / "laliga_calendar.json"
)

# LaLiga son 38 jornadas. Si el calendario trae otra cosa, manda
# el calendario: es el dato real y esto solo es el respaldo.
SEASON_MATCHDAYS = 38

# Una jornada se da por terminada dos horas despues del ultimo
# saque inicial. Es el mismo criterio que usa el resto del
# sistema para desbloquear el trabajo de la jornada siguiente.
MATCH_DURATION_HOURS = 2


# ============================================================
# LA ESCALA DE URGENCIA
# ============================================================
#
#     Se ordena por EXIGENCIA -que porcentaje de una jornada
#     normal hay que sacarle al lider cada jornada-, no por
#     puntos de distancia. Trece puntos en la jornada 4 y trece
#     puntos en la jornada 35 son la misma distancia y no son ni
#     de lejos el mismo problema.
#
#     Los cortes estan puestos contra lo que se puede sacar en
#     una jornada, no elegidos a ojo:
#
#     LIDER          Vas primero. No hay distancia que recuperar.
#                    Y ADEMAS lo que queda por contar no te lo
#                    puede quitar (ver EN_JUEGO, abajo).
#
#     EN_JUEGO       Vas primero en las jornadas cerradas, pero hay
#                    rondas abiertas sin contar y la ventaja no
#                    llega al margen de seguridad. No se dice
#                    LIDER: el 19/10 se decia con 3 de ventaja y la
#                    J8 abierta ya ponia a Pollo17 treinta por
#                    delante.
#
#     COMODA         < 1 %. Una sola jornada buena lo cubre. La
#                    distancia es ruido: la temporada decide.
#
#     EXIGENTE       1-3 %. Hay que ser mejor de forma sostenida,
#                    pero cabe dentro de lo normal.
#
#     DIFICIL        3-6 %. Hace falta una ventaja clara y
#                    mantenida, no una buena racha.
#
#     MUY_DIFICIL    6-15 %. Se necesita que el lider falle.
#
#     FUERA_DE_ALCANCE  > 15 %, o no quedan jornadas. Con el
#                    ritmo que haria falta, no da la temporada.
URGENCY_THRESHOLDS = (
    (0.01, "COMODA"),
    (0.03, "EXIGENTE"),
    (0.06, "DIFICIL"),
    (0.15, "MUY_DIFICIL"),
)

URGENCY_UNKNOWN = "SIN_DATOS"

URGENCY_EN_JUEGO = "EN_JUEGO"


# ============================================================
# LAS RONDAS QUE TODAVIA NO CUENTAN  (19/10/2026)
# ============================================================
#
# EL SINTOMA
#
#     El panel decia LIDER con 323 contra los 320 de Pollo17. El
#     dueño, con la app en la mano: la J8 sigue abierta por el
#     Rayo-Athletic suspendido, y en ella Pollo hizo 74 y
#     nosotros 44. Al cerrarla vamos SEGUNDOS.
#
# LA CAUSA
#
#     `standings[].points` es la clasificacion de Biwenger, y
#     Biwenger solo suma una ronda cuando la CIERRA. Una jornada
#     con un partido aplazado se queda abierta semanas, y el
#     partido aplazado se juega como ronda aparte (el
#     Levante-Athletic de la J6, el 21/10). Todo lo que hay
#     dentro de una ronda abierta es invisible para la
#     clasificacion.
#
# LO QUE SE BUSCO, Y NO ESTA
#
#     La clasificacion PROVISIONAL —lo que lleva cada manager en
#     las rondas abiertas— no la publica ninguna fuente que lea
#     el ciclo:
#
#       - `rounds/league` -> `standings[].points`: solo cerradas
#         (323 con la J8 y la J9 jugadas).
#       - El tablon: `roundFinished` trae los puntos de cada
#         manager, pero SOLO al cerrar la ronda.
#       - El ledger de rivales: plantillas y caja, sin puntos de
#         ronda.
#       - El marcador: reconstruye los NUESTROS de cada jornada,
#         no los de los rivales.
#
#     Reconstruir los de los rivales con sus onces seria
#     inventar: `standings[].lineup` llego a ir cinco dias por
#     detras del once vigente (`el_once_que_jugo`). Asi que no se
#     publica ninguna clasificacion provisional: se publica que
#     no la hay y por que.
#
# LO QUE SI SE SABE
#
#     QUE rondas estan abiertas. El tablon publica
#     `roundStarted` al empezar cada ronda y `roundFinished` al
#     cerrarla, con el mismo `round.id`. Empezada y sin cerrar =
#     abierta: sus puntos no estan en la clasificacion.
#
#     Y CUANTO puede mover una ronda: lo mas que un rival nos ha
#     sacado en una sola ronda cerrada, medido en el mismo
#     tablon (35, Luismi en la J6 aplazada; el dueño vio 30 en la
#     J8). Con un suelo para que una temporada corta no lo deje
#     pequeño.
#
# LA REGLA
#
#     Vamos LIDER solo si la ventaja pasa de
#
#         margen por ronda x rondas abiertas
#
#     Si no llega, la etiqueta es EN_JUEGO. Si no se sabe que
#     rondas hay abiertas (sin tablon), tampoco se dice LIDER: se
#     dice SIN_DATOS. Ausencia de dato != dato.
#
# EL LADO DEL ERROR
#
#     Si Biwenger dejase una ronda empezada sin cerrar para
#     siempre, aqui saldria abierta para siempre y el panel diria
#     EN_JUEGO de mas. Es el lado bueno del error, y la lista va
#     publicada con su fecha de inicio para que se vea: en el
#     JSON (`empezo`) y en la frase que pinta el panel
#     (`por_que`: "Jornada 6 desde el 03/09"), ver `_con_fecha`.

# El suelo del margen, en puntos por ronda abierta. Por encima
# de todo lo medido el 19/10/2026: el mayor hueco de un rival
# sobre nosotros en una ronda cerrada era 35 (tablon) y el de la
# J8 abierta, 30 (app del dueño). Si el tablon mide mas, manda
# el tablon.
SUELO_DEL_MARGEN_POR_RONDA = 40


def _ronda_del_evento(evento) -> dict | None:
    """El `round` de un evento del tablon, o None si no lo trae."""

    if not isinstance(evento, dict):
        return None

    contenido = evento.get("content")

    if not isinstance(contenido, dict):
        return None

    ronda = contenido.get("round")

    if not isinstance(ronda, dict) or not safe_int(ronda.get("id")):
        return None

    return ronda


def _fecha_iso(epoch) -> str | None:
    segundos = safe_int(epoch)

    if not segundos:
        return None

    try:
        return datetime.fromtimestamp(
            segundos,
            tz=timezone.utc,
        ).isoformat()

    except (OverflowError, OSError, ValueError):
        return None


def find_open_rounds(eventos) -> list | None:
    """
    Las rondas de Biwenger empezadas y sin cerrar, segun el tablon.

    None si no se puede saber: sin tablon, o un tablon sin una
    sola ronda empezada. Una lista vacia es otra cosa: se sabe,
    y no hay ninguna abierta.
    """

    if not isinstance(eventos, list):
        return None

    empezadas = {}
    cerradas = set()

    for evento in eventos:

        if not isinstance(evento, dict):
            continue

        tipo = evento.get("type")

        if tipo not in ("roundStarted", "roundFinished"):
            continue

        ronda = _ronda_del_evento(evento)

        if ronda is None:
            continue

        round_id = safe_int(ronda.get("id"))

        if tipo == "roundFinished":
            cerradas.add(round_id)
            continue

        fecha = safe_int(evento.get("date"))
        previa = empezadas.get(round_id)

        # El tablon reemite: se queda la PRIMERA vez que empezo.
        if previa is not None and (
            not fecha or (previa["_fecha"] and previa["_fecha"] <= fecha)
        ):
            continue

        empezadas[round_id] = {
            "_fecha": fecha,
            "round_id": round_id,
            "nombre": str(ronda.get("name") or f"Ronda {round_id}"),
            "parte": safe_int(ronda.get("part")) or None,
            "empezo": _fecha_iso(fecha),
        }

    if not empezadas:
        return None

    abiertas = sorted(
        (
            fila
            for round_id, fila in empezadas.items()
            if round_id not in cerradas
        ),
        key=lambda fila: (fila["_fecha"] or 0, fila["round_id"]),
    )

    return [
        {k: v for k, v in fila.items() if not k.startswith("_")}
        for fila in abiertas
    ]


def measure_round_margin(eventos, mi_user_id) -> dict:
    """
    Cuanto puede movernos una ronda: lo mas que un rival nos ha
    sacado en UNA ronda cerrada, medido en el tablon, con suelo.

    Se mide con los puntos que publica `roundFinished`, tal cual.
    Si a alguien se le anularon por saldo negativo (Luismi en la
    J6 aplazada: 64 publicados, 0 sumados), aqui cuentan los 64:
    el margen es de seguridad y se mide por arriba.
    """

    mi_user_id = safe_int(mi_user_id)

    medido = None
    donde = None
    vistas = set()

    for evento in (eventos if isinstance(eventos, list) else []):

        if not isinstance(evento, dict):
            continue

        if evento.get("type") != "roundFinished":
            continue

        ronda = _ronda_del_evento(evento)

        if ronda is None:
            continue

        round_id = safe_int(ronda.get("id"))

        # El tablon reemite la misma ronda: se mide una vez.
        if round_id in vistas:
            continue

        resultados = (evento.get("content") or {}).get("results")

        if not isinstance(resultados, list):
            continue

        nuestros = None
        mejor = None
        quien = None

        for fila in resultados:

            if not isinstance(fila, dict):
                continue

            puntos = fila.get("points")

            if isinstance(puntos, bool) or not isinstance(
                puntos, (int, float)
            ):
                continue

            usuario = fila.get("user")
            usuario = usuario if isinstance(usuario, dict) else {}

            if mi_user_id and safe_int(usuario.get("id")) == mi_user_id:
                nuestros = int(puntos)

            elif mejor is None or puntos > mejor:
                mejor = int(puntos)
                quien = usuario.get("name")

        if nuestros is None or mejor is None:
            continue

        vistas.add(round_id)

        hueco = mejor - nuestros

        if medido is None or hueco > medido:
            medido = hueco
            donde = {
                "round_id": round_id,
                "nombre": ronda.get("name"),
                "rival": quien,
                "suyos": mejor,
                "nuestros": nuestros,
            }

    return {
        "por_ronda": max(medido or 0, SUELO_DEL_MARGEN_POR_RONDA),
        "medido": medido,
        "medido_en": donde,
        "rondas_medidas": len(vistas),
        "suelo": SUELO_DEL_MARGEN_POR_RONDA,
    }


def _rondas(n: int) -> str:
    return "1 ronda abierta" if n == 1 else f"{n} rondas abiertas"


def _lista(nombres: list) -> str:
    nombres = [str(n) for n in nombres if n]

    if len(nombres) <= 1:
        return "".join(nombres)

    return ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _con_fecha(ronda: dict) -> str | None:
    """
    "Jornada 8 desde el 09/10": el nombre y el dia en que empezo,
    en hora de Madrid.

    LA FECHA SE VE (19/10/2026)

        El lado del error de `find_open_rounds` es una ronda que
        Biwenger no cierre nunca: saldria abierta para siempre.
        La salvaguarda era que la lista lleva su fecha de inicio,
        pero `empezo` solo estaba en el JSON y el panel pinta la
        frase. Una "Jornada 6 desde el 03/09" en octubre se ve;
        una "Jornada 6" a secas, no.
    """

    if not isinstance(ronda, dict):
        return None

    nombre = ronda.get("nombre")

    if not nombre:
        return None

    try:
        cuando = datetime.fromisoformat(str(ronda.get("empezo") or ""))

    except ValueError:
        return str(nombre)

    try:
        from zoneinfo import ZoneInfo

        cuando = cuando.astimezone(ZoneInfo("Europe/Madrid"))

    except Exception:                                    # noqa: BLE001
        pass

    return f"{nombre} desde el {cuando.strftime('%d/%m')}"


def _por_que(datos: dict) -> str:
    """Por que la etiqueta dice lo que dice, para el dueño."""

    abiertas = datos.get("jornadas_abiertas")
    lider = datos.get("is_leader")
    ventaja = datos.get("points_ahead") or 0

    if not datos.get("season_started", True):
        return "Nadie ha puntuado todavia: no hay carrera que contar."

    if abiertas is None:
        return (
            f"No se sabe que rondas estan abiertas "
            f"({datos.get('jornadas_abiertas_motivo')}). La "
            f"clasificacion de Biwenger solo suma las rondas "
            f"cerradas, asi que "
            + (
                "no se nos da por lideres sin saber que falta por "
                "contar."
                if lider
                else "la distancia puede no ser la de verdad."
            )
        )

    if not abiertas:
        return (
            "Todas las rondas empezadas estan cerradas: la "
            "clasificacion cuenta todo lo jugado."
        )

    margen = datos.get("margen_de_seguridad") or {}
    total = margen.get("total") or 0
    medido_en = margen.get("medido_en") or {}

    frase = (
        f"La clasificacion de Biwenger solo suma las rondas "
        f"cerradas. Hay {_rondas(len(abiertas))} cuyos puntos "
        f"todavia no cuentan: "
        f"{_lista([_con_fecha(r) for r in abiertas])}. Ninguna "
        f"fuente que leamos publica cuantos lleva cada manager en "
        f"ellas: el tablon solo los da al cerrar."
    )

    # UN HUECO NEGATIVO NO ES UN HUECO (19/10/2026)
    #
    #     Si en todas las rondas cerradas hicimos mas que cada
    #     rival, `medido` sale <= 0 y la frase decia "un rival nos
    #     ha llegado a sacar -5". Nadie nos ha sacado nada: manda
    #     el suelo, y se dice asi.
    medido = margen.get("medido")

    if medido is not None and medido > 0 and medido_en:
        frase += (
            f" En una sola ronda un rival nos ha llegado a sacar "
            f"{medido}: {medido_en.get('rival')} en la "
            f"{medido_en.get('nombre')}"
        )

    elif medido is not None:
        frase += (
            f" En las rondas cerradas ningun rival nos ha sacado "
            f"puntos en una sola ronda, asi que manda el suelo de "
            f"{margen.get('suelo')}"
        )

    else:
        frase += " Sin rondas cerradas que medir"

    frase += (
        f"; se cuentan {margen.get('por_ronda')} por ronda abierta, "
        f"{total} en total."
    )

    if lider and datos.get("lider_asegurado"):
        frase += (
            f" Con {ventaja} de ventaja no nos alcanzan ni "
            f"perdiendo eso en todas: vamos primeros aunque cierren "
            f"mal."
        )

    elif lider:
        frase += (
            f" Con {ventaja} de ventaja eso no asegura nada: no se "
            f"nos da por lideres hasta que cierren o la ventaja pase "
            f"de {total}."
        )

    else:
        frase += (
            f" La distancia de {datos.get('points_behind') or 0} "
            f"puede moverse hasta {total} en cualquier sentido "
            f"cuando cierren."
        )

    return frase


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _load_calendar(path: Path | None = None) -> dict | None:
    path = path or CALENDAR_FILE

    try:
        valor = json.loads(path.read_text(encoding="utf-8-sig"))

    except (OSError, json.JSONDecodeError):
        return None

    return valor if isinstance(valor, dict) else None


def _kickoff(match: dict) -> datetime | None:
    crudo = (match or {}).get("kickoff")

    if not crudo:
        return None

    try:
        momento = datetime.fromisoformat(
            str(crudo).replace("Z", "+00:00")
        )

    except ValueError:
        return None

    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)

    return momento


def count_finished_matchdays(
    calendar: dict | None,
    now: datetime | None = None,
) -> tuple[int | None, int | None]:
    """
    (jornadas terminadas, jornadas de la temporada).

    Terminada = su ultimo partido empezo hace mas de dos horas.
    Una jornada a medias NO cuenta como jugada: sus puntos
    todavia se estan repartiendo.
    """

    if not calendar:
        return (None, None)

    jornadas = calendar.get("matchdays")

    if not isinstance(jornadas, list) or not jornadas:
        return (None, None)

    now = now or datetime.now(timezone.utc)

    terminadas = 0

    for jornada in jornadas:

        if not isinstance(jornada, dict):
            continue

        saques = [
            momento
            for momento in (
                _kickoff(partido)
                for partido in (jornada.get("matches") or [])
                if isinstance(partido, dict)
            )
            if momento is not None
        ]

        if not saques:
            continue

        final = max(saques) + timedelta(hours=MATCH_DURATION_HOURS)

        if final <= now:
            terminadas += 1

    return (terminadas, len(jornadas))


def _urgency(
    exigencia: float | None,
    distancia: int,
    restantes: int | None,
) -> str:

    if distancia <= 0:
        return "LIDER"

    # Sin jornadas por delante y todavia por detras: eso no es
    # "no lo se", es que se acabo. Distinguirlo importa, porque
    # SIN_DATOS invita a mirar otra vez y esto no.
    if restantes == 0:
        return "FUERA_DE_ALCANCE"

    if exigencia is None:
        return URGENCY_UNKNOWN

    for corte, etiqueta in URGENCY_THRESHOLDS:
        if exigencia < corte:
            return etiqueta

    return "FUERA_DE_ALCANCE"


def _headline(datos: dict) -> str:
    """La frase que va a leer el dueño, con lo que se sepa."""

    puesto = datos.get("position")
    distancia = datos.get("points_behind")

    if puesto is None:
        return (
            "No se pudo leer la clasificacion: sin puesto no hay "
            "carrera que contar."
        )

    # Antes que nada: si nadie ha puntuado, no hay carrera. La
    # distancia es cero porque no se ha jugado, no porque vayamos
    # bien, y contarlo como ir bien seria tranquilizar por falta
    # de datos.
    if not datos.get("season_started", True):
        return (
            f"La temporada no ha empezado: los "
            f"{datos.get('managers_count') or 0} managers estan a "
            f"cero. Todavia no hay carrera que medir."
        )

    # PRIMEROS EN LO CERRADO NO ES IR PRIMEROS (19/10/2026)
    #
    #     `lider_asegurado` solo existe cuando se ha mirado el
    #     tablon. Si vale False siendo `is_leader`, la ventaja es
    #     de las rondas cerradas y lo abierto la puede tumbar: la
    #     frase no dice "Vas 1º" a secas. Sin la clave (quien
    #     llama sin tablon a `_headline`) se queda como estaba.
    abiertas = datos.get("jornadas_abiertas")
    en_el_aire = (
        datos.get("is_leader")
        and datos.get("lider_asegurado") is False
    )

    if en_el_aire and abiertas:
        cabeza = (
            f"Vas 1º solo en las rondas cerradas, con "
            f"{datos.get('points_ahead') or 0} de ventaja: hay "
            f"{_rondas(len(abiertas))} sin contar "
            f"({_lista([r.get('nombre') for r in abiertas])}) y "
            f"hasta que cierren no se sabe quien va primero"
        )

    elif en_el_aire:
        # El motivo es el que ya calculo `build_race_state`: "sin
        # el tablon" a secas mentia cuando el tablon SI llego pero
        # sin una sola ronda empezada (19/10/2026).
        cabeza = (
            f"Vas 1º en las rondas cerradas, con "
            f"{datos.get('points_ahead') or 0} de ventaja, pero no "
            f"se sabe que rondas quedan por contar ("
            f"{datos.get('jornadas_abiertas_motivo') or 'sin el tablon'}"
            f")"
        )

    elif datos.get("is_leader"):
        cabeza = f"Vas 1º, con {datos.get('points_ahead') or 0} de ventaja"

    else:
        cabeza = f"Vas {puesto}º, a {distancia} puntos"

    if abiertas and not en_el_aire:
        cabeza += (
            f" (solo rondas cerradas; {_rondas(len(abiertas))} sin "
            f"contar)"
        )

    restantes = datos.get("matchdays_remaining")
    ritmo = datos.get("required_pace")

    if en_el_aire:
        # "Necesitas sacarle 0,00 por jornada" al lado de "no se
        # sabe quien va primero" se contradice. Se dice lo que
        # queda y nada mas.
        medio = (
            f"; quedan {restantes} jornadas"
            if restantes
            else ""
        )

    elif restantes is None:
        medio = ", jornadas restantes desconocidas (sin calendario)"

    elif restantes <= 0:
        medio = ", no quedan jornadas"

    elif ritmo is None:
        medio = f", quedan {restantes} jornadas"

    else:
        # Coma decimal: esta frase la lee una persona, en español.
        medio = (
            f", quedan {restantes} jornadas: necesitas sacarle "
            + f"{ritmo:.2f}".replace(".", ",")
            + " por jornada"
        )

    # CUANDO SOMOS LIDERES, EL LIDER SOMOS NOSOTROS (19/09/2026)
    #
    #     `value_gap_to_leader = valor_lider - nuestro_valor`. El
    #     dia que vamos primeros esa resta da CERO por
    #     construccion, y la frase salia "Tu plantilla vale lo
    #     mismo que la del lider": nos comparaba con nosotros
    #     mismos y tapaba que el segundo tenia 93,06 M contra
    #     nuestros 57,35 M.
    #
    #     La cabeza de esta misma frase ya usaba `is_leader` dos
    #     lineas mas arriba. El dato estaba; la cola no lo miraba.
    #
    #     Siendo lideres, la comparacion util es contra EL
    #     SEGUNDO. Y se dice contra quien, porque el segundo por
    #     puntos no tiene por que ser el segundo por dinero.
    if datos.get("is_leader"):
        brecha = datos.get("value_gap_to_runner_up")
        nombre_del_otro = datos.get("runner_up_name")
        contra = (
            f"de {nombre_del_otro}"
            if nombre_del_otro
            else "del segundo"
        )

    else:
        brecha = datos.get("value_gap_to_leader")
        contra = "del lider"

    if brecha is None:
        cola = "."

    elif brecha > 0:
        cola = (
            ". Tu plantilla vale "
            + f"{brecha / 1_000_000:.1f}".replace(".", ",")
            + f" M menos que la {contra}."
        )

    elif brecha < 0:
        cola = (
            ". Tu plantilla vale "
            + f"{abs(brecha) / 1_000_000:.1f}".replace(".", ",")
            + f" M mas que la {contra}."
        )

    else:
        cola = f". Tu plantilla vale lo mismo que la {contra}."

    return cabeza + medio + cola


def build_race_state(
    rival_squads: dict | None,
    calendar: dict | None = None,
    calendar_path: Path | None = None,
    now: datetime | None = None,
    eventos: list | None = None,
) -> dict:
    """
    El marcador de la temporada. Nunca lanza.

    `eventos` es el tablon (los eventos normalizados de
    `collect_board_history`). De ahi salen las rondas abiertas y
    el margen de seguridad. Sin el no se sabe que falta por
    contar, y no se dice LIDER.

    FASE OBSERVADOR: ningun motor lee esto.
    """

    try:
        managers = [
            m
            for m in ((rival_squads or {}).get("managers") or [])
            if isinstance(m, dict)
        ]

        if not managers:
            return {
                "available": False,
                "reason": (
                    "No hay clasificacion: sin los puestos de los "
                    "managers no se puede decir en que carrera va."
                ),
                "observer_only": True,
                "managers": [],
            }

        # ------------------------------------------------------
        # QUIENES SOMOS Y QUIEN VA DELANTE
        # ------------------------------------------------------

        nosotros = next(
            (m for m in managers if m.get("is_current_user")),
            None,
        )

        if nosotros is None:
            return {
                "available": False,
                "reason": (
                    "La clasificacion no dice cual de los managers "
                    "somos nosotros: sin eso no hay distancia que "
                    "medir."
                ),
                "observer_only": True,
                "managers": [],
            }

        # El lider es el de mas puntos, no el que venga primero en
        # la lista: el orden lo pone `rank`, y `rank` viene de
        # fuera.
        lider = max(managers, key=lambda m: safe_int(m.get("points")))

        nuestros_puntos = safe_int(nosotros.get("points"))
        puntos_lider = safe_int(lider.get("points"))

        # LOS OTROS SEIS, PARA NO CONFUNDIR EMPATE CON VENTAJA
        otros = sorted(
            (m for m in managers if not m.get("is_current_user")),
            key=lambda m: -safe_int(m.get("points")),
        )

        mejor_de_los_otros = (
            safe_int(otros[0].get("points")) if otros else 0
        )

        # IR PRIMERO ES IR POR DELANTE, NO IR IGUALADO
        #
        #     `max()` con empate devuelve el primero de la lista.
        #     Con toda la liga a cero eso nos coronaba lideres, y
        #     la frase salia "Vas 7º, a 0 puntos" con urgencia
        #     LIDER: dos cosas contradictorias en el mismo
        #     renglon.
        somos_lider = bool(
            otros and nuestros_puntos > mejor_de_los_otros
        )

        distancia = max(puntos_lider - nuestros_puntos, 0)

        ventaja = (
            nuestros_puntos - mejor_de_los_otros
            if somos_lider
            else None
        )

        # LA TEMPORADA NO HA EMPEZADO
        #
        #     Si nadie ha puntuado todavia no hay carrera que
        #     medir: la distancia es cero porque no se ha jugado,
        #     no porque vayamos bien. Decir "COMODA" ahi seria
        #     tranquilizar por falta de datos.
        temporada_empezada = (
            max(safe_int(m.get("points")) for m in managers) > 0
        )

        # ------------------------------------------------------
        # CUANTA TEMPORADA QUEDA
        # ------------------------------------------------------

        if calendar is None:
            calendar = _load_calendar(calendar_path)

        jugadas, del_calendario = count_finished_matchdays(
            calendar,
            now=now,
        )

        total_jornadas = del_calendario or SEASON_MATCHDAYS

        restantes = (
            max(total_jornadas - jugadas, 0)
            if jugadas is not None
            else None
        )

        sin_calendario = jugadas is None

        # ------------------------------------------------------
        # EL RITMO QUE HACE FALTA
        # ------------------------------------------------------

        ritmo = (
            round(distancia / restantes, 3)
            if restantes
            else None
        )

        # Lo que Pepe saca en una jornada normal. Es la vara con
        # la que el ritmo necesario significa algo.
        por_jornada = (
            round(nuestros_puntos / jugadas, 2)
            if jugadas
            else None
        )

        exigencia = (
            round(ritmo / por_jornada, 5)
            if ritmo is not None and por_jornada
            else None
        )

        # ------------------------------------------------------
        # LA BRECHA DE PLANTILLA
        # ------------------------------------------------------

        nuestro_valor = safe_int(nosotros.get("team_value"))
        valor_lider = safe_int(lider.get("team_value"))

        # EL SEGUNDO, PARA CUANDO EL LIDER SEAMOS NOSOTROS
        #
        #     Siendo lideres, compararse con el lider es
        #     compararse con uno mismo y da cero siempre. El
        #     segundo por PUNTOS, que es la carrera que se
        #     cuenta; su valor puede no ser el segundo mayor de
        #     la liga, y por eso la frase dice contra quien.
        detras = [m for m in managers if m is not lider]

        segundo = (
            max(
                detras,
                key=lambda m: safe_int(m.get("points")),
            )
            if detras
            else None
        )

        valor_segundo = (
            safe_int(segundo.get("team_value"))
            if segundo
            else 0
        )

        valores = [safe_int(m.get("team_value")) for m in managers]
        valores_reales = [v for v in valores if v > 0]

        media_liga = (
            round(sum(valores_reales) / len(valores_reales))
            if valores_reales
            else None
        )

        datos = {
            "available": True,
            "reason": None,

            # Que no haya duda leyendo el JSON.
            "observer_only": True,

            "position": safe_int(
                nosotros.get("rank"),
                default=0,
            ) or None,
            "points": nuestros_puntos,
            "is_leader": somos_lider,

            # Sin una sola jornada jugada no hay carrera que
            # medir, y hay que decirlo antes que cualquier
            # otra cosa.
            "season_started": temporada_empezada,

            "leader_name": lider.get("name"),
            "leader_points": puntos_lider,
            "points_behind": distancia,
            "points_ahead": ventaja,

            "matchdays_total": total_jornadas,
            "matchdays_played": jugadas,
            "matchdays_remaining": restantes,

            "required_pace": ritmo,
            "points_per_matchday": por_jornada,
            "required_pace_share": exigencia,

            "team_value": nuestro_valor,
            "leader_team_value": valor_lider,
            "value_gap_to_leader": (
                valor_lider - nuestro_valor
                if valor_lider and nuestro_valor
                else None
            ),

            # Contra el segundo: lo que se compara cuando el
            # lider somos nosotros.
            "runner_up_name": (
                segundo.get("name") if segundo else None
            ),
            "runner_up_points": (
                safe_int(segundo.get("points"))
                if segundo
                else None
            ),
            "runner_up_team_value": valor_segundo,
            "value_gap_to_runner_up": (
                valor_segundo - nuestro_valor
                if valor_segundo and nuestro_valor
                else None
            ),
            "league_average_value": media_liga,
            "value_gap_to_average": (
                media_liga - nuestro_valor
                if media_liga and nuestro_valor
                else None
            ),

            "managers_count": len(managers),

            "calendar_available": not sin_calendario,
            "calendar_reason": (
                "No se pudo leer el calendario de LaLiga: sin el no "
                "hay jornadas restantes, y sin jornadas restantes no "
                "hay ritmo necesario."
                if sin_calendario
                else None
            ),
        }

        # ------------------------------------------------------
        # LO QUE LA CLASIFICACION TODAVIA NO CUENTA (19/10/2026)
        # ------------------------------------------------------
        #
        #     Los puntos de arriba son los de Biwenger: solo
        #     rondas cerradas. Lo abierto no se suma porque nadie
        #     lo publica por manager; se dice que rondas son, cuanto
        #     pueden mover, y si con eso la ventaja aguanta.
        abiertas = find_open_rounds(eventos)

        datos["clasificacion_cuenta"] = "SOLO_RONDAS_CERRADAS"
        datos["jornadas_abiertas"] = abiertas
        datos["jornadas_abiertas_motivo"] = (
            None
            if abiertas is not None
            else (
                "no se paso el tablon"
                if not isinstance(eventos, list)
                else "el tablon no trae ninguna ronda empezada"
            )
        )

        datos["clasificacion_provisional"] = None
        datos["clasificacion_provisional_motivo"] = (
            "Ninguna fuente que lea el ciclo publica los puntos de "
            "cada manager en las rondas abiertas: la clasificacion "
            "de Biwenger solo suma las cerradas, el tablon da los "
            "resultados al cerrar y el marcador solo reconstruye "
            "los nuestros. No se inventan."
        )

        if abiertas is None:
            datos["margen_de_seguridad"] = None

        else:
            margen = measure_round_margin(
                eventos,
                nosotros.get("user_id"),
            )
            margen["rondas_abiertas"] = len(abiertas)
            margen["total"] = margen["por_ronda"] * len(abiertas)
            datos["margen_de_seguridad"] = margen

        datos["lider_asegurado"] = bool(
            somos_lider
            and abiertas is not None
            and (
                not abiertas
                or (ventaja or 0)
                > datos["margen_de_seguridad"]["total"]
            )
        )

        urgencia = (
            _urgency(exigencia, distancia, restantes)
            if temporada_empezada
            else URGENCY_UNKNOWN
        )

        # LIDER solo si lo abierto no nos lo puede quitar. Si hay
        # rondas abiertas y la ventaja no llega, EN_JUEGO; si no
        # se sabe que hay abierto, SIN_DATOS.
        if urgencia == "LIDER" and not datos["lider_asegurado"]:

            if abiertas is None:
                urgencia = URGENCY_UNKNOWN

            elif abiertas:
                urgencia = URGENCY_EN_JUEGO

        datos["urgency"] = urgencia
        datos["urgency_scale"] = [
            etiqueta for _, etiqueta in URGENCY_THRESHOLDS
        ] + ["FUERA_DE_ALCANCE"]

        # La tabla de la carrera: todos, ordenados por puntos, con
        # lo que nos separa de cada uno.
        datos["managers"] = [
            {
                "user_id": m.get("user_id"),
                "name": m.get("name"),
                "rank": safe_int(m.get("rank")) or None,
                "points": safe_int(m.get("points")),
                "points_vs_us": (
                    safe_int(m.get("points")) - nuestros_puntos
                ),
                "team_value": safe_int(m.get("team_value")),
                "value_vs_us": (
                    safe_int(m.get("team_value")) - nuestro_valor
                ),
                "squad_size": safe_int(m.get("squad_size")),
                "is_current_user": bool(m.get("is_current_user")),
                "is_leader": m is lider,
            }
            for m in sorted(
                managers,
                key=lambda item: -safe_int(item.get("points")),
            )
        ]

        datos["headline"] = _headline(datos)
        datos["por_que"] = _por_que(datos)

        return datos

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo construir el estado de carrera: "
                f"{type(error).__name__}: {error}"
            ),
            "observer_only": True,
            "managers": [],
        }
