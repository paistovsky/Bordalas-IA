"""
El reloj del mercado.

QUE PROBLEMA CUBRE
    El 16/08/2026 el mercado del Computer cerro a las 07:00 de
    Madrid y Bordalas IA siguio evaluando fichajes durante horas.
    No es que decidiera mal: es que no tenia forma de saber que la
    ventana estaba cerrada. El unico reloj del sistema era el
    deadline de jornada, que es otra cosa distinta.

QUE SE VERIFICA AQUI
    - Que la hora del reset sale de los datos y no de una
      constante escrita a fuego.
    - Que solo se miran las ventas del Computer. Las de rivales
      tienen `until` individual y contaminarian el calculo.
    - Que un snapshot caducado se detecta y se marca, en vez de
      dejar que Pepe puje por un mercado que ya no existe.
    - Que el reloj no lanza NUNCA. Si revienta, revienta el ciclo.

Ejecutar:
    python -m src.analysis.test_market_clock_v1
"""

from datetime import datetime, timezone

from src.analysis.market_clock import (
    CLOSING_SECONDS,
    CRITICAL_SECONDS,
    build_market_clock,
    computer_reset_epoch,
    is_computer_sale,
    madrid_offset_hours,
)


# Datos reales del snapshot del 16/08/2026.
RESET_REAL = 1786856400          # 16/08 05:00 UTC = 07:00 Madrid
RIVAL = 14175950


def ts(texto: str) -> int:
    return int(
        datetime.fromisoformat(texto)
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def venta_computer(until: int = RESET_REAL, player: int = 1) -> dict:
    return {
        "player": player,
        "price": 7_590_000,
        "until": until,
        "user": None,
    }


def venta_rival(until: int, player: int = 900) -> dict:
    return {
        "player": player,
        "price": 3_000_000,
        "until": until,
        "user": {"id": RIVAL, "name": "Rival"},
    }


def snapshot(ventas: list) -> dict:
    return {"market": {"sales": ventas}}


# ============================================================
# DE DONDE SALE LA HORA
# ============================================================

def test_el_reset_sale_de_los_datos() -> None:
    reset, origen = computer_reset_epoch(
        snapshot([
            venta_computer(player=1),
            venta_computer(player=2),
            venta_computer(player=3),
        ])
    )

    assert reset == RESET_REAL, (
        f"El reset deberia deducirse del `until` del Computer "
        f"({RESET_REAL}), no de una constante. Salio {reset}."
    )
    assert origen == "COMPUTER_LISTINGS"

    print("  OK  el reset se deduce del mercado del Computer")


def test_los_rivales_no_contaminan_el_calculo() -> None:
    """
    El caso real: 20 del Computer y 33 de rivales en el mismo
    bloque. Los rivales tienen `until` individual a 48 h. Si se
    colasen, el reset saldria a cualquier hora.
    """
    reset, _ = computer_reset_epoch(
        snapshot([
            venta_rival(RESET_REAL + 54_490, player=901),
            venta_rival(RESET_REAL + 56_660, player=902),
            venta_computer(player=1),
            venta_computer(player=2),
            venta_rival(RESET_REAL + 59_789, player=903),
        ])
    )

    assert reset == RESET_REAL, (
        f"Las ventas de rivales se colaron en el calculo: salio "
        f"{reset} en vez de {RESET_REAL}."
    )

    print("  OK  las ventas de rivales quedan fuera")


def test_el_computer_se_reconoce_sin_vendedor() -> None:
    assert is_computer_sale({"user": None}) is True
    assert is_computer_sale({}) is True
    assert is_computer_sale({"user": {"id": RIVAL}}) is False

    print("  OK  una venta sin vendedor es del Computer")


def test_sin_mercado_del_computer_hay_respaldo() -> None:
    """
    Sin datos que mirar el reloj no puede quedarse mudo: la
    operativa del dia depende de el.
    """
    reloj = build_market_clock(
        snapshot([venta_rival(RESET_REAL + 50_000)]),
        now_ts=ts("2026-08-16T09:00:00"),
    )

    assert reloj["available"] is True
    assert reloj["source"] == "FALLBACK_DIARIO"
    assert reloj["next_reset_epoch"] > ts("2026-08-16T09:00:00")

    print("  OK  sin mercado del Computer entra el respaldo")


def test_el_respaldo_apunta_al_futuro_no_al_pasado() -> None:
    """
    A las 09:00 el reset de las 05:00 ya paso: toca el de manana.
    """
    ahora = ts("2026-08-16T09:00:00")

    reloj = build_market_clock(snapshot([]), now_ts=ahora)

    assert reloj["seconds_to_reset"] > 0, (
        "El respaldo devolvio un reset en el pasado."
    )
    assert reloj["next_reset_iso"].startswith("2026-08-17T05:00")

    print("  OK  el respaldo salta al dia siguiente")


# ============================================================
# ESTADO DE LA VENTANA
# ============================================================

def test_ventana_abierta_lejos_del_reset() -> None:
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 10 * 3600,
    )

    assert reloj["window_state"] == "OPEN"
    assert reloj["bidding_window_open"] is True
    assert reloj["hours_to_reset"] == 10.0

    print("  OK  a 10 h del reset la ventana esta abierta")


def test_ventana_cerrando_a_dos_horas() -> None:
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 2 * 3600,
    )

    assert reloj["window_state"] == "CLOSING_SOON", (
        f"A 2 h del reset -umbral {CLOSING_SECONDS // 3600} h- el "
        f"estado deberia ser CLOSING_SOON, no "
        f"{reloj['window_state']}."
    )

    print("  OK  a 2 h del reset la ventana esta cerrando")


def test_ventana_critica_en_la_ultima_hora() -> None:
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 900,
    )

    assert reloj["window_state"] == "CRITICAL", (
        f"A 15 min del reset -umbral {CRITICAL_SECONDS // 60} "
        f"min- el estado deberia ser CRITICAL."
    )
    assert reloj["bidding_window_open"] is True, (
        "Critico no es cerrado: hasta el reset todavia se puede "
        "pujar, y es justo cuando mas importa."
    )
    assert reloj["must_publish_before_reset"] is True

    print("  OK  la ultima hora es critica pero sigue operativa")


# ============================================================
# EL SNAPSHOT CADUCADO
# ============================================================

def test_snapshot_caducado_se_detecta() -> None:
    """
    El caso del 16/08: snapshot de las 00:45, consultado a las
    09:43. Entre medias hubo reset. Los 20 jugadores que trae ya
    no estan en el mercado.
    """
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=ts("2026-08-16T09:43:00"),
    )

    assert reloj["listings_stale"] is True, (
        "Un snapshot anterior al reset trae un mercado que ya no "
        "existe y hay que marcarlo."
    )
    assert reloj["bidding_window_open"] is False, (
        "REGRESION: pujar sobre una lista caducada es tirar la "
        "operacion. La ventana debe darse por no operable."
    )

    print("  OK  el snapshot caducado se detecta y bloquea pujas")


def test_snapshot_caducado_apunta_al_reset_siguiente() -> None:
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=ts("2026-08-16T09:43:00"),
    )

    assert reloj["seconds_to_reset"] > 0
    assert reloj["next_reset_iso"].startswith("2026-08-17T05:00"), (
        f"El siguiente reset deberia ser el del 17/08, no "
        f"{reloj['next_reset_iso']}."
    )

    print("  OK  apunta al reset del dia siguiente")


def test_snapshot_muy_viejo_no_se_queda_en_bucle() -> None:
    """
    Un snapshot de hace cinco dias tiene que resolverse igual, no
    quedarse dando vueltas ni devolver un reset pasado.
    """
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL + 5 * 86_400 + 3600,
    )

    assert reloj["seconds_to_reset"] > 0
    assert reloj["listings_stale"] is True

    print("  OK  un snapshot de hace 5 dias se resuelve")


def test_snapshot_fresco_no_se_marca_caducado() -> None:
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 3600 * 6,
    )

    assert reloj["listings_stale"] is False
    assert reloj["computer_listings"] == 2

    print("  OK  un snapshot fresco no se marca caducado")


# ============================================================
# NO PUEDE ROMPER EL CICLO
# ============================================================

def test_no_lanza_con_basura() -> None:
    """
    El reloj se llama dentro de run_cycle. Si lanza, se cae el
    ciclo entero por un dato secundario.
    """
    casos = [
        {},
        {"market": None},
        {"market": {"sales": None}},
        {"market": {"sales": [None, "texto", 42]}},
        {"market": {"sales": [{"user": None, "until": "no-es-hora"}]}},
        {"market": {"sales": [{"user": None, "until": None}]}},
    ]

    for caso in casos:
        reloj = build_market_clock(caso, now_ts=RESET_REAL - 7200)

        assert isinstance(reloj, dict)
        assert "window_state" in reloj
        assert reloj["window_state"] in {
            "OPEN",
            "CLOSING_SOON",
            "CRITICAL",
            "UNKNOWN",
        }

    print("  OK  aguanta snapshots corruptos sin lanzar")


def test_el_contrato_siempre_trae_las_mismas_claves() -> None:
    """
    Quien consuma el reloj no deberia tener que comprobar si la
    clave existe segun por que rama salio.
    """
    obligatorias = {
        "available",
        "next_reset_epoch",
        "seconds_to_reset",
        "hours_to_reset",
        "window_state",
        "source",
        "listings_stale",
        "computer_listings",
        "bidding_window_open",
        "must_publish_before_reset",
        "reason",
    }

    normal = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 7200,
    )
    roto = build_market_clock(
        {"market": {"sales": [None]}},
        now_ts=None,
    )

    for reloj, etiqueta in ((normal, "normal"), (roto, "degradado")):
        faltan = obligatorias - set(reloj)
        assert not faltan, (
            f"El caso {etiqueta} no devuelve {sorted(faltan)}."
        )

    print("  OK  el contrato es el mismo en todos los caminos")


def test_el_desfase_de_madrid_no_depende_del_sistema() -> None:
    """
    Este test nacio de un fallo real.

    La primera version usaba zoneinfo. En GitHub Actions -Linux-
    imprimia el reset como 07:00, correcto. En el PC del usuario
    -Windows, sin base de datos de zonas horarias- zoneinfo
    reventaba, el except se lo tragaba y salia 05:00.

    El mismo codigo daba dos horas distintas segun donde corriera,
    y la que fallaba era la que lee el humano. Ahora el desfase se
    calcula con la regla europea, que es aritmetica pura.
    """
    casos = [
        ("2026-01-15T12:00:00", 1, "enero: invierno"),
        ("2026-08-16T05:00:00", 2, "agosto: verano"),
        ("2026-03-29T00:59:00", 1, "justo antes del cambio de marzo"),
        ("2026-03-29T01:00:00", 2, "justo en el cambio de marzo"),
        ("2026-10-25T00:59:00", 2, "justo antes del cambio de octubre"),
        ("2026-10-25T01:00:00", 1, "justo en el cambio de octubre"),
        ("2027-03-28T01:00:00", 2, "otro ano: marzo de 2027"),
    ]

    for texto, esperado, etiqueta in casos:
        momento = datetime.fromisoformat(texto).replace(
            tzinfo=timezone.utc
        )
        obtenido = madrid_offset_hours(momento)

        assert obtenido == esperado, (
            f"{etiqueta}: Madrid deberia ir UTC+{esperado}, "
            f"no UTC+{obtenido}."
        )

    print("  OK  el desfase de Madrid sale de la regla europea")


def test_hora_local_para_el_humano() -> None:
    """
    El usuario razona en hora de Madrid: el reset es 'las 07:00'.
    En UTC son las 05:00 y eso confunde al leer los informes.
    """
    reloj = build_market_clock(
        snapshot([venta_computer(), venta_computer(player=2)]),
        now_ts=RESET_REAL - 7200,
    )

    assert reloj["next_reset_local"] is not None
    assert "07:00" in reloj["next_reset_local"], (
        f"El reset de las 05:00 UTC deberia mostrarse como 07:00 "
        f"de Madrid. Salio {reloj['next_reset_local']}."
    )

    print(
        f"  OK  se muestra en hora de Madrid: "
        f"{reloj['next_reset_local']}"
    )


# ============================================================

TESTS = [
    test_el_reset_sale_de_los_datos,
    test_los_rivales_no_contaminan_el_calculo,
    test_el_computer_se_reconoce_sin_vendedor,
    test_sin_mercado_del_computer_hay_respaldo,
    test_el_respaldo_apunta_al_futuro_no_al_pasado,
    test_ventana_abierta_lejos_del_reset,
    test_ventana_cerrando_a_dos_horas,
    test_ventana_critica_en_la_ultima_hora,
    test_snapshot_caducado_se_detecta,
    test_snapshot_caducado_apunta_al_reset_siguiente,
    test_snapshot_muy_viejo_no_se_queda_en_bucle,
    test_snapshot_fresco_no_se_marca_caducado,
    test_no_lanza_con_basura,
    test_el_contrato_siempre_trae_las_mismas_claves,
    test_el_desfase_de_madrid_no_depende_del_sistema,
    test_hora_local_para_el_humano,
]


def main() -> None:
    print("=" * 60)
    print(" RELOJ DEL MERCADO")
    print("=" * 60)

    fallos = 0

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()
        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)
    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)
    print(f" {len(TESTS)}/{len(TESTS)} TESTS OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
