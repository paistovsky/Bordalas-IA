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
    renovacion de la ventana ni el escaparate, que no gastan la
    escritura de la vuelta. Un FAILED con la peticion enviada sigue
    siendo escritura y sigue castigandose; el ensayo (`sent: False` sin
    `blocked`) tambien sigue igual.

    Tampoco toca la aceptacion por caducidad de un grupo de ofertas
    (ACCEPT_CLUSTER_BEFORE_EXPIRY): el plan propone el grupo, no un
    jugador, y la oferta la elige el ejecutor con la foto fresca
    (`select_emergency_accept_offer`), que solo salta NEVER_SELL y
    NEVER_AUTO_SELL. Si elige a uno de `conservar` (o un protegido), el
    ejecutor rechaza la accion entera DESPUES de elegir
    (INVALID_SELECTED_OFFER: sin escritura, sin backoff, V10 conserva su
    turno) y las demas ofertas del grupo no se prueban. Igual encendido
    que apagado; solo pesa en una crisis de solvencia. Lo mismo que una
    oferta de `conservar` (no protegida) primera en las cobrables:
    BLOCKED_PROTECTED_PLAYER con el motivo «NEVER_AUTO_SELL». Para otra
    pieza: que el selector salte a `conservados()` antes de elegir.

    Ni lo que ya pasaba en main y esto solo deja correr en unas vueltas
    mas (las que el backoff de Boye se comia): la puja BUY de V10 no
    resta las pujas vivas de la caja ni descuenta que la oferta de un
    `conservar` no se cobrara; el competitivo V2 no mira la orden antes
    de aceptar o contraofertar; la salida de V10
    (`live_sale_executor`) da `sent: True` aunque el escritor la frene.
    Cada una, su pieza.

EL INTERRUPTOR

    `BORDALAS_EL_PROTEGIDO_NO_GASTA_LA_VUELTA`. Nace APAGADO. Se lee en
    UN sitio (`activo`, al llamarse) y vale encendido con lo mismo que el
    paso 0, el tablon y el panel dan por encendido
    (`el_paso_0.ENCENDIDO`). Apagado, el plan, el resultado del ejecutor,
    el backoff y lo que ve V10 son main byte a byte. Nunca lanza: si algo
    falla, lo de siempre (y el escritor sigue frenando). Al importarse no
    hace nada.

AL ENCENDERLO

    1. En UN commit, sobre el ultimo main (no sobre la rama vieja): la
       linea del interruptor a "1" en el YAML de produccion y
       `scripts/run_validation_gate.py --paso-0` en ESE arbol, al final.
       Sin el paso 0 en el arbol final, la guardia del paso 0 se pone
       roja, la validacion del ciclo falla y la vuelta no corre. Se
       anaden por nombre el YAML y `config/paso_0.json` (nunca
       `add -A`, nunca `data/`) y despues la verja normal.
    2. No armar en el mismo commit los literales del interruptor que no
       existe de `test_la_hucha_v1` y `test_la_prima_que_gana_v1`: si se
       arman, el paso 0 va despues, en ese mismo arbol (si no, el
       registro nombra un interruptor que no existe y la verja para).
       Un interruptor por commit.
    3. Los diagnosticos de la maquina del gestor
       (`scripts/que_ofertas_cobro.py`,
       `scripts/mirar_accept_before_expiry.py`) leen el entorno de
       quien los corre: para ver el plan de produccion hay que exportar
       este interruptor y el de la orden del gestor (los dos a 1). Sin
       ellos ensenan el plan de main (la renovacion de Boye).
    4. Encendido, con la oferta aprobada de un protegido primera, se
       cobra la siguiente aprobada (lo que se quiere: «la siguiente se
       queda la vuelta»). Apuntarlo en la bitacora al encender.
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


def _como_lista(items):
    """`items` como lista nueva (None, vacia): una lista, una tupla, un
    generador, la vista de un dict... None si no es una coleccion de
    cosas (un texto, bytes, un dict, algo que no se recorre)."""
    if items is None:
        return []
    if isinstance(items, (str, bytes, bytearray, dict)):
        return None
    try:
        return list(items)
    except Exception:                               # noqa: BLE001
        return None


def fuera_los_protegidos(items, protegidos) -> dict:
    """
    `{"quedan", "fuera"}`: `items` (renovaciones u ofertas a cobrar, con
    `player_id`; cualquier coleccion que se recorra) sin los de
    `protegidos`, en el mismo orden y como lista; los quitados, con su
    nombre y el motivo de la guarda. Sin protegidos, todo queda. Pura.
    Nunca lanza: si algo falla, o `items` no es una coleccion de cosas,
    todo queda (lo de siempre): nunca se pierde una renovacion ni una
    oferta por no entenderla.
    """
    lista = None
    try:
        lista = _como_lista(items)
        if lista is None:
            return {"quedan": items, "fuera": []}
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
        return {"quedan": items if lista is None else lista, "fuera": []}


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
