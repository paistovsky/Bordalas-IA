"""
Un grande solo se suelta si lo que entra cabe en el once.

LO QUE SUSTITUYE A LOS INTOCABLES (dueño, 21/09/2026)

    Habia una lista: de Clave para arriba, nadie se vendia. Nacio
    el 18/08 de "que no me venda a Yamal ni haga locuras" y
    protegia a cinco de catorce -Yamal, Exposito, Olasagasti,
    Djene y el portero-.

    El dueño la retira. No la sustituye otra lista: la sustituye
    la cuenta que se hizo con Yamal el 20/09.

POR QUE ESTA CUENTA ES MEJOR QUE LA LISTA

    Una lista protege al favorito aunque deje de rendir. La
    cuenta lo suelta el dia que deje de rendir, y hasta ese dia
    lo defiende mejor que la lista: con Yamal dijo que se queda
    porque el mercado de hoy lo sustituye 2,93 puntos por jornada
    PEOR, no porque sea Yamal.

    Ese es todo el cambio: de proteger por cariño a proteger por
    aritmetica.

A QUIEN SE LE APLICA

    A los grandes, que son los unicos donde el error es caro:

        - los que pesan mas de un 25 % de la plantilla, o
        - los tres que mas puntuan.

    Al resto no se le pide nada: son justo los que hay que poder
    rotar, y esa era la queja de la regla 14.

LA REGLA

    Si el neto en puntos por jornada no es CLARAMENTE positivo,
    no se vende. Y "claramente" tiene numero, porque la regla 18
    lo exige: ver `MARGEN_NETO`.

NO VENDE NADA

    Contesta si se puede. La orden la da el dueño.
"""

from __future__ import annotations


# Pesa demasiado para soltarlo sin hacer la cuenta.
PESO_GRANDE = 0.25


# O esta entre los que mas puntuan.
TOP_PUNTOS = 3


# EL "CLARAMENTE" DE "CLARAMENTE POSITIVO" (regla 18)
#
#     Con tres jornadas de muestra, un neto de +0,1 puntos por
#     jornada es ruido. Se pide medio punto por jornada, que en
#     35 jornadas son 17,5 puntos: del orden de la distancia que
#     separa del lider.
#
#     No es un umbral de mercado -no mueve ningun liston ni
#     ningun tope-: es cuanto tiene que ganar una venta para que
#     merezca la pena deshacer un activo grande.
MARGEN_NETO = 0.5


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _vacio(motivo: str) -> dict:
    # La forma no cambia con los datos: las mismas claves haya
    # cuenta o no. Regla de la casa desde el 18/09.
    return {
        "available": False,
        "player": None,
        "is_big": None,
        "why_big": None,
        "share": None,
        "points_rank": None,
        "gives_up": None,
        "brings_in": None,
        "displaces": None,
        "net_points_per_matchday": None,
        "required_net": MARGEN_NETO,
        "can_sell": None,
        "reason": motivo,
    }


def es_grande(jugador: dict, roster: list, matchdays: int) -> dict:
    """
    ¿Es de los que hay que pensar antes de soltar?

    Forma fija.
    """

    salida = {
        "is_big": False,
        "why_big": None,
        "share": None,
        "points_rank": None,
    }

    try:
        plantilla = [
            p
            for p in (roster or [])
            if isinstance(p, dict)
        ]

        total = sum(
            safe_int(p.get("price")) for p in plantilla
        )

        parte = (
            safe_int(jugador.get("price")) / total
            if total
            else 0.0
        )

        salida["share"] = round(100 * parte, 2)

        por_puntos = sorted(
            plantilla,
            key=lambda p: -safe_int(p.get("points")),
        )

        posicion = next(
            (
                i + 1
                for i, p in enumerate(por_puntos)
                if str(p.get("id")) == str(jugador.get("id"))
            ),
            None,
        )

        salida["points_rank"] = posicion

        motivos = []

        if parte > PESO_GRANDE:
            motivos.append(
                f"pesa el {salida['share']} % de la plantilla, "
                f"por encima del {round(100 * PESO_GRANDE)} %"
            )

        if posicion is not None and posicion <= TOP_PUNTOS:
            motivos.append(
                f"es el {posicion}.º que mas puntua"
            )

        salida["is_big"] = bool(motivos)
        salida["why_big"] = "; ".join(motivos) or None

        return salida

    except Exception:                                # noqa: BLE001
        return salida


def evaluar_venta(
    jugador: dict | None,
    roster: list | None,
    entrantes: list | None,
    matchdays: int,
) -> dict:
    """
    ¿Se puede soltar a este, con lo que entraria a cambio?

    `entrantes` son fichas con `projected_per_matchday`: lo que se
    compraria con el dinero que libera.

    Nunca lanza. Forma fija. No vende nada.
    """

    try:
        if not jugador or not roster or matchdays <= 0:
            return _vacio(
                "Sin jugador, sin plantilla o sin jornadas "
                "jugadas: no se puede hacer la cuenta."
            )

        tamaño = es_grande(jugador, roster, matchdays)

        aporta = (
            safe_int(jugador.get("points")) / matchdays
        )

        entra = sum(
            safe_float(e.get("projected_per_matchday"))
            for e in (entrantes or [])
        )

        # DESPLAZA A TITULARES, NO A SUPLENTES (21/09/2026)
        #
        #     Esto ordenaba TODOS los jugadores de campo por
        #     puntos y desplazaba a los peores. Pero los peores
        #     son suplentes, y sacar a un suplente no cuesta ni un
        #     punto: el neto salia inflado.
        #
        #     Con Yamal daba +0,70 y "se puede vender", cuando la
        #     cuenta buena da negativo. Es exactamente el error
        #     que la lista de intocables tapaba y que esta prueba
        #     tiene que hacer bien, porque ya no hay lista debajo.
        #
        #     Solo puntuan once: quien entra desplaza a un
        #     TITULAR, y el coste es lo que ese titular aportaba.
        titulares = [
            p
            for p in roster
            if safe_int(p.get("position")) != 1
            and str(p.get("id")) != str(jugador.get("id"))
            and (p.get("is_starter") or p.get("in_lineup"))
        ]

        # Si la plantilla no dice quien es titular, se toma a los
        # diez de campo que mas puntuan: es la mejor aproximacion
        # y no regala desplazamientos gratis.
        if not titulares:
            titulares = sorted(
                (
                    p
                    for p in roster
                    if safe_int(p.get("position")) != 1
                    and str(p.get("id")) != str(jugador.get("id"))
                ),
                key=lambda p: -safe_int(p.get("points")),
            )[:10]

        de_campo = sorted(
            titulares,
            key=lambda p: safe_int(p.get("points")),
        )

        cuantos_desplaza = max(len(entrantes or []) - 1, 0)

        desplazados = sum(
            safe_int(p.get("points")) / matchdays
            for p in de_campo[:cuantos_desplaza]
        )

        neto = entra - aporta - desplazados

        # A un jugador que no es grande no se le pide nada: es
        # justo el que hay que poder rotar.
        if not tamaño["is_big"]:
            return {
                "available": True,
                "player": jugador.get("name"),
                "is_big": False,
                "why_big": None,
                "share": tamaño["share"],
                "points_rank": tamaño["points_rank"],
                "gives_up": round(aporta, 2),
                "brings_in": round(entra, 2),
                "displaces": round(desplazados, 2),
                "net_points_per_matchday": round(neto, 2),
                "required_net": MARGEN_NETO,
                "can_sell": True,
                "reason": (
                    f"{jugador.get('name')} no es un activo "
                    f"grande: no hace falta la cuenta para "
                    f"soltarlo."
                ),
            }

        puede = neto >= MARGEN_NETO

        return {
            "available": True,
            "player": jugador.get("name"),
            "is_big": True,
            "why_big": tamaño["why_big"],
            "share": tamaño["share"],
            "points_rank": tamaño["points_rank"],
            "gives_up": round(aporta, 2),
            "brings_in": round(entra, 2),
            "displaces": round(desplazados, 2),
            "net_points_per_matchday": round(neto, 2),
            "required_net": MARGEN_NETO,
            "can_sell": bool(puede),
            "reason": (
                f"{jugador.get('name')} {tamaño['why_big']}. "
                f"Suelta {aporta:.2f} puntos por jornada y entra "
                f"{entra:.2f} desplazando {desplazados:.2f}: neto "
                f"{neto:+.2f}. "
                + (
                    f"Pasa del margen de {MARGEN_NETO:+.2f} que "
                    f"se exige para deshacer un grande."
                    if puede
                    else f"NO se vende: hace falta al menos "
                    f"{MARGEN_NETO:+.2f} para que la operacion "
                    f"sea una mejora y no un movimiento."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo evaluar: "
            f"{type(error).__name__}: {error}"
        )
