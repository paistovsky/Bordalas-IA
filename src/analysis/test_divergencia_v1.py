"""
El libro de la divergencia: sin control no hay resultado.

DE QUE VA

    El 06/09 salio que las tres fuentes de precio no son tres
    opiniones: son dos medidas y una repetida. Pero en 16
    jugadores el precio y el PULSO DE DEMANDA apuntaban a lados
    contrarios, y eso si es informacion nueva.

    La hipotesis -que la divergencia anticipe algo- NO ESTA
    COMPROBADA, y no se puede comprobar con lo que hay: las
    fuentes publican la demanda de hoy, no una serie. Este libro
    empieza a guardarla.

QUE PROTEGE ESTA GUARDIA

    1. QUE HAYA GRUPO DE CONTROL. Que un divergente suba no dice
       nada si ese dia subieron todos. Si el libro solo apuntase
       divergentes, dentro de un mes habria una coleccion de
       anecdotas con decorado de estadistica.

    2. QUE NO SE CONCLUYA SIN MUESTRA. "Todavia no hay muestra"
       es un resultado valido; un numero endeble presentado como
       hallazgo, no.

    3. QUE NO SE LLAME PREDICCION A UNA HIPOTESIS. Ni en el
       codigo ni en la pantalla.

    4. QUE SE GUARDE LA RACHA. El estudio del 07/09 midio que el
       precio de Biwenger tiene un momento enorme: el 83,8 % de
       los jugadores no cambia de direccion ni una vez en seis
       dias. Asi que una divergencia es una apuesta a que una
       rampa se gira, y sin saber cuantos dias lleva esa rampa el
       libro no podra contestar a nada.

    5. QUE UN FALLO NO TUMBE UN CICLO.
"""

from __future__ import annotations

import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.intelligence.scout.divergence import (
    HORIZONS_DAYS,
    MIN_DEMAND_NET,
    MIN_PRICE_MOVE_PERCENT,
    classify,
    record_report,
    settle,
    study,
    sync_divergence,
)


AHORA = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)


def _ficha(nombre, pct, demanda=None, racha=None, precio=1_000_000):
    """Una ficha del informe del ojeador."""

    return {
        "player_name": nombre,
        "market_price": precio,
        "trend_days": racha,
        "consensus": {
            "direction": "UP" if pct > 0 else "DOWN" if pct < 0 else "FLAT",
            "mean_magnitude_percent": abs(pct),
            "mean_magnitude_eur": int(precio * abs(pct) / 100),
            "agreement": "UNANIMOUS",
        },
        "demand": (
            {"direction": "UP" if demanda > 0 else "DOWN",
             "pressure_points": demanda}
            if demanda is not None
            else None
        ),
    }


def _informe(fichas) -> dict:
    return {"players": {str(i): f for i, f in enumerate(fichas)}}


# ============================================================
# 1. QUE ES Y QUE NO ES UNA DIVERGENCIA
# ============================================================


def test_precio_baja_y_demanda_sube() -> None:
    divergente, tipo = classify(-6.2, 70.0)

    assert divergente is True
    assert tipo == "PRECIO_BAJA_DEMANDA_SUBE"


def test_precio_sube_y_demanda_baja() -> None:
    divergente, tipo = classify(2.4, -51.0)

    assert divergente is True
    assert tipo == "PRECIO_SUBE_DEMANDA_BAJA"


def test_si_van_del_mismo_lado_no_hay_divergencia() -> None:
    assert classify(3.0, 60.0)[0] is False
    assert classify(-3.0, -60.0)[0] is False


def test_un_precio_quieto_no_diverge_de_nada() -> None:
    """Estar parado no es ir en contra: es estar parado."""

    assert classify(0.0, 70.0)[0] is False
    assert classify(MIN_PRICE_MOVE_PERCENT / 2, 70.0)[0] is False


def test_una_demanda_floja_no_es_una_señal() -> None:
    """
    Por debajo del corte casi todos estan en el mismo monton, y
    una señal que le toca a todos no distingue a nadie.
    """

    assert classify(-5.0, MIN_DEMAND_NET - 1)[0] is False
    assert classify(-5.0, MIN_DEMAND_NET + 1)[0] is True


def test_sin_demanda_medida_no_se_supone_nada() -> None:
    assert classify(-5.0, None)[0] is False
    assert classify(None, 70.0)[0] is False


# ============================================================
# 2. EL GRUPO DE CONTROL, QUE ES LO QUE HACE QUE ESTO VALGA
# ============================================================


def test_se_apuntan_los_divergentes_y_TAMBIEN_el_resto() -> None:
    """
    LA GUARDIA QUE MAS IMPORTA.

    Si el libro solo guardase divergentes, dentro de un mes
    tendriamos "los divergentes subieron un 4 %" sin nada con que
    compararlo. Que un divergente suba no dice nada si ese dia
    subieron todos.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe([
                _ficha("Divergente", -6.0, 70.0),
                _ficha("Normal", 3.0, 50.0),
                _ficha("Sin demanda", 2.0, None),
            ]),
            path=Path(carpeta) / "l.json",
            now=AHORA,
        )

        filas = list(libro["observations"].values())

        assert len(filas) == 3, (
            "el grupo de control no es un extra: sin el no hay "
            "resultado"
        )

        divergentes = [f for f in filas if f["divergent"]]

        assert len(divergentes) == 1
        assert divergentes[0]["player_name"] == "Divergente"


def test_la_direccion_del_precio_lleva_su_signo() -> None:
    """
    El ojeador publica la magnitud siempre positiva y la
    direccion aparte. Si aqui se copiara la magnitud a pelo, una
    bajada entraria como subida y la divergencia saldria al reves.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe([_ficha("Baja", -6.0, 70.0)]),
            path=Path(carpeta) / "l.json",
            now=AHORA,
        )

        fila = list(libro["observations"].values())[0]

        assert fila["price_change_percent"] == -6.0
        assert fila["divergence_kind"] == "PRECIO_BAJA_DEMANDA_SUBE"


def test_se_guarda_la_racha() -> None:
    """
    El estudio del 07/09: el 83,8 % de los jugadores no cambia de
    direccion en seis dias. Una divergencia es una apuesta a que
    una rampa se gira, y sin saber cuantos dias lleva esa rampa
    no se podra medir nunca si la demanda avisa del giro.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe([_ficha("Con racha", -2.0, 60.0, racha=-3)]),
            path=Path(carpeta) / "l.json",
            now=AHORA,
        )

        assert list(libro["observations"].values())[0]["trend_days"] == -3


def test_se_dice_de_donde_sale_la_demanda() -> None:
    """
    Solo la publica Comuniate. Es UNA MEDIDA, no un consenso, y
    cada fila tiene que decirlo o dentro de un mes parecera que
    lo dicen tres fuentes.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        libro = record_report(
            _informe([_ficha("X", -6.0, 70.0)]),
            path=Path(carpeta) / "l.json",
            now=AHORA,
        )

        fila = list(libro["observations"].values())[0]

        assert "COMUNIATE" in fila["demand_source"]


def test_un_jugador_no_se_apunta_dos_veces_el_mismo_dia() -> None:
    """El ojeador puede refrescar varias veces: sigue siendo un dia."""

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(
            _informe([_ficha("X", -6.0, 70.0)]), path=ruta, now=AHORA
        )
        libro = record_report(
            _informe([_ficha("X", -9.9, 70.0)]),
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(hours=3),
        )

        assert len(libro["observations"]) == 1
        assert list(libro["observations"].values())[0][
            "price_change_percent"
        ] == -6.0, "vale la primera foto del dia, no la ultima"


# ============================================================
# 3. EL CIERRE POR HORIZONTE
# ============================================================


def test_se_cierra_a_los_tres_y_a_los_siete_dias() -> None:
    assert HORIZONS_DAYS == (3, 7)

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(
            _informe([_ficha("X", -6.0, 70.0, precio=1_000_000)]),
            path=ruta,
            now=AHORA,
        )

        # A los 4 dias: se cierra el de 3, no el de 7.
        libro = settle(
            {"0": 1_100_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=4),
        )

        fila = list(libro["observations"].values())[0]

        assert fila["price_after_3d"] == 1_100_000
        assert fila["return_3d_percent"] == 10.0
        assert fila["price_after_7d"] is None
        assert fila["outcome"] == "PENDING"

        # A los 8, se cierra del todo.
        libro = settle(
            {"0": 1_200_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=8),
        )

        fila = list(libro["observations"].values())[0]

        assert fila["price_after_7d"] == 1_200_000
        assert fila["outcome"] == "CLOSED"
        assert fila["resolved_at"]


def test_antes_de_tiempo_no_se_cierra_nada() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(
            _informe([_ficha("X", -6.0, 70.0)]), path=ruta, now=AHORA
        )
        libro = settle(
            {"0": 1_100_000},
            ledger=libro,
            path=ruta,
            now=AHORA + timedelta(days=1),
        )

        fila = list(libro["observations"].values())[0]

        assert fila["price_after_3d"] is None
        assert fila["outcome"] == "PENDING"


def test_sin_precio_no_se_inventa_un_resultado() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(
            _informe([_ficha("X", -6.0, 70.0)]), path=ruta, now=AHORA
        )
        libro = settle(
            {}, ledger=libro, path=ruta, now=AHORA + timedelta(days=8)
        )

        fila = list(libro["observations"].values())[0]

        assert fila["return_7d_percent"] is None
        assert fila["outcome"] == "PENDING", (
            "sin el precio real no hay nada que apuntar"
        )


# ============================================================
# 4. EL ESTUDIO NO CONCLUYE SIN MUESTRA
# ============================================================


def _libro_con(n_divergentes, n_control, ret_div, ret_ctrl, carpeta):
    """Un libro ya cerrado, con los dos grupos."""

    ruta = Path(carpeta) / "l.json"

    fichas = (
        [_ficha(f"D{i}", -6.0, 70.0) for i in range(n_divergentes)]
        + [_ficha(f"C{i}", 3.0, 5.0) for i in range(n_control)]
    )

    libro = record_report(_informe(fichas), path=ruta, now=AHORA)

    precios = {}

    for clave, fila in libro["observations"].items():
        subida = ret_div if fila["divergent"] else ret_ctrl
        precios[fila["player_id"]] = int(
            fila["price"] * (1 + subida / 100.0)
        )

    return settle(
        precios,
        ledger=libro,
        path=ruta,
        now=AHORA + timedelta(days=8),
    )


def test_sin_muestra_se_dice_que_no_hay_muestra() -> None:
    """
    "Todavia no hay muestra" es un resultado valido y mucho mas
    util que un numero endeble.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        libro = _libro_con(3, 5, 8.0, 1.0, carpeta)

        r = study(libro)

        for horizonte in r["horizons"].values():
            assert horizonte["enough_sample"] is False
            assert "no hay muestra" in horizonte["reason"]

        assert r["hypothesis_confirmed"] is None


def test_con_muestra_se_compara_contra_el_control() -> None:
    with tempfile.TemporaryDirectory() as carpeta:

        libro = _libro_con(25, 30, 8.0, 1.0, carpeta)

        r = study(libro)

        tres = r["horizons"]["3d"]

        assert tres["enough_sample"] is True
        assert tres["divergent_n"] == 25
        assert tres["control_n"] == 30
        assert tres["divergent_mean_return_percent"] == 8.0
        assert tres["control_mean_return_percent"] == 1.0
        assert tres["difference_percent"] == 7.0, (
            "la diferencia contra el control es TODO el resultado"
        )


def test_un_dia_sin_divergentes_no_rompe_nada() -> None:
    """
    Puede pasar perfectamente, y ese dia el libro sigue
    apuntando el grupo de control.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "l.json"

        libro = record_report(
            _informe([
                _ficha("A", 3.0, 50.0),
                _ficha("B", 2.0, None),
            ]),
            path=ruta,
            now=AHORA,
        )

        assert len(libro["observations"]) == 2
        assert not any(
            f["divergent"] for f in libro["observations"].values()
        )

        r = study(libro)

        assert r["available"] is True
        assert r["divergent_total"] == 0

        for horizonte in r["horizons"].values():
            assert horizonte["enough_sample"] is False


def test_el_libro_vacio_lo_dice() -> None:
    r = study({"observations": {}})

    assert r["available"] is False
    assert r["reason"]


def test_nunca_se_llama_prediccion() -> None:
    """
    Vocabulario. Nada puede llamarse prediccion hasta que el
    libro diga que acierta.
    """

    with tempfile.TemporaryDirectory() as carpeta:

        r = study(_libro_con(25, 30, 8.0, 1.0, carpeta))

        assert "SIN COMPROBAR" in r["caveat"]
        assert "Hipotesis" in r["caveat"]

    fuente = Path(
        "src/intelligence/scout/divergence.py"
    ).read_text(encoding="utf-8")

    for palabra in ("prediccion de", "predice que", "predicted"):
        assert palabra not in fuente.lower(), (
            f"el modulo usa la palabra «{palabra}» sobre una "
            f"hipotesis sin medir"
        )


def test_el_enganche_nunca_lanza() -> None:
    for basura in (None, {}, {"players": None}, {"players": "no"}):
        r = sync_divergence(basura, None)
        assert isinstance(r, dict)
        assert "available" in r


MOTORES = [
    "src/analysis/acquisition_valuation.py",
    "src/analysis/speculation_engine.py",
    "src/analysis/rival_bid_model.py",
    "src/analysis/acquisition_budget.py",
    "src/analysis/decision_orchestrator.py",
    "src/analysis/player_value_engine.py",
    "src/v10_full_autonomous_live.py",
]


def test_ningun_motor_lee_la_divergencia() -> None:
    culpables = [
        ruta
        for ruta in MOTORES
        if Path(ruta).exists()
        and "divergence" in Path(ruta).read_text(encoding="utf-8")
    ]

    assert not culpables, (
        f"una hipotesis sin comprobar ha entrado en una ruta de "
        f"decision: {culpables}"
    )


TESTS = [
    test_precio_baja_y_demanda_sube,
    test_precio_sube_y_demanda_baja,
    test_si_van_del_mismo_lado_no_hay_divergencia,
    test_un_precio_quieto_no_diverge_de_nada,
    test_una_demanda_floja_no_es_una_señal,
    test_sin_demanda_medida_no_se_supone_nada,
    test_se_apuntan_los_divergentes_y_TAMBIEN_el_resto,
    test_la_direccion_del_precio_lleva_su_signo,
    test_se_guarda_la_racha,
    test_se_dice_de_donde_sale_la_demanda,
    test_un_jugador_no_se_apunta_dos_veces_el_mismo_dia,
    test_se_cierra_a_los_tres_y_a_los_siete_dias,
    test_antes_de_tiempo_no_se_cierra_nada,
    test_sin_precio_no_se_inventa_un_resultado,
    test_sin_muestra_se_dice_que_no_hay_muestra,
    test_con_muestra_se_compara_contra_el_control,
    test_un_dia_sin_divergentes_no_rompe_nada,
    test_el_libro_vacio_lo_dice,
    test_nunca_se_llama_prediccion,
    test_el_enganche_nunca_lanza,
    test_ningun_motor_lee_la_divergencia,
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
    print(f"DIVERGENCIA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
