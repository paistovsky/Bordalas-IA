"""
Por quien y cuanto va a pujar Pepe esta noche.

LO QUE PIDE EL DUEÑO, CON SUS PALABRAS (22/09/2026)

    «Tengo que saber por quien y cuanto va a pujar Pepe. Si lo
    va a hacer antes del reset, cuando yo duermo, no me entero
    de nada.»

LA SOMBRA MENTIA (25/09/2026)

    La primera version reconstruia la decision: reescalaba el valor
    a la moneda de la liga, elegia la via con un maximo propio y
    llamaba a `optimal_bid` con el bolsillo de la via de HOY. El
    25/09 decia:

        Lejeune   precio 3.560.000   pujaria 3.674.989

    y la decision real era `SUPERA_PRESUPUESTO`: con la moneda la
    operacion pasa a ser un fichaje, y el bolsillo de fichar eran
    2.208.580. Mezclaba el bolsillo de una via con el valor de otra.

    Una sombra que miente es una roja que puede significar cualquier
    cosa (doctrina 91). Y "no dice nada y puja" es peor que "dice y
    no puja": el dueño se entera por el saldo.

AHORA NO RECONSTRUYE NADA

    Pepe puja por cuatro caminos, y la sombra le pregunta a cada uno
    lo que YA decide, sin rehacer ni una cuenta:

        TABLERO             las filas que el tablero deja en `BID`.
                            Es la decision entera: via, bolsillo,
                            topes y puja salen del mismo sitio.
                            (La moneda de la liga esta encendida
                            desde el 25/09: ya va dentro.)

        VENTANA DEL RESET   `plan_del_reset`, la funcion que puja a
                            las 04:45, con el MISMO estado que ve el
                            ciclo. Lo unico que se le cambia es LA
                            HORA: se le dice que esta dentro de la
                            ventana. Todo lo demas -interruptor,
                            solvencia, caja, fichas, cupos- manda
                            igual que esta noche. `en_vivo=False`:
                            no ejecuta.

        CARRIL              NO SE PUEDE PREGUNTAR EN SECO. Decide
                            dentro de su ejecutor
                            (`carril_executor.correr`), y justo
                            despues escribe. Lo que falta para poder
                            llamarlo sin escribir es separar la
                            decision de la escritura en ese fichero.
                            Mientras tanto se enseña LO QUE DECIDIO
                            EN SU ULTIMA VUELTA, tal cual lo publica
                            el ciclo, y se dice que no es una
                            prediccion.

        BUY V10             NO CUBIERTO. Tampoco tiene decision en
                            seco, y lleva dormido desde el 04/09. Se
                            dice, no se calla.

NO DECIDE Y NO ESCRIBE

    Ni contra Biwenger, ni en los libros, ni en disco. No sale a la
    red y no mira el reloj: la hora que se le pone a la ventana la
    recibe. Forma fija. Nunca lanza.
"""

from __future__ import annotations


TABLERO = "TABLERO"
VENTANA = "VENTANA_DEL_RESET"
CARRIL = "CARRIL"
BUY_V10 = "BUY_V10"

# Lo que `plan_del_reset` escribe cuando NO se le pide ir en vivo.
# En la sombra no es un candado: es la sombra.
SIN_LIVE = "SIN_LIVE"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _euros(valor) -> str:
    return f"{safe_int(valor):,}".replace(",", ".")


def las_del_tablero(acquisition: dict | None, ya_vivas: bool = False) -> list:
    """
    Las filas que el tablero deja pujables, tal cual.

    LA QUE YA TIENE PUJA NUESTRA VIVA NO ES UNA PUJA NUEVA
    (25/09/2026). El tablero puede dejar en `BID` a quien ya tiene
    puja nuestra -el 18/09, Maffeo, con 1.664.350 del carril- y el
    que ejecuta, `decision_orchestrator`, lo aparta
    (`players_with_live_bid`). Asi que aqui tambien: salen aparte,
    con `ya_vivas=True`, como lo que son.
    """

    filas = []

    for f in ((acquisition or {}).get("targets") or []):

        if not isinstance(f, dict) or f.get("decision") != "BID":
            continue

        if bool(f.get("has_live_bid")) != ya_vivas:
            continue

        despliegue = f.get("deployment") or {}

        filas.append({
            "camino": TABLERO,
            "id": f.get("id"),
            "jugador": f.get("name"),
            "precio_de_mercado": safe_int(f.get("market_price")),
            "lo_que_pujaria": safe_int(f.get("bid")),
            "via": despliegue.get("route") or f.get("route"),
            "intent": f.get("intent"),
            "bolsillo": f.get("budget_applied"),
            "decision": "BID",
            "reason": (
                f.get("reason")
                or "El tablero la deja pujable; la ejecuta la accion "
                "de la vuelta."
            ),
        })

    return filas


def las_de_la_ventana(plan: dict | None) -> list:
    """Lo que `plan_del_reset` elegiria dentro de la ventana."""

    return [
        {
            "camino": VENTANA,
            "id": b.get("id"),
            "jugador": b.get("name"),
            "precio_de_mercado": safe_int(b.get("market_price")),
            "lo_que_pujaria": safe_int(b.get("bid")),
            "via": b.get("route"),
            "intent": b.get("intent"),
            "bolsillo": None,
            "decision": "BID",
            "reason": "La elige `plan_del_reset` con el estado de esta vuelta.",
        }
        for b in ((plan or {}).get("bids") or [])
        if isinstance(b, dict)
    ]


def la_lista(
    acquisition: dict | None,
    en_la_ventana: dict | None,
    carril: dict | None,
) -> dict:
    """
    Por quien y cuanto pujaria Pepe esta noche, camino a camino.

    `en_la_ventana` es lo que devuelve `plan_del_reset` con la hora
    puesta dentro de la ventana y `en_vivo=False`. `carril` es el
    bloque que publica la rendija. Se reciben: aqui no se calcula
    ninguna puja.
    """

    vacio = {
        "available": False,
        "n": 0,
        "mirados": 0,
        "filas": [],
        "caminos": {},
        "no_cubierto": [],
        "recortada": False,
        "reason": None,
    }

    try:
        del_tablero = las_del_tablero(acquisition)

        plan = en_la_ventana or {}
        bloqueo = plan.get("blocked_by")
        de_la_ventana = (
            las_de_la_ventana(plan)
            if bloqueo in (None, SIN_LIVE)
            else []
        )

        # UN JUGADOR, UNA PUJA. El tablero puja en cualquier vuelta;
        # cuando llega la ventana, `lectura_del_estado` ya lo deja
        # fuera por `has_live_bid`. Asi que si los dos lo eligen, la
        # que sale es la del tablero.
        del_tablero_ids = {f["id"] for f in del_tablero}
        de_la_ventana = [
            f for f in de_la_ventana if f["id"] not in del_tablero_ids
        ]

        filas = sorted(
            del_tablero + de_la_ventana,
            key=lambda f: (
                -f["lo_que_pujaria"],
                -f["precio_de_mercado"],
                str(f["jugador"] or ""),
            ),
        )

        carril = carril or {}

        ya_vivas = [
            {
                "jugador": f["jugador"],
                "precio_de_mercado": f["precio_de_mercado"],
                "puja_viva": safe_int(
                    next(
                        (
                            t.get("live_bid")
                            for t in ((acquisition or {}).get("targets") or [])
                            if isinstance(t, dict) and t.get("id") == f["id"]
                        ),
                        0,
                    )
                ),
            }
            for f in las_del_tablero(acquisition, ya_vivas=True)
        ]

        caminos = {
            TABLERO: {
                "cubierto": True,
                "n": len(del_tablero),
                "ya_vivas": ya_vivas,
                "reason": (
                    f"{len(del_tablero)} fila(s) en BID sin puja nuestra "
                    f"viva"
                    + (
                        f"; {len(ya_vivas)} en BID que ya la tienen y no "
                        f"se repiten: "
                        + ", ".join(v["jugador"] or "?" for v in ya_vivas)
                        if ya_vivas
                        else ""
                    )
                    + "."
                ),
            },
            VENTANA: {
                "cubierto": bool(plan),
                "n": len(de_la_ventana),
                "blocked_by": (
                    None if bloqueo == SIN_LIVE else bloqueo
                ),
                "reason": plan.get("reason") or "Sin plan de la ventana.",
            },
            CARRIL: {
                "cubierto": False,
                "n": None,
                "ultima_vuelta": carril.get("ultima_vuelta"),
                "ultima_decision": carril.get("ultima_decision"),
                "reason": (
                    "No se puede preguntar en seco: decide dentro de "
                    "`carril_executor.correr` y escribe a continuacion. "
                    "Esto es lo que decidio en su ULTIMA vuelta, no una "
                    "prediccion."
                ),
            },
            BUY_V10: {
                "cubierto": False,
                "n": None,
                "reason": (
                    "No cubierto: decide dentro de `build_controlled_run`. "
                    "Dormido desde el 04/09."
                ),
            },
        }

        mirados = sum(
            1 for f in ((acquisition or {}).get("targets") or [])
            if isinstance(f, dict)
        )

        if filas:
            titular = (
                f"Esta noche pujaria por {len(filas)}: "
                + ", ".join(
                    f"{f['jugador']} {_euros(f['lo_que_pujaria'])} EUR "
                    f"({f['camino']})"
                    for f in filas
                )
                + "."
            )
        else:
            titular = "Esta noche no pujaria por nadie."

        return {
            **vacio,
            "available": True,
            "n": len(filas),
            "mirados": mirados,
            "filas": filas,
            "caminos": caminos,
            "no_cubierto": [CARRIL, BUY_V10],
            "reason": (
                titular
                + " Cubre el tablero y la ventana del reset; el carril "
                "y BUY V10 no se pueden preguntar en seco."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar la lista de la noche: "
                f"{type(error).__name__}: {error}"
            ),
        }


def en_la_ventana(lectura: dict | None, segundos_dentro: int | None = None) -> dict:
    """
    `plan_del_reset` con la hora puesta dentro de la ventana.

    `lectura` es `la_subasta.lectura_del_estado(...)`, la MISMA que
    usa el ciclo. Solo se cambia `seconds_to_reset`. `en_vivo` va a
    False: se planifica, no se ejecuta.

    Nunca lanza.
    """

    try:
        from src.analysis.la_subasta import (
            MAX_PUJAS_PRIMER_DIA,
            VENTANA_MINUTOS,
            plan_del_reset,
        )

        base = dict(lectura or {})
        base["seconds_to_reset"] = (
            segundos_dentro
            if segundos_dentro is not None
            else VENTANA_MINUTOS * 60 // 2
        )

        return plan_del_reset(
            **base,
            ya_pujados=None,
            en_vivo=False,
            max_pujas=MAX_PUJAS_PRIMER_DIA,
        )

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "bids": [],
            "blocked_by": "ERROR",
            "reason": (
                f"No se pudo planificar la ventana: "
                f"{type(error).__name__}: {error}"
            ),
        }
