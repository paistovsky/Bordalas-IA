"""
Ojeador de Jornada Perfecta. NO ENTRA: no publica precios.

    https://www.jornadaperfecta.com/blog/

QUE SE ENCONTRO AL ABRIRLO (05/09/2026)

    Cero tablas. Cero filas. Cero atributos de datos. Es un blog
    de WordPress con articulos escritos a mano:

        "Iker Luque, baja en la jornada 4 por arrastrar una
         sancion"
        "Foyth, baja confirmada para la Jornada 4"
        "FOFANA, ¿LA SORPRESA DEL MERCADO?"

    Son noticias de lesiones, sanciones y opinion. En ninguna
    parte hay una variacion de valor por jugador, que es lo que
    este ojeador va a buscar.

POR QUE NO SE SACA "ALGO" IGUALMENTE

    Porque lo unico que se podria sacar de "¿LA SORPRESA DEL
    MERCADO?" es una opinion sobre una opinion. Convertir un
    titular en una direccion UP seria inventarse una señal, y una
    señal inventada contamina el consenso: haria que dos fuentes
    "coincidan" cuando en realidad solo hay una y media.

    La regla del encargo es la que manda aqui: lo que no empareja
    con confianza no entra. Esto ni siquiera llega a emparejar.

    Y hay un precedente en esta casa: FutbolFantasy puntua 0.3365
    de Brier en pronosticos de titular, peor que apostar 50 % fijo.
    Ninguna fuente entra por prestigio.

QUE HACE ESTE FICHERO ENTONCES

    Existe, contesta con la misma forma que los demas, y dice que
    no hay datos y por que. Asi el informe publica los cuatro
    nombres y el dueño ve de un vistazo cual falta y el motivo,
    en vez de preguntarse por que solo salen tres.

    Y el dia que Jornada Perfecta publique una tabla -o el dia
    que se quiera leer la prensa y X, que el encargo deja para
    despues- se rellena esta funcion y no se toca nada mas. Para
    eso es un modulo por fuente.
"""

from __future__ import annotations

from src.intelligence.scout.common import source_result


SOURCE = "JORNADA_PERFECTA"

URL = "https://www.jornadaperfecta.com/blog/"


MOTIVO = (
    "No publica variacion de valor por jugador. Se abrio el "
    "05/09/2026: cero tablas, cero filas y cero atributos de "
    "datos en toda la pagina. Es un blog de noticias de lesiones "
    "y opinion, no un tablero de mercado. Sacar una direccion de "
    "un titular seria inventarse una señal, y una señal inventada "
    "falsea el consenso."
)


def scout(session=None, html: str | None = None) -> dict:
    """
    No sale a la calle: no hay nada que traer.

    Se devuelve `ok=False` a proposito, para que la fuente
    aparezca en el informe con su motivo. Una fuente que
    desaparece del informe se lee como una fuente que nadie
    penso, no como una que se descarto por escrito.
    """

    return source_result(
        SOURCE,
        ok=False,
        error=MOTIVO,
        note=(
            "Descartada a proposito, no por un fallo. Si algun dia "
            "publica precios, se rellena esta funcion y el resto "
            "del ojeador no se entera."
        ),
    )
