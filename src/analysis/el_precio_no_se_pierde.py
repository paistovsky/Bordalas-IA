"""
El precio no se pierde: fichar es cambiar dinero por un activo que
ademas puntua.

EL FALLO (26/09/2026)

    Hinojo: "vale 883.575 y cuesta 1.690.000. No hay margen." Y
    sumaba +0,73 puntos por jornada.

    `xi_upgrade_value` valoraba un fichaje SOLO por los puntos que
    añade (delta x tarifa x margen x confianza) y lo comparaba con el
    precio ENTERO. Como si el precio se perdiera. No se pierde: el
    jugador sigue siendo nuestro y se revende. Lo que se gasta es lo
    que se DEPRECIA mientras lo tienes.

    Medido en la auditoria del 26/09: el bot aporto 11 de 298 puntos
    (4 %); lo fichado por el dueño, a 9.127 EUR por punto neto contra
    los 30.000 que paga la liga.

LA CUENTA, POR DIA Y CON EL MISMO HORIZONTE A LOS DOS LADOS

    ganancia(H) = puntos por jornada x jornadas en H x 30.000
                  x (1 - margen) x confianza
    coste(H)    = precio x depreciacion conservadora a H
                  + precio x coste de oportunidad x H

    se ficha si ganancia(H) > coste(H)

    Y como el motor compara un `value` contra el precio, el valor
    que se devuelve es el MAXIMO que pagariamos:

        valor = precio - coste(H) + ganancia(H)

    `valor > precio`  <=>  `ganancia > coste`. El comparador de
    `rival_bid_model` no cambia, y lo que sobra por encima del precio
    es el margen de puja que la propia cuenta paga.

EL HORIZONTE: 14 DIAS PARA JUGAR, Y NO SE MEZCLA CON REVENDER

    Jugar y revender son dos compras distintas con dos costes
    distintos. Esta cuenta es SOLO la de jugar (mejora del once).
    Revender -especular, reventa al Computer, tener- ya valoraba el
    precio como lo que es (precio x (1 + ganancia esperada)) y no se
    toca: sigue con sus dias y su liston.

    Para jugar, la ganancia y la depreciacion crecen las dos con los
    dias, asi que el horizonte casi se cancela. Se usa 14 dias porque
    es lo que se puede MEDIR: 40,5 dias de historico de precios dan
    ventanas de 14 dias con 7 de tendencia previa. Lo que se gana
    despues de 14 dias no se cuenta, y el sobreprecio de la puja se
    tiene que pagar dentro de esos 14. Conservador a proposito.

LA DEPRECIACION: DEL HISTORICO DE PRECIOS, POR TRAMO, CONSERVADORA

    Medido el 26/09 sobre `data/autopilot/price_history.json` (40,5
    dias), jugadores que juegan (>= 5 de 7 partidos), cambio de precio
    a 14 dias segun la tendencia de los 7 dias previos:

        tramo        ventanas  jugadores  mediana   tercil bajo (q33)
        BAJA (<-0,3 %/dia)  869     213   -10,06 %    -14,74 %
        PLANO               285     146    -1,80 %     -7,34 %
        SUBE (>+0,3 %/dia)  792     198    +8,75 %     +0,37 %
        sin tramo          1946     281       -        -9,70 %

    Se usa el TERCIL BAJO, no la mediana: dos de cada tres compras
    lo mejoran. Y la subida NUNCA se cuenta: SUBE deprecia 0, no
    revaloriza. Mejor suponer que se deprecia de mas que al reves.

    Las ventanas se solapan (cada 3 dias): la `n` de ventanas no es
    independiente; la de jugadores si.

    La tendencia es la que la sombra ya imprime
    (`rate_percent_per_day` de `evaluate_market_rate`). Sin ella, el
    tramo "sin tramo".

EL COSTE DE OPORTUNIDAD: HOY CERO, Y ES UN DATO

    El dinero parado no rinde. La mejor via alternativa medida es la
    cesta: +0,12 % en toda su vida (n=9); el carril pierde un 3,6 % y
    el tablero un 5,8 %. Asi que hoy la tasa es 0. Sube cuando haya
    cola: ahi el que manda es el ORDEN -la cola coge primero al que
    mas puntos gana por euro-, y si algun dia hay una via que rinda de
    verdad, se pasa su tasa por `oportunidad_diaria`.

SOLO PUNTUAN ONCE

    Un suplente que no entra en el once suma cero en esta liga
    (`lineupReserves: false`). Por eso la ficha vacia, con esta
    cuenta, no se valora por sus puntos: vale lo que conserve, que es
    menos que su precio, y no pasa. Si entra en el once, ya lo cubre
    la mejora del once.

NACE APAGADO: `BORDALAS_EL_PRECIO_NO_SE_PIERDE`. Funciones puras: ni
disco, ni red, ni reloj. El interruptor se lee al llamar. Nunca lanza.
"""

from __future__ import annotations

import math
import os


EL_PRECIO_NO_SE_PIERDE_ENV = "BORDALAS_EL_PRECIO_NO_SE_PIERDE"

HORIZONTE_DIAS = 14

JORNADAS_DE_LA_TEMPORADA = 38

# 31 jornadas que quedan (J8 el 09/10/2026 a la J38) en ~240 dias.
# Se usa si quien llama no pasa las suyas.
JORNADAS_POR_DIA = 31 / 240

UMBRAL_TENDENCIA = 0.3        # %/dia

DEPRECIACION_14_DIAS = {
    "BAJA": 0.1474,
    "PLANO": 0.0734,
    "SUBE": 0.0,
    "SIN_TRAMO": 0.0970,
}

OPORTUNIDAD_DIARIA = 0.0


def encendido() -> bool:
    """El interruptor. Se lee al llamar. NACE APAGADO."""

    return str(
        os.environ.get(EL_PRECIO_NO_SE_PIERDE_ENV, "")
    ).strip().lower() in {"1", "true", "si", "yes"}


def _num(value, default=None):
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def tramo(tasa_por_dia) -> str:
    """BAJA, PLANO, SUBE o SIN_TRAMO, por la tasa en %/dia."""

    tasa = _num(tasa_por_dia)
    if tasa is None:
        return "SIN_TRAMO"
    if tasa < -UMBRAL_TENDENCIA:
        return "BAJA"
    if tasa > UMBRAL_TENDENCIA:
        return "SUBE"
    return "PLANO"


def coste_real(
    precio,
    tasa_por_dia=None,
    horizonte_dias: int = HORIZONTE_DIAS,
    oportunidad_diaria: float = OPORTUNIDAD_DIARIA,
) -> dict:
    """
    Lo que cuesta DE VERDAD tener al jugador `horizonte_dias`: lo que
    se deprecia (conservador, por tramo) mas lo que ese dinero habria
    rendido en otra cosa. El precio no esta: se conserva.
    """

    p = max(_num(precio, 0.0), 0.0)
    h = max(_num(horizonte_dias, HORIZONTE_DIAS), 0.0)
    t = tramo(tasa_por_dia)
    dep = DEPRECIACION_14_DIAS[t] * (h / HORIZONTE_DIAS)
    opp = max(_num(oportunidad_diaria, 0.0), 0.0) * h
    depreciacion = int(round(p * dep))
    oportunidad = int(round(p * opp))
    return {
        "tramo": t,
        "depreciacion": depreciacion,
        "oportunidad": oportunidad,
        "coste": depreciacion + oportunidad,
        "horizonte_dias": h,
    }


def valor_para_jugar(
    precio,
    delta_puntos_temporada,
    tarifa,
    margen: float,
    confianza: float,
    tasa_por_dia=None,
    jornadas_por_dia=None,
    horizonte_dias: int = HORIZONTE_DIAS,
    oportunidad_diaria: float = OPORTUNIDAD_DIARIA,
) -> dict:
    """
    El maximo que pagariamos por un fichaje PARA JUGAR:

        valor = precio - coste(H) + ganancia(H)

    `delta_puntos_temporada` son puntos de temporada entera (los de
    `estimate_season_points`): se pasan a puntos por jornada
    dividiendo por 38. Nunca lanza: si algo falla, `valor` 0.
    """

    try:
        p = max(_num(precio, 0.0), 0.0)
        h = max(_num(horizonte_dias, HORIZONTE_DIAS), 0.0)
        jpd = _num(jornadas_por_dia)
        if jpd is None or jpd < 0:
            jpd = JORNADAS_POR_DIA
        por_jornada = _num(delta_puntos_temporada, 0.0) / JORNADAS_DE_LA_TEMPORADA
        jornadas = jpd * h
        conf = max(min(_num(confianza, 0.0), 1.0), 0.0)
        mar = max(min(_num(margen, 0.0), 1.0), 0.0)

        ganancia = int(round(
            por_jornada * jornadas * _num(tarifa, 0.0) * (1.0 - mar) * conf
        ))
        coste = coste_real(p, tasa_por_dia, h, oportunidad_diaria)

        valor = int(round(p - coste["coste"] + ganancia))
        neto = ganancia - coste["coste"]

        return {
            "valor": max(valor, 0),
            "ganancia": ganancia,
            "coste": coste["coste"],
            "depreciacion": coste["depreciacion"],
            "oportunidad": coste["oportunidad"],
            "tramo": coste["tramo"],
            "neto": neto,
            "puntos_por_jornada": round(por_jornada, 3),
            "jornadas_en_el_horizonte": round(jornadas, 2),
            "horizonte_dias": h,
            # Para la cola: puntos que se ganan por cada millon que se
            # inmoviliza. El primero que se coge es el que mas da.
            "puntos_por_millon": (
                round(por_jornada * jornadas / (p / 1e6), 4) if p > 0 else None
            ),
            "compensa": neto > 0,
            "cuenta": (
                f"gana {ganancia:,} en {h:.0f} dias "
                f"({por_jornada * jornadas:.2f} pts) y cuesta "
                f"{coste['coste']:,} (se deprecia {coste['tramo']}); "
                f"el precio se conserva"
            ).replace(",", "."),
        }
    except Exception as error:                      # noqa: BLE001
        return {
            "valor": 0, "ganancia": 0, "coste": 0, "depreciacion": 0,
            "oportunidad": 0, "tramo": None, "neto": 0,
            "puntos_por_millon": None, "compensa": False,
            "cuenta": f"{type(error).__name__}: {error}",
        }
