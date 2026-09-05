"""
La deuda tiene fecha de caducidad, y el reloj no puede mentir.

SINTOMA

    "No quiero salir de rojo hoy. Con estar en positivo 6 horas
     antes del inicio de jornada es suficiente."

    Hasta hoy la solvencia era un ESTADO: cualquier deficit
    encendia "Prioridad: recuperar solvencia" y ahi se quedaba,
    con doce ofertas sobre la mesa, tres planes calculados y cero
    ejecutados. Un aviso que suena siempre no avisa de nada.

CAUSA

    Nadie miraba el calendario. `pepe_now` decia lo mismo a seis
    dias del cierre que a seis horas.

CONSECUENCIA

    Un reloj que se equivoque de lado es peor que no tenerlo:

        - si avisa demasiado pronto, empuja a malvender con
          tiempo por delante;
        - si avisa demasiado tarde, no da tiempo a crear
          liquidez, que es lento;
        - y si dice "cubierto" cuando no lo esta, Pepe llega a la
          jornada en rojo creyendo que iba bien.

    Esta guardia fija los tres lados.
"""

from __future__ import annotations

import ast
import json

from pathlib import Path

from src.analysis.computer_offer_reroll_engine import (
    ACCEPT_BEFORE_DEADLINE_HOURS,
)

from src.analysis.solvency_clock import (
    COMPUTER_CYCLE_HOURS,
    CRITICO,
    CUBIERTO,
    CUBIERTO_PERO_CADUCA,
    EN_EL_PLAZO,
    PUBLICAR,
    SIN_DEUDA,
    SOLVENCY_DEADLINE_HOURS,
    build_solvency_clock,
)


FOTO = Path("diagnostico/status.json")

MODULO = Path("src/analysis/solvency_clock.py")


def _oferta(nombre, importe, horas, protection="SELLABLE"):
    return {
        "players": [nombre],
        "amount": importe,
        "hours_to_expiry": horas,
        "protection": protection,
    }


def _produccion():
    if not FOTO.exists():
        return None

    return json.loads(FOTO.read_text(encoding="utf-8"))


# ============================================================
# 1. EL PLAZO ES UNO SOLO
# ============================================================


def test_el_plazo_no_es_un_numero_nuevo() -> None:
    """
    Seis horas ya estaban escritas en el motor de reroll, y hacen
    exactamente esto. Un segundo numero seria un segundo sitio
    donde equivocarse.
    """

    assert SOLVENCY_DEADLINE_HOURS == ACCEPT_BEFORE_DEADLINE_HOURS
    assert SOLVENCY_DEADLINE_HOURS == 6.0

    fuente = MODULO.read_text(encoding="utf-8")

    assert "ACCEPT_BEFORE_DEADLINE_HOURS" in fuente, (
        "el reloj se ha copiado el plazo en vez de importarlo"
    )


# ============================================================
# 2. LOS TRES LADOS DEL RELOJ
# ============================================================


def test_sin_deuda_el_reloj_no_aprieta() -> None:
    reloj = build_solvency_clock(1_500_000, 12.0)

    assert reloj["state"] == SIN_DEUDA
    assert reloj["deficit"] == 0
    assert reloj["solvency_overrides_hold"] is False


def test_lejos_del_plazo_manda_el_motor_de_ofertas() -> None:
    """
    Con seis dias por delante, un deficit es una posicion
    legitima. Forzar la venta aqui es malvender.
    """

    reloj = build_solvency_clock(
        -421_792,
        150.7,
        offers=[_oferta("Lucas Cepeda", 471_200, 40.9)],
    )

    assert reloj["state"] == CUBIERTO
    assert reloj["solvency_overrides_hold"] is False, (
        "el reloj fuerza la venta a seis dias del cierre"
    )
    assert "lejos del plazo" in (reloj["override_reason"] or "")


def test_dentro_del_plazo_manda_la_solvencia() -> None:
    """
    Estar en numeros rojos cuando empieza la jornada no es una
    opinion discutible.
    """

    reloj = build_solvency_clock(
        -421_792,
        5.0,
        offers=[_oferta("Lucas Cepeda", 471_200, 40.9)],
    )

    assert reloj["state"] == EN_EL_PLAZO
    assert reloj["solvency_overrides_hold"] is True
    assert "manda la solvencia" in reloj["override_reason"]


def test_el_desempate_cambia_justo_en_las_seis_horas() -> None:
    """
    El borde exacto, para que nadie lo mueva sin querer.
    """

    ofertas = [_oferta("Lucas Cepeda", 471_200, 40.9)]

    justo_dentro = build_solvency_clock(
        -100_000, SOLVENCY_DEADLINE_HOURS, offers=ofertas
    )
    justo_fuera = build_solvency_clock(
        -100_000, SOLVENCY_DEADLINE_HOURS + 0.1, offers=ofertas
    )

    assert justo_dentro["solvency_overrides_hold"] is True
    assert justo_fuera["solvency_overrides_hold"] is False


# ============================================================
# 3. LAS DOS VELOCIDADES
# ============================================================


def test_sin_ofertas_y_con_tiempo_toca_publicar() -> None:
    """
    Crear liquidez es lento: hace falta un ciclo entero del
    Computer para que valore lo publicado y ofrezca.
    """

    reloj = build_solvency_clock(
        -3_000_000,
        COMPUTER_CYCLE_HOURS + SOLVENCY_DEADLINE_HOURS + 10,
        offers=[],
    )

    assert reloj["state"] == PUBLICAR
    assert "publicar" in reloj["reason_text"].lower()


def test_sin_ofertas_y_sin_tiempo_es_critico() -> None:
    """
    Menos de un ciclo del Computer y sin ofertas: el unico camino
    es que un manager compre una publicacion, y de eso se vio UNO
    en 67 horas de tablon.
    """

    reloj = build_solvency_clock(
        -3_000_000,
        SOLVENCY_DEADLINE_HOURS + 5,
        offers=[],
    )

    assert reloj["state"] == CRITICO
    assert "67" in reloj["reason_text"], (
        "el estado critico no dice el dato que lo justifica"
    )


def test_una_oferta_que_caduca_antes_no_tapa_nada() -> None:
    """
    Cubierto HOY no es cubierto AL PLAZO.
    """

    reloj = build_solvency_clock(
        -3_000_000,
        20.0,                       # plazo a 14 h
        offers=[_oferta("Alguien", 3_500_000, 2.0)],
    )

    assert reloj["state"] == CUBIERTO_PERO_CADUCA
    assert reloj["covered_now"] >= reloj["deficit"]
    assert reloj["covered_at_deadline"] < reloj["deficit"]


def test_a_seis_dias_no_se_avisa_de_caducidad() -> None:
    """
    EL FALLO DE LA PRIMERA VERSION

        Preguntaba "¿sobreviven las ofertas de hoy hasta el
        plazo?" con el plazo a 144,7 horas, y como las del
        Computer caducan cada 24 h la respuesta era siempre no.
        Salia "cubierto pero caduca" a seis dias del cierre, que
        es una alarma sin sentido.

        Las ofertas se renuevan cada ciclo: mas alla de un ciclo,
        las de hoy no son las que van a tapar nada.
    """

    reloj = build_solvency_clock(
        -421_792,
        150.7,
        offers=[_oferta("Lucas Cepeda", 471_200, 40.9)],
    )

    assert reloj["state"] != CUBIERTO_PERO_CADUCA, (
        "el reloj avisa de una caducidad que no importa hasta "
        "dentro de seis dias"
    )


def test_un_protegido_no_cuenta_como_liquidez() -> None:
    """
    Contar la oferta por Yamal como dinero disponible seria decir
    que la deuda esta cubierta con dinero que no se va a tocar.
    """

    reloj = build_solvency_clock(
        -1_000_000,
        30.0,
        offers=[
            _oferta("Yamal", 21_892_300, 40.9, "NEVER_AUTO_SELL"),
        ],
    )

    assert reloj["covered_now"] == 0
    assert reloj["state"] in (PUBLICAR, CRITICO)


# ============================================================
# 4. A QUIEN SE VENDE SALE DE LA COLA, NO DE LA OFERTA MAS GORDA
# ============================================================


def test_se_vende_lo_justo_y_no_lo_mas_grande() -> None:
    """
    Con un deficit de 421.792, vender 3.377.100 lo arregla y
    ademas rompe el once. La cola del 11/09 ya ordena por quien
    sobra: se coge al primero que llegue al importe.
    """

    cola = {
        "queue": [
            {
                "order": 1,
                "name": "Lucas Cepeda",
                "cash_kind": "OFERTA_VIVA",
                "cash_now": 471_200,
                "reason": "No juega.",
            },
            {
                "order": 2,
                "name": "Gustavo Puerta",
                "cash_kind": "OFERTA_VIVA",
                "cash_now": 3_377_100,
                "reason": "Caro por punto.",
            },
        ]
    }

    reloj = build_solvency_clock(
        -421_792,
        5.0,
        offers=[_oferta("Lucas Cepeda", 471_200, 40.9)],
        sale_order=cola,
    )

    venta = reloj["recommended_sale"]

    assert venta["name"] == "Lucas Cepeda", (
        f"se propone vender a {venta['name']}: el reloj esta "
        f"cogiendo la oferta mas grande en vez de la primera que "
        f"tapa el agujero"
    )
    assert venta["covers_deficit"] is True
    assert venta["order"] == 1


def test_si_ninguna_llega_sola_se_dice() -> None:
    cola = {
        "queue": [
            {
                "order": 1,
                "name": "Barato",
                "cash_kind": "OFERTA_VIVA",
                "cash_now": 100_000,
                "reason": "No juega.",
            },
        ]
    }

    reloj = build_solvency_clock(
        -5_000_000,
        5.0,
        offers=[_oferta("Barato", 100_000, 40.9)],
        sale_order=cola,
    )

    assert reloj["recommended_sale"]["covers_deficit"] is False, (
        "una venta que no tapa el agujero se anuncia como si lo "
        "tapase"
    )


def test_sin_oferta_viva_no_se_recomienda_una_venta_imposible() -> None:
    """
    Un jugador de la cola sin oferta encima no es caja: hay que
    publicarlo y esperar. Proponerlo como la venta del plazo
    seria prometer dinero que no llega.
    """

    cola = {
        "queue": [
            {
                "order": 1,
                "name": "Sin oferta",
                "cash_kind": "A_MERCADO",
                "cash_now": 0,
                "reason": "No juega.",
            },
        ]
    }

    reloj = build_solvency_clock(
        -421_792, 5.0, offers=[], sale_order=cola
    )

    assert reloj["recommended_sale"] is None


# ============================================================
# 5. LO QUE YA NOS HA MORDIDO DOS VECES
# ============================================================


def test_la_coma_de_los_miles_no_se_come_la_de_la_frase() -> None:
    """
    `.replace(",", ".")` sobre la frase entera dejaba escrito
    "cubren los 421.792 EUR. pero caducan". Paso el 11/09 en
    `sale_order` y volvio a pasar aqui al dia siguiente.
    """

    for saldo, horas, ofertas in (
        (1_000_000, 12.0, []),
        (-421_792, 150.7, [_oferta("X", 471_200, 40.9)]),
        (-3_000_000, 20.0, [_oferta("X", 3_500_000, 2.0)]),
        (-3_000_000, 50.0, []),
        (-3_000_000, 8.0, []),
        (-421_792, 3.0, [_oferta("X", 471_200, 40.9)]),
    ):
        reloj = build_solvency_clock(saldo, horas, offers=ofertas)

        texto = " ".join(
            str(reloj.get(clave) or "")
            for clave in ("reason_text", "override_reason")
        )

        assert "EUR. pero" not in texto, texto
        assert "EUR. y" not in texto, texto

    fuente = MODULO.read_text(encoding="utf-8")

    assert 'f"{int(valor or 0):,}".replace(",", ".")' in fuente, (
        "el formateador de euros ha desaparecido"
    )


def test_el_reloj_no_decide_ni_escribe() -> None:
    arbol = ast.parse(MODULO.read_text(encoding="utf-8"))

    prohibidos = (
        "autopilot_executor",
        "write_client",
        "BiwengerWriteClient",
        "accept_offer",
    )

    for nodo in ast.walk(arbol):

        if isinstance(nodo, (ast.Import, ast.ImportFrom)):

            texto = ast.dump(nodo)

            for prohibido in prohibidos:
                assert prohibido not in texto, (
                    f"el reloj importa {prohibido}: deja de ser un "
                    f"observador"
                )

        if isinstance(nodo, ast.Call):

            objetivo = getattr(nodo.func, "attr", None)

            assert objetivo not in ("write_text", "write_bytes"), (
                "el reloj escribe en disco"
            )


def test_nunca_lanza_con_basura() -> None:
    for entrada in (
        (None, None),
        ("no soy un numero", "yo tampoco"),
        (-100, float("nan")),
    ):
        reloj = build_solvency_clock(*entrada)

        assert isinstance(reloj, dict)
        assert "available" in reloj


# ============================================================
# 6. SOBRE LA FOTO DE PRODUCCION
# ============================================================


def test_la_foto_de_produccion_no_esta_en_el_plazo() -> None:
    """
    Con la foto del 05/09 a las 14:03: -421.792 de saldo y 150,7 h
    para el cierre. El plazo esta a 144,7 h, asi que el reloj NO
    puede estar forzando ninguna venta.
    """

    foto = _produccion()

    if not foto:
        return

    reloj = build_solvency_clock(
        (foto.get("summary") or {}).get("balance"),
        (foto.get("summary") or {}).get("hours_to_deadline"),
        offers=foto.get("offers"),
        market_clock=foto.get("market_clock"),
    )

    assert reloj["available"]
    assert reloj["deficit"] > 0, (
        "la foto de referencia ya no tiene deficit: revisa los "
        "numeros de este fichero antes de fiarte de el"
    )
    assert reloj["solvency_overrides_hold"] is False
    assert reloj["state"] == CUBIERTO


def test_la_recomendacion_es_la_misma_regla_que_el_camino_vivo() -> None:
    """
    `offers_to_collect` cobra la oferta mas PEQUEÑA que tape el
    agujero. Si el reloj publicase otra, el dueño aprobaria una
    venta y ocurriria otra distinta.

    Aqui la mas pequeña que tapa es la 5.ª de la cola, no la 1.ª:
    el reloj tiene que elegirla igualmente.
    """

    cola = {
        "queue": [
            {
                "order": 1,
                "name": "Primero pero grande",
                "cash_kind": "OFERTA_VIVA",
                "cash_now": 3_381_600,
                "reason": "No juega.",
            },
            {
                "order": 5,
                "name": "Ultimo pero justo",
                "cash_kind": "OFERTA_VIVA",
                "cash_now": 2_150_700,
                "reason": "Caro por punto.",
            },
        ]
    }

    reloj = build_solvency_clock(
        -1_651_717,
        5.0,
        offers=[_oferta("Ultimo pero justo", 2_150_700, 40.9)],
        sale_order=cola,
    )

    assert reloj["recommended_sale"]["name"] == "Ultimo pero justo", (
        "el reloj recomienda una venta distinta de la que haria "
        "`offers_to_collect`"
    )


TESTS = [
    test_el_plazo_no_es_un_numero_nuevo,
    test_sin_deuda_el_reloj_no_aprieta,
    test_lejos_del_plazo_manda_el_motor_de_ofertas,
    test_dentro_del_plazo_manda_la_solvencia,
    test_el_desempate_cambia_justo_en_las_seis_horas,
    test_sin_ofertas_y_con_tiempo_toca_publicar,
    test_sin_ofertas_y_sin_tiempo_es_critico,
    test_una_oferta_que_caduca_antes_no_tapa_nada,
    test_a_seis_dias_no_se_avisa_de_caducidad,
    test_un_protegido_no_cuenta_como_liquidez,
    test_se_vende_lo_justo_y_no_lo_mas_grande,
    test_la_recomendacion_es_la_misma_regla_que_el_camino_vivo,
    test_si_ninguna_llega_sola_se_dice,
    test_sin_oferta_viva_no_se_recomienda_una_venta_imposible,
    test_la_coma_de_los_miles_no_se_come_la_de_la_frase,
    test_el_reloj_no_decide_ni_escribe,
    test_nunca_lanza_con_basura,
    test_la_foto_de_produccion_no_esta_en_el_plazo,
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
    print(f"RELOJ DE SOLVENCIA V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
