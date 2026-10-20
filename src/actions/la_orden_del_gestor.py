"""
LA ORDEN DEL GESTOR (29/09/2026)

POR QUE EXISTE

    El 29/09 salieron al mercado del Computer Roberto Fernandez (8,38 M,
    59 puntos en 7 jornadas, 8.o de 547) y Adeyemi (10,28 M, 54, 14.o),
    los dos subiendo diez dias seguidos. Pepe los tiro por
    SUPERA_PRESUPUESTO: su presupuesto es la caja libre (~0,2-1,8 M),
    mientras Biwenger deja pujar hasta `maximumBid` (14,4 M ese dia) y
    solo exige saldo >= 0 al empezar la jornada (J8: 09/10 21:00).

    Pepe no sabe hacer «vender para comprar»: gasta la caja en
    calderilla (32 de 55 pujas ganadas son defensas) y nunca junta para
    quien cambia el once. Hasta que eso lo decida el (la hucha, punto
    3-bis del plan), el gestor puede dejarle UNA ORDEN CONCRETA:

        fichar           pujar X por este jugador del Computer
        no_pujar         no dejar viva una puja nuestra por estos
        vender_si_ficha  cuando el fichaje este en la plantilla, poner a
                         la venta a estos y aceptar la oferta del
                         Computer si llega al suelo

    La orden vive en `config/la_orden_del_gestor.json` (la escribe el
    gestor, va a git, pasa por la verja) y caduca sola.

LAS GUARDIAS (12/10/2026)

    La orden se escribe una vez y corre en cada vuelta hasta que caduca
    (la de hoy, el 30/11). Lo que el gestor no vigila a mano a las 07:15
    de un viernes lo vigila `decidir`, con lo que le pasa `correr`:

    1. EL RELOJ. A menos de `HORAS_SIN_FICHAR` de la jornada (o sin
       calendario) no se pone ni se sube una puja de `fichar`, salvo la
       que no necesita vender a nadie y la paga la caja. La que ya este
       viva se deja como esta.
    2. EL PARTE DEL RELEVO. Antes de aceptar la oferta por el que sale,
       su relevo (`si_esta`) tiene que estar en la plantilla Y sano:
       `status` 'ok' o 'warned' en el catalogo de la foto. Duda, lesion,
       sancion o sin saberlo: no se cobra (publicar si), y queda un NADA
       con el motivo. Salvo el ultimo recurso (`si_saldo_negativo`) y en
       rojo a menos de `HORAS_ROJO`: ahi manda la caja... si el relevo
       esta en duda o sin saberlo. Lesionado o sancionado (`FUERA`) no
       juega seguro: vender al que sale dejaria 10 y no se cobra; queda
       un NADA para que el gestor elija entre el hueco y el rojo.
    3. LA JORNADA EN CURSO. Con una jornada jugandose no se acepta
       ninguna oferta del Computer (la de `vender_si_ficha` ni la de un
       viaje). Publicar si se puede: la oferta queda lista para cuando
       acabe.
    4. EL PARTE DEL FICHAJE (13/10/2026). El de `fichar` lesionado, en
       duda o sancionado en el catalogo (`NO_SE_FICHA`): no se puja, y
       la puja viva se retira (CANCELAR_PUJA). Ganado, nadie lo puede
       vender (`protegidos`) y la mejora no lo cambia: un hueco hasta
       el 30/11. Sin estado: la viva se queda como esta, pero no se
       pone ni se sube.

EL APLAZADO NO FRENA LA COMPRA (20/10/2026,
`BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA`, nace APAGADO)

    El reloj (1) mide las 40 h hasta el proximo cierre de cualquier
    clase, y el Levante-Athletic (J6 aplazada, una ronda aparte de un
    partido, mie 21/10 20:00 de Madrid) freno a la orden del mar 20/10 a
    las 04:00 hasta el partido: Kubo (2,88 M, +300.000 en dos dias) se
    resolvia en el reset del 21/10 y no se podia pujar. Un aplazado se
    puntua con el once congelado al empezar su jornada (laboratorio,
    n = 1): comprar no cambia sus puntos. Lo unico que pide es la caja:
    saldo >= 0 al empezar (si no, premio 0) y la regla de la casa
    (saldo - pujas vivas >= 0).

    Con el interruptor, si el proximo cierre es un aplazado a menos de
    `HORAS_SIN_FICHAR` (`el_aplazado`), una puja que el reloj frena se
    pone si se cumplen las TRES:

        1. se resuelve antes del aplazado (el proximo reset cae antes de
           su primer partido: `resuelve_antes`). La de despues del
           ultimo reset espera a que empiece el aplazado, como hoy: se
           resuelve en ese mismo reset y no pierde ningun dia de
           mercado;
        2. la regla de siempre, medida hasta la proxima ronda ENTERA
           (`horas_principal` >= `HORAS_SIN_FICHAR`);
        3. LA CAJA DEL APLAZADO >= 0 (`la_caja_del_aplazado`): saldo -
           TODAS nuestras pujas vivas enteras (esta incluida, la
           sustituida por la nueva) + por cada puja, como mucho su
           importe, lo que se cobra ANTES del aplazado por los que salen
           de su cambio (`lo_que_se_cobra_antes`): la oferta del
           Computer que ya hay por ellos, si llega al suelo, sigue viva
           al empezar el aplazado (`until` >= su inicio) y la
           publicacion tambien. Cada uno que sale cuenta una vez y solo
           paga la puja de su relevo. Nunca la reventa del fichaje, el
           premio, la racha ni una venta esperada.

    `until` >= el inicio y no `until` > el reset: la oferta nace a las
    07:03-07:09 y vive 48 h, asi que la de Exposito emitida el 19/10
    caduca el 21/10 a las ~07:05 de Madrid, minutos DESPUES del reset
    del 21 pero muerta antes de la vuelta de las 07:15.

    Y, encendido, en rojo y a menos de `HORAS_ROJO` antes de un
    aplazado, la caja manda aunque el relevo este lesionado o sancionado
    (EL PARTE DEL RELEVO): el aplazado se juega con el once congelado y
    empezarlo en rojo deja su premio en 0. Solo si la ronda entera de
    despues esta a `HORAS_SIN_FICHAR` o mas (aun se puede fichar otro
    relevo para ella); sin saberlo, o mas cerca, decide el gestor como
    siempre. Es lo que hace que el cobro contado se cobre.

QUE NO HACE

    No decide nada: ejecuta lo escrito. No acepta ofertas de managers,
    no vende a nadie que no este en la orden, no toca a Yamal (se
    rechaza la orden entera si lo nombra), no puja por encima de
    `maximumBid`. Una escritura por jugador y vuelta como mucho. No
    retira la puja viva de `fichar` cuando el reloj ya no deja subirla
    (si cuando su jugador cae lesionado), ni quita de la venta al que
    sale si su relevo cae lesionado.

    Nace APAGADA: `BORDALAS_LA_ORDEN_DEL_GESTOR`. Nunca lanza.
"""

from __future__ import annotations

import json
import math
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path


ENV = "BORDALAS_LA_ORDEN_DEL_GESTOR"

# EL APLAZADO NO FRENA LA COMPRA (20/10/2026): nace APAGADO. Lo leen la
# orden, la mejora del once y el cierre de la jornada (todos importan
# este modulo).
ENV_EL_APLAZADO = "BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA"

# Lo que vive una oferta del Computer (nace en un reset, a las 07:03-07:09,
# y vive 48 h): si la foto no trae su `until`, su `created` + esto.
VIDA_DE_LA_OFERTA = timedelta(hours=48)

RUTA = Path("config") / "la_orden_del_gestor.json"

# Nunca se vende. Regla de la casa.
INTOCABLES = frozenset({"yamal", "lamine yamal"})


# EL RELOJ DE `fichar` (12/10/2026)
#
#     Vender solo se puede aceptando una oferta del Computer, y esa
#     oferta solo nace para quien se publico ANTES de un reset: llega a
#     las 07:03-07:09 y caduca en el siguiente (renovar_ofertas.py,
#     zona_de_silencio.py). Una puja ganada en el reset X publica al que
#     sale a las 07:15 de X y cobra en el reset X+1.
#
#     La J9 empieza el viernes 16/10 a las 21:00. Puja ganada el jueves
#     a las 07:00: se cobra el viernes 07:15, antes del partido. Ganada
#     el viernes a las 07:00 (el ultimo reset antes del partido): la
#     primera oferta llega el sabado, la jornada empieza en rojo y son 0
#     puntos. La puja del jueves se pone, como tarde, en la vuelta de
#     las 04:50 del jueves: a 40 h. Las mismas 40 h que la mejora del
#     once (`HORAS_SIN_COMPRAR`). Vale para cualquier partido que empiece
#     entre las 07:15 y las 23:00 de Madrid (todos los de LaLiga): a
#     40 h, la ultima puja posible siempre se resuelve un reset antes del
#     ultimo.
HORAS_SIN_FICHAR = 40

# EL PARTE DEL RELEVO (12/10/2026): lo que el catalogo de Biwenger da
# por bueno. 'warned' (apercibido) juega (el_once_objetivo.py:216). Todo
# lo demas -'doubt', 'injured', 'sanctioned', sin estado o sin ficha-
# deja al que sale en la plantilla... salvo en rojo y a menos de
# `HORAS_ROJO` de la jornada: ahi manda la caja («mejor un hueco que 0
# puntos en la jornada»).
SANOS = frozenset({"ok", "warned"})
HORAS_ROJO = 24

# Los que seguro no juegan: con el relevo asi, ni en rojo a menos de
# `HORAS_ROJO` se vende al que sale (dejaria 10 que juegan).
FUERA = frozenset({"injured", "sanctioned"})

# EL PARTE DEL FICHAJE (13/10/2026): los de la revision de las pujas
# vivas (`la_revision_de_pujas.MALOS`), que se salta las de la orden.
NO_SE_FICHA = frozenset({"injured", "doubt", "sanctioned"})


# LA LLAVE DE YAMAL (07/10/2026, decision del CEO con permiso del dueño:
# «el objetivo es ganar la liga»). Yamal sigue intocable SALVO que la
# orden lleve `yamal_por_lesion` con un motivo y una baja estimada de
# `BAJA_MINIMA_DIAS` o mas: un Yamal lesionado no puntua y su precio cae
# cada dia; venderlo pronto y reinvertir pierde menos puntos que esperar.
BAJA_MINIMA_DIAS = 28


def _intocables(orden: dict | None) -> frozenset:
    llave = (orden or {}).get("yamal_por_lesion") or {}
    if (
        isinstance(llave, dict)
        and str(llave.get("motivo") or "").strip()
        and (_int(llave.get("baja_estimada_dias"), 0) or 0) >= BAJA_MINIMA_DIAS
    ):
        return frozenset()
    return INTOCABLES


def activa(interruptor: str = ENV) -> bool:
    try:
        return str(
            os.environ.get(interruptor, "")
        ).strip().lower() in {"1", "true", "si", "yes"}

    except Exception:                               # noqa: BLE001
        return False


def el_aplazado_activo() -> bool:
    """`BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA`, leido como `activa`.
    Nace APAGADO. Nunca lanza."""
    return activa(ENV_EL_APLAZADO)


def _int(valor, defecto=None):
    try:
        if valor is None or isinstance(valor, bool):
            return defecto
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _cuando(texto) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(texto))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def leer_la_orden(ruta: Path | str | None = None) -> dict | None:
    try:
        ruta = RUTA if ruta is None else ruta
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def validar(orden: dict | None, ahora: datetime) -> str | None:
    """None si la orden vale. Si no, el motivo."""

    if not isinstance(orden, dict):
        return "SIN_ORDEN"

    caduca = _cuando(orden.get("caduca"))

    if caduca is None:
        return "SIN_CADUCIDAD"

    if ahora >= caduca:
        return "CADUCADA"

    nombres = [
        str(x.get("nombre", "")).strip().lower()
        for x in (orden.get("vender_si_ficha") or {}).get("jugadores") or []
    ]

    if any(n in _intocables(orden) for n in nombres):
        return "NOMBRA_A_UN_INTOCABLE"

    for f in orden.get("fichar") or []:
        if not _int(f.get("player_id")) or not _int(f.get("puja")):
            return "FICHAJE_MAL_ESCRITO"

    return None


def decidir(
    orden: dict,
    *,
    mercado: dict,
    nuestras_pujas: dict,
    plantilla: set,
    ofertas_del_computer: dict,
    en_venta: set,
    precios: dict,
    maximo_de_puja: int | None,
    saldo: int | None = None,
    ahora: datetime | None = None,
    horas_jornada: float | None = math.inf,
    estados: dict | None = None,
    en_curso: bool = False,
    aparte: dict | None = None,
) -> list:
    """
    Las escrituras que tocan en esta vuelta. Pura: ni red ni disco.

        mercado               {player_id: precio} de lo que vende el Computer
        nuestras_pujas        {player_id: {"offer_id", "amount"}}
        plantilla             {player_id} de los nuestros
        ofertas_del_computer  {player_id: {"offer_id", "amount"}} recibidas
        en_venta              {player_id} que ya tenemos publicados
        precios               {player_id: precio de mercado}
        maximo_de_puja        `maximumBid` de Biwenger

    LAS GUARDIAS (12/10/2026; `correr` pasa siempre las tres):

        horas_jornada  horas hasta la proxima jornada; None = no se sabe
                       y no se puja. Sin pasarla (`inf`), no se mira.
        estados        {player_id: status del catalogo}; el relevo tiene
                       que estar 'ok', y el de `fichar` tambien para
                       pujar por el. Sin pasarlo (None), no se mira.
        en_curso       hay una jornada jugandose: no se acepta ninguna
                       oferta del Computer.

    EL APLAZADO NO FRENA LA COMPRA (20/10/2026; `correr` lo pasa solo con
    su interruptor):

        aparte         el de `el_aplazado` (el proximo cierre es un
                       aplazado a menos de `HORAS_SIN_FICHAR`), o None.
                       Con el, la puja de `fichar` que el reloj frena se
                       pone si `_pasa_el_aplazado` (guardia
                       `EL_APLAZADO`, con `caja_del_aplazado`); si la
                       caja del aplazado no llega, NADA con esa guardia y
                       la cifra. Y, en rojo a menos de `HORAS_ROJO` y con
                       la ronda entera a `HORAS_SIN_FICHAR` o mas, el
                       relevo `FUERA` ya no frena el cobro. None: todo
                       como siempre.
    """

    acciones = []
    retiradas = set()
    # Lo que esta vuelta ya va a pujar por `fichar` (para la caja del
    # aplazado de la siguiente: sin el aplazado no se mira).
    pujadas_aqui = {}

    # 1. FICHAR
    for f in orden.get("fichar") or []:
        pid = _int(f.get("player_id"))
        puja = _int(f.get("puja"))

        if pid in plantilla:
            continue

        ya = nuestras_pujas.get(pid)

        # EL PARTE DEL FICHAJE (13/10/2026): Ivan Romero juega la J8 el
        # 12/10 a las 21:00 y su puja se resuelve el 13/10 a las 07:00;
        # la revision de pujas se salta las de la orden. Ganado lesionado,
        # nadie lo puede vender (`protegidos`) ni cambiar: un hueco en un
        # once de 11 justos. Lesionado, en duda o sancionado: no se puja
        # y la viva se retira. Sin estado: la viva se queda, pero no se
        # pone ni se sube.
        if estados is not None:
            parte = str(estados.get(pid) or "").strip().lower()
            if parte in NO_SE_FICHA:
                oferta_viva = _int((ya or {}).get("offer_id"))
                if oferta_viva:
                    retiradas.add(pid)
                    acciones.append({
                        "accion": "CANCELAR_PUJA", "player_id": pid,
                        "nombre": f.get("nombre"), "offer_id": oferta_viva,
                        "guardia": "EL_PARTE_DEL_FICHAJE",
                        "estado_del_fichaje": parte,
                        "motivo": (
                            f"el fichaje esta '{parte}' en el catalogo: se "
                            "retira la puja viva (ganado, nadie lo podria "
                            "vender ni cambiar)"
                        ),
                    })
                elif pid in mercado:
                    acciones.append({
                        "accion": "NADA", "player_id": pid,
                        "nombre": f.get("nombre"),
                        "guardia": "EL_PARTE_DEL_FICHAJE",
                        "estado_del_fichaje": parte,
                        "motivo": (
                            f"el fichaje esta '{parte}' en el catalogo: "
                            "no se puja"
                        ),
                    })
                continue
            if (
                parte not in SANOS and pid in mercado
                and not (ya and _int(ya.get("amount"), 0) >= puja)
            ):
                acciones.append({
                    "accion": "NADA", "player_id": pid,
                    "nombre": f.get("nombre"),
                    "guardia": "EL_PARTE_DEL_FICHAJE",
                    "estado_del_fichaje": parte or None,
                    "motivo": (
                        "el fichaje no tiene estado en el catalogo: no se "
                        "pone ni se sube la puja (la viva se queda)"
                    ),
                })
                continue

        if pid not in mercado:
            continue

        if ya and _int(ya.get("amount"), 0) >= puja:
            continue

        # EL RELOJ (12/10/2026): ganada en el ultimo reset antes del
        # partido, el que sale no cobra hasta despues del partido (ver
        # `HORAS_SIN_FICHAR`). Ni se pone ni se sube; la viva se queda.
        frena = (horas_jornada is None or horas_jornada < HORAS_SIN_FICHAR) and not _la_paga_la_caja(
            orden, pid, puja, saldo, nuestras_pujas,
        )

        # EL APLAZADO NO FRENA LA COMPRA (20/10/2026): si lo que viene es
        # un aplazado, la puja que se resuelve antes de el, con la regla de
        # siempre medida hasta la ronda entera y la caja del aplazado en
        # >= 0, no se frena. Si la regla no aplica (despues del ultimo
        # reset, la ronda entera a menos de 40 h, sin saldo), el reloj de
        # siempre.
        aplazado = None
        if frena and aparte:
            aplazado = _pasa_el_aplazado(
                orden, pid, puja, saldo, {**(nuestras_pujas or {}), **pujadas_aqui},
                ofertas_del_computer, aparte, ahora,
            )
            if aplazado is not None and not aplazado["pasa"]:
                acciones.append({
                    "accion": "NADA", "player_id": pid,
                    "nombre": f.get("nombre"), "guardia": "EL_APLAZADO",
                    "caja_del_aplazado": aplazado["caja"],
                    "motivo": (
                        f"el aplazado empieza en {_horas(aparte.get('horas'))} h y la "
                        f"caja del aplazado con esta puja quedaria en "
                        f"{aplazado['caja']}: no se puja"
                    ),
                })
                continue

        if frena and aplazado is None:
            acciones.append({
                "accion": "NADA", "player_id": pid,
                "nombre": f.get("nombre"), "guardia": "EL_RELOJ",
                "motivo": (
                    "sin calendario no se sabe cuanto falta para la "
                    "jornada: no se puja"
                    if horas_jornada is None else
                    f"la jornada empieza en {horas_jornada:.1f} h (menos de "
                    f"{HORAS_SIN_FICHAR}): el que sale no se cobraria antes "
                    "del partido; no se puja"
                ),
            })
            continue

        # SUBIR UNA PUJA (29/09): `maximumBid` ya descuenta nuestra puja
        # viva por este jugador; al sustituirla, ese dinero vuelve.
        tope = (
            None if maximo_de_puja is None
            else maximo_de_puja + (_int((ya or {}).get("amount"), 0) or 0)
        )

        if tope is not None and puja > tope:
            acciones.append({
                "accion": "NADA", "player_id": pid,
                "nombre": f.get("nombre"),
                "motivo": f"la puja {puja} supera el tope {tope}",
            })
            continue

        pujar = {
            "accion": "PUJAR", "player_id": pid,
            "nombre": f.get("nombre"), "importe": puja,
            "sustituye": ya,
        }
        if aplazado is not None:
            pujar.update({"guardia": "EL_APLAZADO",
                          "caja_del_aplazado": aplazado["caja"]})
        acciones.append(pujar)
        pujadas_aqui[pid] = {"amount": puja}

    # 2. NO PUJAR
    for n in orden.get("no_pujar") or []:
        pid = _int(n.get("player_id"))
        ya = nuestras_pujas.get(pid)

        if ya and _int(ya.get("offer_id")) and pid not in retiradas:
            retiradas.add(pid)
            acciones.append({
                "accion": "CANCELAR_PUJA", "player_id": pid,
                "nombre": n.get("nombre"),
                "offer_id": _int(ya.get("offer_id")),
            })

    # 3. VENDER, SOLO SI EL FICHAJE YA ES NUESTRO
    venta = orden.get("vender_si_ficha") or {}
    condicion = _int(venta.get("si_esta"))

    # VARIOS CAMBIOS A LA VEZ (11/10, el fichaje del dia): sin `si_esta`
    # general, cada jugador manda con su propio relevo (`si_esta`).
    todos_con_relevo = bool(venta.get("jugadores")) and all(
        _int(j.get("si_esta")) for j in venta.get("jugadores") or []
    )

    if (condicion and condicion in plantilla) or (not condicion and todos_con_relevo):
        for j in venta.get("jugadores") or []:
            pid = _int(j.get("player_id"))
            nombre = str(j.get("nombre", ""))

            if pid not in plantilla or nombre.strip().lower() in _intocables(orden):
                continue

            # SU PROPIO RELEVO (30/09): un jugador con `si_esta` solo se
            # vende cuando SU sustituto ya es nuestro (Unai Lopez, cuando
            # llegue Oriol Rey). Asi nunca se queda un hueco en el once.
            relevo = _int(j.get("si_esta"))
            if relevo and relevo not in plantilla:
                continue

            # EL ULTIMO RECURSO (29/09): `desde` + `si_saldo_negativo`.
            # No se toca hasta esa fecha, y solo si el saldo sigue en
            # rojo. Sin saber el saldo o la hora, no se vende.
            desde = _cuando(j.get("desde")) if j.get("desde") else None
            if desde is not None and (ahora is None or ahora < desde):
                continue
            if j.get("si_saldo_negativo") and (saldo is None or saldo >= 0):
                continue

            # EL PARTE DEL RELEVO (12/10/2026): estar en la plantilla no
            # basta. La plantilla es de 11 justos, sin banquillo: si el
            # que entra esta lesionado o en duda, vender al que sale deja
            # un hueco en el once. Ivan Romero (relevo de Jutgla) juega la
            # J8 el 12/10 a las 21:00 y su puja se resuelve el 13/10 a las
            # 07:00; la revision de pujas se salta las de la orden.
            #     Solo frena el COBRO: publicar no saca a nadie del once
            #     y hace nacer la oferta del reset siguiente (si se
            #     frenara, el que sale cobraria un reset tarde). Y no frena
            #     el ultimo recurso (`si_saldo_negativo`) ni, en rojo a
            #     menos de `HORAS_ROJO`, nada: un hueco cuesta un jugador;
            #     empezar la jornada en rojo, el once entero. Salvo con
            #     el relevo `FUERA` (13/10/2026): ver abajo.
            parte_malo = None
            if estados is not None and not j.get("si_saldo_negativo"):
                quien = relevo or condicion
                parte = str(estados.get(quien) or "").strip().lower() if quien else ""
                en_rojo_y_cerca = (
                    saldo is not None and saldo < 0
                    and horas_jornada is not None and horas_jornada < HORAS_ROJO
                )
                if parte not in SANOS and not en_rojo_y_cerca:
                    parte_malo = {
                        "accion": "NADA", "player_id": pid, "nombre": nombre,
                        "guardia": "EL_PARTE_DEL_RELEVO", "relevo": quien,
                        "estado_del_relevo": parte or None,
                        "motivo": (
                            f"el relevo ({quien}) no esta sano "
                            f"({parte or 'sin estado'}): no se cobra"
                        ),
                    }
                # En rojo y cerca, la caja manda solo si el relevo PUEDE
                # jugar (duda, sin estado). Lesionado o sancionado no
                # juega seguro: vender al que sale deja 10 que juegan.
                # Eso lo decide el gestor, no la red (13/10/2026).
                #     Salvo antes de un aplazado (`aparte`, 20/10/2026)
                #     con la ronda entera aun fuera del reloj
                #     (`_manda_la_caja_antes_del_aplazado`): el aplazado se
                #     juega con el once congelado y, en rojo, su premio es
                #     0; para la ronda entera queda tiempo de fichar otro
                #     relevo. Ahi manda la caja: es el cobro que
                #     `_pasa_el_aplazado` conto para dejar pujar.
                elif not _manda_la_caja_antes_del_aplazado(aparte) and parte in FUERA and str(
                    (estados or {}).get(pid) or ""
                ).strip().lower() not in FUERA:
                    # (Si el que sale tampoco juega, venderlo no cuesta a
                    # nadie que juegue: manda la caja.)
                    parte_malo = {
                        "accion": "NADA", "player_id": pid, "nombre": nombre,
                        "guardia": "EL_PARTE_DEL_RELEVO", "relevo": quien,
                        "estado_del_relevo": parte,
                        "motivo": (
                            f"en rojo ({saldo}) a {horas_jornada:.1f} h de "
                            f"la jornada, pero el relevo ({quien}) esta "
                            f"'{parte}' y no jugara: cobrar a {nombre} deja "
                            "un hueco en el once (10 que juegan); no "
                            "cobrarlo deja la jornada en rojo (0 puntos). "
                            "No se cobra: decide el gestor"
                        ),
                    }

            suelo = _int(j.get("suelo"), 0)
            oferta = ofertas_del_computer.get(pid)

            if oferta and _int(oferta.get("amount"), 0) >= suelo:
                # LA JORNADA EN CURSO (12/10/2026): con 11 justos, el que
                # se vende con su partido por jugar deja de puntuar (el
                # Rayo de Unai Lopez cierra la J9 el lunes 19/10 21:00).
                if en_curso:
                    acciones.append(_no_se_cobra_en_jornada(pid, nombre))
                    continue
                if parte_malo:
                    acciones.append(parte_malo)
                    continue
                acciones.append({
                    "accion": "ACEPTAR_OFERTA_DEL_COMPUTER",
                    "player_id": pid, "nombre": nombre,
                    "offer_id": _int(oferta.get("offer_id")),
                    "importe": _int(oferta.get("amount")),
                    "suelo": suelo,
                })
                continue

            if pid not in en_venta:
                precio = _int(precios.get(pid))
                if precio and precio > 0:
                    acciones.append({
                        "accion": "PONER_A_LA_VENTA",
                        "player_id": pid, "nombre": nombre,
                        "precio": precio,
                    })

    # 4. LOS VIAJES CORTOS (30/09/2026)
    #
    #     Salir del rojo sin vender a los top: comprar al Computer a quien
    #     SUBE (E1) y revendérselo con margen. Candidatos elegidos por el
    #     gestor; topes por viaje y en total; todo vendido antes de `hasta`.
    #     Se vende en cuanto la oferta del Computer supera lo pagado
    #     (+1 %); llegado `hasta`, se acepta hasta un 5 % por debajo.
    viajes = orden.get("viajes") or {}
    hasta = _cuando(viajes.get("hasta")) if viajes.get("hasta") else None
    tope_viaje = _int(viajes.get("tope_por_viaje"), 0) or 0
    tope_total = _int(viajes.get("tope_total"), 0) or 0
    gastado = 0

    for v in viajes.get("candidatos") or []:
        pid = _int(v.get("player_id"))
        puja = _int(v.get("puja"), 0) or 0
        nombre = v.get("nombre")
        if not pid or puja <= 0 or (tope_viaje and puja > tope_viaje):
            continue

        if pid in plantilla:
            gastado += puja
            oferta = ofertas_del_computer.get(pid)
            vencido = hasta is not None and ahora is not None and ahora >= hasta
            listo = 0.95 if vencido else 1.01
            if oferta and _int(oferta.get("amount"), 0) >= int(puja * listo):
                if en_curso:
                    acciones.append(_no_se_cobra_en_jornada(pid, nombre))
                    continue
                acciones.append({
                    "accion": "ACEPTAR_OFERTA_DEL_COMPUTER",
                    "player_id": pid, "nombre": nombre,
                    "offer_id": _int(oferta.get("offer_id")),
                    "importe": _int(oferta.get("amount")),
                    "suelo": int(puja * listo), "viaje": True,
                })
            elif pid not in en_venta and _int(precios.get(pid)):
                acciones.append({
                    "accion": "PONER_A_LA_VENTA", "player_id": pid,
                    "nombre": nombre, "precio": _int(precios.get(pid)),
                    "viaje": True,
                })
            continue

        if hasta is None or ahora is None or ahora >= hasta:
            continue
        if pid not in mercado:
            continue
        if tope_total and gastado + puja > tope_total:
            continue
        ya = nuestras_pujas.get(pid)
        if ya and _int(ya.get("amount"), 0) >= puja:
            gastado += puja
            continue
        tope = (
            None if maximo_de_puja is None
            else maximo_de_puja + (_int((ya or {}).get("amount"), 0) or 0)
        )
        if tope is not None and puja > tope:
            continue
        gastado += puja
        acciones.append({
            "accion": "PUJAR", "player_id": pid, "nombre": nombre,
            "importe": puja, "sustituye": ya, "viaje": True,
        })

    return acciones


def _la_paga_la_caja(orden, pid, puja, saldo, nuestras_pujas) -> bool:
    """
    La puja de `fichar` que no necesita vender a nadie: ningun
    `vender_si_ficha` espera a este jugador y el saldo, descontadas las
    pujas vivas, la paga entera. Esa no tiene prisa por cobrar: el reloj
    no la frena (el 30/09 se lleno asi una plantilla de 10). Nunca lanza.
    """

    try:
        venta = orden.get("vender_si_ficha") or {}
        if _int(venta.get("si_esta")) == pid:
            return False
        if any(_int(j.get("si_esta")) == pid for j in venta.get("jugadores") or []):
            return False
        if saldo is None or puja is None:
            return False
        vivas = sum(
            _int((p or {}).get("amount"), 0) or 0
            for q, p in (nuestras_pujas or {}).items() if q != pid
        )
        return saldo - vivas >= puja
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# EL APLAZADO NO FRENA LA COMPRA (20/10/2026)
# ============================================================
#
#     Todo puro y sin lanzar nunca: lo que no se sabe (calendario, reset,
#     saldo, `until`) no relaja nada y no cuenta ni un euro.

def _horas(valor) -> str:
    try:
        return f"{float(valor):.1f}"
    except (TypeError, ValueError):
        return "?"


def _el_importe(puja) -> int:
    """El importe de una puja: `{"amount"}` o el numero suelto."""
    if isinstance(puja, dict):
        return _int(puja.get("amount"), 0) or 0
    return _int(puja, 0) or 0


def _epoch(valor) -> datetime | None:
    """Un `until` o `created` de Biwenger (segundos desde 1970, numero o
    texto) o una fecha ISO, en UTC. None si no se lee. Nunca lanza."""
    try:
        if valor is None or isinstance(valor, bool):
            return None
        if isinstance(valor, datetime):
            return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
        if isinstance(valor, (int, float)):
            return datetime.fromtimestamp(float(valor), tz=timezone.utc)
        texto = str(valor).strip()
        if not texto:
            return None
        try:
            return datetime.fromtimestamp(float(texto), tz=timezone.utc)
        except ValueError:
            pass
        d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:                               # noqa: BLE001
        return None


def las_caducidades(snapshot: dict | None, yo: int | None) -> dict:
    """
    Hasta cuando vale lo que se puede cobrar, de la foto de la vuelta:

        {player_id: {"offer_id", "oferta": datetime | None,
                     "publicacion": datetime | None}}

    `oferta`: el `until` de la oferta del Computer por ese jugador, la
    MISMA que se queda `leer_la_foto` (`from` None, 'waiting', un solo
    jugador, la mas alta); sin `until`, su `created` + `VIDA_DE_LA_OFERTA`;
    sin ninguno, None (no cuenta). `publicacion`: el `until` de nuestra
    publicacion (`market.sales` de `yo`), o None si no se sabe. Vacio si
    no se puede leer. Nunca lanza.
    """
    salida: dict = {}
    try:
        market = (snapshot or {}).get("market") or {}
        mejores: dict = {}
        for o in market.get("offers") or []:
            if not isinstance(o, dict) or str(o.get("status", "waiting")) != "waiting":
                continue
            jugadores = o.get("requestedPlayers") or []
            if len(jugadores) != 1 or o.get("from") is not None:
                continue
            pid = _pid(jugadores[0])
            importe = _int(o.get("amount"), 0)
            if importe > mejores.get(pid, (-1, None))[0]:
                mejores[pid] = (importe, o)
        for pid, (_, o) in mejores.items():
            hasta = _epoch(o.get("until"))
            if hasta is None:
                creada = _epoch(o.get("created"))
                hasta = None if creada is None else creada + VIDA_DE_LA_OFERTA
            salida[pid] = {"offer_id": _int(o.get("id")), "oferta": hasta, "publicacion": None}
        if yo is not None:
            for venta in market.get("sales") or []:
                if not isinstance(venta, dict) or venta.get("user") is None:
                    continue
                if _pid(venta.get("user")) != yo:
                    continue
                pid = _pid(venta.get("player"))
                if pid is None:
                    continue
                fila = salida.setdefault(pid, {"offer_id": None, "oferta": None,
                                               "publicacion": None})
                fila["publicacion"] = _epoch(venta.get("until"))
        return salida
    except Exception:                               # noqa: BLE001
        return {}


def las_parejas_de_la_orden(orden: dict | None, ahora: datetime | None = None) -> dict:
    """
    Los cambios de `vender_si_ficha`, por su relevo:

        {relevo: [(el que sale, su suelo)]}

    El relevo es el `si_esta` de cada jugador o, sin el, el general (sin
    general, todos tienen que traer el suyo, como pide `decidir`). Fuera:
    el que pide DOS relevos distintos (el general y el suyo: ninguna puja
    sola lo paga), un intocable y el que tiene `desde` aun por llegar.
    Vacio si no hay. Pura, nunca lanza.
    """
    parejas: dict = {}
    try:
        venta = (orden or {}).get("vender_si_ficha") or {}
        general = _int(venta.get("si_esta"))
        jugadores = [j for j in venta.get("jugadores") or [] if isinstance(j, dict)]
        if not general and not (jugadores and all(_int(j.get("si_esta")) for j in jugadores)):
            return {}
        intocables = _intocables(orden)
        for j in jugadores:
            pid = _int(j.get("player_id"))
            if pid is None or str(j.get("nombre", "")).strip().lower() in intocables:
                continue
            desde = _cuando(j.get("desde")) if j.get("desde") else None
            if desde is not None and (ahora is None or ahora < desde):
                continue
            propio = _int(j.get("si_esta"))
            if general and propio and propio != general:
                continue
            parejas.setdefault(propio or general, []).append((pid, _int(j.get("suelo"), 0) or 0))
        return parejas
    except Exception:                               # noqa: BLE001
        return {}


def cobrable(sale, suelo, ofertas, caducidades, inicio) -> int:
    """
    Lo que se cobra por `sale` ANTES de que empiece el aplazado (`inicio`):
    el importe de la oferta del Computer que ya hay por el
    (`ofertas`: {player_id: {"offer_id", "amount"}}), si llega a `suelo`,
    sigue viva a esa hora (`until` >= `inicio`, de `caducidades`) y su
    publicacion tambien (si se sabe). Si no, 0. Nunca lanza.
    """
    try:
        oferta = (ofertas or {}).get(sale)
        if not isinstance(oferta, dict) or not isinstance(inicio, datetime):
            return 0
        importe = _int(oferta.get("amount"), 0) or 0
        if importe <= 0 or importe < (_int(suelo, 0) or 0):
            return 0
        fila = (caducidades or {}).get(sale)
        if not isinstance(fila, dict):
            return 0
        suya, esta = _int(fila.get("offer_id")), _int(oferta.get("offer_id"))
        if suya is not None and esta is not None and suya != esta:
            return 0
        hasta = fila.get("oferta")
        if not isinstance(hasta, datetime) or hasta < inicio:
            return 0
        publicacion = fila.get("publicacion")
        if isinstance(publicacion, datetime) and publicacion < inicio:
            return 0
        return importe
    except Exception:                               # noqa: BLE001
        return 0


def lo_que_se_cobra_antes(pujas, parejas, ofertas, caducidades, inicio) -> int:
    """
    Lo que pagan antes del aplazado los cambios de nuestras pujas vivas:
    por cada puja (`pujas`: {relevo: {"amount"} o importe}), lo
    `cobrable` de los que salen de su cambio (`parejas`: {relevo: [(sale,
    suelo)]}), como mucho su importe. Cada uno que sale cuenta UNA vez
    (el primero, por relevo de menor a mayor) y solo paga la puja de su
    relevo: un cambio no paga otra puja. 0 si no se sabe. Nunca lanza.
    """
    try:
        por_relevo: dict = {}
        for relevo, lista in (parejas or {}).items():
            relevo = _int(relevo)
            if relevo is None:
                continue
            for par in lista or []:
                try:
                    sale, suelo = par
                except (TypeError, ValueError):
                    continue
                if _int(sale) is not None:
                    por_relevo.setdefault(relevo, []).append((_int(sale), suelo))
        vivas = {}
        for relevo, puja in (pujas or {}).items():
            if _int(relevo) is not None:
                vivas[_int(relevo)] = _el_importe(puja)
        total, contados = 0, set()
        for relevo in sorted(vivas):
            importe = vivas[relevo]
            if importe <= 0:
                continue
            cobro = 0
            for sale, suelo in por_relevo.get(relevo, []):
                if sale in contados:
                    continue
                valor = cobrable(sale, suelo, ofertas, caducidades, inicio)
                if valor > 0:
                    contados.add(sale)
                    cobro += valor
            total += min(importe, cobro)
        return total
    except Exception:                               # noqa: BLE001
        return 0


def la_caja_del_aplazado(saldo, pujas, parejas, ofertas, caducidades, inicio) -> int | None:
    """
    La caja al empezar el aplazado si se ganan todas nuestras pujas vivas:
    `saldo` - todas (`pujas`, enteras) + `lo_que_se_cobra_antes`. None si
    no se sabe el saldo (y entonces no se relaja nada). Nunca lanza.
    """
    try:
        saldo = _int(saldo)
        if saldo is None:
            return None
        vivas = sum(_el_importe(p) for p in (pujas or {}).values())
        return saldo - vivas + lo_que_se_cobra_antes(pujas, parejas, ofertas, caducidades, inicio)
    except Exception:                               # noqa: BLE001
        return None


def _manda_la_caja_antes_del_aplazado(aparte) -> bool:
    """
    EL PARTE DEL RELEVO antes de un aplazado: True si `aparte` dice que lo
    que viene es un aplazado y la ronda ENTERA de despues esta a
    `HORAS_SIN_FICHAR` o mas (aun se puede fichar otro relevo para ella).
    Entonces, en rojo y a menos de `HORAS_ROJO`, se cobra al que sale
    aunque su relevo este lesionado o sancionado. Sin saber cuando es la
    ronda entera (un calendario que solo trae rondas cortas), o con ella
    mas cerca, False: decide el gestor, como siempre. Nunca lanza.
    """
    try:
        if not isinstance(aparte, dict):
            return False
        principal = aparte.get("horas_principal")
        if principal is None or isinstance(principal, bool):
            return False
        principal = float(principal)
        return math.isfinite(principal) and principal >= HORAS_SIN_FICHAR
    except Exception:                               # noqa: BLE001
        return False


def _pasa_el_aplazado(orden, pid, puja, saldo, pujas, ofertas, aparte, ahora=None) -> dict | None:
    """
    None si la regla del aplazado no aplica a esta puja (el reloj de
    siempre decide): no se resuelve antes del aplazado, la ronda entera
    esta a menos de `HORAS_SIN_FICHAR`, o no se sabe (saldo, inicio). Si
    aplica, `{"pasa": caja >= 0, "caja"}` con `la_caja_del_aplazado` de
    todas las pujas vivas (`pujas`, sin la de `pid`) mas esta, y solo las
    parejas de la orden. Nunca lanza.
    """
    try:
        if not isinstance(aparte, dict) or not aparte.get("resuelve_antes"):
            return None
        principal = aparte.get("horas_principal")
        if principal is None or isinstance(principal, bool):
            return None
        principal = float(principal)
        if not math.isfinite(principal) or principal < HORAS_SIN_FICHAR:
            return None
        if _int(saldo) is None or _int(puja) is None or not isinstance(aparte.get("inicio"), datetime):
            return None
        vivas = {}
        for q, p in (pujas or {}).items():
            if _int(q) is not None and _int(q) != pid:
                vivas[_int(q)] = _el_importe(p)
        vivas[pid] = _int(puja)
        caja = la_caja_del_aplazado(
            saldo, vivas, las_parejas_de_la_orden(orden, ahora), ofertas,
            aparte.get("caducidades") or {}, aparte["inicio"],
        )
        if caja is None:
            return None
        return {"pasa": caja >= 0, "caja": caja}
    except Exception:                               # noqa: BLE001
        return None


def el_aplazado(ahora: datetime, calendario=None, snapshot: dict | None = None,
                yo: int | None = None) -> dict | None:
    """
    Lo que la regla del aplazado necesita en esta vuelta, o None si no
    aplica: el proximo cierre (`la_proxima_jornada.el_proximo_cierre`,
    con `calendario` o el de produccion) no es un aplazado, o esta a
    `HORAS_SIN_FICHAR` o mas, o no se sabe. Si aplica:

        {"inicio", "horas", "horas_principal", "inicio_principal",
         "proximo_reset", "resuelve_antes", "caducidades"}

    (`caducidades`, las de `las_caducidades` de la foto). Nunca lanza.
    """
    try:
        from src.analysis.la_proxima_jornada import el_proximo_cierre

        cierre = el_proximo_cierre(ahora, calendario)
        horas = cierre.get("horas")
        if not cierre.get("parcial") or horas is None or horas >= HORAS_SIN_FICHAR:
            return None
        if not isinstance(cierre.get("inicio"), datetime):
            return None
        return {
            "inicio": cierre["inicio"], "horas": horas,
            "horas_principal": cierre.get("horas_principal"),
            "inicio_principal": cierre.get("inicio_principal"),
            "proximo_reset": cierre.get("proximo_reset"),
            "resuelve_antes": bool(cierre.get("resuelve_antes")),
            "caducidades": las_caducidades(snapshot, yo),
        }
    except Exception:                               # noqa: BLE001
        return None


def el_aplazado_publicado(aparte: dict | None) -> dict | None:
    """El `aparte` para el estado de la vuelta (JSON): las horas a dos
    decimales y las fechas en ISO, sin las caducidades. Nunca lanza."""
    try:
        if not isinstance(aparte, dict):
            return None

        def _iso(x):
            return x.isoformat() if isinstance(x, datetime) else None

        def _redondo(x):
            try:
                return round(float(x), 2)
            except (TypeError, ValueError):
                return None

        return {"inicio": _iso(aparte.get("inicio")), "horas": _redondo(aparte.get("horas")),
                "horas_principal": _redondo(aparte.get("horas_principal")),
                "inicio_principal": _iso(aparte.get("inicio_principal")),
                "proximo_reset": _iso(aparte.get("proximo_reset")),
                "resuelve_antes": bool(aparte.get("resuelve_antes"))}
    except Exception:                               # noqa: BLE001
        return None


def _no_se_cobra_en_jornada(pid, nombre) -> dict:
    return {
        "accion": "NADA", "player_id": pid, "nombre": nombre,
        "guardia": "JORNADA_EN_CURSO",
        "motivo": (
            "hay una jornada jugandose: no se acepta la oferta del "
            "Computer hasta que acabe"
        ),
    }


def el_reloj(ahora: datetime, calendario: Path | str | None = None) -> dict:
    """
    Lo que las guardias necesitan del calendario: `{"horas_jornada",
    "en_curso"}`. Las horas, las de los chollos (`horas_a_la_jornada`);
    si hay jornada jugandose, lo que diga la mejora del once
    (`jornada_en_curso`). Sin saberlo: horas None (no se puja) y en
    curso True (no se cobra). Nunca lanza.
    """

    reloj = {"horas_jornada": None, "en_curso": True}

    try:
        from src.actions.los_chollos import horas_a_la_jornada

        horas = horas_a_la_jornada(ahora, calendario)
        reloj["horas_jornada"] = (
            None if horas is None or isinstance(horas, bool) else float(horas)
        )
    except Exception:                               # noqa: BLE001
        reloj["horas_jornada"] = None

    try:
        from src.actions.la_mejora_del_once import jornada_en_curso

        reloj["en_curso"] = bool(
            jornada_en_curso(ahora) if calendario is None
            else jornada_en_curso(ahora, calendario)
        )
    except Exception:                               # noqa: BLE001
        reloj["en_curso"] = True

    return reloj


def leer_los_estados(snapshot: dict | None) -> dict:
    """
    `{player_id: status}` del catalogo de la foto de la vuelta
    (`catalog.data.players`), como lo leen los chollos. Vacio si no hay
    catalogo: entonces ningun relevo esta sano y no se vende. Nunca lanza.
    """

    try:
        catalogo = (
            (((snapshot or {}).get("catalog") or {}).get("data") or {})
            .get("players")
        ) or {}
        estados = {}
        for k, ficha in catalogo.items():
            pid = _int(k)
            if pid is not None and isinstance(ficha, dict):
                estados[pid] = ficha.get("status")
        return estados
    except Exception:                               # noqa: BLE001
        return {}


def ejecutar(acciones: list, escritor) -> list:
    """Manda las escrituras. Una por accion. Nunca lanza."""

    hechas = []

    for a in acciones:
        r = None
        try:
            if a["accion"] == "PUJAR":
                # La puja a un jugador de otro manager va a su nombre
                # (`vendedor`); la del Computer, como siempre, sin el.
                a_quien = (
                    {"seller_user_id": _int(a["vendedor"])}
                    if a.get("vendedor") else {}
                )
                r = escritor.place_bid(
                    player_id=a["player_id"], amount=a["importe"],
                    execute=True, **a_quien,
                )
                vieja = _int((a.get("sustituye") or {}).get("offer_id"))
                if vieja and r.get("sent"):
                    if r.get("success"):
                        # La nueva entro: se retira la vieja.
                        escritor.cancel_bid(offer_id=vieja, execute=True)
                    else:
                        # Biwenger no admite dos pujas por el mismo: se
                        # retira la vieja y se vuelve a pujar. Si esto
                        # falla, la vuelta siguiente la pone de nuevo.
                        escritor.cancel_bid(offer_id=vieja, execute=True)
                        r = escritor.place_bid(
                            player_id=a["player_id"], amount=a["importe"],
                            execute=True, **a_quien,
                        )
            elif a["accion"] == "CANCELAR_PUJA":
                r = escritor.cancel_bid(offer_id=a["offer_id"], execute=True)
            elif a["accion"] == "ACEPTAR_OFERTA_DEL_COMPUTER":
                r = escritor.accept_offer(offer_id=a["offer_id"], execute=True)
            elif a["accion"] == "PONER_A_LA_VENTA":
                r = escritor.list_player_for_sale(
                    player_id=a["player_id"], price=a["precio"],
                    execute=True,
                )
            else:
                hechas.append({**a, "enviada": False})
                continue

            hechas.append({
                **a,
                "enviada": bool((r or {}).get("sent")),
                "exito": (r or {}).get("success"),
                "http_status": (r or {}).get("http_status"),
            })

        except Exception as error:                  # noqa: BLE001
            hechas.append({
                **a, "enviada": False,
                "error": f"{type(error).__name__}: {error}",
            })

    return hechas


# ============================================================
# DE LA FOTO DE LA VUELTA A LO QUE `decidir` ENTIENDE
# ============================================================
#
#     cycle["snapshot"]["market"]["sales"]   lo que se vende; `user`
#                                            None = el Computer, `user.id`
#                                            nuestro = lo que publicamos
#     cycle["snapshot"]["market"]["offers"]  `from.id` nuestro = puja
#                                            nuestra; `from` None = oferta
#                                            por un jugador nuestro
#     cycle["snapshot"]["market"]["status"]  `maximumBid`
#     cycle["snapshot"]["my_team"]           nuestros jugadores, con `price`

def _pid(x):
    if isinstance(x, dict):
        return _int(x.get("id"))
    return _int(x)


def leer_la_foto(snapshot: dict | None, yo: int | None) -> dict:
    s = snapshot or {}
    market = s.get("market") or {}

    mercado, en_venta, precios = {}, set(), {}
    de_managers = {}

    for venta in market.get("sales") or []:
        pid = _pid(venta.get("player"))
        if pid is None:
            continue
        user = venta.get("user")
        if user is None:
            mercado[pid] = _int(venta.get("price"), 0)
        elif yo is not None and _pid(user) == yo:
            en_venta.add(pid)
        elif _pid(user) is not None:
            # Lo que vende otro manager: lo que pide y a quien se le puja
            # (16/10/2026, `la_ronda_de_la_manana.los_de_managers`).
            de_managers[pid] = {"precio": _int(venta.get("price"), 0),
                                "vendedor": _pid(user)}

    nuestras_pujas, recibidas = {}, {}

    for o in market.get("offers") or []:
        if str(o.get("status", "waiting")) != "waiting":
            continue
        jugadores = o.get("requestedPlayers") or []
        if len(jugadores) != 1:
            continue
        pid = _pid(jugadores[0])
        fila = {"offer_id": _int(o.get("id")), "amount": _int(o.get("amount"), 0)}
        desde = o.get("from")
        if desde is None:
            if fila["amount"] > recibidas.get(pid, {}).get("amount", -1):
                recibidas[pid] = fila
        elif yo is not None and _pid(desde) == yo:
            nuestras_pujas[pid] = fila

    plantilla = set()
    for j in s.get("my_team") or []:
        pid = _pid(j)
        if pid is not None:
            plantilla.add(pid)
            if _int(j.get("price")):
                precios[pid] = _int(j.get("price"))

    return {
        "mercado": mercado,
        "nuestras_pujas": nuestras_pujas,
        "plantilla": plantilla,
        "ofertas_del_computer": recibidas,
        "en_venta": en_venta,
        "de_managers": de_managers,
        "precios": precios,
        "maximo_de_puja": _int((market.get("status") or {}).get("maximumBid")),
        "saldo": _int((market.get("status") or {}).get("balance")),
    }


def correr(
    cycle: dict | None,
    escritor_factory=None,
    ruta: Path | str | None = None,
    ahora: datetime | None = None,
    calendario: Path | str | None = None,
) -> dict:
    """
    La orden, en esta vuelta. Devuelve lo que hizo. Nunca lanza.

    Las guardias (reloj, parte del relevo, jornada en curso) salen de
    `calendario` (el de los chollos si no se pasa) y del catalogo de la
    foto; lo que vio el reloj queda en `salida["reloj"]`. Con
    `BORDALAS_EL_APLAZADO_NO_FRENA_LA_COMPRA` y un aplazado a menos de
    `HORAS_SIN_FICHAR`, lo que vio de el queda en `salida["aplazado"]`
    (20/10/2026); si no, esa clave no esta.
    """

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": []}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        orden = leer_la_orden(ruta)
        ahora = ahora or datetime.now(timezone.utc)
        invalida = validar(orden, ahora)

        if invalida:
            salida["motivo"] = invalida
            return salida

        snapshot = (cycle or {}).get("snapshot") or {}
        yo = _pid(((snapshot.get("league") or {}).get("user")))

        if yo is None:
            salida["motivo"] = "SIN_SABER_QUIEN_SOY"
            return salida

        foto = leer_la_foto(snapshot, yo)
        # La orden solo ficha del Computer: lo de los managers es de la
        # puerta de la ronda (16/10/2026) y `decidir` no lo conoce.
        foto.pop("de_managers", None)
        reloj = el_reloj(ahora, calendario)
        salida["reloj"] = reloj
        # EL APLAZADO NO FRENA LA COMPRA (20/10/2026): solo con su
        # interruptor, y solo si lo que viene es un aplazado a menos de
        # `HORAS_SIN_FICHAR` (si no, None y todo como siempre).
        aparte = el_aplazado(ahora, calendario, snapshot, yo) if el_aplazado_activo() else None
        if aparte is not None:
            salida["aplazado"] = el_aplazado_publicado(aparte)
        acciones = decidir(
            orden, **foto, ahora=ahora,
            horas_jornada=reloj["horas_jornada"],
            en_curso=reloj["en_curso"],
            estados=leer_los_estados(snapshot),
            aparte=aparte,
        )
        salida["acciones"] = acciones

        if not [a for a in acciones if a["accion"] != "NADA"]:
            salida["motivo"] = "NADA_QUE_HACER"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        salida["hechas"] = ejecutar(acciones, escritor_factory())
        salida["motivo"] = "EJECUTADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida


def vetados(ruta: Path | str | None = None, ahora: datetime | None = None) -> set:
    """
    Los `no_pujar` de la orden viva, para que la subasta y el carril
    ni lo intenten. Vacio si la orden esta apagada, caducada o no vale.
    Nunca lanza.
    """

    try:
        if not activa():
            return set()
        orden = leer_la_orden(ruta)
        if validar(orden, ahora or datetime.now(timezone.utc)):
            return set()
        return {
            _int(n.get("player_id")) for n in orden.get("no_pujar") or []
            if _int(n.get("player_id"))
        }
    except Exception:                               # noqa: BLE001
        return set()


def protegidos(ruta: Path | str | None = None, ahora: datetime | None = None) -> set:
    """
    Los que no se publican mientras la orden viva: `proteger` y los de
    `fichar`. Vacio si esta apagada, caducada o no vale. Nunca lanza.
    """

    try:
        if not activa():
            return set()
        orden = leer_la_orden(ruta)
        if validar(orden, ahora or datetime.now(timezone.utc)):
            return set()
        ids = [
            _int(x.get("player_id"))
            for x in (orden.get("proteger") or []) + (orden.get("fichar") or [])
        ]
        return {i for i in ids if i}
    except Exception:                               # noqa: BLE001
        return set()


def conservados(ruta: Path | str | None = None, ahora: datetime | None = None) -> set:
    """
    Los que Pepe NO puede vender por su cuenta (aceptar ofertas en la
    liquidez o antes de caducar) mientras la orden viva: `conservar`,
    `proteger` y `fichar`. La orden si puede vender a los de `conservar`
    que tambien esten en `vender_si_ficha` (el ultimo recurso), porque
    llama al escritor directamente. Vacio si esta apagada, caducada o no
    vale. Nunca lanza.
    """

    try:
        if not activa():
            return set()
        orden = leer_la_orden(ruta)
        if validar(orden, ahora or datetime.now(timezone.utc)):
            return set()
        ids = [
            _int(x.get("player_id"))
            for x in (orden.get("conservar") or [])
            + (orden.get("proteger") or [])
            + (orden.get("fichar") or [])
        ]
        return {i for i in ids if i}
    except Exception:                               # noqa: BLE001
        return set()
