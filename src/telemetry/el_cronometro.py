"""
El cronometro de etapas: donde se van los segundos, en el log.

POR QUE EXISTE (21/09/2026)

    La vuelta #1737 tardo 47 m 18 s y el registro solo decia dos
    numeros: «Analisis completado en 546,30 segundos» y el reloj
    del paso del dashboard. Nueve minutos dentro de una sola
    linea no se pueden repartir mirandolos: hay que partirlos
    donde se gastan.

    Esto NO optimiza nada. Solo reparte el numero que ya se
    imprimia, para que la proxima vez que crezca se sepa cual de
    las siete etapas ha crecido.

LO QUE NO HACE

    No decide, no bloquea y no compara contra ningun tope. Una
    guardia que mide tiempo seria fragil por naturaleza -y
    ademas miraria el reloj del sistema, que en esta casa una
    guardia no hace-. Esto lo imprime quien ya estaba corriendo,
    y nadie lee el numero para actuar.

    Tampoco escribe en ningun libro: va al log y ya esta.

FORMA

    cron = Cronometro("EL ANALISIS")

    with cron.etapa("build_cycle_acquisition_board"):
        tablero = build_cycle_acquisition_board(foto)

    for linea in cron.cuadro():
        print(linea)

    El `with` no se traga las excepciones: si una etapa revienta,
    revienta igual, y la etapa queda apuntada con lo que tardo
    hasta el fallo.
"""

from __future__ import annotations

import time

from contextlib import contextmanager


class Cronometro:
    """Cuanto tarda cada etapa de un proceso largo. Nunca decide nada."""

    def __init__(self, titulo: str = "") -> None:
        self.titulo = titulo
        self.etapas: list[tuple[str, float, bool]] = []
        self._arranco = time.perf_counter()

    @contextmanager
    def etapa(self, nombre: str):
        """Una etapa. Apunta lo que tarda aunque reviente."""

        t0 = time.perf_counter()

        roto = False

        try:
            yield

        except BaseException:
            roto = True
            raise

        finally:
            self.etapas.append(
                (nombre, time.perf_counter() - t0, roto)
            )

    @property
    def total(self) -> float:
        return time.perf_counter() - self._arranco

    def cuadro(self, ancho: int = 46) -> list:
        """
        El reparto, de mas a menos, con su porcentaje.

        Se publica SIEMPRE el «lo demas»: la diferencia entre el
        total y la suma de las etapas. Si esa linea crece, es que
        el tiempo se esta yendo por un sitio que nadie ha puesto
        entre `with`, y callarla lo escondería.
        """

        total = self.total

        lineas = []

        lineas.append("-" * (ancho + 22))

        lineas.append(
            f"{self.titulo or 'REPARTO'}, POR ETAPA "
            f"(total {total:.2f} s)"
        )

        lineas.append("-" * (ancho + 22))

        medido = 0.0

        for nombre, segundos, roto in sorted(
            self.etapas, key=lambda x: -x[1]
        ):
            medido += segundos

            parte = (
                100 * segundos / total if total > 0 else 0.0
            )

            lineas.append(
                f"  {segundos:>8.2f} s  {parte:>5.1f} %  "
                f"{nombre[:ancho]}"
                + ("   (REVENTO)" if roto else "")
            )

        resto = total - medido

        parte = 100 * resto / total if total > 0 else 0.0

        lineas.append(
            f"  {resto:>8.2f} s  {parte:>5.1f} %  "
            f"lo demas (lo que no esta cronometrado)"
        )

        lineas.append("-" * (ancho + 22))

        return lineas
