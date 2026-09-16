"""
El ojeador enchufado: dos jugadores distintos, dos numeros distintos.

EL SINTOMA (15/09/2026)

    El carril rechazaba nueve candidatos de la misma foto con el
    MISMO numero hasta el cuarto decimal:

        Marc Roca     ojeador +0,30 %  ->  rinde 0,1443 %
        Pedro Diaz    ojeador +4,55 %  ->  rinde 0,1443 %

    El ojeador decia que Pedro Diaz sube quince veces mas que
    Marc Roca, y al motor le salia el mismo numero. Un
    instrumento que acierta el 90 % enchufado a ninguna parte.

LO QUE SE PRUEBA AQUI

    1. Que dos pronosticos distintos dan estimaciones distintas.
    2. Que sin lectura del ojeador NO hay numero: "SIN
       PRONOSTICO", nunca una constante.
    3. Que una fuente mala pesa menos que una buena, con el libro
       de acierto delante.
    4. Que el interruptor sigue APAGADO: el enchufe se pone, la
       luz la da el dueño.

UNA GUARDIA CAMBIO LO QUE EXIGE (16/09/2026)

    `test_un_movimiento_pequeno_no_sobrevive_a_su_error` exigia
    que un +0,30 % saliera SIN PRONOSTICO. Ahora se llama
    `test_un_movimiento_pequeno_sale_pequeno_no_mudo` y exige que
    salga +0,28 %.

    El motivo entero esta en su docstring, con la medicion: el
    recorte por tamaño empeoraba la estimacion un 24 % y dejaba
    mudo al 36 % de los casos, incluidos los que MAS se movian.
    Se cambia lo que una guardia exige muy pocas veces y nunca en
    silencio.

DOS COSAS QUE ESTA GUARDIA NO PRUEBA, Y HAY QUE SABERLO

    No prueba que el motor use esto —no lo usa, esta apagado— ni
    que el 0,1443 % haya desaparecido. Prueba que la pieza que lo
    sustituiria distingue jugadores, que es lo que aquel numero
    no hacia.

REGLA 23 / DOCTRINA 50

    Ni disco, ni red, ni reloj: el informe del ojeador y el libro
    de acierto son fixtures escritos aqui.

DOCTRINA 55: un agregado sin su `n` es una anecdota

    El libro de mentira lleva el `n` de cada fuente, y
    `peso_de_la_fuente` se niega a pesar una fuente cuyo `n` sea
    cero aunque traiga un acierto estupendo.
"""

from __future__ import annotations

from src.analysis.el_pronostico_del_ojeador import (
    ENCENDIDO,
    PERSISTENCIA,
    esta_encendido,
    estimacion,
    medir_persistencia,
    peso_de_la_fuente,
)


# EL LIBRO DE ACIERTO, con los numeros medidos en produccion el
# 15/09/2026. Cada uno con su `n`.
#
# EL NULO: CUANTO SE EQUIVOCA NO DECIR NADA (16/09/2026)
#
#     `mean_abs_actual_percent` es el error de estimar cero, sobre
#     la MISMA muestra. Es una propiedad del movimiento de los
#     precios, no de la fuente, asi que es casi igual para todas;
#     medido sobre nuestra serie de 31 dias:
#
#         plazo 1   2,405        plazo 3   6,750
#         plazo 7  14,233
#
#     Una fuente aporta su TAMAÑO solo si se equivoca menos que
#     eso. Las tres buenas lo baten de sobra; COMUNIATE_PULSO,
#     con 35,71 puntos, no lo bate ni de lejos.
LIBRO = {
    "FUTBOLFANTASY": {
        "decided": 7579,
        "hit_rate": 89.1,
        "mean_magnitude_error_percent": 3.98,
        "mean_abs_actual_percent": 6.90,
        "size_beats_null": True,
        "by_horizon": {
            "1": {
                "decided": 4000,
                "hit_rate": 97.8,
                "mean_magnitude_error_percent": 0.748,
                "mean_abs_actual_percent": 2.405,
            },
            "3": {
                "decided": 2500,
                "hit_rate": 90.6,
                "mean_magnitude_error_percent": 3.832,
                "mean_abs_actual_percent": 6.750,
            },
        },
    },
    "ANALITICA": {
        "decided": 3295,
        "hit_rate": 95.5,
        "mean_magnitude_error_percent": 1.12,
        "mean_abs_actual_percent": 6.90,
        "size_beats_null": True,
    },
    "COMUNIATE": {
        "decided": 2982,
        "hit_rate": 97.1,
        "mean_magnitude_error_percent": 0.93,
        "mean_abs_actual_percent": 6.90,
        "size_beats_null": True,
    },
    # LA MALA: acierta el 72,9 % y se equivoca 35,71 puntos en el
    # tamaño. No bate al nulo: su magnitud NO entra.
    "COMUNIATE_PULSO": {
        "decided": 1031,
        "hit_rate": 72.9,
        "mean_magnitude_error_percent": 35.71,
        "mean_abs_actual_percent": 6.90,
        "size_beats_null": False,
    },
    # SIN MEDIR EL NULO: no se sabe si su tamaño acerca o aleja,
    # asi que no se usa. Esta aqui para que la guardia pueda
    # comprobar que "no se sabe" NO es "adelante" (regla 24).
    "FUENTE_SIN_NULO": {
        "decided": 500,
        "hit_rate": 95.0,
        "mean_magnitude_error_percent": 1.00,
    },
}


def _ficha(**por_fuente):
    """Una ficha del informe del ojeador, a un dia."""

    return {
        "signals": [
            {
                "source": fuente,
                "direction": "UP" if magnitud > 0 else "DOWN",
                "magnitude_percent": magnitud,
                "horizon_days": 1,
            }
            for fuente, magnitud in por_fuente.items()
        ]
    }


# Los dos del sintoma, con las tres fuentes buenas de acuerdo.
PEDRO_DIAZ = _ficha(
    FUTBOLFANTASY=4.55, ANALITICA=4.55, COMUNIATE=4.55
)

MARRERO = _ficha(
    FUTBOLFANTASY=2.63, ANALITICA=2.63, COMUNIATE=2.63
)

MARC_ROCA = _ficha(
    FUTBOLFANTASY=0.30, ANALITICA=0.30, COMUNIATE=0.30
)


# ============================================================
# REGLA 24: EL FIXTURE TIENE QUE TRAER DE TODO
# ============================================================


def test_el_fixture_trae_de_todo() -> None:
    """
    Sin libro de acierto, sin fuentes buenas y malas, y sin dos
    pronosticos distintos, las demas se pondrian verdes sin
    haber probado su mitad.
    """

    assert LIBRO, "el libro de acierto de la prueba esta vacio"

    assert len(LIBRO) >= 3, LIBRO

    for fuente, medida in LIBRO.items():
        assert medida["decided"] > 0, (
            f"{fuente} no trae `n`: un agregado sin su n es una "
            f"anecdota (doctrina 55)"
        )
        assert medida["hit_rate"] is not None, fuente

    aciertos = {m["hit_rate"] for m in LIBRO.values()}

    assert len(aciertos) > 1, (
        "todas las fuentes de la prueba aciertan lo mismo: no se "
        "podria distinguir si pesan distinto"
    )

    assert PEDRO_DIAZ["signals"] and MARC_ROCA["signals"], (
        "el ojeador de la prueba llega vacio"
    )

    print(
        f"  OK  el fixture trae {len(LIBRO)} fuentes medidas con "
        f"aciertos distintos y dos pronosticos distintos"
    )


# ============================================================
# 1. DOS PRONOSTICOS DISTINTOS, DOS NUMEROS DISTINTOS
# ============================================================


def test_la_especulacion_lee_al_ojeador() -> None:
    """
    El fallo que abrio el encargo: mismo numero para todos.

    Dos jugadores con el mismo precio y pronosticos distintos
    tienen que dar estimaciones distintas. Y en el mismo orden
    que el ojeador: quien sube mas, estima mas.
    """

    alto = estimacion(PEDRO_DIAZ, LIBRO)

    medio = estimacion(MARRERO, LIBRO)

    assert alto["available"], alto

    assert medio["available"], medio

    assert alto["percent_per_day"] != medio["percent_per_day"], (
        f"dos pronosticos distintos (+4,55 % y +2,63 %) dan la "
        f"MISMA estimacion ({alto['percent_per_day']}): es el "
        f"0,1443 % otra vez"
    )

    assert alto["percent_per_day"] > medio["percent_per_day"], (
        f"el que el ojeador dice que sube mas estima MENOS: "
        f"{alto['percent_per_day']} contra "
        f"{medio['percent_per_day']}"
    )

    # Y NO ES UNA CONSTANTE DISFRAZADA: la estimacion se mueve
    # con el pronostico, no con el precio.
    otro = estimacion(
        _ficha(
            FUTBOLFANTASY=8.0, ANALITICA=8.0, COMUNIATE=8.0
        ),
        LIBRO,
    )

    assert otro["percent_per_day"] > alto["percent_per_day"], otro

    print(
        f"  OK  +4,55 % -> {alto['percent_per_day']:+.3f} %/dia y "
        f"+2,63 % -> {medio['percent_per_day']:+.3f} %/dia: "
        f"distintos y en orden"
    )


def test_la_estimacion_no_supera_a_lo_observado() -> None:
    """
    El recorte recorta: nunca adorna.

    Ninguna estimacion puede salir mayor que el movimiento que la
    fuente observo. Si saliera, el "recorte" estaria inflando.
    """

    for nombre, ficha, dicho in (
        ("Pedro Diaz", PEDRO_DIAZ, 4.55),
        ("Marrero", MARRERO, 2.63),
    ):
        r = estimacion(ficha, LIBRO)

        assert r["available"], (nombre, r)

        assert abs(r["percent_per_day"]) <= abs(dicho), (
            f"{nombre}: el ojeador observa {dicho:+.2f} % y la "
            f"estimacion sale {r['percent_per_day']:+.2f} %"
        )

        assert abs(r["percent_per_day"]) <= abs(
            r["observed_percent"]
        ), r

    print(
        "  OK  la estimacion nunca sale mayor que lo observado"
    )


# ============================================================
# 2. SIN OJEADOR NO HAY NUMERO
# ============================================================


def test_sin_ojeador_no_hay_numero() -> None:
    """
    Doctrina 24: nada pasa con las manos vacias.

    Sin lectura, con el libro vacio, o con las fuentes
    contradiciendose: "SIN PRONOSTICO". Nunca una constante.
    """

    casos = {
        "sin ficha": (None, LIBRO),
        "ficha vacia": ({"signals": []}, LIBRO),
        "sin libro de acierto": (PEDRO_DIAZ, {}),
        "libro nulo": (PEDRO_DIAZ, None),
        "fuente no medida": (
            _ficha(UNA_QUE_NO_ESTA=4.0),
            LIBRO,
        ),
        "se contradicen": (
            _ficha(COMUNIATE=3.0, ANALITICA=-3.0),
            LIBRO,
        ),
    }

    for etiqueta, (ficha, libro) in casos.items():

        r = estimacion(ficha, libro)

        assert r["available"] is False, (etiqueta, r)

        assert r["percent_per_day"] is None, (
            f"{etiqueta}: se ha devuelto un numero "
            f"({r['percent_per_day']}) donde no hay pronostico"
        )

        assert r["decision"] == "SIN_PRONOSTICO", (etiqueta, r)

        assert r["reason"], (
            f"{etiqueta}: no se dice POR QUE no hay pronostico"
        )

    # Y UNA FUENTE MEDIDA CON n=0 TAMPOCO VALE, aunque su acierto
    # sea estupendo: un agregado sin su n es una anecdota.
    sin_n = estimacion(
        _ficha(NUEVA=4.0),
        {
            "NUEVA": {
                "decided": 0,
                "hit_rate": 99.9,
                "mean_magnitude_error_percent": 0.1,
            }
        },
    )

    assert sin_n["available"] is False, sin_n

    print(
        f"  OK  los {len(casos) + 1} casos sin lectura dicen SIN "
        f"PRONOSTICO y explican por que"
    )


# ============================================================
# 3. UNA FUENTE MALA PESA MENOS
# ============================================================


def test_una_fuente_mala_pesa_menos() -> None:
    """
    COMUNIATE_PULSO acierta el 72,9 % con 35,71 puntos de error.
    COMUNIATE acierta el 97,1 % con 0,93.

    No pueden empujar igual.
    """

    magnitud = 4.55

    buena = peso_de_la_fuente(LIBRO["COMUNIATE"], magnitud)

    mala = peso_de_la_fuente(
        LIBRO["COMUNIATE_PULSO"], magnitud
    )

    assert buena["peso"] > mala["peso"], (
        f"la fuente del 72,9 % pesa {mala['peso']} y la del "
        f"97,1 % pesa {buena['peso']}"
    )

    # LA DIRECCION SE RECORTA POR ACIERTO, y la buena acierta mas.
    assert buena["direccion"] > mala["direccion"], (buena, mala)

    # EL TAMAÑO YA NO SE RECORTA: SE ADMITE O NO (16/09/2026)
    #
    #     Antes esta linea era `buena["tamano"] > mala["tamano"]`
    #     con los dos recortados por `1 - error/|magnitud|`. Ese
    #     recorte se quito porque, medido contra lo que paso de
    #     verdad, empeoraba la estimacion un 24 % a un dia y
    #     dejaba mudo al 36 % de los casos. Ver
    #     `peso_de_la_fuente`.
    #
    #     Lo que el recorte SI hacia bien —tapar a PULSO— lo hace
    #     ahora la puerta, y la guardia sigue exigiendo lo mismo
    #     que exigia: que la mala no empuje.
    assert mala["usable"] is False, (
        f"la fuente que se equivoca 35,71 puntos contra un nulo "
        f"de 6,90 esta aportando su tamaño: {mala}"
    )

    assert buena["usable"] is True, (
        f"la fuente del 97,1 % no aporta nada: {buena}"
    )

    # Y UNA FUENTE SIN EL NULO MEDIDO TAMPOCO PASA: no saber si
    # acerca no es lo mismo que saber que acerca (regla 24).
    sin_nulo = peso_de_la_fuente(
        LIBRO["FUENTE_SIN_NULO"], magnitud
    )

    assert sin_nulo["usable"] is False, (
        f"una fuente sin el nulo medido esta pesando: {sin_nulo}"
    )

    # LA MALA, SOLA, NO PUEDE MOVER LA ESTIMACION COMO LA BUENA.
    solo_buena = estimacion(_ficha(COMUNIATE=magnitud), LIBRO)

    solo_mala = estimacion(
        _ficha(COMUNIATE_PULSO=magnitud), LIBRO
    )

    assert solo_buena["available"], solo_buena

    if solo_mala["available"]:
        assert (
            solo_mala["percent_per_day"]
            < solo_buena["percent_per_day"]
        ), (
            f"la fuente mala estima "
            f"{solo_mala['percent_per_day']} y la buena "
            f"{solo_buena['percent_per_day']}"
        )

    # Y SU ERROR SE LA COME cuando dice una barbaridad: 36,6 % de
    # movimiento con 35,71 de error no puede salir como +34 %.
    barbaridad = estimacion(
        _ficha(COMUNIATE_PULSO=36.6), LIBRO
    )

    if barbaridad["available"]:
        assert barbaridad["percent_per_day"] < 5.0, (
            f"un +36,6 % de la fuente con 35,71 puntos de error "
            f"sale como {barbaridad['percent_per_day']:+.2f} %: "
            f"el error de tamaño no esta recortando"
        )

    print(
        f"  OK  la del 72,9 % pesa {mala['peso']:.4f} y la del "
        f"97,1 % pesa {buena['peso']:.4f}"
    )


def test_un_movimiento_pequeno_sale_pequeno_no_mudo() -> None:
    """
    ESTA GUARDIA AFIRMABA LO CONTRARIO HASTA EL 16/09/2026, y hay
    que decirlo entero porque cambiar lo que una guardia exige es
    lo mas peligroso que se hace en este repo.

    LO QUE EXIGIA

        Que un movimiento de +0,30 % saliera SIN PRONOSTICO,
        porque el error de tamaño de la fuente (3,98) se lo comia.
        Se llamaba `test_un_movimiento_pequeno_no_sobrevive_a_su_error`.

    POR QUE ERA FALSO

        Aquel 3,98 agrupaba horizontes de 1, 3 y 7 dias. El error
        a UN dia es 0,748. Y aun con el numero correcto, el
        recorte `1 - error/|magnitud|` deja mudo a todo el que se
        mueva menos que la dispersion de la fuente, que son los
        movimientos normales.

        Medido contra lo que paso de verdad, sobre 12.615 pares a
        un dia (error medio absoluto, menos es mejor):

            no pronosticar nunca            1,8942
            con recorte (lo que exigia)     0,8922   mudo 36 %
            con recorte y error corregido   0,9220   mudo 39 %
            sin recorte (lo de ahora)       0,6805   mudo  0 %

        El silencio no describia al jugador: describia a la
        fuente. Y dejaba fuera a 86 de los 171 mudos, entre ellos
        los que MAS se movian.

    LO QUE EXIGE AHORA

        Que un movimiento pequeño salga PEQUEÑO —no mudo, y no
        inflado—, y que siga siendo mucho menor que uno grande.
        La prudencia no esta en callarse: esta en que el numero
        sea proporcional a lo que se observo.
    """

    pequeno = estimacion(MARC_ROCA, LIBRO)

    grande = estimacion(PEDRO_DIAZ, LIBRO)

    assert grande["available"], (
        "ningun movimiento produce pronostico: entonces el "
        "enchufe no sirve para nada"
    )

    assert pequeno["available"], (
        f"un +0,30 % de tres fuentes que baten al nulo sigue "
        f"saliendo mudo: {pequeno['reason']}"
    )

    # PEQUEÑO DE VERDAD, y no por poco.
    assert 0 < pequeno["percent_per_day"] < 0.5, (
        f"un +0,30 % observado ha salido como "
        f"{pequeno['percent_per_day']}"
    )

    assert (
        pequeno["percent_per_day"] < grande["percent_per_day"] / 5
    ), (
        f"el pequeño ({pequeno['percent_per_day']}) no queda muy "
        f"por debajo del grande ({grande['percent_per_day']}): "
        f"la estimacion no es proporcional a lo observado"
    )

    # Y NUNCA POR ENCIMA DE LO OBSERVADO: la persistencia encoge.
    for nombre, r in (("pequeño", pequeno), ("grande", grande)):
        assert abs(r["percent_per_day"]) <= abs(
            r["observed_percent"]
        ), (
            f"el {nombre} estima {r['percent_per_day']} sobre un "
            f"observado de {r['observed_percent']}: el recorte "
            f"infla en vez de encoger"
        )

    print(
        f"  OK  +0,30 % sale {pequeno['percent_per_day']:+.3f} % "
        f"y +4,55 % sale {grande['percent_per_day']:+.3f} %: "
        f"pequeño, no mudo"
    )


# ============================================================
# 4. LA PERSISTENCIA SE MIDE
# ============================================================


def test_la_persistencia_se_mide_no_se_escribe() -> None:
    """
    `PERSISTENCIA` es una afirmacion sobre Biwenger. Una
    afirmacion sobre el mundo que no se puede recalcular es una
    opinion con cara de constante.
    """

    # Una serie que sube un 10 % y luego la mitad, todos los dias.
    serie = {
        str(i): [1000, 1100, 1155, 1213, 1274]
        for i in range(40)
    }

    medido = medir_persistencia(serie)

    assert medido["available"], medido

    # REGLA 24: sin pares esto no probaria nada.
    assert medido["n"] > 0, medido

    assert medido["factor"] is not None, medido

    assert 0 < medido["factor"] <= 1.5, medido

    assert medido["misma_direccion"] == 1.0, medido

    # UNA SERIE QUE ALTERNA NO PERSISTE.
    alterna = {
        str(i): [1000, 1100, 1000, 1100, 1000]
        for i in range(40)
    }

    contraria = medir_persistencia(alterna)

    assert contraria["available"], contraria

    assert contraria["factor"] < 0, (
        f"una serie que alterna tiene que dar persistencia "
        f"NEGATIVA y da {contraria['factor']}"
    )

    assert contraria["misma_direccion"] == 0.0, contraria

    # Y SIN SERIE, NO SE MIDE.
    for vacio in ({}, None, {"1": [1000]}):
        nada = medir_persistencia(vacio)
        assert nada["available"] is False, (vacio, nada)
        assert nada["factor"] is None, nada
        assert nada["reason"], nada

    assert 0 < PERSISTENCIA <= 1.0, (
        f"la persistencia publicada ({PERSISTENCIA}) no esta "
        f"entre 0 y 1: lo de ayer no puede repetirse AUMENTADO"
    )

    print(
        f"  OK  la persistencia se recalcula: {medido['factor']} "
        f"sobre n={medido['n']}, y una serie que alterna da "
        f"{contraria['factor']}"
    )


# ============================================================
# 5. EL INTERRUPTOR SIGUE APAGADO
# ============================================================


def test_el_enchufe_esta_puesto_y_la_luz_apagada() -> None:
    """
    El encargo: "Dejalo apagado detras de un interruptor. Lo
    enciendo yo con esa tabla delante."
    """

    assert ENCENDIDO is False, (
        "el ojeador se ha quedado ENCENDIDO: la luz la da el "
        "dueño con la tabla delante, no este commit"
    )

    assert esta_encendido() is False, (
        "`esta_encendido()` no respeta la constante"
    )

    # Pero la pieza CALCULA igualmente: hace falta para poder
    # enseñar el antes y el despues.
    assert estimacion(PEDRO_DIAZ, LIBRO)["available"], (
        "apagado no puede significar que no calcule: entonces no "
        "se podria enseñar la tabla del antes y el despues"
    )

    print(
        "  OK  el enchufe esta puesto, calcula, y la luz sigue "
        "apagada"
    )


TESTS = [
    test_el_fixture_trae_de_todo,
    test_la_especulacion_lee_al_ojeador,
    test_la_estimacion_no_supera_a_lo_observado,
    test_sin_ojeador_no_hay_numero,
    test_una_fuente_mala_pesa_menos,
    test_un_movimiento_pequeno_sale_pequeno_no_mudo,
    test_la_persistencia_se_mide_no_se_escribe,
    test_el_enchufe_esta_puesto_y_la_luz_apagada,
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
        f"EL OJEADOR CONECTADO V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
