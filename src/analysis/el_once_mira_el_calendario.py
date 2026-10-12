"""
EL ONCE MIRA EL CALENDARIO (12/10/2026)

POR QUE EXISTE

    El once que Pepe escribe en Biwenger se ordena por la vara
    (`weekly_expected_value`: participacion x calidad x factor de
    posicion, lineup_engine.py:809-893) por 1.000.000. El unico dato
    del partido que entraba era el `HOME_BONUS` de +5
    (home_away_intelligence.py:5): cinco puntos en una escala de un
    millon, un desempate de desempates. Roberto Fernandez en casa
    contra el Atletico (2.º) puntuaba igual que fuera contra el
    colista.

    El laboratorio del 12/10 (`el_calendario_de_puntos.py`) MIDIO
    cuanto pesa el partido, jugador-partido de toda la liga, J7 y J8:

        SEDE   1,06 en casa · 0,94 fuera   (n = 268 / 272, mezclado
               con el estudio del 26/09, n = 1.016)
        RIVAL  0,90 duro (top-6, n = 168) · 1,04 el resto
        EL PORTERO NO TIENE SEDE (n = 34: ruido), el rival si.

    Este modulo lleva esos factores al once de la PROXIMA ronda.

LA REGLA

    1. La ronda objetivo es la proxima que NO ha empezado
       (`el_calendario_de_puntos.proximas_rondas(calendario, ahora,
       1)`), con las rondas a lo Biwenger: el adelantado y el aplazado
       van aparte, con su propio cierre.

    2. El multiplicador de un jugador es la SUMA, sobre los partidos
       de su equipo en esa ronda, de `factor(pos, en_casa,
       rival_duro)`. Dos partidos en la ronda, dos sumandos.

    3. Si su equipo NO juega en esa ronda: 1,0, NEUTRO. Nunca cero.
       El dueño: un aplazado se juega despues CON EL ONCE PUESTO EN
       SU RONDA, asi que esos puntos llegan igual.

    4. Duro = `el_calendario_de_puntos.los_duros(clasificacion,
       valor de plantilla)`: top-6 por puntos por partido, UNION
       top-4 por valor de plantilla (los 15 mas caros del catalogo).

    5. Entra en `lineup_engine.prepare_players` justo DESPUES de
       `weekly_expected_value` (que sigue cruda: se publica y se mide
       sin correccion) y ANTES de `final_score`: vara x multiplicador.

    6. Con el interruptor puesto y el partido sabido, el +5 de casa
       NO se suma: la sede ya va dentro del multiplicador y contarla
       dos veces seria inventar ventaja. Si el calendario no dice nada
       (sin clasificacion, sin ronda, equipo sin id), el jugador se
       queda EXACTAMENTE como hoy: multiplicador 1,0 y su +5.

    7. El bono del Dios (+10 M, lineup_engine.py:623) no se toca.

    PESA POCO, Y ESTA BIEN QUE PESE POCO. El multiplicador va de 0,846
    (fuera contra un duro) a 1,102 (en casa contra el resto): entre
    dos delanteros parecidos decide el partido; un Clave al 90 % no se
    sienta por jugar en el Bernabeu.

UNA VEZ POR VUELTA

    `build_lineup` corre ~135 veces por vuelta
    (el_once_se_busca_una_vez.py:6-17) y `prepare_players` con el. Los
    partidos por equipo se montan UNA vez por (calendario,
    clasificacion, catalogo, ronda objetivo) y se recuerdan en
    `_MEMORIA`, como `_MULTISOURCE_STARTER_CACHE`
    (lineup_engine.py:38). El calendario y la clasificacion del disco
    se leen una vez por fichero y version (`mtime`, tamaño).

    LA MEMORIA DEL ONCE NO SE PUEDE QUEDAR VIEJA. La de
    `el_once_se_busca_una_vez` recuerda por el CONTENIDO exacto de los
    jugadores, y el multiplicador va dentro de cada uno
    (`lineup_score`, `fixture_multiplier`). Si el factor cambiase, la
    entrada seria otra y se buscaria otra vez.

    Y DENTRO DE UNA VUELTA EL FACTOR ES CONSTANTE. Solo cambia si
    cambia el calendario, la clasificacion (la cache del panel: se
    escribe DESPUES de la vuelta, en `build_dashboard`) o la ronda
    objetivo. La ronda solo cambia cuando empieza su primer partido, y
    desde T-15 el once esta cerrado (ROUND_LOCKED,
    matchday_calendar_engine.py:716-797): una vuelta que cruzase un
    primer partido no puede escribir el once de esa ronda.

QUE NO HACE

    No sale a la red: lee la clasificacion de la cache que deja el
    panel (`data/league_center/laliga_standings.json`,
    league_center.py:16-18) y el calendario
    (`data/calendar/laliga_calendar.json`). Si faltan, neutro.

    No cambia `weekly_expected_value` ni el bono del Dios. No mide la
    rotacion por rival (la titularidad es la de FF). No decide compras
    ni ventas, aunque `lineup_score_sporting` lo hereda: quien valore
    la venta de un titular con el once vera su partido.

    Con el interruptor APAGADO no se lee nada ni se toca nada: el once
    es el de siempre, byte a byte (hay guardia).

EL INTERRUPTOR

    `BORDALAS_EL_CALENDARIO_EN_EL_ONCE`, apagado de fabrica.

NUNCA LANZA

    Todo corre en produccion, dentro del once. Con basura de entrada
    sale el neutro (1,0) con su motivo.
"""

from __future__ import annotations

import hashlib
import json
import os

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


ENV = "BORDALAS_EL_CALENDARIO_EN_EL_ONCE"

RAIZ = Path(__file__).parents[2]

# El mismo fichero que `la_proxima_jornada.CALENDARIO` y
# `los_chollos.CALENDARIO`.
CALENDARIO = RAIZ / "data" / "calendar" / "laliga_calendar.json"

# La cache de la clasificacion de LaLiga que escribe el panel
# (`league_center.LALIGA_CACHE_FILE`, league_center.py:16-17). Se
# restaura con `actions/cache` antes de la vuelta, asi que la vuelta
# lee la de la vuelta anterior (de 1 a 7 horas). Sus filas NO traen
# `biwenger_team_id`: se lo pone `enrich_laliga_logos` al montar el
# panel, y por subcadena. Aqui se casa con el catalogo, sin subcadenas.
CLASIFICACION = RAIZ / "data" / "league_center" / "laliga_standings.json"

NEUTRO = 1.0

# Cuantas combinaciones (calendario, clasificacion, catalogo, ronda)
# se recuerdan. En una vuelta hay una, o dos si la foto se rehace y
# cambia un precio del catalogo. 32 es margen de sobra.
TOPE = 32


_MEMORIA: "OrderedDict[tuple, dict]" = OrderedDict()

# huella del calendario -> [(inicio, etiqueta)] de sus rondas.
_RONDAS: "OrderedDict[str, list]" = OrderedDict()

# ruta -> (mtime_ns, tamaño, contenido, huella).
_DISCO: dict = {}

_CUENTA = {"calculos": 0, "aciertos": 0, "sin_clave": 0}


# ============================================================
# EL INTERRUPTOR Y LA MEMORIA
# ============================================================

def activa() -> bool:
    """Si el once mira el calendario. Nunca lanza."""
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


def olvidar() -> None:
    """Vacia la memoria y la cuenta. Para las guardias."""
    _MEMORIA.clear()
    _RONDAS.clear()
    _DISCO.clear()
    for clave in _CUENTA:
        _CUENTA[clave] = 0


def cuenta() -> dict:
    """Calculos hechos, aciertos de memoria y llamadas sin clave."""
    return {**_CUENTA, "recordadas": len(_MEMORIA)}


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


def _momento(valor):
    """La hora con zona; sin zona, UTC (como `el_calendario_de_puntos`)."""
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


def _huella(objeto):
    """sha256 del JSON ordenado. None si no se puede serializar."""
    try:
        crudo = json.dumps(objeto, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(crudo.encode("utf-8")).hexdigest()
    except Exception:                               # noqa: BLE001
        return None


def _del_disco(ruta):
    """
    `(contenido, huella)` de un JSON del disco, leido una vez por
    version del fichero. `(None, "sin-fichero")` si no esta o no se
    puede leer: eso tambien es una respuesta, y se recuerda.
    """
    try:
        camino = Path(ruta)
        if not camino.exists():
            return None, "sin-fichero"
        estado = camino.stat()
        clave = str(camino)
        guardado = _DISCO.get(clave)
        if guardado and guardado[0] == estado.st_mtime_ns and guardado[1] == estado.st_size:
            return guardado[2], guardado[3]
        texto = camino.read_text(encoding="utf-8")
        contenido = json.loads(texto)
        huella = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        _DISCO[clave] = (estado.st_mtime_ns, estado.st_size, contenido, huella)
        return contenido, huella
    except Exception:                               # noqa: BLE001
        return None, "ilegible"


def _filas_de(clasificacion) -> list:
    """Las filas: una lista, o el `standings` de la cache del panel."""
    try:
        if isinstance(clasificacion, dict):
            clasificacion = clasificacion.get("standings")
        return [dict(f) for f in (clasificacion or []) if isinstance(f, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _catalogo(snapshot) -> dict:
    try:
        datos = ((snapshot or {}).get("catalog") or {}).get("data") or {}
        return datos if isinstance(datos, dict) else {}
    except Exception:                               # noqa: BLE001
        return {}


def _valores(coleccion) -> list:
    try:
        if isinstance(coleccion, dict):
            coleccion = list(coleccion.values())
        return [x for x in (coleccion or []) if isinstance(x, dict)]
    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# LO QUE SALE DE LA FOTO: los equipos y su valor
# ============================================================

def equipos_del_catalogo(snapshot) -> list:
    """
    `[{"team", "biwenger_team_id"}]` de `catalog.data.teams`, con la
    forma de una fila de clasificacion para poder casar con ella.
    Vacio sin catalogo. Nunca lanza.
    """
    try:
        filas = []
        for equipo in _valores(_catalogo(snapshot).get("teams")):
            ident = _int(equipo.get("id"))
            nombre = str(equipo.get("name") or "").strip()
            if ident and nombre:
                filas.append({"team": nombre, "biwenger_team_id": ident})
        return sorted(filas, key=lambda f: f["biwenger_team_id"])
    except Exception:                               # noqa: BLE001
        return []


def valores_del_catalogo(snapshot) -> dict:
    """
    `{team_id: valor de plantilla}` del catalogo de la foto, con la
    cuenta del laboratorio (`valor_de_plantilla`: los 15 mas caros).
    Vacio sin catalogo. Nunca lanza.
    """
    try:
        from src.analysis.el_calendario_de_puntos import valor_de_plantilla

        jugadores = [
            {"team_id": j.get("teamID", j.get("team_id")), "price": j.get("price")}
            for j in _valores(_catalogo(snapshot).get("players"))
        ]
        return valor_de_plantilla(jugadores)
    except Exception:                               # noqa: BLE001
        return {}


def con_ids(clasificacion, equipos=None) -> list:
    """
    Las filas de la clasificacion con su `biwenger_team_id`. La que
    ya lo trae se queda como esta; la que no, se casa por nombre con
    los equipos del catalogo (`casar_equipos`: exacto, sin acentos y
    por clave de club, NUNCA por subcadena). Lo que no casa se queda
    sin id. Copias: no toca lo que entra. Nunca lanza.
    """
    try:
        from src.analysis.el_calendario_de_puntos import casar_equipos

        filas = _filas_de(clasificacion)
        faltan = [
            str(f.get("team") or "").strip() for f in filas
            if not _int(f.get("biwenger_team_id")) and str(f.get("team") or "").strip()
        ]
        if not faltan or not equipos:
            return filas
        casado = casar_equipos(faltan, equipos)
        for fila in filas:
            if not _int(fila.get("biwenger_team_id")):
                ident = casado.get(str(fila.get("team") or "").strip())
                if ident:
                    fila["biwenger_team_id"] = ident
        return filas
    except Exception:                               # noqa: BLE001
        return _filas_de(clasificacion)


# ============================================================
# LOS PARTIDOS DE LA RONDA, POR EQUIPO (puro)
# ============================================================

def _vacio(motivo) -> dict:
    return {
        "available": False,
        "ronda": None,
        "equipos": {},
        "conocidos": [],
        "ronda_completa": False,
        "duros": [],
        "sin_casar": [],
        "sin_id": [],
        "reason": motivo,
    }


def los_factores(calendario, clasificacion, ahora, equipos=None, valores=None) -> dict:
    """
    Los partidos de cada equipo en la proxima ronda que no ha
    empezado, con la sede y si el rival es duro:

        {"available", "ronda": {label, matchday, principal, start},
         "equipos": {team_id: [{en_casa, rival, rival_id, rival_duro}]},
         "conocidos": [ids de Biwenger casados], "ronda_completa",
         "duros": [ids], "sin_casar": [nombres del calendario],
         "sin_id": [filas sin id de Biwenger], "reason"}

    Puro: todo llega por argumento, `ahora` incluido (sin `ahora` no
    se mira el reloj: sale neutro). `equipos` son las filas del
    catalogo para casar la clasificacion que no trae ids; `valores`
    el valor de plantilla por equipo. Nunca lanza.
    """
    try:
        from src.analysis.el_calendario_de_puntos import (
            los_duros, los_ids, proximas_rondas,
        )

        momento = _momento(ahora)
        if momento is None:
            return _vacio("sin hora de referencia")

        filas = con_ids(clasificacion, equipos)
        if not filas:
            return _vacio("sin clasificacion de LaLiga")

        conocidos = {
            _int(f.get("biwenger_team_id")) for f in filas
            if (_int(f.get("biwenger_team_id")) or 0) > 0
        }
        if not conocidos:
            return _vacio("la clasificacion no casa con ningun equipo de Biwenger")

        # LA FILA QUE NO CASA SIGUE EN LA TABLA. `los_duros` se salta
        # las filas sin id: con una sin casar, el top-6 se contaria
        # entre 19 y entraria el 7.º. Se le da un id de mentira
        # (negativo: ningun jugador lo tiene) para que cuente al
        # ordenar y como rival. Sus jugadores se quedan como hoy:
        # `para_el_jugador` solo decide por los equipos `conocidos`.
        sin_id = []
        for indice, fila in enumerate(filas):
            if (_int(fila.get("biwenger_team_id")) or 0) <= 0:
                fila["biwenger_team_id"] = -(indice + 1)
                sin_id.append(str(fila.get("team") or "?"))

        rondas = proximas_rondas(calendario, momento, 1)
        if not rondas:
            return _vacio("sin proxima ronda en el calendario")
        ronda = rondas[0]

        ids = los_ids(filas, calendario)
        duros = los_duros(filas, valores if isinstance(valores, dict) else None)

        por_equipo: dict = {}
        sin_casar = set()

        for partido in (ronda.get("matches") or []):
            if not isinstance(partido, dict):
                continue
            nombre_casa = str(partido.get("home") or "").strip()
            nombre_fuera = str(partido.get("away") or "").strip()
            casa = _int(ids.get(nombre_casa))
            fuera = _int(ids.get(nombre_fuera))
            for nombre, ident in ((nombre_casa, casa), (nombre_fuera, fuera)):
                if nombre and not ident:
                    sin_casar.add(nombre)
            for ident, en_casa, rival, rival_id in (
                (casa, True, nombre_fuera, fuera),
                (fuera, False, nombre_casa, casa),
            ):
                if not ident:
                    continue
                # Rival sin id o sin lista de duros: no se sabe (1,0
                # en esa parte del factor), no se adivina.
                rival_duro = (rival_id in duros) if (rival_id and duros) else None
                por_equipo.setdefault(ident, []).append({
                    "en_casa": en_casa,
                    "rival": rival or None,
                    "rival_id": rival_id,
                    "rival_duro": rival_duro,
                })

        etiqueta = ronda.get("label")
        return {
            "available": True,
            "ronda": {
                "label": etiqueta,
                "matchday": ronda.get("matchday"),
                "principal": ronda.get("principal"),
                "start": ronda.get("start"),
            },
            "equipos": por_equipo,
            "conocidos": sorted(conocidos),
            # Con un nombre del calendario sin casar en ESTA ronda no
            # se puede decir de nadie que «no juega»: podria ser el.
            "ronda_completa": not sin_casar,
            "duros": sorted(d for d in duros if d is not None),
            "sin_casar": sorted(sin_casar),
            "sin_id": sorted(sin_id),
            "reason": (
                f"{etiqueta}: {len(por_equipo)} equipos con partido, "
                f"{len(duros)} rivales duros"
                + (f", sin casar: {', '.join(sorted(sin_casar))}" if sin_casar else "")
                + (f", sin id de Biwenger: {', '.join(sorted(sin_id))}" if sin_id else "")
            ),
        }
    except Exception as error:                      # noqa: BLE001
        return _vacio(f"{type(error).__name__}: {error}")


def para_el_jugador(factores, team_id, posicion) -> dict:
    """
    Lo que el calendario dice de un jugador:

        {"multiplicador", "motivo", "con_calendario", "partidos"}

    `con_calendario` es True cuando el calendario HA DECIDIDO (hay
    ronda, clasificacion y el equipo tiene id), juegue o no: entonces
    la sede va en el multiplicador y el +5 de casa no se suma. False
    cuando no sabe nada: multiplicador 1,0 y el jugador como hoy.
    Nunca lanza.
    """
    try:
        from src.analysis.el_calendario_de_puntos import factor

        if not isinstance(factores, dict) or not factores.get("available"):
            motivo = (factores or {}).get("reason") if isinstance(factores, dict) else None
            return {
                "multiplicador": NEUTRO,
                "motivo": f"neutro: {motivo or 'sin calendario'}",
                "con_calendario": False,
                "partidos": [],
            }

        etiqueta = (factores.get("ronda") or {}).get("label") or "proxima ronda"
        equipo = _int(team_id)
        if not equipo:
            return {
                "multiplicador": NEUTRO,
                "motivo": f"{etiqueta}: sin equipo, neutro",
                "con_calendario": False,
                "partidos": [],
            }

        # Su equipo no esta en la clasificacion casada: no se sabe
        # contra quien juega. Como hoy.
        conocidos = {_int(c) for c in (factores.get("conocidos") or [])}
        if equipo not in conocidos:
            return {
                "multiplicador": NEUTRO,
                "motivo": f"{etiqueta}: su equipo no casa con la clasificacion, neutro",
                "con_calendario": False,
                "partidos": [],
            }

        equipos = factores.get("equipos") if isinstance(factores.get("equipos"), dict) else {}
        partidos = [p for p in (equipos.get(equipo) or []) if isinstance(p, dict)]
        if not partidos:
            if not factores.get("ronda_completa"):
                # Un nombre de la ronda sin casar podria ser el suyo.
                return {
                    "multiplicador": NEUTRO,
                    "motivo": f"{etiqueta}: partido sin casar, neutro",
                    "con_calendario": False,
                    "partidos": [],
                }
            # El dueño: el aplazado se juega con el once de su ronda.
            return {
                "multiplicador": NEUTRO,
                "motivo": f"{etiqueta}: no juega en esta ronda, neutro",
                "con_calendario": True,
                "partidos": [],
            }

        total = 0.0
        trozos = []
        for p in partidos:
            total += factor(posicion, p.get("en_casa"), p.get("rival_duro"))
            sede = "en casa" if p.get("en_casa") else "fuera"
            tramo = {True: "duro", False: "resto"}.get(p.get("rival_duro"), "sin dato")
            trozos.append(f"{sede} vs {p.get('rival') or '?'} ({tramo})")

        if not (total > 0) or total != total:
            return {
                "multiplicador": NEUTRO,
                "motivo": f"{etiqueta}: factor sin sentido, neutro",
                "con_calendario": False,
                "partidos": [],
            }

        return {
            "multiplicador": total,
            "motivo": f"{etiqueta}: {' + '.join(trozos)} x{total:.3f}",
            "con_calendario": True,
            "partidos": [dict(p) for p in partidos],
        }
    except Exception as error:                      # noqa: BLE001
        return {
            "multiplicador": NEUTRO,
            "motivo": f"neutro: {type(error).__name__}",
            "con_calendario": False,
            "partidos": [],
        }


# ============================================================
# LA VUELTA: una vez, y recordado
# ============================================================

def _la_ronda_objetivo(calendario, huella, momento):
    """`(inicio, etiqueta)` de la proxima ronda, con las rondas
    del calendario montadas una vez por huella. None si no hay."""
    try:
        from src.analysis.el_calendario_de_puntos import las_rondas

        rondas = _RONDAS.get(huella) if huella else None
        if rondas is None:
            rondas = []
            for r in las_rondas(calendario):
                inicio = _momento(r.get("start"))
                if inicio is not None:
                    rondas.append((inicio, r.get("label")))
            if huella:
                _RONDAS[huella] = rondas
                while len(_RONDAS) > TOPE:
                    _RONDAS.popitem(last=False)
        for inicio, etiqueta in rondas:
            if inicio > momento:
                return inicio.isoformat(), etiqueta
        return None
    except Exception:                               # noqa: BLE001
        return None


def del_ciclo(snapshot, ahora=None, calendario=None, clasificacion=None) -> dict:
    """
    Los factores de la vuelta, calculados UNA vez y recordados.

    En produccion no llega nada mas que la foto: la hora es la del
    reloj (UTC), el calendario y la clasificacion los del disco. Las
    guardias pasan `ahora`, `calendario` y `clasificacion` y no se
    abre nada.

    La clave es (calendario, clasificacion, equipos y valor del
    catalogo, ronda objetivo): con la misma entrada, la misma
    respuesta sin recalcular. Nunca lanza.
    """
    try:
        momento = _momento(ahora if ahora is not None else datetime.now(timezone.utc))
        if momento is None:
            return _vacio("sin hora de referencia")

        if calendario is None:
            calendario, huella_calendario = _del_disco(CALENDARIO)
        else:
            huella_calendario = _huella(calendario)

        if clasificacion is None:
            clasificacion, huella_clasificacion = _del_disco(CLASIFICACION)
        else:
            huella_clasificacion = _huella(clasificacion)

        equipos = equipos_del_catalogo(snapshot)
        valores = valores_del_catalogo(snapshot)
        huella_catalogo = _huella([equipos, sorted(valores.items())])

        ronda = _la_ronda_objetivo(calendario, huella_calendario, momento)

        clave = (
            (huella_calendario, huella_clasificacion, huella_catalogo, ronda)
            if None not in (huella_calendario, huella_clasificacion, huella_catalogo)
            else None
        )

        if clave is not None and clave in _MEMORIA:
            _MEMORIA.move_to_end(clave)
            _CUENTA["aciertos"] += 1
            return _MEMORIA[clave]

        if clave is None:
            _CUENTA["sin_clave"] += 1

        _CUENTA["calculos"] += 1
        factores = los_factores(calendario, clasificacion, momento, equipos, valores)

        if clave is not None:
            _MEMORIA[clave] = factores
            while len(_MEMORIA) > TOPE:
                _MEMORIA.popitem(last=False)

        return factores
    except Exception as error:                      # noqa: BLE001
        return _vacio(f"{type(error).__name__}: {error}")


def para_el_once(snapshot, ahora=None, calendario=None, clasificacion=None):
    """
    Lo que `prepare_players` pide: None con el interruptor APAGADO
    (entonces el once es el de siempre y no se lee nada), y los
    factores de la vuelta con el interruptor puesto. Nunca lanza.
    """
    try:
        if not activa():
            return None
        return del_ciclo(snapshot, ahora=ahora, calendario=calendario,
                         clasificacion=clasificacion)
    except Exception:                               # noqa: BLE001
        return None
