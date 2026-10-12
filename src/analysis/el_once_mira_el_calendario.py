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

    1. La ronda objetivo es la proxima ronda PRINCIPAL que NO ha
       empezado (`el_calendario_de_puntos.proximas_rondas`, filtrada
       por `principal`). El aplazado y el adelantado NO son ronda
       objetivo: la regla del dueño (12/10) es que Biwenger puntua el
       aplazado con el once que habia cuando empezo SU jornada. El
       Levante-Athletic de la J6 del 21/10 cae entre la J9 y la J10,
       pero el once que se escribe esa semana es el de la J10.

    2. El multiplicador de un jugador es `factor(pos, en_casa,
       rival_duro)` de SU partido en esa ronda. Una ronda es una sola
       jornada y en una jornada cada equipo juega una vez: un partido
       repetido en el calendario cuenta una vez, y si un equipo
       saliese dos veces en la jornada se queda el primero (por hora).
       Nunca 2,0 por un dato duplicado.

    3. Si su equipo NO juega en esa ronda: 1,0, NEUTRO. Nunca cero.
       El dueño: un aplazado se juega despues CON EL ONCE PUESTO EN
       SU RONDA, asi que esos puntos llegan igual.

    4. Duro = `el_calendario_de_puntos.los_duros(clasificacion,
       valor de plantilla)`: top-6 por puntos por partido, UNION
       top-4 por valor de plantilla (los 15 mas caros del catalogo).
       Una clasificacion bajada hace mas de `CADUCIDAD` (7 dias,
       `fetched_at_unix` o `fetched_at` de la cache del panel) no
       decide nada: neutro, como sin clasificacion.

    5. Entra en `lineup_engine.prepare_players` justo DESPUES de
       `weekly_expected_value` (que sigue cruda: se publica y se mide
       sin correccion) y ANTES de `final_score`. Con vara positiva,
       vara x multiplicador. Con vara NEGATIVA, vara + |vara| x
       (multiplicador - 1): un partido malo la hunde mas y uno bueno
       la acerca a cero, nunca al reves (`vara_del_once`).

    5 bis. SOLO EL ONCE QUE SE ESCRIBE. `prepare_players` y
       `build_lineup` llevan `con_calendario=False` por defecto: la
       venta, la liquidez, la deuda segura, el tablero de fichajes,
       el orden de venta y el valor deportivo del once
       (`lineup_score_sporting`) siguen con la vara cruda. Solo
       `lineup_monitor.build_lineup_monitor_state` -el once que lleva
       SAVE_LINEUP- pide `con_calendario=True`, y solo con el
       interruptor puesto. Un desempate de una ronda no puede decidir
       una venta para siempre.

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

    DENTRO DE UNA VUELTA EL FACTOR CASI SIEMPRE ES CONSTANTE. Solo
    cambia si cambia el calendario, la clasificacion (la cache del
    panel: se escribe DESPUES de la vuelta, en `build_dashboard`) o la
    ronda objetivo, y la ronda objetivo solo cambia cuando empieza el
    primer partido de una ronda PRINCIPAL. NO es una garantia de que
    eso caiga dentro de ROUND_LOCKED: `matchday_calendar_engine` agrupa
    jornadas enteras por su primer partido, adelantado incluido, y
    aqui se mira la ventana principal. Con un partido adelantado los
    dos motores pueden discrepar de ronda entre el adelantado y la
    ventana principal (de horas a dias), y una
    vuelta que cruce el primer partido de una ronda principal puede
    ver dos factores. La memoria del once sigue siendo correcta
    (recuerda por contenido); lo que no se promete es que dos
    llamadas de la misma vuelta coincidan en ese borde.

QUE NO HACE

    No sale a la red: lee la clasificacion de la cache que deja el
    panel (`data/league_center/laliga_standings.json`,
    league_center.py:16-18) y el calendario
    (`data/calendar/laliga_calendar.json`). Si faltan, neutro.

    No cambia `weekly_expected_value` ni el bono del Dios. No mide la
    rotacion por rival (la titularidad es la de FF). No decide compras
    ni ventas: quien valora (venta, liquidez, deuda segura, fichajes,
    orden de venta) llama a `build_lineup`/`prepare_players` sin
    `con_calendario` y ve el once de siempre, con su
    `lineup_score_sporting` crudo (hay guardia).

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
from datetime import datetime, timedelta, timezone
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

# Una clasificacion mas vieja que esto no decide quien es duro. La
# cache del panel caduca a las 6 h (league_center.py:18), pero si
# LaLiga falla se sigue sirviendo la ultima; una semana es una jornada
# entera sin refrescar.
CADUCIDAD = timedelta(days=7)

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


def _reloj():
    """La hora de la vuelta (UTC). Las guardias la suplantan."""
    return datetime.now(timezone.utc)


def _bajada(clasificacion):
    """
    Cuando se bajo la clasificacion de la cache del panel:
    `fetched_at_unix` (epoch) o, si no, `fetched_at` (ISO; sin zona,
    UTC, que es la hora de CI). None si no lo dice: una lista suelta
    o una fila con ids no trae fecha. Nunca lanza.
    """
    try:
        if not isinstance(clasificacion, dict):
            return None
        epoch = clasificacion.get("fetched_at_unix")
        if isinstance(epoch, (int, float)) and not isinstance(epoch, bool) and epoch > 0:
            return datetime.fromtimestamp(float(epoch), tz=timezone.utc)
        return _momento(clasificacion.get("fetched_at"))
    except Exception:                               # noqa: BLE001
        return None


def caducada(clasificacion, ahora) -> bool:
    """
    True si la clasificacion dice cuando se bajo y fue hace mas de
    `CADUCIDAD`. Sin fecha, o sin `ahora`, no se puede decir: False
    (lo de siempre). Nunca lanza.
    """
    try:
        momento = _momento(ahora)
        bajada = _bajada(clasificacion)
        if momento is None or bajada is None:
            return False
        return (momento - bajada) > CADUCIDAD
    except Exception:                               # noqa: BLE001
        return False


def vara_del_once(vara, multiplicador):
    """
    La vara con el partido dentro, sin que el signo la de la vuelta.

    Con vara positiva, vara x multiplicador. Con vara NEGATIVA (un
    jugador con puntos negativos esta temporada) multiplicar la
    acercaria a cero con un partido MALO: x0,846 hace -0,10 -> -0,085
    y lo sube por encima del que juega en casa contra el colista.
    Asi que se mueve en la direccion del partido: vara + |vara| x
    (multiplicador - 1). Nunca lanza: con basura, la vara tal cual.
    """
    try:
        if vara >= 0:
            return vara * multiplicador
        return vara + abs(vara) * (multiplicador - 1.0)
    except Exception:                               # noqa: BLE001
        return vara


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


def _la_proxima_principal(calendario, momento):
    """
    La proxima ronda PRINCIPAL que no ha empezado, o None. El
    aplazado y el adelantado se saltan: se puntuan con el once de su
    jornada (decision del dueño, 12/10). Se filtra aqui, sobre
    `proximas_rondas`, para no tocar `el_calendario_de_puntos`.
    """
    try:
        from src.analysis.el_calendario_de_puntos import proximas_rondas

        for ronda in proximas_rondas(calendario, momento, 10_000):
            if isinstance(ronda, dict) and ronda.get("principal") is True:
                return ronda
        return None
    except Exception:                               # noqa: BLE001
        return None


def los_factores(calendario, clasificacion, ahora, equipos=None, valores=None) -> dict:
    """
    Los partidos de cada equipo en la proxima ronda PRINCIPAL que no
    ha empezado, con la sede y si el rival es duro:

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
        from src.analysis.el_calendario_de_puntos import los_duros, los_ids

        momento = _momento(ahora)
        if momento is None:
            return _vacio("sin hora de referencia")

        # UNA TABLA DE HACE UNA SEMANA NO DICE QUIEN ES DURO. Si LaLiga
        # lleva dias fallando, el panel sigue sirviendo la ultima.
        if caducada(clasificacion, momento):
            return _vacio(
                f"clasificacion de LaLiga caducada (bajada el "
                f"{_bajada(clasificacion).isoformat()}, mas de "
                f"{CADUCIDAD.days} dias)"
            )

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

        ronda = _la_proxima_principal(calendario, momento)
        if not ronda:
            return _vacio("sin proxima ronda principal en el calendario")

        ids = los_ids(filas, calendario)
        duros = los_duros(filas, valores if isinstance(valores, dict) else None)

        por_equipo: dict = {}
        sin_casar = set()

        # UN PARTIDO POR EQUIPO Y JORNADA. Una ronda es una jornada y
        # en una jornada cada equipo juega una vez: un equipo que
        # saliese dos veces (el mismo partido duplicado en el
        # calendario, o dos rivales) se queda con el primero, por
        # hora. Sumar los dos daria ~2,0: +600.000 de score por un
        # dato repetido.
        jornada_de = {}

        for partido in (ronda.get("matches") or []):
            if not isinstance(partido, dict):
                continue
            nombre_casa = str(partido.get("home") or "").strip()
            nombre_fuera = str(partido.get("away") or "").strip()
            jornada = _int(partido.get("matchday"), _int(ronda.get("matchday")))
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
                if jornada in jornada_de.setdefault(ident, set()):
                    continue
                jornada_de[ident].add(jornada)
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
    """`(inicio, etiqueta)` de la proxima ronda PRINCIPAL, con las
    rondas del calendario montadas una vez por huella. None si no
    hay. La misma que elige `los_factores`: el aplazado no cuenta."""
    try:
        from src.analysis.el_calendario_de_puntos import las_rondas

        rondas = _RONDAS.get(huella) if huella else None
        if rondas is None:
            rondas = []
            for r in las_rondas(calendario):
                if not isinstance(r, dict) or r.get("principal") is not True:
                    continue
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
    catalogo, ronda objetivo, clasificacion caducada): con la misma
    entrada, la misma respuesta sin recalcular. Nunca lanza.
    """
    try:
        momento = _momento(ahora if ahora is not None else _reloj())
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

        # La misma tabla deja de valer al cumplir la semana: eso
        # tambien va en la clave.
        vieja = caducada(clasificacion, momento)

        clave = (
            (huella_calendario, huella_clasificacion, huella_catalogo, ronda, vieja)
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
