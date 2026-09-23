"""
La sombra de la puja: a quien pujaria Pepe y cuanto, aunque no pueda.

LO QUE PIDIO EL DUEÑO (23/09/2026)

    «Hay que ver lo que haria Pepe, porque no me fio.»

    Cada vuelta, en el panel y no en un `.jsonl`: si hay que mirarlo
    a las tres de la mañana, un libro no sirve.

        jugador · precio · lo que pujaria · la prima · por que ·
        que candado le queda

    Ordenado por lo que mas pujaria.

COMO SE CALCULA: LA MISMA CUENTA, CON LOS CANDADOS LEVANTADOS

    Se llama a `plan_del_reset` -la misma funcion que puja- con las
    puertas de MOMENTO abiertas: el interruptor, el reloj de
    solvencia, el bloqueo temporal y la ventana del reset. Cada una
    que hoy este cerrada se apunta como candado de la vuelta, con su
    motivo.

    Si aun asi la cesta sale vacia por DINERO -el tope de la ventana,
    caja libre / caida- o por FICHAS, se levanta tambien, y se apunta
    como candado. Asi la sombra dice por quien pujaria y que le
    falta, en vez de salir vacia sin decir por que.

    Una sombra calculada con otra cuenta no seria la sombra de nada:
    por eso no hay aqui ni una formula de puja.

SIN UNA SOLA ESCRITURA

    `en_vivo` va siempre a False, no se importa ningun cliente y no
    se toca `os.environ`: el interruptor se LEE, no se apaga. Guardia:
    `test_la_sombra_no_escribe`.

Forma fija. Nunca lanza.
"""

from __future__ import annotations


INTERRUPTOR = "INTERRUPTOR"
SOLVENCIA = "SOLVENCIA"
BLOQUEO_TEMPORAL = "BLOQUEO_TEMPORAL"
FUERA_DE_VENTANA = "FUERA_DE_VENTANA"
TOPE_DE_LA_VENTANA = "TOPE_DE_LA_VENTANA"
FICHAS_LIBRES = "FICHAS_LIBRES"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def la_sombra_de_la_puja(lectura: dict | None) -> dict:
    """
    Por quien pujaria Pepe en el reset, y que candado se lo impide.

    `lectura` es la salida de `la_subasta.lectura_del_estado`: la
    misma que usa el ciclo para pujar.
    """

    vacio = {
        "available": False,
        "observer_only": True,
        "bids": [],
        "candados": [],
        "committed": 0,
        "reason": None,
    }

    try:
        from src.analysis.la_subasta import (
            CAIDA_QUE_HAY_QUE_AGUANTAR,
            DISABLE_ENV,
            VENTANA_MINUTOS,
            _euros,
            _sin_subasta,
            el_freno_de_la_solvencia,
            plan_del_reset,
            ventana_abierta,
        )

        lectura = dict(lectura or {})

        candidatos = [
            c for c in (lectura.get("candidatos") or [])
            if isinstance(c, dict)
        ]

        # LOS CANDADOS DE LA VUELTA: cierran a todos a la vez.
        candados = []

        if _sin_subasta():
            candados.append(
                {
                    "candado": INTERRUPTOR,
                    "reason": f"{DISABLE_ENV} puesto.",
                }
            )

        freno = el_freno_de_la_solvencia(lectura.get("solvency_clock"))

        if freno["frena"]:
            candados.append(
                {"candado": SOLVENCIA, "reason": freno["reason"]}
            )

        if lectura.get("bloqueo_temporal"):
            candados.append(
                {
                    "candado": BLOQUEO_TEMPORAL,
                    "reason": (
                        f"Operaciones bloqueadas en fase "
                        f"«{lectura['bloqueo_temporal']}»."
                    ),
                }
            )

        ventana = ventana_abierta(lectura.get("seconds_to_reset"))

        if not ventana["abierta"]:
            candados.append(
                {
                    "candado": FUERA_DE_VENTANA,
                    "reason": ventana["reason"],
                }
            )

        # LA MISMA CUENTA, CON LAS PUERTAS DE MOMENTO ABIERTAS.
        base = {
            **lectura,
            "solvency_clock": {"state": "SIN_DEUDA", "deficit": 0},
            "bloqueo_temporal": None,

            # Dentro de la ventana: la mitad de ella.
            "seconds_to_reset": VENTANA_MINUTOS * 60 // 2,
            "ya_pujados": None,
            "en_vivo": False,
            "mirar_el_interruptor": False,
        }

        plan = plan_del_reset(**base)

        levantados = []

        # SI LA CESTA SALE VACIA POR DINERO O POR FICHAS, SE LEVANTA
        # Y SE DICE. En este orden: primero el tope, que es el que
        # manda con la caja a cero.
        presupuesto = safe_int(lectura.get("presupuesto"))

        if not plan.get("bids") and candidatos:

            caja = safe_int(lectura.get("caja_libre"))

            caja_que_no_topa = int(
                presupuesto / CAIDA_QUE_HAY_QUE_AGUANTAR
            ) + 1

            if caja < caja_que_no_topa:
                base["caja_libre"] = caja_que_no_topa

                levantados.append(
                    {
                        "candado": TOPE_DE_LA_VENTANA,
                        "reason": (
                            f"Con {_euros(caja)} EUR de caja libre "
                            f"el tope de la ventana es "
                            f"{_euros(int(caja / CAIDA_QUE_HAY_QUE_AGUANTAR))}"
                            f" EUR (caja / "
                            f"{CAIDA_QUE_HAY_QUE_AGUANTAR:.0%})."
                        ),
                    }
                )

                plan = plan_del_reset(**base)

        if not plan.get("bids") and candidatos:

            fichas = safe_int(lectura.get("fichas_libres"))

            if fichas < len(candidatos):
                base["fichas_libres"] = len(candidatos)

                levantados.append(
                    {
                        "candado": FICHAS_LIBRES,
                        "reason": (
                            f"Quedan {fichas} ficha(s) libre(s) en "
                            f"la plantilla."
                        ),
                    }
                )

                plan = plan_del_reset(**base)

        todos = candados + levantados

        filas = []

        for puja in (plan.get("bids") or []):

            precio = safe_int(puja.get("market_price"))
            importe = safe_int(puja.get("bid"))

            filas.append(
                {
                    "id": safe_int(puja.get("id")),
                    "name": puja.get("name"),
                    "price": precio,
                    "bid": importe,
                    "prima": importe - precio,
                    "prima_percent": (
                        round(100.0 * (importe - precio) / precio, 3)
                        if precio > 0
                        else None
                    ),
                    "win_odds": puja.get("win_odds"),
                    "expected_value": safe_int(
                        puja.get("expected_value")
                    ),
                    "intent": puja.get("intent"),
                    "route": puja.get("route"),
                    "por_que": puja.get("bid_reason"),
                    "candados": [c["candado"] for c in todos],
                }
            )

        filas.sort(key=lambda f: (-f["bid"], f["id"]))

        comprometido = sum(f["bid"] for f in filas)

        if filas:
            motivo = (
                f"Pujaria por {len(filas)} jugador(es), "
                f"{_euros(comprometido)} EUR en total, de mayor a "
                f"menor puja. "
                + (
                    "Candados que se lo impiden: "
                    + ", ".join(c["candado"] for c in todos)
                    + "."
                    if todos
                    else "Sin candados: esta vuelta pujaria de verdad."
                )
            )
        elif not candidatos:
            motivo = (
                "No hay candidatos en el tablero: sin nadie a quien "
                "mirar no hay sombra."
            )
        else:
            motivo = (
                f"Ni con los candados levantados pujaria: "
                f"{plan.get('blocked_by')} - {plan.get('reason')}"
            )

        return {
            "available": True,
            "observer_only": True,
            "bids": filas,
            "candados": todos,
            "committed": comprometido,
            "mirados": len(candidatos),
            "blocked_by": plan.get("blocked_by"),
            "reason": motivo,
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular la sombra de la puja: "
                f"{type(error).__name__}: {error}"
            ),
        }
