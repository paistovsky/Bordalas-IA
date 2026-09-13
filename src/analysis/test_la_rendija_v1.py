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
    CARRIL_TOPE_POR_OPERACION,
    CUPO_DE_LA_PRUEBA,
    PRIMA_DEL_TRAMO_BARATO,
    SUELO_RETIRADO_DE_LA_PRUEBA,
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
    bolsillo_del_carril,
    importe_de_la_puja,
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

    # EL ONCE HACE FALTA desde el 13/09: sin saber quienes son
    # los titulares no se publica nada, y esta guardia probaria
    # otra cosa. Se le da uno para que llegue a lo suyo.
    visto = que_publicar(
        [{"player_id": 99999, "name": "Fantasma"}],
        plantilla=[{"id": 19862, "name": "Exposito"}],
        titulares=[19862],
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
    # LA HORA EN CRISTIANO, y en Madrid: 10:00 UTC son las 12:00.
    # El formato de maquina no lo lee nadie de un vistazo.
    assert "el 11/09 a las 12:00" in huerfano["reason"], (
        huerfano
    )

    assert "2026-09-11T" not in huerfano["reason"], huerfano

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


def test_la_hora_declarada_manda_en_el_silencio() -> None:
    """
    Los disparos de las 04:45 y 04:50 caen DENTRO de la zona de
    silencio a proposito, y la zona los deja pasar.

    DOS ARREGLOS, Y EL SEGUNDO SE COMIO AL PRIMERO

        11/09. `permiso()` llamaba a `permite_escribir(momento)`
        SIN el disparo, asi que bloqueaba los de la ventana igual
        que a los del cron. Se arreglo pasandole el disparo.

        12/09. Se retiro el `schedule` de GitHub y ese arreglo
        dejo de servir: desde entonces TODAS las vueltas entran
        como `workflow_dispatch`, el latido incluido, asi que
        todas eran "deliberadas" y la zona dejo de frenar nada.

        Ahora decide LA HORA, contra `config/disparos.json`. El
        disparo se sigue pasando y se sigue publicando —para
        mirar un incidente vale— pero no decide.
    """

    # 04:50 de Madrid: hora declarada. Pasa venga de donde venga.
    en_la_ventana = datetime(
        2026, 9, 12, 2, 50, tzinfo=timezone.utc
    )

    for quien in (None, "schedule", "workflow_dispatch", "manual"):
        visto = permiso(ahora=en_la_ventana, disparo=quien)

        assert visto["puede"] is True, (quien, visto)

    # 05:30 y 06:40 de Madrid: DESCOLOCADOS. No pasa ninguno.
    for hora, minuto in ((3, 30), (4, 40)):

        descolocado = datetime(
            2026, 9, 12, hora, minuto, tzinfo=timezone.utc
        )

        for quien in (
            None,
            "workflow_dispatch",
            "manual",
            "ventana",
        ):
            visto = permiso(ahora=descolocado, disparo=quien)

            assert visto["blocked_by"] == "SILENCIO", (
                quien,
                visto,
            )

    # Y el ciclo se lo sigue pasando: se publica como `trigger`.
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


def test_la_prueba_de_humo_es_de_cupo_no_de_suelo() -> None:
    """
    LO QUE SE PROBO Y SE RETIRO EL MISMO DIA.

    El 12/09 se bajo el suelo a 400.000 para que la prueba de
    humo pudiera comprar algo. Medido con el mercado de ese dia,
    no valia: por debajo del millon el Computer casi no ofrece
    nada, y cuando ofrece la prima de reventa es la PEOR de las
    cuatro bandas (+1,52 %). La prueba se habria hecho en el
    unico tramo donde el negocio no existe.

    El freno NUNCA fue el suelo. Era el TECHO: 843.612 EUR de
    tope por operacion, que salia de un porcentaje del bolsillo
    de OTRO motor y era menor que el propio suelo.

    Asi que la prueba de humo se queda —UN viaje, de punta a
    punta— y el suelo vuelve a su sitio.
    """

    assert CUPO_DE_LA_PRUEBA == 1, CUPO_DE_LA_PRUEBA

    assert cupo_del_reset([])["cupo"] == CUPO_DE_LA_PRUEBA

    assert cupo_del_reset([])["estado"] == "PRUEBA_DE_HUMO"

    # EL SUELO VOLVIO, y tiene un solo estado.
    from src.analysis.salida_del_viaje import (
        PRECIO_QUE_NO_PAGA_LA_FICHA,
    )

    suelo = suelo_de_precio([])

    assert suelo["suelo"] == PRECIO_QUE_NO_PAGA_LA_FICHA, suelo

    assert suelo["estado"] == "NORMAL", suelo

    # Y no lo mueve haber cerrado un viaje: ya no es un escalon.
    assert suelo_de_precio(
        [{"profit": 9_000, "player_name": "el primero"}]
    )["suelo"] == PRECIO_QUE_NO_PAGA_LA_FICHA

    # El 400.000 sigue escrito, pero SOLO como lo que se retiro.
    assert SUELO_RETIRADO_DE_LA_PRUEBA == 400_000


def test_al_completar_un_viaje_vuelve_todo_a_su_sitio() -> None:
    """
    La prueba termina sola. Un viaje completo —cobrado por encima
    del suelo— y el cupo vuelve a 2.

    Y la condicion NO la cumple un corte de perdidas: eso cerro
    el viaje, no lo completo.
    """

    completo = [{"profit": 9_000, "player_name": "el primero"}]

    assert cupo_del_reset(completo)["cupo"] == CUPO_DE_ESTRENO

    # Nueve mil euros bastan: lo que compran es saber que la
    # cadena funciona.
    assert completo[0]["profit"] < 10_000

    # Un corte de perdidas NO termina la prueba.
    for falso in (
        [{"profit": -5_000, "loss_cut": True}],
        [{"profit": 0}],
    ):
        assert cupo_del_reset(falso)["estado"] == (
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


# ============================================================
# 10. EL BOLSILLO PROPIO DEL CARRIL
# ============================================================


def test_el_carril_tiene_bolsillo_propio_en_euros() -> None:
    """
    EL FRENO DE VERDAD NO ERA EL SUELO, ERA EL TECHO.

    Mientras el tope por operacion del carril salia de
    `MAX_SINGLE_SPECULATION_PERCENT` sobre el bolsillo del motor
    de especular, valia 843.612 EUR el 12/09: MENOS QUE EL SUELO
    de 1.000.000. El carril no podia comprar nada, nunca, por
    construccion —y bajar el suelo a 400.000 no lo arreglaba,
    solo lo mandaba al tramo de peor prima de reventa.

    Ahora el tope es suyo, en euros, y no depende de ningun
    porcentaje de otro motor.
    """

    assert CARRIL_TOPE_POR_OPERACION == 3_000_000, (
        CARRIL_TOPE_POR_OPERACION
    )

    # EL TOPE TIENE QUE SER MAYOR QUE EL SUELO, o estamos otra
    # vez donde estabamos: un carril que no puede comprar nada.
    assert CARRIL_TOPE_POR_OPERACION > (
        suelo_de_precio([])["suelo"]
    ), (
        "el tope por operacion es menor que el suelo: el carril "
        "no puede comprar nada, que es el fallo de origen"
    )

    # POR QUE 3 M Y NO 2 M: por el tramo de mejor prima medida
    # sobre las 34 recompras —1-3 M, +3,46 %—. Con 2 M el carril
    # solo alcanza la parte baja de ese tramo.
    assert CARRIL_TOPE_POR_OPERACION >= 3_000_000, (
        "por debajo de 3 M se pierde la parte alta del tramo "
        "1-3 M, que es el de mejor prima de reventa medida"
    )

    # Y NO SALE DE NINGUN PORCENTAJE DEL MOTOR DE ESPECULAR.
    from src.analysis.speculation_engine import (
        MAX_SINGLE_SPECULATION_PERCENT,
    )

    assert MAX_SINGLE_SPECULATION_PERCENT == 0.40, (
        "se ha movido un porcentaje del motor de especular, que "
        "es exactamente lo que el bolsillo propio existe para no "
        "tener que hacer"
    )


def test_el_bolsillo_no_puede_gastar_lo_que_no_hay() -> None:
    """
    Tener bolsillo propio NO es tener dinero propio.

    El carril no abre deuda para especular: su tope es el menor
    de los dos, su bolsillo y la caja LIBRE. Por eso no puede
    romper ninguna barandilla de solvencia — nunca compromete
    mas de lo que hay.
    """

    CAJA = 4_333_406                 # medida el 12/09

    holgado = bolsillo_del_carril(CAJA)

    assert holgado["tope"] == CARRIL_TOPE_POR_OPERACION, holgado

    assert holgado["limitado_por"] == (
        "CARRIL_TOPE_POR_OPERACION"
    ), holgado

    # Con la caja justa, manda la caja.
    corto = bolsillo_del_carril(1_200_000)

    assert corto["tope"] == 1_200_000, corto
    assert corto["limitado_por"] == "CAJA", corto

    # LO YA COMPROMETIDO NO ES CAJA.
    #
    #     El motor de especular ya descuenta de lo suyo lo que
    #     aparta el carril. Este es el mismo descuento en el otro
    #     sentido, que faltaba: las dos pujas se resuelven en el
    #     MISMO reset.
    con_pujas_vivas = bolsillo_del_carril(
        CAJA, comprometido=2_000_000
    )

    assert con_pujas_vivas["tope"] == CAJA - 2_000_000, (
        con_pujas_vivas
    )

    assert con_pujas_vivas["limitado_por"] == "CAJA"

    # Regla 24: sin saber la caja NO SE PUJA. Un tope de 3 M a
    # ciegas es justo lo que no puede pasar. Y dos casos
    # distintos, dos nombres (regla 33).
    for ciego, nombre in (
        (bolsillo_del_carril(None), "CAJA_DESCONOCIDA"),
        (bolsillo_del_carril(0), "CAJA_DESCONOCIDA"),
        (
            bolsillo_del_carril(CAJA, comprometido=CAJA),
            "SIN_CAJA_LIBRE",
        ),
    ):
        assert ciego["tope"] == 0, ciego
        assert ciego["available"] is False, ciego
        assert ciego["limitado_por"] == nombre, ciego


def test_el_bolsillo_propio_manda_al_elegir() -> None:
    """
    EL HALLAZGO DEL 12/09, PROBADO CON EL TOPE NUEVO.

    El tope se aplicaba AL PAGAR y no AL ELEGIR.

    Y OJO AL PORQUE, que no es "prefiere a los caros": el orden
    NO MIRA EL PRECIO. Va por prima de posicion —defensas
    primero—, asi que el primero de la lista puede costar
    cualquier cosa. El 12/09 el primero era Cancelo, defensa de
    5.970.000, contra un tope de 843.612.

    Con el tope nuevo de 3 M el caso es el mismo con otros
    numeros: Cancelo sigue siendo el primero y sigue sin caber.
    """

    CAJA = 4_333_406

    tope = bolsillo_del_carril(CAJA)["tope"]

    assert tope == 3_000_000, tope

    # Los tres son del mercado real del 12/09. Cancelo y Trent
    # son defensas: el orden los pone por delante de un medio, y
    # entre ellos no mira cual cuesta el doble.
    mercado = [
        {"player_id": 1, "name": "Cancelo", "position": 2,
         "market_price": 5_970_000},
        {"player_id": 2, "name": "Trent", "position": 2,
         "market_price": 2_760_000},
        {"player_id": 3, "name": "Ruben Garcia", "position": 3,
         "market_price": 2_680_000},
    ]

    # SIN FILTRAR: el orden elige al que no se puede pagar.
    assert a_quien_pujar(mercado, cuantos=1)["elegidos"][0][
        "name"
    ] == "Cancelo", (
        "si esto cambia, el caso que motiva la guardia ya no es "
        "el que era: revisala"
    )

    filtrado = los_que_se_pueden_pagar(
        mercado, curva=1.0, tope_por_operacion=tope
    )

    assert filtrado["tope"] == 3_000_000, filtrado

    assert [x["name"] for x in filtrado["caben"]] == [
        "Trent",
        "Ruben Garcia",
    ], filtrado

    assert [x["name"] for x in filtrado["no_caben"]] == [
        "Cancelo"
    ], filtrado

    assert filtrado["no_caben"][0]["capped_by"] == (
        "CARRIL_TOPE_POR_OPERACION"
    ), filtrado

    # CON FILTRO: elige a uno que SI se puede pagar.
    elegido = a_quien_pujar(
        filtrado["caben"], cuantos=1
    )["elegidos"][0]

    assert elegido["name"] == "Trent", elegido

    assert importe_de_la_puja(
        elegido["market_price"],
        curva=1.0,
        tope_por_operacion=tope,
    )["amount"] > 0, "el elegido no se puede pagar"

    # Y SIN CAJA no cabe nadie, aunque haya candidatos.
    a_ciegas = los_que_se_pueden_pagar(
        mercado,
        curva=1.0,
        tope_por_operacion=bolsillo_del_carril(None)["tope"],
    )

    assert a_ciegas["caben"] == [], a_ciegas


def test_un_viaje_de_tres_millones_no_rompe_la_solvencia() -> None:
    """
    LA EXPOSICION MAXIMA, EN NUMEROS.

    UN viaje —`CUPO_DE_LA_PRUEBA` = 1— de 3 M como mucho, con el
    tope acotado por la caja libre. Lo que puede perderse de
    verdad no son los 3 M: es la caida del precio mientras dure,
    que medida esta en torno al 8 % en cuatro resets.

    Esta guardia NO lee el mundo (regla 23): usa la caja medida
    el 12/09 como numero fijo. Si algun dia la caja real fuera
    otra, `bolsillo_del_carril` lo recorta solo — y eso es lo que
    se comprueba abajo.
    """

    CAJA = 4_333_406                 # medida el 12/09
    CAIDA_EN_CUATRO_RESETS = 0.08    # medida

    tope = bolsillo_del_carril(CAJA)["tope"]

    assert tope == 3_000_000

    # Despues de pagarlo entero queda caja, y positiva.
    queda = CAJA - tope

    assert queda > 0, queda

    # Y despues de la caida, tambien.
    perdida = int(tope * CAIDA_EN_CUATRO_RESETS)

    assert perdida == 240_000, perdida

    assert queda - perdida > 0, (queda, perdida)

    # NUNCA se puede comprometer mas de lo que hay: es la
    # propiedad que hace innecesario mirar la deuda, porque el
    # carril no la abre.
    for caja in (0, 100_000, 999_999, 3_000_000, 9_000_000):
        assert bolsillo_del_carril(caja)["tope"] <= caja, caja

    # Y un solo viaje: el cupo no deja abrir dos.
    assert CUPO_DE_LA_PRUEBA == 1


def test_un_viaje_sin_coste_no_se_cobra() -> None:
    """
    UN SUELO QUE NO SE PUEDE CALCULAR NO ES UN SUELO DE CERO.

    SINTOMA (13/09/2026)

        El viaje de Trent salia con `cost: 0` porque su ficha no
        traia `owner.price` —medido ese dia: la plantilla que
        devuelve Biwenger NO TRAE `owner`, ni la clave—.

        Y el suelo de cobro es coste + 1 %. Con coste 0 el suelo
        es 0 y CUALQUIER oferta lo pasa.

        Medido: con una oferta de 2.400.000 por un jugador que
        costo 2.760.000, `que_cobrar` lo vendia. 360.000 de
        perdida, y el panel diria que el primer viaje del carril
        salio bien.

    ES UN "NO VENDER", y va antes que las otras cinco
    prohibiciones: si no se sabe lo que costo, no hay
    conversacion que tener sobre la oferta.
    """

    from src.analysis.salida_del_viaje import que_cobrar

    OFERTA_ALTISIMA = 99_000_000

    for sin_coste in (0, None, "", -1):

        visto = que_cobrar(
            viajes=[
                {
                    "player_id": 37499,
                    "name": "Trent",
                    "position": 2,
                    "cost": sin_coste,
                    "state": "ABIERTO",
                }
            ],
            ofertas=[
                {
                    "player_id": 37499,
                    "amount": OFERTA_ALTISIMA,
                    "offer_id": 1,
                }
            ],
            titulares=[1599],
            porteros_en_plantilla=2,
        )

        assert visto["sell"] == [], (
            f"se cobra un viaje con coste `{sin_coste}` y una "
            f"oferta de {OFERTA_ALTISIMA}: el suelo salio 0 y "
            f"cualquier oferta lo pasa"
        )

        assert visto["skipped"], (sin_coste, visto)

        assert "no hay suelo" in visto["skipped"][0]["reason"], (
            visto["skipped"][0]
        )

    # NI CON EL CORTE DE PERDIDAS. Ese existe para vender POR
    # DEBAJO del suelo a sabiendas; aqui no hay suelo que
    # conocer, asi que no hay nada que saber.
    con_corte = que_cobrar(
        viajes=[
            {
                "player_id": 37499,
                "name": "Trent",
                "position": 2,
                "cost": 0,
                "state": "ABIERTO",
            }
        ],
        ofertas=[
            {"player_id": 37499, "amount": 10, "offer_id": 1}
        ],
        titulares=[1599],
        porteros_en_plantilla=2,
        corte_de_perdidas=True,
    )

    assert con_corte["sell"] == [], con_corte

    # Y CON COSTE, EL SUELO VUELVE A MANDAR: no se ha roto el
    # camino normal, solo se ha tapado el agujero.
    COSTE = 2_760_000

    def _con(importe):
        return que_cobrar(
            viajes=[
                {
                    "player_id": 37499,
                    "name": "Trent",
                    "position": 2,
                    "cost": COSTE,
                    "state": "ABIERTO",
                }
            ],
            ofertas=[
                {
                    "player_id": 37499,
                    "amount": importe,
                    "offer_id": 1,
                }
            ],
            titulares=[1599],
            porteros_en_plantilla=2,
        )

    assert _con(2_400_000)["sell"] == [], "vende por debajo"

    assert _con(2_790_000)["sell"], "no cobra una oferta buena"


def test_el_coste_se_guarda_cuando_se_puede_probar() -> None:
    """
    DE DONDE SALE EL COSTE, QUE ERA EL FONDO DEL PROBLEMA.

    Salia de `acquisition_cost` de la ficha, que viene de
    `owner.price`. Biwenger NO lo publica: medido el 13/09 sobre
    la plantilla real, la ficha no trae ni la clave.

    El tablon SI lo prueba —dice cuanto se pago y cuando—, asi
    que el coste se anota en el libro EN EL MOMENTO EN QUE SE
    SABE, y deja de depender de que Biwenger lo publique algun
    dia.

    Y un coste inventado seria peor que ninguno: fija un suelo
    falso y el viaje se cobra por debajo sin que nadie lo note.
    """

    import tempfile

    from pathlib import Path

    from src.analysis.libro_de_viajes import (
        abiertos,
        abrir,
        anotar_coste,
    )

    PLANTILLA = [
        {"id": 37499, "name": "Trent", "position": 2}
    ]

    with tempfile.TemporaryDirectory() as tmp:

        ruta = Path(tmp) / "viajes.jsonl"

        # 1. EL CASO DE TRENT: abierto sin saber lo que costo.
        abrir(
            player_id=37499,
            name="Trent",
            position=2,
            ruta=ruta,
        )

        primero = abiertos(plantilla=PLANTILLA, ruta=ruta)

        assert primero["viajes"] == [], primero

        assert len(primero["sin_coste"]) == 1, primero

        # 2. El tablon lo prueba, y el libro lo recoge.
        visto = anotar_coste(37499, 2_760_000, ruta=ruta)

        assert visto["noted"] is True, visto

        despues = abiertos(plantilla=PLANTILLA, ruta=ruta)

        assert len(despues["viajes"]) == 1, despues

        assert despues["viajes"][0]["cost"] == 2_760_000

        # 3. NO SE PISA lo ya anotado.
        assert anotar_coste(37499, 999, ruta=ruta)["noted"] is (
            False
        )

        assert abiertos(plantilla=PLANTILLA, ruta=ruta)[
            "viajes"
        ][0]["cost"] == 2_760_000

        # 4. Y sin importe probado, no se anota nada.
        for sin_prueba in (0, None, -1):
            assert anotar_coste(
                37499, sin_prueba, ruta=ruta
            )["noted"] is False, sin_prueba

    # 5. Y al abrir con coste, ya viene puesto: los viajes que
    #    vengan despues no pasan por esto.
    with tempfile.TemporaryDirectory() as tmp:

        ruta = Path(tmp) / "viajes.jsonl"

        abrir(
            player_id=37499,
            name="Trent",
            position=2,
            ruta=ruta,
            coste=2_760_000,
        )

        nuevo = abiertos(plantilla=PLANTILLA, ruta=ruta)

        assert nuevo["viajes"], nuevo

        assert nuevo["viajes"][0]["cost"] == 2_760_000


def test_la_pantalla_no_habla_en_jerga() -> None:
    """
    LA PANTALLA HABLA EL IDIOMA DEL QUE LEE.

    SINTOMA (13/09/2026). El cartel decia:

        "VIAJE COMPRADO Y SIN LISTAR. VIAJES SIN LISTAR: Trent
         (desde 2026-09-13T08:08). Comprados para revender y no
         estan en venta: cada vuelta asi es escaparate tirado."

    Cuatro cosas mal: "viaje" es jerga NUESTRA —el dueño no ha
    usado esa palabra nunca—, lo decia dos veces, la fecha en
    formato de maquina, y "escaparate tirado" es una metafora
    inventada aqui.

    Los nombres de los CAMPOS del estado se quedan como estan
    —`viajes_completados`, `hay_viajes`—: eso es el contrato que
    lee el codigo, no texto que lea nadie. Lo que no puede tener
    jerga es lo que se pinta.
    """

    import re

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    for ruta in (
        raiz / "dashboard-v8" / "src" / "App.jsx",
        raiz
        / "dashboard-v8"
        / "src"
        / "components"
        / "RendijaPanel.jsx",
    ):
        fuente = ruta.read_text(encoding="utf-8")

        # Sin comentarios: los de JSX CUENTAN el incidente y
        # nombran la palabra. Octava vez que una guardia
        # tropieza con su propia documentacion.
        codigo = re.sub(
            r"\{/\*.*?\*/\}", "", fuente, flags=re.S
        )

        codigo = chr(10).join(
            linea
            for linea in codigo.splitlines()
            if not linea.strip().startswith("//")
        )

        # UNA PALABRA, NO UN IDENTIFICADOR.
        #
        #     `rendija.viajes_completados` y `hay_viajes` son
        #     nombres de campo del estado: el contrato que lee el
        #     codigo, no texto que lea nadie. Se distinguen por
        #     lo que tienen ANTES —un punto o un guion bajo— o
        #     por lo que sigue.
        #
        #     Intentar extraer "el texto visible" de un JSX con
        #     expresiones regulares no funciono: el primer
        #     intento caza atributos enteros. Esto pregunta otra
        #     cosa y se puede contestar bien.
        for encaje in re.finditer(
            r"[Vv]iaje|VIAJE", codigo
        ):
            antes = (
                codigo[encaje.start() - 1]
                if encaje.start()
                else " "
            )

            despues = codigo[encaje.end() : encaje.end() + 2]

            es_identificador = (
                antes in "._"
                or antes.isalnum()
                or despues.startswith("_")
                or despues.startswith("s_")
            )

            assert es_identificador, (
                f"{ruta.name} pinta la palabra «viaje», que es "
                f"jerga nuestra: "
                f"...{codigo[max(0, encaje.start() - 40):encaje.end() + 30]}... "
                f"Donde ponga eso, que ponga lo que es: "
                f"«comprado para revender»"
            )

        assert "escaparate tirado" not in codigo, (
            f"{ruta.name} usa una metafora inventada"
        )


def test_el_cartel_dice_lo_que_pasa_en_una_frase() -> None:
    """
    Una frase, con el nombre, cuando se compro en HORA DE MADRID,
    y la consecuencia concreta: que el Computer no ofrecera nada.

    Y sin repetir el titulo: el motivo ya empieza por el nombre.

    LA HORA SE LE PASA (14/09/2026, madrugada)

        Esta guardia paso todo el 13/09 en verde y se puso roja a
        las 00:00 sin que nadie tocara nada: la frase decia "hoy
        a las 10:08" hasta las 23:59 y "ayer a las 10:08" a las
        00:01, porque `_cuando` leia `datetime.now()`.

        NO SE HA AFLOJADO NADA. La comprobacion sigue siendo la
        frase ENTERA, palabra por palabra, incluido el "hoy": esa
        palabra es la que le dice al dueño si el jugador lleva dos
        horas o veintiseis sin publicar, que es de lo que va el
        cartel.

        Lo que ha cambiado es que la hora de referencia entra por
        la puerta, como en `permite_escribir`.
    """

    from src.actions.escaparate_executor import viajes_sin_listar

    # LA FOTO: el 13/09 a las 17:17, la misma que el snapshot de
    # produccion. Fija, escrita aqui, y sin tocar el reloj.
    LA_FOTO = datetime(
        2026, 9, 13, 17, 17, 17, tzinfo=timezone.utc
    )

    visto = viajes_sin_listar(
        [
            {
                "player_id": 37499,
                "name": "Trent",
                "opened_at": "2026-09-13T08:08:00+00:00",
                "cost": 2_760_000,
            }
        ],
        [],
        ahora=LA_FOTO,
    )

    texto = visto["reason"]

    assert texto.startswith("Trent esta comprado para revender"), (
        texto
    )

    assert "no esta a la venta" in texto, texto

    assert "no recibira oferta del Computer" in texto, texto

    # LA HORA, EN MADRID Y EN CRISTIANO.
    #
    #     08:08 UTC son las 10:08 de Madrid. El cartel viejo
    #     enseñaba el 08:08 crudo de la marca de tiempo, que es
    #     la hora de otro sitio.
    assert "hoy a las 10:08" in texto, texto

    assert "2026-09-13T" not in texto, (
        "la fecha sigue en formato de maquina"
    )

    # Y NO SE REPITE. La pantalla no le pone titulo encima.
    from pathlib import Path

    app = (
        Path(__file__).parents[2] / "dashboard-v8" / "src"
        / "App.jsx"
    ).read_text(encoding="utf-8")

    assert "VIAJE COMPRADO Y SIN LISTAR" not in app.replace(
        '"VIAJE COMPRADO Y SIN LISTAR" decia lo mismo dos', ""
    ), "el titulo repetido ha vuelto"

    # NARANJA, NO ROJO: cuesta un dia de escaparate, no puntos.
    trozo = app[
        app.index("sin_listar?.ok === false") : app.index(
            "sin_listar?.ok === false"
        )
        + 200
    ]

    assert 'className="alert warn"' in trozo, (
        "el cartel sigue en rojo: el rojo se reserva para lo que "
        "cuesta puntos o dinero HOY"
    )

    # ========================================================
    # Y LA MISMA FOTO DICE LA MISMA FRASE SIEMPRE.
    # ========================================================
    #
    #     Esto es lo que habria cazado el fallo el 13/09 por la
    #     tarde, en vez de a las 00:00. Se pide el cartel con la
    #     misma foto y horas de referencia repartidas por todo el
    #     dia: si alguna palabra cambia, la frase depende del
    #     reloj.
    from src.actions.escaparate_executor import _cuando

    #     EL DIA ES EL DE MADRID, NO EL DE UTC. En septiembre
    #     Madrid va dos horas por delante, asi que el dia cambia
    #     a las 22:00 UTC. Las horas de abajo se quedan todas
    #     dentro del 13/09 DE MADRID a proposito: 21:59 UTC son
    #     las 23:59 de Madrid, la ultima que sigue siendo "hoy".
    frases = {
        _cuando(
            "2026-09-13T08:08:00+00:00",
            datetime(2026, 9, 13, h, m, tzinfo=timezone.utc),
        )
        for h, m in (
            (6, 30),
            (12, 0),
            (17, 17),
            (21, 0),
            (21, 59),
        )
    }

    assert frases == {"hoy a las 10:08"}, (
        f"la frase cambia segun la hora a la que se pregunte: "
        f"{sorted(frases)}"
    )

    # Y AL DIA SIGUIENTE DICE "AYER", que es lo que tiene que
    # decir: la palabra no sobra, informa de cuanto lleva parado.
    #
    #     22:00 UTC son ya las 00:00 de Madrid: el primer momento
    #     del 14. Es el limite exacto, y se deja escrito porque
    #     si algun dia se compara en UTC este caso lo dira.
    assert _cuando(
        "2026-09-13T08:08:00+00:00",
        datetime(2026, 9, 13, 22, 0, tzinfo=timezone.utc),
    ) == "ayer a las 10:08"

    assert _cuando(
        "2026-09-13T08:08:00+00:00",
        datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc),
    ) == "ayer a las 10:08"

    # SIN REFERENCIA, LA FECHA ENTERA Y NINGUN "HOY".
    #
    #     El respaldo no puede ser mirar el reloj: seria la misma
    #     bomba con otro nombre.
    assert _cuando("2026-09-13T08:08:00+00:00") == (
        "el 13/09 a las 10:08"
    )


def test_ningun_nivel_de_amenaza_cae_al_gris() -> None:
    """
    TERCERA VEZ EL MISMO FALLO.

    `VERY_HIGH` faltaba en el mapa de colores y caia al gris del
    `||`: la amenaza mas alta del tablero se pintaba igual que
    "ninguna". Se arreglo.

    El 13/09 se vio que faltaban OTROS DOS por el mismo motivo:
    `VERY_LOW` y `US`. El rival mas inofensivo y NOSOTROS MISMOS
    salian del color de un desconocido.

    Esta guardia lee los niveles que el MOTOR produce y exige que
    la pantalla tenga color para todos. Ya no hace falta que a
    alguien se le ocurra mirar.
    """

    import re

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    motor = (
        raiz / "src" / "analysis" / "rival_intelligence_engine.py"
    ).read_text(encoding="utf-8")

    # Los niveles, del motor. Se buscan donde se asignan.
    del_motor = set(
        re.findall(
            r'level\s*=\s*\(?\s*"([A-Z_]+)"', motor
        )
    ) | {"US"}

    assert len(del_motor) >= 6, (
        f"solo se han encontrado {del_motor}: si el motor ha "
        f"cambiado como nombra los niveles, esta guardia deja de "
        f"comprobar nada"
    )

    panel = (
        raiz
        / "dashboard-v8"
        / "src"
        / "components"
        / "StandingsIntelPanel.jsx"
    ).read_text(encoding="utf-8")

    mapa = panel[
        panel.index("const THREAT = {") : panel.index(
            "const THREAT = {"
        )
        + 400
    ]

    faltan = [
        nivel
        for nivel in sorted(del_motor)
        if f"{nivel}:" not in mapa
    ]

    assert not faltan, (
        f"la pantalla no tiene color para {faltan}: caen al gris "
        f"por defecto y se pintan igual que «ninguna amenaza»"
    )

    # Y LOS DOS VERDES SE DISTINGUEN.
    #
    #     El dueño pidio VERY_LOW claro y LOW oscuro. El verde
    #     oscuro da 2,21 de contraste sobre el fondo del panel:
    #     no se ve. La pareja aprobada mantiene la intencion —el
    #     mas inofensivo, mas claro— y los dos se leen.
    assert '"pill ok-claro"' in mapa, (
        "VERY_LOW ya no usa el verde claro"
    )

    assert 'LOW: "pill ok"' in mapa, (
        "LOW ya no usa el verde medio"
    )


def test_ningun_color_de_la_amenaza_es_ilegible() -> None:
    """
    NO ES CUESTION DE GUSTO, ES QUE NO SE VE.

    El verde oscuro que se pidio primero da 2,21 de contraste
    sobre el fondo del panel (#111a24). Se midio antes de
    ponerlo, se paro y se pregunto.

    Esta guardia lo mide sola, para que la proxima vez no dependa
    de que a alguien se le ocurra.

    El listón es 3,0 —el minimo de WCAG para texto grande y en
    negrita, que es lo que son estas pildoras—. Por debajo de ahi
    no es un color flojo: es invisible.
    """

    import re

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    css = (
        raiz / "dashboard-v8" / "src" / "styles.css"
    ).read_text(encoding="utf-8")

    jsx = (
        raiz
        / "dashboard-v8"
        / "src"
        / "components"
        / "StandingsIntelPanel.jsx"
    ).read_text(encoding="utf-8")

    FONDO = (17, 26, 36)          # --pan  #111a24

    MINIMO = 3.0

    VARIABLES = {
        "--ok": "#22c55e",
        "--warn": "#eab308",
        "--crit": "#ef4444",
        "--blue": "#3b82f6",
        "--dim": "#7b8794",
    }

    def _lineal(canal):
        canal = canal / 255

        return (
            canal / 12.92
            if canal <= 0.03928
            else ((canal + 0.055) / 1.055) ** 2.4
        )

    def _luz(rgb):
        r, v, a = [_lineal(x) for x in rgb]

        return 0.2126 * r + 0.7152 * v + 0.0722 * a

    def _contraste(a, b):
        la, lb = _luz(a), _luz(b)

        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    def _hex(texto):
        texto = texto.lstrip("#")

        return tuple(
            int(texto[i : i + 2], 16) for i in (0, 2, 4)
        )

    def _sobre(color, alfa, fondo):
        return tuple(
            round(fondo[i] * (1 - alfa) + color[i] * alfa)
            for i in range(3)
        )

    trozo = jsx[
        jsx.index("const THREAT = {") : jsx.index(
            "};", jsx.index("const THREAT = {")
        )
    ]

    niveles = re.findall(r'(\w+):\s*"pill ([\w-]+)"', trozo)

    assert len(niveles) >= 6, niveles

    flojos = []

    for nivel, clase in niveles:

        regla = re.search(
            r"\.pill\."
            + re.escape(clase)
            + r"[,{][^}]*background:rgba\(([\d.,\s]+)\)"
            r";color:(var\(--\w+\)|#[0-9a-fA-F]{6})",
            css,
        )

        assert regla, (
            f"`pill {clase}` no tiene regla de color: "
            f"{nivel} se pintaria con el estilo base"
        )

        partes = [
            float(x) for x in regla.group(1).split(",")
        ]

        color = regla.group(2)

        if color.startswith("var("):
            color = VARIABLES[color[4:-1]]

        fondo = _sobre(
            tuple(int(x) for x in partes[:3]),
            partes[3],
            FONDO,
        )

        visto = _contraste(_hex(color), fondo)

        if visto < MINIMO:
            flojos.append(f"{nivel} ({color}): {visto:.2f}")

    assert not flojos, (
        "estos colores no se leen sobre el fondo del panel: "
        + " · ".join(flojos)
        + ". No es cuestion de gusto: por debajo de "
        f"{MINIMO} el texto es invisible."
    )


def test_la_racha_se_lee_y_no_se_estima() -> None:
    """
    250.000 EUR POR ACORDARSE DE PULSAR UN BOTON.

    Medido sobre 34 dias del tablon: Pollo17 cobro 750.000 de
    racha diaria y nosotros 250.000. Medio millon de diferencia.

    SE LEE, NO SE ESTIMA. Biwenger la publica en la CUENTA
    —`account.dailyStreak`, un 0-5— y asi la lee su propia app.
    Confirmado contra la API el 13/09: GET /api/v2/account
    devuelve `data.account.dailyStreak`.

    NO se deduce de `lastAccess` ni de los eventos `bonus`: un
    contador que finge saber es peor que no tenerlo, porque se
    confia en el y se pierden los 250.000.
    """

    import re

    from pathlib import Path

    raiz = Path(__file__).parents[2]

    colector = (
        raiz / "src" / "collectors" / "league_collector.py"
    ).read_text(encoding="utf-8")

    codigo = chr(10).join(
        linea
        for linea in colector.splitlines()
        if not linea.strip().startswith("#")
    )

    assert "get_account()" in codigo, (
        "el colector no pide la cuenta: la racha no puede venir "
        "de ningun otro sitio"
    )

    assert '"dailyStreak"' in codigo or (
        'get("dailyStreak")' in codigo
    ), "no se lee `dailyStreak`"

    assert '"daily_streak"' in codigo, (
        "la racha no viaja en la foto"
    )

    # Y NO SE DEDUCE de otra cosa.
    for inventada in ("lastAccess", "bonus"):
        assert inventada not in codigo, (
            f"la racha se esta deduciendo de `{inventada}` en vez "
            f"de leerse"
        )

    # LA PANTALLA: el numero, y "SIN MEDIR" si no viene.
    app = (
        raiz / "dashboard-v8" / "src" / "App.jsx"
    ).read_text(encoding="utf-8")

    assert "daily_streak" in app, "la pantalla no lee la racha"

    assert "RACHA SIN MEDIR" in app, (
        "sin dato la pantalla no dice «sin medir»: pintaria un "
        "numero inventado"
    )

    # 5/5 EN ROJO: hay 250.000 esperando a que alguien canjee.
    assert "freshness cobrar" in app, (
        "la racha no se pone en rojo al llegar a 5"
    )

    estilos = (
        raiz / "dashboard-v8" / "src" / "styles.css"
    ).read_text(encoding="utf-8")

    assert ".freshness.cobrar" in estilos, (
        "falta el estilo de la pildora roja"
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
    test_la_hora_declarada_manda_en_el_silencio,
    test_el_filtro_es_el_suelo_no_el_cero,
    test_un_viaje_sin_coste_no_se_cobra,
    test_la_pantalla_no_habla_en_jerga,
    test_ningun_nivel_de_amenaza_cae_al_gris,
    test_ningun_color_de_la_amenaza_es_ilegible,
    test_la_racha_se_lee_y_no_se_estima,
    test_el_cartel_dice_lo_que_pasa_en_una_frase,
    test_el_coste_se_guarda_cuando_se_puede_probar,
    test_la_prueba_de_humo_es_de_cupo_no_de_suelo,
    test_al_completar_un_viaje_vuelve_todo_a_su_sitio,
    test_los_baratos_usan_la_prima_de_su_tramo,
    test_la_via_vieja_esta_en_pausa,
    test_pausar_no_cambia_la_forma,
    test_el_tope_se_pregunta_al_elegir_no_al_pagar,
    test_el_carril_filtra_por_el_tope_antes_de_elegir,
    test_el_suelo_vive_en_un_sitio,
    test_la_pantalla_dice_el_suelo_y_los_viajes,
    test_el_carril_tiene_bolsillo_propio_en_euros,
    test_el_bolsillo_no_puede_gastar_lo_que_no_hay,
    test_el_bolsillo_propio_manda_al_elegir,
    test_un_viaje_de_tres_millones_no_rompe_la_solvencia,
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
