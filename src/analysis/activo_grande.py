"""
El jugador que pesa demasiado: las dos columnas, sin recomendar.

LA REGLA 15, Y LA PREGUNTA QUE ABRE

    Pollo vendio a Vinicius y bajo de 85 M a 67,8 M. No se enamoro
    del cromo.

    Yamal es el 42,81 % de nuestra plantilla, por encima del tope
    de concentracion del 35 %, y sube un 0,19 % diario -por
    debajo del mercado-.

    "No digo que haya que venderlo. Digo que nadie lo ha
     calculado nunca."

LO QUE HACE ESTE MODULO

    Las dos columnas, con la misma fuerza:

        VENDER   cuanto se libera, que se compraria con eso en el
                 escaparate de hoy, cuantos puntos entrarian de
                 verdad en el once y como queda la concentracion.

        TENER    lo que aporta hoy, medido; su parte de los
                 puntos frente a su parte del dinero; y con
                 cuantas jornadas se estaria decidiendo.

    Ninguna recomendacion. Decide el dueño.

LA TRAMPA QUE NO SE COMETE

    Con 21 M se compran cinco jugadores, pero **solo once
    puntuan**. Sumar los puntos de los cinco seria el error mas
    caro del informe: lo que cuenta es lo que ENTRA en el once y
    a quien desplaza.

    Y hay una asimetria que se dice cada vez que se cita el
    numero: lo que aporta el grande esta MEDIDO en esta
    temporada; lo que aportarian los que entran es una PROYECCION
    de la anterior. No son la misma clase de dato.
"""

from __future__ import annotations


# Solo puntuan once, y uno es el portero.
PLAZAS = 11


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
        "player": None,
        "share": None,
        "limit": None,
        "over_limit": None,
        "keep": {},
        "sell": {},
        "reason": motivo,
    }


def evaluar(
    roster: list | None,
    targets: list | None,
    matchdays: int,
    cash: int = 0,
    limit_share: float = 0.35,
) -> dict:
    """
    El activo mas concentrado de la plantilla, en dos columnas.

    Nunca lanza. Forma fija. No recomienda.
    """

    try:
        plantilla = [
            p
            for p in (roster or [])
            if isinstance(p, dict) and safe_int(p.get("price")) > 0
        ]

        if not plantilla or matchdays <= 0:
            return _vacio(
                "Sin plantilla o sin jornadas jugadas: no hay con "
                "que calcular."
            )

        valor_total = sum(
            safe_int(p.get("price")) for p in plantilla
        )

        grande = max(
            plantilla,
            key=lambda p: safe_int(p.get("price")),
        )

        parte = (
            safe_int(grande.get("price")) / valor_total
            if valor_total
            else 0.0
        )

        puntos_jornada = {
            str(p.get("id")): safe_int(p.get("points")) / matchdays
            for p in plantilla
        }

        suyos = puntos_jornada.get(str(grande.get("id")), 0.0)

        total_puntos = sum(puntos_jornada.values())

        parte_puntos = (
            suyos / total_puntos if total_puntos else 0.0
        )

        # ------------------------------------------------
        # COLUMNA TENER
        # ------------------------------------------------
        tener = {
            "points_per_matchday": round(suyos, 2),
            "points_share": round(100 * parte_puntos, 1),
            "value_share": round(100 * parte, 2),
            "euros_per_point": (
                round(safe_int(grande.get("price")) / suyos)
                if suyos
                else None
            ),
            "rest_euros_per_point": (
                round(
                    (valor_total - safe_int(grande.get("price")))
                    / (total_puntos - suyos)
                )
                if (total_puntos - suyos) > 0
                else None
            ),
            "daily_percent": (
                round(
                    100
                    * safe_int(grande.get("price_increment"))
                    / safe_int(grande.get("price")),
                    3,
                )
                if safe_int(grande.get("price"))
                else None
            ),
            "starter_probability": safe_float(
                grande.get("starter_probability")
            ),
            "matchdays": matchdays,
            "warning": (
                f"Lo que aporta esta MEDIDO, pero sobre "
                f"{matchdays} jornadas. Vender al mejor de la "
                f"plantilla con esa muestra puede ser el error "
                f"mas caro del año."
            ),
        }

        # ------------------------------------------------
        # COLUMNA VENDER
        # ------------------------------------------------
        disponible = safe_int(grande.get("price")) + safe_int(cash)

        comprables = sorted(
            (
                t
                for t in (targets or [])
                if isinstance(t, dict)
                and safe_int(t.get("market_price")) > 0
                and str(t.get("decision")) != "NO_DISPONIBLE"
            ),
            key=lambda t: -safe_int(t.get("expected_points")),
        )

        cesta = []
        gastado = 0

        for objetivo in comprables:

            precio = safe_int(objetivo.get("market_price"))

            if gastado + precio > disponible:
                continue

            gastado += precio

            cesta.append({
                "name": objetivo.get("name"),
                "price": precio,
                "expected_points": safe_int(
                    objetivo.get("expected_points")
                ),
                "projected_per_matchday": round(
                    safe_int(objetivo.get("expected_points")) / 38,
                    2,
                ),
                "starter_probability": safe_float(
                    objetivo.get("starter_probability")
                ),
            })

            if len(cesta) >= 5:
                break

        # SOLO ONCE PUNTUAN. Los que entrarian de verdad al once
        # son los que superan al peor titular de campo actual.
        de_campo = sorted(
            (
                p
                for p in plantilla
                if safe_int(p.get("position")) != 1
                and str(p.get("id")) != str(grande.get("id"))
            ),
            key=lambda p: puntos_jornada.get(str(p.get("id")), 0.0),
        )

        peor = (
            puntos_jornada.get(str(de_campo[0].get("id")), 0.0)
            if de_campo
            else 0.0
        )

        # SOLO HAY DIEZ PLAZAS DE CAMPO
        #
        #     Con 21 M caben cinco fichas, pero el once no crece.
        #     Contar cinco "entradas" diria que se suman cinco
        #     rendimientos cuando como mucho se sustituyen unos
        #     titulares por otros.
        entran = [
            c
            for c in cesta
            if c["projected_per_matchday"] > peor
        ][: PLAZAS - 1]

        # El once pierde al grande y gana a los que entran,
        # desplazando a los peores titulares actuales.
        desplazados = sum(
            puntos_jornada.get(str(p.get("id")), 0.0)
            for p in de_campo[: max(len(entran) - 1, 0)]
        )

        neto = (
            sum(c["projected_per_matchday"] for c in entran)
            - suyos
            - desplazados
        )

        nueva_concentracion = None

        if cesta:
            mayor = max(c["price"] for c in cesta)
            nuevo_total = (
                valor_total
                - safe_int(grande.get("price"))
                + gastado
            )
            nueva_concentracion = (
                round(100 * mayor / nuevo_total, 2)
                if nuevo_total
                else None
            )

        vender = {
            "frees": safe_int(grande.get("price")),
            "available_to_spend": disponible,
            "basket": cesta,
            "basket_cost": gastado,
            "cash_left": disponible - gastado,
            "would_enter_xi": len(entran),
            "net_points_per_matchday": round(neto, 2),
            "new_max_share": nueva_concentracion,
            "warning": (
                "Con este dinero caben cinco, pero solo puntuan "
                "once: lo que suma es lo que ENTRA en el once "
                "menos a quien desplaza. Y sus puntos son una "
                "PROYECCION de la temporada pasada, no una "
                "medicion de esta."
            ),
        }

        return {
            "available": True,
            "player": grande.get("name"),
            "share": round(100 * parte, 2),
            "limit": round(100 * limit_share, 2),
            "over_limit": bool(parte > limit_share),
            "keep": tener,
            "sell": vender,
            "reason": _reason(grande, tener, vender, parte, limit_share),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo evaluar: "
            f"{type(error).__name__}: {error}"
        )


def _reason(grande, tener, vender, parte, limite) -> str:

    nombre = grande.get("name")

    frase = (
        f"{nombre} es el {tener['value_share']} % del dinero y el "
        f"{tener['points_share']} % de los puntos"
        + (
            f", por encima del tope del {round(100 * limite)} %."
            if parte > limite
            else "."
        )
    )

    if tener["euros_per_point"] and tener["rest_euros_per_point"]:

        # LOS PUNTOS DE MILES, UNO A UNO (20/09/2026)
        #
        #     Aplicar `.replace(",", ".")` a la frase entera se
        #     come las comas de la prosa. Ya ha pasado cuatro
        #     veces en este proyecto: "el resto de la plantilla,
        #     714.202" salia como "el resto de la plantilla.
        #     714.202". Se formatea cada numero por separado.
        suyo = f"{tener['euros_per_point']:,}".replace(",", ".")
        resto = (
            f"{tener['rest_euros_per_point']:,}".replace(",", ".")
        )

        frase += (
            f" Cuesta {suyo} EUR por punto por jornada; el resto "
            f"de la plantilla, {resto}."
        )

    neto = vender["net_points_per_matchday"]

    if neto is None:
        return frase

    if neto > 0:
        frase += (
            f" Cambiarlo por lo que hay hoy en el escaparate "
            f"daria {neto:+.2f} puntos por jornada."
        )
    else:
        frase += (
            f" Cambiarlo por lo que hay hoy en el escaparate "
            f"daria {neto:+.2f} puntos por jornada: el mercado de "
            f"hoy no tiene con que sustituirlo."
        )

    return frase + " Sin recomendacion: decide el dueño."
