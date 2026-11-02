"""
LA SUBASTA EN EL COLCHON (01/11/2026)

POR QUE EXISTE

    El 31/10 a las 04:48 la cesta del reset del motor viejo
    (`la_subasta.plan_del_reset`, la que puja `_pujar_en_el_reset` en las
    vueltas de las 04:45 y 04:50) pujo 2.025.051 por Dani Lorenzo con el
    saldo en 1.299.975 y 929.800 en pujas vivas de la ronda (Macia
    709.900, Angel Ortiz 219.900). Se gano y dejo el saldo en -944.976.

        - el freno de la solvencia dijo SIN_DEUDA: no ve la cesta ni las
          pujas vivas;
        - el tope es min(presupuesto, 3 x saldo);
        - no mira lo cerca que esta la jornada;
        - y el colchon de la casa (`BORDALAS_UN_SOLO_COLCHON`,
          `la_ronda_de_la_manana.cabe_en_el_colchon`) solo lo mira el
          ejecutor del motor viejo, no esta cesta.

    Repetida: el colchon era 1.179.775 contra 2.025.051. No cabia. Y Dani
    subia +10.000 sobre 2.020.000, por debajo de la subida minima de su
    tramo (22.220). Su historial desde el 22/09: 2 pujas, unos -305.000;
    solo el cubo de menos de 1,5 M gano dinero (bitacora del 31/10 22:30).

LA REGLA

    Sobre las pujas que ya eligio la cesta (despues del reparto, el tope
    del primer dia, el peor caso y la orden del gestor), y en este orden:

    1. EL RELOJ. Si faltan menos de `HORAS_SIN_COMPRAR` (40 h, la de la
       ronda: lo comprado tiene que recibir al menos una oferta del
       Computer antes de la jornada) o no se sabe cuanto falta, no se
       puja: CERCA_DE_LA_JORNADA. Las horas son las de
       `horas_a_la_jornada`, la misma cuenta que la ronda.
    2. SUBE DE VERDAD. Solo las que suben hoy al menos la subida minima
       de su tramo (`la_mejora_del_once.sube_de_verdad`, la vara de la
       mejora y del motor viejo): `price_increment` > 0 no basta. Si no
       queda ninguna: NO_SUBE_DE_VERDAD.
    3. EL COLCHON. En el orden de la cesta, cada puja tiene que caber en
       el colchon de la casa CONTANDO las que ya caben delante
       (`cabe_en_el_colchon(foto, jugador, delante + puja)`): saldo
       menos todas las pujas vivas mas el 92 % de lo de la cartera. La
       que no cabe se queda fuera y la siguiente se mira igual. Si no
       queda ninguna: SIN_COLCHON. Y SIN_COLCHON tambien, sin mirar
       nada, si no se puede calcular: sin saldo en la foto, o una foto
       en la que no se reconocen nuestras pujas vivas (sin `yo` en
       `league.user`, o sin la lista `market.offers`: la misma foto que
       `limpiar_el_libro` no se cree). No se puja a ciegas.

       LA FOTO es la mas fresca de la vuelta (`foto_del_colchon`): si el
       motor viejo ya escribio en `run_cycle`, la de `post_action`, que
       trae su puja; si no, la de la vuelta. Y "delante" empieza con lo
       que el libro de pujas apunta en esta ventana (`pujas_desde`) y
       la foto aun no trae: lo puesto despues de sacarla, o una foto
       que llega con retraso. Contarlo de mas cae del lado de no pujar.
    4. Las cuentas del plan (`committed`, `expected`, `all_won`,
       `slots_used`, `worst_case`, `execute`, `reason`) se rehacen con lo
       que queda. Lo que se ha mirado va en `en_el_colchon`.

    Sin pujas que mirar (la cesta ya estaba cerrada por otra puerta), el
    plan sale tal cual.

    El reloj desconocido sale CERCA_DE_LA_JORNADA, como pide el encargo,
    pero con `en_el_colchon.sin_reloj` a True y su motivo ("no se sabe
    cuanto falta"): en el panel no se confunde con "faltan 16 h".

UN SOLO COLCHON EN LA VUELTA: LO PUJADO SE RESERVA

    Despues de la cesta, en la misma vuelta, pujan la orden, los chollos
    y la ronda, y cada uno saca su colchon de `cycle["snapshot"]`. Sin
    mas, ninguno veria lo que la cesta acaba de pujar y cada uno
    volveria a gastar el colchon entero (el revisor, 01/11: cesta
    1.152.876 y ronda 1.010.000 sobre un colchon de 1.179.775).
    Encendido, `_pujar_en_el_reset` cambia `cycle["snapshot"]` por
    `con_lo_pujado(...)`: la misma foto con lo que la cesta pujo, y lo
    que conto sin estar en la foto, como pujas vivas nuestras, y con
    `maximumBid` bajado lo que sube lo comprometido. Es lo que traeria
    una foto nueva, sin pedirla. La foto vieja no se toca. Una puja viva
    que ya estaba no baja nunca: se queda la mayor. Y se reserva tambien
    cuando la cesta no puja (SIN_COLCHON y demas): lo que el colchon
    conto sin estar en la foto (`sin_foto`, `de_otra_foto`) existe
    igual (los revisores, 01/11).

    Lo que se reserva es `la_reserva` (02/11): no la puja que Biwenger
    rechazo sin duda (`la_rechazada`: se mando y contesto un 4xx; lo
    que no se sabe sigue contando), y lo de `sin_foto` cuenta como puja
    viva pero no baja `maximumBid`: una puja del libro que una foto
    fresca no trae casi siempre es una rechazada o retirada, y el tope
    de Biwenger ya es el de verdad (sin esto la orden no fichaba por un
    tope 50.000 por debajo del real).

UN SOLO COLCHON ENTRE PROCESOS (02/11/2026)

    Lo que corre despues en el mismo workflow (la mejora del once y la
    rotacion, que pujan; el cierre y el parte, en sus cuentas) son
    procesos aparte: leen la foto del disco, de antes de la cesta, y lo
    que la vuelta ya hizo, del estado de v10. Encendido, el estado lleva
    un bloque `subasta` (`el_bloque_de_la_vuelta`) con `hechas` de la
    misma forma que las de la ronda: lo mismo que se reservo en
    `cycle["snapshot"]`, cuente o no se sepa si entro, menos lo de
    `sin_foto` (que va aparte: la mejora no vuelve a pujar por ellos,
    pero no entra en ninguna caja, porque el cierre y la mejora tambien
    venden); la rechazada va con `exito` False. La mejora lo lee con la
    orden, los chollos y la ronda; el cierre (y la rotacion, que en la
    franja no escribe) leen todos los bloques con `hechas`; el parte solo
    lo vendido y lo publicado. Una puja que la foto del disco ya trae
    (una foto sacada despues de la cesta) no se cuenta dos veces: el
    cierre y la rotacion cuentan por jugador, y la mejora solo resta del
    `maximumBid` lo que la foto aun no trae, y de una puja de despues por
    el mismo, solo lo que crece. Si un 429 retira la vuelta despues de la
    cesta, `main` deja un estado minimo con el bloque. Apagado no hay
    bloque y el estado es el de siempre, byte a byte.

    Siguen sin verlo (no sacan su colchon de esa foto, y en main
    tampoco): el V10 BUY (`build_controlled_run`, lee la foto del disco)
    y el carril (su comprometido sale de `bid_exposure`).

SUBCONJUNTO POR LLAMADA, NO POR VENTANA

    En cada llamada, encendido solo QUITA pujas del plan de main (con
    el mismo importe) y nunca pone `execute` a True. En la ventana
    entera no es asi: la que el colchon deja fuera a las 04:45 no va al
    libro, y la vuelta de las 04:50 puede llenar ese hueco con otra que
    main no pujo en ninguno de los dos disparos (el revisor, 01/11:
    04:45 [X1, X2], 04:50 [D] contra main 04:45 [X1, X2, GRANDE]). Esa
    tambien pasa el reloj, la subida y el colchon acumulado con la foto
    nueva, y en total se compromete menos: no hay riesgo contra la regla
    del colchon, pero "encendido nunca puja lo que main no pujaria" vale
    por llamada, no por ventana.

EL INTERRUPTOR

    `BORDALAS_LA_SUBASTA_EN_EL_COLCHON`, que se lee en UN sitio:
    `la_subasta._en_el_colchon`, desde `plan_desde_el_estado`, por donde
    pasan el ciclo y la pantalla. Este modulo no lo lee. Nace APAGADO, y
    apagado no se llama.

    ENCENDERLO (los revisores, 02/11). No antes del jue 05/11 05:00 (la
    cesta aun podria pujar para la J12 el mie 04/11 y el jue 05/11 a las
    04:45). Un solo commit con las tres cosas:

        1. el YAML: fuera `BORDALAS_SIN_SUBASTA`, y
           `BORDALAS_LA_SUBASTA_EN_EL_COLCHON: "1"` y
           `BORDALAS_CESTA_SOLO_EL_SUELO: "1"`, con "1" literal (el
           paso 0 da "on" o "si" por encendido; este lector, no);
        2. `python scripts/run_validation_gate.py --paso-0` sobre ese
           mismo arbol;
        3. `config/paso_0.json`, el que deja el paso 0.

    Sin el 3, `test_el_paso_0_no_se_olvida_v1` pone roja la verja de
    CI, que es el primer paso de cada vuelta: v10, la mejora y el
    cierre no corren hasta arreglarlo. Una verja que cambia los
    interruptores en memoria no lo ve: esa guardia lee el YAML del
    disco. Despues, la verja normal en 3.11 y 3.13.

    EL ENSAYO, en la rama de ese commit o, antes, en main con
    `interruptores: -BORDALAS_SIN_SUBASTA BORDALAS_LA_SUBASTA_EN_EL_COLCHON
    BORDALAS_CESTA_SOLO_EL_SUELO` (el `-` quita). Sumar sin quitar no
    prueba nada: `BORDALAS_SIN_SUBASTA` cierra la cesta antes del
    colchon. Y dentro de la ventana (135 min antes del reset de las
    07:00) pero lejos de las vueltas de las 04:45 y 04:50 (05:05-06:30):
    dos sesiones a la vez son un 429. Mirar que el estado de v10 del
    artefacto lleve `subasta.hechas` y que `escrituras_no_enviadas`
    traiga las pujas de la cesta.

    APAGARLO ES VOLVER A PONER `BORDALAS_SIN_SUBASTA: "1"` (ya pasa el
    paso 0). NUNCA quitando el colchon o el suelo: sin el colchon, la
    cesta vuelve a ser la del 31/10 (2.025.051 por Dani Lorenzo). Lo
    vigila `test_la_subasta_en_el_colchon_v1` (la cesta no se abre sin
    sus candados): si el YAML abre la cesta, el colchon y el suelo
    tienen que estar encendidos para su lector de verdad.

QUE NO HACE

    No cambia las reglas de la ronda, la mejora, los chollos, el carril
    ni el tablero de fichajes: solo les deja ver, en la foto o en el
    estado de la vuelta, lo que la cesta ya pujo. Tampoco la sombra (`la_sombra_de_la_puja`) ni la
    lista de la noche, que llaman a `plan_del_reset` directamente para
    ver lo que haria la cesta sin candados (sin colchon). No sube
    ninguna puja: solo quita.

    Importarlo no hace nada. Lee la foto que se le pasa, el calendario,
    el libro de la ronda y, con `pujas_desde`, el libro de pujas (los de
    la casa si no se pasan). Nunca lanza: si algo falla, no se puja y se
    dice por que.
"""

from __future__ import annotations


CERCA_DE_LA_JORNADA = "CERCA_DE_LA_JORNADA"
NO_SUBE_DE_VERDAD = "NO_SUBE_DE_VERDAD"
SIN_COLCHON = "SIN_COLCHON"


def _cerrado(plan: dict, motivo: str, reason: str, detalle: dict, **extra) -> dict:
    """El plan sin ninguna puja, con su motivo. Nunca lanza."""

    return {
        **plan,
        "execute": False,
        "bids": [],
        "committed": 0,
        "expected": 0,
        "all_won": 0,
        "slots_used": 0,
        "worst_case": None,
        **extra,
        "blocked_by": motivo,
        "reason": reason,
        "en_el_colchon": detalle,
    }


def _yo_y_ofertas(foto) -> tuple:
    """(yo, ofertas) de la foto; `None` lo que no se puede leer. Pura."""

    from src.actions.la_orden_del_gestor import _pid

    foto = foto if isinstance(foto, dict) else {}
    liga = foto.get("league")
    yo = _pid(liga.get("user")) if isinstance(liga, dict) else None
    mercado = foto.get("market")
    ofertas = mercado.get("offers") if isinstance(mercado, dict) else None
    return yo, (ofertas if isinstance(ofertas, list) else None)


def _nuestras(foto, yo) -> dict:
    """{jugador: importe} de nuestras pujas vivas en la foto. Pura."""

    from src.actions.la_orden_del_gestor import _int, leer_la_foto

    return {
        pid: _int((fila or {}).get("amount"), 0) or 0
        for pid, fila in (leer_la_foto(foto, yo).get("nuestras_pujas") or {}).items()
        if pid is not None
    }


def _las_del_libro(libro, desde, vistas) -> list:
    """
    Las pujas del libro de pujas PENDIENTES puestas desde `desde` por
    jugadores que la foto no trae como nuestros (`vistas`). Una por
    jugador, la mas alta. Pura; lo que no se lee, fuera.
    """

    from datetime import datetime, timezone

    from src.actions.la_orden_del_gestor import _int

    if isinstance(desde, str):
        desde = datetime.fromisoformat(desde)
    if desde.tzinfo is None:
        desde = desde.replace(tzinfo=timezone.utc)

    salida = {}
    entradas = (libro or {}).get("bids") if isinstance(libro, dict) else None

    for entrada in (entradas or {}).values() if isinstance(entradas, dict) else ():
        if not isinstance(entrada, dict):
            continue
        if entrada.get("outcome") not in (None, "PENDING"):
            continue
        pid, importe = _int(entrada.get("player_id")), _int(entrada.get("amount"), 0) or 0
        if pid is None or importe <= 0 or pid in vistas:
            continue
        try:
            marca = datetime.fromisoformat(str(entrada.get("placed_at")))
        except Exception:                           # noqa: BLE001
            continue
        if marca.tzinfo is None:
            marca = marca.replace(tzinfo=timezone.utc)
        if marca < desde:
            continue
        if importe > salida.get(pid, {}).get("amount", 0):
            salida[pid] = {"id": pid, "amount": importe,
                           "placed_at": entrada.get("placed_at"),
                           "source": entrada.get("target_source")}

    return [salida[pid] for pid in sorted(salida)]


def con_lo_pujado(snapshot, pujas, sin_tope=None) -> dict | None:
    """
    La foto de la vuelta con `pujas` ([(jugador, importe)]) como pujas
    vivas nuestras: lo que traeria una foto nueva despues de pujar. La
    que ya estaba por el mismo jugador se queda con la MAYOR de las dos
    (Biwenger deja una por jugador, y una foto nueva no la traeria mas
    baja de lo que hay: el revisor, 01/11); la nueva va con `id` None
    (no se puede retirar desde aqui) y `reservada_por`.

    Y `market.status.maximumBid`, si es un entero, baja lo que sube lo
    comprometido: la nueva entera y, de la que ya estaba, solo lo que
    crece. Es lo que traeria la foto nueva; sin esto, la orden sumaba la
    reservada a un tope viejo (tope = maximo + lo ya pujado) y pujaba
    donde main no, y los chollos de 72 h y la ronda no veian la cesta en
    el tope (el revisor, 01/11). Los de `sin_tope` ({jugador}: los que
    solo estan por `sin_foto`) entran como pujas vivas pero NO bajan
    `maximumBid`: una puja del libro que una foto fresca no trae casi
    siempre es una que Biwenger rechazo o que se retiro, y su tope ya es
    el de verdad (el revisor, 02/11: la orden no fichaba por un tope
    50.000 por debajo del de Biwenger).

    Devuelve una foto NUEVA y no toca la que se le pasa. Si no se puede
    (sin `yo`, sin ofertas), la misma. Nunca lanza.
    """

    try:
        from src.actions.la_orden_del_gestor import _int, _pid

        yo, ofertas = _yo_y_ofertas(snapshot)
        if yo is None or ofertas is None:
            return snapshot

        nuevas = {}
        for pid, importe in pujas or ():
            pid, importe = _int(pid), _int(importe, 0) or 0
            if pid is not None and importe > 0:
                nuevas[pid] = max(nuevas.get(pid, 0), importe)
        if not nuevas:
            return snapshot
        sin_tope = {_int(p) for p in sin_tope or ()}

        salida = []
        sube = 0
        for oferta in ofertas:
            jugadores = (oferta.get("requestedPlayers") or []) if isinstance(oferta, dict) else []
            pid = _pid(jugadores[0]) if isinstance(jugadores, list) and len(jugadores) == 1 else None
            if (pid in nuevas and str(oferta.get("status", "waiting")) == "waiting"
                    and _pid(oferta.get("from")) == yo):
                habia = _int(oferta.get("amount"), 0) or 0
                queda = max(habia, nuevas.pop(pid))
                if pid not in sin_tope:
                    sube += queda - habia
                salida.append({**oferta, "amount": queda})
                continue
            salida.append(oferta)

        for pid, importe in nuevas.items():
            if pid not in sin_tope:
                sube += importe
            salida.append({
                "id": None, "from": {"id": yo}, "status": "waiting",
                "amount": importe, "requestedPlayers": [{"id": pid}],
                "reservada_por": "LA_SUBASTA_EN_EL_COLCHON",
            })

        mercado = {**snapshot["market"], "offers": salida}
        estado = mercado.get("status")
        maximo = estado.get("maximumBid") if isinstance(estado, dict) else None
        if sube and isinstance(maximo, int) and not isinstance(maximo, bool):
            mercado["status"] = {**estado, "maximumBid": maximo - sube}

        return {**snapshot, "market": mercado}

    except Exception:                               # noqa: BLE001
        return snapshot


def lo_que_reservar(plan) -> list:
    """
    [(jugador, importe)] que la vuelta tiene que ver como pujas vivas
    nuestras despues de la cesta: lo que pujo (`plan["bids"]`, haya
    entrado o no: lo que no se sabe cuenta) y lo que el colchon conto
    sin estar en la foto de la vuelta (`en_el_colchon.sin_foto` y
    `de_otra_foto`). Nunca lanza.
    """

    try:
        from src.actions.la_orden_del_gestor import _int

        plan = plan if isinstance(plan, dict) else {}
        detalle = plan.get("en_el_colchon") if isinstance(plan.get("en_el_colchon"), dict) else {}
        salida = [(b.get("id"), b.get("bid")) for b in plan.get("bids") or []
                  if isinstance(b, dict)]
        for clave in ("sin_foto", "de_otra_foto"):
            salida += [(f.get("id"), f.get("amount")) for f in detalle.get(clave) or []
                       if isinstance(f, dict)]
        return [(_int(p), _int(i, 0)) for p, i in salida
                if _int(p) is not None and (_int(i, 0) or 0) > 0]

    except Exception:                               # noqa: BLE001
        return []


def _la_respuesta(fila) -> tuple:
    """(puja, resultado, error) de una fila de `respuestas`; lo que no se
    lee, None. Pura, nunca lanza."""

    try:
        puja, resultado, error = (tuple(fila) + (None, None, None))[:3] \
            if isinstance(fila, (list, tuple)) else (None, None, None)
        return (puja if isinstance(puja, dict) else None,
                resultado if isinstance(resultado, dict) else None, error)
    except Exception:                               # noqa: BLE001
        return None, None, None


def la_rechazada(resultado) -> str | None:
    """
    El motivo si Biwenger RECHAZO la puja sin duda; si no, None.

    Rechazada es: se mando (`sent` True), `success` False y un 4xx, en el
    HTTP o en el `status` del cuerpo (un 200 con {"status": 400, ...}).
    Eso es una respuesta, no una duda: la puja no existe y no se reserva
    (el revisor, 02/11: una 400 contaba entera en la caja del cierre, que
    vende en rojo). Lo que NO se sabe sigue contando: una excepcion (la
    red, un 429 que no cede), un 5xx, un 200 con una pagina de
    mantenimiento (`success` False sin 4xx: puede haber entrado), y lo
    que no se mando (`sent` False: el ensayo; ahi se mira lo que haria).
    Pura, nunca lanza.
    """

    try:
        if (not isinstance(resultado, dict) or resultado.get("sent") is not True
                or resultado.get("success") is not False):
            return None

        def _4xx(valor):
            return (isinstance(valor, int) and not isinstance(valor, bool)
                    and 400 <= valor < 500)

        if _4xx(resultado.get("http_status")):
            return f"HTTP {resultado.get('http_status')}"
        cuerpo = resultado.get("response")
        if isinstance(cuerpo, dict) and _4xx(cuerpo.get("status")):
            return f"status {cuerpo.get('status')} en la respuesta"
        return None
    except Exception:                               # noqa: BLE001
        return None


def la_reserva(plan, respuestas=None) -> dict:
    """
    Lo que la vuelta reserva despues de la cesta. UNA cuenta para la foto
    de la vuelta (`_reservar_lo_pujado` -> `con_lo_pujado`) y para el
    estado de la vuelta (`el_bloque_de_la_vuelta`):

        pujas       [(jugador, importe)], como `lo_que_reservar`: las del
                    plan que se mandaron (con `respuestas` None, ninguna:
                    no se mando nada) menos las que Biwenger rechazo sin
                    duda (`la_rechazada`; con varias por el mismo, si las
                    rechazo todas), y lo de `sin_foto` y `de_otra_foto`.
        sin_tope    {jugador} que solo estan por `sin_foto`: cuentan como
                    pujas vivas para los que pujan en la vuelta (de mas cae
                    del lado de no pujar), pero no bajan `maximumBid` ni
                    van al estado, donde las leen el cierre y la mejora,
                    que tambien venden: una puja del libro que una foto
                    fresca no trae casi siempre es una rechazada o
                    retirada (el revisor, 02/11).
        rechazadas  {jugador: motivo}

    Nunca lanza.
    """

    try:
        from src.actions.la_orden_del_gestor import _int

        plan = plan if isinstance(plan, dict) else {}
        detalle = plan.get("en_el_colchon") if isinstance(plan.get("en_el_colchon"), dict) else {}

        motivos = {}
        for fila in respuestas or ():
            puja, resultado, _ = _la_respuesta(fila)
            pid = _int(puja.get("id")) if puja else None
            if pid is not None:
                motivos.setdefault(pid, []).append(la_rechazada(resultado))
        rechazadas = {pid: m[0] for pid, m in motivos.items() if m and all(m)}

        bids = [] if respuestas is None else [
            b for b in plan.get("bids") or []
            if not (isinstance(b, dict) and _int(b.get("id")) in rechazadas)]

        del_plan = lo_que_reservar({"bids": bids})
        sin_foto = lo_que_reservar({"en_el_colchon": {"sin_foto": detalle.get("sin_foto")}})
        de_otra = lo_que_reservar({"en_el_colchon": {"de_otra_foto": detalle.get("de_otra_foto")}})

        return {
            "pujas": del_plan + sin_foto + de_otra,
            "sin_tope": {p for p, _ in sin_foto} - {p for p, _ in del_plan + de_otra},
            "rechazadas": rechazadas,
        }

    except Exception:                               # noqa: BLE001
        return {"pujas": [], "sin_tope": set(), "rechazadas": {}}


def el_bloque_de_la_vuelta(plan, respuestas=None) -> dict:
    """
    El bloque `subasta` del estado de la vuelta
    (`data/trading/v10_full_autonomous_status.json`): lo que la cesta
    deja reservado, para los pasos de despues, que son OTROS procesos (la
    mejora del once, el cierre, el parte, la rotacion) y leen la foto del
    disco, que es de antes de la cesta.

        respuestas  [(puja, resultado, error)] de cada puja mandada, en
                    el orden del plan (`resultado`, lo que devolvio
                    `place_bid`; `error`, el texto si reviento). None:
                    no se mando nada (la salida sin ejecutar) y de las
                    del plan no va ninguna.

    `hechas` es UNA fila por jugador, con la forma de las `hechas` de la
    ronda y los chollos (`la_orden_del_gestor.ejecutar`): `accion`
    PUJAR, `player_id`, `importe`, `sustituye` None, `enviada`, `exito`,
    `http_status`, y `subasta` True donde la ronda pone `ronda` True.
    Con `exito` True va lo mismo que `_reservar_lo_pujado` deja en
    `cycle["snapshot"]` (`la_reserva`, por jugador la mayor, como
    `con_lo_pujado`) menos lo que solo esta por `sin_foto`:

        - las pujas de la cesta, aunque no se sepa si entraron (una
          excepcion, un 5xx, un 200 con una pagina de mantenimiento);
          contarla de mas cae del lado de no pujar;
        - lo que el colchon conto en la foto de `post_action` y no en
          la de la vuelta (`de_otra_foto`: el motor viejo pujo en
          `run_cycle`), marcadas `reservada`.

    Una que Biwenger rechazo sin duda (`la_rechazada`) va con `exito`
    False y `rechazada`: no la cuenta nadie. Lo que contesto Biwenger va
    en `enviada`, `http_status`, `exito_de_biwenger` y `error`.

    `sin_foto` no va en `hechas` (ver `la_reserva`): va aparte, con
    `de_otra_foto` ([{id, amount}], las del colchon), y la mejora no
    vuelve a pujar por ellos. `reservado` es la suma de las de `exito`.
    Nunca lanza.
    """

    try:
        from src.actions.la_orden_del_gestor import _int

        plan = plan if isinstance(plan, dict) else {}
        detalle = plan.get("en_el_colchon") if isinstance(plan.get("en_el_colchon"), dict) else {}
        reserva = la_reserva(plan, respuestas)

        importes = {}
        for pid, importe in reserva["pujas"]:
            if pid not in reserva["sin_tope"]:
                importes[pid] = max(importes.get(pid, 0), importe)

        de_la_cesta, orden = {}, []
        for fila in respuestas or ():
            puja, resultado, error = _la_respuesta(fila)
            pid = _int(puja.get("id")) if puja else None
            if pid is not None and pid not in de_la_cesta:
                de_la_cesta[pid] = (puja, resultado or {}, error)
                orden.append(pid)
        orden += [pid for pid in importes if pid not in de_la_cesta]

        marcas = {}
        for f in detalle.get("de_otra_foto") or []:
            pid = _int(f.get("id")) if isinstance(f, dict) else None
            if pid is not None:
                marcas.setdefault(pid, "DE_OTRA_FOTO")

        hechas = []
        for pid in orden:
            if pid in de_la_cesta:
                puja, resultado, error = de_la_cesta[pid]
                rechazo = None if pid in importes else reserva["rechazadas"].get(pid)
                if pid not in importes and not rechazo:
                    continue
                fila = {
                    "accion": "PUJAR", "player_id": pid,
                    "importe": importes[pid] if pid in importes
                    else (_int(puja.get("bid"), 0) or 0),
                    "nombre": puja.get("name"),
                    "pide": _int(puja.get("market_price")),
                    "sube": _int(puja.get("price_increment")),
                    "sustituye": None, "subasta": True,
                    "enviada": bool(resultado.get("sent")),
                    "exito": rechazo is None,
                    "http_status": resultado.get("http_status"),
                    "exito_de_biwenger": resultado.get("success"),
                }
                if rechazo:
                    fila["rechazada"] = rechazo
                elif pid in marcas and reserva["rechazadas"].get(pid):
                    fila["reservada"] = marcas[pid]
                if error:
                    fila["error"] = str(error)
            else:
                fila = {
                    "accion": "PUJAR", "player_id": pid, "importe": importes[pid],
                    "sustituye": None, "subasta": True,
                    "reservada": marcas.get(pid, "DE_OTRA_FOTO"),
                    "enviada": False, "exito": True, "http_status": None,
                }
            hechas.append(fila)

        def _lista(clave):
            return [{"id": _int(f.get("id")), "amount": _int(f.get("amount"), 0) or 0}
                    for f in detalle.get(clave) or []
                    if isinstance(f, dict) and _int(f.get("id")) is not None]

        return {
            "hechas": hechas,
            "reservado": sum(importes.values()),
            "de_otra_foto": _lista("de_otra_foto"),
            "sin_foto": _lista("sin_foto"),
        }

    except Exception as error:                      # noqa: BLE001
        return {"hechas": [], "reservado": 0, "de_otra_foto": [], "sin_foto": [],
                "error": f"{type(error).__name__}: {error}"}


def en_el_colchon(
    plan: dict | None,
    snapshot: dict | None,
    plantilla: list | None = None,
    ahora=None,
    calendario=None,
    libro_ruta=None,
    foto_del_colchon: dict | None = None,
    pujas_desde=None,
    libro_de_pujas: dict | None = None,
) -> dict:
    """
    El plan de la cesta, con solo las pujas que pasan el reloj, suben de
    verdad y caben en el colchon de la casa. Ver la cabecera.

        plan        la salida de `plan_del_reset` (ya con la orden)
        snapshot    la foto de Biwenger de la vuelta: saldo y pujas vivas
        plantilla   la de `lectura_del_estado`, para el peor caso
        ahora       UTC; `None` es el reloj de verdad
        calendario  ruta o dict; `None` es el de la casa
        libro_ruta  el libro de la ronda; `None` es el de la casa
        foto_del_colchon  una foto mas fresca que `snapshot` (la de
                    `post_action`); `None`, la de la vuelta
        pujas_desde el comienzo de la ventana: lo que el libro de pujas
                    apunta desde ahi y la foto no trae, cuenta delante;
                    `None`, no se mira el libro (la pantalla)
        libro_de_pujas  el libro de pujas; `None` es el de la casa

    Nunca lanza.
    """

    base = plan if isinstance(plan, dict) else {}

    detalle = {
        "puesta": True,
        "horas_a_la_jornada": None,
        "horas_minimas": None,
        "sin_reloj": False,
        "colchon": None,
        "foto": None,
        "sin_foto": [],
        "de_otra_foto": [],
        "comprometido": 0,
        "caben": [],
        "fuera": [],
        "no_suben": [],
    }

    try:
        from datetime import datetime, timezone

        from src.actions.la_mejora_del_once import sube_de_verdad
        from src.actions.la_ronda_de_la_manana import (
            HORAS_SIN_COMPRAR,
            cabe_en_el_colchon,
            horas_a_la_jornada,
            la_subida_minima,
        )
        from src.analysis.la_subasta import (
            _euros,
            peor_caso,
            safe_float,
            safe_int,
        )

        pujas = base.get("bids")

        if not pujas:
            return base

        pujas = (
            [b for b in pujas if isinstance(b, dict)]
            if isinstance(pujas, list)
            else []
        )

        if not pujas:
            return _cerrado(
                base, SIN_COLCHON,
                "Las pujas de la cesta no se pueden leer: no se puja.",
                detalle,
            )

        # 1. EL RELOJ
        minimas = float(HORAS_SIN_COMPRAR)
        detalle["horas_minimas"] = minimas

        horas = horas_a_la_jornada(
            ahora or datetime.now(timezone.utc), calendario
        )

        if horas is None:
            detalle["sin_reloj"] = True
            return _cerrado(
                base, CERCA_DE_LA_JORNADA,
                (
                    "No se sabe cuanto falta para la jornada (sin "
                    "calendario): la cesta no puja a ciegas."
                ),
                detalle,
            )

        horas = float(horas)
        detalle["horas_a_la_jornada"] = horas

        if horas < minimas:
            return _cerrado(
                base, CERCA_DE_LA_JORNADA,
                (
                    f"Faltan {f'{horas:.1f}'.replace('.', ',')} h para la "
                    f"jornada y la cesta no "
                    f"compra a menos de {minimas:.0f} h: lo que se gane en "
                    f"el reset no llegaria a recibir la oferta del Computer "
                    f"antes del cierre. No se puja."
                ),
                detalle,
            )

        # 2. SUBE DE VERDAD
        siguen, no_suben = [], []

        for puja in pujas:
            precio = safe_int(puja.get("market_price"))
            sube = puja.get("price_increment")

            if sube_de_verdad({"price": precio, "price_increment": sube}):
                siguen.append(puja)
                continue

            no_suben.append({
                "id": safe_int(puja.get("id")),
                "name": puja.get("name"),
                "market_price": precio,
                "price_increment": sube,
                "minima": la_subida_minima(precio),
            })

        detalle["no_suben"] = no_suben

        texto_no_suben = "; ".join(
            f"{f['name']} "
            f"{'+' if safe_int(f['price_increment']) > 0 else ''}"
            f"{_euros(f['price_increment'])} sobre "
            f"{_euros(f['market_price'])} (pide {_euros(f['minima'])})"
            for f in no_suben
        )

        if not siguen:
            return _cerrado(
                base, NO_SUBE_DE_VERDAD,
                (
                    f"Ninguna sube de verdad hoy (la subida minima de su "
                    f"tramo, la vara de la mejora): {texto_no_suben}. No "
                    f"se puja."
                ),
                detalle,
                dropped_by_no_sube_de_verdad=len(no_suben),
            )

        # 3. EL COLCHON, ACUMULADO
        #
        #     La foto, la mas fresca de la vuelta. Si en ella no se
        #     reconocen nuestras pujas vivas, el colchon saldria sin
        #     restarlas (mas grande de lo que es): no se puja a ciegas.
        fresca = isinstance(foto_del_colchon, dict) and bool(foto_del_colchon)
        foto = foto_del_colchon if fresca else snapshot
        detalle["foto"] = "POST_ACTION" if fresca else "LA_DE_LA_VUELTA"

        yo, ofertas = _yo_y_ofertas(foto)

        if yo is None or ofertas is None:
            return _cerrado(
                base, SIN_COLCHON,
                (
                    "La foto no deja ver nuestras pujas vivas (sin usuario "
                    "o sin las ofertas del mercado): el colchon saldria sin "
                    "restarlas y la cesta no puja a ciegas."
                ),
                detalle,
                dropped_by_no_sube_de_verdad=len(no_suben),
            )

        vistas = _nuestras(foto, yo)

        if fresca:
            yo_vuelta, _ = _yo_y_ofertas(snapshot)
            de_la_vuelta = _nuestras(snapshot, yo_vuelta) if yo_vuelta == yo else {}
            detalle["de_otra_foto"] = [
                {"id": pid, "amount": importe}
                for pid, importe in sorted(vistas.items())
                if importe > 0 and de_la_vuelta.get(pid) != importe
            ]

        # Lo que el libro apunta en esta ventana y la foto no trae va
        # delante de la primera.
        if pujas_desde is not None:
            if libro_de_pujas is None:
                from src.intelligence.bid_outcome_ledger import load_ledger

                libro_de_pujas = load_ledger()
            detalle["sin_foto"] = _las_del_libro(
                libro_de_pujas, pujas_desde, set(vistas)
            )

        sin_foto = sum(safe_int(f.get("amount")) for f in detalle["sin_foto"])
        texto_sin_foto = (
            f", contando {len(detalle['sin_foto'])} puja(s) del libro de "
            f"esta ventana que la foto aun no trae ({_euros(sin_foto)} EUR)"
            if sin_foto else ""
        )

        acumulado = 0
        colchon = None
        caben, fuera = [], []

        for puja in siguen:
            importe = safe_int(puja.get("bid"))

            mira = cabe_en_el_colchon(
                foto, puja.get("id"), sin_foto + acumulado + importe, libro_ruta
            )

            if not isinstance(mira, dict) or mira.get("colchon") is None:
                return _cerrado(
                    base, SIN_COLCHON,
                    (
                        "No se puede calcular el colchon de la casa (sin "
                        "saldo en la foto): la cesta no puja a ciegas."
                    ),
                    detalle,
                    dropped_by_no_sube_de_verdad=len(no_suben),
                )

            if colchon is None:
                colchon = int(mira["colchon"])

            if importe > 0 and mira.get("cabe") is True:
                caben.append(puja)
                acumulado += importe
                continue

            fuera.append({
                "id": safe_int(puja.get("id")),
                "name": puja.get("name"),
                "bid": importe,
                "acumulado": sin_foto + acumulado,
                "colchon": int(mira["colchon"]),
            })

        detalle.update({
            "colchon": colchon,
            "comprometido": acumulado,
            "caben": [safe_int(b.get("id")) for b in caben],
            "fuera": fuera,
        })

        texto_fuera = "; ".join(
            f"{f['name']} {_euros(f['bid'])}"
            + (f" (con {_euros(f['acumulado'])} delante)" if f["acumulado"] else "")
            for f in fuera
        )

        if not caben:
            return _cerrado(
                base, SIN_COLCHON,
                (
                    f"Ninguna puja cabe en el colchon de la casa "
                    f"({_euros(colchon)} EUR: saldo menos todas las pujas "
                    f"vivas mas el 92 % de lo de la cartera"
                    f"{texto_sin_foto}): {texto_fuera}. No se puja."
                ),
                detalle,
                dropped_by_colchon=len(fuera),
                dropped_by_no_sube_de_verdad=len(no_suben),
            )

        # 4. LAS CUENTAS, CON LO QUE QUEDA
        comprometido = sum(safe_int(b.get("bid")) for b in caben)

        esperado = int(
            sum(
                safe_float(b.get("expected_value"))
                * safe_float(b.get("win_odds"), 0.0)
                for b in caben
            )
        )

        si_todas = int(
            sum(safe_float(b.get("expected_value")) for b in caben)
        )

        ventana = base.get("window")
        ventana = ventana.get("reason") if isinstance(ventana, dict) else None

        reason = (
            f"{len(caben)} puja(s) por {_euros(comprometido)} EUR, "
            f"esperado {_euros(esperado)} EUR; caben en el colchon de la "
            f"casa ({_euros(colchon)} EUR{texto_sin_foto})."
            + (f" No caben: {texto_fuera}." if fuera else "")
            + (f" No suben de verdad: {texto_no_suben}." if no_suben else "")
            + (f" {ventana}" if ventana else "")
            + (
                " NO se ejecuta: falta el modo en vivo."
                if base.get("blocked_by") == "SIN_LIVE"
                else ""
            )
        )

        return {
            **base,
            "execute": bool(base.get("execute")) and bool(caben),
            "bids": caben,
            "committed": comprometido,
            "expected": esperado,
            "all_won": si_todas,
            "slots_used": len(caben),
            "worst_case": peor_caso({"elegidos": caben}, plantilla),
            "dropped_by_colchon": len(fuera),
            "dropped_by_no_sube_de_verdad": len(no_suben),
            "reason": reason,
            "en_el_colchon": detalle,
        }

    except Exception as error:                      # noqa: BLE001
        return _cerrado(
            base, SIN_COLCHON,
            (
                f"No se pudo mirar el colchon de la casa: "
                f"{type(error).__name__}: {error}. No se puja."
            ),
            detalle,
        )
