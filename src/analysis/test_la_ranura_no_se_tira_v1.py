"""
LA RANURA NO SE TIRA (12/10/2026). Guardias de
`decision_orchestrator.los_que_se_pueden_publicar` y de
`autopilot_executor.resultado_de_publicar`.

LO QUE PASO

    Del 02/10 14:09 al 12/10 13:09, 36 «FAILED Publicacion de Yamal»
    en el autopilot_log. LIST_FOR_LIQUIDITY publicaba `to_list[0]`
    (Yamal, en `proteger`), el escritor lo frenaba sin enviar nada, y
    el executor devolvia `write_performed: True`: la unica escritura
    de la vuelta, tirada. Olasagasti, el siguiente, nunca se publico.

QUE SE PRUEBA

    1. Un protegido nunca es el que se publica: el siguiente sin
       proteger pasa a ser el primero, y si no queda ninguno no hay
       candidata.
    2. Con la orden real (`proteger` + `fichar` + `conservar`) se
       quitan proteger y fichar; `conservar` se sigue publicando,
       porque el escritor no lo frena.
    3. La misma puerta que el escritor: lo que el filtro quita es
       exactamente lo que `list_player_for_sale` frena.
    4. El orquestador filtra ANTES de las dos publicaciones (saldo
       negativo y mantenimiento).
    5. Una publicacion frenada no es una escritura: ni para el
       backoff, ni para la regla de una escritura por ciclo, ni para
       V10. Una enviada (bien o mal) y el ensayo siguen igual.
    6. El executor entero, con un escritor de mentira, devuelve
       write_performed False si el escritor frena.
    7. Nunca lanza.

    Sin red, sin login, sin reloj real y sin disco de produccion.
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import tempfile

from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.actions.autopilot_executor as executor_mod      # noqa: E402
import src.actions.la_orden_del_gestor as orden_mod        # noqa: E402
import src.analysis.decision_orchestrator as orquestador   # noqa: E402

from src.actions.autopilot_executor import (               # noqa: E402
    resultado_de_publicar,
)
from src.analysis.action_failure_backoff import (          # noqa: E402
    record_action_result,
)
from src.analysis.decision_orchestrator import (           # noqa: E402
    los_que_se_pueden_publicar,
)


AHORA = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)

# Los ids reales, para que la prueba se lea con la foto del 12/10.
YAMAL, OLASAGASTI, JUTGLA, IVAN = 26271, 29661, 3159, 17937


def _ficha(pid, nombre, precio=1_000_000):
    return {
        "id": pid,
        "name": nombre,
        "listing_price": precio,
        "listing_action": "LIST_FOR_LIQUIDITY",
    }


# El `to_list` del 12/10, en el orden de Biwenger: Yamal el primero.
COLA = [
    _ficha(YAMAL, "Yamal", 30_000_000),
    _ficha(OLASAGASTI, "Olasagasti", 4_000_000),
    _ficha(JUTGLA, "Jutglà", 2_600_000),
]

ORDEN = {
    "caduca": "2026-11-30T23:59:00+01:00",
    "fichar": [{"player_id": IVAN, "nombre": "Iván Romero", "puja": 3_777_000}],
    "proteger": [{"player_id": YAMAL, "nombre": "Yamal"}],
    "conservar": [{"player_id": OLASAGASTI, "nombre": "Olasagasti"}],
}


class _Entorno:
    """Pone y quita una variable de entorno sin dejar rastro."""

    def __init__(self, nombre, valor):
        self.nombre, self.valor = nombre, valor

    def __enter__(self):
        self.antes = os.environ.get(self.nombre)
        if self.valor is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.valor
        return self

    def __exit__(self, *_):
        if self.antes is None:
            os.environ.pop(self.nombre, None)
        else:
            os.environ[self.nombre] = self.antes


def _escritor_sin_red():
    """Un BiwengerWriteClient real sin login: nunca llega a enviar."""

    import src.biwenger.write_client as escritura

    cliente = object.__new__(escritura.BiwengerWriteClient)

    class _C:
        BASE_URL = "https://biwenger.invalid/api/v2"

    cliente.client = _C()
    cliente.version, cliente.league_id, cliente.user_id = "0", 1, 2
    return cliente


# ============================================================
# 1. UN PROTEGIDO NUNCA ES EL QUE SE PUBLICA
# ============================================================


def test_un_protegido_nunca_es_el_que_se_publica():
    r = los_que_se_pueden_publicar(COLA, {YAMAL})

    assert [p["id"] for p in r["to_list"]] == [OLASAGASTI, JUTGLA], r
    assert r["to_list"][0]["name"] == "Olasagasti", r
    assert [x["id"] for x in r["no_se_publican"]] == [YAMAL], r
    assert r["no_se_publican"][0]["motivo"] == (
        "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR"
    ), r

    # El resto de la cola no cambia de orden ni de contenido.
    assert r["to_list"] == COLA[1:], r

    # Si solo quedan protegidos, no hay candidata de publicar.
    assert los_que_se_pueden_publicar(COLA[:1], {YAMAL})["to_list"] == []

    # Sin protegidos (orden apagada o caducada), la cola sale igual.
    assert los_que_se_pueden_publicar(COLA, set())["to_list"] == COLA
    assert los_que_se_pueden_publicar([], {YAMAL})["to_list"] == []


# ============================================================
# 2. CON LA ORDEN REAL: PROTEGER Y FICHAR FUERA, CONSERVAR NO
# ============================================================


def test_con_la_orden_real_conservar_se_sigue_publicando():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "orden.json"
        ruta.write_text(json.dumps(ORDEN), encoding="utf-8")

        with _Entorno(orden_mod.ENV, "1"):
            ids = orden_mod.protegidos(ruta, AHORA)
            assert ids == {YAMAL, IVAN}, ids

            cola = COLA + [_ficha(IVAN, "Iván Romero")]
            r = los_que_se_pueden_publicar(cola, ids)
            assert [p["id"] for p in r["to_list"]] == [OLASAGASTI, JUTGLA], r
            assert {x["id"] for x in r["no_se_publican"]} == {YAMAL, IVAN}, r

        # Apagada: no protege a nadie, y la cola sale como entra.
        with _Entorno(orden_mod.ENV, None):
            assert orden_mod.protegidos(ruta, AHORA) == set()

        # Caducada: tampoco.
        with _Entorno(orden_mod.ENV, "1"):
            despues = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
            assert orden_mod.protegidos(ruta, despues) == set()


# ============================================================
# 3. LA MISMA PUERTA QUE EL ESCRITOR
# ============================================================


def test_la_misma_puerta_que_el_escritor():
    """
    Se sustituye `la_orden_del_gestor.protegidos` por una de mentira y
    se mira que el filtro (con su lectura por defecto) y el escritor
    real (`list_player_for_sale`) dicen lo mismo jugador a jugador.
    """

    original = orden_mod.protegidos
    orden_mod.protegidos = lambda *a, **k: {YAMAL}

    try:
        r = los_que_se_pueden_publicar(COLA)
        cliente = _escritor_sin_red()

        frenados = set()
        for ficha in COLA:
            # execute=False: la puerta va ANTES y no hay red.
            respuesta = cliente.list_player_for_sale(
                player_id=ficha["id"], price=1, execute=False,
            )
            if respuesta.get("blocked"):
                frenados.add(ficha["id"])
            assert respuesta.get("sent") is False, respuesta

        assert frenados == {YAMAL}, frenados
        assert {x["id"] for x in r["no_se_publican"]} == frenados, r
        assert r["to_list"][0]["id"] not in frenados, r
    finally:
        orden_mod.protegidos = original


# ============================================================
# 4. EL ORQUESTADOR FILTRA ANTES DE LAS DOS PUBLICACIONES
# ============================================================


def test_el_orquestador_filtra_antes_de_publicar():
    fuente = inspect.getsource(orquestador.build_global_decision_uncached)

    filtro = fuente.find("los_que_se_pueden_publicar(")
    reasigna = fuente.find('to_list = publicables["to_list"]')

    assert filtro != -1, "el orquestador no llama al filtro"
    assert reasigna > filtro, "el orquestador no usa la cola filtrada"

    # Las dos publicaciones (saldo negativo y mantenimiento) leen
    # `to_list` despues del filtro.
    publicaciones = [
        i for i in range(len(fuente))
        if fuente.startswith('"LIST_FOR_LIQUIDITY"', i)
    ]
    assert len(publicaciones) == 2, publicaciones
    assert all(i > reasigna for i in publicaciones), publicaciones

    # Y se puede mirar a quien se dejo fuera.
    assert '"no_se_publican"' in fuente


# ============================================================
# 5. UNA PUBLICACION FRENADA NO ES UNA ESCRITURA
# ============================================================


FRENADA = {
    "operation": "LIST_FOR_SALE",
    "sent": False,
    "success": False,
    "blocked": "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR",
}


def test_una_publicacion_frenada_no_es_una_escritura():
    jugador = COLA[0]
    r = resultado_de_publicar("LIST_FOR_LIQUIDITY", jugador, FRENADA)

    assert r["write_performed"] is False, r
    assert r["success"] is False, r
    assert r["status"] == "BLOCKED", r
    assert r["blocked"] == "PROTEGIDO_POR_LA_ORDEN_DEL_GESTOR", r
    assert r["action"] == "LIST_FOR_LIQUIDITY", r
    assert r["player"] is jugador, r
    assert "Yamal" in r["reason"], r

    # El backoff no la castiga: no se intento nada.
    estado = record_action_result(
        {}, action=r["action"], target_id=YAMAL, success=r["success"],
        write_performed=r["write_performed"], now=AHORA.replace(tzinfo=None),
    )
    assert estado == {}, estado

    # El ciclo no la cuenta como su escritura (autopilot y V10).
    from src.autopilot import register_action_outcome
    from src.v10_full_autonomous_live import _write_used

    apuntado = register_action_outcome(
        {"action": "LIST_FOR_LIQUIDITY", "data": {"player": jugador}}, r,
    )
    assert apuntado["recorded"] is False, apuntado
    assert _write_used({"execution": r}) is False


def test_lo_que_se_envia_sigue_siendo_escritura():
    jugador = COLA[1]

    bien = resultado_de_publicar(
        "LIST_FOR_LIQUIDITY", jugador,
        {"sent": True, "success": True, "http_status": 204, "response": None},
    )
    assert bien["write_performed"] is True, bien
    assert bien["status"] == "LISTED", bien
    assert bien["success"] is True, bien
    assert bien["reason"] == "Publicacion de Olasagasti.", bien
    assert "blocked" not in bien, bien

    # HTTP 400: se envio. Si no sabemos si llego, no se manda otra.
    mal = resultado_de_publicar(
        "LIST_FOR_LIQUIDITY", jugador,
        {"sent": True, "success": False, "http_status": 400,
         "response": {"error": "x"}},
    )
    assert mal["write_performed"] is True, mal
    assert mal["status"] == "FAILED", mal
    assert mal["http_status"] == 400, mal

    # Ensayo: `sent: False` SIN `blocked`. En produccion se habria
    # enviado, y el ensayo tiene que ver la misma vuelta.
    ensayo = resultado_de_publicar(
        "LIST_FOR_LIQUIDITY", jugador,
        {"sent": False, "operation": "LIST_FOR_SALE"},
    )
    assert ensayo["write_performed"] is True, ensayo
    assert ensayo["status"] == "FAILED", ensayo


# ============================================================
# 6. EL EXECUTOR ENTERO, CON UN ESCRITOR DE MENTIRA
# ============================================================


def test_el_executor_no_gasta_la_ranura_si_el_escritor_frena():
    original_escritor = executor_mod.BiwengerWriteClient
    original_protegidos = orden_mod.protegidos

    decision = {
        "action": "LIST_FOR_LIQUIDITY",
        "executable": True,
        "temporal_gate": {"phase": "NORMAL", "operations_locked": False,
                          "hard_safety_mode": False},
        "data": {"player": COLA[0]},
    }

    try:
        # El escritor real, sin red, con la orden de mentira.
        orden_mod.protegidos = lambda *a, **k: {YAMAL}
        executor_mod.BiwengerWriteClient = _escritor_sin_red

        r = executor_mod.execute_autopilot_decision(decision, execute=True)
        assert r["write_performed"] is False, r
        assert r["status"] == "BLOCKED", r

        # Uno que no esta protegido si gasta la escritura.
        class _Escritor:
            def list_player_for_sale(self, player_id, price, execute=False):
                return {"sent": True, "success": True, "http_status": 204}

        executor_mod.BiwengerWriteClient = _Escritor
        r = executor_mod.execute_autopilot_decision(
            {**decision, "data": {"player": COLA[1]}}, execute=True,
        )
        assert r["write_performed"] is True, r
        assert r["status"] == "LISTED", r
    finally:
        executor_mod.BiwengerWriteClient = original_escritor
        orden_mod.protegidos = original_protegidos


# ============================================================
# 7. NUNCA LANZA
# ============================================================


def test_nunca_lanza():
    # Fichas raras: se quedan donde estan, no rompen nada.
    raras = [None, {"id": "x"}, {"name": "sin id"}, {"id": 5, "name": "B"}]
    r = los_que_se_pueden_publicar(raras, {5})
    assert r["to_list"] == raras[:3], r
    assert [x["id"] for x in r["no_se_publican"]] == [5], r

    # Protegidos ilegibles: la cola sale como entra, con el motivo.
    r = los_que_se_pueden_publicar(COLA, {"no-es-un-id"})
    assert r["to_list"] == COLA, r
    assert "error" in r, r

    assert los_que_se_pueden_publicar(None, set())["to_list"] == []

    # El executor con respuestas raras.
    for rara in (None, "texto", 7, {}):
        r = resultado_de_publicar("LIST_FOR_LIQUIDITY", COLA[1], rara)
        assert r["write_performed"] is True, r
        assert r["success"] is False, r

    r = resultado_de_publicar("LIST_FOR_LIQUIDITY", None, FRENADA)
    assert r["write_performed"] is False, r


TESTS = [
    test_un_protegido_nunca_es_el_que_se_publica,
    test_con_la_orden_real_conservar_se_sigue_publicando,
    test_la_misma_puerta_que_el_escritor,
    test_el_orquestador_filtra_antes_de_publicar,
    test_una_publicacion_frenada_no_es_una_escritura,
    test_lo_que_se_envia_sigue_siendo_escritura,
    test_el_executor_no_gasta_la_ranura_si_el_escritor_frena,
    test_nunca_lanza,
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
    print(f"{len(TESTS) - fallos}/{len(TESTS)} en verde")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
