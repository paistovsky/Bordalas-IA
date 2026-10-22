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

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_LA_ORDEN_DEL_GESTOR"

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
    """

    acciones = []
    retiradas = set()

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
        pagan_sus_ventas = _la_pagan_sus_ventas(
            orden, f, puja, saldo, nuestras_pujas, plantilla, ofertas_del_computer,
        )
        if (horas_jornada is None or horas_jornada < HORAS_SIN_FICHAR) and not _la_paga_la_caja(
            orden, pid, puja, saldo, nuestras_pujas,
        ) and not pagan_sus_ventas:
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

        accion = {
            "accion": "PUJAR", "player_id": pid,
            "nombre": f.get("nombre"), "importe": puja,
            "sustituye": ya,
        }
        if pagan_sus_ventas and horas_jornada is not None and horas_jornada < HORAS_SIN_FICHAR:
            accion["guardia"] = "LA_PAGAN_SUS_VENTAS"
        acciones.append(accion)

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
                elif parte in FUERA and str(
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


def _la_pagan_sus_ventas(orden, f, puja, saldo, nuestras_pujas, plantilla,
                         ofertas_del_computer) -> bool:
    """
    LA PAGAN SUS VENTAS (22/10/2026). Boye sale al mercado el jueves 22/10
    y su subasta se resuelve el viernes a las 07:00, 14 h antes de la J10:
    el reloj no deja pujar (los que salen cobrarian el sabado). Pero
    nuestros titulares ya tienen oferta viva del Computer: aceptada en la
    vuelta de despues del reset, la caja esta en positivo antes del
    partido. El reloj no sabia mirar eso (el mismo hueco que con Kubo).

    Solo si el gestor lo escribe en el fichaje
    (`"la_pagan_sus_ventas": true`): no lo decide Pepe. Y solo si saldo -
    las demas pujas vivas + las ofertas vivas del Computer por los que
    salen por ESTE fichaje (el `si_esta` general o el suyo apuntan a el,
    siguen siendo nuestros y su oferta llega a su `suelo`) pagan la puja
    entera. Una oferta que caduca en el reset se cuenta: el Computer
    renueva la oferta de los publicados en ese mismo reset (el riesgo lo
    asume el gestor al escribirlo). Nunca lanza.
    """

    try:
        if not isinstance(f, dict) or f.get("la_pagan_sus_ventas") is not True:
            return False
        pid = _int(f.get("player_id"))
        if pid is None or saldo is None or puja is None:
            return False
        venta = orden.get("vender_si_ficha") or {}
        general = _int(venta.get("si_esta"))
        plantilla = set(plantilla or ())
        cobro = 0
        for j in venta.get("jugadores") or []:
            sale = _int(j.get("player_id"))
            suyo = _int(j.get("si_esta"))
            if sale not in plantilla or pid not in {general, suyo}:
                continue
            if suyo is not None and general is not None and suyo != general:
                continue
            importe = _int(((ofertas_del_computer or {}).get(sale) or {}).get("amount"), 0) or 0
            if importe >= (_int(j.get("suelo"), 0) or 0):
                cobro += importe
        vivas = sum(
            _int((p or {}).get("amount"), 0) or 0
            for q, p in (nuestras_pujas or {}).items() if q != pid
        )
        return cobro > 0 and saldo - vivas + cobro >= puja
    except Exception:                               # noqa: BLE001
        return False


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
    foto; lo que vio el reloj queda en `salida["reloj"]`.
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
        acciones = decidir(
            orden, **foto, ahora=ahora,
            horas_jornada=reloj["horas_jornada"],
            en_curso=reloj["en_curso"],
            estados=leer_los_estados(snapshot),
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
