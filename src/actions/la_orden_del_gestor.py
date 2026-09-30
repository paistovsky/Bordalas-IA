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

QUE NO HACE

    No decide nada: ejecuta lo escrito. No acepta ofertas de managers,
    no vende a nadie que no este en la orden, no toca a Yamal (se
    rechaza la orden entera si lo nombra), no puja por encima de
    `maximumBid`. Una escritura por jugador y vuelta como mucho.

    Nace APAGADA: `BORDALAS_LA_ORDEN_DEL_GESTOR`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_LA_ORDEN_DEL_GESTOR"

RUTA = Path("config") / "la_orden_del_gestor.json"

# Nunca se vende. Regla de la casa.
INTOCABLES = frozenset({"yamal", "lamine yamal"})


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

    if any(n in INTOCABLES for n in nombres):
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
    """

    acciones = []

    # 1. FICHAR
    for f in orden.get("fichar") or []:
        pid = _int(f.get("player_id"))
        puja = _int(f.get("puja"))

        if pid in plantilla or pid not in mercado:
            continue

        ya = nuestras_pujas.get(pid)

        if ya and _int(ya.get("amount"), 0) >= puja:
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

        acciones.append({
            "accion": "PUJAR", "player_id": pid,
            "nombre": f.get("nombre"), "importe": puja,
            "sustituye": ya,
        })

    # 2. NO PUJAR
    for n in orden.get("no_pujar") or []:
        pid = _int(n.get("player_id"))
        ya = nuestras_pujas.get(pid)

        if ya and _int(ya.get("offer_id")):
            acciones.append({
                "accion": "CANCELAR_PUJA", "player_id": pid,
                "nombre": n.get("nombre"),
                "offer_id": _int(ya.get("offer_id")),
            })

    # 3. VENDER, SOLO SI EL FICHAJE YA ES NUESTRO
    venta = orden.get("vender_si_ficha") or {}
    condicion = _int(venta.get("si_esta"))

    if condicion and condicion in plantilla:
        for j in venta.get("jugadores") or []:
            pid = _int(j.get("player_id"))
            nombre = str(j.get("nombre", ""))

            if pid not in plantilla or nombre.strip().lower() in INTOCABLES:
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

            suelo = _int(j.get("suelo"), 0)
            oferta = ofertas_del_computer.get(pid)

            if oferta and _int(oferta.get("amount"), 0) >= suelo:
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


def ejecutar(acciones: list, escritor) -> list:
    """Manda las escrituras. Una por accion. Nunca lanza."""

    hechas = []

    for a in acciones:
        r = None
        try:
            if a["accion"] == "PUJAR":
                r = escritor.place_bid(
                    player_id=a["player_id"], amount=a["importe"],
                    execute=True,
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
                            execute=True,
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

    for venta in market.get("sales") or []:
        pid = _pid(venta.get("player"))
        if pid is None:
            continue
        user = venta.get("user")
        if user is None:
            mercado[pid] = _int(venta.get("price"), 0)
        elif yo is not None and _pid(user) == yo:
            en_venta.add(pid)

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
        "precios": precios,
        "maximo_de_puja": _int((market.get("status") or {}).get("maximumBid")),
        "saldo": _int((market.get("status") or {}).get("balance")),
    }


def correr(
    cycle: dict | None,
    escritor_factory=None,
    ruta: Path | str | None = None,
    ahora: datetime | None = None,
) -> dict:
    """La orden, en esta vuelta. Devuelve lo que hizo. Nunca lanza."""

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
        acciones = decidir(orden, **foto, ahora=ahora)
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
