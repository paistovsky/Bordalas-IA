"""
Los tres denominadores: el plazo, los dias planos y la masa.

QUE SE PRUEBA AQUI

    1. `test_el_valor_de_reserva_grita`
       Si dos candidatos con ritmos distintos comparten el mismo
       valor, se dice CON NOMBRE Y MOTIVO. Y con la lista de
       candidatos vacia la guardia FALLA: no haber mirado nada no
       es un aprobado.

    2. `test_la_persistencia_cuenta_los_dias_planos`
       El factor se calcula sobre TODOS los pares, no solo sobre
       los que se movieron los dos dias. La guardia falla si los
       dos denominadores salen iguales, porque entonces no
       probaria nada.

    3. `test_el_ojeador_funciona_sin_red`
       Con las tres fuentes caidas la estimacion sigue saliendo
       de nuestro historico y lo dice. Y falla si el historico
       llega vacio.

    Y, alrededor de esas tres, las que sostienen los numeros del
    informe: que el plazo se garantiza, que la racha no se
    inventa sobre agujeros, y que la masa de la curva no es 1/7.

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    Todas las series de esta guardia son fixtures escritos aqui,
    con fechas fijas puestas a mano. No se abre `data/`, no se
    llama a `datetime.now()` y la zona horaria es UTC fija.

DOCTRINA 53 / 54 / 55

    Cada afirmacion de estas pruebas lleva su plazo, su
    denominador y su `n`, porque las tres se rompieron en el
    informe anterior.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from src.analysis.los_tres_denominadores import (
    MOVIMIENTO_MINIMO_PUNTOS,
    contraste_con_el_ojeador,
    el_valor_de_reserva,
    estimacion_desde_el_historico,
    factor_de_persistencia,
    masa_real_de_la_curva,
    pares_al_plazo,
    racha_hasta,
    se_agota_la_racha,
    serie_por_dia,
    tabla_de_persistencia,
)


# El huso entra por argumento en todo el modulo. Aqui se fija a
# UTC para que la guardia no dependa de la maquina.
ZONA = timezone.utc

PRIMER_DIA = date(2026, 9, 1)


def _serie(movimientos, desde=PRIMER_DIA, base=1_000_000, saltar=()):
    """
    Una serie {fecha: precio} a partir de una lista de deltas.

    `saltar` son los indices de dia que NO se escriben: asi se
    fabrican los agujeros del almacen de verdad, que es lo que
    obligo a escribir `pares_al_plazo`.
    """

    serie = {}

    precio = base

    for k, delta in enumerate([0] + list(movimientos)):

        precio += delta

        if k in saltar:
            continue

        serie[desde + timedelta(days=k)] = precio

    return serie


# UN FIXTURE QUE TRAE DE TODO (regla 24)
#
#     Sube, baja, se queda plano, tiene una racha larga y tiene
#     un agujero. Si alguna de esas cosas faltara, media guardia
#     pasaria sin probar nada.
SERIE_QUE_SUBE = _serie([20_000] * 8)

SERIE_QUE_BAJA = _serie([-20_000] * 8)

SERIE_PLANA = _serie([0] * 8)

# Sube tres dias, se queda plano dos, y baja tres.
SERIE_MIXTA = _serie(
    [20_000, 30_000, 20_000, 0, 0, -30_000, -20_000, -20_000]
)

# La misma que sube, pero al almacen le falta el cuarto dia.
SERIE_CON_AGUJERO = _serie([20_000] * 8, saltar=(4,))

# A TIRONES: sube fuerte, se queda quieto, vuelve a subir.
#
#     Sin esta serie los dos denominadores del factor dan el
#     mismo numero -la mediana aguanta un dia plano suelto- y
#     `test_la_persistencia_cuenta_los_dias_planos` daria verde
#     sin haber enseñado nada. Aqui el dia plano ES la mitad de
#     la muestra, que es lo que hace visible la diferencia.
SERIE_A_TIRONES = _serie([30_000, 0] * 4)


def test_el_fixture_trae_de_todo():
    """
    REGLA 24: un fixture que solo trae el caso bueno no prueba
    nada. Antes de usar las series, se comprueba que dentro hay
    subidas, bajadas, dias planos, una racha larga y un agujero.
    """

    assert len(SERIE_QUE_SUBE) == 9, (
        f"la serie que sube trae {len(SERIE_QUE_SUBE)} dias y "
        f"hacen falta 9"
    )

    assert len(SERIE_CON_AGUJERO) == 8, (
        "la serie con agujero no tiene agujero: entonces no prueba "
        "que el plazo se garantice"
    )

    pares = pares_al_plazo({"mixta": SERIE_MIXTA}, horizonte=1)

    assert any(p["hoy"] > 0 for p in pares), "faltan dias que suben"
    assert any(p["hoy"] == 0 for p in pares), "faltan dias PLANOS"
    assert any(p["hoy"] < 0 for p in pares), "faltan dias que bajan"

    assert any(p["ayer"] > 0 for p in pares), "faltan ayeres que suben"
    assert any(p["ayer"] < 0 for p in pares), "faltan ayeres que bajan"

    assert max(abs(p["racha"]) for p in pares) >= 3, (
        "no hay ninguna racha larga: el tramo por dias de racha "
        "quedaria sin muestra"
    )

    print(
        f"  OK  el fixture trae subidas, bajadas, planos, racha y "
        f"agujero ({len(pares)} pares)"
    )


# ============================================================
# EL PRIMER DENOMINADOR: EL PLAZO (doctrina 53)
# ============================================================


def test_el_plazo_de_cada_par_esta_garantizado():
    """
    Dos posiciones seguidas de la lista de precios NO son dos
    dias seguidos cuando al almacen le falta un dia. Un par que
    cruza el agujero mide tres dias y se publicaria como uno.
    """

    sin_agujero = pares_al_plazo(
        {"a": SERIE_QUE_SUBE}, horizonte=1
    )

    con_agujero = pares_al_plazo(
        {"a": SERIE_CON_AGUJERO}, horizonte=1
    )

    assert len(con_agujero) < len(sin_agujero), (
        f"el agujero no ha quitado ningun par "
        f"({len(con_agujero)} contra {len(sin_agujero)}): se "
        f"estarian mezclando plazos"
    )

    faltante = PRIMER_DIA + timedelta(days=4)

    for par in con_agujero:
        assert par["date"] != faltante, (
            f"hay un par fechado el {faltante}, que no esta en la "
            f"serie"
        )

        vecinos = (
            par["date"] - timedelta(days=1),
            par["date"] + timedelta(days=1),
        )

        for dia in vecinos:
            assert dia in SERIE_CON_AGUJERO, (
                f"el par del {par['date']} usa el {dia}, que el "
                f"almacen no tiene: el plazo no seria de un dia"
            )

    assert all(p["plazo"] == 1 for p in con_agujero), (
        "hay pares sin su plazo escrito (doctrina 53)"
    )

    print(
        f"  OK  el agujero quita {len(sin_agujero) - len(con_agujero)} "
        f"par(es) y los {len(con_agujero)} que quedan son de un dia"
    )


def test_el_horizonte_largo_exige_todos_los_dias():
    """
    A tres dias de plazo hacen falta CUATRO dias seguidos en la
    serie. Con menos, el par no existe.
    """

    a_uno = pares_al_plazo({"a": SERIE_QUE_SUBE}, horizonte=1)
    a_tres = pares_al_plazo({"a": SERIE_QUE_SUBE}, horizonte=3)

    assert len(a_tres) < len(a_uno), (
        f"a tres dias salen {len(a_tres)} pares y a uno "
        f"{len(a_uno)}: el horizonte largo no esta exigiendo mas "
        f"dias"
    )

    assert all(p["plazo"] == 3 for p in a_tres), (
        "los pares a tres dias no llevan su plazo"
    )

    # El movimiento acumulado a tres dias tiene que ser MAYOR que
    # el de un dia sobre la misma serie que sube.
    assert max(p["hoy"] for p in a_tres) > max(
        p["hoy"] for p in a_uno
    ), (
        "el movimiento a tres dias no supera al de un dia: no se "
        "esta acumulando"
    )

    print(
        f"  OK  a 3 dias quedan {len(a_tres)} pares (de "
        f"{len(a_uno)} a 1 dia) y acumulan mas movimiento"
    )


def test_la_racha_se_corta_en_el_agujero():
    """
    Una racha con un hueco en medio no es una racha: son dos
    trozos. Si no se cortara, se publicarian rachas de veinte
    dias que nunca existieron.
    """

    ultimo = max(SERIE_QUE_SUBE)

    entera = racha_hasta(SERIE_QUE_SUBE, ultimo)

    partida = racha_hasta(SERIE_CON_AGUJERO, max(SERIE_CON_AGUJERO))

    assert entera == 8, (
        f"la racha entera sale {entera} y la serie sube 8 dias "
        f"seguidos"
    )

    assert 0 < partida < entera, (
        f"la racha con agujero sale {partida} y la entera "
        f"{entera}: el hueco no la ha cortado"
    )

    # Y una serie plana no tiene racha en ningun sentido.
    assert racha_hasta(SERIE_PLANA, max(SERIE_PLANA)) == 0, (
        "una serie plana esta declarando racha"
    )

    # Bajando, la racha es negativa.
    assert racha_hasta(SERIE_QUE_BAJA, max(SERIE_QUE_BAJA)) < 0, (
        "una serie que baja no declara racha negativa"
    )

    print(
        f"  OK  racha entera {entera}, con agujero {partida}, "
        f"plana 0, bajando negativa"
    )


# ============================================================
# EL SEGUNDO DENOMINADOR: LOS DIAS PLANOS
# ============================================================


def test_la_persistencia_cuenta_los_dias_planos():
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    El factor se calcula sobre TODOS los pares, no solo sobre los
    que se movieron los dos dias. Un dia plano es un resultado
    -el dinero se queda quieto-, no una observacion que se tira.

    Y ESTA GUARDIA FALLA SI LOS DOS DENOMINADORES SALEN IGUALES,
    porque entonces no probaria nada: haria falta una muestra con
    dias planos dentro para que la diferencia se pueda ver.
    """

    pares = pares_al_plazo(
        {
            "sube": SERIE_QUE_SUBE,
            "baja": SERIE_QUE_BAJA,
            "mixta": SERIE_MIXTA,
            "tirones": SERIE_A_TIRONES,
        },
        horizonte=1,
    )

    con = factor_de_persistencia(pares, contando_planos=True)
    sin = factor_de_persistencia(pares, contando_planos=False)

    assert con["available"] and sin["available"], (
        "una de las dos mediciones no esta disponible: sin las dos "
        "no hay comparacion"
    )

    # EL DENOMINADOR TIENE QUE SER DISTINTO. Si fuera el mismo, la
    # guardia estaria dando verde sin haber probado nada.
    assert con["n"] != sin["n"], (
        f"los dos denominadores salen iguales (n={con['n']}): esta "
        f"guardia no prueba nada si la muestra no tiene dias "
        f"planos dentro. Arreglar el fixture, no la guardia."
    )

    assert con["n"] > sin["n"], (
        f"contando los dias planos salen MENOS pares "
        f"({con['n']}) que sin contarlos ({sin['n']}): el "
        f"denominador honesto tiene que ser el mayor"
    )

    planos = con["n"] - sin["n"]

    assert planos > 0, "no hay ni un dia plano en la muestra"

    # Y EL NUMERO TIENE QUE MOVERSE, no solo el `n`. Un factor
    # identico con dos denominadores distintos significa que la
    # muestra no tiene bastantes dias planos para que se vea, y
    # entonces esta guardia estaria dando verde de adorno.
    assert con["factor"] != sin["factor"], (
        f"los dos factores salen iguales ({con['factor']}) con "
        f"denominadores distintos ({con['n']} y {sin['n']}): la "
        f"muestra no tiene bastantes dias planos para enseñar la "
        f"diferencia. Arreglar el fixture, no la guardia."
    )

    assert abs(con["factor"]) < abs(sin["factor"]), (
        f"contando los dias planos el factor sale MAS alto "
        f"({con['factor']} contra {sin['factor']}): un dia sin "
        f"movimiento no puede subir la persistencia"
    )

    # Y los dos numeros llevan su plazo escrito (doctrina 53).
    assert con["plazo"] == 1 and sin["plazo"] == 1, (
        "el factor se publica sin su plazo"
    )

    # La direccion tambien se cuenta sobre TODOS los pares: si se
    # midiera solo sobre los que se movieron, saldria mas alta.
    assert con["misma_direccion"] <= sin["misma_direccion"], (
        f"contando los dias planos la direccion sale MAS alta "
        f"({con['misma_direccion']} contra "
        f"{sin['misma_direccion']}): el plano se estaria contando "
        f"como acierto"
    )

    print(
        f"  OK  con planos n={con['n']} factor {con['factor']}, "
        f"sin planos n={sin['n']} factor {sin['factor']} "
        f"({planos} dias planos de diferencia)"
    )


def test_la_tabla_suma_cien_y_lleva_su_n():
    """
    Las tres filas -sube, plano, baja- son el reparto COMPLETO de
    lo que pasa hoy. Si no sumaran el `n` del grupo, habria
    pares que no se cuentan en ningun sitio.
    """

    pares = pares_al_plazo(
        {
            "sube": SERIE_QUE_SUBE,
            "baja": SERIE_QUE_BAJA,
            "plana": SERIE_PLANA,
            "mixta": SERIE_MIXTA,
        },
        horizonte=1,
    )

    tabla = tabla_de_persistencia(pares)

    assert tabla["available"], tabla["reason"]

    assert tabla["plazo"] == 1, "la tabla se publica sin su plazo"

    for nombre, grupo in tabla["groups"].items():

        assert (
            grupo["sube"] + grupo["plano"] + grupo["baja"]
            == grupo["n"]
        ), (
            f"el grupo «{nombre}» reparte "
            f"{grupo['sube'] + grupo['plano'] + grupo['baja']} de "
            f"{grupo['n']} pares: hay pares sin contar"
        )

    # La muestra tiene que tener las dos direcciones y los planos.
    assert tabla["groups"]["subio"]["n"] > 0, "faltan ayeres al alza"
    assert tabla["groups"]["bajo"]["n"] > 0, "faltan ayeres a la baja"
    assert tabla["groups"]["plano"]["n"] > 0, "faltan ayeres planos"

    print(
        f"  OK  la tabla reparte los {tabla['n']} pares sin dejar "
        f"ninguno fuera, a {tabla['plazo']} dia de plazo"
    )


def test_la_racha_se_mide_por_tramos_y_los_vacios_se_dicen():
    """
    Un tramo sin muestra se publica con `n = 0` y sin numeros. No
    se interpola, no se hereda del tramo de al lado: se dice que
    no hay.
    """

    medido = se_agota_la_racha(
        pares_al_plazo({"sube": SERIE_QUE_SUBE}, horizonte=1)
    )

    assert medido["available"], medido["reason"]

    vacios = [t for t in medido["tramos"] if t["n"] == 0]

    assert vacios, (
        "todos los tramos tienen muestra: entonces esta guardia no "
        "prueba que un tramo vacio se diga"
    )

    for tramo in vacios:
        assert tramo["sigue_percent"] is None, (
            f"el tramo «{tramo['tramo']}» no tiene muestra y "
            f"publica un porcentaje: {tramo['sigue_percent']}"
        )
        assert tramo["factor"] is None, (
            f"el tramo «{tramo['tramo']}» no tiene muestra y "
            f"publica un factor"
        )

    con_muestra = [t for t in medido["tramos"] if t["n"] > 0]

    assert con_muestra, "ningun tramo tiene muestra"

    for tramo in con_muestra:
        assert tramo["sigue_percent"] is not None, (
            f"el tramo «{tramo['tramo']}» tiene n={tramo['n']} y no "
            f"publica direccion"
        )

    print(
        f"  OK  {len(con_muestra)} tramo(s) con muestra y "
        f"{len(vacios)} vacio(s), dichos como vacios"
    )


# ============================================================
# EL TERCER DENOMINADOR: LA MASA
# ============================================================


def test_la_masa_de_la_curva_no_es_un_septimo():
    """
    Siete cuantiles llevan 1/7 cada uno POR CONSTRUCCION, y eso
    esta bien. Lo que no esta bien es leer ese 1/7 como "aqui cae
    una de cada siete pujas": los cortes no estan repartidos por
    igual y el de arriba cubre el 0,5 % de la muestra.
    """

    cortes = [0.05, 0.20, 0.40, 0.60, 0.80, 0.95, 0.995]

    # La curva calibrada de la foto del 14/09, con sus 72 pujas.
    curva = [
        (1.0000, 0.1429),
        (1.0052, 0.1429),
        (1.0222, 0.1429),
        (1.0323, 0.1429),
        (1.0622, 0.1429),
        (1.2109, 0.1429),
        (1.2449, 0.1429),
    ]

    medido = masa_real_de_la_curva(curva, cortes, muestras=72)

    assert medido["available"], medido["reason"]

    assert sum(p["n"] for p in medido["steps"]) == 72, (
        f"los peldaños reparten "
        f"{sum(p['n'] for p in medido['steps'])} de 72 pujas: hay "
        f"pujas sin caer en ningun sitio"
    )

    arriba = medido["steps"][-1]

    assert arriba["masa_real"] < arriba["peso_por_construccion"], (
        f"el peldaño de arriba lleva {arriba['masa_real']} de masa "
        f"real y {arriba['peso_por_construccion']} por "
        f"construccion: si no estuviera sobrevalorado, esta "
        f"medicion no diria nada"
    )

    assert arriba["masa_real"] * 5 < arriba["peso_por_construccion"], (
        f"el peldaño de arriba esta solo "
        f"{arriba['peso_por_construccion'] / max(arriba['masa_real'], 1e-9):.1f} "
        f"veces sobrevalorado: el informe afirma que son mas de "
        f"cinco"
    )

    assert abs(sum(p["masa_real"] for p in medido["steps"]) - 1.0) < 0.01, (
        "la masa real no suma uno"
    )

    print(
        f"  OK  el peldaño de arriba lleva "
        f"{arriba['peso_por_construccion']} por construccion y "
        f"{arriba['masa_real']} de verdad (n={arriba['n']} de 72)"
    )


def test_la_masa_no_se_inventa_sin_muestras():
    """
    Sin curva, sin cortes o sin muestras no se dice donde cae la
    masa: se dice que no se sabe.
    """

    for etiqueta, argumentos in (
        ("sin curva", ([], [0.05], 72)),
        ("sin cortes", ([(1.0, 0.5)], [], 72)),
        ("sin muestras", ([(1.0, 0.5)], [0.05], 0)),
        ("descuadradas", ([(1.0, 0.5)], [0.05, 0.9], 72)),
    ):
        medido = masa_real_de_la_curva(*argumentos)

        assert not medido["available"], (
            f"«{etiqueta}» ha devuelto una masa: "
            f"{medido['curva_por_masa']}"
        )

        assert medido["reason"], (
            f"«{etiqueta}» no dice por que no se puede"
        )

    print("  OK  sin muestra la masa no se inventa: se dice")


# ============================================================
# EL VALOR DE RESERVA
# ============================================================


def test_el_valor_de_reserva_grita():
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    Si la estimacion cae al valor de reserva, se dice CON EL
    MOTIVO Y EL JUGADOR, nunca en silencio.

    EL CASO DE VERDAD, del 14/09: Marc Roca subiendo un 0,297 %
    al dia y Veiga cayendo un 1,187 % al dia -dos ritmos que no
    se parecen en nada- salieron con el MISMO valor, porque el
    que gano el `max` fue `computer_resale_value`, que es
    `precio x 1,015075` para todo el mundo.

    Y LA GUARDIA FALLA SI LA LISTA DE CANDIDATOS LLEGA VACIA:
    no haber mirado a nadie no es un aprobado.
    """

    candidatos = [
        {
            "player": "Marc Roca",
            "price": 3_370_000,
            "value": 3_420_802,
            "route": "COMPUTER_RESALE",
            "intent": "SPECULATION",
            "rate_percent_per_day": 0.297,
        },
        {
            "player": "Veiga",
            "price": 3_370_000,
            "value": 3_420_802,
            "route": "COMPUTER_RESALE",
            "intent": "SPECULATION",
            "rate_percent_per_day": -1.187,
        },
        {
            "player": "Pedro Diaz",
            "price": 880_000,
            "value": 935_451,
            "route": "PRICE_TREND",
            "intent": "SPECULATION",
            "rate_percent_per_day": 4.545,
        },
    ]

    medido = el_valor_de_reserva(candidatos)

    assert medido["available"], medido["reason"]

    assert medido["reserva"], (
        "Marc Roca y Veiga comparten valor con ritmos opuestos y no "
        "ha saltado ningun aviso: el valor de reserva estaria "
        "pasando en silencio"
    )

    nombrados = {s["player"] for s in medido["reserva"]}

    for quien in ("Marc Roca", "Veiga"):
        assert quien in nombrados, (
            f"el aviso no nombra a {quien}: un aviso sin jugador no "
            f"sirve para ir a mirarlo"
        )

    # EL MOTIVO, no solo el nombre.
    for aviso in medido["reserva"]:
        assert aviso["motivo"], (
            f"el aviso de {aviso['player']} no trae motivo"
        )
        assert aviso["reason"], (
            f"el aviso de {aviso['player']} no trae explicacion"
        )

    motivos = {s["motivo"] for s in medido["reserva"]}

    assert "RATIO_COMPARTIDO" in motivos, (
        "no se ha detectado el ratio compartido, que es la huella "
        "del valor de reserva"
    )

    assert "VIA_QUE_NO_PROYECTA" in motivos, (
        "no se ha detectado que COMPUTER_RESALE se presente como "
        "SPECULATION: ese es el fallo con su nombre"
    )

    # El que SI depende de su ritmo no se denuncia.
    assert "Pedro Diaz" not in {
        s["player"]
        for s in medido["reserva"]
        if s["motivo"] == "RATIO_COMPARTIDO"
    }, (
        "Pedro Diaz tiene su propio valor por PRICE_TREND y se le "
        "esta acusando de llevar un valor de reserva"
    )

    # ------------------------------------------------------
    # CON LAS MANOS VACIAS SE FALLA
    # ------------------------------------------------------
    vacio = el_valor_de_reserva([])

    assert not vacio["available"], (
        "con la lista de candidatos VACIA la medicion se ha dado "
        "por buena: no haber mirado nada no es un aprobado "
        "(regla 24)"
    )

    assert vacio["reason"], "la lista vacia no dice por que falla"

    assert el_valor_de_reserva(None)["available"] is False, (
        "con `None` tampoco puede dar verde"
    )

    print(
        f"  OK  {len(medido['reserva'])} aviso(s) con nombre y "
        f"motivo; con la lista vacia NO pasa"
    )


def test_un_tablero_sano_no_dispara_el_aviso():
    """
    El aviso tiene que poder callarse. Si gritara siempre, no
    distinguiria el dia malo del bueno.
    """

    sanos = [
        {
            "player": "A",
            "price": 1_000_000,
            "value": 1_040_000,
            "route": "PRICE_TREND",
            "intent": "SPECULATION",
            "rate_percent_per_day": 1.5,
        },
        {
            "player": "B",
            "price": 1_000_000,
            "value": 1_090_000,
            "route": "PRICE_TREND",
            "intent": "SPECULATION",
            "rate_percent_per_day": 3.2,
        },
    ]

    medido = el_valor_de_reserva(sanos)

    assert medido["available"], medido["reason"]

    assert not medido["reserva"], (
        f"se ha disparado el aviso con dos valores que SI dependen "
        f"del ritmo: {medido['reserva']}"
    )

    print("  OK  con valores que dependen del ritmo, el aviso calla")


def test_dos_jugadores_con_el_mismo_ritmo_no_son_sospechosos():
    """
    Dos jugadores con el MISMO ritmo deben dar el mismo ratio: eso
    es que el motor funciona, no que este roto. La huella del
    valor de reserva es ritmos DISTINTOS con el mismo valor.
    """

    iguales = [
        {
            "player": "A",
            "price": 1_000_000,
            "value": 1_040_000,
            "route": "PRICE_TREND",
            "intent": "SPECULATION",
            "rate_percent_per_day": 1.5,
        },
        {
            "player": "B",
            "price": 2_000_000,
            "value": 2_080_000,
            "route": "PRICE_TREND",
            "intent": "SPECULATION",
            "rate_percent_per_day": 1.5,
        },
    ]

    medido = el_valor_de_reserva(iguales)

    assert not medido["reserva"], (
        f"mismo ritmo y mismo ratio se ha tomado por averia: "
        f"{medido['reserva']}"
    )

    print("  OK  mismo ritmo, mismo ratio: eso no es una averia")


# ============================================================
# QUE EL OJEADOR DEJE DE SER UNA DEPENDENCIA
# ============================================================


def test_el_ojeador_funciona_sin_red():
    """
    LA GUARDIA QUE PIDIO EL ENCARGO DEL 16/09.

    Con las tres fuentes caidas, la estimacion sigue saliendo del
    historico NUESTRO y lo dice. Las tres webs publican
    `price_increment / precio` -69 de 69 en la foto del 14/09, 15
    de 15 contra nuestra serie-, asi que el numero estaba en casa
    desde el principio.

    Y FALLA SI EL HISTORICO LLEGA VACIO: de una serie vacia no
    sale una estimacion, sale un motivo.
    """

    # LAS TRES FUENTES CAIDAS. No se le pasa ninguna.
    dia = max(SERIE_QUE_SUBE)

    medido = estimacion_desde_el_historico(
        SERIE_QUE_SUBE, dia, persistencia=0.9231
    )

    assert medido["available"], (
        f"con el historico delante no hay estimacion: "
        f"{medido['reason']}"
    )

    assert medido["percent_per_day"] is not None, (
        "la estimacion no trae numero"
    )

    assert medido["source"] == "PRICE_HISTORY", (
        f"la estimacion dice venir de «{medido['source']}» y tiene "
        f"que decir que sale de nuestro historico"
    )

    assert medido["plazo"] == 1, (
        "la estimacion se publica sin su plazo (doctrina 53)"
    )

    assert "red" in (medido["reason"] or "").lower(), (
        f"la estimacion no dice que no ha salido a la red: "
        f"«{medido['reason']}»"
    )

    # El recorte por persistencia RECORTA, no adorna.
    assert abs(medido["percent_per_day"]) <= abs(
        medido["observed_percent"]
    ), (
        f"la estimacion ({medido['percent_per_day']}) supera a lo "
        f"observado ({medido['observed_percent']}): el «recorte» "
        f"esta inflando"
    )

    # Y va en el mismo sentido que el precio.
    assert medido["percent_per_day"] > 0, (
        "la serie sube y la estimacion no sale positiva"
    )

    bajando = estimacion_desde_el_historico(
        SERIE_QUE_BAJA, max(SERIE_QUE_BAJA), persistencia=0.9231
    )

    assert bajando["available"] and bajando["percent_per_day"] < 0, (
        "la serie baja y la estimacion no sale negativa"
    )

    # ------------------------------------------------------
    # CON EL HISTORICO VACIO SE FALLA
    # ------------------------------------------------------
    for etiqueta, serie in (
        ("vacio", {}),
        ("None", None),
    ):
        sin = estimacion_desde_el_historico(
            serie, dia, persistencia=0.9231
        )

        assert not sin["available"], (
            f"con el historico «{etiqueta}» ha salido una "
            f"estimacion: {sin['percent_per_day']}. De una serie "
            f"vacia no sale un numero"
        )

        assert sin["decision"] == "SIN_PRONOSTICO", (
            f"con el historico «{etiqueta}» no se dice "
            f"SIN_PRONOSTICO"
        )

        assert sin["reason"], (
            f"con el historico «{etiqueta}» no se dice por que"
        )

    # Y un dia suelto sin su anterior tampoco vale.
    huerfano = estimacion_desde_el_historico(
        {PRIMER_DIA: 1_000_000}, PRIMER_DIA, persistencia=0.9231
    )

    assert not huerfano["available"], (
        "con un solo dia en la serie ha salido una estimacion: no "
        "hay contra que compararlo"
    )

    print(
        f"  OK  sin las tres fuentes la estimacion sale del "
        f"historico ({medido['percent_per_day']:+.3f} %/dia, racha "
        f"{medido['trend_days']}); con el historico vacio NO sale"
    )


def test_un_movimiento_de_redondeo_no_es_un_pronostico():
    """
    Biwenger mueve los precios en saltos de 10.000. Un movimiento
    por debajo de un punto no se distingue del redondeo, y de ahi
    no sale un pronostico: sale un motivo.
    """

    # Un millon que sube 5.000: +0,5 %, por debajo del minimo.
    serie = _serie([5_000], base=1_000_000)

    medido = estimacion_desde_el_historico(
        serie, max(serie), persistencia=0.9231
    )

    assert not medido["available"], (
        f"un movimiento de {medido['observed_percent']} % ha dado "
        f"pronostico, y el minimo son {MOVIMIENTO_MINIMO_PUNTOS} "
        f"punto(s)"
    )

    assert medido["observed_percent"] is not None, (
        "no se publica lo observado, asi que no se puede ver que "
        "era pequeño"
    )

    assert medido["reason"], "no se dice por que no hay pronostico"

    print(
        f"  OK  {medido['observed_percent']:+.3f} % en un dia no es "
        f"un pronostico: es redondeo"
    )


def test_una_discrepancia_con_el_ojeador_se_grita():
    """
    Mientras el ojeador coincida con nuestro precio es un ECO
    (doctrina 57) y no aporta nada. El dia que NO coincida, una de
    las dos fotos esta mal y eso si es informacion.
    """

    dia = max(SERIE_QUE_SUBE)

    nuestro = estimacion_desde_el_historico(
        SERIE_QUE_SUBE, dia, persistencia=0.9231
    )

    eco = contraste_con_el_ojeador(
        nuestro, nuestro["observed_percent"]
    )

    assert eco["available"] and eco["agree"] is True, (
        f"coincidiendo al decimal no se reconoce el eco: "
        f"{eco['reason']}"
    )

    assert "eco" in eco["reason"].lower(), (
        f"el contraste no llama eco a un eco: «{eco['reason']}»"
    )

    discrepa = contraste_con_el_ojeador(
        nuestro, nuestro["observed_percent"] + 5.0
    )

    assert discrepa["available"] and discrepa["agree"] is False, (
        "cinco puntos de diferencia no se han detectado"
    )

    assert "DISCREPAN" in discrepa["reason"], (
        f"la discrepancia no se grita: «{discrepa['reason']}»"
    )

    # Sin uno de los dos numeros no hay contraste, y se dice.
    assert (
        contraste_con_el_ojeador(nuestro, None)["available"] is False
    ), "sin el numero del ojeador se esta dando un contraste"

    assert (
        contraste_con_el_ojeador(None, 1.0)["available"] is False
    ), "sin nuestro numero se esta dando un contraste"

    print(
        f"  OK  coincidir es un eco; {discrepa['delta']:+.2f} "
        f"puntos de diferencia se gritan"
    )


def test_la_serie_por_dia_no_mira_el_reloj():
    """
    `serie_por_dia` recibe el huso por argumento. Con marcas
    fijas y UTC, el resultado es siempre el mismo dia, corra esto
    en Madrid o en Tokio.
    """

    # Dos marcas ESCRITAS A MANO, no derivadas de ningun reloj ni
    # de `.timestamp()`: 2026-09-01 08:00 UTC y 03:00 UTC. La de
    # las tres de la mañana se descarta por la hora minima.
    tarde = 1_788_249_600
    temprano = 1_788_231_600

    assert datetime.fromtimestamp(tarde, ZONA) == datetime(
        2026, 9, 1, 8, 0, tzinfo=ZONA
    ), "la marca escrita a mano no es la que dice el comentario"

    assert datetime.fromtimestamp(temprano, ZONA) == datetime(
        2026, 9, 1, 3, 0, tzinfo=ZONA
    ), "la marca escrita a mano no es la que dice el comentario"

    series = serie_por_dia(
        {"7": {"t": [temprano, tarde], "p": [900_000, 1_000_000]}},
        ZONA,
    )

    assert series == {"7": {date(2026, 9, 1): 1_000_000}}, (
        f"la serie por dia sale {series} y tenia que quedarse con "
        f"la muestra de las 08:00"
    )

    # Basura dentro no tumba la funcion.
    assert serie_por_dia(None, ZONA) == {}, "con None tiene que dar {}"

    assert serie_por_dia({"x": None}, ZONA) == {}, (
        "con una fila vacia tiene que dar {}"
    )

    assert serie_por_dia(
        {"x": {"t": ["no-es-una-marca"], "p": [1]}}, ZONA
    ) == {}, "una marca ilegible tiene que caerse sola"

    print("  OK  la serie por dia usa el huso que se le pasa y no lanza")


TESTS = [
    test_el_fixture_trae_de_todo,
    test_el_plazo_de_cada_par_esta_garantizado,
    test_el_horizonte_largo_exige_todos_los_dias,
    test_la_racha_se_corta_en_el_agujero,
    test_la_persistencia_cuenta_los_dias_planos,
    test_la_tabla_suma_cien_y_lleva_su_n,
    test_la_racha_se_mide_por_tramos_y_los_vacios_se_dicen,
    test_la_masa_de_la_curva_no_es_un_septimo,
    test_la_masa_no_se_inventa_sin_muestras,
    test_el_valor_de_reserva_grita,
    test_un_tablero_sano_no_dispara_el_aviso,
    test_dos_jugadores_con_el_mismo_ritmo_no_son_sospechosos,
    test_el_ojeador_funciona_sin_red,
    test_un_movimiento_de_redondeo_no_es_un_pronostico,
    test_una_discrepancia_con_el_ojeador_se_grita,
    test_la_serie_por_dia_no_mira_el_reloj,
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
        f"LOS TRES DENOMINADORES V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
