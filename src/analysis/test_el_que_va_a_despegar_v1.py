"""
El que vuelve de lesion no es un malo.

SINTOMA (23/09/2026)

    Ceballos: 13 puntos en 3 partidos, 4,33 por partido, vuelve de
    lesion y llego tarde al Betis. El motor le ponia «sin interés»
    con `nos_suma = -9`, porque resta su total al de la vara -Ruben
    Garcia, 22 en 7- y le cobra los cuatro partidos que no jugo.

    Un total no es una tasa: restar acumulados castiga al que no
    jugo.

LO QUE SE PROTEGE

    1. Un jugador con 3 partidos, buena tasa y un motivo sale
       marcado «va a despegar», y no como «sin interés».
    2. `nos_suma` no cambia: la marca va encima, no en su sitio.
    3. Lleva el dato: jugados contra posibles, y el motivo.
    4. Los dos frenos: con 2 partidos no se marca, y lesionado hoy
       tampoco. Sin ellos, el primero de la liga es uno de 18 puntos
       en 2 partidos que no esta disponible.
    5. Sin motivo no hay marca: el que jugo todo y va mal sigue
       siendo «sin interés».
    6. Las cuatro clases salen de su dato.
    7. La lista del dia cruza la liga con el mercado de hoy, trae lo
       que pujaria Pepe copiado del tablero, y deja fuera al que no
       esta disponible.
    8. Este modulo no puja: no nombra ninguna escritura.

LA GUARDIA MUERDE SI TODOS HAN JUGADO TODOS LOS PARTIDOS

    Sin nadie con menos partidos que su equipo no hay pasado corto
    que marcar, y la 1 pasaria diciendo nada. Lo primero es
    exigirlo.

NO LEE EL MUNDO

    Ni `data/`, ni red, ni reloj: el catalogo es de mentira y va
    escrito aqui, con los numeros de la foto del 23/09.

COMO SE USA

    python -m src.analysis.test_el_que_va_a_despegar_v1
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.analysis.el_que_va_a_despegar import (
    LESION,
    PRENSA,
    RECIEN_FICHADO,
    SIN_PRIMERA,
    la_lista_del_dia,
    por_que_se_queda_corto,
)
from src.analysis.toda_la_liga import toda_la_liga


BETIS = 87

OTRO = 1


def _ficha(nombre, puntos, casa, fuera, forma, equipo=BETIS,
           status="ok", pasada=100, precio=1_000_000, posicion=3):
    return {
        "name": nombre,
        "position": posicion,
        "teamID": equipo,
        "status": status,
        "points": puntos,
        "playedHome": casa,
        "playedAway": fuera,
        "fitness": forma,
        "pointsLastSeason": pasada,
        "price": precio,
        "priceIncrement": 0,
    }


# EL CASO. Los numeros de Ceballos y de la vara, de la foto.
CATALOGO = {
    # La vara del medio campo: 22 en 7.
    1602: _ficha("Ruben Garcia", 22, 4, 3, [3, 2, 4, 5, 1],
                 equipo=OTRO),

    # 13 en 3, vuelve de lesion y llego tarde: 4 entradas en
    # `fitness` con un equipo de 7 partidos.
    2044: _ficha("Ceballos", 13, 1, 2, [3, 4, 6, "injured"],
                 precio=4_180_000),

    # Un compañero que lo jugo todo: da los 7 partidos del Betis.
    3000: _ficha("Titular del Betis", 30, 4, 3, [5, 5, 5, 5, 5]),

    # Freno 1: 18 en 2, con motivo. Tasa enorme, pocos partidos.
    3001: _ficha("Dos partidos", 18, 1, 1, [9, 9, "injured",
                 "injured", "injured"]),

    # Freno 2: buena tasa y motivo, pero lesionado HOY.
    3002: _ficha("Lesionado hoy", 15, 2, 1, ["injured", 5, 5, 5,
                 "injured"], status="injured"),

    # Sin motivo: jugo todo y va mal. Sigue sin interes.
    # Caro a proposito: a 1 M seria «chollo» por puntos por euro.
    3003: _ficha("Jugo todo y va mal", 10, 4, 3, [1, 1, 2, 3, 3],
                 precio=3_000_000),

    # Clase 3: viene de Segunda. 12 en 3 y sin temporada pasada
    # en Primera; su equipo jugo 7.
    3004: _ficha("De Segunda", 12, 2, 1, [4, None, None, 4, 4],
                 pasada=0),

    # Clase 4: suplente con prensa que dice que sube.
    3005: _ficha("Canterano", 11, 1, 2, [4, 3, None, None, 4]),
}

ONCE = [{"id": 1602}]

PRENSA_UP = [
    {"player_id": 3005, "direction": "UP",
     "headline": "El canterano entra en los planes"},
    {"player_id": 3004, "direction": "DOWN",
     "headline": "Esto no es una subida"},
]

MERCADO_HOY = {2044, 3002, 3003}

TABLERO = [
    {"id": 2044, "bid": 0, "our_value": 4_254_299,
     "decision": "RENDIMIENTO_INSUFICIENTE",
     "reason": "Por reventa rinde un 0.20 %."},
]


def _liga() -> dict:
    return toda_la_liga(
        CATALOGO, ONCE, [{"id": 1602}], [], MERCADO_HOY,
        prensa=PRENSA_UP,
    )


def _fila(liga, nombre) -> dict:
    return next(f for f in liga["players"] if f["name"] == nombre)


def _exige_pasados_cortos(liga) -> None:
    cortos = [
        f for f in liga["players"]
        if (f.get("pasado_corto") or {}).get("corto")
    ]

    assert cortos, (
        "en el caso todos han jugado todos los partidos: no hay "
        "pasado corto que marcar y esta guardia no prueba nada"
    )


# ============================================================
# 1-3. EL QUE VUELVE DE LESION
# ============================================================

def test_el_que_vuelve_de_lesion_no_es_un_malo() -> None:

    liga = _liga()

    assert liga["available"], liga["reason"]

    _exige_pasados_cortos(liga)

    ceballos = _fila(liga, "Ceballos")

    assert ceballos["etiqueta"] != "sin interés", (
        f"el que vuelve de lesion con 4,33 por partido sigue saliendo "
        f"«sin interés»: {ceballos}"
    )
    assert ceballos["etiqueta"] == "va a despegar", ceballos["etiqueta"]
    assert ceballos["va_a_despegar"] is True

    # LA MARCA VA ENCIMA: `nos_suma` es el de siempre.
    assert ceballos["nos_suma"] == 13 - 22, ceballos["nos_suma"]

    # EL DATO, no solo la etiqueta.
    corto = ceballos["pasado_corto"]

    assert (corto["jugados"], corto["posibles"]) == (3, 7), corto

    clases = {m["clase"] for m in corto["motivos"]}

    assert LESION in clases, clases
    assert RECIEN_FICHADO in clases, clases

    assert ceballos["tasa"] == 4.33, ceballos["tasa"]
    assert ceballos["vara_tasa"] == 3.14, ceballos["vara_tasa"]

    assert "POR ESTE HAY QUE PUJAR" in (ceballos["por_que"] or "")


# ============================================================
# 4. LOS DOS FRENOS
# ============================================================

def test_los_frenos_pocos_partidos_y_no_disponible() -> None:

    liga = _liga()

    _exige_pasados_cortos(liga)

    dos = _fila(liga, "Dos partidos")

    assert dos["tasa"] == 9.0 and dos["bate_a_la_vara"], dos
    assert dos["va_a_despegar"] is False, (
        "18 puntos en 2 partidos sale marcado: sin el minimo de "
        "partidos se cambia un sesgo por otro peor"
    )

    lesionado = _fila(liga, "Lesionado hoy")

    assert lesionado["bate_a_la_vara"], lesionado
    assert lesionado["va_a_despegar"] is False, (
        "un lesionado de hoy sale marcado como que va a despegar"
    )
    assert lesionado["etiqueta"] == "no disponible"


# ============================================================
# 5. SIN MOTIVO NO HAY MARCA
# ============================================================

def test_sin_motivo_no_hay_marca() -> None:

    liga = _liga()

    malo = _fila(liga, "Jugo todo y va mal")

    assert malo["pasado_corto"]["corto"] is False, malo
    assert malo["va_a_despegar"] is False
    assert malo["etiqueta"] == "sin interés", malo["etiqueta"]


# ============================================================
# 6. LAS CUATRO CLASES, CADA UNA DE SU DATO
# ============================================================

def test_las_cuatro_clases_salen_de_su_dato() -> None:

    liga = _liga()

    clases = lambda nombre: {                                  # noqa: E731
        m["clase"] for m in _fila(liga, nombre)["pasado_corto"]["motivos"]
    }

    assert SIN_PRIMERA in clases("De Segunda"), clases("De Segunda")
    assert PRENSA in clases("Canterano"), clases("Canterano")

    # La noticia que baja no es la clase 4.
    assert PRENSA not in clases("De Segunda")

    # Y el titular que lo jugo todo, sin ninguna.
    assert clases("Titular del Betis") == set()

    # Sin partidos posibles no se dice que su pasado sea corto.
    sin_equipo = por_que_se_queda_corto(CATALOGO[2044], None)

    assert sin_equipo["corto"] is False, sin_equipo


# ============================================================
# 7. LA LISTA DEL DIA
# ============================================================

def test_la_lista_del_dia_cruza_la_liga_con_el_mercado() -> None:

    liga = _liga()

    dia = la_lista_del_dia(liga, MERCADO_HOY, TABLERO)

    nombres = [p["name"] for p in dia["players"]]

    assert "Ceballos" in nombres, (
        f"Ceballos esta hoy en el mercado, marcado, y no sale en la "
        f"lista del dia: {nombres}"
    )
    assert "Lesionado hoy" not in nombres, nombres

    # Solo los de hoy.
    assert set(nombres) <= {"Ceballos", "Jugo todo y va mal"}, nombres

    # El marcado va antes que el que no.
    assert nombres.index("Ceballos") < nombres.index(
        "Jugo todo y va mal"
    ), nombres

    ceballos = dia["players"][nombres.index("Ceballos")]

    assert ceballos["pepe"]["en_el_tablero"] is True
    assert ceballos["pepe"]["bid"] == 0
    assert ceballos["pepe"]["decision"] == "RENDIMIENTO_INSUFICIENTE"

    otro = dia["players"][nombres.index("Jugo todo y va mal")]

    assert otro["pepe"]["en_el_tablero"] is False
    assert otro["pepe"]["bid"] is None, (
        "sin fila en el tablero se inventa una puja"
    )

    assert dia["despegan"] == 1, dia["despegan"]


# ============================================================
# 8. NO PUJA
# ============================================================

def test_la_senal_no_puja() -> None:

    fuente = Path("src/analysis/el_que_va_a_despegar.py").read_text(
        encoding="utf-8"
    )

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            modulo = getattr(nodo, "module", None) or ""
            nombres = [a.name for a in nodo.names]

            for nombre in [modulo, *nombres]:
                assert "actions" not in nombre, nombre
                assert "biwenger" not in nombre.lower(), nombre

        if isinstance(nodo, ast.Attribute):
            assert nodo.attr not in (
                "place_bid",
                "counter_offer",
                "cancel_bid",
                "accept_offer",
                "list_player_for_sale",
            ), nodo.attr


TESTS = [
    test_el_que_vuelve_de_lesion_no_es_un_malo,
    test_los_frenos_pocos_partidos_y_no_disponible,
    test_sin_motivo_no_hay_marca,
    test_las_cuatro_clases_salen_de_su_dato,
    test_la_lista_del_dia_cruza_la_liga_con_el_mercado,
    test_la_senal_no_puja,
]


def main() -> None:

    print()
    print("=" * 60)
    print("EL QUE VA A DESPEGAR V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
