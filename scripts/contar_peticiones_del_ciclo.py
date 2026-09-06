"""
Cuantas peticiones hace un ciclo, ejecutando el codigo de verdad.

POR QUE NO BASTA CON CONTARLAS LEYENDO

    Se puede sumar a mano leyendo `collect_league_snapshot` y
    `collect_board_history`, y sale 32. Pero una suma a mano se
    equivoca en silencio, y ademas caduca: la siguiente llamada
    que alguien meta dentro de un bucle no la va a ver nadie.

    Esto ejecuta los colectores DE VERDAD contra una sesion de
    mentira que devuelve payloads minimos, y cuenta lo que
    piden. Si mañana alguien añade una llamada, este numero
    sube solo.

NI UNA LLAMADA A BIWENGER

    La sesion se sustituye antes de construir el cliente. No
    sale un solo byte a la red, y no hacen falta credenciales
    validas.

COMO SE USA

    python -m scripts.contar_peticiones_del_ciclo
"""

from __future__ import annotations

import json
import os
import re


# Los managers de la liga. El numero importa: los perfiles se
# piden UNO A UNO, asi que cada manager es una peticion.
MANAGERS = 7


class RespuestaFalsa:

    def __init__(self, cuerpo: dict):
        self.status_code = 200
        self.headers = {}
        self._cuerpo = cuerpo

    def raise_for_status(self):
        return None

    def json(self):
        return self._cuerpo


def _jugadores(cuantos: int = 3) -> dict:
    return {
        str(1000 + n): {
            "id": 1000 + n,
            "name": f"Jugador {n}",
            "slug": f"jugador-{n}",
            "price": 1_000_000,
            "priceIncrement": 0,
            "position": 3,
            "teamID": 1,
            "status": "ok",
            "points": 10,
            "pointsLastSeason": 50,
        }
        for n in range(cuantos)
    }


def cuerpo_para(url: str) -> dict:
    """
    El payload minimo que cada endpoint tiene que devolver para
    que el colector siga adelante.

    No pretende parecerse a Biwenger: solo tener las claves que
    el codigo lee, para que llegue hasta la ultima peticion.
    """

    if "/auth/login" in url:
        return {"token": "de-mentira"}

    if "/account" in url:
        return {
            "status": 200,
            "data": {
                "leagues": [
                    {
                        "id": 1,
                        "name": "Liga",
                        "user": {"id": 99, "name": "Pepe"},
                    }
                ]
            },
        }

    if "/competitions/la-liga/data" in url:
        return {"data": {"players": _jugadores()}}

    if "/market" in url:
        return {
            "status": 200,
            "data": {
                "status": {"balance": 1_000_000},
                "sales": [],
                "offers": [],
            },
        }

    if "/rounds/league" in url:
        return {"status": 200, "data": {}}

    if re.search(r"/league/\d+/board", url):
        return {"status": 200, "data": []}

    if re.search(r"/user/\d+/finances", url):
        return {"status": 200, "data": {}}

    if re.search(r"/user/\d+", url):
        return {"status": 200, "data": {"id": 1, "players": []}}

    if url.rstrip("/").endswith("/league"):
        return {
            "status": 200,
            "data": {
                "users": [
                    {"id": n, "name": f"Manager {n}"}
                    for n in range(1, MANAGERS + 1)
                ]
            },
        }

    if "/user" in url:
        return {
            "status": 200,
            "data": {"players": [], "lineup": {}},
        }

    return {"status": 200, "data": {}}


class SesionFalsa:

    def __init__(self):
        self.headers = {}

    def _responder(self, url, *a, **k):
        return RespuestaFalsa(cuerpo_para(str(url)))

    get = _responder
    post = _responder
    put = _responder
    delete = _responder


def main() -> None:

    # Credenciales de mentira: el cliente las exige en el
    # constructor y aqui no se usa ninguna.
    os.environ.setdefault("BIWENGER_USERNAME", "no-se-usa")
    os.environ.setdefault("BIWENGER_PASSWORD", "no-se-usa")

    import requests

    from src.biwenger import peticiones

    # LA SUSTITUCION, ANTES DE CONSTRUIR NADA
    #
    #     El cliente envuelve `self.session` en su constructor,
    #     asi que si se sustituye `requests.Session` antes, lo
    #     que se envuelve -y se cuenta- es la de mentira.
    original = requests.Session
    requests.Session = SesionFalsa

    try:
        peticiones.reiniciar()

        from src.collectors.board_history_collector import (
            collect_board_history,
        )
        from src.collectors.league_collector import (
            collect_league_snapshot,
        )

        print("Ejecutando collect_league_snapshot()...")

        antes = peticiones.CONTADOR.total()

        try:
            collect_league_snapshot()

        except Exception as error:                  # noqa: BLE001
            print(f"  (paro en: {type(error).__name__}: {error})")

        snapshot = peticiones.CONTADOR.total() - antes

        print(f"  -> {snapshot} peticiones")

        print()
        print("Ejecutando collect_board_history()...")

        antes = peticiones.CONTADOR.total()

        try:
            collect_board_history()

        except Exception as error:                  # noqa: BLE001
            print(f"  (paro en: {type(error).__name__}: {error})")

        tablon = peticiones.CONTADOR.total() - antes

        print(f"  -> {tablon} peticiones")

    finally:
        requests.Session = original

    cuenta = peticiones.resumen()

    print()
    print("=" * 70)
    print("UN CICLO COMPLETO")
    print("=" * 70)
    print()
    print(f"  refresh_snapshot            {snapshot:>4}")
    print(f"  colecta del tablon          {tablon:>4}")
    print(
        f"  colecta del tablon (2a vez) {tablon:>4}"
        f"   <-- duplicada, ver el informe"
    )
    print("  " + "-" * 34)
    print(f"  TOTAL POR CICLO             {snapshot + 2 * tablon:>4}")
    print()
    print(
        f"  Con cron cada 30 min (48 vueltas/dia): "
        f"{48 * (snapshot + 2 * tablon):,}".replace(",", ".")
        + " al dia"
    )

    print()
    print("POR ENDPOINT (una sola colecta de cada)")
    print("-" * 70)

    for endpoint, cuantas in cuenta["by_endpoint"].items():
        marca = "   <-- repetida" if cuantas > 1 else ""
        print(f"  {cuantas:>3}  {endpoint}{marca}")

    print()
    print(
        f"  repetidas en esta pasada: {cuenta['repeated']} de "
        f"{cuenta['total']} ({cuenta['repeated_percent']} %)"
    )

    print()
    print("  Ni una llamada ha salido a la red.")


if __name__ == "__main__":
    main()
