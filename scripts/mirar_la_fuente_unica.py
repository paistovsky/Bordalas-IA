"""
MIRAR la fuente unica contra el HTML y las fotos guardadas.

POR QUE ESTAN AQUI Y NO ENTRE LAS GUARDIAS

    Estas siete comprobaciones vivian en
    `test_futbolfantasy_source_v12` y todas empezaban igual:

        if not ficheros:
            print("    (sin HTML: corre el volcador)")
            return

    Sin `data/ff_html` o sin fotos en `data/`, SALIAN SIN AFIRMAR
    NADA y contaban como verdes. Siete de las trece que el censo
    de `test_ninguna_pasa_con_las_manos_vacias_v1` tenia
    apuntadas, y las siete en este fichero.

    No es un fallo de quien las escribio: parsear HTML de verdad
    es lo que hacen, y el HTML no esta versionado. Lo que estaba
    mal era el sitio.

LO QUE SIGUE EN LA VERJA

    Las trece que se quedan en `test_futbolfantasy_source_v12` no
    tocan `data/`: la jerarquia escalon a escalon, la identidad
    con casos escritos a mano, y el guardarrail que frena sin
    pronostico — que es lo unico de alli que mueve dinero.

COMO SE LEEN LOS RESULTADOS

    Cada comprobacion es la MISMA funcion que estaba en la
    guardia, con sus `assert` intactos. Aqui un `assert` que salta
    no tumba nada: se imprime y se sigue, porque lo que falla
    puede ser el mundo y no el codigo.

USO

    python scripts/mirar_la_fuente_unica.py

    Solo lectura. No escribe en Biwenger ni en ningun libro.
"""

from __future__ import annotations

import glob
import json
import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.analysis.candidate_starter_lookup import (    # noqa: E402
    build_starter_lookup,
)

from src.intelligence.futbolfantasy_provider import (  # noqa: E402
    build_player_entry,
    match_team,
    parse_team_page,
    team_slug,
)

from src.analysis.test_futbolfantasy_source_v12 import (  # noqa: E402
    EQUIPOS_LIGA,
)


HTML_DIR = Path("data/ff_html")


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

LAS_SIETE = (
    test_parser_sobre_html_real,
    test_identidad_por_equipo,
    test_partes_de_baja,
    test_la_cache_comprueba_a_quien_cubre,
    test_a_quien_se_vende,
    test_intencion_de_venta_solo_observa,
    test_el_once_usa_la_fuente_unica,
)


def main() -> int:

    print("=" * 78)
    print("MIRAR LA FUENTE UNICA, contra el HTML y las fotos")
    print("=" * 78)

    hay_html = HTML_DIR.exists() and any(HTML_DIR.glob("*.html"))

    hay_fotos = bool(glob.glob("data/snapshot_*.json"))

    print(f"  HTML guardado: {'si' if hay_html else 'NO'}"
          f"   fotos en disco: {'si' if hay_fotos else 'NO'}")

    if not (hay_html or hay_fotos):
        print("  No hay nada que mirar. Eso no es un fallo.")
        print("=" * 78)
        return 0

    print()

    saltaron = 0

    for comprobacion in LAS_SIETE:

        try:
            comprobacion()
            print(f"  OK    {comprobacion.__name__}")

        except AssertionError as error:
            saltaron += 1
            print(f"  MIRA  {comprobacion.__name__}")
            print(f"          {error}")

        except Exception as error:                  # noqa: BLE001
            saltaron += 1
            print(f"  MIRA  {comprobacion.__name__}")
            print(f"          reviento: "
                  f"{type(error).__name__}: {error}")

    print()
    print("=" * 78)
    print(
        f"LA FUENTE UNICA: {len(LAS_SIETE) - saltaron}"
        f"/{len(LAS_SIETE)} sin nada que mirar"
    )
    print("=" * 78)

    # Un mirador no devuelve error por el estado del mundo.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
