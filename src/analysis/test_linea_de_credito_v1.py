"""
Una puja del dueno no puede arruinar a la liga entera.

SINTOMA (10/09/2026)

    El dueno pujo 12.217.000 por Aubameyang. Dos ciclos del
    mismo dia, sin que ningun rival hiciera nada:

        manager       07:52         09:04
        Pollo17       9.413.772           0
        Luismi_Haz   23.342.594   2.880.828
        Manzagool    11.330.280           0

    Pepe paso a creer que Pollo no podia pujar y que Luismi
    tenia 2,9 M en vez de 23,3 M.

CAUSA — EL DESPEJE EQUIVOCADO

    Hay una sola ecuacion y dos formas de despejarla:

        correcto:    comprometido = saldo + plantilla/4 - maximumBid
        produccion:  headroom     = maximumBid - saldo

    `maximumBid` YA viene con las pujas descontadas (medido el
    16/08). El segundo despeje se traga la puja: el headroom
    cayo de 12.510.000 a 293.000 y el ratio de 0,25 a 0,0059.

    Y ese ratio se aplicaba a los SIETE managers.

CONSECUENCIA

    Toda la doctrina de no pagar la prima se apoya en estimar
    bien la competencia. Y Pepe se lo iba a hacer a si mismo: en
    cuanto la cartera pusiera cuatro pujas en la ventana del
    reset, su propio ratio se hundiria y concluiria que nadie
    puede competirle, justo en el momento de decidir cuanto
    ofrecer.

LO QUE SE PROTEGE

    1. Que con la foto envenenada de las 09:04 el ratio siga
       siendo 0,25 y lo comprometido salga 12.217.000.
    2. Que ningun rival baje de capacidad respecto a las 07:52.
    3. Que el ratio NO se deduzca de `maximumBid`.
    4. Que la capacidad de un rival no dependa de nuestras
       pujas, ni de una ni de cuatro.
    5. Que las tres vias concuerden sobre el caso real.
    6. Que un ratio imposible se AVISE y no se adopte.
    7. Que nuestro propio `maximum_bid` sea el oficial, que si
       tiene que llevar nuestras pujas descontadas.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Las dos fotos estan EMPOTRADAS como numeros. Ni `data/`, ni
    red, ni reloj.

REGLA 24

    Si las tablas se quedan vacias, fallan.

COMO SE USA

    python -m src.analysis.test_linea_de_credito_v1
"""

from __future__ import annotations

from src.analysis.linea_de_credito import (
    LINEA_DE_CREDITO,
    capacidad_de,
    comprometido_de,
    headroom_de,
)

from src.analysis.rival_intelligence_engine import (
    apply_market_power,
    calibrate_debt_ratio,
)


# ============================================================
# LAS DOS FOTOS DEL INCIDENTE
# ============================================================

NUESTRO_ID = 14175949

LA_PUJA = 12_217_000


# Nosotros, en los dos ciclos. Mismo saldo, mismo valor de
# plantilla: lo unico que cambia es `maximumBid`, y cambia
# exactamente por el importe de la puja.
FOTO_0752 = {
    "balance": 3_315_383,
    "maximum_bid": 15_825_383,
    "roster_value": 50_040_000,
}

FOTO_0904 = {
    "balance": 3_315_383,
    "maximum_bid": 3_608_383,
    "roster_value": 50_040_000,
}


# Los managers tal como salen en la foto de las 09:04: saldo y
# valor de plantilla, que es lo unico con lo que se puede
# estimar su capacidad.
MANAGERS_0904 = {
    14145555: {
        "user_id": 14145555,
        "name": "Pollo17",
        "balance": -7_332_328,
        "roster_value": 83_620_000,
    },
    14175949: {
        "user_id": 14175949,
        "name": "Pepe Bordalás",
        "balance": 3_215_383,
        "roster_value": 50_040_000,
    },
    14156489: {
        "user_id": 14156489,
        "name": "Luismi_Haz",
        "balance": 2_390_094,
        "roster_value": 83_810_000,
    },
    14178736: {
        "user_id": 14178736,
        "name": "Mex",
        "balance": 3_180_800,
        "roster_value": 51_760_000,
    },
    14151726: {
        "user_id": 14151726,
        "name": "DiosMande",
        "balance": 4_160_283,
        "roster_value": 42_800_000,
    },
    14154203: {
        "user_id": 14154203,
        "name": "Prinzipote",
        "balance": 2_498_172,
        "roster_value": 54_280_000,
    },
    14176382: {
        "user_id": 14176382,
        "name": "Manzagool",
        "balance": -1_162_220,
        "roster_value": 49_970_000,
    },
}


# La capacidad que Pepe publicaba a las 07:52, ANTES de que la
# puja envenenase el ratio. Es la que hay que recuperar.
CAPACIDAD_0752 = {
    14145555: 9_413_772,
    14156489: 23_342_594,
    14178736: 16_120_800,
    14151726: 14_860_283,
    14154203: 16_068_172,
    14176382: 11_330_280,
}


# Los 12 estados con los que se midio la linea, del 12 al 17/08.
# (saldo, maximumBid, plantilla, comprometido)
DOCE_ESTADOS = [
    (-4651032, 8533968, 52740000, 0),
    (-4651032, 8593968, 52980000, 0),
    (-4651032, 7203968, 52980000, 1390000),
    (-4651032, 7261468, 53210000, 1390000),
    (239968, 12414968, 48700000, 0),
    (239968, 12404968, 48660000, 0),
    (239968, 11924968, 48660000, 480000),
    (239968, 11420968, 48660000, 984000),
    (239968, 11900968, 48660000, 504000),
    (239968, 10664967, 48660000, 1740001),
    (239968, 9278966, 48660000, 3126002),
    (-264032, 12053468, 49270000, 0),
]


def _managers():
    """Una copia, que `apply_market_power` escribe encima."""

    return {
        clave: dict(valor)
        for clave, valor in MANAGERS_0904.items()
    }


def _capacidades(own_maximum_bid: int) -> dict:
    """
    La capacidad que publicaria Pepe con ese `maximumBid` suyo.
    """

    managers = _managers()

    calibracion = calibrate_debt_ratio(
        managers=managers,
        current_user_id=NUESTRO_ID,
        own_balance=FOTO_0904["balance"],
        own_maximum_bid=own_maximum_bid,
    )

    apply_market_power(
        managers=managers,
        calibration=calibracion,
        current_user_id=NUESTRO_ID,
        own_maximum_bid=own_maximum_bid,
    )

    return {
        clave: valor["maximum_bid"]
        for clave, valor in managers.items()
    }


# ============================================================
# REGLA 24
# ============================================================

def test_hay_fotos_que_comprobar():

    assert len(MANAGERS_0904) == 7, (
        f"la liga tiene 7 managers y la tabla trae "
        f"{len(MANAGERS_0904)}"
    )

    assert len(CAPACIDAD_0752) == 6, (
        "faltan las capacidades de las 07:52 contra las que "
        "comparar"
    )

    assert len(DOCE_ESTADOS) == 12, (
        f"la linea se midio sobre 12 estados y la tabla trae "
        f"{len(DOCE_ESTADOS)}"
    )

    assert FOTO_0752["maximum_bid"] - FOTO_0904["maximum_bid"] == (
        LA_PUJA
    ), (
        "las dos fotos del incidente no se llevan el importe de "
        "la puja: el fixture no es el caso real"
    )


# ============================================================
# EL INCIDENTE
# ============================================================

def test_una_puja_del_dueno_no_arruina_a_la_liga():
    """
    La foto envenenada de las 09:04, entera.

    Con la puja viva dentro de `maximumBid`, el ratio tiene que
    seguir siendo 0,25, lo comprometido tiene que salir, y NINGUN
    rival puede bajar de capacidad.
    """

    managers = _managers()

    calibracion = calibrate_debt_ratio(
        managers=managers,
        current_user_id=NUESTRO_ID,
        own_balance=FOTO_0904["balance"],
        own_maximum_bid=FOTO_0904["maximum_bid"],
    )

    assert calibracion["available"] is True

    assert calibracion["ratio"] == LINEA_DE_CREDITO == 0.25, (
        f"el ratio se ha vuelto a deducir: sale "
        f"{calibracion['ratio']} en vez de 0,25"
    )

    assert calibracion["headroom"] == 12_510_000, (
        f"el headroom sale {calibracion['headroom']} y tenia que "
        f"ser 12.510.000 (el 25 % de 50.040.000)"
    )

    assert calibracion["committed"] == LA_PUJA, (
        f"la resta da {calibracion['committed']} y la puja del "
        f"dueno fue {LA_PUJA}"
    )

    assert calibracion["anomaly"] is None, (
        "publica anomalia con una foto que cuadra"
    )

    apply_market_power(
        managers=managers,
        calibration=calibracion,
        current_user_id=NUESTRO_ID,
        own_maximum_bid=FOTO_0904["maximum_bid"],
    )

    for clave, antes in CAPACIDAD_0752.items():

        ahora = managers[clave]["maximum_bid"]

        assert ahora >= antes, (
            f"{managers[clave]['name']} baja de {antes} a "
            f"{ahora} por una puja NUESTRA"
        )

    # Y los cinco que no se movieron tienen que salir clavados.
    # Si solo se comprobara ">=", un bug que multiplicara por
    # diez pasaria.
    quietos = {
        k: v for k, v in CAPACIDAD_0752.items()
        if k != 14145555
    }

    for clave, antes in quietos.items():

        assert managers[clave]["maximum_bid"] == antes, (
            f"{managers[clave]['name']}: {managers[clave]['maximum_bid']} "
            f"contra los {antes} de las 07:52"
        )


def test_pollo_sube_porque_vendio_el_no_por_nosotros():
    """
    Pollo17 SI cambia entre las dos fotos, y tiene que cambiar:
    vendio unos 5,3 M. Su capacidad sube, no baja.

    Sin esta guardia, "ningun rival baja" se podria cumplir
    congelando la capacidad de todos, que seria otro error.
    """

    capacidades = _capacidades(FOTO_0904["maximum_bid"])

    assert capacidades[14145555] > CAPACIDAD_0752[14145555], (
        "Pollo vendio 5,3 M y su capacidad no sube"
    )

    esperado = capacidad_de(-7_332_328, 83_620_000)

    assert capacidades[14145555] == esperado == 13_572_672, (
        f"la capacidad de Pollo sale {capacidades[14145555]} y "
        f"su saldo y su plantilla dan {esperado}"
    )


# ============================================================
# EL RATIO NO SE DEDUCE
# ============================================================

def test_el_ratio_no_se_deduce_de_maximum_bid():
    """
    Con `maximumBid` contaminado, el despeje viejo daba 0,0059.
    """

    contaminado = calibrate_debt_ratio(
        managers=_managers(),
        current_user_id=NUESTRO_ID,
        own_balance=FOTO_0904["balance"],
        own_maximum_bid=FOTO_0904["maximum_bid"],
    )

    limpio = calibrate_debt_ratio(
        managers=_managers(),
        current_user_id=NUESTRO_ID,
        own_balance=FOTO_0752["balance"],
        own_maximum_bid=FOTO_0752["maximum_bid"],
    )

    # El despeje viejo, para que se vea lo que se evita.
    ratio_viejo = (
        FOTO_0904["maximum_bid"] - FOTO_0904["balance"]
    ) / FOTO_0904["roster_value"]

    assert round(ratio_viejo, 6) == 0.005855, (
        "el fixture ya no reproduce el ratio hundido del "
        "incidente"
    )

    assert contaminado["ratio"] == limpio["ratio"] == 0.25, (
        "el ratio cambia segun tengamos pujas puestas o no"
    )

    assert contaminado["headroom"] == limpio["headroom"], (
        "el margen de deuda cambia porque nosotros pujemos"
    )


def test_la_capacidad_de_un_rival_no_depende_de_nuestras_pujas():
    """
    Mismos rivales, nuestro `maximumBid` por los suelos: sus
    capacidades no se mueven ni un euro.
    """

    sin_pujas = _capacidades(FOTO_0752["maximum_bid"])

    con_puja = _capacidades(FOTO_0904["maximum_bid"])

    rivales = [k for k in MANAGERS_0904 if k != NUESTRO_ID]

    assert rivales, "no hay rivales que comprobar"

    for clave in rivales:

        assert sin_pujas[clave] == con_puja[clave], (
            f"{MANAGERS_0904[clave]['name']} pasa de "
            f"{sin_pujas[clave]} a {con_puja[clave]} por una "
            f"puja nuestra"
        )


def test_con_cuatro_pujas_puestas_la_liga_sigue_igual():
    """
    El caso que venia: la cartera pone cuatro pujas en la
    ventana del reset y el propio `maximumBid` de Pepe se hunde
    JUSTO cuando decide cuanto ofrecer.
    """

    cuatro_pujas = 2_000_000

    hundido = FOTO_0752["maximum_bid"] - cuatro_pujas

    limpio = _capacidades(FOTO_0752["maximum_bid"])

    pujando = _capacidades(hundido)

    for clave in MANAGERS_0904:

        if clave == NUESTRO_ID:
            continue

        assert limpio[clave] == pujando[clave], (
            f"con cuatro pujas puestas, "
            f"{MANAGERS_0904[clave]['name']} cambia de "
            f"{limpio[clave]} a {pujando[clave]}"
        )


# ============================================================
# LAS TRES VIAS
# ============================================================

def test_las_tres_vias_concuerdan_sobre_el_caso_real():
    """
    Tablon, resta y diferencia entre fotos: las tres,
    12.217.000.

    Hoy la resta daba CERO y mandaba la conservadora por suerte,
    no por diseno.
    """

    # A. El tablon lo publicaba: live_bid 12.217.000.
    tablon = LA_PUJA

    # B. La resta, con la linea medida.
    resta = comprometido_de(
        FOTO_0904["balance"],
        FOTO_0904["maximum_bid"],
        FOTO_0904["roster_value"],
    )

    # C. La diferencia entre las dos fotos: mismo saldo, sin
    #    reset por medio.
    assert FOTO_0752["balance"] == FOTO_0904["balance"], (
        "las dos fotos no tienen el mismo saldo: la via de la "
        "diferencia no valdria"
    )

    diferencia = (
        FOTO_0752["maximum_bid"] - FOTO_0904["maximum_bid"]
    )

    assert resta["committed"] == tablon, (
        f"la resta da {resta['committed']} y el tablon "
        f"{tablon}"
    )

    assert diferencia == tablon, (
        f"la diferencia da {diferencia} y el tablon {tablon}"
    )

    assert resta["anomaly"] is None


def test_la_linea_medida_cuadra_en_los_doce_estados():
    """
    maximumBid == saldo + plantilla/4 - comprometido, al euro.
    """

    for saldo, tope, valor, comprometido in DOCE_ESTADOS:

        previsto = saldo + headroom_de(valor) - comprometido

        assert previsto == tope, (
            f"saldo {saldo}: la cuenta da {previsto} y "
            f"maximumBid es {tope}"
        )

        cuenta = comprometido_de(saldo, tope, valor)

        assert cuenta["committed"] == comprometido, (
            f"saldo {saldo}: la resta da "
            f"{cuenta['committed']} y habia {comprometido}"
        )


# ============================================================
# LO IMPOSIBLE SE AVISA
# ============================================================

def test_lo_imposible_se_avisa_y_no_se_adopta():
    """
    Un comprometido negativo dice que el 0,25 ya no vale. Se
    publica el aviso y se SIGUE con 0,25 hasta medirlo otra vez.

    Adoptar en caliente un ratio deducido de una foto rara es
    exactamente lo que arruino a la liga.
    """

    # maximumBid mas alto de lo que la linea permite.
    raro = comprometido_de(1_000_000, 90_000_000, 40_000_000)

    assert raro["available"] is True
    assert raro["committed"] == 0, (
        "publica un comprometido negativo, que no existe"
    )

    assert raro["anomaly"] is not None, (
        "no avisa de que la linea no cuadra"
    )

    assert raro["ratio"] == 0.25, (
        f"ha adoptado un ratio nuevo en caliente: "
        f"{raro['ratio']}"
    )

    assert raro["anomaly"]["implied_ratio"] is not None, (
        "no publica cual seria el ratio, que es lo que hace "
        "falta para volver a medirlo"
    )

    assert "ANOMALIA" in (raro["reason"] or "")


# ============================================================
# NOSOTROS, CON EL NUMERO OFICIAL
# ============================================================

def test_nuestro_maximum_bid_es_el_oficial():
    """
    De los rivales no sabemos si tienen pujas puestas; de
    nosotros, si. Para decidir manda el oficial.
    """

    managers = _managers()

    calibracion = calibrate_debt_ratio(
        managers=managers,
        current_user_id=NUESTRO_ID,
        own_balance=FOTO_0904["balance"],
        own_maximum_bid=FOTO_0904["maximum_bid"],
    )

    apply_market_power(
        managers=managers,
        calibration=calibracion,
        current_user_id=NUESTRO_ID,
        own_maximum_bid=FOTO_0904["maximum_bid"],
    )

    nuestro = managers[NUESTRO_ID]

    assert nuestro["maximum_bid"] == FOTO_0904["maximum_bid"], (
        f"nuestra capacidad sale {nuestro['maximum_bid']} y el "
        f"oficial es {FOTO_0904['maximum_bid']}"
    )

    assert nuestro["maximum_bid_source"] == "OFICIAL_BIWENGER"

    # Y lo bruto al lado, para poder ver cuanto nos quita la
    # puja.
    assert nuestro["maximum_bid_gross"] > nuestro["maximum_bid"], (
        "no se publica lo que podriamos pujar sin la puja "
        "puesta"
    )


def test_ningun_manager_se_queda_sin_capacidad_por_nuestra_culpa():
    """
    Pollo17 y Manzagool salieron a CERO el 10/09. Con saldo
    negativo su capacidad no puede ser cero mientras tengan
    plantilla.
    """

    capacidades = _capacidades(FOTO_0904["maximum_bid"])

    for clave in (14145555, 14176382):

        assert capacidades[clave] > 0, (
            f"{MANAGERS_0904[clave]['name']} sigue saliendo a "
            f"cero"
        )


# ============================================================
# FORMA Y BLINDAJE
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    con = comprometido_de(100, 200, 400)
    sin = comprometido_de(None, None, None)

    assert set(con) == set(sin), (
        f"la forma cambia: {set(con) ^ set(sin)}"
    )


def test_nada_de_esto_lanza():

    for basura in (None, "no", {}, [], 0, -1):

        assert isinstance(
            comprometido_de(basura, basura, basura), dict
        )
        assert isinstance(headroom_de(basura), int)
        assert isinstance(capacidad_de(basura, basura), int)

    assert capacidad_de(-5_000_000, 0) == 0, (
        "una capacidad negativa no existe"
    )


TESTS = [
    test_hay_fotos_que_comprobar,
    test_una_puja_del_dueno_no_arruina_a_la_liga,
    test_pollo_sube_porque_vendio_el_no_por_nosotros,
    test_el_ratio_no_se_deduce_de_maximum_bid,
    test_la_capacidad_de_un_rival_no_depende_de_nuestras_pujas,
    test_con_cuatro_pujas_puestas_la_liga_sigue_igual,
    test_las_tres_vias_concuerdan_sobre_el_caso_real,
    test_la_linea_medida_cuadra_en_los_doce_estados,
    test_lo_imposible_se_avisa_y_no_se_adopta,
    test_nuestro_maximum_bid_es_el_oficial,
    test_ningun_manager_se_queda_sin_capacidad_por_nuestra_culpa,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA LINEA DE CREDITO V1")
    print("=" * 60)

    fallos = 0

    for prueba in TESTS:

        try:
            prueba()
            print(f"  OK    {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"  FALLA {prueba.__name__}")
            print(f"        {error}")

        except Exception as error:                  # noqa: BLE001
            fallos += 1
            print(f"  ROMPE {prueba.__name__}")
            print(f"        {type(error).__name__}: {error}")

    print("=" * 60)

    if fallos:
        print(f"{fallos} de {len(TESTS)} en rojo.")
        raise SystemExit(1)

    print(f"Los {len(TESTS)} en verde.")


if __name__ == "__main__":
    main()
