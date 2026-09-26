"""
El carril tambien pregunta si el jugador va a jugar.

QUE SE PRUEBA (26/09/2026)

    `la_regla_de_compra` frenaba la reventa solo en la subasta del
    reset. El carril de la rendija compra para revender y no la
    miraba: Trent y Drkusic entraron por el sin pronostico de
    titularidad y perdieron 259.876 EUR.

    Ahora el carril la llama con su propio interruptor,
    `BORDALAS_REVENTA_SOLO_SI_JUEGA_EN_EL_CARRIL`, que nace
    APAGADO. Esta guardia comprueba las tres cosas que importan:

        1. Apagado, el carril puja como ayer: Trent sin pronostico
           sigue pujandose.
        2. Encendido, MUERDE Y DISTINGUE: Trent sin pronostico no
           se puja y el motivo se llama `NO_VA_A_JUGAR`; un
           titular al 70 % si se puja.
        3. El interruptor de la subasta, que YA esta encendido en
           produccion, no enciende el carril: sin paso 0 no hay
           cambio de comportamiento.

    Pone y quita ella misma los interruptores (doctrina 104).
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


from src.analysis.test_la_puja_del_carril_v1 import (    # noqa: E402
    TRENT,
    _correr,
    _EscritorDeMentira,
)
from src.analysis.la_regla_de_compra import (            # noqa: E402
    ENV,
    ENV_CARRIL,
)


# Trent, pero titular: pronostico y jerarquia por encima del corte.
TITULAR = {
    **TRENT,
    "starter_probability": 70.0,
    "hierarchy_value": 80,
    "hierarchy_label": "Titular",
}


class _Interruptores:
    """Pone exactamente estos, quita los dos de la regla, y restaura."""

    def __init__(self, **puestos):
        self.puestos = puestos
        self.antes = {}

    def __enter__(self):
        for nombre in (ENV, ENV_CARRIL):
            self.antes[nombre] = os.environ.get(nombre)
            os.environ.pop(nombre, None)

        for nombre, valor in self.puestos.items():
            os.environ[nombre] = valor

        return self

    def __exit__(self, *_):
        for nombre, valor in self.antes.items():
            if valor is None:
                os.environ.pop(nombre, None)
            else:
                os.environ[nombre] = valor


def _vuelta(candidato: dict):
    """Una vuelta del carril con un solo candidato, sin red ni `data/`."""

    import tempfile

    import src.analysis.test_la_puja_del_carril_v1 as carril

    # `_correr` puja por el `TRENT` de su modulo, leido al llamar:
    # se cambia solo durante esta vuelta.
    assert "TRENT" in _correr.__code__.co_names, (
        "`_correr` ya no puja por `TRENT`: esta guardia no sabria "
        "por quien puja el carril"
    )

    libro = {"version": 1, "bids": {}}

    escritor = _EscritorDeMentira()

    original = carril.TRENT

    try:
        carril.TRENT = candidato

        with tempfile.TemporaryDirectory() as tmp:
            salida = _correr(libro, escritor, Path(tmp))

    finally:
        carril.TRENT = original

    return escritor, salida


def test_apagado_el_carril_puja_como_ayer() -> None:

    with _Interruptores():
        escritor, salida = _vuelta(TRENT)

    assert escritor.pujas, (
        "con la regla del carril apagada, Trent sin pronostico "
        f"deberia pujarse como ayer: {salida.get('reason')}"
    )

    assert not salida.get("frenados_por_no_jugar"), salida


def test_encendido_muerde_y_distingue() -> None:

    with _Interruptores(**{ENV_CARRIL: "1"}):
        sin_pronostico, frenada = _vuelta(TRENT)
        titular, puesta = _vuelta(TITULAR)

    # MUERDE: sin pronostico no se puja, y se dice quien decidio.
    assert sin_pronostico.pujas == [], (
        "con la regla del carril puesta, el carril puja por un "
        "jugador sin pronostico de titularidad"
    )

    assert frenada.get("blocked_by") == "NO_VA_A_JUGAR", frenada

    assert frenada.get("frenados_por_no_jugar"), frenada

    # DISTINGUE: el titular sigue. Sin esto, la guardia solo
    # probaria que la regla apaga el carril.
    assert titular.pujas, (
        "con la regla del carril puesta, un titular al 70 % no se "
        f"puja: {puesta.get('reason')}"
    )


def test_el_interruptor_de_la_subasta_no_enciende_el_carril() -> None:

    # Produccion hoy: la de la subasta puesta, la del carril no.
    with _Interruptores(**{ENV: "1"}):
        escritor, salida = _vuelta(TRENT)

    assert escritor.pujas, (
        f"`{ENV}` ha cambiado el carril: encenderlo en el carril es "
        f"cosa de `{ENV_CARRIL}`, con su paso 0. "
        f"{salida.get('reason')}"
    )


TESTS = [
    test_apagado_el_carril_puja_como_ayer,
    test_encendido_muerde_y_distingue,
    test_el_interruptor_de_la_subasta_no_enciende_el_carril,
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
