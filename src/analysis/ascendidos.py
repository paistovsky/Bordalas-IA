"""
Que clubes acaban de ascender, y si eso paga.

LA REGLA 8, DEL VIDEO (truco nº 3)

    "Hay jugadores que son ahora mismo titulares que valen
     500.000, 600.000, que estan subiendo 70.000 al dia (...)
     como se le ocurra meter un gol se te van a los 6 o 7
     millones rapido."

    70.000 sobre 600.000 es un +11,6 % diario. Nuestro tramo
    `> 4 %/dia` ya esta medido rindiendo +21,15 % a tres dias: la
    via TENER sabe valorar esto. Lo que no sabia es BUSCARLO,
    porque Pepe no sabia que club acaba de ascender.

DE DONDE SALE LA LISTA, Y POR QUE ASI

    No de mi memoria ni de una constante escrita a mano: del
    propio catalogo de Biwenger.

    Un club que subio de Segunda tiene a toda su plantilla sin
    puntos de la temporada anterior en Primera. Medido sobre los
    569 jugadores del catalogo, la separacion no admite duda:

        Racing       3,6 puntos de media,  95 % de la plantilla a 0
        Malaga       4,3                   93 %
        Deportivo    5,5                   93 %
        ------------------------------------------------ salto x8
        Elche       46,1                   33 %

    Ocho veces de diferencia entre el tercero y el cuarto. No
    hace falta afinar el corte: cualquier umbral entre 10 y 40
    da los mismos tres.

    Si algun año la separacion no fuera tan limpia, este modulo
    lo dice en vez de elegir por su cuenta.

Y LO QUE MIDE ANTES DE CREERSELO (regla 18)

    El encargo lo pide por su nombre: "antes de darles ningun
    trato especial, midelo". Ver `medir_ascendidos`.
"""

from __future__ import annotations

import statistics


# Por debajo de esto, un jugador no jugo en Primera la temporada
# pasada. El salto real entre el tercer club y el cuarto es de
# 5,5 a 46,1, asi que el corte exacto no cambia el resultado.
PUNTOS_TEMPORADA_ANTERIOR = 20.0


# Cuantos clubes ascienden cada año en esta competicion.
ASCIENDEN = 3


# El video habla de titulares BARATOS. Es la unica franja donde
# nuestra medicion confirma el consejo.
PRECIO_BARATO = 1_000_000


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _vacio(motivo: str) -> dict:
    return {
        "available": False,
        "teams": [],
        "team_ids": [],
        "method": None,
        "threshold": PUNTOS_TEMPORADA_ANTERIOR,
        "rows": [],
        "clean_split": None,
        "reason": motivo,
    }


def detectar(catalog: dict | None) -> dict:
    """
    Los clubes recien ascendidos, deducidos del catalogo.

    Nunca lanza. Forma fija.
    """

    try:
        datos = (catalog or {}).get("data") or catalog or {}

        jugadores = (datos.get("players") or {})
        equipos = (datos.get("teams") or {})

        if not jugadores or not equipos:
            return _vacio(
                "Sin catalogo de jugadores o de equipos: no se "
                "puede deducir quien ascendio."
            )

        if isinstance(jugadores, dict):
            jugadores = list(jugadores.values())

        por_equipo = {}

        for jugador in jugadores:

            if not isinstance(jugador, dict):
                continue

            por_equipo.setdefault(
                str(jugador.get("teamID")), []
            ).append(
                safe_int(jugador.get("pointsLastSeason"))
            )

        filas = []

        for team_id, puntos in por_equipo.items():

            if not puntos:
                continue

            ficha = equipos.get(team_id) or {}

            filas.append({
                "team_id": team_id,
                "name": (
                    ficha.get("name")
                    or ficha.get("slug")
                    or f"#{team_id}"
                ),
                "players": len(puntos),
                "mean_points": round(
                    statistics.fmean(puntos), 1
                ),
                "zero_percent": round(
                    100 * sum(1 for p in puntos if p == 0)
                    / len(puntos),
                    1,
                ),
            })

        if len(filas) < ASCIENDEN + 1:
            return _vacio(
                f"Solo se ven {len(filas)} equipos: hacen falta "
                f"mas para distinguir a los que ascendieron."
            )

        filas.sort(key=lambda f: f["mean_points"])

        ascendidos = [
            f
            for f in filas[:ASCIENDEN]
            if f["mean_points"] < PUNTOS_TEMPORADA_ANTERIOR
        ]

        if not ascendidos:
            return _vacio(
                "Ningun equipo esta por debajo del corte: o no "
                "hay ascendidos en el catalogo, o la temporada "
                "anterior no trae puntos."
            )

        # ¿Se separan de verdad del cuarto, o esta pegado?
        siguiente = filas[len(ascendidos)]["mean_points"]
        ultimo = ascendidos[-1]["mean_points"]

        limpio = bool(
            siguiente >= PUNTOS_TEMPORADA_ANTERIOR
            and siguiente > ultimo * 2
        )

        return {
            "available": True,
            "teams": [f["name"] for f in ascendidos],
            "team_ids": [f["team_id"] for f in ascendidos],
            "method": (
                "Media de puntos de la temporada anterior por "
                "club, sobre el catalogo de Biwenger. Los "
                "ascendidos vienen de Segunda y su plantilla no "
                "tiene puntos en Primera."
            ),
            "threshold": PUNTOS_TEMPORADA_ANTERIOR,
            "rows": filas[: ASCIENDEN + 2],
            "clean_split": limpio,
            "reason": (
                f"Ascendidos: {', '.join(f['name'] for f in ascendidos)}. "
                + (
                    f"La separacion es limpia: el ultimo tiene "
                    f"{ultimo} puntos de media y el siguiente "
                    f"{siguiente}."
                    if limpio
                    else f"CUIDADO: el siguiente club tiene "
                    f"{siguiente} de media contra {ultimo} del "
                    f"ultimo ascendido. La separacion no es "
                    f"limpia y la lista puede estar mal."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo deducir: "
            f"{type(error).__name__}: {error}"
        )


# ============================================================
# ¿PAGA? (regla 18: ningun umbral sin numero detras)
# ============================================================


def medir_ascendidos(
    price_history: dict | None,
    team_of_player: dict | None,
    promoted_ids,
    price_of_player: dict | None = None,
) -> dict:
    """
    ¿Suben mas los jugadores de recien ascendidos, en NUESTRO
    historico?

    El almacen entra por parametro: este modulo no va a buscarlo.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "groups": [],
        "supports_advice": None,
        "cheap_threshold": PRECIO_BARATO,
        "reason": None,
    }

    try:
        series = (price_history or {}).get("players") or {}

        if not series or not team_of_player:
            return {
                **vacio,
                "reason": (
                    "Sin almacen de precios o sin equipos: no se "
                    "puede medir si los ascendidos suben mas."
                ),
            }

        promovidos = {str(t) for t in (promoted_ids or [])}

        precios = price_of_player or {}

        cubos = {
            "ascendidos baratos": [],
            "resto baratos": [],
            "ascendidos caros": [],
            "resto caros": [],
        }

        for player_id, serie in series.items():

            equipo = team_of_player.get(str(player_id))

            if equipo is None:
                continue

            precio = safe_int(precios.get(str(player_id)))

            valores = (serie or {}).get("p") or []

            tasas = [
                (valores[i] - valores[i - 1]) / valores[i - 1]
                for i in range(1, len(valores))
                if valores[i - 1] > 0
            ]

            if not tasas:
                continue

            es_ascendido = str(equipo) in promovidos
            es_barato = 0 < precio <= PRECIO_BARATO

            clave = (
                ("ascendidos " if es_ascendido else "resto ")
                + ("baratos" if es_barato else "caros")
            )

            cubos[clave].append(statistics.fmean(tasas))

        grupos = []

        for nombre, valores in cubos.items():

            if not valores:
                grupos.append({
                    "group": nombre,
                    "n": 0,
                    "mean_daily_percent": None,
                    "median_daily_percent": None,
                    "above_4_percent": None,
                })
                continue

            grupos.append({
                "group": nombre,
                "n": len(valores),
                "mean_daily_percent": round(
                    statistics.fmean(valores) * 100, 3
                ),
                "median_daily_percent": round(
                    statistics.median(valores) * 100, 3
                ),
                "above_4_percent": round(
                    100 * sum(1 for v in valores if v > 0.04)
                    / len(valores),
                    1,
                ),
            })

        por_nombre = {g["group"]: g for g in grupos}

        baratos_asc = por_nombre["ascendidos baratos"]
        baratos_resto = por_nombre["resto baratos"]

        apoya = None

        if (
            baratos_asc["n"]
            and baratos_resto["n"]
            and baratos_asc["mean_daily_percent"] is not None
            and baratos_resto["mean_daily_percent"] is not None
        ):
            apoya = (
                baratos_asc["mean_daily_percent"]
                > baratos_resto["mean_daily_percent"]
            )

        return {
            "available": True,
            "groups": grupos,
            "supports_advice": apoya,
            "cheap_threshold": PRECIO_BARATO,
            "reason": _reason_medicion(
                baratos_asc,
                baratos_resto,
                por_nombre["ascendidos caros"],
                apoya,
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason_medicion(asc, resto, caros, apoya) -> str:

    if apoya is None:
        return (
            "Sin muestra suficiente en alguno de los dos grupos: "
            "el consejo se queda como aviso, no como factor."
        )

    veces = (
        round(
            asc["mean_daily_percent"]
            / resto["mean_daily_percent"],
            2,
        )
        if resto["mean_daily_percent"]
        else None
    )

    if not apoya:
        return (
            f"En nuestro historico los baratos de recien "
            f"ascendidos suben {asc['mean_daily_percent']} % al "
            f"dia y el resto de baratos "
            f"{resto['mean_daily_percent']} %. El consejo NO se "
            f"confirma: se queda como aviso, no como factor."
        )

    frase = (
        f"Los baratos de recien ascendidos suben "
        f"{asc['mean_daily_percent']} % al dia contra "
        f"{resto['mean_daily_percent']} % del resto de baratos"
        + (f" ({veces}x)" if veces else "")
        + f", y el {asc['above_4_percent']} % pasa del 4 % diario "
        f"contra el {resto['above_4_percent']} %. Con n="
        f"{asc['n']}."
    )

    if (
        caros["mean_daily_percent"] is not None
        and caros["mean_daily_percent"] < 0
    ):
        frase += (
            f" Y es SOLO en los baratos: los caros de esos mismos "
            f"clubes caen un {abs(caros['mean_daily_percent'])} % "
            f"al dia."
        )

    frase += (
        " Muestra corta: sirve para marcarlos en el tablero, no "
        "para darles un factor."
    )

    return frase


# ============================================================
# LOS QUE HAY HOY EN EL MERCADO
# ============================================================


def en_el_mercado(
    targets,
    team_of_player: dict | None,
    promoted_ids,
) -> dict:
    """
    Titulares baratos de recien ascendidos que hay hoy a la venta.

    Publica. No compra.
    """

    vacio = {
        "available": False,
        "rows": [],
        "count": 0,
        "reason": None,
    }

    try:
        promovidos = {str(t) for t in (promoted_ids or [])}

        if not promovidos:
            return {
                **vacio,
                "reason": "Sin lista de ascendidos.",
            }

        filas = []

        for objetivo in (targets or []):

            player_id = str(objetivo.get("id"))

            equipo = (team_of_player or {}).get(player_id)

            if equipo is None or str(equipo) not in promovidos:
                continue

            precio = safe_int(objetivo.get("market_price"))

            ritmo = safe_float(
                (objetivo.get("market_gate") or {}).get(
                    "rate_percent_per_day"
                )
            )

            filas.append({
                "id": safe_int(objetivo.get("id")),
                "name": objetivo.get("name"),
                "team": objetivo.get("team"),
                "position": safe_int(objetivo.get("position")),
                "price": precio,
                "starter_probability": safe_float(
                    objetivo.get("starter_probability")
                ),
                "rate_percent_per_day": ritmo,
                "cheap": bool(0 < precio <= PRECIO_BARATO),
                "decision": objetivo.get("decision"),
            })

        filas.sort(key=lambda f: -(f["rate_percent_per_day"] or 0))

        baratos = [f for f in filas if f["cheap"]]

        return {
            "available": True,
            "rows": filas,
            "count": len(filas),
            "reason": (
                f"{len(filas)} jugador(es) de recien ascendidos en "
                f"el mercado de hoy, {len(baratos)} por debajo de "
                f"{PRECIO_BARATO:,} EUR."
                if filas
                else (
                    "Hoy no hay ningun jugador de recien "
                    "ascendidos en el mercado."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar el mercado: "
                f"{type(error).__name__}: {error}"
            ),
        }
