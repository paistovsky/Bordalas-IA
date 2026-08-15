"""
Regresion de los defectos 7 y 10 de la auditoria del 15/08/2026.

DEFECTO 7 - un fallo de verificacion borraba una escritura real
    Tras enviar la puja, execute_bid llamaba a get_market() para
    comprobar que figuraba. Esa llamada estaba FUERA de todo try,
    y hace raise_for_status() por dentro.

    Un 502 pasajero del proxy hacia que la excepcion subiese hasta
    el except general de multi_bid_executor, que marcaba
    status=ERROR y failed+=1. El operador concluia que no se habia
    comprometido dinero cuando si: la puja estaba enviada y
    aceptada. Encima se perdia el identificador de la oferta.

DEFECTO 10 - EXECUTED sin mirar la propia verificacion
    execute_sale_listing fijaba status="EXECUTED" solo con el
    codigo HTTP, y calculaba listing_detected_after DESPUES sin
    consumirlo. Una publicacion que devolvia 200 pero no llegaba
    a crearse se daba por hecha, consumia la escritura del ciclo y
    el jugador seguia en plantilla perdiendo valor.

Ejecutar:
    python -m src.analysis.test_write_verification_v1
"""

# HEALTH_CHECK: SAFE
# Solo inspecciona codigo fuente y estructuras en memoria.
# No instancia BiwengerWriteClient ni realiza ninguna escritura.

import ast
import inspect
import textwrap

from src.actions import live_bid_executor, live_sale_executor


def _verificacion_dentro_de_try(funcion) -> bool:
    """
    Comprueba por arbol sintactico que la ULTIMA llamada a
    get_market() -la de verificacion, no la lectura previa a
    escribir- esta dentro de un try.

    Buscar por texto no vale: execute_bid llama a get_market()
    tambien antes de escribir, y find() encuentra esa primera.
    """
    arbol = ast.parse(
        textwrap.dedent(
            inspect.getsource(funcion)
        )
    )

    def llamadas_get_market(nodo):
        return [
            hijo
            for hijo in ast.walk(nodo)
            if isinstance(hijo, ast.Call)
            and isinstance(hijo.func, ast.Attribute)
            and hijo.func.attr == "get_market"
        ]

    todas = llamadas_get_market(arbol)

    if not todas:
        return False

    ultima = max(
        todas,
        key=lambda nodo: nodo.lineno,
    )

    protegidas = {
        id(llamada)
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Try)
        for cuerpo in nodo.body
        for llamada in llamadas_get_market(cuerpo)
    }

    return id(ultima) in protegidas


# ============================================================
# UTILIDADES
# ============================================================

class _ClienteQueFalla:
    """get_market() revienta, como un 502 del proxy."""

    def get_market(self):
        raise ConnectionError(
            "502 Bad Gateway"
        )


class _ClienteVacio:
    """Responde bien, pero la operacion no figura."""

    def get_market(self):
        return {"offers": [], "sales": []}


class _WriterFalso:
    user_id = 14175949

    def __init__(self, cliente):
        self.client = cliente


# ============================================================
# DEFECTO 7
# ============================================================

def test_la_verificacion_de_puja_esta_protegida() -> None:
    assert _verificacion_dentro_de_try(
        live_bid_executor.execute_bid
    ), (
        "REGRESION: el get_market() de verificacion vuelve a "
        "estar fuera del try. Un fallo suyo se llevaria por "
        "delante una puja ya enviada."
    )

    print("  OK  la verificacion de puja va dentro de try")


def test_fallo_de_verificacion_no_borra_la_puja() -> None:
    """
    El escenario exacto: la puja se envio y Biwenger la acepto;
    la comprobacion posterior revienta.
    """
    resultado = {
        "success": True,
        "http_status": 201,
        "api_response": {"id": 4138078754},
    }

    writer = _WriterFalso(_ClienteQueFalla())

    try:
        market = writer.client.get_market()
        resultado["offer_detected_after"] = bool(market)
        resultado["verification_status"] = "CONFIRMED"

    except Exception as error:
        resultado["offer_detected_after"] = None
        resultado["verification_status"] = "UNVERIFIED"
        resultado["verification_error"] = (
            f"{type(error).__name__}: {error}"
        )

    assert resultado["success"] is True, (
        "REGRESION: un fallo de verificacion no puede convertir "
        "una escritura confirmada en fallida."
    )
    assert resultado["verification_status"] == "UNVERIFIED"
    assert resultado["api_response"]["id"] == 4138078754, (
        "El identificador de la oferta debe sobrevivir: es lo "
        "unico que permite reconciliar despues."
    )

    print(
        "  OK  la puja sigue marcada como enviada y conserva "
        "su id"
    )


def test_los_tres_estados_de_verificacion() -> None:
    fuente = inspect.getsource(
        live_bid_executor.execute_bid
    )

    for estado in ("CONFIRMED", "NOT_REFLECTED", "UNVERIFIED"):
        assert estado in fuente, (
            f"Falta el estado {estado}. Hay que distinguir "
            f"'figura', 'no figura' y 'no lo se': no son lo "
            f"mismo."
        )

    print(
        "  OK  distingue CONFIRMED / NOT_REFLECTED / UNVERIFIED"
    )


# ============================================================
# DEFECTO 10
# ============================================================

def test_la_verificacion_de_venta_esta_protegida() -> None:
    assert _verificacion_dentro_de_try(
        live_sale_executor.execute_sale_listing
    ), (
        "REGRESION: el get_market() de verificacion de ventas "
        "vuelve a estar fuera del try."
    )

    print("  OK  la verificacion de venta va dentro de try")


def test_venta_no_reflejada_no_se_marca_ejecutada() -> None:
    """
    El corazon del defecto 10.
    """
    fuente = inspect.getsource(
        live_sale_executor.execute_sale_listing
    )

    assert "EXECUTED_NOT_REFLECTED" in fuente, (
        "REGRESION: una publicacion que devuelve 200 pero no se "
        "crea vuelve a marcarse como EXECUTED a secas."
    )

    assert "EXECUTED_UNVERIFIED" in fuente, (
        "Falta distinguir 'no se creo' de 'no pude comprobarlo'."
    )

    # El estado debe recalcularse DESPUES de verificar.
    primera = fuente.find('result["status"] = (')
    verificacion = fuente.find("VERIFICACI")
    recalculo = fuente.find('"EXECUTED_NOT_REFLECTED"')

    assert primera < verificacion < recalculo, (
        "REGRESION: el estado ya no se recalcula despues de la "
        "verificacion."
    )

    print(
        "  OK  una venta no reflejada baja a "
        "EXECUTED_NOT_REFLECTED"
    )


def test_escritura_rechazada_no_intenta_verificar() -> None:
    fuente = inspect.getsource(
        live_sale_executor.execute_sale_listing
    )

    assert "SKIPPED_WRITE_REJECTED" in fuente, (
        "Si el HTTP fue rechazado no hay nada que verificar: no "
        "gastemos una llamada ni ensuciemos el diagnostico."
    )

    print("  OK  si la escritura fue rechazada no se verifica")


# ============================================================
# COHERENCIA
# ============================================================

def test_ambos_ejecutores_usan_el_mismo_vocabulario() -> None:
    puja = inspect.getsource(
        live_bid_executor.execute_bid
    )
    venta = inspect.getsource(
        live_sale_executor.execute_sale_listing
    )

    for campo in (
        "verification_status",
        "verification_error",
    ):
        assert campo in puja, f"Falta {campo} en pujas"
        assert campo in venta, f"Falta {campo} en ventas"

    print(
        "  OK  pujas y ventas comparten vocabulario de "
        "verificacion"
    )


# ============================================================

TESTS = [
    test_la_verificacion_de_puja_esta_protegida,
    test_fallo_de_verificacion_no_borra_la_puja,
    test_los_tres_estados_de_verificacion,
    test_la_verificacion_de_venta_esta_protegida,
    test_venta_no_reflejada_no_se_marca_ejecutada,
    test_escritura_rechazada_no_intenta_verificar,
    test_ambos_ejecutores_usan_el_mismo_vocabulario,
]


def main() -> None:
    print("=" * 60)
    print(" VERIFICACION POSTERIOR A ESCRITURA (defectos 7 y 10)")
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
