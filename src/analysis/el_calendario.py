"""
El calendario: contra quien juega cada uno de los nuestros.

POR QUE HACE FALTA (13/09/2026)

    `data/calendar/laliga_calendar.json` esta vivo —380 partidos,
    refrescado hoy— y NO LO MIRA NADIE. Ni una decision, ni una
    pantalla. Es el mejor dato desaprovechado que tenemos.

    Saber que un jugador nuestro tiene tres partidos seguidos
    contra los tres primeros no cambia nada hoy, pero es la
    diferencia entre "este mes rinde poco" y "este mes le toca lo
    mas duro de la liga".

LO QUE HACE ESTE MODULO

    Cruza tres cosas que YA EXISTEN:

        el equipo de cada jugador nuestro   `team_id`
        los proximos partidos de ese equipo  el calendario
        el puesto del rival                  la clasificacion

    Ni una peticion nueva. Es juntar.

LO QUE NO HACE

    NINGUNA DECISION SALE DE AQUI. Ni una puja, ni una venta, ni
    un umbral. Primero el dueño quiere ver si dice cosas
    sensatas.

EL CASADO, Y LO QUE PASA SI FALLA

    Las fichas del calendario casan con las de la clasificacion
    POR NOMBRE. Hoy casan las veinte, comprobado. El dia que una
    no case, SE DICE EN LA PANTALLA y el equipo sale con su
    puesto "sin dato": tirarlo en silencio dejaria una fila menos
    y nadie se enteraria.

REGLA 23

    No lee ficheros. Calendario, clasificacion y plantilla llegan
    como argumentos.
"""

from __future__ import annotations

from datetime import datetime, timezone


# LOS TRES TRAMOS DEL RIVAL, por puesto en LaLiga.
#
#     1-6 duro · 7-13 normal · 14-20 blando
#
#     SIN MEDIR. Es el reparto que pidio el dueño para la previa:
#     tres grupos de tamaño parecido sobre veinte equipos. No
#     esta calibrado contra puntos reales y no decide nada, asi
#     que vale como etiqueta de color y para nada mas. Viaja
#     publicado como "sin medir" para que no se olvide.
RIVAL_DURO_HASTA = 6
RIVAL_NORMAL_HASTA = 13

# Cuantos partidos se enseñan por equipo.
PROXIMOS = 3

# El corte del veredicto, sobre la media del puesto de los tres
# rivales. TAMPOCO ESTA MEDIDO: sale de partir 1-20 en tres.
MEDIA_TRAMO_DURO = 9.0
MEDIA_TRAMO_BLANDO = 13.0


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _cuando(valor):
    try:
        cuando = datetime.fromisoformat(str(valor))

    except (TypeError, ValueError):
        return None

    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc)

    return cuando


def tramo_del_rival(puesto) -> str:
    """
    Duro, normal o blando. Sin puesto, "sin dato".

    Sin puesto NO se supone blando: un equipo que no casa con la
    clasificacion se pintaria verde y se leeria como una buena
    noticia que nadie ha comprobado.
    """

    if not puesto:
        return "sin dato"

    if puesto <= RIVAL_DURO_HASTA:
        return "duro"

    if puesto <= RIVAL_NORMAL_HASTA:
        return "normal"

    return "blando"


def el_calendario(
    calendario: dict | None,
    clasificacion: list | None,
    nuestros: list | None,
    ahora=None,
) -> dict:
    """
    Una fila por equipo nuestro, con sus tres proximos partidos.

    Forma fija. Nunca lanza. Sin calendario o sin clasificacion
    devuelve `available: False` y dice cual falta, en vez de un
    cuadro vacio que se lee como "no hay partidos".
    """

    vacio = {
        "available": False,
        "equipos": [],
        "sin_casar": [],
        "casan_todas": None,
        "partidos": 0,
        "fetched_at": (calendario or {}).get("fetched_at"),
        "tramos_sin_medir": {
            "duro_hasta": RIVAL_DURO_HASTA,
            "normal_hasta": RIVAL_NORMAL_HASTA,
        },
        "reason": None,
    }

    try:
        partidos = [
            m
            for m in ((calendario or {}).get("matches") or [])
            if isinstance(m, dict)
        ]

        if not partidos:
            return {
                **vacio,
                "reason": (
                    "El calendario no trae ni un partido: sin él "
                    "no se sabe contra quién juega nadie."
                ),
            }

        filas = [
            r for r in (clasificacion or []) if isinstance(r, dict)
        ]

        if not filas:
            return {
                **vacio,
                "partidos": len(partidos),
                "reason": (
                    "No llegó la clasificación de LaLiga: se "
                    "sabe contra quién juega cada uno, pero no "
                    "si ese rival es de los de arriba o de los "
                    "de abajo."
                ),
            }

        # EL CASADO, POR NOMBRE. Es como casan hoy las veinte.
        por_nombre = {
            str(r.get("team") or "").strip(): r for r in filas
        }

        # Y EL PUENTE AL ID DE BIWENGER, que es por donde entra
        # nuestra plantilla.
        por_id = {
            safe_int(r.get("biwenger_team_id")): r
            for r in filas
            if safe_int(r.get("biwenger_team_id"))
        }

        # LO QUE NO CASA SE DICE, NO SE TIRA.
        del_calendario = set()

        for m in partidos:
            del_calendario.add(str(m.get("home") or "").strip())
            del_calendario.add(str(m.get("away") or "").strip())

        del_calendario.discard("")

        sin_casar = sorted(
            nombre
            for nombre in del_calendario
            if nombre not in por_nombre
        )

        ahora = ahora or datetime.now(timezone.utc)

        # NUESTROS JUGADORES, AGRUPADOS POR EQUIPO.
        por_equipo = {}

        for jugador in (nuestros or []):

            if not isinstance(jugador, dict):
                continue

            equipo = safe_int(jugador.get("team_id"))

            if not equipo:
                continue

            por_equipo.setdefault(equipo, []).append(
                {
                    "id": safe_int(jugador.get("id")),
                    "name": jugador.get("name"),
                    "position": safe_int(jugador.get("position")),
                    "points": safe_int(jugador.get("points")),
                }
            )

        equipos = []

        for equipo_id, jugadores in por_equipo.items():

            ficha = por_id.get(equipo_id) or {}

            nombre = str(ficha.get("team") or "").strip()

            proximos = _los_proximos(
                partidos, nombre, por_nombre, ahora
            )

            puestos = [
                p["rival_puesto"]
                for p in proximos
                if p["rival_puesto"]
            ]

            media = (
                round(sum(puestos) / len(puestos), 1)
                if puestos
                else None
            )

            equipos.append(
                {
                    "team_id": equipo_id,
                    "team": nombre or None,
                    "puesto": safe_int(ficha.get("rank")) or None,
                    "casa": bool(nombre),
                    "jugadores": sorted(
                        jugadores,
                        key=lambda j: -j["points"],
                    ),
                    "proximos": proximos,
                    "media_del_rival": media,
                    "veredicto": _veredicto(media, proximos),
                }
            )

        # DE MAS BLANDO A MAS DURO. Sin media, al final: "no se
        # sabe" no es "es facil".
        equipos.sort(
            key=lambda e: (
                e["media_del_rival"] is None,
                -(e["media_del_rival"] or 0),
            )
        )

        return {
            "available": True,
            "equipos": equipos,
            "sin_casar": sin_casar,
            "casan_todas": not sin_casar,
            "partidos": len(partidos),
            "fetched_at": (calendario or {}).get("fetched_at"),
            "tramos_sin_medir": {
                "duro_hasta": RIVAL_DURO_HASTA,
                "normal_hasta": RIVAL_NORMAL_HASTA,
            },
            "reason": (
                f"{len(partidos)} partidos, {len(equipos)} "
                f"equipos nuestros"
                + (
                    f". {len(sin_casar)} ficha(s) del calendario "
                    f"no casan con la clasificación: "
                    f"{', '.join(sin_casar)}."
                    if sin_casar
                    else ", y las fichas del calendario casan "
                    "todas con la clasificación."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar el calendario: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _los_proximos(partidos, nombre, por_nombre, ahora) -> list:
    """
    Los tres siguientes de este equipo, por hora de comienzo.

    "Siguientes" es POR RELOJ, no por numero de jornada. En esta
    liga hay partidos aplazados: la jornada 6 tiene uno el 3 de
    septiembre, antes que toda la jornada 5. Ordenar por jornada
    pondria como "proximo" uno que ya se jugo.
    """

    if not nombre:
        return []

    suyos = []

    for m in partidos:

        casa = str(m.get("home") or "").strip()

        fuera = str(m.get("away") or "").strip()

        if nombre not in (casa, fuera):
            continue

        cuando = _cuando(m.get("kickoff"))

        if cuando is None or cuando <= ahora:
            continue

        rival = fuera if nombre == casa else casa

        ficha = por_nombre.get(rival) or {}

        puesto = safe_int(ficha.get("rank")) or None

        suyos.append(
            {
                "jornada": safe_int(m.get("matchday")) or None,
                "rival": rival,
                "rival_puesto": puesto,
                "rival_id": (
                    safe_int(ficha.get("biwenger_team_id"))
                    or None
                ),
                "en_casa": nombre == casa,
                "kickoff": m.get("kickoff"),
                "tramo": tramo_del_rival(puesto),

                # SIN CASAR SE DICE. Un rival que no aparece en
                # la clasificacion sale con su nombre y sin
                # puesto, no desaparece.
                "casa_con_la_clasificacion": bool(ficha),
            }
        )

    suyos.sort(key=lambda p: _cuando(p["kickoff"]))

    return suyos[:PROXIMOS]


def _veredicto(media, proximos) -> str:
    """
    Tramo blando, normal o duro, en cristiano.

    Sin media NO se dice "normal": se dice que no se sabe. Un
    veredicto por defecto es justo lo que absorbe el caso raro.
    """

    if media is None:
        return "sin dato"

    if not proximos:
        return "sin partidos"

    if media < MEDIA_TRAMO_DURO:
        return "tramo duro"

    if media < MEDIA_TRAMO_BLANDO:
        return "normal"

    return "tramo blando"
