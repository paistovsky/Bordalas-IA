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
    · el cupo por ciclo de reset: DOS de estreno, y cuatro
      solo cuando se haya cerrado un viaje entero
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
    APAGADO_ENV,
    CUPO_DE_LA_PRUEBA,
    PRIMA_DEL_TRAMO_BARATO,
    SUELO_DE_LA_PRUEBA,
    CUPO_DE_ESTRENO,
    CUPO_PLENO,
    ESCRITURAS_POR_VUELTA,
    VIAJES_PARA_JUZGAR,
    a_quien_pujar,
    con_margen,
    cupo_del_reset,
    en_vivo,
    margen_esperado,
    permiso,
    ritmo_de_los_candidatos,
    los_que_se_pueden_pagar,
    se_apaga_sola,
    suelo_de_precio,
    un_viaje_cerrado_entero,
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


def test_el_cupo_empieza_en_uno_y_sube_solo() -> None:
    """
    LA ESCALERA DEL CUPO.

    Escrita el 11/09 como 2 -> 4 y corregida el 12/09 a
    1 -> 2 -> 4, porque el 12 se supo que el carril no habia
    podido comprar NUNCA: el tope por operacion (~740.000) era
    menor que el suelo de 1 M.

    El primer viaje no tiene que ganar dinero: tiene que
    COMPLETARSE. Una vez, de punta a punta. Por eso se abre con
    UNO y no con dos, y el escalon siguiente sigue siendo el que
    era.
    """

    assert CUPO_DE_LA_PRUEBA == 1, CUPO_DE_LA_PRUEBA
    assert CUPO_DE_ESTRENO == 2, CUPO_DE_ESTRENO
    assert CUPO_PLENO == 4, CUPO_PLENO

    de_prueba = cupo_del_reset([])

    assert de_prueba["cupo"] == CUPO_DE_LA_PRUEBA, de_prueba
    assert de_prueba["estado"] == "PRUEBA_DE_HUMO", de_prueba

    # En cuanto se cierra uno entero, sube solo al escalon
    # siguiente. NO al pleno: eso son dos viajes, no uno.
    de_estreno = cupo_del_reset(
        [{"profit": 120_000, "player_name": "Starfelt"}]
    )

    assert de_estreno["cupo"] == CUPO_DE_ESTRENO, de_estreno
    assert de_estreno["estado"] == "ESTRENO", de_estreno

    # Y lo dice con el nombre, para que la portada lo pinte.
    assert "Starfelt" in de_estreno["reason"], de_estreno


def test_un_corte_de_perdidas_no_sube_el_cupo() -> None:
    """
    "Entero" es cobrado POR ENCIMA DEL SUELO. Un corte de
    perdidas cerro el viaje pero la rueda no giro: se paro.
    """

    for falso in (
        [{"profit": -5_000, "loss_cut": True}],
        [{"profit": 0}],
        [{"profit": None}],
        [{}],
    ):
        assert un_viaje_cerrado_entero(falso)["hay"] is False, (
            falso
        )

        # Se queda en el escalon de abajo: la prueba de humo
        # sigue pendiente.
        assert cupo_del_reset(falso)["cupo"] == (
            CUPO_DE_LA_PRUEBA
        ), falso


def test_el_cupo_manda_sobre_el_permiso() -> None:
    """Un numero en un sitio: el permiso lo pregunta, no lo lleva."""

    for ya in range(CUPO_DE_LA_PRUEBA):
        assert permiso(
            ahora=DE_DIA, operaciones_en_este_reset=ya
        )["puede"] is True, ya

    agotado = permiso(
        ahora=DE_DIA,
        operaciones_en_este_reset=CUPO_DE_LA_PRUEBA,
    )

    assert agotado["blocked_by"] == "CUPO_DEL_RESET", agotado

    assert agotado["cupo_por_reset"] == CUPO_DE_LA_PRUEBA, (
        agotado
    )

    assert agotado["cupo_estado"] == "PRUEBA_DE_HUMO", agotado

    # Con un viaje cerrado entero, esa misma ya no agota.
    con_uno = permiso(
        ahora=DE_DIA,
        operaciones_en_este_reset=CUPO_DE_LA_PRUEBA,
        cierres=[{"profit": 120_000}],
    )

    assert con_uno["puede"] is True, con_uno


def test_la_pantalla_lee_el_cupo_no_lo_escribe() -> None:
    """
    El cupo vive en UN sitio. Si la pantalla llevara el numero
    escrito, el dia que suba a cuatro habria dos y uno estaria
    mal.
    """

    from pathlib import Path

    panel = (
        Path(__file__).parents[2]
        / "dashboard-v8"
        / "src"
        / "components"
        / "RendijaPanel.jsx"
    ).read_text(encoding="utf-8")

    assert "rendija.cupo" in panel, (
        "el panel no lee el cupo del estado publicado"
    )

    assert "cupo_reason" in panel, (
        "el panel no pinta POR QUE esta en ese cupo"
    )

    # Y no lleva el numero escrito.
    for suelto in ("cupo: 2", "cupo: 4", "= 2;", "= 4;"):
        assert suelto not in panel, (
            f"el panel lleva el cupo escrito a mano: `{suelto}`"
        )


def test_se_ve_si_los_candidatos_suben_o_caen() -> None:
    """
    La compuerta de ritmo se quito a proposito -el negocio es el
    spread, no la rampa- pero eso no es dejar de mirar.

    Si lo que compramos viniera todo cayendo, el experimento
    real seria "comprar caidos y revender", y hay que saberlo
    MIENTRAS PASA.
    """

    visto = ritmo_de_los_candidatos(
        [
            {"player_id": 1, "name": "Sube", "position": 2},
            {"player_id": 2, "name": "Cae", "position": 2},
            {"player_id": 3, "name": "Plano", "position": 2},
            {"player_id": 4, "name": "Nadie", "position": 2},
        ],
        rates={
            1: {"rate_percent_per_day": 1.2, "trend_days": 3},
            2: {"rate_percent_per_day": -0.8, "trend_days": 5},
            3: {"rate_percent_per_day": 0.0, "trend_days": 1},
        },
    )

    assert visto["available"], visto

    assert visto["subiendo"] == 1, visto
    assert visto["cayendo"] == 1, visto
    assert visto["planos"] == 1, visto
    assert visto["sin_dato"] == 1, visto

    assert visto["todos_cayendo"] is False, visto

    # Y el caso que hay que cazar.
    todos = ritmo_de_los_candidatos(
        [
            {"player_id": 1, "name": "A"},
            {"player_id": 2, "name": "B"},
        ],
        rates={
            1: {"rate_percent_per_day": -0.5},
            2: {"rate_percent_per_day": -1.1},
        },
    )

    assert todos["todos_cayendo"] is True, todos

    assert "comprar caidos y revender" in todos["reason"], todos

    # NO decide nada: nadie se cae de la lista por su ritmo.
    assert len(todos["filas"]) == 2, todos


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

    # Sin decirle cuantos, le PREGUNTA al cupo. No lo lleva
    # escrito: por eso bajar el cupo a 1 cambio esto solo.
    assert len(a_quien_pujar(candidatos)["elegidos"]) == (
        CUPO_DE_LA_PRUEBA
    )

    assert len(
        a_quien_pujar(candidatos, cuantos=CUPO_DE_ESTRENO)[
            "elegidos"
        ]
    ) == CUPO_DE_ESTRENO

    assert a_quien_pujar(candidatos, cuantos=0)["elegidos"] == []


# ============================================================
# 6. EL MARGEN ESPERADO — EL NUMERO QUE DEFINE UN VIAJE
# ============================================================


STARFELT = {
    "player_id": 1,
    "name": "Starfelt",
    "position": 2,          # defensa
    "market_price": 2_150_000,
}


def test_el_caso_de_starfelt() -> None:
    """
    EL CASO QUE MOTIVA EL NUMERO.

    Defensa, 2.150.000, CAYENDO un 2,01 %/dia. Con la prima
    mediana de la liga la operacion no llega al suelo de venta;
    con la prima de su posicion, si.

    Y eso es exactamente lo que separa este filtro de la
    compuerta de ritmo: aquella lo habria tirado por caer. Este
    lo deja entrar porque, cayendo y todo, la operacion gana.
    """

    visto = margen_esperado(
        STARFELT, prima_de_puja=0.28, ritmo_diario=-2.01
    )

    assert visto["available"], visto

    # Con la prima de SU POSICION: pasa, y pasa el suelo.
    assert 1.2 < visto["margen_percent"] < 1.4, visto

    assert visto["llega_al_suelo"] is True, visto

    # Con la mediana de la liga: positivo, pero NO llega al
    # suelo de venta. Ese es el caso del dueno.
    assert 0 < visto["margen_con_mediana_percent"] < 1.0, visto

    # El estimador que aplica es el de su posicion, y se ve cual
    # es: defensa.
    assert visto["prima_de_reventa_percent"] == 3.67, visto


def test_el_margen_no_es_la_compuerta_de_ritmo() -> None:
    """
    La compuerta exigia que el precio SUBIERA. Esto exige que la
    OPERACION GANE. No es lo mismo, y hay casos que lo separan en
    las dos direcciones.
    """

    # CAE y entra: la prima de su posicion compensa la caida.
    cayendo = margen_esperado(
        STARFELT, prima_de_puja=0.28, ritmo_diario=-2.01
    )

    assert cayendo["gana"] is True, cayendo

    # SUBE y no entra: una prima de puja alta se come la subida.
    subiendo = margen_esperado(
        {**STARFELT, "position": 4},   # delantero, +1,80 %
        prima_de_puja=8.0,
        ritmo_diario=+1.0,
    )

    assert subiendo["gana"] is False, subiendo


def test_un_margen_negativo_no_entra() -> None:
    """El unico filtro que anade este carril."""

    visto = con_margen(
        [
            {**STARFELT, "player_id": 1, "name": "Gana"},
            {
                "player_id": 2,
                "name": "Pierde",
                "position": 4,
                "market_price": 2_000_000,
            },
        ],
        prima_de_puja=8.0,
        rates={
            1: {"rate_percent_per_day": 10.0},
            2: {"rate_percent_per_day": -5.0},
        },
    )

    assert visto["available"], visto

    nombres = [x["margen"]["name"] for x in visto["entran"]]

    assert nombres == ["Gana"], visto

    assert visto["fuera"], visto

    # Regla 24: si nadie quedara fuera, esto no probaria el
    # filtro.
    assert visto["fuera"][0]["margen_percent"] < 0, visto


def test_sin_ritmo_se_usa_el_supuesto_y_se_dice() -> None:
    """
    5 de 11 candidatos no traen ritmo. Se usa el mediano del
    mercado, pero la fila queda MARCADA: un margen que descansa
    en un supuesto no es lo mismo que uno medido, y hay que poder
    juzgarlos aparte despues.
    """

    con_dato = margen_esperado(
        STARFELT, prima_de_puja=0.28, ritmo_diario=-2.01
    )

    assert con_dato["supuesto"] is False, con_dato

    sin_dato = margen_esperado(
        STARFELT,
        prima_de_puja=0.28,
        ritmo_diario=None,
        ritmo_supuesto=0.0,
    )

    assert sin_dato["supuesto"] is True, sin_dato

    assert "SUPUESTO" in sin_dato["reason"], sin_dato

    # Y sin ritmo NI supuesto no se inventa un margen.
    a_ciegas = margen_esperado(
        STARFELT, prima_de_puja=0.28, ritmo_diario=None
    )

    assert a_ciegas["available"] is False, a_ciegas

    assert a_ciegas["margen_percent"] is None, a_ciegas


def test_se_publica_si_llega_al_suelo_de_venta() -> None:
    """
    EL HUECO QUE SE VE AL MEDIRLO.

    El suelo de venta es coste + 1 %, y el margen es
    oferta/coste - 1. Asi que un margen POSITIVO pero por debajo
    del 1 % es una operacion que espera una oferta que nosotros
    mismos rechazariamos: el viaje entra y no puede cerrarse.

    El filtro pedido es "negativo fuera", y no se cambia. Pero
    esto se PUBLICA para que la diferencia se vea.
    """

    from src.analysis.salida_del_viaje import SUELO_DEL_VIAJE

    justo = margen_esperado(
        {**STARFELT, "position": 4},
        prima_de_puja=1.0,
        ritmo_diario=0.0,
    )

    assert justo["available"], justo

    # +1,80 % de delantero contra +1 % de puja: ~+0,79 %.
    assert 0 < justo["margen_percent"] < (
        SUELO_DEL_VIAJE * 100
    ), justo

    assert justo["gana"] is True, justo

    assert justo["llega_al_suelo"] is False, justo

    assert "no llega al suelo" in justo["reason"], justo


# ============================================================
# 7. ARMADA, Y APAGABLE SIN DESPLEGAR
# ============================================================


def test_la_rendija_esta_armada() -> None:
    """
    Armada el 11/09/2026, con el dueno delante y despues de leer
    el ensayo en seco.
    """

    import os

    antes = os.environ.get(APAGADO_ENV)

    try:
        os.environ.pop(APAGADO_ENV, None)

        assert en_vivo() is True, (
            "la rendija ya no esta armada"
        )

        # Y se apaga SIN DESPLEGAR.
        os.environ[APAGADO_ENV] = "1"

        assert en_vivo() is False, (
            f"`{APAGADO_ENV}=1` ya no apaga el carril: el dia que "
            f"haya que pararla habria que esperar a un commit"
        )

        assert (
            permiso(ahora=DE_DIA)["en_vivo"] is False
        ), "el permiso no obedece al interruptor"

    finally:
        if antes is None:
            os.environ.pop(APAGADO_ENV, None)
        else:
            os.environ[APAGADO_ENV] = antes


# ============================================================
# 8. Y ALGUIEN LA LLAMA
# ============================================================


def test_el_ciclo_llama_al_carril() -> None:
    """
    EL FALLO DEL 12/09/2026.

    La rendija se encendio el 11 y al dia siguiente no habia
    comprado nada. No fue ninguna de las cinco puertas: era que
    NADIE LLAMABA AL CARRIL. Los modulos escritos, 24 guardias en
    verde, el estado publicado y la pantalla pintando "EN VIVO"
    sobre codigo que no corria.

    `en_vivo = True` era la bandera del modulo, no una prueba de
    que se ejecutara. Armar algo y no enchufarlo es PEOR que no
    armarlo, porque la pantalla dice que funciona.
    """

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    ciclo = (
        raiz / "src" / "v10_full_autonomous_live.py"
    ).read_text(encoding="utf-8")

    assert "_correr_el_carril" in ciclo, (
        "el ciclo no llama al carril: la rendija esta encendida "
        "y no la ejecuta nadie"
    )

    assert '"carril": carril' in ciclo, (
        "el ciclo no publica lo que hizo el carril"
    )

    ejecutor = (
        raiz / "src" / "actions" / "carril_executor.py"
    ).read_text(encoding="utf-8")

    # La unica escritura, y ninguna otra.
    assert "place_bid" in ejecutor, ejecutor[:0]

    for prohibida in (
        "accept_offer",
        "list_player_for_sale",
        "cancel_bid",
        "counter_offer",
    ):
        assert prohibida not in ejecutor, (
            f"el carril escribe `{prohibida}`, y solo puede pujar"
        )


def test_el_disparo_deliberado_viaja_hasta_el_silencio() -> None:
    """
    Los disparos de las 04:45 y 04:50 caen DENTRO de la zona de
    silencio a proposito, y la zona los salva si se le dice que
    son deliberados.

    `permiso()` llamaba a `permite_escribir(momento)` sin el
    disparo, asi que los bloqueaba igual que a los del cron —
    justo en la ventana del reset, que es para lo que estan.
    """

    # 04:50 de Madrid.
    en_la_ventana = datetime(
        2026, 9, 12, 2, 50, tzinfo=timezone.utc
    )

    assert permiso(ahora=en_la_ventana)["blocked_by"] == (
        "SILENCIO"
    ), "sin decir el disparo tiene que seguir bloqueando"

    assert permiso(
        ahora=en_la_ventana, disparo="schedule"
    )["blocked_by"] == "SILENCIO", (
        "el cron NO puede escribir en la zona de silencio"
    )

    for deliberado in ("ventana", "workflow_dispatch", "manual"):
        visto = permiso(
            ahora=en_la_ventana, disparo=deliberado
        )

        assert visto["puede"] is True, (deliberado, visto)

    # Y el ciclo se lo pasa.
    from pathlib import Path

    ejecutor = (
        Path(__file__).parents[2]
        / "src"
        / "actions"
        / "carril_executor.py"
    ).read_text(encoding="utf-8")

    assert "disparo=disparo" in ejecutor, (
        "el ejecutor no le pasa el disparo al permiso"
    )


def test_el_filtro_es_el_suelo_no_el_cero() -> None:
    """
    EL ARREGLO PENDIENTE.

    El suelo de cobro es coste + 1 %, y el margen es
    oferta/coste - 1. Un margen entre 0 y 1 % es un viaje que
    espera una oferta que NOSOTROS MISMOS RECHAZARIAMOS.

    Ayer entro asi Robbie Ure, con +0,49 %.
    """

    from src.analysis.salida_del_viaje import SUELO_DEL_VIAJE

    ure = {
        "player_id": 9,
        "name": "Robbie Ure",
        "position": 4,
        "market_price": 3_590_000,
    }

    visto = con_margen(
        [ure],
        prima_de_puja=0.28,
        rates={9: {"rate_percent_per_day": -1.01}},
    )

    assert visto["entran"] == [], (
        f"Robbie Ure vuelve a entrar con un margen que no llega "
        f"al suelo: {visto}"
    )

    assert visto["fuera"], visto

    # Y su margen SI era positivo: el filtro viejo lo dejaba
    # pasar. Si esto dejara de ser positivo, la guardia estaria
    # probando otra cosa.
    assert 0 < visto["fuera"][0]["margen_percent"] < (
        SUELO_DEL_VIAJE * 100
    ), visto


# ============================================================
# 9. LA PRUEBA DE HUMO
# ============================================================


def test_la_prueba_de_humo_baja_el_suelo_y_el_cupo() -> None:
    """
    El primer viaje NO tiene que ganar dinero: tiene que
    COMPLETARSE. Con el tope por operacion de hoy (~740.000) y el
    suelo normal de 1 M, las dos condiciones eran incompatibles y
    el carril no podia comprar NUNCA.

    Un viaje, y se mira.
    """

    assert SUELO_DE_LA_PRUEBA == 400_000, SUELO_DE_LA_PRUEBA
    assert CUPO_DE_LA_PRUEBA == 1, CUPO_DE_LA_PRUEBA

    suelo = suelo_de_precio([])

    assert suelo["suelo"] == SUELO_DE_LA_PRUEBA, suelo
    assert suelo["estado"] == "PRUEBA_DE_HUMO", suelo

    assert cupo_del_reset([])["cupo"] == CUPO_DE_LA_PRUEBA


def test_al_completar_un_viaje_vuelve_todo_a_su_sitio() -> None:
    """
    La prueba termina sola. Un viaje completo —cobrado por encima
    del suelo— y el suelo vuelve a 1.000.000 y el cupo a 2.

    Y la condicion NO la cumple un corte de perdidas: eso cerro
    el viaje, no lo completo.
    """

    from src.analysis.salida_del_viaje import (
        PRECIO_QUE_NO_PAGA_LA_FICHA,
    )

    completo = [{"profit": 9_000, "player_name": "el primero"}]

    assert suelo_de_precio(completo)["suelo"] == (
        PRECIO_QUE_NO_PAGA_LA_FICHA
    )

    assert suelo_de_precio(completo)["estado"] == "NORMAL"

    assert cupo_del_reset(completo)["cupo"] == CUPO_DE_ESTRENO

    # Nueve mil euros bastan: lo que compran es saber que la
    # cadena funciona.
    assert completo[0]["profit"] < 10_000

    # Un corte de perdidas NO termina la prueba.
    for falso in (
        [{"profit": -5_000, "loss_cut": True}],
        [{"profit": 0}],
    ):
        assert suelo_de_precio(falso)["estado"] == (
            "PRUEBA_DE_HUMO"
        ), falso


def test_los_baratos_usan_la_prima_de_su_tramo() -> None:
    """
    LO QUE HABRIA HECHO OPTIMISTA LA PRUEBA.

    Las dos tablas salen de las MISMAS 34 recompras, partidas de
    dos formas. Para un jugador de menos de 1 M la que describe
    su caso es la del TRAMO (+1,52 %), no la de su posicion.

    A un medio de 660.000 se le aplicaba +2,85 %: casi dos puntos
    de margen inventados, justo en el rango donde va a jugarse la
    prueba de humo.
    """

    assert PRIMA_DEL_TRAMO_BARATO == 1.52, PRIMA_DEL_TRAMO_BARATO

    barato = margen_esperado(
        {
            "player_id": 1,
            "name": "Víctor García",
            "position": 3,          # medio, +2,85 %
            "market_price": 660_000,
        },
        prima_de_puja=0.25,
        ritmo_diario=-1.80,
    )

    assert barato["prima_de_reventa_percent"] == (
        PRIMA_DEL_TRAMO_BARATO
    ), barato

    # Y con la prima buena NO llega al suelo: la prueba no puede
    # entrar en un viaje que no se puede cerrar.
    assert barato["llega_al_suelo"] is False, barato

    # Por encima de 1 M sigue mandando la posicion.
    caro = margen_esperado(
        {
            "player_id": 2,
            "name": "Un medio caro",
            "position": 3,
            "market_price": 2_000_000,
        },
        prima_de_puja=0.25,
        ritmo_diario=0.0,
    )

    assert caro["prima_de_reventa_percent"] == 2.85, caro


def test_la_via_vieja_esta_en_pausa() -> None:
    """
    UNA TEORIA CADA VEZ.

    La via vieja y el carril son dos teorias opuestas del mismo
    negocio sobre el mismo mercado. Mientras las dos corran, cada
    compra puede ser de cualquiera y no se puede juzgar ninguna.
    """

    import os

    from src.analysis.speculation_engine import (
        ESPECULACION_EN_PAUSA_ENV,
        especulacion_vieja_en_pausa,
    )

    antes = os.environ.get(ESPECULACION_EN_PAUSA_ENV)

    try:
        # Sin decir nada, esta en pausa. Y si el entorno no se
        # puede leer tambien: durante la prueba el lado seguro es
        # que solo corra una teoria.
        os.environ.pop(ESPECULACION_EN_PAUSA_ENV, None)

        assert especulacion_vieja_en_pausa() is True, (
            "la via vieja ya no esta en pausa"
        )

        # Y se reanuda sin desplegar.
        os.environ[ESPECULACION_EN_PAUSA_ENV] = "0"

        assert especulacion_vieja_en_pausa() is False

    finally:
        if antes is None:
            os.environ.pop(ESPECULACION_EN_PAUSA_ENV, None)
        else:
            os.environ[ESPECULACION_EN_PAUSA_ENV] = antes


def test_pausar_no_cambia_la_forma() -> None:
    """
    DOS VECES LO MISMO, Y LA SEGUNDA CASI TUMBA LA PRUEBA.

    1. La primera version de la pausa devolvia un diccionario
       corto y `portfolio_roi_engine` reviento con
       KeyError: 'owned'.

    2. Arreglada la forma, seguia devolviendo `budget: 0`. El
       presupuesto NO es una opinion de la via vieja: es la caja
       de la liga, y EL CARRIL LO LEE DE AHI. Con aquel cero, el
       carril contestaba "Sin presupuesto de especulacion
       conocido no se puja" — pausar la via vieja apagaba en
       silencio justo lo que la pausa existia para poder medir.

    Pausar una via para sus DECISIONES, nunca sus MEDICIONES.
    """

    import ast

    from pathlib import Path

    from src.analysis.speculation_engine import (
        _tablero_en_pausa,
    )

    # LAS CLAVES DEL RETORNO DE VERDAD, del arbol y no de una
    # lista escrita a mano: el dia que alguien anada una clave al
    # tablero y se olvide de la pausa, esto se pone rojo.
    fuente = (
        Path(__file__).parents[1] / "analysis"
        / "speculation_engine.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    completo = None

    for nodo in ast.walk(arbol):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "build_speculation_board"
        ):
            for hijo in ast.walk(nodo):

                if (
                    isinstance(hijo, ast.Return)
                    and isinstance(hijo.value, ast.Dict)
                    and len(hijo.value.keys) > 10
                ):
                    completo = {
                        k.value
                        for k in hijo.value.keys
                        if isinstance(k, ast.Constant)
                    }

    assert completo and len(completo) >= 13, completo

    pausado = _tablero_en_pausa(budget=1_234_567)

    faltan = completo - set(pausado)

    assert not faltan, (
        f"pausar se come estas claves, que otros leen: "
        f"{sorted(faltan)}"
    )

    # LO QUE SE MIDE PASA ENTERO.
    assert pausado["budget"] == 1_234_567, pausado

    # LO QUE SE DECIDE VA VACIO.
    for callado in (
        "players",
        "buy_candidates",
        "executable_buys",
        "owned",
        "sell_candidates",
        "hold_candidates",
        "watchlist",
    ):
        assert pausado[callado] == [], (callado, pausado[callado])

    assert pausado["paused"] is True


def test_el_tope_se_pregunta_al_elegir_no_al_pagar() -> None:
    """
    EL FALLO DE CANCELO (12/09/2026).

    Bajado el suelo a 400.000 para que el carril pudiera comprar
    algo por fin, siguio sin comprar: elegia a CANCELO
    -5.970.000- contra un tope por operacion de 843.612. Siete
    veces el tope.

    El tope existia y se aplicaba... AL PAGAR. Para entonces el
    candidato ya estaba elegido y el ciclo, gastado. Y como el
    orden de preferencia va por prima de reventa, que prefiere a
    los caros, el carril elegia SIEMPRE al que menos podia pagar.

    Un techo que solo se comprueba cuando ya no se puede hacer
    nada no es un techo: es un parte de defuncion.
    """

    PRESUPUESTO = 2_109_030          # medido el 12/09
    TOPE = 843_612                   # 40 % de ese presupuesto

    mercado = [
        {"player_id": 1, "name": "Cancelo", "position": 2,
         "market_price": 5_970_000},
        {"player_id": 2, "name": "Víctor García", "position": 3,
         "market_price": 660_000},
    ]

    filtrado = los_que_se_pueden_pagar(
        mercado, curva=1.0, presupuesto=PRESUPUESTO
    )

    assert filtrado["tope"] == TOPE, filtrado

    assert [x["name"] for x in filtrado["caben"]] == (
        ["Víctor García"]
    ), filtrado

    # Y el que no cabe sale CON SU NOMBRE y con el tope que le
    # echa: la pantalla tiene que poder decir por que no se
    # compro, en vez de callarse.
    fuera = filtrado["no_caben"]

    assert len(fuera) == 1, fuera
    assert fuera[0]["name"] == "Cancelo", fuera
    assert fuera[0]["capped_by"] == (
        "MAX_SINGLE_SPECULATION_PERCENT"
    ), fuera

    # EL ORDEN PREFIERE AL CARO: por eso el filtro tiene que ir
    # ANTES. Sin el, el elegido es el imposible.
    sin_filtrar = a_quien_pujar(mercado, cuantos=1)["elegidos"]

    assert sin_filtrar[0]["name"] == "Cancelo", (
        "si esto cambia, el caso que motivo la guardia ya no es "
        "el que era: revisala"
    )

    con_filtro = a_quien_pujar(
        filtrado["caben"], cuantos=1
    )["elegidos"]

    assert con_filtro[0]["name"] == "Víctor García", con_filtro

    # Regla 24: sin presupuesto no pasa nadie, y se dice.
    a_ciegas = los_que_se_pueden_pagar(
        mercado, curva=1.0, presupuesto=None
    )

    assert a_ciegas["caben"] == [], a_ciegas
    assert len(a_ciegas["no_caben"]) == 2, a_ciegas

    # Y con la lista vacia no pasa en vacio: lo dice.
    assert "no habia nadie" in (
        los_que_se_pueden_pagar(
            [], curva=1.0, presupuesto=PRESUPUESTO
        )["reason"]
    )


def test_el_carril_filtra_por_el_tope_antes_de_elegir() -> None:
    """
    Lo mismo, pero en el camino de verdad: que el ejecutor lo
    llame, y que no puje por quien no puede pagar.
    """

    import ast
    from pathlib import Path

    fuente = (
        Path(__file__).parents[1] / "actions"
        / "carril_executor.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    llamadas = [
        n.func.id
        for n in ast.walk(arbol)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
    ]

    assert "los_que_se_pueden_pagar" in llamadas, (
        "el ejecutor no pregunta por el tope antes de elegir: "
        "volveria a elegir a Cancelo"
    )

    # Y lo pregunta ANTES de elegir, no despues.
    assert fuente.index("los_que_se_pueden_pagar(") < (
        fuente.index("elegidos = a_quien_pujar(")
    ), (
        "el tope se pregunta DESPUES de elegir, que es "
        "exactamente el fallo"
    )


def test_el_suelo_vive_en_un_sitio() -> None:
    """
    UN DATO, UN NOMBRE (regla 33).

    La telemetria llevaba el suelo escrito a mano —
    `>= 1_000_000` — al filtrar los candidatos que pinta. Al
    bajarlo a 400.000 para la prueba de humo, la pantalla habria
    seguido pintando la lista vieja: el carril mirando una cosa y
    el panel otra, y ninguna de las dos avisando.
    """

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    def _sin_comentarios(texto: str) -> str:
        # Las lineas que EXPLICAN el incidente nombran el
        # numero. Esta guardia se ha puesto roja sobre su propia
        # documentacion mas de una vez.
        return chr(10).join(
            linea
            for linea in texto.splitlines()
            if not linea.strip().startswith("#")
        )

    for ruta in (
        raiz / "src" / "telemetry" / "dashboard_state.py",
        raiz / "src" / "actions" / "carril_executor.py",
    ):
        codigo = _sin_comentarios(
            ruta.read_text(encoding="utf-8")
        )

        for escrito in ("1_000_000", "400_000"):
            assert escrito not in codigo, (
                f"{ruta.name} lleva el suelo escrito a mano "
                f"(`{escrito}`) en vez de preguntarselo a "
                f"`suelo_de_precio`"
            )

        assert "suelo_de_precio" in codigo or 'suelo["suelo"]' in (
            codigo
        ), f"{ruta.name} no le pregunta el suelo a su unico sitio"


def test_la_pantalla_dice_el_suelo_y_los_viajes() -> None:
    """
    Lo que el dueno quiere ver cada dia: en que suelo esta, por
    que, y cuantos viajes se han completado.
    """

    from pathlib import Path

    import re

    panel = (
        Path(__file__).parents[2] / "dashboard-v8" / "src"
        / "components" / "RendijaPanel.jsx"
    ).read_text(encoding="utf-8")

    # LOS COMENTARIOS QUE EXPLICAN EL INCIDENTE NOMBRAN EL
    # NUMERO. Es la tercera vez que una guardia se pone roja
    # sobre su propia documentacion: lo que no puede llevar el
    # numero escrito es el CODIGO que se ejecuta.
    codigo = re.sub(
        r"\{/\*.*?\*/\}", "", panel, flags=re.S
    )

    codigo = re.sub(r"/\*.*?\*/", "", codigo, flags=re.S)

    codigo = chr(10).join(
        linea
        for linea in codigo.splitlines()
        if not linea.strip().startswith("//")
    )

    for dato in (
        "rendija.suelo",
        "suelo_reason",
        "viajes_completados",
        "VIAJES COMPLETADOS",
    ):
        assert dato in panel, (
            f"el panel no pinta `{dato}`"
        )

    # Y no lleva ningun numero escrito a mano.
    for suelto in ("400.000", "1.000.000", "400000", "1000000"):
        assert suelto not in codigo, (
            f"el panel lleva el suelo escrito a mano: `{suelto}`"
        )


TESTS = [
    test_el_carril_no_escribe_en_la_zona_de_silencio,
    test_con_una_emergencia_el_carril_se_calla,
    test_el_cupo_empieza_en_uno_y_sube_solo,
    test_un_corte_de_perdidas_no_sube_el_cupo,
    test_el_cupo_manda_sobre_el_permiso,
    test_la_pantalla_lee_el_cupo_no_lo_escribe,
    test_se_ve_si_los_candidatos_suben_o_caen,
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
    test_el_caso_de_starfelt,
    test_el_margen_no_es_la_compuerta_de_ritmo,
    test_un_margen_negativo_no_entra,
    test_sin_ritmo_se_usa_el_supuesto_y_se_dice,
    test_se_publica_si_llega_al_suelo_de_venta,
    test_la_rendija_esta_armada,
    test_el_ciclo_llama_al_carril,
    test_el_disparo_deliberado_viaja_hasta_el_silencio,
    test_el_filtro_es_el_suelo_no_el_cero,
    test_la_prueba_de_humo_baja_el_suelo_y_el_cupo,
    test_al_completar_un_viaje_vuelve_todo_a_su_sitio,
    test_los_baratos_usan_la_prima_de_su_tramo,
    test_la_via_vieja_esta_en_pausa,
    test_pausar_no_cambia_la_forma,
    test_el_tope_se_pregunta_al_elegir_no_al_pagar,
    test_el_carril_filtra_por_el_tope_antes_de_elegir,
    test_el_suelo_vive_en_un_sitio,
    test_la_pantalla_dice_el_suelo_y_los_viajes,
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
