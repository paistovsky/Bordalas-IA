"""
La lista de la compra: de quien es cada jugador, y en que orden se opera.

QUE SE PRUEBA AQUI

    1. `test_la_lista_dice_de_quien_es`
       Ningun candidato aparece sin decir si es comprable hoy o
       hay que pedirselo. Falla si el catalogo llega vacio.

    2. `test_el_mercado_libre_entra_en_la_lista`
       Un jugador libre que mejora el once y ESTA EN EL
       ESCAPARATE aparece en la lista; los que no estan
       publicados se cuentan aparte con su motivo. Falla si no
       hay ningun libre en la foto.

    3. `test_no_se_vende_un_titular_sin_recambio`
       Ninguna operacion propone vender a un titular antes de
       tener el sustituto. Falla si la lista de titulares llega
       vacia.

    4. `test_el_guardarrail_mira_titularidad`
       Quedarse con dos porteros que no juegan es una violacion.
       Falla si todos los porteros de la prueba son titulares,
       porque entonces no probaria nada.

    5. `test_la_tabla_por_plazas_empieza_por_la_peor`
       Y arriba del todo va la mejor operacion sin vender a nadie.

    6. `test_la_puerta_viaja_con_la_segunda_lista`

    7. `test_esto_sigue_apagado`

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aqui. La vara entra por argumento.
    La cache de pronosticos se clava vacia antes de nada, porque
    `build_position_guardrail` relee el tablero de titularidades
    por dentro —cazado por el vigilante de la verja el 17/09—.

    Y NINGUN MENSAJE DE ASERCION NOMBRA EL DIRECTORIO DE ESTADO:
    la Regla A de `test_verja_determinista_v1` busca esa cadena
    en cualquier literal del modulo y no distingue una lectura de
    una frase que hable de ella.

UNA GUARDIA QUE NO MUERDE ES PEOR QUE NINGUNA

    Las trece inyecciones de fallo se probaron una a una, en
    memoria. Y una NO MORDIA al principio, dicho porque importa
    mas que las que si:

    `test_el_guardarrail_mira_titularidad` empezo con tres
    porteros de los que DOS eran titulares. Con ese fixture,
    vender al primero deja un titular y el suelo se cumple: la
    comprobacion pasaba con y sin el freno nuevo. El fixture
    tiene que tener UN solo portero titular y dos que no juegan,
    que es justo la foto del 17/09, y por eso la guardia
    comprueba primero la forma del fixture.
"""

from __future__ import annotations

from src.analysis.la_lista_de_la_compra import (
    COMPRABLE_HOY,
    ENCENDIDO,
    GRUPOS,
    HAY_QUE_PEDIRSELO,
    RECAMBIO_PRIMERO,
    SIN_VENTA,
    VENTA_PRIMERO,
    de_quien_es,
    esta_encendido,
    libres_que_se_pueden_comprar,
    orden_de_la_operacion,
    partir_la_lista,
    tabla_por_plazas,
)
from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
    validate_sale_set_con_titularidad,
)

import src.analysis.candidate_starter_lookup as _pronosticos


_pronosticos._CACHE = {}
_pronosticos._CACHE_KEY = _pronosticos._files_key()


POR, DEF, MED, DEL = 1, 2, 3, 4


VARA = {POR: 1.0, DEF: 0.787, MED: 1.147, DEL: 1.139}


def factor_de(posicion):
    return VARA.get(int(posicion or 0), 1.0)


# ============================================================
# LOS FIXTURES
# ============================================================
#
# La forma de la foto del 17/09: 3 porteros de los que UNO juega,
# 7 defensas, 6 medios, 4 delanteros.


def _ficha(pid, nombre, posicion, precio, titular, puntos, partidos):
    return {
        "id": pid,
        "name": nombre,
        "position": posicion,
        "price": precio,
        "priceIncrement": 0,
        "in_lineup": titular,
        "is_starter": titular,
        "points": puntos,
        "played_home": partidos,
        "played_away": 0,
    }


PLANTILLA = [
    # EL CASO QUE MOTIVA TODO: un portero que juega y dos que no
    # han jugado nunca. Si los tres fuesen titulares, la guardia
    # del guardarrail no probaria nada.
    _ficha(1, "Dituro", POR, 2_200_000, True, 6, 6),
    _ficha(2, "Lunin", POR, 420_000, False, 0, 0),
    _ficha(3, "Fortuño", POR, 150_000, False, 0, 0),

    _ficha(10, "Jonny", DEF, 2_450_000, True, 18, 5),
    _ficha(11, "Djené", DEF, 1_820_000, True, 13, 5),
    _ficha(12, "Manu Sánchez", DEF, 1_750_000, True, 17, 5),
    _ficha(13, "Balde", DEF, 1_520_000, False, 6, 1),
    _ficha(14, "Trent", DEF, 2_530_000, False, 16, 4),
    _ficha(15, "Drkusic", DEF, 1_250_000, False, 7, 3),
    _ficha(16, "Álvaro Carreras", DEF, 1_340_000, False, 21, 4),

    _ficha(20, "Expósito", MED, 5_340_000, True, 29, 6),
    _ficha(21, "Olasagasti", MED, 3_480_000, True, 32, 5),
    _ficha(22, "Rubén García", MED, 2_590_000, True, 19, 6),
    _ficha(23, "Pablo Ibáñez", MED, 2_510_000, True, 26, 6),
    _ficha(24, "Oriol Rey", MED, 1_180_000, True, 19, 5),
    _ficha(25, "Benavidez", MED, 150_000, False, 5, 2),

    _ficha(30, "Yamal", DEL, 22_100_000, True, 76, 6),
    _ficha(31, "Jutglà", DEL, 3_160_000, True, 25, 6),
    _ficha(32, "Pablo Durán", DEL, 380_000, False, 9, 4),
    _ficha(33, "Paco Cortés", DEL, 150_000, False, 4, 3),
]

ONCE = [f for f in PLANTILLA if f["in_lineup"]]


def _guardarrail():
    return build_position_guardrail(
        PLANTILLA, lineup_ids=[f["id"] for f in ONCE]
    )


# Las filas del universo comprable, con `seller_kind` puesto —que
# es el dato que la lista de candidatos NO trae.
UNIVERSO = {
    101: {"seller_kind": "MANAGER", "seller_name": "Luismi_Haz"},
    102: {"seller_kind": "COMPUTER", "seller_name": "Computer"},
    103: {"seller_kind": "MANAGER", "seller_name": "Pollo17"},
    104: {"seller_kind": "COMPUTER", "seller_name": "Computer"},
    # Y uno sin decir de quien es: no se supone que sea comprable.
    105: {},
}


CANDIDATOS = [
    {
        "id": 101,
        "name": "Kang-in Lee",
        "position": MED,
        "market_price": 8_950_000,
        "puntos_netos_por_millon": 1.403,
    },
    {
        "id": 102,
        "name": "Budimir",
        "position": DEL,
        "market_price": 11_990_000,
        "puntos_netos_por_millon": 0.527,
    },
    {
        "id": 103,
        "name": "Javi Hernández",
        "position": MED,
        "market_price": 3_780_000,
        "puntos_netos_por_millon": 1.550,
    },
    {
        "id": 104,
        "name": "Miguel Román",
        "position": MED,
        "market_price": 3_720_000,
        "puntos_netos_por_millon": 0.900,
    },
    {
        "id": 105,
        "name": "Sin vendedor",
        "position": DEF,
        "market_price": 1_000_000,
        "puntos_netos_por_millon": None,
    },
]


PUERTA = {
    "available": True,
    "cuantos": 9,
    "nuestros": 4,
    "compras_al_computer": 182,
}


# El vestuario libre: veinte, y solo UNO en el escaparate.
VESTUARIO = {
    "libres": 423,
    "recuento": {
        "nos_mejoran": 101,
        "en_el_mercado_hoy": 1,
    },
    "players": [
        {
            "id": 11677,
            "name": "Dimitrievski",
            "position": POR,
            "price": 3_240_000,
            "points": 27,
            "played": 6,
            "nos_suma": 21,
            "en_el_mercado": False,
        },
        {
            "id": 9090,
            "name": "Dmitrovic",
            "position": POR,
            "price": 4_780_000,
            "points": 31,
            "played": 6,
            "nos_suma": 25,
            "en_el_mercado": False,
        },
        {
            "id": 18398,
            "name": "Budimir",
            "position": DEL,
            "price": 11_990_000,
            "points": 45,
            "played": 6,
            "nos_suma": 20,
            "en_el_mercado": True,
        },
    ],
}


# ============================================================
# 1. LA LISTA DICE DE QUIEN ES
# ============================================================


def test_la_lista_dice_de_quien_es():
    """
    Ningun candidato sale sin grupo, y el desconocido cae del
    lado prudente.
    """

    partida = partir_la_lista(CANDIDATOS, UNIVERSO, puerta=PUERTA)

    assert partida["available"] and partida["n"] == 5

    todos = [
        item
        for grupo in GRUPOS
        for item in partida["grupos"][grupo]
    ]

    assert len(todos) == 5, (
        "alguien se ha perdido por el camino al partir la lista"
    )

    for item in todos:
        assert item["grupo"] in GRUPOS, (
            f"{item['name']} sale sin grupo"
        )

        assert item["grupo_label"], (
            f"{item['name']} sale con grupo pero sin nombre: la "
            "etiqueta es la mitad del aviso"
        )

        assert item["de_quien_reason"], (
            f"{item['name']} no dice por que esta en su grupo"
        )

    comprables = {
        i["name"] for i in partida["grupos"][COMPRABLE_HOY]
    }

    pedir = {
        i["name"] for i in partida["grupos"][HAY_QUE_PEDIRSELO]
    }

    assert comprables == {"Budimir", "Miguel Román"}, (
        f"solo los del Computer se pueden comprar hoy: {comprables}"
    )

    assert "Kang-in Lee" in pedir and "Javi Hernández" in pedir

    # EL DESCONOCIDO VA DEL LADO PRUDENTE. Suponer que es del
    # Computer seria pintar como comprable algo que a lo mejor
    # hay que negociar.
    sin_vendedor = next(
        i for i in todos if i["name"] == "Sin vendedor"
    )

    assert sin_vendedor["grupo"] == HAY_QUE_PEDIRSELO
    assert sin_vendedor["seller_known"] is False

    # Y CADA GRUPO ORDENADO POR PUNTOS NETOS POR EURO.
    assert [
        i["name"] for i in partida["grupos"][HAY_QUE_PEDIRSELO]
    ][:2] == ["Javi Hernández", "Kang-in Lee"], (
        "dentro del grupo manda el punto neto por euro"
    )

    assert (
        partida["grupos"][HAY_QUE_PEDIRSELO][-1]["name"]
        == "Sin vendedor"
    ), "el que no se puede medir va al final, sin numero inventado"

    # ------------------------------------------------
    # EL CATALOGO VACIO: MUERDE AQUI
    # ------------------------------------------------
    vacia = partir_la_lista([], UNIVERSO, puerta=PUERTA)

    assert vacia["available"] is False, (
        "con la lista vacia no se publican dos grupos vacios como "
        "si fueran una medicion"
    )

    assert vacia["grupos"] == {}

    # Y sin universo, nadie se cuenta como comprable.
    a_ciegas = partir_la_lista(CANDIDATOS, {}, puerta=PUERTA)

    assert a_ciegas["n_comprable_hoy"] == 0, (
        "sin saber de quien es nadie, nadie es comprable hoy"
    )

    print("  OK  ningun candidato sale sin decir de quien es")


# ============================================================
# 2. EL MERCADO LIBRE
# ============================================================


def test_el_mercado_libre_entra_en_la_lista():
    """
    El libre que ESTA en el escaparate aparece; los que no lo
    estan se cuentan aparte y con su motivo.
    """

    assert VESTUARIO["players"], (
        "no hay ningun libre en la foto: sin catalogo esta guardia "
        "no prueba nada"
    )

    libres = libres_que_se_pueden_comprar(VESTUARIO)

    assert libres["available"]

    dentro = [j["name"] for j in libres["en_el_mercado"]]

    assert dentro == ["Budimir"], (
        f"el unico libre publicado hoy es Budimir: {dentro}"
    )

    # Y ESE APARECE EN LA LISTA DE LA COMPRA, del lado comprable.
    partida = partir_la_lista(CANDIDATOS, UNIVERSO, puerta=PUERTA)

    assert "Budimir" in {
        i["name"] for i in partida["grupos"][COMPRABLE_HOY]
    }, (
        "un libre que esta en el escaparate y mejora el once tiene "
        "que salir en la lista comprable"
    )

    # LOS QUE NO ESTAN PUBLICADOS NO SE PIERDEN: se cuentan, con
    # el tamaño de lo que hay fuera.
    fuera = [j["name"] for j in libres["fuera_del_mercado"]]

    assert "Dimitrievski" in fuera and "Dmitrovic" in fuera

    assert libres["nos_mejoran"] == 101
    assert libres["en_el_mercado_hoy"] == 1

    assert "no estan publicados" in libres["reason"], (
        "el motivo tiene que decir que no es un veto: es que no se "
        "puede pujar por ellos"
    )

    # El vestuario vacio no publica nada.
    assert libres_que_se_pueden_comprar(
        {"players": []}
    )["available"] is False

    print("  OK  el libre publicado entra; los demas se cuentan aparte")


# ============================================================
# 3. NO SE VENDE UN TITULAR SIN RECAMBIO
# ============================================================


def test_no_se_vende_un_titular_sin_recambio():
    """
    Para un sobrante, la venta va primero. Para un titular, el
    recambio entra antes.
    """

    assert ONCE, (
        "la lista de titulares llega vacia: sin once esta guardia "
        "no prueba nada"
    )

    guardarrail = _guardarrail()

    # Ni disco.
    assert _pronosticos._CACHE == {}, (
        "construir el guardarrail ha releido el tablero de "
        "titularidades: esta guardia acaba de leer estado de "
        "produccion"
    )

    sobrantes = [f for f in PLANTILLA if not f["in_lineup"]]

    # 1. SOBRANTES: venta primero, y needs_sale_first puesto.
    solo_sobrantes = orden_de_la_operacion(
        sobrantes[:2], guardarrail=guardarrail
    )

    assert solo_sobrantes["orden"] == VENTA_PRIMERO
    assert solo_sobrantes["needs_sale_first"] is True
    assert solo_sobrantes["titulares_que_salen"] == []

    # 2. UN TITULAR: el recambio primero, y needs_sale_first NO
    #    se marca. Marcarlo es lo que manda vender antes.
    dituro = next(f for f in PLANTILLA if f["name"] == "Dituro")

    con_titular = orden_de_la_operacion(
        [dituro], guardarrail=guardarrail
    )

    assert con_titular["orden"] == RECAMBIO_PRIMERO, (
        f"vender a un titular no puede ir primero: "
        f"{con_titular['orden']}"
    )

    assert con_titular["needs_sale_first"] is False, (
        "`needs_sale_first` en una venta de titular es exactamente "
        "la orden de vender antes de tener el recambio"
    )

    assert con_titular["titulares_que_salen"], (
        "hay que decir QUIEN es el titular que saldria"
    )

    assert "recambio" in con_titular["reason"].lower()

    # 3. MEZCLA: si entre los que salen hay UN titular, manda el
    #    titular. Es la parte que se salta una version que mire
    #    solo al primero de la lista.
    mezcla = orden_de_la_operacion(
        sobrantes[:2] + [dituro], guardarrail=guardarrail
    )

    assert mezcla["orden"] == RECAMBIO_PRIMERO, (
        "con un titular entre los que salen, manda el titular"
    )

    assert mezcla["needs_sale_first"] is False

    # 4. Y SIN VENDER A NADIE, ni una cosa ni la otra.
    assert orden_de_la_operacion(
        [], guardarrail=guardarrail
    )["orden"] == SIN_VENTA

    assert orden_de_la_operacion(
        sobrantes[:1], hace_falta_vender=False
    )["orden"] == SIN_VENTA

    # 5. SIN GUARDARRAIL sigue mirando `in_lineup`: el freno no
    #    depende de que le llegue el guardarrail.
    a_ciegas = orden_de_la_operacion([dituro])

    assert a_ciegas["orden"] == RECAMBIO_PRIMERO, (
        "sin guardarrail se mira `in_lineup`, que la cola si trae"
    )

    print("  OK  ningun titular se vende antes de tener el recambio")


# ============================================================
# 4. EL GUARDARRAIL MIRA TITULARIDAD
# ============================================================


def test_el_guardarrail_mira_titularidad():
    """
    Quedarse con dos porteros que no juegan es una violacion.
    """

    porteros = [f for f in PLANTILLA if f["position"] == POR]

    titulares = [f for f in porteros if f["in_lineup"]]

    # LA FORMA DEL FIXTURE, COMPROBADA PRIMERO.
    #
    #     Con dos porteros titulares, vender al primero deja uno y
    #     el suelo se cumple: la comprobacion pasaria con y sin el
    #     freno nuevo, y no probaria nada. Tiene que haber UNO que
    #     juegue y dos que no.
    assert len(titulares) == 1, (
        f"el fixture necesita UN solo portero titular para probar "
        f"algo, y tiene {len(titulares)}"
    )

    assert len(porteros) == 3, (
        "y dos porteros mas que no juegan, para que el suelo de "
        "cuerpos se cumpla al vender al que juega"
    )

    for suplente in porteros:
        if suplente["in_lineup"]:
            continue

        assert suplente["points"] == 0, (
            f"{suplente['name']} tiene puntos: el caso es el de dos "
            f"porteros que NO han jugado nunca"
        )

    guardarrail = _guardarrail()

    dituro = titulares[0]["id"]

    # LA REGLA VIEJA DEJA PASAR.
    cuerpos = validate_sale_set(guardarrail, [dituro])

    assert cuerpos["ok"] is True, (
        "el fixture no prueba nada: si contar cuerpos ya lo "
        "bloqueara, el freno nuevo no haria falta"
    )

    # LA NUEVA NO.
    titularidad = validate_sale_set_con_titularidad(
        guardarrail, [dituro]
    )

    assert titularidad["ok"] is False, (
        "vender al unico portero que juega deja dos cuerpos y "
        "ningun titular, y eso tiene que ser una violacion"
    )

    assert titularidad["starters_checked"] is True

    assert titularidad["starter_violations"], (
        "la violacion tiene que salir con su detalle, no solo "
        "como un `ok: False`"
    )

    # CON ESAS PALABRAS, que es lo que pedia el encargo.
    assert "cuerpos" in titularidad["reason"].lower(), (
        f"el motivo tiene que decir que quedan los cuerpos y no "
        f"queda quien juegue: {titularidad['reason']!r}"
    )

    assert "titular" in titularidad["reason"].lower()

    violacion = titularidad["starter_violations"][0]

    assert violacion["would_remain_starters"] == 0
    assert violacion["starter_floor"] == 1
    assert violacion["would_remain"] == 2, (
        "quedan dos porteros en plantilla: ese es justo el numero "
        "que hacia pasar la regla vieja"
    )

    # Y NO SE PASA DE FRENADA: vender a los dos que no juegan
    # sigue estando bien.
    suplentes = [f["id"] for f in porteros if not f["in_lineup"]]

    assert validate_sale_set_con_titularidad(
        guardarrail, suplentes
    )["ok"] is True, (
        "soltar a dos porteros que no han jugado nunca no rompe "
        "ningun once"
    )

    # Ni con posiciones que van sobradas de titulares.
    medios_titulares = [
        f["id"]
        for f in PLANTILLA
        if f["position"] == MED and f["in_lineup"]
    ]

    assert len(medios_titulares) > 2

    assert validate_sale_set_con_titularidad(
        guardarrail, medios_titulares[:1]
    )["ok"] is True, (
        "con cinco medios en el once y un suelo de dos, soltar uno "
        "no rompe nada: el freno tiene que morder donde toca"
    )

    print("  OK  quedarse con dos porteros que no juegan es violacion")


# ============================================================
# 5. LA TABLA POR PLAZAS
# ============================================================
#
# Recambios COMPRABLES HOY: dos porteros de 0 puntos -lo que de
# verdad traia el escaparate del 17/09- y un medio que si mejora.

RECAMBIOS = [
    {
        "id": 201,
        "name": "Iturbe",
        "position": POR,
        "price": 150_000,
        "points": 0,
        "played": 0,
    },
    {
        "id": 202,
        "name": "Esquivel",
        "position": POR,
        "price": 150_000,
        "points": 0,
        "played": 0,
    },
    {
        "id": 203,
        "name": "Miguel Román",
        "position": MED,
        "price": 3_720_000,
        "points": 28,
        "played": 6,
    },
    {
        "id": 204,
        "name": "Mayol",
        "position": MED,
        "price": 470_000,
        "points": 5,
        "played": 1,
    },
]


CAJA = 8_874_116


def test_la_tabla_por_plazas_empieza_por_la_peor():
    """
    Las peores plazas primero, y arriba del todo la mejor
    operacion sin vender a nadie.
    """

    tabla = tabla_por_plazas(
        ONCE,
        RECAMBIOS,
        factor_de=factor_de,
        caja_ahora=CAJA,
        guardarrail=_guardarrail(),
    )

    assert tabla["available"] and tabla["n"] == 11

    # LA PEOR PLAZA PRIMERO. Dituro suma 1,00 por partido y el
    # portero no lleva vara: es el ultimo de la lista por puntos.
    assert tabla["plazas"][0]["name"] == "Dituro", (
        f"la peor plaza del once es la de Dituro: "
        f"{tabla['plazas'][0]['name']}"
    )

    assert tabla["plazas"][0]["con_vara"] == 1.0

    # Y LA MEJOR SIN VENDER A NADIE.
    mejor = tabla["mejor_sin_vender"]

    assert mejor is not None

    assert mejor["name"] == "Mayol", (
        f"Mayol da 5,00 por partido a 470.000: es el que mas puntos "
        f"por euro deja sin vender a nadie, no {mejor['name']}"
    )

    assert mejor["cabe_en_caja"] is True

    assert "sin vender" in tabla["reason"].lower()

    # LA PLAZA DE DITURO NO TIENE RECAMBIO, Y LO DICE.
    #
    #     Los dos porteros del escaparate llevan 0 puntos en 0
    #     partidos: no se les puede medir, asi que no entran como
    #     recambio. La plaza se queda sin arreglo HOY, y eso es
    #     una respuesta.
    plaza_dituro = tabla["plazas"][0]

    assert plaza_dituro["recambios_que_mejoran"] == 0
    assert plaza_dituro["mejor"] is None
    assert plaza_dituro["reason"], (
        "una plaza sin recambio tiene que decir por que"
    )

    # Y Dituro sale marcado como intocable por el guardarrail.
    assert plaza_dituro["es_intocable"] is True

    # LA VARA, PUESTA. Olasagasti: 32 puntos en 5 partidos = 6,4;
    # con la vara de medio, 6,4 x 1,147.
    olasagasti = next(
        p for p in tabla["plazas"] if p["name"] == "Olasagasti"
    )

    assert olasagasti["con_vara"] == round(6.4 * VARA[MED], 3), (
        f"la plaza no lleva la vara de su posicion: "
        f"{olasagasti['con_vara']}"
    )

    # ------------------------------------------------
    # EL ONCE VACIO: MUERDE AQUI
    # ------------------------------------------------
    assert tabla_por_plazas(
        [], RECAMBIOS, factor_de=factor_de
    )["available"] is False

    # Y sin recambios comprables, ninguna plaza tiene arreglo hoy.
    sin_nada = tabla_por_plazas(
        ONCE, [], factor_de=factor_de, caja_ahora=CAJA
    )

    assert sin_nada["available"] is True
    assert sin_nada["mejor_sin_vender"] is None, (
        "sin recambios comprables no se puede proponer ninguna "
        "operacion"
    )

    # Un recambio que no cabe en caja no puede salir como "sin
    # vender a nadie".
    caro = tabla_por_plazas(
        ONCE,
        RECAMBIOS,
        factor_de=factor_de,
        caja_ahora=100,
    )

    assert caro["mejor_sin_vender"] is None, (
        "con cien euros en caja no hay operacion que no necesite "
        "vender"
    )

    print("  OK  la tabla empieza por la peor plaza y corona la mejor")


# ============================================================
# 6. LA PUERTA
# ============================================================


def test_la_puerta_viaja_con_la_segunda_lista():
    """
    Nadie puede confundir una carta con una lista de la compra.
    """

    partida = partir_la_lista(CANDIDATOS, UNIVERSO, puerta=PUERTA)

    puerta = partida["puerta"]

    assert puerta["available"] is True
    assert puerta["traspasos"] == 9
    assert puerta["nuestros"] == 4
    assert puerta["compras_al_computer"] == 182

    assert "9" in puerta["reason"] and "182" in puerta["reason"], (
        "el dato de la puerta tiene que llevar los dos numeros: "
        "nueve traspasos no dicen nada sin las 182 compras al lado"
    )

    # SIN RECUENTO NO SE INVENTA UNO.
    sin_puerta = partir_la_lista(CANDIDATOS, UNIVERSO)

    assert sin_puerta["puerta"]["traspasos"] is None, (
        "sin recuento, el numero es None y no un cero que parezca "
        "medido"
    )

    assert sin_puerta["puerta"]["available"] is False

    print("  OK  la puerta viaja con su `n` al lado de la segunda lista")


# ============================================================
# 7. APAGADO
# ============================================================


def test_esto_sigue_apagado():

    assert ENCENDIDO is False, (
        "este encargo dice construir y parar"
    )

    assert esta_encendido() is False

    # Pero calcula.
    assert partir_la_lista(
        CANDIDATOS, UNIVERSO, puerta=PUERTA
    )["available"]

    assert tabla_por_plazas(
        ONCE, RECAMBIOS, factor_de=factor_de, caja_ahora=CAJA
    )["available"]

    # Y `de_quien_es` contesta sin fila, sin reventar.
    assert de_quien_es(None)["grupo"] == HAY_QUE_PEDIRSELO

    print("  OK  la lista calcula, se publica y sigue apagada")


TESTS = [
    test_la_lista_dice_de_quien_es,
    test_el_mercado_libre_entra_en_la_lista,
    test_no_se_vende_un_titular_sin_recambio,
    test_el_guardarrail_mira_titularidad,
    test_la_tabla_por_plazas_empieza_por_la_peor,
    test_la_puerta_viaja_con_la_segunda_lista,
    test_esto_sigue_apagado,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LA LISTA DE LA COMPRA V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
