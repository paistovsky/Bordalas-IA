"""
No se valora por encima de lo que se ha medido.

SINTOMA

    El 14/09 la via TENER se encendio apoyada en una celda del
    retrotest medida con racha de UN dia. Y al dia siguiente se
    aplico a estos tres:

        Roro Riquelme   1,666 %/dia   racha de 50 dias
        Amatucci        1,098 %/dia   racha de 19 dias
        Pedri           0,305 %/dia   racha de  8 dias

    Ninguna de esas rachas existe en el retrotest.

CAUSA

    Una racha de `n` dias consume `n` dias por delante y deja el
    resto por detras, asi que con una ventana corta la racha
    maxima medible AL HORIZONTE DE TRES DIAS es DOS.

CONSECUENCIA

    Extrapolar a 50 dias desde una curva que llega a 2, en la
    direccion en que el rendimiento cae, es la clase de error que
    este proyecto lleva un mes aprendiendo a no cometer.

    Y el precio de equivocarse aqui no es un decimal: es meter
    medio patrimonio en el jugador equivocado.

# ============================================================
# LO QUE CAMBIO EL 17/09/2026, CON PRODUCCION CAIDA
# ============================================================

SEGUNDO SINTOMA

    Verde en el disco del dueño, rojo en GitHub Actions. Ciclo de
    produccion parado desde las 11:00.

SEGUNDA CAUSA

    Esta guardia leia el almacen REAL. `_calibrado()` solo se
    protegia de que el fichero NO EXISTIERA; del caso de que
    existiera con OTRO contenido, no.

    Y ese es justo el caso de Actions, donde la cache se restaura
    antes de correr la verja. Reproducido con el mismo codigo:

        almacen de 25 dias:
            "la calibracion dice que llega a rachas de 7 dias
             con una ventana de seis"

        almacen de 3 dias:
            TypeError: '<=' not supported between instances of
            'NoneType' and 'int'

    Lo segundo ni siquiera era un rojo: era un traceback que
    `main` no atrapaba.

LO QUE SE HIZO

    Almacen de fixture, construido en el repositorio, siempre
    igual. Cero lecturas de `data/`.

    Y la comprobacion que era una conclusion de mercado —"los
    tres del informe dejan de compensar"— pasa a comprobar el
    MECANISMO: que el recorte muerde en el techo del tramo. Si lo
    que se quiere saber es cuanto rinden hoy esos tres, eso se
    mide en el informe de la noche, con datos de verdad.
"""

from __future__ import annotations

from src.analysis.hold_backtest import rate_bucket_of
from src.analysis.hold_value import (
    DEFAULT_HORIZON_DAYS,
    calibration_for,
    hold_value,
    reset_calibration_cache,
)
from src.analysis.price_store_fixture import almacen_de_mentira


# Los tres del informe del 14/09, con sus numeros de produccion.
# Se conservan porque son el caso real que hay que sostener; lo
# que ya no se conserva es la tabla contra la que se median.
FUERA_DE_MUESTRA = (
    ("Roro Riquelme", 4_240_000, 1.666, 50),
    ("Amatucci", 3_670_000, 1.098, 19),
    ("Pedri", 15_350_000, 0.305, 8),
)


# ============================================================
# 1. EL RANGO MEDIDO ES EL QUE ES
# ============================================================


def test_la_racha_maxima_medida_a_tres_dias_es_dos() -> None:
    """
    Con seis dias de ventana y horizonte de tres, la racha mas
    larga que se puede observar es de dos dias. No cinco, que es
    lo que dice la tabla mirada por encima: cinco es la racha
    maxima observada A UN DIA de horizonte.

    ANTES ESTO DEPENDIA DEL DIA

        Con la cache de Actions -25 dias- la calibracion llegaba
        a rachas de 7 y la guardia caia. Con una cache de 3 dias,
        `max_streak` venia a None y esto reventaba con un
        TypeError. La ventana es ahora del fixture.
    """

    with almacen_de_mentira():

        calibrado = calibration_for(DEFAULT_HORIZON_DAYS)

        assert calibrado["available"]

        assert calibrado["max_streak"] is not None, (
            "la calibracion no trae racha maxima: antes esto "
            "reventaba con un TypeError en vez de dar un rojo"
        )

        assert calibrado["max_streak"] <= 5, (
            f"la calibracion dice que llega a rachas de "
            f"{calibrado['max_streak']} dias con una ventana de "
            f"seis"
        )

        # El tramo de arriba se partio el 16/09 en 1-2 %, 2-4 % y
        # > 4 %. Se mira el primero, que es donde caen Roro
        # (1,666) y Amatucci (1,098).
        tramo = calibrado["by_rate_bucket"].get("1-2 %")

        assert tramo and tramo.get("calibrated")
        assert tramo["max_streak"] == 2, (
            f"el tramo bueno dice estar calibrado hasta rachas de "
            f"{tramo['max_streak']} dias a "
            f"{DEFAULT_HORIZON_DAYS} de horizonte"
        )


def test_el_rango_de_validez_viaja_con_el_valor() -> None:
    """
    "calibrado sobre rachas de 1 a 2 dias; este lleva 50". En el
    objeto, para que la pantalla pueda decirlo.
    """

    with almacen_de_mentira():

        salida = hold_value(
            4_240_000, 1.666, trend_days=50, sources=3
        )

        for clave in (
            "in_sample",
            "calibrated_streak_max",
            "trend_days",
            "gain_before_clamp",
            "clamped",
            "sample_note",
        ):
            assert clave in salida, f"falta `{clave}` en la salida"

        assert salida["in_sample"] is False
        assert salida["trend_days"] == 50
        assert "FUERA DE MUESTRA" in salida["sample_note"]
        assert "50" in salida["sample_note"]


# ============================================================
# 2. EL RECORTE
# ============================================================


def test_una_racha_fuera_de_muestra_no_vale_mas_que_la_ultima_medida() -> None:
    """
    LA GUARDIA QUE PIDIO EL ENCARGO POR SU NOMBRE

        Un jugador con racha por encima del maximo observado no
        puede recibir un `hold_value` mayor que el del ultimo
        tramo medido.
    """

    with almacen_de_mentira():

        calibrado = calibration_for(DEFAULT_HORIZON_DAYS)

        for nombre, precio, tasa, racha in FUERA_DE_MUESTRA:

            salida = hold_value(
                precio, tasa, trend_days=racha, sources=3
            )

            if not salida["value"]:
                continue

            tramo = calibrado["by_rate_bucket"].get(
                rate_bucket_of(tasa)
            )

            if not tramo or not tramo.get("calibrated"):
                continue

            if racha <= tramo["max_streak"]:
                continue

            techo = int(precio * float(tramo["median"]))

            assert salida["in_sample"] is False, (
                f"{nombre} lleva {racha} dias de racha y sale "
                f"como dentro de muestra"
            )

            assert salida["raw_gain"] <= techo, (
                f"{nombre}: se le reconoce una ganancia de "
                f"{salida['raw_gain']:,} y lo mas largo que hemos "
                f"medido en su tramo rindio {techo:,}"
            )


def test_el_recorte_muerde_en_el_techo_del_tramo() -> None:
    """
    EL MECANISMO, QUE ES LO QUE PUEDE VIGILAR UNA VERJA

        Antes aqui se comprobaba que los tres del informe rendian
        menos del 3 % una vez recortados. Eso era cierto con los
        datos de produccion del 15/09 y dejaba de serlo con
        cualquier otro almacen: no es una propiedad del codigo,
        es una medicion del mercado, y por eso tiro produccion.

        Lo que si es del codigo: cuando la rampa bruta supera el
        techo del tramo medido, el recorte la deja EXACTAMENTE en
        ese techo. Ni mas, ni a ojo.
    """

    with almacen_de_mentira():

        calibrado = calibration_for(DEFAULT_HORIZON_DAYS)

        mordio = 0

        for nombre, precio, tasa, racha in FUERA_DE_MUESTRA:

            salida = hold_value(
                precio, tasa, trend_days=racha, sources=3
            )

            if not salida.get("clamped"):
                continue

            tramo = calibrado["by_rate_bucket"].get(
                rate_bucket_of(tasa)
            )

            techo = int(precio * float(tramo["median"]))

            assert salida["raw_gain"] == techo, (
                f"{nombre}: recortado a {salida['raw_gain']:,} y "
                f"el techo de su tramo es {techo:,}"
            )

            assert salida["raw_gain"] < salida["gain_before_clamp"]

            mordio += 1

        assert mordio, (
            "con este fixture ninguno de los tres queda "
            "recortado: el caso que la guardia vigila ha dejado "
            "de estar cubierto"
        )


def test_dentro_de_muestra_no_se_recorta_nada() -> None:
    """
    El recorte solo muerde fuera del rango. Si mordiera dentro,
    estariamos castigando lo que si sabemos medir.
    """

    with almacen_de_mentira():

        salida = hold_value(
            1_000_000, 2.0, trend_days=1, sources=3
        )

        assert salida["in_sample"] is True
        assert salida["clamped"] is False
        assert salida["raw_gain"] == salida["gain_before_clamp"]


def test_el_recorte_solo_resta() -> None:
    """
    Nunca puede subir un valor. Si algun dia lo sube, es que se
    ha convertido en otra cosa.
    """

    with almacen_de_mentira():

        for precio, tasa, racha in (
            (4_240_000, 1.666, 50),
            (3_670_000, 1.098, 19),
            (420_000, 4.849, 4),
            (1_000_000, 0.5, 30),
        ):
            salida = hold_value(
                precio, tasa, trend_days=racha, sources=3
            )

            if not salida["value"]:
                continue

            assert (
                salida["raw_gain"] <= salida["gain_before_clamp"]
            ), (
                f"el recorte ha SUBIDO la ganancia de "
                f"{salida['gain_before_clamp']:,} a "
                f"{salida['raw_gain']:,}"
            )


def test_sin_retrotest_no_se_recorta_pero_se_dice() -> None:
    """
    Degradar, nunca romper. Y que se note que no se comprobo.
    """

    reset_calibration_cache()

    try:
        salida = hold_value(
            4_240_000,
            1.666,
            trend_days=50,
            sources=3,
            calibration_override={
                "available": False,
                "by_rate_bucket": {},
                "reason": "sin almacen",
            },
        )

        assert salida["value"] > 0
        assert salida["clamped"] is False
        assert "no se recorta" in (salida["sample_note"] or "")

    finally:
        reset_calibration_cache()


def test_la_calibracion_se_calcula_una_sola_vez() -> None:
    """
    Recorrer miles de operaciones por cada jugador del tablero
    seria absurdo. Se cachea, y se puede vaciar.
    """

    with almacen_de_mentira():

        primera = calibration_for(DEFAULT_HORIZON_DAYS)
        segunda = calibration_for(DEFAULT_HORIZON_DAYS)

        assert primera is segunda


def test_el_fixture_deja_la_cache_como_estaba() -> None:
    """
    Una guardia que sale dejando la calibracion del fixture en la
    cache envenena a la siguiente, y el rojo aparece en un
    fichero que no tiene la culpa.

    Ese es el mismo genero de fallo que se esta arreglando esta
    noche: estado compartido que decide el veredicto.
    """

    with almacen_de_mentira():
        dentro = calibration_for(DEFAULT_HORIZON_DAYS)

    fuera = calibration_for(DEFAULT_HORIZON_DAYS)

    assert fuera is not dentro, (
        "la calibracion del fixture ha sobrevivido al contexto: "
        "la siguiente guardia la heredaria"
    )

    reset_calibration_cache()


TESTS = [
    test_la_racha_maxima_medida_a_tres_dias_es_dos,
    test_el_rango_de_validez_viaja_con_el_valor,
    test_una_racha_fuera_de_muestra_no_vale_mas_que_la_ultima_medida,
    test_el_recorte_muerde_en_el_techo_del_tramo,
    test_dentro_de_muestra_no_se_recorta_nada,
    test_el_recorte_solo_resta,
    test_sin_retrotest_no_se_recorta_pero_se_dice,
    test_la_calibracion_se_calcula_una_sola_vez,
    test_el_fixture_deja_la_cache_como_estaba,
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

        # Un TypeError tambien es un rojo. Antes salia como
        # traceback suelto y no se sabia ni que guardia era.
        except Exception as exc:                    # noqa: BLE001
            fallos += 1
            print(
                f"ROMPE {test.__name__}: "
                f"{type(exc).__name__}: {exc}"
            )

    print("=" * 60)
    print(f"FUERA DE MUESTRA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
