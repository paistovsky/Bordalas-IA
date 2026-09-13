"""
Los 570 de la liga: la lista de la compra.

SINTOMA (13/09/2026)

    El cuadro de objetivos enseña lo que hay HOY en el mercado.
    Es la caja registradora, y faltaba la lista de la compra.

    Medido: de once "chollos" publicados sin dueño, CERO
    menciones en toda la foto de Pepe. No estaban rechazados: NO
    EXISTIAN. Su universo eran los veinte del mercado del
    Computer mas los que ya tienen dueño.

LA VARA

    Los puntos del jugador menos los del PEOR TITULAR nuestro en
    su posicion. Misma vara para las cuatro, y de puntos YA
    JUGADOS.

    Medida el 13/09 sobre el once real:

        POR  Dituro    4        MED  Mangala  13
        DEF  Djene     7        DEL  Jutgla   14

UN NUMERO SIN RESPALDO, Y SE DICE

    El corte de "chollo" en 6 puntos por millon lo puso el dueño
    a ojo para la previa del diseño. NO ESTA MEDIDO, y esta
    guardia lo deja escrito como tal.

ESTO NO DECIDE NADA. Ninguna puja sale de aqui.

REGLA 23

    No lee estado externo: catalogo, once y plantillas se
    construyen aqui.
"""

from __future__ import annotations

from pathlib import Path


RAIZ = Path(__file__).parents[2]


# EL ONCE REAL DEL 13/09, con los puntos del catalogo.
EL_ONCE = [
    {"id": 17482, "position": 1},   # Dituro,   4  <- peor POR
    {"id": 1599, "position": 2},    # Jonny,   18
    {"id": 9983, "position": 2},    # Djene,    7  <- peor DEF
    {"id": 1721, "position": 2},    # M. Sanchez, 11
    {"id": 41606, "position": 3},   # Mangala, 13  <- peor MED
    {"id": 1602, "position": 3},    # Ruben G., 20
    {"id": 3159, "position": 4},    # Jutgla,  14  <- peor DEL
    {"id": 26271, "position": 4},   # Yamal,   31
]

CATALOGO = {
    17482: {"id": 17482, "name": "Dituro", "position": 1,
            "points": 4, "price": 3_100_000, "status": "ok",
            "playedHome": 3, "playedAway": 3, "teamID": 75},
    1599: {"id": 1599, "name": "Jonny", "position": 2,
           "points": 18, "price": 2_380_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 2},
    9983: {"id": 9983, "name": "Djene", "position": 2,
           "points": 7, "price": 2_400_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 9},
    1721: {"id": 1721, "name": "Manu Sanchez", "position": 2,
           "points": 11, "price": 1_800_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 4},
    41606: {"id": 41606, "name": "Mangala", "position": 3,
            "points": 13, "price": 2_700_000, "status": "ok",
            "playedHome": 3, "playedAway": 3, "teamID": 5},
    1602: {"id": 1602, "name": "Ruben Garcia", "position": 3,
           "points": 20, "price": 2_680_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 6},
    3159: {"id": 3159, "name": "Jutgla", "position": 4,
           "points": 14, "price": 3_050_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 7},
    26271: {"id": 26271, "name": "Yamal", "position": 4,
            "points": 31, "price": 32_000_000, "status": "ok",
            "playedHome": 3, "playedAway": 3, "teamID": 1},

    # Y los que NO son nuestros.
    9001: {"id": 9001, "name": "Libre bueno", "position": 4,
           "points": 30, "price": 2_000_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 20},
    9002: {"id": 9002, "name": "En el mercado", "position": 2,
           "points": 25, "price": 3_000_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 21},
    9003: {"id": 9003, "name": "De un rival", "position": 3,
           "points": 28, "price": 4_000_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 22},
    9004: {"id": 9004, "name": "Lesionado bueno", "position": 4,
           "points": 40, "price": 5_000_000, "status": "injured",
           "playedHome": 3, "playedAway": 3, "teamID": 23},
    9005: {"id": 9005, "name": "Apenas juega", "position": 4,
           "points": 22, "price": 1_000_000, "status": "ok",
           "playedHome": 1, "playedAway": 1, "teamID": 24},
    9006: {"id": 9006, "name": "Barato y flojo", "position": 3,
           "points": 9, "price": 500_000, "status": "ok",
           "playedHome": 3, "playedAway": 3, "teamID": 25},
}

NUESTRA_PLANTILLA = [
    {"id": pid} for pid in (
        17482, 1599, 9983, 1721, 41606, 1602, 3159, 26271
    )
]

MANAGERS = [{"name": "Pollo17", "roster": [{"id": 9003}]}]

EN_EL_MERCADO = {9002}


def _liga(**cambios):
    from src.analysis.toda_la_liga import toda_la_liga

    argumentos = {
        "catalogo": CATALOGO,
        "once": EL_ONCE,
        "nuestra_plantilla": NUESTRA_PLANTILLA,
        "managers": MANAGERS,
        "en_el_mercado": EN_EL_MERCADO,
    }

    argumentos.update(cambios)

    return toda_la_liga(**argumentos)


def _por_nombre(visto, nombre):
    for fila in visto["players"]:
        if fila["name"] == nombre:
            return fila

    raise AssertionError(f"no esta {nombre}")


# ============================================================
# 1. LA VARA
# ============================================================


def test_nos_suma_usa_al_peor_titular() -> None:
    """
    LA RESTA SE HACE CONTRA EL PEOR TITULAR DE SU POSICION, y no
    contra otro.

    Con el once del fixture:

        POR  Dituro    4        MED  Mangala  13
        DEF  Djene     7        DEL  Jutgla   14

    Un delantero de 30 puntos suma +16, no +(-1) contra Yamal.
    """

    visto = _liga()

    assert visto["available"] is True, visto

    vara = visto["vara"]

    # REGLA 24: si la vara saliera vacia, nada de esto probaria
    # nada.
    assert set(vara) == {"POR", "DEF", "MED", "DEL"}, vara

    assert vara["POR"]["name"] == "Dituro", vara
    assert vara["DEF"]["name"] == "Djene", vara
    assert vara["MED"]["name"] == "Mangala", vara
    assert vara["DEL"]["name"] == "Jutgla", vara

    assert vara["DEL"]["points"] == 14, vara

    # UN DELANTERO DE 30 SUMA +16, contra Jutgla (14) y NO contra
    # Yamal (31), que es el mejor.
    libre = _por_nombre(visto, "Libre bueno")

    assert libre["nos_suma"] == 16, libre

    assert libre["vara_nombre"] == "Jutgla", libre

    # Y un defensa de 25 suma +18, contra Djene (7).
    mercado = _por_nombre(visto, "En el mercado")

    assert mercado["nos_suma"] == 18, mercado

    assert mercado["vara_nombre"] == "Djene", mercado


def test_sin_once_no_se_inventa_una_vara() -> None:
    """
    Sin el once no se puede saber a quien mejora nadie.

    Una vara inventada convierte "nos suma" en cualquier cosa —y
    parece medido—. Se dice que no se sabe.
    """

    for sin_once in (None, [], [{}]):

        visto = _liga(once=sin_once)

        assert visto["available"] is False, sin_once

        assert visto["players"] == [], sin_once

        assert "vara" in visto["reason"], visto["reason"]


# ============================================================
# 2. LAS ETIQUETAS
# ============================================================


def test_cada_jugador_cae_en_su_grupo() -> None:
    """
    El orden de las etiquetas importa: "no disponible" gana a
    "nos mejora" —un lesionado no mejora nada— y "ya es nuestro"
    gana a todo, porque no hay nada que decidir.

    Y DONDE ESTA NO ES UNA ETIQUETA (13/09/2026, noche). Los tres
    que nos mejoran llevan la misma —"nos mejora"— este en el
    mercado del Computer, libre o en la plantilla de un rival.
    """

    visto = _liga()

    espera = {
        "En el mercado": "nos mejora",
        "Libre bueno": "nos mejora",
        "De un rival": "nos mejora",
        "Lesionado bueno": "no disponible",
        "Apenas juega": "no disponible",
        "Barato y flojo": "chollo · muchos puntos por euro",
        "Yamal": "ya es nuestro",
        "Djene": "ya es nuestro",
    }

    for nombre, etiqueta in espera.items():
        assert _por_nombre(visto, nombre)["etiqueta"] == (
            etiqueta
        ), (nombre, _por_nombre(visto, nombre)["etiqueta"])

    # EL RECUENTO, que es el numero que mas importa del cuadro.
    assert sum(visto["recuento"].values()) == visto["total"]

    assert visto["total"] == len(CATALOGO)


def test_el_orden_es_por_escalon_y_luego_por_calidad_precio() -> None:
    """
    DENTRO DE CADA GRUPO MANDA LA CALIDAD-PRECIO.

        calidad_precio = nos_suma / (precio / 1.000.000)

    Con el fixture, los tres que nos mejoran salen asi:

        Libre bueno     +16 / 2,00 M  =  8,0
        En el mercado   +18 / 3,00 M  =  6,0
        De un rival     +15 / 4,00 M  =  3,8

    El que mas suma en bruto es "En el mercado" (+18) y NO es el
    primero: por eso esta guardia mide la division y no la resta.
    """

    visto = _liga()

    escalones = [f["escalon"] for f in visto["players"]]

    assert escalones == sorted(escalones), escalones

    mejoran = [
        f for f in visto["players"] if f["etiqueta"] == "nos mejora"
    ]

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(mejoran) == 3, mejoran

    assert [f["name"] for f in mejoran] == [
        "Libre bueno",
        "En el mercado",
        "De un rival",
    ], [(f["name"], f["calidad_precio"]) for f in mejoran]

    assert [f["calidad_precio"] for f in mejoran] == [
        8.0,
        6.0,
        3.8,
    ], mejoran

    # EL QUE MAS SUMA EN BRUTO NO ES EL PRIMERO.
    assert max(mejoran, key=lambda f: f["nos_suma"])["name"] == (
        "En el mercado"
    ), mejoran

    # Y los nuestros, al final.
    assert visto["players"][-1]["etiqueta"] == "ya es nuestro"


def test_estar_en_el_mercado_no_adelanta() -> None:
    """
    ESTAR HOY EN EL MERCADO DEL COMPUTER DEJO DE ORDENAR.

    SINTOMA (13/09/2026)

        La primera version ponia arriba a los que se podian pujar
        hoy. El dueño lo vio y dijo que no:

            "que no sean primero los que estan hoy en el mercado.
             Quiero que Pepe me diga cual es el que mas le
             interesa por calidad-precio."

    CONSECUENCIA

        Con el mercado ordenando, la respuesta a "cual me
        interesa mas" cambiaba cada mañana a las 07:00 sin que
        cambiara ni un punto ni un euro. Era la pregunta "que
        puedo comprar hoy" disfrazada de "que me conviene".

    En el fixture, "En el mercado" es EL QUE MAS SUMA (+18) y
    esta en el mercado del Computer. Aun asi va segundo, detras
    de un libre con mejor calidad-precio.
    """

    visto = _liga()

    nombres = [f["name"] for f in visto["players"]]

    assert nombres.index("Libre bueno") < nombres.index(
        "En el mercado"
    ), nombres

    # 1. LA ETIQUETA NO DICE DONDE ESTA.
    del_mercado = _por_nombre(visto, "En el mercado")

    assert del_mercado["de_quien"] == "computer", del_mercado

    assert del_mercado["etiqueta"] == "nos mejora", del_mercado

    assert _por_nombre(visto, "Libre bueno")["etiqueta"] == (
        "nos mejora"
    )

    assert _por_nombre(visto, "De un rival")["etiqueta"] == (
        "nos mejora"
    )

    # 2. QUITAR EL MERCADO NO MUEVE NI UNA FILA.
    #
    #    Es la prueba de verdad: si el orden dependiera de quien
    #    esta hoy en venta, la lista cambiaria.
    sin_mercado = _liga(en_el_mercado=set())

    assert [f["name"] for f in sin_mercado["players"]] == (
        nombres
    ), [f["name"] for f in sin_mercado["players"]]

    # 3. Y EL ESCALON TAMPOCO SALE DE AHI.
    import ast

    fuente = (
        RAIZ / "src" / "analysis" / "toda_la_liga.py"
    ).read_text(encoding="utf-8")

    cuerpo = ast.parse(fuente)

    etiqueta = next(
        nodo
        for nodo in ast.walk(cuerpo)
        if isinstance(nodo, ast.FunctionDef)
        and nodo.name == "_etiqueta"
    )

    # Sin docstring: esta guardia se ha puesto roja ocho veces
    # por el texto que la explica.
    codigo = ast.dump(
        ast.Module(body=etiqueta.body[1:], type_ignores=[])
    )

    for del_mercado in ("computer", "en_el_mercado"):
        assert del_mercado not in codigo, (
            f"`_etiqueta` vuelve a mirar `{del_mercado}`: estar "
            f"hoy en el mercado no es un escalon"
        )


def test_ninguna_plantilla_llega_vacia() -> None:
    """
    LAS OCHO PLANTILLAS, CONTADAS Y PUBLICADAS.

    SINTOMA (13/09/2026)

        El recuento daba mas "libres" de los que parecian
        razonables. Una plantilla que llega vacia no se nota: sus
        jugadores pasan a contarse como libres, y un libre es
        alguien a quien se puede fichar.

    CONSECUENCIA

        Pepe recomendaria pujar por alguien que ya tiene dueño.
        No falla nada: la lista queda mal y callada.

    LA CUENTA

        los de cada plantilla + los libres = el catalogo

    Con el fixture: 8 nuestros + 1 de Pollo17 = 9 con dueño, y
    14 - 9 = 5 libres.
    """

    visto = _liga()

    censo = visto["plantillas"]

    # REGLA 24: sin equipos esto no probaria nada.
    assert censo["equipos"], censo

    assert len(censo["equipos"]) == 1 + len(MANAGERS), censo

    assert censo["total"] == len(CATALOGO), censo

    assert censo["con_dueño"] == 9, censo

    assert censo["libres"] == 5, censo

    assert censo["cuadra"] is True, censo

    assert censo["descuadre"] == 0, censo

    # NINGUNA VACIA.
    assert censo["vacias"] == [], censo

    for equipo in censo["equipos"]:
        assert equipo["jugadores"] > 0, equipo

    # LA NUESTRA SE DISTINGUE.
    nuestra = [e for e in censo["equipos"] if e["es_nuestra"]]

    assert len(nuestra) == 1, censo

    assert nuestra[0]["jugadores"] == len(NUESTRA_PLANTILLA)

    # UNA PLANTILLA VACIA SE VE, y no se disuelve en los libres.
    hueca = _liga(
        managers=[{"name": "Pollo17", "roster": []}]
    )["plantillas"]

    assert hueca["vacias"] == ["Pollo17"], hueca

    assert hueca["libres"] == 6, hueca

    # Y UN DESCUADRE SE PUBLICA COMO NUMERO, no como sospecha.
    #
    #     Dos managers con el mismo jugador: la suma de las
    #     plantillas dice 2 y los con dueño dicen 1.
    doble = _liga(
        managers=[
            {"name": "Pollo17", "roster": [{"id": 9003}]},
            {"name": "Mex", "roster": [{"id": 9003}]},
        ]
    )["plantillas"]

    assert doble["cuadra"] is False, doble

    assert doble["descuadre"] == 1, doble


def test_el_corte_del_chollo_consta_como_no_medido() -> None:
    """
    LO PUSO EL DUEÑO A OJO PARA LA PREVIA.

    No esta medido, y un umbral sin respaldo que nadie recuerda
    que lo es acaba tratandose como si lo estuviera. Va escrito
    en el modulo, en el estado publicado y en la pantalla.
    """

    from src.analysis.toda_la_liga import (
        PUNTOS_POR_MILLON_CHOLLO,
    )

    assert PUNTOS_POR_MILLON_CHOLLO == 6.0

    visto = _liga()

    assert visto["chollo_sin_medir"] == 6.0, visto

    assert "NO esta medido" in visto["reason"], visto["reason"]

    fuente = (
        RAIZ / "src" / "analysis" / "toda_la_liga.py"
    ).read_text(encoding="utf-8")

    assert "SIN MEDIR" in fuente, (
        "el modulo no dice que el corte no esta medido"
    )

    panel = (
        RAIZ
        / "dashboard-v8"
        / "src"
        / "components"
        / "TodaLaLigaPanel.jsx"
    ).read_text(encoding="utf-8")

    assert "NO" in panel and "medido" in panel, (
        "la pantalla no avisa de que el corte no esta medido"
    )


def test_esta_lista_no_decide_nada() -> None:
    """
    Es para MIRAR. Ninguna puja sale de aqui, y el dia que
    alguien la conecte esta guardia se pone roja y se habla
    antes.
    """

    import ast

    fuente = (
        RAIZ / "src" / "analysis" / "toda_la_liga.py"
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
        "list_player_for_sale",
        "accept_offer",
        "record_bid",
        "abrir",
    ):
        assert escribe not in llamadas, (
            f"la lista de la liga llama a `{escribe}`: deberia "
            f"ser solo para mirar"
        )

    # Y no importa ningun ejecutor.
    for modulo in ("write_client", "executor", "carril"):
        assert modulo not in fuente, (
            f"la lista importa `{modulo}`"
        )


def test_el_panel_esta_montado_y_lee_lo_publicado() -> None:
    """
    Que exista no basta: tiene que estar en la pagina y leer el
    bloque publicado.
    """

    mercado = (
        RAIZ / "dashboard-v8" / "src" / "pages" / "MarketPage.jsx"
    ).read_text(encoding="utf-8")

    assert "<TodaLaLigaPanel" in mercado, (
        "el cuadro 2 no esta montado en MERCADO"
    )

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"todaLaLiga"' in estado, (
        "la telemetria no publica la liga entera"
    )

    assert "toda_la_liga(" in estado, (
        "no se llama al modulo que la monta"
    )


TESTS = [
    test_nos_suma_usa_al_peor_titular,
    test_sin_once_no_se_inventa_una_vara,
    test_cada_jugador_cae_en_su_grupo,
    test_el_orden_es_por_escalon_y_luego_por_calidad_precio,
    test_estar_en_el_mercado_no_adelanta,
    test_ninguna_plantilla_llega_vacia,
    test_el_corte_del_chollo_consta_como_no_medido,
    test_esta_lista_no_decide_nada,
    test_el_panel_esta_montado_y_lee_lo_publicado,
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
        f"TODA LA LIGA V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
