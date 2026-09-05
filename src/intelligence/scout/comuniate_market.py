"""
Ojeador de Comuniate: mercado fantasy de Biwenger.

    https://www.comuniate.com/mercado/fantasy

DONDE ESTAN LOS DATOS

    Tampoco en el HTML de la pagina: la tabla se carga despues
    por AJAX. Pero la propia pagina publica la direccion del
    endpoint en su codigo, asi que no hay nada que adivinar:

        /ajax/mercado/biwenger_subidas_bajadas_carga.php

    Devuelve el listado entero -142 subidas y 245 bajadas el
    05/09/2026- en un solo HTML. Una peticion.

LO QUE APORTA Y NO TIENE NADIE MAS: EL PULSO

    Las otras tres fuentes dicen lo que YA se movio. Comuniate
    dice ademas lo que la gente esta haciendo AHORA:

        Compras   % de usuarios que han pujado por el jugador en
                  las ultimas 24 horas
        Ventas    % de ligas en las que esta puesto a la venta
        Uso       % de ligas que lo tienen en plantilla

    Eso si mira hacia delante. En Biwenger el precio sube porque
    hay demanda, asi que "el 90 % esta pujando por el" es lo mas
    parecido a un pronostico que se ha encontrado en las cuatro
    webs — y ninguna de las cuatro lo llama pronostico.

    Se publica como señal aparte, con horizonte 1 y marcada como
    NO observada: es la unica de todo el ojeador que habla del
    futuro en vez del pasado.

EDUCACION

    Una peticion por refresco, y el refresco es cada seis horas.
    El endpoint es el mismo que usa el navegador de cualquiera
    que abra la pagina.
"""

from __future__ import annotations

import re

from src.intelligence.scout.common import (
    DOWN,
    UP,
    direction,
    fetch,
    safe_float,
    safe_int,
    signal,
    source_result,
)


SOURCE = "COMUNIATE"

URL = "https://www.comuniate.com/mercado/fantasy"

AJAX_URL = (
    "https://www.comuniate.com/ajax/mercado/"
    "biwenger_subidas_bajadas_carga.php"
)


# A partir de que demanda se considera que el pulso dice algo.
# Por debajo, la mayoria de los jugadores estan en el mismo
# monton y la señal no distingue a nadie de nadie.
PULSO_MINIMO = 20.0


def _euros(texto) -> int | None:
    """"1.120.000€" -> 1120000. "+250.000€" -> 250000."""

    if not texto:
        return None

    limpio = re.sub(r"[^\d\-+]", "", str(texto))

    if not limpio or limpio in ("+", "-"):
        return None

    return safe_int(limpio)


def _porcentaje(nodo) -> float | None:
    if nodo is None:
        return None

    fuerte = nodo.find("strong")

    if fuerte is None:
        return None

    return safe_float(
        str(fuerte.get_text(strip=True)).replace("%", "")
    )


def parse_market(html: str) -> list[dict]:

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    registros = []

    for ficha in soup.select("a.ficha-player"):

        try:
            nodo_nombre = ficha.select_one(".player-name")

            if nodo_nombre is None:
                continue

            nombre = nodo_nombre.get_text(strip=True)

            if not nombre:
                continue

            precio = _euros(
                ficha.select_one(".player-price").get_text(strip=True)
                if ficha.select_one(".player-price")
                else None
            )

            nodo_cambio = ficha.select_one(".player-value")

            cambio = _euros(
                nodo_cambio.get_text(strip=True)
                if nodo_cambio
                else None
            )

            # El signo va en la clase, no siempre en el texto.
            clases = set(nodo_cambio.get("class") or []) if nodo_cambio else set()

            if cambio is not None and "down" in clases and cambio > 0:
                cambio = -cambio

            escudo = ficha.select_one("img.player-team")

            equipo = escudo.get("alt") if escudo else None

            compras = _porcentaje(ficha.select_one(".pulso-compras"))
            ventas = _porcentaje(ficha.select_one(".pulso-ventas"))
            uso = _porcentaje(ficha.select_one(".pulso-uso"))

            señales = []

            if cambio is not None:

                porcentaje = (
                    round(cambio * 100.0 / precio, 3)
                    if precio
                    else None
                )

                señales.append(
                    signal(
                        SOURCE,
                        direction_=(
                            DOWN
                            if "down" in clases
                            else UP
                            if "up" in clases
                            else direction(cambio)
                        ),
                        magnitude_percent=porcentaje,
                        magnitude_eur=cambio,
                        horizon_days=1,
                        confidence=None,
                        confidence_basis=(
                            "La fuente no publica confianza."
                        ),
                        quote=(
                            f"cambio={cambio}, precio={precio}, "
                            f"compras={compras}%, ventas={ventas}%, "
                            f"uso={uso}%"
                        ),
                        observed=True,
                    )
                )

            # EL PULSO: LA UNICA SEÑAL QUE MIRA HACIA DELANTE
            #
            #     Y por eso va marcada `observed=False` y con su
            #     propio horizonte. Mezclarla con el movimiento ya
            #     ocurrido seria contar dos veces la misma cosa, y
            #     ademas contar el futuro como si fuera pasado.
            if compras is not None and ventas is not None:

                presion = compras - ventas

                if abs(presion) >= PULSO_MINIMO:

                    señales.append(
                        signal(
                            SOURCE + "_PULSO",
                            direction_=direction(presion),
                            magnitude_percent=round(presion, 2),
                            magnitude_eur=None,
                            horizon_days=1,
                            confidence=None,
                            confidence_basis=(
                                "La fuente no publica confianza; el "
                                "numero es demanda medida, no una "
                                "probabilidad."
                            ),
                            quote=(
                                f"compras={compras}% menos "
                                f"ventas={ventas}% = {presion:+.0f} "
                                f"puntos de presion, uso={uso}%"
                            ),
                            observed=False,
                        )
                    )

            if not señales:
                continue

            registros.append(
                {
                    "ff_name": nombre,
                    "ff_slug": None,

                    "team_hint": equipo,
                    "position_hint": (
                        ficha.select_one(".player-pos").get_text(strip=True)
                        if ficha.select_one(".player-pos")
                        else None
                    ),

                    "market_value": precio,

                    "demand_percent": compras,
                    "supply_percent": ventas,
                    "ownership_percent": uso,

                    "signals": señales,
                }
            )

        except Exception:                           # noqa: BLE001
            continue

    return registros


def scout(session=None, html: str | None = None) -> dict:

    if html is None:

        if session is None:
            import requests

            session = requests.Session()

        # El endpoint quiere saber de donde vienes. Es lo que
        # manda el navegador de cualquiera que abra la pagina.
        anterior = dict(getattr(session, "headers", {}) or {})

        try:
            session.headers.update(
                {
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": URL,
                }
            )

            html, error = fetch(session, AJAX_URL)

        finally:
            try:
                session.headers.clear()
                session.headers.update(anterior)
            except Exception:                       # noqa: BLE001
                pass

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
                "El endpoint contesto pero no trajo ninguna ficha "
                "de jugador: ha cambiado el HTML."
            ),
        )

    return source_result(
        SOURCE,
        ok=True,
        records=registros,
        note=(
            "Movimiento OBSERVADO mas el pulso de demanda "
            "(compras/ventas), que es la unica señal del ojeador "
            "que mira hacia delante."
        ),
    )
