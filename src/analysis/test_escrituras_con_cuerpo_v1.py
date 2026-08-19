"""
Una escritura sin cuerpo es un 500 esperando a que alguien la use.

EL CASO (19/08/2026)

    El dashboard lo dijo asi:

        "ACCEPT RECOVERY OFFER apartada: ha fallado 4 veces
         seguidas (HTTP 500). Se reintenta en 66 min."

    `write_client.py` tiene seis escrituras. Cinco pasan
    `json=request["json"]`. `accept_offer` hacia un PUT pelado a
    /offers/{id}, sin decir que hacer con la oferta, y Biwenger
    contestaba 500.

    El endpoint es exactamente el mismo que el de rechazar, que
    si manda {"status": "rejected"} y lleva funcionando desde
    siempre. Lo unico que distinguia aceptar de rechazar era la
    palabra que no se enviaba.

POR QUE NADIE LO VIO EN MESES

    Porque nadie llamaba a esa rama. El camino de cobrar estaba
    desconectado del orquestador -las cinco paredes del 18/08- y
    se conecto ayer. El codigo estaba escrito, revisado y
    documentado ("Endpoint validado manualmente en Biwenger"), y
    era incorrecto desde la primera linea.

    Una rama que no se ejecuta no esta probada aunque este
    escrita. Y este proyecto tiene varias mas en shadow.

LA REGLA

    Toda escritura con cuerpo construye su cuerpo y lo manda.
    Se comprueba sobre el arbol sintactico, sin red y sin
    credenciales: no hace falta hablar con Biwenger para ver que
    a una peticion le falta el sobre.
"""

from __future__ import annotations

import ast
from pathlib import Path


RUTA = (
    Path(__file__).resolve().parents[1]
    / "biwenger"
    / "write_client.py"
)


# DELETE no lleva cuerpo y no tiene por que llevarlo.
METODOS_CON_CUERPO = ("post", "put")


def _arbol():
    return ast.parse(
        RUTA.read_text(encoding="utf-8")
    )


def test_ninguna_escritura_va_muda():
    """
    Todo POST y todo PUT a Biwenger manda su cuerpo.
    """

    mudas = []

    for nodo in ast.walk(_arbol()):

        if not isinstance(nodo, ast.Call):
            continue

        funcion = nodo.func

        if not isinstance(funcion, ast.Attribute):
            continue

        if funcion.attr not in METODOS_CON_CUERPO:
            continue

        # Que sea `algo.session.post(...)` y no cualquier `.put`.
        origen = funcion.value

        if not (
            isinstance(origen, ast.Attribute)
            and origen.attr == "session"
        ):
            continue

        tiene_cuerpo = any(
            kw.arg in ("json", "data")
            for kw in nodo.keywords
        )

        if not tiene_cuerpo:
            mudas.append(
                f"{funcion.attr.upper()} en la linea "
                f"{nodo.lineno}"
            )

    assert not mudas, (
        "hay escrituras a Biwenger sin cuerpo, y Biwenger "
        "contesta 500 a eso: " + "; ".join(mudas)
    )


def test_aceptar_dice_que_acepta():
    """
    El caso concreto, por su nombre.

    Aceptar y rechazar comparten endpoint y metodo. Lo unico que
    los distingue es el cuerpo, asi que el cuerpo no es un
    detalle: es la operacion entera.
    """

    cuerpos = {}

    for nodo in ast.walk(_arbol()):

        if not isinstance(nodo, ast.FunctionDef):
            continue

        if nodo.name not in (
            "build_accept_offer_request",
            "build_reject_offer_request",
        ):
            continue

        for hijo in ast.walk(nodo):

            if not isinstance(hijo, ast.Dict):
                continue

            for clave, valor in zip(hijo.keys, hijo.values):

                if (
                    isinstance(clave, ast.Constant)
                    and clave.value == "status"
                    and isinstance(valor, ast.Constant)
                ):
                    cuerpos[nodo.name] = valor.value

    assert cuerpos.get(
        "build_accept_offer_request"
    ) == "accepted", (
        "aceptar una oferta ha dejado de decir que la acepta"
    )

    assert cuerpos.get(
        "build_reject_offer_request"
    ) == "rejected"


def test_el_cuerpo_viaja_hasta_la_peticion():
    """
    Construirlo no basta: hay que meterlo en el sobre.

    El fallo original no era que faltase el payload en el
    builder. Era que el builder no lo tenia Y el envio tampoco lo
    pasaba. Con arreglar uno solo de los dos, sigue el 500.
    """

    peticion = None

    for nodo in ast.walk(_arbol()):

        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == "accept_offer"
        ):
            peticion = ast.unparse(nodo)

    assert peticion is not None, (
        "no existe accept_offer en el cliente de escritura"
    )

    assert "json=request['json']" in peticion.replace('"', "'"), (
        "accept_offer construye el cuerpo pero no lo envia"
    )


def main():

    pruebas = [
        test_ninguna_escritura_va_muda,
        test_aceptar_dice_que_acepta,
        test_el_cuerpo_viaja_hasta_la_peticion,
    ]

    for prueba in pruebas:
        prueba()
        print(f"  OK  {prueba.__name__}")

    print()
    print("Escrituras con cuerpo: todo en verde.")


if __name__ == "__main__":
    main()
