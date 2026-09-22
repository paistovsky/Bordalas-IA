"""
La vuelta se apunta entera: las que pierden, y lo que costo.

DE DONDE SALE (22/09/2026)

    `append_log` guarda la ganadora y nada mas. Para contestar
    "¿cuantas veces la puja perdio la escritura?" hubo que
    reconstruir nueve vueltas pasando otra vez
    `build_global_decision` por fotos viejas: 86 segundos cada
    una, y con el codigo de hoy sobre datos de entonces. Habrian
    sido nueve lineas de un fichero.

    Y `peticiones.resumen()` dice de si mismo "para publicarlo" y
    solo se imprime: el unico aviso antes del proximo 429 es que
    alguien estuviera mirando la consola.

LO QUE SE PROTEGE

    1. Que apagado la linea del log sea la de hoy, sin un campo
       de mas.
    2. Que encendido esten TODAS las candidatas, no solo la
       ganadora.
    3. Que se pueda saber CUAL gano sin cruzar con otro campo.
    4. Que se marque cual de ellas escribe, que es la pregunta
       que se va a hacer.
    5. Que el motivo recortado se marque como recortado.
    6. Que el recuento de peticiones viaje en la misma linea.
    7. Que lo que ocupa se pueda medir, no estimar.
    8. Que la forma no cambie con los datos.
    9. Que el modulo no lea el mundo.

ESTAS GUARDIAS NO LEEN EL MUNDO

    Ni `data/`, ni red, ni reloj: las candidatas y el recuento se
    pasan. La unica que toca el entorno es la del interruptor
    —que ES una variable de entorno— y lo deja como estaba.

COMO SE USA

    python -m src.analysis.test_la_vuelta_se_apunta_v1
"""

from __future__ import annotations

import os


# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104)
os.environ.pop("BORDALAS_LA_VUELTA_SE_APUNTA", None)

import json                                         # noqa: E402

from src.analysis.la_vuelta_se_apunta import (       # noqa: E402
    ENV as APUNTA_ENV,
    ESCRIBEN,
    MOTIVO_MAXIMO,
    cuanto_ocupa,
    la_cola,
    lo_que_costo,
)


class _Interruptor:
    """Pone y quita una variable, y la deja como estaba."""

    def __init__(self, nombre, valor="1"):
        self.nombre = nombre
        self.valor = valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes
        return False


# La cola del 13/09 reconstruida, que es un caso real: gana un
# tramite y hay una puja detras.
def _cola_real() -> list:
    return [
        {
            "action": "RENEW_MARKET_LISTING",
            "type": "MARKET_LISTING_RENEW",
            "priority": 690,
            "executable": True,
            "reason": "R" * (MOTIVO_MAXIMO + 150),
        },
        {
            "action": "ACCEPT_RECOVERY_OFFER",
            "type": "INCOMING_OFFERS",
            "priority": 650,
            "executable": True,
            "reason": "corto",
        },
        {
            "action": "BUY_SPECULATION",
            "type": "SPECULATION_BUY",
            "priority": 400,
            "executable": True,
            "reason": "la puja que pierde",
        },
        {
            "action": "MONITOR_SOLVENCY",
            "type": "SOLVENCY_GUARANTEE",
            "priority": 500,
            "executable": False,
            "reason": "no escribe",
        },
        {
            "action": "WAIT",
            "type": "IDLE",
            "priority": 0,
            "executable": False,
            "reason": "nada que hacer",
        },
    ]


def _recuento() -> dict:
    return {
        "available": True,
        "total": 19,
        "unique_endpoints": 14,
        "repeated": 5,
        "repeated_percent": 26.3,
        "rate_limited": 0,
        "waited_seconds": 0.0,
        "by_endpoint": {f"/e{i}": 20 - i for i in range(30)},
    }


# ============================================================
# 1. APAGADO, LA LINEA ES LA DE HOY
# ============================================================

def test_apagado_la_linea_no_cambia():
    """
    Un interruptor apagado que añade un campo no esta apagado.
    """

    assert os.environ.get(APUNTA_ENV) is None

    assert la_cola(_cola_real(), _cola_real()[0]) == []
    assert lo_que_costo(_recuento()) == {}

    # Y encendido SI añade: sin esto lo de arriba pasaria aunque
    # el interruptor no hiciera nada (doctrina 24).
    with _Interruptor(APUNTA_ENV):
        assert la_cola(_cola_real(), _cola_real()[0])
        assert lo_que_costo(_recuento())


# ============================================================
# 2. ESTAN TODAS, NO SOLO LA GANADORA
# ============================================================

def test_se_apuntan_las_que_pierden():
    """
    Es el encargo entero: la ganadora ya estaba.
    """

    candidatas = _cola_real()

    ganadora = candidatas[0]

    perdedoras = [c for c in candidatas if c is not ganadora]

    assert perdedoras, (
        "el caso no trae ninguna perdedora: esta guardia no "
        "estaria midiendo nada"
    )

    with _Interruptor(APUNTA_ENV):
        cola = la_cola(candidatas, ganadora)

    assert len(cola) == len(candidatas), (
        f"se apuntan {len(cola)} de {len(candidatas)}"
    )

    apuntadas = {f["action"] for f in cola}

    for c in perdedoras:
        assert c["action"] in apuntadas, (
            f"{c['action']} perdio y no se ha apuntado"
        )

    # Y con su prioridad, que es lo que permite contestar la
    # pregunta sin volver a ejecutar nada.
    for f in cola:
        assert f["priority"] is not None
        assert "executable" in f


# ============================================================
# 3. SE SABE CUAL GANO, SIN CRUZAR NADA
# ============================================================

def test_la_ganadora_va_marcada():

    candidatas = _cola_real()

    with _Interruptor(APUNTA_ENV):
        cola = la_cola(candidatas, candidatas[0])

    ganadoras = [f for f in cola if f["won"]]

    assert len(ganadoras) == 1, (
        f"marcadas {len(ganadoras)} ganadoras"
    )
    assert ganadoras[0]["action"] == "RENEW_MARKET_LISTING"

    # Sin ganadora no se inventa una.
    with _Interruptor(APUNTA_ENV):
        sin = la_cola(candidatas, None)

    assert not any(f["won"] for f in sin), (
        "sin ganadora se ha marcado alguna"
    )


# ============================================================
# 4. SE MARCA CUAL ESCRIBE
# ============================================================

def test_se_marca_cual_consume_la_escritura():
    """
    Es LA pregunta que se va a hacer leyendo esto. Deducirla
    despues obliga a mantener la lista en dos sitios.
    """

    candidatas = _cola_real()

    escriben = [
        c for c in candidatas if c["action"] in ESCRIBEN
    ]

    no_escriben = [
        c for c in candidatas if c["action"] not in ESCRIBEN
    ]

    assert escriben and no_escriben, (
        "el caso necesita de las dos clases para probar que las "
        "distingue"
    )

    with _Interruptor(APUNTA_ENV):
        cola = la_cola(candidatas, candidatas[0])

    por_accion = {f["action"]: f for f in cola}

    for c in escriben:
        assert por_accion[c["action"]]["writes"] is True, (
            f"{c['action']} escribe y no esta marcada"
        )

    for c in no_escriben:
        assert por_accion[c["action"]]["writes"] is False, (
            f"{c['action']} no escribe y esta marcada"
        )

    # Y la lista de las que escriben es la del ejecutor, no una
    # copia a mano: se ejercita contra sus constantes.
    from src.actions.autopilot_executor import (
        ACCEPT_EXPIRY_ACTION,
        RENEW_LISTING_ACTION,
        REROLL_ACTION,
        SPECULATION_BUY_ACTION,
    )

    for accion in (
        ACCEPT_EXPIRY_ACTION,
        RENEW_LISTING_ACTION,
        REROLL_ACTION,
        SPECULATION_BUY_ACTION,
        "LIST_FOR_LIQUIDITY",
        "ACCEPT_RECOVERY_OFFER",
        "SAVE_LINEUP",
    ):
        assert accion in ESCRIBEN, (
            f"{accion} escribe en el ejecutor y no esta en "
            f"`ESCRIBEN`"
        )


# ============================================================
# 5. UN MOTIVO CORTADO SE DICE CORTADO
# ============================================================

def test_el_motivo_cortado_se_marca():
    """
    Un texto cortado sin avisar se lee como si estuviera entero.
    """

    candidatas = _cola_real()

    largo = candidatas[0]

    assert len(largo["reason"]) > MOTIVO_MAXIMO, (
        "el caso no trae ningun motivo largo que cortar"
    )

    corto = candidatas[1]

    assert len(corto["reason"]) <= MOTIVO_MAXIMO, (
        "el caso no trae ningun motivo corto: no probaria que "
        "solo se marca el que se corta"
    )

    with _Interruptor(APUNTA_ENV):
        cola = la_cola(candidatas, None)

    por_accion = {f["action"]: f for f in cola}

    cortada = por_accion[largo["action"]]

    assert cortada["reason_truncated"] is True
    assert len(cortada["reason"]) == MOTIVO_MAXIMO

    entera = por_accion[corto["action"]]

    assert "reason_truncated" not in entera
    assert entera["reason"] == corto["reason"]


# ============================================================
# 6. LO QUE COSTO LA VUELTA, EN LA MISMA LINEA
# ============================================================

def test_el_recuento_de_peticiones_viaja_con_la_vuelta():

    with _Interruptor(APUNTA_ENV):
        coste = lo_que_costo(_recuento())

    assert coste["total"] == 19
    assert coste["repeated"] == 5
    assert coste["rate_limited"] == 0

    # La cola larga de endpoints no se guarda entera.
    assert len(coste["by_endpoint"]) == 12, (
        f"se guardan {len(coste['by_endpoint'])} endpoints"
    )

    # Un recuento que no esta disponible no se inventa.
    with _Interruptor(APUNTA_ENV):
        assert lo_que_costo({"available": False}) == {}
        assert lo_que_costo(None) == {}


# ============================================================
# 7. LO QUE OCUPA SE MIDE
# ============================================================

def test_lo_que_ocupa_se_mide_y_no_se_estima():
    """
    Doctrina 90: un numero que recibes tambien necesita su
    medicion. El tamaño de esto decide si el fichero puede ir a
    git, asi que se mide, no se calcula a ojo.
    """

    with _Interruptor(APUNTA_ENV):
        cola = la_cola(_cola_real(), _cola_real()[0])
        coste = lo_que_costo(_recuento())
        bytes_ = cuanto_ocupa(cola, coste)

    esperado = len(
        json.dumps(
            {"decision_candidates": cola, "requests": coste},
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    )

    assert bytes_ == esperado, (
        f"dice {bytes_} y son {esperado}"
    )

    assert bytes_ > 0

    # Y apagado no ocupa nada.
    assert cuanto_ocupa([], {}) == len(b'{"decision_candidates": [], "requests": {}}')


# ============================================================
# 8. LA FORMA NO CAMBIA CON LOS DATOS
# ============================================================

def test_la_forma_no_cambia_con_los_datos():

    casos = [
        (None, None),
        ([], {}),
        (["basura", 7, None], "basura"),
        ([{"action": "X"}], {"action": "X"}),
        (_cola_real(), _cola_real()[2]),
    ]

    for candidatas, ganadora in casos:
        for encendido in (False, True):

            if encendido:
                with _Interruptor(APUNTA_ENV):
                    cola = la_cola(candidatas, ganadora)
                    coste = lo_que_costo(candidatas)
            else:
                cola = la_cola(candidatas, ganadora)
                coste = lo_que_costo(candidatas)

            assert isinstance(cola, list)
            assert isinstance(coste, dict)

            for f in cola:
                for campo in (
                    "order",
                    "action",
                    "priority",
                    "executable",
                    "writes",
                    "won",
                    "reason",
                ):
                    assert campo in f, (
                        f"falta `{campo}` con {candidatas!r}"
                    )

            json.dumps({"c": cola, "r": coste}, default=str)


# ============================================================
# 9. NO LEE EL MUNDO
# ============================================================

def test_la_vuelta_se_apunta_no_lee_el_mundo():

    import inspect

    from src.analysis import la_vuelta_se_apunta

    fuente = inspect.getsource(la_vuelta_se_apunta)

    for prohibido in (
        "open(",
        "Path(",
        "requests.",
        "urllib",
        "datetime.now",
        "time.time",
        "json.load",
    ):
        assert prohibido not in fuente, (
            f"`la_vuelta_se_apunta` usa `{prohibido}`: lo que "
            f"registra una vuelta no puede salir a buscarla"
        )


# ============================================================
# EL CORREDOR
# ============================================================

TESTS = [
    test_apagado_la_linea_no_cambia,
    test_se_apuntan_las_que_pierden,
    test_la_ganadora_va_marcada,
    test_se_marca_cual_consume_la_escritura,
    test_el_motivo_cortado_se_marca,
    test_el_recuento_de_peticiones_viaja_con_la_vuelta,
    test_lo_que_ocupa_se_mide_y_no_se_estima,
    test_la_forma_no_cambia_con_los_datos,
    test_la_vuelta_se_apunta_no_lee_el_mundo,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA VUELTA SE APUNTA V1")
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
