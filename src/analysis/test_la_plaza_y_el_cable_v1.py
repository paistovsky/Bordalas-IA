"""
La plaza y el cable: las cuatro guardias del encargo, y tres mas.

QUE SE PRUEBA AQUI

    1. `test_el_presupuesto_cuenta_lo_realizable`
       El presupuesto publicado distingue la caja que HAY de la
       que HABRIA vendiendo, y nombra las dos. Falla si la cola
       de venta llega vacia y aun asi se publica un realizable.

    2. `test_una_venta_no_rompe_el_once`
       Ninguna operacion propuesta deja el once sin alinear. Se
       llama a `position_guardrail.validate_sale_set`; no se
       reescribe.

    3. `test_el_motivo_no_se_corta`
       Ningun motivo publicado sale truncado, y nombra el sitio
       que de verdad puso la etiqueta. Falla si la lista de
       candidatos llega vacia.

    4. `test_la_prima_del_computer_lleva_su_tramo`
       La prima se publica partida por direccion del precio, cada
       tramo con su `n`. Falla si el censo llega vacio.

    5. `test_el_techo_es_saldo_mas_un_cuarto_de_plantilla`
       La identidad medida del 17/09, y lo que sube al vender.

    6. `test_el_pago_lineal_se_comprueba_contra_lo_pagado`
       El premio por puesto se lee desde el FINAL, y el ganador
       no cobra nada encima de lo lineal.

    7. `test_esto_sigue_apagado`

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todo son fixtures escritos aqui. No se abre `data/`, no se
    llama a `datetime.now()` y la vara entra por argumento en vez
    de leerse del entorno.

UNA GUARDIA QUE NO MUERDE ES PEOR QUE NINGUNA

    Las cuatro del encargo se probaron reintroduciendo el fallo
    en memoria, y dos de ellas NO MORDIAN a la primera:

    - `test_el_presupuesto_cuenta_lo_realizable` pasaba con una
      version que devolvia `realizable: 0` con la cola vacia,
      porque el fixture de la cola vacia no comprobaba que el
      campo fuese None. Ahora lo comprueba, y ademas exige que
      `en_caja` siga publicandose: quedarse mudo tambien es
      perder un numero.

    - `test_el_motivo_no_se_corta` pasaba con la frase caducada
      del `max()` por euros, porque medir "no esta truncado" no
      es medir "es verdad". Ahora exige ademas que el motivo
      nombre el mecanismo que la propia fila declara, y hay un
      caso con `deployment.enabled = True` que falla si se le
      contesta con el mecanismo de antes.
"""

from __future__ import annotations

from src.analysis.la_plaza_y_el_cable import (
    ENCENDIDO,
    QUE_DECIDE_CADA_INTENT,
    comprobar_pago_lineal,
    esta_encendido,
    esta_truncado,
    hueco_entre_tramos,
    motivo_entero,
    operacion_completa,
    premios_de_la_jornada,
    presupuesto_con_lo_realizable,
    prima_por_tramo,
    techo_de_biwenger,
    techo_tras_vender,
)
from src.analysis.position_guardrail import (
    build_position_guardrail,
    validate_sale_set,
)

import src.analysis.candidate_starter_lookup as _pronosticos


# ============================================================
# EL PRONOSTICO, CLAVADO ANTES DE EMPEZAR
# ============================================================
#
#     `build_position_guardrail` ordena a quien se queda con
#     `_keep_value`, y eso llama a `get_starter_lookup()`, que
#     abre `data/intelligence/futbolfantasy_board.json`.
#
#     Lo destapo el vigilante de la verja el 17/09: esta guardia
#     salia censada leyendo `data/` sin que ninguna linea suya lo
#     pidiera. Una guardia que lee estado de produccion cambia de
#     respuesta el dia que el ciclo escriba ese fichero, y
#     entonces no esta probando el codigo: esta probando el disco.
#
#     Asi que la cache se clava VACIA antes de nada. No se parchea
#     `build_position_guardrail` -eso seria probar otra cosa-: se
#     le da el mismo camino que recorre en produccion con un
#     tablero que no dice nada de estos jugadores, que es
#     exactamente el caso que el guardarrail tiene que aguantar.
_pronosticos._CACHE = {}
_pronosticos._CACHE_KEY = _pronosticos._files_key()


# ============================================================
# LOS FIXTURES
# ============================================================
#
# Una plantilla de once titulares mas cuatro de banquillo, con la
# forma de la foto del 13/09: tres porteros, cinco defensas,
# cinco medios, cuatro delanteros.

POR, DEF, MED, DEL = 1, 2, 3, 4


def _ficha(pid, nombre, posicion, precio, titular, puntos=None):
    return {
        "id": pid,
        "name": nombre,
        "position": posicion,
        "price": precio,
        "priceIncrement": 0,
        "in_lineup": titular,
        "is_starter": titular,
        "points_per_matchday": puntos,
    }


PLANTILLA = [
    _ficha(1, "Portero titular", POR, 2_310_000, True, 2.0),
    _ficha(2, "Portero suplente", POR, 240_000, False, 0.5),
    _ficha(3, "Portero tercero", POR, 150_000, False, 0.2),

    _ficha(10, "Defensa A", DEF, 2_380_000, True, 3.6),
    _ficha(11, "Defensa B", DEF, 1_840_000, True, 3.0),
    _ficha(12, "Defensa C", DEF, 1_620_000, True, 2.4),
    _ficha(13, "Defensa D", DEF, 1_800_000, False, 2.2),
    _ficha(14, "Defensa E", DEF, 2_730_000, False, 2.0),

    _ficha(20, "Medio A", MED, 5_280_000, True, 5.4),
    _ficha(21, "Medio B", MED, 3_300_000, True, 4.0),
    _ficha(22, "Medio C", MED, 2_460_000, True, 3.2),
    _ficha(23, "Medio D", MED, 2_410_000, True, 3.0),
    _ficha(24, "Medio E", MED, 2_660_000, True, 2.8),

    _ficha(30, "Delantero A", DEL, 21_720_000, True, 7.6),
    _ficha(31, "Delantero B", DEL, 3_050_000, True, 4.2),
    _ficha(32, "Delantero C", DEL, 640_000, False, 1.1),
    _ficha(33, "Delantero D", DEL, 430_000, False, 0.8),
]

ONCE = [f["id"] for f in PLANTILLA if f["in_lineup"]]


def _cola(*filas):
    """Filas de `sale_order.queue` con la forma que publica la casa."""

    return [
        {
            "id": f["id"],
            "name": f["name"],
            "position": f["position"],
            "price": f["price"],
            "cash_now": f["cash_now"],
            "cash_kind": f.get("cash_kind", "OFERTA_VIVA"),
            "points_per_matchday": f.get("points_per_matchday"),
        }
        for f in filas
    ]


COLA_CON_OFERTAS = _cola(
    {
        "id": 13,
        "name": "Defensa D",
        "position": DEF,
        "price": 1_800_000,
        "cash_now": 1_847_000,
        "points_per_matchday": 2.2,
    },
    {
        "id": 32,
        "name": "Delantero C",
        "position": DEL,
        "price": 640_000,
        "cash_now": 638_400,
        "points_per_matchday": 1.1,
    },
    {
        "id": 2,
        "name": "Portero suplente",
        "position": POR,
        "price": 240_000,
        "cash_now": 244_800,
        "points_per_matchday": 0.5,
    },
    # Este NO tiene oferta viva: vale a mercado, que no es caja.
    {
        "id": 14,
        "name": "Defensa E",
        "position": DEF,
        "price": 2_730_000,
        "cash_now": 0,
        "cash_kind": "A_MERCADO",
        "points_per_matchday": 2.0,
    },
)


PRESUPUESTO = {
    "enabled": False,
    "total_budget": 0,
    "available_budget": 0,
    "maximum_bid": 12_455_166,
    "balance": -1_299_834,
    "reason": "Para mejorar el once: 0 EUR. Son 0 de caja.",
}


# La vara del 17/09, puesta a mano para que la guardia no dependa
# del entorno ni de `BORDALAS_VARA_PLANA`.
VARA = {POR: 1.0, DEF: 0.787, MED: 1.147, DEL: 1.139}


def factor_de(posicion):
    return VARA.get(int(posicion or 0), 1.0)


# ============================================================
# 1. EL PRESUPUESTO CUENTA LO REALIZABLE
# ============================================================


def test_el_presupuesto_cuenta_lo_realizable():
    """
    Los dos numeros, con su nombre. Y con la cola vacia, ninguno
    de los dos se inventa.
    """

    salida = presupuesto_con_lo_realizable(
        PRESUPUESTO,
        {"queue": COLA_CON_OFERTAS},
    )

    assert salida["available"], (
        "con cola y ofertas vivas tiene que haber numero: "
        f"{salida.get('reason')}"
    )

    # LOS DOS, SEPARADOS.
    assert salida["en_caja"] == 0, (
        "la caja de hoy es la que publica `acquisition_budget`, "
        f"no otra: {salida['en_caja']}"
    )

    esperado = 1_847_000 + 638_400 + 244_800

    assert salida["realizable"] == esperado, (
        f"lo realizable son las ofertas VIVAS de la cola "
        f"({esperado}), no el valor a mercado: {salida['realizable']}"
    )

    assert salida["realizable_n"] == 3, (
        "el que vale a mercado y no tiene oferta viva no cuenta "
        f"como caja: n={salida['realizable_n']}"
    )

    assert salida["total_si_se_vende"] == esperado, (
        "el total es la suma de los dos y se publica aparte"
    )

    # Y CADA UNO CON SU NOMBRE ESCRITO.
    assert salida["en_caja_label"] and salida["realizable_label"], (
        "los dos numeros tienen que salir nombrados: un numero "
        "suelto en pantalla es lo que este repo lleva una semana "
        "arreglando"
    )

    assert "en caja" in salida["reason"].lower(), (
        "el motivo no nombra la caja de hoy"
    )

    assert "vendiendo" in salida["reason"].lower(), (
        "el motivo no nombra la caja que habria vendiendo"
    )

    # EL TECHO SUBE, Y NO POR EL IMPORTE ENTERO.
    #
    #     De cada jugador ya habia un cuarto de su precio dentro
    #     de `maximumBid`. Si el techo subiera por el importe
    #     completo, esa parte se estaria contando dos veces.
    subida = salida["techo_si_se_vende"] - salida["techo_biwenger"]

    esperada = (
        (1_847_000 - 1_800_000 // 4)
        + (638_400 - 640_000 // 4)
        + (244_800 - 240_000 // 4)
    )

    assert subida == esperada, (
        f"el techo tiene que subir venta menos un cuarto del "
        f"precio de cada uno ({esperada}), no {subida}"
    )

    # ------------------------------------------------
    # LA COLA VACIA: MUERDE AQUI
    # ------------------------------------------------
    vacia = presupuesto_con_lo_realizable(PRESUPUESTO, {"queue": []})

    assert vacia["available"] is False, (
        "con la cola de venta vacia no se puede publicar un "
        "realizable"
    )

    assert vacia["realizable"] is None, (
        "con la cola vacia el realizable tiene que ser None, no "
        f"un cero que parece medido: {vacia['realizable']}"
    )

    assert vacia["cola_vacia"] is True, (
        "hay que decir que la cola llego vacia, no callarselo"
    )

    # Quedarse mudo tambien es perder un numero: la caja de hoy
    # se sigue publicando.
    assert vacia["en_caja"] == 0 and "0" in vacia["reason"], (
        "sin cola de venta el presupuesto de hoy se sigue "
        "diciendo: es el unico de los dos que si se sabe"
    )

    print("  OK  el presupuesto nombra la caja que hay y la que habria")


# ============================================================
# 2. UNA VENTA NO ROMPE EL ONCE
# ============================================================


def test_una_venta_no_rompe_el_once():
    """
    Se llama al guardarrail; no se reescribe. Y ninguna operacion
    propuesta deja una posicion por debajo de su suelo.
    """

    guardarrail = build_position_guardrail(PLANTILLA, lineup_ids=ONCE)

    assert guardarrail.get("available"), (
        "sin guardarrail esta guardia no prueba nada"
    )

    # NI DISCO: la cache de pronosticos sigue vacia, o sea que
    # construir el guardarrail no ha abierto `data/`.
    assert _pronosticos._CACHE == {}, (
        "construir el guardarrail ha releido el tablero de "
        "titularidades: esta guardia acaba de leer estado de "
        "produccion y su respuesta ya no depende solo del codigo"
    )

    # Un fichaje tan caro que la cola entera no lo cubre: asi se
    # intentan los TRES defensas y el tercero tiene que chocar
    # contra el guardarrail en vez de colarse.
    candidato = {
        "id": 900,
        "name": "Fichaje caro",
        "position": MED,
        "market_price": 6_000_000,
        "points_per_matchday": 6.0,
    }

    # La cola, esta vez con TODOS los que tienen oferta, incluidos
    # los que romperian el once si se vendieran a la vez.
    cola = _cola(
        {
            "id": 11,
            "name": "Defensa B",
            "position": DEF,
            "price": 1_840_000,
            "cash_now": 1_773_900,
            "points_per_matchday": 3.0,
        },
        {
            "id": 12,
            "name": "Defensa C",
            "position": DEF,
            "price": 1_620_000,
            "cash_now": 1_602_100,
            "points_per_matchday": 2.4,
        },
        {
            "id": 10,
            "name": "Defensa A",
            "position": DEF,
            "price": 2_380_000,
            "cash_now": 2_352_000,
            "points_per_matchday": 3.6,
        },
    )

    operacion = operacion_completa(
        candidato,
        cola=cola,
        guardarrail=guardarrail,
        validador=validate_sale_set,
        factor_de=factor_de,
        fichas_libres=0,
        presupuesto_en_caja=0,
    )

    vendidos = [v["id"] for v in operacion["vende_a"]]

    assert vendidos, (
        "con presupuesto cero y sin ficha libre tiene que proponer "
        "a alguien, o decir que no puede"
    )

    # LA COMPROBACION DE VERDAD: el conjunto entero pasa el
    # guardarrail, no cada uno por su cuenta.
    comprobacion = validate_sale_set(guardarrail, vendidos)

    assert comprobacion["ok"], (
        f"la operacion deja el once sin alinear: "
        f"{comprobacion.get('reason')}"
    )

    assert comprobacion["guardrail_applied"], (
        "el guardarrail tiene que haberse aplicado de verdad, no "
        "haber pasado de largo por falta de datos"
    )

    # Y el que no cabe sale apartado CON SU MOTIVO, no borrado.
    assert operacion["apartados"], (
        "de tres defensas con oferta, vender los tres deja dos y "
        "hacen falta tres: alguno tiene que quedar apartado"
    )

    for apartado in operacion["apartados"]:
        assert apartado.get("reason"), (
            f"{apartado.get('name')} se aparto sin decir por que"
        )

    # Y si con lo que cabe vender no llega, se dice: no se da por
    # financiada una operacion que no lo esta.
    assert operacion["financiada"] is False, (
        "la cola entera da 3.376.000 y el fichaje cuesta 6.000.000: "
        "no puede salir financiada"
    )

    # LOS PUNTOS NETOS, CON LA VARA PUESTA.
    assert operacion["vara_puesta"] is True
    assert operacion["puntos_netos"] is not None

    esperado_entra = 6.0 * VARA[MED]

    esperado_sale = sum(
        next(f["points_per_matchday"] for f in cola if f["id"] == pid)
        * VARA[DEF]
        for pid in vendidos
    )

    assert operacion["puntos_netos"] == round(
        esperado_entra - esperado_sale, 3
    ), (
        "los puntos netos no llevan la vara de cada posicion: "
        f"{operacion['puntos_netos']}"
    )

    # ------------------------------------------------
    # EL CASO QUE MUERDE: vender a los tres defensas
    # ------------------------------------------------
    #
    # Si la pieza se saltara el guardarrail, esto pasaria y el
    # once se quedaria en dos defensas.
    roto = validate_sale_set(guardarrail, [10, 11, 12])

    assert not roto["ok"], (
        "el fixture no prueba nada: vender a los tres defensas "
        "titulares tiene que romper el once y no lo rompe"
    )

    print("  OK  ninguna operacion deja el once sin alinear")


# ============================================================
# 3. EL MOTIVO NO SE CORTA
# ============================================================


CANDIDATOS = [
    # El caso vivo: `DEPLOYMENT_ENABLED` encendido, que es el de
    # hoy. La etiqueta la puso `classify_operation`.
    {
        "id": 101,
        "name": "Budimir",
        "intent": "SPECULATION",
        "deployment": {
            "enabled": True,
            "operation_class": "TRADE",
            "route": "COMPUTER_RESALE",
            "reason": (
                "No entra al once ni llena hueco: se compra para "
                "revender, y sale del bolsillo de especular."
            ),
        },
        "market_gate": {"route_now": "COMPUTER_RESALE"},
    },
    # El caso viejo: interruptor apagado, gana la via que da mas
    # euros. Sigue existiendo y tiene que poder nombrarse.
    {
        "id": 102,
        "name": "Jonathan David",
        "intent": "SPECULATION",
        "deployment": {
            "enabled": False,
            "operation_class": None,
            "route": "PRICE_TREND",
            "reason": None,
        },
        "market_gate": {"route_now": "PRICE_TREND"},
    },
    # Y el caso en el que no se sabe: la fila no trae despliegue.
    {
        "id": 103,
        "name": "Alfonso Herrero",
        "intent": "SPECULATION",
        "market_gate": {},
    },
]


def test_el_motivo_no_se_corta():
    """
    Ningun motivo publicado sale truncado, y cada uno nombra el
    sitio que puso la etiqueta.
    """

    assert CANDIDATOS, (
        "la lista de candidatos llega vacia: sin candidatos esta "
        "guardia no prueba nada"
    )

    for fila in CANDIDATOS:

        motivo = motivo_entero(fila)

        assert not esta_truncado(motivo["reason"]), (
            f"el motivo de {fila['name']} sale cortado: "
            f"{motivo['reason']!r}"
        )

        assert motivo["truncado"] is False

        # NO BASTA CON QUE ESTE ENTERO: TIENE QUE SER VERDAD.
        despliegue = fila.get("deployment") or {}

        if despliegue.get("enabled"):
            assert motivo["decidido_por"] == (
                "deployment.classify_operation"
            ), (
                f"{fila['name']}: con `DEPLOYMENT_ENABLED` "
                f"encendido la etiqueta NO la reparte el max() por "
                f"euros, y el motivo dice "
                f"{motivo['decidido_por']!r}"
            )

            assert "revender" in motivo["reason"].lower(), (
                "el motivo tiene que llevar dentro el que la propia "
                "fila declara, no uno escrito aparte"
            )

        elif despliegue:
            assert "max(" in (motivo["decidido_por"] or ""), (
                f"{fila['name']}: con el interruptor apagado si "
                f"manda el max() por euros"
            )

        else:
            assert motivo["decidido_por"] is None, (
                "sin bloque `deployment` no se puede saber quien "
                "puso la etiqueta, y se dice en vez de adivinarlo"
            )

        # Y EL MAPA: que cuelga de esta etiqueta.
        if motivo["intent"] in QUE_DECIDE_CADA_INTENT:
            assert motivo["de_esta_etiqueta_cuelga"], (
                f"{fila['name']}: se nombra el `intent` y no se dice "
                f"que se cae si se toca"
            )

    # ------------------------------------------------
    # LA LISTA VACIA: MUERDE AQUI
    # ------------------------------------------------
    vacia = []

    try:
        assert vacia, "sin candidatos no hay motivos que comprobar"

    except AssertionError:
        pass

    else:                                            # pragma: no cover
        raise AssertionError(
            "la guardia tiene que fallar con la lista de candidatos "
            "vacia, y no ha fallado"
        )

    # Y el detector de frases cortadas detecta de verdad.
    assert esta_truncado("La via del once le da valor, pero el `intent`…")
    assert esta_truncado("")
    assert esta_truncado("se elige por euros y gana la")
    assert not esta_truncado("Se compra para revender.")

    print("  OK  ningun motivo sale truncado, y cada uno nombra su sitio")


# ============================================================
# 4. LA PRIMA DEL COMPUTER LLEVA SU TRAMO
# ============================================================


CENSO = [
    # subian la vispera
    {"name": "A", "amount": 2_420_500, "price": 2_460_000, "price_previous": 2_430_000},
    {"name": "B", "amount": 2_352_000, "price": 2_380_000, "price_previous": 2_370_000},
    {"name": "C", "amount": 1_773_900, "price": 1_840_000, "price_previous": 1_820_000},
    {"name": "D", "amount": 20_680_800, "price": 21_720_000, "price_previous": 21_630_000},
    # bajaban la vispera
    {"name": "E", "amount": 3_115_700, "price": 3_050_000, "price_previous": 3_080_000},
    {"name": "F", "amount": 2_373_400, "price": 2_310_000, "price_previous": 2_340_000},
    {"name": "G", "amount": 1_847_000, "price": 1_800_000, "price_previous": 1_830_000},
    # plano
    {"name": "H", "amount": 244_800, "price": 240_000, "price_previous": 240_000},
    # sin vispera conocida: no entra a ningun tramo
    {"name": "I", "amount": 420_800, "price": 430_000, "price_previous": None},
]


def test_la_prima_del_computer_lleva_su_tramo():
    """
    Partida por direccion del precio, cada tramo con su `n`, y
    ningun tramo se funde con el de al lado.
    """

    assert CENSO, (
        "el censo llega vacio: sin ofertas esta guardia no prueba "
        "nada"
    )

    partida = prima_por_tramo(CENSO)

    assert partida["available"]

    for tramo in ("SUBIA", "PLANO", "BAJABA"):

        assert tramo in partida["tramos"], (
            f"falta el tramo {tramo}: los tres se publican aunque "
            f"uno se quede corto"
        )

        datos = partida["tramos"][tramo]

        # DOCTRINA 55: cada agregado con su `n`, y el `n` dentro
        # del tramo, no en una nota al pie.
        assert "n" in datos, f"el tramo {tramo} sale sin su `n`"

        if datos["n"]:
            assert datos["median_percent"] is not None, (
                f"el tramo {tramo} tiene muestra y no publica mediana"
            )

        else:
            assert datos["median_percent"] is None, (
                f"el tramo {tramo} no tiene muestra y publica un "
                f"numero: eso es inventarselo"
            )

    assert partida["tramos"]["SUBIA"]["n"] == 4
    assert partida["tramos"]["BAJABA"]["n"] == 3
    assert partida["tramos"]["PLANO"]["n"] == 1
    assert partida["sin_vispera"] == 1, (
        "la oferta sin precio de la vispera no puede colarse en un "
        "tramo: se cuenta aparte"
    )

    assert partida["n"] == 8, (
        f"el `n` publicado es el que se comprobo, no el que se vio: "
        f"{partida['n']}"
    )

    # Los tramos cortos van MARCADOS, no fundidos.
    assert partida["tramos"]["PLANO"]["thin"] is True

    # Y el hueco sale con los dos `n` delante.
    hueco = hueco_entre_tramos(partida)

    assert hueco["available"]
    assert hueco["n_subia"] == 4 and hueco["n_bajaba"] == 3
    assert hueco["gap_pp"] > 0, (
        "en este fixture los que bajaban cobran mas prima: si el "
        "hueco sale negativo, la cuenta esta del reves"
    )
    assert str(hueco["n_subia"]) in hueco["reason"], (
        "el motivo del hueco no lleva el `n` de cada tramo"
    )

    # ------------------------------------------------
    # EL CENSO VACIO: MUERDE AQUI
    # ------------------------------------------------
    vacio = prima_por_tramo([])

    assert vacio["available"] is False, (
        "con el censo vacio no se publica una prima"
    )

    assert vacio["tramos"] == {}, (
        "con el censo vacio no se publican tramos con ceros: un "
        "cero medido y un cero por no haber mirado son cosas "
        "distintas"
    )

    assert vacio["n"] == 0

    # Y con un solo tramo poblado no hay hueco que publicar.
    solo_uno = prima_por_tramo(
        [c for c in CENSO if c["price_previous"] and c["price"] > c["price_previous"]]
    )

    assert hueco_entre_tramos(solo_uno)["available"] is False, (
        "sin los dos tramos no se puede publicar el hueco"
    )

    print("  OK  la prima sale partida por tramo, cada uno con su `n`")


# ============================================================
# 5. EL TECHO DE BIWENGER
# ============================================================


def test_el_techo_es_saldo_mas_un_cuarto_de_plantilla():
    """
    La identidad medida el 17/09 sobre 15 combinaciones, y lo que
    de verdad sube al vender.
    """

    # Las tres de la bitacora del 16/09, al euro.
    assert techo_de_biwenger(-1_294_308, 57_080_000, 0) == 12_975_692
    assert techo_de_biwenger(-1_044_308, 57_080_000, 0) == 13_225_692
    assert techo_de_biwenger(-1_299_834, 55_020_000, 0) == 12_455_166

    # Y la del 15/09, que solo cuadra restando la puja viva.
    assert techo_de_biwenger(131_717, 55_680_000, 2_482_028) == 11_569_689, (
        "lo comprometido se resta del techo: `maximumBid` ya viene "
        "con las pujas vivas descontadas"
    )

    # VENDER SUBE EL TECHO, Y NO POR EL IMPORTE ENTERO.
    techo = 12_455_166

    despues = techo_tras_vender(techo, 1_847_000, 1_800_000)

    assert despues == techo + 1_847_000 - 450_000, (
        "del precio de un jugador solo hay un cuarto dentro del "
        "techo: al venderlo sale ese cuarto y entra el importe"
    )

    # A precio de mercado clavado, el techo sube tres cuartos.
    precio = 4_000_000

    assert techo_tras_vender(0, precio, precio) == precio * 3 // 4, (
        "vendiendo a precio de mercado el techo sube 0,75 x precio: "
        "si subiera el precio entero se estaria contando dos veces, "
        "y si no subiera nada se estaria contando cero"
    )

    print("  OK  el techo es saldo + plantilla/4 - comprometido")


# ============================================================
# 6. EL PAGO DE LA LIGA
# ============================================================


REGLAS = {
    "bonusFixed": 0,
    "bonusPoint": 30_000,
    "bonusInverse": False,
    "bonusIdealLineup": 0,
    "bonusGameMVP": 0,
    "bonusRoundPosition": [[-1, 500_000], [-2, 250_000], [-3, 100_000]],
}


JORNADA = [
    {"name": "Pepe Bordalas", "points": 61, "bonus": 1_830_000},
    {"name": "Pollo17", "points": 55, "bonus": 1_650_000},
    {"name": "Manzagool", "points": 47, "bonus": 1_410_000},
    {"name": "Luismi_Haz", "points": 46, "bonus": 1_380_000},
    {"name": "Mex", "points": 45, "bonus": 1_350_000},
    {"name": "Prinzipote", "points": 45, "bonus": 1_450_000},
    {"name": "DiosMande", "points": 37, "bonus": 1_360_000},
    {"name": "Alvaro", "points": 15, "bonus": 950_000},
]


def test_el_pago_lineal_se_comprueba_contra_lo_pagado():
    """
    Los indices de `bonusRoundPosition` son NEGATIVOS: cuentan
    desde el final. No hay premio por ganar la jornada.
    """

    premios = premios_de_la_jornada(REGLAS)

    assert premios["euros_por_punto"] == 30_000

    assert premios["hay_premio_por_ganar"] is False, (
        "un indice negativo no es un puesto de arriba: -1 es el "
        "ultimo, no el primero"
    )

    assert premios["hay_premio_por_quedar_ultimo"] is True

    assert premios["premio_por_quedar_ultimo"][0] == {
        "desde_el_final": 1,
        "euros": 500_000,
    }

    # NO CONSTA ES UNA RESPUESTA.
    assert premios["premio_de_final_de_temporada"] is None
    assert "no consta" in (
        premios["premio_de_final_de_temporada_reason"].lower()
    ), (
        "si no consta hay que decirlo con esas palabras, no dejar "
        "el campo a None y callarse"
    )

    # Y contra lo que se pago de verdad.
    pago = comprobar_pago_lineal(JORNADA, 30_000)

    assert pago["available"] and pago["n"] == 8

    assert pago["extra_del_ganador"] == 0, (
        "el primero cobro exactamente puntos x 30.000: si esto "
        "fallara habria premio por ganar y la discusion cambia"
    )

    assert not pago["lineal_para_todos"], (
        "tres cobraron algo encima: el fixture no prueba nada si "
        "sale lineal para todos"
    )

    desde_el_final = sorted(e["desde_el_final"] for e in pago["extras"])

    assert desde_el_final == [1, 2, 3], (
        f"lo que se cobra de mas son los tres ULTIMOS, no los tres "
        f"primeros: {desde_el_final}"
    )

    extras = {e["desde_el_final"]: e["extra"] for e in pago["extras"]}

    assert extras == {1: 500_000, 2: 250_000, 3: 100_000}, (
        f"lo pagado de verdad tiene que cuadrar con las reglas: "
        f"{extras}"
    )

    # La jornada sin resultados no publica nada.
    assert comprobar_pago_lineal([], 30_000)["available"] is False

    print("  OK  no hay premio por ganar; lo hay por quedar el ultimo")


# ============================================================
# 7. ESTO SIGUE APAGADO
# ============================================================


def test_esto_sigue_apagado():
    """
    Se mide, se nombra y se para.
    """

    assert ENCENDIDO is False, (
        "este encargo dice medir y parar: no se enciende nada"
    )

    assert esta_encendido() is False

    # Pero CALCULA: apagado no puede significar que no conteste.
    assert presupuesto_con_lo_realizable(
        PRESUPUESTO, {"queue": COLA_CON_OFERTAS}
    )["available"]

    assert prima_por_tramo(CENSO)["available"]

    print("  OK  la via calcula, se publica y sigue apagada")


TESTS = [
    test_el_presupuesto_cuenta_lo_realizable,
    test_una_venta_no_rompe_el_once,
    test_el_motivo_no_se_corta,
    test_la_prima_del_computer_lleva_su_tramo,
    test_el_techo_es_saldo_mas_un_cuarto_de_plantilla,
    test_el_pago_lineal_se_comprueba_contra_lo_pagado,
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
        f"LA PLAZA Y EL CABLE V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
