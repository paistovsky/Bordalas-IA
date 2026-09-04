"""
La segunda opinion: cuanto vale un jugador de aqui a final de
temporada.

POR QUE EXISTE

    Hoy todo se valora a tres dias
    (`DEFAULT_SPECULATION_HORIZON = 3`) o a un ciclo. Es el
    horizonte correcto para una reventa -lo que el mercado tarda
    en digerir una jornada- y es el horizonte equivocado para un
    fichaje.

    Un jugador que da 6 puntos por jornada durante 30 jornadas
    vale 180 puntos. Lo que valga su reventa el jueves es otra
    cosa, y es la unica que Pepe mira.

    El caso de la auditoria lo enseña entero: Exposito -Clave,
    90 % titular, 196 puntos esperados- se rechaza porque "como
    especulacion rinde un 0,59 % y se exige al menos un 3 %". Ni
    siquiera se esta mirando el futbol.

FASE OBSERVADOR

    Esto NO sustituye nada y NO decide nada. Se escribe al lado
    de la valoracion de siempre, en el mismo tablero, para que se
    puedan leer las dos:

        "Pepe hoy lo valora en X; a horizonte de temporada
         valdria Y."

    El motor de decision sigue usando SOLO la vieja. Ninguna ruta
    de decision importa este modulo, y hay una guardia que lo
    comprueba.

LA CUENTA

        puntos por jornada = puntos esperados / 38
        puntos restantes   = puntos por jornada x jornadas que quedan
        valor temporada    = puntos restantes x precio del punto

    `expected_points` ya viene escalado por la jerarquia, por la
    probabilidad de ser titular de esta jornada y por las
    ausencias -las tres, multiplicadas, en
    `expected_points_factor`-. No se vuelven a aplicar aqui:
    contarlas dos veces seria el error facil.

    Y son puntos de TEMPORADA COMPLETA -salen de
    `pointsLastSeason`, 38 jornadas-, asi que repartirlos entre
    38 y multiplicar por las que quedan es exactamente lo que
    hay que hacer.

EL PRECIO DEL PUNTO

    El medido, `points_market.rate_median`, no la constante
    `EUROS_POR_PUNTO = 30.000` de `rival_intelligence_engine`. El
    mercado real de esta liga los paga a unos 21.758, y valorar
    con una constante un 38 % por encima de lo que se paga
    hincharia todos los numeros a la vez.

    Sin precio del punto medido no hay valor de temporada: va
    None y se dice por que. Un valor sacado de una constante
    seria un numero con pinta de medida.

POR QUE NO SE AJUSTA POR DIFICULTAD DE CALENDARIO

    Porque a horizonte de temporada se cancela sola.

    La dificultad del calendario importa a tres dias: contra
    quien juegas ESTE sabado cambia mucho. De aqui a la jornada
    38 cada equipo juega contra todos, en casa y fuera, asi que
    el calendario restante de dos jugadores cualesquiera es casi
    el mismo por construccion.

    Aplicar un factor ahi seria darle precision a un ajuste que
    tiende a uno. Lo unico que quedaria seria el ruido del
    emparejamiento de nombres entre el calendario de LaLiga
    -"Deportivo Alaves"- y el catalogo de Biwenger -"Alaves"-, y
    ese ruido ya nos ha costado dinero por otro lado.
"""

from __future__ import annotations


# La temporada sobre la que estan medidos los puntos esperados.
# `pointsLastSeason` son 38 jornadas, y de ahi sale la escala.
SEASON_MATCHDAYS = 38


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def season_value(
    expected_points,
    matchdays_remaining,
    euros_per_point,
    market_price=0,
    season_matchdays: int = SEASON_MATCHDAYS,
) -> dict:
    """
    Lo que rinde este jugador de aqui a final de temporada.

    Nunca lanza. Sin alguno de los tres datos que hacen falta,
    devuelve None y dice cual falta.
    """

    puntos = safe_int(expected_points)
    restantes = matchdays_remaining
    tarifa = safe_int(euros_per_point)
    precio = safe_int(market_price)

    faltan = []

    if puntos <= 0:
        faltan.append("puntos esperados")

    if restantes is None:
        faltan.append("jornadas restantes")

    if tarifa <= 0:
        faltan.append("precio del punto")

    if faltan:
        return {
            "available": False,
            "season_value": None,
            "season_points_remaining": None,
            "points_per_matchday": None,
            "cost_per_point": None,
            "beats_market_rate": None,
            "matchdays_remaining": restantes,
            "euros_per_point": tarifa or None,
            "reason": (
                "No se puede valorar a temporada: falta "
                + ", ".join(faltan)
                + "."
            ),
        }

    restantes = max(int(restantes), 0)

    por_jornada = puntos / season_matchdays
    puntos_restantes = por_jornada * restantes
    valor = int(round(puntos_restantes * tarifa))

    # Lo que costaria cada punto que queda por dar. Es la cuenta
    # que `rival_intelligence_engine` calcula como
    # `cost_per_point` y que, segun la auditoria, no lee nadie:
    # sale null en las 22 filas del tablero.
    coste_punto = (
        int(round(precio / puntos_restantes))
        if precio > 0 and puntos_restantes > 0
        else None
    )

    return {
        "available": True,

        "season_value": valor,
        "season_points_remaining": round(puntos_restantes, 1),
        "points_per_matchday": round(por_jornada, 2),

        "cost_per_point": coste_punto,

        # Comprar puntos por debajo de lo que el mercado los paga
        # es negocio por si solo. Se PUBLICA; no autoriza nada.
        "beats_market_rate": (
            coste_punto is not None and coste_punto < tarifa
        ),

        "matchdays_remaining": restantes,
        "euros_per_point": tarifa,

        "reason": (
            f"{puntos} puntos de temporada son "
            f"{por_jornada:.2f} por jornada; por {restantes} "
            f"jornadas quedan {puntos_restantes:.1f} puntos, que a "
            f"{tarifa:,} EUR el punto valen {valor:,} EUR."
        ).replace(",", "."),
    }


def _caveat(fila: dict) -> dict:
    """
    De que pie cojea el valor de temporada de esta fila.

    No cambia el numero: lo acompaña. Un chollo por punto que
    resulta ser un suplente sigue siendo un dato util; lo que no
    puede es salir sin la etiqueta.
    """

    probabilidad = fila.get("starter_probability")
    consenso = fila.get("starter_consensus")

    if probabilidad is None:
        return {
            "starter_known": False,
            "caveat": (
                "Sin pronostico de titularidad: sus puntos no llevan "
                "descuento por si juega o no, asi que este valor es "
                "el mejor caso, no el esperado."
            ),
        }

    if consenso == "BENCH":
        return {
            "starter_known": True,
            "caveat": (
                f"FutbolFantasy lo da suplente ({probabilidad:.0f} % "
                f"titular). El pronostico semanal pesa 0,15 en los "
                f"puntos esperados, asi que conserva casi todos: a "
                f"horizonte de temporada eso puede ser un chollo o un "
                f"banquillo caro, y este numero no lo distingue."
            ),
        }

    return {"starter_known": True, "caveat": None}


def annotate_rows(
    rows: list | None,
    matchdays_remaining,
    euros_per_point,
) -> list:
    """
    La misma cuenta para cada fila del tablero, escrita al lado
    de la valoracion de siempre.

    Devuelve filas NUEVAS: no toca las que le pasan. El tablero
    que decide tiene que seguir siendo bit a bit el mismo.
    """

    salida = []

    for fila in (rows or []):

        if not isinstance(fila, dict):
            continue

        temporada = season_value(
            fila.get("expected_points"),
            matchdays_remaining,
            euros_per_point,
            market_price=fila.get("market_price"),
        )

        actual = safe_int(fila.get("our_value"))

        nueva = dict(fila)

        nueva["season_horizon"] = {
            **temporada,

            # DE QUE PIE COJEA ESTE NUMERO
            #
            #     Un valor de temporada se apoya entero en los
            #     puntos esperados, asi que hereda sus dos puntos
            #     flacos. Publicarlos al lado es lo que separa una
            #     segunda opinion de un segundo error:
            #
            #     - Sin pronostico de titularidad, los puntos NO
            #       llevan descuento. Es el caso Gustavo Puerta de
            #       la auditoria: 156 esperados = 156 en bruto.
            #
            #     - El pronostico semanal pesa 0,15, asi que un
            #       jugador que FF da suplente conserva casi todos
            #       sus puntos. A tres dias da igual; a temporada
            #       es la diferencia entre un chollo y un banquillo
            #       caro.
            **_caveat(fila),

            # Lo que hace comparables las dos opiniones de un
            # vistazo. Sin esto habria que restar a mano fila a
            # fila, que es como se dejan de mirar las cosas.
            "current_value": actual,
            "difference": (
                temporada["season_value"] - actual
                if temporada["season_value"] is not None
                else None
            ),
            "ratio": (
                round(temporada["season_value"] / actual, 2)
                if temporada["season_value"] is not None and actual > 0
                else None
            ),
        }

        salida.append(nueva)

    return salida


def build_season_horizon_shadow(
    acquisition: dict | None,
    race: dict | None,
    points_market: dict | None,
) -> dict:
    """
    El bloque entero para el dashboard.

    FASE OBSERVADOR: se calcula, se pinta, y no manda. Nunca
    lanza: un termometro no puede tumbar la telemetria.
    """

    try:
        restantes = (race or {}).get("matchdays_remaining")
        tarifa = safe_int((points_market or {}).get("rate_median"))

        filas = (acquisition or {}).get("targets") or []

        anotadas = annotate_rows(filas, restantes, tarifa)

        con_valor = [
            f
            for f in anotadas
            if (f.get("season_horizon") or {}).get("season_value")
            is not None
        ]

        # Los que mas cambian de opinion al mirar la temporada
        # entera. Es la lista que contesta a "¿a quien estaria
        # rechazando por mirar solo al jueves?".
        mayores_diferencias = sorted(
            con_valor,
            key=lambda f: -(
                (f.get("season_horizon") or {}).get("difference") or 0
            ),
        )[:10]

        return {
            "available": bool(con_valor),
            "observer_only": True,

            "matchdays_remaining": restantes,
            "euros_per_point": tarifa or None,

            "reason": (
                None
                if con_valor
                else (
                    "No se pudo valorar a temporada ninguna fila: "
                    + (
                        "faltan las jornadas restantes."
                        if restantes is None
                        else (
                            "falta el precio del punto medido."
                            if tarifa <= 0
                            else "no hay candidatos con puntos esperados."
                        )
                    )
                )
            ),

            "rows": anotadas,
            "candidates_valued": len(con_valor),
            "candidates_total": len(anotadas),

            "biggest_gaps": [
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "market_price": safe_int(f.get("market_price")),
                    "expected_points": f.get("expected_points"),
                    "starter_probability": f.get("starter_probability"),
                    "intent": f.get("intent"),
                    "decision_today": f.get("decision"),
                    "current_value": (
                        f.get("season_horizon") or {}
                    ).get("current_value"),
                    "season_value": (
                        f.get("season_horizon") or {}
                    ).get("season_value"),
                    "difference": (
                        f.get("season_horizon") or {}
                    ).get("difference"),
                    "cost_per_point": (
                        f.get("season_horizon") or {}
                    ).get("cost_per_point"),
                    "beats_market_rate": (
                        f.get("season_horizon") or {}
                    ).get("beats_market_rate"),
                    "starter_known": (
                        f.get("season_horizon") or {}
                    ).get("starter_known"),
                    "caveat": (
                        f.get("season_horizon") or {}
                    ).get("caveat"),
                }
                for f in mayores_diferencias
            ],
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo valorar a temporada: "
                f"{type(error).__name__}: {error}"
            ),
            "rows": [],
            "biggest_gaps": [],
        }
