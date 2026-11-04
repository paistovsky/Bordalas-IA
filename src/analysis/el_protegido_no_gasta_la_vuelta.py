"""
EL PROTEGIDO NO GASTA LA VUELTA (04/11/2026)

LO QUE PASO (supervision del 04/11 08:22)

    Boye (12494) esta en `proteger` de la orden del gestor hasta el lun
    09/11. Su publicacion caducaba el 04/11 ~09:10 y la de Chust (1760),
    ~10:10. El autopilot viejo propone UNA renovacion por vuelta, la mas
    urgente (`decision_orchestrator`, MARKET LISTING LIFECYCLE), y la
    primera de la cola ordenada por caducidad era Boye. El ejecutor la
    mandaba, la guarda del escritor (`write_client.list_player_for_sale`)
    la frenaba ANTES de enviar nada (`blocked:
    PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR`) y el ejecutor:

      1. tiraba el `blocked` y decia «Biwenger no confirmo la
         renovacion», que es falso: no se envio nada;
      2. la contaba como fallo: backoff de 30 min, 1 h, 2 h...;
      3. devolvia `write_performed: True` sin haber escrito, y la vuelta
         perdia su UNICA escritura: BUY V10, la contraoferta y la salida
         de V10 no corrian, y el competitivo decia
         BLOCKED_LEGACY_ALREADY_WROTE (07:15, 08:07 y 10:07).

    Mientras, Chust no se renovaba nunca: el plan solo propone la primera
    renovacion y, con Boye en backoff (09:07), ninguna. Su publicacion
    caduco a las 10:10.

QUE HACE, ENCENDIDO

    1. EL PLAN (`los_del_plan` + `fuera_los_protegidos`, desde
       `decision_orchestrator.build_global_decision_uncached`). El
       orquestador no propone renovar la publicacion ni cobrar una
       oferta (vender) de un jugador que la orden protege: los de
       `la_orden_del_gestor.protegidos()` (`proteger` y `fichar` de la
       orden viva y valida), que es EXACTAMENTE la puerta que cierra
       `list_player_for_sale`: la misma funcion, no una copia. La
       siguiente renovacion (o la siguiente oferta aprobada, o la
       siguiente accion) se queda la vuelta. A quien se deja fuera queda
       en `state.no_se_renuevan` y `state.no_se_cobran`.
       (La publicacion por liquidez ya salta a los protegidos desde el
       12/10, siempre: `los_que_se_pueden_publicar`.)
    2. LA ESCRITURA FRENADA (`la_que_frena_el_escritor`, desde la
       renovacion de `autopilot_executor.execute_autopilot_decision`).
       Defensa en profundidad: si la guarda frena igual (sin enviar), la
       vuelta lo dice como es: status BLOCKED, el `blocked` en el
       resultado y en el motivo («BLOQUEADA_POR_LA_ORDEN: ...»),
       `write_performed: False` (no se ha escrito nada: el competitivo y
       V10 conservan su turno) y, por eso mismo, sin backoff
       (`register_action_outcome` solo apunta escrituras reales). Lo
       mismo que hace la publicacion de liquidez desde el 12/10
       (`autopilot_executor.resultado_de_publicar`).

QUE NO HACE

    No toca la guarda del escritor: sigue siendo la red de seguridad, y
    `proteger` sigue siendo «ni se vende, ni se publica, ni se renueva».
    No toca el tablero de publicaciones (el panel sigue viendo las dos
    caducar), ni las prioridades, ni el orden del resto de la cola, ni
    `conservar` (eso lo frena el ejecutor al cobrar, como siempre), ni la
    aceptacion por caducidad de un grupo de ofertas (la elige el
    ejecutor con la foto fresca, sin los de `conservar`), ni la
    renovacion de la ventana ni el escaparate, que no gastan la
    escritura de la vuelta. Un FAILED con la peticion enviada sigue
    siendo escritura y sigue castigandose; el ensayo (`sent: False` sin
    `blocked`) tambien sigue igual.

EL INTERRUPTOR

    `BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA`. Nace APAGADO. Se lee en
    UN sitio (`activo`, al llamarse) y vale encendido con lo mismo que el
    paso 0, el tablon y el panel dan por encendido
    (`el_paso_0.ENCENDIDO`). Apagado, el plan, el resultado del ejecutor,
    el backoff y lo que ve V10 son main byte a byte. Nunca lanza: si algo
    falla, lo de siempre (y el escritor sigue frenando). Al importarse no
    hace nada.
"""

from __future__ import annotations

import os


ENV = "BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA"

# Lo que vale como encendido: lo mismo que `el_paso_0.ENCENDIDO` (el paso
# 0, el tablon, el panel y el ensayo). Escrito aqui para no importar nada
# al leerlo; la prueba mira que sean iguales.
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})

# El motivo con el que frena la guarda del escritor
# (`write_client.list_player_for_sale`).
MOTIVO = "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"

GUARDIA = "EL_PROTEGIDO_NO_GASTA_LA_VUELTA"
PREFIJO = "BLOQUEADA_POR_LA_ORDEN"
PREFIJO_OTRA = "BLOQUEADA_POR_EL_ESCRITOR"


def activo() -> bool:
    """`BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA`, leido al llamarse.
    Encendido con lo que el paso 0 da por encendido (`ENCENDIDO`);
    cualquier otra cosa, apagado. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in ENCENDIDO
    except Exception:                               # noqa: BLE001
        return False


def los_protegidos() -> frozenset:
    """
    Los que la guarda del escritor no deja publicar: la MISMA funcion que
    llama `write_client.list_player_for_sale`
    (`la_orden_del_gestor.protegidos()`, sin argumentos: la orden de
    `config/`, a la hora de ahora). Vacio con la orden apagada, caducada o
    que no vale. Nunca lanza: si no se puede leer, vacio (lo de siempre;
    el escritor sigue frenando).
    """
    try:
        from src.actions.la_orden_del_gestor import protegidos

        return frozenset(int(pid) for pid in (protegidos() or ()) if pid is not None)
    except Exception:                               # noqa: BLE001
        return frozenset()


def los_del_plan() -> frozenset | None:
    """Para el orquestador: None apagado (nada cambia); encendido, los
    protegidos que no entran en el plan. Nunca lanza."""
    try:
        if not activo():
            return None
        return los_protegidos()
    except Exception:                               # noqa: BLE001
        return None


def _pid(item):
    try:
        if not isinstance(item, dict):
            return None
        valor = item.get("player_id")
        if valor is None or isinstance(valor, bool):
            return None
        return int(valor)
    except (TypeError, ValueError):
        return None


def fuera_los_protegidos(items, protegidos) -> dict:
    """
    `{"quedan", "fuera"}`: `items` (renovaciones u ofertas a cobrar, con
    `player_id`) sin los de `protegidos`, en el mismo orden; los quitados,
    con su nombre y el motivo de la guarda. Sin protegidos, todo queda.
    Pura. Nunca lanza: si algo falla, todo queda (lo de siempre).
    """
    lista = list(items or []) if isinstance(items, (list, tuple)) else []
    try:
        vetados = {int(p) for p in (protegidos or ())}
        if not vetados:
            return {"quedan": lista, "fuera": []}
        quedan, fuera = [], []
        for item in lista:
            pid = _pid(item)
            if pid is not None and pid in vetados:
                fuera.append({
                    "player_id": pid,
                    "name": item.get("name") or item.get("player_name"),
                    "motivo": MOTIVO,
                })
            else:
                quedan.append(item)
        return {"quedan": quedan, "fuera": fuera}
    except Exception:                               # noqa: BLE001
        return {"quedan": lista, "fuera": []}


def la_que_frena_el_escritor(salida, respuesta):
    """
    Para el ejecutor, con lo que iba a devolver (`salida`) y lo que
    contesto el escritor (`respuesta`). Si el escritor freno sin enviar
    (`blocked` y no `sent`) y esto esta encendido: la salida honesta
    (BLOCKED, `write_performed` False, el `blocked` y el motivo). Si no,
    `salida` tal cual (el mismo objeto). Nunca lanza.
    """
    try:
        if not isinstance(salida, dict) or not isinstance(respuesta, dict):
            return salida
        frenada = respuesta.get("blocked")
        if respuesta.get("sent") or not frenada:
            return salida
        if not activo():
            return salida
        listing = salida.get("listing") if isinstance(salida.get("listing"), dict) else {}
        nombre = listing.get("name") or "el jugador"
        pid = salida.get("player_id")
        prefijo = PREFIJO if frenada == MOTIVO else PREFIJO_OTRA
        quien = "la orden del gestor lo protege y " if frenada == MOTIVO else ""
        return {
            **salida,
            "status": "BLOCKED",
            "reason": (
                f"{prefijo}: renovar la publicacion de {nombre} ({pid}): "
                f"{quien}el escritor la ha frenado ({frenada}) sin enviar nada "
                "a Biwenger. No gasta la escritura de la vuelta ni entra en "
                "el backoff."
            ),
            "write_performed": False,
            "success": False,
            "blocked": frenada,
            "guardia": GUARDIA,
            "http_status": None,
            "response": None,
        }
    except Exception:                               # noqa: BLE001
        return salida
