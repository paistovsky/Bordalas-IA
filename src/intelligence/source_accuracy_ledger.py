"""
Libro de aciertos por fuente de titularidad.

MOTIVO
    El consenso multifuente trata a Jornada Perfecta,
    FutbolFantasy y Analitica Fantasy como si valiesen lo mismo.
    En la jornada 1 de 2026 JP acerto con Jonny Castro y Mangala
    -ambos salieron de inicio- mientras las otras dos fallaban, y
    el consenso premio a la mayoria equivocada.

    Este modulo mide el acierto real de cada fuente para poder,
    mas adelante, ponderar su voto.

POR QUE BRIER Y NO PUNTOS POR ACERTAR
    Un sistema de aciertos castiga a quien admite que no sabe.
    FutbolFantasy dijo 50% en Mangala: eso no es equivocarse, es
    abstenerse. Penalizarlo empuja a las fuentes a farolear,
    porque la que siempre dice 90% acumularia mas puntos que la
    honesta.

    Brier mide la distancia al resultado ponderada por la
    conviccion:

        brier = (probabilidad/100 - resultado)^2

        dijo 92% y jugo   -> 0.006  excelente
        dijo 92% y no jugo-> 0.846  castigo duro
        dijo 50%          -> 0.250  neutro, gane o pierda
        dijo 25% y jugo   -> 0.563  mal

    Cuanto MENOR es el Brier, mejor la fuente.

DOS FASES
    Fase 1 (esta): registrar y puntuar. No afecta a ninguna
    decision.
    Fase 2 (cuando haya varias jornadas): usar los pesos en el
    consenso.

LIMITACION CONOCIDA
    Biwenger da puntos y partidos jugados, no minutos. Un
    suplente que entra cuenta como "jugo". El campo
    ground_truth_method deja constancia de como se decidio cada
    resultado para poder afinarlo despues.
"""

from __future__ import annotations

import json
from pathlib import Path


LEDGER_PATH = (
    Path("data")
    / "intelligence"
    / "source_accuracy_ledger.json"
)

VERSION = "V1.0"

SOURCES = (
    "JORNADA_PERFECTA",
    "FUTBOLFANTASY",
    "ANALITICA_FANTASY",
)

# Inercia del peso. Con una jornada de ~17 jugadores y solo unos
# pocos casos disputados, los pesos apenas deben moverse: seria
# aprenderse el ruido. Con este valor hacen falta varias jornadas
# para que las diferencias signifiquen algo.
PRIOR_STRENGTH = 50.0

# Brier de referencia: el de decir siempre 50%.
NEUTRAL_BRIER = 0.25


# ============================================================
# ESTRUCTURA
# ============================================================

def empty_ledger() -> dict:
    return {
        "version": VERSION,
        "matchdays": {},
    }


def load_ledger(
    path: Path | None = None,
) -> dict:

    ruta = path or LEDGER_PATH

    if not ruta.exists():
        return empty_ledger()

    try:
        with open(
            ruta,
            encoding="utf-8",
        ) as fichero:
            datos = json.load(fichero)

    except (OSError, json.JSONDecodeError):
        return empty_ledger()

    if not isinstance(datos, dict):
        return empty_ledger()

    datos.setdefault(
        "version",
        VERSION,
    )
    datos.setdefault(
        "matchdays",
        {},
    )

    return datos


def save_ledger(
    ledger: dict,
    path: Path | None = None,
) -> None:

    ruta = path or LEDGER_PATH
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        ruta,
        "w",
        encoding="utf-8",
    ) as fichero:
        json.dump(
            ledger,
            fichero,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# REGISTRO DE PREDICCIONES
# ============================================================

def record_predictions(
    board: dict,
    matchday: int,
    ledger: dict | None = None,
    snapshot: dict | None = None,
) -> dict:
    """
    Congela lo que dijo cada fuente ANTES de que se juegue.

    starter_multisource_v1124.json se reescribe en cada ciclo, de
    modo que sin esta foto las predicciones se pierden en cuanto
    empieza a calcularse la jornada siguiente.

    Vuelve a registrar sin miedo: mientras la jornada no este
    puntuada se actualiza la foto; una vez puntuada no se toca.
    """

    ledger = (
        ledger
        if ledger is not None
        else load_ledger()
    )

    clave = str(int(matchday))
    existente = ledger["matchdays"].get(clave, {})

    if existente.get("scored"):
        return ledger

    # Linea base de partidos disputados en el momento de
    # predecir. Guardarla aqui hace que puntuar despues no
    # necesite recuperar la foto antigua: basta la de entonces
    # contra la de ahora.
    base_apariciones = (
        catalog_players(snapshot)
        if snapshot
        else {}
    )

    predicciones = {}

    for jugador in board.get("players", []) or []:

        player_id = jugador.get("player_id")

        if player_id is None:
            continue

        fuentes = {}

        for nombre, dato in (
            jugador.get("sources", {}) or {}
        ).items():

            probabilidad = (
                (dato or {}).get("probability")
            )

            if probabilidad is None:
                # Fuente que se abstiene: no vota y no puntua.
                continue

            fuentes[nombre] = float(probabilidad)

        base = _appearances(
            base_apariciones.get(
                int(player_id),
                {},
            )
        )

        predicciones[str(int(player_id))] = {
            "player_name": jugador.get("player_name"),
            "team": jugador.get("team"),
            "appearances_at_prediction": base,
            "sources": fuentes,
            "consensus": jugador.get("consensus"),
            "consensus_probability": jugador.get(
                "starter_probability"
            ),
        }

    ledger["matchdays"][clave] = {
        **existente,
        "matchday": int(matchday),
        "predictions": predicciones,
        "scored": False,
    }

    return ledger


# ============================================================
# VERDAD SOBRE EL TERRENO
# ============================================================

def _appearances(
    player: dict,
) -> int | None:

    casa = player.get("playedHome")
    fuera = player.get("playedAway")

    if casa is None and fuera is None:
        return None

    try:
        return int(casa or 0) + int(fuera or 0)

    except (TypeError, ValueError):
        return None


def catalog_players(
    snapshot: dict,
) -> dict[int, dict]:
    """
    Indexa el catalogo por id, tolerando las dos formas en que
    Biwenger lo devuelve.
    """

    datos = (
        (
            snapshot.get(
                "catalog",
                {},
            )
            or {}
        ).get(
            "data",
            {},
        )
        or {}
    )

    jugadores = datos.get("players")

    if isinstance(jugadores, dict):
        jugadores = list(jugadores.values())

    if not isinstance(jugadores, list):
        return {}

    indexados = {}

    for jugador in jugadores:

        if not isinstance(jugador, dict):
            continue

        try:
            indexados[int(jugador["id"])] = jugador

        except (KeyError, TypeError, ValueError):
            continue

    return indexados


def infer_outcomes(
    snapshot_before: dict,
    snapshot_after: dict,
) -> dict[str, dict]:
    """
    Un jugador cuenta como que jugo si su numero de partidos
    disputados subio entre las dos fotos.

    Es el indicador mas fiable disponible: Biwenger no expone
    minutos, asi que no distingue titular de suplente que entra.
    Se guarda el metodo para poder afinarlo mas adelante.
    """

    antes = catalog_players(snapshot_before)
    despues = catalog_players(snapshot_after)

    resultados = {}

    for player_id, jugador_despues in despues.items():

        jugador_antes = antes.get(player_id)

        if jugador_antes is None:
            continue

        previos = _appearances(jugador_antes)
        actuales = _appearances(jugador_despues)

        if previos is None or actuales is None:
            continue

        if actuales < previos:
            # Datos incoherentes: no inventamos resultado.
            continue

        resultados[str(player_id)] = {
            "played": 1 if actuales > previos else 0,
            "appearances_before": previos,
            "appearances_after": actuales,
            "ground_truth_method": "APPEARANCE_DELTA",
        }

    return resultados


# ============================================================
# PUNTUACION
# ============================================================

def brier(
    probability: float,
    outcome: int,
) -> float:

    return (
        (float(probability) / 100.0 - float(outcome))
        ** 2
    )


def score_matchday(
    matchday: int,
    outcomes: dict,
    ledger: dict | None = None,
    only_contested: bool = False,
) -> dict:
    """
    Cruza las predicciones guardadas con lo que de verdad paso.

    only_contested limita la puntuacion a los jugadores en los
    que las fuentes discreparon. Que las tres acierten con Yamal
    no informa de nada: la senal esta en los desacuerdos.
    """

    ledger = (
        ledger
        if ledger is not None
        else load_ledger()
    )

    clave = str(int(matchday))
    registro = ledger["matchdays"].get(clave)

    if not registro:
        raise KeyError(
            f"No hay predicciones registradas para la jornada "
            f"{matchday}."
        )

    por_fuente = {
        nombre: {
            "n": 0,
            "sum_brier": 0.0,
        }
        for nombre in SOURCES
    }

    detalle = {}

    for player_id, prediccion in (
        registro.get("predictions", {}) or {}
    ).items():

        resultado = outcomes.get(player_id)

        if resultado is None:
            continue

        jugo = int(resultado.get("played", 0))
        fuentes = prediccion.get("sources", {}) or {}

        if only_contested:

            votos = {
                "STARTER"
                if valor >= 67.0
                else "BENCH"
                if valor <= 40.0
                else "UNCERTAIN"
                for valor in fuentes.values()
            }

            if len(votos) < 2:
                continue

        fila = {
            "player_name": prediccion.get("player_name"),
            "played": jugo,
            "brier": {},
        }

        for nombre, probabilidad in fuentes.items():

            if nombre not in por_fuente:
                por_fuente[nombre] = {
                    "n": 0,
                    "sum_brier": 0.0,
                }

            valor = brier(
                probabilidad,
                jugo,
            )

            por_fuente[nombre]["n"] += 1
            por_fuente[nombre]["sum_brier"] += valor

            fila["brier"][nombre] = round(valor, 4)

        detalle[player_id] = fila

    for nombre, datos in por_fuente.items():

        datos["mean_brier"] = (
            round(
                datos["sum_brier"] / datos["n"],
                4,
            )
            if datos["n"]
            else None
        )

    registro["outcomes"] = outcomes
    registro["scored"] = True
    registro["only_contested"] = bool(only_contested)
    registro["per_source"] = por_fuente
    registro["detail"] = detalle

    ledger["matchdays"][clave] = registro

    return ledger


# ============================================================
# PESOS
# ============================================================

def source_weights(
    ledger: dict | None = None,
) -> dict:
    """
    Peso por fuente, con inercia deliberada.

    Con pocas jornadas el resultado se queda pegado al reparto
    equitativo: ajustar pesos con una muestra de una jornada
    seria aprenderse el ruido, no la calidad de la fuente.

    FASE 1: nadie consume esto todavia. Es observacion.
    """

    ledger = (
        ledger
        if ledger is not None
        else load_ledger()
    )

    acumulado = {
        nombre: {
            "n": 0,
            "sum_brier": 0.0,
        }
        for nombre in SOURCES
    }

    jornadas = 0

    for registro in ledger.get("matchdays", {}).values():

        if not registro.get("scored"):
            continue

        jornadas += 1

        for nombre, datos in (
            registro.get("per_source", {}) or {}
        ).items():

            destino = acumulado.setdefault(
                nombre,
                {
                    "n": 0,
                    "sum_brier": 0.0,
                },
            )

            destino["n"] += int(datos.get("n", 0) or 0)
            destino["sum_brier"] += float(
                datos.get("sum_brier", 0.0) or 0.0
            )

    # Calidad cruda: Brier 0 -> 1, Brier 0.25 -> 0.
    calidades = {}

    for nombre, datos in acumulado.items():

        n = datos["n"]

        if not n:
            calidades[nombre] = 0.0
            continue

        brier_medio = datos["sum_brier"] / n

        calidades[nombre] = max(
            0.0,
            1.0 - brier_medio / NEUTRAL_BRIER,
        )

    equitativo = 1.0 / len(calidades)

    total = sum(calidades.values())

    if total <= 0:
        pesos_crudos = {
            nombre: equitativo
            for nombre in calidades
        }
    else:
        pesos_crudos = {
            nombre: valor / total
            for nombre, valor in calidades.items()
        }

    # ENCOGIMIENTO SOBRE EL PESO, NO SOBRE EL BRIER.
    #
    # Encoger solo el Brier no basta: al normalizar, diferencias
    # minusculas se reamplifican y una sola jornada acaba
    # moviendo los pesos casi tanto como cien. El encogimiento
    # tiene que aplicarse al reparto final.
    #
    # La confianza la marca la fuente con MENOS muestras: no
    # queremos separar pesos apoyandonos en una sola fuente bien
    # medida mientras otra apenas ha opinado.
    muestras = [
        datos["n"]
        for datos in acumulado.values()
    ]

    n_minimo = min(muestras) if muestras else 0

    confianza = (
        n_minimo
        / (n_minimo + PRIOR_STRENGTH)
    )

    pesos = {
        nombre: (
            equitativo * (1.0 - confianza)
            + valor * confianza
        )
        for nombre, valor in pesos_crudos.items()
    }

    return {
        "phase": "OBSERVER",
        "scored_matchdays": jornadas,
        "prior_strength": PRIOR_STRENGTH,
        "confidence": round(confianza, 4),
        "samples": {
            nombre: datos["n"]
            for nombre, datos in acumulado.items()
        },
        "mean_brier": {
            nombre: (
                round(
                    datos["sum_brier"] / datos["n"],
                    4,
                )
                if datos["n"]
                else None
            )
            for nombre, datos in acumulado.items()
        },
        "weights": {
            nombre: round(valor, 4)
            for nombre, valor in pesos.items()
        },
    }


def print_weights(
    resumen: dict,
) -> None:

    print()
    print("=" * 72)
    print(" ACIERTO POR FUENTE DE TITULARIDAD")
    print("=" * 72)
    print(
        f"Jornadas puntuadas: "
        f"{resumen.get('scored_matchdays')}"
    )
    print(
        f"Fase: {resumen.get('phase')} "
        f"(no afecta a ninguna decision)"
    )
    print("-" * 72)
    print(
        f"{'FUENTE':<22}{'MUESTRAS':>10}"
        f"{'BRIER':>10}{'PESO':>10}"
    )
    print("-" * 72)

    for nombre in sorted(
        resumen.get("weights", {}),
    ):
        brier_medio = resumen["mean_brier"].get(nombre)
        print(
            f"{nombre:<22}"
            f"{resumen['samples'].get(nombre, 0):>10}"
            f"{(f'{brier_medio:.4f}' if brier_medio is not None else '--'):>10}"
            f"{resumen['weights'][nombre]:>10.4f}"
        )

    print("-" * 72)
    print(
        "Brier mas bajo = mejor fuente. "
        "0.25 equivale a decir siempre 50%."
    )
    print("=" * 72)


# ============================================================
# CICLO AUTOMATICO
# ============================================================

def outcomes_from_snapshot(
    matchday: int,
    snapshot: dict,
    ledger: dict,
) -> dict[str, dict]:
    """
    Resultados usando la linea base guardada al predecir.

    No hace falta conservar la foto antigua: cada prediccion
    lleva anotados los partidos que el jugador tenia entonces.
    """

    registro = (
        ledger.get("matchdays", {})
        .get(str(int(matchday)), {})
    )

    actuales = catalog_players(snapshot)
    resultados = {}

    for player_id, prediccion in (
        registro.get("predictions", {}) or {}
    ).items():

        base = prediccion.get(
            "appearances_at_prediction"
        )

        if base is None:
            continue

        ahora = _appearances(
            actuales.get(
                int(player_id),
                {},
            )
        )

        if ahora is None or ahora < base:
            continue

        resultados[player_id] = {
            "played": 1 if ahora > base else 0,
            "appearances_before": base,
            "appearances_after": ahora,
            "ground_truth_method": "APPEARANCE_DELTA",
        }

    return resultados


def sync_ledger(
    board: dict,
    snapshot: dict,
    current_matchday: int,
    ledger: dict | None = None,
) -> dict:
    """
    Punto de entrada unico para el ciclo de produccion.

    1. Registra las predicciones de la jornada en curso. Se
       reescriben en cada ciclo, asi que la version que queda es
       la ultima antes de que la jornada avance.
    2. Puntua cualquier jornada anterior que siguiese pendiente.

    Nunca lanza: un fallo del libro no puede detener un ciclo de
    produccion. Devuelve el libro y un resumen de lo hecho.
    """

    ledger = (
        ledger
        if ledger is not None
        else load_ledger()
    )

    hecho = {
        "recorded": None,
        "scored": [],
        "error": None,
    }

    try:
        current_matchday = int(current_matchday)

        if board:
            ledger = record_predictions(
                board=board,
                matchday=current_matchday,
                ledger=ledger,
                snapshot=snapshot,
            )
            hecho["recorded"] = current_matchday

        for clave in sorted(
            ledger.get("matchdays", {}),
            key=lambda valor: int(valor),
        ):

            jornada = int(clave)

            if jornada >= current_matchday:
                continue

            if ledger["matchdays"][clave].get("scored"):
                continue

            resultados = outcomes_from_snapshot(
                matchday=jornada,
                snapshot=snapshot,
                ledger=ledger,
            )

            if not resultados:
                continue

            ledger = score_matchday(
                matchday=jornada,
                outcomes=resultados,
                ledger=ledger,
            )

            hecho["scored"].append(jornada)

    except Exception as error:
        hecho["error"] = (
            f"{type(error).__name__}: {error}"
        )

    return {
        "ledger": ledger,
        "summary": hecho,
    }
