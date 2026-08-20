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
# EL DEBATE DEL ONCE
# ============================================================


POSICIONES = {1: "Portero", 2: "Defensa", 3: "Medio", 4: "Delantero"}


# Por debajo de esto la decision estaba reñida y merece contarse.
# Por encima, el suplente no estaba ni cerca y decirlo seria
# ruido.
MARGEN_DISCUTIBLE = 0.12


def build_lineup_debate(roster: dict) -> dict:
    """Las decisiones ajustadas del once, posicion por posicion.

    POR QUE ESTO Y NO MAS NUMEROS

        El panel del plan contaba la media de titularidad, el
        valor del once y quien tenia mas jerarquia. Todo eso ya
        sale, jugador a jugador, en la tabla de abajo. Repetirlo
        agregado no informa: ocupa.

        Lo que la tabla NO puede contar es la DECISION. El once
        no es una lista, es once elecciones, y de esas solo dos o
        tres estuvieron reñidas. Esas son las que hay que poder
        discutir —"¿no compensa meter al delantero del Elche en
        vez de a Bigas?"— y para discutirlas hace falta ver al que
        entro y al que se quedo, con su numero al lado.

        El cambio se plantea DENTRO DE LA POSICION porque ahi
        siempre es legal: cualquier titular se puede cambiar por
        un suplente de su misma posicion sin tocar el dibujo.
    """

    jugadores = (roster or {}).get("players") or []

    titulares = [
        j for j in jugadores
        if isinstance(j, dict) and j.get("is_starter")
    ]

    suplentes = [
        j for j in jugadores
        if isinstance(j, dict) and not j.get("is_starter")
    ]

    def valor(jugador):
        return jugador.get("weekly_expected_value")

    duelos = []

    for posicion in (1, 2, 3, 4):

        dentro = [
            j for j in titulares
            if safe_int(j.get("position")) == posicion
            and valor(j) is not None
        ]

        fuera = [
            j for j in suplentes
            if safe_int(j.get("position")) == posicion
            and valor(j) is not None
        ]

        if not dentro or not fuera:
            continue

        peor_dentro = min(dentro, key=valor)
        mejor_fuera = max(fuera, key=valor)

        margen = round(
            valor(peor_dentro) - valor(mejor_fuera),
            3,
        )

        duelos.append({
            "position": posicion,
            "position_name": POSICIONES.get(posicion, "?"),

            "entra": _ficha_de_duelo(peor_dentro),
            "se_queda": _ficha_de_duelo(mejor_fuera),

            "margen": margen,

            # Un margen negativo no es un fallo: el motor tambien
            # mira rival, campo y penaltis, y esos desempates no
            # caben en este numero. Pero si sale negativo hay que
            # poder verlo.
            "discutible": margen < MARGEN_DISCUTIBLE,
        })

    duelos.sort(key=lambda item: item["margen"])

    # El riesgo de la jornada: quien del once puede no salir.
    riesgo = [
        _ficha_de_duelo(j)
        for j in titulares
        if (
            j.get("starter_probability") is not None
            and float(j["starter_probability"]) < 60
        )
        or (
            j.get("availability")
            and j["availability"] != "DISPONIBLE"
        )
    ]

    riesgo.sort(
        key=lambda item: (
            item.get("starter_probability")
            if item.get("starter_probability") is not None
            else 999
        )
    )

    sin_dato = [
        _ficha_de_duelo(j)
        for j in titulares
        if j.get("starter_probability") is None
    ]

    return {
        "available": bool(titulares),
        "duelos": duelos,
        "riesgo": riesgo,
        "sin_dato": sin_dato,
    }


def _ficha_de_duelo(jugador: dict) -> dict:
    return {
        "id": safe_int(jugador.get("id")),
        "name": jugador.get("name"),
        "position": safe_int(jugador.get("position")),
        "hierarchy": jugador.get("hierarchy"),
        "starter_probability": jugador.get("starter_probability"),
        "weekly_expected_value": jugador.get(
            "weekly_expected_value"
        ),
        "availability": jugador.get("availability"),
        "team_name": jugador.get("team_name"),
        "next_match": jugador.get("next_match") or {},
    }


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


def build_rival_squads(
    snapshot: dict,
    current_user_id=None,
) -> dict:
    """La plantilla de cada manager de la liga, con la misma ficha.

    Incluye la propia con `is_current_user: True`, para que la
    pantalla pueda tratarlas igual y el dueño compare sin cambiar
    de sitio.
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

        jugadores = []

        for player_id in titulares + banquillo:

            if not player_id:
                continue

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

            # Cuanta de esa plantilla sabemos explicar. Sin esto,
            # una pantalla a medias parece una pantalla completa.
            "with_starter_data": sum(
                1
                for j in jugadores
                if j.get("starter_probability") is not None
            ),
        })

    managers.sort(key=lambda item: item.get("rank", 9999))

    return {
        "available": True,
        "reason": None,
        "managers": managers,
    }
