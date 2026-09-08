"""
Que clase de noticia mueve el precio, y cuanto tarda.

POR QUE ES EL PRODUCTO Y NO UNA PRECAUCION

    Los rivales leen las mismas webs que nosotros. Leerlas nos
    empata; no nos adelanta.

    Lo que un humano no tiene es MEMORIA: el lee "el Malaga
    busca a fulano" y decide a ojo. Nosotros podemos saber que
    paso las cincuenta veces anteriores que salio esa clase de
    noticia.

    Si "vuelve de lesion" mueve el precio un 8 % el 60 % de las
    veces y "mencion" no lo mueve nada, ellos siguen adivinando
    y nosotros no.

Y EL NUMERO QUE DECIDE LA OPERATIVA

    Cuanto TARDA en moverse. Si tarda dos dias, hay margen para
    entrar con calma; si se mueve en dos horas, llegar el
    primero es lo unico que importa — y eso decide si el ciclo
    tiene que mirar cada hora o basta una vez al dia.

DE DONDE SALE

    Del archivo diario -`archivo_diario`- cruzado con el almacen
    de precios. Las dos cosas ya estan en disco: esto no baja
    nada.

    HOY ESTARA VACIO, y se publica igual. El 09/09 es el primer
    dia archivado; hasta que no haya siete dias no se puede
    medir el horizonte de siete. Se enseña llenandose.

NO DECIDE NADA

    Mide y publica. La fase 1 del encargo dice que la noticia
    ORDENA entre los que ya pasan el liston, y no crea compras.
    Este modulo ni siquiera hace eso: solo cuenta.
"""

from __future__ import annotations

import json

from datetime import date, timedelta
from pathlib import Path


# Los horizontes del encargo. Los mismos que ya usa el retrotest
# de precios, para que las dos mediciones se puedan comparar.
HORIZONTES = (1, 3, 7)


# Por debajo de esto una clase no publica porcentaje. Es el mismo
# numero que usa el resto de la casa.
MUESTRA_MINIMA = 30


def safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dias_del_archivo(directorio: Path) -> list:
    """Las fechas archivadas, en orden. Nunca lanza."""

    try:
        if not directorio.exists():
            return []

        dias = []

        for carpeta in directorio.iterdir():

            if not carpeta.is_dir():
                continue

            try:
                dias.append(date.fromisoformat(carpeta.name))

            except ValueError:
                continue

        return sorted(dias)

    except Exception:                               # noqa: BLE001
        return []


def avisos_de(dia: date, directorio: Path) -> list:
    """
    Los avisos de prensa de ese dia: `(player_id, kind)`.

    Cada jugador cuenta UNA vez por clase: si tres periodicos
    dicen lo mismo, sigue siendo una noticia. Contarla tres veces
    inflaria la muestra sin añadir informacion.
    """

    salida = []

    try:
        fichero = directorio / dia.isoformat() / "press.json"

        if not fichero.exists():
            return []

        informe = json.loads(
            fichero.read_text(encoding="utf-8")
        )

        for identificador, ficha in (
            (informe.get("players") or {}).items()
        ):

            if not isinstance(ficha, dict):
                continue

            clases = {
                item.get("kind")
                for item in (ficha.get("items") or [])
                if isinstance(item, dict) and item.get("kind")
            }

            for clase in sorted(clases):
                salida.append(
                    {
                        "player_id": identificador,
                        "player_name": ficha.get("player_name"),
                        "kind": clase,
                        "day": dia,
                    }
                )

        return salida

    except Exception:                               # noqa: BLE001
        return []


def _precio_en(series: dict, player_id, cuando: date):
    """
    El precio de ese jugador ese dia, o None.

    No se interpola ni se coge el mas cercano: si ese dia no hay
    precio, no hay dato. Rellenar huecos es como se fabrican
    correlaciones que no existen.
    """

    try:
        return (series.get(str(player_id)) or {}).get(cuando)

    except Exception:                               # noqa: BLE001
        return None


def _series_por_dia(almacen: dict) -> dict:
    """`{player_id: {fecha: precio}}` desde el almacen."""

    from datetime import datetime

    salida = {}

    try:
        for identificador, ficha in (
            (almacen or {}).get("players") or {}
        ).items():

            if not isinstance(ficha, dict):
                continue

            por_dia = {}

            for marca, precio in zip(
                ficha.get("t") or [], ficha.get("p") or []
            ):

                try:
                    por_dia[
                        datetime.fromtimestamp(marca).date()
                    ] = precio

                except (TypeError, ValueError, OSError):
                    continue

            salida[str(identificador)] = por_dia

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def _vacio(motivo: str) -> dict:
    """
    LA FORMA NO CAMBIA CON LOS DATOS.

    El dia uno esto sale vacio, y tiene que salir con las mismas
    claves que el dia sesenta: la pantalla se construye hoy, no
    cuando haya muestra.
    """

    return {
        "available": False,
        "observer_only": True,
        "days_archived": 0,
        "notices": 0,
        "measurable": 0,
        "horizons": list(HORIZONTES),
        "min_sample": MUESTRA_MINIMA,
        "by_kind": {},
        "reason": motivo,
    }


def libro(
    directorio: Path | None = None,
    almacen: dict | None = None,
    hoy: date | None = None,
) -> dict:
    """
    Que hizo el precio despues de cada clase de noticia.

    `directorio`, `almacen` y `hoy` se PASAN: las guardias los
    inyectan y no se lee ni disco ni reloj cuando te los dan.

    Forma fija. Nunca lanza.
    """

    try:
        if directorio is None:
            from src.intelligence.archivo_diario import (
                DIRECTORIO,
            )

            directorio = DIRECTORIO

        directorio = Path(directorio)

        dias = _dias_del_archivo(directorio)

        if not dias:
            return {
                **_vacio(
                    "El archivo esta vacio: no hay ningun dia "
                    "de prensa guardado todavia."
                ),
                "available": True,
            }

        if almacen is None:
            try:
                from src.analysis.hold_backtest import STORE

                almacen = json.loads(
                    STORE.read_text(encoding="utf-8")
                )

            except Exception:                       # noqa: BLE001
                almacen = {}

        series = _series_por_dia(almacen)

        por_clase: dict = {}

        avisos = 0
        medibles = 0

        for dia in dias:

            for aviso in avisos_de(dia, directorio):

                avisos += 1

                clase = aviso["kind"]

                celda = por_clase.setdefault(
                    clase,
                    {
                        "notices": 0,
                        "horizons": {
                            str(h): {
                                "n": 0,
                                "moves": [],
                            }
                            for h in HORIZONTES
                        },
                    },
                )

                celda["notices"] += 1

                base = _precio_en(
                    series, aviso["player_id"], dia
                )

                if not base:
                    continue

                for horizonte in HORIZONTES:

                    despues = _precio_en(
                        series,
                        aviso["player_id"],
                        dia + timedelta(days=horizonte),
                    )

                    if not despues:
                        continue

                    medibles += 1

                    celda["horizons"][str(horizonte)][
                        "n"
                    ] += 1

                    celda["horizons"][str(horizonte)][
                        "moves"
                    ].append(
                        100 * (despues - base) / base
                    )

        return {
            "available": True,
            "observer_only": True,
            "days_archived": len(dias),
            "notices": avisos,
            "measurable": medibles,
            "horizons": list(HORIZONTES),
            "min_sample": MUESTRA_MINIMA,
            "by_kind": _resumir(por_clase),
            "reason": _reason(dias, avisos, medibles),
        }

    except Exception as error:                      # noqa: BLE001
        return _vacio(
            f"No se pudo montar el libro: "
            f"{type(error).__name__}: {error}"
        )


def _resumir(por_clase: dict) -> dict:
    """
    La mediana, la direccion y el fallo de cada clase.

    Con menos de `MUESTRA_MINIMA` no se publica mediana: se dice
    cuantos hay. Una mediana de cuatro casos parece un dato y no
    lo es.
    """

    import statistics

    salida = {}

    for clase, celda in sorted(por_clase.items()):

        horizontes = {}

        for nombre, datos in celda["horizons"].items():

            movimientos = datos["moves"]

            if len(movimientos) < MUESTRA_MINIMA:
                horizontes[nombre] = {
                    "n": len(movimientos),
                    "enough": False,
                    "median_percent": None,
                    "up_ratio": None,
                }
                continue

            horizontes[nombre] = {
                "n": len(movimientos),
                "enough": True,
                "median_percent": round(
                    statistics.median(movimientos), 3
                ),
                "up_ratio": round(
                    sum(1 for m in movimientos if m > 0)
                    / len(movimientos),
                    3,
                ),
            }

        salida[clase] = {
            "notices": celda["notices"],
            "horizons": horizontes,
        }

    return salida


def _reason(dias, avisos, medibles) -> str:

    if not avisos:
        return (
            f"{len(dias)} dia(s) archivados y ningun aviso de "
            f"prensa dentro."
        )

    if not medibles:
        return (
            f"{len(dias)} dia(s) archivados con {avisos} avisos, "
            f"pero ninguno tiene precio antes Y despues: hacen "
            f"falta al menos {min(HORIZONTES)} dia(s) mas de "
            f"archivo para medir el horizonte mas corto."
        )

    return (
        f"{len(dias)} dia(s) archivados, {avisos} avisos, "
        f"{medibles} medicion(es) de precio. Con "
        f"{MUESTRA_MINIMA} por clase y horizonte se empieza a "
        f"publicar mediana."
    )
