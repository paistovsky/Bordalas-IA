"""
La cola ordena entre escalas por la unidad comun, no por el
porcentaje crudo de cada via.

QUE VIGILA (26/09/2026)

    Un candidato de FICHA VACIA publica su porcentaje contando todos sus
    puntos, como si jugara (acquisition_valuation.py:640). Uno de MEJORA
    DEL ONCE publica solo los puntos de mas contra el titular de su
    posicion. En esta liga solo puntuan once, asi que el primero puede
    no sumar nada.

    La guardia pone uno de cada: el de ficha vacia, alto en crudo pero
    que no entraria en el once; el de mejora del once, mas bajo en crudo
    pero que si entra. La cola tiene que poner primero al segundo.

    MUERDE SI EN EL CASO LAS DOS ESCALAS COMPARTEN UNIDAD: si el crudo
    del de ficha vacia ya fuera su unidad comun, ordenar por una o por
    otra daria lo mismo y esto no probaria nada.

NO MIRA EL MUNDO

    Plantilla de mentira, escrita aqui. Sin disco, red, reloj ni entorno.
"""

from __future__ import annotations

import sys

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.la_cola import (                             # noqa: E402
    el_mejor_once,
    mejora_del_once,
    ordenar,
    unidad,
)


# Un 3-5-2 que ya es el mejor para esta plantilla.
PLANTILLA = (
    [{"id": 1, "pos": 1, "pts": 180}]
    + [{"id": 10 + i, "pos": 2, "pts": p} for i, p in enumerate((165, 138, 108, 60))]
    + [{"id": 20 + i, "pos": 3, "pts": p} for i, p in enumerate((178, 146, 121, 116, 102, 30))]
    + [{"id": 30 + i, "pos": 4, "pts": p} for i, p in enumerate((290, 135, 34))]
)

JORNADAS_QUE_QUEDAN = 31


def _crudo_de_ficha_vacia(puntos, precio) -> float:
    """Lo que publicaria la ficha vacia: TODOS sus puntos, como si jugara."""

    return unidad(puntos, precio, JORNADAS_QUE_QUEDAN)["rendimiento"]


def _crudo_de_mejora(puntos, sale, precio) -> float:
    """Lo que publicaria la mejora del once: contra el titular de su posicion."""

    return unidad(puntos - sale, precio, JORNADAS_QUE_QUEDAN)["rendimiento"]


def test_la_cola_ordena_entre_escalas() -> None:

    base = el_mejor_once(PLANTILLA)

    # FICHA VACIA: un medio de 90 por 1.000.000. En crudo cuenta sus 90.
    vacia = {"id": 91, "pos": 3, "pts": 90, "precio": 1_000_000}
    crudo_vacia = _crudo_de_ficha_vacia(vacia["pts"], vacia["precio"])

    # MEJORA DEL ONCE: un delantero de 158 por 4.000.000, contra el
    # segundo punta de 135.
    once = {"id": 92, "pos": 4, "pts": 158, "precio": 4_000_000}
    crudo_once = _crudo_de_mejora(once["pts"], 135, once["precio"])

    assert crudo_vacia > crudo_once, (
        "el caso no enfrenta al crudo alto de ficha vacia con el crudo "
        "bajo de la mejora: no probaria nada"
    )

    filas = []
    for c in (vacia, once):
        m = mejora_del_once(PLANTILLA, c, base)
        u = unidad(m["mejora"], c["precio"], JORNADAS_QUE_QUEDAN)
        filas.append({**c, **m, **u})

    comun = {f["id"]: f["rendimiento"] for f in filas}

    assert comun[91] != crudo_vacia, (
        "en el caso la ficha vacia ya se mide en la unidad comun: las dos "
        "escalas comparten unidad y esta guardia no mediria nada"
    )

    cola = ordenar(filas)

    assert cola[0]["id"] == 92, (
        f"la cola pone primero a {cola[0]['id']}: esta ordenando por el "
        f"crudo ({crudo_vacia:.2%} contra {crudo_once:.2%}) y no por lo "
        f"que suma al once ({comun})"
    )

    assert not filas[0]["entra"] and filas[0]["mejora"] == 0
    assert filas[1]["entra"] and filas[1]["mejora"] > 0


def test_la_mejora_es_la_del_once_rehecho() -> None:
    """Con el delantero dentro, lo mejor pasa a 3-4-3 y sale el quinto medio."""

    base = el_mejor_once(PLANTILLA)
    m = mejora_del_once(PLANTILLA, {"id": 92, "pos": 4, "pts": 158}, base)

    assert base["formacion"] == "3-5-2"
    assert m["formacion"] == "3-4-3"
    assert m["mejora"] == 158 - 102
    assert m["salen"] == [24]


def test_la_unidad_no_inventa() -> None:

    assert unidad(0, 1_000_000, 31)["premios"] == 0
    assert unidad(10, 0, 31)["rendimiento"] is None
    assert unidad(10, 1_000_000, 31, recuperado=400_000)["caja_neta"] == 600_000


TESTS = [
    test_la_cola_ordena_entre_escalas,
    test_la_mejora_es_la_del_once_rehecho,
    test_la_unidad_no_inventa,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA COLA ORDENA ENTRE ESCALAS V1")
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
