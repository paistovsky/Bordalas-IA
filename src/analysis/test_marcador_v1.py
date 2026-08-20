"""
Candado del marcador.

EL RIESGO

    Un marcador que miente es peor que no tener marcador. Si
    dice 92 % cuando es 61 %, se deja de tocar el motor de
    alineacion justo donde estaba la liga entera.

    Por eso lo que se prueba aqui no es que "funcione": es que
    cuando no sepa algo, lo diga.

LOS CUATRO SITIOS DONDE PODIA MENTIR

    1. Medir la jornada por el array `fitness`, cuyo indice no
       dice a que jornada pertenece cada valor.

    2. Contar la jornada en curso, que tiene la clasificacion a
       cero porque todavia no ha cerrado.

    3. Inventar una jornada sin observacion previa, en vez de
       marcarla `medible: false`.

    4. Calcular el techo con menos formaciones de las que evalua
       el motor de alineacion, que hace que el once real parezca
       mejor de lo que es.
"""

from __future__ import annotations

import ast
import json
import tempfile

from pathlib import Path

from src.analysis import marcador as M


# ============================================================
# UTILIDAD: un ledger de mentira en un directorio temporal
# ============================================================


class ledger_temporal:
    """Aparta el fichero real mientras dura la prueba."""

    def __enter__(self):
        self._directorio = tempfile.TemporaryDirectory()

        self._state = M.STATE_DIRECTORY
        self._file = M.LEDGER_FILE

        M.STATE_DIRECTORY = Path(self._directorio.name)
        M.LEDGER_FILE = M.STATE_DIRECTORY / "marcador.json"

        return M.LEDGER_FILE

    def __exit__(self, *_):
        M.STATE_DIRECTORY = self._state
        M.LEDGER_FILE = self._file
        self._directorio.cleanup()


def plantilla():
    """
    Dos porteros, cinco defensas, cinco medios y dos delanteros:
    lo justo para que salgan varias formaciones legales y el
    techo tenga que elegir entre ellas.
    """

    jugadores = []

    def add(player_id, posicion, nombre):
        jugadores.append({
            "id": player_id,
            "name": nombre,
            "position": posicion,
        })

    add(100, 1, "Dituro")
    add(101, 1, "Bayindir")

    for i in range(5):
        add(200 + i, 2, f"DEF{i}")

    for i in range(5):
        add(300 + i, 3, f"MC{i}")

    add(400, 4, "Jutglà")
    add(401, 4, "Yamal")

    return jugadores


def escribir_ledger(fichero: Path, jornadas: list[dict]) -> None:

    fichero.parent.mkdir(parents=True, exist_ok=True)

    with open(fichero, "w", encoding="utf-8") as file:
        json.dump(
            {
                "version": 1,
                "updated_at": None,
                "jornadas": {
                    str(j["round_id"]): j
                    for j in jornadas
                },
            },
            file,
            ensure_ascii=False,
        )


def jornada(
    round_id: int,
    totales: dict,
    once: list[int],
    puntos_biwenger: int,
    puntos_rivales=(10, 20, 30),
    formacion: str = "4-4-2",
) -> dict:

    clasificacion = [
        {"user_id": 1, "name": "Pepe", "points": puntos_biwenger},
    ]

    for indice, puntos in enumerate(puntos_rivales, start=2):
        clasificacion.append({
            "user_id": indice,
            "name": f"Rival{indice}",
            "points": puntos,
        })

    return {
        "round_id": round_id,
        "visto": "2026-08-20T13:00:00",
        "clasificacion": clasificacion,
        "mi_user_id": 1,
        "mi_once": {
            "formation": formacion,
            "players": once,
        },
        "plantilla": plantilla(),
        "totales": {str(k): v for k, v in totales.items()},
    }


def sin_puntos() -> dict:
    return {j["id"]: 0 for j in plantilla()}


# ============================================================
# PRUEBAS
# ============================================================


def test_las_formaciones_son_las_del_motor():
    """
    El techo se calcula sobre las formaciones que Pepe puede
    alinear de verdad. Si el motor aprende una nueva y el
    marcador no, el techo sale bajo y la eficiencia sale
    inflada: parecera que alinea mejor de lo que alinea.
    """

    from src.analysis.lineup_engine import FORMATIONS

    assert M.FORMACIONES == FORMATIONS, (
        "el marcador y el motor de alineacion ya no evaluan las "
        "mismas formaciones: la eficiencia queda inflada"
    )


def test_la_jornada_se_mide_por_diferencia_de_totales():
    """
    Un jugador que se salta una jornada tiene el array `fitness`
    mas corto, no un hueco. Medir por indice le adjudicaria los
    puntos de otra jornada.
    """

    despues_de_j1 = sin_puntos()
    despues_de_j1[300] = 7
    despues_de_j1[200] = 4

    despues_de_j2 = dict(despues_de_j1)
    despues_de_j2[300] += 2
    despues_de_j2[400] = 11

    puntos = M._puntos_de_la_jornada(
        {"round_id": 4900, "totales": {
            str(k): v for k, v in despues_de_j2.items()
        }},
        {"round_id": 4899, "totales": {
            str(k): v for k, v in despues_de_j1.items()
        }},
    )

    assert puntos["300"] == 2, (
        "se estan contando puntos de jornadas anteriores"
    )
    assert puntos["400"] == 11
    assert puntos["200"] == 0


def test_sin_observacion_previa_no_se_inventa():
    """
    Ausencia de dato != dato. Una jornada que no es la primera
    de la temporada y no tiene anterior anotada no se puede
    medir, y tiene que decirlo.
    """

    assert M._puntos_de_la_jornada(
        {"round_id": 4903, "totales": {"300": 40}},
        None,
    ) is None

    # La primera de la temporada si: no hay nada antes.
    assert M._puntos_de_la_jornada(
        {"round_id": M.PRIMERA_JORNADA, "totales": {"300": 7}},
        None,
    ) == {"300": 7}


def test_el_mejor_once_es_un_once_legal():
    """
    Once jugadores, un portero, y un reparto que exista en la
    lista de formaciones. Un techo ilegal no es un techo.
    """

    puntos = {str(j["id"]): 1 for j in plantilla()}
    puntos["400"] = 20
    puntos["401"] = 18

    posiciones = {
        str(j["id"]): j["position"] for j in plantilla()
    }

    techo = M.mejor_once(puntos, posiciones)

    assert len(techo["players"]) == 11
    assert techo["formation"] in M.FORMACIONES

    cuenta = {1: 0, 2: 0, 3: 0, 4: 0}
    for player_id in techo["players"]:
        cuenta[posiciones[player_id]] += 1

    assert cuenta == M.FORMACIONES[techo["formation"]]

    assert "400" in techo["players"], (
        "el techo no ha metido al maximo anotador"
    )


def test_los_empates_no_corrigen_a_quien_jugo():
    """
    En una jornada normal hay ocho o diez jugadores a cero. Si el
    desempate es arbitrario, la pantalla acaba diciendo "debio
    jugar Bayindir, 0 puntos" y la lista de fallos se vuelve
    ruido que nadie mira.

    Con empate manda el que Pepe alineo.
    """

    puntos = {str(j["id"]): 0 for j in plantilla()}
    puntos["300"] = 9

    posiciones = {
        str(j["id"]): j["position"] for j in plantilla()
    }

    once = [
        100,
        200, 201, 202, 203,
        300, 301, 302, 303,
        400, 401,
    ]

    techo = M.mejor_once(
        puntos,
        posiciones,
        alineados=once,
        formacion_usada="4-4-2",
    )

    assert techo["formation"] == "4-4-2", (
        "con los mismos puntos se le esta corrigiendo el dibujo"
    )

    assert set(techo["players"]) == {str(p) for p in once}, (
        "el techo ha cambiado jugadores que puntuaron igual"
    )


def test_la_jornada_en_curso_no_cuenta():
    """
    `/rounds/league` devuelve la jornada en curso con todos a
    cero. Contarla hundiria la media y el dueño veria que Pepe
    "va ultimo" cuando aun no se ha jugado.
    """

    with ledger_temporal() as fichero:

        j1 = jornada(
            4899,
            {**sin_puntos(), 300: 7, 200: 4},
            once=[100, 200, 201, 202, 203, 300, 301, 302, 303, 400, 401],
            puntos_biwenger=11,
        )

        j2 = jornada(
            4900,
            {**sin_puntos(), 300: 7, 200: 4},
            once=[100, 200, 201, 202, 203, 300, 301, 302, 303, 400, 401],
            puntos_biwenger=0,
            puntos_rivales=(0, 0, 0),
        )

        escribir_ledger(fichero, [j1, j2])

        datos = M.marcador()

    por_jornada = {
        f["round_id"]: f for f in datos["jornadas"]
    }

    assert por_jornada[4899]["medible"] is True
    assert por_jornada[4900]["medible"] is False, (
        "se esta midiendo la jornada en curso"
    )

    assert datos["resumen"]["jornadas_medibles"] == 1


def test_el_contrafactual_dice_lo_que_se_dejo_en_el_banquillo():
    """
    El caso entero. Pepe alinea a cuatro medios flojos teniendo
    en el banquillo al que puntuo 12. El marcador tiene que
    enseñar esa distancia.
    """

    with ledger_temporal() as fichero:

        totales = sin_puntos()
        totales[300] = 1
        totales[301] = 1
        totales[302] = 1
        totales[303] = 1
        totales[304] = 12          # el del banquillo

        once = [
            100,
            200, 201, 202, 203,
            300, 301, 302, 303,
            400, 401,
        ]

        j1 = jornada(4899, totales, once, puntos_biwenger=4)
        j2 = jornada(4900, totales, once, puntos_biwenger=0)

        escribir_ledger(fichero, [j1, j2])

        datos = M.marcador()

    fila = datos["jornadas"][0]

    assert fila["puntos_once"] == 4
    assert fila["mejor_puntos"] >= 15, (
        "el techo no ha visto al jugador del banquillo"
    )
    assert fila["mejor_puntos"] > fila["puntos_once"]
    assert fila["eficiencia"] < 30


def test_el_cuadre_avisa_cuando_el_marcador_miente():
    """
    Los puntos del once reconstruido tienen que coincidir con
    los que Biwenger le dio a Pepe. Si no coinciden, hay un
    fallo de reconstruccion y el numero no vale.
    """

    with ledger_temporal() as fichero:

        totales = sin_puntos()
        totales[300] = 7

        once = [
            100, 200, 201, 202, 203,
            300, 301, 302, 303, 400, 401,
        ]

        # Biwenger dice 99: la reconstruccion da 7.
        j1 = jornada(4899, totales, once, puntos_biwenger=99)
        j2 = jornada(4900, totales, once, puntos_biwenger=0)

        escribir_ledger(fichero, [j1, j2])

        datos = M.marcador()

    assert datos["jornadas"][0]["cuadra"] is False
    assert datos["resumen"]["cuadra_todo"] is False


def test_el_marcador_no_toca_biwenger():
    """
    Es un observador. Si alguien le mete un cliente de escritura
    dentro, deja de ser un termometro y pasa a ser un actor.
    """

    fuente = (
        Path(__file__).parent / "marcador.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nombres = [nodo.module or ""]
        else:
            continue

        for nombre in nombres:
            assert "biwenger" not in nombre, (
                f"el marcador importa {nombre}: ha dejado de ser "
                f"un observador"
            )
            assert "requests" not in nombre, (
                "el marcador ha empezado a salir a la red"
            )


def test_observar_guarda_la_ultima_foto_de_la_jornada():
    """
    Se llama en cada ciclo, dos veces por hora. La observacion
    que queda tiene que ser la ultima, que es la definitiva
    justo antes de que Biwenger salte de jornada.
    """

    with ledger_temporal():

        snapshot = {
            "rounds": {"data": {
                "round": {"id": 4899},
                "league": {"standings": [
                    {
                        "id": 1,
                        "name": "Pepe",
                        "points": 0,
                        "lineup": {
                            "type": "4-4-2",
                            "players": [100, 200, 201],
                        },
                    },
                ]},
            }},
            "my_team": [
                {"id": 300, "name": "MC0", "position": 3, "points": 7},
            ],
        }

        primera = M.observar(snapshot, current_user_id=1)
        assert primera["anotada"] is True

        snapshot["my_team"][0]["points"] = 9

        segunda = M.observar(snapshot, current_user_id=1)
        assert segunda["jornadas_en_ledger"] == 1

        ledger = M.cargar_ledger()

        assert ledger["jornadas"]["4899"]["totales"]["300"] == 9, (
            "la observacion no se ha refrescado: quedaria "
            "congelada la primera del dia"
        )


def main():

    pruebas = [
        test_las_formaciones_son_las_del_motor,
        test_la_jornada_se_mide_por_diferencia_de_totales,
        test_sin_observacion_previa_no_se_inventa,
        test_el_mejor_once_es_un_once_legal,
        test_los_empates_no_corrigen_a_quien_jugo,
        test_la_jornada_en_curso_no_cuenta,
        test_el_contrafactual_dice_lo_que_se_dejo_en_el_banquillo,
        test_el_cuadre_avisa_cuando_el_marcador_miente,
        test_el_marcador_no_toca_biwenger,
        test_observar_guarda_la_ultima_foto_de_la_jornada,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Marcador: todo en verde.")


if __name__ == "__main__":
    main()
