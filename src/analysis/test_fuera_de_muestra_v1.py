"""
No se valora por encima de lo que se ha medido.

SINTOMA

    El 14/09 la via TENER se encendio apoyada en una celda del
    retrotest medida con racha de UN dia: `> 1 %/dia`, m=3,
    n=142, mediana +4,47 %, 5 % de operaciones en perdida.

    Y al dia siguiente se aplico a estos tres:

        Roro Riquelme   1,666 %/dia   racha de 50 dias
        Amatucci        1,098 %/dia   racha de 19 dias
        Pedri           0,305 %/dia   racha de  8 dias

    Ninguna de esas rachas existe en el retrotest.

CAUSA

    La ventana del almacen es de seis dias. Una racha de `n` dias
    consume `n` dias por delante y deja `5 - n` por detras, asi
    que AL HORIZONTE DE TRES DIAS la racha maxima medible es DOS.

    El informe del 14/09 ya lo decia —"la racha maxima observable
    en 6 dias es 5"— y aun asi la via valoraba rachas de 50 sin
    pestañear.

CONSECUENCIA

    No es un detalle de precision, porque la direccion esta
    medida y va EN CONTRA:

        tasa > 1 %/dia, m=3, racha 1 dia   +4,47 %    5 % perdida
        tasa > 1 %/dia, m=3, racha 2 dias  +3,09 %   10 % perdida

    Extrapolar a 50 dias desde una curva que llega a 2, en la
    direccion en que el rendimiento cae, es la clase de error que
    este proyecto lleva un mes aprendiendo a no cometer.

    Y el precio de equivocarse aqui no es un decimal: es meter
    medio patrimonio en el jugador equivocado.
"""

from __future__ import annotations

from pathlib import Path

from src.analysis.hold_backtest import backtest, calibration
from src.analysis.hold_value import (
    DEFAULT_HORIZON_DAYS,
    calibration_for,
    hold_value,
    reset_calibration_cache,
)


ALMACEN = Path("data") / "autopilot" / "price_history.json"


# Los tres del informe del 14/09, con sus numeros de produccion.
FUERA_DE_MUESTRA = (
    ("Roro Riquelme", 4_240_000, 1.666, 50),
    ("Amatucci", 3_670_000, 1.098, 19),
    ("Pedri", 15_350_000, 0.305, 8),
)


def _calibrado():
    if not ALMACEN.exists():
        return None

    return calibration_for(DEFAULT_HORIZON_DAYS)


# ============================================================
# 1. EL RANGO MEDIDO ES EL QUE ES
# ============================================================


def test_la_racha_maxima_medida_a_tres_dias_es_dos() -> None:
    """
    Y no cinco, que es lo que dice la tabla mirada por encima.
    Cinco es la racha maxima observada A UN DIA de horizonte.
    """

    calibrado = _calibrado()

    if calibrado is None:
        return

    assert calibrado["available"]

    assert calibrado["max_streak"] <= 5, (
        f"la calibracion dice que llega a rachas de "
        f"{calibrado['max_streak']} dias con una ventana de seis"
    )

    # El tramo de arriba se partio el 16/09 en 1-2 %, 2-4 % y
    # > 4 %. Se mira el primero, que es donde caen Roro (1,666) y
    # Amatucci (1,098).
    tramo = calibrado["by_rate_bucket"].get("1-2 %")

    assert tramo and tramo.get("calibrated")
    assert tramo["max_streak"] == 2, (
        f"el tramo bueno dice estar calibrado hasta rachas de "
        f"{tramo['max_streak']} dias a {DEFAULT_HORIZON_DAYS} de "
        f"horizonte"
    )


def test_el_rango_de_validez_viaja_con_el_valor() -> None:
    """
    "calibrado sobre rachas de 1 a 2 dias; este lleva 50". En el
    objeto, para que la pantalla pueda decirlo.
    """

    salida = hold_value(4_240_000, 1.666, trend_days=50, sources=3)

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

    calibrado = _calibrado()

    if calibrado is None:
        return

    for nombre, precio, tasa, racha in FUERA_DE_MUESTRA:

        salida = hold_value(precio, tasa, trend_days=racha, sources=3)

        if not salida["value"]:
            continue

        assert salida["in_sample"] is False, (
            f"{nombre} lleva {racha} dias de racha y sale como "
            f"dentro de muestra"
        )

        from src.analysis.hold_backtest import rate_bucket_of

        tramo = calibrado["by_rate_bucket"].get(
            rate_bucket_of(tasa)
        )

        if not tramo or not tramo.get("calibrated"):
            continue

        techo = int(precio * float(tramo["median"]))

        assert salida["raw_gain"] <= techo, (
            f"{nombre}: se le reconoce una ganancia de "
            f"{salida['raw_gain']:,} y lo mas largo que hemos "
            f"medido en su tramo rindio {techo:,}"
        )


def test_dentro_de_muestra_no_se_recorta_nada() -> None:
    """
    El recorte solo muerde fuera del rango. Si mordiera dentro,
    estariamos castigando lo que si sabemos medir.
    """

    salida = hold_value(1_000_000, 2.0, trend_days=1, sources=3)

    assert salida["in_sample"] is True
    assert salida["clamped"] is False
    assert salida["raw_gain"] == salida["gain_before_clamp"]


def test_el_recorte_solo_resta() -> None:
    """
    Nunca puede subir un valor. Si algun dia lo sube, es que se
    ha convertido en otra cosa.
    """

    for precio, tasa, racha in (
        (4_240_000, 1.666, 50),
        (3_670_000, 1.098, 19),
        (420_000, 4.849, 4),
        (1_000_000, 0.5, 30),
    ):
        salida = hold_value(precio, tasa, trend_days=racha, sources=3)

        if not salida["value"]:
            continue

        assert salida["raw_gain"] <= salida["gain_before_clamp"], (
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


# ============================================================
# 3. EL EFECTO, MEDIDO
# ============================================================


def test_los_tres_del_informe_dejan_de_compensar() -> None:
    """
    EL RESULTADO QUE DECIDE EL ENCARGO

        Una vez recortados al rango medido, ninguno de los tres
        pasa el liston del 3 %. Si algun dia uno lo pasa, no es
        que este test sobre: es que ha cambiado el retrotest, y
        entonces hay que volver a mirarlo todo.
    """

    calibrado = _calibrado()

    if calibrado is None:
        return

    for nombre, precio, tasa, racha in FUERA_DE_MUESTRA:

        salida = hold_value(precio, tasa, trend_days=racha, sources=3)

        rinde = (
            (salida["value"] - precio) / precio
            if salida["value"]
            else 0.0
        )

        assert rinde < 0.03, (
            f"{nombre} rinde un {rinde * 100:.2f} % una vez "
            f"recortado al rango medido: pasaria el liston del "
            f"3 % con una racha que nunca se ha medido"
        )


def test_la_calibracion_se_calcula_una_sola_vez() -> None:
    """
    Recorrer 5.577 operaciones por cada jugador del tablero seria
    absurdo. Se cachea, y se puede vaciar.
    """

    reset_calibration_cache()

    primera = calibration_for(DEFAULT_HORIZON_DAYS)
    segunda = calibration_for(DEFAULT_HORIZON_DAYS)

    assert primera is segunda


TESTS = [
    test_la_racha_maxima_medida_a_tres_dias_es_dos,
    test_el_rango_de_validez_viaja_con_el_valor,
    test_una_racha_fuera_de_muestra_no_vale_mas_que_la_ultima_medida,
    test_dentro_de_muestra_no_se_recorta_nada,
    test_el_recorte_solo_resta,
    test_sin_retrotest_no_se_recorta_pero_se_dice,
    test_los_tres_del_informe_dejan_de_compensar,
    test_la_calibracion_se_calcula_una_sola_vez,
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
    print(f"FUERA DE MUESTRA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
