"""
Cruzar los nombres de las webs con los IDs de Biwenger.

AQUI ES DONDE ESTO SE ROMPE, Y YA NOS HEMOS QUEMADO

    Hay un caso conocido sin resolver: Javi Hernandez, metodo
    NAME, margen 0,586, desvio de precio del 45,7 %. Sigue en la
    metadata del tablero de titularidad desde que se genero, y no
    lo ha mirado nadie.

    Un emparejamiento equivocado mete la prediccion de otro
    jugador en la ficha de uno tuyo. Eso es peor que no tener
    prediccion: sin dato no decides, con dato falso decides mal y
    encima con confianza.

LA REGLA DURA

    Lo que no empareje con confianza va a `unmatched` y se
    publica con su motivo. Nunca se adivina.

DOS LLAVES, COMO EN EL PROVEEDOR

    Se reutiliza la maquinaria de `futbolfantasy_provider`:
    `_name_score`, que ya sabe que "Mbappe" y "Kylian Mbappe" son
    el mismo, y que "Andres" no identifica a nadie.

    Y encima, la llave del euro: las tres fuentes publican el
    valor Biwenger. Si el valor cuadra al euro y ademas el nombre
    es plausible, la identidad esta cerrada.

LA DIFERENCIA CON EL PROVEEDOR, QUE IMPORTA

    `match_team` empareja DENTRO DE UN EQUIPO: veinticinco
    nombres, y el que gana suele ganar por mucho. Aqui se empareja
    contra los 569 de la liga entera, asi que hay mas donde
    equivocarse y los listones tienen que ser mas altos.

    Se midio sobre el catalogo del 17/08: solo el 40 % de los
    jugadores tiene un precio UNICO en la liga, y 102 comparten el
    minimo de 150.000 EUR. Asi que el precio solo no identifica: es
    una llave, no la llave.

    Por eso el valor exacto exige ademas nombre plausible, y
    cuando varios comparten precio se exige mucho mas nombre.
"""

from __future__ import annotations

from src.intelligence.scout.common import safe_int


# ============================================================
# LOS LISTONES
# ============================================================
#
#     Los mismos que usa `match_team` para la via del valor, y
#     mas altos para la via del nombre, porque aqui el rival no
#     son 25 jugadores sino 569.

# Valor exacto + un solo candidato con ese precio: basta con que
# el nombre sea plausible. El euro ya ha dicho quien es.
VALUE_NAME_FLOOR = 0.45

# Valor exacto pero varios candidatos comparten precio: el nombre
# tiene que desempatar de verdad.
VALUE_TIE_FLOOR = 0.70

# Sin valor que ayude, solo el nombre. En el proveedor esto es
# 0,82 dentro de un equipo; contra la liga entera se sube.
NAME_ONLY_FLOOR = 0.88

# Y ademas tiene que ganar al segundo por un margen claro. Un
# empate entre dos nombres parecidos no se resuelve tirando una
# moneda: se deja sin emparejar.
NAME_ONLY_MARGIN = 0.08


def _name_score(record: dict, target: dict) -> float:
    """
    El scorer del proveedor, tal cual.

    Se importa dentro de la funcion para no arrastrar el modulo
    de scraping entero cada vez que alguien importa el ojeador.
    """

    from src.intelligence.futbolfantasy_provider import (
        _name_score as puntuar,
    )

    return puntuar(record, target)


def build_targets(catalog: dict | None) -> list[dict]:
    """
    Los 569 de Biwenger, con la forma que espera el scorer.
    """

    # Cada escalon por separado: un `{"data": null}` -que llega
    # cuando el snapshot viene a medias- hacia reventar el
    # encadenado, y un ojeador que lanza detiene el ciclo.
    datos = (catalog or {}).get("data")

    if not isinstance(datos, dict):
        return []

    jugadores = datos.get("players")

    if not isinstance(jugadores, dict):
        return []

    objetivos = []

    for clave, ficha in jugadores.items():

        if not isinstance(ficha, dict):
            continue

        identificador = safe_int(ficha.get("id") or clave)

        nombre = ficha.get("name")

        if not identificador or not nombre:
            continue

        objetivos.append(
            {
                "id": identificador,
                "name": nombre,
                "slug": ficha.get("slug"),
                "price": safe_int(ficha.get("price")),
                "team_id": safe_int(ficha.get("teamID")),
            }
        )

    return objetivos


def match_records(
    records: list | None,
    targets: list | None,
) -> tuple[list, list]:
    """
    `(emparejados, sin_emparejar)`.

    Cada emparejado lleva `method`, `score` y `margin`, para que
    una guardia pueda comprobar despues que nadie dudoso entro
    como bueno.

    Cada jugador de Biwenger se asigna UNA vez. Si dos filas de
    la misma fuente reclaman al mismo, la segunda se queda sin
    emparejar y lo dice: dos predicciones distintas sobre el
    mismo jugador no pueden ser las dos suyas.
    """

    libres = {
        objetivo["id"]: objetivo
        for objetivo in (targets or [])
    }

    por_precio: dict[int, list] = {}

    for objetivo in libres.values():

        if objetivo["price"] > 0:
            por_precio.setdefault(objetivo["price"], []).append(
                objetivo
            )

    emparejados = []
    sin_emparejar = []

    pendientes = [
        registro
        for registro in (records or [])
        if isinstance(registro, dict)
    ]

    def cerrar(registro, objetivo, metodo, score, margen):

        libres.pop(objetivo["id"], None)

        for lista in por_precio.values():
            if objetivo in lista:
                lista.remove(objetivo)

        emparejados.append(
            {
                "record": registro,
                "target": objetivo,
                "method": metodo,
                "score": round(score, 3),
                "margin": round(margen, 3),
            }
        )

    def descartar(registro, motivo):
        sin_emparejar.append(
            {
                "source": (
                    (registro.get("signals") or [{}])[0].get("source")
                    or "?"
                ),
                "name": registro.get("ff_name"),
                "team": registro.get("team_hint"),
                "market_value": registro.get("market_value"),
                "reason": motivo,
            }
        )

    # ------------------------------------------------------
    # 1. EL EURO, Y UN NOMBRE QUE NO CONTRADIGA
    # ------------------------------------------------------

    resto = []

    for registro in pendientes:

        valor = safe_int(registro.get("market_value"))

        candidatos = por_precio.get(valor, []) if valor else []

        if not candidatos:
            resto.append(registro)
            continue

        if len(candidatos) == 1:

            score = _name_score(registro, candidatos[0])

            if score >= VALUE_NAME_FLOOR:
                cerrar(
                    registro,
                    candidatos[0],
                    "VALUE_AND_NAME",
                    score,
                    1.0,
                )
                continue

            # El precio cuadra y el nombre dice que no. Eso no es
            # un emparejamiento flojo: es una coincidencia de
            # precio entre dos jugadores distintos.
            descartar(
                registro,
                f"El valor {valor} cuadra con "
                f"'{candidatos[0]['name']}' pero el nombre no "
                f"({score:.2f} < {VALUE_NAME_FLOOR}).",
            )
            continue

        puntuados = sorted(
            ((_name_score(registro, o), o) for o in candidatos),
            key=lambda par: par[0],
            reverse=True,
        )

        mejor, objetivo = puntuados[0]
        segundo = puntuados[1][0] if len(puntuados) > 1 else 0.0

        if mejor >= VALUE_TIE_FLOOR and mejor > segundo:
            cerrar(
                registro,
                objetivo,
                "VALUE_AND_NAME",
                mejor,
                mejor - segundo,
            )
            continue

        descartar(
            registro,
            f"{len(candidatos)} jugadores comparten el valor "
            f"{valor} y el nombre no desempata "
            f"({mejor:.2f} contra {segundo:.2f}).",
        )

    # ------------------------------------------------------
    # 2. SOLO EL NOMBRE, Y EXIGIENDO MUCHO
    # ------------------------------------------------------

    for registro in resto:

        if not libres:
            descartar(registro, "No quedan jugadores por asignar.")
            continue

        puntuados = sorted(
            ((_name_score(registro, o), o) for o in libres.values()),
            key=lambda par: par[0],
            reverse=True,
        )

        mejor, objetivo = puntuados[0]
        segundo = puntuados[1][0] if len(puntuados) > 1 else 0.0

        if mejor >= NAME_ONLY_FLOOR and (mejor - segundo) >= NAME_ONLY_MARGIN:
            cerrar(registro, objetivo, "NAME", mejor, mejor - segundo)
            continue

        valor = safe_int(registro.get("market_value"))

        descartar(
            registro,
            (
                f"Sin valor que cuadre en el catalogo"
                + (f" (dice {valor})" if valor else "")
                + f" y el nombre no llega: mejor '{objetivo['name']}' "
                f"con {mejor:.2f}, segundo {segundo:.2f} "
                f"(hace falta {NAME_ONLY_FLOOR} y "
                f"{NAME_ONLY_MARGIN} de margen)."
            ),
        )

    return (emparejados, sin_emparejar)
