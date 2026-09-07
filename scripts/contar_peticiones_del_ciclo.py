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

    # Y LA OTRA SUSTITUCION, QUE ME COSTO LA VERJA (07/09/2026)
    #
    #     Los colectores no solo piden: ESCRIBEN. Al ejecutarlos
    #     aqui dejaron en `data/` un snapshot con tres jugadores
    #     de mentira, y `test_futbolfantasy_source_v12` -que coge
    #     el snapshot mas reciente- se puso rojo con un `0`.
    #
    #     Una sonda que deja estado detras es peor que una que
    #     lo lee: lo lee el siguiente que pase. Asi que los
    #     directorios de salida se mandan a un temporal que se
    #     borra al terminar, y `data/` no se toca.
    import tempfile

    from pathlib import Path

    from src.collectors import (
        board_history_collector as tablon_mod,
    )
    from src.collectors import league_collector as liga_mod

    temporal = tempfile.TemporaryDirectory(
        prefix="bordalas_recuento_"
    )

    fuera = Path(temporal.name)

    (fuera / "rival_intelligence").mkdir(
        parents=True, exist_ok=True
    )

    salidas_originales = (
        liga_mod.DATA_DIR,
        tablon_mod.DATA_DIR,
        tablon_mod.BOARD_FILE,
        tablon_mod.BOARD_RAW_FILE,
    )

    liga_mod.DATA_DIR = fuera
    tablon_mod.DATA_DIR = fuera / "rival_intelligence"
    tablon_mod.BOARD_FILE = (
        tablon_mod.DATA_DIR / "board_events.json"
    )
    tablon_mod.BOARD_RAW_FILE = (
        tablon_mod.DATA_DIR / "board_latest_raw.json"
    )

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

        (
            liga_mod.DATA_DIR,
            tablon_mod.DATA_DIR,
            tablon_mod.BOARD_FILE,
            tablon_mod.BOARD_RAW_FILE,
        ) = salidas_originales

        temporal.cleanup()

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

    proyeccion(snapshot, tablon)


# ============================================================
# EL NUMERO QUE DECIDE
# ============================================================
#
#     "Cuantas quedarian" no puede ser una frase: tiene que ser
#     una resta que se pueda repetir. Cada paso lleva lo que
#     ahorra y de donde sale ese ahorro.


# Vueltas al dia con el cron de siempre: "7,37 * * * *".
VUELTAS_HOY = 48


# Vueltas con el cron propuesto. Ver el informe para la linea.
VUELTAS_PROPUESTAS = 24


# Cuantos de los 7 managers cambian de plantilla en un dia.
#
# MEDIDO, no supuesto (07/09/2026): sobre los 30 movimientos del
# tablon de la liga -del 04/09 al 07/09- se movieron 4, 5, 2 y 1
# managers cada dia. Media 3.
#
# Importa porque la plantilla de un rival SOLO cambia cuando
# ficha o vende, y eso lo dice el tablon, que cuesta UNA
# peticion. Hoy se piden los 7 perfiles 48 veces al dia por si
# acaso.
MANAGERS_QUE_SE_MUEVEN_AL_DIA = 3


# Lo que solo cambia en el reset de las 07:00, o menos.
# `catalogo` son los precios; `league` la lista de managers;
# `rounds` la jornada.
CACHEABLES_AL_DIA = {
    "GET /competitions/la-liga/data": 1,
    "GET /league": 1,
    "GET /rounds/league": 1,
}


def proyeccion(snapshot: int, tablon: int) -> None:
    """
    De lo medido a lo propuesto, paso a paso.

    Nunca lanza: si algo no cuadra lo dice y sigue.
    """

    try:
        ahora_ciclo = snapshot + 2 * tablon

        print()
        print("=" * 70)
        print("EL NUMERO QUE DECIDE")
        print("=" * 70)

        # ---------------------------------------------------
        # PASO A: quitar lo que se pide dos veces
        # ---------------------------------------------------
        #
        #     Sin cachear nada y sin perder un solo dato: la
        #     segunda colecta del tablon, el catalogo duplicado
        #     dentro del snapshot, y compartir el cliente entre
        #     los dos colectores en vez de hacer dos logins.
        paso_a = ahora_ciclo - tablon - 1 - 2

        # ---------------------------------------------------
        # PASO B: cachear lo que solo cambia en el reset
        # ---------------------------------------------------
        #
        #     Lo que queda por ciclo despues de sacar los
        #     cacheables y los perfiles de rivales.
        cacheables_por_ciclo = len(CACHEABLES_AL_DIA)

        perfiles_por_ciclo = 7

        paso_b_ciclo = (
            paso_a - cacheables_por_ciclo - perfiles_por_ciclo
        )

        extras_al_dia = (
            sum(CACHEABLES_AL_DIA.values())
            + MANAGERS_QUE_SE_MUEVEN_AL_DIA
        )

        filas = [
            (
                "AHORA (medido)",
                ahora_ciclo,
                VUELTAS_HOY,
                0,
                "el ciclo tal cual esta hoy",
            ),
            (
                "A. sin duplicados",
                paso_a,
                VUELTAS_HOY,
                0,
                "misma informacion, menos llamadas",
            ),
            (
                "B. + cache al reset",
                paso_b_ciclo,
                VUELTAS_HOY,
                extras_al_dia,
                "lo que solo cambia a las 07:00",
            ),
            (
                "C. + cron de 24",
                paso_b_ciclo,
                VUELTAS_PROPUESTAS,
                extras_al_dia,
                "vueltas donde pasan cosas",
            ),
        ]

        print()
        print(
            f"  {'PASO':<22}{'x CICLO':>9}{'VUELTAS':>9}"
            f"{'+DIA':>7}{'AL DIA':>9}   {'AHORRO':>8}"
        )
        print("  " + "-" * 68)

        base = None

        for nombre, ciclo, vueltas, extra, nota in filas:

            al_dia = ciclo * vueltas + extra

            if base is None:
                base = al_dia
                ahorro = ""

            else:
                ahorro = f"{100 * (base - al_dia) / base:5.1f} %"

            print(
                f"  {nombre:<22}{ciclo:>9}{vueltas:>9}"
                f"{extra:>7}{al_dia:>9}   {ahorro:>8}"
            )

        final = paso_b_ciclo * VUELTAS_PROPUESTAS + extras_al_dia

        print()
        print(
            f"  DE {base} A {final} PETICIONES AL DIA "
            f"({100 * (base - final) / base:.0f} % menos)."
        )
        print()
        print(
            "  El paso A es el que mas pesa y el unico que no "
            "cambia nada de lo que Pepe ve."
        )
        print(
            f"  El cron es el que menos: {VUELTAS_PROPUESTAS} "
            f"vueltas de {ahora_ciclo} peticiones seguirian "
            f"siendo {VUELTAS_PROPUESTAS * ahora_ciclo} al dia."
        )

    except Exception as error:                      # noqa: BLE001
        print(f"  No se pudo proyectar: {error}")


if __name__ == "__main__":
    main()
