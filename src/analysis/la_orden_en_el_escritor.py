"""
LA ORDEN EN EL ESCRITOR (05/11/2026)

EL HUECO (mapa del 05/11 por la manana)

    Todas las aceptaciones y contraofertas del proyecto salen por dos
    metodos del escritor: `write_client.accept_offer` y `counter_offer`. No
    hay otra escritura HTTP que acepte o conteste una oferta. Y ninguno de
    los dos mira la orden del gestor: reciben solo el `offer_id`, asi que
    no saben a quien venden. La guarda de `list_player_for_sale`
    (PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR) no tenia pareja aqui.

    Lo que queda abierto en main:

    - Competitive V2 (`competitive_live_executor`) contesta las ofertas de
      OTROS MANAGERS con COUNTER u ACCEPT sin mirar la orden (lo cierra en
      la eleccion la pieza de los managers, que nace apagada).
    - V10 RAISE_COUNTER (`v10_full_autonomous_live`) sube una contraoferta
      viva sin mirar la orden, y nadie la RETIRA: el tablero
      (`dynamic_counteroffer_repricing_v107.evaluate_counteroffer`) solo
      da CANCEL_COUNTER con NEVER_SELL, y los de `conservar` no lo son. Si
      el rival acepta nuestra contraoferta viva, el jugador se va.
    - El motor viejo parte una oferta por varios jugadores en una fila por
      jugador con el MISMO `offer_id` (`liquidity_manager`), y su ejecutor
      (`autopilot_executor`) solo mira el jugador de la fila: aceptar la
      fila de Juan Iglesias vende tambien a Roberto si la misma oferta lo
      pide.
    - Cualquier llamador que venga despues.

QUE HACE, ENCENDIDO

    En `accept_offer` y `counter_offer`, solo con `execute=True` y ANTES
    del ensayo (`_en_ensayo`), `guardar` lee la orden y, si guarda a
    alguien, la oferta FRESCA de `/market` (UN GET por aceptacion o
    contraoferta: son un punado al dia frente a unas 1.500 peticiones).
    Mira TODOS los jugadores que la oferta pide (`requestedPlayers` y
    `player`, los mismos campos que `offer_analyzer.extract_player_ids`) y
    de quien viene (`from`; None es el Computer, como en
    `la_orden_del_gestor.leer_la_foto`):

        proteger y fichar (`la_orden_del_gestor.protegidos()`): ni se
            acepta ni se contraoferta, venga de quien venga
            (PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR, el mismo codigo que la
            guarda de publicar).
        conservar (`conservados()`): no se contraoferta nunca, y no se
            acepta la oferta de un MANAGER
            (CONSERVADO_POR_LA_ORDEN_DEL_GESTOR).
        la oferta del Computer por uno de `conservar`: SE ACEPTA. Es la
            venta de verdad: el cambio de la mejora del once (SALIDA), el
            `vender_si_ficha` de la orden, el cierre y la rotacion solo
            venden aceptando ofertas del Computer
            (ACEPTAR_OFERTA_DEL_COMPUTER).

    Frenada: no sale nada hacia Biwenger y el ensayo no la apunta. El
    escritor devuelve lo de siempre con `sent` False y `success` False, y
    ademas `status` BLOQUEADA_POR_LA_ORDEN, `reason`, `guardia`
    (LA_ORDEN_EN_EL_ESCRITOR), `blocked` (el codigo), `de_la_orden` (los de
    la orden que se irian), `pedidos` (todos los que pide la oferta) y
    `de_un_manager`. El motor viejo lo devuelve como su
    BLOCKED_PROTECTED_PLAYER y Competitive V2 como
    COMPETITIVE_BLOCKED_EL_ESCRITOR, los dos con `write_performed` False:
    no se envio nada, asi que la vuelta no la gasta ni el backoff la
    castiga. V10 ya era honesto (`write_used` es `success`: False). La
    orden (`la_orden_del_gestor.ejecutar`) ya da `enviada` False y `exito`
    False, y no se toca.

    Sin poder ver la oferta (el GET falla, no contesta en
    `TIEMPO_DEL_GET` segundos, no da 200, el mercado no se lee, la oferta
    no esta, o no pide a nadie que se sepa leer): la escritura sigue como
    siempre y lleva `guardia_sin_ver` con el motivo. Las guardias de cada
    llamador siguen ahi, y una venta justo antes del cierre no se pierde
    por un fallo de red.

    NUESTRA CONTRAOFERTA VIVA (revision encendida del 05/11). Frenar la
    subida no basta: la contraoferta vieja, mas barata, seguiria viva y el
    rival la podria aceptar (apagado, V10 la habria subido antes). Asi que
    el tablero de V10 (`evaluate_counteroffer`, por
    `retirar_la_contraoferta`) da CANCEL_COUNTER, lo primero de todo, a
    toda contraoferta NUESTRA viva que venda a uno de `proteger`, `fichar`
    o `conservar` (los de la fila, los de la contraoferta y los de la
    oferta del rival a la que contesta: una contraoferta es siempre para
    un manager). V10 ya ejecuta CANCEL_COUNTER antes que RAISE_COUNTER
    (`cancel_bid` sobre `counter_offer_id`, NUESTRA contraoferta), y con
    eso tampoco queda una subida frenada que le quite la salida
    (EXIT_LISTING) vuelta tras vuelta. Retirar no vende a nadie. Se lee la
    orden (sin red) una vez por contraoferta viva; hoy hay 0.

    Los viajes (`salida_executor.cobrar`): una aceptacion frenada se
    apunta en su libro con `blocked` y `reason`, y el fallo dice «Frenada
    por la orden», no «Biwenger contesto None».

    DE QUIEN VIENE (corrige la especificacion del 05/11). La especificacion
    decia «de un manager: `from` con id». Aqui cuenta como «no es el
    Computer» todo `from` que no sea None: un `from` raro (un dict sin id,
    un texto) nunca es una venta legitima, porque todos los que venden a
    un conservado leen las ofertas del Computer con `leer_la_foto`, que
    solo da por Computer `from` None. Asi que el raro se trata como el de
    un manager, que es el lado seguro.

QUE NO HACE

    No toca publicar (`list_player_for_sale`, que ya tiene su guarda), ni
    rechazar (`reject_offer`), ni retirar (`cancel_bid`: el CANCEL_COUNTER
    de V10 es lo seguro, y aqui solo se le dan mas filas), ni pujar, ni el
    once, ni la racha. No decide ni elige otra oferta: Competitive V2
    volveria a elegir la misma la vuelta siguiente (la pieza de los
    managers la aparta en la eleccion), y el motor viejo vuelve a proponer
    cada vuelta la misma fila frenada de una oferta por varios (sin
    escritura gastada, asi que no hay castigo y tampoco pasa a la
    siguiente oferta; en main ya le pasa con las filas de un conservado).
    Cada vuelta asi cuesta un login del escritor y un GET. Que pasen a la
    siguiente, otra pieza. No rechaza ni contesta la oferta frenada: se
    queda ahi. V10 no ejecuta CANCEL_COUNTER si en esa vuelta ya escribio
    otro o estan cerradas las escrituras (`temporal_block`): como con
    NEVER_SELL en main, la retira la vuelta siguiente. No mira
    `no_rotar`, `no_pujar` ni a Yamal por su nombre: solo `proteger`,
    `fichar` y `conservar` de la orden. Con `execute=False` no corre (ni GET
    ni lectura de la orden): la vuelta en seco es main.

    Igual que la guarda de publicar: con la orden apagada, caducada, que no
    vale, que no esta o que no se lee, `protegidos()` y `conservados()` dan
    vacio y NO SE FRENA NADA (y no se hace el GET). Una sola entrada mal
    escrita en la orden la deja sin valer, y esto se apaga solo.

    Boye: el lunes 09/11 sale de `proteger` y sigue en `conservar`. Desde
    entonces su oferta del Computer se puede aceptar (la orden o la mejora).
    La de un MANAGER por el sigue frenada hasta que el gestor lo quite
    tambien de `conservar`.

    Yamal: lo guarda su id en `proteger`. Con la llave `yamal_por_lesion` el
    gestor lo quita de `proteger`, y entonces aqui ya no se frena.

    El GET: con la sesion del escritor y `timeout` `TIEMPO_DEL_GET` (15 s;
    `client.get_market()` no lleva). Un 429 lo reintenta la sesion como
    cualquier peticion (`peticiones.envolver`, unos 15 s); si no cede, se
    escribe como siempre (`guardia_sin_ver`) y la escritura se lleva su
    propio 429.

    Los llamadores fuera de la vuelta: `live_solvency_recovery` (a mano)
    imprime «HTTP: None» sin el motivo de una frenada (esta en `reason`
    de lo que devuelve el escritor); `write_transport_validation_v109` es
    una validacion. La orden (`ejecutar`) apunta `enviada` False y `exito`
    False sin motivo, como con la guarda de publicar.

EL INTERRUPTOR

    `BORDALAS_LA_ORDEN_EN_EL_ESCRITOR`. Nace APAGADO. Se lee en UN sitio
    (`activo`, al llamarse) y vale encendido con lo mismo que el paso 0, el
    tablon y el panel dan por encendido (`el_paso_0.ENCENDIDO`). Apagado,
    `guardar` devuelve None sin red y sin leer la orden: el escritor y sus
    llamadores son main byte a byte. Nunca lanza. Al importarse no hace
    nada.

AL ENCENDERLO

    1. ANTES, en un commit anterior (un interruptor por commit), la pieza
       de los managers (`la_orden_en_los_managers`; su interruptor esta en
       su modulo). Sola, esta deja que Competitive V2 elija cada vuelta la
       misma oferta de la orden y se la frene aqui: Competitive pierde su
       turno. La de los managers pasa la vuelta a la siguiente oferta. Un
       solo `--paso-0` con las dos piezas en el arbol ya prueba las dos.
    2. En UN commit, sobre el ultimo main DE GITHUB (traido a una ref
       privada; el main del checkout local se queda atras): la linea del
       interruptor a "1" en el YAML de produccion y `python
       scripts/run_validation_gate.py --paso-0` en ESE arbol limpio, lo
       ultimo. Se anaden por nombre el YAML y `config/paso_0.json` (nunca
       `add -A`, nunca `data/`). `config/paso_0.json` NUNCA a mano, y no
       se tocan los literales del interruptor que no existe de las
       pruebas. Un conflicto en ese fichero se resuelve corriendo
       `--paso-0` otra vez en el arbol final. OJO: el registro del 04/11
       09:44 tiene 64 probados y le faltan 4 (las tres piezas del 04/11 y
       esta): sin `--paso-0` en ese commit, la verja del ciclo se pone
       roja y la vuelta horaria se para.
    3. Ensayar con la foto real. Hoy (05/11, vuelta de las 11:07) se espera
       1 frenada, la oferta del Computer por Boye (5.316.300; `proteger`),
       que la guardia de cada llamador ya para; las otras 9 ofertas, todas
       del Computer, pasan. 0 contraofertas nuestras vivas: encender no
       retira ninguna. Si al encender hubiera alguna viva por uno de la
       orden, la primera vuelta la retira (CANCEL_COUNTER de V10).
    4. Comprobar que la orden vale (si no, esto no frena a nadie): con el
       interruptor de la orden puesto, `python -c "from
       src.actions.la_orden_del_gestor import protegidos, conservados;
       print(sorted(protegidos()), sorted(conservados()))"`. Hoy, proteger
       Yamal 26271 y Boye 12494; conservar, los nueve.

    LAS HUELLAS DE LA PRUEBA (`test_la_orden_en_el_escritor_v1`). Fijan main:
    `HUELLAS_DE_MAIN` (lo que devuelven, apagado, el escritor, el motor
    viejo y su cluster, Competitive V2, la orden, el tablero de V10 y su
    eleccion, y los viajes) y `FUENTES_DE_MAIN` (el texto del resto del
    escritor y de `la_orden_del_gestor.ejecutar`). Quien cambie a
    proposito algo de eso vuelve a medir, en el MISMO commit, con `python
    -m src.analysis.test_la_orden_en_el_escritor_v1 --medir` en 3.11 Y en
    3.13 sobre su arbol, y pone las dos. Si no, la verja se pone roja y el
    ciclo horario se para. Con un Python que no sea 3.11 ni 3.13 no hay
    huella: se mide antes de cambiar de version en el YAML.
"""

from __future__ import annotations

import os


ENV = "BORDALAS_LA_ORDEN_EN_EL_ESCRITOR"

# Lo que vale como encendido: lo mismo que `el_paso_0.ENCENDIDO` (el paso
# 0, el tablon, el panel y el ensayo). Escrito aqui para no importar nada
# al leerlo; la prueba mira que sean iguales.
ENCENDIDO = frozenset({"1", "true", "si", "sí", "yes", "on"})

GUARDIA = "LA_ORDEN_EN_EL_ESCRITOR"

# El de `proteger` y `fichar`: el mismo codigo que la guarda de publicar
# (`list_player_for_sale`).
BLOQUEO_PROTEGIDO = "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"
BLOQUEO_CONSERVADO = "CONSERVADO_POR_LA_ORDEN_DEL_GESTOR"

# El `status` de la respuesta del escritor cuando frena.
ESTADO = "BLOQUEADA_POR_LA_ORDEN"

ACEPTAR = "ACCEPT_OFFER"
CONTRAOFERTAR = "COUNTER_OFFER"

MOTIVO_PROTEGIDO = (
    "LA_ORDEN_EN_EL_ESCRITOR: la oferta pide a un jugador que la orden del "
    "gestor protege (`proteger` o `fichar`); ni se acepta ni se contraoferta, "
    "venga de quien venga. No ha salido nada hacia Biwenger."
)

MOTIVO_CONSERVADO = (
    "LA_ORDEN_EN_EL_ESCRITOR: la oferta pide a un jugador que la orden del "
    "gestor manda conservar; no se contraoferta nunca (si el rival la acepta "
    "tambien es vender) y solo se acepta la del Computer. No ha salido nada "
    "hacia Biwenger."
)

SIN_LEER_EL_MERCADO = "SIN_LEER_EL_MERCADO"

# Segundos que se espera la respuesta del GET de `/market` (la escritura
# lleva 30).
TIEMPO_DEL_GET = 15

MOTIVO_RETIRAR = (
    "LA_ORDEN_EN_EL_ESCRITOR: nuestra contraoferta viva vende a un jugador "
    "que la orden del gestor guarda (`proteger`, `fichar` o `conservar`); si "
    "el rival la acepta, es vender. Se retira y no se sube."
)
NO_ESTA = "LA_OFERTA_NO_ESTA_EN_EL_MERCADO"
SIN_JUGADORES = "LA_OFERTA_SIN_JUGADORES"


def activo() -> bool:
    """`BORDALAS_LA_ORDEN_EN_EL_ESCRITOR`, leido al llamarse. Encendido con
    lo que el paso 0 da por encendido (`ENCENDIDO`); cualquier otra cosa,
    apagado. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in ENCENDIDO
    except Exception:                               # noqa: BLE001
        return False


def _pid(valor):
    """Un id (de jugador o de oferta) como entero; None si no lo es (ni un
    bool, ni un texto que no es un numero, ni cero o negativo)."""
    try:
        if valor is None or isinstance(valor, bool):
            return None
        pid = int(valor)
        return pid if pid > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _los_pedidos(oferta) -> set:
    """Los jugadores que pide una oferta cruda de Biwenger: los de
    `requestedPlayers` (una lista, o uno suelto como lo lee el tablero de
    V10, `_requested_player_ids`; cada uno un id o `{"id"}`) y `player` (un
    id o `{"id"}`). Uno a uno: el que no es un id se salta y los demas
    cuentan. Nunca lanza."""
    ids = set()
    try:
        pedidos = oferta.get("requestedPlayers")
        if isinstance(pedidos, (int, str, dict)) and not isinstance(pedidos, bool):
            pedidos = [pedidos]
        for x in (list(pedidos) if isinstance(pedidos, list) else []) + [oferta.get("player")]:
            p = _pid(x.get("id") if isinstance(x, dict) else x)
            if p is not None:
                ids.add(p)
    except Exception:                               # noqa: BLE001
        pass
    return ids


def la_oferta(mercado, offer_id) -> dict | None:
    """
    La oferta `offer_id` en el mercado de `/market` (`mercado["offers"]`):
    `{"pedidos": set de ids, "de_un_manager": bool}`. `de_un_manager` es
    True si su `from` no es None (None es el Computer). None si el mercado
    no se lee o la oferta no esta. Si (por error de Biwenger) hubiera dos
    con el mismo id, se juntan: todos los pedidos, y de un manager si lo es
    alguna. Nunca lanza.
    """
    try:
        oid = _pid(offer_id)
        ofertas = mercado.get("offers") if isinstance(mercado, dict) else None
        if oid is None or not isinstance(ofertas, list):
            return None
        vista = None
        for oferta in ofertas:
            if not isinstance(oferta, dict) or _pid(oferta.get("id")) != oid:
                continue
            vista = vista or {"pedidos": set(), "de_un_manager": False}
            vista["pedidos"] |= _los_pedidos(oferta)
            vista["de_un_manager"] = vista["de_un_manager"] or oferta.get("from") is not None
        return vista
    except Exception:                               # noqa: BLE001
        return None


def _de_la_orden():
    """(`protegidos()`, `conservados()`) de la orden de `config/`, ahora: las
    MISMAS funciones que la guarda de publicar. Vacios con la orden apagada,
    caducada, que no vale o que no esta."""
    from src.actions.la_orden_del_gestor import conservados, protegidos

    def _ids(xs):
        return {p for p in (_pid(x) for x in (xs or ())) if p is not None}

    return _ids(protegidos()), _ids(conservados())


def _la_orden_activa():
    """(`protegidos`, `conservados`) con el interruptor encendido (el UNICO
    sitio que lo mira); None apagado, sin leer la orden."""
    if not activo():
        return None
    return _de_la_orden()


def _el_mercado(escritor):
    """(mercado, None) o (None, motivo): `/market` fresco, con la sesion del
    escritor (la de `client.get_market`, que reintenta el 429) y un plazo,
    `TIEMPO_DEL_GET`. Nunca lanza."""
    try:
        cliente = escritor.client
        respuesta = cliente.session.get(f"{cliente.BASE_URL}/market",
                                        timeout=TIEMPO_DEL_GET)
        status = getattr(respuesta, "status_code", None)
        if status != 200:
            return None, f"{SIN_LEER_EL_MERCADO}: HTTP {status}"
        return respuesta.json()["data"], None
    except Exception as error:                      # noqa: BLE001
        return None, f"{SIN_LEER_EL_MERCADO}: {type(error).__name__}"


def lo_que_frena(operacion, oferta, protegidos=None, conservados=None) -> dict | None:
    """
    Lo que la orden frena de `oferta` (la de `la_oferta`) para `operacion`
    (ACCEPT_OFFER o COUNTER_OFFER). Pura: sin `protegidos` ni `conservados`,
    los de `la_orden_del_gestor` (sin argumentos).

        proteger/fichar que pide la oferta: PROTEGIDO, venga de quien venga.
        conservar que pide la oferta: CONSERVADO si es una contraoferta o la
            oferta es de un manager. La del Computer, no.

    `{"blocked", "de_la_orden"}` o None (nada que frenar). Lo que no es
    una oferta o un id, no cuenta.
    """
    if not isinstance(oferta, dict):
        return None
    if protegidos is None or conservados is None:
        protegidos, conservados = _de_la_orden()
    try:
        pedidos = {p for p in (_pid(x) for x in (oferta.get("pedidos") or ())) if p is not None}
    except TypeError:
        pedidos = set()
    prot = pedidos & set(protegidos)
    cons = (
        pedidos & set(conservados)
        if operacion == CONTRAOFERTAR or oferta.get("de_un_manager")
        else set()
    )
    if prot:
        return {"blocked": BLOQUEO_PROTEGIDO, "de_la_orden": sorted(prot | cons)}
    if cons:
        return {"blocked": BLOQUEO_CONSERVADO, "de_la_orden": sorted(cons)}
    return None


def guardar(escritor, operacion, offer_id) -> dict | None:
    """
    Para `accept_offer` y `counter_offer`, con `execute=True` y antes del
    ensayo.

        None                      apagado (sin red ni leer la orden), la
                                  orden no guarda a nadie (sin red), o la
                                  oferta no pide a nadie de la orden.
        {"sin_ver": motivo}       no se pudo ver la oferta: se escribe como
                                  siempre y la respuesta lo lleva.
        {"status", "reason", "guardia", "blocked", "de_la_orden",
         "pedidos", "de_un_manager"}
                                  frenada: el escritor no envia nada.

    Nunca lanza: si algo falla, None (lo de siempre).
    """
    try:
        orden = _la_orden_activa()
        if orden is None:
            return None
        protegidos, conservados = orden
        if not protegidos and not conservados:
            return None
        mercado, sin_ver = _el_mercado(escritor)
        if sin_ver:
            return {"sin_ver": sin_ver}
        oferta = la_oferta(mercado, offer_id)
        if oferta is None:
            return {"sin_ver": NO_ESTA}
        if not oferta["pedidos"]:
            return {"sin_ver": SIN_JUGADORES}
        frena = lo_que_frena(operacion, oferta, protegidos, conservados)
        if not frena:
            return None
        return {
            "status": ESTADO,
            "reason": (
                MOTIVO_PROTEGIDO if frena["blocked"] == BLOQUEO_PROTEGIDO
                else MOTIVO_CONSERVADO
            ),
            "guardia": GUARDIA,
            **frena,
            "pedidos": sorted(oferta["pedidos"]),
            "de_un_manager": bool(oferta["de_un_manager"]),
        }
    except Exception:                               # noqa: BLE001
        return None


def retirar_la_contraoferta(contraoferta, recibida=None) -> dict | None:
    """
    Para `dynamic_counteroffer_repricing_v107.evaluate_counteroffer`, antes
    de todo: ¿se retira esta contraoferta NUESTRA viva?

    `contraoferta` es la fila del tablero (`player_id` y `raw_offer`, la
    contraoferta cruda) y `recibida` la oferta del rival a la que contesta
    (o None). Si alguno de todos esos jugadores esta en `proteger`/`fichar`
    (PROTEGIDO) o en `conservar` (CONSERVADO; una contraoferta siempre es
    para un manager): `{"guardia", "blocked", "de_la_orden", "pedidos",
    "reason"}` y el tablero da CANCEL_COUNTER. None apagado (sin leer la
    orden), con la orden vacia o si no vende a nadie de la orden. Sin red.
    Nunca lanza: si algo falla, None (lo de siempre).
    """
    try:
        orden = _la_orden_activa()
        if orden is None:
            return None
        protegidos, conservados = orden
        if not protegidos and not conservados:
            return None
        pedidos = set()
        if isinstance(contraoferta, dict):
            pid = _pid(contraoferta.get("player_id"))
            if pid is not None:
                pedidos.add(pid)
            if isinstance(contraoferta.get("raw_offer"), dict):
                pedidos |= _los_pedidos(contraoferta["raw_offer"])
        if isinstance(recibida, dict):
            pedidos |= _los_pedidos(recibida)
        frena = lo_que_frena(CONTRAOFERTAR, {"pedidos": pedidos, "de_un_manager": True},
                             protegidos, conservados)
        if not frena:
            return None
        return {
            "guardia": GUARDIA,
            **frena,
            "pedidos": sorted(pedidos),
            "reason": MOTIVO_RETIRAR,
        }
    except Exception:                               # noqa: BLE001
        return None
