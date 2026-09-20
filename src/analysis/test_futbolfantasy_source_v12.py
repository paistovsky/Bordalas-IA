"""
Fija el bloque 1: FutbolFantasy como fuente unica.

QUE VIGILA Y POR QUE

    1. EL PARSER, contra HTML de verdad guardado en data/ff_html.
       No hay API: el dato viaja en atributos data-* de la pagina,
       asi que un rediseño de FF nos rompe el parser en silencio.
       Este test es la alarma. Si un dia baja la cobertura, salta
       aqui y no en una puja.

    2. LA JERARQUIA, escalon a escalon. 60 es Dios y 0 NO es
       Descarte: es "sin definir". Confundirlos seria inventarse
       el dato mas bajo para quien no tiene dato.

    3. LA IDENTIDAD, incluidos los que costaron sangre: Mbappe,
       Lo Celso, Aleña. Y los que NO deben emparejar: dos
       apellidos iguales de personas distintas.

    4. EL GUARDARRAIL, que es lo unico de aqui que mueve dinero:
       sin pronostico no se puja. Se comprueba que la ausencia de
       dato FRENA, no que deja pasar.

USO
    python -m src.analysis.test_futbolfantasy_source_v12
"""

from pathlib import Path

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA  (doctrina 104, 20/09/2026)
#
#     Medido: con `BORDALAS_SIN_REFERENCIA_ESCALA` puesto en el
#     entorno, esta guardia se caia — y una guardia roja para el
#     paso «Validate optimized production cycle», o sea para EL
#     CICLO. Es lo que paso la noche del 20/09 con
#     `BORDALAS_OBJETIVOS_EL_CATALOGO`.
#
#     Este caso mide el comportamiento POR DEFECTO, asi que el
#     interruptor se apaga aqui. El comportamiento con el puesto
#     lo mide su propia guardia, que lo enciende y lo apaga ella.
os.environ.pop("BORDALAS_SIN_REFERENCIA_ESCALA", None)

from src.analysis.candidate_starter_lookup import (
    build_starter_lookup,
)

from src.analysis.player_value_engine import (
    xi_upgrade_value,
)

from src.intelligence.futbolfantasy_provider import (
    HIERARCHY_LABELS,
    build_player_entry,
    match_team,
    parse_team_page,
    team_slug,
)


HTML_DIR = Path("data/ff_html")

MERCADO = {"rate_median": 22589}


EQUIPOS_LIGA = [
    "Alavés", "Athletic", "Atlético", "Barcelona", "Betis",
    "Celta", "Deportivo", "Elche", "Espanyol", "Getafe",
    "Levante", "Málaga", "Osasuna", "Racing", "Rayo Vallecano",
    "Real Madrid", "Real Sociedad", "Sevilla", "Valencia",
    "Villarreal",
]


def test_slugs():
    """
    Los veinte equipos del catalogo resuelven pagina.

    `Atletico` se quedaba fuera porque el diccionario decia
    "atletico madrid" y Biwenger dice "Atletico" a secas. Y el
    Rayo daba 404 con el slug `rayo`.
    """

    for equipo in EQUIPOS_LIGA:

        slug = team_slug(equipo)

        assert slug, f"{equipo} no resuelve slug de FutbolFantasy"

    assert team_slug("Atlético") == "atletico"
    assert team_slug("Rayo Vallecano") == "rayo-vallecano"


def test_jerarquia_completa():
    """
    La escala, entera, y el 0 fuera de ella.
    """

    assert HIERARCHY_LABELS[60] == "DIOS"
    assert HIERARCHY_LABELS[50] == "CLAVE"
    assert HIERARCHY_LABELS[40] == "IMPORTANTE"
    assert HIERARCHY_LABELS[30] == "ROTACION"
    assert HIERARCHY_LABELS[25] == "REVULSIVO"
    assert HIERARCHY_LABELS[20] == "RESERVA"
    assert HIERARCHY_LABELS[10] == "DESCARTE"

    # Sin definir no es el escalon de abajo: es ausencia de dato.
    assert 0 not in HIERARCHY_LABELS


def test_identidad():
    """
    Los nombres que costaron, y los que no deben cruzarse.
    """

    from src.intelligence.futbolfantasy_provider import _name_score

    def score(ff_nombre, biwenger):
        return _name_score(
            {"ff_name": ff_nombre, "ff_slug": None},
            {"name": biwenger, "slug": None},
        )

    # FF escribe el nombre completo; Biwenger el de camiseta.
    for ff_nombre, biwenger in (
        ("Kylian Mbappe", "Mbappé"),
        ("Giovani Lo Celso", "Lo Celso"),
        ("Carles Aleña", "Aleñá"),
        ("Federico Valverde", "Valverde"),
    ):
        assert score(ff_nombre, biwenger) >= 0.9, (
            f"{ff_nombre} deberia emparejar con {biwenger}"
        )

    # Apellido compartido no es identidad.
    for ff_nombre, biwenger in (
        ("Andres Garcia", "Pedro Garcia"),
        ("Marcos Alonso", "Alonso Perez"),
        ("Jonny Castro", "Castro Otto"),
    ):
        assert score(ff_nombre, biwenger) < 0.82, (
            f"{ff_nombre} NO deberia emparejar con {biwenger}"
        )


def test_lookup():
    """
    El tablero se traduce a lo que consume la valoracion.
    """

    tablero = {
        "players": [
            {
                "player_id": 7,
                "player_name": "Mbappé",
                "team": "Real Madrid",
                "scope": "MARKET",
                "starter_probability": 70.0,
                "consensus": "STARTER",
                "source": "FUTBOLFANTASY",
                "source_coverage": 1,
                "hierarchy": {
                    "value": 60,
                    "label": "Dios",
                    "franchise": True,
                },
                "availability": {
                    "code": 0,
                    "label": "DISPONIBLE",
                    "can_play": True,
                },
                "match": {"method": "NAME"},
            },
            {
                "player_id": 8,
                "player_name": "Sin jerarquia",
                "team": "Getafe",
                "scope": "ROSTER",
                "starter_probability": 0.0,
                "consensus": "BENCH",
                "source": "FUTBOLFANTASY",
                "source_coverage": 1,
                "hierarchy": None,
                "availability": {
                    "code": 50,
                    "label": "LESIONADO",
                    "can_play": False,
                },
                "match": {"method": "NAME"},
            },
        ]
    }

    lookup = build_starter_lookup(tablero)

    assert lookup[7]["probability"] == 70.0
    assert lookup[7]["franchise"] is True
    assert lookup[7]["hierarchy_value"] == 60
    assert lookup[7]["scope"] == "MARKET"

    # Un 0 % es un dato, no una ausencia. Si esto se rompe,
    # vuelve el "0/20 con pronostico" teniendo pronostico.
    assert 8 in lookup
    assert lookup[8]["probability"] == 0.0
    assert lookup[8]["hierarchy_value"] is None
    assert lookup[8]["can_play"] is False


def test_sin_pronostico_no_se_puja():
    """
    EL QUE MUEVE DINERO.

    Con el tablero vacio, la regla del once bloqueaba cero
    operaciones y el sistema proponia comprar a ciegas. Un
    guardarrail que cuanto menos sabe mas permite esta al reves.
    """

    def decision(candidato, sustituido):
        return xi_upgrade_value(
            candidate_points=120,
            replaced_points=20,
            points_market=MERCADO,
            candidate_starter=candidato,
            replaced_starter=sustituido,
        )

    # Sin dato de ninguno de los dos lados: se frena.
    assert decision(None, None)["decision"] == "SIN_PRONOSTICO"

    assert (
        decision({"probability": 70.0}, None)["decision"]
        == "SIN_PRONOSTICO"
    )

    assert (
        decision(None, {"probability": 70.0})["decision"]
        == "SIN_PRONOSTICO"
    )

    # Con dato de los dos, manda la regla del once.
    assert (
        decision(
            {"probability": 20.0},
            {"probability": 70.0},
        )["decision"]
        == "NO_MEJORA_TITULARIDAD"
    )

    # Y una mejora de verdad se valora.
    buena = decision(
        {"probability": 80.0},
        {"probability": 70.0},
    )

    assert buena.get("value", 0) > 0
    assert buena.get("intent") == "XI_UPGRADE"

    # Un 0 % del que sale es un dato: se puede sustituir.
    assert (
        decision(
            {"probability": 80.0},
            {"probability": 0.0},
        ).get("value", 0)
        > 0
    )


def test_jerarquia_en_los_puntos():
    """
    La base es estructural; el % solo ajusta.

    LO QUE ESTE TEST IMPIDE

        Contar dos veces lo mismo. Jerarquia y porcentaje van de
        la mano -un Clave ronda el 72 %, un Reserva el 14 %-, asi
        que multiplicar los dos factores castigaria al mismo
        jugador por partida doble. El % solo aporta su desviacion
        respecto a lo normal en su escalon.
    """

    from src.analysis.player_value_engine import (
        expected_points_factor,
    )

    def senal(probabilidad, valor, etiqueta):
        return {
            "probability": probabilidad,
            "hierarchy_value": valor,
            "hierarchy_label": etiqueta,
        }

    # Un Clave en su probabilidad tipica no mueve la base.
    factor, _ = expected_points_factor(senal(71.7, 50, "Clave"))
    assert abs(factor - 1.0) < 0.01, factor

    # Por debajo de lo suyo, baja.
    abajo, _ = expected_points_factor(senal(0.0, 50, "Clave"))

    assert abajo < 1.0, abajo

    # Por encima de lo suyo NO sube del historico: decision del
    # dueño el 17/08/2026. Los puntos de la temporada pasada son
    # el tope. Se paga mejor, no se paga de mas.
    arriba, _ = expected_points_factor(senal(90.0, 50, "Clave"))

    assert arriba == 1.0, arriba

    tope, _ = expected_points_factor(senal(100.0, 60, "Dios"))

    assert tope == 1.0, tope

    # Un Reserva con una semana buena NO se convierte en titular.
    reserva, _ = expected_points_factor(senal(70.0, 20, "Reserva"))

    assert reserva < 0.4, reserva

    # El orden de los escalones se respeta cuando cada uno esta en
    # SU probabilidad normal. Ahi manda la base estructural.
    from src.analysis.player_value_engine import (
        HIERARCHY_TYPICAL_PROBABILITY,
    )

    anterior = None

    for valor, etiqueta in (
        (50, "Clave"),
        (40, "Importante"),
        (30, "Rotacion"),
        (25, "Revulsivo"),
        (20, "Reserva"),
        (10, "Descarte"),
    ):
        factor, _ = expected_points_factor(
            senal(
                HIERARCHY_TYPICAL_PROBABILITY[valor],
                valor,
                etiqueta,
            )
        )

        if anterior is not None:
            assert factor < anterior, (etiqueta, factor, anterior)

        anterior = factor

    # A UNA MISMA probabilidad los dos escalones vecinos quedan muy
    # juntos: un Clave al 50 % esta mas lejos de lo suyo (72 %) que
    # un Importante al 50 % de lo suyo (66 %), asi que la ventaja
    # estructural del Clave casi se le consume.
    #
    # Con el peso semanal en 0,5 llegaban a cruzarse. Con 0,15 ya
    # no, pero la distancia sigue siendo minima, y eso es lo que
    # importa: el porcentaje de una jornada no puede dar la vuelta
    # a lo que un jugador es.
    clave_50, _ = expected_points_factor(senal(50.0, 50, "Clave"))
    imp_50, _ = expected_points_factor(senal(50.0, 40, "Importante"))

    assert abs(clave_50 - imp_50) < 0.05, (clave_50, imp_50)

    # Sin jerarquia no se rompe: se cae al comportamiento viejo.
    sin_jerarquia, motivo = expected_points_factor(
        senal(70.0, None, None)
    )

    assert 0 < sin_jerarquia <= 1.0
    assert "sin jerarquia" in motivo


def test_veto_estructural():
    """
    Se veta bajar dos escalones, no que un % cruce el 67.
    """

    def senal(probabilidad, valor, etiqueta):
        return {
            "probability": probabilidad,
            "hierarchy_value": valor,
            "hierarchy_label": etiqueta,
        }

    def decision(candidato, sustituido):
        return xi_upgrade_value(
            candidate_points=120,
            replaced_points=20,
            points_market=MERCADO,
            candidate_starter=candidato,
            replaced_starter=sustituido,
        )

    clave = senal(70.0, 50, "Clave")

    # Dos escalones o mas: fuera.
    assert (
        decision(senal(70.0, 25, "Revulsivo"), clave)["decision"]
        == "NO_MEJORA_JERARQUIA"
    )

    assert (
        decision(senal(70.0, 30, "Rotacion"), clave)["decision"]
        == "NO_MEJORA_JERARQUIA"
    )

    # Un escalon: se permite y se valora.
    assert (
        decision(senal(70.0, 40, "Importante"), clave).get("value", 0)
        > 0
    )

    # Lo que ya no debe pasar: vetar porque el % bajo de 67 a 63
    # entre dos jugadores del mismo escalon.
    assert (
        decision(senal(63.0, 50, "Clave"), clave).get("value", 0) > 0
    )

    # Pero un suplente claro sigue frenado, aunque sea Clave.
    assert (
        decision(senal(20.0, 50, "Clave"), clave)["decision"]
        == "NO_MEJORA_TITULARIDAD"
    )

    # Y subir de escalon es justo lo que queremos que ocurra.
    assert (
        decision(
            senal(80.0, 50, "Clave"),
            senal(30.0, 20, "Reserva"),
        ).get("value", 0)
        > 0
    )


def test_lesion_y_sancion_no_se_pisan():
    """
    Un cruzado y dos partidos de sancion no son la misma baja.

    EL CASO (19/08/2026)

        FutbolFantasy nos daba, y nosotros recogiamos, el tipo de
        lesion, el pronostico en palabras, si la roja fue directa
        o por acumulacion y cuantos partidos van cumplidos.

        `merge_absences` se quedaba con la ausencia mas larga y
        de la otra guardaba `also` con el tipo a secas. Asi que de
        un jugador con el ligamento roto Y sancionado sobrevivia
        "SUSPENSION" y se perdia todo lo demas.

        Importa porque se decide distinto con cada una: una lesion
        larga es motivo de venta, una sancion de dos partidos no
        lo es. Fundirlas en un campo obligaba a tratarlas igual.
    """

    from src.intelligence.futbolfantasy_absences import (
        merge_absences,
    )

    lesiones = {
        "roto": {
            "type": "INJURY",
            "detail": "Rotura del ligamento cruzado",
            "matchdays_out": 20,
            "prognosis": "6 meses",
            "severity_label": "GRAVE",
        },
    }

    sanciones = {
        "roto": {
            "type": "SUSPENSION",
            "detail": "Roja directa (0/2)",
            "matches_total": 2,
            "matches_served": 0,
            "matchdays_out": 2,
        },
        "solo_sancion": {
            "type": "SUSPENSION",
            "detail": "Acumulación de amarillas (0/1)",
            "matchdays_out": 1,
        },
    }

    todas = merge_absences(lesiones, sanciones)

    roto = todas["roto"]

    # Manda la mas larga, como siempre.
    assert roto["type"] == "INJURY"
    assert roto["matchdays_out"] == 20

    # Pero la otra ya no se pierde, y con su detalle entero.
    assert roto["injury"]["detail"] == (
        "Rotura del ligamento cruzado"
    )
    assert roto["injury"]["prognosis"] == "6 meses"

    assert roto["suspension"]["detail"] == "Roja directa (0/2)", (
        "la sancion vuelve a perderse cuando hay una lesion mas "
        "larga: en pantalla saldra la casilla vacia"
    )
    assert roto["suspension"]["matches_total"] == 2

    # Quien solo tiene una, solo tiene una. Sin inventar la otra.
    solo = todas["solo_sancion"]

    assert solo.get("injury") is None
    assert solo["suspension"]["matchdays_out"] == 1

    # Y el orden de los factores no altera el resultado: FF puede
    # devolver las paginas en cualquier orden.
    al_reves = merge_absences(sanciones, lesiones)

    assert al_reves["roto"]["injury"]["prognosis"] == "6 meses"
    assert (
        al_reves["roto"]["suspension"]["detail"]
        == "Roja directa (0/2)"
    )


def test_a_quien_se_conserva():
    """
    Un Dios roto hasta marzo se suelta antes que un Clave sano.

    EL FALLO QUE ARREGLA

        El orden de permanencia terminaba en "el mas caro se
        conserva". El precio va justo al reves de lo que hace
        falta cuando alguien se rompe: quien se parte el cruzado
        en agosto valdra mucho menos en octubre, y era a quien el
        guardarrail agarraba con mas fuerza.

        Y un Dios de baja una semana y otro de baja hasta enero
        eran, para esta lista, el mismo jugador.
    """

    from src.analysis.position_guardrail import (
        _keep_priority,
        _keep_value,
    )

    # Sin señal se comporta como antes: manda el precio.
    assert _keep_value({"id": 1, "price": 10_000_000}) == 10_000_000

    # Con señal, la baja descuenta.
    sano = _keep_value(
        {"id": 1, "price": 25_440_000, "keep_factor": 1.0}
    )

    roto = _keep_value(
        {"id": 1, "price": 25_440_000, "keep_factor": 0.24}
    )

    assert roto < sano

    # Y el orden se da la vuelta frente a uno mas barato pero sano.
    plantel = [
        {
            "id": 1,
            "price": 25_440_000,
            "keep_factor": 0.24,
            "in_lineup": False,
        },
        {
            "id": 2,
            "price": 10_000_000,
            "keep_factor": 1.0,
            "in_lineup": False,
        },
    ]

    orden = sorted(plantel, key=_keep_priority)

    assert orden[0]["id"] == 2, (
        "el Clave sano tiene que conservarse antes que el Dios roto"
    )

    # Estar en el once sigue mandando por encima de todo: si juega,
    # es que puede jugar.
    plantel[0]["in_lineup"] = True

    assert sorted(plantel, key=_keep_priority)[0]["id"] == 1


def test_rival_y_previsibilidad():
    """
    El rival de la jornada y lo fiable que es cada pronostico.

    LA TRAMPA QUE EVITA

        La previsibilidad de TEMPORADA seria mejor multiplicador
        -es estable- pero el 17/08/2026 solo 7 equipos de 18
        tenian valor y los otros 11 marcaban 0,0. Ese 0 no es
        "impredecible": es que aun no hay historial.

        Usarlo habria castigado a once equipos por un dato que no
        existe. Mismo error que tratar `hierarchy = 0` como
        Descarte.
    """

    from src.analysis.player_value_engine import (
        expected_points_factor,
        fixture_factor,
        predictability_confidence,
    )

    def senal(dificultad=None, previsibilidad=None, escalon=30):
        valor = {
            "probability": 43.4,
            "hierarchy_value": escalon,
            "hierarchy_label": "Rotacion",
            "matchday": 2,
        }

        if dificultad:
            valor["next_match"] = {
                "difficulty": dificultad,
                "rival": "RIV",
            }

        if previsibilidad is not None:
            valor["team_context"] = {
                "predictability": previsibilidad,
            }

        return valor

    # La escala es simetrica y el 3 no mueve nada.
    neutro, _ = fixture_factor(senal(dificultad=3))

    assert abs(neutro - 1.0) < 1e-9, neutro

    facil, _ = fixture_factor(senal(dificultad=1))
    duro, _ = fixture_factor(senal(dificultad=5))

    assert facil > 1.0 > duro, (facil, duro)
    assert abs((facil - 1.0) + (duro - 1.0)) < 1e-9, (facil, duro)

    # Un indice que no existe no inventa factor.
    assert fixture_factor(senal(dificultad=9)) == (None, None)
    assert fixture_factor(senal()) == (None, None)

    # Y en los puntos se nota, pero poco: es un partido de 38.
    con_facil, _ = expected_points_factor(senal(dificultad=1))
    con_duro, _ = expected_points_factor(senal(dificultad=5))

    assert con_facil > con_duro
    assert (con_facil / con_duro) < 1.25, con_facil / con_duro

    # ------------------------------------------------------
    # LA FIABILIDAD
    # ------------------------------------------------------

    for valor, esperado in ((40.0, 0.85), (60.0, 0.925), (80.0, 1.0)):

        factor, _ = predictability_confidence(
            senal(previsibilidad=valor)
        )

        assert abs(factor - esperado) < 1e-6, (valor, factor)

    # EL CANDADO: sin dato no se penaliza. Un 0 de FF significa
    # "aun no hay historial", no "impredecible".
    assert predictability_confidence(
        senal(previsibilidad=0.0)
    ) == (None, None)

    assert predictability_confidence(senal()) == (None, None)

    assert predictability_confidence({}) == (None, None)


def test_se_puede_comprar_con_saldo_negativo():
    """
    La compra no se bloquea por deber dinero.

    POR QUE

        Habia un `balance >= 0` delante de todo el bloque de
        compra. Con el saldo en -264.032 EUR, el ciclo del
        17/08/2026 tenia tres objetivos marcados PUJAR en el
        tablero y no ejecutaba ninguno: ni siquiera llegaba a
        mirarlos.

        No era una proteccion, era una puerta vieja. El sistema de
        deuda segura que vino despues ya decide esto mucho mejor,
        y esta en la MISMA condicion: con saldo negativo,
        `budget["enabled"]` exige garantia de solvencia, ventana
        de calendario abierta y margen de deuda positivo.

        El freno pasa de "¿tienes dinero?" a "¿puedes devolverlo y
        te da tiempo a venderlo?".

    QUE VIGILA ESTE TEST

        Que nadie vuelva a poner la puerta. Se mira el arbol del
        codigo, no el texto: se busca el `if` que autoriza la
        compra y se comprueba que no compara el saldo.
    """

    import ast
    import inspect

    from src.analysis import decision_orchestrator

    arbol = ast.parse(inspect.getsource(decision_orchestrator))

    guardas = []

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.If):
            continue

        cuerpo = " ".join(ast.dump(hijo) for hijo in nodo.body)

        # El bloque que crea la accion de compra.
        if "SPECULATION_BUY" not in cuerpo:
            continue

        if "BUY_SPECULATION" not in cuerpo:
            continue

        guardas.append(ast.dump(nodo.test))

    assert guardas, (
        "no se encuentra el bloque que autoriza la compra"
    )

    for guarda in guardas:

        assert "balance" not in guarda, (
            "la compra ha vuelto a bloquearse por saldo negativo. "
            "Quien decide con deuda es el presupuesto de "
            "especulacion, que mira garantia, ventana de "
            "calendario y margen: no la caja."
        )

        # Y que el presupuesto siga siendo condicion. Si esto
        # desaparece, se compra sin ningun freno.
        assert "enabled" in guarda, (
            "el presupuesto ha dejado de ser condicion para "
            "comprar: eso si seria quitar la red"
        )


def test_la_jerarquia_decide_el_once():
    """
    Un Dios con dudas juega. Un Revulsivo confirmado, no.

    EL CASO QUE LO DESTAPO

        18/08/2026. Yamal -Dios del Barcelona, 60 % de titular
        en FF, sano- se cayo del once, y entraba en su sitio
        cualquier titular confirmado.

        El motor ya leia FF -eso se migro el 17- pero ordenaba
        por la ETIQUETA del consenso, que sale de un corte seco
        en el 67 %. Yamal al 60 % era UNCERTAIN y valia tres
        escalones; un Revulsivo al 70 % era STARTER y valia
        cinco. La jerarquia llegaba hasta el motor y no puntuaba.

        "Hay que ponerlo en el XI aunque vaya a jugar unos
        minutos solo."

    QUE SE COMPRUEBA

        Que el orden del once ya no lo decide el corte del 67 %,
        sino jerarquia y porcentaje juntos: un Dios al 60 % vale
        mas que un Revulsivo al 70 %, y un Reserva no se cuela
        por marcar un buen porcentaje puntual.

        Y que la jerarquia no lo tapa todo: por debajo de Clave,
        el porcentaje sigue mandando.
    """

    from src.analysis.lineup_engine import weekly_expected_value

    dios_dudoso = weekly_expected_value(60, 60.0)
    revulsivo_titular = weekly_expected_value(25, 70.0)

    assert dios_dudoso > revulsivo_titular, (
        f"Yamal otra vez fuera: Dios al 60 % vale "
        f"{dios_dudoso:.3f} y Revulsivo al 70 % "
        f"{revulsivo_titular:.3f}"
    )

    # El caso de Hugo Rincon, por el otro lado.
    reserva = weekly_expected_value(20, 40.0)
    importante = weekly_expected_value(40, 70.0)

    assert reserva < importante

    # Y el freno: la jerarquia no es un salvoconducto. Un
    # Importante al que FF no da de titular pierde contra un
    # Rotacion confirmado.
    importante_suplente = weekly_expected_value(40, 40.0)
    rotacion_titular = weekly_expected_value(30, 90.0)

    assert importante_suplente < rotacion_titular, (
        "la jerarquia se ha comido al porcentaje"
    )

    # Sin jerarquia no se asume la peor: se ordena por el
    # porcentaje, que es lo unico que se sabe.
    assert (
        weekly_expected_value(None, 90.0)
        >
        weekly_expected_value(None, 20.0)
    )

    # Sin porcentaje no hay valor que inventar.
    assert weekly_expected_value(60, None) == 0.0

    # Y que el motor lo use de verdad, no solo lo calcule.
    import ast
    import inspect

    from src.analysis import lineup_engine

    fuente = inspect.getsource(lineup_engine.prepare_players)

    assert "weekly_expected_value(" in fuente, (
        "el once ha vuelto a ordenarse sin la jerarquia"
    )

    arbol = ast.parse(fuente)

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Name):
            continue

        assert nodo.id != "starter_tier", (
            "ha vuelto el ranking por clase de consenso, que es "
            "lo que saco a Yamal del once"
        )


def _plantilla_de_prueba(fichas):
    """
    Un snapshot minimo y su tablero, para probar el once sin red.

    `fichas` es una lista de (id, nombre, posicion, status,
    probabilidad, jerarquia, disponibilidad).
    """

    equipo = []
    tablero = []

    for (
        pid,
        nombre,
        posicion,
        status,
        probabilidad,
        jerarquia,
        disponibilidad,
    ) in fichas:

        equipo.append(
            {
                "id": pid,
                "name": nombre,
                "position": posicion,
                "price": 1_000_000,
                "pointsLastSeason": 50,
                "status": status,
                "fitness": [],
            }
        )

        tablero.append(
            {
                "player_id": pid,
                "player_name": nombre,
                "starter_probability": probabilidad,
                "source_coverage": 1,
                "consensus": (
                    "STARTER"
                    if (probabilidad or 0) >= 67
                    else "BENCH"
                ),
                "hierarchy": jerarquia,
                "availability": disponibilidad,
            }
        )

    snapshot = {
        "my_team": equipo,
        "team": {},
        "players": [],
    }

    board = {
        "version": "TEST",
        "source": "FUTBOLFANTASY",
        "players": tablero,
    }

    return snapshot, board


def test_un_dios_juega_siempre():
    """
    Un Dios entra en el once salvo 0 % con motivo.

    LA REGLA (decision del dueño, 18/08/2026)

        "Para elegir el XI, hay que hacer que los jerarquia DIOS
        jueguen siempre salvo caso de titularidad 0 % asegurada
        -lesion, sancion u otro motivo-."

    POR QUE NO BASTABA CON EL VALOR SEMANAL

        Esa misma mañana se hizo que la jerarquia puntuase, y con
        eso Yamal al 60 % ya ganaba a un Revulsivo al 70 %. Pero
        seguia siendo una competicion: un Dios al 20 % perdia
        contra medio equipo, y bastaba con dos Claves al 90 % en
        su linea para devolverlo al banquillo.

        El dueño no quiere que compita: quiere que juegue.

    LO QUE NO CAMBIA

        La disponibilidad manda. Un Dios que no se puede alinear
        no se alinea, y ahi no hay bono que valga.

    Y EL 0 % TIENE QUE ESTAR MOTIVADO

        "Asegurada" es la palabra. Un 0 % sin lesion, sancion ni
        parte de baja es un dato raro, no una baja: el Dios juega
        igual y el ciclo lo canta.
    """

    from src.analysis.lineup_engine import (
        god_is_ruled_out,
        prepare_players,
    )

    DIOS = {"value": 60, "label": "Dios", "franchise": True}
    CLAVE = {"value": 50, "label": "Clave"}

    SANO = {
        "code": 0,
        "label": "DISPONIBLE",
        "can_play": True,
        "sanctioned": False,
    }

    LESIONADO = {
        "code": 50,
        "label": "LESIONADO",
        "can_play": False,
        "sanctioned": False,
    }

    SANCIONADO = {
        "code": 100,
        "label": "SANCIONADO",
        "can_play": False,
        "sanctioned": True,
    }

    # 1. Un Dios hundido gana a dos Claves confirmados.
    snapshot, board = _plantilla_de_prueba(
        [
            (1, "Dios hundido", 4, "ok", 20.0, DIOS, SANO),
            (2, "Clave A", 4, "ok", 90.0, CLAVE, SANO),
            (3, "Clave B", 4, "ok", 95.0, CLAVE, SANO),
        ]
    )

    fichas = {
        p["id"]: p
        for p in prepare_players(snapshot, {"lookup": {}}, board)
    }

    assert (
        fichas[1]["lineup_score"]
        >
        max(
            fichas[2]["lineup_score"],
            fichas[3]["lineup_score"],
        )
    ), "un Dios sano ha vuelto a competir por su sitio"

    assert fichas[1]["mandatory_hierarchy"] is True
    assert fichas[2]["mandatory_hierarchy"] is False

    # 2. El 0 % motivado si lo sienta.
    for disponibilidad, motivo in (
        (LESIONADO, "LESIONADO"),
        (SANCIONADO, "SANCIONADO"),
    ):

        sentado, razon = god_is_ruled_out(
            {
                "starter_probability": 0.0,
                "availability": disponibilidad,
            }
        )

        assert sentado, f"un Dios {motivo} deberia sentarse"
        assert razon

    # Y un parte de baja con jornadas, aunque FF no marque nada.
    sentado, razon = god_is_ruled_out(
        {
            "starter_probability": 0.0,
            "availability": SANO,
            "absence": {
                "matchdays_out": 6,
                "reason": "Rotura fibrilar",
            },
        }
    )

    assert sentado and razon

    # 3. El 0 % SIN motivo no lo sienta: juega y se canta.
    sentado, razon = god_is_ruled_out(
        {
            "starter_probability": 0.0,
            "availability": SANO,
        }
    )

    assert not sentado, (
        "un 0 % suelto no es una baja: ausencia de dato no es dato"
    )
    assert razon is None

    snapshot, board = _plantilla_de_prueba(
        [
            (1, "Dios raro", 4, "ok", 0.0, DIOS, SANO),
            (2, "Clave A", 4, "ok", 90.0, CLAVE, SANO),
        ]
    )

    fichas = {
        p["id"]: p
        for p in prepare_players(snapshot, {"lookup": {}}, board)
    }

    assert fichas[1]["mandatory_hierarchy"] is True
    assert fichas[1]["mandatory_hierarchy_unexplained"] is True

    assert (
        fichas[1]["lineup_score"]
        >
        fichas[2]["lineup_score"]
    )

    # 4. Pero la disponibilidad manda: un Dios que Biwenger no
    #    deja alinear no se alinea, con bono o sin el.
    snapshot, board = _plantilla_de_prueba(
        [
            (1, "Dios roto", 4, "injured", 0.0, DIOS, LESIONADO),
            (2, "Clave A", 4, "ok", 90.0, CLAVE, SANO),
        ]
    )

    fichas = {
        p["id"]: p
        for p in prepare_players(snapshot, {"lookup": {}}, board)
    }

    assert fichas[1]["lineup_score"] < 0, (
        "un Dios lesionado se ha colado en el once"
    )

    assert fichas[1]["mandatory_hierarchy"] is False
    assert fichas[1]["mandatory_hierarchy_ruled_out"] is True
    assert fichas[1]["mandatory_hierarchy_reason"]

    # 5. El bono elige, no valora.
    #
    #    Si los diez millones se colasen en el valor deportivo
    #    del once, el total se inflaria y todo lo demas se
    #    volveria barato en comparacion: vender un Clave costaria
    #    la mitad de porcentaje solo por tener un Dios en
    #    plantilla, y `safe_debt_portfolio_engine` -que decide a
    #    quien se puede soltar mirando ese porcentaje- se
    #    volveria mas permisivo sin que nadie lo hubiese
    #    decidido.
    from src.analysis.lineup_engine import (
        MANDATORY_HIERARCHY_BONUS,
    )

    snapshot, board = _plantilla_de_prueba(
        [
            (1, "Dios hundido", 4, "ok", 20.0, DIOS, SANO),
            (2, "Clave A", 4, "ok", 90.0, CLAVE, SANO),
        ]
    )

    fichas = {
        p["id"]: p
        for p in prepare_players(snapshot, {"lookup": {}}, board)
    }

    assert (
        fichas[1]["lineup_score"]
        -
        fichas[1]["lineup_score_sporting"]
        ==
        MANDATORY_HIERARCHY_BONUS
    )

    # Y el que no es Dios no lleva dos varas distintas.
    assert (
        fichas[2]["lineup_score"]
        ==
        fichas[2]["lineup_score_sporting"]
    )

    # Y que el once publique el valor deportivo, no el de la
    # busqueda: es el numero que leen el motor de solvencia y el
    # de ofertas, y tiene que seguir significando lo mismo que
    # antes de existir el bono.
    import inspect

    from src.analysis import lineup_engine

    fuente = inspect.getsource(lineup_engine.build_lineup)

    assert "lineup_score_sporting" in fuente, (
        "build_lineup ha vuelto a publicar el score con el bono "
        "dentro: eso infla el once y abarata cualquier venta"
    )


def main():

    pruebas = [
        test_slugs,
        test_jerarquia_completa,
        test_identidad,
        test_lookup,
        test_sin_pronostico_no_se_puja,
        test_jerarquia_en_los_puntos,
        test_veto_estructural,
        test_lesion_y_sancion_no_se_pisan,
        test_a_quien_se_conserva,
        test_rival_y_previsibilidad,
        test_se_puede_comprar_con_saldo_negativo,
        test_la_jerarquia_decide_el_once,
        test_un_dios_juega_siempre,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("FutbolFantasy v12: todo en verde.")


if __name__ == "__main__":
    main()
