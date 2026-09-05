"""
Que la venta se ejecute. El camino entero, de punta a punta.

SINTOMA

    `ACCEPT_RECOVERY_OFFER` no se ha disparado ni una vez. En las
    34 horas de registro de produccion del 04-05/09/2026 hay
    veinte escrituras -doce renovaciones, cuatro rechazos, dos
    alineaciones, una compra y una publicacion- y ninguna venta
    cobrada.

    Y `accept_offer` no ha devuelto un 200 desde que se le
    arreglo el cuerpo el 19/08. No parece que falle: su gemelo
    `reject_offer` usa el MISMO `PUT /offers/{id}` con el mismo
    `{"status": ...}` y devuelve 200 cuatro veces al dia. Pero
    "no parece que falle" no es una demostracion, y lo que se
    compra con la demostracion es autorizacion para endeudarse.

CAUSA

    El camino tiene siete tramos y cada uno lo escribio otra
    noche:

        1. la oferta se reserva para solvencia
        2. `analyze_computer_offer` -> ACCEPT_BEFORE_EXPIRY
        3. `decide_incoming_offer`  -> ACCEPT_FOR_SOLVENCY
        4. `offers_to_collect`      -> la deja pasar
        5. el orquestador emite     -> ACCEPT_RECOVERY_OFFER
        6. la barrera temporal      -> no la bloquea
        7. el executor llama        -> writer.accept_offer

    Ninguna prueba recorria los siete. Habia pruebas de tramos
    sueltos, y el 18/08 se descubrio que cinco paredes seguidas
    estaban bien y ninguna llegaba al gatillo.

CONSECUENCIA

    Esta guardia recorre los siete tramos con un cliente de
    escritura falso, y comprueba lo ultimo que se puede
    comprobar sin vender de verdad: que sale un
    `PUT /api/v2/offers/{id}` con `{"status": "accepted"}`
    dentro.

    Es lo que el encargo del 12/09 acepta como demostracion:
    "una prueba que recorra el camino entero hasta el cliente de
    escritura".

NO VENDE NADA

    El cliente esta suplantado. Si algun dia esta prueba tocase
    la red de verdad, `test_el_cliente_falso_es_falso` lo dice.
"""

from __future__ import annotations

import json

from pathlib import Path

from src.actions import autopilot_executor

from src.analysis.decision_orchestrator import offers_to_collect

from src.analysis.offer_decision_engine import decide_incoming_offer

from src.analysis.computer_offer_reroll_engine import (
    ACCEPT_BEFORE_DEADLINE_HOURS,
    ACCEPT_BEFORE_EXPIRY_HOURS,
)


FOTO = Path("diagnostico/status.json")


# ============================================================
# EL CLIENTE FALSO
# ============================================================
#
#     Suplanta la sesion HTTP, no el cliente entero. Asi se
#     ejercita `build_accept_offer_request`, `_evaluate_success`
#     y el paso del cuerpo: justo las tres cosas que fallaron.


class RespuestaFalsa:

    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self):
        if self._payload is None:
            raise ValueError("sin cuerpo")
        return self._payload


class SesionFalsa:

    def __init__(self):
        self.llamadas = []

    def put(self, url, json=None, timeout=None):     # noqa: A002
        self.llamadas.append(
            {
                "method": "PUT",
                "url": url,
                "json": json,
                "timeout": timeout,
            }
        )

        return RespuestaFalsa(
            200,
            {"status": 200, "offer": {"status": "processed"}},
        )

    def post(self, *args, **kwargs):
        raise AssertionError(
            "aceptar una oferta no puede acabar en un POST"
        )


class ClienteFalso:
    """
    La URL base es la DE VERDAD, sacada del cliente real. Si se
    inventase aqui, la prueba comprobaria una URL que no existe.
    """

    def __init__(self):
        from src.biwenger.client import BiwengerClient

        self.BASE_URL = BiwengerClient.BASE_URL
        self.session = SesionFalsa()


class WriterFalso:
    """
    El cliente de escritura de verdad, con la sesion cambiada.
    """

    def __new__(cls):
        from src.biwenger.write_client import BiwengerWriteClient

        # Se salta `__init__` a proposito: ahi dentro hay un
        # login real contra Biwenger. Se rellena a mano lo que la
        # ruta de aceptar una oferta necesita, y NADA MAS: si
        # manana usa otro campo, la prueba peta en vez de mentir.
        writer = object.__new__(BiwengerWriteClient)

        writer.client = ClienteFalso()
        writer.version = "0.0-test"
        writer.league_id = 2165477
        writer.user_id = 14175949

        WriterFalso.ultimo = writer

        return writer


def _con_writer_falso(funcion):
    """
    Suplanta `BiwengerWriteClient` DENTRO del executor y lo deja
    como estaba, pase lo que pase.
    """

    original = autopilot_executor.BiwengerWriteClient

    autopilot_executor.BiwengerWriteClient = WriterFalso

    try:
        return funcion()

    finally:
        autopilot_executor.BiwengerWriteClient = original


# ============================================================
# LA SITUACION: DEFICIT, OFERTA RESERVADA Y LA JORNADA ENCIMA
# ============================================================
#
#     Los numeros son los de produccion del 05/09: deficit de
#     421.792 y la oferta de Lucas Cepeda, 471.200, que es el
#     plan A del motor de solvencia.


DEFICIT = 421_792

OFERTA = {
    "offer_id": 987654,
    "player_id": 39874,
    "player_name": "Lucas Cepeda",
    "amount": 471_200,
    "market_value": 480_000,
    "premium_percent": -1.8,
    "counterparty": {"type": "COMPUTER"},
    "hours_to_expiry": 40.9,
}


def _reroll(action: str) -> dict:
    return {
        "action": action,
        "solvency_reserved": True,
        "reroll_safe": False,
        "reroll_count": 0,
    }


def _decide(reroll_action: str) -> dict:
    return decide_incoming_offer(
        offer=OFERTA,
        roster={
            "sale_score": 65.0,
            "protection": "SELLABLE",
            "in_lineup": False,
            "price_increment": 0,
        },
        strategic={},
        speculation={},
        reroll_offer=_reroll(reroll_action),
        recovery_selected_offer_ids=set(),
    )


# ============================================================
# TRAMO 3: LA DECISION DE COBRAR EXISTE
# ============================================================


def test_con_la_jornada_encima_la_oferta_reservada_se_cobra() -> None:
    """
    Es la unica puerta del Computer hacia aceptar, y estaba
    escrita desde el 18/08. Lo que no habia era una prueba de que
    llegase a algun sitio.
    """

    decision = _decide("ACCEPT_BEFORE_EXPIRY")

    assert decision["decision"] == "ACCEPT_FOR_SOLVENCY", (
        f"una oferta reservada con la jornada encima no se cobra: "
        f"{decision['decision']}"
    )


def test_sin_presion_la_misma_oferta_se_conserva() -> None:
    """
    Y lejos del plazo NO se cobra, que es igual de importante:
    malvender con tiempo por delante es la otra forma de perder.
    """

    decision = _decide("KEEP_SOLVENCY_RESERVED")

    assert decision["decision"] == "HOLD_SOLVENCY_RESERVED", (
        f"la reserva se pierde en silencio: {decision['decision']}"
    )


# ============================================================
# TRAMO 4: EL FILTRO LA DEJA PASAR
# ============================================================


def test_la_oferta_aprobada_llega_a_la_cola_de_cobro() -> None:
    decision = _decide("ACCEPT_BEFORE_EXPIRY")

    cobrables = offers_to_collect(
        [decision],
        position_floor={39874: False},
    )

    assert cobrables, (
        "la oferta aprobada no llega a la cola de cobro"
    )

    assert cobrables[0]["offer_id"] == OFERTA["offer_id"]


def test_el_ultimo_de_su_posicion_no_se_cobra() -> None:
    """
    Cobrar 471.200 por el unico portero es un mal negocio aunque
    la prima sea buena: el domingo no hay a quien alinear.
    """

    decision = _decide("ACCEPT_BEFORE_EXPIRY")

    assert not offers_to_collect(
        [decision],
        position_floor={39874: True},
    )


# ============================================================
# TRAMOS 6 Y 7: LA BARRERA TEMPORAL Y EL GATILLO
# ============================================================


def _decision_de_ciclo(temporal_gate: dict | None = None) -> dict:
    return {
        "action": "ACCEPT_RECOVERY_OFFER",
        "executable": True,
        "executor": "AUTOPILOT",
        "temporal_gate": temporal_gate
        or {
            "phase": "HIGH_ATTENTION",
            "operations_locked": False,
            "hard_safety_mode": False,
        },
        "data": {
            "offer": {
                "offer_id": OFERTA["offer_id"],
                "player_name": OFERTA["player_name"],
                "amount": OFERTA["amount"],
                "protection": "SELLABLE",
            }
        },
    }


def test_el_camino_entero_acaba_en_un_put_con_cuerpo() -> None:
    """
    LA PRUEBA QUE PEDIA EL ENCARGO

        El bug del 19/08 era exactamente este: `accept_offer`
        hacia un PUT pelado a /offers/{id} y Biwenger contestaba
        500. Aqui se comprueba lo que sale por el cable.
    """

    resultado = _con_writer_falso(
        lambda: autopilot_executor.execute_autopilot_decision(
            _decision_de_ciclo(),
            execute=True,
        )
    )

    assert resultado["write_performed"] is True, resultado
    assert resultado["success"] is True, resultado
    assert resultado["status"] == "OFFER_ACCEPTED", resultado
    assert resultado["http_status"] == 200, resultado

    llamadas = WriterFalso.ultimo.client.session.llamadas

    assert len(llamadas) == 1, (
        f"se esperaba UNA escritura y hubo {len(llamadas)}"
    )

    llamada = llamadas[0]

    assert llamada["method"] == "PUT"

    assert llamada["url"].endswith(f"/offers/{OFERTA['offer_id']}"), (
        f"la URL no es la del endpoint de ofertas: {llamada['url']}"
    )

    assert llamada["json"] == {"status": "accepted"}, (
        f"el cuerpo que se manda no es el que Biwenger espera: "
        f"{llamada['json']}. Era exactamente el bug del 19/08."
    )


def test_en_observador_no_se_escribe() -> None:
    """
    `execute=False` no puede tocar la red. Es el modo en el que
    corre el dashboard.
    """

    resultado = _con_writer_falso(
        lambda: autopilot_executor.execute_autopilot_decision(
            _decision_de_ciclo(),
            execute=False,
        )
    )

    assert resultado["write_performed"] is False
    assert resultado["status"] == "DRY_RUN"


def test_la_barrera_temporal_para_la_venta_con_la_jornada_cerrada() -> None:
    """
    Y esto es lo que hay que mirar con lupa: la barrera temporal
    bloquea TODA escritura cuando `operations_locked`, sin
    excepciones.

    Con la regla nueva del dueño -en positivo a T-6h- eso ya no
    choca: `ROUND_LOCKED` empieza a T-15 MINUTOS del primer
    partido, no a T-6h. Hay seis horas largas de margen entre el
    plazo de solvencia y el cierre de escrituras.

    Pero si alguien mueve el bloqueo hacia atras, la venta de
    solvencia deja de poder ejecutarse y nada lo avisa. Por eso
    esta escrito aqui.
    """

    resultado = _con_writer_falso(
        lambda: autopilot_executor.execute_autopilot_decision(
            _decision_de_ciclo(
                {
                    "phase": "ROUND_LOCKED",
                    "operations_locked": True,
                    "hard_safety_mode": True,
                }
            ),
            execute=True,
        )
    )

    assert resultado["write_performed"] is False
    assert resultado["status"] == "TEMPORAL_LOCK"


def test_en_hard_safety_la_venta_si_esta_autorizada() -> None:
    """
    Hard Safety apaga casi todo, y a proposito deja pasar lo que
    genera liquidez. Si algun dia se le quita
    `ACCEPT_RECOVERY_OFFER`, Pepe se quedaria sin poder salir de
    rojo justo cuando mas falta le hace.
    """

    assert (
        "ACCEPT_RECOVERY_OFFER"
        in autopilot_executor.HARD_SAFETY_ALLOWED_ACTIONS
    )

    resultado = _con_writer_falso(
        lambda: autopilot_executor.execute_autopilot_decision(
            _decision_de_ciclo(
                {
                    "phase": "HARD_SAFETY",
                    "operations_locked": False,
                    "hard_safety_mode": True,
                }
            ),
            execute=True,
        )
    )

    assert resultado["write_performed"] is True, resultado
    assert resultado["status"] == "OFFER_ACCEPTED", resultado


def test_un_protegido_no_se_vende_ni_llegando_hasta_aqui() -> None:
    """
    Cinturon sobre los tirantes: el orquestador ya lo filtra, y
    el executor vuelve a mirarlo.
    """

    decision = _decision_de_ciclo()
    decision["data"]["offer"]["protection"] = "NEVER_AUTO_SELL"

    resultado = _con_writer_falso(
        lambda: autopilot_executor.execute_autopilot_decision(
            decision,
            execute=True,
        )
    )

    assert resultado["write_performed"] is False
    assert resultado["status"] == "BLOCKED_PROTECTED_PLAYER"


# ============================================================
# LOS DOS PLAZOS QUE HACEN QUE ESTO OCURRA
# ============================================================


def test_el_plazo_de_solvencia_son_seis_horas() -> None:
    """
    "Con estar en positivo 6 horas antes del inicio de jornada es
    suficiente."

    Los dos plazos ya estaban escritos y valen 6. No se tocan: se
    fijan aqui para que nadie los mueva sin querer.
    """

    assert ACCEPT_BEFORE_DEADLINE_HOURS == 6.0
    assert ACCEPT_BEFORE_EXPIRY_HOURS == 6.0


def test_el_cliente_falso_es_falso() -> None:
    """
    Si esta prueba llegase a tocar la red de verdad, esto lo
    dice: el writer suplantado no tiene credenciales ni sesion
    real.
    """

    writer = WriterFalso()

    assert isinstance(writer.client, ClienteFalso)
    assert isinstance(writer.client.session, SesionFalsa)

    assert autopilot_executor.BiwengerWriteClient is not WriterFalso, (
        "el executor se ha quedado con el cliente falso puesto"
    )


def test_se_cobra_la_mas_pequeña_que_tapa_el_agujero() -> None:
    """
    MEDIDO EN PRODUCCION EL 05/09

        Deficit de 421.792 y la oferta reservada para taparlo era
        la de Gustavo Puerta: 3.377.100. Ocho veces lo que hacia
        falta, y ademas es el plan C del motor de solvencia — el
        que deja el once incompleto. El plan A era Lucas Cepeda
        por 471.200, sin tocar el once.

        La reserva elige por prima, que es razonable para el
        precio y ciego para el tamaño. Entre ofertas ya
        aprobadas, se cobra la mas pequeña que tape el agujero:
        es el mismo criterio que la cola de venta del 11/09.
    """

    grande = {
        "decision": "ACCEPT_FOR_SOLVENCY",
        "offer_id": 1,
        "player_id": 41271,
        "amount": 3_377_100,
        "premium_percent": -0.7,
    }

    justa = {
        "decision": "ACCEPT_FOR_SOLVENCY",
        "offer_id": 2,
        "player_id": 39874,
        "amount": 471_200,
        "premium_percent": -1.8,
    }

    cobrables = offers_to_collect(
        [grande, justa],
        deficit=DEFICIT,
    )

    assert cobrables[0]["offer_id"] == justa["offer_id"], (
        f"se cobra {cobrables[0]['amount']:,} para tapar un "
        f"agujero de {DEFICIT:,}: se esta vendiendo de mas"
    )


def test_si_ninguna_tapa_se_coge_la_mas_grande() -> None:
    """
    La que mas se acerca. Media solvencia es mejor que ninguna.
    """

    cobrables = offers_to_collect(
        [
            {
                "decision": "ACCEPT_FOR_SOLVENCY",
                "offer_id": 1,
                "player_id": 1,
                "amount": 300_000,
            },
            {
                "decision": "ACCEPT_FOR_SOLVENCY",
                "offer_id": 2,
                "player_id": 2,
                "amount": 400_000,
            },
        ],
        deficit=5_000_000,
    )

    assert cobrables[0]["amount"] == 400_000


def test_sin_deficit_el_orden_es_el_de_siempre() -> None:
    """
    Cobrar sin necesitar el dinero se decide por prima, como
    hasta hoy. El criterio nuevo solo aparece con el saldo en
    rojo.
    """

    cobrables = offers_to_collect(
        [
            {
                "decision": "ACCEPT_NOW",
                "offer_id": 1,
                "player_id": 1,
                "amount": 300_000,
                "premium_percent": 1.0,
            },
            {
                "decision": "ACCEPT_NOW",
                "offer_id": 2,
                "player_id": 2,
                "amount": 3_000_000,
                "premium_percent": 4.0,
            },
        ]
    )

    assert cobrables[0]["premium_percent"] == 4.0


TESTS = [
    test_con_la_jornada_encima_la_oferta_reservada_se_cobra,
    test_sin_presion_la_misma_oferta_se_conserva,
    test_la_oferta_aprobada_llega_a_la_cola_de_cobro,
    test_el_ultimo_de_su_posicion_no_se_cobra,
    test_se_cobra_la_mas_pequeña_que_tapa_el_agujero,
    test_si_ninguna_tapa_se_coge_la_mas_grande,
    test_sin_deficit_el_orden_es_el_de_siempre,
    test_el_camino_entero_acaba_en_un_put_con_cuerpo,
    test_en_observador_no_se_escribe,
    test_la_barrera_temporal_para_la_venta_con_la_jornada_cerrada,
    test_en_hard_safety_la_venta_si_esta_autorizada,
    test_un_protegido_no_se_vende_ni_llegando_hasta_aqui,
    test_el_plazo_de_solvencia_son_seis_horas,
    test_el_cliente_falso_es_falso,
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
    print(f"VENTA EJECUTABLE V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
