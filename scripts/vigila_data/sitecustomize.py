"""
El vigilante de `data/`: apunta lo que una guardia abre de verdad.

SINTOMA (13/09/2026)

    `test_la_puja_del_carril_v1` verde a las 08:23, verde a las
    10:07 y ROJO a las 10:50. EL MISMO COMMIT.

    Entre medias, el ciclo de las 10:07 anoto a Trent como viaje
    del carril y gasto el cupo del reset. `data/trading` se
    restaura entre ciclos con `actions/cache@v4`, asi que la
    verja paso a depender de lo que Pepe hubiera hecho esa
    mañana.

    Pepe se echaba el candado a si mismo TRABAJANDO.

POR QUE LA COMPROBACION ESTATICA NO LO CAZO

    `test_verja_determinista_v1` busca la ruta `data/` ESCRITA en
    el codigo de la guardia. Y la guardia no la escribia: llamaba
    a `correr()`, que llamaba a `cuantos_en_este_reset()`, que
    por defecto abre `data/trading/libro_de_viajes.jsonl`.

    La lectura era TRANSITIVA, tres saltos mas abajo, en codigo
    de produccion que hace bien su trabajo.

    Mirar el texto encuentra la primera forma del fallo. Solo
    EJECUTAR encuentra la segunda.

POR QUE ESTO ES UN `sitecustomize` Y NO UNA GUARDIA MAS

    Una guardia que corriera las otras 119 para vigilarlas
    duplicaria la verja entera: medido, no termino en diez
    minutos. Y una verja lenta se acaba saltando.

    Python importa `sitecustomize` solo al arrancar. La verja ya
    lanza cada guardia en su propio proceso, asi que poniendo
    este directorio en `PYTHONPATH` el vigilante viaja dentro de
    la ejecucion que YA se hace. Coste: cero.

QUE HACE, Y QUE NO

    NO impide la lectura. Dejarla fallar cambiaria el resultado
    de la guardia y estariamos midiendo otra cosa. Solo la apunta
    y la escupe por `stderr` al terminar, con una marca que la
    verja reconoce.

    Solo se activa con `BORDALAS_VIGILA_DATA=1`. Fuera de la
    verja no existe.
"""

import os


MARCA = "VIGILANTE-DATA:"

MARCA_ESCRIBE = "VIGILANTE-ESCRIBE:"

_ENCENDIDO = "BORDALAS_VIGILA_DATA"


def _activar() -> None:

    if str(os.environ.get(_ENCENDIDO, "")).strip() != "1":
        return

    import atexit
    import builtins
    import sys

    from pathlib import Path

    vistos = set()

    # LOS DOS SITIOS DONDE VIVE EL ESTADO DE PRODUCCION
    #
    #     `diagnostico/` entro el 20/09/2026. Hasta entonces esta
    #     red solo miraba `data/`, y CINCO guardias leian
    #     `diagnostico/status.json` —la foto que rehace cada
    #     vuelta— sin que nadie las viera:
    #
    #         `las_dos_poblaciones()` busca `get_latest_snapshot(`
    #         la verja determinista busca `data/` ESCRITO
    #         esto miraba `data/` al abrirse
    #
    #     Las tres a la vez, y `diagnostico/` se colaba por las
    #     tres. Una de ellas —la del orden de venta— se puso roja
    #     el 20/09 porque habiamos vendido a Dituro esa mañana.
    CARPETAS = ("data/", "diagnostico/")

    def _bajo_data(ruta) -> bool:
        """¿Esta esa ruta dentro de `data/` o de `diagnostico/`?"""

        try:
            texto = str(ruta).replace(chr(92), "/")

        except Exception:                           # noqa: BLE001
            return False

        if texto.startswith("./"):
            texto = texto[2:]

        return any(
            texto.startswith(carpeta) or f"/{carpeta}" in texto
            for carpeta in CARPETAS
        )

    open_real = builtins.open

    read_text_real = Path.read_text

    read_bytes_real = Path.read_bytes

    # LO QUE SE ESCRIBE (29/09/2026). Leer `data/` es deuda; escribir
    # es peor: la verja en local cambia los libros de Pepe
    # (divergence_ledger, scout_accuracy_ledger...) y en CI deja
    # rastro en la cache. Se apunta con su propia marca.
    escritos = set()

    def _modo(args, kwargs) -> str:
        return str(kwargs.get("mode") or (args[0] if args else "r"))

    def _open(archivo, *args, **kwargs):

        if _bajo_data(archivo):
            vistos.add(str(archivo))

            if any(c in _modo(args, kwargs) for c in "wax+"):
                escritos.add(os.path.abspath(str(archivo)))

        return open_real(archivo, *args, **kwargs)

    def _read_text(self, *args, **kwargs):

        if _bajo_data(self):
            vistos.add(str(self))

        return read_text_real(self, *args, **kwargs)

    def _read_bytes(self, *args, **kwargs):

        if _bajo_data(self):
            vistos.add(str(self))

        return read_bytes_real(self, *args, **kwargs)

    builtins.open = _open

    write_text_real = Path.write_text

    write_bytes_real = Path.write_bytes

    replace_real = os.replace

    rename_real = os.rename

    def _write_text(self, *args, **kwargs):

        if _bajo_data(self):
            escritos.add(os.path.abspath(str(self)))

        return write_text_real(self, *args, **kwargs)

    def _write_bytes(self, *args, **kwargs):

        if _bajo_data(self):
            escritos.add(os.path.abspath(str(self)))

        return write_bytes_real(self, *args, **kwargs)

    def _replace(origen, destino, *args, **kwargs):

        if _bajo_data(destino):
            escritos.add(os.path.abspath(str(destino)))

        return replace_real(origen, destino, *args, **kwargs)

    def _rename(origen, destino, *args, **kwargs):

        if _bajo_data(destino):
            escritos.add(os.path.abspath(str(destino)))

        return rename_real(origen, destino, *args, **kwargs)

    Path.write_text = _write_text

    Path.write_bytes = _write_bytes

    os.replace = _replace

    os.rename = _rename

    Path.read_text = _read_text

    Path.read_bytes = _read_bytes

    def _al_salir() -> None:

        for ruta in sorted(vistos):

            try:
                sys.stderr.write(f"{MARCA} {ruta}\n")

            except Exception:                       # noqa: BLE001
                pass

        for ruta in sorted(escritos):

            try:
                sys.stderr.write(f"{MARCA_ESCRIBE} {ruta}\n")

            except Exception:                       # noqa: BLE001
                pass

    atexit.register(_al_salir)


try:
    _activar()

except Exception:                                   # noqa: BLE001
    # Un vigilante que revienta no puede tumbar la verja. Si no
    # puede instalarse, no vigila — y la comprobacion estatica de
    # `test_verja_determinista_v1` sigue en pie.
    pass


# ============================================================
# LA VERJA NO SALE A LA RED (29/09/2026)
# ============================================================
#
#     La regla «ninguna guardia sale a internet» existia y nada la
#     hacia cumplir. El 28/09, correr la verja en local escribio
#     311 lineas en `data/calendar/calendar_changes.jsonl`: alguna
#     guardia llego, por codigo de produccion, a bajar el
#     calendario de LaLiga. Una guardia que sale a la red depende
#     de lo que diga internet ese dia: el mismo commit, verde por
#     la manana y rojo por la tarde.
#
#     AQUI SI SE IMPIDE. A diferencia de `data/`, cortar la red no
#     cambia lo que se mide: una guardia no deberia depender de
#     ella nunca. Cada intento se corta con un `OSError` —que el
#     codigo de produccion ya sabe tratar: sin red, no hay dato— y
#     se apunta con su destino para que la verja diga quien fue.
#
#     La propia maquina (127.0.0.1, ::1, sockets de fichero) sigue
#     abierta: eso no es internet.
#
#     Solo con `VERJA_SIN_RED=1`. No lleva `BORDALAS_` a proposito:
#     no es un interruptor de Pepe y el paso 0 no debe encenderlo.

MARCA_RED = "VIGILANTE-RED:"

_SIN_RED = "VERJA_SIN_RED"


def _cortar_la_red() -> None:

    if str(os.environ.get(_SIN_RED, "")).strip() != "1":
        return

    import atexit
    import socket
    import sys

    intentos = set()

    LOCALES = {"127.0.0.1", "::1", "localhost", "0.0.0.0"}

    def _es_fuera(direccion) -> bool:

        # Sockets de fichero (AF_UNIX): una ruta, no una maquina.
        if not isinstance(direccion, tuple) or not direccion:
            return False

        return str(direccion[0]) not in LOCALES

    connect_real = socket.socket.connect

    connect_ex_real = socket.socket.connect_ex

    def _cortar(direccion):

        intentos.add(f"{direccion[0]}:{direccion[1] if len(direccion) > 1 else '?'}")

        raise OSError(
            f"La verja no sale a la red ({direccion[0]}): una guardia "
            f"no puede depender de internet."
        )

    def _connect(self, direccion):

        if _es_fuera(direccion):
            _cortar(direccion)

        return connect_real(self, direccion)

    def _connect_ex(self, direccion):

        if _es_fuera(direccion):
            _cortar(direccion)

        return connect_ex_real(self, direccion)

    socket.socket.connect = _connect

    socket.socket.connect_ex = _connect_ex

    def _al_salir() -> None:

        for destino in sorted(intentos):

            try:
                sys.stderr.write(f"{MARCA_RED} {destino}\n")

            except Exception:                       # noqa: BLE001
                pass

    atexit.register(_al_salir)


try:
    _cortar_la_red()

except Exception:                                   # noqa: BLE001
    pass
