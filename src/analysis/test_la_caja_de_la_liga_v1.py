"""
La caja de los siete: reconstruida, no derivada.

SINTOMA

    10/09/2026: la pantalla publicaba 4,37 M de caja nuestra
    contra 4.474.383 reales de la API. Cien mil exactos.

    De ese numero cuelgan CAJA, PATRIMONIO, TOPE, PUJA %, MAX.
    VISTO y AMENAZA. Media pantalla colgando de un dato torcido.

CAUSA

    El abono de jornada se derivaba: `puntos x 30.000`. Eso deja
    fuera el PREMIO POR PUESTO, y nosotros fuimos 5os en la J2.

    Y una segunda, encontrada por la misma comparacion: la
    Jornada 1 se jugo partida y la liga la ignora
    (`splitRound: "ignoreFirst"`). Contarla sumaba 870.000 de
    mas.

CONSECUENCIA

    Estas tres guardias llevan el nombre de las tres cosas que
    tienen que seguir siendo verdad, y ninguna puede pasar en
    vacio: con la lista de eventos vacia, FALLAN.

    Los eventos son los REALES del tablon, copiados aqui como
    fixture. No se leen de `data/` -Regla 23- pero tampoco se
    inventan: son los que pagaron.
"""

from __future__ import annotations

from src.analysis.caja_de_la_liga import (
    EUROS_POR_PUNTO,
    PREMIO_POR_PUESTO,
    SALDO_INICIAL,
    cuadra,
    jornadas_que_pagan,
    reconstruir,
)


YO = 14175949

# ============================================================
# LOS EVENTOS REALES, COPIADOS DEL TABLON
# ============================================================

# La Jornada 1: se jugo partida y la liga la IGNORA. Fijate en
# que es la unica que paga `puntos x 30.000` a todos, sin un solo
# premio por puesto: la propia Biwenger no la trata como jornada
# de clasificacion.
J1_IGNORADA = {
    "type": "roundFinished",
    "date": 1787220405,
    "content": {
        "round": {"id": 4899, "name": "Jornada 1"},
        "results": [
            {"user": {"id": 14178736}, "points": 42, "bonus": 1260000},
            {"user": {"id": 14151726}, "points": 31, "bonus": 930000},
            {"user": {"id": YO}, "points": 29, "bonus": 870000},
            {"user": {"id": 14156489}, "points": 29, "bonus": 870000},
            {"user": {"id": 14145555}, "points": 21, "bonus": 630000},
            {"user": {"id": 14154203}, "points": 14, "bonus": 420000},
            {"user": {"id": 14176382}, "points": 10, "bonus": 300000},
        ],
    },
}

# La segunda parte de esa misma jornada. ESTA si paga, y ya trae
# los premios por puesto.
J1_APLAZADA = {
    "type": "roundFinished",
    "date": 1787906190,
    "content": {
        # Tal cual llega: sin `short`. Escribiendo esto le
        # puse un "short": "J1" que el evento real no tiene, y
        # la agrupacion dejo de funcionar. Un fixture que no es
        # el dato real prueba otra cosa.
        "round": {
            "id": 4937,
            "name": "Jornada 1 (aplazada)",
            "part": 2,
        },
        "results": [
            {"user": {"id": 14178736}, "points": 59, "bonus": 1770000},
            {"user": {"id": 14151726}, "points": 43, "bonus": 1290000},
            {"user": {"id": YO}, "points": 41, "bonus": 1230000},
            {"user": {"id": 14154203}, "points": 36, "bonus": 1080000},
            {"user": {"id": 14145555}, "points": 31, "bonus": 1030000},
            {"user": {"id": 14156489}, "points": 28, "bonus": 1090000},
            {"user": {"id": 14176382}, "points": 26, "bonus": 1280000},
        ],
    },
}

# LA JORNADA 2, ENTERA Y REAL. Es el caso del dueno:
#
#   Pepe        31 pts  ->  1.030.000   (5o, +100.000)
#   Prinzipote  28 pts  ->  1.090.000   (6o, +250.000)
#   Manzagool   28 pts  ->  1.340.000   (7o, +500.000)
#
# Los dos ultimos EMPATAN a 28 puntos y cobran distinto: por eso
# el premio no se deduce de la posicion, se resta.
J2 = {
    "type": "roundFinished",
    "date": 1787670557,
    "content": {
        "round": {"id": 4900, "name": "Jornada 2"},
        "results": [
            {"user": {"id": 14145555}, "points": 58, "bonus": 1740000},
            {"user": {"id": 14156489}, "points": 55, "bonus": 1650000},
            {"user": {"id": 14151726}, "points": 38, "bonus": 1140000},
            {"user": {"id": 14178736}, "points": 32, "bonus": 960000},
            {"user": {"id": YO}, "points": 31, "bonus": 1030000},
            {"user": {"id": 14154203}, "points": 28, "bonus": 1090000},
            {"user": {"id": 14176382}, "points": 28, "bonus": 1340000},
        ],
    },
}

# Una compra y una venta reales nuestras, para que la caja tenga
# las cuatro patas y no solo la jornada.
COMPRA_EXPOSITO = {
    "type": "market",
    "date": 1788584792,
    "content": [
        {"player": 19862, "to": {"id": YO}, "amount": 5147000}
    ],
}

VENTA_PUERTA = {
    "type": "transfer",
    "date": 1788652942,
    "content": [
        {"player": 41271, "from": {"id": YO}, "amount": 3377100}
    ],
}

RACHA_DE_POLLO = {
    "type": "bonus",
    "date": 1788470760,
    "content": [
        {
            "user": {"id": 14145555},
            "amount": 250000,
            "reason": "dailyStreak",
        }
    ],
}

TABLON = [
    J1_IGNORADA,
    J2,
    J1_APLAZADA,
    COMPRA_EXPOSITO,
    VENTA_PUERTA,
    RACHA_DE_POLLO,
]


# ============================================================
# 1. LA CAJA CUADRA CON LA REAL
# ============================================================


def test_la_caja_reconstruida_cuadra_con_la_real() -> None:
    """
    La comprobacion permanente, en pequeno.

    Es la UNICA auditoria posible de un numero que no podemos
    ver: la liga tiene `settings.balance = "hidden"`, asi que de
    los seis rivales no hay saldo contra el que contrastar. Si el
    metodo acierta con el nuestro, acierta con el suyo.

    Y ya demostro que sirve: fue esta comparacion la que
    encontro el `splitRound`, con 870.000 clavados.
    """

    salida = reconstruir(TABLON, [YO])

    assert salida["available"], salida["reason"]

    caja = salida["managers"][YO]["cash"]

    esperada = (
        SALDO_INICIAL
        + 1_030_000          # J2, con su premio de 5o
        + 1_230_000          # J1 aplazada
        + 3_377_100          # venta de Gustavo Puerta
        - 5_147_000          # compra de Exposito
    )

    assert caja == esperada, (
        f"la caja sale {caja} y tenia que salir {esperada}"
    )

    # Y la comparacion contra el saldo "real" tiene que verlo.
    assert cuadra(caja, esperada)["ok"] is True

    fallo = cuadra(caja, esperada - 100_000)

    assert fallo["ok"] is False, fallo
    assert fallo["difference"] == 100_000, fallo
    assert "NO CUADRA" in fallo["reason"], fallo


def test_la_comprobacion_no_pasa_con_las_manos_vacias() -> None:
    """
    Regla 24. Sin las dos cifras no hay comprobacion, y eso NO es
    un aprobado: es un "no se sabe", y se dice.
    """

    for a, b in ((None, 100), (100, None), (None, None)):
        salida = cuadra(a, b)
        assert salida["available"] is False, (a, b, salida)
        assert salida["ok"] is None, (a, b, salida)


# ============================================================
# 2. EL PREMIO POR PUESTO SE PAGA
# ============================================================


def test_el_premio_por_puesto_se_paga() -> None:
    """
    LA JORNADA 2 REAL.

    `puntos x 30.000` se dejaba fuera esto, y son los cien mil
    del dueno. Medido sobre 4 jornadas x 7 managers, 12 de 12
    casos: 5o +100.000, 6o +250.000, 7o +500.000.
    """

    salida = reconstruir([J2], [YO])

    assert salida["available"], salida["reason"]

    libro = salida["managers"]

    # Nosotros: 31 puntos, 5os, 1.030.000.
    assert libro[YO]["matchday"] == 1_030_000, libro[YO]
    assert libro[YO]["matchday_premium"] == 100_000, libro[YO]

    assert (
        libro[YO]["matchday"]
        > 31 * EUROS_POR_PUNTO
    ), "el premio por puesto ha vuelto a perderse"

    # Los dos EMPATADOS a 28 puntos cobran distinto. Si el premio
    # se dedujera de la posicion, uno de los dos saldria mal.
    assert libro[14154203]["matchday_premium"] == 250_000, libro
    assert libro[14176382]["matchday_premium"] == 500_000, libro

    # Y los cuatro de arriba no cobran premio ninguno.
    for quien in (14145555, 14156489, 14151726, 14178736):
        assert libro[quien]["matchday_premium"] == 0, (
            quien,
            libro[quien],
        )

    # La tabla medida sigue siendo la que es.
    assert PREMIO_POR_PUESTO == {
        5: 100_000,
        6: 250_000,
        7: 500_000,
    }, PREMIO_POR_PUESTO


# ============================================================
# 3. LA JORNADA PARTIDA NO PAGA
# ============================================================


def test_la_jornada_partida_no_paga() -> None:
    """
    `splitRound: "ignoreFirst"`.

    La Jornada 1 se jugo en dos partes y la liga ignora la
    primera. Contarla metia 870.000 de mas en nuestra caja, y fue
    justo el hueco que delato el fallo.

    El evento de la primera parte NO trae `short`, asi que
    agrupar por el nombre crudo no las junta: "Jornada 1" contra
    "Jornada 1 (aplazada)". Por eso se quita el parentesis.
    """

    pagan = jornadas_que_pagan([J1_IGNORADA, J1_APLAZADA, J2])

    assert 4899 not in pagan, (
        "la primera parte de la jornada partida ha vuelto a pagar"
    )
    assert 4937 in pagan, pagan
    assert 4900 in pagan, pagan

    salida = reconstruir([J1_IGNORADA, J1_APLAZADA], [YO])

    assert salida["managers"][YO]["matchday"] == 1_230_000, (
        salida["managers"][YO]
    )

    assert "Jornada 1" in (salida["ignored_rounds"] or []), (
        f"no se dice que jornada no se pago: "
        f"{salida['ignored_rounds']}"
    )

    # Con el ajuste apagado, las dos pagan: la regla es de la
    # liga y tiene que poder mirarse desde fuera.
    todas = jornadas_que_pagan(
        [J1_IGNORADA, J1_APLAZADA], split_round="all"
    )

    assert 4899 in todas and 4937 in todas, todas


def test_la_jornada_ignorada_es_la_unica_sin_premio() -> None:
    """
    La confirmacion cruzada, y la razon para creerse la regla.

    La Jornada 1 es la unica que paga `puntos x 30.000` EXACTOS a
    los siete, sin un solo premio por puesto. La propia Biwenger
    no la trata como jornada de clasificacion.
    """

    for fila in J1_IGNORADA["content"]["results"]:
        assert (
            fila["bonus"] == fila["points"] * EUROS_POR_PUNTO
        ), fila

    premiadas = 0

    for jornada in (J2, J1_APLAZADA):
        for fila in jornada["content"]["results"]:
            if fila["bonus"] != fila["points"] * EUROS_POR_PUNTO:
                premiadas += 1

    assert premiadas == 6, (
        f"las dos jornadas que pagan tenian que repartir tres "
        f"premios cada una y reparten {premiadas}"
    )


# ============================================================
# 4. NINGUNA PASA EN VACIO
# ============================================================


def test_sin_eventos_no_hay_caja_y_se_dice() -> None:
    """
    Doctrina 36. Si la reconstruccion no se puede hacer, la
    columna dice SIN DATO: no se vuelve al metodo viejo ni se
    pinta una estimacion con la misma cara que un numero medido.

    Y una guardia que pasara con la lista vacia no estaria
    comprobando nada.
    """

    for entrada in (None, [], [1, 2, 3], ["basura"]):

        salida = reconstruir(entrada, [YO])

        assert salida["available"] is False, (entrada, salida)
        assert salida["managers"] == {}, (entrada, salida)
        assert salida["reason"], (entrada, salida)

    # Y el saldo inicial NO se cuela como caja cuando no hay nada
    # que reconstruir: eso seria pintar 23,3 M de la nada.
    assert reconstruir([], [YO])["managers"] == {}


def test_el_motor_publica_el_cuadre_en_cada_vuelta() -> None:
    """
    La comprobacion permanente no sirve de nada si vive en un
    log. Tiene que viajar al estado publicado para poder salir en
    ROJO en la pantalla.
    """

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    motor = (
        raiz / "src" / "analysis" / "rival_intelligence_engine.py"
    ).read_text(encoding="utf-8")

    assert "caja_de_la_liga" in motor, (
        "el motor no reconstruye la caja: ha vuelto a derivarla "
        "de los puntos"
    )

    assert "cash_check" in motor, (
        "el motor no publica el cuadre"
    )

    assert 'manager["balance"] = None' in motor, (
        "sin reconstruccion el motor ya no dice SIN DATO: estara "
        "pintando un cero con cara de numero medido"
    )

    pantalla = (
        raiz / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"cash_check"' in pantalla, (
        "el cuadre no llega al estado publicado"
    )


def test_la_alarma_del_cuadre_solo_sale_si_esta_roja() -> None:
    """
    "Una alarma que no salta no ocupa sitio."

    Cuando la caja cuadra NO aparece nada nuevo en pantalla. La
    comprobacion corre igual en cada ciclo; lo que no hace es
    pedir sitio para decir que todo va bien.

    Y se compara contra `false` a proposito, no contra un valor
    falsy: un `null` es "no se ha podido comprobar", y eso no es
    una alarma -es la columna diciendo SIN DATO-.
    """

    from pathlib import Path

    app = (
        Path(__file__).parents[2]
        / "dashboard-v8"
        / "src"
        / "App.jsx"
    ).read_text(encoding="utf-8")

    assert "cash_check?.ok === false" in app, (
        "la alarma del cuadre no existe, o no se esconde cuando "
        "la caja cuadra"
    )

    # Un `&&` sobre el objeto entero saldria SIEMPRE, porque un
    # objeto es truthy. Es el fallo facil de escribir aqui.
    assert "{data.rivalIntel?.cash_check && (" not in app, (
        "la alarma saldria siempre: se esta comprobando el "
        "objeto, no el resultado"
    )


def test_la_tabla_de_clasificacion_no_ha_crecido() -> None:
    """
    El dueno lo dijo con todas las letras: la pantalla se queda
    EXACTAMENTE IGUAL. Mismas columnas, mismo orden, mismo
    aspecto. Lo unico que cambia son los numeros.

    Esta guardia existe porque arreglar un numero y aprovechar
    para "ensenar de donde sale" es la forma mas natural de
    llenar una tabla sin que nadie lo haya pedido.
    """

    from pathlib import Path

    panel = (
        Path(__file__).parents[2]
        / "dashboard-v8"
        / "src"
        / "components"
        / "StandingsIntelPanel.jsx"
    ).read_text(encoding="utf-8")

    columnas = [
        linea.strip()
        for linea in panel.splitlines()
        # `<thead>` empieza igual y no es una columna.
        if linea.strip().startswith(("<th>", "<th "))
    ]

    esperadas = [
        "#",
        "MÁNAGER",
        "PTS",
        "CAJA",
        "PLANTILLA",
        "PATRIMONIO",
        "TOPE",
        "PUJA",
        "MÁX. VISTO",
        "AMENAZA",
    ]

    assert len(columnas) == len(esperadas), (
        f"la tabla tiene {len(columnas)} columnas y tenia "
        f"{len(esperadas)}: {columnas}"
    )

    for titulo, linea in zip(esperadas, columnas):
        assert titulo in linea, (
            f"la columna `{titulo}` ha cambiado o se ha movido de "
            f"sitio: {linea}"
        )

    # Y ni una etiqueta nueva colada en las filas.
    for intruso in (
        "cash_source",
        "SIN_DATO",
        "cash_check",
        "RECONSTRUIDA",
    ):
        assert intruso not in panel, (
            f"`{intruso}` se ha colado en la tabla de "
            f"Clasificacion"
        )


TESTS = [
    test_la_caja_reconstruida_cuadra_con_la_real,
    test_la_comprobacion_no_pasa_con_las_manos_vacias,
    test_el_premio_por_puesto_se_paga,
    test_la_jornada_partida_no_paga,
    test_la_jornada_ignorada_es_la_unica_sin_premio,
    test_sin_eventos_no_hay_caja_y_se_dice,
    test_el_motor_publica_el_cuadre_en_cada_vuelta,
    test_la_alarma_del_cuadre_solo_sale_si_esta_roja,
    test_la_tabla_de_clasificacion_no_ha_crecido,
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
        f"LA CAJA DE LA LIGA V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
