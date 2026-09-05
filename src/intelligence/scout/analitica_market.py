"""
Ojeador de Analitica Fantasy: mercado de Biwenger.

    https://www.analiticafantasy.com/en/biwenger/mercado

DONDE ESTAN LOS DATOS

    No en el HTML. La pagina es una aplicacion Next.js y la tabla
    se pinta en el navegador, asi que buscar `<tr>` no devuelve
    nada: en la respuesta hay once filas y ninguna es un jugador.

    Pero el servidor manda los datos YA dentro de la respuesta,
    en los trozos de React Server Components -las llamadas a
    `self.__next_f.push(...)`- como cadenas JavaScript escapadas.
    Dentro de esas cadenas hay un objeto JSON por jugador:

        {"nickname":"Yamal", "marketValue":21170000,
         "subida":50000, "frenada":10000,
         "titularityPercent":80, "teamName":"Barcelona", ...}

    Asi que no hace falta un navegador ni una API privada: se
    desescapa la cadena y se leen los objetos. Una sola peticion,
    la misma que hace cualquiera que abra la pagina.

QUE SIGNIFICAN `subida` Y `frenada`

    `subida` es el cambio del ultimo mercado, en euros. `frenada`
    es cuanto se ha frenado ese cambio respecto al anterior: un
    jugador que subio 200.000 y ahora sube 190.000 lleva una
    frenada de -10.000.

    Las dos son OBSERVADAS. Aqui tampoco hay pronostico ni
    confianza publicada.

POR QUE `frenada` MERECE LA PENA

    Es lo que ninguna otra fuente da tan claro: la segunda
    derivada. Un jugador que sube pero cada vez menos esta a
    punto de girar, y en un mercado donde se compra para revender
    en tres dias eso importa mas que la subida de hoy.
"""

from __future__ import annotations

import json
import re

from src.intelligence.scout.common import (
    direction,
    fetch,
    safe_int,
    signal,
    source_result,
)


SOURCE = "ANALITICA"

URL = "https://www.analiticafantasy.com/en/biwenger/mercado"


# El principio de un objeto de jugador dentro del payload.
INICIO_JUGADOR = '{"nickname":'


def _cadenas_del_payload(html: str) -> list[str]:
    """
    Las cadenas JavaScript que Next.js empuja con los datos.

    Se desescapan con `json.loads`, que es lo unico que trata
    bien los acentos: `unicode_escape` convertia "Pablo Garcia"
    en "Pablo GarcÃ­a" y luego el emparejamiento por nombre
    fallaba por un motivo que no tenia nada que ver con el
    emparejamiento.
    """

    salida = []

    for bruto in re.findall(
        r'self\.__next_f\.push\(\[\d+,\s*("(?:[^"\\]|\\.)*")\s*\]\)',
        html,
    ):
        try:
            salida.append(json.loads(bruto))

        except (ValueError, TypeError):
            continue

    return salida


def _objetos_jugador(texto: str) -> list[dict]:
    """
    Los objetos de jugador que haya en esta cadena.

    Se recorre contando llaves en vez de con una expresion
    regular: los objetos llevan otros dentro -`currentSeason`,
    `lastSeason`- y una regular se queda corta o se pasa de largo
    segun el jugador. Contando llaves siempre se corta donde toca.
    """

    encontrados = []

    inicio = texto.find(INICIO_JUGADOR)

    while inicio != -1:

        profundidad = 0
        dentro_de_texto = False
        escapado = False

        for posicion in range(inicio, len(texto)):

            caracter = texto[posicion]

            if escapado:
                escapado = False
                continue

            if caracter == "\\":
                escapado = True
                continue

            if caracter == '"':
                dentro_de_texto = not dentro_de_texto
                continue

            if dentro_de_texto:
                continue

            if caracter == "{":
                profundidad += 1

            elif caracter == "}":
                profundidad -= 1

                if profundidad == 0:
                    try:
                        encontrados.append(
                            json.loads(texto[inicio: posicion + 1])
                        )
                    except (ValueError, TypeError):
                        pass
                    break

        inicio = texto.find(INICIO_JUGADOR, inicio + 1)

    return encontrados


def parse_market(html: str) -> list[dict]:

    vistos = set()
    registros = []

    for cadena in _cadenas_del_payload(html):

        if INICIO_JUGADOR not in cadena:
            continue

        for jugador in _objetos_jugador(cadena):

            nombre = str(jugador.get("nickname") or "").strip()

            if not nombre:
                continue

            # El mismo jugador puede venir en varios trozos.
            clave = jugador.get("masterPlayerId") or nombre

            if clave in vistos:
                continue

            vistos.add(clave)

            valor = safe_int(jugador.get("marketValue"))
            subida = jugador.get("subida")
            frenada = jugador.get("frenada")

            if subida is None:
                continue

            porcentaje = (
                round(safe_int(subida) * 100.0 / valor, 3)
                if valor
                else None
            )

            señales = [
                signal(
                    SOURCE,
                    direction_=direction(subida),
                    magnitude_percent=porcentaje,
                    magnitude_eur=subida,
                    horizon_days=1,
                    confidence=None,
                    confidence_basis=(
                        "La fuente no publica confianza."
                    ),
                    quote=(
                        f"subida={subida}, frenada={frenada}, "
                        f"marketValue={valor}, "
                        f"titularityPercent="
                        f"{jugador.get('titularityPercent')}"
                    ),
                    observed=True,
                )
            ]

            registros.append(
                {
                    "ff_name": nombre,
                    "ff_slug": jugador.get("slug"),

                    "source_player_id": jugador.get("masterPlayerId"),
                    "team_hint": jugador.get("teamName"),
                    "position_hint": jugador.get("positionId"),

                    "market_value": valor,

                    # La segunda derivada, que no da nadie mas.
                    "deceleration": safe_int(frenada),
                    "starter_percent": jugador.get(
                        "titularityPercent"
                    ),

                    "signals": señales,
                }
            )

    return registros


def scout(session=None, html: str | None = None) -> dict:

    if html is None:

        if session is None:
            import requests

            session = requests.Session()

        html, error = fetch(session, URL)

        if error:
            return source_result(SOURCE, ok=False, error=error)

    try:
        registros = parse_market(html)

    except Exception as error:                      # noqa: BLE001
        return source_result(
            SOURCE,
            ok=False,
            error=f"parser: {type(error).__name__}: {error}",
        )

    if not registros:
        return source_result(
            SOURCE,
            ok=False,
            error=(
                "No se encontro ningun objeto de jugador en los "
                "trozos de React: la pagina ha cambiado de forma."
            ),
        )

    return source_result(
        SOURCE,
        ok=True,
        records=registros,
        note=(
            "Movimiento OBSERVADO (`subida`) mas la segunda "
            "derivada (`frenada`). La fuente no publica confianza."
        ),
    )
