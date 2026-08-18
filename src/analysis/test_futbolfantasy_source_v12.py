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


def test_parser_sobre_html_real():
    """
    Cobertura medida, no prometida.

    Referencia del 17/08/2026: 18 paginas, 464 jugadores, ni uno
    sin probabilidad. Los margenes van holgados a proposito -las
    plantillas cambian- pero un desplome se ve.
    """

    # Solo paginas de EQUIPO. En la misma carpeta viven ahora
    # lesionados.html y sancionados.html, que tienen otra
    # estructura y otro parser.
    slugs_equipo = {
        team_slug(equipo)
        for equipo in EQUIPOS_LIGA
        if team_slug(equipo)
    }

    ficheros = sorted(
        fichero
        for fichero in HTML_DIR.glob("*.html")
        if fichero.stem in slugs_equipo
    )

    if not ficheros:
        print(
            "    (sin HTML en data/ff_html: corre "
            "scripts/dump_ff_team_html.py)"
        )
        return

    total = 0
    sin_probabilidad = 0
    etiquetas = set()

    for fichero in ficheros:

        pagina = parse_team_page(
            fichero.read_text(encoding="utf-8")
        )

        jugadores = pagina["players"]

        # Una plantilla de LaLiga no baja de 18 fichas. Si el
        # parser saca menos, no es que el equipo tenga poca gente.
        assert len(jugadores) >= 18, (
            f"{fichero.name}: solo {len(jugadores)} jugadores"
        )

        total += len(jugadores)

        for jugador in jugadores:

            if jugador["probability"] is None:
                sin_probabilidad += 1

            if jugador["hierarchy_label"]:
                etiquetas.add(jugador["hierarchy_label"].upper())

        # El equipo tambien trae contexto.
        assert pagina["team"]["coach"], (
            f"{fichero.name}: sin entrenador"
        )

    assert total >= 350, f"solo {total} jugadores en total"

    assert sin_probabilidad == 0, (
        f"{sin_probabilidad} jugadores sin probabilidad"
    )

    # Que aparezcan varios escalones distintos: si un cambio de
    # DOM dejase la jerarquia en blanco, esto lo caza.
    assert len(etiquetas) >= 5, f"solo {etiquetas}"


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


def test_identidad_por_equipo():
    """
    El emparejamiento ocurre dentro de una plantilla, y el margen
    sobre el segundo es lo que sostiene la identidad.
    """

    fichero = HTML_DIR / "alaves.html"

    if not fichero.exists():
        print("    (sin alaves.html: me lo salto)")
        return

    pagina = parse_team_page(fichero.read_text(encoding="utf-8"))

    objetivos = [
        {
            "id": 1, "name": "Tenaglia", "slug": "nahuel-tenaglia",
            "team": "Alavés", "price": 3390000, "scope": "MARKET",
        },
        {
            "id": 2, "name": "Sivera", "slug": "antonio-sivera",
            "team": "Alavés", "price": 4060000, "scope": "ROSTER",
        },
        {
            "id": 3, "name": "Facundo Garcés",
            "slug": "facundo-garces",
            "team": "Alavés", "price": 150000, "scope": "MARKET",
        },
    ]

    emparejados = match_team(pagina["players"], objetivos)

    assert len(emparejados) == len(objetivos), (
        f"solo {len(emparejados)} de {len(objetivos)}"
    )

    for match in emparejados:

        entrada = build_player_entry(
            match,
            pagina["team"],
            "Alavés",
        )

        assert entrada["match"]["confidence"] == "ALTA", (
            f"{entrada['player_name']} salio "
            f"{entrada['match']['confidence']}"
        )

        assert entrada["starter_probability"] is not None

    # Garces es el caso de estado fisico: FF sabe que no esta
    # disponible; Biwenger solo dice que no juega.
    garces = [
        build_player_entry(m, pagina["team"], "Alavés")
        for m in emparejados
        if m["target"]["id"] == 3
    ][0]

    assert garces["availability"]["label"] == "NO_DISPONIBLE"
    assert garces["availability"]["can_play"] is False


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


def test_partes_de_baja():
    """
    Una gripe y un cruzado dejan de ser el mismo 0 %.

    Contra el HTML real de /laliga/lesionados y /laliga/sancionados.
    """

    import json
    from datetime import datetime, timezone

    from src.analysis.player_value_engine import (
        expected_points_factor,
    )

    from src.intelligence import futbolfantasy_absences as bajas

    lesionados_html = HTML_DIR / "lesionados.html"

    if not lesionados_html.exists():
        print(
            "    (sin lesionados.html: corre "
            "scripts/dump_ff_team_html.py)"
        )
        return

    calendario = json.loads(
        bajas.CALENDAR_FILE.read_text(encoding="utf-8")
    )

    fechas = bajas.matchday_dates(calendario)

    assert len(fechas) >= 30, len(fechas)

    partes = bajas.parse_injuries(
        lesionados_html.read_text(encoding="utf-8"),
        current_matchday=2,
        fechas=fechas,
        today=datetime(2026, 8, 17, tzinfo=timezone.utc),
    )

    assert len(partes) >= 20, len(partes)

    # Una baja larga tiene que salir larga.
    largas = [
        p
        for p in partes.values()
        if (p.get("matchdays_out") or 0) >= 10
    ]

    assert largas, "ninguna baja larga detectada"

    # Y una duda no es una baja.
    #
    # OJO: manda el TEXTO, no la clase de gravedad. FF mete en
    # `gravedad-1` tanto "Duda para la jornada 2" como "Baja hasta
    # finales de agosto", que son cosas distintas -uno puede jugar
    # el sabado y el otro no-. Si algun dia se prefiere la clase
    # al texto, este test lo cazara.
    dudas = [
        p
        for p in partes.values()
        if str(p.get("prognosis") or "").lower().startswith("duda")
    ]

    assert dudas, "ninguna duda leida"

    for parte in dudas:
        assert parte["matchdays_out"] == 0, parte

    # Y al reves: una baja que aun no ha terminado nunca sale como
    # cero, aunque FF la haya etiquetado como duda.
    #
    # Se comparan contra la jornada 2, que es la del fixture. Una
    # "baja confirmada para la jornada 1" ya se cumplio y vale
    # cero: eso es correcto, no un fallo.
    pendientes = [
        p
        for p in partes.values()
        if str(p.get("prognosis") or "").lower().startswith("baja")
        and p.get("basis") in ("FECHA", "JORNADA")
        and (p.get("return_matchday") or 0) > 2
    ]

    assert pendientes, "ninguna baja pendiente"

    for parte in pendientes:
        assert (parte.get("matchdays_out") or 0) >= 1, parte

    # Ante una horquilla -"hasta octubre-noviembre"- se coge el
    # mes tardio. Acortar una baja infla el valor del jugador.
    horquillas = [
        p
        for p in partes.values()
        if "-" in str(p.get("prognosis") or "")
        and p.get("matchdays_out")
    ]

    for parte in horquillas:
        assert parte["basis"] == "FECHA", parte

    # "Baja indefinida" se marca distinto de "no lo he entendido".
    indefinidas = [
        p
        for p in partes.values()
        if p.get("basis") == "INDEFINIDA"
    ]

    for parte in indefinidas:
        assert parte["matchdays_out"] is None

    sanciones_html = HTML_DIR / "sancionados.html"

    if sanciones_html.exists():

        sanciones = bajas.parse_suspensions(
            sanciones_html.read_text(encoding="utf-8")
        )

        assert sanciones, "ninguna sancion leida"

        for parte in sanciones.values():
            assert parte["matchdays_out"] is not None

    # ------------------------------------------------------
    # Y LO QUE IMPORTA: QUE MUEVA EL VALOR
    # ------------------------------------------------------

    def dios(ausencia):
        return {
            "probability": 0.0,
            "hierarchy_value": 60,
            "hierarchy_label": "Dios",
            "matchday": 2,
            "absence": ausencia,
        }

    corta, _ = expected_points_factor(
        dios({"matchdays_out": 1, "basis": "JORNADA"})
    )

    media, _ = expected_points_factor(
        dios({"matchdays_out": 6, "basis": "FECHA"})
    )

    larga, _ = expected_points_factor(
        dios({"matchdays_out": 18, "basis": "FECHA"})
    )

    assert corta > media > larga, (corta, media, larga)

    # Mes y medio fuera tiene que doler de verdad, y una jornada
    # poco.
    assert corta > 0.85, corta
    assert larga < 0.6, larga

    # Una baja indefinida no puede salir gratis.
    indefinida, _ = expected_points_factor(
        dios({"matchdays_out": None, "basis": "INDEFINIDA"})
    )

    assert indefinida < corta, (indefinida, corta)

    # ORDEN QUE PIDIO EL DUEÑO (17/08/2026)
    #
    # Una baja confirmada de una jornada nunca puede valer mas que
    # una simple duda, y cuantas mas jornadas se pierda, menos
    # vale. Con el peso semanal en 0,5 esto se incumplia: la duda
    # penalizaba mas que la baja.
    duda, _ = expected_points_factor(
        {
            "probability": 0.0,
            "hierarchy_value": 60,
            "hierarchy_label": "Dios",
            "matchday": 2,
        }
    )

    anterior = duda

    for jornadas in (1, 2, 3, 4, 6, 10, 18):

        factor, _ = expected_points_factor(
            dios({"matchdays_out": jornadas, "basis": "FECHA"})
        )

        assert factor <= anterior, (jornadas, factor, anterior)

        anterior = factor


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


def test_la_cache_comprueba_a_quien_cubre():
    """
    Una caché fresca que no cubre el mercado de hoy NO vale.

    EL FALLO QUE ARREGLA, VISTO EN EL PRIMER CICLO REAL

        17/08/2026, 20:25. El tablero de las 17:06 tenia hora y
        media de vida, la jornada correcta y 59 jugadores, asi que
        se sirvio como valido.

        Pero el mercado de Biwenger rota: de los 48 candidatos de
        ese momento, 19 no estaban en el tablero -Lunin, Tenaglia,
        Mendy, Diego Conde...-. Ninguno tenia pronostico y la
        cabecera cayo de 18/20 a 8/20 sin que nada fallase ni nadie
        se enterase.

        Mirar la edad y la jornada no bastaba. Hay que mirar a
        quien cubre.
    """

    import json
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path

    from src.intelligence import futbolfantasy_provider as ff

    if not (HTML_DIR / "alaves.html").exists():
        print("    (sin HTML de equipos: me lo salto)")
        return

    class RespuestaFalsa:
        def __init__(self, texto):
            self.text = texto

        def raise_for_status(self):
            return None

    class SesionDeDisco:
        """
        Sirve las paginas ya descargadas. Cuenta cuantas pide, que
        es la otra mitad de lo que se comprueba aqui: al completar
        no se pueden bajar los veinte equipos otra vez.
        """

        def __init__(self):
            self.pedidas = []

        def get(self, url, **kwargs):
            self.pedidas.append(url)

            nombre = url.rstrip("/").rsplit("/", 1)[-1]

            fichero = HTML_DIR / f"{nombre}.html"

            if not fichero.exists():
                return RespuestaFalsa("<html></html>")

            return RespuestaFalsa(
                fichero.read_text(encoding="utf-8")
            )

    snapshots = sorted(Path("data").glob("snapshot_*.json"))

    if not snapshots:
        print("    (sin snapshots: me lo salto)")
        return

    snapshot = json.loads(
        snapshots[-1].read_text(encoding="utf-8")
    )

    objetivos = ff.build_targets(snapshot)

    assert len(objetivos) > 20, len(objetivos)

    # Un tablero recien hecho que solo cubre a la mitad.
    mitad = objetivos[: len(objetivos) // 2]

    fuera = [
        o
        for o in objetivos[len(objetivos) // 2:]
        if o.get("team")
    ]

    assert fuera, "el fixture necesita objetivos sin cubrir"

    cacheado = {
        "version": "V12.0",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "matchday": 2,
        "metadata": {},
        "players": [
            {
                "player_id": o["id"],
                "player_name": o["name"],
                "team": o["team"],
                "scope": o["scope"],
                "starter_probability": 70.0,
                "consensus": "STARTER",
                "source": "FUTBOLFANTASY",
                "source_coverage": 1,
                "hierarchy": None,
                "availability": {"code": 0, "label": "DISPONIBLE"},
                "match": {"method": "NAME", "confidence": "ALTA"},
                "ff": {"slug": None},
            }
            for o in mitad
        ],
        "cache": {},
    }

    original = ff.BOARD_FILE

    with tempfile.TemporaryDirectory() as carpeta:

        ff.BOARD_FILE = Path(carpeta) / "board.json"

        ff.BOARD_FILE.write_text(
            json.dumps(cacheado, ensure_ascii=False),
            encoding="utf-8",
        )

        try:
            sesion = SesionDeDisco()

            resultado = ff.refresh_board(
                snapshot,
                2,
                session=sesion,
            )

            estado = (resultado.get("cache") or {}).get("status")

            # Lo que fallaba: esto salia "HIT".
            assert estado == "TOPPED_UP", estado

            cubiertos = {
                p["player_id"] for p in resultado["players"]
            }

            sin_cubrir = [
                o["name"]
                for o in objetivos
                if o.get("team")
                and ff.team_slug(o["team"])
                and o["id"] not in cubiertos
            ]

            # Que los que ya estaban no se pierdan al completar.
            for o in mitad:
                assert o["id"] in cubiertos, o["name"]

            # Y que no se rebaje la liga entera para añadir unos
            # pocos: solo los equipos que hacen falta.
            equipos_pedidos = [
                u for u in sesion.pedidas if "/equipos/" in u
            ]

            equipos_necesarios = {
                o["team"] for o in fuera if ff.team_slug(o["team"])
            }

            assert len(equipos_pedidos) <= len(equipos_necesarios), (
                f"pidio {len(equipos_pedidos)} paginas para "
                f"{len(equipos_necesarios)} equipos"
            )

            print(
                f"    (completado: {len(equipos_pedidos)} paginas, "
                f"{len(sin_cubrir)} sin emparejar)"
            )

        finally:
            ff.BOARD_FILE = original


def test_a_quien_se_vende():
    """
    La venta mira lo que un jugador ES, no lo que fue.

    LOS DOS ERRORES OPUESTOS QUE ARREGLA

        `analyze_sales` puntuaba con puntos de la temporada
        pasada, precio y si entra en el once. Con la plantilla
        real del 17/08/2026 eso daba:

            Gustavo Puerta  CLAVE en el Racing, sin LaLiga el ano
                            pasado -> marcado para vender por
                            "bajo rendimiento historico".

            Hugo Rincon     RESERVA, titular hoy por falta de
                            alternativa -> protegido por estar en
                            el once.

        Fallaba en las dos direcciones a la vez.
    """

    import glob
    import json

    from src.analysis import sales_analyzer as ventas

    snapshots = sorted(glob.glob("data/snapshot_*.json"))

    if not snapshots:
        print("    (sin snapshots: me lo salto)")
        return

    snapshot = json.loads(
        open(snapshots[-1], encoding="utf-8").read()
    )

    original = ventas._ff_signal

    def con_senal(senal):
        ventas._ff_signal = lambda pid: dict(senal)
        return {p["id"]: p for p in ventas.analyze_sales(snapshot)}

    try:
        sin_datos = con_senal({})

        claves = con_senal(
            {
                "hierarchy_value": 50,
                "hierarchy_label": "Clave",
                "probability": 80.0,
            }
        )

        reservas = con_senal(
            {
                "hierarchy_value": 20,
                "hierarchy_label": "Reserva",
                "probability": 15.0,
            }
        )

        rotos = con_senal(
            {
                "hierarchy_value": 20,
                "hierarchy_label": "Reserva",
                "probability": 0.0,
                "absence": {
                    "matchdays_out": 18,
                    "basis": "FECHA",
                },
            }
        )

    finally:
        ventas._ff_signal = original

    assert sin_datos, "el fixture necesita plantilla"

    for player_id, clave in claves.items():

        # A un Clave no se le reprocha no tener historico.
        assert not any(
            "Bajo rendimiento" in r for r in clave["reasons"]
        ), (clave["name"], clave["reasons"])

        # Y siempre cuesta mas soltarlo que a un Reserva.
        assert (
            clave["sale_score"]
            < reservas[player_id]["sale_score"]
        ), clave["name"]

        # Una baja larga lo empeora todavia mas.
        assert (
            rotos[player_id]["sale_score"]
            >= reservas[player_id]["sale_score"]
        ), clave["name"]

    # Un Reserva titular no queda protegido por estarlo: si juega
    # es porque no hay nadie mejor, y eso pide fichar, no
    # conservar.
    titulares_reserva = [
        p for p in reservas.values() if p["in_lineup"]
    ]

    assert titulares_reserva, "el fixture necesita titulares"

    for player in titulares_reserva:
        assert any(
            "falta de alternativa" in r for r in player["reasons"]
        ), (player["name"], player["reasons"])

    # Sin tablero de FutbolFantasy se puntua como siempre: peor,
    # pero nunca se cae.
    assert all(
        p["hierarchy"] is None for p in sin_datos.values()
    )


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


def test_intencion_de_venta_solo_observa():
    """
    Pepe dice a quien soltaria. Y no lo hace.

    LO QUE VIGILA

        1. Que PROPONGA. Hasta hoy solo se vendia cuando faltaba
           caja, asi que un Reserva podia pudrirse en la plantilla
           mientras la caja aguantase.

        2. Que el liston sea mas alto que el de vender por
           necesidad: proponer una venta sin necesitar el dinero
           pide mas conviccion.

        3. Que el guardarrail posicional mande por encima.

        4. Y sobre todo: QUE NO VENDA. Este modulo no puede
           importar un executor ni devolver nada ejecutable. Una
           venta mala no se corrige: el jugador se lo lleva otro.
    """

    import ast
    import glob
    import inspect
    import json

    from src.analysis import sale_intent

    # EL CANDADO DE VERDAD: que no haya por donde escribir.
    #
    # Se miran las IMPORTACIONES, no el texto. La primera version
    # buscaba la palabra "executor" en el codigo fuente y saltaba
    # con el propio comentario que explica que no hay executor.
    arbol = ast.parse(inspect.getsource(sale_intent))

    importados = set()

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                importados.add(alias.name)

        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module or "")

    for modulo in importados:
        for prohibido in ("executor", "write_client", "requests"):
            assert prohibido not in modulo, (
                f"sale_intent importa {modulo}: solo observa"
            )

    # Y que no llame a nada que escriba.
    llamadas = {
        nodo.func.id
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
    }

    assert "open" not in llamadas, "sale_intent no escribe ficheros"

    snapshots = sorted(glob.glob("data/snapshot_*.json"))

    if not snapshots:
        print("    (sin snapshots: me lo salto)")
        return

    snapshot = json.loads(
        open(snapshots[-1], encoding="utf-8").read()
    )

    intencion = sale_intent.build_sale_intent(snapshot)

    assert intencion["available"], intencion.get("reason")
    assert intencion["mode"] == "OBSERVACION"

    # El liston de proponer va por encima del de vigilar.
    assert (
        intencion["propose_score"] > intencion["watch_score"]
    )

    for ficha in intencion["proposals"]:

        assert ficha["sale_score"] >= intencion["propose_score"]

        # Toda propuesta tiene que poder explicarse.
        assert ficha["reasons"], ficha["name"]

        # Publicar, no vender: aceptar una oferta tiene su propio
        # motor con sus propios frenos.
        assert ficha["action"] == "PUBLICAR_EN_MERCADO"

    for ficha in intencion["watch"]:
        assert ficha["sale_score"] < intencion["propose_score"]
        assert "action" not in ficha

    # Un bloqueo del guardarrail siempre dice por que.
    for ficha in intencion["blocked"]:
        assert ficha.get("blocked_reason")

    # Con el liston imposible no se propone a nadie, y no revienta.
    vacio = sale_intent.build_sale_intent(
        snapshot,
        propose_score=1000,
    )

    assert vacio["available"]
    assert vacio["proposals"] == []

    # Y un snapshot roto se dice, no se lanza.
    roto = sale_intent.build_sale_intent({})

    assert roto["available"] is False
    assert roto["reason"]
    assert roto["proposals"] == []


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


def test_el_once_usa_la_fuente_unica():
    """
    El XI se elige con FutbolFantasy, no con el sistema retirado.

    EL CASO QUE LO DESTAPO

        Lo vio el dueño en su propio dashboard, la noche del
        17/08/2026:

            Jonny Castro  70 % IMPORTANTE  ->  al banquillo
            Hugo Rincon   41 % RESERVA     ->  al once

        En FF, Castro es Importante al 70 % y Rincon es Reserva.
        El motor los alineaba al reves porque `lineup_engine`
        seguia reconstruyendo el tablero multifuente -scrapeando
        Jornada Perfecta y Analitica en cada ciclo- en vez de leer
        la fuente unica que ya usaban la compra y la venta.

        Se habia migrado todo menos lo unico que puntua.
    """

    import ast
    import inspect

    from src.analysis import lineup_engine

    # 1. Que no vuelva a importar el modulo retirado.
    arbol = ast.parse(inspect.getsource(lineup_engine))

    for nodo in ast.walk(arbol):

        modulo = ""

        if isinstance(nodo, ast.ImportFrom):
            modulo = nodo.module or ""

        elif isinstance(nodo, ast.Import):
            modulo = " ".join(a.name for a in nodo.names)

        assert "multisource_starter" not in modulo, (
            "el once ha vuelto al sistema multifuente retirado"
        )

    # 2. Que el tablero que arma salga de la fuente unica.
    tablero = lineup_engine.board_from_single_source()

    assert tablero["source"] == "FUTBOLFANTASY"

    if not tablero["players"]:
        print("    (sin tablero de FF: me lo salto)")
        return

    for jugador in tablero["players"]:

        assert jugador["source_coverage"] >= 1

        # Un solo voto, el de FF: no puede votar titular y
        # suplente a la vez.
        votos = (
            jugador["starter_votes"]
            + jugador["bench_votes"]
            + jugador["uncertain_votes"]
        )

        assert votos <= 1, jugador["player_name"]

    # 3. Y que la jerarquia viaje hasta aqui.
    con_jerarquia = [
        j
        for j in tablero["players"]
        if (j.get("hierarchy") or {}).get("label")
    ]

    assert con_jerarquia, (
        "la jerarquia no llega al motor del once"
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
        test_parser_sobre_html_real,
        test_identidad,
        test_identidad_por_equipo,
        test_lookup,
        test_sin_pronostico_no_se_puja,
        test_jerarquia_en_los_puntos,
        test_veto_estructural,
        test_partes_de_baja,
        test_a_quien_se_conserva,
        test_la_cache_comprueba_a_quien_cubre,
        test_a_quien_se_vende,
        test_rival_y_previsibilidad,
        test_intencion_de_venta_solo_observa,
        test_se_puede_comprar_con_saldo_negativo,
        test_el_once_usa_la_fuente_unica,
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
