"""
LOS CHOLLOS DEL PRECIO FIJO (02/10/2026)

POR QUE EXISTE

    Lo vio el dueño con Moi Gómez (01/10) y lo confirmó el laboratorio
    (E12): la venta del Computer pide el valor del día en que salió y no
    se mueve; el valor sí. Si el jugador sube mientras sigue a la venta,
    vale más de lo que pide y se puede comprar por debajo de lo que vale.
    Los rivales lo pujan a «lo que pide + 7 €». Poco dinero (E12: +50-100
    mil a la semana), pero gratis.

LA REGLA (la del dueño, 02/10)

    1. Cuándo: un jugador del Computer a la venta que hoy vale más de lo
       que pide.
    2. Cuánto: siempre, aunque haya más pujas, entre lo que pide y lo que
       vale, nunca por encima de su valor: valor - 1.000 € (o a mitad de
       camino si el hueco es menor de 2.000 €).
    3. Después: se revende al Computer en cuanto ofrezca más de lo pagado.
    4. Prioridad: detrás de las pujas normales. Solo puja en la última
       vuelta antes del reset (las pujas normales ya están puestas) y con
       lo que quede de `maximumBid` menos `RESERVA`.
    5. Cerca de una jornada (menos de `HORAS_SOLO_CAJA`), solo con caja
       propia: saldo - pujas vivas - esta puja >= 0. Sin calendario, igual.

QUE NO HACE

    No compra a rivales, ni lesionados, ni a quien ya tenemos. No sube la
    puja de nadie. Lo comprado y lo pagado se apunta en `LIBRO`, que es lo
    único que se revende como chollo.

    Nace APAGADA: `BORDALAS_LOS_CHOLLOS`. Nunca lanza.
"""

from __future__ import annotations

import json
import os

from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_LOS_CHOLLOS"
RAIZ = Path(__file__).parents[2]
LIBRO = RAIZ / "data" / "trading" / "los_chollos.json"
CALENDARIO = RAIZ / "data" / "calendar" / "laliga_calendar.json"

MINUTOS_ULTIMA_VUELTA = 65      # las vueltas son cada hora: la última antes del reset
RESERVA = 0                     # lo que se deja sin tocar de `maximumBid`
TOPE_POR_DIA = 3_000_000
HORAS_SOLO_CAJA = 72
DESCUENTO = 1_000
MALOS = frozenset({"injured", "doubt", "sanctioned"})


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError):
        return defecto


def la_puja(pide: int, vale: int) -> int | None:
    """Entre lo que pide y lo que vale, nunca por encima. None si no hay hueco."""
    hueco = vale - pide
    if hueco <= 1:
        return None
    if hueco >= 2 * DESCUENTO:
        return vale - DESCUENTO
    return pide + hueco // 2


def horas_a_la_jornada(ahora: datetime, ruta: Path | str | None = None):
    """Horas hasta el primer partido futuro del calendario. None si no se sabe."""
    try:
        d = json.loads(Path(ruta or CALENDARIO).read_text())
        futuros = []
        for j in d.get("matchdays") or []:
            k = j.get("first_kickoff")
            if not k:
                continue
            t = datetime.fromisoformat(k)
            if t > ahora:
                futuros.append(t)
        if not futuros:
            return None
        return (min(futuros) - ahora).total_seconds() / 3600
    except Exception:                               # noqa: BLE001
        return None


def decidir(
    *, mercado, valores, estados, nuestras_pujas, plantilla,
    ofertas_del_computer, en_venta, maximo_de_puja, saldo,
    minutos_al_reset, horas_jornada, libro,
) -> list:
    """Qué hacer con los chollos. Pura."""

    acciones = []

    # 3. REVENDER lo comprado como chollo.
    for pid, pagado in (libro or {}).items():
        pid = _int(pid)
        if pid not in plantilla:
            continue
        oferta = ofertas_del_computer.get(pid)
        if oferta and _int(oferta.get("amount"), 0) > _int(pagado, 0):
            acciones.append({
                "accion": "ACEPTAR_OFERTA_DEL_COMPUTER", "player_id": pid,
                "offer_id": _int(oferta.get("offer_id")),
                "importe": _int(oferta.get("amount")), "pagado": pagado,
                "chollo": True,
            })
        elif pid not in en_venta and _int(valores.get(pid)):
            acciones.append({
                "accion": "PONER_A_LA_VENTA", "player_id": pid,
                "precio": _int(valores.get(pid)), "chollo": True,
            })

    # 4. Solo en la última vuelta antes del reset.
    if minutos_al_reset is None or minutos_al_reset > MINUTOS_ULTIMA_VUELTA:
        return acciones

    # 5. Cerca de la jornada (o sin calendario), solo con caja propia.
    comprometido = sum(_int(p.get("amount"), 0) for p in nuestras_pujas.values())
    solo_caja = horas_jornada is None or horas_jornada < HORAS_SOLO_CAJA
    if solo_caja:
        disponible = (_int(saldo, 0) or 0) - comprometido
    else:
        disponible = (_int(maximo_de_puja, 0) or 0) - RESERVA
    disponible = min(disponible, TOPE_POR_DIA)

    # 1-2. Los que valen más de lo que piden, el mayor hueco primero.
    candidatos = []
    for pid, pide in mercado.items():
        vale = _int(valores.get(pid))
        if not vale or not pide or pid in plantilla or pid in nuestras_pujas:
            continue
        if str(estados.get(pid) or "").lower() in MALOS:
            continue
        puja = la_puja(pide, vale)
        if puja:
            candidatos.append((vale - puja, pid, pide, vale, puja))

    for _, pid, pide, vale, puja in sorted(candidatos, reverse=True):
        if puja > disponible:
            continue
        disponible -= puja
        acciones.append({
            "accion": "PUJAR", "player_id": pid, "importe": puja,
            "pide": pide, "vale": vale, "sustituye": None, "chollo": True,
        })

    return acciones


def leer_libro(ruta: Path | str | None = None) -> dict:
    try:
        return json.loads(Path(ruta or LIBRO).read_text())
    except Exception:                               # noqa: BLE001
        return {}


def correr(cycle, minutos_al_reset, escritor_factory=None,
           ahora: datetime | None = None, libro_ruta=None) -> dict:
    """Los chollos, en esta vuelta. Nunca lanza."""

    salida = {"activa": activa(), "motivo": None, "acciones": [], "hechas": []}

    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADA"
            return salida

        from src.actions.la_orden_del_gestor import (
            _pid, ejecutar, leer_la_foto, vetados,
        )

        ahora = ahora or datetime.now(timezone.utc)
        snapshot = (cycle or {}).get("snapshot") or {}
        yo = _pid((snapshot.get("league") or {}).get("user"))
        foto = leer_la_foto(snapshot, yo)

        catalogo = (((snapshot.get("catalog") or {}).get("data") or {}).get("players")) or {}
        valores, estados = {}, {}
        for k, f in catalogo.items():
            pid = _int(k)
            if pid is not None and isinstance(f, dict):
                valores[pid] = _int(f.get("price"))
                estados[pid] = f.get("status")

        veto = vetados()
        mercado = {p: v for p, v in foto["mercado"].items() if p not in veto}

        libro = leer_libro(libro_ruta)
        acciones = decidir(
            mercado=mercado, valores=valores, estados=estados,
            nuestras_pujas=foto["nuestras_pujas"], plantilla=foto["plantilla"],
            ofertas_del_computer=foto["ofertas_del_computer"],
            en_venta=foto["en_venta"], maximo_de_puja=foto["maximo_de_puja"],
            saldo=foto["saldo"], minutos_al_reset=minutos_al_reset,
            horas_jornada=horas_a_la_jornada(ahora), libro=libro,
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

        # El libro: lo pujado queda apuntado para revenderlo si se gana;
        # lo vendido sale. Lo que no se gane no estará en la plantilla y
        # se limpia solo a los dos días.
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
