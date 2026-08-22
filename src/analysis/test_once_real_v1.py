"""
El once se compara con Biwenger, no con la libreta.

EL CASO (20/08/2026, dos horas antes del cierre)

    "Tengo esta alineacion en Biwenger y esta es la que tiene
     Pepe. ¿Que esta pasando?"

    Pepe recomendaba un 5-3-2 con Bigas. En Biwenger habia un
    4-3-3 con Lucas Cepeda. Y el dashboard decia 11/11 en verde.

EL FALLO, EN DOS PIEZAS

    1. `compare_lineups` comparaba el XI recomendado de hoy con
       el ultimo XI que el propio monitor se habia anotado en
       `data/lineup_monitor/state.json`.

    2. `ensure_lineup_baseline` escribia esa libreta la primera
       vez que corria el ciclo, SIN haber enviado nada a
       Biwenger.

    Juntas: la recomendacion coincidia con su propia libreta,
    salia KEEP_LINEUP y no se escribia nunca. Pepe se estaba
    comparando consigo mismo.

    Una libreta que se adelanta a la realidad es peor que no
    tener libreta: convierte "no lo he hecho" en "ya estaba
    hecho".

LA REGLA, EN PALABRAS DEL DUEÑO

    "Que haga lo que tenga que hacer, pero que siempre lea lo
     que hay en Biwenger y luego lo ajuste."

CORRECCION DEL 22/08/2026

    Este fichero nacio dando por bueno que el once que hay puesto
    vivia en `standings[<mi id>].lineup`. No: eso es el once
    CONGELADO de una jornada ya jugada.

    El once de la jornada que viene se lee donde se escribe,
    `GET /user?fields=*,lineup(*)`, y el snapshot lo trae en
    `user_lineup`. El caso entero esta en
    `test_once_de_verdad_v1`.

    Lo que se comprueba aqui sigue valiendo igual -leer antes de
    escribir, no fiarse de la libreta-; lo que cambia es de donde
    sale el dato.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.lineup_monitor import (
    compare_with_live,
    live_lineup,
)


MI_ID = 14175949


def snapshot(once_puesto, dibujo="4-3-3", con_fila=True):
    """
    Un snapshot con la alineacion de verdad dentro.

    Se conserva tambien la clasificacion, con OTRO once, para que
    quede probado que no se cuela: si alguien vuelve a leer de
    ahi, estas pruebas se caen.
    """

    datos = {
        "league": {"user": {"id": MI_ID}},

        # La foto congelada de una jornada ya jugada. Existe en el
        # snapshot de verdad y NO es lo que hay puesto ahora.
        "rounds": {
            "data": {
                "round": {"id": 4899},
                "league": {
                    "standings": [
                        {
                            "id": MI_ID,
                            "name": "Pepe Bordalás",
                            "lineup": {
                                "type": "5-4-1",
                                "players": list(range(90, 101)),
                                "discarded": [],
                            },
                        },
                        {
                            "id": 777,
                            "name": "Otro",
                            "lineup": {
                                "type": "4-4-2",
                                "players": [],
                                "discarded": [],
                            },
                        },
                    ]
                },
            }
        },
    }

    if con_fila:
        datos["user_lineup"] = {
            "data": {
                "lineup": {
                    "type": dibujo,
                    "playersID": once_puesto,
                }
            }
        }

    return datos


def once(ids):
    return [{"id": i, "name": f"J{i}"} for i in ids]


ONCE_A = list(range(1, 12))


# ============================================================
# LEER LO QUE HAY
# ============================================================


def test_se_lee_el_once_que_hay_puesto():
    """
    El once de la jornada que viene, leido de `user_lineup`, que
    es donde Pepe lo escribe.

    Y con la clasificacion delante trayendo otro distinto: si se
    colase, esto se caeria.
    """

    live = live_lineup(snapshot(ONCE_A, "5-3-2"))

    assert live["known"] is True
    assert live["formation"] == "5-3-2"
    assert live["player_ids"] == ONCE_A


def test_sin_alineacion_no_se_inventa_una():
    """
    Ausencia de dato != dato.

    Antes, sin el once real se caia al de la jornada cerrada y se
    comparaba contra el. Comparar contra un dato equivocado es
    peor que no comparar: ahora se contesta "no se sabe" y manda
    la memoria del ultimo XI escrito.
    """

    base = snapshot(ONCE_A, con_fila=False)

    assert live_lineup(base) is None, (
        "sin alineacion de verdad se esta cogiendo la de la "
        "jornada ya jugada"
    )


# ============================================================
# LA DECISION
# ============================================================


def test_si_lo_puesto_ya_es_lo_recomendado_no_se_toca():

    live = live_lineup(snapshot(ONCE_A, "4-4-2"))

    resultado = compare_with_live(live, once(ONCE_A), "4-4-2")

    assert resultado["matches"] is True


def test_un_jugador_distinto_obliga_a_escribir():
    """
    El caso literal: Bigas dentro, Cepeda fuera.
    """

    live = live_lineup(snapshot(ONCE_A, "4-4-2"))

    recomendado = ONCE_A[:-1] + [99]

    resultado = compare_with_live(live, once(recomendado), "4-4-2")

    assert resultado["matches"] is False

    assert [j["id"] for j in resultado["missing_in_biwenger"]] == [99]
    assert [j["id"] for j in resultado["extra_in_biwenger"]] == [11]


def test_el_mismo_once_con_otro_dibujo_no_es_el_mismo_once():
    """
    Biwenger guarda dos cosas: quienes juegan y con que
    formacion. Un 4-3-3 y un 5-3-2 con los mismos once no son lo
    mismo.
    """

    live = live_lineup(snapshot(ONCE_A, "4-3-3"))

    resultado = compare_with_live(live, once(ONCE_A), "5-3-2")

    assert resultado["matches"] is False
    assert resultado["formation_differs"] is True


def test_sin_once_puesto_hay_que_ponerlo():
    """
    Una fila con `players` vacio no es "no lo sabemos": es que no
    hay nadie alineado, y eso hay que arreglarlo ya.
    """

    live = live_lineup(snapshot([], "4-4-2"))

    assert live["known"] is True

    resultado = compare_with_live(live, once(ONCE_A), "4-4-2")

    assert resultado["matches"] is False
    assert len(resultado["missing_in_biwenger"]) == 11


def test_no_poder_leer_no_es_que_coincida():
    """
    Ausencia de dato != dato.

    Si no aparece nuestra fila, `matches` es None, no True. Un
    True aqui volveria a dejar el once sin tocar creyendo que ya
    estaba bien, que es exactamente lo que paso.
    """

    resultado = compare_with_live(None, once(ONCE_A), "4-4-2")

    assert resultado["known"] is False
    assert resultado["matches"] is None
    assert resultado["matches"] is not True


# ============================================================
# LOS DOS CANDADOS DE LA REGRESION
# ============================================================


def test_el_monitor_lee_biwenger_antes_de_decidir():
    """
    Si alguien vuelve a hacer que la decision dependa solo de
    `comparison`, el once se queda sin escribir para siempre y no
    se entera nadie hasta que el dueño mira Biwenger a mano.
    """

    fuente = (
        Path(__file__).parent / "lineup_monitor.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    build = next(
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef)
        and nodo.name == "build_lineup_monitor_state"
    )

    llamadas = {
        nodo.func.id
        for nodo in ast.walk(build)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
    }

    assert "live_lineup" in llamadas, (
        "el monitor ha dejado de leer el XI real de Biwenger"
    )

    assert "compare_with_live" in llamadas, (
        "el monitor lee el XI real pero ya no lo compara"
    )


def test_la_libreta_no_se_adelanta_a_la_escritura():
    """
    `ensure_lineup_baseline` guardaba el XI recomendado en el
    fichero de estado sin haberlo enviado. El estado solo puede
    escribirse DESPUES de que Biwenger confirme.
    """

    fuente = (
        Path(__file__).parent.parent / "autopilot.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    funcion = next(
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.FunctionDef)
        and nodo.name == "ensure_lineup_baseline"
    )

    guarda = any(
        isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
        and nodo.func.id == "save_lineup_monitor_state"
        for nodo in ast.walk(funcion)
    )

    assert not guarda, (
        "el autopilot vuelve a anotar el XI como escrito sin "
        "haberlo enviado a Biwenger"
    )


def main():

    pruebas = [
        test_se_lee_el_once_que_hay_puesto,
        test_sin_alineacion_no_se_inventa_una,
        test_si_lo_puesto_ya_es_lo_recomendado_no_se_toca,
        test_un_jugador_distinto_obliga_a_escribir,
        test_el_mismo_once_con_otro_dibujo_no_es_el_mismo_once,
        test_sin_once_puesto_hay_que_ponerlo,
        test_no_poder_leer_no_es_que_coincida,
        test_el_monitor_lee_biwenger_antes_de_decidir,
        test_la_libreta_no_se_adelanta_a_la_escritura,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("El once real: todo en verde.")


if __name__ == "__main__":
    main()
