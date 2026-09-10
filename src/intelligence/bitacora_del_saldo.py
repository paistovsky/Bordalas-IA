"""
La bitacora del saldo: `maximumBid` guardado para poder restar.

POR QUE EXISTE

    La via mas solida para ver una puja del dueno es la
    diferencia entre dos fotos: mismo saldo, `maximumBid` mas
    bajo, sin reset por medio. No necesita saber cuanto vale la
    linea de credito.

    Pero para restar hacen falta DOS fotos, y hasta hoy solo
    existia la de ahora. Esto guarda una linea por vuelta para
    que la resta se pueda hacer siempre.

POR QUE NO VA EN EL ARCHIVO DIARIO

    El encargo pedia guardarlo "en el archivo diario". No cabe:
    `archivo_diario` guarda INFORMES de fuentes -scout, prensa-,
    con una carpeta por dia nombrada por el `generated_at` del
    informe y una poda a 60 dias. Meter una serie numerica de
    cuatro campos ahi obligaria a inventar un informe falso con
    su fecha de generacion.

    Esto es otra cosa: una linea por vuelta, en orden, para
    restar. Un JSONL sirve mejor y no rompe la forma del
    archivo. Se dice aqui para que se pueda discutir.

EL CENSO DE OFERTAS, EN EL MISMO SITIO

    La segunda medicion diaria: que trae la tanda nueva del
    Computer en cada reset. Contesta a "¿hace falta vender a
    ciegas la noche antes?" con datos en vez de con nervios.

    CUAL ES LA TANDA NUEVA, MEDIDO (10/09/2026)

        Una oferta del Computer vive 47,9 h -54 de las 64 con
        fecha en las fotos del 11-17/08-, se crea a las 05:03
        UTC (07:03 de Madrid, justo despues del reset) y caduca
        en un reset dos dias despues.

        Asi que conviven DOS tandas, y la NUEVA es la de
        caducidad MAS LEJANA, no la mas cercana.

ESTE MODULO SI TOCA DISCO

    Es un almacen, no una guardia. Todas las funciones aceptan
    `ruta` para poder probarlas sin escribir en `data/`.
    Ninguna lanza: perder una anotacion no puede tumbar un
    ciclo.
"""

from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path


DIRECTORIO = Path("data") / "solvency"

BITACORA = DIRECTORIO / "bitacora_del_saldo.jsonl"

CENSO = DIRECTORIO / "censo_de_ofertas.jsonl"


# Lo medido el 10/09/2026 sobre 64 ofertas con fecha.
VIDA_DE_UNA_OFERTA_HORAS = 47.9

OFERTAS_MEDIDAS = 64


# Cuantas lineas se guardan. A una por vuelta y una vuelta por
# hora, esto es mes y medio.
LINEAS_QUE_SE_GUARDAN = 1000


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _euros(valor) -> str:
    """
    El separador de miles, APARTE de la frase.

    `f"frase, {n:,}".replace(",", ".")` se come las comas de la
    prosa: la primera version de esta linea decia "por
    30.595.000 EUR. de las que 2 son...". Ya ha pasado seis
    veces en esta casa; por eso ya no se escribe a mano.
    """

    try:
        return f"{int(valor):,}".replace(",", ".")

    except (TypeError, ValueError):
        return "?"


def _leer(ruta: Path) -> list:
    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines()

    except Exception:                               # noqa: BLE001
        return []

    filas = []

    for linea in lineas:

        linea = linea.strip()

        if not linea:
            continue

        try:
            fila = json.loads(linea)

        except Exception:                           # noqa: BLE001
            continue

        if isinstance(fila, dict):
            filas.append(fila)

    return filas


def _apendar(fila: dict, ruta: Path, tope: int) -> bool:
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        filas = _leer(ruta)

        filas.append(fila)

        ruta.write_text(
            "\n".join(
                json.dumps(f, ensure_ascii=False)
                for f in filas[-tope:]
            )
            + "\n",
            encoding="utf-8",
        )

        return True

    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# LA BITACORA DEL SALDO
# ============================================================

def ultima_lectura(ruta: Path | None = None) -> dict | None:
    """
    La foto anterior, para poder restar contra ella.

    Devuelve None si no hay ninguna: el primer dia no hay resta
    que hacer, y eso no es un fallo.
    """

    filas = _leer(ruta or BITACORA)

    return filas[-1] if filas else None


def apuntar_lectura(
    balance,
    maximum_bid,
    roster_value=None,
    hours_to_reset=None,
    committed=None,
    source=None,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Una linea por vuelta. Nunca lanza.
    """

    fila = {
        "at": at or _ahora(),
        "balance": safe_int(balance),
        "maximum_bid": safe_int(maximum_bid),
        "roster_value": safe_int(roster_value),
        "hours_to_reset": safe_float(hours_to_reset),
        "committed": safe_int(committed),
        "source": source,
    }

    fila["written"] = _apendar(
        fila, ruta or BITACORA, LINEAS_QUE_SE_GUARDAN
    )

    return fila


# ============================================================
# EL CENSO DE OFERTAS DE CADA RESET
# ============================================================

def cohorte_nueva(offers, hours_to_reset) -> list:
    """
    La tanda que acaba de publicar el Computer.

    Es la de caducidad MAS LEJANA: una oferta vive 47,9 h, asi
    que la recien nacida caduca dentro de casi dos dias y la
    vieja en el proximo reset.

    Sin `hours_to_reset` no se puede separar, y devuelve vacio en
    vez de adivinar.
    """

    horas = safe_float(hours_to_reset)

    filas = [
        o for o in (offers or [])
        if isinstance(o, dict)
        and safe_float(o.get("hours_to_expiry")) is not None
    ]

    if not filas or horas is None:
        return []

    # La nueva caduca al menos un ciclo del Computer despues del
    # proximo reset. Con 12 h de margen no se confunde con la
    # vieja, que caduca en el reset de manana.
    return [
        o for o in filas
        if safe_float(o["hours_to_expiry"]) > horas + 12.0
    ]


def censar_el_reset(
    offers,
    hours_to_reset,
    starters=None,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Cuantas ofertas trae la tanda nueva, por cuanto, y cuantas
    son de gente que no juega.

    LA PREGUNTA QUE CONTESTA

        "¿Hace falta vender a ciegas la noche antes de un reset?"

        Si el Computer publica todas las mananas una tanda que
        tapa el agujero con gente del banquillo, la respuesta es
        que no hace falta nunca. Con dos observaciones no se
        sabe. Con treinta, si.

    Una linea por reset. Si ya hay una de este reset, no se
    duplica.
    """

    vacio = {
        "available": False,
        "offers": 0,
        "total": 0,
        "bench_offers": 0,
        "bench_total": 0,
        "reason": None,
    }

    try:
        nueva = cohorte_nueva(offers, hours_to_reset)

        if not nueva:
            return {
                **vacio,
                "reason": (
                    "No se puede separar la tanda nueva sin "
                    "saber cuanto falta para el reset, o no hay "
                    "ofertas."
                ),
            }

        titulares = {str(n) for n in (starters or []) if n}

        def _nombre(oferta) -> str:
            nombres = oferta.get("players") or []

            return str(
                oferta.get("player_name")
                or (nombres[0] if nombres else "")
            )

        # Un jugador protegido no es liquidez: contarlo diria que
        # el agujero se tapa con dinero que no se va a tocar.
        cobrables = [
            o for o in nueva
            if o.get("protection") != "NEVER_AUTO_SELL"
        ]

        banquillo = [
            o for o in cobrables
            if _nombre(o) not in titulares
        ]

        fila = {
            "at": at or _ahora(),
            "offers": len(nueva),
            "total": sum(safe_int(o.get("amount")) for o in nueva),
            "sellable_offers": len(cobrables),
            "sellable_total": sum(
                safe_int(o.get("amount")) for o in cobrables
            ),
            "bench_offers": len(banquillo),
            "bench_total": sum(
                safe_int(o.get("amount")) for o in banquillo
            ),
            "players": [
                {
                    "name": _nombre(o),
                    "amount": safe_int(o.get("amount")),
                    "starter": _nombre(o) in titulares,
                }
                for o in nueva
            ],
        }

        ruta_final = ruta or CENSO

        # Una por reset: se compara contra la ultima por el dia.
        anteriores = _leer(ruta_final)

        hoy = str(fila["at"])[:10]

        if anteriores and str(anteriores[-1].get("at"))[:10] == hoy:
            return {
                **fila,
                "available": True,
                "written": False,
                "reason": (
                    "Ya hay censo de este reset: no se duplica."
                ),
            }

        escrito = _apendar(
            fila, ruta_final, LINEAS_QUE_SE_GUARDAN
        )

        return {
            **fila,
            "available": True,
            "written": escrito,
            "reason": (
                f"Tanda nueva: {fila['offers']} ofertas por "
                f"{_euros(fila['total'])} EUR, de las que "
                f"{fila['bench_offers']} son de gente que no "
                f"juega por {_euros(fila['bench_total'])} EUR."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo censar el reset: "
                f"{type(error).__name__}: {error}"
            ),
        }


# ============================================================
# LA PUJA POR DEBAJO DEL PRECIO NUEVO
# ============================================================
#
#     NO SE SABE, Y NO SE INVENTA (10/09/2026)
#
#         El dueno pujo 11.800.000 por Aubameyang. Al reset
#         siguiente el jugador pasa a costar 12.170.000: 370.000
#         POR ENCIMA de la puja.
#
#         ¿Sigue viva esa puja? Nadie de esta casa lo ha medido.
#         Y decide algo concreto: si sobrevive, se puede pujar la
#         tarde anterior con tranquilidad; si no, hay que esperar
#         al ultimo momento, dentro de la ventana del reset.
#
#     Se registra el caso y se mira al dia siguiente. Una linea.

PUJAS_BAJO_PRECIO = DIRECTORIO / "pujas_bajo_precio.jsonl"


def apuntar_puja_bajo_precio(
    player_name,
    bid_amount,
    price_when_bid=None,
    price_now=None,
    still_live=None,
    won=None,
    note=None,
    at: str | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Una observacion del caso "puje por debajo del precio nuevo".

    `still_live` y `won` pueden venir a None: el dia que se pone
    la puja todavia no se sabe, y fingir un False seria peor que
    dejarlo vacio.
    """

    puja = safe_int(bid_amount)

    precio = safe_int(price_now)

    fila = {
        "at": at or _ahora(),
        "player_name": player_name,
        "bid_amount": puja,
        "price_when_bid": safe_int(price_when_bid),
        "price_now": precio,
        "gap": (precio - puja) if precio and puja else None,
        "below_price": bool(precio and puja and puja < precio),
        "still_live": still_live,
        "won": won,
        "note": note,
    }

    fila["written"] = _apendar(
        fila, ruta or PUJAS_BAJO_PRECIO, LINEAS_QUE_SE_GUARDAN
    )

    return fila


def historia_bajo_precio(ruta: Path | None = None) -> dict:
    """
    Lo que sabemos del caso, que hoy es nada.
    """

    filas = [
        f for f in _leer(ruta or PUJAS_BAJO_PRECIO)
        if f.get("below_price")
    ]

    resueltas = [
        f for f in filas if f.get("still_live") is not None
    ]

    vivas = [f for f in resueltas if f.get("still_live")]

    return {
        "available": bool(resueltas),
        "observed": len(filas),
        "resolved": len(resueltas),
        "survived": len(vivas),
        "reason": (
            f"{len(vivas)} de {len(resueltas)} pujas por debajo "
            f"del precio nuevo siguieron vivas."
            if resueltas
            else (
                f"{len(filas)} caso(s) apuntados y ninguno "
                f"resuelto todavia: NO SE SABE si una puja por "
                f"debajo del precio nuevo sobrevive al reset."
            )
        ),
    }


def historia_del_censo(ruta: Path | None = None) -> dict:
    """
    Lo que llevamos contado. Con pocas observaciones lo dice.
    """

    filas = _leer(ruta or CENSO)

    if not filas:
        return {
            "available": False,
            "resets": 0,
            "reason": (
                "Todavia no hay ningun reset censado. Empieza hoy."
            ),
        }

    totales = [safe_int(f.get("bench_total")) for f in filas]

    return {
        "available": True,
        "resets": len(filas),
        "bench_total_min": min(totales),
        "bench_total_max": max(totales),
        "bench_total_median": sorted(totales)[len(totales) // 2],
        "reason": (
            f"{len(filas)} reset(s) censados. Con menos de 30 no "
            f"hay tasa base: hay cuenta, no medida."
            if len(filas) < 30
            else f"{len(filas)} resets censados."
        ),
    }
