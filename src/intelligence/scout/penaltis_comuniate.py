"""
Quien tira los penaltis, leido de Comuniate.

LA REGLA 2, QUE ERA EL TRUCO Nº 1 DEL VIDEO Y SEGUIA APAGADA

    "Estos jugadores te pueden salvar de hacer un -2 (...) con el
     penalti, con el gol, hacerte nueve puntos. Estamos hablando
     de un -2 a nueve puntos."

    El modulo `penalty_intelligence.py` existe desde agosto con
    sus bonos escritos, y cuelga de API-Football, que en el plan
    gratuito rompe la cadena por los dos extremos. Lleva un mes
    dormido con su guardia.

    Aqui no se enciende ese: se abre una via nueva desde una web
    que ya visitamos.

LO QUE SE ENCONTRO, Y LO QUE NO (22/09/2026)

    De las tres fuentes que ya leemos cada ciclo:

        Comuniate            /lanzadores/penaltis   -> HTTP 200
        Comuniate            /lanzadores/faltas     -> HTTP 404
        Comuniate            /lanzadores/corners    -> HTTP 404
        Analitica Fantasy    estadisticas           -> HTTP 404
        FutbolFantasy        estadisticas           -> 200, pero son
                                                      penaltis MARCADOS,
                                                      no quien los tira

    Asi que **hay penaltis y no hay faltas ni corners**. El
    encargo pedia decirlo si no se podia, y no se puede: no se
    inventan con una lista escrita a mano.

COMO VIENE EL DATO

    Una tarjeta por equipo y, debajo, sus lanzadores en orden. La
    tarjeta del equipo va ANTES que sus jugadores, que es donde
    tropezo el primer intento: cortando por jugador, cada uno se
    quedaba con el equipo del siguiente y salia "Lucas Boye,
    Athletic" cuando Boye es del Alaves.

    De cada lanzador se saca: nombre, id de Comuniate, penaltis
    lanzados, penaltis anotados y su ORDEN dentro del equipo, que
    es la señal de quien es el primero.

NO DECIDE NADA AQUI

    Esto lee y devuelve filas. Quien las convierte en bono es
    `src/analysis/balon_parado.py`, y ese bono esta marcado como
    DECRETADO mientras no haya muestra para medirlo.
"""

from __future__ import annotations

import re

from datetime import datetime


URL = "https://www.comuniate.com/lanzadores/penaltis"

FUENTE = "COMUNIATE"


# Lo que Comuniate NO publica, comprobado el 22/09/2026. Se deja
# escrito para que nadie lo vuelva a buscar a ciegas.
SIN_FUENTE = ("faltas", "corners")


def _texto(valor) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def _vacio(motivo: str) -> dict:
    return {
        "available": False,
        "source": FUENTE,
        "url": URL,
        "fetched_at": None,
        "rows": [],
        "teams": 0,
        "missing": list(SIN_FUENTE),
        "reason": motivo,
    }


def parse(html: str | None) -> dict:
    """
    Los lanzadores de penaltis de la pagina.

    Nunca lanza. Forma fija.
    """

    try:
        if not html or len(html) < 500:
            return _vacio(
                "La pagina de lanzadores vino vacia o demasiado "
                "corta para ser la buena."
            )

        # EL ORDEN DEL DOCUMENTO ES LA CLAVE
        #
        #     La tarjeta del equipo precede a sus lanzadores. Se
        #     recorren los dos tipos de evento por posicion y se
        #     arrastra el equipo vigente.
        eventos = []

        for m in re.finditer(
            r'comu-team-mini__name">([^<]+)<', html
        ):
            eventos.append((m.start(), "EQUIPO", _texto(m.group(1))))

        patron_jugador = re.compile(
            r'font-size:20px; font-weight:bold;">\s*'
            r'<a href="[^"]*jugadores/(\d+)/[^"]*"[^>]*>'
            r"([^<]+)</a>"
        )

        for m in patron_jugador.finditer(html):

            cola = html[m.end():m.end() + 400]

            lanzados = re.search(
                r"Penaltis lanzados:\s*<strong>(\d+)", cola
            )
            anotados = re.search(
                r"Penaltis anotados:\s*<strong>(\d+)", cola
            )

            eventos.append((
                m.start(),
                "JUGADOR",
                {
                    "source_id": m.group(1),
                    "name": _texto(m.group(2)),
                    "taken": (
                        int(lanzados.group(1))
                        if lanzados
                        else None
                    ),
                    "scored": (
                        int(anotados.group(1))
                        if anotados
                        else None
                    ),
                },
            ))

        eventos.sort(key=lambda e: e[0])

        filas = []
        equipo = None
        orden = 0

        for _, tipo, dato in eventos:

            if tipo == "EQUIPO":
                equipo = dato
                orden = 0
                continue

            if equipo is None:
                # Un lanzador antes de cualquier equipo no se
                # puede atribuir. No se adivina.
                continue

            orden += 1

            filas.append({
                **dato,
                "team": equipo,

                # 1 = el primero que lista Comuniate para ese
                # equipo. Es la señal de quien es el titular del
                # punto de penalti.
                "order": orden,
            })

        if not filas:
            return _vacio(
                "La pagina llego pero no se reconocio ni un "
                "lanzador: la estructura ha cambiado."
            )

        equipos = len({f["team"] for f in filas})

        return {
            "available": True,
            "source": FUENTE,
            "url": URL,
            "fetched_at": datetime.now().isoformat(),
            "rows": filas,
            "teams": equipos,
            "missing": list(SIN_FUENTE),
            "reason": (
                f"{len(filas)} lanzadores de penaltis en "
                f"{equipos} equipos. Faltas y corners no los "
                f"publica esta fuente."
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo leer la pagina: "
            f"{type(error).__name__}: {error}"
        )


def fetch(session=None, timeout: int = 20) -> dict:
    """
    Pide la pagina y la parsea.

    Se separa de `parse` a proposito: la guardia prueba el parseo
    con un fixture y no toca la red.
    """

    try:
        import requests

        cliente = session or requests

        respuesta = cliente.get(
            URL,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        if getattr(respuesta, "status_code", 0) != 200:
            return _vacio(
                f"La fuente respondio "
                f"{getattr(respuesta, 'status_code', '?')}."
            )

        return parse(respuesta.text)

    except Exception as error:                       # noqa: BLE001
        return _vacio(
            f"No se pudo pedir la pagina: "
            f"{type(error).__name__}: {error}"
        )
