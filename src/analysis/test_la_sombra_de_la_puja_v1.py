"""
La sombra de la puja no escribe.

LO QUE SE PROTEGE (23/09/2026)

    «Hay que ver lo que haria Pepe, porque no me fio.» La sombra
    calcula a quien pujaria y cuanto con los candados levantados.

    1. Con el interruptor puesto, la solvencia en rojo, la ventana
       cerrada y la caja a cero, la lista SALE, con cada candado.
    2. Ni una escritura contra Biwenger: los siete metodos que
       escriben de `BiwengerWriteClient` revientan si se les llama.
    3. El interruptor se LEE, no se apaga: el entorno sale como
       entro.
    4. Ordenada de mayor a menor puja.
    5. Las pujas son las de `plan_del_reset` en su camino normal:
       la sombra no tiene formula propia.

LA GUARDIA MUERDE SI EL CASO NO TIENE CANDIDATOS

    Cero nombres es lo que devuelve un modulo roto. Sin candidatos,
    la 1 daria verde probando nada: lo primero es exigirlos.

NO LEE EL MUNDO: ni `data/`, ni red, ni reloj.

COMO SE USA

    python -m src.analysis.test_la_sombra_de_la_puja_v1
"""

from __future__ import annotations

import os

# EL ENTORNO NO DECIDE ESTA GUARDIA (doctrina 104). Los que cierran
# la cesta se quitan; el de la subasta lo pone la prueba que lo mide.
for _nombre in (
    "BORDALAS_SIN_SUBASTA",
    "BORDALAS_SIN_REVENTA",
    "BORDALAS_SOLVENCIA_POR_SU_PLAZO",
    "BORDALAS_CUPO_POR_VENTANA",
    "BORDALAS_CESTA_SOLO_EL_SUELO",
):
    os.environ.pop(_nombre, None)

from src.analysis.la_sombra_de_la_puja import (  # noqa: E402
    FUERA_DE_VENTANA,
    INTERRUPTOR,
    SOLVENCIA,
    TOPE_DE_LA_VENTANA,
    la_sombra_de_la_puja,
)
from src.analysis.la_subasta import (  # noqa: E402
    DISABLE_ENV,
    VENTANA_MINUTOS,
    plan_del_reset,
)
from src.biwenger.write_client import BiwengerWriteClient  # noqa: E402


ESCRITURAS = (
    "place_bid",
    "counter_offer",
    "cancel_bid",
    "accept_offer",
    "reject_offer",
    "list_player_for_sale",
    "save_lineup",
)


def _candidatos() -> list:
    return [
        {
            "id": 100 + i,
            "name": f"Jugador {i}",
            "market_price": 400_000 + 100_000 * i,
            "team_id": 1 + i,
            "starter_probability": 80.0,
            "hierarchy_value": 60,
        }
        for i in range(4)
    ]


def _lectura(**cambios) -> dict:
    """La vuelta de hoy: todo cerrado."""

    lectura = {
        "candidatos": _candidatos(),
        "prima_de_reventa": 0.0237,
        "presupuesto": 5_185_150,
        "fichas_libres": 6,
        "caja_libre": 0,
        "seconds_to_reset": 79_735,
        "solvency_clock": {"state": "CUBIERTO", "deficit": 1_525_782},
        "plantilla": [],
        "bloqueo_temporal": None,
        "max_por_club": 4,
    }

    lectura.update(cambios)

    return lectura


class _SinManos:
    """Quita las manos al cliente mientras dura el `with`."""

    def __enter__(self):
        self.antes = {}
        self.llamadas = []

        for metodo in ESCRITURAS:
            self.antes[metodo] = getattr(BiwengerWriteClient, metodo)

            def revienta(*_a, _m=metodo, **_k):
                self.llamadas.append(_m)
                raise AssertionError(f"la sombra ha llamado a {_m}")

            setattr(BiwengerWriteClient, metodo, revienta)

        return self

    def __exit__(self, *_):
        for metodo, original in self.antes.items():
            setattr(BiwengerWriteClient, metodo, original)


def _exige_candidatos(lectura) -> None:
    assert lectura["candidatos"], (
        "el caso no tiene candidatos: esta guardia no prueba nada"
    )


# ============================================================
# 1-3. CON TODO CERRADO, SALE LA LISTA Y NO SE ESCRIBE
# ============================================================

def test_la_sombra_no_escribe() -> None:

    lectura = _lectura()

    _exige_candidatos(lectura)

    antes = os.environ.get(DISABLE_ENV)

    try:
        os.environ[DISABLE_ENV] = "1"

        entorno = dict(os.environ)

        with _SinManos() as manos:
            sombra = la_sombra_de_la_puja(lectura)

        assert manos.llamadas == [], manos.llamadas

        assert dict(os.environ) == entorno, (
            "la sombra ha tocado el entorno: un interruptor se lee, "
            "no se apaga"
        )

        assert sombra["available"], sombra["reason"]
        assert sombra["observer_only"] is True

        assert sombra["bids"], (
            f"con candidatos y todo cerrado la sombra sale vacia: "
            f"{sombra['reason']}"
        )

        candados = {c["candado"] for c in sombra["candados"]}

        for esperado in (
            INTERRUPTOR,
            SOLVENCIA,
            FUERA_DE_VENTANA,
            TOPE_DE_LA_VENTANA,
        ):
            assert esperado in candados, (esperado, candados)

        for fila in sombra["bids"]:
            assert set(fila["candados"]) == candados, fila

    finally:
        if antes is None:
            os.environ.pop(DISABLE_ENV, None)
        else:
            os.environ[DISABLE_ENV] = antes


# ============================================================
# 4. DE MAYOR A MENOR PUJA
# ============================================================

def test_de_mayor_a_menor_puja() -> None:

    lectura = _lectura()

    _exige_candidatos(lectura)

    sombra = la_sombra_de_la_puja(lectura)

    pujas = [f["bid"] for f in sombra["bids"]]

    assert len(pujas) >= 2, (
        f"con una sola fila no se puede probar el orden: {pujas}"
    )
    assert pujas == sorted(pujas, reverse=True), pujas

    for fila in sombra["bids"]:
        assert fila["prima"] == fila["bid"] - fila["price"], fila


# ============================================================
# 5. LA MISMA CUENTA QUE PUJA
# ============================================================

def test_las_pujas_son_las_del_plan() -> None:

    lectura = _lectura()

    _exige_candidatos(lectura)

    sombra = la_sombra_de_la_puja(lectura)

    # El plan con todo abierto de verdad: dentro de la ventana,
    # sin deficit y con caja.
    abierto = plan_del_reset(
        **{
            **lectura,
            "solvency_clock": {"state": "SIN_DEUDA", "deficit": 0},
            "seconds_to_reset": VENTANA_MINUTOS * 60 // 2,
            "caja_libre": 10_000_000,
        },
        en_vivo=False,
    )

    esperadas = sorted(
        (int(b["id"]), int(b["bid"])) for b in abierto["bids"]
    )

    assert esperadas, "el plan abierto no puja: el caso no prueba nada"

    assert sorted(
        (f["id"], f["bid"]) for f in sombra["bids"]
    ) == esperadas, (sombra["bids"], esperadas)


# ============================================================
# Y SIN CANDADOS, LO DICE
# ============================================================

def test_sin_candados_lo_dice() -> None:

    sombra = la_sombra_de_la_puja(
        _lectura(
            seconds_to_reset=VENTANA_MINUTOS * 60 // 2,
            solvency_clock={"state": "SIN_DEUDA", "deficit": 0},
            caja_libre=10_000_000,
        )
    )

    assert sombra["bids"], sombra["reason"]
    assert sombra["candados"] == [], sombra["candados"]
    assert "Sin candados" in sombra["reason"], sombra["reason"]


TESTS = [
    test_la_sombra_no_escribe,
    test_de_mayor_a_menor_puja,
    test_las_pujas_son_las_del_plan,
    test_sin_candados_lo_dice,
]


def main() -> None:

    print()
    print("=" * 60)
    print("LA SOMBRA DE LA PUJA V1")
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
