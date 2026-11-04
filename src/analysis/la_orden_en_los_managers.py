"""
LA ORDEN EN LOS MANAGERS (04/11/2026)

EL HUECO (revision encendida del 04/11 por la manana)

    Competitive V2 es el motor que contesta las ofertas de OTROS
    MANAGERS (no las del Computer):

      1. `competitive_transaction_engine.evaluate_sale_to_rival` decide
         por oferta NEVER_SELL, ACCEPT_NOW, ACCEPT_SACRIFICE_LINEUP o
         COUNTER_OFFER;
      2. el Safety Gate (`competitive_safety_gate`) solo frena
         NEVER_SELL y NEVER_AUTO_SELL, y la eleccion
         (`select_single_competitive_action`) se queda la PRIMERA
         autorizada;
      3. el ejecutor (`competitive_live_executor.execute_competitive_live_action`)
         revalida con una foto fresca y escribe: `counter_offer` o
         `accept_offer`, en la vuelta en que el motor viejo no ha
         escrito.

    Nadie mira la orden del gestor. La unica guarda parecida es
    EL_RELEVO (el que entra por un cambio vivo de la mejora). Y el
    escritor tampoco: `accept_offer` y `counter_offer` no tienen la
    guarda de `list_player_for_sale` (PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR).
    Asi que la oferta de un manager por Roberto Fernandez (`conservar` y
    `no_rotar`; el DUENO lo dijo el 02/11: «No lo vendas de momento») o
    por Boye (`proteger`) se podia ACEPTAR, o CONTRAOFERTAR (una
    contraoferta que el rival acepta tambien es vender). El 04/11 hay 0
    ofertas de managers: no ha pasado todavia.

QUE HACE, ENCENDIDO

    1. LA ELECCION (`la_eleccion`, desde
       `competitive_safety_gate.select_single_competitive_action`). La
       oferta de un manager por un jugador que la orden guarda
       (`los_de_la_orden`: `la_orden_del_gestor.conservados()` y
       `protegidos()`, las mismas funciones, de la orden viva y valida)
       no se elige: si el Safety Gate la autorizaba, su evaluacion sale
       BLOCK_LA_ORDEN_DEL_GESTOR (con la `guardia` y el estado que tenia)
       y la vuelta se la queda la siguiente oferta autorizada, si la hay.
       Las que se dejan, en `no_se_responden`. La sombra V1.9 elige con
       la misma funcion: ve lo mismo.
    2. LA ESCRITURA (`lo_guarda_la_orden`, desde
       `execute_competitive_live_action`). Defensa en profundidad: si la
       oferta llega igual al ejecutor, despues de revalidar y de EL_RELEVO
       y ANTES de crear el escritor, noop honesto:
       COMPETITIVE_BLOCKED_LA_ORDEN, `success` False, `write_performed`
       False, `guardia` LA_ORDEN_EN_LOS_MANAGERS. Ni `accept_offer` ni
       `counter_offer`. Como EL_RELEVO.

    La oferta no se rechaza ni se contesta: se deja pasar (el rival
    puede retirarla o caduca). La negociacion no avanza: su transicion
    solo se guarda con una escritura confirmada
    (`autopilot.confirm_negotiation_transitions`).

QUE NO HACE

    No toca el motor (`competitive_transaction_engine`), ni el Safety
    Gate (`evaluate_competitive_safety_gate`: NEVER_SELL y
    NEVER_AUTO_SELL siguen igual, y Yamal no se vende nunca, con esto o
    sin esto), ni EL_RELEVO (sigue primero en el ejecutor), ni la
    revalidacion fresca, ni el escritor, ni el motor viejo (sus ventas
    ya miran `conservados()`). No mira `no_rotar` ni `no_pujar`:
    Roberto esta en `conservar`, que es lo que manda aqui. Solo frena
    aceptar y contraofertar; el ensayo (`execute=False`) no escribe y
    sigue igual.

    Tampoco toca a V10: su RAISE_COUNTER
    (`v10_full_autonomous_live`, `writer.counter_offer` sobre una oferta
    recibida, del tablero de `dynamic_counteroffer_repricing_v107`)
    sube una contraoferta que ya existe y no mira la orden. Encendido
    esto, Competitive V2 no abre contraofertas por los de la orden; una
    abierta a mano o por otra via la puede subir V10. Otra pieza.

EL INTERRUPTOR

    `BORDALAS_LA_ORDEN_EN_LOS_MANAGERS`. Nace APAGADO. Se lee en UN sitio
    (`activo`, al llamarse) y vale encendido con lo mismo que el paso 0,
    el tablon y el panel dan por encendido (`el_paso_0.ENCENDIDO`).
    Apagado no lee la orden: la eleccion, la sombra y el ejecutor son
    main byte a byte. Con la orden apagada
    (`BORDALAS_LA_ORDEN_DEL_GESTOR`), caducada, que no vale, que no
    esta o que no se lee, tampoco cambia nada. Nunca lanza: si algo
    falla, lo de siempre. Al importarse no hace nada.

AL ENCENDERLO

    1. En UN commit, sobre el ultimo main (no sobre la rama vieja): la
       linea del interruptor a "1" en el YAML de produccion y
       `scripts/run_validation_gate.py --paso-0` en ESE arbol, al final.
       Sin el paso 0 en el arbol final, la guardia del paso 0 se pone
       roja, la validacion del ciclo falla y la vuelta no corre. Se
       anaden por nombre el YAML y `config/paso_0.json` (nunca `add -A`,
       nunca `data/`) y despues la verja normal. Un interruptor por
       commit.
    2. Solo pesa con la orden del gestor encendida y viva (hoy lo esta,
       hasta el 30/11). Cuando la orden caduque, Competitive V2 vuelve a
       ser el de siempre: renovar la orden es renovar esto.
    3. Encendido, con una oferta autorizada por Roberto primera y otra
       por un jugador libre detras, la vuelta contesta a la segunda (lo
       que se quiere: «la siguiente se queda la vuelta»). Apuntarlo en
       la bitacora al encender.
"""

from __future__ import annotations

import os


ENV = "BORDALAS_LA_ORDEN_EN_LOS_MANAGERS"

# Lo que vale como encendido: lo mismo que `el_paso_0.ENCENDIDO` (el paso
# 0, el tablon, el panel y el ensayo). Escrito aqui para no importar nada
# al leerlo; la prueba mira que sean iguales.
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})

GUARDIA = "LA_ORDEN_EN_LOS_MANAGERS"

# En la eleccion (el estado de la evaluacion del Safety Gate) y en el
# ejecutor (el estado de la vuelta).
BLOQUEO = "BLOCK_LA_ORDEN_DEL_GESTOR"
ESTADO = "COMPETITIVE_BLOCKED_LA_ORDEN"

MOTIVO = (
    "LA_ORDEN_DEL_GESTOR: el jugador esta en `conservar` o `proteger` de la "
    "orden del gestor; ni se acepta ni se contraoferta la oferta de un "
    "manager por el (una contraoferta aceptada por el rival tambien es "
    "vender)."
)


def activo() -> bool:
    """`BORDALAS_LA_ORDEN_EN_LOS_MANAGERS`, leido al llamarse. Encendido
    con lo que el paso 0 da por encendido (`ENCENDIDO`); cualquier otra
    cosa, apagado. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in ENCENDIDO
    except Exception:                               # noqa: BLE001
        return False


def _pid(valor):
    """El id de un jugador como entero; None si no es un id (ni un bool,
    ni un texto que no es un numero, ni cero o negativo)."""
    try:
        if valor is None or isinstance(valor, bool):
            return None
        pid = int(valor)
        return pid if pid > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def los_de_la_orden() -> frozenset:
    """
    Los que Competitive V2 no vende: `la_orden_del_gestor.conservados()`
    y `protegidos()` (las MISMAS funciones, sin argumentos: la orden de
    `config/`, a la hora de ahora). Vacio con la orden apagada, caducada,
    que no vale o que no esta. Nunca lanza: si no se puede leer, vacio
    (lo de siempre).
    """
    try:
        from src.actions.la_orden_del_gestor import conservados, protegidos

        ids = set(conservados() or ()) | set(protegidos() or ())
        return frozenset(p for p in (_pid(x) for x in ids) if p is not None)
    except Exception:                               # noqa: BLE001
        return frozenset()


def _el_bloqueo(gate: dict) -> dict:
    """La evaluacion del Safety Gate, frenada por la orden (con la forma
    de sus bloqueos)."""
    return {
        "observer_only": True,
        "authorized": False,
        "status": BLOQUEO,
        "would_execute": False,
        "decision": gate.get("decision"),
        "reason": MOTIVO,
        "guardia": GUARDIA,
        "status_sin_la_orden": gate.get("status"),
    }


def la_eleccion(evaluaciones):
    """
    Para `select_single_competitive_action`, con sus evaluaciones
    (`[{"player_id", "player_name", "offer_id", "decision", "gate"}]`).

    None (nada cambia): apagado, sin ninguna autorizada, sin nadie en la
    orden o sin ninguna autorizada de la orden. Si no,
    `{"evaluations", "no_se_responden"}`: una lista nueva, en el mismo
    orden, con la autorizada de un jugador de la orden cambiada a su
    bloqueo (las demas, el mismo objeto), y las que no se responden.
    Nunca lanza: si algo falla, None.
    """
    try:
        if not activo():
            return None
        if not isinstance(evaluaciones, list):
            return None

        def _autorizada(e):
            return (isinstance(e, dict) and isinstance(e.get("gate"), dict)
                    and bool(e["gate"].get("authorized", False)))

        if not any(_autorizada(e) for e in evaluaciones):
            return None
        de_la_orden = los_de_la_orden()
        if not de_la_orden:
            return None
        nuevas, fuera = [], []
        for e in evaluaciones:
            if _autorizada(e) and _pid(e.get("player_id")) in de_la_orden:
                nuevas.append({**e, "gate": _el_bloqueo(e["gate"])})
                fuera.append({
                    "player_id": _pid(e.get("player_id")),
                    "player_name": e.get("player_name"),
                    "offer_id": e.get("offer_id"),
                    "rival_name": e.get("rival_name"),
                    "decision": e.get("decision") or e["gate"].get("decision"),
                    "motivo": BLOQUEO,
                })
            else:
                nuevas.append(e)
        if not fuera:
            return None
        return {"evaluations": nuevas, "no_se_responden": fuera}
    except Exception:                               # noqa: BLE001
        return None


def lo_guarda_la_orden(*player_ids) -> bool:
    """
    Para el ejecutor, justo antes de escribir: True solo encendido y con
    alguno de `player_ids` (el de la foto fresca y el de la oferta
    elegida) en la orden viva. Apagado, False sin leer la orden. Nunca
    lanza: si algo falla, False (lo de siempre).
    """
    try:
        if not activo():
            return False
        ids = {p for p in (_pid(x) for x in player_ids) if p is not None}
        if not ids:
            return False
        return bool(ids & los_de_la_orden())
    except Exception:                               # noqa: BLE001
        return False
