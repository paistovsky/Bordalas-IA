"""
El libro de acierto del ojeador: quien lo dijo, y si acerto.

POR QUE ES LO MAS IMPORTANTE DE TODO ESTO

    Ninguna fuente entra por prestigio. Hay precedente en esta
    casa: FutbolFantasy puntua 0.3365 de Brier en pronosticos de
    titular, y apostar 50 % fijo a todo saca 0.25. Es decir, en
    esa tarea concreta FF es PEOR que no saber nada, y solo se
    supo porque alguien lo midio.

    En dos semanas este libro dira a cual de las tres hacerle
    caso. Si alguna resulta ser ruido, se apaga.

QUE SE APUNTA, Y CUANDO

    Al construir un informe se anota cada señal con su fuente, su
    direccion, su magnitud y el PRECIO DE BIWENGER de ese momento.
    Ese precio es la unica verdad contra la que se puede puntuar
    despues.

    Cuando pasa el horizonte de la señal, se compara con el
    precio real de Biwenger de ese dia y se puntua.

TRES COSAS, NO UNA

    1. DIRECCION. ¿Dijo que subia y subio? Es lo que mas importa
       y lo unico que se puede exigir a todas.

    2. MAGNITUD. Cuanto se equivoco en euros y en porcentaje. Una
       fuente puede acertar siempre la direccion y exagerar
       siempre el tamaño, y eso hay que verlo por separado.

    3. CALIBRACION DE LA CONFIANZA. Solo FutbolFantasy trae
       confianza -y derivada por nosotros de `data-tendencia`-,
       asi que aqui se mide si esa derivacion sirve: cuando dice
       0,9 ¿acierta mas que cuando dice 0,5?

POR QUE UN "FLAT" NO PUNTUA COMO ACIERTO NI COMO FALLO

    Decir "no se movera" y que no se mueva no demuestra nada: la
    mayoria de los jugadores no se mueve la mayoria de los dias.
    Contarlo como acierto inflaria a la fuente mas prudente hasta
    hacerla parecer la mejor.

    Los FLAT se cuentan aparte, en `flat`, y no entran en el
    porcentaje de acierto.

FASE OBSERVADOR

    Este libro no cambia ninguna decision. Mide.
"""

from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone
from pathlib import Path


VERSION = "V1.0"

LEDGER_PATH = (
    Path("data")
    / "intelligence"
    / "scout_accuracy_ledger.json"
)


# Una prediccion que lleva mas de esto sin poder puntuarse se da
# por perdida: o el jugador salio del catalogo o nunca hubo
# observacion. No se inventa un resultado.
GIVE_UP_DAYS = 21


def safe_int(value, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def empty_ledger() -> dict:
    return {
        "version": VERSION,
        "predictions": {},
    }


def load_ledger(path: Path | None = None) -> dict:

    ruta = path or LEDGER_PATH

    if not ruta.exists():
        return empty_ledger()

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))

    except (OSError, json.JSONDecodeError):
        return empty_ledger()

    if not isinstance(datos, dict):
        return empty_ledger()

    datos.setdefault("version", VERSION)
    datos.setdefault("predictions", {})

    return datos


def save_ledger(ledger: dict, path: Path | None = None) -> None:

    ruta = path or LEDGER_PATH

    ruta.parent.mkdir(parents=True, exist_ok=True)

    ruta.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse(marca) -> datetime | None:
    if not marca:
        return None

    try:
        momento = datetime.fromisoformat(
            str(marca).replace("Z", "+00:00")
        )

    except ValueError:
        return None

    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)

    return momento


# ============================================================
# APUNTAR
# ============================================================


def record_report(
    report: dict | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
) -> dict:
    """
    Apunta cada señal del informe con el precio de HOY.

    Una señal por jugador, fuente y horizonte. Si ya estaba
    apuntada no se reescribe: el precio de partida es el de
    cuando se dijo, no el de la ultima vez que se miro.
    """

    libro = load_ledger(path) if ledger is None else ledger

    predicciones = libro.setdefault("predictions", {})

    nuevas = 0

    for player_id, ficha in (
        (report or {}).get("players") or {}
    ).items():

        precio = safe_int(ficha.get("market_price"))

        if precio <= 0:
            continue

        for señal in ficha.get("signals") or []:

            fuente = señal.get("source")
            horizonte = señal.get("horizon_days")

            if not fuente or horizonte is None:
                continue

            visto = señal.get("seen_at")

            momento = _parse(visto)

            if momento is None:
                continue

            # La clave lleva el dia dentro: la misma fuente dice
            # lo mismo del mismo jugador cada dia, y son
            # predicciones distintas.
            clave = (
                f"{player_id}|{fuente}|{horizonte}|"
                f"{momento.date().isoformat()}"
            )

            if clave in predicciones:
                continue

            predicciones[clave] = {
                "player_id": player_id,
                "player_name": ficha.get("player_name"),
                "source": fuente,
                "direction": señal.get("direction"),
                "magnitude_percent": señal.get("magnitude_percent"),
                "magnitude_eur": señal.get("magnitude_eur"),
                "horizon_days": horizonte,
                "confidence": señal.get("confidence"),
                "observed_signal": señal.get("observed"),

                # La verdad contra la que se puntuara.
                "price_at_prediction": precio,

                "predicted_at": visto,
                "due_at": (
                    momento + timedelta(days=int(horizonte))
                ).isoformat(),

                "outcome": "PENDING",
                "price_at_outcome": None,
                "actual_direction": None,
                "actual_percent": None,
                "direction_hit": None,
                "magnitude_error_percent": None,
                "scored_at": None,
            }

            nuevas += 1

    libro["version"] = VERSION

    if save:
        save_ledger(libro, path)

    return libro


# ============================================================
# PUNTUAR
# ============================================================


def _direction_of(cambio: int) -> str:
    if cambio > 0:
        return "UP"
    if cambio < 0:
        return "DOWN"
    return "FLAT"


def settle(
    prices: dict | None,
    ledger: dict | None = None,
    *,
    path: Path | None = None,
    save: bool = True,
    now: datetime | None = None,
) -> dict:
    """
    Cierra las predicciones vencidas contra el precio real.

    `prices` es `{player_id: precio}` de Biwenger HOY.
    """

    libro = load_ledger(path) if ledger is None else ledger

    ahora = now or datetime.now(timezone.utc)

    precios = {
        str(k): safe_int(v)
        for k, v in (prices or {}).items()
    }

    for entrada in (libro.get("predictions") or {}).values():

        if entrada.get("outcome") != "PENDING":
            continue

        vence = _parse(entrada.get("due_at"))

        if vence is None or ahora < vence:
            continue

        precio_hoy = precios.get(str(entrada.get("player_id")))

        if not precio_hoy:

            nacido = _parse(entrada.get("predicted_at"))

            # Sin precio y ya muy vieja: se cierra sin inventar
            # un resultado.
            if nacido and (ahora - nacido).days >= GIVE_UP_DAYS:
                entrada["outcome"] = "UNKNOWN"
                entrada["scored_at"] = ahora.isoformat()

            continue

        partida = safe_int(entrada.get("price_at_prediction"))

        if partida <= 0:
            entrada["outcome"] = "UNKNOWN"
            entrada["scored_at"] = ahora.isoformat()
            continue

        cambio = precio_hoy - partida

        real = _direction_of(cambio)
        dicho = entrada.get("direction")

        entrada["price_at_outcome"] = precio_hoy
        entrada["actual_direction"] = real
        entrada["actual_percent"] = round(cambio * 100.0 / partida, 3)

        # Un FLAT no puntua ni a favor ni en contra: ver el
        # docstring del modulo.
        if dicho == "FLAT" or real == "FLAT":
            entrada["outcome"] = "FLAT"
            entrada["direction_hit"] = None

        else:
            entrada["direction_hit"] = bool(dicho == real)
            entrada["outcome"] = "HIT" if dicho == real else "MISS"

        dijo = entrada.get("magnitude_percent")

        if dijo is not None:
            entrada["magnitude_error_percent"] = round(
                abs(float(dijo) - entrada["actual_percent"]), 3
            )

        entrada["scored_at"] = ahora.isoformat()

    if save:
        save_ledger(libro, path)

    return libro


# ============================================================
# EL RESUMEN, POR FUENTE
# ============================================================


def summary(ledger: dict | None = None, path: Path | None = None) -> dict:
    """
    A quien hacerle caso. Nunca inventa un numero.

    Sin predicciones cerradas, `hit_rate` va None y NO un 0 %,
    que se leeria como "falla siempre" cuando lo que pasa es que
    todavia no ha jugado.
    """

    libro = load_ledger(path) if ledger is None else ledger

    entradas = list((libro.get("predictions") or {}).values())

    por_fuente: dict[str, dict] = {}

    for entrada in entradas:

        fuente = entrada.get("source") or "?"

        datos = por_fuente.setdefault(
            fuente,
            {
                "source": fuente,
                "recorded": 0,
                "pending": 0,
                "hits": 0,
                "misses": 0,
                "flat": 0,
                "unknown": 0,
                "_errores": [],
                "_confianzas": [],
            },
        )

        datos["recorded"] += 1

        resultado = entrada.get("outcome")

        if resultado == "PENDING":
            datos["pending"] += 1
            continue

        if resultado == "HIT":
            datos["hits"] += 1
        elif resultado == "MISS":
            datos["misses"] += 1
        elif resultado == "FLAT":
            datos["flat"] += 1
        else:
            datos["unknown"] += 1

        error = entrada.get("magnitude_error_percent")

        if error is not None:
            datos["_errores"].append(float(error))

        confianza = entrada.get("confidence")
        acierto = entrada.get("direction_hit")

        if confianza is not None and acierto is not None:
            datos["_confianzas"].append(
                (float(confianza), bool(acierto))
            )

    salida = {}

    for fuente, datos in por_fuente.items():

        decididas = datos["hits"] + datos["misses"]

        errores = datos.pop("_errores")
        confianzas = datos.pop("_confianzas")

        datos["decided"] = decididas

        datos["hit_rate"] = (
            round(datos["hits"] / decididas, 4)
            if decididas
            else None
        )

        datos["mean_magnitude_error_percent"] = (
            round(sum(errores) / len(errores), 3)
            if errores
            else None
        )

        # CALIBRACION: cuando dice mucho, ¿acierta mas?
        #
        #     Se parte por la mitad de la escala. Si acierta
        #     igual diciendo 0,9 que diciendo 0,5, la confianza
        #     no vale para nada y hay que dejar de usarla.
        altas = [a for c, a in confianzas if c >= 0.7]
        bajas = [a for c, a in confianzas if c < 0.7]

        datos["calibration"] = {
            "high_confidence_n": len(altas),
            "high_confidence_hit_rate": (
                round(sum(altas) / len(altas), 4) if altas else None
            ),
            "low_confidence_n": len(bajas),
            "low_confidence_hit_rate": (
                round(sum(bajas) / len(bajas), 4) if bajas else None
            ),
            "separates": (
                bool(
                    altas
                    and bajas
                    and (sum(altas) / len(altas))
                    > (sum(bajas) / len(bajas))
                )
                if (altas and bajas)
                else None
            ),
        }

        salida[fuente] = datos

    total_decididas = sum(d["decided"] for d in salida.values())

    return {
        "available": bool(total_decididas),
        "observer_only": True,
        "sources": salida,
        "recorded_total": len(entradas),
        "decided_total": total_decididas,
        "reason": (
            None
            if total_decididas
            else (
                "Todavia no ha vencido ninguna prediccion. El libro "
                "apunta desde hoy y puntua cuando pasa el horizonte: "
                "no hay porcentaje de acierto que dar, y un 0 % "
                "seria mentira."
            )
        ),
    }


def sync_scout_accuracy(
    report: dict | None,
    prices: dict | None,
    *,
    path: Path | None = None,
) -> dict:
    """
    El enganche del ciclo: apunta lo de hoy y cierra lo vencido.

    NUNCA LANZA. Un fallo del libro jamas puede detener un ciclo.
    """

    try:
        libro = record_report(report, path=path, save=False)
        libro = settle(prices, ledger=libro, path=path, save=True)

        return summary(libro)

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "observer_only": True,
            "sources": {},
            "recorded_total": 0,
            "decided_total": 0,
            "reason": (
                f"No se pudo alimentar el libro de acierto: "
                f"{type(error).__name__}: {error}"
            ),
        }
