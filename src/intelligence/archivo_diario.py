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

    Y LA TITULARIDAD DEL DIA (19/10/2026), aparte y en un libro de
    git: la de FutbolFantasy de todos los que ya lee el ciclo y el
    estado de Biwenger de todo el catalogo. Ver
    `archivar_la_titularidad`, abajo.

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


# ============================================================
# LA TITULARIDAD DEL DIA (19/10/2026)
# ============================================================
#
#     EL HUECO. El laboratorio del 19/10 quiso validar el xP de la
#     J8 y la J9 y no pudo: la titularidad de FutbolFantasy solo
#     quedaba guardada para 141 de los 551 jugadores (los objetivos
#     del tablero, que se pisa cada vuelta) y, antes de cada
#     jornada, solo para los que salieron al mercado (el informe de
#     la mañana). El estado de Biwenger de todo LaLiga, igual: vive
#     en la foto, que caduca. "Sin esto, J8 y J9 no se pueden
#     validar bien y la penalizacion de -1,2 no se puede comprobar."
#
#     UNA LINEA AL DIA, EN UN LIBRO. No en `archivo/` de arriba: ese
#     vive en la cache de GitHub Actions, que se desaloja a los 7
#     dias sin uso y que el laboratorio no puede leer. Este va a git
#     (`src/estado/los_libros.py`).
#
#     LO QUE CUESTA: NI UNA PETICION. Las filas de FF ya las bajaba
#     el tablero -las 20 paginas traen la plantilla entera- y ahora
#     las guarda (`futbolfantasy_provider.CAMPOS_DE_LA_PLANTILLA`).
#     El estado viene en el catalogo de la foto. Lo unico nuevo es
#     emparejar, una vez al dia, las filas que el tablero no
#     emparejo: con la misma maquina (`match_team`: por equipo, el
#     euro y el nombre) y contra el catalogo de ese equipo. Lo que
#     no empareja NO se adivina: se guarda con su identidad de FF
#     (`ff_sin_id`), que lleva el valor Biwenger de FF para cruzarlo
#     despues.
#
#     NADIE DECIDE CON ESTO. Es para medir.
#
#     LA FORMA, compacta (una linea de ~21 KB con 551 del catalogo y
#     ~550 filas de FF; 1,3 MB a 60 dias):
#
#         dia          el dia de Madrid de la vuelta que la escribe:
#                      la primera DESPUES DEL RESET de ese dia; las
#                      demas ven que ya esta (y solo la reescriben si
#                      esta a medias y la suya es mejor: ver abajo)
#         reset_at     el reset del que es el estado de Biwenger: la
#                      cache del catalogo no sirve nada de antes
#                      (`cache_del_reset.leer`)
#         ff           {player_id: [titular, jerarquia, parte]}: el %
#                      de FF, `data-jerarquia` y `data-estado`
#         ff_sin_id    [[equipo, slug, nombre, titular, jerarquia,
#                      parte, valor_biwenger_de_ff]]
#         biwenger     {player_id: status} de todo el catalogo
#         ff_at        cuando se bajo el tablero; con mas de
#                      `HORAS_QUE_VALE` no se guarda FF (`ff_motivo`)
#         ff_at_por_equipo  {equipo: cuando se bajo SU pagina}: al
#                      completar, el tablero arrastra plantillas de
#                      otras vueltas con la hora del tablero nueva. La
#                      de mas de `HORAS_QUE_VALE` o de antes de ese dia
#                      no se guarda como de hoy (`ff_viejos`)
#         ff_cache, ff_errores  `cache.status` y `metadata.errors` del
#                      tablero
#         ff_motivo    por que FF falta o esta a medias; None = entera
#
#     EL DIA EMPIEZA EN EL RESET. La vuelta de las 00:07 de Madrid
#     es la primera del dia, pero fuera del dia de jornada su
#     catalogo es el de la cache, guardado en la primera vuelta
#     despues del reset ANTERIOR (07:15 de ayer), y la foto no dice
#     cuando se bajo (`timestamp` es la hora de la foto). Archivado
#     como de hoy, era el estado de ayer. Ahora no se escribe hasta
#     la primera vuelta despues del reset de hoy (la de las 07:15).
#
#     UNA LINEA A MEDIAS NO CONGELA EL DIA. La primera linea del dia
#     lo era aunque fuera CADUCADO, SIN_PLANTILLAS o con paginas de FF
#     que fallaron. Ahora el dia solo "ya esta" si su linea esta
#     entera (`_entera`: sin `ff_motivo`, con estado de Biwenger y con
#     FF); si no, una vuelta posterior la reescribe EN SU SITIO cuando
#     la suya es mejor (`_calidad`). Igual de buena, no se toca: cada
#     linea escrita es un commit.
#
#     SE PODA a `DIAS_QUE_SE_GUARDAN` (60), como el archivo: lo de
#     antes sigue en el historial de git. Una linea que no se sabe
#     leer no se borra: se lee linea a linea, y una cortada a mitad
#     de una letra (UTF-8 roto) se queda tal cual, con sus bytes, sin
#     tapar al resto. Antes tapaba el libro entero: cada vuelta veia
#     un libro vacio y añadia otra linea del mismo dia, pegada a la
#     cortada. Si el fichero existe y no se puede abrir, no se escribe.

LIBRO_DE_LA_TITULARIDAD = (
    Path("data") / "intelligence" / "la_titularidad_del_dia.jsonl"
)

CAMPOS_FF = ("titular", "jerarquia", "parte")

CAMPOS_FF_SIN_ID = (
    "equipo", "slug", "nombre", "titular", "jerarquia", "parte",
    "valor_biwenger_de_ff",
)


def _compacto(valor):
    """85.0 -> 85: la linea pesa menos y dice lo mismo."""

    if isinstance(valor, float) and valor.is_integer():
        return int(valor)

    return valor


def _int(valor):
    try:
        if valor is None or isinstance(valor, bool):
            return None
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return None


def _cuando(valor):
    """ISO a datetime con zona (sin zona, UTC). None si no se lee."""

    try:
        cuando = (
            valor
            if isinstance(valor, datetime)
            else datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        )
    except (TypeError, ValueError):
        return None

    if cuando.tzinfo is None:
        from datetime import timezone

        cuando = cuando.replace(tzinfo=timezone.utc)

    return cuando


def el_dia_de_madrid(ahora) -> date:
    """El dia de Madrid de `ahora` (UTC si no trae zona)."""

    from datetime import timedelta, timezone

    from src.analysis.market_clock import madrid_offset_hours

    momento = (_cuando(ahora) or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )

    return (momento + timedelta(hours=madrid_offset_hours(momento))).date()


def _inicio_del_dia(dia: date) -> datetime:
    """Las 00:00 de Madrid de `dia`, en UTC."""

    from datetime import timedelta, timezone

    from src.analysis.market_clock import madrid_offset_hours

    medianoche = datetime(dia.year, dia.month, dia.day, tzinfo=timezone.utc)

    # Dos pasadas: el desfase que vale es el de la medianoche de
    # Madrid, no el de las 00:00 UTC (el dia del cambio de hora).
    inicio = medianoche - timedelta(hours=madrid_offset_hours(medianoche))

    return medianoche - timedelta(hours=madrid_offset_hours(inicio))


def el_ultimo_reset(ahora) -> datetime | None:
    """
    El reset mas reciente a `ahora`, en UTC: el mismo corte que usa
    la cache del catalogo (`cache_del_reset.ultimo_reset`). None si
    no se sabe. Nunca lanza.
    """

    from datetime import timezone

    try:
        from src.biwenger.cache_del_reset import ultimo_reset

        epoch = ultimo_reset(_cuando(ahora) or datetime.now(timezone.utc))

        return datetime.fromtimestamp(epoch, timezone.utc) if epoch else None

    except Exception:                               # noqa: BLE001
        return None


def la_titularidad_de_hoy(snapshot, tablero, ahora) -> dict:
    """
    La linea del dia, SIN escribirla. Pura: todo entra por
    argumento. Forma fija, nunca lanza.
    """

    from datetime import timezone

    linea = {
        "dia": None,
        "at": None,
        "reset_at": None,
        "foto_at": None,
        "ff_at": None,
        "ff_at_por_equipo": {},
        "ff_jornada": None,
        "ff_cache": None,
        "ff_errores": [],
        "ff_viejos": [],
        "ff_motivo": None,
        "campos_ff": list(CAMPOS_FF),
        "campos_ff_sin_id": list(CAMPOS_FF_SIN_ID),
        "ff": {},
        "ff_sin_id": [],
        "n_ff_leidos": 0,
        "biwenger": {},
    }

    try:
        momento = (_cuando(ahora) or datetime.now(timezone.utc))
        dia = el_dia_de_madrid(momento)
        linea["dia"] = dia.isoformat()
        linea["at"] = momento.astimezone(timezone.utc).isoformat()

        # De que reset es el estado: la cache del catalogo no sirve
        # nada guardado antes de el.
        reset = el_ultimo_reset(momento)
        linea["reset_at"] = reset.isoformat() if reset else None

        snapshot = snapshot if isinstance(snapshot, dict) else {}
        datos = ((snapshot.get("catalog") or {}).get("data") or {})
        datos = datos if isinstance(datos, dict) else {}
        catalogo = datos.get("players") or {}
        catalogo = catalogo if isinstance(catalogo, dict) else {}
        equipos = datos.get("teams") or {}
        equipos = equipos if isinstance(equipos, dict) else {}

        linea["foto_at"] = (
            str(snapshot.get("timestamp"))
            if snapshot.get("timestamp")
            else None
        )

        # EL ESTADO DE BIWENGER, de todo el catalogo.
        for clave, ficha in catalogo.items():
            if not isinstance(ficha, dict):
                continue
            pid = _int(ficha.get("id")) or _int(clave)
            if pid is None:
                continue
            linea["biwenger"][str(pid)] = ficha.get("status")

        # LA TITULARIDAD DE FF.
        tablero = tablero if isinstance(tablero, dict) else {}

        if not tablero:
            linea["ff_motivo"] = "SIN_TABLERO: no hay tablero de FF."
            return linea

        # Lo que el tablero dice de si mismo: de donde salio y que
        # paginas fallaron.
        metadata = tablero.get("metadata")
        errores = (metadata or {}).get("errors") if isinstance(metadata, dict) else None
        linea["ff_errores"] = (
            [str(e) for e in errores] if isinstance(errores, list) else []
        )
        estado_cache = tablero.get("cache")
        linea["ff_cache"] = (
            estado_cache.get("status") if isinstance(estado_cache, dict) else None
        )

        hecho = _cuando(tablero.get("updated_at"))
        linea["ff_at"] = hecho.isoformat() if hecho else None
        linea["ff_jornada"] = tablero.get("matchday")

        if hecho is None:
            linea["ff_motivo"] = "SIN_FECHA: el tablero de FF no dice cuando se bajo."
            return linea

        edad = (momento - hecho).total_seconds() / 3600

        if edad > HORAS_QUE_VALE:
            linea["ff_motivo"] = (
                f"CADUCADO: el tablero de FF es de {hecho.isoformat()} "
                f"({edad:.0f} h): no representa hoy."
            )
            return linea

        ff = linea["ff"]
        por_slug = {}
        equipo_de = {}

        for entrada in tablero.get("players") or []:
            if not isinstance(entrada, dict):
                continue
            pid = _int(entrada.get("player_id"))
            if pid is None:
                continue
            ff[str(pid)] = [
                _compacto(entrada.get("starter_probability")),
                ((entrada.get("hierarchy") or {}).get("value")),
                ((entrada.get("availability") or {}).get("code")),
            ]
            equipo_de[str(pid)] = entrada.get("team")
            slug = (entrada.get("ff") or {}).get("slug")
            if slug:
                por_slug[slug] = pid

        plantillas = tablero.get("plantillas") or {}

        if not isinstance(plantillas, dict) or not plantillas:
            linea["ff_motivo"] = (
                "SIN_PLANTILLAS: el tablero no trae las filas enteras; "
                "solo sus objetivos."
            )
            return linea

        avisos = []

        if linea["ff_errores"]:
            avisos.append(
                f"ERRORES: FF fallo en {len(linea['ff_errores'])} "
                f"pagina(s): {'; '.join(linea['ff_errores'])[:300]}."
            )

        # CADA PLANTILLA CON SU HORA. Al completar, el tablero lleva la
        # hora de ahora y arrastra de la cache las plantillas de los
        # equipos que no vuelve a bajar, cada una con su `at`. La de mas
        # de `HORAS_QUE_VALE` o de antes de este dia no es de hoy: ni
        # sus filas ni los objetivos de su equipo (tan viejos como su
        # pagina). Sin `at`, la del tablero.
        inicio = _inicio_del_dia(dia)
        viejos = set()

        for equipo, plantilla in plantillas.items():
            cuando = (
                _cuando(plantilla.get("at"))
                if isinstance(plantilla, dict) and plantilla.get("at")
                else None
            ) or hecho
            linea["ff_at_por_equipo"][str(equipo)] = cuando.isoformat()
            if (
                (momento - cuando).total_seconds() / 3600 > HORAS_QUE_VALE
                or cuando < inicio
            ):
                viejos.add(equipo)

        linea["ff_viejos"] = sorted(str(e) for e in viejos)

        for pid in [p for p, e in equipo_de.items() if e in viejos]:
            ff.pop(pid, None)

        if viejos:
            avisos.append(
                f"PLANTILLAS_VIEJAS: {', '.join(linea['ff_viejos'])} de "
                f"antes de hoy o de mas de {HORAS_QUE_VALE} h: no se "
                "guardan como de hoy."
            )

        # Un equipo con objetivos en el tablero y sin su plantilla: la
        # linea esta a medias.
        sin_plantilla = sorted(
            {str(e) for e in equipo_de.values() if e and e not in plantillas}
        )

        if sin_plantilla:
            avisos.append(
                f"PLANTILLAS_A_MEDIAS: sin la plantilla de "
                f"{', '.join(sin_plantilla)}, que tiene objetivos en el "
                "tablero."
            )

        from src.intelligence.futbolfantasy_provider import match_team

        nombre_de = {
            _int(k): (v or {}).get("name")
            for k, v in equipos.items()
            if isinstance(v, dict)
        }

        for equipo, plantilla in sorted(plantillas.items()):

            if equipo in viejos:
                continue

            filas = [
                f for f in ((plantilla or {}).get("players") or [])
                if isinstance(f, dict)
            ]
            linea["n_ff_leidos"] += len(filas)

            sueltas = []

            for fila in filas:
                pid = por_slug.get(fila.get("ff_slug"))
                if pid is not None:
                    ff[str(pid)] = [
                        _compacto(fila.get("probability")),
                        fila.get("hierarchy_value"),
                        fila.get("availability_code"),
                    ]
                else:
                    sueltas.append(fila)

            # Los del catalogo de ESE equipo que aun no tienen fila.
            objetivos = []

            for clave, ficha in catalogo.items():
                if not isinstance(ficha, dict):
                    continue
                pid = _int(ficha.get("id")) or _int(clave)
                if (
                    pid is None
                    or str(pid) in ff
                    or not ficha.get("name")
                    or nombre_de.get(_int(ficha.get("teamID"))) != equipo
                ):
                    continue
                objetivos.append(
                    {
                        "id": pid,
                        "name": ficha.get("name"),
                        "slug": ficha.get("slug"),
                        "price": _int(ficha.get("price")),
                        "team": equipo,
                        "scope": "ARCHIVO",
                    }
                )

            emparejadas = set()

            if sueltas and objetivos:
                for cruce in match_team(sueltas, objetivos):
                    fila = cruce["record"]
                    emparejadas.add(id(fila))
                    ff[str(cruce["target"]["id"])] = [
                        _compacto(fila.get("probability")),
                        fila.get("hierarchy_value"),
                        fila.get("availability_code"),
                    ]

            for fila in sueltas:
                if id(fila) in emparejadas:
                    continue
                linea["ff_sin_id"].append(
                    [
                        equipo,
                        fila.get("ff_slug"),
                        fila.get("ff_name"),
                        _compacto(fila.get("probability")),
                        fila.get("hierarchy_value"),
                        fila.get("availability_code"),
                        fila.get("ff_biwenger_value"),
                    ]
                )

        if avisos:
            linea["ff_motivo"] = " ".join(avisos)

        return linea

    except Exception as error:                      # noqa: BLE001
        linea["ff_motivo"] = (
            f"ERROR: {type(error).__name__}: {error}"
        )
        return linea


def _leer_lineas(ruta: Path) -> list | None:
    """
    `[(texto, dict o None)]` del libro. [] si no existe; None si
    existe y no se puede abrir (quien escribe, no escribe: veria un
    libro vacio). Linea a linea: un trozo con UTF-8 roto se queda
    como texto ilegible con sus mismos bytes (`surrogateescape`), sin
    tapar al resto. Nunca lanza.
    """

    try:
        if not ruta.exists():
            return []

        datos = ruta.read_bytes()

    except Exception:                               # noqa: BLE001
        return None

    salida = []

    for texto in datos.decode("utf-8", errors="surrogateescape").split("\n"):
        texto = texto.rstrip("\r")
        if not texto.strip():
            continue
        try:
            fila = json.loads(texto)
        except ValueError:
            fila = None
        salida.append((texto, fila if isinstance(fila, dict) else None))

    return salida


def _termina_a_medias(ruta: Path) -> bool:
    """¿El libro acaba sin salto de linea (una escritura cortada)?"""

    try:
        if not ruta.exists() or ruta.stat().st_size == 0:
            return False

        with ruta.open("rb") as fh:
            fh.seek(-1, os.SEEK_END)
            return fh.read(1) != b"\n"

    except Exception:                               # noqa: BLE001
        return True


def _entera(fila) -> bool:
    """
    ¿Esta linea deja el dia cerrado? Sin `ff_motivo` (ni caducado,
    ni sin plantillas, ni paginas que fallaron, ni plantillas a
    medias o viejas), con estado de Biwenger y con FF.
    """

    fila = fila if isinstance(fila, dict) else {}

    return (
        fila.get("ff_motivo") is None
        and bool(fila.get("biwenger"))
        and bool(fila.get("ff") or fila.get("ff_sin_id"))
    )


def _calidad(fila) -> tuple:
    """Para comparar dos lineas del mismo dia: entera, filas de FF y
    estado de Biwenger, por ese orden."""

    fila = fila if isinstance(fila, dict) else {}

    def cuantos(valor):
        return len(valor) if isinstance(valor, (dict, list)) else 0

    return (
        int(_entera(fila)),
        cuantos(fila.get("ff")) + cuantos(fila.get("ff_sin_id")),
        cuantos(fila.get("biwenger")),
    )


def archivar_la_titularidad(
    snapshot=None,
    tablero=None,
    ahora=None,
    ruta=None,
    dias=DIAS_QUE_SE_GUARDAN,
) -> dict:
    """
    Escribe la linea de hoy en `LIBRO_DE_LA_TITULARIDAD`, si no esta
    ya entera, y poda lo que pase de `dias`. Idempotente: con la
    linea del dia entera no toca nada; a medias, la reescribe en su
    sitio solo si la de esta vuelta es mejor (`_calidad`). Antes del
    reset de hoy no escribe: el catalogo puede ser el de ayer.

    `tablero` es el de FF; sin el, el de disco
    (`futbolfantasy_provider.BOARD_FILE`). `ahora` y `ruta` se PASAN
    en las guardias. Forma fija. Nunca lanza.
    """

    from datetime import timezone

    vacio = {
        "available": False,
        "written": False,
        "already": False,
        "replaced": False,
        "day": None,
        "ff": 0,
        "ff_sin_id": 0,
        "biwenger": 0,
        "removed": 0,
        "reason": None,
    }

    try:
        if _apagado():
            return {
                **vacio,
                "reason": f"{DISABLE_ENV} puesto: no se archiva.",
            }

        el_libro = Path(ruta or LIBRO_DE_LA_TITULARIDAD)

        momento = _cuando(ahora) or datetime.now(timezone.utc)

        dia = el_dia_de_madrid(momento)

        # EL DIA EMPIEZA EN EL RESET. Antes, el catalogo de la foto
        # puede ser el de la cache del reset de ayer.
        reset = el_ultimo_reset(momento)

        if reset is None or el_dia_de_madrid(reset) != dia:
            return {
                **vacio,
                "available": True,
                "day": dia.isoformat(),
                "reason": (
                    f"Antes del reset del {dia.isoformat()}: el estado "
                    "de Biwenger de la foto puede ser el de ayer (la "
                    "cache del catalogo es del reset anterior). Se "
                    "archiva desde la primera vuelta despues del reset."
                ),
            }

        anteriores = _leer_lineas(el_libro)

        if anteriores is None:
            return {
                **vacio,
                "day": dia.isoformat(),
                "reason": (
                    f"El libro {el_libro} existe y no se puede leer: no "
                    "se escribe (cada vuelta añadiria otra linea del "
                    "mismo dia)."
                ),
            }

        de_hoy = [
            fila for _, fila in anteriores
            if (fila or {}).get("dia") == dia.isoformat()
        ]

        guardada = max(de_hoy, key=_calidad) if de_hoy else None

        if guardada is not None and _entera(guardada):
            return {
                **vacio,
                "available": True,
                "already": True,
                "day": dia.isoformat(),
                "reason": f"La titularidad del {dia.isoformat()} ya esta.",
            }

        if tablero is None:
            from src.intelligence.futbolfantasy_provider import BOARD_FILE

            try:
                tablero = json.loads(
                    Path(BOARD_FILE).read_text(encoding="utf-8")
                )
            except Exception:                       # noqa: BLE001
                tablero = None

        linea = la_titularidad_de_hoy(snapshot, tablero, momento)

        if guardada is not None and _calidad(linea) <= _calidad(guardada):
            return {
                **vacio,
                "available": True,
                "already": True,
                "day": dia.isoformat(),
                "reason": (
                    f"La titularidad del {dia.isoformat()} ya esta, a "
                    f"medias ({guardada.get('ff_motivo')}), y la de esta "
                    "vuelta no es mejor."
                ),
            }

        if not (linea["biwenger"] or linea["ff"] or linea["ff_sin_id"]):
            return {
                **vacio,
                "available": True,
                "day": dia.isoformat(),
                "reason": (
                    "Nada que archivar: ni catalogo en la foto ni "
                    f"tablero de FF ({linea['ff_motivo']}). La vuelta "
                    "siguiente lo vuelve a intentar."
                ),
            }

        nueva = json.dumps(linea, ensure_ascii=False, separators=(",", ":"))

        # LA PODA, y la linea de hoy a medias se cambia EN SU SITIO
        # (si hubiera mas de una, se queda una). Ante la duda, no se
        # borra.
        limite = dia.toordinal() - int(dias)
        quedan = []
        podadas = 0
        puesta = False

        for texto, fila in anteriores:
            if (fila or {}).get("dia") == dia.isoformat():
                if not puesta:
                    quedan.append(nueva)
                    puesta = True
                continue
            try:
                suyo = date.fromisoformat(str((fila or {}).get("dia")))
            except ValueError:
                quedan.append(texto)
                continue
            if suyo.toordinal() >= limite:
                quedan.append(texto)
            else:
                podadas += 1

        el_libro.parent.mkdir(parents=True, exist_ok=True)

        if puesta or podadas:
            # Entero, a un temporal y cambiado de una vez: cortado a
            # medias, el libro de antes sigue en su sitio. Lo ilegible
            # vuelve con sus mismos bytes.
            temporal = el_libro.with_suffix(".jsonl.tmp")
            temporal.write_bytes(
                "".join(
                    t + "\n" for t in quedan + ([] if puesta else [nueva])
                ).encode(
                    "utf-8", errors="surrogateescape"
                )
            )
            os.replace(temporal, el_libro)

        else:
            # Detras de un salto de linea: si la ultima escritura se
            # corto, la nueva no se pega a la linea rota.
            salto = b"\n" if _termina_a_medias(el_libro) else b""
            with el_libro.open("ab") as fh:
                fh.write(salto + (nueva + "\n").encode("utf-8"))

        return {
            **vacio,
            "available": True,
            "written": True,
            "replaced": puesta,
            "day": dia.isoformat(),
            "ff": len(linea["ff"]),
            "ff_sin_id": len(linea["ff_sin_id"]),
            "biwenger": len(linea["biwenger"]),
            "removed": podadas,
            "reason": (
                f"Titularidad del {dia.isoformat()}"
                + (" (mejor que la que habia)" if puesta else "")
                + f": FF de "
                f"{len(linea['ff'])} con id y {len(linea['ff_sin_id'])} "
                f"sin emparejar (de {linea['n_ff_leidos']} filas), "
                f"estado de {len(linea['biwenger'])}."
                + (f" {linea['ff_motivo']}" if linea["ff_motivo"] else "")
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo archivar la titularidad: "
                f"{type(error).__name__}: {error}"
            ),
        }
