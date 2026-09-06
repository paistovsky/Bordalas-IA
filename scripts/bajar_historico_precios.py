"""
El historico de precios de Biwenger, jugador a jugador.

POR QUE EXISTE (26/09/2026)

    El almacen que alimenta el retrotest lo escribe el ciclo cada
    seis horas y vive en la cache de Actions: 22 dias en
    produccion, 6 en el disco del dueño. Con 22 dias no se puede
    medir un horizonte de 10 con muestra, y con 6 no se puede
    medir nada.

    Pero Biwenger publica el precio de cada jugador dia a dia en
    su propia ficha:

        GET /players/la-liga/{slug}?fields=*,prices
        -> "prices": [[YYMMDD, precio], ...]   366 dias

    Es el MISMO concepto -precio de mercado por dia- de la fuente
    original y con un año de fondo en vez de tres semanas.

LO QUE NO ES

    No sustituye al almacen del ciclo. El almacen tiene lo que
    Pepe VIO cuando decidio, con su marca de tiempo; esto es la
    serie oficial cerrada. Para calibrar es mejor; para auditar
    una decision concreta, no.

QUE HACE Y QUE NO

    Solo GET, contra la ficha publica de cada jugador. No puja,
    no vende, no responde ofertas y no toca el almacen de
    produccion: escribe donde se le diga.

COMO SE USA

    python -m scripts.bajar_historico_precios <fichero_salida>
"""

from __future__ import annotations

import json
import sys
import time

from datetime import datetime
from pathlib import Path

from src.biwenger.client import BiwengerClient


# Entre peticion y peticion. Seiscientas y pico lecturas seguidas
# a la ficha publica no son un problema, pero tampoco hay ninguna
# prisa: esto se ejecuta una vez.
PAUSA = 0.15


# LO QUE PASO LA PRIMERA VEZ (26/09/2026)
#
#     A partir de la peticion 419 Biwenger empezo a devolver
#     error y lo hizo 160 veces seguidas, hasta el final del
#     alfabeto. El fichero salio con 418 jugadores y sin decir en
#     voz alta que los que faltaban NO eran aleatorios: eran
#     todos los de la cola alfabetica.
#
#     Una muestra que se corta por una letra no es una muestra
#     mas pequeña, es otra muestra. Asi que ahora: se reintenta
#     con espera creciente, y si aun asi falta gente se dice
#     cuanta y quienes.
REINTENTOS = 4
ESPERA_TRAS_FALLO = 5.0


def marca_de(dia_yymmdd) -> int | None:
    """
    `250906` -> el timestamp de ese dia a mediodia.

    Mediodia y no medianoche a proposito: el almacen del ciclo
    guarda la hora real de la lectura, y `load_series` agrupa por
    fecha local. Con las doce del mediodia ningun huso horario
    puede empujar un precio al dia de al lado.
    """

    try:
        texto = str(int(dia_yymmdd)).zfill(6)

        fecha = datetime(
            2000 + int(texto[0:2]),
            int(texto[2:4]),
            int(texto[4:6]),
            12,
            0,
        )

        return int(fecha.timestamp())

    except (TypeError, ValueError, OverflowError):
        return None


def main() -> None:

    salida = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else "historico_precios.json"
    )

    client = BiwengerClient()

    print("Iniciando sesion...")
    client.login()
    client.select_league()

    catalogo = client.get_player_catalog()

    fichas = [
        f
        for f in catalogo.values()
        if isinstance(f, dict) and f.get("slug")
    ]

    print(f"Jugadores en el catalogo: {len(fichas)}")

    # REANUDAR EN VEZ DE EMPEZAR DE CERO
    #
    #     Bajar 578 fichas cuesta un par de minutos y agota la
    #     paciencia del servidor. Si ya hay fichero, se conserva
    #     lo bueno y solo se piden los que faltan.
    almacen = {"players": {}}

    if salida.exists():
        try:
            previo = json.loads(salida.read_text(encoding="utf-8"))

            almacen["players"] = dict(
                (previo or {}).get("players") or {}
            )

            print(
                f"Reanudando: ya habia "
                f"{len(almacen['players'])} jugadores"
            )

        except Exception:                           # noqa: BLE001
            almacen = {"players": {}}

    fallos = []
    total_puntos = sum(
        len(f.get("t") or [])
        for f in almacen["players"].values()
    )

    for numero, ficha in enumerate(fichas, start=1):

        slug = ficha.get("slug")

        if str(ficha.get("id")) in almacen["players"]:
            continue

        precios = None

        for intento in range(REINTENTOS):

            try:
                respuesta = client.session.get(
                    f"{client.BASE_URL}/players/la-liga/{slug}",
                    params={"lang": "es", "fields": "*,prices"},
                    timeout=30,
                )

                respuesta.raise_for_status()

                datos = (respuesta.json() or {}).get("data") or {}

                precios = datos.get("prices") or []
                break

            except Exception as error:              # noqa: BLE001

                if intento == REINTENTOS - 1:
                    fallos.append(slug)
                    print(
                        f"  [{numero}] {slug}: "
                        f"{type(error).__name__}"
                    )

                else:
                    # Espera creciente: si el servidor esta
                    # limitando, insistir al mismo ritmo solo
                    # alarga el castigo.
                    time.sleep(
                        ESPERA_TRAS_FALLO * (intento + 1)
                    )

        if precios is None:
            time.sleep(PAUSA)
            continue

        marcas = []
        valores = []

        for par in precios:

            if not isinstance(par, (list, tuple)) or len(par) < 2:
                continue

            marca = marca_de(par[0])

            try:
                valor = int(par[1])

            except (TypeError, ValueError):
                continue

            if marca is None or valor <= 0:
                continue

            marcas.append(marca)
            valores.append(valor)

        if len(marcas) >= 2:
            almacen["players"][str(ficha.get("id"))] = {
                "t": marcas,
                "p": valores,
            }

            total_puntos += len(marcas)

        if numero % 50 == 0:
            print(
                f"  {numero}/{len(fichas)} "
                f"({total_puntos:,} puntos)".replace(",", ".")
            )

        time.sleep(PAUSA)

    salida.parent.mkdir(parents=True, exist_ok=True)

    salida.write_text(
        json.dumps(almacen), encoding="utf-8"
    )

    print()
    print(f"Jugadores con historico: {len(almacen['players'])}")
    print(f"Puntos de precio:        {total_puntos:,}".replace(",", "."))
    print(f"Del catalogo:            {len(fichas)}")
    print(f"Fallos:                  {len(fallos)}")

    if fallos:
        # QUIENES faltan, no cuantos. Si los que faltan son
        # "todos los de la W a la Z", la muestra esta cortada por
        # una letra y hay que saberlo antes de calibrar con ella.
        print(f"  {', '.join(fallos[:20])}")

        if len(fallos) > 20:
            print(f"  ...y {len(fallos) - 20} mas")

    print(f"Escrito en:              {salida}")


if __name__ == "__main__":
    main()
