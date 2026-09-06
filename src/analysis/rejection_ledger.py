"""
El libro de rechazos: lo que nos juzga a nosotros.

LA IDEA (16/09/2026)

    La casa ya puntua a las fuentes con Brier: FutbolFantasy saca
    0,3365 en pronosticos de titular, peor que tirar una moneda,
    y por eso ninguna fuente entra por prestigio.

    Nunca nos hemos aplicado esa vara a nosotros. Cada noche el
    modelo concluye que no hay que comprar nada, y nadie apunta
    que paso despues con los que rechazo.

DOS COSAS DISTINTAS, Y HACEN FALTA LAS DOS

    1. EL LIBRO HACIA DELANTE. Cada rechazo de hoy, con su
       motivo y su precio, para mirarlo dentro de tres dias. Es
       la unica evidencia que de verdad nos juzga, y empieza
       vacio: hoy no dice nada y hay que decir que no dice nada.

    2. EL RETROTEST DE NUESTRA PROPIA REGLA. Ese si se puede
       contestar hoy, porque el almacen de precios tiene el
       historico completo: se aplica la regla de Pepe a cada
       (jugador, dia) de agosto y se mira que hicieron despues
       los que habria RECHAZADO frente a los que habria
       ACEPTADO.

       Si los rechazados suben tanto como los aceptados, la regla
       no discrimina y sobra. Si los rechazados se quedan planos
       o caen, la regla esta haciendo su trabajo.

    La segunda no sustituye a la primera —agosto no es
    septiembre— pero es lo unico medible esta noche y contesta la
    pregunta de fondo: ¿es el modelo demasiado exigente?

ESTE MODULO NO DECIDE NADA

    Apunta y puntua. No importa ningun executor y no escribe en
    ninguna ruta de decision.
"""

from __future__ import annotations

import json
import statistics

from datetime import datetime, timedelta, timezone
from pathlib import Path


VERSION = "V1.0"

LEDGER_PATH = (
    Path("data") / "intelligence" / "rejection_ledger.json"
)


# El mismo horizonte que usa la via TENER, para que el libro
# puntue lo que la via prometia.
HORIZON_DAYS = 3


# Por debajo de esto no se publica mediana. El mismo corte que el
# retrotest.
MIN_SAMPLE = 30


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_ledger() -> dict:
    return {"version": VERSION, "rejections": {}}


def load_ledger(path: Path | None = None) -> dict:
    try:
        return json.loads(
            (path or LEDGER_PATH).read_text(encoding="utf-8")
        )
    except Exception:                               # noqa: BLE001
        return empty_ledger()


def save_ledger(ledger: dict, path: Path | None = None) -> None:
    destino = path or LEDGER_PATH

    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(ledger, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    except Exception:                               # noqa: BLE001
        pass


def _parse(marca):
    try:
        fecha = datetime.fromisoformat(str(marca))
    except (TypeError, ValueError):
        return None

    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)

    return fecha


# ============================================================
# 1. EL LIBRO HACIA DELANTE
# ============================================================


def record_rejections(
    targets: list | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
    now: datetime | None = None,
) -> dict:
    """
    Apunta los rechazos de hoy con el precio de hoy.

    Una entrada por jugador y dia: el mismo objetivo rechazado
    dos ciclos seguidos es el mismo rechazo, no dos.
    """

    libro = load_ledger(path) if ledger is None else ledger

    rechazos = libro.setdefault("rejections", {})

    momento = now or datetime.now(timezone.utc)

    nuevos = 0

    for fila in (targets or []):

        if not isinstance(fila, dict):
            continue

        decision = str(fila.get("decision") or "")

        # BID es lo contrario de un rechazo. Y sin precio no hay
        # nada que puntuar despues.
        if decision in ("", "BID"):
            continue

        precio = safe_int(fila.get("market_price"))

        if precio <= 0:
            continue

        player_id = safe_int(fila.get("id"))

        if not player_id:
            continue

        clave = f"{player_id}|{momento.date().isoformat()}"

        if clave in rechazos:
            continue

        rechazos[clave] = {
            "player_id": player_id,
            "player_name": fila.get("name"),

            "decision": decision,
            "reason": fila.get("reason"),

            "price_at_rejection": precio,
            "rate_percent_per_day": (
                (fila.get("market_gate") or {}).get(
                    "rate_percent_per_day"
                )
            ),
            "trend_days": (
                (fila.get("market_gate") or {}).get("trend_days")
            ),

            "rejected_at": momento.isoformat(),
            "due_at": (
                momento + timedelta(days=HORIZON_DAYS)
            ).isoformat(),

            "outcome": "PENDING",
            "price_at_outcome": None,
            "return_percent": None,
            "scored_at": None,
        }

        nuevos += 1

    libro["version"] = VERSION

    if save:
        save_ledger(libro, path)

    return libro


def settle_rejections(
    prices: dict | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
    now: datetime | None = None,
) -> dict:
    """
    Cierra los rechazos vencidos con el precio de hoy.

    `prices` es `{player_id (str): precio}`.
    """

    libro = load_ledger(path) if ledger is None else ledger

    momento = now or datetime.now(timezone.utc)

    catalogo = {
        str(k): safe_int(v) for k, v in (prices or {}).items()
    }

    for entrada in (libro.get("rejections") or {}).values():

        if entrada.get("outcome") != "PENDING":
            continue

        vence = _parse(entrada.get("due_at"))

        if vence is None or momento < vence:
            continue

        precio_hoy = catalogo.get(str(entrada["player_id"]))

        if not precio_hoy:
            entrada["outcome"] = "SIN_PRECIO"
            entrada["scored_at"] = momento.isoformat()
            continue

        base = safe_int(entrada.get("price_at_rejection"))

        if base <= 0:
            continue

        cambio = (precio_hoy - base) / base

        entrada["outcome"] = (
            "SUBIO" if cambio > 0 else "BAJO" if cambio < 0 else "IGUAL"
        )
        entrada["price_at_outcome"] = precio_hoy
        entrada["return_percent"] = round(cambio * 100, 3)
        entrada["scored_at"] = momento.isoformat()

    if save:
        save_ledger(libro, path)

    return libro


def summary(ledger: dict | None = None, path: Path | None = None) -> dict:
    """
    Lo que el libro sabe decir hoy.

    Con la muestra por delante: un libro que empieza vacio tiene
    que decir que esta vacio, no publicar una mediana de dos.
    """

    libro = load_ledger(path) if ledger is None else ledger

    entradas = list((libro.get("rejections") or {}).values())

    cerradas = [
        e
        for e in entradas
        if e.get("outcome") in ("SUBIO", "BAJO", "IGUAL")
        and e.get("return_percent") is not None
    ]

    if not cerradas:
        return {
            "available": bool(entradas),
            "observer_only": True,
            "recorded": len(entradas),
            "closed": 0,
            "enough": False,
            "reason": (
                f"{len(entradas)} rechazo(s) apuntado(s) y ninguno "
                f"vencido todavia. El libro empieza hoy: hasta "
                f"dentro de {HORIZON_DAYS} dias no dice nada, y "
                f"decir que no dice nada es parte de decirlo."
            ),
        }

    retornos = [e["return_percent"] / 100.0 for e in cerradas]

    # LO QUE HABRIAMOS GANADO O PERDIDO COMPRANDOLOS TODOS
    #
    #     Es la unica cifra que traduce el libro a euros. Se
    #     calcula sobre el precio al que los rechazamos, que es
    #     lo que habriamos pagado.
    invertido = sum(
        safe_int(e.get("price_at_rejection")) for e in cerradas
    )

    resultado = sum(
        safe_int(e.get("price_at_outcome"))
        - safe_int(e.get("price_at_rejection"))
        for e in cerradas
    )

    return {
        "available": True,
        "observer_only": True,

        "recorded": len(entradas),
        "closed": len(cerradas),
        "enough": len(cerradas) >= MIN_SAMPLE,
        "min_sample": MIN_SAMPLE,

        "rose": sum(1 for e in cerradas if e["outcome"] == "SUBIO"),
        "fell": sum(1 for e in cerradas if e["outcome"] == "BAJO"),
        "flat": sum(1 for e in cerradas if e["outcome"] == "IGUAL"),

        "median_return_percent": round(
            statistics.median(retornos) * 100, 3
        ),

        "would_have_invested": invertido,
        "would_have_gained": resultado,
        "would_have_gained_percent": (
            round(resultado / invertido * 100, 3)
            if invertido
            else None
        ),

        "horizon_days": HORIZON_DAYS,
        "reason": (
            None
            if len(cerradas) >= MIN_SAMPLE
            else (
                f"Solo {len(cerradas)} rechazos cerrados; hacen "
                f"falta {MIN_SAMPLE} para fiarse de la mediana."
            )
        ),
    }


# ============================================================
# 2. EL RETROTEST DE NUESTRA PROPIA REGLA
# ============================================================
#
#     Lo unico que se puede contestar HOY, y contesta la pregunta
#     de fondo: ¿es el modelo demasiado exigente?


def rule_backtest(
    horizon_days: int = HORIZON_DAYS,
    min_yield: float = 0.03,
) -> dict:
    """
    Aplica la regla de Pepe a cada (jugador, dia) del almacen y
    compara lo que hicieron los ACEPTADOS y los RECHAZADOS.

    La regla es la de la via TENER: se compra si el rendimiento
    despues de recortar y descontar llega al liston.

    Nunca lanza.
    """

    try:
        from src.analysis.hold_backtest import (
            build_operations,
            load_series,
        )
        from src.analysis.hold_value import hold_value

        operaciones = [
            o
            for o in build_operations(load_series())
            if o["horizon"] == horizon_days
        ]

        if not operaciones:
            return {
                "available": False,
                "reason": (
                    f"El almacen no da para un horizonte de "
                    f"{horizon_days} dias."
                ),
            }

        aceptados = []
        rechazados = []

        # Un precio cualquiera basta: el rendimiento de la via no
        # depende del precio, solo de la tasa y la racha.
        PRECIO = 1_000_000

        for o in operaciones:

            valor = hold_value(
                PRECIO,
                rate_percent_per_day=o["rate"] * 100.0,
                trend_days=o["streak"],
                sources=3,
                horizon_days=horizon_days,
            )

            rinde = (
                (valor["value"] - PRECIO) / PRECIO
                if valor["value"]
                else 0.0
            )

            (aceptados if rinde >= min_yield else rechazados).append(
                o["return"]
            )

        def resumen(grupo, etiqueta):

            if len(grupo) < MIN_SAMPLE:
                return {
                    "n": len(grupo),
                    "enough": False,
                    "reason": (
                        f"Solo {len(grupo)} operaciones "
                        f"{etiqueta}; hacen falta {MIN_SAMPLE}."
                    ),
                }

            ordenados = sorted(grupo)

            return {
                "n": len(grupo),
                "enough": True,
                "median": statistics.median(ordenados),
                "mean": statistics.fmean(ordenados),
                "p25": ordenados[len(ordenados) // 4],
                "loss_rate": sum(1 for r in grupo if r < 0)
                / len(grupo),
            }

        aceptado = resumen(aceptados, "aceptadas")
        rechazado = resumen(rechazados, "rechazadas")

        discrimina = None

        if aceptado.get("enough") and rechazado.get("enough"):
            discrimina = (
                aceptado["median"] > rechazado["median"]
            )

        return {
            "available": True,
            "observer_only": True,

            "horizon_days": horizon_days,
            "min_yield": min_yield,
            "operations": len(operaciones),

            "accepted": aceptado,
            "rejected": rechazado,

            "discriminates": discrimina,

            "reason": (
                None
                if discrimina is not None
                else (
                    "Uno de los dos grupos no llega a la muestra "
                    "minima: no se puede comparar."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "reason": (
                f"El retrotest de la regla no pudo correr: "
                f"{type(error).__name__}: {error}"
            ),
        }


def sync_rejections(
    targets: list | None,
    prices: dict | None,
    *,
    path: Path | None = None,
) -> dict:
    """
    El enganche del ciclo: apunta lo de hoy y cierra lo vencido.

    NUNCA LANZA.
    """

    try:
        libro = record_rejections(
            targets, path=path, save=False
        )
        libro = settle_rejections(
            prices, ledger=libro, path=path, save=True
        )

        return summary(libro)

    except Exception as error:                       # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                f"No se pudo alimentar el libro de rechazos: "
                f"{type(error).__name__}: {error}"
            ),
        }
