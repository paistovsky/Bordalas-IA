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
LIBRO = {
    "FUTBOLFANTASY": {
        "decided": 7579,
        "hit_rate": 89.1,
        "mean_magnitude_error_percent": 3.98,
    },
    "ANALITICA": {
        "decided": 3295,
        "hit_rate": 95.5,
        "mean_magnitude_error_percent": 1.12,
    },
    "COMUNIATE": {
        "decided": 2982,
        "hit_rate": 97.1,
        "mean_magnitude_error_percent": 0.93,
    },
    # LA MALA: acierta el 72,9 % y se equivoca 35,71 puntos en el
    # tamaño sobre magnitudes que rondan el 1 %.
    "COMUNIATE_PULSO": {
        "decided": 1031,
        "hit_rate": 72.9,
        "mean_magnitude_error_percent": 35.71,
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

    # Y LOS DOS RECORTES TIRAN EN EL MISMO SENTIDO.
    assert buena["direccion"] > mala["direccion"], (buena, mala)

    assert buena["tamano"] > mala["tamano"], (buena, mala)

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


def test_un_movimiento_pequeno_no_sobrevive_a_su_error() -> None:
    """
    El detalle que hace que esto no sea una imprudencia.

    FutbolFantasy se equivoca 3,98 puntos en el tamaño. Sobre un
    movimiento de +0,30 % eso no es un pronostico: es ruido con
    decimales. Tiene que salir SIN PRONOSTICO, no +0,28 %.
    """

    r = estimacion(MARC_ROCA, LIBRO)

    assert r["available"] is False, (
        f"un movimiento de +0,30 % con fuentes que se equivocan "
        f"entre 0,93 y 3,98 puntos ha producido "
        f"{r['percent_per_day']}"
    )

    assert r["decision"] == "SIN_PRONOSTICO", r

    # Y EL GRANDE SI SOBREVIVE: si no, esto solo probaria que
    # nunca hay pronostico.
    grande = estimacion(PEDRO_DIAZ, LIBRO)

    assert grande["available"], (
        "ningun movimiento sobrevive al recorte: entonces el "
        "enchufe no sirve para nada"
    )

    print(
        "  OK  +0,30 % no sobrevive a su propio error y +4,55 % si"
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
    test_un_movimiento_pequeno_no_sobrevive_a_su_error,
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
