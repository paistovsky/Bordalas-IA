"""
LOS QUE OTROS VENDEN (12/10/2026)

POR QUE EXISTE

    El REROLL del orquestador (prioridad 670, la escritura de la vuelta)
    rechaza toda oferta del Computer a -2 % o peor de su valor si queda
    otro ciclo y su simulacion de solvencia pasa. No leia a nadie mas. La
    ronda (desde pagado + 1 %), los chollos, la mejora del once y el
    cierre (desde el 90 %) y la orden del gestor (`vender_si_ficha`, con
    su suelo: Jutgla a 2.466.000) cobran justo esas ofertas. Corren
    DESPUES del orquestador en la misma vuelta: el reroll tiraba la
    oferta que iban a aceptar, y la orden, la ronda y los chollos (que
    leen la foto de antes) mandaban un ACEPTAR que fallaba. Con la J9 el
    viernes 16/10 a las 21:00, cada oferta tirada empuja la venta hacia
    el ultimo reset.

LA REGLA

    Ningun reroll para un jugador que otro modulo tiene planeado vender:

        la ronda       claves de `data/trading/la_ronda.json`
        los chollos    claves de `data/trading/los_chollos.json`
        la mejora      claves (el que entra) y `sale` de cada cambio de
                       `data/trading/la_mejora.json`
        la orden       `vender_si_ficha.jugadores` de la orden VIVA
                       (encendida y valida, como la leen `vetados`,
                       `protegidos` y `conservados`)
        el cierre      `vender` y `candidatos` de
                       `data/trading/el_cierre.json` si su `generated_at`
                       es de las ultimas `HORAS_DEL_CIERRE`

    El orquestador saca a esos jugadores de los candidatos a reroll (y
    lo publica en `no_se_rerollean`) y `revalidate_reroll_offer` lo
    vuelve a mirar con los libros de ese momento, asi que el executor no
    puede rechazar una de esas ofertas.

QUE NO HACE

    No toca prioridades ni umbrales del reroll para nadie mas. No vende
    ni acepta nada. Solo lee: no escribe ningun libro.

    Nunca lanza. Un libro que falta o no se lee no aporta a nadie; si
    todo falla, conjunto vacio (el reroll de siempre).
"""

from __future__ import annotations

import importlib
import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


# El plan del cierre se publica en cada vuelta en la que esta encendido.
# Uno de hace mas de 3 h es de un cierre que ya no corre: no manda.
HORAS_DEL_CIERRE = 3

# Holgura para un `generated_at` un poco por delante del reloj (otro
# runner). Mas alla, el plan es raro y no se usa.
MINUTOS_POR_DELANTE = 10

# Los libros de cada modulo: sus propias constantes, no una copia.
_LIBROS = (
    ("ronda", "src.actions.la_ronda_de_la_manana", "LIBRO"),
    ("chollos", "src.actions.los_chollos", "LIBRO"),
    ("mejora", "src.actions.la_mejora_del_once", "LIBRO"),
    ("cierre", "src.actions.el_cierre_de_la_jornada", "PLAN"),
)


def _int(valor):
    try:
        if valor is None or isinstance(valor, bool):
            return None
        if isinstance(valor, dict):
            valor = valor.get("player_id", valor.get("id"))
            if valor is None or isinstance(valor, bool):
                return None
        return int(valor)
    except (TypeError, ValueError):
        return None


def _leer(ruta):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:                               # noqa: BLE001
        return None


def _cuando(texto):
    try:
        d = datetime.fromisoformat(str(texto))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _rutas_por_defecto() -> dict:
    """Los libros de cada modulo. `orden`: None = `la_orden_del_gestor.RUTA`."""
    rutas = {"orden": None}
    for nombre, modulo, atributo in _LIBROS:
        try:
            rutas[nombre] = getattr(importlib.import_module(modulo), atributo)
        except Exception:                           # noqa: BLE001
            rutas[nombre] = None
    return rutas


def _claves(libro) -> set:
    if not isinstance(libro, dict):
        return set()
    return {i for i in (_int(k) for k in libro) if i is not None}


def _de_la_mejora(libro) -> set:
    ids = _claves(libro)
    if isinstance(libro, dict):
        for cambio in libro.values():
            if isinstance(cambio, dict):
                sale = _int(cambio.get("sale"))
                if sale is not None:
                    ids.add(sale)
    return ids


def _de_la_orden(ruta, ahora) -> set:
    from src.actions import la_orden_del_gestor as orden_mod

    if not orden_mod.activa():
        return set()
    orden = orden_mod.leer_la_orden(ruta)
    if orden_mod.validar(orden, ahora):
        return set()
    jugadores = (orden.get("vender_si_ficha") or {}).get("jugadores") or []
    return {i for i in (_int(j) for j in jugadores) if i is not None}


def _del_cierre(plan, ahora) -> set:
    if not isinstance(plan, dict):
        return set()
    generado = _cuando(plan.get("generated_at"))
    if generado is None:
        return set()
    edad = ahora - generado
    if edad > timedelta(hours=HORAS_DEL_CIERRE) or edad < -timedelta(minutes=MINUTOS_POR_DELANTE):
        return set()
    ids = set()
    for clave in ("vender", "candidatos"):
        lista = plan.get(clave)
        if isinstance(lista, list):
            ids.update(i for i in (_int(x) for x in lista) if i is not None)
    return ids


def quien_los_vende(rutas: dict | None = None, ahora: datetime | None = None) -> dict:
    """
    {player_id: [modulos que lo van a vender]}. Pura salvo leer los
    libros. `rutas` sobrescribe las de `_rutas_por_defecto` (para las
    pruebas). Nunca lanza: lo que no se lee no aporta.
    """

    quien = {}
    try:
        ahora = ahora or datetime.now(timezone.utc)
        if ahora.tzinfo is None:
            ahora = ahora.replace(tzinfo=timezone.utc)
        rutas = {**_rutas_por_defecto(), **(rutas or {})}

        fuentes = (
            ("LA_RONDA", lambda: _claves(_leer(rutas["ronda"])) if rutas.get("ronda") else set()),
            ("LOS_CHOLLOS", lambda: _claves(_leer(rutas["chollos"])) if rutas.get("chollos") else set()),
            ("LA_MEJORA", lambda: _de_la_mejora(_leer(rutas["mejora"])) if rutas.get("mejora") else set()),
            ("LA_ORDEN_DEL_GESTOR", lambda: _de_la_orden(rutas.get("orden"), ahora)),
            ("EL_CIERRE", lambda: _del_cierre(_leer(rutas["cierre"]), ahora) if rutas.get("cierre") else set()),
        )
        for nombre, leer in fuentes:
            try:
                for pid in leer():
                    quien.setdefault(pid, []).append(nombre)
            except Exception:                       # noqa: BLE001
                continue
    except Exception:                               # noqa: BLE001
        return quien
    return quien


def los_de_la_oferta(oferta) -> set:
    """Los ids de una oferta del Computer (`player_ids`, `player_id`, `players`). Nunca lanza."""
    try:
        oferta = oferta if isinstance(oferta, dict) else {}
        crudos = list(oferta.get("player_ids") or []) + [oferta.get("player_id")]
        crudos += [p.get("id") for p in (oferta.get("players") or []) if isinstance(p, dict)]
        return {i for i in (_int(c) for c in crudos if not isinstance(c, dict)) if i is not None}
    except Exception:                               # noqa: BLE001
        return set()


def los_que_otros_venden(rutas: dict | None = None, ahora: datetime | None = None) -> set:
    """Los ids que algun otro modulo va a vender. Nunca lanza."""
    try:
        return set(quien_los_vende(rutas, ahora))
    except Exception:                               # noqa: BLE001
        return set()
