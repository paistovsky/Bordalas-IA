"""
Que la vuelta se apunte entera: las que pierden, y lo que costo.

QUE PASA HOY (22/09/2026)

    `append_log` guarda LA GANADORA y nada mas: `decision_action`,
    `decision_priority`, `decision_reason`. Las candidatas que
    perdieron no se apuntan en ninguna parte.

    Consecuencia medida: para contestar "¿cuantas veces la puja
    perdio la escritura?" hubo que RECONSTRUIR nueve vueltas
    volviendo a pasar `build_global_decision` por fotos viejas —86
    segundos cada una, y con el codigo de hoy sobre datos de
    entonces, que es lo que doctrina 53 llama medir con el plazo
    equivocado—. Habrian sido nueve lineas de un fichero.

    Y `peticiones.py` cuenta cada llamada por endpoint y `resumen`
    dice de si mismo "el recuento del ciclo, PARA PUBLICARLO" —
    pero solo se imprime. No queda en ningun sitio que se pueda
    leer despues, asi que el unico aviso antes del proximo 429 es
    que alguien estuviera mirando la consola en ese momento.

QUE APUNTA ESTO

    Dos cosas, las dos en la MISMA linea del log que ya existe,
    porque la vuelta es una y su registro tambien:

        `decision_candidates`   las que perdieron, con su
                                prioridad, si eran ejecutables, si
                                escribian, y su motivo.
        `requests`              lo que costo la vuelta en
                                peticiones, por endpoint.

    No se crea ningun libro nuevo (doctrina 84): el sitio donde se
    apunta lo que paso en una vuelta ya existe.

LO QUE OCUPA, MEDIDO

    Linea de hoy          5.088 B   (n=50, mediana = media)
    Cuatro perdedoras     1.276 B   con el motivo a 200 caracteres
    Vueltas por dia          35,1   (n=281 en 8 dias, bitacora)

        el log de hoy        5,1 MB al mes
        con las perdedoras   6,4 MB al mes   (+1,3)

    Y NO CRECE SIN FRENO: `prune_github_state` lo poda a 2.000
    lineas, que a 35 vueltas al dia son 57 dias de historia y
    12,1 MB estables. El repositorio ya versiona
    `scout_accuracy_ledger.json` (31 MB) y `divergence_ledger.json`
    (5,4 MB). Doce megas es menos que uno solo de los que ya hay.

EL MOTIVO SE RECORTA, Y SE DICE

    Los motivos de este proyecto son parrafos. Guardarlos enteros
    multiplicaria por tres la linea sin añadir nada que no se
    pueda mirar en el codigo. Se guardan los primeros
    `MOTIVO_MAXIMO` caracteres y se marca `truncated` cuando se ha
    cortado: un texto cortado sin avisar es un texto que se lee
    como si estuviera entero.

EL INTERRUPTOR

    `BORDALAS_LA_VUELTA_SE_APUNTA=1`. APAGADO de fabrica: sin el,
    la linea del log es exactamente la de hoy, byte a byte.

NO LEE EL MUNDO

    Ni disco, ni red, ni reloj: las candidatas y el recuento
    entran por la puerta. Solo mira el entorno, que es lo que ES
    el interruptor. Forma fija. Nunca lanza.
"""

from __future__ import annotations


ENV = "BORDALAS_LA_VUELTA_SE_APUNTA"


# Cuanto motivo se guarda de cada candidata.
MOTIVO_MAXIMO = 200


# Las acciones que consumen la escritura de la vuelta. Es la
# pregunta que se querra contestar leyendo esto, asi que se apunta
# al lado y no se deduce despues.
ESCRIBEN = frozenset(
    {
        "SAVE_LINEUP",
        "ACCEPT_CLUSTER_BEFORE_EXPIRY",
        "REROLL_COMPUTER_OFFER",
        "ACCEPT_RECOVERY_OFFER",
        "LIST_FOR_LIQUIDITY",
        "RENEW_MARKET_LISTING",
        "BUY_SPECULATION",
    }
)


def activa() -> bool:
    """Si la vuelta se apunta entera. Nunca lanza."""

    try:
        import os

        return str(
            os.environ.get(ENV, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def _motivo(texto) -> tuple:
    """(motivo recortado, si se ha recortado)."""

    entero = str(texto or "")

    if len(entero) <= MOTIVO_MAXIMO:
        return entero, False

    return entero[:MOTIVO_MAXIMO], True


def la_cola(candidatas, ganadora=None) -> list:
    """
    La cola de la vuelta, compacta y en orden.

    `ganadora` se marca en vez de quitarse: una cola sin su
    ganadora no se puede leer sola, y quien la lea tendria que
    cruzarla con otro campo para saber quien mando.

    Forma fija. Nunca lanza. Devuelve `[]` si el interruptor esta
    quitado: apagado, la linea del log no cambia.
    """

    try:
        if not activa():
            return []

        filas = [
            c for c in (candidatas or []) if isinstance(c, dict)
        ]

        if not filas:
            return []

        elegida = (ganadora or {}) if isinstance(ganadora, dict) else {}

        salida = []

        for puesto, c in enumerate(filas):

            accion = c.get("action")

            motivo, cortado = _motivo(c.get("reason"))

            fila = {
                "order": puesto,
                "action": accion,
                "type": c.get("type"),
                "priority": c.get("priority"),
                "executable": bool(c.get("executable")),
                "writes": accion in ESCRIBEN,
                "won": bool(
                    elegida
                    and accion == elegida.get("action")
                    and c.get("priority") == elegida.get("priority")
                ),
                "reason": motivo,
            }

            if cortado:
                fila["reason_truncated"] = True

            salida.append(fila)

        return salida

    except Exception:                               # noqa: BLE001
        # Un registro que revienta no puede tumbar la vuelta que
        # estaba registrando.
        return []


def lo_que_costo(recuento) -> dict:
    """
    Las peticiones de la vuelta, compactas.

    `recuento` es lo que devuelve `peticiones.resumen()`. Se
    recibe: este modulo no llama a nadie.

    Forma fija. Nunca lanza. `{}` con el interruptor quitado.
    """

    try:
        if not activa():
            return {}

        cuenta = recuento if isinstance(recuento, dict) else {}

        if not cuenta.get("available"):
            return {}

        return {
            "total": cuenta.get("total"),
            "unique_endpoints": cuenta.get("unique_endpoints"),
            "repeated": cuenta.get("repeated"),
            "repeated_percent": cuenta.get("repeated_percent"),
            "rate_limited": cuenta.get("rate_limited"),
            "waited_seconds": cuenta.get("waited_seconds"),

            # Los doce mas llamados. El resto es cola larga y no
            # cambia ninguna decision.
            "by_endpoint": dict(
                list((cuenta.get("by_endpoint") or {}).items())[:12]
            ),
        }

    except Exception:                               # noqa: BLE001
        return {}


def cuanto_ocupa(cola, coste) -> int:
    """
    Los bytes que esto añade a la linea. Para poder vigilarlo sin
    estimarlo (doctrina 90: un numero que recibes tambien necesita
    su medicion).
    """

    try:
        import json

        return len(
            json.dumps(
                {"decision_candidates": cola, "requests": coste},
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
        )

    except Exception:                               # noqa: BLE001
        return 0
