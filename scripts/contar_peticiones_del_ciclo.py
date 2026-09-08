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


# Lo que costaba una vuelta antes del paso A (07/09/2026), para
# poder enseñar el antes y el despues sin ir a buscarlo:
#
#     8 del snapshot -con el catalogo pedido dos veces-
#   + 12 de la colecta del tablon
#   + 12 de la MISMA colecta, otra vez
#   ----
#    32
ANTES_DEL_PASO_A = 32


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

    perfil = re.search(r"/user/(\d+)", url)

    if perfil:
        # EL ID DE VERDAD, NO UNO FIJO (07/09/2026)
        #
        #     Con un `id: 1` para todos, los siete perfiles se
        #     guardaban bajo la misma clave y la medicion de la
        #     cache salia mal: decia que se refrescaban seis
        #     cuando el codigo estaba haciendo lo correcto.
        #
        #     Un arnes que colapsa identidades mide otra cosa.
        return {
            "status": 200,
            "data": {
                "id": int(perfil.group(1)),
                "players": [],
            },
        }

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


class _entorno_de_mentira:
    """
    Todo lo que hace falta para ejecutar los colectores en seco.

    Sustituye la sesion por una falsa y manda TODA la escritura
    a un directorio temporal.

    LO SEGUNDO NO ES UN DETALLE (07/09/2026)

        Los colectores no solo piden: escriben. La primera
        version de esta sonda dejo en el estado un snapshot con
        tres jugadores de mentira, y
        `test_futbolfantasy_source_v12` -que coge el mas
        reciente- se puso rojo con un cero, en otro fichero y
        sin relacion aparente.

        Vive aqui, y no dentro de `main`, para que la guardia
        pueda usar exactamente el mismo montaje: si la sonda y
        la guardia midieran con arneses distintos, el numero de
        una no probaria nada sobre el otro.
    """

    def __init__(self):
        self.requests = None
        self.session_original = None
        self.temporal = None
        self.salidas = None

    def __enter__(self):

        import tempfile

        from pathlib import Path

        os.environ.setdefault("BIWENGER_USERNAME", "no-se-usa")
        os.environ.setdefault("BIWENGER_PASSWORD", "no-se-usa")

        import requests

        from src.biwenger import client as cliente_mod
        from src.biwenger import peticiones
        from src.collectors import (
            board_history_collector as tablon_mod,
        )
        from src.collectors import league_collector as liga_mod

        self.requests = requests
        self.session_original = requests.Session
        requests.Session = SesionFalsa

        self.temporal = tempfile.TemporaryDirectory(
            prefix="bordalas_recuento_"
        )

        fuera = Path(self.temporal.name)

        (fuera / "rival_intelligence").mkdir(
            parents=True, exist_ok=True
        )

        from src.biwenger import cache_del_reset as cache_mod

        self.cache_mod = cache_mod

        self.salidas = (
            liga_mod,
            tablon_mod,
            liga_mod.DATA_DIR,
            tablon_mod.DATA_DIR,
            tablon_mod.BOARD_FILE,
            tablon_mod.BOARD_RAW_FILE,
            tablon_mod.PROFILES_FILE,
            cache_mod.FICHERO,
        )

        liga_mod.DATA_DIR = fuera
        tablon_mod.DATA_DIR = fuera / "rival_intelligence"
        tablon_mod.BOARD_FILE = (
            tablon_mod.DATA_DIR / "board_events.json"
        )
        tablon_mod.BOARD_RAW_FILE = (
            tablon_mod.DATA_DIR / "board_latest_raw.json"
        )

        # La cache entre resets y los perfiles guardados: si no
        # se desvian, la sonda leeria -y escribiria- la cache de
        # produccion, y el numero saldria distinto segun la hora
        # a la que se ejecute.
        tablon_mod.PROFILES_FILE = (
            tablon_mod.DATA_DIR / "profiles_cache.json"
        )
        cache_mod.FICHERO = fuera / "cache_biwenger.json"

        # El cliente compartido es de una vuelta. Sin reiniciar,
        # la segunda medicion heredaria el login de la primera y
        # saldrian dos peticiones de menos.
        cliente_mod.reset_cliente_del_ciclo()

        peticiones.reiniciar()

        self.peticiones = peticiones

        return self

    def __exit__(self, *_):

        from src.biwenger import client as cliente_mod

        self.requests.Session = self.session_original

        (
            liga_mod,
            tablon_mod,
            liga_dir,
            tablon_dir,
            board_file,
            board_raw,
            profiles_file,
            cache_file,
        ) = self.salidas

        liga_mod.DATA_DIR = liga_dir
        tablon_mod.DATA_DIR = tablon_dir
        tablon_mod.BOARD_FILE = board_file
        tablon_mod.BOARD_RAW_FILE = board_raw
        tablon_mod.PROFILES_FILE = profiles_file
        self.cache_mod.FICHERO = cache_file

        cliente_mod.reset_cliente_del_ciclo()

        self.temporal.cleanup()

        return False


class _en_fase:
    """
    Fija la fase temporal sin tocar el reloj ni el calendario.

    La fase decide si el catalogo se cachea. Para medir las dos
    situaciones -martes cualquiera y dia de jornada- hay que
    poder ponerla, no esperar al viernes.
    """

    def __init__(self, fase: str | None):
        self.fase = fase
        self.original = None

    def __enter__(self):

        if self.fase is None:
            return self

        from src.biwenger import cache_del_reset as cache_mod

        self.original = cache_mod.fase_del_calendario
        cache_mod.fase_del_calendario = lambda *a, **k: self.fase

        return self

    def __exit__(self, *_):

        if self.original is not None:

            from src.biwenger import (
                cache_del_reset as cache_mod,
            )

            cache_mod.fase_del_calendario = self.original

        return False


def medir_un_ciclo(
    vueltas: int = 1,
    fase: str | None = None,
) -> dict:
    """
    Las peticiones de una vuelta, ejecutando los colectores.

    `vueltas` corre varias seguidas sobre la MISMA cache y
    devuelve lo que costo la ULTIMA. Con 1 se mide la primera
    del dia -cache vacia-; con 2 o mas, el estado de crucero,
    que es lo que se paga 47 de cada 48 veces.

    `{snapshot, board, total, by_endpoint, vueltas}`. Forma
    fija.

    Ni una llamada a la red, ni un byte escrito en el estado.
    """

    with _entorno_de_mentira() as entorno, _en_fase(fase):

        from src.biwenger import client as cliente_mod
        from src.collectors.board_history_collector import (
            collect_board_history,
        )
        from src.collectors.league_collector import (
            collect_league_snapshot,
        )

        contador = entorno.peticiones.CONTADOR

        snapshot = 0
        tablon = 0

        for vuelta in range(max(1, int(vueltas))):

            # Cada vuelta es un proceso nuevo en produccion: el
            # cliente compartido no cruza ciclos.
            cliente_mod.reset_cliente_del_ciclo()

            entorno.peticiones.reiniciar()

            contador = entorno.peticiones.CONTADOR

            antes = contador.total()

            try:
                collect_league_snapshot()

            except Exception:                       # noqa: BLE001
                pass

            snapshot = contador.total() - antes

            antes = contador.total()

            try:
                collect_board_history()

            except Exception:                       # noqa: BLE001
                pass

            tablon = contador.total() - antes

        resumen = entorno.peticiones.resumen()

    return {
        "snapshot": snapshot,
        "board": tablon,
        "total": snapshot + tablon,
        "by_endpoint": resumen.get("by_endpoint") or {},
        "vueltas": max(1, int(vueltas)),
        "fase": fase,
    }


def main() -> None:

    print("Midiendo la PRIMERA vuelta tras el reset...")

    primera = medir_un_ciclo(vueltas=1)

    print(
        f"  snapshot {primera['snapshot']} + tablon "
        f"{primera['board']} = {primera['total']}"
    )

    print()
    print("Midiendo una vuelta DE CRUCERO (martes, cache llena)...")

    crucero = medir_un_ciclo(vueltas=2, fase="NORMAL")

    print(
        f"  snapshot {crucero['snapshot']} + tablon "
        f"{crucero['board']} = {crucero['total']}"
    )

    print()
    print("Midiendo una vuelta EL DIA DE LA JORNADA...")

    jornada = medir_un_ciclo(
        vueltas=2, fase="HIGH_ATTENTION"
    )

    print(
        f"  snapshot {jornada['snapshot']} + tablon "
        f"{jornada['board']} = {jornada['total']}"
    )

    print()
    print("=" * 70)
    print("POR ENDPOINT")
    print("=" * 70)
    print()
    print(
        f"  {'ENDPOINT':<38}{'1a':>5}{'CRUCERO':>9}"
        f"{'JORNADA':>9}"
    )
    print("  " + "-" * 61)

    endpoints = sorted(
        set(primera["by_endpoint"])
        | set(crucero["by_endpoint"])
        | set(jornada["by_endpoint"])
    )

    for endpoint in endpoints:
        print(
            f"  {endpoint:<38}"
            f"{primera['by_endpoint'].get(endpoint, 0):>5}"
            f"{crucero['by_endpoint'].get(endpoint, 0):>9}"
            f"{jornada['by_endpoint'].get(endpoint, 0):>9}"
        )

    print()
    print("  Ni una llamada ha salido a la red.")

    proyeccion(
        primera["total"], crucero["total"], jornada["total"]
    )


# ============================================================
# EL NUMERO QUE DECIDE
# ============================================================
#
#     Ya no es una proyeccion: los pasos A y B estan puestos, y
#     esto MIDE lo que cuesta cada clase de vuelta.


def vueltas_al_dia() -> int:
    """
    Cuantas veces al dia corre el ciclo, LEIDO DEL WORKFLOW.

    Estaba escrito a mano -48- y el dueño lo bajo a una por hora
    el 08/09 tras el bloqueo. El numero del informe se quedo
    viejo sin que nadie se enterara: es la misma familia que
    todo lo demas.

    Solo lee. El workflow no se toca.

    Nunca lanza: si no se puede leer, devuelve el valor de
    siempre y lo dice quien llame.
    """

    try:
        import re

        from pathlib import Path

        fichero = (
            Path(__file__).parent.parent
            / ".github"
            / "workflows"
            / "bordalas-live.yml"
        )

        texto = fichero.read_text(encoding="utf-8")

        total = 0

        for linea in re.findall(
            r'-\s*cron:\s*"([^"]+)"', texto
        ):

            campos = linea.split()

            if len(campos) < 5:
                continue

            minutos, horas = campos[0], campos[1]

            def _cuantos(campo: str, tope: int) -> int:
                if campo == "*":
                    return tope
                cuenta = 0
                for trozo in campo.split(","):
                    if "-" in trozo:
                        a, b = trozo.split("-")[:2]
                        cuenta += int(b) - int(a) + 1
                    else:
                        cuenta += 1
                return cuenta

            total += _cuantos(minutos, 60) * _cuantos(horas, 24)

        return total or 48

    except Exception:                               # noqa: BLE001
        return 48


VUELTAS_AL_DIA = vueltas_al_dia()


# Cuantos de los 7 managers cambian de plantilla en un dia.
#
# MEDIDO (07/09/2026): sobre los 30 movimientos del tablon del
# 04 al 07 de septiembre se movieron 4, 5, 2 y 1 managers cada
# dia. Media 3.
#
# Cada uno cuesta UNA peticion extra el ciclo en que se entera.
MANAGERS_QUE_SE_MUEVEN_AL_DIA = 3


# Horas por jornada en que el catalogo se pide fresco:
# HIGH_ATTENTION (T-12 h) hasta el cierre. Sale de los listones
# de `matchday_calendar_engine.classify_phase`, no de una
# suposicion.
HORAS_FRESCAS_POR_JORNADA = 12


def proyeccion(
    primera: int, crucero: int, jornada: int | None = None
) -> None:
    """
    El antes y el despues, medidos.

    `primera` es la primera vuelta tras el reset -paga el
    catalogo, la jornada, la lista de managers y los siete
    perfiles-. `crucero` es cada una de las otras 47.

    Nunca lanza.
    """

    try:
        al_dia = (
            primera
            + crucero * (VUELTAS_AL_DIA - 1)
            + MANAGERS_QUE_SE_MUEVEN_AL_DIA
        )

        antes_al_dia = ANTES_DEL_PASO_A * VUELTAS_AL_DIA

        print()
        print("=" * 70)
        print("EL NUMERO QUE DECIDE")
        print("=" * 70)
        print()
        print(
            f"  {'':<26}{'x CICLO':>9}{'VUELTAS':>9}"
            f"{'AL DIA':>9}"
        )
        print("  " + "-" * 55)
        print(
            f"  {'ANTES (06/09)':<26}"
            f"{ANTES_DEL_PASO_A:>9}{VUELTAS_AL_DIA:>9}"
            f"{antes_al_dia:>9}"
        )
        print(
            f"  {'AHORA, primera del dia':<26}"
            f"{primera:>9}{1:>9}{primera:>9}"
        )
        print(
            f"  {'AHORA, las otras 47':<26}"
            f"{crucero:>9}{VUELTAS_AL_DIA - 1:>9}"
            f"{crucero * (VUELTAS_AL_DIA - 1):>9}"
        )
        print(
            f"  {'+ los que se mueven':<26}"
            f"{1:>9}{MANAGERS_QUE_SE_MUEVEN_AL_DIA:>9}"
            f"{MANAGERS_QUE_SE_MUEVEN_AL_DIA:>9}"
        )
        print("  " + "-" * 55)
        print(f"  {'TOTAL AL DIA':<26}{'':>9}{'':>9}{al_dia:>9}")

        print()
        print(
            f"  DE {antes_al_dia} A {al_dia} PETICIONES AL DIA "
            f"({100 * (antes_al_dia - al_dia) / antes_al_dia:.0f} % menos), "
            f"con el MISMO cron."
        )

        if jornada is not None and jornada != crucero:

            vueltas_frescas = int(
                HORAS_FRESCAS_POR_JORNADA
                * VUELTAS_AL_DIA
                / 24
            )

            extra = (jornada - crucero) * vueltas_frescas

            print()
            print(
                f"  EL DIA DE LA JORNADA el catalogo va fresco: "
                f"{jornada} por vuelta en vez de {crucero}."
            )
            print(
                f"  Son {HORAS_FRESCAS_POR_JORNADA} h por "
                f"jornada = {vueltas_frescas} vueltas = "
                f"+{extra} peticiones POR JORNADA."
            )
            print(
                f"  No cachearlo nunca costaria "
                f"{VUELTAS_AL_DIA} al dia."
            )

        print()
        print()
        print(
            f"  El cron actual son {VUELTAS_AL_DIA} vueltas al "
            f"dia, leidas del propio workflow."
        )
        print(
            "  El cron de la subasta (10/09) tiene el MISMO "
            "numero de vueltas:"
        )
        print(
            "  lo que cambia es donde caen, no cuantas son."
        )

    except Exception as error:                      # noqa: BLE001
        print(f"  No se pudo proyectar: {error}")


if __name__ == "__main__":
    main()
