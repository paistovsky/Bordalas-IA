"""
El que va a despegar: el jugador cuyo pasado no dice lo que va a hacer.

EL CASO (23/09/2026)

    Ceballos, Betis, 4.180.000 EUR y subiendo. 13 puntos en 3
    partidos: 4,33 por partido. Vuelve de lesion y llego tarde a su
    equipo. El motor le ponia «sin interés» y `nos_suma = -9`:

        nos_suma = 13 (Ceballos, 3 partidos) - 22 (Ruben Garcia, 7)

    Total contra total. Le cobraba los partidos que no jugo. Por
    partido va un 38 % por encima de la vara (4,33 contra 3,14).

    Un total no es una tasa: restar acumulados castiga al que no
    jugo.

LA SEÑAL, NO LA SUSTITUCION

    `nos_suma` se queda como esta. Encima va una marca: «su pasado
    se queda corto», con el motivo y el dato. Las dos cosas se ven a
    la vez.

LAS CUATRO CLASES, LAS QUE NOMBRO EL DUEÑO

    1  LESION        vuelve de lesion: tiene pocos partidos, no
                     pocos puntos. `fitness` trae sus ultimos
                     partidos, el mas reciente primero, y marca
                     `injured` donde estuvo lesionado.
    2  RECIEN_FICHADO  no tiene historico en este equipo. `fitness`
                     tiene una entrada por partido del equipo desde
                     que llego: si trae menos que los partidos que
                     ha jugado su equipo -hasta cinco-, llego tarde.
    3  SIN_PRIMERA   venia de Segunda o de fuera: `pointsLastSeason`
                     por debajo de `ascendidos.PUNTOS_TEMPORADA_ANTERIOR`,
                     el corte con el que ya se separan los ascendidos.
    4  PRENSA        suplente o cantera con prensa que dice que va a
                     despegar: una noticia con direccion UP.

    PARTIDOS POSIBLES son los que ha jugado su equipo: el maximo de
    partidos jugados entre los jugadores de su club en el catalogo.
    Es una cota inferior -si nadie del club jugo uno, no cuenta-, y
    se dice asi.

LOS DOS FRENOS, O SE CAMBIA UN SESGO POR OTRO PEOR

    Con la tasa pelada, el primero de la liga es Sergio Martinez: 18
    puntos en 2 partidos, «no disponible». Por eso:

        - un minimo de partidos: `toda_la_liga.PARTIDOS_PARA_JUZGAR`,
          el mismo con el que ya no se juzga a nadie;
        - un veto de disponibilidad: lesionado o sancionado HOY no
          despega, igual que en `_etiqueta`.

    Y la tasa tiene que batir a la de su vara, por partido.

LO MEDIDO, Y NO LE DA LA RAZON (23/09/2026)

    `scripts/el_que_va_a_despegar.py`. Base: el catalogo del 13/09
    17:17, el ultimo con una semana cerrada detras.

                                          n   precio +7 d   puntuaron +6 d
        baten a su vara, nos_suma <= 0   72     -8,21 %      44 de 70
          de ellos, marcados              8    -12,53 %       4 de 8
        control: no la baten            129     -6,68 %      72 de 125
        nos mejoran                     215     -0,91 %     158 de 214

    Repetido sobre el 19/09 18:18 (precio a +3,5 d): -3,27 % contra
    -3,64 % del control, y puntuaron el 41 % contra el 46 %.

    Los que batian a su vara por partido NO lo hicieron mejor que el
    control en la semana siguiente, y los que `nos_suma` ya daba por
    buenos si. En esta muestra el motor tenia razon. Por eso esto es
    una señal para MIRAR y no entra en ninguna decision.

ESTO NO PUJA. NI UNA.

    Marca y ordena una lista para mirar. Lo que pujaria Pepe por
    cada uno lo pone el tablero de siempre, y aqui solo se copia.

REGLA 23

    No lee estado: el catalogo, la liga, la prensa y el tablero
    entran por la puerta.
"""

from __future__ import annotations


# Las noticias que dicen que alguien sube. Las demas direcciones
# -DOWN, FLAT- no son esta clase.
PRENSA_QUE_SUBE = "UP"

# Cuantos partidos trae `fitness` como mucho. Medido sobre el
# catalogo del 19/09: 509 de 547 jugadores traen cinco.
PARTIDOS_EN_FITNESS = 5

VETO = ("injured", "sanctioned")

LESION = "LESION"
RECIEN_FICHADO = "RECIEN_FICHADO"
SIN_PRIMERA = "SIN_PRIMERA"
PRENSA = "PRENSA"


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _jugados(ficha: dict) -> int:
    return safe_int(ficha.get("playedHome")) + safe_int(
        ficha.get("playedAway")
    )


def partidos_del_equipo(catalogo: dict | None) -> dict:
    """
    Los partidos que ha jugado cada club: el maximo de partidos
    jugados entre sus jugadores. Nunca lanza.
    """

    equipos: dict = {}

    try:
        for ficha in (catalogo or {}).values():

            if not isinstance(ficha, dict):
                continue

            club = ficha.get("teamID")

            if club is None:
                continue

            equipos[club] = max(
                equipos.get(club, 0), _jugados(ficha)
            )

    except Exception:                               # noqa: BLE001
        pass

    return equipos


def prensa_que_sube(items) -> dict:
    """`{player_id: titular}` de las noticias con direccion UP."""

    suben: dict = {}

    for item in (items or []):

        if not isinstance(item, dict):
            continue

        if str(item.get("direction") or "") != PRENSA_QUE_SUBE:
            continue

        pid = safe_int(item.get("player_id"))

        if pid and pid not in suben:
            suben[pid] = (
                item.get("headline") or item.get("quote") or ""
            )

    return suben


def por_que_se_queda_corto(
    ficha: dict | None,
    posibles: int | None,
    titular_que_sube: str | None = None,
    corte_primera: float | None = None,
) -> dict:
    """
    Por que el historico de un jugador es corto, con el dato.

    Devuelve los partidos jugados contra los posibles, desde
    cuando, y los motivos que se pueden probar. Sin motivo, un
    jugador que ha jugado poco es eso: uno que ha jugado poco.

    Nunca lanza.
    """

    ficha = ficha if isinstance(ficha, dict) else {}

    try:
        if corte_primera is None:
            from src.analysis.ascendidos import (
                PUNTOS_TEMPORADA_ANTERIOR,
            )

            corte_primera = PUNTOS_TEMPORADA_ANTERIOR

        jugados = _jugados(ficha)

        posibles = safe_int(posibles) or None

        forma = list(ficha.get("fitness") or [])

        motivos = []

        # 1. VUELVE DE LESION
        lesionado = [
            i for i, x in enumerate(forma) if x == "injured"
        ]

        if lesionado:
            hace = lesionado[0]

            motivos.append(
                {
                    "clase": LESION,
                    "texto": (
                        f"vuelve de lesion: lesionado en "
                        f"{len(lesionado)} de sus ultimos "
                        f"{len(forma)} partidos"
                        + (
                            f", la ultima vez hace {hace} "
                            f"partido(s)"
                            if hace
                            else ", y en el ultimo"
                        )
                    ),
                }
            )

        # 2. RECIEN FICHADO: `fitness` mas corto que los partidos
        #    de su equipo.
        esperado = (
            min(PARTIDOS_EN_FITNESS, posibles) if posibles else None
        )

        if forma and esperado and len(forma) < esperado:
            motivos.append(
                {
                    "clase": RECIEN_FICHADO,
                    "texto": (
                        f"llego tarde a su equipo: esta en sus "
                        f"ultimos {len(forma)} partidos, y el "
                        f"equipo ha jugado {posibles}"
                    ),
                }
            )

        # 3. SIN HISTORICO EN PRIMERA
        pasada = ficha.get("pointsLastSeason")

        if pasada is None or safe_int(pasada) < corte_primera:
            motivos.append(
                {
                    "clase": SIN_PRIMERA,
                    "texto": (
                        "sin historico en Primera: "
                        + (
                            "no trae puntos de la temporada pasada"
                            if pasada is None
                            else (
                                f"{safe_int(pasada)} puntos la "
                                f"temporada pasada"
                            )
                        )
                    ),
                }
            )

        # 4. LA PRENSA DICE QUE SUBE
        if titular_que_sube:
            motivos.append(
                {
                    "clase": PRENSA,
                    "texto": f"la prensa: «{titular_que_sube}»",
                }
            )

        return {
            "jugados": jugados,
            "posibles": posibles,
            "corto": bool(
                posibles is not None and jugados < posibles
            ),
            "motivos": motivos,
            "desde": (
                f"en sus ultimos {len(forma)} partidos"
                if forma
                else None
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "jugados": _jugados(ficha),
            "posibles": None,
            "corto": False,
            "motivos": [],
            "desde": None,
            "reason": f"{type(error).__name__}: {error}",
        }


def la_senal(
    fila: dict,
    ficha: dict | None,
    vara: dict | None,
    posibles: int | None,
    titular_que_sube: str | None = None,
    partidos_minimos: int | None = None,
) -> dict:
    """
    La marca de «su pasado se queda corto» sobre una fila de la liga.

    `vara` es la de su posicion, con `points` y `played`. No toca
    `nos_suma`: pone al lado la tasa por partido, la de la vara y la
    marca con su motivo. Nunca lanza.
    """

    try:
        if partidos_minimos is None:
            from src.analysis.toda_la_liga import (
                PARTIDOS_PARA_JUZGAR,
            )

            partidos_minimos = PARTIDOS_PARA_JUZGAR

        corto = por_que_se_queda_corto(
            ficha, posibles, titular_que_sube
        )

        jugados = corto["jugados"]

        puntos = safe_int(fila.get("points"))

        tasa = round(puntos / jugados, 2) if jugados > 0 else None

        vara = vara or {}

        vara_jugados = safe_int(vara.get("played"))

        vara_tasa = (
            round(safe_int(vara.get("points")) / vara_jugados, 2)
            if vara_jugados > 0
            else None
        )

        bate = bool(
            tasa is not None
            and vara_tasa is not None
            and tasa > vara_tasa
        )

        frenos = []

        if jugados < partidos_minimos:
            frenos.append(
                f"solo {jugados} partido(s): hacen falta "
                f"{partidos_minimos} para juzgar"
            )

        estado = str(fila.get("status") or "").lower()

        if estado in VETO:
            frenos.append(f"no disponible hoy ({estado})")

        marcado = bool(corto["corto"] and corto["motivos"])

        despega = bool(marcado and bate and not frenos)

        porque = "; ".join(m["texto"] for m in corto["motivos"])

        return {
            "tasa": tasa,
            "vara_tasa": vara_tasa,
            "bate_a_la_vara": bate,
            "pasado_corto": {
                **corto,
                "marcado": marcado,
                "frenos": frenos,
            },
            "va_a_despegar": despega,
            "por_que": (
                (
                    f"POR ESTE HAY QUE PUJAR: {tasa} por partido "
                    f"contra {vara_tasa} de su vara, en "
                    f"{jugados} de {corto['posibles']} partidos "
                    f"posibles. Su pasado se queda corto: {porque}."
                )
                if despega
                else None
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "tasa": None,
            "vara_tasa": None,
            "bate_a_la_vara": False,
            "pasado_corto": None,
            "va_a_despegar": False,
            "por_que": None,
            "reason": f"{type(error).__name__}: {error}",
        }


def la_lista_del_dia(
    liga: dict | None,
    en_el_mercado=None,
    tablero=None,
) -> dict:
    """
    Los que se pueden fichar HOY, los mejor valorados primero.

    Cruza la liga -con su marca- con el mercado del dia. Cada fila
    lleva su precio, su marca y lo que pujaria Pepe por el, copiado
    del tablero: la puja, el valor que le da y la decision con su
    motivo. Si el tablero no lo trae, se dice.

    Fuera: los no disponibles y los nuestros. Dentro, en este orden:
    los que nos mejoran, los que van a despegar, y el resto por su
    tasa contra la vara.

    Forma fija. Nunca lanza. NO PUJA.
    """

    vacio = {
        "available": False,
        "en_el_mercado": 0,
        "players": [],
        "despegan": 0,
        "reason": None,
    }

    try:
        datos = liga if isinstance(liga, dict) else {}

        if not datos.get("available"):
            return {
                **vacio,
                "reason": (
                    "Sin la liga no hay lista del dia: "
                    + str(datos.get("reason") or "no disponible")
                ),
            }

        hoy = {safe_int(p) for p in (en_el_mercado or set())}

        filas = [
            f
            for f in (datos.get("players") or [])
            if isinstance(f, dict)
            and (
                safe_int(f.get("id")) in hoy
                or f.get("de_quien") == "computer"
            )
        ]

        if not filas:
            return {
                **vacio,
                "available": True,
                "reason": (
                    "Nadie de la liga esta hoy en el mercado: o no "
                    "llego el mercado, o el catalogo no los trae."
                ),
            }

        del_tablero = {
            safe_int(t.get("id")): t
            for t in (tablero or [])
            if isinstance(t, dict)
        }

        def _grupo(f) -> int:
            if f.get("etiqueta") == "nos mejora":
                return 0
            if f.get("va_a_despegar"):
                return 1
            return 2

        def _ratio(f) -> float:
            tasa = f.get("tasa")
            vara = f.get("vara_tasa")
            if tasa is None or not vara:
                return 0.0
            return tasa / vara

        fichables = [
            f
            for f in filas
            if f.get("etiqueta")
            not in ("no disponible", "ya es nuestro")
        ]

        fichables.sort(
            key=lambda f: (
                _grupo(f),
                -_ratio(f),
                safe_int(f.get("id")),
            )
        )

        players = []

        for f in fichables:

            t = del_tablero.get(safe_int(f.get("id")))

            players.append(
                {
                    "id": safe_int(f.get("id")),
                    "name": f.get("name"),
                    "position": f.get("position"),
                    "price": safe_int(f.get("price")),
                    "price_increment": f.get("price_increment"),
                    "points": f.get("points"),
                    "played": f.get("played"),
                    "nos_suma": f.get("nos_suma"),
                    "tasa": f.get("tasa"),
                    "vara_tasa": f.get("vara_tasa"),
                    "etiqueta": f.get("etiqueta"),
                    "va_a_despegar": bool(f.get("va_a_despegar")),
                    "pasado_corto": f.get("pasado_corto"),
                    "por_que": f.get("por_que"),

                    # LO QUE PUJARIA PEPE, DEL TABLERO. Copiado, no
                    # recalculado.
                    "pepe": (
                        {
                            "en_el_tablero": True,
                            "bid": safe_int(t.get("bid")),
                            "our_value": t.get("our_value"),
                            "decision": t.get("decision"),
                            "reason": t.get("reason"),
                        }
                        if t
                        else {
                            "en_el_tablero": False,
                            "bid": None,
                            "our_value": None,
                            "decision": None,
                            "reason": (
                                "El tablero no lo trae: no se sabe "
                                "que pujaria."
                            ),
                        }
                    ),
                }
            )

        despegan = sum(1 for p in players if p["va_a_despegar"])

        return {
            "available": True,
            "en_el_mercado": len(filas),
            "players": players,
            "despegan": despegan,
            "fuera": len(filas) - len(fichables),
            "reason": (
                f"{len(filas)} de la liga estan hoy en el mercado; "
                f"{len(players)} se pueden fichar y {despegan} "
                f"llevan la marca de que van a despegar. Esta "
                f"lista NO puja."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "reason": (
                f"No se pudo montar la lista del dia: "
                f"{type(error).__name__}: {error}"
            ),
        }
