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

Y CON EL TABLON (28/10/2026)

    Si se le pasan los eventos del tablon, cada nota se cruza con
    `roundFinished` de su ronda (`puntos_biwenger`, `cuadra`), y
    una jornada cuya ventana lleva dentro OTRA ronda —una aplazada
    que se jugo entre dos cierres— no se publica como nota.

Y LA FOTO QUE LLEGA ANTES DEL LUNES (28/10/2026)

    La foto de cierre se hace unas dos horas despues del ultimo
    partido del lunes, antes de que Biwenger lo puntue: cada
    ventana lleva el lunes de la jornada anterior y le falta el
    suyo. Una ventana con algun jugador de DOS partidos no se
    publica como nota, con tablon o sin el. Era la J9 «49 = 49»:
    +6 de Olasagasti (lunes de la J8) y -5 de Unai Lopez (lunes
    de la J9, que la foto no tenia); el mismo once suma 48.

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

        # LA VENTANA CON EL LUNES DE LA ANTERIOR (28/10/2026). Un
        # jugador con dos partidos en la ventana dice que la foto
        # anterior se hizo antes de puntuar su lunes: esta ventana
        # lo lleva, y casi seguro le falta el suyo. Los puntos por
        # jugador no son los de la jornada; tampoco los «no jugo».
        dos_partidos = sorted(
            pid
            for pid, (hechos, jugados) in medida["puntos"].items()
            if jugados >= 2
        )

        salida["jugadores_con_dos_partidos"] = len(dos_partidos)

        if dos_partidos:
            salida["puntos_mezclados"] = sum(j["puntos"] for j in jugadores)
            salida["motivo"] = (
                f"La ventana de la jornada {jornada} lleva partidos "
                f"de otra: {len(dos_partidos)} jugador(es) con dos "
                f"partidos (el lunes de la anterior, porque la foto "
                f"de cierre se hace antes de que Biwenger lo puntue, "
                f"o una aplazada). Y la que se deja el lunes de la "
                f"anterior se deja tambien el suyo: la suma "
                f"({salida['puntos_mezclados']}) no es la de la "
                f"jornada. No es una nota."
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


# ================================================================
# LA VENTANA QUE LLEVA DOS RONDAS DENTRO  (28/10/2026)
# ================================================================
#
#     El cuaderno daba 49 en la J10 y Biwenger pago 39. El once
#     ERA el bueno (el congelado de la J10, el mismo que vio el
#     marcador tras el pitido). Lo que sobraba eran los puntos:
#     la resta va del cierre de la J9 (19/10) al de la J10
#     (26/10), y esa ventana lleva DOS cosas que no son la J10:
#
#         · la «Jornada 6 (aplazada)» parte 3 (round 5176), solo
#           Levante-Athletic el 21/10: Olasagasti (Levante) +5,
#           en una ronda que Biwenger cobra aparte;
#         · el lunes de la J9 (Getafe-Rayo, 19/10 21:00), que la
#           foto de la J9 aun no tenia: Unai Lopez (Rayo) +5.
#
#     49 = 39 + 5 + 5. Lo segundo no es de la J10 ni de ninguna
#     aplazada: es la foto de cierre, que se hace antes de puntuar
#     el lunes (ver `la_nota_del_once`), y le pasa a todas.
#
#     El tablon dice cuando empieza cada ronda. Si en la ventana
#     de la jornada N empieza alguna que no sea «Jornada N», la
#     suma mezcla dos rondas: no se publica como nota.


def rondas_en_la_ventana(fotos, jornada, cierres) -> dict:
    """Que rondas del tablon empiezan entre el cierre de la N-1 y
    el de la N. `{"propia", "otras"}`. Nunca lanza."""

    from src.analysis.marcador import _momento, es_aplazada

    salida = {"propia": None, "otras": []}

    try:
        jornada = safe_int(jornada)
        por_jornada = _por_jornada(fotos, "jornada")

        actual = por_jornada.get(jornada)
        previa = por_jornada.get(jornada - 1)

        desde = _momento((previa or {}).get("cerrada_en"))
        hasta = _momento((actual or {}).get("cerrada_en"))

        if desde is None or hasta is None:
            return salida

        for round_id, fila in sorted((cierres or {}).items()):

            empieza = (fila or {}).get("empieza")

            if empieza is None or not (desde < empieza <= hasta):
                continue

            if (
                fila.get("numero") == jornada
                and not es_aplazada(fila.get("nombre"), fila.get("part"))
            ):
                salida["propia"] = round_id
                continue

            salida["otras"].append({
                "round_id": round_id,
                "nombre": fila.get("nombre") or "",
            })

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def _con_el_tablon(nota, fotos, cierres, mi_user_id) -> dict:
    """La nota, cruzada con el tablon. Nunca lanza."""

    try:
        ventana = rondas_en_la_ventana(fotos, nota.get("jornada"), cierres)

        nota["ronda"] = ventana["propia"]
        nota["rondas_dentro"] = ventana["otras"]

        # La aplazada dentro se dice tambien cuando la nota ya se
        # habia caido por el lunes de la anterior: son dos motivos.
        if ventana["otras"] and (
            nota.get("medible") or nota.get("puntos_mezclados") is not None
        ):

            cuales = ", ".join(
                f"{o['nombre'] or o['round_id']} ({o['round_id']})"
                for o in ventana["otras"]
            )

            if nota.get("medible"):
                nota["puntos_mezclados"] = nota.get("puntos_once")

            antes = None if nota.get("medible") else nota.get("motivo")

            nota["puntos_once"] = None
            nota["medible"] = False
            nota["motivo"] = (
                f"La ventana de la jornada {nota.get('jornada')} "
                f"lleva dentro {cuales}, que Biwenger puntua aparte "
                f"y con otro once: la suma ({nota['puntos_mezclados']}) "
                f"mezcla dos rondas. No es una nota."
                + (f" {antes}" if antes else "")
            )

        cierre = (cierres or {}).get(ventana["propia"]) or {}

        nota["puntos_biwenger"] = (
            (cierre.get("puntos") or {}).get(safe_int(mi_user_id))
            if cierre.get("puntos") is not None and mi_user_id
            else None
        )

        nota["cuadra"] = (
            nota["puntos_once"] == nota["puntos_biwenger"]
            if nota.get("medible")
            and nota["puntos_biwenger"] is not None
            else None
        )

        return nota

    except Exception:                               # noqa: BLE001
        return nota


def el_cuaderno(fotos, onces, eventos=None, mi_user_id=None) -> dict:
    """
    Una nota por cada jornada con foto cerrada. Forma fija. Nunca
    lanza. Lo que publica el panel.

    Con `eventos` (el tablon) cada nota se cruza con su ronda:
    `puntos_biwenger`, `cuadra`, y fuera de la nota la jornada
    cuya ventana lleva dentro otra ronda.
    """

    try:
        jornadas = sorted(_por_jornada(fotos, "jornada"))

        notas = [
            la_nota_del_once(fotos, onces, jornada)
            for jornada in jornadas
        ]

        if eventos:
            from src.analysis.marcador import cierres_del_tablon

            cierres = cierres_del_tablon(eventos)

            notas = [
                _con_el_tablon(nota, fotos, cierres, mi_user_id)
                for nota in notas
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
