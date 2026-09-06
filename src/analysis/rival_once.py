"""
El equipo que habia que mirar: Mex.

POR QUE MEX Y NO POLLO (17/09/2026)

    Un mes mirando la cartera de Pollo, que tiene 21 fichas y
    67,84 M. Ese no es nuestro problema: juega a otra cosa.

    El equipo comparable es Mex:

        Mex     2.º   141 puntos   14 fichas   52,25 M
        Pepe    4.º   133 puntos   14 fichas   49,54 M

    Las mismas fichas, casi el mismo dinero, ocho puntos por
    delante. Si Mex esta quieto en el mercado y va segundo con
    nuestro presupuesto, la leccion no esta en comprar mejor:
    esta en alinear mejor.

QUE SE VE Y QUE NO

    Se ve: su formacion, quien tiene en el once, los puntos de
    cada uno, y cuanto se mueve en el mercado.

    NO se ve: que once puso en cada jornada pasada. El tablon
    solo guarda la alineacion vigente. Asi que la comparacion es
    de HOY, y se dice.

    Tampoco se usan `activity` ni `profile` de la ficha de
    rivales: los siete managers salen con el mismo valor en las
    dos, asi que no distinguen a nadie. Se usa lo que si varia
    -pujas perdidas y movimientos del tablon-.

NO DECIDE NADA

    No propone fichar a nadie ni cambiar el once. Enseña en que
    se diferencian dos equipos que cuestan lo mismo.
"""

from __future__ import annotations


POSICIONES = {
    1: "Portero",
    2: "Defensa",
    3: "Medio",
    4: "Delantero",
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _manager(status: dict, nombre: str) -> dict | None:

    for manager in (
        (status.get("rival_squads") or {}).get("managers") or []
    ):
        if str(manager.get("name") or "").strip() == nombre:
            return manager

    return None


def _nosotros(status: dict) -> dict | None:

    for manager in (
        (status.get("rival_squads") or {}).get("managers") or []
    ):
        if manager.get("is_current_user"):
            return manager

    return None


def _retrato(manager: dict | None) -> dict:
    """Como es el equipo de este manager, hoy."""

    if not manager:
        return {"available": False}

    jugadores = manager.get("players") or []

    once = [j for j in jugadores if j.get("is_starter")]
    banquillo = [j for j in jugadores if not j.get("is_starter")]

    reparto = {}

    for posicion, nombre in POSICIONES.items():
        reparto[nombre] = sum(
            1
            for j in once
            if safe_int(j.get("position")) == posicion
        )

    # TITULARES DE VERDAD EN SU EQUIPO REAL
    #
    #     La pregunta del encargo. Con nuestra propia vara: un
    #     80 % o mas de probabilidad de salir de inicio.
    con_dato = [
        j
        for j in once
        if j.get("starter_probability") is not None
    ]

    fijos = [
        j
        for j in con_dato
        if float(j["starter_probability"]) >= 80.0
    ]

    return {
        "available": True,
        "name": manager.get("name"),
        "rank": safe_int(manager.get("rank")),
        "points": safe_int(manager.get("points")),
        "squad_size": len(jugadores),
        "team_value": safe_int(manager.get("team_value")),
        "formation": manager.get("formation"),

        "lineup_size": len(once),
        "by_position": reparto,

        # Donde estan los puntos: medios y delanteros contra
        # portero y defensas.
        "attacking_half": (
            reparto.get("Medio", 0)
            + reparto.get("Delantero", 0)
        ),

        "lineup_points": sum(
            safe_int(j.get("points")) for j in once
        ),
        "bench_points": sum(
            safe_int(j.get("points")) for j in banquillo
        ),

        "nailed_starters": len(fijos),
        "nailed_starters_of": len(con_dato),

        "lineup": [
            {
                "name": j.get("name"),
                "position": safe_int(j.get("position")),
                "points": safe_int(j.get("points")),
                "starter_probability": j.get(
                    "starter_probability"
                ),
                "hierarchy": j.get("hierarchy"),
                "price": safe_int(j.get("price")),
            }
            for j in sorted(
                once,
                key=lambda j: (
                    safe_int(j.get("position")),
                    -safe_int(j.get("points")),
                ),
            )
        ],
    }


def _mercado(status: dict, nombre: str) -> dict:
    """¿Se mueve, o esta quieto y ganando?"""

    vistos = set()
    compras = 0
    ventas = 0

    feed = (
        (status.get("league_center") or {}).get("market_feed")
        or []
    )

    for movimiento in feed:

        clave = (
            movimiento.get("type"),
            movimiento.get("player_id"),
            movimiento.get("amount"),
        )

        if clave in vistos:
            continue

        vistos.add(clave)

        if nombre in str(movimiento.get("buyer")):
            compras += 1

        if nombre in str(movimiento.get("seller")):
            ventas += 1

    pujas_perdidas = None

    for manager in (
        (status.get("rival_intelligence") or {}).get("managers")
        or []
    ):
        if str(manager.get("name") or "").strip() == nombre:
            pujas_perdidas = safe_int(manager.get("lost_bids"))
            break

    return {
        "buys": compras,
        "sells": ventas,
        "lost_bids": pujas_perdidas,
        "quiet": bool(
            compras == 0
            and ventas == 0
        ),
        "window": (
            "El tablon solo guarda unos dias: 'quieto' significa "
            "quieto en esa ventana, no en toda la temporada."
        ),
    }


def comparar_con(
    status: dict | None,
    rival: str = "Mex",
) -> dict:
    """
    En que se diferencia nuestro once del de un rival comparable.

    Nunca lanza.
    """

    try:
        estado = status or {}

        ellos = _retrato(_manager(estado, rival))
        nosotros = _retrato(_nosotros(estado))

        if not ellos.get("available") or not nosotros.get(
            "available"
        ):
            return {
                "available": False,
                "observer_only": True,
                "reason": (
                    f"No se ve la plantilla de {rival} o la "
                    f"nuestra: sin comparacion. Prefiero decirlo "
                    f"a compararlo con huecos."
                ),
            }

        mercado = _mercado(estado, rival)

        return {
            "available": True,
            "observer_only": True,

            "rival": ellos,
            "us": nosotros,
            "market": mercado,

            "points_gap": (
                ellos["points"] - nosotros["points"]
            ),
            "value_gap": (
                ellos["team_value"] - nosotros["team_value"]
            ),
            "lineup_points_gap": (
                ellos["lineup_points"] - nosotros["lineup_points"]
            ),
            "attacking_half_gap": (
                ellos["attacking_half"]
                - nosotros["attacking_half"]
            ),

            "reason": _reason(ellos, nosotros, mercado),

            "caveat": (
                "Comparacion de HOY. El tablon no guarda que once "
                "puso cada manager en las jornadas pasadas, asi "
                "que esto no dice como llego hasta aqui: dice en "
                "que se diferencian ahora mismo."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo comparar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(ellos: dict, nosotros: dict, mercado: dict) -> str:

    trozos = []

    diferencia = ellos["points"] - nosotros["points"]

    if diferencia:
        trozos.append(
            f"{ellos['name']} va {abs(diferencia)} puntos "
            f"{'por delante' if diferencia > 0 else 'por detras'} "
            f"con {ellos['squad_size']} fichas contra nuestras "
            f"{nosotros['squad_size']}."
        )

    hueco = (
        ellos["attacking_half"]
        - nosotros["attacking_half"]
    )

    if hueco:
        trozos.append(
            f"Su once lleva {ellos['attacking_half']} jugadores "
            f"de medio campo hacia arriba y el nuestro "
            f"{nosotros['attacking_half']}."
        )

    # LO MAS INCOMODO DE LA COMPARACION
    #
    #     Nuestro once esta lleno de titulares seguros y el suyo
    #     no. Si el que gana es el que tiene menos, la vara con
    #     la que elegimos el once esta mirando lo que no paga.
    if (
        ellos["nailed_starters_of"]
        and nosotros["nailed_starters_of"]
    ):
        trozos.append(
            f"Y lo incomodo: de su once, "
            f"{ellos['nailed_starters']} de "
            f"{ellos['nailed_starters_of']} son titulares fijos "
            f"en su equipo real; del nuestro, "
            f"{nosotros['nailed_starters']} de "
            f"{nosotros['nailed_starters_of']}."
        )

    if mercado.get("quiet"):
        trozos.append(
            f"En el tablon no aparece ni una compra ni una venta "
            f"suya, y lleva {mercado.get('lost_bids')} pujas "
            f"perdidas. Esta quieto."
        )

    return " ".join(trozos) or "Sin diferencias que contar."
