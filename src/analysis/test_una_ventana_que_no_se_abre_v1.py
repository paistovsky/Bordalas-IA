"""
Una ventana que no se abre se ve.

SINTOMA (10/09/2026)

    La ventana del reset no se abrio NUNCA. El cron externo
    disparaba una hora tarde -CET en vez de CEST- y el plan
    contestaba `FUERA_DE_VENTANA`.

    Esa frase es la misma que sale el resto del dia. Dos semanas
    sin una sola puja, con el motivo delante, y **indistinguible
    de una noche normal**.

LA REGLA QUE SALE DE AHI

    Una capacidad que nunca se dispara tiene que anunciar su
    propia ausencia.

LO QUE SE PROTEGE

     1. Que se publique cuando se entro por ultima vez y que se
        hizo alli.
     2. Que pasadas 24 h sin entrar salga en ROJO.
     3. Que "nunca se ha entrado" tambien sea ROJO, y lo diga
        con esas palabras.
     4. Que entrar y no hacer nada NO sea rojo, y se distinga de
        no entrar.
     5. Que la ventana ampliada -135 min- y el silencio -desde
        las 04:45- sigan atados.
     6. Que los dos disparos externos no puedan renovar ni pujar
        dos veces, y que eso salga DEL LIBRO y no de la foto.

ESTAS GUARDIAS NO LEEN EL MUNDO

    `estado_de_la_ventana` es pura: se le pasan la anotacion y
    la hora. Lo que toca disco se prueba contra un directorio
    temporal.

REGLA 24: si no hay casos que mirar, falla.

COMO SE USA

    python -m src.analysis.test_una_ventana_que_no_se_abre_v1
"""

from __future__ import annotations

import tempfile

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.la_subasta import (
    VENTANA_MINUTOS,
    plan_del_reset,
    ventana_abierta,
)
from src.analysis.renovar_ofertas import que_renovar
from src.analysis.zona_de_silencio import (
    SILENCIO_DESDE,
    SILENCIO_HASTA,
    permite_escribir,
)
from src.intelligence.libro_de_la_ventana import (
    HORAS_SIN_ENTRAR_QUE_SON_ROJO,
    apuntar_ventana,
    estado_de_la_ventana,
    ultima_ventana,
)


AHORA = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)


def _hace(horas: float, **extra) -> dict:
    fila = {
        "at": (AHORA - timedelta(hours=horas)).isoformat(),
        "bids": 0,
        "renewals": 0,
        "trigger": "workflow_dispatch",
        "executed": False,
    }
    fila.update(extra)
    return fila


# ============================================================
# REGLA 24
# ============================================================

def test_hay_casos_que_mirar():

    assert HORAS_SIN_ENTRAR_QUE_SON_ROJO == 24.0, (
        "el rojo ya no son 24 h: el reset es diario y ese numero "
        "es el periodo, no un ajuste"
    )

    # Y que el fixture DE VERDAD distinga verde de rojo: si los
    # dos salieran igual, todo lo de abajo pasaria sin mirar.
    verde = estado_de_la_ventana(_hace(2), AHORA)
    rojo = estado_de_la_ventana(_hace(30), AHORA)

    assert verde["red"] is False and rojo["red"] is True, (
        "el fixture no separa una ventana reciente de una vieja"
    )


# ============================================================
# 1, 2, 3, 4. QUE LA AUSENCIA SE VEA
# ============================================================

def test_se_publica_cuando_se_entro_y_que_se_hizo():

    estado = estado_de_la_ventana(
        _hace(3, bids=3, renewals=8), AHORA
    )

    assert estado["ever"] is True
    assert estado["hours_since"] == 3.0
    assert estado["last_bids"] == 3
    assert estado["last_renewals"] == 8
    assert "3 puja(s) y 8 renovacion(es)" in estado["reason"]


def test_mas_de_24_horas_sin_entrar_es_rojo():

    for horas in (24.1, 30, 48, 200):

        estado = estado_de_la_ventana(_hace(horas), AHORA)

        assert estado["red"] is True, (
            f"{horas} h sin entrar y no sale en rojo"
        )

        assert "NO SE ENTRA" in estado["reason"], (
            f"no lo dice con claridad: {estado['reason']}"
        )

    # Y justo por debajo, no.
    assert estado_de_la_ventana(_hace(23.9), AHORA)["red"] is False


def test_no_haber_entrado_nunca_tambien_es_rojo():
    """
    Es el caso real del 10/09, y el que mas cuesta ver: no hay
    nada de lo que tirar.
    """

    for vacio in (None, {}, {"at": None}, "no soy una fila"):

        estado = estado_de_la_ventana(vacio, AHORA)

        assert estado["red"] is True, (
            f"con {vacio!r} no sale en rojo"
        )

        assert estado["ever"] is False

    assert "NUNCA" in estado_de_la_ventana(None, AHORA)["reason"]


def test_entrar_y_no_hacer_nada_no_es_rojo():
    """
    "Entre y no habia trabajo" es informacion, y es MUY distinto
    de "no entre". Manana mismo la ventana no tiene trabajo
    porque el dueno renovo a mano.
    """

    estado = estado_de_la_ventana(
        _hace(1, bids=0, renewals=0), AHORA
    )

    assert estado["red"] is False
    assert estado["ever"] is True
    assert "no habia trabajo" in estado["reason"], (
        f"no distingue entrar sin trabajo: {estado['reason']}"
    )


def test_el_libro_de_la_ventana_apunta_y_se_lee():

    with tempfile.TemporaryDirectory() as carpeta:

        ruta = Path(carpeta) / "ventana.jsonl"

        assert ultima_ventana(ruta=ruta) is None, (
            "sin libro tendria que devolver None"
        )

        apuntar_ventana(
            seconds_to_reset=300,
            bids=3,
            renewals=8,
            trigger="workflow_dispatch",
            executed=True,
            ruta=ruta,
        )

        ultima = ultima_ventana(ruta=ruta)

        assert ultima["bids"] == 3
        assert ultima["renewals"] == 8
        assert ultima["executed"] is True

        estado = estado_de_la_ventana(ultima)

        assert estado["red"] is False


# ============================================================
# 5. LA VENTANA Y EL SILENCIO VAN ATADOS
# ============================================================

def test_la_ventana_ampliada_deja_entrar_al_cron_externo():
    """
    Con 15 minutos, los cuatro disparos posibles quedaban fuera.
    """

    assert VENTANA_MINUTOS == 135, (
        f"la ventana son {VENTANA_MINUTOS} min: con menos de "
        f"135 el disparo de las 04:45 no entra"
    )

    reset = 7 * 60

    for hora, minuto in ((4, 45), (4, 50), (5, 45), (5, 50)):

        faltan = reset - (hora * 60 + minuto)

        assert ventana_abierta(faltan * 60)["abierta"], (
            f"a las {hora:02d}:{minuto:02d} de Madrid la ventana "
            f"sigue cerrada"
        )


def test_el_silencio_cubre_la_ventana_entera():
    """
    Ampliar sin mover el silencio dejaba 04:45-05:00 sin
    vigilar. Medido antes de tocarlo: un `schedule` a las 04:47
    salia ABIERTA y con permiso para escribir.

    Los dos numeros van atados.
    """

    assert SILENCIO_DESDE == 4 * 60 + 45, (
        f"el silencio empieza en {SILENCIO_DESDE} min y la "
        f"ventana se abre a las 04:45"
    )

    assert SILENCIO_HASTA == 7 * 60

    # No puede quedar ni un minuto de ventana sin silencio.
    inicio_ventana = 7 * 60 - VENTANA_MINUTOS

    assert SILENCIO_DESDE <= inicio_ventana, (
        f"la ventana se abre a los {inicio_ventana} min y el "
        f"silencio no empieza hasta los {SILENCIO_DESDE}: "
        f"quedan {inicio_ventana - SILENCIO_DESDE} minutos sin "
        f"vigilar"
    )

    # Y en la practica: el cron de GitHub que llega tarde calla
    # en todo el rango; el disparo deliberado escribe.
    for hora, minuto in ((4, 45), (4, 47), (5, 30), (6, 52)):

        utc = datetime(
            2026, 9, 11, hora - 2, minuto, tzinfo=timezone.utc
        )

        tarde = permite_escribir(utc, "schedule")

        deliberado = permite_escribir(utc, "workflow_dispatch")

        assert tarde["allowed"] is False, (
            f"a las {hora:02d}:{minuto:02d} un cron tarde "
            f"escribiria"
        )

        assert deliberado["allowed"] is True, (
            f"a las {hora:02d}:{minuto:02d} el disparo "
            f"deliberado no puede trabajar"
        )


# ============================================================
# 6. DOS DISPAROS, UNA SOLA VEZ
# ============================================================

def _candidatos():
    return [
        {
            "id": i,
            "name": f"J{i}",
            "market_price": 100_000 + i * 1_000,
            "team_id": i,
        }
        for i in range(1, 5)
    ]


def _plan(**cambios):
    argumentos = {
        "candidatos": _candidatos(),
        "prima_de_reventa": 0.0187,
        "presupuesto": 2_500_000,
        "fichas_libres": 6,
        "caja_libre": 500_000,
        "seconds_to_reset": 300,
        "solvency_clock": {"state": "SIN_DEUDA", "deficit": 0},
        "en_vivo": True,
        "max_por_club": 4,
    }
    argumentos.update(cambios)
    return plan_del_reset(**argumentos)


def test_el_segundo_disparo_no_puja_dos_veces():
    """
    Los dos crones externos estan a cinco minutos y ahora caen
    los dos dentro de la ventana. Pujar dos veces por el mismo
    compromete capacidad POR DUPLICADO.
    """

    primero = _plan()

    assert primero["bids"], (
        "el primer disparo no puja: la guardia no prueba nada"
    )

    puestos = [b["id"] for b in primero["bids"]]

    segundo = _plan(ya_pujados=puestos)

    repetidos = [
        b["id"] for b in segundo["bids"] if b["id"] in puestos
    ]

    assert not repetidos, (
        f"el segundo disparo repite pujas: {repetidos}"
    )


def test_el_segundo_disparo_no_renueva_dos_veces():

    listado = {
        "id": 1,
        "name": "Jonny",
        "listed_price": 2_350_000,
        "listing_hours_to_expiry": 4.7,
        "offer_amount": 2_401_600,
    }

    primero = que_renovar(
        [listado], 300, puede_escribir=True
    )

    assert primero["count"] == 1, (
        "el primer disparo no renueva: no prueba nada"
    )

    # El segundo, con la foto SIN refrescar -la oferta todavia
    # viva- pero con el LIBRO diciendo que ya se hizo.
    segundo = que_renovar(
        [listado],
        60,
        puede_escribir=True,
        ya_renovados=["Jonny"],
    )

    assert segundo["count"] == 0, (
        "renueva dos veces en la misma ventana con la foto sin "
        "refrescar"
    )

    motivos = [s["reason"] for s in segundo["skipped"]]

    assert any("ya se renovo" in m.lower() for m in motivos), (
        f"no dice que ya se habia renovado: {motivos}"
    )


def test_la_dedup_sale_del_libro_y_no_de_la_foto():
    """
    La prueba de que no depende de la foto: los mismos datos de
    entrada, cambiando SOLO lo que dice el libro.
    """

    listado = {
        "id": 1,
        "name": "Jonny",
        "listed_price": 100,
        "listing_hours_to_expiry": 1.0,
        "offer_amount": 500,
    }

    sin_libro = que_renovar([listado], 300, puede_escribir=True)

    con_libro = que_renovar(
        [listado],
        300,
        puede_escribir=True,
        ya_renovados=["Jonny"],
    )

    assert sin_libro["count"] == 1
    assert con_libro["count"] == 0, (
        "el libro no cambia la decision: la dedup no depende de "
        "el"
    )


def test_no_se_apunta_una_entrada_si_la_ventana_no_se_abrio():
    """
    EL FALLO QUE SE COMETIO AL CONSTRUIR ESTO (10/09/2026)

        La condicion para apuntar la entrada era
        `blocked_by != "FUERA_DE_VENTANA"`. Cuando se quito la
        puerta de la ventana de `que_renovar` -porque renovar
        dejo de depender de ella- esa condicion se quedo sin
        sentido: `blocked_by` ya no vale nunca FUERA_DE_VENTANA.

        Resultado: se apuntaba una entrada EN CADA VUELTA. El
        libro se lleno de entradas falsas y la alarma de "24 h
        sin entrar" no habria saltado JAMAS.

        Un verde falso en el panel que existe para cazar verdes
        falsos.

    NO TOCA LA RED NI `data/`: se cambian por delante las
    funciones que tocarian Biwenger y se desvia el libro.
    """

    import src.autopilot as autopilot
    import src.intelligence.libro_de_la_ventana as libro
    import src.v10_full_autonomous_live as v10

    retrato = autopilot.load_rival_intelligence
    tablon = autopilot.board_del_ciclo
    ruta_original = libro.FICHERO

    with tempfile.TemporaryDirectory() as carpeta:

        try:
            autopilot.load_rival_intelligence = lambda s: {
                "managers": [],
                "current_user_id": 9,
            }
            autopilot.board_del_ciclo = lambda s: {
                "current_user_id": 9
            }

            libro.FICHERO = Path(carpeta) / "ventana.jsonl"

            # Una vuelta CUALQUIERA: doce horas para el reset.
            v10._renovar_en_la_ventana(
                {
                    "snapshot": {"my_team": []},
                    "result": {
                        "state": {
                            "market_clock": {
                                "seconds_to_reset": 12 * 3600
                            }
                        }
                    },
                }
            )

            assert not libro.FICHERO.exists(), (
                "ha apuntado una entrada en la ventana con la "
                "ventana CERRADA: la alarma de las 24 h no "
                "volveria a saltar"
            )

        finally:
            autopilot.load_rival_intelligence = retrato
            autopilot.board_del_ciclo = tablon
            libro.FICHERO = ruta_original


def test_nada_de_esto_lanza():

    for basura in (None, "no", {}, [], 0):

        assert isinstance(
            estado_de_la_ventana(basura, basura), dict
        )

    assert estado_de_la_ventana(None, None)["red"] is True


TESTS = [
    test_hay_casos_que_mirar,
    test_se_publica_cuando_se_entro_y_que_se_hizo,
    test_mas_de_24_horas_sin_entrar_es_rojo,
    test_no_haber_entrado_nunca_tambien_es_rojo,
    test_entrar_y_no_hacer_nada_no_es_rojo,
    test_el_libro_de_la_ventana_apunta_y_se_lee,
    test_la_ventana_ampliada_deja_entrar_al_cron_externo,
    test_el_silencio_cubre_la_ventana_entera,
    test_el_segundo_disparo_no_puja_dos_veces,
    test_el_segundo_disparo_no_renueva_dos_veces,
    test_la_dedup_sale_del_libro_y_no_de_la_foto,
    test_no_se_apunta_una_entrada_si_la_ventana_no_se_abrio,
    test_nada_de_esto_lanza,
]


def main() -> None:

    print()
    print("=" * 60)
    print("UNA VENTANA QUE NO SE ABRE SE VE — V1")
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
