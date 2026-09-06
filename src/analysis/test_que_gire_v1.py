"""
LOS TRES TAPONES — ninguno era un umbral.

SINTOMA

    Pepe tiene permiso, dinero y maquina para comerciar y lleva
    semanas sin fichar. La rueda vale entre 718.629 y 1.555.885
    EUR al mes y gira a cero.

CAUSA — TRES SITIOS MIRANDO DONDE NO ERA

    1. El interruptor de la via TENER juzgaba el tramo con la
       banda de racha MAS LARGA con muestra. En el tramo 1-2 %
       eso son 1,80 % -racha de dos dias- cuando la doctrina solo
       compra racha corta, que rinde 3,22 %. El tramo donde cabe
       el 100 % del capital estaba apagado por una compra que
       nunca haríamos.

    2. La prioridad de emergencia se disparaba por el SIGNO del
       saldo, no por el reloj. Un martes en rojo -que la doctrina
       permite- el ciclo se dedicaba a la solvencia y no volvia a
       mirar el mercado.

    3. El motivo del rechazo narraba once, especulacion y
       reventa, y NO TENER: la via que sostiene la rueda decidia
       en silencio.

CONSECUENCIA

    Ningun umbral estaba mal. El 3 % queda confirmado por segunda
    vez, EMERGENCY_SOLVENCY sigue valiendo 1100 y MAX_SAFE_DEBT no
    se ha tocado. Lo que cambia es que miran donde tienen que
    mirar.

    Guardias con fixture. Ni una lectura de `data/` ni de la red.
"""

from __future__ import annotations

from src.analysis.decision_orchestrator import (
    FASES_CON_PRISA,
    LOCK_PHASES,
    PRIORITY,
    calculate_accept_expiry_priority,
)
from src.analysis.hold_switch import (
    MIN_TENER_YIELD,
    RACHA_QUE_SE_COMPRA,
    bucket_backing,
    route_state,
)


# ============================================================
# EL FIXTURE: EL CASO REAL DEL 23/09
# ============================================================
#
# El tramo 1-2 % a horizonte 3, con sus dos bandas medidas.

CALIBRACION = {
    "available": True,
    "horizon": 3,
    "max_streak": 2,
    "by_rate_bucket": {
        "1-2 %": {
            "calibrated": True,
            "band": "2 dias",
            "max_streak": 2,

            # El techo del recorte: la banda mas larga.
            "median": 0.0180,
            "loss_rate": 0.10,
            "n": 58,

            # Y las dos bandas, cada una con lo suyo.
            "bands": {
                "1 dia": {
                    "median": 0.0322,
                    "loss_rate": 0.074,
                    "n": 68,
                },
                "2 dias": {
                    "median": 0.0180,
                    "loss_rate": 0.10,
                    "n": 58,
                },
            },
            "reason": None,
        },
        "0,5-1 %": {
            "calibrated": True,
            "band": "2 dias",
            "max_streak": 2,
            "median": 0.0060,
            "loss_rate": 0.31,
            "n": 55,
            "bands": {
                "1 dia": {
                    "median": 0.0125,
                    "loss_rate": 0.12,
                    "n": 66,
                },
            },
            "reason": None,
        },
    },
}


# ============================================================
# TAPON 1 — LA CELDA QUE MIRA EL INTERRUPTOR
# ============================================================


def test_el_tramo_se_juzga_por_la_racha_que_se_compra() -> None:
    """
    EL CASO EXACTO DEL 23/09

        tramo 1-2 %   bloque (racha 2)   1,80 %  ->  APAGADO
                      racha 1            3,22 %  ->  ENCENDIDO

        Y ese tramo coloca el 100 % del capital: 1.244.755 EUR al
        mes contra los 309.634 del tramo de arriba.
    """

    con_racha = bucket_backing(CALIBRACION, "1-2 %", streak=1)

    assert con_racha["band"] == "1 dia"
    assert abs(con_racha["median"] - 0.0322) < 1e-9
    assert con_racha["backed"] is True, (
        "el tramo 1-2 % sigue apagado a racha corta, que es la "
        "unica que la doctrina compra"
    )

    # Y a racha larga sigue apagado, que es lo correcto.
    larga = bucket_backing(CALIBRACION, "1-2 %", streak=2)

    assert larga["band"] == "2 dias"
    assert larga["backed"] is False


def test_sin_racha_se_comporta_como_antes() -> None:
    """
    Quien no pase la racha no cambia de comportamiento: se sigue
    juzgando con la banda mas larga, que es el techo del recorte.
    """

    sin_racha = bucket_backing(CALIBRACION, "1-2 %")

    assert sin_racha["band"] == "2 dias"
    assert sin_racha["backed"] is False


def test_el_liston_del_tres_por_ciento_no_se_ha_movido() -> None:
    """
    "El 3 % no se toca. Queda confirmado por segunda vez; lo que
     cambia es contra que numero se compara."
    """

    assert MIN_TENER_YIELD == 0.03

    from src.analysis.rival_bid_model import MIN_SPECULATION_YIELD

    assert MIN_TENER_YIELD == MIN_SPECULATION_YIELD


def test_una_banda_sin_muestra_cae_al_bloque() -> None:
    """
    Si la racha del jugador cae en una banda sin medir, se usa la
    del bloque en vez de inventarse una.
    """

    salida = bucket_backing(
        CALIBRACION, "0,5-1 %", streak=2
    )

    # `0,5-1 %` solo tiene medida la banda de 1 dia.
    assert salida["band"] == "2 dias"
    assert abs(salida["median"] - 0.0060) < 1e-9


def test_el_tablero_publica_con_que_celda_juzga() -> None:
    """
    Un tramo encendido sin decir con que racha se ha juzgado es
    un numero sin procedencia.
    """

    estado = route_state(CALIBRACION, horizon_days=3)

    assert estado["available"]

    for tramo in estado["buckets"]:
        assert "band" in tramo
        assert "streak" in tramo

    assert "1-2 %" in estado["backing"], (
        "el tramo donde cabe todo el capital sigue apagado en el "
        "tablero"
    )

    # Y el tablero juzga con la racha que se compra.
    assert RACHA_QUE_SE_COMPRA == 1


# ============================================================
# TAPON 2 — LA EMERGENCIA, POR EL RELOJ Y NO POR EL SIGNO
# ============================================================


def test_el_martes_en_rojo_ya_no_aplasta_al_mercado() -> None:
    """
    LA DOCTRINA, LITERAL

        "Se puede ir en rojo de lunes a jueves. El viernes se
         vende y se vuelve a verde."

    Con una accion por vuelta, escalar a 1110 por el signo del
    saldo dejaba a la rueda parada toda la semana.
    """

    martes = calculate_accept_expiry_priority(-800_000, "NORMAL")

    assert martes == PRIORITY["ACCEPT_EXPIRY_URGENT"]
    assert martes < PRIORITY["EMERGENCY_SOLVENCY"], (
        "un martes en rojo sigue disparando la emergencia"
    )


def test_el_viernes_a_seis_horas_manda_la_solvencia() -> None:
    """
    LA GUARDIA QUE PROTEGE LO UNICO QUE PROTEGE DINERO

        A T-6 h la fase aprieta, y ahi la escalada es la de
        siempre. Si esto se pusiera rojo, la rueda habria comido
        al reloj de solvencia.
    """

    for fase in ("PREPARATION", "HIGH_ATTENTION",
                 "FINALIZATION", "HARD_SAFETY"):

        assert calculate_accept_expiry_priority(
            -800_000, fase
        ) == PRIORITY["EMERGENCY_SOLVENCY"] + 10, (
            f"en {fase} la solvencia ha dejado de mandar"
        )

    assert set(FASES_CON_PRISA) == {
        "PREPARATION", "HIGH_ATTENTION",
        "FINALIZATION", "HARD_SAFETY",
    }


def test_el_numero_de_la_emergencia_no_se_ha_movido() -> None:
    """
    "No bajes EMERGENCY_SOLVENCY. Esa prioridad esta bien puesta
     cuando de verdad hay una emergencia."
    """

    assert PRIORITY["EMERGENCY_SOLVENCY"] == 1100
    assert PRIORITY["SPECULATION_BUY"] == 400
    assert PRIORITY["ACCEPT_EXPIRY_URGENT"] == 680


def test_con_la_jornada_cerrada_no_se_toca_nada() -> None:
    for fase in LOCK_PHASES:
        assert calculate_accept_expiry_priority(
            -800_000, fase
        ) == 0


def test_en_verde_nada_cambia() -> None:
    for fase in ("NORMAL", "HIGH_ATTENTION"):
        assert calculate_accept_expiry_priority(
            500_000, fase
        ) == PRIORITY["ACCEPT_EXPIRY_URGENT"]


# ============================================================
# TAPON 2b — EL PRESUPUESTO EN ROJO
# ============================================================


def _solvencia(guaranteed=True, ventana=True, permitida=True,
               holgura=3_000_000) -> dict:
    return {
        "hard_safety": {},
        "solvency_guarantee": {"guaranteed": guaranteed},
        "max_safe_debt": {
            "debt_window_open": ventana,
            "additional_debt_headroom": holgura,
        },
        "temporary_debt": {"allowed": permitida},
    }


def _snapshot(balance: int) -> dict:
    return {
        "market": {
            "status": {
                "balance": balance,
                "maximumBid": 14_110_383,
            }
        }
    }


def test_en_rojo_con_garantia_si_se_puede_comprar() -> None:
    """
    LO QUE YO DIJE MAL EL 23/09

        Dije que `cash_budget = max(balance, 0)` mataba la compra
        en rojo. La caja si se hace cero, pero **la deuda segura
        toma el relevo**: con garantia y holgura el presupuesto
        sale a 3.000.000 y `enabled` a True.

        Estaba equivocado y esta guardia lo fija para que no se
        vuelva a decir.
    """

    from src.analysis.acquisition_budget import (
        calculate_acquisition_budget,
    )

    rojo = calculate_acquisition_budget(
        _snapshot(-800_000), _solvencia()
    )

    assert rojo["cash_budget"] == 0
    assert rojo["debt_budget"] > 0
    assert rojo["enabled"] is True, (
        "en rojo con garantia y holgura el presupuesto sigue "
        "cerrado: entonces el permiso de endeudarse no sirve"
    )


def test_sin_garantia_la_puerta_se_cierra() -> None:
    """
    Y tiene que cerrarse: la deuda solo vale si se puede
    recuperar antes del plazo.
    """

    from src.analysis.acquisition_budget import (
        calculate_acquisition_budget,
    )

    for solvencia in (
        _solvencia(guaranteed=False),
        _solvencia(ventana=False),
        _solvencia(permitida=False),
        _solvencia(holgura=0),
    ):
        salida = calculate_acquisition_budget(
            _snapshot(-800_000), solvencia
        )

        assert salida["debt_budget"] == 0
        assert salida["enabled"] is False


def test_se_publica_cual_de_las_tres_puertas_esta_cerrada() -> None:
    """
    EL AGUJERO DE VISIBILIDAD

        Que Pepe pueda comprar en rojo depende de tres campos, y
        ninguno se publicaba. Al mirar por que el permiso llevaba
        semanas sin usarse, no habia forma de saber cual fallaba.
    """

    from src.analysis.acquisition_budget import (
        calculate_acquisition_budget,
    )

    salida = calculate_acquisition_budget(
        _snapshot(-800_000), _solvencia(ventana=False)
    )

    for clave in (
        "solvency_guaranteed",
        "debt_window_open",
        "temporary_debt_allowed",
        "safe_debt_headroom",
    ):
        assert clave in salida, f"no se publica `{clave}`"

    assert salida["debt_window_open"] is False
    assert salida["solvency_guaranteed"] is True


# ============================================================
# TAPON 3 — EL MOTIVO QUE NO NOMBRABA A TENER
# ============================================================


def test_el_rechazo_nombra_las_cuatro_vias() -> None:
    """
    Con la regla 17, un rechazo que no cuenta la via que decide
    es un rechazo que miente por omision.
    """

    from pathlib import Path

    fuente = Path(
        "src/analysis/acquisition_valuation.py"
    ).read_text(encoding="utf-8")

    assert "como tenerlo mientras sube" in fuente, (
        "el motivo del rechazo ha vuelto a callarse la via TENER"
    )

    # Y las otras tres siguen.
    for trozo in (
        "como mejora del once",
        "como especulacion",
        "como reventa al Computer",
    ):
        assert trozo in fuente


# ============================================================
# NI SE MUEVE UN UMBRAL NI CAMBIA LA FORMA
# ============================================================


def test_ningun_umbral_se_ha_movido() -> None:
    from src.analysis.hold_switch import MAX_TENER_LOSS_RATE
    from src.analysis.rival_bid_model import (
        MIN_SPECULATION_YIELD,
    )

    assert MIN_SPECULATION_YIELD == 0.03
    assert MAX_TENER_LOSS_RATE == 0.20
    assert PRIORITY["EMERGENCY_SOLVENCY"] == 1100


def test_la_forma_no_cambia_con_los_datos() -> None:
    lleno = bucket_backing(CALIBRACION, "1-2 %", streak=1)
    vacio = bucket_backing(None, "1-2 %")

    assert set(lleno) == set(vacio), (
        f"bucket_backing cambia de forma: "
        f"faltan {sorted(set(lleno) - set(vacio))}, "
        f"sobran {sorted(set(vacio) - set(lleno))}"
    )

    lleno = route_state(CALIBRACION, horizon_days=3)
    vacio = route_state(None)

    assert set(lleno) == set(vacio)


def test_nada_de_esto_lanza() -> None:
    for basura in (None, {}, "x", []):
        assert isinstance(
            bucket_backing(basura, "1-2 %", streak=basura), dict
        )
        assert isinstance(route_state(basura), dict)


def test_estas_guardias_no_leen_el_estado() -> None:
    from src.analysis.test_verja_determinista_v1 import (
        lecturas_de_estado,
    )

    assert not lecturas_de_estado(
        "src.analysis.test_que_gire_v1"
    )


TESTS = [
    test_el_tramo_se_juzga_por_la_racha_que_se_compra,
    test_sin_racha_se_comporta_como_antes,
    test_el_liston_del_tres_por_ciento_no_se_ha_movido,
    test_una_banda_sin_muestra_cae_al_bloque,
    test_el_tablero_publica_con_que_celda_juzga,
    test_el_martes_en_rojo_ya_no_aplasta_al_mercado,
    test_el_viernes_a_seis_horas_manda_la_solvencia,
    test_el_numero_de_la_emergencia_no_se_ha_movido,
    test_con_la_jornada_cerrada_no_se_toca_nada,
    test_en_verde_nada_cambia,
    test_en_rojo_con_garantia_si_se_puede_comprar,
    test_sin_garantia_la_puerta_se_cierra,
    test_se_publica_cual_de_las_tres_puertas_esta_cerrada,
    test_el_rechazo_nombra_las_cuatro_vias,
    test_ningun_umbral_se_ha_movido,
    test_la_forma_no_cambia_con_los_datos,
    test_nada_de_esto_lanza,
    test_estas_guardias_no_leen_el_estado,
]


def main() -> None:

    print()
    print("=" * 60)
    print("QUE GIRE V1")
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
