"""
Cuanto tiempo va a estar fuera. No solo si hoy juega.

POR QUE ESTE MODULO EXISTE

    Con solo el % de titularidad, una gripe y una rotura de cruzado
    son el mismo dato: 0 %. Y no lo son.

    Al pasar la valoracion a base estructural (17/08/2026) el
    agujero se volvio caro: un Clave lesionado paso de valer el
    15 % de sus puntos al 64 %, porque la jerarquia dice "es un
    Clave" y nadie contaba las jornadas que se pierde. Con eso,
    Yamal con el cruzado roto seguiria valorandose casi como Yamal
    sano.

    FF publica dos paginas que cubren la liga entera:

        /laliga/lesionados    tipo de lesion, desde cuando, y un
                              pronostico -"Baja hasta enero 2027",
                              "Duda para la jornada 2"- con una
                              clase de gravedad al lado.

        /laliga/sancionados   "Roja directa (2/2)", "Sancion
                              disciplinaria (2/3)": partidos
                              cumplidos sobre el total.

LA IDENTIDAD AQUI ES GRATIS

    Estas paginas usan el MISMO slug que las de equipo
    (`/jugadores/unai-egiluz` frente a `data-nombre="unai-egiluz"`).
    Misma fuente, misma clave: se cruza por igualdad exacta, sin
    parecidos de nombre ni margenes.

LO QUE NO HACE

    No decide vender. Saber que a un Clave le quedan seis semanas
    es un dato; que hacer con el es una politica de plantilla y se
    decide en otro sitio. Aqui solo se mide la ausencia.
"""

from __future__ import annotations

import re
import unicodedata

from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


FF_BASE = "https://www.futbolfantasy.com"

INJURIES_URL = f"{FF_BASE}/laliga/lesionados"
SUSPENSIONS_URL = f"{FF_BASE}/laliga/sancionados"

CALENDAR_FILE = Path("data/calendar/laliga_calendar.json")


# La clase `gravedad-N` que FF pone al pronostico. Medido sobre
# los 64 partes del 17/08/2026: 28 bajas, 22 dudas, 14 disponibles.
SEVERITY = {
    0: "BAJA",
    1: "DUDA",
    2: "DISPONIBLE",
}


MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# "principios / mediados / finales de agosto". Sin matiz, mitad de
# mes: es el error mas pequeño posible cuando no se dice.
DIA_DEL_MES = {
    "principio": 5,
    "principios": 5,
    "mediados": 15,
    "finales": 25,
    "final": 25,
}


def normalize(value) -> str:

    value = str(value or "").strip().lower()

    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def _slug_from_href(href: str) -> str | None:

    if not href:
        return None

    trozo = str(href).rstrip("/").split("/")[-1]

    return trozo or None


# ----------------------------------------------------------------
# CALENDARIO: de una fecha a una jornada
# ----------------------------------------------------------------


def matchday_dates(calendar: dict) -> dict[int, datetime]:
    """
    Primer partido de cada jornada.

    Con esto una fecha se convierte en jornada, que es la unidad en
    la que se piensa una ausencia: no "45 dias", sino "se pierde
    seis jornadas".
    """

    fechas: dict[int, datetime] = {}

    for jornada in ((calendar or {}).get("matchdays") or []):

        numero = jornada.get("matchday")

        if numero is None:
            continue

        arranques = []

        for partido in (jornada.get("matches") or []):

            crudo = partido.get("kickoff")

            if not crudo:
                continue

            try:
                arranques.append(
                    datetime.fromisoformat(
                        str(crudo).replace("Z", "+00:00")
                    )
                )
            except ValueError:
                continue

        if arranques:
            fechas[int(numero)] = min(arranques)

    return fechas


def matchday_on_or_after(
    fechas: dict[int, datetime],
    momento: datetime,
) -> int | None:
    """
    La primera jornada que se juega en o despues de esa fecha.
    """

    candidatas = [
        numero
        for numero, cuando in sorted(fechas.items())
        if cuando >= momento
    ]

    return candidatas[0] if candidatas else None


# ----------------------------------------------------------------
# EL PRONOSTICO, EN JORNADAS
# ----------------------------------------------------------------


def parse_prognosis(
    texto: str,
    *,
    current_matchday: int,
    fechas: dict[int, datetime],
    today: datetime,
) -> dict:
    """
    "Baja hasta enero 2027" -> jornada de vuelta y cuantas se pierde.

    Devuelve siempre `basis`, que dice de que calidad es la
    estimacion:

        JORNADA   FF nombro la jornada. Es exacto.
        FECHA     FF dio un mes; se traduce con el calendario.
                  Aproximado y se dice.
        NINGUNA   no se ha entendido el texto. No se inventa un
                  numero: se devuelve None.
    """

    limpio = normalize(texto)

    resultado = {
        "text": texto,
        "return_matchday": None,
        "matchdays_out": None,
        "basis": "NINGUNA",
    }

    if not limpio:
        return resultado

    # ------------------------------------------------
    # "Baja indefinida"
    #
    # FF admite que no lo sabe. Es el caso peligroso: sin horizonte
    # no habria penalizacion ninguna, y "indefinida" detras de una
    # rotura de menisco son meses, no una semana.
    #
    # No se inventa aqui un numero de jornadas: se marca, y quien
    # valore decide con que prudencia trata lo desconocido. Pero se
    # marca DISTINTO de "no lo he entendido".
    # ------------------------------------------------

    if "indefinid" in limpio:
        resultado["basis"] = "INDEFINIDA"
        return resultado

    # ------------------------------------------------
    # "... para la jornada N"
    # ------------------------------------------------

    jornada = re.search(r"jornada (\d+)", limpio)

    if jornada:

        numero = int(jornada.group(1))

        resultado["basis"] = "JORNADA"

        if limpio.startswith("disponible"):
            resultado["return_matchday"] = numero
            resultado["matchdays_out"] = 0

        elif limpio.startswith("duda"):
            # Duda no es baja. Que lo resuelva el % de la jornada.
            resultado["return_matchday"] = numero
            resultado["matchdays_out"] = 0

        else:
            # "Baja confirmada para la jornada N": se pierde esa y
            # vuelve en la siguiente.
            resultado["return_matchday"] = numero + 1
            resultado["matchdays_out"] = max(
                0,
                numero + 1 - current_matchday,
            )

        return resultado

    # ------------------------------------------------
    # "... hasta [principios/mediados/finales de] MES [AÑO]"
    # ------------------------------------------------

    mes = None
    matiz = None
    anio = None

    # FF escribe horquillas: "Baja hasta octubre-noviembre". Se
    # coge el mes MAS TARDIO, no el primero que aparezca.
    #
    # Quedarse con octubre acorta la baja, y acortar una baja
    # infla el valor del jugador. Ante una horquilla, el lado
    # prudente es el largo.
    encontrados = []

    for palabra, numero in MESES.items():

        posicion = limpio.find(palabra)

        if posicion >= 0:
            encontrados.append((posicion, numero))

    if encontrados:
        mes = max(encontrados, key=lambda par: par[0])[1]

    if mes is None:
        return resultado

    for palabra, dia in DIA_DEL_MES.items():
        if re.search(rf"\b{palabra}\b", limpio):
            matiz = dia
            break

    anio_texto = re.search(r"\b(20\d{2})\b", limpio)

    if anio_texto:
        anio = int(anio_texto.group(1))

    else:
        # Sin año: la proxima vez que llegue ese mes.
        anio = today.year if mes >= today.month else today.year + 1

    objetivo = datetime(
        anio,
        mes,
        matiz or 15,
        tzinfo=timezone.utc,
    )

    vuelta = matchday_on_or_after(fechas, objetivo)

    if vuelta is None:
        # Mas alla del final de la temporada: se pierde lo que
        # queda.
        resultado["basis"] = "FECHA"
        resultado["return_matchday"] = None
        resultado["matchdays_out"] = max(
            0,
            (max(fechas) if fechas else current_matchday)
            - current_matchday
            + 1,
        )
        return resultado

    resultado["basis"] = "FECHA"
    resultado["return_matchday"] = vuelta
    resultado["matchdays_out"] = max(0, vuelta - current_matchday)

    return resultado


# ----------------------------------------------------------------
# LOS PARSERS
# ----------------------------------------------------------------


def parse_injuries(
    html: str,
    *,
    current_matchday: int,
    fechas: dict[int, datetime],
    today: datetime,
) -> dict[str, dict]:

    soup = BeautifulSoup(html, "html.parser")

    partes: dict[str, dict] = {}

    for fila in soup.select("div.elemento.lesionado"):

        enlace = fila.select_one("a.jugador")

        if enlace is None:
            continue

        slug = _slug_from_href(enlace.get("href"))

        if not slug:
            continue

        tipo = fila.select_one(".comentario span.lesion")

        pronostico_el = fila.select_one(
            ".comentario span[class^=gravedad]"
        )

        gravedad = None

        if pronostico_el is not None:

            for clase in (pronostico_el.get("class") or []):

                encontrado = re.fullmatch(r"gravedad-(\d+)", clase)

                if encontrado:
                    gravedad = int(encontrado.group(1))
                    break

        desde = None
        dias = None

        for span in fila.select(".comentario span"):

            texto = span.get_text(" ", strip=True)

            encontrado = re.search(
                r"Desde\s+(\d{1,2}/\d{1,2})\s*\((\d+)\s*d",
                texto,
            )

            if encontrado:
                desde = encontrado.group(1)
                dias = int(encontrado.group(2))
                break

        pronostico = parse_prognosis(
            pronostico_el.get_text(" ", strip=True)
            if pronostico_el is not None
            else "",
            current_matchday=current_matchday,
            fechas=fechas,
            today=today,
        )

        partes[slug] = {
            "type": "INJURY",
            "detail": (
                tipo.get_text(" ", strip=True)
                if tipo is not None
                else None
            ),
            "since": desde,
            "days_out": dias,
            "severity": gravedad,
            "severity_label": SEVERITY.get(gravedad),
            "prognosis": pronostico["text"],
            "return_matchday": pronostico["return_matchday"],
            "matchdays_out": pronostico["matchdays_out"],
            "basis": pronostico["basis"],
        }

    return partes


def parse_suspensions(html: str) -> dict[str, dict]:
    """
    "Roja directa (2/2)" -> cumplidos 2 de 2, o sea ninguno queda.

    Sin parentesis se asume un partido, que es lo que dura una roja
    directa simple. Es la suposicion mas barata y la unica que hay.
    """

    soup = BeautifulSoup(html, "html.parser")

    partes: dict[str, dict] = {}

    for fila in soup.select("div.elemento.sancionado"):

        enlace = fila.select_one("a.jugador")

        if enlace is None:
            continue

        slug = _slug_from_href(enlace.get("href"))

        if not slug:
            continue

        detalle_el = fila.select_one("span.sancion")

        detalle = (
            detalle_el.get_text(" ", strip=True)
            if detalle_el is not None
            else ""
        )

        cuenta = re.search(r"\((\d+)\s*/\s*(\d+)\)", detalle)

        if cuenta:
            cumplidos = int(cuenta.group(1))
            totales = int(cuenta.group(2))
            pendientes = max(0, totales - cumplidos)

        else:
            cumplidos = None
            totales = None
            pendientes = 1

        partes[slug] = {
            "type": "SUSPENSION",
            "detail": detalle,
            "matches_served": cumplidos,
            "matches_total": totales,
            "matchdays_out": pendientes,
            "basis": "JORNADA" if cuenta else "SUPUESTO",
        }

    return partes


# ----------------------------------------------------------------
# LA COMBINACION
# ----------------------------------------------------------------


def merge_absences(
    injuries: dict[str, dict],
    suspensions: dict[str, dict],
) -> dict[str, dict]:
    """
    Un jugador puede estar lesionado Y sancionado -FF tiene un
    estado 150 justo para eso-. Manda la ausencia mas larga.

    LAS DOS FICHAS SE GUARDAN ENTERAS (19/08/2026)

        Antes solo sobrevivia la ausencia mas larga, y de la otra
        quedaba `also` con el tipo a secas. O sea, de un jugador
        con el ligamento roto y ademas dos partidos de sancion se
        conservaba "SUSPENSION" y se perdia si era roja directa,
        acumulacion o cuantos partidos quedaban.

        Y son dos cosas distintas para decidir: una lesion larga
        es motivo de venta, y una sancion de dos partidos no lo
        es. Fundirlas en un campo obligaba a tratarlas igual.

        `injury` y `suspension` viajan ahora completas al lado de
        la que manda. Quien solo quiera saber cuanto falta sigue
        leyendo `matchdays_out` como siempre.
    """

    todas: dict[str, dict] = {}

    for origen in (injuries, suspensions):

        for slug, parte in origen.items():

            actual = todas.get(slug)

            if actual is None:
                combinada = dict(parte)

            else:
                fuera_actual = actual.get("matchdays_out") or 0
                fuera_nueva = parte.get("matchdays_out") or 0

                if fuera_nueva > fuera_actual:
                    combinada = dict(parte)
                else:
                    combinada = dict(actual)

                combinada["also"] = (
                    parte["type"]
                    if combinada["type"] != parte["type"]
                    else combinada.get("also")
                )

            # Cada ficha en su sitio, pase lo que pase con cual
            # manda. Se copia para que nadie de fuera pueda
            # cambiar la original sin querer.
            if parte.get("type") == "INJURY":
                combinada["injury"] = dict(parte)

            elif parte.get("type") == "SUSPENSION":
                combinada["suspension"] = dict(parte)

            if actual is not None:
                for clave in ("injury", "suspension"):
                    if clave not in combinada and clave in actual:
                        combinada[clave] = actual[clave]

            todas[slug] = combinada

    return todas
