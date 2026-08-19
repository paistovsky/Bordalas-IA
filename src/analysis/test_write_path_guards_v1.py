"""
Regresion de dos guardias dormidas en la ruta de escritura.

Auditoria del 15/08/2026, defectos 1 y 5.

DEFECTO 1 - autopilot.py:2570
    run_cycle leia temporal_gate y balance de result directamente,
    pero build_global_decision los devuelve dentro de
    result["state"]. Resultado: temporal_gate siempre {},
    operations_locked siempre False, y BLOCK_TEMPORAL_LOCK del
    safety gate competitivo era codigo inalcanzable. Con la
    jornada bloqueada, la ruta competitiva podia escribir.

DEFECTO 5 - biwenger/write_client.py
    _is_success solo miraba el codigo HTTP. Un 200 con
    {"status":400,"message":"saldo insuficiente"} o una pagina
    HTML de mantenimiento se daba por operacion confirmada.

Ejecutar:
    python -m src.analysis.test_write_path_guards_v1
"""

# HEALTH_CHECK: SAFE
# Solo inspecciona codigo fuente y estructuras en memoria.
# No instancia BiwengerWriteClient ni realiza ninguna escritura.

import ast
import inspect
from pathlib import Path

from src.analysis.competitive_safety_gate import (
    evaluate_competitive_safety_gate,
)


# ============================================================
# DEFECTO 1
# ============================================================

# Quien construye de verdad el diccionario de la decision.
#
# Era `build_global_decision` a secas. Desde el 19/08/2026 ese
# nombre es una envoltura que recuerda la ultima decision mientras
# el snapshot no cambie -el ciclo la calculaba cinco veces por
# ronda y tardaba 15m44s- y la logica vive en la version sin
# cache.
#
# Se miran las dos y se queda con la que de verdad devuelve el
# diccionario, asi el candado sigue puesto se llame como se llame
# y no hay que volver aqui cada vez que alguien la envuelva.
CONSTRUCTORES_DE_LA_DECISION = (
    "build_global_decision_uncached",
    "build_global_decision",
)


def _claves_de_build_global_decision() -> tuple[set, set]:
    """
    Lee el arbol sintactico en vez de ejecutar el orquestador,
    que necesitaria snapshot, red y credenciales.
    """
    ruta = (
        Path(__file__).resolve().parent
        / "decision_orchestrator.py"
    )
    arbol = ast.parse(
        ruta.read_text(encoding="utf-8", errors="ignore")
    )

    arriba: set = set()
    dentro_state: set = set()

    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.FunctionDef):
            continue
        if nodo.name not in CONSTRUCTORES_DE_LA_DECISION:
            continue

        for ret in ast.walk(nodo):
            if not isinstance(ret, ast.Return):
                continue
            if not isinstance(ret.value, ast.Dict):
                continue

            for clave, valor in zip(
                ret.value.keys,
                ret.value.values,
            ):
                if not isinstance(clave, ast.Constant):
                    continue
                arriba.add(clave.value)

                if (
                    clave.value == "state"
                    and isinstance(valor, ast.Dict)
                ):
                    dentro_state = {
                        k.value
                        for k in valor.keys
                        if isinstance(k, ast.Constant)
                    }

    return arriba, dentro_state


def test_temporal_gate_no_esta_en_nivel_superior() -> None:
    arriba, dentro = _claves_de_build_global_decision()

    assert dentro, (
        "No se pudo leer result['state']; revisa el parser."
    )

    assert "temporal_gate" in dentro
    assert "balance" in dentro

    assert "temporal_gate" not in arriba, (
        "temporal_gate ha subido al nivel superior: revisa si "
        "run_cycle debe volver a leerlo de ahi."
    )

    print(
        "  OK  temporal_gate y balance viven en result['state']"
    )


def test_run_cycle_lee_del_sitio_correcto() -> None:
    """
    El fallo original era literalmente result.get("temporal_gate").
    """
    from src import autopilot

    fuente = inspect.getsource(autopilot.run_cycle)

    assert 'result.get(\n                    "temporal_gate"' not in fuente, (
        "REGRESION: run_cycle vuelve a leer temporal_gate del "
        "nivel superior de result, donde siempre vale {}."
    )

    assert "cycle_state" in fuente, (
        "REGRESION: run_cycle ya no usa result['state'] para "
        "obtener el gate temporal."
    )

    print("  OK  run_cycle lee el gate de result['state']")


def test_gate_competitivo_bloquea_con_operaciones_cerradas() -> None:
    """
    Con el gate bien alimentado, BLOCK_TEMPORAL_LOCK dispara.
    """
    oferta = {
        "offer_id": 1,
        "amount": 1_000_000,
        "decision_authority": "COMPETITIVE",
        "authoritative_decision": "ACCEPT_NOW",
        "negotiation": {
            "action_gate": "RESPOND",
            "should_respond": True,
        },
    }

    bloqueado = evaluate_competitive_safety_gate(
        offer=oferta,
        temporal_gate={
            "operations_locked": True,
            "phase": "ROUND_LOCKED",
        },
        current_balance=500_000,
    )

    assert bloqueado["status"] == "BLOCK_TEMPORAL_LOCK", (
        f"REGRESION: con operations_locked=True el gate no "
        f"bloqueo por fase. Devolvio: {bloqueado['status']}"
    )
    assert bloqueado["authorized"] is False

    # Y con el gate vacio -que era lo que llegaba antes del
    # arreglo- esa barrera no se activa: por eso era invisible.
    con_gate_vacio = evaluate_competitive_safety_gate(
        offer=oferta,
        temporal_gate={},
        current_balance=500_000,
    )

    assert con_gate_vacio["status"] != "BLOCK_TEMPORAL_LOCK", (
        "El gate vacio no deberia bloquear por fase; si lo hace, "
        "este test ya no demuestra nada."
    )

    print(
        "  OK  operations_locked=True bloquea; gate vacio no "
        "(por eso el bug era invisible)"
    )


# ============================================================
# DEFECTO 5
# ============================================================

class _ClienteFalso:
    """
    Evita el login real: solo queremos _evaluate_success.
    """
    SUCCESS_CODES = {200, 201, 204}

    from src.biwenger.write_client import (  # noqa: E402
        BiwengerWriteClient as _Real,
    )

    _evaluate_success = _Real._evaluate_success
    _is_success = _Real._is_success


CASOS = [
    # (codigo, cuerpo, exito_esperado, etiqueta)
    (200, {"status": 200, "data": {"id": 1}}, True,
     "200 con cuerpo correcto"),
    (201, {"status": 201}, True,
     "201 con cuerpo correcto"),
    (204, None, True,
     "204 sin contenido"),
    (200, {"status": 400, "message": "saldo insuficiente"}, False,
     "200 con status 400 en el cuerpo"),
    (200, {"status": 500}, False,
     "200 con status 500 en el cuerpo"),
    (200, {"error": "forbidden"}, False,
     "200 con campo error"),
    (200, "<!DOCTYPE html><html>mantenimiento</html>", False,
     "200 con pagina HTML"),
    (200, "", True,
     "200 con cuerpo vacio"),
    (200, {"data": {"id": 7}}, True,
     "200 sin campo status (se acepta)"),
    (400, {"status": 400}, False,
     "400 HTTP"),
    (500, None, False,
     "500 HTTP"),
]


def test_validacion_del_cuerpo() -> None:
    cliente = _ClienteFalso()
    fallos = []

    for codigo, cuerpo, esperado, etiqueta in CASOS:
        obtenido, motivo = cliente._evaluate_success(
            codigo,
            cuerpo,
        )

        if obtenido != esperado:
            fallos.append(
                f"{etiqueta}: esperaba {esperado}, "
                f"obtuve {obtenido} ({motivo})"
            )

    assert not fallos, (
        "REGRESION en la validacion de respuestas:\n  "
        + "\n  ".join(fallos)
    )

    print(
        f"  OK  {len(CASOS)} casos de respuesta clasificados bien"
    )


def test_el_caso_que_costaba_dinero() -> None:
    """
    El escenario concreto: Biwenger devuelve 200 diciendo que no
    hay saldo. Antes esto era una escritura confirmada.
    """
    cliente = _ClienteFalso()

    exito, motivo = cliente._evaluate_success(
        200,
        {"status": 400, "message": "saldo insuficiente"},
    )

    assert exito is False
    assert "400" in motivo

    print(f"  OK  200 + saldo insuficiente = fallo ({motivo})")


def test_compatibilidad_sin_cuerpo() -> None:
    """
    Llamadas antiguas con un solo argumento siguen funcionando.
    """
    cliente = _ClienteFalso()

    assert cliente._is_success(200) is True
    assert cliente._is_success(404) is False

    print("  OK  la firma antigua de un argumento sigue valida")


# ============================================================

TESTS = [
    test_temporal_gate_no_esta_en_nivel_superior,
    test_run_cycle_lee_del_sitio_correcto,
    test_gate_competitivo_bloquea_con_operaciones_cerradas,
    test_validacion_del_cuerpo,
    test_el_caso_que_costaba_dinero,
    test_compatibilidad_sin_cuerpo,
]


def main() -> None:
    print("=" * 60)
    print(" GUARDIAS DE LA RUTA DE ESCRITURA (defectos 1 y 5)")
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
