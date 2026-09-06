"""
Un almacen de precios de mentira, siempre igual.

POR QUE EXISTE (17/09/2026, produccion caida)

    Dos guardias de la verja leian el almacen REAL
    -`data/autopilot/price_history.json`-. En el disco del dueño
    ese fichero tiene seis dias; en la cache de Actions tiene los
    que lleve produccion acumulados.

    Mismo codigo, misma verja, dos veredictos. Verde en local,
    rojo en CI, y el ciclo de produccion parado desde las 11:00.

    `data/` esta entero en `.gitignore`: ahi no hay ni un fixture,
    solo estado mutable. Una comprobacion que lee de ahi no
    comprueba el codigo: mide el mercado del dia.

QUE CONSTRUYE ESTO

    Series diarias inventadas, con la forma exacta que hace falta
    para comprobar el CODIGO:

        CAE      120 jugadores que bajan todos los dias
        1-2 %     60 que suben al 1,5 % diario
        2-4 %     60 que suben al 3 % diario
        > 4 %     60 que suben al 6 % diario

    Seis puntos por jugador, uno al dia, exactamente como la
    ventana que tenia el almacen cuando se escribieron estas
    guardias. Con seis puntos:

        - los horizontes de 5, 7 y 10 no caben y salen vacios;
        - a horizonte 3 la racha maxima medible es 2, porque una
          racha de `n` consume `n` dias por delante.

    Las dos cosas que las guardias comprueban, y las dos
    deducidas de la ventana en vez de escritas a mano.

LO QUE ESTE FIXTURE NO PUEDE SOSTENER

    Nada sobre el mercado de verdad. Que la via TENER pague, o
    que los tres del informe del 14/09 dejen de compensar, son
    conclusiones sobre datos de produccion: se miden en el
    informe, no en la verja.

    Una verja que vuelve a medir el mercado en cada ejecucion no
    es una verja. Es lo que acaba de tirar produccion.
"""

from __future__ import annotations

import json

from pathlib import Path


# Un dia exacto entre punto y punto: las rachas y las tasas
# diarias se calculan contra el dia anterior.
DIA = 86_400

# 2026-08-12T00:00:00Z, el primer dia del almacen que habia
# cuando se escribieron estas guardias.
ORIGEN = 1_786_492_800


# Seis puntos = cinco tasas diarias. De ahi salen, sin escribir
# ningun numero a mano, las dos propiedades que se comprueban:
# horizontes largos vacios y racha maxima 2 a horizonte 3.
PUNTOS = 6


# Cada grupo cae en un tramo de tasa distinto, y las medianas
# quedan ordenadas de menos a mas por construccion.
GRUPOS = (
    ("CAE", -0.02, 120),
    ("1-2 %", 0.015, 60),
    ("2-4 %", 0.030, 60),
    ("> 4 %", 0.060, 60),
)


PRECIO_BASE = 1_000_000


def build_store(puntos: int = PUNTOS) -> dict:
    """
    El almacen entero, sin azar y sin leer nada del disco.

    Dos llamadas devuelven exactamente lo mismo, hoy y dentro de
    un mes.
    """

    jugadores = {}

    player_id = 1000

    for _, tasa, cuantos in GRUPOS:

        for indice in range(cuantos):

            player_id += 1

            # Precios de partida distintos para que las series no
            # sean once veces la misma, pero deterministas.
            precio = PRECIO_BASE + indice * 10_000

            tiempos = []
            precios = []

            for dia in range(puntos):
                tiempos.append(ORIGEN + dia * DIA)
                precios.append(int(round(precio)))
                precio = precio * (1.0 + tasa)

            jugadores[str(player_id)] = {
                "t": tiempos,
                "p": precios,
            }

    return {
        "version": 1,
        "updated_at": "2026-08-17T00:00:00",
        "players": jugadores,
    }


def write_store(destino: Path, puntos: int = PUNTOS) -> Path:
    """Deja el almacen de mentira en `destino` y lo devuelve."""

    destino.parent.mkdir(parents=True, exist_ok=True)

    destino.write_text(
        json.dumps(build_store(puntos)),
        encoding="utf-8",
    )

    return destino


class almacen_de_mentira:
    """
    Redirige el retrotest a un almacen inventado, y lo deshace.

    Se usa como contexto:

        with almacen_de_mentira() as almacen:
            resultado = backtest(almacen)

    Ademas de escribir el fichero, apunta `hold_backtest.STORE` a
    el, porque `hold_value` llama al retrotest sin pasarle ruta.
    Al salir lo devuelve todo a su sitio, incluida la cache de
    calibracion: una guardia que deja la cache envenenada rompe a
    la siguiente.
    """

    def __init__(self, puntos: int = PUNTOS):
        self.puntos = puntos
        self._temporal = None
        self._store_original = None

    def __enter__(self) -> Path:

        import tempfile

        from src.analysis import hold_backtest
        from src.analysis.hold_value import reset_calibration_cache

        self._temporal = tempfile.TemporaryDirectory(
            prefix="bordalas-fixture-"
        )

        ruta = write_store(
            Path(self._temporal.name) / "price_history.json",
            self.puntos,
        )

        self._store_original = hold_backtest.STORE
        hold_backtest.STORE = ruta

        reset_calibration_cache()

        return ruta

    def __exit__(self, *_) -> bool:

        from src.analysis import hold_backtest
        from src.analysis.hold_value import reset_calibration_cache

        hold_backtest.STORE = self._store_original

        reset_calibration_cache()

        if self._temporal is not None:
            self._temporal.cleanup()
            self._temporal = None

        return False
