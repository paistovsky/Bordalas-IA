"""
LA RONDA DE LA MAÑANA (12/10/2026)

POR QUE EXISTE

    Lo pidió el dueño el 12/10: «cada día, revisar quiénes están nuevos
    en el mercado, leer sus noticias y pujar por todos los que se pueda
    si van a subir». Es lo que hacen Pollo17 y Luismi (E28: ~2-2,5 M a
    la semana): compran al Computer a quien SUBE (E1), tiran de la
    deuda entre jornadas y se lo revenden al Computer a los pocos días,
    liquidando antes de cada jornada. A Pepe la reventa le cabe en la
    caja libre, y la caja libre casi nunca llega: no lo hacemos nunca.

LA REGLA

    1. A quién: del Computer, no nuestro, sin puja nuestra, no vetado ni
       protegido por el gestor, estado «ok» (las noticias solo como
       guardia, E4: ni lesionados, ni dudas, ni sancionados, ni lo que no
       se sepa), subiendo (`priceIncrement` > 0, E1) y que juega y puntúa
       (3 partidos o más y 3 puntos por partido o más). Primero el que
       más sube en proporción a su precio.
    2. Cuánto: precio + 1 % redondeado a miles (E9: sin pelear la
       subasta). Como mucho `TOPE_POR_VIAJE` por jugador; todo lo de la
       ronda (pujas vivas + lo comprado, a lo pagado) como mucho
       `TOPE_TOTAL` (sin tope: «se ejecuta toda la deuda»); y nunca más
       que `maximumBid` - `RESERVA` (que ya descuenta las pujas vivas).
    3. Cuándo: en CADA vuelta (el dueño, 12/10: «revisión cada ciclo,
       que para eso está 24/7») salvo en la zona de silencio, y solo si
       la jornada está a `HORAS_SIN_COMPRAR` o más. Sin calendario, no
       compra.
    4. Salida (solo lo del libro y lo que tenemos): se publica a su valor;
       se acepta la oferta del Computer con beneficio (pagado + 1 %); el
       primer día que baja (E3), a pagado - 2 %; a menos de
       `HORAS_LIQUIDAR` de la jornada, a pagado - 7 %; a menos de
       `HORAS_SOLVENCIA`, lo que ofrezca (en rojo al empezar la jornada
       se hacen 0 puntos).

QUE NO HACE

    No compra a rivales, no sube pujas, no vende a nadie que no haya
    comprado ella (lo apunta en `LIBRO`) ni a un protegido del gestor.

    Nace APAGADA: `BORDALAS_LA_RONDA_DE_LA_MANANA`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from pathlib import Path

from src.actions.los_chollos import (
    MINUTOS_ULTIMA_VUELTA, _int, _puede_escribir, horas_a_la_jornada,
)


ENV = "BORDALAS_LA_RONDA_DE_LA_MANANA"
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "la_ronda.json"

TOPE_POR_VIAJE = 3_000_000
TOPE_TOTAL = None                # el dueño (12/10): «se ejecuta toda la deuda»; manda maximumBid - RESERVA
RESERVA = 1_000_000             # lo que se deja sin tocar de `maximumBid`
HORAS_SIN_COMPRAR = 40           # lo comprado tiene que recibir al menos una oferta del Computer (en el reset) antes de la jornada
HORAS_LIQUIDAR = 36
HORAS_SOLVENCIA = 20
SUBE = 1.01                     # la puja (E9) y el beneficio mínimo
BAJA = 0.98                     # el primer día que baja (E3)
LIQUIDA = 0.93                  # cerca de la jornada
PUNTOS_POR_PARTIDO = 3.0
PARTIDOS_MINIMOS = 3


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def la_puja(precio: int) -> int:
    """Precio + 1 %, redondeado a miles (E9)."""
    return int(round(precio * SUBE, -3))


def el_suelo(pagado: int, incremento, horas_jornada) -> int:
    """Lo mínimo que se acepta del Computer por un jugador de la ronda."""
    suelo = SUBE
    if (_int(incremento, 0) or 0) < 0:
        suelo = min(suelo, BAJA)
    # Sin calendario se trata como cerca (liquidar), pero no a cualquier precio.
    if horas_jornada is None or horas_jornada < HORAS_LIQUIDAR:
        suelo = min(suelo, LIQUIDA)
    if horas_jornada is not None and horas_jornada < HORAS_SOLVENCIA:
        return 0
    return int(pagado * suelo)


def juega(ficha: dict) -> bool:
    """3 partidos o más y 3 puntos por partido o más."""
    partidos = (_int(ficha.get("playedHome"), 0) or 0) + (_int(ficha.get("playedAway"), 0) or 0)
    if partidos < PARTIDOS_MINIMOS:
        return False
    return (_int(ficha.get("points"), 0) or 0) / partidos >= PUNTOS_POR_PARTIDO


def decidir(
    *, mercado, fichas, nuestras_pujas, plantilla, ofertas_del_computer,
    en_venta, maximo_de_puja, minutos_al_reset, horas_jornada, libro,
    protegidos=frozenset(), puede_escribir=True,
) -> list:
    """Qué hace la ronda en esta vuelta. Pura.

        fichas   {player_id: ficha del catálogo} (price, priceIncrement,
                 status, points, playedHome, playedAway)
        libro    {"player_id": lo pagado} de lo comprado por la ronda
    """

    acciones = []
    protegidos = set(protegidos or ())

    # 4. SALIR de lo comprado por la ronda.
    for pid, pagado in (libro or {}).items():
        pid, pagado = _int(pid), _int(pagado, 0) or 0
        if pid not in plantilla or pid in protegidos or pagado <= 0:
            continue
        ficha = fichas.get(pid) or {}
        suelo = el_suelo(pagado, ficha.get("priceIncrement"), horas_jornada)
        oferta = ofertas_del_computer.get(pid)
        if oferta and (_int(oferta.get("amount"), 0) or 0) >= suelo:
            acciones.append({
                "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                "offer_id": _int(oferta.get("offer_id")),
                "importe": _int(oferta.get("amount")), "pagado": pagado,
                "suelo": suelo, "ronda": True,
            })
        elif pid not in en_venta and _int(ficha.get("price")):
            acciones.append({
                "accion": "PONER_A_LA_VENTA", "player_id": pid,
                "precio": _int(ficha.get("price")), "ronda": True,
            })

    # 3. EN CADA VUELTA (el dueño, 12/10: «revisión cada ciclo, que para
    # eso está 24/7»), salvo en la zona de silencio, y lejos de la jornada.
    if (
        not puede_escribir
        or horas_jornada is None
        or horas_jornada < HORAS_SIN_COMPRAR
    ):
        return acciones

    # 2. Lo que ya lleva la ronda: pujas vivas + lo comprado, a lo pagado.
    expuesto = 0
    for pid, pagado in (libro or {}).items():
        pid = _int(pid)
        if pid in nuestras_pujas:
            expuesto += _int(nuestras_pujas[pid].get("amount"), 0) or 0
        elif pid in plantilla:
            expuesto += _int(pagado, 0) or 0
    disponible = (_int(maximo_de_puja, 0) or 0) - RESERVA

    # 1. Los que suben, están bien y juegan; el que más sube primero.
    candidatos = []
    for pid, precio in mercado.items():
        ficha = fichas.get(pid) or {}
        if not precio or pid in plantilla or pid in nuestras_pujas or pid in protegidos:
            continue
        if str(ficha.get("status") or "").lower() != "ok":
            continue
        sube = _int(ficha.get("priceIncrement"), 0) or 0
        if sube <= 0 or not juega(ficha):
            continue
        candidatos.append((sube / precio, pid, precio, sube))

    for _, pid, precio, sube in sorted(candidatos, reverse=True):
        puja = la_puja(precio)
        if puja > TOPE_POR_VIAJE or (TOPE_TOTAL is not None and expuesto + puja > TOPE_TOTAL) or puja > disponible:
            continue
        expuesto += puja
        disponible -= puja
        acciones.append({
            "accion": "PUJAR", "player_id": pid, "importe": puja,
            "pide": precio, "sube": sube, "sustituye": None, "ronda": True,
        })

    return acciones


def leer_libro(ruta: Path | str | None = None) -> dict:
    try:
        return json.loads(Path(ruta or LIBRO).read_text())
    except Exception:                               # noqa: BLE001
        return {}


def correr(cycle, minutos_al_reset, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None) -> dict:
    """La ronda, en esta vuelta. Nunca lanza."""

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": []}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _pid, ejecutar, leer_la_foto, protegidos, vetados,
        )

        ahora = ahora or datetime.now(timezone.utc)
        snapshot = (cycle or {}).get("snapshot") or {}
        yo = _pid((snapshot.get("league") or {}).get("user"))
        foto = leer_la_foto(snapshot, yo)

        catalogo = (((snapshot.get("catalog") or {}).get("data") or {}).get("players")) or {}
        fichas = {}
        for k, f in catalogo.items():
            pid = _int(k)
            if pid is not None and isinstance(f, dict):
                fichas[pid] = f

        veto = vetados()
        mercado = {p: v for p, v in foto["mercado"].items() if p not in veto}

        libro = leer_libro(libro_ruta)
        acciones = decidir(
            mercado=mercado, fichas=fichas,
            nuestras_pujas=foto["nuestras_pujas"], plantilla=foto["plantilla"],
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=foto["en_venta"], maximo_de_puja=foto["maximo_de_puja"],
            minutos_al_reset=minutos_al_reset,
            horas_jornada=horas_a_la_jornada(ahora), libro=libro,
            protegidos=protegidos(), puede_escribir=_puede_escribir(ahora),
        )
        salida["acciones"] = acciones

        if not acciones:
            salida["motivo"] = "NADA_QUE_HACER"
            return salida

        if escritor_factory is None:
            from src.biwenger.write_client import BiwengerWriteClient

            escritor_factory = BiwengerWriteClient

        hechas = ejecutar(acciones, escritor_factory())
        salida["hechas"] = hechas

        # El libro, como el de los chollos: lo pujado queda apuntado para
        # revenderlo si se gana; lo vendido sale; lo que ni es nuestro ni
        # tiene puja viva se limpia solo.
        for pid in list(libro):
            if _int(pid) not in foto["plantilla"] and _int(pid) not in foto["nuestras_pujas"]:
                libro.pop(pid, None)
        for h in hechas:
            pid = str(h.get("player_id"))
            if h.get("accion") == "PUJAR" and h.get("exito"):
                libro[pid] = h.get("importe")
            elif h.get("accion") == "ACEPTAR_OFERTA_DEL_COMPUTER" and h.get("exito"):
                libro.pop(pid, None)
        try:
            ruta = Path(libro_ruta or LIBRO)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(libro, indent=2) + "\n")
        except Exception:                           # noqa: BLE001
            pass

        salida["motivo"] = "EJECUTADA"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"

    return salida
