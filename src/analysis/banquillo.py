"""
Los puntos que se quedaron sentados.

LA CUENTA QUE LO CAMBIA TODO (17/09/2026)

    Cuatro noches empujando hacia "sube patrimonio o no ganamos".
    El arbitro desmonto la tesis: el valor de plantilla no
    explica los puntos en esta liga (r = +0,553 con siete
    equipos, cuando haria falta 0,754).

    Lo que gana son los puntos, y los puntos los marcan ONCE
    jugadores. Y la distancia real es esta:

        13 puntos  /  35 jornadas  =  0,371 puntos por jornada

    No hace falta un equipo nuevo. Hace falta sacarle al lider
    cuatro decimas de punto por jornada. Si el once esta dejando
    mas que eso en el banquillo, la liga esta ahi y no en el
    mercado.

QUE MIDE ESTE MODULO

    Por cada jornada cerrada: lo que puntuo el once que se
    alineo contra lo que habria puntuado el mejor once legal de
    esa misma plantilla, ya sabiendo los resultados. La
    diferencia son los puntos que se quedaron sentados.

    Y lo compara con las 0,371 que hacen falta.

MEDIA MEDICION HONESTA VALE; UNA ENTERA INVENTADA, NO

    Una jornada solo cuenta si su reconstruccion esta entera y
    cuadra con lo que Biwenger pago. Las demas salen listadas
    con su motivo y fuera de la media.

    Es lo que separa "el motor deja 7,7 puntos por jornada" de
    "faltaba media alineacion en la foto".

NO DECIDE NADA

    No toca el motor de alineacion, ni un umbral, ni el mercado.
    Cuenta lo que paso y lo pone donde se vea.
"""

from __future__ import annotations


# CUANDO UNA JORNADA CASI CUADRA (17/09/2026)
#
#     El cuadre es exacto y no se afloja: una media que mezcla
#     reconstrucciones buenas con reconstrucciones cojas no mide
#     nada.
#
#     Pero "no cuadra" a secas tira a la basura una jornada que
#     se queda a 3 puntos de 73 igual que una que se queda a 16
#     de 29, y la primera es la unica evidencia que hay.
#
#     Asi que esas se publican APARTE, etiquetadas, y NUNCA
#     entran en la media estricta. El descuadre conocido tiene
#     nombre: un jugador fichado a mitad de semana cuenta como 0
#     por diseño, porque no se sabe cuanto de su total es de esa
#     jornada.
CASI_CUADRA_PERCENT = 5.0


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


def _fiable(fila: dict) -> bool:
    return bool(
        fila.get("medible")
        and fila.get("cuadra")
        and fila.get("reconstruccion_completa")
    )


def _motivo(fila: dict) -> str:
    """Por que una jornada no entra en la media."""

    if not fila.get("medible"):
        return str(fila.get("motivo") or "No medible.")

    if not fila.get("reconstruccion_completa"):
        return str(
            fila.get("motivo_incompleta")
            or "La reconstruccion del once no esta entera."
        )

    if not fila.get("cuadra"):

        once = safe_int(fila.get("puntos_once"))
        biwenger = fila.get("puntos_biwenger")

        return (
            f"El once reconstruido suma {once} y Biwenger pago "
            f"{biwenger} esa jornada: la reconstruccion no "
            f"coincide con el dato oficial."
        )

    return "Cuenta."


def con_la_plantilla_de_hoy(fila: dict, plantilla_actual) -> dict:
    """
    De los puntos que se dejaron sentados, cuantos podriamos
    recuperar HOY.

    POR QUE DOS CIFRAS Y NO UNA (18/09/2026)

        Los 8 puntos de la J4901 salian de dos cambios:

            Yusi Enriquez (4) por Djene (-1)     -> +5
            Lucas Cepeda  (3) por Pablo Duran (0) -> +3

        Yusi Enriquez ya no es nuestro: se traspaso a Prinzipote.
        Asi que cinco de esos ocho los aportaba alguien que hoy
        no tenemos.

        La primera cifra JUZGA al motor -eso se dejo, con la
        plantilla que habia-. La segunda es la que vale dinero
        -eso se podria ganar manaña-. Mezclarlas seria prometer
        un margen que no existe.

    Nunca lanza.
    """

    try:
        nuestros = set()

        for jugador in (plantilla_actual or []):

            if isinstance(jugador, dict):
                nuestros.add(safe_int(jugador.get("id")))
            else:
                nuestros.add(safe_int(jugador))

        detalle = fila.get("detalle") or {}

        faltaron = list(detalle.get("faltaron") or [])
        sobraron = list(detalle.get("sobraron") or [])

        # El cambio se empareja por posicion: el que debio jugar
        # ocupa el hueco del que jugo en su misma linea.
        cambios = []

        pendientes = list(sobraron)

        for entra in sorted(
            faltaron,
            key=lambda j: -safe_int(j.get("points")),
        ):
            pareja = None

            for indice, sale in enumerate(pendientes):
                if safe_int(sale.get("position")) == safe_int(
                    entra.get("position")
                ):
                    pareja = pendientes.pop(indice)
                    break

            if pareja is None:
                continue

            gana = safe_int(entra.get("points")) - safe_int(
                pareja.get("points")
            )

            sigue = safe_int(entra.get("id")) in nuestros

            cambios.append({
                "in": entra.get("name"),
                "in_id": safe_int(entra.get("id")),
                "out": pareja.get("name"),
                "position": safe_int(entra.get("position")),
                "points": gana,
                "still_ours": sigue,
            })

        historico = sum(c["points"] for c in cambios)

        de_hoy = sum(
            c["points"]
            for c in cambios
            if c["still_ours"]
        )

        perdidos = [c for c in cambios if not c["still_ours"]]

        return {
            "available": bool(cambios),

            "historical": historico,
            "with_todays_squad": de_hoy,

            "changes": cambios,
            "no_longer_ours": [c["in"] for c in perdidos],

            "reason": (
                f"{historico} puntos con la plantilla de "
                f"entonces; {de_hoy} con la de hoy."
                + (
                    " Ya no son nuestros: "
                    + ", ".join(c["in"] for c in perdidos)
                    + "."
                    if perdidos
                    else ""
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "historical": None,
            "with_todays_squad": None,
            "changes": [],
            "no_longer_ours": [],
            "reason": (
                f"No se pudo recalcular: "
                f"{type(error).__name__}: {error}"
            ),
        }


def puntos_en_el_banquillo(
    marcador: dict | None,
    race: dict | None = None,
    plantilla_actual=None,
) -> dict:
    """
    Cuantos puntos se dejaron sentados, y si eso es la liga.

    Nunca lanza.
    """

    try:
        filas = list((marcador or {}).get("jornadas") or [])

        # El marcador publica de mas reciente a mas antigua. Aqui
        # se lee en orden de calendario, que es como se cuenta
        # una temporada.
        filas = sorted(
            filas,
            key=lambda f: safe_int(f.get("round_id")),
        )

        detalle = []
        casi = []
        perdidos = 0
        jugados = 0
        techo = 0

        for fila in filas:

            cuenta = _fiable(fila)

            entrada = {
                "round_id": safe_int(fila.get("round_id")),
                "cuenta": cuenta,
                "motivo": _motivo(fila),

                "formacion": fila.get("formacion"),
                "puntos_once": fila.get("puntos_once"),
                "mejor_formacion": fila.get("mejor_formacion"),
                "mejor_puntos": fila.get("mejor_puntos"),
                "puntos_perdidos": fila.get("puntos_perdidos"),
                "eficiencia": fila.get("eficiencia"),

                "puntos_biwenger": fila.get("puntos_biwenger"),

                # LO UNICO ACCIONABLE: UN NOMBRE, NO UN PORCENTAJE
                "debieron_jugar": [
                    {
                        "name": j.get("name"),
                        "position": j.get("position"),
                        "points": j.get("points"),
                    }
                    for j in (
                        (fila.get("detalle") or {}).get("faltaron")
                        or []
                    )
                ],
                "jugaron_y_no_debian": [
                    {
                        "name": j.get("name"),
                        "position": j.get("position"),
                        "points": j.get("points"),
                    }
                    for j in (
                        (fila.get("detalle") or {}).get("sobraron")
                        or []
                    )
                ],
            }

            entrada["hoy"] = con_la_plantilla_de_hoy(
                fila,
                plantilla_actual,
            )

            # LOS TRES NUMEROS DEL BLOQUE 2
            entrada["puntos_vara_vieja"] = fila.get(
                "puntos_vara_vieja"
            )
            entrada["formacion_vara_vieja"] = fila.get(
                "formacion_vara_vieja"
            )
            entrada["vara_gana"] = (
                fila.get("puntos_once")
                - fila.get("puntos_vara_vieja")
                if fila.get("puntos_vara_vieja") is not None
                and fila.get("puntos_once") is not None
                else None
            )

            descuadre = fila.get("descuadre_percent")

            entrada["descuadre"] = fila.get("descuadre")
            entrada["descuadre_percent"] = descuadre

            # Ni cuadra ni es basura: se queda a un pelo.
            entrada["casi"] = bool(
                not cuenta
                and fila.get("medible")
                and fila.get("reconstruccion_completa")
                and descuadre is not None
                and descuadre <= CASI_CUADRA_PERCENT
            )

            detalle.append(entrada)

            if entrada["casi"]:
                casi.append(entrada)

            if not cuenta:
                continue

            jugados += 1
            perdidos += safe_int(fila.get("puntos_perdidos"))
            techo += safe_int(fila.get("mejor_puntos"))

        carrera = race or {}

        distancia = safe_int(carrera.get("points_behind"))
        ritmo_necesario = safe_float(carrera.get("required_pace"))

        por_jornada = (
            round(perdidos / jugados, 2)
            if jugados
            else None
        )

        # CUANTAS VECES LO QUE HACE FALTA
        #
        #     La cifra sola no dice nada. Puesta al lado de las
        #     0,371 que separan del lider, dice si la liga esta
        #     en el banquillo o en el mercado.
        veces = (
            round(por_jornada / ritmo_necesario, 1)
            if por_jornada and ritmo_necesario
            else None
        )

        return {
            "available": bool(filas),
            "observer_only": True,

            "jornadas_que_cuentan": jugados,
            "jornadas_observadas": len(filas),

            "puntos_perdidos": perdidos if jugados else None,
            "puntos_perdidos_por_jornada": por_jornada,
            "techo_acumulado": techo if jugados else None,

            "distancia_al_lider": distancia or None,
            "ritmo_necesario": ritmo_necesario,
            "veces_lo_que_hace_falta": veces,

            # LA EVIDENCIA QUE HAY CUANDO NO HAY NOTA
            #
            #     Separada de la media estricta a proposito. Se
            #     mira cuando `jornadas_que_cuentan` es 0, que es
            #     justo cuando el numero de arriba no dice nada.
            "jornadas_casi": len(casi),
            "puntos_perdidos_casi": (
                sum(
                    safe_int(j.get("puntos_perdidos"))
                    for j in casi
                )
                if casi
                else None
            ),
            "puntos_perdidos_casi_por_jornada": (
                round(
                    sum(
                        safe_int(j.get("puntos_perdidos"))
                        for j in casi
                    )
                    / len(casi),
                    2,
                )
                if casi
                else None
            ),

            # LA RED: EL ACUMULADO DE LOS TRES NUMEROS
            #
            #     Si tras tres jornadas la vara nueva va por
            #     detras de la vieja, esto lo dice sin que haya
            #     que discutirlo.
            "net": _red(detalle),

            # Los 8 puntos, separados: lo que juzga al motor y lo
            # que se puede ganar manaña. Nunca sumados.
            "historical_points": sum(
                (j.get("hoy") or {}).get("historical") or 0
                for j in detalle
                if j.get("cuenta") or j.get("casi")
            ),
            "todays_points": sum(
                (j.get("hoy") or {}).get("with_todays_squad") or 0
                for j in detalle
                if j.get("cuenta") or j.get("casi")
            ),

            "jornadas": detalle,
            "veredicto": _veredicto(
                jugados,
                perdidos,
                por_jornada,
                veces,
                distancia,
                len(filas),
                casi,
                ritmo_necesario,
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "jornadas": [],
            "reason": (
                f"No se pudo contar el banquillo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _red(detalle: list) -> dict:
    """
    El acumulado de los tres numeros, desde que hay con que.

    Solo cuentan las jornadas que TIENEN once alternativo
    anotado: las anteriores al cambio de vara no se pueden
    comparar, y meterlas como ceros diria que la vara nueva no
    aporto nada cuando en realidad no existia.
    """

    comparables = [
        j
        for j in detalle
        if j.get("puntos_vara_vieja") is not None
        and (j.get("cuenta") or j.get("casi"))
    ]

    if not comparables:
        return {
            "available": False,
            "matchdays": 0,
            "reason": (
                "Todavia no hay ninguna jornada jugada con los "
                "factores puestos: la comparacion empieza en la "
                "proxima."
            ),
        }

    alineado = sum(
        safe_int(j.get("puntos_once")) for j in comparables
    )
    vieja = sum(
        safe_int(j.get("puntos_vara_vieja")) for j in comparables
    )
    techo = sum(
        safe_int(j.get("mejor_puntos")) for j in comparables
    )

    diferencia = alineado - vieja

    if diferencia > 0:
        veredicto = (
            f"La vara nueva va {diferencia} puntos POR DELANTE "
            f"de la vieja en {len(comparables)} jornada(s)."
        )
    elif diferencia < 0:
        veredicto = (
            f"LA VARA NUEVA VA {abs(diferencia)} PUNTOS POR "
            f"DETRAS DE LA VIEJA en {len(comparables)} "
            f"jornada(s). Si esto se mantiene, se apaga con "
            f"BORDALAS_VARA_PLANA=1."
        )
    else:
        veredicto = (
            f"Empate entre las dos varas en "
            f"{len(comparables)} jornada(s)."
        )

    if len(comparables) < 3:
        veredicto += (
            " Con menos de tres jornadas es un aviso, no una "
            "conclusion."
        )

    return {
        "available": True,
        "matchdays": len(comparables),
        "aligned": alineado,
        "old_vara": vieja,
        "best_possible": techo,
        "difference": diferencia,
        "behind": diferencia < 0,
        "reason": veredicto,
    }


def _veredicto(
    jugados: int,
    perdidos: int,
    por_jornada,
    veces,
    distancia: int,
    observadas: int,
    casi=None,
    ritmo_necesario=None,
) -> str:

    if not jugados:

        sin_nota = (
            f"Ninguna de las {observadas} jornadas observadas "
            f"cuadra todavia. Sin nota: no se inventa."
        )

        if not casi:
            return sin_nota

        sentados = sum(
            safe_int(j.get("puntos_perdidos"))
            for j in casi
        )

        media = round(sentados / len(casi), 2)

        indicio = (
            f" Lo unico que hay: {len(casi)} jornada(s) con la "
            f"alineacion entera y menos de "
            f"{CASI_CUADRA_PERCENT:.0f} % de descuadre dejaron "
            f"{sentados} puntos en el banquillo ({media} por "
            f"jornada)."
        )

        if ritmo_necesario:
            indicio += (
                f" Hacen falta {ritmo_necesario} por jornada "
                f"para alcanzar al lider. Es un indicio, no una "
                f"nota."
            )

        return sin_nota + indicio

    cuantas = (
        f"{jugados} jornada"
        + ("s" if jugados != 1 else "")
    )

    cabecera = (
        f"{perdidos} puntos sentados en {cuantas} "
        f"({por_jornada} por jornada)."
    )

    if veces is None:
        return cabecera

    if jugados < 3:
        return cabecera + (
            f" Son {veces} veces las que hacen falta para "
            f"alcanzar al lider, pero con {cuantas} no es una "
            f"conclusion: es un aviso."
        )

    if veces >= 2:
        return cabecera + (
            f" Es {veces} veces lo que hace falta para alcanzar "
            f"al lider. La liga esta en el banquillo, no en el "
            f"mercado."
        )

    if veces >= 1:
        return cabecera + (
            f" Justo del orden de lo que hace falta ({veces}x). "
            f"Alinear mejor da para pelearla, pero no sobra."
        )

    cerrado = cabecera + (
        f" Es menos de lo que hace falta ({veces}x): el once ya "
        f"esta casi optimo y el problema esta en la calidad de "
        f"la plantilla, no en elegirla."
    )

    if distancia:
        cerrado += (
            f" Con {distancia} puntos de distancia, hay que "
            f"volver al mercado con otra cabeza."
        )

    return cerrado
