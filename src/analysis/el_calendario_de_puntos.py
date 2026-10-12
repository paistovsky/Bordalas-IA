"""
El calendario de puntos: los puntos esperados, con el rival delante.

POR QUE EXISTE (12/10/2026)

    Hoy Pepe espera de cada jugador `tasa x titularidad / 100`
    (`esperado`, src/actions/la_mejora_del_once.py:114-121) y le da
    igual jugar en casa contra el colista que fuera en el Camp Nou.
    El dueño lo ve al reves: con tres partidos seguidos fuera contra
    Barça, Atletico y Madrid, ese jugador rinde menos este mes.

    `el_calendario.py` ya enseña contra quien juega cada uno, pero
    con tramos SIN MEDIR y sin decir cuantos puntos son. Este modulo
    convierte el calendario en puntos esperados, con los factores
    que MIDIO el laboratorio del 12/10.

LO QUE SE MIDIO (laboratorio del 12/10/2026, fixture_effect.py)

    Partidos jugador-partido de toda la liga, J7 y J8 de la
    2026-27, rehechos restando los totales de Biwenger entre fotos
    que abrazan una sola jornada:

        n = 564 jugador-partido (J7 313, J8 251; POR 36, DEF 182,
        MED 188, DEL 158), 18 partidos, 36 racimos equipo-partido.
        Media 4,17 puntos por aparicion. El error se infla 1,47x
        por el racimo: casi todos los IC95 tocan el 1,0.

    EN CASA, medido 1,09 (n = 268, IC95 0,99-1,21; quitando un
    partido 1,04-1,13). FUERA 0,91 (n = 272, IC95 0,80-1,01).
    Mezclado por precision con el estudio del 26/09 (catalogo
    pointsHome/pointsAway, ±0,217 puntos, n = 1.016, sin fuga):
    RECOMENDADO 1,06 / 0,94.

    RIVAL DURO (puesto 1-6 ANTES del partido), medido 0,87 (n = 168,
    IC95 0,73-0,99; quitando un partido 0,85-0,91: aguanta).
    Corregido el sesgo del dejar-uno-fuera y encogido por tener solo
    18 partidos: RECOMENDADO 0,90. Por valor de plantilla (top-4:
    Barça, Madrid, Atletico, Betis) sale lo mismo, 0,87.

    EL RESTO (puesto 7-20), medido ~1,06: RECOMENDADO 1,04, para que
    una temporada equilibrada promedie ~1,0. NO hay tramo "blando"
    aparte: con la tabla de antes del partido, 14-20 dio 0,98, no
    mejor que 7-13. El "bonus del rival flojo" era fuga de la tabla
    de hoy (que ya contiene el partido): 1,13 con fuga, 1,00 sin.

    EL PORTERO NO TIENE SEDE. Medido 0,79 en casa y 1,25 fuera con
    n = 34 (un portero por racimo): ruido. Su sede vale 1,0. El
    rival si le aplica: POR+DEF contra top-4 dio 0,83 (n = 51).

    LA FUERZA DEL PROPIO EQUIPO YA ESTA DENTRO DE LA TASA. Top-4 hoy
    puntua 1,34x la media de la liga (n = 75 jugadores), 11-20 0,86x
    (n = 199). Pero eso ya va en los puntos por partido de cada uno:
    multiplicarlo otra vez lo contaria dos veces. NUNCA es un factor
    por partido: solo entra como el PREVIO hacia el que se encoge
    una tasa con pocos partidos (`tasa_encogida`).

LA REGLA

    xP de un partido = tasa x titularidad / 100 x SEDE x RIVAL

        SEDE   1,06 en casa · 0,94 fuera · 1,0 el portero
        RIVAL  0,90 si es duro · 1,04 si no

    Duro = top-6 de la tabla por puntos por partido, O top-4 por
    valor de plantilla (la opcion robusta del laboratorio: la tabla
    con 6-8 jornadas es una vara ruidosa, el valor es mas estable).

    xP de una RONDA = la suma de sus partidos. Si el equipo NO
    juega en esa ronda, xP NEUTRO (tasa x titularidad / 100), NO
    cero. El laboratorio recomendaba cero; el dueño corrige: un
    partido aplazado se juega despues CON EL ONCE PUESTO EN SU
    RONDA, asi que esos puntos llegan igual. Y asi el horizonte
    compara lo mismo con lo mismo: tres huecos para todos, sin premio
    por una ronda extra ni castigo por un aplazado.

LO QUE PESA: POCO. ES UN DESEMPATE

    El factor por partido va de 0,846 (fuera contra un duro) a 1,102
    (en casa contra el resto). En tres partidos el calendario mueve
    el xP entre -15 % y +10 %: para un delantero de 5 puntos por
    partido, ~3,8 puntos en tres jornadas, lo mismo que ~1,3 puntos
    por partido de calidad. Solo sirve entre jugadores cuya tasa
    este a 1-1,5 puntos. NO para vender a uno bueno por calendario:
    la ida y vuelta cuesta un 10-20 % (E14, E7).

    El calendario esta "Cerrado" como criterio de decision en
    docs/EL-PUESTO-DE-MANDO.md:229-232 (el once de la jornada con
    calendario dio -6 en 13). Este modulo CALCULA; quien lo use para
    decidir tiene que medirlo antes.

LAS RONDAS NO SON LAS JORNADAS

    Biwenger alinea por RONDA, no por jornada. La J6 de esta liga
    vino partida: la ronda 4904 con un solo partido el 03/09 y la
    5125 "Jornada 6 (aplazada)" con el grueso el 15-17/09
    (marcador.py:258-266). Y el Levante-Athletic de la J6 se juega
    el 21/10, entre la J9 y la J10. Asi que aqui una ronda es:

        la VENTANA PRINCIPAL de cada jornada = los partidos a 3 dias
        o menos de la mediana de sus horas (la mediana baja: siempre
        es la hora de un partido de verdad);

        cada partido FUERA de esa ventana (adelantado o aplazado) va
        a SU PROPIA ronda. Si varios de la misma jornada caen a 3
        dias o menos entre si, comparten ronda (dos aplazados el
        mismo miercoles serian una sola ronda en Biwenger). SIN
        MEDIR: solo hay un caso real, el de la 5125.

    "Proximas" es por RELOJ: las que no han empezado.

LO QUE NO HACE

    No decide nada: ni puja, ni venta, ni once. No lee ficheros, ni
    red, ni entorno (regla 23): todo llega por argumento. No toma la
    hora del reloj si se le pasa `ahora`.

    No sabe si un partido se aplazo: el calendario no trae estado.
    El Rayo-Athletic de la J8 sigue en el calendario el 10/10 sin
    haberse jugado. Eso lo tiene que decir otra fuente.

    No mide la rotacion por rival: todo es condicionado a jugar.
    La titularidad sale de quien llama (`prob`).

    No encoge entrenadores: no hay previo medido para ellos.

NUNCA LANZA

    Todo corre en produccion. Con basura de entrada, cada funcion
    devuelve su valor neutro: factor 1,0, conjunto vacio, lista
    vacia, o None donde "no se sabe" no es lo mismo que cero (el
    mismo contrato que `esperado`).
"""

from __future__ import annotations

import re
import unicodedata

from datetime import datetime, timedelta, timezone
from fractions import Fraction
from functools import lru_cache


# ============================================================
# LOS FACTORES (laboratorio del 12/10/2026, recomendados)
# ============================================================

# Sede. Medido 1,09 / 0,91 (n = 268 / 272), mezclado con el estudio
# del 26/09 (±0,217 sobre ~4,1, n = 1.016): 1,06 / 0,94.
VENUE_CASA = 1.06
VENUE_FUERA = 0.94

# El portero: medido 0,79 / 1,25 con n = 34. Ruido. Sin sede.
VENUE_PORTERO = 1.0

# Rival. Duro medido 0,87 (n = 168) -> 0,90. Resto medido ~1,06 ->
# 1,04 para que la temporada promedie ~1,0.
RIVAL_DURO = 0.90
RIVAL_RESTO = 1.04

# Quien es duro: top-6 por puntos por partido (el corte de
# `el_calendario.RIVAL_DURO_HASTA`, el que se midio) o top-4 por
# valor de plantilla (Barça 165,8 M, Madrid 133,4 M, Atletico 94,4 M,
# Betis 78,2 M el 12/10: da el mismo 0,87).
DUROS_POR_TABLA = 6
DUROS_POR_VALOR = 4

# El valor de plantilla: la suma de los 15 mas caros, como el
# laboratorio (todos los que tienen equipo y precio).
PLANTILLA_TOP = 15

# La ventana principal de una jornada: ±3 dias de la mediana.
VENTANA_DIAS = 3

# El horizonte por defecto: tres rondas.
HORIZONTE = 3

# El encogimiento: (puntos + k·m) / (jugados + k). k = 3 es juicio,
# NO esta medido. m es la media medida por tramo y posicion (12/10,
# 394 jugadores con 3+ partidos, tramo por el puesto de HOY).
K_ENCOGIMIENTO = 3

PORTERO, DEFENSA, MEDIO, DELANTERO, ENTRENADOR = 1, 2, 3, 4, 5

TRAMO_ARRIBA = "1-4"
TRAMO_MEDIO = "5-10"
TRAMO_ABAJO = "11-20"

TASA_DEL_TRAMO = {
    TRAMO_ARRIBA: {PORTERO: 5.45, DEFENSA: 4.75, MEDIO: 5.47, DELANTERO: 6.54},
    TRAMO_MEDIO: {PORTERO: 5.30, DEFENSA: 3.70, MEDIO: 4.02, DELANTERO: 4.39},
    TRAMO_ABAJO: {PORTERO: 4.00, DEFENSA: 2.86, MEDIO: 3.50, DELANTERO: 4.17},
}

# Sin tramo (equipo que no casa), el 5-10: medido 1,00x la media de
# la liga, es lo mas parecido a "no se sabe".
TRAMO_POR_DEFECTO = TRAMO_MEDIO


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(valor, defecto=None):
    try:
        if valor is None or isinstance(valor, bool):
            return defecto
        return int(valor)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _num(valor, defecto=None):
    try:
        if valor is None or isinstance(valor, bool):
            return defecto
        salida = float(valor)
    except (TypeError, ValueError, OverflowError):
        return defecto
    if salida != salida or salida in (float("inf"), float("-inf")):
        return defecto
    return salida


def _fraccion(valor) -> Fraction:
    """Exacta, para que dos empates de verdad sean iguales."""
    try:
        if isinstance(valor, bool) or valor is None:
            return Fraction(0)
        if isinstance(valor, int):
            return Fraction(valor)
        numero = _num(valor)
        return Fraction(numero) if numero is not None else Fraction(0)
    except Exception:                               # noqa: BLE001
        return Fraction(0)


def _cuando(valor):
    """La hora, con zona. Sin zona se toma UTC (como el_calendario)."""
    try:
        if isinstance(valor, datetime):
            cuando = valor
        elif isinstance(valor, str) and valor.strip():
            cuando = datetime.fromisoformat(valor.strip())
        else:
            return None
    except (TypeError, ValueError):
        return None
    if cuando.tzinfo is None:
        return cuando.replace(tzinfo=timezone.utc)
    return cuando


_POSICIONES = {
    "1": PORTERO, "gk": PORTERO, "por": PORTERO, "pt": PORTERO,
    "portero": PORTERO, "goalkeeper": PORTERO,
    "2": DEFENSA, "def": DEFENSA, "df": DEFENSA, "defensa": DEFENSA,
    "defender": DEFENSA,
    "3": MEDIO, "mid": MEDIO, "med": MEDIO, "cen": MEDIO, "mc": MEDIO,
    "centrocampista": MEDIO, "medio": MEDIO, "midfielder": MEDIO,
    "4": DELANTERO, "fwd": DELANTERO, "del": DELANTERO, "dl": DELANTERO,
    "delantero": DELANTERO, "forward": DELANTERO,
    "5": ENTRENADOR, "ent": ENTRENADOR, "coach": ENTRENADOR,
    "entrenador": ENTRENADOR,
}


def _pos(valor):
    """1 POR, 2 DEF, 3 MED, 4 DEL, 5 entrenador. Si no, None."""
    try:
        if isinstance(valor, bool) or valor is None:
            return None
        if isinstance(valor, (int, float)):
            entero = int(valor)
            return entero if 1 <= entero <= 5 else None
        return _POSICIONES.get(str(valor).strip().lower())
    except Exception:                               # noqa: BLE001
        return None


def _filas(clasificacion) -> list:
    try:
        return [r for r in (clasificacion or []) if isinstance(r, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _jugadores(jugadores) -> list:
    try:
        if isinstance(jugadores, dict):
            jugadores = list(jugadores.values())
        return [j for j in (jugadores or []) if isinstance(j, dict)]
    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# 1. EL CASADO DE NOMBRES: calendario <-> clasificacion -> id
# ============================================================
#
# Hoy las veinte fichas del calendario y de la clasificacion son
# IDENTICAS letra a letra. Pero `league_center.enrich_laliga_logos`
# (league_center.py:616-631) casa por subcadena y gana la ultima:
# "Deportivo Alavés" contiene "Deportivo" y "RCD Espanyol de
# Barcelona" contiene "Barcelona". Aqui NO hay subcadenas: primero
# el nombre exacto, luego sin acentos ni puntuacion, y luego una
# clave por club con reglas escritas para cada par peligroso. Lo que
# no casa sale como None y se dice; nunca se adivina.

def normaliza(nombre) -> str:
    """Minusculas, sin acentos ni puntuacion. "Barça" -> "barca"."""
    try:
        texto = unicodedata.normalize("NFKD", str(nombre or ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = re.sub(r"[^a-z0-9]+", " ", texto.lower())
        return " ".join(texto.split())
    except Exception:                               # noqa: BLE001
        return ""


# Las palabras que no distinguen a nadie. "real" va aqui: solo no
# dice si es el Madrid, la Sociedad, el Betis o el Oviedo.
_GENERICAS = frozenset({
    "fc", "cf", "cd", "sd", "ud", "rcd", "rc", "ca", "cp", "ad", "sad",
    "club", "de", "del", "la", "las", "el", "los", "real", "r",
    "futbol", "balompie",
})

# Las reglas para los pares peligrosos, EN ORDEN: la primera que
# casa gana. Los nombres con una palabra unica van antes que los
# ambiguos ("Club Atletico Osasuna" es Osasuna, no el Atletico).
_REGLAS = (
    ("osasuna", lambda f: "osasuna" in f),
    ("real sociedad", lambda f: "sociedad" in f),
    ("betis", lambda f: "betis" in f),
    ("oviedo", lambda f: "oviedo" in f),
    ("celta", lambda f: "celta" in f or "vigo" in f),
    ("alaves", lambda f: "alaves" in f),
    ("racing", lambda f: "racing" in f and "ferrol" not in f),
    ("rayo", lambda f: "rayo" in f or "vallecano" in f),
    ("espanyol", lambda f: "espanyol" in f or "espanol" in f),
    ("athletic", lambda f: "athletic" in f or "bilbao" in f),
    ("atletico", lambda f: bool(f & {"atletico", "atleti", "atl", "atm"})
        or ("at" in f and "madrid" in f)),
    ("barcelona", lambda f: bool(f & {"barcelona", "barca", "fcb"})),
    ("deportivo", lambda f: bool(f & {"deportivo", "depor", "coruna"})),
    ("real madrid", lambda f: "madrid" in f),
)


def clave_de_equipo(nombre):
    """
    La clave del club: la de su regla, o sus palabras distintivas.

    "RCD Espanyol de Barcelona" -> "espanyol" (nunca "barcelona").
    "Atlético de Madrid" -> "atletico"; "Real Madrid" -> "real madrid".
    "Deportivo Alavés" -> "alaves"; "RC Deportivo" -> "deportivo".
    "Real" a secas -> None: no dice quien es.
    """
    try:
        fichas = frozenset(normaliza(nombre).split())
        if not fichas:
            return None
        for clave, regla in _REGLAS:
            if regla(fichas):
                return clave
        resto = sorted(fichas - _GENERICAS)
        return " ".join(resto) or None
    except Exception:                               # noqa: BLE001
        return None


def _indices(clasificacion):
    """Tres indices de la clasificacion: exacto, normalizado, clave."""
    exacto, normal, por_clave = {}, {}, {}
    repetidas = set()
    for fila in _filas(clasificacion):
        equipo = _int(fila.get("biwenger_team_id"))
        nombre = str(fila.get("team") or "").strip()
        if not equipo or not nombre:
            continue
        exacto.setdefault(nombre, equipo)
        normal.setdefault(normaliza(nombre), equipo)
        clave = clave_de_equipo(nombre)
        if clave:
            if clave in por_clave and por_clave[clave] != equipo:
                repetidas.add(clave)
            por_clave.setdefault(clave, equipo)
    # Una clave que comparten dos equipos no sirve para casar.
    for clave in repetidas:
        por_clave.pop(clave, None)
    return exacto, normal, por_clave


def _casa_uno(nombre, exacto, normal, por_clave):
    texto = str(nombre or "").strip()
    if not texto:
        return None
    if texto in exacto:
        return exacto[texto]
    llano = normaliza(texto)
    if llano and llano in normal:
        return normal[llano]
    clave = clave_de_equipo(texto)
    if clave and clave in por_clave:
        return por_clave[clave]
    return None


def casar_equipos(nombres, clasificacion) -> dict:
    """
    `{nombre: biwenger_team_id o None}` para cada nombre pedido.

    Nunca lanza. Lo que no casa sale con None: quien llama lo dice.
    """
    try:
        exacto, normal, por_clave = _indices(clasificacion)
        salida = {}
        for nombre in (nombres or []):
            if isinstance(nombre, str):
                salida[nombre] = _casa_uno(nombre, exacto, normal, por_clave)
        return salida
    except Exception:                               # noqa: BLE001
        return {}


def _partidos_del_calendario(calendario) -> list:
    """Todos los partidos: los de `matchdays[]` o, si no hay, `matches`."""
    try:
        calendario = calendario if isinstance(calendario, dict) else {}
        partidos = []
        for jornada in (calendario.get("matchdays") or []):
            if not isinstance(jornada, dict):
                continue
            for m in (jornada.get("matches") or []):
                if isinstance(m, dict):
                    if m.get("matchday") is None and jornada.get("matchday") is not None:
                        m = {**m, "matchday": jornada.get("matchday")}
                    partidos.append(m)
        if partidos:
            return partidos
        return [m for m in (calendario.get("matches") or []) if isinstance(m, dict)]
    except Exception:                               # noqa: BLE001
        return []


def los_ids(clasificacion, calendario=None) -> dict:
    """
    `{nombre: biwenger_team_id}` con los nombres de la clasificacion
    y, si llega, los del calendario que casan. Lo que no casa NO
    entra (no se adivina).
    """
    try:
        ids = {}
        for fila in _filas(clasificacion):
            equipo = _int(fila.get("biwenger_team_id"))
            nombre = str(fila.get("team") or "").strip()
            if equipo and nombre:
                ids.setdefault(nombre, equipo)
        nombres = set()
        for m in _partidos_del_calendario(calendario):
            for lado in ("home", "away"):
                nombre = str(m.get(lado) or "").strip()
                if nombre:
                    nombres.add(nombre)
        for nombre, equipo in casar_equipos(sorted(nombres), clasificacion).items():
            if equipo:
                ids.setdefault(nombre, equipo)
        return ids
    except Exception:                               # noqa: BLE001
        return {}


def _id_de(nombre, ids):
    """El id de un nombre del calendario, con el mapa `ids`."""
    try:
        if not isinstance(ids, dict) or not ids:
            return None
        texto = str(nombre or "").strip()
        if not texto:
            return None
        if texto in ids:
            return _int(ids[texto])
        # Un nombre que no estaba al montar el mapa: el mismo casado.
        # Con memoria: se pregunta una vez por jugador y partido.
        pares = tuple(sorted(
            (k, _int(v)) for k, v in ids.items()
            if isinstance(k, str) and _int(v)
        ))
        return _casa_con_el_mapa(texto, pares)
    except Exception:                               # noqa: BLE001
        return None


@lru_cache(maxsize=512)
def _casa_con_el_mapa(texto, pares):
    try:
        filas = [{"team": k, "biwenger_team_id": v} for k, v in pares]
        return casar_equipos([texto], filas).get(texto)
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 2. LA FUERZA DEL RIVAL: quien es duro
# ============================================================

def valor_de_plantilla(jugadores) -> dict:
    """
    `{team_id: suma de los 15 precios mas altos}`. Como el
    laboratorio: todos los que tienen equipo y precio positivo.
    """
    try:
        por_equipo = {}
        for jugador in _jugadores(jugadores):
            equipo = _int(jugador.get("team_id"))
            precio = _num(jugador.get("price"))
            if not equipo or not precio or precio <= 0:
                continue
            por_equipo.setdefault(equipo, []).append(precio)
        return {
            equipo: int(sum(sorted(precios, reverse=True)[:PLANTILLA_TOP]))
            for equipo, precios in por_equipo.items()
        }
    except Exception:                               # noqa: BLE001
        return {}


def _puesto_oficial(fila, indice):
    return _int(fila.get("rank")) or (indice + 1)


def los_duros(clasificacion, valores_de_plantilla=None) -> set:
    """
    Los ids de los rivales DUROS.

    Top-6 por PUNTOS POR PARTIDO (no por puntos: hoy hay equipos
    con 6, 7 y 8 jugados), UNION top-4 por valor de plantilla si
    llega `valores_de_plantilla` (`{team_id: valor}`).

    EL DESEMPATE, por este orden:

        1  puntos por partido
        2  diferencia de goles por partido
        3  goles a favor por partido
        4  el puesto oficial de la tabla (LaLiga ya desempata con el
           golaveraje particular, que aqui no se tiene)
        5  el id, para que el resultado no dependa del orden

    Las cuentas son EXACTAS (fracciones): 19/8 y 19/8 empatan de
    verdad. Siempre salen 6 por la tabla (o todos si hay menos):
    un empate en el corte lo rompe el puesto oficial, no se mete un
    septimo. Sin partidos jugados (inicio de liga) todo empata y
    decide el puesto oficial; por eso el valor de plantilla ayuda.

    En el valor: mas valor primero; a igual valor, el puesto oficial
    y luego el id. Si hay clasificacion, solo cuentan sus equipos
    (un jugador suelto de otro equipo no mete a nadie).
    """
    try:
        filas = _filas(clasificacion)
        orden = []
        puestos = {}
        for indice, fila in enumerate(filas):
            equipo = _int(fila.get("biwenger_team_id"))
            if not equipo:
                continue
            puesto = _puesto_oficial(fila, indice)
            puestos[equipo] = puesto
            jugados = _int(fila.get("played"), 0) or 0
            puntos = _fraccion(fila.get("points"))
            favor = _fraccion(fila.get("goals_for"))
            contra = _fraccion(fila.get("goals_against"))
            diferencia = (
                _fraccion(fila.get("goals_diff"))
                if fila.get("goals_diff") is not None
                else favor - contra
            )
            if jugados > 0:
                ppp = puntos / jugados
                dpp = diferencia / jugados
                fpp = favor / jugados
            else:
                ppp = dpp = fpp = Fraction(0)
            orden.append(((-ppp, -dpp, -fpp, puesto, equipo), equipo))
        orden.sort(key=lambda x: x[0])
        duros = {equipo for _, equipo in orden[:DUROS_POR_TABLA]}

        if isinstance(valores_de_plantilla, dict) and valores_de_plantilla:
            valores = []
            for equipo, valor in valores_de_plantilla.items():
                equipo = _int(equipo)
                valor = _num(valor)
                if not equipo or valor is None or valor <= 0:
                    continue
                if puestos and equipo not in puestos:
                    continue
                valores.append(((-valor, puestos.get(equipo, 99), equipo), equipo))
            valores.sort(key=lambda x: x[0])
            duros |= {equipo for _, equipo in valores[:DUROS_POR_VALOR]}

        return duros
    except Exception:                               # noqa: BLE001
        return set()


def tier(team_id, clasificacion):
    """
    El tramo del equipo por su puesto en la tabla: "1-4", "5-10" o
    "11-20". Sin puesto, None. Sin campo `rank`, el orden de la lista.
    """
    try:
        equipo = _int(team_id)
        if not equipo:
            return None
        for indice, fila in enumerate(_filas(clasificacion)):
            if _int(fila.get("biwenger_team_id")) == equipo:
                puesto = _puesto_oficial(fila, indice)
                if puesto <= 4:
                    return TRAMO_ARRIBA
                if puesto <= 10:
                    return TRAMO_MEDIO
                return TRAMO_ABAJO
        return None
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 3. LAS RONDAS (como las arma Biwenger)
# ============================================================

def _ronda(numero, partidos, etiqueta, principal):
    return {
        "label": etiqueta,
        "matchday": numero,
        "principal": principal,
        "start": partidos[0].get("kickoff"),
        "end": partidos[-1].get("kickoff"),
        "matches": [dict(m) for m in partidos],
    }


def _inicio(ronda):
    """La hora del primer partido de una ronda, ya leida (o None)."""
    try:
        return _cuando((ronda or {}).get("start"))
    except Exception:                               # noqa: BLE001
        return None


def las_rondas(calendario) -> list:
    """
    Las rondas a la Biwenger, ordenadas por su primer partido.

    Por jornada: la VENTANA PRINCIPAL son los partidos a 3 dias o
    menos (72 h) de la mediana (baja) de sus horas. Cada partido de
    fuera es su propia ronda ("Jornada N (adelantada)" o "(aplazada)"),
    salvo que otro de la misma jornada y del mismo lado caiga a 3 dias
    o menos: entonces comparten. Un partido sin hora no se puede
    colocar y no entra.

    Cada ronda: `label`, `matchday`, `principal`, `start` y `end`
    (las horas del primer y ultimo partido, tal cual vienen: texto,
    para que se pueda publicar en JSON) y `matches`.
    """
    try:
        por_jornada = {}
        for m in _partidos_del_calendario(calendario):
            if _cuando(m.get("kickoff")) is None:
                continue
            numero = _int(m.get("matchday"))
            por_jornada.setdefault(numero, []).append(m)

        ventana = timedelta(days=VENTANA_DIAS)
        rondas = []

        for numero, partidos in por_jornada.items():
            partidos = sorted(partidos, key=lambda m: _cuando(m.get("kickoff")))
            horas = [_cuando(m.get("kickoff")) for m in partidos]
            mediana = horas[(len(horas) - 1) // 2]

            nombre = f"Jornada {numero}" if numero is not None else "Jornada ?"

            dentro = [m for m, h in zip(partidos, horas) if abs(h - mediana) <= ventana]
            antes = [m for m, h in zip(partidos, horas) if h < mediana - ventana]
            despues = [m for m, h in zip(partidos, horas) if h > mediana + ventana]

            if dentro:
                rondas.append(_ronda(numero, dentro, nombre, True))

            for lado, sufijo in ((antes, "adelantada"), (despues, "aplazada")):
                grupo = []
                for m in lado:
                    hora = _cuando(m.get("kickoff"))
                    if grupo and hora - _cuando(grupo[0].get("kickoff")) > ventana:
                        rondas.append(_ronda(numero, grupo, f"{nombre} ({sufijo})", False))
                        grupo = []
                    grupo.append(m)
                if grupo:
                    rondas.append(_ronda(numero, grupo, f"{nombre} ({sufijo})", False))

        rondas.sort(key=lambda r: (_inicio(r), r["matchday"] or 0, not r["principal"]))
        return rondas
    except Exception:                               # noqa: BLE001
        return []


def proximas_rondas(calendario, ahora=None, n=HORIZONTE, *, solo_principales=False) -> list:
    """
    Las `n` siguientes rondas que NO han empezado (primer partido
    despues de `ahora`), por hora. La que esta en curso no cuenta:
    su once ya esta cerrado. Sin `ahora`, el reloj (UTC); en los
    tests se pasa siempre.

    `solo_principales` (12/10/2026, la regla del dueño): solo las
    VENTANAS PRINCIPALES. Un adelantado o un aplazado (el
    Levante-Athletic de la J6, el 21/10) Biwenger lo puntua con el
    once que habia al empezar SU jornada: no es una ronda para la
    que se pueda alinear a nadie, asi que no cuenta para valorar
    jugadores ni para el once que se busca. Las `n` son entonces
    `n` principales. Sin pasarlo, todas, como antes.
    """
    try:
        cuando = _cuando(ahora) if ahora is not None else datetime.now(timezone.utc)
        if cuando is None:
            return []
        cuantas = max(_int(n, HORIZONTE) or 0, 0)
        futuras = [
            r for r in las_rondas(calendario)
            if _inicio(r) is not None and _inicio(r) > cuando
            and (not solo_principales or r.get("principal"))
        ]
        return futuras[:cuantas]
    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# 4. LOS FACTORES
# ============================================================

def factor(pos, en_casa, rival_duro) -> float:
    """
    SEDE x RIVAL de un partido.

        sede   1,06 en casa · 0,94 fuera · 1,0 el portero
        rival  0,90 duro · 1,04 el resto

    None en `en_casa` o en `rival_duro` = no se sabe = 1,0 en esa
    parte. Nunca lanza: con basura, 1,0.
    """
    try:
        if _pos(pos) == PORTERO:
            sede = VENUE_PORTERO
        elif en_casa is None:
            sede = 1.0
        else:
            sede = VENUE_CASA if en_casa else VENUE_FUERA
        if rival_duro is None:
            rival = 1.0
        else:
            rival = RIVAL_DURO if rival_duro else RIVAL_RESTO
        return sede * rival
    except Exception:                               # noqa: BLE001
        return 1.0


def _sus_partidos(team_id, ronda, ids, duros) -> list:
    """`[(en_casa, rival_duro)]` del equipo en esa ronda."""
    equipo = _int(team_id)
    if not equipo or not isinstance(ronda, dict):
        return []
    hay_duros = isinstance(duros, (set, frozenset, list, tuple, dict)) and bool(duros)
    duros = {_int(d) for d in duros} if hay_duros else set()
    suyos = []
    for m in (ronda.get("matches") or []):
        if not isinstance(m, dict):
            continue
        casa = _id_de(m.get("home"), ids)
        fuera = _id_de(m.get("away"), ids)
        if casa is not None and casa == equipo:
            en_casa, rival = True, fuera
        elif fuera is not None and fuera == equipo:
            en_casa, rival = False, casa
        else:
            continue
        # Sin lista de duros, o sin rival casado: no se sabe (1,0).
        rival_duro = (rival in duros) if (hay_duros and rival is not None) else None
        suyos.append((en_casa, rival_duro))
    return suyos


def _factor_de_ronda(team_id, pos, ronda, ids, duros) -> float:
    """La suma de los factores de sus partidos; 1,0 si no juega."""
    try:
        suyos = _sus_partidos(team_id, ronda, ids, duros)
        if not suyos:
            return 1.0
        return sum(factor(pos, en_casa, rival_duro) for en_casa, rival_duro in suyos)
    except Exception:                               # noqa: BLE001
        return 1.0


def _base(tasa, prob):
    """`esperado` de la mejora: tasa x titularidad / 100. None si no hay."""
    tasa = _num(tasa)
    prob = _num(prob)
    if tasa is None or prob is None:
        return None
    return tasa * prob / 100.0


# ============================================================
# 5. EL xP DE UNA RONDA Y DEL HORIZONTE
# ============================================================

def xp_ronda(tasa, prob, team_id, pos, ronda, ids, duros):
    """
    xP de la ronda: por cada partido del equipo en ella,
    tasa x prob / 100 x factor, sumados (dos partidos, dos sumas).

    Si el equipo NO juega en esa ronda: tasa x prob / 100, NEUTRO.
    No cero: el aplazado se juega despues con el once de su ronda.

    Sin tasa o sin prob: None (como `esperado`).
    """
    try:
        base = _base(tasa, prob)
        if base is None:
            return None
        return base * _factor_de_ronda(team_id, pos, ronda, ids, duros)
    except Exception:                               # noqa: BLE001
        return None


def xp_horizonte(tasa, prob, team_id, pos, rondas, ids, duros, n=HORIZONTE):
    """
    La suma de `xp_ronda` en las `n` primeras rondas de `rondas`.

    Sin rondas (calendario roto): n x neutro, que es el `esperado`
    de siempre: sin calendario no se castiga ni se premia a nadie.
    Con menos de `n` (fin de liga), las que hay.
    """
    try:
        base = _base(tasa, prob)
        if base is None:
            return None
        cuantas = max(_int(n, HORIZONTE) or 0, 0)
        lista = [r for r in (rondas or []) if isinstance(r, dict)][:cuantas]
        if not lista:
            return base * cuantas
        return sum(
            base * _factor_de_ronda(team_id, pos, r, ids, duros)
            for r in lista
        )
    except Exception:                               # noqa: BLE001
        return None


def factor_medio(team_id, pos, rondas, ids, duros, n=None) -> float:
    """
    La media del factor por ronda (1,0 donde no juega; la suma donde
    juega dos). Para quien solo quiere un multiplicador:

        xp_horizonte == tasa x prob / 100 x factor_medio x rondas

    Sin rondas, 1,0.
    """
    try:
        lista = [r for r in (rondas or []) if isinstance(r, dict)]
        if n is not None:
            lista = lista[:max(_int(n, 0) or 0, 0)]
        if not lista:
            return 1.0
        return sum(
            _factor_de_ronda(team_id, pos, r, ids, duros) for r in lista
        ) / len(lista)
    except Exception:                               # noqa: BLE001
        return 1.0


# ============================================================
# 6. EL ENCOGIMIENTO HACIA EL TRAMO DEL EQUIPO
# ============================================================

def tasa_encogida(points, played, tier, pos, k=K_ENCOGIMIENTO):
    """
    (puntos + k·m) / (jugados + k), con m la media medida de su
    posicion en su tramo (TASA_DEL_TRAMO). La misma cuenta que
    `el_once_objetivo.encoger`.

    El dueño prefiere a los de arriba; el laboratorio dice que la
    fuerza del equipo ya va en la tasa. Las dos cosas a la vez: el
    tramo solo pesa cuando hay pocos partidos. Con 2 partidos y k=3
    el previo pesa un 60 %; con 15, un 17 %.

    Sin tramo, el 5-10 (1,00x la liga). Sin posicion con previo
    (entrenador, basura): la tasa cruda, o None sin partidos.
    """
    try:
        puntos = _num(points, 0.0) or 0.0
        jugados = max(_num(played, 0.0) or 0.0, 0.0)
        peso = max(_num(k, float(K_ENCOGIMIENTO)), 0.0)
        tramo = tier if tier in TASA_DEL_TRAMO else TRAMO_POR_DEFECTO
        media = TASA_DEL_TRAMO[tramo].get(_pos(pos))
        if media is None:
            return puntos / jugados if jugados > 0 else None
        if jugados + peso <= 0:
            return media
        return (puntos + peso * media) / (jugados + peso)
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# 7. EL CONTEXTO: una vez por vuelta
# ============================================================

def contexto(status, calendario, ahora=None, n=HORIZONTE, *, solo_principales=False) -> dict:
    """
    Todo lo que no depende del jugador, montado UNA vez por vuelta:
    el mapa de ids, los duros, los tramos y las `n` proximas rondas
    (con `solo_principales`, las `n` proximas PRINCIPALES: ver
    `proximas_rondas`).

    `status` es el de dashboard/data/status.json (o cualquier dict
    con `league_center.laliga.standings` y `todaLaLiga.players`).
    Forma fija, nunca lanza. `available` dice si hay calendario y
    clasificacion; `sin_casar` los nombres del calendario sin id.
    """
    vacio = {
        "available": False,
        "ids": {},
        "duros": set(),
        "tramos": {},
        "valores": {},
        "rondas": [],
        "sin_casar": [],
        "reason": None,
    }
    try:
        status = status if isinstance(status, dict) else {}
        clasificacion = _filas(
            (((status.get("league_center") or {}).get("laliga") or {})
             .get("standings"))
        )
        jugadores = _jugadores((status.get("todaLaLiga") or {}).get("players"))

        valores = valor_de_plantilla(jugadores)
        duros = los_duros(clasificacion, valores)
        ids = los_ids(clasificacion, calendario)
        rondas = proximas_rondas(calendario, ahora, n, solo_principales=solo_principales)
        tramos = {}
        for fila in clasificacion:
            equipo = _int(fila.get("biwenger_team_id"))
            if equipo:
                tramos[equipo] = tier(equipo, clasificacion)

        nombres = set()
        for m in _partidos_del_calendario(calendario):
            for lado in ("home", "away"):
                nombre = str(m.get(lado) or "").strip()
                if nombre:
                    nombres.add(nombre)
        sin_casar = sorted(x for x in nombres if x not in ids)

        if not clasificacion:
            motivo = "Sin clasificación: no se sabe quién es duro ni el tramo."
        elif not nombres:
            motivo = "Sin calendario: el xP sale neutro (el esperado de siempre)."
        elif sin_casar:
            motivo = f"{len(sin_casar)} equipo(s) del calendario sin casar: {', '.join(sin_casar)}."
        else:
            motivo = f"{len(rondas)} ronda(s) por delante, {len(duros)} rivales duros."

        return {
            "available": bool(clasificacion) and bool(nombres),
            "ids": ids,
            "duros": duros,
            "tramos": tramos,
            "valores": valores,
            "rondas": rondas,
            "sin_casar": sin_casar,
            "reason": motivo,
        }
    except Exception as error:                      # noqa: BLE001
        return {**vacio, "reason": f"{type(error).__name__}: {error}"}


def xp_jugador(ctx, player, prob=None, n=1):
    """
    xP de un jugador en las `n` proximas rondas (1 o 3), con su tasa
    ENCOGIDA hacia su tramo y los factores del calendario.

    `prob` es la titularidad 0-100; si no llega, la del jugador
    (`starter_probability`). Sin ninguna, None.
    """
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        if not isinstance(player, dict):
            return None
        if prob is None:
            prob = player.get("starter_probability")
        equipo = _int(player.get("team_id"))
        pos = _pos(player.get("position"))
        tramos = ctx.get("tramos") if isinstance(ctx.get("tramos"), dict) else {}
        tasa = tasa_encogida(
            player.get("points"), player.get("played"), tramos.get(equipo), pos,
        )
        return xp_horizonte(
            tasa, prob, equipo, pos,
            ctx.get("rondas") or [], ctx.get("ids") or {}, ctx.get("duros") or set(),
            n,
        )
    except Exception:                               # noqa: BLE001
        return None
