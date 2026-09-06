"""
El retrotest entero, sobre ventanas de verdad.

LA PREGUNTA (26/09/2026)

    Toda la calibracion viva se midio sobre SEIS dias del 12 al
    17 de agosto: la semana siguiente al cierre del mercado, con
    los precios recolocandose. Quedo escrito en su dia que era
    "la semana mas rara del año" y que por eso todo salia con
    rango.

    Con historico de verdad hay cuatro preguntas:

        1. Sigue siendo 3 el horizonte que maximiza la mediana?
        2. Aguanta el +4,47 % fuera de esa semana de agosto?
        3. Sigue el 3 % donde tiene que estar?
        4. Las celdas vacias por falta de dias, se llenan?

COMO SE CONTESTA

    Con `hold_backtest.backtest(path)`, que ya acepta un almacen
    cualquiera. No se reimplementa nada: se le dan ventanas
    distintas del mismo historico y se comparan las tablas.

    Recortar la ventana es lo unico que hace este script, y lo
    hace sobre las marcas de tiempo, no sobre las tablas: una
    operacion de compra a 3 dias que salta de agosto a
    septiembre no puede contarse en ninguno de los dos meses. Si
    se recortara despues, se contaria en los dos.

NO ENCIENDE NADA

    Calcula y publica. No mueve ningun liston, no compra y no
    vende.

COMO SE USA

    python -m scripts.recalibrar_ventana_larga <historico.json>
"""

from __future__ import annotations

import json
import sys

from datetime import date, datetime
from pathlib import Path

from src.analysis.hold_backtest import (
    HORIZONS,
    build_operations,
    load_series,
    MIN_SAMPLE,
    RATE_BUCKETS,
    STREAK_BUCKETS,
    backtest,
    best_horizon,
    calibration,
)


# Lo que hay vivo hoy, para poder poner el antes al lado del
# despues sin ir a buscarlo a mano. Sale de
# `docs/resultado-que-gire-2026-09-24.md`, medido sobre los seis
# dias del 12 al 17 de agosto.
VIVO_HOY = {
    "horizonte": 3,
    "liston": 3.0,
    "tramos": {
        "0,5-1 %": {"1 dia": 1.25, "2 dias": 0.60},
        "1-2 %": {"1 dia": 3.22, "2 dias": 1.80},
        "2-4 %": {"1 dia": 5.61, "2 dias": 3.14},
        "> 4 %": {"1 dia": 18.37, "2 dias": 21.15},
    },
}


# Las ventanas que contestan las preguntas. `None` es "sin
# limite por ese lado".
VENTANAS = (
    (
        "LA SEMANA DE AGOSTO",
        date(2026, 8, 12),
        date(2026, 8, 17),
        "donde se midio todo lo que esta vivo hoy",
    ),
    (
        "LOS 22 DIAS DE PRODUCCION",
        date(2026, 8, 16),
        date(2026, 9, 6),
        "lo que el almacen del ciclo tiene ahora mismo",
    ),
    (
        "TODO MENOS ESA SEMANA",
        date(2026, 8, 18),
        date(2026, 9, 6),
        "la prueba de si el numero existe fuera de agosto",
    ),
    (
        "AGOSTO",
        date(2026, 8, 1),
        date(2026, 8, 31),
        "el mes entero",
    ),
    (
        "SEPTIEMBRE",
        date(2026, 9, 1),
        None,
        "el mes en curso",
    ),
    (
        "LA TEMPORADA ENTERA",
        date(2026, 8, 1),
        None,
        "todo lo que lleva jugado",
    ),
)


def recortar(almacen: dict, desde, hasta) -> dict:
    """
    El mismo almacen con las marcas fuera de ventana quitadas.

    Forma fija: siempre `{"players": {...}}`, tenga o no puntos
    dentro.
    """

    recortado = {"players": {}}

    for player_id, ficha in (
        (almacen or {}).get("players") or {}
    ).items():

        if not isinstance(ficha, dict):
            continue

        marcas = ficha.get("t") or []
        precios = ficha.get("p") or []

        if len(marcas) != len(precios):
            continue

        dentro_t = []
        dentro_p = []

        for marca, precio in zip(marcas, precios):

            try:
                dia = datetime.fromtimestamp(marca).date()

            except (TypeError, ValueError, OSError):
                continue

            if desde is not None and dia < desde:
                continue

            if hasta is not None and dia > hasta:
                continue

            dentro_t.append(marca)
            dentro_p.append(precio)

        if len(dentro_t) >= 2:
            recortado["players"][player_id] = {
                "t": dentro_t,
                "p": dentro_p,
            }

    return recortado


def indice_del_mercado(almacen: dict, desde, hasta) -> dict:
    """
    Cuanto subio el mercado ENTERO en la ventana.

    EL CONTROL QUE FALTABA, Y ES EL QUE DECIDE

        "Aguantar diez dias rinde un 6 %" no significa nada por
        si solo. Si el mercado entero subio un 6 % en diez dias,
        la via no aporta nada: solo esta cobrando la marea.

        El indice se calcula sobre los jugadores que tienen
        precio TODOS los dias de la ventana. Con los que entran
        y salen, una subida del indice podria ser solo que hoy
        se cuentan mas jugadores que ayer.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "from": None,
        "to": None,
        "days": 0,
        "players": 0,
        "change_percent": None,
        "drift_per_day": None,
        "risers": None,
        "reason": "Sin dias completos con los que hacer indice.",
    }

    try:
        por_jugador = {}

        for player_id, ficha in (
            (almacen or {}).get("players") or {}
        ).items():

            if not isinstance(ficha, dict):
                continue

            serie = {}

            for marca, precio in zip(
                ficha.get("t") or [], ficha.get("p") or []
            ):

                try:
                    dia = datetime.fromtimestamp(marca).date()

                except (TypeError, ValueError, OSError):
                    continue

                if desde is not None and dia < desde:
                    continue

                if hasta is not None and dia > hasta:
                    continue

                serie[dia] = precio

            if serie:
                por_jugador[player_id] = serie

        dias = sorted(
            {d for serie in por_jugador.values() for d in serie}
        )

        if len(dias) < 2:
            return vacio

        completos = [
            pid
            for pid, serie in por_jugador.items()
            if all(dia in serie for dia in dias)
        ]

        if not completos:
            return vacio

        inicio = sum(
            por_jugador[pid][dias[0]] for pid in completos
        )

        final = sum(
            por_jugador[pid][dias[-1]] for pid in completos
        )

        if inicio <= 0:
            return vacio

        recorrido = (dias[-1] - dias[0]).days or 1

        cambio = 100 * (final - inicio) / inicio

        suben = sum(
            1
            for pid in completos
            if por_jugador[pid][dias[-1]]
            > por_jugador[pid][dias[0]]
        )

        return {
            "available": True,
            "from": dias[0].isoformat(),
            "to": dias[-1].isoformat(),
            "days": recorrido,
            "players": len(completos),
            "change_percent": round(cambio, 2),
            "drift_per_day": round(cambio / recorrido, 4),
            "risers": suben,
            "reason": None,
        }

    except Exception as error:                       # noqa: BLE001
        return {**vacio, "reason": f"{type(error).__name__}: {error}"}


def tabla_neta(resultado: dict, indice: dict) -> None:
    """
    La mediana menos la marea, horizonte a horizonte.

    Es la unica columna que dice si la via aporta algo. Sin ella
    "diez dias rinde mas que tres" puede ser solo que diez dias
    de marea son mas que tres.
    """

    if not indice.get("available"):
        print("  Sin indice: no se puede descontar la marea.")
        return

    deriva = indice["drift_per_day"]

    por_horizonte = resultado.get("by_horizon_rising") or {}

    print()
    print(
        f"  Marea del mercado: {indice['change_percent']:+.2f} % "
        f"en {indice['days']} dias "
        f"({deriva:+.3f} %/dia, {indice['players']} jugadores "
        f"con serie completa, suben {indice['risers']})"
    )
    print()
    print("  HORIZONTE    BRUTO     MAREA      NETO   PIERDE")
    print("  " + "-" * 50)

    mejor_neto = None

    for m in HORIZONS:

        datos = (
            por_horizonte.get(m)
            or por_horizonte.get(str(m))
            or {}
        )

        if not datos.get("enough"):
            continue

        bruto = 100 * datos["median"]
        marea = deriva * m
        neto = bruto - marea

        if mejor_neto is None or neto > mejor_neto[1]:
            mejor_neto = (m, neto)

        print(
            f"  {m:>5} d   {bruto:>+7.2f} % {marea:>+8.2f} % "
            f"{neto:>+8.2f} % {100 * datos['loss_rate']:>7.1f} %"
        )

    if mejor_neto:
        print()
        print(
            f"  Descontada la marea, el maximo esta en "
            f"{mejor_neto[0]} dias ({mejor_neto[1]:+.2f} %)."
        )


def contraste_de_direccion(resultado_path) -> None:
    """
    Comprar el que sube contra comprar el que baja.

    Si las dos cosas rindieran parecido, no habria señal: solo
    marea. La simetria es la prueba de que el momento existe.
    """

    try:
        operaciones = build_operations(load_series(resultado_path))

    except Exception as error:                       # noqa: BLE001
        print(f"  No se pudo contrastar: {error}")
        return

    print()
    print("  HORIZONTE   COMPRA EL QUE SUBE   COMPRA EL QUE CAE")
    print("  " + "-" * 52)

    for m in HORIZONS:

        suben = sorted(
            o["return"]
            for o in operaciones
            if o["horizon"] == m and o["rate"] > 0
        )

        caen = sorted(
            o["return"]
            for o in operaciones
            if o["horizon"] == m and o["rate"] < 0
        )

        if len(suben) < MIN_SAMPLE or len(caen) < MIN_SAMPLE:
            continue

        print(
            f"  {m:>5} d "
            f"{100 * suben[len(suben) // 2]:>+17.2f} % "
            f"{100 * caen[len(caen) // 2]:>+17.2f} %"
        )


def porcentaje(valor) -> str:
    if valor is None:
        return "     —"
    return f"{100 * valor:+6.2f}"


def tabla_de_horizontes(resultado: dict) -> None:
    """La pregunta 1: que horizonte maximiza la mediana."""

    por_horizonte = resultado.get("by_horizon_rising") or {}

    mejor = best_horizon(resultado)

    print()
    print("  HORIZONTE   MEDIANA   PIERDE      n")
    print("  " + "-" * 44)

    for m in HORIZONS:

        datos = por_horizonte.get(m) or por_horizonte.get(str(m)) or {}

        if not datos.get("enough"):
            print(
                f"  {m:>5} d     {'sin muestra':>18} "
                f"{datos.get('n', 0):>6}"
            )
            continue

        marca = "  <-- MAXIMO" if m == mejor else ""

        print(
            f"  {m:>5} d   {porcentaje(datos['median'])} % "
            f"{100 * datos['loss_rate']:>6.1f} % "
            f"{datos['n']:>6}{marca}"
        )

    print()
    print(f"  El horizonte que maximiza la mediana: {mejor}")


def tabla_de_tramos(resultado: dict, horizonte: int) -> dict:
    """Las preguntas 2, 3 y 4: cada tramo con cada racha."""

    calibrado = calibration(resultado, horizonte)

    if not calibrado.get("available"):
        print(f"  {calibrado.get('reason')}")
        return {}

    bandas = [b[0] for b in STREAK_BUCKETS]

    print()
    print(
        f"  {'TRAMO':<12}"
        + "".join(f"{b:>16}" for b in bandas)
    )
    print("  " + "-" * (12 + 16 * len(bandas)))

    resumen = {}

    for tramo in [b[0] for b in RATE_BUCKETS]:

        datos = (calibrado["by_rate_bucket"] or {}).get(
            tramo
        ) or {}

        celdas = datos.get("bands") or {}

        fila = f"  {tramo:<12}"

        resumen[tramo] = {}

        for banda in bandas:

            celda = celdas.get(banda)

            if not celda:
                fila += f"{'—':>16}"
                continue

            resumen[tramo][banda] = celda["median"]

            fila += (
                f"{porcentaje(celda['median'])} %"
                f" ({celda['n']:>4})"
            ).rjust(16)

        print(fila)

    return resumen


def main() -> None:

    origen = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "historico_precios.json"
    )

    almacen = json.loads(origen.read_text(encoding="utf-8"))

    print(f"Historico: {len(almacen.get('players') or {})} jugadores")

    todas = []

    for nombre, desde, hasta, nota in VENTANAS:

        recortado = recortar(almacen, desde, hasta)

        # `backtest` lee de un fichero, asi que la ventana se le
        # sirve en uno temporal al lado del original.
        temporal = origen.parent / (
            "ventana_"
            + nombre.lower().replace(" ", "_")
            + ".json"
        )

        temporal.write_text(
            json.dumps(recortado), encoding="utf-8"
        )

        resultado = backtest(temporal)

        print()
        print("=" * 74)
        print(f"{nombre}  —  {nota}")
        print("=" * 74)

        if not resultado.get("available"):
            print(f"  {resultado.get('reason')}")
            continue

        ventana = resultado.get("window") or {}

        print(
            f"  {ventana.get('from')} a {ventana.get('to')}  "
            f"({ventana.get('days')} dias)  ·  "
            f"{resultado['players']} jugadores  ·  "
            f"{resultado['operations']:,} operaciones".replace(
                ",", "."
            )
        )

        tabla_de_horizontes(resultado)

        print()
        print("  --- DESCONTADA LA MAREA DEL MERCADO ---")
        tabla_neta(resultado, indice_del_mercado(almacen, desde, hasta))

        print()
        print("  --- Y LA PRUEBA DE QUE HAY SEÑAL ---")
        contraste_de_direccion(temporal)

        mejor = best_horizon(resultado)

        for horizonte in sorted(
            {3, mejor} - {None}
        ):
            print()
            print(f"  --- TRAMOS A {horizonte} DIAS ---")
            tabla_de_tramos(resultado, horizonte)

        todas.append((nombre, resultado))

    # ==========================================================
    # EL ANTES Y EL DESPUES, LADO A LADO
    # ==========================================================

    print()
    print("=" * 74)
    print("LO QUE ESTA ENCENDIDO HOY, CONTRA LA VENTANA LARGA")
    print("=" * 74)
    print()
    print(
        "  Vivo hoy: horizonte 3, liston 3 %, medido sobre los "
        "seis dias\n  del 12 al 17 de agosto."
    )

    larga = next(
        (
            r
            for nombre, r in todas
            if nombre == "LA TEMPORADA ENTERA"
        ),
        None,
    )

    if larga is None:
        print("  Sin ventana larga con la que comparar.")
        return

    calibrado = calibration(larga, VIVO_HOY["horizonte"])

    print()
    print(
        f"  {'TRAMO':<12}{'RACHA':<10}"
        f"{'ANTES':>10}{'AHORA':>12}{'n AHORA':>10}  RESPALDO"
    )
    print("  " + "-" * 72)

    for tramo, bandas_antes in VIVO_HOY["tramos"].items():

        datos = (
            calibrado.get("by_rate_bucket") or {}
        ).get(tramo) or {}

        celdas = datos.get("bands") or {}

        for banda, antes in bandas_antes.items():

            celda = celdas.get(banda)

            if not celda:
                print(
                    f"  {tramo:<12}{banda:<10}"
                    f"{antes:>9.2f} %{'sin muestra':>12}"
                    f"{'—':>10}  NO SE PUEDE DECIR"
                )
                continue

            ahora = 100 * celda["median"]

            respaldo = (
                "SIGUE"
                if ahora >= VIVO_HOY["liston"]
                else "YA NO"
            )

            print(
                f"  {tramo:<12}{banda:<10}"
                f"{antes:>9.2f} %{ahora:>11.2f} %"
                f"{celda['n']:>10}  {respaldo}"
            )

    print()
    print(f"  Muestra minima por celda: {MIN_SAMPLE}")
    print("  Ni un liston movido. Solo medido.")


if __name__ == "__main__":
    main()
