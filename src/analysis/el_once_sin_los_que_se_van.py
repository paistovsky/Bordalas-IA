"""
EL ONCE SIN LOS QUE SE VAN (27/10/2026)

LO QUE PASO (26/10/2026, J11)

    El once escrito en Biwenger llevaba a Jonny en vez de a Sergi
    Cardona. En el panel, los dos al 50 % en FutbolFantasy; Jonny
    'Importante' (27 puntos) y Cardona 'Rotacion' (22): 287.917 contra
    266.274 de `lineup_score`, y Cardona al banquillo con «puntua menos
    que Jonny».

    El motor no sabia tres cosas:

        a) que a Jonny lo estaba vendiendo la orden del gestor esa
           misma noche (`vender_si_ficha` con Kike Salas, su relevo,
           ganado el 25/10 a las 07:00; vendido el 27/10 a las 00:07);
        b) que Jornada Perfecta daba a Cardona de titular y a Jonny al
           40 % (SUPLENTE): con FF dando un numero, JP no pesa nada;
        c) que Cardona juega el partido que abre la ronda (su once se
           sabe antes de nuestro cierre).

    No costo nada porque la venta cayo cuatro dias antes del cierre y
    el once se reescribio. Pero una venta pegada al cierre deja en el
    once a uno que ya no es nuestro: cero puntos en ese hueco.

    Y el cierre de la jornada ya lo sabia: su once (`el_mejor_once`)
    deja fuera a los que se van (`se_van`). El once escrito y el del
    cierre no coincidian.

QUE HACE (con `BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN`)

    1. QUIEN SE VA ANTES DEL CIERRE NO SE ALINEA si hay otro DE FIAR
       que pueda jugar su hueco. Se va:

         - LA ORDEN: un `vender_si_ficha` que pasa las puertas de
           `decidir` -la condicion general o todos con su relevo, su
           relevo ya en la plantilla, `desde`, `si_saldo_negativo` y EL
           PARTE DEL RELEVO (el relevo 'ok' o 'warned' en el catalogo,
           salvo en rojo a menos de `HORAS_ROJO`)-; y un viaje en la
           plantilla.
         - LA MEJORA: el `sale` de un cambio vivo con el `entra` ya
           dentro y sano (su PARTE DEL RELEVO).
         - LA ROTACION: el que sale de una pareja GANADA.

       Y solo si se puede cobrar ANTES DEL CIERRE: ya tiene una oferta
       del Computer que llega a su suelo, o el proximo reset de las
       07:00 de Madrid -cuando nacen las ofertas- cae antes del cierre.
       Si no, a la hora del cierre sigue siendo nuestro y juega: el
       publicado la misma mañana en que llega su relevo no cobra hasta
       el reset siguiente. Sin saber cuando cierra, solo cuenta la
       oferta que ya esta.

       Una puja viva por el relevo NO cuenta: se resuelve en un reset y
       la venta necesita otro. Si caben los dos antes del cierre, tras
       el primero el relevo ya esta dentro y cuenta por la via de
       siempre; contarla antes solo metia vaivenes en el once (y en el
       `once` que lee la mejora).

       NUNCA SE SIENTA por venderse (`se_quedan` en el informe):

         - un Dios (`mandatory_hierarchy`) ni un intocable de la orden;
         - si la proxima ronda es de aplazados, uno de un equipo que la
           juega (o cualquiera, si no se sabe quien la juega, o si no se
           sabe si es de aplazados): el once se congela al empezar esa
           ronda, la rotacion no lo vende antes
           (`TITULAR_ANTES_DE_UNA_RONDA_PARCIAL`) y sentarlo le quitaria
           sus puntos y desarmaria esa guardia, que mira si esta en el
           once escrito.

       El inventario de la ronda y los chollos y los `vender` del cierre
       NO cuentan: el cierre adopta el inventario en su once y nunca
       vende a uno del once.

       COMO. Primero, la busqueda de siempre. Si su once no lleva a
       nadie que se va, es ese: nada cambia. Si lo lleva, se busca otra
       vez con `SE_VA` restado a los que se van: la busqueda maximiza
       primero cuantos huecos llena y luego el score, asi que el que se
       va solo entra si nadie mas puede llenar su hueco (el mismo truco
       que el suelo del que no tiene pronostico), y el dibujo cambia si
       hace falta. Ese once solo vale si TODOS los que entran respecto al
       de siempre son DE FIAR: alineables sin aviso (`automatic_lineup`),
       con pronostico de FF y con una titularidad de al menos
       `TITULARIDAD_HUECO` (la de la mejora) o a `MARGEN_FF` puntos o
       menos del que se va. Al que no lo es se le resta `NO_ENTRA` (mas
       que once `SE_VA`) y se busca otra vez, hasta `VUELTAS` veces; si
       no sale, el once de siempre. Antes juega el que se va que uno en
       duda, sin pronostico o al 0 %: si al final se queda, puntua; el
       otro, casi seguro que no. Y el once nunca lleva menos alineables
       sin aviso que el de siempre: un SAVE_LINEUP que hoy se escribe no
       pasa a quedarse bloqueado (`playable_count` < 11).

       Al salir, todas las fichas vuelven a sus numeros de verdad:
       ningun numero castigado sale del motor.

    2. JORNADA PERFECTA DESEMPATA. Si FF deja a dos del mismo puesto a
       `MARGEN_FF` puntos o menos de titularidad, y JP (de la jornada
       que toca y de menos de `HORAS_DE_JP`) dice que juega el de fuera
       (TITULAR o PROBABLE) y que el de dentro puede no jugar (DUDA,
       SUPLENTE o NO_CONVOCADO), se cambian. Un PROBABLE dentro no se
       toca: entre PROBABLE (84) y TITULAR (96) hay muy poco para
       ganarle a la calidad. El que entra, siempre alineable sin aviso;
       nunca se sienta a un Dios; nunca entra uno que se va. Cada uno se
       cambia una vez como mucho, y en su mismo puesto: el dibujo no se
       toca.

    El banquillo lo cuenta: SE_VA y DESEMPATE_JP en vez de un «puntua
    menos que Cardona» que seria falso. Y la salida trae el informe en
    `el_once_sin_los_que_se_van`.

DONDE MANDA, Y DONDE NO

    Solo en el once QUE SE ESCRIBE: `lineup_monitor` lo pide
    (`sin_los_que_se_van`), y de ahi beben SAVE_LINEUP, `live_lineup`,
    el panel, el `once_escrito` del cierre y el `once` de la mejora.
    Los que VALORAN (venta, liquidez, deuda segura, fichajes...) llaman
    a `build_lineup` sin el y ven el once de siempre, interruptor
    puesto o no. El mismo precedente que `con_calendario`.

    Lo (c), el once confirmado del que abre la ronda, se queda fuera:
    no es seguro (hace falta el once oficial a T-60 y escribir antes de
    T-15, y el tablero de FF vive 2 h sin mirar el cierre). Algo llega
    gratis: JP se refresca cada 10 minutos en las 2 ultimas horas, y
    su TITULAR del que abre ya entra en el desempate.

    Con una jornada jugandose (`en_curso`) la orden y la mejora no
    cobran, pero no hace falta mirarlo: el once que se escribe entonces
    es el de la ronda SIGUIENTE, y cobran en cuanto acaba esta, antes de
    ese cierre.

EL INTERRUPTOR

    `BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN`. Nace APAGADO: sin el, el
    once es el de hoy byte a byte (`test_el_once_sin_los_que_se_van_v1`).
    Nunca lanza: si algo falla, el once de hoy.
"""

from __future__ import annotations

import math
import os

from datetime import datetime, timedelta, timezone


ENV = "BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN"


# Lo que se le resta en la busqueda al que se va. Mas que el bono del
# Dios (10.000.000) mas cualquier score posible (~1.000.000): uno que
# se va solo llena un hueco que nadie mas puede llenar. Los que
# Biwenger no deja alinear (-1.000.000) ni entran en la busqueda, asi
# que nunca compite con ellos.
SE_VA = 100_000_000.0

# Lo que se le resta al que entraria por uno que se va sin ser de
# fiar: mas que once `SE_VA` (no hay mas de once que se van en un
# once). Antes juega el que se va que el.
NO_ENTRA = 12 * SE_VA

# Cuantas veces se vuelve a buscar quitando a los que no son de fiar.
# Cada vuelta quita al menos uno; si no basta, el once de siempre.
VUELTAS = 4

# Lo mas que FF puede separar a dos del mismo puesto para que desempate
# Jornada Perfecta, en puntos de titularidad. Y lo mas por debajo del
# que se va que puede estar el que entra por el (si no llega a
# `TITULARIDAD_HUECO`).
MARGEN_FF = 10.0

# Lo mas viejo que puede ser JP para desempatar: la misma frescura
# (>= 0,85) que exige el bloqueo de un NO_CONVOCADO
# (`lineup_intelligence.evaluate_lineup_signal`).
HORAS_DE_JP = 12.0

# El veredicto de JP, de mejor a peor. UNKNOWN o sin casar: no hay
# veredicto.
ORDEN_JP = {
    "TITULAR": 4,
    "PROBABLE": 3,
    "DUDA": 2,
    "SUPLENTE": 1,
    "NO_CONVOCADO": 0,
}

# Los que dicen que juega: solo estos entran por JP.
DICE_QUE_JUEGA = frozenset({"TITULAR", "PROBABLE"})

# Y el de dentro solo sale si JP dice que puede no jugar: DUDA o peor.
PUEDE_NO_JUGAR = ORDEN_JP["DUDA"]

# Los motivos del banquillo que se pueden reescribir con SE_VA: los
# que hablan de puntuar. Un lesionado o uno en duda se queda con su
# motivo, que es el primer corte que no paso.
REESCRIBIBLES = frozenset({"POSICION_CUBIERTA", "SIN_PRONOSTICO", "PUNTUA_MENOS"})

POR_LA_ORDEN = "LA_ORDEN_DEL_GESTOR"
POR_LA_MEJORA = "LA_MEJORA"
POR_LA_ROTACION = "LA_ROTACION"
DE_VIAJE = ": viaje"

# Por que uno que se esta vendiendo no se sienta (`se_quedan`).
NO_SE_COBRA_ANTES = "NO_SE_COBRA_ANTES_DEL_CIERRE"
UN_DIOS = "UN_DIOS"
JUEGA_LOS_APLAZADOS = "JUEGA_LA_RONDA_DE_APLAZADOS"
SIN_SABER_LAS_RONDAS = "SIN_SABER_SI_VIENE_UNA_RONDA_DE_APLAZADOS"


def activa() -> bool:
    """`BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN`, leido como los demas.
    Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {
            "1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError):
        return defecto


def _num(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        valor = float(x)
        return defecto if math.isnan(valor) else valor
    except (TypeError, ValueError):
        return defecto


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    return x if isinstance(x, list) else []


def _ids(x) -> set:
    """Los ids de un iterable (o de las claves de un dict). Nunca lanza."""
    try:
        if isinstance(x, dict):
            x = x.keys()
        if isinstance(x, (str, bytes)):
            return set()
        return {i for i in (_int(v) for v in (x or ())) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def _pid(ficha) -> int | None:
    if isinstance(ficha, dict):
        return _int(ficha.get("id"))
    return _int(ficha)


def _momento(ahora) -> datetime | None:
    """`ahora` como fecha con zona (UTC si viene sin ella), o None."""
    try:
        if isinstance(ahora, str):
            ahora = datetime.fromisoformat(ahora)
        if not isinstance(ahora, datetime):
            return None
        return ahora if ahora.tzinfo else ahora.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _estado(estados, pid) -> str:
    return str(_dict(estados).get(pid) or "").strip().lower()


def _apuntar(salida: dict, plantilla: set, pid, motivo: str, suelo) -> None:
    """`salida[pid][motivo] = suelo` (el mas bajo si se repite; None si
    no se sabe)."""
    pid = _int(pid)
    if pid is None or pid not in plantilla:
        return
    motivos = salida.setdefault(pid, {})
    suelo = _int(suelo)
    if motivo in motivos and motivos[motivo] is not None and suelo is not None:
        motivos[motivo] = min(motivos[motivo], suelo)
    elif motivo not in motivos:
        motivos[motivo] = suelo


# ============================================================
# 1. QUIEN SE VA
# ============================================================

def _relevo_sano(relevo, sale, estados, saldo, horas, *, sanos, horas_rojo,
                 fuera=frozenset()) -> bool:
    """
    EL PARTE DEL RELEVO, como lo mira `decidir` (la orden y la mejora):
    para cobrar al que sale, su relevo 'ok' o 'warned' en el catalogo,
    salvo en rojo a menos de `horas_rojo`. Y en rojo y cerca, con
    `fuera`, tampoco si el relevo no juega seguro y el que sale si (la
    orden). Sin `estados` (None), no se mira. Sin estado, no esta sano.
    """
    if estados is None:
        return True
    parte = _estado(estados, relevo) if relevo is not None else ""
    en_rojo_y_cerca = (
        saldo is not None and saldo < 0
        and horas is not None and horas < horas_rojo
    )
    if parte not in sanos and not en_rojo_y_cerca:
        return False
    if parte in fuera and _estado(estados, sale) not in fuera:
        return False
    return True


def _de_la_orden(salida, plantilla, orden, saldo, ahora, horas, estados) -> None:
    """La orden del gestor: `vender_si_ficha` (con las puertas de
    `decidir`, seccion 3) y los viajes (seccion 4). Solo viva:
    encendida, valida y sin caducar."""

    from src.actions import la_orden_del_gestor as orden_mod

    if ahora is None or not orden_mod.activa() or orden_mod.validar(orden, ahora) is not None:
        return

    intocables = orden_mod._intocables(orden)
    venta = _dict(orden.get("vender_si_ficha"))
    general = _int(venta.get("si_esta"))
    jugadores = _lista(venta.get("jugadores"))

    # LA PUERTA DE `decidir`: con `si_esta` general, que este; sin el,
    # todos tienen que traer su propio relevo (si falta uno, nadie).
    todos_con_relevo = bool(jugadores) and all(
        isinstance(j, dict) and _int(j.get("si_esta")) for j in jugadores)

    if (general and general in plantilla) or (not general and todos_con_relevo):
        for j in jugadores:
            if not isinstance(j, dict):
                continue
            pid = _int(j.get("player_id"))
            if pid not in plantilla:
                continue
            if str(j.get("nombre", "")).strip().lower() in intocables:
                continue
            # SU PROPIO RELEVO: dentro. Uno pujado no basta (ver la
            # cabecera: la puja no cuenta).
            relevo = _int(j.get("si_esta"))
            if relevo and relevo not in plantilla:
                continue
            desde = orden_mod._cuando(j.get("desde")) if j.get("desde") else None
            if desde is not None and ahora < desde:
                continue
            if j.get("si_saldo_negativo") and (saldo is None or saldo >= 0):
                continue
            # EL PARTE DEL RELEVO: no frena el ultimo recurso.
            if not j.get("si_saldo_negativo") and not _relevo_sano(
                relevo or general, pid, estados, saldo, horas,
                sanos=orden_mod.SANOS, horas_rojo=orden_mod.HORAS_ROJO,
                fuera=orden_mod.FUERA,
            ):
                continue
            _apuntar(salida, plantilla, pid, POR_LA_ORDEN, _int(j.get("suelo"), 0))

    # LOS VIAJES: el candidato que ya es nuestro se pone a la venta
    # siempre. Los mismos filtros y el mismo suelo que `decidir`.
    viajes = _dict(orden.get("viajes"))
    tope = _int(viajes.get("tope_por_viaje"), 0) or 0
    hasta = orden_mod._cuando(viajes.get("hasta")) if viajes.get("hasta") else None
    listo = 0.95 if (hasta is not None and ahora >= hasta) else 1.01
    for v in _lista(viajes.get("candidatos")):
        if not isinstance(v, dict):
            continue
        pid = _int(v.get("player_id"))
        puja = _int(v.get("puja"), 0) or 0
        if not pid or puja <= 0 or (tope and puja > tope):
            continue
        _apuntar(salida, plantilla, pid, POR_LA_ORDEN + DE_VIAJE, int(puja * listo))


def _de_la_mejora(salida, plantilla, libro, saldo, horas, estados) -> None:
    """La mejora del once: el `sale` de cada cambio vivo con el `entra`
    ya dentro y sano. Nunca el `entra`."""

    from src.actions import la_mejora_del_once as mejora_mod

    if not mejora_mod.activa():
        return

    for entra, cambio in _dict(libro).items():
        cambio = _dict(cambio)
        entra, sale = _int(entra), _int(cambio.get("sale"))
        if entra is None or sale is None or entra not in plantilla:
            continue
        if not _relevo_sano(entra, sale, estados, saldo, horas,
                            sanos=mejora_mod.SANOS, horas_rojo=mejora_mod.HORAS_ROJO):
            continue
        # El suelo de `decidir`: en rojo y cerca de la jornada, cualquiera.
        suelo = _int(cambio.get("suelo"), 0) or 0
        if (horas is not None and horas < mejora_mod.HORAS_SOLVENCIA
                and saldo is not None and saldo < 0):
            suelo = 0
        _apuntar(salida, plantilla, sale, POR_LA_MEJORA, suelo)


def _de_la_rotacion(salida, plantilla, parejas, precios) -> None:
    """La rotacion: `las_parejas_abiertas()` (vacia si esta apagada).
    Se va el que sale de una GANADA: su relevo ya esta dentro. Su suelo,
    el que acepta sin prisa (`ACEPTA` de su valor)."""

    from src.actions.la_rotacion import ACEPTA

    for pid in sorted(_ids(_dict(parejas).get("se_van"))):
        precio = _int(_dict(precios).get(pid))
        suelo = math.ceil(precio * ACEPTA) if precio else None
        _apuntar(salida, plantilla, pid, POR_LA_ROTACION, suelo)


def _el_proximo_reset(ahora) -> datetime | None:
    """El proximo reset de las 07:00 de Madrid (cuando nacen las ofertas
    del Computer y se resuelven las pujas), en UTC. None si falla."""
    try:
        from src.actions.la_rotacion import los_resets

        return los_resets(ahora)[1]
    except Exception:                               # noqa: BLE001
        return None


def se_cobra_antes_del_cierre(oferta, suelo, ahora, segundos_al_cierre) -> bool:
    """
    Si al que se vende se le puede cobrar antes del cierre: ya tiene una
    oferta del Computer que llega a su `suelo`, o el proximo reset de
    las 07:00 de Madrid (cuando nacen las ofertas) cae antes del cierre.
    Sin saber cuando cierra, solo la oferta. Pura, nunca lanza.
    """
    try:
        oferta, suelo = _int(oferta), _int(suelo)
        if oferta is not None and suelo is not None and oferta >= suelo:
            return True
        ahora, segundos = _momento(ahora), _num(segundos_al_cierre)
        if ahora is None or segundos is None:
            return False
        proximo = _el_proximo_reset(ahora)
        return proximo is not None and proximo < ahora + timedelta(seconds=segundos)
    except Exception:                               # noqa: BLE001
        return False


def _quien_se_va(
    plantilla,
    *,
    orden=None,
    libro_mejora=None,
    parejas=None,
    saldo=None,
    ahora=None,
    segundos_al_cierre=None,
    estados=None,
    ofertas=None,
    precios=None,
) -> tuple:
    """`(se_van, no_llegan)`: `{id: [motivos]}` de los que se van antes
    del cierre, y de los que se estan vendiendo pero no se cobran antes.
    Ver `los_que_se_van`. Nunca lanza."""

    candidatos: dict = {}

    try:
        plantilla = _ids(plantilla)
        saldo = _int(saldo)
        ahora = _momento(ahora)
        segundos = _num(segundos_al_cierre)
        horas = None if segundos is None else segundos / 3600.0
        estados = None if estados is None else {
            _int(k): v for k, v in _dict(estados).items() if _int(k) is not None}

        # Cada libro por su lado: uno roto no se lleva a los demas.
        for paso in (
            lambda: _de_la_orden(candidatos, plantilla, _dict(orden), saldo, ahora,
                                 horas, estados) if isinstance(orden, dict) else None,
            lambda: _de_la_mejora(candidatos, plantilla, libro_mejora, saldo, horas, estados),
            lambda: _de_la_rotacion(candidatos, plantilla, parejas, precios),
        ):
            try:
                paso()
            except Exception:                       # noqa: BLE001
                continue

        ofertas = {_int(k): v for k, v in _dict(ofertas).items() if _int(k) is not None}
        se_van, no_llegan = {}, {}

        for pid, motivos in candidatos.items():
            suelos = [s for s in motivos.values() if s is not None]
            oferta = _dict(ofertas.get(pid)).get("amount")
            if se_cobra_antes_del_cierre(oferta, min(suelos) if suelos else None,
                                         ahora, segundos):
                se_van[pid] = list(motivos)
            else:
                no_llegan[pid] = list(motivos)

        return se_van, no_llegan

    except Exception:                               # noqa: BLE001
        return {}, {}


def los_que_se_van(
    plantilla,
    *,
    orden=None,
    libro_mejora=None,
    parejas=None,
    saldo=None,
    ahora=None,
    segundos_al_cierre=None,
    estados=None,
    ofertas=None,
    precios=None,
) -> dict:
    """
    `{player_id: [motivos]}` de los de la plantilla que se estan
    vendiendo y se pueden cobrar antes del cierre. Pura: ni disco, ni
    red, ni reloj. Nunca lanza.

        plantilla           {id} de los nuestros
        orden               la orden del gestor (`leer_la_orden`)
        libro_mejora        el libro de la mejora ({entra: {sale, suelo}})
        parejas             `la_rotacion.las_parejas_abiertas()`
        saldo               el saldo de la foto (`si_saldo_negativo`, y
                            en rojo y cerca para EL PARTE DEL RELEVO)
        ahora               la hora (sin ella, la orden no cuenta: no se
                            sabe si caduco)
        segundos_al_cierre  hasta el cierre de la jornada (T-15); sin el,
                            solo se va el que ya tiene oferta a su suelo
        estados             {id: status} del catalogo (EL PARTE DEL
                            RELEVO); None, no se mira
        ofertas             {id: {amount}} del Computer (`leer_la_foto`)
        precios             {id: precio} (el suelo de la rotacion)

    El 26/10: la orden vende a Jonny (1599) cuando esta Kike Salas
    (28115), Kike ya es nuestro y sano, y quedan cuatro dias al cierre
    -> {1599: ['LA_ORDEN_DEL_GESTOR']}.
    """

    return _quien_se_va(
        plantilla, orden=orden, libro_mejora=libro_mejora, parejas=parejas,
        saldo=saldo, ahora=ahora, segundos_al_cierre=segundos_al_cierre,
        estados=estados, ofertas=ofertas, precios=precios,
    )[0]


def _nombrados(plantilla, libros) -> set:
    """Los de la plantilla que nombra algun libro, sin mirar ninguna
    puerta: si no hay ninguno, el reloj no hace falta. Nunca lanza."""
    try:
        libros = _dict(libros)
        orden = _dict(libros.get("orden"))
        nombres = set()
        for j in _lista(_dict(orden.get("vender_si_ficha")).get("jugadores")):
            nombres |= _ids([_dict(j).get("player_id")])
        for v in _lista(_dict(orden.get("viajes")).get("candidatos")):
            nombres |= _ids([_dict(v).get("player_id")])
        for cambio in _dict(libros.get("mejora")).values():
            nombres |= _ids([_dict(cambio).get("sale")])
        nombres |= _ids(_dict(libros.get("parejas")).get("se_van"))
        return nombres & _ids(plantilla)
    except Exception:                               # noqa: BLE001
        return set()


# ============================================================
# 2. LOS QUE NUNCA SE SIENTAN POR VENDERSE
# ============================================================

def los_que_no_se_sientan(players, se_van, rondas, equipos) -> dict:
    """
    `{id: motivo}` de los de `se_van` que juegan igual (cabecera, punto
    1): un Dios o un intocable (`UN_DIOS`); y, si la proxima ronda es de
    aplazados (`rondas`, el de `la_rotacion.el_reloj`), el de un equipo
    que la juega (`JUEGA_LOS_APLAZADOS`), o cualquiera si no se sabe
    quien la juega o si no se sabe si viene una
    (`SIN_SABER_LAS_RONDAS`). `equipos`, {teamID: nombre} del catalogo.
    Pura, nunca lanza: si algo falla, todos.
    """

    se_van = _ids(se_van)

    try:
        from src.actions.la_orden_del_gestor import INTOCABLES
        from src.analysis.el_calendario_de_puntos import clave_de_equipo

        fichas = {_pid(p): p for p in (players or []) if isinstance(p, dict)}
        salida = {}

        for pid in se_van:
            ficha = _dict(fichas.get(pid))
            nombre = str(ficha.get("name") or "").strip().lower()
            if ficha.get("mandatory_hierarchy") or any(t in nombre for t in INTOCABLES):
                salida[pid] = UN_DIOS

        resto = sorted(se_van - set(salida))
        if not resto:
            return salida

        rondas = _dict(rondas)
        if rondas.get("sin_calendario", True):
            return {**salida, **{pid: SIN_SABER_LAS_RONDAS for pid in resto}}

        if not rondas.get("ronda_parcial"):
            return salida

        claves = rondas.get("equipos_parcial")
        claves = ({str(c) for c in claves}
                  if isinstance(claves, (list, tuple, set, frozenset)) else set())
        nombres = {_int(k): v for k, v in _dict(equipos).items() if _int(k) is not None}

        for pid in resto:
            equipo = _int(_dict(fichas.get(pid)).get("teamID"))
            clave = clave_de_equipo(nombres.get(equipo)) if nombres.get(equipo) else None
            if not claves or clave is None or clave in claves:
                salida[pid] = JUEGA_LOS_APLAZADOS

        return salida

    except Exception:                               # noqa: BLE001
        return {pid: SIN_SABER_LAS_RONDAS for pid in se_van}


# ============================================================
# 3. JORNADA PERFECTA, SI VALE
# ============================================================

def jp_vale(lineup_intelligence, ronda) -> tuple:
    """
    `(vale, motivo)`: si Jornada Perfecta puede desempatar. Solo si
    esta disponible, es de la jornada que toca (`ronda`, la
    `target_matchday` del calendario) y tiene `HORAS_DE_JP` o menos.
    Cualquier duda: no vale. Pura, nunca lanza.
    """

    try:
        jp = _dict(lineup_intelligence)

        if not jp.get("available"):
            return False, "Jornada Perfecta no esta disponible"

        suya, toca = _int(jp.get("round")), _int(ronda)

        if suya is None or toca is None:
            return False, f"no se sabe la jornada (JP {jp.get('round')}, toca {ronda})"

        if suya != toca:
            return False, f"Jornada Perfecta es de la jornada {suya} y toca la {toca}"

        edad = _num(jp.get("age_hours"))

        if edad is None:
            return False, "no se sabe cuando se actualizo Jornada Perfecta"

        if edad > HORAS_DE_JP:
            return False, (
                f"Jornada Perfecta tiene {edad:.1f} h (mas de {HORAS_DE_JP:g})")

        return True, f"Jornada Perfecta de la jornada {suya}, de hace {edad:.1f} h"

    except Exception:                               # noqa: BLE001
        return False, "Jornada Perfecta ilegible"


def _veredicto(ficha) -> str | None:
    """El veredicto de JP de una ficha del motor, o None si no lo hay."""
    externo = _dict(_dict(ficha).get("external_lineup"))
    estado = str(externo.get("status") or "").strip().upper()
    if externo.get("matched") is not True or estado not in ORDEN_JP:
        return None
    return estado


# ============================================================
# 4. LA BUSQUEDA Y EL REMATE
# ============================================================

def para_la_busqueda(players, se_van, no_entran=()) -> list:
    """
    La lista que ve la busqueda: la misma, con `SE_VA` restado al
    `lineup_score` de los que se van y `NO_ENTRA` al de los que no son
    de fiar para entrar por ellos (una copia de su ficha; las demas, tal
    cual). Como la entrada es otra, `el_once_se_busca_una_vez` no la
    confunde con la de los que valoran.
    """

    se_van, no_entran = _ids(se_van), _ids(no_entran)

    def _castigo(pid):
        return (SE_VA if pid in se_van else 0.0) + (NO_ENTRA if pid in no_entran else 0.0)

    return [
        {**p, "lineup_score": float(p.get("lineup_score") or 0.0) - _castigo(_pid(p))}
        if _pid(p) in se_van or _pid(p) in no_entran
        else p
        for p in players
    ]


def el_liston(fuera) -> float:
    """
    La titularidad de FF minima del que entra por los que se van
    (`fuera`, sus fichas): `TITULARIDAD_HUECO` (la de la mejora: por
    debajo, es un hueco) o `MARGEN_FF` por debajo del que se va, lo que
    sea menos. Si uno de ellos no tiene pronostico, cualquiera con
    pronostico. Nunca lanza.
    """

    try:
        from src.actions.la_mejora_del_once import TITULARIDAD_HUECO

        liston = float(TITULARIDAD_HUECO)
    except Exception:                               # noqa: BLE001
        liston = 50.0

    for ficha in fuera or ():
        ff = _num(_dict(ficha).get("starter_probability"))
        if ff is None:
            return float("-inf")
        liston = min(liston, ff - MARGEN_FF)

    return liston


def de_fiar(ficha, liston) -> bool:
    """Si puede entrar por uno que se va: alineable sin aviso, con
    pronostico de FF y con al menos `liston`. Nunca lanza."""
    ficha = _dict(ficha)
    ff = _num(ficha.get("starter_probability"))
    return bool(
        ficha.get("lineup_eligible")
        and ficha.get("automatic_lineup")
        and ff is not None
        and ff >= liston
    )


def elegir(preparado, players, candidatas, buscar) -> tuple:
    """
    `(candidatas, notas)`. `candidatas`, las de la busqueda de siempre
    (de mejor a peor: la primera es el once); `buscar(lista)`, la misma
    busqueda sobre otra lista (`lineup_engine._todas_las_formaciones`).

    Si el once de siempre no lleva a nadie que se va, el mismo. Si lo
    lleva, se busca sin ellos y solo vale si todos los que entran son de
    fiar (cabecera, punto 1, COMO). Si no sale en `VUELTAS`, el de
    siempre. Las candidatas que salen pueden traer numeros castigados:
    `rematar` y `sin_castigo` los devuelven a los de verdad.

    `notas`: {no_entran: [ids], al_de_siempre, vueltas}. Nunca lanza:
    si algo falla, las de siempre.
    """

    notas = {"no_entran": [], "al_de_siempre": False, "vueltas": 0}

    try:
        se_van = _ids(_dict(preparado).get("se_van"))
        players = [p for p in (players or []) if isinstance(p, dict)]

        if not se_van or not candidatas:
            return candidatas, notas

        de_siempre = _lista(_dict(candidatas[0]).get("selected"))
        dentro = {_pid(c) for c in de_siempre}
        fuera = [c for c in de_siempre if _pid(c) in se_van]

        if not fuera:
            return candidatas, notas

        fichas = {_pid(p): p for p in players}
        liston = el_liston(fuera)
        no_entran: set = set()

        for vuelta in range(1, VUELTAS + 1):
            notas["vueltas"] = vuelta
            otras = buscar(para_la_busqueda(players, se_van, no_entran))
            if not otras:
                break
            nuevos = {_pid(c) for c in _lista(_dict(otras[0]).get("selected"))} - dentro
            malos = {
                n for n in nuevos
                if n in se_van or not de_fiar(fichas.get(n), liston)
            }
            if not malos:
                notas["no_entran"] = sorted(no_entran)
                return otras, notas
            if malos <= no_entran:
                break
            no_entran |= malos

        notas["no_entran"] = sorted(no_entran)
        notas["al_de_siempre"] = True
        return candidatas, notas

    except Exception:                               # noqa: BLE001
        return candidatas, {"no_entran": [], "al_de_siempre": True, "vueltas": 0}


def _restaurar(players, selected) -> list:
    """Cada ficha elegida, con sus numeros de verdad y su puesto."""

    originales = {_pid(p): p for p in players}

    return [
        {**originales[_pid(c)], "lineup_position": c.get("lineup_position")}
        if _pid(c) in originales
        else c
        for c in selected
    ]


def _desempatar(once, players, se_van) -> tuple:
    """
    El desempate de JP sobre el once ya restaurado. Devuelve `(once,
    desempates)`. Ver la cabecera, punto 2.
    """

    dentro = {_pid(c) for c in once}

    def _rango(ficha):
        estado = _veredicto(ficha)
        return None if estado is None else ORDEN_JP[estado]

    def _ff(ficha):
        return _num(ficha.get("starter_probability"))

    # El que entra, siempre alineable sin aviso: nunca baja la cuenta de
    # los que Biwenger deja alinear sin duda.
    candidatos = [
        o for o in players
        if _pid(o) not in dentro
        and o.get("lineup_eligible")
        and o.get("automatic_lineup")
        and _pid(o) not in se_van
        and _ff(o) is not None
        and _veredicto(o) in DICE_QUE_JUEGA
    ]

    candidatos.sort(
        key=lambda o: (-_rango(o), -float(o.get("lineup_score") or 0.0)))

    tocados: set = set()
    desempates = []
    once = list(once)

    for fuera in candidatos:

        puestos = set(fuera.get("eligible_positions") or [])

        opciones = [
            (indice, s)
            for indice, s in enumerate(once)
            if _pid(s) not in tocados
            and not s.get("mandatory_hierarchy")
            and _ff(s) is not None
            and _rango(s) is not None
            and _rango(s) <= PUEDE_NO_JUGAR
            and _rango(s) < _rango(fuera)
            and abs(_ff(s) - _ff(fuera)) <= MARGEN_FF
            and s.get("lineup_position") in puestos
        ]

        if not opciones:
            continue

        indice, sale = min(
            opciones,
            key=lambda par: (_rango(par[1]), float(par[1].get("lineup_score") or 0.0)),
        )

        once[indice] = {**fuera, "lineup_position": sale.get("lineup_position")}
        tocados |= {_pid(sale), _pid(fuera)}

        desempates.append({
            "entra": _pid(fuera),
            "entra_nombre": fuera.get("name"),
            "sale": _pid(sale),
            "sale_nombre": sale.get("name"),
            "ff": [_ff(fuera), _ff(sale)],
            "jp": [_veredicto(fuera), _veredicto(sale)],
        })

    return once, desempates


def rematar(preparado, players, selected, notas=None) -> tuple:
    """
    `(once, informe)` tras la busqueda (y `elegir`):

        1. cada ficha elegida vuelve a sus numeros de verdad (los de
           `players`), con su `lineup_position`;
        2. si JP vale, el desempate (cabecera, punto 2).

    El informe: `{"se_van": [{id, name, por, en_el_once}], "se_quedan":
    [{id, name, por, motivo}], "no_entran": [{id, name}],
    "al_de_siempre", "desempates": [{entra, entra_nombre, sale,
    sale_nombre, ff, jp}], "jp": {vale, motivo, ronda, edad_horas,
    jornada}}`. Con basura, devuelve lo que le llego y un informe vacio.
    Nunca lanza.
    """

    informe = {"se_van": [], "se_quedan": [], "no_entran": [], "al_de_siempre": False,
               "desempates": [], "jp": {}}

    if not isinstance(selected, list):
        return selected, informe

    try:
        preparado = _dict(preparado)
        players = [p for p in (players or []) if isinstance(p, dict)]
        once = _restaurar(players, selected)
    except Exception:                               # noqa: BLE001
        return selected, informe

    try:
        por = _dict(preparado.get("se_van"))
        se_van = set(por)
        notas = _dict(notas)
        informe["jp"] = dict(_dict(preparado.get("jp")))
        informe["al_de_siempre"] = bool(notas.get("al_de_siempre"))

        if informe["jp"].get("vale"):
            try:
                once, informe["desempates"] = _desempatar(once, players, se_van)
            except Exception:                       # noqa: BLE001
                informe["desempates"] = []

        dentro = {_pid(c) for c in once}
        fichas = {_pid(p): p for p in players}

        informe["se_van"] = [
            {
                "id": _pid(p),
                "name": p.get("name"),
                "por": list(por[_pid(p)]),
                "en_el_once": _pid(p) in dentro,
            }
            for p in players
            if _pid(p) in se_van
        ]

        quedan = _dict(preparado.get("se_quedan"))
        informe["se_quedan"] = [
            {
                "id": _pid(p),
                "name": p.get("name"),
                "por": list(_dict(quedan[_pid(p)]).get("por") or []),
                "motivo": _dict(quedan[_pid(p)]).get("motivo"),
            }
            for p in players
            if _pid(p) in quedan
        ]

        informe["no_entran"] = [
            {"id": pid, "name": _dict(fichas.get(pid)).get("name")}
            for pid in _lista(notas.get("no_entran"))
        ]

    except Exception:                               # noqa: BLE001
        pass

    return once, informe


def con_motivo(bench, informe) -> list:
    """
    El banquillo con el motivo de verdad para el que se va (SE_VA) y
    para el que pierde el desempate (DESEMPATE_JP). Las demas filas, tal
    cual. Con basura, devuelve lo que le llego. Nunca lanza.
    """

    if not isinstance(bench, list):
        return bench

    try:
        informe = _dict(informe)

        se_van = {
            e["id"]: e for e in _lista(informe.get("se_van"))
            if isinstance(e, dict) and not e.get("en_el_once")
        }

        pierden = {
            d["sale"]: d for d in _lista(informe.get("desempates"))
            if isinstance(d, dict)
        }

        if not se_van and not pierden:
            return bench

        salida = []

        for fila in bench:

            if not isinstance(fila, dict):
                salida.append(fila)
                continue

            pid = _pid(fila)

            if pid in pierden:
                d = pierden[pid]
                ff_entra, ff_sale = (d.get("ff") or [None, None])[:2]
                jp_entra, jp_sale = (d.get("jp") or [None, None])[:2]
                fila = {
                    **fila,
                    "reason": "DESEMPATE_JP",
                    "reason_text": (
                        f"FF los deja a {MARGEN_FF:g} puntos o menos "
                        f"({_por_ciento(ff_sale)} y {_por_ciento(ff_entra)}) "
                        f"y Jornada Perfecta da titular a "
                        f"{d.get('entra_nombre') or 'el otro'} ({jp_entra}); "
                        f"a el, {jp_sale}"
                    ),
                }

            elif pid in se_van and fila.get("reason") in REESCRIBIBLES:
                motivos = ", ".join(se_van[pid].get("por") or [])
                fila = {
                    **fila,
                    "reason": "SE_VA",
                    "reason_text": (
                        f"se vende antes del cierre ({motivos}) y hay otro "
                        "de fiar que puede jugar: no se alinea"
                    ),
                }

            salida.append(fila)

        return salida

    except Exception:                               # noqa: BLE001
        return bench


def _por_ciento(x) -> str:
    valor = _num(x)
    return "?" if valor is None else f"{valor:g} %"


def sin_castigo(formation_results, players) -> list:
    """
    Las candidatas de la busqueda (`formation_candidates`) con sus
    numeros de verdad: cada ficha restaurada y su `score` rehecho. La
    eleccion de cada dibujo es la de la busqueda. Con basura, lo que
    le llego. Nunca lanza.
    """

    try:
        players = [p for p in (players or []) if isinstance(p, dict)]
        salida = []

        for resultado in formation_results:
            elegidas = _restaurar(players, resultado.get("selected") or [])
            salida.append({
                **resultado,
                "selected": elegidas,
                "score": sum(float(c.get("lineup_score") or 0.0) for c in elegidas),
            })

        return salida

    except Exception:                               # noqa: BLE001
        return formation_results


# ============================================================
# 5. EL ENGANCHE: LO QUE LEE EN PRODUCCION
# ============================================================

def _ahora() -> datetime:
    """La hora del sistema, en UTC. Las guardias la suplantan."""

    return datetime.now(timezone.utc)


def _el_reloj(snapshot) -> dict:
    """La jornada que toca y lo que falta para su cierre: el estado del
    calendario que la vuelta ya monta dentro de
    `build_lineup_intelligence`."""

    from src.analysis.calendar_state import build_calendar_state

    return build_calendar_state(snapshot)


def _las_rondas(ahora) -> dict:
    """Si la proxima ronda es de aplazados y que equipos la juegan: el
    reloj de la rotacion (`la_rotacion.el_reloj`, del calendario de
    `la_proxima_jornada`)."""

    from src.actions.la_rotacion import el_reloj

    return el_reloj(ahora)


def _libros_de_produccion() -> dict:
    """La orden, el libro de la mejora y las parejas de la rotacion,
    de sus ficheros de siempre. Cada uno solo con su interruptor."""

    import json

    from pathlib import Path

    from src.actions import la_mejora_del_once as mejora_mod
    from src.actions import la_orden_del_gestor as orden_mod
    from src.actions.la_rotacion import las_parejas_abiertas

    orden = orden_mod.leer_la_orden() if orden_mod.activa() else None

    mejora = {}
    if mejora_mod.activa():
        try:
            mejora = json.loads(Path(mejora_mod.LIBRO).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            mejora = {}

    return {"orden": orden, "mejora": mejora, "parejas": las_parejas_abiertas()}


def preparar(
    snapshot,
    players,
    lineup_intelligence,
    *,
    ahora=None,
    libros=None,
    reloj=None,
    rondas=None,
) -> dict | None:
    """
    Lo que necesitan `elegir` y `rematar` en el once que se escribe, o
    None.

        se_van      {id: [motivos]} (`los_que_se_van`, sin los que no se
                    sientan)
        se_quedan   {id: {por, motivo}}: se estan vendiendo y juegan
                    igual (no se cobran antes del cierre, un Dios, la
                    ronda de aplazados)
        jp          {vale, motivo, ronda, edad_horas, jornada}

    La plantilla sale de `players`; las ofertas del Computer y el saldo,
    de la foto (`la_orden_del_gestor.leer_la_foto`); los estados, de su
    catalogo (`leer_los_estados`: sin catalogo, ningun relevo esta sano,
    como en `decidir`); la jornada y el cierre, de `reloj` o del
    calendario de la vuelta (este, solo si algun libro nombra a uno de
    la plantilla o JP esta disponible: si no, no cambia nada); la ronda
    de aplazados, de `rondas` o del reloj de la rotacion (solo si alguien
    se va); los libros, de `libros` o de produccion. `ahora`, de la hora
    del sistema si no se pasa.

    None -y entonces el once de hoy, byte a byte- con el interruptor
    apagado, si algo falla, o si no hay nada que hacer: nadie se va y
    JP no vale (aunque alguno se este vendiendo y se quede: el once es
    el de siempre). Nunca lanza.
    """

    try:
        if not activa():
            return None

        from src.actions import la_orden_del_gestor as orden_mod

        players = [p for p in (players or []) if isinstance(p, dict)]
        plantilla = {_pid(p) for p in players if _pid(p) is not None}
        precios = {_pid(p): p.get("price") for p in players if _pid(p) is not None}

        foto = _dict(snapshot)
        yo = _pid(_dict(foto.get("league")).get("user"))
        de_la_foto = _dict(orden_mod.leer_la_foto(foto, yo))
        ofertas = _dict(de_la_foto.get("ofertas_del_computer"))
        saldo = de_la_foto.get("saldo")
        estados = orden_mod.leer_los_estados(foto)

        libros = _dict(libros if libros is not None else _libros_de_produccion())
        intel = _dict(lineup_intelligence)

        # EL RELOJ, SOLO SI ALGO LO NECESITA. Lo leen los que se venden
        # (¿se cobran antes del cierre?) y JP (¿es de la jornada que
        # toca?). Sin ninguno de los dos, el reloj no cambia nada y no
        # se pregunta al calendario. Roto, no se sabe: solo cuenta la
        # oferta que ya esta, y JP no vale.
        if reloj is None and (_nombrados(plantilla, libros) or intel.get("available")):
            try:
                reloj = _el_reloj(snapshot)
            except Exception:                       # noqa: BLE001
                reloj = {}

        reloj = _dict(reloj)
        ronda = reloj.get("target_matchday")
        segundos = reloj.get("seconds_to_deadline")

        momento = _momento(ahora) if ahora is not None else _ahora()

        se_van, no_llegan = _quien_se_va(
            plantilla,
            orden=libros.get("orden"),
            libro_mejora=libros.get("mejora"),
            parejas=libros.get("parejas"),
            saldo=saldo,
            ahora=momento,
            segundos_al_cierre=segundos,
            estados=estados,
            ofertas=ofertas,
            precios=precios,
        )

        se_quedan = {
            pid: {"por": motivos, "motivo": NO_SE_COBRA_ANTES}
            for pid, motivos in no_llegan.items()
        }

        # LOS QUE NUNCA SE SIENTAN: un Dios y el de la ronda de
        # aplazados. La ronda, solo si alguien se va.
        if se_van:
            if rondas is None:
                try:
                    rondas = _las_rondas(momento)
                except Exception:                   # noqa: BLE001
                    rondas = {"sin_calendario": True}
            equipos = {
                k: _dict(v).get("name")
                for k, v in _dict(_dict(_dict(foto.get("catalog")).get("data")).get(
                    "teams")).items()
            }
            for pid, motivo in los_que_no_se_sientan(players, se_van, rondas, equipos).items():
                se_quedan[pid] = {"por": se_van.pop(pid), "motivo": motivo}

        vale, motivo = jp_vale(lineup_intelligence, ronda)

        if not se_van and not vale:
            return None

        return {
            "se_van": se_van,
            "se_quedan": se_quedan,
            "jp": {
                "vale": vale,
                "motivo": motivo,
                "ronda": intel.get("round"),
                "edad_horas": intel.get("age_hours"),
                "jornada": ronda,
            },
            "segundos_al_cierre": segundos,
        }

    except Exception:                               # noqa: BLE001
        return None
