"""
Ojeador de FutbolFantasy: subidas y bajadas del mercado Biwenger.

    https://www.futbolfantasy.com/analytics/biwenger/mercado

QUE TRAE, DE VERDAD

    554 jugadores el 05/09/2026, cada uno con estos atributos en
    la propia fila de la tabla:

        data-valor            valor actual en Biwenger
        data-valorN           valor hace N dias (1, 2, 3, 7, 14, 30)
        data-diferenciaN      actual - valor de hace N dias, en euros
        data-diferencia-pctN  lo mismo en porcentaje
        data-tendencia        dias consecutivos subiendo o bajando
        data-aceleracion      si acelera o se frena

    NO son pronosticos. La leyenda de la propia pagina lo dice
    con estas palabras:

        "Dif: Diferencia de valor respecto al mercado del dia
         anterior"
        "Tend: Tendencia del valor del jugador. Dias consecutivos
         que ha estado aumentando o bajando de valor"
        "Valor ant.: Valor del jugador en el mercado anterior"

    Se comprobo al abrirla y esta escrito aqui para que nadie lo
    lea al reves dentro de un mes.

POR QUE ES LA MEJOR FUENTE DE LAS CUATRO

    Por dos cosas:

    1. Publica `data-valor`, que es el valor Biwenger AL EURO.
       Eso da la segunda llave de emparejamiento -la misma que
       usa `futbolfantasy_provider.match_team`- y es lo que
       separa identificar de adivinar.

    2. Da varios horizontes. Un jugador puede llevar un dia
       subiendo y treinta bajando, y esas dos cosas juntas dicen
       mas que cualquiera de las dos sola.

QUE SEÑALES SE SACAN

    Una por horizonte corto -1, 3 y 7 dias-, que es donde el
    movimiento reciente tiene algo que decir sobre el siguiente
    mercado. Los de 14 y 30 se guardan en la cita pero no se
    convierten en señal: a esa distancia el numero habla de otra
    temporada del jugador, no del proximo mercado.
"""

from __future__ import annotations

from src.intelligence.scout.common import (
    direction,
    fetch,
    safe_float,
    safe_int,
    signal,
    source_result,
)


SOURCE = "FUTBOLFANTASY"

URL = "https://www.futbolfantasy.com/analytics/biwenger/mercado"


# Los horizontes que se convierten en señal. Ver el docstring:
# 14 y 30 dias describen la temporada del jugador, no el proximo
# mercado.
HORIZONS = (1, 3, 7)


def _tendencia_a_confianza(tendencia) -> tuple[float | None, str]:
    """
    Cuanta constancia lleva detras este movimiento.

    OJO: ESTO LO CALCULAMOS NOSOTROS

        FutbolFantasy NO publica ninguna confianza. Lo que
        publica es `data-tendencia`, los dias consecutivos que
        lleva subiendo o bajando.

        Un jugador que lleva cinco dias subiendo es una señal mas
        firme que uno que subio ayer y nada mas, y eso es lo
        unico que dice este numero. Se convierte en 0,5-0,9 para
        que el consenso pueda pesarlo, y se etiqueta como
        DERIVADA para que nadie lo confunda con una confianza
        publicada por la fuente.
    """

    dias = abs(safe_int(tendencia))

    if dias <= 0:
        return (
            0.50,
            "DERIVADA: sin racha (data-tendencia = 0)",
        )

    # 1 dia -> 0,58 ... 5 dias o mas -> 0,90
    valor = min(0.50 + 0.08 * dias, 0.90)

    return (
        round(valor, 2),
        f"DERIVADA de data-tendencia: {dias} dia(s) consecutivos",
    )


def parse_market(html: str) -> list[dict]:
    """
    Las filas de la tabla, en crudo y sin emparejar todavia.

    Nunca lanza por una fila mala: una fila rara no puede
    llevarse por delante a las otras 553.
    """

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    registros = []

    for fila in soup.find_all(attrs={"data-nombre": True}):

        try:
            atributos = fila.attrs

            nombre = str(atributos.get("data-nombre") or "").strip()

            if not nombre:
                continue

            valor = safe_int(atributos.get("data-valor"))

            tendencia = safe_int(atributos.get("data-tendencia"))
            aceleracion = safe_int(atributos.get("data-aceleracion"))

            confianza, base = _tendencia_a_confianza(tendencia)

            señales = []

            for dias in HORIZONS:

                euros = atributos.get(f"data-diferencia{dias}")
                pct = atributos.get(f"data-diferencia-pct{dias}")

                if euros is None and pct is None:
                    continue

                anterior = safe_int(
                    atributos.get(f"data-valor{dias}")
                )

                señales.append(
                    signal(
                        SOURCE,
                        direction_=direction(euros),
                        magnitude_percent=safe_float(pct),
                        magnitude_eur=euros,
                        horizon_days=dias,
                        confidence=confianza,
                        confidence_basis=base,
                        quote=(
                            f"data-diferencia{dias}={euros}, "
                            f"data-diferencia-pct{dias}={pct}, "
                            f"valor={valor}, "
                            f"valor hace {dias} d={anterior}, "
                            f"tendencia={tendencia}, "
                            f"aceleracion={aceleracion}"
                        ),
                        observed=True,
                    )
                )

            if not señales:
                continue

            registros.append(
                {
                    # Con los nombres que espera `_name_score` del
                    # proveedor, para poder reutilizarlo tal cual.
                    "ff_name": nombre,
                    "ff_slug": None,

                    "source_player_id": atributos.get("data-id"),
                    "team_hint": atributos.get("data-equipo"),
                    "position_hint": atributos.get("data-posicion"),

                    # La llave del euro. Es lo que convierte el
                    # emparejamiento en identificacion.
                    "market_value": valor,

                    "trend_days": tendencia,
                    "acceleration": aceleracion,

                    "signals": señales,
                }
            )

        except Exception:                           # noqa: BLE001
            continue

    return registros


def scout(session=None, html: str | None = None) -> dict:
    """
    Sale a la calle una vez y vuelve con lo que haya.

    `html` existe para las guardias: se prueba el parser con una
    pagina en disco, sin tocar la red.
    """

    if html is None:

        if session is None:
            import requests

            session = requests.Session()

        html, error = fetch(session, URL)

        if error:
            return source_result(SOURCE, ok=False, error=error)

    try:
        registros = parse_market(html)

    except Exception as error:                      # noqa: BLE001
        return source_result(
            SOURCE,
            ok=False,
            error=f"parser: {type(error).__name__}: {error}",
        )

    if not registros:
        return source_result(
            SOURCE,
            ok=False,
            error=(
                "La pagina contesto pero no trajo ni una fila con "
                "`data-nombre`: o ha cambiado el HTML o vino vacia."
            ),
        )

    return source_result(
        SOURCE,
        ok=True,
        records=registros,
        note=(
            "Movimiento OBSERVADO, no pronostico. La fuente no "
            "publica confianza: la que viaja se deriva de "
            "`data-tendencia`."
        ),
    )
