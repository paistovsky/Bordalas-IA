"""
Concentracion: cuanto de la plantilla puede estar en un solo
nombre, y cuantos jugadores del mismo club.

POR QUE AHORA

    No existia ningun tope. Hoy Yamal son 22.220.000 de los
    54.000.000 de plantilla: el 41 % en un solo jugador.

    Mientras Pepe no compraba, eso era una foto. En cuanto empiece
    a desplegar caja, importa mas y no menos: cada compra decide
    si la plantilla se concentra o se reparte.

    Y cierra por fin la leccion de Soler del 16/08. Aquello se
    guardo con un test de rendimiento porque `optimal_bid` no ve
    el presupuesto, pero el problema era de CONCENTRACION: 5,95 M
    inmovilizando el 81 % del bolsillo. Hasta hoy no lo cubria
    nadie.

LOS DOS NUMEROS NO SON INVENTADOS: SALEN DE LA LIGA

    Medido sobre las siete plantillas el 10/09/2026, con el valor
    real de cada jugador:

        manager        fichas   mayor jugador   mismo club
        Pollo17  (1º)    19        31,0 %           4
        Mex      (2º)    14        32,2 %           2
        Luismi   (3º)    15        19,0 %           2
        PEPE     (4º)    14        41,1 %           2
        DiosMande(5º)    11        24,7 %           4
        Prinzipote(6º)   17        44,9 %           2
        Manzagool(7º)    13        17,4 %           3

    LOS TRES QUE VAN POR DELANTE ESTAN ENTRE EL 19 % Y EL 32 %.
    Los dos mas concentrados de la liga -Prinzipote con Mbappe al
    44,9 % y Pepe con Yamal al 41,1 %- van sextos y cuartos.

    No demuestra causalidad con siete equipos. Pero si dice donde
    esta la banda de los que ganan, y que Pepe esta fuera de ella.

POR JUGADOR: 35 %

    Por encima de la banda de los lideres (32,2 % el mayor de los
    tres) y por debajo de donde estan los dos concentrados. Deja
    sitio para un fichaje franquicia sin llegar a lo que hoy tiene
    Pepe.

POR CLUB: 4

    Es lo que lleva el lider. Nadie en la liga lleva cinco del
    mismo equipo, asi que cinco seria salirse de lo que hace
    alguien que gana.

    Importa porque comparten calendario: puntuan juntos en una
    jornada buena y se hunden juntos en una mala, y encima sus
    precios se mueven a la vez.

AVISA Y ACOTA, NO PROHIBE EN SILENCIO

    Como el resto de guardarrailes de la casa. Una plantilla que
    YA esta por encima no obliga a vender a nadie: se dice y ya.
    Lo que se acota es EMPEORARLO — una compra que dejaria al
    comprado por encima del tope, o que pondria un quinto jugador
    del mismo club.
"""

from __future__ import annotations

import collections


# Ver el docstring: la banda de los tres que van por delante llega
# al 32,2 %. Este tope queda justo encima.
MAX_PLAYER_SHARE = 0.35

# Lo que lleva el lider. Nadie en la liga lleva cinco.
MAX_SAME_TEAM = 4


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _squad_rows(squad) -> list:
    """Los jugadores con precio, vengan como vengan."""

    filas = []

    for jugador in (squad or []):

        if not isinstance(jugador, dict):
            continue

        precio = safe_int(jugador.get("price"))

        if precio <= 0:
            continue

        filas.append(
            {
                "id": safe_int(jugador.get("id")),
                "name": jugador.get("name"),
                "price": precio,
                "team_id": safe_int(
                    jugador.get("team_id") or jugador.get("teamID")
                ),
            }
        )

    return filas


def build_concentration(squad) -> dict:
    """
    Como esta repartida la plantilla hoy. Nunca lanza.
    """

    try:
        filas = _squad_rows(squad)

        if not filas:
            return {
                "available": False,
                "reason": (
                    "No hay plantilla con precios: no se puede medir "
                    "la concentracion."
                ),
                "players": [],
                "teams": [],
                "breaches": [],
            }

        total = sum(f["price"] for f in filas)

        por_jugador = sorted(
            (
                {
                    "id": f["id"],
                    "name": f["name"],
                    "price": f["price"],
                    "share": round(f["price"] / total, 4),
                    "over_limit": (f["price"] / total) > MAX_PLAYER_SHARE,
                }
                for f in filas
            ),
            key=lambda item: -item["share"],
        )

        cuenta = collections.Counter(
            f["team_id"] for f in filas if f["team_id"]
        )

        por_equipo = sorted(
            (
                {
                    "team_id": team_id,
                    "players": n,
                    "over_limit": n > MAX_SAME_TEAM,
                }
                for team_id, n in cuenta.items()
            ),
            key=lambda item: -item["players"],
        )

        incumplimientos = [
            {
                "kind": "PLAYER_SHARE",
                "name": p["name"],
                "value": p["share"],
                "limit": MAX_PLAYER_SHARE,
                "reason": (
                    f"{p['name']} son el {p['share'] * 100:.1f} % de "
                    f"la plantilla y el tope es el "
                    f"{MAX_PLAYER_SHARE * 100:.0f} %. No obliga a "
                    f"venderlo: acota comprar mas de lo mismo."
                ),
            }
            for p in por_jugador
            if p["over_limit"]
        ] + [
            {
                "kind": "SAME_TEAM",
                "team_id": t["team_id"],
                "value": t["players"],
                "limit": MAX_SAME_TEAM,
                "reason": (
                    f"{t['players']} jugadores del equipo "
                    f"{t['team_id']} y el tope es {MAX_SAME_TEAM}. "
                    f"Comparten calendario: puntuan juntos y se "
                    f"hunden juntos."
                ),
            }
            for t in por_equipo
            if t["over_limit"]
        ]

        return {
            "available": True,
            "reason": None,

            "squad_value": total,
            "squad_size": len(filas),

            "max_player_share": por_jugador[0]["share"],
            "max_player_name": por_jugador[0]["name"],
            "max_same_team": por_equipo[0]["players"] if por_equipo else 0,

            "limit_player_share": MAX_PLAYER_SHARE,
            "limit_same_team": MAX_SAME_TEAM,

            "players": por_jugador[:8],
            "teams": por_equipo[:8],

            "breaches": incumplimientos,
            "breach_count": len(incumplimientos),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"No se pudo medir la concentracion: "
                f"{type(error).__name__}: {error}"
            ),
            "players": [],
            "teams": [],
            "breaches": [],
        }


def check_purchase(
    concentration: dict | None,
    price,
    team_id=None,
) -> dict:
    """
    ¿Cuanto se puede pagar por este jugador sin romper los topes?

    Devuelve `allowed` -lo maximo que dejan los topes, o None si
    no acotan- y el motivo. No prohibe: acota.

    OJO CON EL DENOMINADOR

        Comprar a alguien SUBE el valor de la plantilla, asi que
        su parte es `precio / (plantilla + precio)`, no
        `precio / plantilla`. Con la segunda formula el tope
        mordería mucho antes y por una cuenta que no es la real.
    """

    estado = concentration or {}

    importe = safe_int(price)

    if not estado.get("available") or importe <= 0:
        return {
            "capped": False,
            "allowed": None,
            "reason": None,
        }

    total = safe_int(estado.get("squad_value"))

    if total <= 0:
        return {"capped": False, "allowed": None, "reason": None}

    # ------------------------------------------------------
    # 1. EL QUINTO DEL MISMO CLUB
    # ------------------------------------------------------

    equipo = safe_int(team_id)

    if equipo:

        actuales = next(
            (
                t["players"]
                for t in (estado.get("teams") or [])
                if t.get("team_id") == equipo
            ),
            0,
        )

        if actuales >= MAX_SAME_TEAM:
            return {
                "capped": True,
                "allowed": 0,
                "kind": "SAME_TEAM",
                "reason": (
                    f"Ya hay {actuales} jugadores del equipo "
                    f"{equipo} y el tope es {MAX_SAME_TEAM}. "
                    f"Comparten calendario: puntuan juntos y se "
                    f"hunden juntos."
                ),
            }

    # ------------------------------------------------------
    # 2. LA PARTE QUE OCUPARIA EN LA PLANTILLA
    # ------------------------------------------------------

    # parte = P / (total + P) <= tope  ->  P <= tope*total/(1-tope)
    maximo = int(
        MAX_PLAYER_SHARE * total / (1.0 - MAX_PLAYER_SHARE)
    )

    if importe <= maximo:
        return {"capped": False, "allowed": None, "reason": None}

    return {
        "capped": True,
        "allowed": maximo,
        "kind": "PLAYER_SHARE",
        "reason": (
            f"Pagar {importe:,} EUR lo dejaria en el "
            f"{importe / (total + importe) * 100:.1f} % de la "
            f"plantilla y el tope es el "
            f"{MAX_PLAYER_SHARE * 100:.0f} %. Los tres managers que "
            f"van por delante estan entre el 19 % y el 32 %. "
            f"Acotado a {maximo:,} EUR."
        ).replace(",", "."),
    }
