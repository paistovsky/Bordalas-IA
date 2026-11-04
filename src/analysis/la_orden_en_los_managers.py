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
       oferta de un manager que se llevaria a un jugador que la orden
       guarda (`los_de_la_orden`: `la_orden_del_gestor.conservados()` y
       `protegidos()`, las mismas funciones, de la orden viva y valida)
       no se elige: si el Safety Gate la autorizaba, su evaluacion sale
       BLOCK_LA_ORDEN_DEL_GESTOR (con la `guardia` y el estado que tenia)
       y la vuelta se la queda la siguiente oferta autorizada, si la hay.
       Las que se dejan, en `no_se_responden`, y la vuelta lo imprime
       («Bloqueada por la orden: ...», en el bloque SAFETY GATE V1.8). La
       sombra V1.9 elige con la misma funcion: ve lo mismo.
    2. LA ESCRITURA (`lo_guarda_la_orden`, desde
       `execute_competitive_live_action`). Defensa en profundidad: si la
       oferta llega igual al ejecutor, despues de revalidar y de EL_RELEVO
       y ANTES de crear el escritor, noop honesto:
       COMPETITIVE_BLOCKED_LA_ORDEN, `success` False, `write_performed`
       False, `guardia` LA_ORDEN_EN_LOS_MANAGERS y `de_la_orden` (los
       ids). Ni `accept_offer` ni `counter_offer`. Como EL_RELEVO.

    UNA OFERTA POR VARIOS (revision encendida del 04/11 por la noche).
    Un manager puede pedir varios jugadores en UNA oferta
    (`requestedPlayers`); la liquidez la parte en una entrada por jugador
    con el MISMO `offer_id` (`liquidity_manager.build_incoming_offer_candidates`),
    y aceptarla o contraofertarla los vende a todos. Asi que se frena
    tambien la del jugador libre que va en la misma oferta que uno de la
    orden: en la eleccion, por `offer_id` (aunque la evaluacion del de la
    orden no estuviera autorizada: la de Yamal sale
    BLOCK_PROTECTED_PLAYER); en el ejecutor, con TODOS los que esa oferta
    pide en la foto fresca (`market.offers`), esten o no en el tablero.

    La oferta no se rechaza ni se contesta: se deja pasar (el rival
    puede retirarla o caduca). La negociacion no avanza: su transicion
    solo se guarda con una escritura confirmada
    (`autopilot.confirm_negotiation_transitions`).

QUE NO HACE

    No toca el motor (`competitive_transaction_engine`), ni el Safety
    Gate (`evaluate_competitive_safety_gate`: NEVER_SELL y
    NEVER_AUTO_SELL siguen igual), ni EL_RELEVO (sigue primero en el
    ejecutor), ni la revalidacion fresca, ni el escritor, ni el motor
    viejo (sus ventas ya miran `conservados()`). No mira `no_rotar` ni
    `no_pujar`: Roberto esta en `conservar`, que es lo que manda aqui.
    Solo frena aceptar y contraofertar; el ensayo (`execute=False`) no
    escribe y sigue igual.

    Dos huecos de main que esto NO cierra (otras piezas):
    - Una oferta que pide a Yamal (NEVER_AUTO_SELL) y a un jugador libre:
      el Safety Gate frena la evaluacion de Yamal pero autoriza la del
      otro, y aceptarla vende a los dos. Encendido y con la orden viva,
      esto la frena (Yamal esta en `proteger`); apagado, o con la orden
      caducada, que no vale o que no se lee, es main.
    - EL_RELEVO mira solo al jugador de la oferta, no a los demas que
      pide la misma oferta.

    Tampoco toca a V10: su RAISE_COUNTER
    (`v10_full_autonomous_live`, `writer.counter_offer` sobre una oferta
    recibida, del tablero de `dynamic_counteroffer_repricing_v107`)
    sube una contraoferta que ya existe y no mira la orden. Encendido
    esto, Competitive V2 no abre contraofertas por los de la orden; una
    abierta a mano o por otra via la puede subir V10 (CANCEL_COUNTER solo
    salta con NEVER_SELL). Otra pieza.

EL INTERRUPTOR

    `BORDALAS_LA_ORDEN_EN_LOS_MANAGERS`. Nace APAGADO. Se lee en UN sitio
    (`activo`, al llamarse) y vale encendido con lo mismo que el paso 0,
    el tablon y el panel dan por encendido (`el_paso_0.ENCENDIDO`).
    Apagado no lee la orden ni la foto: la eleccion, la sombra, el
    ejecutor y lo que imprime la vuelta son main byte a byte. Con la
    orden apagada (`BORDALAS_LA_ORDEN_DEL_GESTOR`), caducada, que no
    vale, que no esta o que no se lee, tampoco cambia nada. Nunca lanza:
    si algo falla, lo de siempre. Al importarse no hace nada.

AL ENCENDERLO

    1. En UN commit, sobre el ultimo main (no sobre la rama vieja): la
       linea del interruptor a "1" en el YAML de produccion y
       `scripts/run_validation_gate.py --paso-0` en ESE arbol, al final.
       Sin el paso 0 en el arbol final, la guardia del paso 0 se pone
       roja, la validacion del ciclo falla y la vuelta no corre. Se
       anaden por nombre el YAML y `config/paso_0.json` (nunca `add -A`,
       nunca `data/`) y despues la verja normal. Un interruptor por
       commit.
       - El paso 0 en un checkout de git de verdad (no en una copia de
         `git archive`: `test_los_libros_v1` necesita `.git`) y con
         Python 3.13 o 3.11 (la huella de esta prueba es por version: con
         otra, `sin huella medida para Python` y el paso 0 no enciende).
       - `config/paso_0.json` NUNCA a mano: solo lo escribe `--paso-0`
         (su guardia no puede saber si la vuelta con todo encendido
         corrio de verdad). Ni se quita a mano el interruptor que no
         existe (sale de dos pruebas, `test_la_hucha_v1` y
         `test_la_prima_que_gana_v1`). Un conflicto en ese fichero se
         resuelve corriendo `--paso-0` otra vez en el arbol fusionado.
       - El paso 0 del 04/11 09:44 no tiene ni esto ni el interruptor de
         `el_protegido_no_gasta_la_vuelta`: el siguiente `--paso-0` los
         prueba juntos. Si la pieza de V10 que cuenta lo pujado entra
         antes, otro `--paso-0` con las dos piezas en el arbol.
         (Aqui no se escribe el nombre de otro interruptor: las pruebas
         de cada pieza miran que solo lo nombren sus ficheros.)
    2. Solo pesa con la orden del gestor encendida y viva (hoy lo esta,
       hasta el 30/11). Cuando la orden caduque, Competitive V2 vuelve a
       ser el de siempre: renovar la orden es renovar esto. Y la orden se
       edita con cuidado: una sola entrada mal escrita en `conservar` (o
       un `fichar` sin `puja`, o el JSON roto) la deja sin valer, y esta
       guarda se apaga sola (Roberto y Boye vuelven a poder venderse a un
       manager). Comprobarlo antes de encender y cada vez que se toque:
       `BORDALAS_LA_ORDEN_DEL_GESTOR=1 python -c "from
       src.analysis.la_orden_en_los_managers import los_de_la_orden as l;
       print(sorted(l()))"` (hoy, los diez: Roberto 35678, Boye 12494,
       Yamal 26271 y los demas de `conservar`). Vacio: la guarda no frena
       a nadie.
    3. Roberto lo guarda `conservar` (no `no_rotar`): mientras valga el
       «No lo vendas de momento» del dueno, que siga en `conservar`. Boye
       sigue frenado despues del lunes 09/11 por `conservar`: si para la
       operacion Raphinha hubiera que contestar a un manager por el, que
       salga tambien de `conservar`.
    4. Antes de encender, 0 contraofertas nuestras vivas por los de la
       orden (V10 las puede subir, ver QUE NO HACE): el log de la vuelta,
       «Contraofertas activas: 0» (hoy, 0).
    5. Encendido, con una oferta autorizada por Roberto primera y otra
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

# La de un jugador libre que va en la MISMA oferta que uno de la orden
# (una oferta puede pedir varios jugadores; aceptarla o contraofertarla
# los vende a todos).
MOTIVO_EN_EL_LOTE = (
    "LA_ORDEN_DEL_GESTOR: la misma oferta del manager pide tambien a un "
    "jugador que la orden del gestor manda conservar o proteger; aceptarla "
    "o contraofertarla lo venderia con ella."
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
    """El id de un jugador (o de una oferta) como entero; None si no es
    un id (ni un bool, ni un texto que no es un numero, ni cero o
    negativo)."""
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


def _los_pedidos(oferta) -> set:
    """Los jugadores que pide una oferta cruda de Biwenger: los de
    `requestedPlayers` (un id o `{"id"}`) y `player` (los mismos campos
    que `offer_analyzer.extract_player_ids`), uno a uno: el que no es un
    id se salta y los demas cuentan. Nunca lanza."""
    ids = set()
    try:
        if not isinstance(oferta, dict):
            return ids
        pedidos = oferta.get("requestedPlayers")
        for x in (list(pedidos) if isinstance(pedidos, list) else []) + [oferta.get("player")]:
            p = _pid(x.get("id") if isinstance(x, dict) else x)
            if p is not None:
                ids.add(p)
    except Exception:                               # noqa: BLE001
        pass
    return ids


def _los_de_la_oferta(foto, offer_id) -> set:
    """Todos los jugadores que pide la oferta `offer_id` en la foto
    fresca (`market.offers`, de donde sale el tablero de ofertas). Vacio
    si no esta o no se lee. Nunca lanza."""
    ids = set()
    try:
        oid = _pid(offer_id)
        mercado = foto.get("market") if isinstance(foto, dict) else None
        ofertas = mercado.get("offers") if isinstance(mercado, dict) else None
        if oid is None or not isinstance(ofertas, list):
            return ids
        for oferta in ofertas:
            if isinstance(oferta, dict) and _pid(oferta.get("id")) == oid:
                ids |= _los_pedidos(oferta)
    except Exception:                               # noqa: BLE001
        pass
    return ids


def _el_bloqueo(gate: dict, motivo: str) -> dict:
    """La evaluacion del Safety Gate, frenada por la orden (con la forma
    de sus bloqueos)."""
    return {
        "observer_only": True,
        "authorized": False,
        "status": BLOQUEO,
        "would_execute": False,
        "decision": gate.get("decision"),
        "reason": motivo,
        "guardia": GUARDIA,
        "status_sin_la_orden": gate.get("status"),
    }


def la_eleccion(evaluaciones):
    """
    Para `select_single_competitive_action`, con sus evaluaciones
    (`[{"player_id", "player_name", "offer_id", "decision", "gate"}]`).

    Una oferta por varios jugadores llega como una evaluacion por jugador
    con el MISMO `offer_id` (`liquidity_manager.build_incoming_offer_candidates`),
    y aceptarla o contraofertarla los vende a todos. Asi que se frena la
    autorizada de un jugador de la orden Y la autorizada de cualquier otro
    jugador de una oferta que pide a alguno de la orden (autorizada o no
    la evaluacion de ese: la de Yamal sale BLOCK_PROTECTED_PLAYER).

    None (nada cambia): apagado, sin ninguna autorizada, sin nadie en la
    orden o sin ninguna autorizada que frenar. Si no,
    `{"evaluations", "no_se_responden"}`: una lista nueva, en el mismo
    orden, con las frenadas cambiadas a su bloqueo (las demas, el mismo
    objeto), y las que no se responden (con `por_la_orden`: los de la
    orden que pide esa oferta). Nunca lanza: si algo falla, None.
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

        # Las ofertas que piden a alguno de la orden: {offer_id: [nombres]}.
        lotes = {}
        for e in evaluaciones:
            if not isinstance(e, dict):
                continue
            pid, oid = _pid(e.get("player_id")), _pid(e.get("offer_id"))
            if pid in de_la_orden and oid is not None:
                nombre = e.get("player_name") or pid
                if nombre not in lotes.setdefault(oid, []):
                    lotes[oid].append(nombre)

        nuevas, fuera = [], []
        for e in evaluaciones:
            if not _autorizada(e):
                nuevas.append(e)
                continue
            pid, oid = _pid(e.get("player_id")), _pid(e.get("offer_id"))
            suyo = pid in de_la_orden
            lote = lotes.get(oid) if oid is not None else None
            if not suyo and not lote:
                nuevas.append(e)
                continue
            nuevas.append({**e, "gate": _el_bloqueo(
                e["gate"], MOTIVO if suyo else MOTIVO_EN_EL_LOTE)})
            fuera.append({
                "player_id": pid,
                "player_name": e.get("player_name"),
                "offer_id": e.get("offer_id"),
                "rival_name": e.get("rival_name"),
                "decision": e.get("decision") or e["gate"].get("decision"),
                "motivo": BLOQUEO,
                "por_la_orden": list(lote or [e.get("player_name") or pid]),
            })
        if not fuera:
            return None
        return {"evaluations": nuevas, "no_se_responden": fuera}
    except Exception:                               # noqa: BLE001
        return None


def lo_guarda_la_orden(*player_ids, foto=None, offer_id=None) -> frozenset:
    """
    Para el ejecutor, justo antes de escribir: los de la orden viva que
    se irian con la oferta. Mira `player_ids` (el de la foto fresca y el
    de la oferta elegida) y, con `foto` y `offer_id`, TODOS los que esa
    oferta pide en la foto fresca (una oferta puede pedir varios). Vacio
    (falso): nada que guardar. Apagado, vacio sin leer la orden ni la
    foto. Nunca lanza: si algo falla, vacio (lo de siempre).
    """
    try:
        if not activo():
            return frozenset()
        ids = {p for p in (_pid(x) for x in player_ids) if p is not None}
        ids |= _los_de_la_oferta(foto, offer_id)
        if not ids:
            return frozenset()
        return frozenset(ids & los_de_la_orden())
    except Exception:                               # noqa: BLE001
        return frozenset()
