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
        # ------------------------------------------------------

        ciclo = dashboard.get("cycle") or {}
        ultima = dashboard.get("last_execution") or {}

        escribio = bool(ciclo.get("write_used"))

        contada = bool(
            ultima.get("action")
            and ultima.get("status")
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
