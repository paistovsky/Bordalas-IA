"""
El dashboard se audita a si mismo antes de publicarse.

POR QUE EXISTE

    El dueno del equipo lo dijo asi: "El dashboard son mis ojos.
    No puede ser que haya algo ahi que Pepe este haciendo y no
    aparezca, o aparezca mal, que es peor."

    Y habia pasado dos veces el mismo dia:

    - Tres pujas vivas en Biwenger por 3.126.002 EUR. El panel de
      CAJA las contaba bien. La tabla de OBJETIVOS decia "0 CON
      PUJA" y guiones en toda la columna, porque nunca se le paso
      el dato y ademas el recorte a 12 filas dejaba fuera a dos
      de los tres jugadores.

    - El XI con "sin dato" en los once mientras la consola decia
      96 %.

    En los dos casos el fallo no fue un numero mal calculado: fue
    que una parte de la pantalla sabia algo y otra no, y nada
    comparaba las dos.

QUE HACE

    Cruza el snapshot -la verdad- con lo que va a salir pintado.
    Cada comprobacion dice que esperaba, que encontro y si cuadra.

    No corrige nada. Levanta la mano.

COMO SE LEE

    `ok: false` en cualquier fila significa que el dashboard esta
    ensenando menos -o distinto- de lo que Pepe tiene hecho. En
    ese estado no se decide mirando la pantalla.
"""

from __future__ import annotations


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _check(
    key: str,
    label: str,
    expected,
    found,
    detail: str = "",
) -> dict:
    return {
        "key": key,
        "label": label,
        "expected": expected,
        "found": found,
        "ok": expected == found,
        "detail": detail,

        # De donde sale cada lado de la comparacion. Sin esto la
        # pantalla escribe "Biwenger dice X" incluso cuando el
        # numero no viene de Biwenger.
        "source": "BIWENGER",
        "expected_label": None,
        "found_label": None,
    }


def build_consistency_report(
    dashboard: dict,
    snapshot: dict,
    current_user_id=None,
) -> dict:
    """
    Nunca lanza. Si no puede comprobar algo lo dice, en vez de
    dar por bueno lo que no ha mirado.
    """

    try:
        comprobaciones = []

        mercado = (snapshot or {}).get("market") or {}

        # ------------------------------------------------------
        # 1. PUJAS VIVAS
        #
        # Las que hay en Biwenger tienen que estar en la tabla de
        # objetivos con su importe. Esta es la que fallo.
        # ------------------------------------------------------

        exposicion = dashboard.get("exposure") or {}
        adquisicion = dashboard.get("acquisition") or {}

        vivas = safe_int(exposicion.get("operation_count"))

        objetivos = adquisicion.get("targets") or []

        pintadas = sum(
            1
            for fila in objetivos
            if safe_int(fila.get("live_bid")) > 0
        )

        comprometido = safe_int(
            exposicion.get("committed_total")
        )

        pintado_total = sum(
            safe_int(fila.get("live_bid"))
            for fila in objetivos
        )

        comprobaciones.append(
            _check(
                "live_bids_shown",
                "Pujas vivas visibles en OBJETIVOS",
                vivas,
                pintadas,
                (
                    "Cada puja puesta en Biwenger tiene que "
                    "aparecer en la tabla con su importe."
                ),
            )
        )

        comprobaciones.append(
            _check(
                "live_bid_amount_shown",
                "Euros comprometidos visibles",
                comprometido,
                pintado_total,
                (
                    "La suma de la columna PUESTO tiene que ser "
                    "la misma que la de CAJA."
                ),
            )
        )

        # ------------------------------------------------------
        # 2. PUBLICACIONES
        # ------------------------------------------------------

        propios = {
            safe_int(jugador.get("id"))
            for jugador in ((snapshot or {}).get("my_team") or [])
        }

        publicados = sum(
            1
            for venta in (mercado.get("sales") or [])
            if isinstance(venta, dict)
            and safe_int(
                (venta.get("player") or {}).get("id")
            )
            in propios
        )

        listados = safe_int(
            (dashboard.get("listings") or {}).get(
                "listing_count"
            )
        )

        comprobaciones.append(
            _check(
                "listings_shown",
                "Publicaciones nuestras",
                publicados,
                listados,
                (
                    "Lo que tenemos puesto a la venta en Biwenger "
                    "frente a lo que dice el panel."
                ),
            )
        )

        # ------------------------------------------------------
        # 3. OFERTAS RECIBIDAS
        # ------------------------------------------------------

        recibidas = 0

        for oferta in (mercado.get("offers") or []):

            if not isinstance(oferta, dict):
                continue

            emisor = oferta.get("from") or {}
            emisor_id = emisor.get("id") if isinstance(
                emisor, dict
            ) else None

            # Las nuestras son pujas, no ofertas recibidas.
            if (
                current_user_id is not None
                and safe_int(emisor_id) == safe_int(
                    current_user_id
                )
            ):
                continue

            recibidas += 1

        mostradas = len(dashboard.get("offers") or [])

        comprobaciones.append(
            _check(
                "offers_shown",
                "Ofertas recibidas",
                recibidas,
                mostradas,
                (
                    "Ofertas de compra por jugadores nuestros que "
                    "estan sobre la mesa ahora mismo."
                ),
            )
        )

        # ------------------------------------------------------
        # 4. LA ULTIMA ESCRITURA
        #
        # Si el ciclo escribio, la pantalla tiene que poder decir
        # que escribio.
        #
        # LA FALSA ALARMA DEL 23/08/2026
        #
        #     "ESTA PANTALLA NO CUADRA CON BIWENGER. La ultima
        #      escritura esta contada: Biwenger dice true, aqui
        #      sale false."
        #
        #     Y la pantalla la tenia contada, entera:
        #
        #         action   RAISE_COUNTER
        #         success  true
        #         http     200
        #         status   null      <- lo unico vacio
        #
        #     Esta guarda exigia `status`, que no es el desenlace:
        #     es un campo opcional que solo rellenan algunas vias
        #     de escritura -`_compact_execution` lo copia con
        #     `result.get("status")`- y la contraoferta no lo trae.
        #     El desenlace de verdad son `success` y `http_status`.
        #
        #     Pedir un campo que no todas las vias rellenan es
        #     confundir "no lo se" con "no ha pasado". Esa es
        #     exactamente la regla que este fichero existe para
        #     defender, y aqui estaba rota del lado contrario:
        #     acusando a la pantalla de esconder algo que si
        #     enseñaba.
        #
        # LO QUE SE EXIGE AHORA
        #
        #     Dos cosas, las mismas que promete el texto de la
        #     fila: el QUE -un nombre de accion- y el COMO ACABO
        #     -cualquiera de los campos que si describen el
        #     desenlace-.
        #
        #     Y una tercera que antes no estaba: que la escritura
        #     enseñada sea la de ESTE ciclo. Cuando `last_execution`
        #     se cae al historial porque el ciclo no supo nombrar
        #     lo que hizo, la pantalla enseña una escritura vieja
        #     con cara de reciente. Eso si es el fallo que esta
        #     fila deberia haber cazado.
        # ------------------------------------------------------

        ciclo = dashboard.get("cycle") or {}
        ultima = dashboard.get("last_execution") or {}

        escribio = bool(ciclo.get("write_used"))

        accion_enseñada = ultima.get("action")

        # El COMO ACABO. Basta con uno: no todas las vias de
        # escritura rellenan los mismos campos.
        dice_como_acabo = (
            ultima.get("succeeded") is not None
            or ultima.get("success") is not None
            or bool(ultima.get("status"))
            or ultima.get("http_status") is not None
        )

        # Y que sea la de este ciclo, no una del historial.
        es_de_este_ciclo = (
            accion_enseñada is not None
            and accion_enseñada == ciclo.get("action")
        )

        contada = bool(
            accion_enseñada
            and dice_como_acabo
            and es_de_este_ciclo
        )

        comprobaciones.append(
            _check(
                "last_write_shown",
                "La ultima escritura esta contada",
                escribio,
                contada if escribio else False,
                (
                    "Si el ciclo ha escrito en Biwenger, la "
                    "pantalla tiene que decir el que y el como "
                    "acabo."
                ),
            )
            if escribio
            else _check(
                "last_write_shown",
                "La ultima escritura esta contada",
                False,
                False,
                "Este ciclo no ha escrito nada.",
            )
        )

        # ------------------------------------------------------
        # 4-bis. Y QUE NO SEA DE ANTEAYER
        #
        # La comprobacion de arriba tiene un agujero de nacimiento:
        # compara `cycle.write_used` contra campos de
        # `last_execution`, y LOS DOS SALEN DEL MISMO FICHERO. Se
        # esta comparando consigo misma, asi que no puede fallar.
        #
        # Por eso el 17/08/2026 este panel decia "todo lo que Pepe
        # tiene hecho aparece en pantalla", con las seis en verde,
        # mientras el cuadro titulado ESTE CICLO enseñaba una
        # escritura del dia anterior. Un chequeo que no puede
        # fallar no es un chequeo.
        #
        # Esta fila mira otra cosa: la EDAD. Y esa si es
        # verificable, porque el reloj no sale del fichero.
        # ------------------------------------------------------

        edad = ciclo.get("age_seconds")

        if edad is None:

            comprobaciones.append(
                {
                    **_check(
                        "last_write_fresh",
                        "El ciclo que se enseña es de ahora",
                        "con fecha",
                        "sin fecha",
                        (
                            "El ultimo ciclo no trae marca de "
                            "tiempo legible, asi que no se puede "
                            "saber si lo que se enseña es de ahora "
                            "o de anteayer."
                        ),
                    ),
                    "source": "RELOJ",
                }
            )

        else:

            horas = edad / 3600.0

            comprobaciones.append(
                {
                    **_check(
                        "last_write_fresh",
                        "El ciclo que se enseña es de ahora",
                        False,
                        bool(ciclo.get("stale")),
                        (
                            f"El cuadro ESTE CICLO tiene "
                            f"{horas:.1f} h. Ese fichero solo se "
                            "reescribe cuando el motor con permiso "
                            "de escritura ejecuta, asi que si se "
                            "queda viejo la pantalla lo sigue "
                            "enseñando como si acabara de pasar."
                        ),
                    ),
                    "source": "RELOJ",
                    "expected_label": "reciente",
                    "found_label": f"hace {horas:.1f} h",
                }
            )

        # ------------------------------------------------------
        # 5. TITULARIDAD DEL ONCE
        # ------------------------------------------------------

        alineacion = dashboard.get("lineup") or {}

        total_xi = safe_int(alineacion.get("starter_data_total"))
        con_dato = safe_int(
            alineacion.get("starter_data_players")
        )

        # OJO CON EL TEXTO DE ESTA FILA.
        #
        # Las cuatro de arriba comparan contra Biwenger. Esta no:
        # compara el tamano del XI contra cuantos de esos once
        # tienen pronostico. Decir "Biwenger dice 11" aqui seria
        # mentir sobre el origen del numero, en un panel cuyo
        # unico trabajo es no mentir.
        comprobaciones.append(
            {
                **_check(
                    "starter_data",
                    "Pronostico de titular en el XI",
                    total_xi,
                    con_dato,
                    (
                        alineacion.get("starter_source_error")
                        or (
                            "El tablero de titularidad trae "
                            f"{alineacion.get('starter_board_players')} "
                            f"jugadores (cache "
                            f"{alineacion.get('starter_cache_status')}, "
                            f"jornada "
                            f"{alineacion.get('starter_board_matchday')}, "
                            f"generado "
                            f"{alineacion.get('starter_board_updated_at')}). "
                            "Sin pronostico, el XI se elige por valor y "
                            "puntos, no por quien va a jugar."
                        )
                    ),
                ),
                "source": "XI",
                "expected_label": f"{total_xi} jugadores en el XI",
                "found_label": f"{con_dato} con pronostico",
            }
        )

        fallos = [c for c in comprobaciones if not c["ok"]]

        return {
            "available": True,
            "ok": not fallos,
            "checks": comprobaciones,
            "failed": [c["key"] for c in fallos],
            "failed_count": len(fallos),
            "summary": (
                "Todo lo que Pepe tiene hecho aparece en pantalla."
                if not fallos
                else (
                    f"{len(fallos)} comprobacion(es) no cuadran: "
                    + ", ".join(c["label"] for c in fallos)
                    + ". La pantalla esta ensenando menos de lo "
                    "que hay."
                )
            ),
        }

    except Exception as error:
        return {
            "available": False,
            "ok": False,
            "checks": [],
            "failed": ["ERROR"],
            "failed_count": 1,
            "summary": (
                f"No se ha podido auditar el dashboard: "
                f"{type(error).__name__}: {error}"
            ),
        }
