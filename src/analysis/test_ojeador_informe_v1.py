"""
El informe del ojeador: consenso honesto, TTL, libro de acierto
y ningun motor leyendolo.

QUE PROTEGE

    1. QUE EL CONSENSO NO INVENTE ACUERDOS. Con una fuente, el
       consenso es esa fuente y lo dice. Y el pulso de Comuniate
       no vota: si votase, Comuniate contaria dos veces y ademas
       mezclaria lo que ya paso con lo que la gente hace ahora.

    2. QUE NO SALGA A LA CALLE EN CADA CICLO. El ciclo corre 48
       veces al dia. Sin TTL serian 48 visitas diarias a cada web
       para leer lo mismo, y el camino mas corto a que nos
       bloqueen.

    3. QUE UN FALLO DEL OJEADOR NO TUMBE UN CICLO. Nunca.

    4. QUE EL LIBRO DE ACIERTO NO SE INVENTE UN PORCENTAJE
       mientras no haya vencido ninguna prediccion.

    5. QUE SIGA SIENDO UN OBSERVADOR. Ningun motor lo importa.
"""

from __future__ import annotations

import json
import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.intelligence.scout.accuracy import (
    record_report,
    settle,
    summary,
    sync_scout_accuracy,
)
from src.intelligence.scout.report import (
    DEFAULT_TTL_SECONDS,
    _consensus,
    build_report,
    crossed_reset,
    is_fresh,
    refresh_report,
)


AHORA = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


def _señal(fuente, direccion, pct=1.0, horizonte=1, observada=True):
    return {
        "source": fuente,
        "direction": direccion,
        "magnitude_percent": pct,
        "magnitude_eur": 10_000,
        "horizon_days": horizonte,
        "confidence": None,
        "confidence_basis": "x",
        "quote": "x",
        "observed": observada,
        "seen_at": AHORA.isoformat(),
    }


# ============================================================
# 1. EL CONSENSO NO INVENTA ACUERDOS
# ============================================================


def test_una_sola_fuente_no_es_un_consenso() -> None:
    c = _consensus([_señal("FUTBOLFANTASY", "UP")])

    assert c["agreement"] == "SINGLE"
    assert c["sources_total"] == 1
    assert "no es un consenso" in c["note"], (
        "decir 'consenso: UP' con una sola fuente es inventarse un "
        "acuerdo"
    )


def test_tres_de_acuerdo_son_tres_de_acuerdo() -> None:
    c = _consensus([
        _señal("FUTBOLFANTASY", "UP", 4.0),
        _señal("ANALITICA", "UP", 3.0),
        _señal("COMUNIATE", "UP", 2.0),
    ])

    assert c["agreement"] == "UNANIMOUS"
    assert c["sources_agreeing"] == 3
    assert c["mean_magnitude_percent"] == 3.0


def test_cuando_no_hay_acuerdo_se_dice() -> None:
    c = _consensus([
        _señal("FUTBOLFANTASY", "UP"),
        _señal("ANALITICA", "DOWN"),
    ])

    assert c["agreement"] == "SPLIT"
    assert "No hay acuerdo" in c["note"]


def test_una_fuente_no_vota_tres_veces_por_tener_tres_horizontes() -> None:
    """
    FutbolFantasy manda señales a 1, 3 y 7 dias. Son un voto, no
    tres: si contaran tres, FF decidiria el consenso ella sola.
    """

    c = _consensus([
        _señal("FUTBOLFANTASY", "UP", horizonte=1),
        _señal("FUTBOLFANTASY", "UP", horizonte=3),
        _señal("FUTBOLFANTASY", "UP", horizonte=7),
        _señal("ANALITICA", "DOWN", horizonte=1),
    ])

    assert c["sources_total"] == 2, (
        f"contó {c['sources_total']} fuentes teniendo dos"
    )
    assert c["agreement"] == "SPLIT"


def test_se_queda_el_horizonte_mas_corto() -> None:
    c = _consensus([
        _señal("FUTBOLFANTASY", "DOWN", 9.0, horizonte=7),
        _señal("FUTBOLFANTASY", "UP", 1.0, horizonte=1),
    ])

    assert c["direction"] == "UP", (
        "el proximo mercado lo describe el horizonte corto"
    )


def test_el_pulso_no_vota() -> None:
    """
    Si votase, Comuniate contaria dos veces y ademas mezclaria un
    hecho con una expectativa.
    """

    c = _consensus([
        _señal("COMUNIATE", "DOWN"),
        _señal("COMUNIATE_PULSO", "UP", observada=False),
    ])

    assert c["sources_total"] == 1
    assert c["direction"] == "DOWN"


def test_sin_señales_no_hay_direccion() -> None:
    c = _consensus([])

    assert c["direction"] is None
    assert c["agreement"] == "NONE"


# ============================================================
# 2. NO SALE A LA CALLE EN CADA CICLO
# ============================================================


def _informe(generado: datetime, jugadores=1) -> dict:
    return {
        "version": "V1.0",
        "generated_at": generado.isoformat(),
        "players": {
            str(i): {"player_name": f"J{i}", "signals": []}
            for i in range(jugadores)
        },
    }


def test_el_ttl_por_defecto_son_seis_horas() -> None:
    assert DEFAULT_TTL_SECONDS == 6 * 3600


def test_un_informe_reciente_no_se_vuelve_a_bajar() -> None:
    fresco = _informe(AHORA - timedelta(hours=2))

    assert is_fresh(fresco, now=AHORA) is True


def test_un_informe_viejo_si() -> None:
    viejo = _informe(AHORA - timedelta(hours=8))

    assert is_fresh(viejo, now=AHORA) is False


def test_un_informe_de_antes_del_reset_no_vale_aunque_sea_reciente() -> None:
    """
    Un informe de las 06:50 habla del mercado de AYER aunque solo
    tenga veinte minutos: a las 07:00 el Computer resetea y los
    precios se mueven.
    """

    manana = datetime(2026, 9, 6, 6, 0, tzinfo=timezone.utc)   # 08:00 Madrid

    antes_del_reset = _informe(
        datetime(2026, 9, 6, 4, 50, tzinfo=timezone.utc)       # 06:50 Madrid
    )

    assert crossed_reset(antes_del_reset, now=manana) is True
    assert is_fresh(antes_del_reset, now=manana) is False, (
        "veinte minutos de edad y aun asi habla de otro mercado"
    )


def test_un_informe_vacio_nunca_esta_fresco() -> None:
    assert is_fresh({"generated_at": AHORA.isoformat()}, now=AHORA) is False
    assert is_fresh(None, now=AHORA) is False


def test_si_esta_fresco_no_se_toca_la_red() -> None:
    """La prueba de verdad: con informe fresco, cero peticiones."""

    class SesionQueGrita:
        def get(self, *args, **kwargs):
            raise AssertionError("ha salido a la red teniendo informe fresco")

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "informe.json"
        ruta.write_text(
            json.dumps(_informe(AHORA - timedelta(hours=1))),
            encoding="utf-8",
        )

        r = refresh_report(
            {},
            path=ruta,
            session=SesionQueGrita(),
            now=AHORA,
        )

        assert r["cache"]["status"] == "HIT"


def test_si_no_trae_nada_no_se_pisa_lo_que_habia() -> None:
    """
    Un informe vacio recien escrito es peor que uno de hace seis
    horas, porque parece dato.
    """

    class SesionCaida:
        def get(self, *args, **kwargs):
            raise OSError("sin red")

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "informe.json"
        bueno = _informe(AHORA - timedelta(hours=20), jugadores=5)
        ruta.write_text(json.dumps(bueno), encoding="utf-8")

        r = refresh_report(
            {},
            path=ruta,
            session=SesionCaida(),
            now=AHORA,
        )

        assert r["cache"]["status"] == "STALE_FALLBACK"
        assert len(r["players"]) == 5, "se conserva lo ultimo bueno"
        assert r["cache"]["error"]


def test_el_ojeador_nunca_lanza() -> None:
    """Un fallo del ojeador jamas puede detener un ciclo."""

    class SesionCaida:
        def get(self, *args, **kwargs):
            raise OSError("sin red")

    with tempfile.TemporaryDirectory() as carpeta:

        r = refresh_report(
            None,
            path=Path(carpeta) / "no-existe.json",
            session=SesionCaida(),
            now=AHORA,
        )

        assert isinstance(r, dict)
        assert "players" in r


def test_una_fuente_caida_no_se_lleva_a_las_demas() -> None:
    informe = build_report(
        {
            "data": {
                "players": {
                    "1": {"id": 1, "name": "Lamine Yamal",
                          "price": 21_170_000, "teamID": 1}
                }
            }
        },
        html_by_source={
            "FUTBOLFANTASY": (
                '<tr data-nombre="lamine yamal" data-valor="21170000" '
                'data-tendencia="2" data-diferencia1="50000" '
                'data-diferencia-pct1="0.23"></tr>'
            ),
            "ANALITICA": "<html>roto</html>",
            "COMUNIATE": "<html>roto</html>",
        },
    )

    assert informe["sources"]["FUTBOLFANTASY"]["ok"] is True
    assert informe["sources"]["ANALITICA"]["ok"] is False
    assert informe["players_count"] == 1, (
        "una fuente caida no puede llevarse por delante a la que si "
        "contesto"
    )


def test_el_informe_se_declara_observador_y_dice_lo_que_no_es() -> None:
    informe = build_report({}, html_by_source={})

    assert informe["observer_only"] is True
    assert "no pronostico" in informe["caveat"].lower(), (
        "el informe tiene que decir en su cabecera que es "
        "movimiento observado, o dentro de un mes alguien lo leera "
        "como una prediccion de la casa"
    )


# ============================================================
# 3. EL LIBRO DE ACIERTO
# ============================================================


def _informe_con_señal(precio=1_000_000) -> dict:
    return {
        "players": {
            "1": {
                "player_name": "Fulano",
                "market_price": precio,
                "signals": [
                    _señal("FUTBOLFANTASY", "UP", 5.0),
                    _señal("ANALITICA", "DOWN", -3.0),
                ],
            }
        }
    }


def test_se_apunta_el_precio_de_partida() -> None:
    """Sin el precio de cuando se dijo, no hay contra que puntuar."""

    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe_con_señal(),
            path=Path(carpeta) / "l.json",
        )

        entradas = list(libro["predictions"].values())

        assert len(entradas) == 2
        assert all(e["price_at_prediction"] == 1_000_000 for e in entradas)
        assert all(e["outcome"] == "PENDING" for e in entradas)


def test_se_puntua_contra_el_precio_real() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(_informe_con_señal(), path=ruta)

        # Subio de verdad: acierta FF, falla Analitica.
        libro = settle(
            {"1": 1_100_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=5),
        )

        por_fuente = {
            e["source"]: e for e in libro["predictions"].values()
        }

        assert por_fuente["FUTBOLFANTASY"]["outcome"] == "HIT"
        assert por_fuente["ANALITICA"]["outcome"] == "MISS"
        assert por_fuente["FUTBOLFANTASY"]["actual_percent"] == 10.0


def test_un_flat_no_puntua_ni_a_favor_ni_en_contra() -> None:
    """
    La mayoria de los jugadores no se mueve la mayoria de los
    dias. Contar eso como acierto premiaria a la fuente mas
    prudente hasta hacerla parecer la mejor.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(_informe_con_señal(), path=ruta)
        libro = settle(
            {"1": 1_000_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=5),
        )

        r = summary(libro)

        for datos in r["sources"].values():
            assert datos["flat"] == 1
            assert datos["decided"] == 0
            assert datos["hit_rate"] is None, (
                "un empate no puede contar como acierto"
            )


def test_sin_nada_vencido_no_se_inventa_un_porcentaje() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe_con_señal(),
            path=Path(carpeta) / "l.json",
        )

        r = summary(libro)

        assert r["available"] is False
        assert r["reason"], "y se dice por que"

        for datos in r["sources"].values():
            assert datos["hit_rate"] is None, (
                "un 0 % se leeria como 'falla siempre' cuando lo que "
                "pasa es que todavia no ha jugado"
            )


def test_la_misma_prediccion_no_se_apunta_dos_veces_el_mismo_dia() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(_informe_con_señal(), path=ruta)
        libro = record_report(
            _informe_con_señal(precio=9_999_999),
            ledger=libro,
            path=ruta,
        )

        assert len(libro["predictions"]) == 2, (
            "el precio de partida es el de cuando se dijo, no el de "
            "la ultima vez que se miro"
        )
        assert all(
            e["price_at_prediction"] == 1_000_000
            for e in libro["predictions"].values()
        )


def test_el_libro_mide_la_calibracion_de_la_confianza() -> None:
    """
    Solo FF trae confianza, y derivada por nosotros. Hay que
    poder comprobar si sirve: cuando dice 0,9 ¿acierta mas que
    cuando dice 0,5?
    """

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        informe = {
            "players": {
                str(i): {
                    "player_name": f"J{i}",
                    "market_price": 1_000_000,
                    "signals": [
                        {
                            **_señal("FUTBOLFANTASY", "UP"),
                            "confidence": 0.9 if i < 2 else 0.5,
                            "horizon_days": i + 1,
                        }
                    ],
                }
                for i in range(4)
            }
        }

        libro = record_report(informe, path=ruta)

        # Los de confianza alta aciertan, los de baja fallan.
        libro = settle(
            {"0": 1_100_000, "1": 1_100_000,
             "2": 900_000, "3": 900_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=10),
        )

        cal = summary(libro)["sources"]["FUTBOLFANTASY"]["calibration"]

        assert cal["high_confidence_hit_rate"] == 1.0
        assert cal["low_confidence_hit_rate"] == 0.0
        assert cal["separates"] is True


def test_el_enganche_del_libro_nunca_lanza() -> None:
    for basura in (None, {}, {"players": None}, {"players": "no"}):
        r = sync_scout_accuracy(basura, None)
        assert isinstance(r, dict)
        assert "available" in r


# ============================================================
# 4. QUE SIGA SIN MANDAR
# ============================================================


MOTORES = [
    "src/analysis/acquisition_valuation.py",
    "src/analysis/acquisition_board.py",
    "src/analysis/speculation_engine.py",
    "src/analysis/rival_bid_model.py",
    "src/analysis/acquisition_budget.py",
    "src/analysis/decision_orchestrator.py",
    "src/analysis/lineup_engine.py",
    "src/analysis/offer_decision_engine.py",
    "src/analysis/sales_analyzer.py",
    "src/analysis/player_value_engine.py",
    "src/v10_full_autonomous_live.py",
]


def test_ningun_motor_lee_el_ojeador() -> None:
    """
    En cuanto un motor importe esto, el ojeador deja de ser un
    termometro y pasa a decidir cuanto se paga por un jugador.
    Esa decision se toma con el dueño delante.
    """

    culpables = [
        ruta
        for ruta in MOTORES
        if Path(ruta).exists()
        and "scout" in Path(ruta).read_text(encoding="utf-8")
    ]

    assert not culpables, (
        f"el ojeador ha entrado en una ruta de decision: {culpables}"
    )


def test_el_ciclo_lo_llama_pero_blindado() -> None:
    fuente = Path("src/autopilot.py").read_text(encoding="utf-8")

    assert "sync_scout(" in fuente, (
        "el ciclo ha dejado de llamar al ojeador: el informe no se "
        "refrescaria nunca"
    )

    trozo = fuente[fuente.index("def sync_scout("):]
    trozo = trozo[: trozo.index("\ndef ")]

    assert "try:" in trozo and "except Exception" in trozo, (
        "el ojeador tiene que estar blindado: un fallo suyo jamas "
        "puede detener un ciclo"
    )


def test_la_telemetria_lee_del_disco_y_no_raspa() -> None:
    """
    El dashboard se regenera mucho mas a menudo que el ciclo. Si
    raspara, serian cientos de visitas al dia a cada web.
    """

    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    assert "load_report" in fuente, (
        "la telemetria tiene que LEER el informe"
    )
    assert "refresh_report" not in fuente, (
        "la telemetria ha empezado a salir a la calle"
    )
    assert '"scout": scout' in fuente, (
        "el bloque del ojeador no llega a status.json"
    )


TESTS = [
    test_una_sola_fuente_no_es_un_consenso,
    test_tres_de_acuerdo_son_tres_de_acuerdo,
    test_cuando_no_hay_acuerdo_se_dice,
    test_una_fuente_no_vota_tres_veces_por_tener_tres_horizontes,
    test_se_queda_el_horizonte_mas_corto,
    test_el_pulso_no_vota,
    test_sin_señales_no_hay_direccion,
    test_el_ttl_por_defecto_son_seis_horas,
    test_un_informe_reciente_no_se_vuelve_a_bajar,
    test_un_informe_viejo_si,
    test_un_informe_de_antes_del_reset_no_vale_aunque_sea_reciente,
    test_un_informe_vacio_nunca_esta_fresco,
    test_si_esta_fresco_no_se_toca_la_red,
    test_si_no_trae_nada_no_se_pisa_lo_que_habia,
    test_el_ojeador_nunca_lanza,
    test_una_fuente_caida_no_se_lleva_a_las_demas,
    test_el_informe_se_declara_observador_y_dice_lo_que_no_es,
    test_se_apunta_el_precio_de_partida,
    test_se_puntua_contra_el_precio_real,
    test_un_flat_no_puntua_ni_a_favor_ni_en_contra,
    test_sin_nada_vencido_no_se_inventa_un_porcentaje,
    test_la_misma_prediccion_no_se_apunta_dos_veces_el_mismo_dia,
    test_el_libro_mide_la_calibracion_de_la_confianza,
    test_el_enganche_del_libro_nunca_lanza,
    test_ningun_motor_lee_el_ojeador,
    test_el_ciclo_lo_llama_pero_blindado,
    test_la_telemetria_lee_del_disco_y_no_raspa,
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
    print(f"OJEADOR INFORME V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
