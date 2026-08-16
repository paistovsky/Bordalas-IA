"""
Cuanto costaba un jugador en un momento dado.

POR QUE EXISTE
    La curva de primas del modelo de puja se calibraba dividiendo
    cada puja observada entre el precio ACTUAL del jugador. Los
    precios suben, asi que las pujas viejas salian
    sistematicamente baratas.

    Medido con datos reales el 16/08/2026: de 23 pujas, 18 daban
    una prima por debajo de 1,0. Hugo Gonzalez aparecia pujando un
    58 % por debajo del mercado cuando lo que habia pasado es que
    su precio se habia duplicado desde entonces.

    Una puja por debajo del precio de salida es imposible en una
    subasta del Computer. Que salieran 18 no era ruido: era la
    prueba de que el denominador estaba mal. Y el efecto era caro:
    el modelo creia que los rivales pujan bajo, pujaba al minimo y
    perdia las subastas.

COMO LO RESUELVE
    Los snapshots guardan el precio de cada jugador con su
    instante. `price_history_engine` ya los indexa. Aqui solo hay
    que buscar el registro mas cercano ANTERIOR a la puja.

    Si no hay ninguno lo bastante cerca, se devuelve cero y esa
    puja no se usa para calibrar. Preferimos calibrar con menos
    muestras que con muestras sesgadas.

LIMITE CONOCIDO
    Solo alcanza hasta donde llegan los snapshots. Las pujas
    anteriores al primero no se pueden medir y quedan fuera. Es
    una limitacion honesta: la alternativa era inventarse el
    denominador.
"""

from __future__ import annotations

from src.analysis.price_history_engine import (
    build_price_history_index,
)


# Un precio de hace mas de esto no describe el momento de la puja.
#
# Los precios se mueven a diario, asi que el margen es corto. Con
# los snapshots cada media hora del ciclo, en la practica se
# encuentra uno muy cercano.
MAX_AGE_SECONDS = 36 * 3600


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def build_historical_price_lookup(
    directory: str | None = None,
    max_age_seconds: int = MAX_AGE_SECONDS,
):
    """
    Devuelve una funcion `precio(player_id, cuando)`.

    Busca el precio registrado mas reciente ANTERIOR al instante
    pedido. Nunca usa uno posterior: seria mirar el futuro, que es
    justo el sesgo que venimos a quitar.
    """

    try:
        indice = (
            build_price_history_index(directory)
            if directory
            else build_price_history_index()
        )

    except Exception:
        indice = {}

    # Los registros vienen ordenados por instante, pero no se da
    # por hecho.
    ordenado = {
        int(player_id): sorted(
            (
                r for r in registros
                if safe_int(r.get("timestamp")) > 0
                and safe_int(r.get("price")) > 0
            ),
            key=lambda r: safe_int(r.get("timestamp")),
        )
        for player_id, registros in (indice or {}).items()
    }

    def precio(player_id, cuando) -> int:

        momento = safe_int(cuando)

        if momento <= 0:
            return 0

        registros = ordenado.get(safe_int(player_id))

        if not registros:
            return 0

        anterior = None

        for registro in registros:

            if safe_int(registro["timestamp"]) > momento:
                break

            anterior = registro

        if anterior is None:
            return 0

        antiguedad = momento - safe_int(anterior["timestamp"])

        if antiguedad > max_age_seconds:
            return 0

        return safe_int(anterior["price"])

    precio.players_indexed = len(ordenado)

    return precio
