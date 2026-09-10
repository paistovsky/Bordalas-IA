"""
Guardar hoy lo que mañana no se podra reconstruir.

POR QUE EXISTE (09/09/2026)

    Al intentar cruzar las 156 subastas del tablon con las
    recomendaciones de las webs, no se pudo: el libro del ojeador
    guarda OCHO predicciones, todas del mismo dia. Las subastas
    iban del 10/08 al 06/09.

    No es que el analisis fuera dificil: es que el dato no
    existia. Se sobrescribia cada vuelta.

    **Cada dia sin archivar es un dia que no se podra analizar
    nunca.** Un precio se puede recuperar de Biwenger meses
    despues; un titular de prensa, no.

LO QUE CUESTA: NADA

    No baja nada nuevo. Copia lo que el ciclo YA descarga —el
    informe del ojeador y el de prensa— y lo deja fechado.

    Cero peticiones. Es la pieza mas barata del encargo y la mas
    valiosa.

QUE SE GUARDA, Y CON QUE FECHA

        archivo/2026-09-05/scout.json
        archivo/2026-09-05/press.json

    LA CARPETA LLEVA LA FECHA DEL INFORME, NO LA DE HOY
    (09/09/2026)

        La primera version estampaba el dia en que se archivaba.
        El 09/09 guardo bajo `2026-09-09` un informe cuyo
        `generated_at` era del 05/09: cuatro dias de diferencia.

        Eso envenena el libro de la prensa, que fecha los avisos
        por la carpeta. Un titular de hace cinco dias guardado
        como de hoy hace que el libro concluya que la noticia NO
        movio el precio — cuando lo movio cuatro dias antes, y
        el libro estaba mirando desde el dia equivocado.

        Es la sexta vez de la familia "un dato que dice ser lo
        que no es", y la primera que se caza antes de que nadie
        decida con ella.

    Y LO CADUCADO SE QUEDA FUERA

        Si el informe tiene mas de `HORAS_QUE_VALE`, no se
        archiva: se dice que la fuente esta parada y se deja
        fuera. Guardarlo otra vez bajo su propia fecha no haria
        daño —es idempotente— pero callarse que lleva cuatro
        dias sin refrescarse si lo hace.

    Uno por dia y fuente. La primera vuelta del dia escribe; las
    23 siguientes ven que ya esta y no hacen nada.

    Se guarda el informe ENTERO, no un resumen. Lo que hoy
    parece irrelevante es lo que mañana hara falta: el mes
    pasado nadie sabia que ibamos a querer cruzar titulares con
    subastas.

QUE NO HACE

    No decide nada, no borra nada y no lanza. Si el disco falla,
    el ciclo sigue: perder un dia de archivo es malo, tumbar el
    ciclo es peor.
"""

from __future__ import annotations

import json
import os

from datetime import date, datetime
from pathlib import Path


DIRECTORIO = (
    Path("data") / "intelligence" / "archivo"
)


# Lo que se archiva, y de donde sale. Todo esto lo escribe el
# ciclo en cada vuelta, asi que copiarlo no cuesta red.
FUENTES = {
    "scout": Path("data") / "intelligence" / "scout_report.json",
    "press": Path("data") / "intelligence" / "press_report.json",
}


DISABLE_ENV = "BORDALAS_SIN_ARCHIVO"


# Desde cuando un informe deja de poder representar "ahora".
#
# Veinticuatro horas, y sale de como corren las fuentes: el
# ojeador se refresca cada seis horas y la prensa dos veces al
# dia. Un informe de mas de un dia significa que su fuente esta
# parada, no que el mercado no se haya movido.
#
# No es un umbral de decision: nada se compra ni se vende por
# este numero. Solo decide si una copia entra en el archivo o se
# marca como caducada.
HORAS_QUE_VALE = 24


def dia_del_informe(ruta) -> dict:
    """
    La fecha que el propio informe dice tener.

    `{dia, generado, edad_horas, reason}`. Forma fija, nunca
    lanza. Sin `generated_at` legible devuelve `dia: None`, y
    quien llame decide — que aqui es no archivar.
    """

    vacio = {
        "dia": None,
        "generado": None,
        "edad_horas": None,
        "reason": None,
    }

    try:
        from pathlib import Path as _Path

        datos = json.loads(
            _Path(ruta).read_text(encoding="utf-8")
        )

        marca = (datos or {}).get("generated_at")

        if not marca:
            return {
                **vacio,
                "reason": (
                    "El informe no dice cuando se genero: no se "
                    "puede fechar."
                ),
            }

        cuando = datetime.fromisoformat(
            str(marca).replace("Z", "+00:00")
        )

        return {
            "dia": cuando.date(),
            "generado": cuando,
            "edad_horas": None,
            "reason": None,
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo leer la fecha: "
                f"{type(error).__name__}: {error}"
            ),
        }


# Cuantos dias se conservan. Sesenta, como el almacen de precios:
# el mismo horizonte para los dos, porque se van a cruzar.
#
# No es una limpieza agresiva: 521 jugadores de informe pesan
# unos cientos de KB al dia.
DIAS_QUE_SE_GUARDAN = 60


def _apagado() -> bool:
    return str(
        os.environ.get(DISABLE_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def archivar(
    dia: date | None = None,
    directorio: Path | None = None,
    fuentes: dict | None = None,
) -> dict:
    """
    Deja copia fechada de lo de hoy. Idempotente.

    `dia` se PASA -no se lee el reloj aqui si te lo dan-, para
    que las guardias puedan fijarlo. Sin el, hoy.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "available": False,
        "day": None,
        "written": [],
        "already": [],
        "missing": [],
        "stale": [],
        "undated": [],
        "failed": [],
        "reason": None,
    }

    try:
        if _apagado():
            return {
                **vacio,
                "reason": (
                    f"{DISABLE_ENV} puesto: no se archiva."
                ),
            }

        # `dia` es AHORA, para medir si un informe esta
        # caducado. No es la carpeta: la carpeta la dice cada
        # informe.
        ahora = dia or datetime.now().date()

        base = directorio or DIRECTORIO

        origenes = fuentes or FUENTES

        escritos = []
        ya_estaban = []
        sin_origen = []
        caducados = []
        sin_fecha = []
        fallidos = []

        for nombre, origen in origenes.items():

            origen = Path(origen)

            if not origen.exists():
                sin_origen.append(nombre)
                continue

            # LA FECHA LA DICE EL INFORME, NO EL RELOJ
            fechado = dia_del_informe(origen)

            if fechado["dia"] is None:
                sin_fecha.append(nombre)
                continue

            edad = (ahora - fechado["dia"]).days

            if edad * 24 > HORAS_QUE_VALE:
                caducados.append(
                    f"{nombre} ({fechado['dia'].isoformat()}, "
                    f"{edad} dia(s))"
                )
                continue

            raiz = base / fechado["dia"].isoformat()

            destino = raiz / f"{nombre}.json"

            if destino.exists():
                ya_estaban.append(nombre)
                continue

            try:
                raiz.mkdir(parents=True, exist_ok=True)

                # Se copia el texto tal cual: sin releer ni
                # reserializar. Lo que se archiva tiene que ser
                # EXACTAMENTE lo que el ciclo uso, no una version
                # limpia de ello.
                destino.write_text(
                    origen.read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

                escritos.append(nombre)

            except Exception as error:              # noqa: BLE001
                fallidos.append(
                    f"{nombre}: {type(error).__name__}"
                )

        return {
            "available": True,
            "day": ahora.isoformat(),
            "written": escritos,
            "already": ya_estaban,
            "missing": sin_origen,
            "stale": caducados,
            "undated": sin_fecha,
            "failed": fallidos,
            "reason": _reason(
                ahora,
                escritos,
                ya_estaban,
                sin_origen,
                caducados,
                sin_fecha,
                fallidos,
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo archivar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason(
    ahora, escritos, ya, sin_origen, caducados, sin_fecha,
    fallidos,
) -> str:

    if escritos:
        texto = f"Archivado: {', '.join(sorted(escritos))}."

    elif ya:
        texto = (
            f"Ya estaba archivado: {', '.join(sorted(ya))}."
        )

    else:
        texto = "Nada nuevo que archivar."

    if sin_origen:
        texto += (
            f" Sin fichero de origen: "
            f"{', '.join(sorted(sin_origen))}."
        )

    if caducados:
        # Esto no es un detalle: significa que una fuente lleva
        # dias sin refrescarse, y sin decirlo nadie se entera.
        texto += (
            f" CADUCADOS, fuera del archivo: "
            f"{', '.join(sorted(caducados))}."
        )

    if sin_fecha:
        texto += (
            f" Sin fecha dentro: "
            f"{', '.join(sorted(sin_fecha))}."
        )

    if fallidos:
        texto += f" Fallaron: {', '.join(sorted(fallidos))}."

    return texto


def dias_archivados(directorio: Path | None = None) -> dict:
    """
    Que dias hay y desde cuando. Forma fija, nunca lanza.

    Es lo que hay que publicar en pantalla para que el archivo
    no vuelva a estar vacio sin que nadie se entere.
    """

    vacio = {
        "available": False,
        "days": 0,
        "oldest": None,
        "newest": None,
        "sources": {},
        "reason": None,
    }

    try:
        raiz = directorio or DIRECTORIO

        if not raiz.exists():
            return {
                **vacio,
                "available": True,
                "reason": (
                    "El archivo esta vacio: hoy es el primer dia."
                ),
            }

        dias = sorted(
            carpeta.name
            for carpeta in raiz.iterdir()
            if carpeta.is_dir()
        )

        por_fuente: dict = {}

        for nombre in FUENTES:
            por_fuente[nombre] = sum(
                1
                for dia in dias
                if (raiz / dia / f"{nombre}.json").exists()
            )

        return {
            "available": True,
            "days": len(dias),
            "oldest": dias[0] if dias else None,
            "newest": dias[-1] if dias else None,
            "sources": por_fuente,
            "reason": (
                f"{len(dias)} dia(s) archivados, de "
                f"{dias[0]} a {dias[-1]}."
                if dias
                else "El archivo esta vacio: hoy es el primer dia."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo mirar el archivo: "
                f"{type(error).__name__}: {error}"
            ),
        }


def podar(
    hoy: date | None = None,
    directorio: Path | None = None,
    dias=DIAS_QUE_SE_GUARDAN,
) -> dict:
    """
    Borra lo que pase de `DIAS_QUE_SE_GUARDAN`.

    Se le PASA el dia, como todo aqui. Nunca lanza, y ante
    cualquier duda no borra: perder archivo es el fallo que este
    modulo existe para evitar.
    """

    vacio = {
        "available": False,
        "removed": [],
        "kept": 0,
        "reason": None,
    }

    try:
        import shutil

        raiz = directorio or DIRECTORIO

        if not raiz.exists():
            return {
                **vacio,
                "available": True,
                "reason": "No hay archivo que podar.",
            }

        cuando = hoy or datetime.now().date()

        borrados = []
        guardados = 0

        for carpeta in sorted(raiz.iterdir()):

            if not carpeta.is_dir():
                continue

            try:
                suyo = date.fromisoformat(carpeta.name)

            except ValueError:
                # Una carpeta con nombre raro NO se borra: no
                # sabemos que es.
                guardados += 1
                continue

            if (cuando - suyo).days > int(dias):
                shutil.rmtree(carpeta, ignore_errors=True)
                borrados.append(carpeta.name)

            else:
                guardados += 1

        return {
            "available": True,
            "removed": borrados,
            "kept": guardados,
            "reason": (
                f"{len(borrados)} dia(s) borrados por pasar de "
                f"{dias}; quedan {guardados}."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo podar: "
                f"{type(error).__name__}: {error}"
            ),
        }
