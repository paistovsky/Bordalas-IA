"""
El ensayo no escribe en Biwenger. Ni una vez, por ninguna puerta.

QUE SE PRUEBA (27/09/2026)

    `BORDALAS_ENSAYO=1` convierte a Pepe en un ensayo: lee Biwenger de
    verdad y no escribe nada. Todas las escrituras pasan por los metodos de
    `BiwengerWriteClient` (siete, y la racha desde el 28/09), asi que
    esta guardia llama a LOS OCHO con execute=True y comprueba:

        1. Con el ensayo puesto, la sesion HTTP no recibe NI UNA
           escritura (post, put, delete, patch), y las siete quedan
           apuntadas en el libro del ensayo.
        2. Sin el ensayo, la misma llamada SI escribe. Sin esto, la
           guardia solo probaria que el cliente esta roto, no que el
           candado distingue.

    Sin red, sin login y sin tocar `data/`: el libro del ensayo va a un
    temporal. Pone y quita ella misma el interruptor (doctrina 104).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


import src.biwenger.write_client as escritura              # noqa: E402


class _Respuesta:
    status_code = 200

    def json(self):
        return {"status": 200}

    text = '{"status": 200}'


class _SesionEspia:
    """Apunta cada escritura que le llega. No sale a la red."""

    def __init__(self):
        self.escrituras = []
        self.headers = {}

    def _apunta(self, metodo):
        def llamada(url, *args, **kwargs):
            self.escrituras.append((metodo, url))
            return _Respuesta()
        return llamada

    def __getattr__(self, nombre):
        if nombre in {"post", "put", "delete", "patch"}:
            return self._apunta(nombre)
        raise AttributeError(nombre)


class _ClienteFalso:
    BASE_URL = "https://biwenger.invalid/api/v2"

    def __init__(self):
        self.session = _SesionEspia()


def _escritor():
    """Un BiwengerWriteClient sin login ni red."""

    cliente = object.__new__(escritura.BiwengerWriteClient)
    cliente.client = _ClienteFalso()
    cliente.version = "0"
    cliente.league_id = 1
    cliente.user_id = 2
    cliente.league = {}
    return cliente


def _las_siete(cliente):
    """Llama a las ocho escrituras con execute=True."""

    return [
        cliente.place_bid(player_id=10, amount=1_000_000, execute=True),
        cliente.counter_offer(offer_id=20, amount=900_000, execute=True),
        cliente.cancel_bid(offer_id=30, execute=True),
        cliente.accept_offer(offer_id=40, execute=True),
        cliente.reject_offer(offer_id=50, execute=True),
        cliente.list_player_for_sale(
            player_id=60, price=2_000_000, execute=True
        ),
        cliente.save_lineup(
            player_ids=list(range(100, 111)),
            formation="4-4-2",
            execute=True,
        ),
        # La octava (28/09): cobrar la racha diaria.
        cliente.redeem_daily_streak(league_id=1, execute=True),
    ]


class _Ensayo:
    def __init__(self, puesto: bool):
        self.puesto = puesto

    def __enter__(self):
        self.antes = os.environ.get(escritura.ENSAYO_ENV)
        self.libro_antes = escritura.ESCRITURAS_DEL_ENSAYO
        self.tmp = tempfile.TemporaryDirectory()
        escritura.ESCRITURAS_DEL_ENSAYO = str(
            Path(self.tmp.name) / "escrituras.jsonl"
        )
        if self.puesto:
            os.environ[escritura.ENSAYO_ENV] = "1"
        else:
            os.environ.pop(escritura.ENSAYO_ENV, None)
        return self

    def __exit__(self, *_):
        escritura.ESCRITURAS_DEL_ENSAYO = self.libro_antes
        if self.antes is None:
            os.environ.pop(escritura.ENSAYO_ENV, None)
        else:
            os.environ[escritura.ENSAYO_ENV] = self.antes
        self.tmp.cleanup()


def test_en_ensayo_no_sale_ni_una_escritura() -> None:

    with _Ensayo(puesto=True):
        cliente = _escritor()
        salidas = _las_siete(cliente)

        assert cliente.client.session.escrituras == [], (
            "con BORDALAS_ENSAYO=1 salieron escrituras a Biwenger: "
            f"{cliente.client.session.escrituras}"
        )

        assert all(s.get("sent") is False for s in salidas), salidas

        libro = Path(escritura.ESCRITURAS_DEL_ENSAYO)
        apuntadas = [
            json.loads(linea)
            for linea in libro.read_text(encoding="utf-8").splitlines()
        ]

        assert len(apuntadas) == 8, (
            f"el ensayo tenia que apuntar las 8 escrituras y apunto "
            f"{len(apuntadas)}"
        )


def test_sin_ensayo_si_escribe() -> None:

    with _Ensayo(puesto=False):
        cliente = _escritor()
        cliente.place_bid(player_id=10, amount=1_000_000, execute=True)

        assert cliente.client.session.escrituras, (
            "sin el ensayo, place_bid con execute=True no escribio: el "
            "candado estaria cerrando tambien la produccion"
        )

        assert not Path(escritura.ESCRITURAS_DEL_ENSAYO).exists(), (
            "sin el ensayo no se debe apuntar nada en su libro"
        )


TESTS = [
    test_en_ensayo_no_sale_ni_una_escritura,
    test_sin_ensayo_si_escribe,
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
