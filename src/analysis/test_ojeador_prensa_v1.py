"""
La prensa entra con las mismas reglas que todo lo demas.

SINTOMA

    Pepe solo leia webs que COPIAN el precio de Biwenger. Se
    midio el 06/09/2026: cero discrepancias de direccion en 288
    jugadores, cifras identicas al tercer decimal. Tres fuentes
    que son la misma medida repetida.

    Lo que el dueño pidio el primer dia -la prensa- seguia sin
    existir.

CAUSA

    Nadie habia abierto un RSS. Y cuando se abrieron, cuatro de
    cinco canales valian y uno estaba muerto sin decirlo.

CONSECUENCIA

    Un ojeador de prensa es la pieza mas facil de hacer mal de
    todo el repo, porque el texto libre invita a adivinar:

        - a adivinar el jugador ("sale 'Molina', sera el del
          Getafe"),
        - a adivinar la noticia ("dice 'tocado', sera una
          lesion"),
        - y a adivinar una confianza que nadie publica.

    Esta guardia fija los tres noes. Y no toca la red: todos los
    casos van con feeds de mentira escritos aqui, para que la
    puerta no dependa de que Marca este de pie.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.intelligence.scout import press


MODULO = Path("src/intelligence/scout/press.py")


# ============================================================
# UN FEED DE MENTIRA, CON LA FORMA DE LOS DE VERDAD
# ============================================================


def _feed(*titulares) -> str:
    items = "".join(
        f"<item><title><![CDATA[{t}]]></title>"
        f"<description><![CDATA[{d}]]></description>"
        f"<link>https://ejemplo/{i}</link>"
        f"<pubDate>Sat, 05 Sep 2026 17:00:00 +0200</pubDate>"
        f"</item>"
        for i, (t, d) in enumerate(titulares)
    )

    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss><channel>'
        + items
        + "</channel></rss>"
    )


def _catalogo(*jugadores) -> dict:
    return {
        "data": {
            "players": {
                str(identificador): {
                    "id": identificador,
                    "name": nombre,
                    "price": precio,
                    "teamID": 1,
                }
                for identificador, nombre, precio in jugadores
            }
        }
    }


CATALOGO = _catalogo(
    (1, "Lobete", 150_000),
    (2, "Cucurella", 11_630_000),
    (3, "Vivian", 4_000_000),
    (4, "Canales", 3_000_000),
    (5, "Cabello", 500_000),
    (6, "Oso", 200_000),
    (7, "Simeone", 2_000_000),
)


def _informe(titulares, feed="MARCA", ahora=None):
    return press.build_press_report(
        CATALOGO,
        xml_by_feed={feed: _feed(*titulares)},
        now=ahora,
    )


def _items(informe) -> list:
    return [
        {**item, "player_name": ficha["player_name"]}
        for ficha in (informe.get("players") or {}).values()
        for item in ficha["items"]
    ]


# ============================================================
# 1. NO SE ADIVINA EL JUGADOR
# ============================================================


def test_el_nombre_tiene_que_ir_en_mayuscula() -> None:
    """
    "cabello" es pelo. "Cabello" es un jugador. Son dos de los
    569 nombres del catalogo que ademas son palabra corriente en
    castellano.
    """

    pelo = _informe([("Se cortó el cabello antes del partido", "")])
    jugador = _informe([("Cabello marcó el primero", "")])

    assert not _items(pelo), (
        "una palabra en minuscula se ha emparejado con un jugador"
    )
    assert [i["player_name"] for i in _items(jugador)] == ["Cabello"]


def test_los_nombres_de_tres_letras_no_se_buscan() -> None:
    """
    "Oso" esta en el catalogo y sale en cualquier frase. Por
    debajo de cuatro letras no se busca.
    """

    informe = _informe([("El Oso de la Cartuja ruge otra vez", "")])

    assert not _items(informe)
    assert press.MIN_NAME_LENGTH == 4


def test_un_nombre_de_dos_fichas_no_se_adivina() -> None:
    """
    Solo hay uno repetido en el catalogo real -Moussa Diarra, dos
    fichas- y con ese no se elige el mas probable.
    """

    catalogo = _catalogo(
        (10, "Moussa Diarra", 1_000_000),
        (11, "Moussa Diarra", 2_000_000),
    )

    informe = press.build_press_report(
        catalogo,
        xml_by_feed={"MARCA": _feed(("Moussa Diarra es baja", ""))},
    )

    assert not (informe.get("players") or {}), (
        "se ha elegido una de las dos fichas del nombre repetido"
    )


def test_lo_que_no_empareja_va_a_unmatched_con_su_motivo() -> None:
    informe = _informe([("El Betis gana en Sevilla", "")])

    assert informe["unmatched_total"] == 1

    sin = informe["unmatched"][0]

    assert sin["title"] == "El Betis gana en Sevilla"
    assert sin["url"]
    assert sin["reason"]


# ============================================================
# 2. NO SE ADIVINA LA NOTICIA
# ============================================================


def test_una_frase_con_dos_nombres_no_se_clasifica() -> None:
    """
    EL CASO REAL DE LA PRIMERA EJECUCION EN VIVO

        "El centrocampista navarro regresa despues de perderse
         los dos ultimos encuentros por una leve lesion muscular,
         el central cubre la baja de Vivian"

        Tres nombres del catalogo en una frase, y la regla le
        colgaba BAJA a los tres. Solo uno es la baja; otro
        justamente REGRESA.
    """

    informe = _informe(
        [("Canales regresa y el central cubre la baja de Vivian", "")]
    )

    items = _items(informe)

    assert len(items) == 2, [i["player_name"] for i in items]

    for item in items:
        assert item["kind"] == press.MENCION, (
            f"{item['player_name']} sale clasificado como "
            f"{item['kind']} en una frase con dos sujetos"
        )
        assert item["ambiguous_subject"] is True
        assert item["subjects_in_quote"] == 2
        assert item["ambiguous_reason"]


def test_con_un_solo_sujeto_si_se_clasifica() -> None:
    informe = _informe(
        [("Lobete se rompe el cruzado y será baja todo el curso", "")]
    )

    item = _items(informe)[0]

    assert item["kind"] == press.BAJA
    assert item["direction"] == press.DOWN
    assert item["ambiguous_subject"] is False


def test_tocado_no_es_una_lesion() -> None:
    """
    "no podemos amedrentarnos porque nos hayan TOCADO el Atletico"
    no es un jugador tocado: es un sorteo. La palabra fallo en el
    primer titular que la contenia y por eso no esta en las
    reglas.
    """

    fuente = MODULO.read_text(encoding="utf-8")

    for regla in press.REGLAS:
        assert "tocado" not in regla[2], (
            "«tocado» ha vuelto a las reglas: significa las dos "
            "cosas en castellano futbolistico"
        )

    assert "TOCADO el Atletico" in fuente, (
        "se ha perdido el motivo por el que «tocado» esta fuera"
    )


def test_nombrar_a_alguien_no_es_una_señal() -> None:
    informe = _informe(
        [("Cucurella cumple 200 partidos en Primera", "")]
    )

    item = _items(informe)[0]

    assert item["kind"] == press.MENCION
    assert item["direction"] == press.FLAT


# ============================================================
# 3. NO SE INVENTA UNA CONFIANZA
# ============================================================


def test_la_confianza_es_siempre_nula_y_dice_por_que() -> None:
    informe = _informe(
        [
            ("Lobete se rompe el cruzado", ""),
            ("Cucurella, duda para el domingo", ""),
        ]
    )

    items = _items(informe)

    assert items

    for item in items:
        assert item["confidence"] is None, (
            "alguien ha inventado una confianza para la prensa"
        )
        assert item["confidence_basis"]

    assert informe["confidence_basis"]


def test_la_clase_viaja_marcada_como_deduccion() -> None:
    """
    "Nada de prediccion. Si el modelo deduce algo, que quede
    marcado como deduccion y no como dato."
    """

    item = _items(_informe([("Lobete se rompe el cruzado", "")]))[0]

    assert item["deduced"] is True
    assert item["deduced_from"]

    assert "DEDUCCION" in informe_caveat(), (
        "el informe no avisa de que la clase es una deduccion"
    )


def informe_caveat() -> str:
    return _informe([("Lobete se rompe el cruzado", "")])["caveat"]


def test_la_cita_es_literal_y_lleva_su_enlace() -> None:
    """
    "La cita literal siempre. Si mañana la señal falla, hay que
    poder ver quien lo dijo y con que palabras."
    """

    titular = "Lobete se rompe el cruzado y será baja todo el curso"

    item = _items(_informe([(titular, "")]))[0]

    assert item["quote"] == titular
    assert item["headline"] == titular
    assert item["url"]
    assert item["published_at"]
    assert item["source"] == "MARCA"


def test_la_cita_no_sale_con_etiquetas_html_dentro() -> None:
    """
    Mundo Deportivo mete HTML ESCAPADO dentro del CDATA. Quitando
    etiquetas antes de desescapar, reaparecen y la cita sale
    ilegible.
    """

    sucio = (
        "El central &lt;b&gt;Vivian&lt;/b&gt; es baja &amp; no "
        "viaja"
    )

    assert press.limpiar(sucio) == "El central Vivian es baja & no viaja"


# ============================================================
# 4. LOS CANALES
# ============================================================


def test_as_esta_apagado_y_se_dice_por_que() -> None:
    """
    AS responde 200 y trae 68 noticias bien formadas cuya mas
    reciente es de 2022. Es el caso mas peligroso: una fuente que
    parece viva.
    """

    configuracion = press.FEEDS["AS"]

    assert configuracion["enabled"] is False
    assert "2022" in configuracion["note"], (
        "el motivo de apagar AS ya no lleva la fecha dentro"
    )

    resultado = press.scout("AS")

    assert resultado["ok"] is False
    assert resultado["error"]


def test_los_canales_vivos_son_los_que_se_probaron() -> None:
    vivos = {
        nombre
        for nombre, conf in press.FEEDS.items()
        if conf.get("enabled")
    }

    assert vivos == {"MARCA", "MUNDO_DEPORTIVO", "RELEVO"}


def test_una_noticia_de_hace_cuatro_dias_no_entra() -> None:
    from datetime import datetime, timedelta, timezone

    ahora = datetime(2026, 9, 5, 15, 0, tzinfo=timezone.utc)

    viejo = ahora + timedelta(
        hours=press.MAX_ITEM_AGE_HOURS + 24
    )

    informe = _informe(
        [("Lobete se rompe el cruzado", "")],
        ahora=viejo,
    )

    assert informe["too_old"] == 1
    assert not _items(informe)


# ============================================================
# 5. NI DECIDE NI REVIENTA
# ============================================================


def test_el_ojeador_no_decide_nada() -> None:
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))

    prohibidos = (
        "autopilot_executor",
        "write_client",
        "decision_orchestrator",
        "acquisition_valuation",
        "sale_order",
        "BiwengerWriteClient",
    )

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"el ojeador de prensa importa {prohibido}: "
                    f"deja de ser un observador"
                )


def test_ninguna_ruta_de_decision_lee_la_prensa() -> None:
    """
    El otro lado del mismo candado: que nadie la importe.
    """

    rutas = (
        "src/analysis/decision_orchestrator.py",
        "src/analysis/acquisition_valuation.py",
        "src/analysis/offer_decision_engine.py",
        "src/analysis/sale_order.py",
        "src/analysis/solvency_clock.py",
        "src/analysis/lineup_engine.py",
    )

    for ruta in rutas:

        fichero = Path(ruta)

        if not fichero.exists():
            continue

        assert "scout.press" not in fichero.read_text(
            encoding="utf-8"
        ), f"{ruta} lee el ojeador de prensa"


def test_nunca_lanza_con_basura() -> None:
    for catalogo in (None, {}, {"data": None}, {"data": {"players": []}}):
        informe = press.build_press_report(
            catalogo,
            xml_by_feed={"MARCA": "esto no es un xml"},
        )
        assert isinstance(informe, dict)
        assert "available" in informe

    assert press.parse_items(None) == []
    assert press.parse_items("<rss></rss>") == []


# ============================================================
# 6. AL LIBRO DE ACIERTO
# ============================================================


def test_al_libro_solo_van_las_apuestas_de_verdad() -> None:
    """
    Una noticia de alineacion o de fichaje dice algo del jugador
    pero no dice hacia donde va su precio. Apuntarla como
    prediccion inflaria el acierto con casos que no se pueden
    fallar.
    """

    assert set(press.SCORABLE_KINDS) == {
        press.BAJA,
        press.DUDA,
        press.VUELVE,
    }

    informe = _informe(
        [
            ("Lobete se rompe el cruzado", ""),
            ("Cucurella es titular hoy", ""),
        ]
    )

    adaptado = press.as_accuracy_report(informe)

    nombres = {
        ficha["player_name"]
        for ficha in adaptado["players"].values()
    }

    assert nombres == {"Lobete"}, nombres


def test_la_fuente_del_libro_lleva_el_medio_dentro() -> None:
    """
    Para poder ver en dos semanas si Marca acierta mas que Mundo
    Deportivo. Un solo cajon "PRENSA" no responderia eso.
    """

    adaptado = press.as_accuracy_report(
        _informe([("Lobete se rompe el cruzado", "")])
    )

    señal = list(adaptado["players"].values())[0]["signals"][0]

    assert señal["source"] == "PRENSA_MARCA"
    assert señal["horizon_days"] == press.ACCURACY_HORIZON_DAYS
    assert señal["confidence"] is None


def test_lo_ambiguo_no_entra_al_libro() -> None:
    adaptado = press.as_accuracy_report(
        _informe(
            [("Canales regresa y el central cubre la baja de Vivian", "")]
        )
    )

    assert not adaptado["players"], (
        "una clasificacion que no se afirma se esta puntuando "
        "igual"
    )


# ============================================================
# 7. DOS VECES AL DIA, NO CUARENTA Y OCHO
# ============================================================


def _en_disco(informe: dict):
    """
    Escribe un informe en un fichero temporal y devuelve la ruta.
    """

    import json
    import tempfile

    destino = Path(tempfile.gettempdir()) / "press_report_guardia.json"

    destino.write_text(
        json.dumps(informe, ensure_ascii=False),
        encoding="utf-8",
    )

    return destino


class _SesionQueGrita:
    """
    Si alguien sale a la calle cuando no toca, se entera.
    """

    def get(self, *args, **kwargs):
        raise AssertionError(
            "se ha salido a la red teniendo un informe fresco en "
            "disco"
        )


def test_con_el_informe_fresco_no_se_sale_a_la_calle() -> None:
    """
    El ciclo corre 48 veces al dia y las noticias no cambian cada
    media hora. TTL de doce horas.
    """

    from datetime import datetime, timedelta, timezone

    ahora = datetime(2026, 9, 5, 18, 0, tzinfo=timezone.utc)

    ruta = _en_disco(
        {
            "version": press.VERSION,
            "generated_at": (ahora - timedelta(hours=2)).isoformat(),
            "headlines": 10,
            "players": {},
        }
    )

    salida = press.refresh_press(
        CATALOGO,
        path=ruta,
        now=ahora,
        session=_SesionQueGrita(),
    )

    assert salida["cache"]["status"] == "HIT"
    assert salida["cache"]["ttl_seconds"] == press.DEFAULT_TTL_SECONDS
    assert press.DEFAULT_TTL_SECONDS == 12 * 3600


def test_un_informe_vacio_no_pisa_al_anterior() -> None:
    """
    Un informe recien escrito sin ni un titular es peor que uno de
    hace doce horas: parece dato y no lo es. Es la misma regla que
    ya tiene el ojeador de mercado.
    """

    from datetime import datetime, timedelta, timezone

    ahora = datetime(2026, 9, 5, 18, 0, tzinfo=timezone.utc)

    ruta = _en_disco(
        {
            "version": press.VERSION,
            "generated_at": (ahora - timedelta(days=2)).isoformat(),
            "headlines": 163,
            "players_with_signal": 12,
            "players": {},
        }
    )

    class SesionMuda:
        def get(self, *args, **kwargs):
            raise RuntimeError("no contesta ninguna web")

    salida = press.refresh_press(
        CATALOGO,
        path=ruta,
        now=ahora,
        session=SesionMuda(),
    )

    assert salida["cache"]["status"] == "STALE_FALLBACK"
    assert salida["headlines"] == 163, (
        "se ha pisado el informe bueno con uno vacio"
    )
    assert salida["cache"]["error"]


def test_el_ruido_se_publica_en_vez_de_esconderse() -> None:
    """
    Los contadores tienen que salir en el informe: cuantos
    titulares se leyeron, cuantos jugadores se mencionan, cuantos
    traen señal de verdad y cuantos se quedaron sin emparejar.

    Sin esos cuatro numeros, doce señales parecen doce aciertos.
    """

    informe = _informe(
        [
            ("Lobete se rompe el cruzado", ""),
            ("El Betis gana en Sevilla", ""),
            ("Cucurella cumple 200 partidos", ""),
        ]
    )

    for clave in (
        "headlines",
        "players_mentioned",
        "players_with_signal",
        "unmatched_total",
        "too_old",
    ):
        assert clave in informe, f"el informe no publica `{clave}`"

    assert informe["headlines"] == 3
    assert informe["unmatched_total"] == 1
    assert informe["players_mentioned"] == 2
    assert informe["players_with_signal"] == 1, (
        "una mencion sin señal se esta contando como señal"
    )


TESTS = [
    test_el_nombre_tiene_que_ir_en_mayuscula,
    test_los_nombres_de_tres_letras_no_se_buscan,
    test_un_nombre_de_dos_fichas_no_se_adivina,
    test_lo_que_no_empareja_va_a_unmatched_con_su_motivo,
    test_una_frase_con_dos_nombres_no_se_clasifica,
    test_con_un_solo_sujeto_si_se_clasifica,
    test_tocado_no_es_una_lesion,
    test_nombrar_a_alguien_no_es_una_señal,
    test_la_confianza_es_siempre_nula_y_dice_por_que,
    test_la_clase_viaja_marcada_como_deduccion,
    test_la_cita_es_literal_y_lleva_su_enlace,
    test_la_cita_no_sale_con_etiquetas_html_dentro,
    test_as_esta_apagado_y_se_dice_por_que,
    test_los_canales_vivos_son_los_que_se_probaron,
    test_una_noticia_de_hace_cuatro_dias_no_entra,
    test_el_ojeador_no_decide_nada,
    test_ninguna_ruta_de_decision_lee_la_prensa,
    test_nunca_lanza_con_basura,
    test_al_libro_solo_van_las_apuestas_de_verdad,
    test_la_fuente_del_libro_lleva_el_medio_dentro,
    test_lo_ambiguo_no_entra_al_libro,
    test_con_el_informe_fresco_no_se_sale_a_la_calle,
    test_un_informe_vacio_no_pisa_al_anterior,
    test_el_ruido_se_publica_en_vez_de_esconderse,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"OJEADOR DE PRENSA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
