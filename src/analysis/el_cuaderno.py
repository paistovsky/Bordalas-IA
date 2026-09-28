"""
El cuaderno: los puntos que hizo el once que jugo, jornada a jornada.

POR QUE EL MARCADOR NO CUADRA (27/09/2026)

    Cinco jornadas cerradas y cero cuadran con Biwenger. En la J7
    el once anotado suma 27 y Biwenger dio 61. Medido sobre el
    historial de `marcador.json` en git, son TRES fallos a la vez:

    1. EL ROUND DE BIWENGER SALTA A MITAD DE JORNADA.
       `rounds.data.round.id` paso de 5125 (J7) a 4905 (J8) el
       19/09 entre las 07:17 y las 11:48 de Madrid, con la J7 a
       medio jugar (cerro el 20/09 a las 23:00). El marcador guarda
       por ese id: la J7 se quedo congelada con los totales del
       viernes y el resto de sus puntos se esta sumando a la J8.

    2. LOS TOTALES SOLO CUBREN LA PLANTILLA DE HOY.
       `observar()` saca los totales de `my_team`. Dituro y Djene
       jugaron la J7 y el 21/09 ya no estaban: salen de la resta y
       el once pierde sus puntos sin avisar.

    3. LA CLASIFICACION PARECE IR CON RETRASO.
       Pepe acumulado: 186 (16/09), 247 (19/09 manana, con la J7
       casi sin jugar) y 276 (21/09). No se sabe aun de que
       jornada es cada salto. Este modulo NO lo arregla: no compara
       contra la clasificacion.

LO QUE HACE ESTE MODULO

    Cruza dos libros que ya existen y que no tienen los fallos 1 y
    2, porque los dos van por la jornada de LALIGA y no por el
    round de Biwenger:

        puntos_por_jornada.jsonl   una linea por jornada cerrada
                                   con los totales de TODO el
                                   catalogo (547), vendidos incluidos
        onces_de_la_jornada.jsonl  el once, congelado en la ventana
                                   antes del primer partido

    Los puntos de la jornada N de un jugador son
    total(linea N) - total(linea N-1). Lo mismo con los partidos
    jugados: si no sube, ese jugador no jugo, y un titular que no
    juega es un cero seguro. Eso es lo que hay que mirar.

QUE NO HACE

    No decide. No escribe en Biwenger ni en ningun libro. No
    inventa: sin las dos lineas o sin el once congelado, la
    jornada sale `medible: false` con el motivo.

REGLA 23

    Las funciones reciben las filas por la puerta. Solo
    `cargar_libros()` lee disco, y ninguna guardia la llama.
"""

from __future__ import annotations

import json
from pathlib import Path


LIBRO_DE_PUNTOS = (
    Path("data") / "intelligence" / "puntos_por_jornada.jsonl"
)

LIBRO_DE_ONCES = (
    Path("data") / "intelligence" / "onces_de_la_jornada.jsonl"
)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _leer(ruta: Path) -> list:
    try:
        if not ruta.exists():
            return []

        filas = []

        for linea in ruta.read_text(encoding="utf-8").splitlines():

            if not linea.strip():
                continue

            try:
                fila = json.loads(linea)
            except json.JSONDecodeError:
                continue

            if isinstance(fila, dict):
                filas.append(fila)

        return filas

    except OSError:
        return []


def cargar_libros() -> tuple:
    """Las dos listas de filas, del disco. Nunca lanza."""

    return _leer(LIBRO_DE_PUNTOS), _leer(LIBRO_DE_ONCES)


def _por_jornada(filas, clave: str) -> dict:
    """`{jornada: fila}`. Si hay dos, gana la PRIMERA."""

    salida = {}

    for fila in (filas or []):

        if not isinstance(fila, dict):
            continue

        numero = safe_int(fila.get(clave))

        if numero and numero not in salida:
            salida[numero] = fila

    return salida


def puntos_de_la_jornada(fotos, jornada) -> dict:
    """
    Lo que hizo cada jugador en esa jornada de LaLiga. Forma fija.

        {"medible", "motivo", "puntos": {id: [puntos, jugados]}}
    """

    jornada = safe_int(jornada)

    por_jornada = _por_jornada(fotos, "jornada")

    actual = por_jornada.get(jornada)
    previa = por_jornada.get(jornada - 1)

    if actual is None:
        return {
            "medible": False,
            "motivo": f"No hay foto de la jornada {jornada} cerrada.",
            "puntos": {},
        }

    if previa is None:
        return {
            "medible": False,
            "motivo": (
                f"No hay foto de la jornada {jornada - 1}: sin ella "
                f"no se puede restar y los totales no son de una "
                f"jornada sino de la temporada."
            ),
            "puntos": {},
        }

    ahora = actual.get("players") or {}
    antes = previa.get("players") or {}

    puntos = {}

    for pid, fila in ahora.items():

        if pid not in antes:
            continue

        try:
            hechos = safe_int(fila[0]) - safe_int(antes[pid][0])
            jugados = safe_int(fila[1]) - safe_int(antes[pid][1])
        except (TypeError, IndexError, KeyError):
            continue

        puntos[str(pid)] = [hechos, jugados]

    return {"medible": True, "motivo": None, "puntos": puntos}


def la_nota_del_once(fotos, onces, jornada) -> dict:
    """
    Los puntos que hizo el once congelado de esa jornada. Forma
    fija. Nunca lanza.
    """

    jornada = safe_int(jornada)

    salida = {
        "jornada": jornada,
        "medible": False,
        "motivo": None,
        "formation": None,
        "puntos_once": None,
        "no_jugaron": [],
        "sin_dato": [],
        "jugadores": [],
    }

    try:

        once = _por_jornada(onces, "matchday").get(jornada)

        if once is None:
            salida["motivo"] = (
                f"No se congelo el once de la jornada {jornada}: "
                f"no se sabe que once jugo."
            )
            return salida

        medida = puntos_de_la_jornada(fotos, jornada)

        if not medida["medible"]:
            salida["motivo"] = medida["motivo"]
            return salida

        jugadores = []
        sin_dato = []
        no_jugaron = []

        for pid in (once.get("players") or []):

            clave = str(safe_int(pid))

            if clave not in medida["puntos"]:
                sin_dato.append(clave)
                continue

            hechos, jugados = medida["puntos"][clave]

            if jugados <= 0:
                no_jugaron.append(clave)

            jugadores.append({
                "id": clave,
                "puntos": hechos,
                "jugo": jugados > 0,
            })

        salida["formation"] = once.get("formation")
        salida["jugadores"] = jugadores
        salida["sin_dato"] = sin_dato
        salida["no_jugaron"] = no_jugaron

        # UN HUECO NO ES UN CERO. Si falta un jugador en las fotos,
        # la suma saldria baja y pareceria buena. Se dice y no se
        # publica numero.
        if sin_dato:
            salida["motivo"] = (
                f"{len(sin_dato)} jugador(es) del once sin foto: "
                f"la suma saldria incompleta."
            )
            return salida

        salida["puntos_once"] = sum(j["puntos"] for j in jugadores)
        salida["medible"] = True

        return salida

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = (
            f"No se pudo medir: {type(error).__name__}: {error}"
        )
        return salida


def el_cuaderno(fotos, onces) -> dict:
    """
    Una nota por cada jornada con foto cerrada. Forma fija. Nunca
    lanza. Lo que publica el panel.
    """

    try:
        jornadas = sorted(_por_jornada(fotos, "jornada"))

        notas = [
            la_nota_del_once(fotos, onces, jornada)
            for jornada in jornadas
        ]

        medibles = [n for n in notas if n["medible"]]

        return {
            "available": True,
            "jornadas": notas,
            "medibles": len(medibles),
            "titulares_que_no_jugaron": sum(
                len(n["no_jugaron"]) for n in medibles
            ),
            "reason": (
                f"{len(medibles)} de {len(notas)} jornada(s) con nota."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "available": False,
            "jornadas": [],
            "medibles": 0,
            "titulares_que_no_jugaron": 0,
            "reason": (
                f"No se pudo leer el cuaderno: "
                f"{type(error).__name__}: {error}"
            ),
        }
