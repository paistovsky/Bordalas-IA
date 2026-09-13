"""
El calendario no se inventa rivales, y lo que no casa lo dice.

POR QUE (13/09/2026, noche)

    `laliga_calendar.json` lleva vivo desde siempre y no lo
    miraba nadie. Al enchufarlo a una pantalla, el riesgo nuevo
    es el casado: las fichas del calendario y las de la
    clasificacion se cruzan POR NOMBRE.

    Hoy casan las veinte, comprobado. Pero un nombre que cambia
    —"Celta" pasa a "RC Celta"— desemparejaria un equipo y su
    fila se quedaria sin puesto de rival.

CONSECUENCIA DE TIRARLO EN SILENCIO

    Un equipo menos en el cuadro no lo echa de menos nadie: no
    hay hueco, no hay error, simplemente hay diez filas donde
    habia once. Y la media del rival de los que quedan seguiria
    calculandose como si nada.

    Peor todavia: un rival sin puesto pintado como "blando" se
    lee como una buena noticia que nadie ha comprobado.

REGLA 23

    No lee ficheros: calendario, clasificacion y plantilla se
    construyen aqui.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

AHORA = datetime(2026, 9, 13, 22, 48, tzinfo=timezone.utc)


CLASIFICACION = [
    {"rank": 1, "team": "FC Barcelona", "biwenger_team_id": 3},
    {"rank": 2, "team": "Real Madrid", "biwenger_team_id": 1},
    {"rank": 8, "team": "Sevilla FC", "biwenger_team_id": 5},
    {"rank": 15, "team": "Getafe CF", "biwenger_team_id": 7},
    {"rank": 19, "team": "Deportivo Alavés", "biwenger_team_id": 9},
]

# EL PARTIDO APLAZADO ESTA AQUI A PROPOSITO.
#
#     La jornada 9 se juega ANTES que la 8. Es lo que pasa de
#     verdad en esta liga: la jornada 6 tiene un partido el 3 de
#     septiembre, antes que toda la jornada 5.
PARTIDOS = [
    # Ya jugado: no puede salir como "proximo".
    {"matchday": 5, "home": "FC Barcelona", "away": "Sevilla FC",
     "kickoff": "2026-09-11T21:00:00+00:00"},

    {"matchday": 8, "home": "FC Barcelona", "away": "Real Madrid",
     "kickoff": "2026-10-09T21:00:00+00:00"},

    # APLAZADO: jornada 9, pero se juega antes que la 8.
    {"matchday": 9, "home": "Getafe CF", "away": "FC Barcelona",
     "kickoff": "2026-09-20T17:00:00+00:00"},

    {"matchday": 10, "home": "FC Barcelona",
     "away": "Deportivo Alavés",
     "kickoff": "2026-10-25T17:00:00+00:00"},

    # Este entra en los tres primeros: es el que comprueba que
    # un rival sin casar sigue saliendo.
    {"matchday": 11, "home": "FC Barcelona", "away": "Sevilla FC",
     "kickoff": "2026-09-25T17:00:00+00:00"},
]

NUESTROS = [
    {"id": 1, "name": "Yamal", "position": 4, "points": 45,
     "team_id": 3},
    {"id": 2, "name": "Otro", "position": 2, "points": 10,
     "team_id": 3},
]


def _calendario(**cambios):
    from src.analysis.el_calendario import el_calendario

    argumentos = {
        "calendario": {
            "matches": PARTIDOS,
            "fetched_at": "2026-09-13T21:20:59+02:00",
        },
        "clasificacion": CLASIFICACION,
        "nuestros": NUESTROS,
        "ahora": AHORA,
    }

    argumentos.update(cambios)

    return el_calendario(**argumentos)


def test_el_calendario_no_inventa_rivales() -> None:
    """
    TODOS LOS NOMBRES DEL CALENDARIO CASAN CON LA CLASIFICACION.

    Y si uno no casa, SE DICE: sale en `sin_casar`, el partido se
    pinta igual con el nombre del rival, y su puesto va a `None`
    en vez de a un numero inventado.
    """

    visto = _calendario()

    assert visto["available"] is True, visto

    # REGLA 24: sin equipos ni partidos esto no probaria nada.
    assert visto["equipos"], visto

    assert visto["partidos"] == len(PARTIDOS), visto

    # 1. HOY CASAN TODAS.
    assert visto["sin_casar"] == [], visto

    assert visto["casan_todas"] is True, visto

    assert "casan todas" in visto["reason"], visto["reason"]

    # 2. UNA QUE NO CASA SALE CON SU NOMBRE.
    sin_sevilla = _calendario(
        clasificacion=[
            r
            for r in CLASIFICACION
            if r["team"] != "Sevilla FC"
        ]
    )

    assert sin_sevilla["sin_casar"] == ["Sevilla FC"], (
        sin_sevilla["sin_casar"]
    )

    assert sin_sevilla["casan_todas"] is False, sin_sevilla

    assert "Sevilla FC" in sin_sevilla["reason"], (
        sin_sevilla["reason"]
    )

    # Y SU PARTIDO SIGUE AHI, sin puesto y sin color de bueno.
    equipo = sin_sevilla["equipos"][0]

    de_sevilla = [
        p
        for p in equipo["proximos"]
        if p["rival"] == "Sevilla FC"
    ]

    assert de_sevilla, [
        p["rival"] for p in equipo["proximos"]
    ]

    for p in de_sevilla:
        assert p["rival_puesto"] is None, p

        assert p["casa_con_la_clasificacion"] is False, p

        # SIN PUESTO NO SE SUPONE BLANDO. Un verde sin comprobar
        # se lee como una buena noticia.
        assert p["tramo"] == "sin dato", p

    # 3. SIN PARTIDOS, NO SE MONTA UN CUADRO VACIO.
    for vacio in (None, {}, {"matches": []}):

        hueco = _calendario(calendario=vacio)

        assert hueco["available"] is False, vacio

        assert hueco["equipos"] == [], vacio

        assert "partido" in (hueco["reason"] or ""), hueco

    # 4. SIN CLASIFICACION TAMPOCO SE ADIVINAN LOS PUESTOS.
    sin_tabla = _calendario(clasificacion=[])

    assert sin_tabla["available"] is False, sin_tabla

    assert "clasificación" in sin_tabla["reason"], sin_tabla


def test_los_proximos_son_por_reloj_y_no_por_jornada() -> None:
    """
    "PROXIMO" ES POR HORA DE COMIENZO, NO POR NUMERO DE JORNADA.

    SINTOMA QUE EVITA

        En esta liga hay partidos aplazados: la jornada 6 tiene
        uno el 3 de septiembre, antes que toda la jornada 5.
        Ordenando por numero de jornada, el cuadro pondria como
        "proximo" un partido que ya se jugo.

    En el fixture las jornadas 9 y 11 se juegan ANTES que la 8 y
    la 10. Y la 5 ya paso: no puede aparecer.
    """

    visto = _calendario()

    equipo = visto["equipos"][0]

    proximos = equipo["proximos"]

    # REGLA 24.
    assert len(proximos) == 3, proximos

    # 1. POR RELOJ, y no por numero de jornada.
    #
    #    9 (20/09) · 11 (25/09) · 8 (09/10). Por jornada saldria
    #    8, 9, 10 y el primero seria uno de dentro de un mes.
    assert [p["jornada"] for p in proximos] == [9, 11, 8], (
        [(p["jornada"], p["kickoff"]) for p in proximos]
    )

    # 2. LO YA JUGADO NO SALE. La 5 fue el 11/09.
    assert 5 not in [p["jornada"] for p in proximos], proximos

    # 3. CASA Y FUERA, BIEN PUESTOS.
    #
    #    En la 9 jugamos EN GETAFE; la 11 y la 8, en casa.
    assert proximos[0]["rival"] == "Getafe CF", proximos[0]
    assert proximos[0]["en_casa"] is False, proximos[0]

    assert proximos[1]["rival"] == "Sevilla FC", proximos[1]
    assert proximos[1]["en_casa"] is True, proximos[1]

    # 4. LA MEDIA: (15 + 8 + 2) / 3 = 8,3 -> tramo duro.
    assert equipo["media_del_rival"] == 8.3, equipo

    assert equipo["veredicto"] == "tramo duro", equipo


def test_el_veredicto_no_se_inventa_cuando_no_sabe() -> None:
    """
    SIN MEDIA NO SE DICE "NORMAL": SE DICE QUE NO SE SABE.

    Un veredicto por defecto es justo lo que absorbe el caso mas
    importante (regla 36): el equipo cuyos rivales no casan
    saldria como "normal" y se ordenaria entre los demas, en vez
    de destacar que de ese no se sabe nada.
    """

    from src.analysis.el_calendario import tramo_del_rival

    # 1. SIN PUESTO, "sin dato" Y NUNCA "blando".
    for sin_dato in (None, 0):
        assert tramo_del_rival(sin_dato) == "sin dato", sin_dato

    assert tramo_del_rival(1) == "duro"
    assert tramo_del_rival(6) == "duro"
    assert tramo_del_rival(7) == "normal"
    assert tramo_del_rival(13) == "normal"
    assert tramo_del_rival(14) == "blando"
    assert tramo_del_rival(20) == "blando"

    # 2. UN EQUIPO SIN NINGUN RIVAL CASADO NO TIENE VEREDICTO.
    ciego = _calendario(
        clasificacion=[
            r
            for r in CLASIFICACION
            if r["biwenger_team_id"] == 3
        ]
    )

    equipo = ciego["equipos"][0]

    assert equipo["media_del_rival"] is None, equipo

    assert equipo["veredicto"] == "sin dato", equipo

    # 3. Y SE ORDENA AL FINAL: "no se sabe" no es "es facil".
    assert ciego["equipos"][-1]["veredicto"] == "sin dato"

    # 4. LOS TRAMOS VIAJAN COMO NO MEDIDOS.
    assert _calendario()["tramos_sin_medir"] == {
        "duro_hasta": 6,
        "normal_hasta": 13,
    }

    fuente = (
        RAIZ / "src" / "analysis" / "el_calendario.py"
    ).read_text(encoding="utf-8")

    assert "SIN MEDIR" in fuente, (
        "el modulo no dice que el reparto de tramos no esta "
        "medido"
    )

    panel = (
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "ElCalendarioPanel.jsx"
    ).read_text(encoding="utf-8")

    assert "NO está medido" in panel, (
        "la pantalla no avisa de que el reparto no esta medido"
    )


def test_el_calendario_no_decide_nada() -> None:
    """
    Es para mirar. Ninguna puja ni ninguna venta salen de aqui, y
    el dia que alguien lo conecte esta guardia se pone roja y se
    habla antes.
    """

    import ast

    fuente = (
        RAIZ / "src" / "analysis" / "el_calendario.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
    } | {
        nodo.func.attr
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
    }

    for escribe in (
        "place_bid",
        "accept_offer",
        "list_player_for_sale",
        "abrir",
        "write_text",
    ):
        assert escribe not in llamadas, (
            f"el calendario llama a `{escribe}`"
        )

    for modulo in ("write_client", "executor", "autopilot"):
        assert modulo not in fuente, (
            f"el calendario importa `{modulo}`"
        )

    # Y ESTA MONTADO EN LA PAGINA, leyendo lo publicado.
    pagina = (
        RAIZ / "dashboard-v8" / "src" / "pages" / "BrainPage.jsx"
    ).read_text(encoding="utf-8")

    assert "<ElCalendarioPanel" in pagina, (
        "el calendario no esta montado en ESTRATEGIA"
    )

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"elCalendario"' in estado, (
        "la telemetria no publica el calendario"
    )


TESTS = [
    test_el_calendario_no_inventa_rivales,
    test_los_proximos_son_por_reloj_y_no_por_jornada,
    test_el_veredicto_no_se_inventa_cuando_no_sabe,
    test_el_calendario_no_decide_nada,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"EL CALENDARIO V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
