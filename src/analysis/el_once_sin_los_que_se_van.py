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

    1. QUIEN SE VA NO SE ALINEA si hay otro que pueda jugar. Se va:

         - LA ORDEN: un `vender_si_ficha` que pasa la puerta de
           `decidir` (la condicion general o todos con su relevo), con
           su relevo ya en la plantilla, o con puja viva nuestra que se
           resuelve antes del cierre; y un viaje en la plantilla.
         - LA MEJORA: el `sale` de un cambio vivo con el `entra` ya
           dentro, o con puja viva que se resuelve antes del cierre.
         - LA ROTACION: el que sale de una pareja GANADA, o de una
           PUJADA que se resuelve antes del cierre.

       Una puja se resuelve en el reset de las 07:00 de Madrid (25 h el
       dia del cambio de hora): con menos de `HORAS_DE_UNA_PUJA` hasta
       el cierre no sienta a nadie. El inventario de la ronda y los
       chollos y los `vender` del cierre NO cuentan: el cierre adopta
       el inventario en su once y nunca vende a uno del once.

       Como: en la busqueda, el que se va lleva `SE_VA` restado. La
       busqueda maximiza primero cuantos huecos llena y luego el score,
       asi que solo entra si nadie mas puede llenar su hueco (el mismo
       truco que el suelo del que no tiene pronostico). Al salir, todas
       las fichas vuelven a sus numeros de verdad: ningun numero
       castigado sale del motor.

    2. JORNADA PERFECTA DESEMPATA. Si FF deja a dos del mismo puesto a
       `MARGEN_FF` puntos o menos de titularidad, y JP (de la jornada
       que toca y de menos de `HORAS_DE_JP`) dice que juega el de fuera
       (TITULAR o PROBABLE) y da peor veredicto al de dentro, se
       cambian. Nunca se sienta a un Dios; nunca entra uno que se va.
       Cada uno se cambia una vez como mucho, y en su mismo puesto: el
       dibujo no se toca.

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

EL INTERRUPTOR

    `BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN`. Nace APAGADO: sin el, el
    once es el de hoy byte a byte (`test_el_once_sin_los_que_se_van_v1`).
    Nunca lanza: si algo falla, el once de hoy.
"""

from __future__ import annotations

import os

from datetime import datetime, timezone


ENV = "BORDALAS_EL_ONCE_SIN_LOS_QUE_SE_VAN"


# Lo que se le resta en la busqueda al que se va. Mas que el bono del
# Dios (10.000.000) mas cualquier score posible (~1.000.000): uno que
# se va solo llena un hueco que nadie mas puede llenar. Los que
# Biwenger no deja alinear (-1.000.000) ni entran en la busqueda, asi
# que nunca compite con ellos.
SE_VA = 100_000_000.0

# Una puja se resuelve en el siguiente reset de las 07:00 de Madrid:
# como mucho 24 h, 25 el dia del cambio de hora. Con menos hasta el
# cierre, puede no resolverse a tiempo: no sienta a nadie.
HORAS_DE_UNA_PUJA = 25

# Lo mas que FF puede separar a dos del mismo puesto para que desempate
# Jornada Perfecta, en puntos de titularidad.
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

# Los motivos del banquillo que se pueden reescribir con SE_VA: los
# que hablan de puntuar. Un lesionado o uno en duda se queda con su
# motivo, que es el primer corte que no paso.
REESCRIBIBLES = frozenset({"POSICION_CUBIERTA", "SIN_PRONOSTICO", "PUNTUA_MENOS"})

POR_LA_ORDEN = "LA_ORDEN_DEL_GESTOR"
POR_LA_MEJORA = "LA_MEJORA"
POR_LA_ROTACION = "LA_ROTACION"
CON_PUJA = ": relevo pujado"
DE_VIAJE = ": viaje"


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
        return float(x)
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


def _apuntar(salida: dict, plantilla: set, pid, motivo: str) -> None:
    pid = _int(pid)
    if pid is None or pid not in plantilla:
        return
    motivos = salida.setdefault(pid, [])
    if motivo not in motivos:
        motivos.append(motivo)


# ============================================================
# 1. QUIEN SE VA
# ============================================================

def _de_la_orden(salida, plantilla, orden, pujas, saldo, ahora, puja_cuenta) -> None:
    """La orden del gestor: `vender_si_ficha` (con la puerta de
    `decidir`) y los viajes. Solo viva: encendida, valida y sin
    caducar."""

    from src.actions import la_orden_del_gestor as orden_mod
    from src.actions.la_mejora_del_once import las_ventas_de_la_orden

    if ahora is None or not orden_mod.activa() or orden_mod.validar(orden, ahora) is not None:
        return

    intocables = orden_mod._intocables(orden)
    venta = _dict(orden.get("vender_si_ficha"))
    general = _int(venta.get("si_esta"))
    jugadores = _lista(venta.get("jugadores"))

    # LA PUERTA DE `decidir` (seccion 3): sin `si_esta` general, todos
    # tienen que traer su propio relevo; si falta uno, no vende a nadie.
    todos_con_relevo = bool(jugadores) and all(
        isinstance(j, dict) and _int(j.get("si_esta")) for j in jugadores)

    if general or todos_con_relevo:
        # Los que siguen en pie: su relevo (el general y el suyo) esta
        # dentro o tiene puja viva nuestra. Sin `mercado`: uno que solo
        # sigue en el mercado del Computer no se va todavia.
        for j in las_ventas_de_la_orden(orden, plantilla=plantilla, pujadas=pujas):
            pid = _int(j.get("player_id"))
            if pid not in plantilla:
                continue
            if str(j.get("nombre", "")).strip().lower() in intocables:
                continue
            desde = orden_mod._cuando(j.get("desde")) if j.get("desde") else None
            if desde is not None and ahora < desde:
                continue
            if j.get("si_saldo_negativo") and (saldo is None or saldo >= 0):
                continue
            relevos = {r for r in (general, _int(j.get("si_esta"))) if r is not None}
            if relevos and all(r in plantilla for r in relevos):
                _apuntar(salida, plantilla, pid, POR_LA_ORDEN)
            elif puja_cuenta:
                _apuntar(salida, plantilla, pid, POR_LA_ORDEN + CON_PUJA)

    # LOS VIAJES (seccion 4): el candidato que ya es nuestro se pone a
    # la venta siempre. Los mismos filtros que `decidir`.
    viajes = _dict(orden.get("viajes"))
    tope = _int(viajes.get("tope_por_viaje"), 0) or 0
    for v in _lista(viajes.get("candidatos")):
        if not isinstance(v, dict):
            continue
        pid = _int(v.get("player_id"))
        puja = _int(v.get("puja"), 0) or 0
        if not pid or puja <= 0 or (tope and puja > tope):
            continue
        _apuntar(salida, plantilla, pid, POR_LA_ORDEN + DE_VIAJE)


def _de_la_mejora(salida, plantilla, libro, pujas, puja_cuenta) -> None:
    """La mejora del once: el `sale` de cada cambio vivo. Nunca el
    `entra`."""

    from src.actions import la_mejora_del_once as mejora_mod
    from src.actions.el_cierre_de_la_jornada import la_mejora

    if not mejora_mod.activa():
        return

    # Con `pujas` (aunque vacio): el cambio cuyo `entra` ni esta ni
    # tiene puja viva es una puja perdida y no cuenta.
    de_la_mejora = la_mejora(_dict(libro), plantilla, set(pujas))

    for pid in sorted(de_la_mejora["se_van"]):
        _apuntar(salida, plantilla, pid, POR_LA_MEJORA)

    if puja_cuenta:
        for pid in sorted(de_la_mejora["vende"] - de_la_mejora["se_van"]):
            _apuntar(salida, plantilla, pid, POR_LA_MEJORA + CON_PUJA)


def _de_la_rotacion(salida, plantilla, parejas, puja_cuenta) -> None:
    """La rotacion: `las_parejas_abiertas()` (vacia si esta apagada).
    GANADA se va; PUJADA, si su puja llega antes del cierre."""

    parejas = _dict(parejas)
    se_van = _ids(parejas.get("se_van"))

    for pid in sorted(se_van):
        _apuntar(salida, plantilla, pid, POR_LA_ROTACION)

    if puja_cuenta:
        for pid in sorted(_ids(parejas.get("salen")) - se_van):
            _apuntar(salida, plantilla, pid, POR_LA_ROTACION + CON_PUJA)


def los_que_se_van(
    plantilla,
    *,
    orden=None,
    libro_mejora=None,
    parejas=None,
    pujas=None,
    saldo=None,
    ahora=None,
    segundos_al_cierre=None,
) -> dict:
    """
    `{player_id: [motivos]}` de los de la plantilla que se estan
    vendiendo. Pura: ni disco, ni red, ni reloj. Nunca lanza.

        plantilla           {id} de los nuestros
        orden               la orden del gestor (`leer_la_orden`)
        libro_mejora        el libro de la mejora ({entra: {sale, ...}})
        parejas             `la_rotacion.las_parejas_abiertas()`
        pujas               {id} con puja viva nuestra (o su dict)
        saldo               el saldo de la foto (para `si_saldo_negativo`)
        ahora               la hora (sin ella, la orden no cuenta: no se
                            sabe si caduco)
        segundos_al_cierre  hasta el cierre de la jornada (T-15); sin el,
                            ninguna puja viva sienta a nadie

    El 26/10: la orden vende a Jonny (1599) cuando esta Kike Salas
    (28115), y Kike ya es nuestro -> {1599: ['LA_ORDEN_DEL_GESTOR']}.
    """

    salida: dict = {}

    try:
        plantilla = _ids(plantilla)
        pujas = _ids(pujas)
        saldo = _int(saldo)
        ahora = _momento(ahora)
        segundos = _num(segundos_al_cierre)
        puja_cuenta = segundos is not None and segundos > HORAS_DE_UNA_PUJA * 3600

        # Cada libro por su lado: uno roto no se lleva a los demas.
        for paso in (
            lambda: _de_la_orden(salida, plantilla, _dict(orden), pujas, saldo,
                                 ahora, puja_cuenta) if isinstance(orden, dict) else None,
            lambda: _de_la_mejora(salida, plantilla, libro_mejora, pujas, puja_cuenta),
            lambda: _de_la_rotacion(salida, plantilla, parejas, puja_cuenta),
        ):
            try:
                paso()
            except Exception:                       # noqa: BLE001
                continue

    except Exception:                               # noqa: BLE001
        return {}

    return salida


# ============================================================
# 2. JORNADA PERFECTA, SI VALE
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
# 3. LA BUSQUEDA Y EL REMATE
# ============================================================

def para_la_busqueda(players, se_van) -> list:
    """
    La lista que ve la busqueda: la misma, con `SE_VA` restado al
    `lineup_score` de los que se van (una copia de su ficha; las demas,
    tal cual). Como la entrada es otra, `el_once_se_busca_una_vez` no
    la confunde con la de los que valoran.
    """

    se_van = _ids(se_van)

    return [
        {**p, "lineup_score": float(p.get("lineup_score") or 0.0) - SE_VA}
        if _pid(p) in se_van
        else p
        for p in players
    ]


def _restaurar(players, selected) -> list:
    """Cada ficha elegida, con sus numeros de verdad y su puesto."""

    originales = {_pid(p): p for p in players}

    return [
        {**originales[_pid(c)], "lineup_position": c.get("lineup_position")}
        if _pid(c) in originales
        else c
        for c in selected
    ]


def _desempatar(once, players, se_van, con_dudas) -> tuple:
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

    candidatos = [
        o for o in players
        if _pid(o) not in dentro
        and o.get("lineup_eligible")
        and (o.get("automatic_lineup") or con_dudas)
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


def rematar(preparado, players, selected, con_dudas=False) -> tuple:
    """
    `(once, informe)` tras la busqueda:

        1. cada ficha elegida vuelve a sus numeros de verdad (los de
           `players`), con su `lineup_position`;
        2. si JP vale, el desempate (cabecera, punto 2).

    El informe: `{"se_van": [{id, name, por, en_el_once}], "desempates":
    [{entra, entra_nombre, sale, sale_nombre, ff, jp}], "jp": {vale,
    motivo, ronda, edad_horas, jornada}}`. Con basura, devuelve lo que
    le llego y un informe vacio. Nunca lanza.
    """

    informe = {"se_van": [], "desempates": [], "jp": {}}

    if not isinstance(selected, list):
        return selected, informe

    try:
        preparado = _dict(preparado)
        players = [p for p in (players or []) if isinstance(p, dict)]
        once = _restaurar(players, selected)
    except Exception:                               # noqa: BLE001
        return selected, informe

    try:
        por = _dict(preparado.get("por"))
        se_van = set(por)
        informe["jp"] = dict(_dict(preparado.get("jp")))

        if informe["jp"].get("vale"):
            try:
                once, informe["desempates"] = _desempatar(
                    once, players, se_van, bool(con_dudas))
            except Exception:                       # noqa: BLE001
                informe["desempates"] = []

        dentro = {_pid(c) for c in once}

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
                        f"se vende ({motivos}): con otro que puede jugar, "
                        "no se alinea"
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
# 4. EL ENGANCHE: LO QUE LEE EN PRODUCCION
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
) -> dict | None:
    """
    Lo que necesita la busqueda del once que se escribe, o None.

        se_van     {id: [motivos]} (`los_que_se_van`)
        por        lo mismo (lo lee `rematar`)
        busqueda   la lista para la busqueda (`para_la_busqueda`)
        jp         {vale, motivo, ronda, edad_horas, jornada}

    La plantilla sale de `players`; las pujas vivas y el saldo, de la
    foto (`la_orden_del_gestor.leer_la_foto`, con el usuario de la
    liga: sin el, ninguna puja); la jornada y el cierre, de `reloj` o
    del calendario de la vuelta (este, solo si hay una puja viva o JP
    disponible: si no, no cambia nada); los libros, de `libros` o de
    produccion. `ahora`, de la hora del sistema si no se pasa.

    None -y entonces el once de hoy, byte a byte- con el interruptor
    apagado, si algo falla, o si no hay nada que hacer: nadie se va y
    JP no vale. Nunca lanza.
    """

    try:
        if not activa():
            return None

        from src.actions.la_orden_del_gestor import leer_la_foto

        players = [p for p in (players or []) if isinstance(p, dict)]
        plantilla = {_pid(p) for p in players if _pid(p) is not None}

        foto = _dict(snapshot)
        yo = _pid(_dict(foto.get("league")).get("user"))
        de_la_foto = leer_la_foto(foto, yo)
        pujas = set(de_la_foto.get("nuestras_pujas") or {}) if yo is not None else set()
        saldo = de_la_foto.get("saldo")

        libros = _dict(libros if libros is not None else _libros_de_produccion())

        # EL RELOJ, SOLO SI ALGO LO NECESITA. Lo leen las pujas vivas
        # (nuestras o las PUJADA de la rotacion: ¿se resuelven antes del
        # cierre?) y JP (¿es de la jornada que toca?). Sin ninguna de las
        # dos, el reloj no cambia nada y no se pregunta al calendario.
        parejas = _dict(libros.get("parejas"))
        lo_necesita = (
            bool(pujas)
            or bool(_ids(parejas.get("salen")) - _ids(parejas.get("se_van")))
            or bool(_dict(lineup_intelligence).get("available"))
        )

        if reloj is None and lo_necesita:
            reloj = _el_reloj(snapshot)

        reloj = _dict(reloj)
        ronda = reloj.get("target_matchday")
        segundos = reloj.get("seconds_to_deadline")

        momento = _momento(ahora) if ahora is not None else _ahora()

        se_van = los_que_se_van(
            plantilla,
            orden=libros.get("orden"),
            libro_mejora=libros.get("mejora"),
            parejas=libros.get("parejas"),
            pujas=pujas,
            saldo=saldo,
            ahora=momento,
            segundos_al_cierre=segundos,
        )

        vale, motivo = jp_vale(lineup_intelligence, ronda)
        intel = _dict(lineup_intelligence)

        if not se_van and not vale:
            return None

        return {
            "se_van": se_van,
            "por": se_van,
            "busqueda": para_la_busqueda(players, se_van),
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
