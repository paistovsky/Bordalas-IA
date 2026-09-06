"""
Quien tira los penaltis, y cuanto vale saberlo.

LA REGLA 2: EL TRUCO Nº 1 DEL VIDEO, APAGADO DESDE AGOSTO

    "Con el penalti, con el gol, hacerte nueve puntos. Estamos
     hablando de un -2 a nueve puntos."

    `penalty_intelligence.py` lleva un mes dormido colgando de
    API-Football. **No se enciende**: se abre una via nueva desde
    Comuniate, que ya visitamos.

LO QUE SE PUEDE SABER Y LO QUE NO (22/09/2026)

    Penaltis: si. Veinte equipos, veinte lanzadores designados,
    con cuantos han lanzado y cuantos han anotado.

    Faltas y corners: NO. Comuniate solo publica penaltis
    -`/lanzadores/faltas` y `/lanzadores/corners` dan 404-,
    Analitica no tiene esa pagina y FutbolFantasy publica
    penaltis MARCADOS, que es historico, no designacion.

    El encargo pedia decirlo en vez de inventarlo con una lista
    escrita a mano. Dicho.

# ============================================================
# Y AHORA LO INCOMODO: EL BONO NO SOBREVIVE A LA MEDICION
# ============================================================

    El encargo mandaba medir los 8,0 y 3,0 decretados contra los
    puntos reales antes de darlos por buenos. Medido sobre los 22
    lanzadores que se pudieron emparejar con el catalogo:

        lanzadores de penaltis        5,73 puntos por partido
        delanteros que NO lanzan      3,68
        todos los que no lanzan       3,52
        ------------------------------------------
        diferencia                   +2,21

    Parece enorme. Y es casi todo un espejismo, porque el
    lanzador de penaltis ES, por seleccion, el mejor atacante de
    su equipo. Comparando a cada lanzador con el MEJOR delantero
    de su propio equipo que no lanza:

        n = 18     media -0,25     mediana -1,29

    Es decir: **una vez descontado "ser el mejor de tu equipo",
    lanzar penaltis no añade nada medible** con tres jornadas.

    Y hay una segunda razon, independiente de la muestra: la
    calidad medida son PUNTOS POR PARTIDO, y los puntos de un
    penalti marcado ya estan dentro. Sumar un bono encima seria
    contar el mismo gol dos veces, que es el error que este
    proyecto lleva un mes aprendiendo a no cometer.

    Por eso el bono se publica **DECRETADO y sin aplicar**. La
    señal -quien tira- se publica igual, porque es informacion
    util que no teniamos; lo que no se hace es meterla en la vara
    sin numero que la sostenga (regla 18).

    Si en tres jornadas el libro de acierto dice otra cosa, se
    enciende. Para eso esta el libro.
"""

from __future__ import annotations

import re
import statistics
import unicodedata


# Los bonos que `penalty_intelligence` tiene escritos desde
# agosto. Se citan para poder decir que NO se aplican, y en que
# escala estaban: la suya, no la de la vara.
BONO_DECRETADO_PRIMERO = 8.0
BONO_DECRETADO_SEGUNDO = 3.0


# Lo que de verdad se aplica hoy. Cero, y con motivo escrito.
BONO_APLICADO = 0.0


# Con menos de esto no hay medicion que sostenga un bono.
MUESTRA_MINIMA = 30


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def normalizar(nombre) -> str:
    """
    Un nombre comparable entre Comuniate y Biwenger.

    Sin tildes, sin puntuacion, en minusculas. Es lo mismo que
    hace el emparejador del ojeador, y por el mismo motivo: los
    acentos y los guiones no son informacion.
    """

    texto = unicodedata.normalize(
        "NFKD", str(nombre or "")
    ).encode("ascii", "ignore").decode()

    return re.sub(r"[^a-z ]", "", texto.lower()).strip()


def emparejar(filas, catalogo) -> dict:
    """
    Los lanzadores, con su id de Biwenger cuando se puede.

    Nunca lanza. Forma fija.

    LO QUE NO SE EMPAREJA SE DICE, NO SE ADIVINA. Un nombre que
    casa con dos jugadores distintos se queda fuera: meter el
    bono en el jugador equivocado es peor que no meterlo.
    """

    vacio = {
        "available": False,
        "rows": [],
        "matched": 0,
        "unmatched": [],
        "reason": None,
    }

    try:
        jugadores = (catalogo or {}).values() if isinstance(
            catalogo, dict
        ) else (catalogo or [])

        por_nombre = {}

        for jugador in jugadores:

            if not isinstance(jugador, dict):
                continue

            por_nombre.setdefault(
                normalizar(jugador.get("name")), []
            ).append(jugador)

        if not por_nombre:
            return {
                **vacio,
                "reason": (
                    "Sin catalogo con el que emparejar los "
                    "nombres."
                ),
            }

        casados = []
        sueltos = []

        for fila in (filas or []):

            nombre = normalizar(fila.get("name"))

            candidatos = por_nombre.get(nombre)

            if not candidatos:
                # Segundo intento: por apellido, que es como
                # Comuniate nombra a la mitad.
                apellido = nombre.split()[-1] if nombre else ""

                candidatos = [
                    jugador
                    for clave, lista in por_nombre.items()
                    for jugador in lista
                    if clave.split()[-1] == apellido
                ] if apellido else []

            if len(candidatos) != 1:
                sueltos.append({
                    "name": fila.get("name"),
                    "team": fila.get("team"),
                    "candidates": len(candidatos or []),
                })
                continue

            jugador = candidatos[0]

            casados.append({
                **fila,
                "player_id": safe_int(jugador.get("id")),
                "biwenger_name": jugador.get("name"),
            })

        return {
            "available": bool(casados),
            "rows": casados,
            "matched": len(casados),
            "unmatched": sueltos,
            "reason": (
                f"{len(casados)} de "
                f"{len(casados) + len(sueltos)} lanzadores "
                f"emparejados con el catalogo."
                + (
                    " Sin emparejar: "
                    + ", ".join(
                        str(s["name"]) for s in sueltos
                    )
                    + "."
                    if sueltos
                    else ""
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo emparejar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _por_partido(jugador: dict):
    partidos = (
        safe_int(jugador.get("playedHome"))
        + safe_int(jugador.get("playedAway"))
    ) or (
        safe_int(jugador.get("played_home"))
        + safe_int(jugador.get("played_away"))
    )

    if partidos <= 0:
        return None

    return safe_int(jugador.get("points")) / partidos


def medir_el_bono(lanzadores, catalogo) -> dict:
    """
    ¿Rinde mas un lanzador de penaltis? Y sobre todo: ¿rinde mas
    QUE EL MEJOR DE SU PROPIO EQUIPO?

    La segunda es la que importa. La primera mide "ser el mejor
    atacante de tu equipo", que ya lo sabiamos.

    Nunca lanza. Forma fija.
    """

    vacio = {
        "available": False,
        "takers": 0,
        "takers_points_per_match": None,
        "others_points_per_match": None,
        "raw_gap": None,
        "within_team_n": 0,
        "within_team_mean": None,
        "within_team_median": None,
        "supports_bonus": None,
        "minimum_sample": MUESTRA_MINIMA,
        "reason": None,
    }

    try:
        jugadores = [
            j
            for j in (
                (catalogo or {}).values()
                if isinstance(catalogo, dict)
                else (catalogo or [])
            )
            if isinstance(j, dict)
        ]

        ids = {
            safe_int(f.get("player_id"))
            for f in (lanzadores or [])
            if safe_int(f.get("player_id"))
        }

        if not ids or not jugadores:
            return {
                **vacio,
                "reason": (
                    "Sin lanzadores emparejados o sin catalogo: "
                    "no se puede medir el bono."
                ),
            }

        suyos = [
            _por_partido(j)
            for j in jugadores
            if safe_int(j.get("id")) in ids
        ]
        suyos = [v for v in suyos if v is not None]

        otros = [
            _por_partido(j)
            for j in jugadores
            if safe_int(j.get("id")) not in ids
        ]
        otros = [v for v in otros if v is not None]

        if not suyos or not otros:
            return {**vacio, "reason": "Sin muestra comparable."}

        # LA COMPARACION QUE DE VERDAD AISLA EL EFECTO
        #
        #     Cada lanzador contra el MEJOR delantero de su propio
        #     equipo que no lanza. Sin esto se mide "ser el mejor
        #     atacante", que no es lo que el bono pretende pagar.
        diferencias = []

        for fila in (lanzadores or []):

            if safe_int(fila.get("order")) != 1:
                continue

            jugador = next(
                (
                    j
                    for j in jugadores
                    if safe_int(j.get("id"))
                    == safe_int(fila.get("player_id"))
                ),
                None,
            )

            if not jugador:
                continue

            mio = _por_partido(jugador)

            if mio is None:
                continue

            rivales = [
                _por_partido(j)
                for j in jugadores
                if safe_int(j.get("teamID"))
                == safe_int(jugador.get("teamID"))
                and safe_int(j.get("id")) not in ids
                and safe_int(j.get("position")) == 4
            ]

            rivales = [v for v in rivales if v is not None]

            if not rivales:
                continue

            diferencias.append(mio - max(rivales))

        dentro_media = (
            statistics.fmean(diferencias)
            if diferencias
            else None
        )

        # El bono solo se sostiene si el efecto DENTRO del equipo
        # es positivo Y hay muestra. Hoy no se cumple ninguna.
        apoya = bool(
            diferencias
            and len(diferencias) >= MUESTRA_MINIMA
            and dentro_media
            and dentro_media > 0
        )

        return {
            "available": True,
            "takers": len(suyos),
            "takers_points_per_match": round(
                statistics.fmean(suyos), 2
            ),
            "others_points_per_match": round(
                statistics.fmean(otros), 2
            ),
            "raw_gap": round(
                statistics.fmean(suyos)
                - statistics.fmean(otros),
                2,
            ),
            "within_team_n": len(diferencias),
            "within_team_mean": (
                round(dentro_media, 2)
                if dentro_media is not None
                else None
            ),
            "within_team_median": (
                round(statistics.median(diferencias), 2)
                if diferencias
                else None
            ),
            "supports_bonus": apoya,
            "minimum_sample": MUESTRA_MINIMA,
            "reason": _reason_medicion(
                suyos, otros, diferencias, dentro_media, apoya
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo medir: "
                f"{type(error).__name__}: {error}"
            ),
        }


def _reason_medicion(suyos, otros, dentro, media, apoya) -> str:

    bruto = statistics.fmean(suyos) - statistics.fmean(otros)

    frase = (
        f"Los lanzadores hacen "
        f"{statistics.fmean(suyos):.2f} puntos por partido y el "
        f"resto {statistics.fmean(otros):.2f}: "
        f"{bruto:+.2f} de diferencia bruta."
    )

    if not dentro:
        return frase + (
            " No hay con que compararlos dentro de su propio "
            "equipo, asi que no se puede separar el efecto del "
            "penalti de el de ser el mejor atacante."
        )

    frase += (
        f" Pero contra el MEJOR delantero de su propio equipo que "
        f"no lanza, la diferencia es {media:+.2f} "
        f"(mediana {statistics.median(dentro):+.2f}, n="
        f"{len(dentro)}): el hueco bruto era casi todo el sesgo "
        f"de seleccion."
    )

    if apoya:
        return frase + " El bono se sostiene."

    return frase + (
        f" Con n={len(dentro)} y ese signo, el bono NO se "
        f"sostiene: se publica la señal y el bono queda "
        f"DECRETADO y sin aplicar. Ademas, los puntos de un "
        f"penalti marcado ya estan dentro de la calidad medida: "
        f"sumarlo seria contar el mismo gol dos veces."
    )


def por_euro_y_punto(lanzadores, catalogo) -> dict:
    """
    Los lanzadores ordenados por lo que cuesta cada punto suyo.

    EL MATIZ DEL VIDEO-2, MEDIDO (22/09/2026)

        "A Salah o Palmer no los vas a fichar solo por los
         penaltis, pero Kluivert metio seis de penalti la
         temporada pasada y es mucho mas barato."

        Medido aqui: ser lanzador NO es buen precio. La mediana
        de los lanzadores es 1.039.000 EUR por punto y partido, y
        la de los delanteros que no lanzan 553.333: los
        lanzadores cuestan casi el DOBLE, porque son las
        estrellas de su equipo.

        Pero dentro de los lanzadores hay 6,7 veces de diferencia
        entre el mas barato y el mas caro. Ahi si esta el valor, y
        es exactamente lo que dice el video.

    Publica. No compra. Forma fija.
    """

    vacio = {
        "available": False,
        "rows": [],
        "takers_median": None,
        "others_median": None,
        "reason": None,
    }

    try:
        jugadores = [
            j
            for j in (
                (catalogo or {}).values()
                if isinstance(catalogo, dict)
                else (catalogo or [])
            )
            if isinstance(j, dict)
        ]

        ids = {
            safe_int(f.get("player_id"))
            for f in (lanzadores or [])
            if safe_int(f.get("player_id"))
        }

        if not ids or not jugadores:
            return {
                **vacio,
                "reason": (
                    "Sin lanzadores emparejados o sin catalogo."
                ),
            }

        def euro_punto(jugador):
            rendimiento = _por_partido(jugador)

            if not rendimiento or rendimiento <= 0:
                return None

            precio = safe_int(jugador.get("price"))

            return precio / rendimiento if precio else None

        filas = []
        otros = []

        for jugador in jugadores:

            coste = euro_punto(jugador)

            if coste is None:
                continue

            if safe_int(jugador.get("id")) in ids:
                filas.append({
                    "player_id": safe_int(jugador.get("id")),
                    "name": jugador.get("name"),
                    "price": safe_int(jugador.get("price")),
                    "points_per_match": round(
                        _por_partido(jugador), 2
                    ),
                    "euros_per_point": round(coste),
                })

            elif safe_int(jugador.get("position")) == 4:
                otros.append(coste)

        if not filas:
            return {**vacio, "reason": "Sin lanzadores medibles."}

        filas.sort(key=lambda f: f["euros_per_point"])

        mediana_suya = statistics.median(
            f["euros_per_point"] for f in filas
        )

        mediana_otros = (
            statistics.median(otros) if otros else None
        )

        return {
            "available": True,
            "rows": filas,
            "takers_median": round(mediana_suya),
            "others_median": (
                round(mediana_otros)
                if mediana_otros is not None
                else None
            ),
            "reason": (
                f"El lanzador mas barato por punto es "
                f"{filas[0]['name']} y el mas caro "
                f"{filas[-1]['name']}: "
                f"{filas[-1]['euros_per_point'] / max(filas[0]['euros_per_point'], 1):.1f} "
                f"veces de diferencia."
                + (
                    f" Y ser lanzador NO es buen precio de por si: "
                    f"su mediana es {round(mediana_suya):,} EUR "
                    f"por punto contra {round(mediana_otros):,} de "
                    f"los delanteros que no lanzan. El valor esta "
                    f"en el barato que los tira, no en tirarlos."
                    .replace(",", ".")
                    if mediana_otros
                    else ""
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo ordenar: "
                f"{type(error).__name__}: {error}"
            ),
        }


def bono(fila: dict | None, medicion: dict | None = None) -> dict:
    """
    Lo que suma a la calidad ser lanzador de penaltis.

    Hoy: cero, y con el motivo escrito. Forma fija.
    """

    vacio = {
        "applies": False,
        "value": BONO_APLICADO,
        "declared": None,
        "status": "SIN_DATO",
        "order": None,
        "reason": "No consta como lanzador.",
    }

    try:
        if not fila:
            return vacio

        orden = safe_int(fila.get("order"))

        declarado = (
            BONO_DECRETADO_PRIMERO
            if orden == 1
            else BONO_DECRETADO_SEGUNDO
        )

        apoya = bool((medicion or {}).get("supports_bonus"))

        return {
            "applies": apoya,
            "value": BONO_APLICADO if not apoya else declarado,
            "declared": declarado,
            "status": "MEDIDO" if apoya else "DECRETADO",
            "order": orden,
            "reason": (
                f"Lanzador nº {orden} de penaltis de su equipo."
                + (
                    ""
                    if apoya
                    else " El bono esta DECRETADO y no se aplica: "
                    "no hay medicion que lo sostenga y sus "
                    "penaltis ya cuentan dentro de sus puntos."
                )
            ),
        }

    except Exception as error:                       # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo calcular el bono: "
                f"{type(error).__name__}: {error}"
            ),
        }
