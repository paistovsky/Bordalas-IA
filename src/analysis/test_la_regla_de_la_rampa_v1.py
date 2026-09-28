"""
Solo se compra para revender lo que SUBE (E1, 28/09/2026).

SINTOMA

    Las 34 pujas para revender de Pepe (subasta del reset y carril)
    fueron TODAS a jugadores con el precio quieto o bajando. E1 mide
    que ahi se pierde: 24/58 viajes verdes y -567.940, contra 57/73
    y +25,7 M de los que subian. El 28/09 el carril pujo por
    Zubeldia, ocho dias seguidos bajando.

LO QUE VIGILAN ESTAS GUARDIAS

    1. Apagada, no frena a nadie: el comportamiento de antes.
    2. Encendida, solo pasa el que sube; quieto, bajando y sin dato
       se frenan, y el motivo dice por que.
    3. En el carril de verdad: con el interruptor, Zubeldia bajando
       no se puja y el motivo nombra a la regla; el mismo jugador
       subiendo, si.
    4. La subasta copia `price_increment` del tablero: sin eso, con
       la regla puesta, no pasaria nadie.

REGLA 23 Y DOCTRINA 50

    Ni disco, ni red, ni reloj. Los interruptores se ponen y se
    quitan dentro de cada prueba, y se restauran al salir.
"""

from __future__ import annotations

import os
import sys

from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


CANDIDATOS = [
    {"id": 1, "name": "Sube", "price_increment": 30000},
    {"id": 2, "name": "Baja", "price_increment": -10000},
    {"id": 3, "name": "Quieto", "price_increment": 0},
    {"id": 4, "name": "Sin dato"},
]


class _Interruptores:
    """Pone exactamente estos, quita los de las dos reglas, y restaura."""

    def __init__(self, **puestos):
        self.puestos = puestos
        self.antes = {}

    def __enter__(self):
        from src.analysis.la_regla_de_compra import ENV, ENV_CARRIL
        from src.analysis.la_regla_de_la_rampa import ENV as RAMPA

        for nombre in (ENV, ENV_CARRIL, RAMPA):
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


def test_apagada_no_frena_a_nadie() -> None:

    from src.analysis.la_regla_de_la_rampa import mira_si_sube

    with _Interruptores():
        visto = mira_si_sube(CANDIDATOS)

    assert visto["activa"] is False, visto

    assert visto["siguen"] == CANDIDATOS, visto

    assert visto["frenados"] == [], visto


def test_encendida_solo_pasa_el_que_sube() -> None:

    from src.analysis.la_regla_de_la_rampa import ENV, mira_si_sube

    with _Interruptores(**{ENV: "1"}):
        visto = mira_si_sube(CANDIDATOS)

    assert visto["activa"] is True, visto

    assert [f["id"] for f in visto["siguen"]] == [1], visto

    frenados = {f["id"]: f for f in visto["frenados"]}

    assert sorted(frenados) == [2, 3, 4], frenados

    assert frenados[2]["direccion"] == "BAJA", frenados

    assert frenados[3]["direccion"] == "QUIETO", frenados

    assert frenados[4]["direccion"] == "SIN_DATO", frenados

    assert "no sube" in frenados[2]["reason"], frenados


def test_en_el_carril_zubeldia_bajando_no_se_puja() -> None:

    from src.analysis.la_regla_de_compra import ENV_CARRIL
    from src.analysis.la_regla_de_la_rampa import ENV
    from src.analysis.test_el_carril_mira_si_juega_v1 import (
        TITULAR,
        _vuelta,
    )

    bajando = {**TITULAR, "name": "Zubeldia", "price_increment": -10000}
    subiendo = {**bajando, "price_increment": 10000}

    # Produccion: la de jugar puesta en el carril. Mas la rampa.
    with _Interruptores(**{ENV_CARRIL: "1", ENV: "1"}):
        frenado, salida = _vuelta(bajando)
        pujado, puesta = _vuelta(subiendo)

    assert frenado.pujas == [], (
        "con la rampa puesta, el carril puja por un jugador cuyo "
        "precio baja"
    )

    assert salida.get("blocked_by") == "NO_SUBE", salida

    assert salida.get("frenados_por_no_subir"), salida

    # DISTINGUE: el mismo, subiendo, si se puja.
    assert pujado.pujas, (
        "con la rampa puesta, el carril no puja por un jugador que "
        f"sube: {puesta.get('reason')}"
    )


def test_la_subasta_copia_el_ultimo_cambio_de_precio() -> None:

    from src.analysis.la_subasta import lectura_del_estado

    estado = {
        "acquisition": {
            "targets": [
                {"id": 7, "name": "Sube", "market_price": 1000000,
                 "price_increment": 20000},
            ],
        },
    }

    lectura = lectura_del_estado(estado)

    candidatos = lectura.get("candidatos") or []

    assert candidatos, lectura

    assert candidatos[0].get("price_increment") == 20000, candidatos


TESTS = [
    test_apagada_no_frena_a_nadie,
    test_encendida_solo_pasa_el_que_sube,
    test_en_el_carril_zubeldia_bajando_no_se_puja,
    test_la_subasta_copia_el_ultimo_cambio_de_precio,
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
        f"LA REGLA DE LA RAMPA V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
