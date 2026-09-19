"""
El cupo cuenta lo que se ENVIA, no lo que se gana.

EL AGUJERO, CON LA LINEA DELANTE

    `libro_de_viajes.cuantos_en_este_reset`, linea 521:

        if fila.get("state") != ABIERTO:
            continue

    Cuenta filas de `libro_de_viajes.jsonl` con `state ==
    ABIERTO`. Un viaje solo se abre cuando la puja se GANA. Asi
    que:

        se puja        -> no hay viaje todavia -> no cuenta
        se repuja      -> sigue sin haber viaje -> no cuenta
        se gana        -> AHORA cuenta, una vez

    El numero va a `la_rendija.permiso` (linea 1461):

        quedan_reset = max(0, cupo["cupo"] - operaciones_en_este_reset)

    Un cupo que cuenta lo que ganas no es un cupo: es un
    marcador. Medido: nueve escrituras de Maffeo el 18/09 contra
    un cupo de 1, y el portero no se entero porque estaba
    contando otra cosa.

    Y el otro cupo, el de la vuelta, tampoco mordia:
    `escrituras_en_esta_vuelta` tiene valor por defecto 0 y NADIE
    se lo pasa.

QUE CUENTA ESTO

    Filas con `sent: True` en los libros de cada familia, desde
    una marca de tiempo. Una por envio, repetidas incluidas —que
    es justo el punto: si deduplicara, repetir volveria a ser
    gratis.

    La identidad de la OPERACION sigue viviendo en `event_id`,
    que es otra pregunta y otro sitio.

DOCTRINA 24: NADA PASA CON LAS MANOS VACIAS

    Un libro que NO EXISTE significa que esa familia no ha
    escrito nunca: cero, y se puede seguir.

    Un libro que existe y NO SE PUEDE LEER significa que no se
    sabe cuanto se ha escrito. Eso NO es cero. Se devuelve
    `available: False` y quien llame no debe escribir.

    Las dos cosas salian iguales hasta hoy en todo lo que toca
    esta cadena.
"""

from __future__ import annotations

import json
import os

from datetime import datetime
from pathlib import Path


# EL INTERRUPTOR
#
#     Apagado, el cupo sigue contando viajes abiertos y el
#     comportamiento es el de siempre.
#
#     NO SE ENCIENDE SIN NUMEROS NUEVOS, y eso lo decide el
#     dueno. Medido sobre la ventana 10/09 -> 18/09, con el cupo
#     actual de 1 por reset contando envios se habrian frenado 37
#     de las 43 escrituras — y entre ellas DIEZ renovaciones
#     legitimas de jugadores DISTINTOS. Ver el informe.
CUPO_POR_ENVIOS_ENV = "BORDALAS_CUPO_POR_ENVIOS"


# ============================================================
# LOS CUPOS, POR FAMILIA (19/09/2026)
# ============================================================
#
#     Decididos por el dueno sobre el pico LEGITIMO medido, ya
#     sin repeticiones, en n=5 resets con actividad del 10/09 al
#     18/09:
#
#         familia    pico medido    cupo
#         renovar         9          12
#         puja            2           3
#         publicar        1           4
#
#     POR QUE UNO POR FAMILIA Y NO UNO SOLO. Las unidades no son
#     comparables: renovar es mantenimiento y no compromete un
#     euro; pujar si. Un cupo compartido dimensionado para la
#     puja estrangula a renovar —el 10/09 hubo NUEVE
#     renovaciones legitimas de nueve jugadores distintos— y
#     dimensionado para renovar deja pujar nueve veces.
#
#     POR QUE GENEROSOS. Con `filtrar_los_repetidos` puesto
#     delante, el cupo ya solo limita VOLUMEN: la repeticion la
#     para la identidad, que es otra pieza (doctrina 93). En esa
#     situacion pasarse de generoso cuesta poco y quedarse corto
#     mata trabajo legitimo. Con el cupo de 1 se habrian frenado
#     37 de las 43 escrituras de la ventana, diez de ellas
#     renovaciones buenas.
#
#     LAS QUE NO LLEVAN NUMERO. `vender`, `aceptar`, `reroll` y
#     `alineacion` no tienen cupo porque no hay una sola
#     escritura suya medida: sus libros se crearon el 19/09. No
#     se pone un tope a lo que no se ha visto.
CUPOS_POR_FAMILIA = {
    "renovar": 12,
    "puja": 3,
    "publicar": 4,
}


# ============================================================
# ESTOS NUMEROS CADUCAN. FECHA PUESTA.
# ============================================================
#
#     n = 5 resets es poco para fijar un tope y quedo dicho al
#     proponerlos. Se aceptaron sabiendolo.
#
#     El 26/09/2026 hay que volver a medir, y para entonces
#     habra con que: los tres libros nuevos -aceptar, reroll,
#     alineacion- llevaran una semana escribiendo, y la foto
#     diaria en `data/fotos/` otra semana acumulada.
#
#     `la_revision_del_cupo()` lo publica para que salga en el
#     panel. No vive solo en un informe: un recordatorio que hay
#     que acordarse de leer no es un recordatorio.
REVISION_DE_LOS_CUPOS = "2026-09-26"

REVISION_MOTIVO = (
    "Los cupos por familia se pusieron con n=5 resets "
    "(10/09-18/09), que es poco para un tope. Toca volver a "
    "medirlos con los tres libros nuevos escribiendo y una "
    "semana de fotos diarias."
)


def cupo_de(familia: str) -> int | None:
    """
    El cupo de esta familia, o None si no tiene numero.

    `None` NO es cero: es que no se ha medido. Quien lo reciba
    no debe convertirlo en un freno.
    """

    return CUPOS_POR_FAMILIA.get(familia)


def la_revision_del_cupo(hoy: str | None = None) -> dict:
    """
    Si toca volver a medir los cupos. Forma fija, nunca lanza.

    `hoy` se RECIBE, no se deduce del reloj: una guardia que
    mira la hora del sistema cambia de color sin que cambie el
    codigo, y eso ya nos costo una verja roja el 13/09.
    """

    salida = {
        "fecha": REVISION_DE_LOS_CUPOS,
        "toca": None,
        "dias": None,
        "cupos": dict(CUPOS_POR_FAMILIA),
        "n_resets": 5,
        "ventana": "10/09-18/09",
        "reason": REVISION_MOTIVO,
    }

    if not hoy:
        return {
            **salida,
            "reason": (
                f"{REVISION_MOTIVO} Sin saber que dia es hoy no "
                f"se puede decir si toca: la revision es el "
                f"{REVISION_DE_LOS_CUPOS}."
            ),
        }

    try:
        from datetime import date

        dia = date.fromisoformat(str(hoy)[:10])

        limite = date.fromisoformat(REVISION_DE_LOS_CUPOS)

        dias = (limite - dia).days

        return {
            **salida,
            "toca": dias <= 0,
            "dias": dias,
            "reason": (
                f"{REVISION_MOTIVO} "
                + (
                    f"TOCA: la fecha era el "
                    f"{REVISION_DE_LOS_CUPOS} y han pasado "
                    f"{-dias} dia(s)."
                    if dias <= 0
                    else f"Quedan {dias} dia(s), hasta el "
                    f"{REVISION_DE_LOS_CUPOS}."
                )
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **salida,
            "reason": (
                f"{REVISION_MOTIVO} No se pudo leer la fecha: "
                f"{type(error).__name__}: {error}"
            ),
        }


def cupo_por_envios_activo() -> bool:
    """
    Si el cupo cuenta envios en vez de viajes ganados.

    Forma fija. Nunca lanza.
    """

    return str(
        os.environ.get(CUPO_POR_ENVIOS_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


# ============================================================
# LAS FAMILIAS Y SUS LIBROS
# ============================================================
#
#     Cada familia de escritura contra Biwenger, con el libro
#     donde deja rastro. Los tres primeros existian; los cuatro
#     siguientes se crean hoy porque sin rastro no se puede
#     medir, y una de ellas -aceptar- es la que la regla del
#     deficit va a usar en cuanto se encienda.
LIBROS_POR_FAMILIA = {
    "puja": Path("data") / "trading" / "libro_del_carril.jsonl",
    "publicar": (
        Path("data") / "trading" / "libro_de_escaparate.jsonl"
    ),
    "renovar": (
        Path("data") / "trading" / "libro_de_renovaciones.jsonl"
    ),
    "vender": Path("data") / "trading" / "libro_de_salidas.jsonl",
    "aceptar": (
        Path("data") / "trading" / "libro_de_aceptadas.jsonl"
    ),
    "reroll": Path("data") / "trading" / "libro_de_rerolls.jsonl",
    "alineacion": (
        Path("data") / "trading" / "libro_de_alineaciones.jsonl"
    ),
}


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return default


def _marca(fila: dict) -> float | None:
    """La hora del envio, en epoch. None si no se sabe."""

    crudo = fila.get("at") or fila.get("timestamp")

    if not crudo:
        return None

    try:
        return datetime.fromisoformat(str(crudo)).timestamp()

    except (TypeError, ValueError):
        return None


def escrituras_enviadas(
    familia: str,
    desde_epoch: float | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    Cuantas escrituras REALES lleva esta familia desde la marca.

    Forma fija. Nunca lanza.

    `available: False` significa "no se sabe", y quien llame no
    debe escribir. No confundir con `cuantas: 0`, que significa
    "no ha escrito ninguna".
    """

    vacio = {
        "available": False,
        "familia": familia,
        "cuantas": 0,
        "reason": None,
    }

    destino = ruta or LIBROS_POR_FAMILIA.get(familia)

    if destino is None:
        return {
            **vacio,
            "reason": (
                f"La familia «{familia}» no tiene libro "
                f"declarado: no se sabe cuanto ha escrito."
            ),
        }

    if desde_epoch is None:
        return {
            **vacio,
            "reason": (
                "Sin marca desde la que contar no se sabe cuantas "
                "escrituras van en este reset."
            ),
        }

    # UN LIBRO QUE NO EXISTE SI ES UN CERO.
    #
    #     Esa familia no ha escrito nunca. Es un hecho, no una
    #     ausencia de dato: el fichero lo crea la primera
    #     escritura.
    if not destino.exists():
        return {
            "available": True,
            "familia": familia,
            "cuantas": 0,
            "reason": (
                f"«{familia}» no ha escrito nunca: su libro "
                f"todavia no existe."
            ),
        }

    try:
        crudo = destino.read_text(encoding="utf-8")

    except OSError as error:
        return {
            **vacio,
            "reason": (
                f"No se pudo leer el libro de «{familia}» "
                f"({type(error).__name__}): no se sabe cuanto ha "
                f"escrito, y no saberlo no es cero."
            ),
        }

    cuantas = 0

    ilegibles = 0

    for linea in crudo.splitlines():

        if not linea.strip():
            continue

        try:
            fila = json.loads(linea)

        except json.JSONDecodeError:
            ilegibles += 1
            continue

        if not isinstance(fila, dict):
            ilegibles += 1
            continue

        if not fila.get("sent"):
            continue

        cuando = _marca(fila)

        if cuando is None:
            # Una escritura sin hora no se puede situar en este
            # reset ni fuera de el. Cuenta, que es el lado
            # seguro: de las dos formas de equivocarse, la que
            # frena de mas cuesta una vuelta y la otra cuesta una
            # repeticion.
            cuantas += 1
            continue

        if cuando >= desde_epoch:
            cuantas += 1

    # UN LIBRO ROTO NO SE REDONDEA A LA BAJA.
    if ilegibles:
        return {
            **vacio,
            "cuantas": cuantas,
            "reason": (
                f"El libro de «{familia}» tiene {ilegibles} "
                f"linea(s) ilegible(s): lo que se ha contado "
                f"({cuantas}) puede quedarse corto, y no se "
                f"escribe con un cupo que no se sabe."
            ),
        }

    return {
        "available": True,
        "familia": familia,
        "cuantas": cuantas,
        "reason": (
            f"«{familia}» lleva {cuantas} escritura(s) enviada(s) "
            f"en este reset."
        ),
    }


def puerta_del_cupo(
    familia: str,
    cupo: int,
    desde_epoch: float | None = None,
    ruta: Path | None = None,
) -> dict:
    """
    ¿Le queda cupo a esta familia? Y si no, que lo diga entero.

    EL MOTIVO NOMBRA AL QUE DECIDIO (doctrina 87)

        Que escritura, contra que cupo, y cuantas van. Un "sin
        cupo" pelado no se puede comprobar.

    Forma fija. Nunca lanza.
    """

    llevadas = escrituras_enviadas(
        familia, desde_epoch=desde_epoch, ruta=ruta
    )

    tope = safe_int(cupo)

    if not llevadas["available"]:
        return {
            "available": False,
            "puede": False,
            "familia": familia,
            "cupo": tope,
            "llevadas": llevadas["cuantas"],
            "quedan": 0,
            "blocked_by": "CUPO_SIN_SABER",
            "reason": llevadas["reason"],
        }

    van = llevadas["cuantas"]

    quedan = max(tope - van, 0)

    return {
        "available": True,
        "puede": quedan > 0,
        "familia": familia,
        "cupo": tope,
        "llevadas": van,
        "quedan": quedan,
        "blocked_by": None if quedan > 0 else "CUPO_DE_LA_FAMILIA",
        "reason": (
            f"«{familia}»: van {van} escritura(s) enviada(s) de "
            f"un cupo de {tope} en este reset"
            + (
                f"; quedan {quedan}."
                if quedan > 0
                else ". No se escribe ninguna mas."
            )
        ),
    }
