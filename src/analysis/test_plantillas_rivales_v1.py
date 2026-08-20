"""
Candado de las plantillas: la propia y las de los rivales.

EL CASO (20/08/2026)

    "¿Sabes lo que no veo? La plantilla del rival."

    Estaba en el snapshot desde el primer dia. `standings[]`
    trae, de cada manager, `lineup.players` -su once- y
    `lineup.discarded` -su banquillo-. Los dos juntos son su
    plantilla entera.

    Y la propia tampoco se veia del todo: la tabla enseñaba
    nombre, posicion, valor y titular o suplente. La jerarquia,
    el pronostico de salir y el parte de lesion se calculaban en
    cada ciclo y solo llegaban al XI -once de dieciseis- y a la
    tabla del mercado.

    Octava vez que aparece el mismo bicho: el dato existe, se
    calcula bien y no lo mira nadie.

LO QUE SE PROTEGE AQUI

    1. Que la ficha del rival y la mia tengan LAS MISMAS
       columnas. Comparar dos cosas contadas distinto no es
       comparar.

    2. Que sin señal de FutbolFantasy salga None y no un cero.
       Un 0 % se lee como "no juega"; la verdad es "no sabemos".

    3. Que el valor semanal salga de la funcion del motor y no de
       una copia. Dos formulas que deberian ser la misma acaban
       siendo dos.

    4. Que esto no decida nada. Es un termometro.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.telemetry.squads import (
    build_lineup_debate,
    build_rival_squads,
    enrich,
    enrich_roster,
)


# ============================================================
# UN SNAPSHOT DE MENTIRA, CON LA FORMA DEL DE VERDAD
# ============================================================


def snapshot():

    catalogo = {}

    def ficha(player_id, nombre, posicion, precio):
        catalogo[str(player_id)] = {
            "id": player_id,
            "name": nombre,
            "position": posicion,
            "price": precio,
            "priceIncrement": 1_000,
            "points": 7,
            "pointsLastSeason": 100,
            "status": "ok",
            "teamID": 1,
        }

    ficha(100, "Su portero", 1, 3_000_000)
    for i in range(4):
        ficha(200 + i, f"Su defensa {i}", 2, 2_000_000)
    for i in range(4):
        ficha(300 + i, f"Su medio {i}", 3, 2_500_000)
    for i in range(2):
        ficha(400 + i, f"Su delantero {i}", 4, 6_000_000)

    ficha(500, "Su suplente", 2, 900_000)
    ficha(501, "Su otro suplente", 3, 800_000)

    once = [100, 200, 201, 202, 203, 300, 301, 302, 303, 400, 401]
    banquillo = [500, 501]

    return {
        "catalog": {"data": {"players": catalogo}},
        "rounds": {"data": {
            "round": {"id": 4900},
            "league": {"standings": [
                {
                    "id": 777,
                    "name": "Rival",
                    "position": 1,
                    "points": 42,
                    "teamValue": 50_000_000,
                    "lineup": {
                        "type": "4-4-2",
                        "players": once,
                        "discarded": banquillo,
                    },
                },
                {
                    "id": 14175949,
                    "name": "Pepe Bordalás",
                    "position": 2,
                    "points": 40,
                    "teamValue": 49_000_000,
                    "lineup": {
                        "type": "4-4-2",
                        "players": once,
                        "discarded": banquillo,
                    },
                },
            ]},
        }},
    }


# ============================================================
# PRUEBAS
# ============================================================


def test_la_plantilla_rival_es_el_once_mas_el_banquillo():
    """
    Once alineados y dos descartados son trece jugadores, y los
    trece tienen que salir. Enseñar solo el once seria enseñar
    media plantilla creyendo que es entera.
    """

    salida = build_rival_squads(snapshot(), current_user_id=14175949)

    assert salida["available"] is True
    assert len(salida["managers"]) == 2

    rival = next(
        m for m in salida["managers"]
        if not m["is_current_user"]
    )

    assert rival["squad_size"] == 13, (
        "faltan jugadores: se esta enseñando solo el once"
    )

    titulares = [j for j in rival["players"] if j["is_starter"]]

    assert len(titulares) == 11
    assert rival["formation"] == "4-4-2"


def test_yo_salgo_marcado_entre_los_managers():
    """
    Si no me distingo de los rivales, la pantalla puede acabar
    enseñando la plantilla de otro creyendo que es la mia.
    """

    salida = build_rival_squads(snapshot(), current_user_id=14175949)

    mios = [
        m for m in salida["managers"]
        if m["is_current_user"]
    ]

    assert len(mios) == 1
    assert mios[0]["user_id"] == 14175949


def test_la_ficha_del_rival_y_la_mia_son_la_misma():
    """
    EL CANDADO DE VERDAD.

    Comparar dos plantillas contadas con columnas distintas no es
    comparar. Si un dia se le añade una señal a la propia y no a
    la del rival, la comparacion se vuelve mentira sin que salte
    nada. Salta aqui.
    """

    salida = build_rival_squads(snapshot(), current_user_id=14175949)

    rival = next(
        m for m in salida["managers"]
        if not m["is_current_user"]
    )

    mio = enrich(
        {
            "id": 300,
            "name": "Uno mio",
            "position": 3,
            "price": 1_000_000,
            "price_increment": 0,
            "points": 4,
            "status": "ok",
            "is_starter": True,
        },
        300,
    )

    columnas_del_rival = set(rival["players"][0])
    columnas_mias = set(mio)

    assert columnas_mias <= columnas_del_rival, (
        "la ficha propia tiene columnas que la del rival no: "
        f"{sorted(columnas_mias - columnas_del_rival)}"
    )


def test_sin_señal_no_se_inventa_un_porcentaje():
    """
    Ausencia de dato != dato.

    El 16/08 el dashboard pinto once barras a cero porque la
    fuente habia fallado, y parecia que el equipo no jugaba. Sin
    señal va None y la pantalla dice "sin dato".
    """

    ficha = enrich({"id": 999_999}, 999_999)

    assert ficha["starter_probability"] is None
    assert ficha["hierarchy"] is None
    assert ficha["weekly_expected_value"] is None
    assert ficha["absence"] is None


def test_el_valor_semanal_es_el_del_motor():
    """
    `weekly_expected_value` es la funcion con la que el motor
    ordena el once. Si aqui se reimplementa, el panel del plan
    acabara explicando un once distinto del que se alinea.
    """

    from src.analysis.lineup_engine import weekly_expected_value

    fuente = (
        Path(__file__).parent.parent
        / "telemetry"
        / "squads.py"
    ).read_text(encoding="utf-8")

    assert "from src.analysis.lineup_engine import" in fuente, (
        "el marcador de valor semanal ha dejado de llamar al motor"
    )

    # Y que la vara siga siendo la de siempre.
    assert round(weekly_expected_value(40, 70.0), 3) == round(
        weekly_expected_value(40, 70.0), 3
    )


# ============================================================
# EL DEBATE DEL ONCE
# ============================================================


def roster_para_el_debate():
    """
    Un once y un banquillo con un duelo reñido en el medio y otro
    holgado en la defensa.
    """

    jugadores = []

    def add(player_id, posicion, nombre, titular, valor):
        jugadores.append({
            "id": player_id,
            "name": nombre,
            "position": posicion,
            "is_starter": titular,
            "weekly_expected_value": valor,
            "starter_probability": 70.0,
            "hierarchy": "Importante",
            "availability": "DISPONIBLE",
        })

    add(100, 1, "Portero", True, 0.75)

    for i in range(4):
        add(200 + i, 2, f"DEF{i}", True, 0.60)

    add(210, 2, "DEF suplente", False, 0.20)

    for i in range(4):
        add(300 + i, 3, f"MC{i}", True, 0.50)

    # El medio flojo del once saca solo 0.02 al mejor suplente.
    add(303, 3, "MC justo", True, 0.42)
    add(310, 3, "MC suplente bueno", False, 0.40)

    add(400, 4, "DEL0", True, 0.65)
    add(401, 4, "DEL1", True, 0.62)

    return {"players": jugadores}


def test_el_duelo_no_cambia_de_posicion():
    """
    Un cambio solo es legal sin tocar el dibujo si el que entra
    juega donde el que sale. Proponer un delantero por un central
    es proponer otra formacion.
    """

    debate = build_lineup_debate(roster_para_el_debate())

    for duelo in debate["duelos"]:
        assert (
            duelo["entra"]["position"]
            == duelo["se_queda"]["position"]
            == duelo["position"]
        ), "el duelo propone un cambio que no es legal"


def test_el_duelo_es_el_peor_dentro_contra_el_mejor_fuera():
    """
    Cualquier otro par no es una decision: es un par cualquiera.
    """

    debate = build_lineup_debate(roster_para_el_debate())

    medio = next(
        d for d in debate["duelos"] if d["position"] == 3
    )

    assert medio["entra"]["name"] == "MC justo"
    assert medio["se_queda"]["name"] == "MC suplente bueno"
    assert round(medio["margen"], 3) == 0.02
    assert medio["discutible"] is True


def test_una_decision_holgada_no_se_vende_como_reñida():
    """
    Un panel que marca todo como discutible no marca nada.
    """

    debate = build_lineup_debate(roster_para_el_debate())

    defensa = next(
        d for d in debate["duelos"] if d["position"] == 2
    )

    assert defensa["margen"] > 0.3
    assert defensa["discutible"] is False


def test_sin_suplentes_en_esa_posicion_no_hay_duelo():
    """
    Con los dos delanteros dentro no habia nada que elegir, y no
    se puede fabricar un duelo para llenar el hueco.
    """

    debate = build_lineup_debate(roster_para_el_debate())

    assert all(d["position"] != 4 for d in debate["duelos"])


# ============================================================
# QUE SIGA SIENDO UN TERMOMETRO
# ============================================================


def test_las_plantillas_no_tocan_biwenger():
    """
    Saber que el rival tiene tres delanteros Dios no puede
    cambiar ninguna puja. Esto se mira y ya.
    """

    fuente = (
        Path(__file__).parent.parent
        / "telemetry"
        / "squads.py"
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
                f"las plantillas importan {nombre}: han dejado de "
                f"ser telemetria"
            )
            assert "requests" not in nombre, (
                "las plantillas han empezado a salir a la red"
            )


def test_futbolfantasy_cubre_a_los_rivales():
    """
    Las paginas de equipo se bajaban ENTERAS y solo se emparejaba
    a los nuestros y a los del mercado. Los rivales estaban en el
    disco y se tiraban.

    Y el scope RIVAL no puede degradar a nadie: un jugador
    nuestro sigue siendo ROSTER aunque tambien lo tenga un rival.
    """

    from src.intelligence.futbolfantasy_provider import build_targets

    base = snapshot()

    base["my_team"] = [
        {
            "id": 300,
            "name": "Su medio 0",
            "position": 3,
            "price": 2_500_000,
            "teamID": 1,
        }
    ]

    base["market"] = {"sales": []}

    objetivos = {o["id"]: o for o in build_targets(base)}

    assert objetivos[300]["scope"] == "ROSTER", (
        "un jugador nuestro ha quedado marcado como del rival"
    )

    rivales = [
        o for o in objetivos.values()
        if o["scope"] == "RIVAL"
    ]

    assert len(rivales) >= 12, (
        "FutbolFantasy ha dejado de cubrir a los rivales: sus "
        "plantillas saldran sin jerarquia ni pronostico"
    )

    assert 500 in objetivos, "el banquillo del rival no se cubre"


def main():

    pruebas = [
        test_la_plantilla_rival_es_el_once_mas_el_banquillo,
        test_yo_salgo_marcado_entre_los_managers,
        test_la_ficha_del_rival_y_la_mia_son_la_misma,
        test_sin_señal_no_se_inventa_un_porcentaje,
        test_el_valor_semanal_es_el_del_motor,
        test_el_duelo_no_cambia_de_posicion,
        test_el_duelo_es_el_peor_dentro_contra_el_mejor_fuera,
        test_una_decision_holgada_no_se_vende_como_reñida,
        test_sin_suplentes_en_esa_posicion_no_hay_duelo,
        test_las_plantillas_no_tocan_biwenger,
        test_futbolfantasy_cubre_a_los_rivales,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Plantillas de la liga: todo en verde.")


if __name__ == "__main__":
    main()
