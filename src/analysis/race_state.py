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

    if datos.get("is_leader"):
        cabeza = f"Vas 1º, con {datos.get('points_ahead') or 0} de ventaja"

    else:
        cabeza = f"Vas {puesto}º, a {distancia} puntos"

    restantes = datos.get("matchdays_remaining")
    ritmo = datos.get("required_pace")

    if restantes is None:
        medio = ", jornadas restantes desconocidas (sin calendario)"

    elif restantes <= 0:
        medio = ", no quedan jornadas"

    elif ritmo is None:
        medio = f", quedan {restantes} jornadas"

    else:
        # Coma decimal: esta frase la lee una persona, en español.
        medio = (
            f", quedan {restantes} jornadas: necesitas sacarle "
            f"{ritmo:.2f}".replace(".", ",")
            + " por jornada"
        )

    brecha = datos.get("value_gap_to_leader")

    if brecha is None:
        cola = "."

    elif brecha > 0:
        cola = (
            f". Tu plantilla vale {brecha / 1_000_000:.1f}".replace(
                ".", ","
            )
            + " M menos que la del lider."
        )

    elif brecha < 0:
        cola = (
            f". Tu plantilla vale {abs(brecha) / 1_000_000:.1f}".replace(
                ".", ","
            )
            + " M mas que la del lider."
        )

    else:
        cola = ". Tu plantilla vale lo mismo que la del lider."

    return cabeza + medio + cola


def build_race_state(
    rival_squads: dict | None,
    calendar: dict | None = None,
    calendar_path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """
    El marcador de la temporada. Nunca lanza.

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

        somos_lider = bool(lider.get("is_current_user"))

        distancia = max(puntos_lider - nuestros_puntos, 0)

        # La ventaja solo tiene sentido si vamos primeros: es lo
        # que le sacamos al segundo.
        segundo = sorted(
            (m for m in managers if not m.get("is_current_user")),
            key=lambda m: -safe_int(m.get("points")),
        )

        ventaja = (
            nuestros_puntos - safe_int(segundo[0].get("points"))
            if somos_lider and segundo
            else None
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

        datos["urgency"] = _urgency(exigencia, distancia, restantes)
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
