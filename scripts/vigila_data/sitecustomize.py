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

    def _open(archivo, *args, **kwargs):

        if _bajo_data(archivo):
            vistos.add(str(archivo))

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

    Path.read_text = _read_text

    Path.read_bytes = _read_bytes

    def _al_salir() -> None:

        for ruta in sorted(vistos):

            try:
                sys.stderr.write(f"{MARCA} {ruta}\n")

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
