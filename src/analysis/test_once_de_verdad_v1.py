"""
Se lee el once donde se escribe.

EL CASO (22/08/2026)

    El dueño tenia en Biwenger su 4-4-2, con Pablo Ibáñez dentro,
    exactamente el que Pepe recomendaba. Y el cartel decia:

        "El XI puesto en Biwenger no es el recomendado:
         1 por entrar, 1 por salir, dibujo 5-3-2 en vez de 4-4-2.
         Deberian entrar: Pablo Ibáñez."

    Lo dijo el asi:

        "Está bien el 11 pero no sé por qué sale el mensaje ese."

    Y tenia razon: Biwenger estaba bien.

DONDE ESTABA EL FALLO

    Pepe ESCRIBE el once con `PUT /user?fields=*,lineup(date)`.

    Y lo LEIA de `rounds.data.league.standings[].lineup`, que es
    otra cosa: el once que quedo congelado en una jornada YA
    JUGADA. En el snapshot del 17/08 ese bloque apuntaba a
    `round.id 4899`, que es la jornada 1.

    Ese 5-3-2 sin Pablo Ibáñez era su alineacion de la jornada 1,
    cuando todavia no tenia a ese jugador. No es que Pepe no viera
    el cambio: es que miraba una foto vieja.

    Escribir en un sitio y leer en otro. Desde el momento en que
    la plantilla cambia, no pueden coincidir nunca.

POR QUE NO ERA SOLO UN CARTEL

    Desde el 21/08 la decision de reescribir el once depende de
    esta comparacion. Un "no coincide" que no se puede apagar se
    lleva por delante la unica accion que Pepe hace por ciclo
    -alinear va a prioridad 760 y fichar a 400- cada media hora,
    para siempre.

LO QUE SE PROTEGE AQUI

    1. Que el once se lea del mismo sitio donde se escribe.
    2. Que la clasificacion de una jornada cerrada no vuelva a
       usarse como "lo que hay puesto ahora".
    3. Que sin ese dato se conteste "no se sabe" y no un once
       equivocado. Ausencia de dato != dato.
    4. Que el colector siga pidiendolo, porque sin eso lo de
       arriba no sirve de nada.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.lineup_monitor import (
    compare_with_live,
    live_lineup,
)


MI_ID = 14175949

EL_ONCE_BUENO = [17482, 9983, 2169, 8376, 38072,
                 14800, 41606, 41271, 29661, 26271, 3159]

# El de la jornada 1: 5-3-2 y sin Pablo Ibáñez (14800).
EL_ONCE_VIEJO = [17482, 9983, 2169, 8376, 38072, 5771,
                 41606, 41271, 29661, 26271, 3159]


def snapshot(con_once_actual=True):
    """
    Un snapshot con las dos cosas dentro: la foto congelada de la
    jornada 1 y la alineacion de verdad.
    """

    datos = {
        "league": {"user": {"id": MI_ID}},

        # La foto vieja. Existe, y no se puede usar.
        "rounds": {
            "data": {
                "round": {"id": 4899},
                "league": {
                    "standings": [
                        {
                            "id": MI_ID,
                            "lineup": {
                                "type": "5-3-2",
                                "players": EL_ONCE_VIEJO,
                                "date": 1786729446,
                            },
                        }
                    ]
                },
            }
        },
    }

    if con_once_actual:
        datos["user_lineup"] = {
            "data": {
                "lineup": {
                    "type": "4-4-2",
                    "playersID": EL_ONCE_BUENO,
                    "date": 1787700000,
                }
            }
        }

    return datos


def recomendado(ids=None):
    return [{"id": i, "name": f"J{i}"} for i in (ids or EL_ONCE_BUENO)]


# ============================================================
# PRUEBAS
# ============================================================


def test_se_lee_el_once_de_ahora_y_no_el_de_la_jornada_cerrada():
    """
    LA REGRESION.

    Con las dos fuentes delante, tiene que ganar la de `/user`.
    Si vuelve a leer la clasificacion, sale el 5-3-2 de la
    jornada 1 y el cartel se queda rojo para siempre.
    """

    once = live_lineup(snapshot())

    assert once is not None
    assert once["formation"] == "4-4-2", (
        "se esta leyendo el once congelado de una jornada ya "
        "jugada en vez del que hay puesto ahora"
    )
    assert once["player_ids"] == sorted(EL_ONCE_BUENO)
    assert once["source"] == "USER"


def test_el_cartel_se_apaga_cuando_biwenger_esta_bien():
    """
    El caso entero, de punta a punta: Biwenger bien, cartel verde.
    """

    comparacion = compare_with_live(
        live_lineup(snapshot()),
        recomendado(),
        "4-4-2",
    )

    assert comparacion["known"] is True
    assert comparacion["matches"] is True, (
        f"Biwenger tiene el once correcto y se sigue diciendo que "
        f"no: {comparacion.get('reason')}"
    )
    assert not comparacion["missing_in_biwenger"]
    assert comparacion["source"] == "USER"


def test_con_la_foto_vieja_habria_dicho_que_falta_pablo_ibanez():
    """
    Se reproduce el fallo a proposito, para que quede escrito cual
    era el sintoma exacto: sobra un defensa, falta un medio y el
    dibujo no cuadra.
    """

    viejo = {
        "known": True,
        "source": "ROUND",
        "formation": "5-3-2",
        "player_ids": sorted(EL_ONCE_VIEJO),
    }

    comparacion = compare_with_live(viejo, recomendado(), "4-4-2")

    assert comparacion["matches"] is False
    assert comparacion["formation_differs"] is True
    assert [j["id"] for j in comparacion["missing_in_biwenger"]] == [
        14800
    ]


def test_sin_el_dato_se_dice_que_no_se_sabe():
    """
    Ausencia de dato != dato.

    Antes, si no habia nada se caia a la foto de la jornada. Ahora
    se contesta None y `compare_with_live` vuelve a la memoria del
    ultimo XI escrito, que es el comportamiento prudente.
    """

    assert live_lineup(snapshot(con_once_actual=False)) is None

    comparacion = compare_with_live(None, recomendado(), "4-4-2")

    assert comparacion["known"] is False
    assert comparacion["matches"] is None


def test_los_jugadores_pueden_venir_como_fichas():
    """
    EL SEGUNDO SINTOMA (22/08/2026)

        Con el arreglo ya subido, el cartel cambio de queja: paso
        de "falta Pablo Ibáñez" a "No hay ningun XI puesto en
        Biwenger", y listaba los once.

        El campo llegaba; lo que no se sabia leer era la lista.
        `lineup(*)` no devuelve numeros sueltos, y con fichas
        dentro el lector se quedaba en cero.
    """

    fichas = [{"id": i, "name": f"J{i}"} for i in EL_ONCE_BUENO]

    once = live_lineup({
        "user_lineup": {
            "lineup": {"type": "4-4-2", "players": fichas}
        }
    })

    assert once is not None, (
        "con la lista en fichas se esta contestando 'no se sabe'"
    )
    assert once["player_ids"] == sorted(EL_ONCE_BUENO)

    # Y con el jugador anidado un nivel mas, que es como vienen
    # los huecos de la alineacion en algunas respuestas.
    huecos = [
        {"position": n, "player": {"id": i}}
        for n, i in enumerate(EL_ONCE_BUENO)
    ]

    otra = live_lineup({
        "user_lineup": {
            "lineup": {"type": "4-4-2", "players": huecos}
        }
    })

    assert otra is not None
    assert otra["player_ids"] == sorted(EL_ONCE_BUENO)


def test_no_saber_leer_la_lista_no_es_un_once_vacio():
    """
    LA PARTE QUE IMPORTA.

    Cero jugadores no es un dato neutro: significa "hay que poner
    el once entero", y eso es una ESCRITURA. Un fallo de lectura
    no puede disparar una escritura.

    Con cosas dentro que no se saben leer, se contesta "no se
    sabe" y manda la memoria del ultimo XI escrito.
    """

    once = live_lineup({
        "user_lineup": {
            "lineup": {
                "type": "4-4-2",
                "players": [
                    {"formato": "raro"},
                    {"otro": "campo"},
                ],
            }
        }
    })

    assert once is None, (
        "una lista ilegible se esta tomando por un once vacio: "
        "Pepe escribiria el once entero cada media hora"
    )


def test_sin_la_clave_players_no_se_sabe_nada():
    """
    MEDIDO CONTRA BIWENGER EL 22/08/2026.

        fields=*,lineup(*,players(*))  -> `players`: 11 fichas
        fields=*,lineup(*)             -> el bloque llega SIN
                                          `players`

    Pedir mal el campo no devuelve una lista vacia: devuelve un
    bloque sin la clave. Confundir las dos cosas es decir "no hay
    once puesto" cuando lo que pasa es que no se ha preguntado, y
    eso dispara una escritura del once entero.
    """

    once = live_lineup({
        "user_lineup": {
            "data": {
                "lineup": {
                    "type": "4-4-2",
                    "count": 1,
                    "date": 1787388369,
                }
            }
        }
    })

    assert once is None, (
        "un bloque sin la clave `players` se esta tomando por un "
        "once vacio"
    )


def test_un_once_vacio_de_verdad_si_es_un_once_vacio():
    """
    Y la otra cara: si de verdad no hay nadie puesto, hay que
    ponerlo. Eso no cambia.
    """

    once = live_lineup({
        "user_lineup": {"lineup": {"type": "4-4-2", "players": []}}
    })

    assert once is not None
    assert once["player_ids"] == []


def test_da_igual_como_venga_envuelto():
    """
    La respuesta puede llegar con `data` o sin el segun como se
    pida el campo. Las dos formas valen; media respuesta no puede
    dejar a Pepe ciego.
    """

    for envoltorio in (
        {"lineup": {"type": "4-4-2", "playersID": EL_ONCE_BUENO}},
        {"data": {"lineup": {"type": "4-4-2",
                             "playersID": EL_ONCE_BUENO}}},
        {"type": "4-4-2", "playersID": EL_ONCE_BUENO},
    ):
        once = live_lineup({"user_lineup": envoltorio})

        assert once is not None, envoltorio
        assert once["player_ids"] == sorted(EL_ONCE_BUENO)


def test_la_clasificacion_ya_no_es_fuente_del_once_propio():
    """
    El candado estructural. Mientras `live_lineup` no vuelva a
    tocar `standings`, este fallo no puede reaparecer por
    despiste.
    """

    fuente = (
        Path(__file__).parent / "lineup_monitor.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.FunctionDef):
            continue

        if nodo.name != "live_lineup":
            continue

        # Sin el docstring: ahi se CUENTA el fallo, y contarlo no
        # es cometerlo.
        cuerpo_sin_texto = [
            n for n in nodo.body
            if not (
                isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)
            )
        ]

        cuerpo = " ".join(ast.dump(n) for n in cuerpo_sin_texto)

        assert "standings" not in cuerpo, (
            "live_lineup ha vuelto a leer la clasificacion: eso "
            "es el once de una jornada ya jugada"
        )

        assert "user_lineup" in cuerpo or "_current_lineup_block" in cuerpo

        return

    raise AssertionError("no se encuentra live_lineup")


def test_el_colector_pide_la_alineacion():
    """
    Sin esto, `user_lineup` no existe nunca y Pepe se queda
    diciendo "no se sabe" para siempre. Se comprueba tambien que
    se pide al MISMO endpoint donde se escribe.
    """

    fuente = (
        Path(__file__).parents[1]
        / "collectors"
        / "league_collector.py"
    ).read_text(encoding="utf-8")

    assert "user_lineup" in fuente, (
        "el colector ha dejado de pedir la alineacion actual"
    )

    assert "lineup(*)" in fuente
    assert '"user_lineup": user_lineup' in fuente, (
        "se pide pero no se guarda en el snapshot"
    )

    escritura = (
        Path(__file__).parents[1]
        / "biwenger"
        / "write_client.py"
    ).read_text(encoding="utf-8")

    assert "/user" in escritura, (
        "el once ya no se escribe en /user: si ha cambiado el "
        "sitio de escritura, tiene que cambiar el de lectura"
    )


def main():

    pruebas = [
        test_se_lee_el_once_de_ahora_y_no_el_de_la_jornada_cerrada,
        test_el_cartel_se_apaga_cuando_biwenger_esta_bien,
        test_con_la_foto_vieja_habria_dicho_que_falta_pablo_ibanez,
        test_sin_el_dato_se_dice_que_no_se_sabe,
        test_da_igual_como_venga_envuelto,
        test_los_jugadores_pueden_venir_como_fichas,
        test_no_saber_leer_la_lista_no_es_un_once_vacio,
        test_sin_la_clave_players_no_se_sabe_nada,
        test_un_once_vacio_de_verdad_si_es_un_once_vacio,
        test_la_clasificacion_ya_no_es_fuente_del_once_propio,
        test_el_colector_pide_la_alineacion,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("El once de verdad: todo en verde.")


if __name__ == "__main__":
    main()
