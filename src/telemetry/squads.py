from __future__ import annotations

"""
Plantillas con toda la informacion: la propia y las de los seis rivales.

EL CASO (20/08/2026)

    "¿Sabes lo que no veo? La plantilla del rival."

    Y tenia razon en algo mas grande de lo que preguntaba. La
    tabla de PLANTILLA enseñaba nombre, posicion, valor y si era
    titular. Nada mas. Ni el porcentaje de salir, ni la
    jerarquia, ni si estaba lesionado o sancionado.

    Todo eso ya se calculaba. Estaba en el XI —once jugadores de
    dieciseis— y en la tabla del mercado. La plantilla, que es
    donde se mira, era la unica pantalla ciega.

DE DONDE SALEN LOS RIVALES

    Del propio snapshot. `rounds.data.league.standings[].lineup`
    trae `players` —el once que alineo— y `discarded` —su
    banquillo—. Los dos juntos son su plantilla completa.

    Los nombres, posiciones y precios salen del catalogo. La
    jerarquia y el pronostico, del tablero de FutbolFantasy, que
    desde hoy tambien los cubre: las paginas de equipo se bajaban
    enteras y solo se emparejaba a los nuestros y a los del
    mercado.

    Cero peticiones nuevas. Solo se deja de tirar lo que ya
    estaba en el disco.

LO QUE NO HACE

    No decide. Saber que el rival tiene tres delanteros Dios no
    cambia ninguna puja: es telemetria, se mira y ya.

    Y no inventa: un jugador sin señal de FutbolFantasy sale con
    `starter_probability: null`, no con un 50 % de relleno. En
    pantalla eso es "sin dato", que es la verdad.
"""


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def starter_signal(player_id) -> dict:
    """
    La señal de FutbolFantasy de un jugador cualquiera.

    Blindada a proposito: esto es telemetria. Si el tablero no
    esta o no se puede leer, se pintan menos columnas; lo que no
    puede es tumbar la generacion del estado.
    """

    try:
        from src.analysis.candidate_starter_lookup import (
            get_starter_lookup,
        )

        return get_starter_lookup().get(safe_int(player_id)) or {}

    except Exception:                               # noqa: BLE001
        return {}


def enrich(base: dict, player_id) -> dict:
    """Añade a una ficha lo que sabe FutbolFantasy.

    Devuelve una ficha nueva: no toca la que le pasan.
    """

    ficha = dict(base or {})

    senal = starter_signal(player_id)

    jerarquia = senal.get("hierarchy") or {}

    probabilidad = senal.get("probability")

    ficha.update({
        "team_name": senal.get("team"),

        "hierarchy": jerarquia.get("label"),
        "hierarchy_value": jerarquia.get("value"),
        "franchise": bool(jerarquia.get("franchise")),

        # Ausencia de dato != dato. Sin señal va None, y la
        # pantalla dice "sin dato" en vez de un 0 % que leeria
        # como "no juega".
        "starter_probability": (
            round(float(probabilidad), 1)
            if probabilidad is not None
            else None
        ),
        "starter_consensus": senal.get("consensus"),

        "availability": (
            (senal.get("availability") or {}).get("label")
        ),

        # El parte entero: tipo de lesion, pronostico, partidos
        # de sancion cumplidos. La pantalla decide cuanto enseña.
        "absence": senal.get("absence"),

        "next_match": senal.get("next_match") or {},

        # LA MISMA VARA QUE USA EL MOTOR
        #
        # `weekly_expected_value` es la funcion con la que el
        # motor de alineacion ordena el once. Se llama a ELLA, no
        # se reimplementa: si mañana cambia la formula, cambia
        # sola en las dos pantallas.
        "weekly_expected_value": _valor_semanal(
            jerarquia.get("value"),
            probabilidad,
        ),
    })

    return ficha


def _valor_semanal(hierarchy_value, probability):
    """De 0 a 1: lo que se espera de este jugador esta jornada."""

    if probability is None:
        return None

    try:
        from src.analysis.lineup_engine import (
            weekly_expected_value,
        )

        return round(
            weekly_expected_value(
                hierarchy_value,
                probability,
            ),
            3,
        )

    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# LA PROPIA
# ============================================================


def enrich_roster(roster: dict) -> dict:
    """Mete la señal de FF en las tres listas del roster."""

    if not isinstance(roster, dict):
        return roster

    cache: dict[int, dict] = {}

    def enriquecido(jugador: dict) -> dict:
        player_id = safe_int(jugador.get("id"))

        if player_id not in cache:
            cache[player_id] = enrich({}, player_id)

        return {**jugador, **cache[player_id]}

    salida = dict(roster)

    for clave in ("players", "starters", "substitutes"):

        lista = roster.get(clave)

        if isinstance(lista, list):
            salida[clave] = [
                enriquecido(j)
                for j in lista
                if isinstance(j, dict)
            ]

    return salida


# ============================================================
# LAS DE LOS RIVALES
# ============================================================


def _catalog(snapshot: dict) -> dict:
    catalogo = (
        (snapshot.get("catalog") or {})
        .get("data", {})
        .get("players")
        or {}
    )

    return catalogo if isinstance(catalogo, dict) else {}


def _standings(snapshot: dict) -> list:
    filas = (
        (snapshot.get("rounds") or {})
        .get("data", {})
        .get("league", {})
        .get("standings")
        or []
    )

    return [f for f in filas if isinstance(f, dict)]


def _rosters_del_ledger(rival_intelligence: dict | None) -> dict:
    """
    La plantilla de cada manager segun el ledger de rivales.

    LA SEGUNDA FUENTE, QUE ES LA QUE FUNCIONA (04/09/2026)

        `standings[].lineup` es la alineacion que dejo puesta cada
        manager. Puede venir vacia -y venia: en la foto de
        produccion los SIETE managers salian con `squad_size: 0` y
        `players: []`, y aun asi `available: true`-.

        El ledger de rivales reconstruye la plantilla desde los
        perfiles de usuario, que es de donde salen los 17/14/13/12
        jugadores que ya conocia `ledger_audit`. Dos fuentes en
        casa y se estaba pintando la vacia.

        Se prefiere el ledger: la alineacion dice a quien puso el
        sabado, el perfil dice a quien TIENE, y una plantilla es
        lo segundo.
    """

    rosters = {}

    for manager in ((rival_intelligence or {}).get("managers") or []):

        if not isinstance(manager, dict):
            continue

        identificador = safe_int(
            manager.get("user_id") or manager.get("id")
        )

        if not identificador:
            continue

        ids = [
            safe_int(jugador.get("id"))
            for jugador in (manager.get("roster") or [])
            if isinstance(jugador, dict)
        ]

        ids = [player_id for player_id in ids if player_id]

        if ids:
            rosters[identificador] = ids

    return rosters


def build_rival_squads(
    snapshot: dict,
    current_user_id=None,
    rival_intelligence: dict | None = None,
) -> dict:
    """La plantilla de cada manager de la liga, con la misma ficha.

    Incluye la propia con `is_current_user: True`, para que la
    pantalla pueda tratarlas igual y el dueño compare sin cambiar
    de sitio.

    `rival_intelligence` es opcional a proposito: sin el se cae a
    `standings[].lineup`, que es lo que habia. Con el, se pinta la
    plantilla entera.
    """

    filas = _standings(snapshot)

    if not filas:
        return {
            "available": False,
            "reason": (
                "El snapshot no trae la clasificacion, que es de "
                "donde salen las plantillas rivales."
            ),
            "managers": [],
        }

    catalogo = _catalog(snapshot)
    mi_id = safe_int(current_user_id)

    rosters = _rosters_del_ledger(rival_intelligence)

    managers = []

    for indice, fila in enumerate(filas, start=1):

        alineacion = fila.get("lineup") or {}

        titulares = [
            safe_int(p)
            for p in (alineacion.get("players") or [])
        ]

        banquillo = [
            safe_int(p)
            for p in (alineacion.get("discarded") or [])
        ]

        titulares_set = set(titulares)

        del_ledger = rosters.get(safe_int(fila.get("id")))

        if del_ledger:
            fuente = "LEDGER"
            plantilla = del_ledger

        elif titulares or banquillo:
            fuente = "LINEUP"
            plantilla = titulares + banquillo

        else:
            fuente = "NINGUNA"
            plantilla = []

        jugadores = []

        vistos = set()

        for player_id in plantilla:

            if not player_id or player_id in vistos:
                continue

            vistos.add(player_id)

            ficha = (
                catalogo.get(str(player_id))
                or catalogo.get(player_id)
                or {}
            )

            jugadores.append(enrich(
                {
                    "id": player_id,

                    # Sin catalogo no se inventa un nombre: se
                    # dice que no se sabe quien es.
                    "name": ficha.get("name") or f"#{player_id}",

                    "position": safe_int(ficha.get("position")),

                    # Para el escudo del campo. Sin esto el XI
                    # del rival se pinta sin equipo.
                    "team_id": safe_int(ficha.get("teamID")),

                    "price": safe_int(ficha.get("price")),
                    "price_increment": safe_int(
                        ficha.get("priceIncrement")
                    ),
                    "points": safe_int(ficha.get("points")),
                    "points_last_season": safe_int(
                        ficha.get("pointsLastSeason")
                    ),
                    "status": ficha.get("status"),
                    "is_starter": player_id in titulares_set,
                    "in_catalog": bool(ficha),
                    "photo_url": (
                        f"https://cdn.biwenger.com/cdn-cgi/image/"
                        f"f=avif/i/p/{player_id}.png"
                    ),
                },
                player_id,
            ))

        jugadores.sort(
            key=lambda item: (
                not item["is_starter"],
                safe_int(item.get("position")),
                -safe_int(item.get("price")),
            )
        )

        user_id = safe_int(fila.get("id"))

        managers.append({
            "user_id": user_id,
            "name": str(fila.get("name") or f"Mánager {indice}"),
            "rank": safe_int(fila.get("position"), default=indice),
            "points": safe_int(fila.get("points")),
            "team_value": safe_int(fila.get("teamValue")),
            "team_value_inc": safe_int(fila.get("teamValueInc")),
            "icon": fila.get("icon"),
            "is_current_user": bool(mi_id and user_id == mi_id),

            "formation": alineacion.get("type"),
            "lineup_date": alineacion.get("date"),

            "squad_size": len(jugadores),
            "players": jugadores,

            # De donde salio esta plantilla, y -si esta vacia- por
            # que. Una tabla en blanco sin motivo se lee como "no
            # tiene jugadores" en vez de "no lo sabemos".
            "squad_source": fuente,
            "squad_reason": (
                None
                if jugadores
                else (
                    "Ni el ledger de rivales ni la alineacion "
                    "publicada traen su plantilla."
                )
            ),

            # Cuanta de esa plantilla sabemos explicar. Sin esto,
            # una pantalla a medias parece una pantalla completa.
            "with_starter_data": sum(
                1
                for j in jugadores
                if j.get("starter_probability") is not None
            ),
        })

    managers.sort(key=lambda item: item.get("rank", 9999))

    con_jugadores = [m for m in managers if m["squad_size"] > 0]

    # PUBLICAR "DISPONIBLE" SIN DATOS ES PEOR QUE DECIR QUE NO HAY
    #
    #     La foto de produccion salia con `available: true` y los
    #     siete managers a `squad_size: 0`. Quien lee eso ve una
    #     pantalla en blanco y entiende "no hay nada que ver",
    #     cuando lo que pasaba es que la fuente estaba vacia. Es
    #     la mentira mas barata de contar y la mas cara de
    #     detectar.
    if not con_jugadores:
        return {
            "available": False,
            "reason": (
                "Hay clasificacion, pero ninguna plantilla: ni el "
                "ledger de rivales ni las alineaciones publicadas "
                "traen jugadores."
            ),
            "managers": managers,
        }

    return {
        "available": True,
        "reason": None,
        "managers": managers,

        # Cuantos de los que salen en la tabla traen plantilla de
        # verdad. Si es menor que el total, la pantalla esta a
        # medias y tiene que poder decirlo.
        "managers_with_squad": len(con_jugadores),
        "managers_total": len(managers),
    }
