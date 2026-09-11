"""
La rendija: carril propio, escaparate, y la oferta de un VIAJE.

QUE SE ARMA AQUI

    La primera ruta de esta casa que COMPRA sola para revender, y
    la mitad que faltaba para que un viaje pueda cerrarse.

LO QUE SE QUITA, Y POR QUE

    LA VENTANA, para pujar por revender. Esta medido: todas las
    pujas se resuelven en el reset de las 07:00 y las de los
    rivales son INVISIBLES, asi que pujar tarde no nos esconde de
    nadie. La ventana no aportaba nada — era una creencia
    nuestra, no una mecanica del juego.

    LA COMPUERTA DE RITMO, para el cupo de abajo.

LO QUE NO SE QUITA, Y ESTAS GUARDIAS LO PRUEBAN

    · la zona de silencio
    · cuatro operaciones por ciclo de reset
    · dos escrituras del carril por vuelta
    · ni una si la vuelta se fue en una emergencia
    · las cinco prohibiciones de `que_cobrar`
    · y que la rendija se apaga sola si pierde dinero

LA GUARDIA CLAVE

    Un jugador marcado VIAJE no puede terminar un ciclo SIN
    LISTAR. Comprado para revender y fuera del escaparate es una
    vuelta tirada, y sin esto no lo notaria nadie.
"""

from __future__ import annotations

import tempfile

from datetime import datetime, timezone
from pathlib import Path

from src.actions.escaparate_executor import (
    precio_de_escaparate,
    que_publicar,
    viajes_sin_listar,
)
from src.analysis.la_rendija import (
    ESCRITURAS_POR_VUELTA,
    OPERACIONES_POR_RESET,
    VIAJES_PARA_JUZGAR,
    a_quien_pujar,
    permiso,
    se_apaga_sola,
)
from src.analysis.offer_decision_engine import (
    decide_incoming_offer,
)


# Una hora cualquiera fuera del silencio, fijada para que estas
# guardias no dependan del reloj (regla 23).
DE_DIA = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)

# 06:00 de Madrid: dentro de la zona de silencio.
EN_SILENCIO = datetime(2026, 9, 11, 4, 0, tzinfo=timezone.utc)


def _sin_marcas(fn):
    """Ejecuta con un libro de viajes vacio y desechable."""

    with tempfile.TemporaryDirectory() as carpeta:
        return fn(Path(carpeta) / "viajes.jsonl")


# ============================================================
# 1. EL CARRIL NO COMPITE, PERO TIENE CINCO PUERTAS
# ============================================================


def test_el_carril_no_escribe_en_la_zona_de_silencio() -> None:
    """
    Lo unico que no se negocia. Mientras el mercado se resuelve,
    los datos son de otro mundo y no se toca nada.
    """

    visto = permiso(ahora=EN_SILENCIO)

    assert visto["puede"] is False, visto

    assert visto["blocked_by"] == "SILENCIO", visto

    # Y la zona es la que ya habia: no se ha movido ningun
    # umbral para abrir esto.
    from src.analysis.zona_de_silencio import (
        SILENCIO_DESDE,
        SILENCIO_HASTA,
    )

    assert SILENCIO_HASTA == 7 * 60, SILENCIO_HASTA

    # Cubre de sobra el 05:00-07:00 que pidio el dueno.
    assert SILENCIO_DESDE <= 5 * 60, SILENCIO_DESDE


def test_con_una_emergencia_el_carril_se_calla() -> None:
    """
    Si la vuelta se fue en una emergencia, no es momento de
    comprar para revender. El carril se calla ESA vuelta.
    """

    for emergencia in (
        "EMERGENCY_SOLVENCY",
        "EMERGENCY_LINEUP",
        "HARD_SAFETY",
        "ROUND_LOCK",
    ):
        visto = permiso(
            ahora=DE_DIA, accion_principal=emergencia
        )

        assert visto["puede"] is False, (emergencia, visto)

        assert visto["blocked_by"] == "EMERGENCIA", visto

    # Y con una accion normal, no estorba.
    assert permiso(
        ahora=DE_DIA, accion_principal="LINEUP_LOW"
    )["puede"] is True


def test_el_cupo_es_por_ciclo_de_reset() -> None:
    """
    Al no haber ventana, el cupo necesitaba una unidad. Es el
    ciclo de reset: de 07:00 a 07:00, cuatro operaciones.
    """

    assert OPERACIONES_POR_RESET == 4, OPERACIONES_POR_RESET

    for ya in range(OPERACIONES_POR_RESET):
        assert permiso(
            ahora=DE_DIA, operaciones_en_este_reset=ya
        )["puede"] is True, ya

    agotado = permiso(
        ahora=DE_DIA,
        operaciones_en_este_reset=OPERACIONES_POR_RESET,
    )

    assert agotado["puede"] is False, agotado

    assert agotado["blocked_by"] == "CUPO_DEL_RESET", agotado


def test_dos_escrituras_del_carril_por_vuelta() -> None:
    """
    El presupuesto propio y pequeno. Sin esto, el carril podria
    gastarse una vuelta entera en pujas.
    """

    assert ESCRITURAS_POR_VUELTA == 2, ESCRITURAS_POR_VUELTA

    agotado = permiso(
        ahora=DE_DIA,
        escrituras_en_esta_vuelta=ESCRITURAS_POR_VUELTA,
    )

    assert agotado["blocked_by"] == "CUPO_DE_LA_VUELTA", agotado


def test_si_no_se_sabe_si_puede_no_puede() -> None:
    """
    Regla 24 y doctrina 36: la duda no abre la puerta. Con una
    entrada imposible, el permiso sale que NO y lo dice.
    """

    visto = permiso(ahora="no soy una fecha")

    assert visto["puede"] is False, visto

    assert visto["reason"], visto


# ============================================================
# 2. SE APAGA SOLA
# ============================================================


def test_la_rendija_se_apaga_sola_si_pierde_dinero() -> None:
    """
    Tras 10 viajes cerrados con mediana negativa, se cierra. No
    hace falta que nadie se acuerde de mirarla.
    """

    perdiendo = se_apaga_sola([{"profit": -50_000}] * 10)

    assert perdiendo["apagada"] is True, perdiendo

    assert "CERRADO SOLA" in perdiendo["reason"], perdiendo

    # Y el permiso obedece.
    assert permiso(
        ahora=DE_DIA, cierres=[{"profit": -50_000}] * 10
    )["blocked_by"] == "APAGADA"

    ganando = se_apaga_sola([{"profit": 40_000}] * 10)

    assert ganando["apagada"] is False, ganando


def test_una_racha_corta_no_apaga_nada() -> None:
    """
    Con nueve no se opina. Apagar por una racha seria el mismo
    error que montar una regla sobre un caso — y ese ya costo la
    primera ventana del reset.
    """

    assert VIAJES_PARA_JUZGAR == 10, VIAJES_PARA_JUZGAR

    corta = se_apaga_sola([{"profit": -90_000}] * 9)

    assert corta["apagada"] is False, corta

    assert corta["mediana"] is None, corta

    assert "aun no hay con que juzgar" in corta["reason"]


# ============================================================
# 3. EL ESCAPARATE
# ============================================================


def test_el_recien_comprado_se_lista_a_valor_por_115() -> None:
    """
    La misma regla de renovar. Aqui el `max(precio_actual, ...)`
    se resuelve solo: un recien comprado no tiene precio anterior
    que proteger.
    """

    from src.analysis.renovar_ofertas import PRIMA_DE_LA_PETICION

    assert PRIMA_DE_LA_PETICION == 1.15, PRIMA_DE_LA_PETICION

    assert precio_de_escaparate(5_230_000) == 6_014_500

    # Sin valor de mercado NO se inventa un precio.
    assert precio_de_escaparate(0) == 0
    assert precio_de_escaparate(None) == 0


def test_no_se_publica_a_quien_no_esta_en_plantilla() -> None:
    """
    Si la puja no se gano, el jugador no esta. Marcar y listar a
    quien no es nuestro seria escribir contra Biwenger por un
    jugador de otro.
    """

    visto = que_publicar(
        [{"player_id": 99999, "name": "Fantasma"}],
        plantilla=[{"id": 19862, "name": "Exposito"}],
    )

    assert visto["publicar"] == [], visto

    assert visto["saltados"], visto

    assert "no esta en la plantilla" in (
        visto["saltados"][0]["reason"]
    )


def test_un_viaje_no_puede_acabar_el_ciclo_sin_listar() -> None:
    """
    LA GUARDIA CLAVE.

    Comprado para revender y fuera del escaparate es una vuelta
    tirada, y sin esto no lo notaria nadie. Sale en ROJO en la
    portada, con nombre y hora.
    """

    huerfano = viajes_sin_listar(
        viajes=[
            {
                "player_id": 19862,
                "name": "Exposito",
                "opened_at": "2026-09-11T10:00:00+00:00",
                "cost": 5_147_000,
            }
        ],
        listados=[],
    )

    assert huerfano["ok"] is False, huerfano

    assert huerfano["players"], huerfano

    # Nombre Y hora, que es lo que pidio el dueno.
    assert "Exposito" in huerfano["reason"], huerfano
    assert "2026-09-11T10:00" in huerfano["reason"], huerfano

    # Y publicado, no molesta.
    bien = viajes_sin_listar(
        viajes=[{"player_id": 19862, "name": "Exposito"}],
        listados=[{"player_id": 19862}],
    )

    assert bien["ok"] is True, bien


# ============================================================
# 4. LA OFERTA DE UN VIAJE NO LA JUZGA EL MOTOR DE SIEMPRE
# ============================================================


def _oferta(amount: int) -> dict:
    return {
        "offer_id": 1,
        "player_id": 19862,
        "player_name": "Exposito",
        "amount": amount,
        "market_value": 5_230_000,
        "price_increment": 40_000,
    }


def _resto():
    return {
        "roster": {},
        "strategic": {},
        # ALTO A PROPOSITO: es el caso que hoy da HOLD.
        "speculation": {"score": 90},
        "reroll_offer": None,
        "recovery_selected_offer_ids": set(),
    }


def test_un_viaje_se_vende_aunque_el_score_diga_que_no() -> None:
    """
    EL CASO EXACTO.

    `speculation_score >= 62 and price_increment > 0` da
    HOLD_OFFER, y para un VIAJE es la pregunta equivocada: un
    jugador comprado para revender tiene por construccion señal
    alta y precio subiendo, asi que la regla lo retenia JUSTO
    cuando el viaje salia bien.

    Con la marca, la unica pregunta es el suelo.
    """

    # Sin marca: sigue haciendo lo de siempre. No se toca nada
    # de la plantilla.
    sin_marca = decide_incoming_offer(
        _oferta(5_300_000), **_resto()
    )

    assert sin_marca["decision"] == "HOLD_OFFER", sin_marca

    # Con marca y oferta por encima del suelo: se cobra.
    con_marca = decide_incoming_offer(
        _oferta(5_300_000),
        viaje={"cost": 5_147_000},
        **_resto(),
    )

    assert con_marca["decision"] == "ACCEPT_TRIP", con_marca

    assert con_marca["decision_authority"] == "VIAJE", con_marca

    assert con_marca["trip"]["profit"] == 153_000, con_marca


def test_un_viaje_por_debajo_del_suelo_no_se_vende() -> None:
    """
    El suelo es coste + 1 %. Por debajo, no. Y sin coste
    conocido tampoco: con coste 0 el suelo seria 0 y cualquier
    oferta pasaria — la puerta abierta mas cara que hay.
    """

    from src.analysis.salida_del_viaje import SUELO_DEL_VIAJE

    assert SUELO_DEL_VIAJE == 0.01, SUELO_DEL_VIAJE

    justo_debajo = decide_incoming_offer(
        _oferta(5_198_469),
        viaje={"cost": 5_147_000},
        **_resto(),
    )

    assert justo_debajo["decision"] == "HOLD_TRIP", justo_debajo

    sin_coste = decide_incoming_offer(
        _oferta(9_999_999), viaje={"cost": 0}, **_resto()
    )

    assert sin_coste["decision"] == "HOLD_TRIP", sin_coste

    assert "sin coste conocido" in sin_coste["reasons"][0]


# ============================================================
# 5. A QUIEN PREFERIR — ORDEN, NO FILTRO
# ============================================================


def test_se_prefieren_defensas_y_porteros() -> None:
    """
    Medido el 10/09 sobre 34 recompras del Computer: defensa
    +3,67 %, portero +3,26 %, medio +2,85 %, delantero +1,80 %.

    Es un ORDEN, no un filtro: no se descarta a nadie por su
    posicion.
    """

    candidatos = [
        {"player_id": 1, "name": "Delantero", "position": 4,
         "market_price": 2_000_000},
        {"player_id": 2, "name": "Defensa", "position": 2,
         "market_price": 2_000_000},
        {"player_id": 3, "name": "Portero", "position": 1,
         "market_price": 2_000_000},
    ]

    visto = a_quien_pujar(candidatos)

    assert visto["available"], visto

    nombres = [
        c.get("name") for c in visto["orden"]
    ]

    assert nombres[0] == "Defensa", nombres

    assert nombres.index("Portero") < nombres.index(
        "Delantero"
    ), nombres

    # Nadie se ha caido: es orden, no filtro.
    assert len(visto["orden"]) == len(candidatos), visto


def test_caben_los_que_diga_el_cupo() -> None:
    """Regla 24: si el cupo fuera 0, no se elige a nadie."""

    candidatos = [
        {"player_id": i, "name": f"J{i}", "position": 2,
         "market_price": 2_000_000}
        for i in range(1, 8)
    ]

    assert len(a_quien_pujar(candidatos)["elegidos"]) == (
        OPERACIONES_POR_RESET
    )

    assert a_quien_pujar(candidatos, cuantos=0)["elegidos"] == []


TESTS = [
    test_el_carril_no_escribe_en_la_zona_de_silencio,
    test_con_una_emergencia_el_carril_se_calla,
    test_el_cupo_es_por_ciclo_de_reset,
    test_dos_escrituras_del_carril_por_vuelta,
    test_si_no_se_sabe_si_puede_no_puede,
    test_la_rendija_se_apaga_sola_si_pierde_dinero,
    test_una_racha_corta_no_apaga_nada,
    test_el_recien_comprado_se_lista_a_valor_por_115,
    test_no_se_publica_a_quien_no_esta_en_plantilla,
    test_un_viaje_no_puede_acabar_el_ciclo_sin_listar,
    test_un_viaje_se_vende_aunque_el_score_diga_que_no,
    test_un_viaje_por_debajo_del_suelo_no_se_vende,
    test_se_prefieren_defensas_y_porteros,
    test_caben_los_que_diga_el_cupo,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LA RENDIJA V1: {len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
