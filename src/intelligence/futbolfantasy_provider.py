"""
FutbolFantasy: la fuente de titularidad y jerarquia. La unica.

POR QUE ESTE MODULO SUSTITUYE AL MULTIFUENTE

    El sistema de tres fuentes no funcionaba. Con cobertura 1 el
    consenso topaba todo en 74/26 y las etiquetas dejaban de
    significar nada: un 92 % de Jornada Perfecta y un 25 % de
    Analitica salian como "UNCERTAIN 58 %", que no es un acuerdo,
    es un promedio de dos cosas que no se pueden promediar.

    Se decide una sola fuente, sin consenso y sin topes.

POR QUE EL SCRAPER ANTERIOR VEIA TAN POCO

    Leia por la ventana lo que esta escrito en la puerta. Buscaba
    ventanas de texto alrededor de un "%" y sacaba 9 registros de
    12 paginas.

    Cada jugador de FF es un <div> con ~150 atributos data-*. El
    dato viene etiquetado en origen. Verificado contra el HTML
    real de tres equipos (78 jugadores): ver docs/ff-dom-contrato.md.

QUE HACE ESTE MODULO Y QUE NO

    Cubre PLANTILLA Y MERCADO. El anterior agrupaba por `roster`,
    asi que solo bajaba las paginas de los equipos donde tenemos
    jugadores y ningun candidato del mercado tenia pronostico. Esa
    es la causa directa del "0/20 CON PRONOSTICO DE TITULAR".

    No inventa. Un jugador que no empareja no sale en el tablero;
    no sale con un 50 % de relleno. Una jerarquia sin definir es
    None, no "Descarte".
"""

from __future__ import annotations

import json
import re
import unicodedata

from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import requests
from bs4 import BeautifulSoup


FF_BASE = "https://www.futbolfantasy.com"

BOARD_FILE = Path(
    "data/intelligence/futbolfantasy_board.json"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

TIMEOUT = 25

DEFAULT_TTL_SECONDS = 7200


# ----------------------------------------------------------------
# EQUIPOS
#
# `Atletico` es el fallo que dejaba un equipo de veinte invisible:
# el diccionario tenia "atletico madrid" y el catalogo de Biwenger
# lo llama "Atletico" a secas. Las claves van normalizadas (sin
# tildes, minusculas), asi que basta con cubrir las dos formas.
# ----------------------------------------------------------------

FF_TEAM_SLUGS = {
    "alaves": "alaves",
    "athletic": "athletic",
    "athletic bilbao": "athletic",
    "athletic club": "athletic",
    "atletico": "atletico",
    "atletico madrid": "atletico",
    "atletico de madrid": "atletico",
    "barcelona": "barcelona",
    "fc barcelona": "barcelona",
    "betis": "betis",
    "real betis": "betis",
    "celta": "celta",
    "celta vigo": "celta",
    "celta de vigo": "celta",
    "deportivo": "deportivo",
    "deportivo la coruna": "deportivo",
    "elche": "elche",
    "espanyol": "espanyol",
    "getafe": "getafe",
    "levante": "levante",
    "malaga": "malaga",
    "osasuna": "osasuna",
    "racing": "racing",
    "racing santander": "racing",
    # `rayo` a secas devuelve 404. La pagina buena es
    # rayo-vallecano, comprobado.
    "rayo": "rayo-vallecano",
    "rayo vallecano": "rayo-vallecano",
    "real madrid": "real-madrid",
    "real sociedad": "real-sociedad",
    "sevilla": "sevilla",
    "valencia": "valencia",
    "villarreal": "villarreal",
}


# ----------------------------------------------------------------
# JERARQUIA
#
# Ordinal y ya numerica en origen (`data-jerarquia`). No se
# normaliza a 0-100 aqui a proposito: que decida la escala quien
# la use para valorar. Lo que se publica es el dato de FF.
#
# El salto no es lineal -Revulsivo 25 y Rotacion 30 estan a cinco
# puntos, Rotacion e Importante a diez-, asi que tratarlo como una
# recta seria inventarse la distancia.
#
# El 0 NO es Descarte: es "sin definir", y en FF no lleva etiqueta.
# Se devuelve None. Ausencia de dato, no el escalon mas bajo.
# ----------------------------------------------------------------

HIERARCHY_LABELS = {
    60: "DIOS",
    50: "CLAVE",
    40: "IMPORTANTE",
    30: "ROTACION",
    25: "REVULSIVO",
    20: "RESERVA",
    10: "DESCARTE",
}

# En el vocabulario de esta casa, el escalon de arriba es el
# fichaje franquicia: el jugador por el que se rompe la caja.
# `franchise_funding_engine` ya razona sobre eso; que la jerarquia
# hable su idioma evita tener dos nombres para lo mismo.
FRANCHISE_TIER = 60


# ----------------------------------------------------------------
# ESTADO FISICO
#
# `data-estado` es compuesto, no una escala. Mapeo contado sobre
# los 464 jugadores de las 18 paginas:
#
#     0    sin icono                  disponible
#     30   disponible_box_min.png     tocado / vuelve de lesion
#     40   duda_box_min.png           duda
#     50   lesionado_box_min.png      lesionado
#     100  sin icono, sancionado=1    sancionado
#     130  lesionado_box_min.png      lesionado
#     150  lesionado_box_min.png      lesionado y sancionado=3
#     90   icono_big_nodisponible     no disponible
#
# Un codigo que no este aqui NO se traduce a la fuerza: se
# devuelve SIN_CLASIFICAR con el numero crudo al lado y se apunta
# en la metadata. Si FF añade un estado manana, queremos verlo,
# no que se disfrace de "disponible".
# ----------------------------------------------------------------

AVAILABILITY_LABELS = {
    0: "DISPONIBLE",
    30: "TOCADO",
    40: "DUDA",
    50: "LESIONADO",
    90: "NO_DISPONIBLE",
    100: "SANCIONADO",
    130: "LESIONADO",
    150: "LESIONADO",
}

# Con estos dos puede alinear. El resto, no.
AVAILABLE_CODES = (0, 30)


# Cuanto tiene que ganar el mejor candidato al segundo de su
# MISMO EQUIPO para dar la identidad por firme.
IDENTITY_MARGIN = 0.15

# Desde que desvio el valor que publica FF deja de parecer
# retraso de la fuente. No pone en duda la identidad: pone en
# duda el dato.
PRICE_GAP_ALERT = 15.0


# Los mismos cortes que usa el resto del sistema para votar.
# Repetidos aqui a proposito: si la pantalla o el guardarrail
# usasen otros, un jugador podria salir verde y contar como
# suplente en la decision.
STARTER_VOTE = 67.0
BENCH_VOTE = 40.0


# ----------------------------------------------------------------
# TEXTO
# ----------------------------------------------------------------


def normalize(value) -> str:

    value = str(value or "").strip().lower()

    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def team_slug(team_name: str) -> str | None:
    return FF_TEAM_SLUGS.get(normalize(team_name))


def vote_label(probability: float | None) -> str | None:

    if probability is None:
        return None

    if probability >= STARTER_VOTE:
        return "STARTER"

    if probability <= BENCH_VOTE:
        return "BENCH"

    return "UNCERTAIN"


def _int(value) -> int | None:

    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _percent(value) -> float | None:

    match = re.search(r"(\d{1,3})", str(value or ""))

    if not match:
        return None

    number = float(match.group(1))

    return number if 0 <= number <= 100 else None


# ----------------------------------------------------------------
# LOS JUGADORES DE BIWENGER QUE HAY QUE CUBRIR
# ----------------------------------------------------------------


def _catalog(snapshot: dict) -> dict:

    return (
        (snapshot or {})
        .get("catalog", {})
        .get("data", {})
        .get("players", {})
        or {}
    )


def _team_name(snapshot: dict, team_id) -> str | None:

    if team_id is None:
        return None

    teams = (
        (snapshot or {})
        .get("catalog", {})
        .get("data", {})
        .get("teams", {})
        or {}
    )

    return (teams.get(str(team_id)) or {}).get("name")


def _price(record: dict):

    for key in ("price", "value", "marketValue"):

        value = record.get(key)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

    return None


def build_targets(snapshot: dict) -> list[dict]:
    """
    Todo el que necesita pronostico: plantilla Y mercado.

    Aqui esta el arreglo del 1.2. El proveedor anterior recibia
    solo `roster`, asi que bajaba doce paginas -las de los equipos
    donde tenemos gente- y ningun candidato del mercado quedaba
    cubierto. La regla del once los bloqueaba a todos por falta de
    dato y el dashboard lo contaba como "no hay chollos".
    """

    catalogo = _catalog(snapshot)

    objetivos: dict[int, dict] = {}

    def anota(player_id, nombre, team_id, precio, scope):

        if player_id is None:
            return

        player_id = int(player_id)

        # La plantilla manda sobre el mercado: si un jugador
        # nuestro esta ademas listado, sigue siendo nuestro.
        if player_id in objetivos and objetivos[player_id]["scope"] == "ROSTER":
            return

        ficha = catalogo.get(str(player_id)) or {}

        nombre = nombre or ficha.get("name")

        if not nombre:
            return

        equipo = _team_name(snapshot, team_id or ficha.get("teamID"))

        # EL PRECIO QUE VALE AQUI ES EL DEL CATALOGO.
        #
        # `data-valor-biwenger` de FF es el valor del jugador. El
        # precio que pide un vendedor en el mercado es otra cosa
        # y casi nunca coincide. Emparejar con el precio de venta
        # tiraba la llave del valor a la basura para justo los
        # jugadores que mas falta hacen: los del mercado.
        objetivos[player_id] = {
            "id": player_id,
            "name": nombre,
            "slug": ficha.get("slug"),
            "team": equipo,
            "price": _price(ficha) if _price(ficha) is not None else precio,
            "asking_price": precio,
            "scope": scope,
        }

    for player in ((snapshot or {}).get("my_team") or []):

        if isinstance(player, dict):
            anota(
                player.get("id"),
                player.get("name"),
                player.get("teamID"),
                _price(player),
                "ROSTER",
            )

    ventas = (
        ((snapshot or {}).get("market") or {}).get("sales")
        or []
    )

    for venta in ventas:

        if not isinstance(venta, dict):
            continue

        jugador = venta.get("player") or {}

        anota(
            jugador.get("id"),
            jugador.get("name"),
            jugador.get("teamID"),
            _price(venta) if venta.get("price") is not None else None,
            "MARKET",
        )

    return list(objetivos.values())


# ----------------------------------------------------------------
# EL PARSER
# ----------------------------------------------------------------


def _is_player_row(tag) -> bool:

    clases = tag.get("class") or []

    if "tipo_lista" not in clases:
        return False

    return any(re.fullmatch(r"jugador_\d+", c) for c in clases)


def parse_team_page(html: str) -> dict:
    """
    Una pagina de equipo -> jugadores y datos del equipo.

    Las filas `tipo_lista` traen la PLANTILLA ENTERA, titulares y
    suplentes: 26 en el Alaves, 29 en el Athletic, 23 en el Barca.
    Las filas `tipo_campo` / `camiseta-wrapper` son el dibujo del
    campo, solo cubren el once y duplican jugadores. No se usan.
    """

    soup = BeautifulSoup(html, "html.parser")

    jugadores = []

    for fila in soup.find_all(_is_player_row):

        ff_id = None

        for clase in (fila.get("class") or []):
            if re.fullmatch(r"jugador_\d+", clase):
                ff_id = _int(clase.split("_", 1)[1])
                break

        nombre_el = fila.select_one(".nombre")

        jerarquia = _int(fila.get("data-jerarquia"))

        etiqueta_el = fila.select_one(".text-truncate.ml-2")

        estado = _int(fila.get("data-estado")) or 0

        jugadores.append(
            {
                "ff_id": ff_id,
                "ff_slug": fila.get("data-nombre"),
                "ff_name": (
                    nombre_el.get_text(strip=True)
                    if nombre_el
                    else None
                ),
                "probability": _percent(fila.get("data-probabilidad")),
                "hierarchy_value": jerarquia,
                "hierarchy_label": (
                    etiqueta_el.get_text(strip=True)
                    if etiqueta_el
                    else HIERARCHY_LABELS.get(jerarquia)
                ),
                "availability_code": estado,

                # `data-sancionado` no es un booleano: se han visto
                # 0, 1 y 3. Cualquier cosa distinta de 0 es una
                # sancion.
                "sanctioned": bool(_int(fila.get("data-sancionado")) or 0),

                "booked": bool(_int(fila.get("data-apercibido")) or 0),
                "situation": _int(fila.get("data-situacion")) or 0,
                "minutes": _int(fila.get("data-totalminutosjugados")),
                "form": fila.get("data-forma_value"),
                "ff_biwenger_value": _int(fila.get("data-valor-biwenger")),
                "ff_biwenger_diff": _int(fila.get("data-valor-diff-biwenger")),
                "next_rival": fila.get("data-rival"),
                "next_difficulty": _int(fila.get("data-rival_dif_index")),
                "next_away": "Fuera" in str(fila.get("data-locvis") or ""),
            }
        )

    return {
        "players": jugadores,
        "team": parse_team_meta(soup),
    }


def parse_team_meta(soup) -> dict:
    """
    Previsibilidad y rotaciones del equipo.

    Es la calibracion de confianza que hoy esta escrita a mano: un
    pronostico de un equipo "muy previsible" y otro de uno
    "imprevisible" no valen lo mismo, y hasta ahora valian igual.

    La barra da el numero; el texto, la etiqueta. Se guardan los
    dos porque el numero sirve para multiplicar y la etiqueta para
    enseñar.
    """

    entrenador = soup.select_one("strong.nombre-entrenador")

    resultado = {
        "coach": (
            entrenador.get_text(strip=True)
            if entrenador
            else None
        ),
        "rotation_percent": None,
        "rotation_label": None,

        # La previsibilidad de ESTA jornada: como de fiable es el
        # pronostico de hoy.
        "predictability_percent": None,
        "predictability_label": None,

        # La de la temporada: como de fiable ha sido este equipo
        # hasta ahora. Es la que sirve de multiplicador estable.
        "season_predictability_percent": None,
        "season_predictability_label": None,
    }

    for wrapper in soup.select("div.prevision-wrapper"):

        barra = wrapper.select_one("div.prevision")
        texto = wrapper.select_one("div.porcentaje")

        ancho = None

        if barra is not None:

            medida = re.search(
                r"width\s*:\s*([\d.]+)%",
                str(barra.get("style") or ""),
            )

            if medida:
                try:
                    ancho = round(float(medida.group(1)), 1)
                except ValueError:
                    ancho = None

        etiqueta = texto.get_text(strip=True) if texto else None

        # Cual de las dos barras es se lee del rotulo de su fila
        # ("Rotaciones" / "Previsib. J2"), no de la clase del
        # contenedor: el Barca sirve la de rotaciones sin
        # `one-container` y la heuristica de clases las cambiaba
        # de sitio en silencio.
        fila = wrapper.find_parent(
            lambda tag: tag.name == "div"
            and "row" in (tag.get("class") or [])
        )

        rotulo = ""

        if fila is not None:

            celda = fila.select_one("div[class*=col-5]")

            if celda is not None:
                rotulo = normalize(celda.get_text(strip=True))

        if rotulo.startswith("rotacion"):
            resultado["rotation_percent"] = ancho
            resultado["rotation_label"] = etiqueta

        elif rotulo.startswith("previsib temp"):
            resultado["season_predictability_percent"] = ancho
            resultado["season_predictability_label"] = etiqueta

        elif rotulo.startswith("previsib"):
            resultado["predictability_percent"] = ancho
            resultado["predictability_label"] = etiqueta

    return resultado


# ----------------------------------------------------------------
# IDENTIDAD
# ----------------------------------------------------------------


def _primary_aliases(target: dict) -> list[str]:
    """
    El nombre entero, tal cual lo escribe Biwenger. Nada de
    trozos: es el unico que sirve para decir "este nombre esta
    contenido en aquel".
    """

    aliases = []

    for value in (
        target.get("name"),
        str(target.get("slug") or "").replace("-", " "),
    ):

        texto = normalize(value)

        if texto and texto not in aliases:
            aliases.append(texto)

    return aliases


def _aliases(target: dict) -> list[str]:

    aliases = list(_primary_aliases(target))

    # "Jonny Castro" empareja con "castro" y con "jonny". Los
    # apellidos sueltos son la forma en que FF nombra a la mitad
    # de la liga.
    for alias in list(aliases):

        partes = alias.split()

        if len(partes) > 1:
            for parte in partes:
                if len(parte) >= 4 and parte not in aliases:
                    aliases.append(parte)

    return aliases


def _contains_name(largo: str, corto: str) -> bool:
    """
    ¿Esta el nombre corto dentro del largo, entero y en orden?

    FF escribe el nombre completo -"Kylian Mbappe", "Giovani Lo
    Celso"- y Biwenger el de camiseta -"Mbappe", "Lo Celso". El
    parecido de cadenas los da por distintos: "kylian mbappe"
    contra "mbappe" saca 0.63 y se queda muy por debajo de
    cualquier corte razonable.

    Por eso Mbappe, Lo Celso, Aleña, Xavi Grande, Urko Gonzalez y
    Brian Fariñas salian sin pronostico teniendo su ficha bajada.

    Se exige la secuencia COMPLETA y CONTIGUA de palabras, no un
    apellido suelto compartido: asi "Lo Celso" entra y dos
    "Garcia" distintos no se confunden.
    """

    if not largo or not corto:
        return False

    palabras_largo = largo.split()
    palabras_corto = corto.split()

    if not palabras_corto or len(palabras_corto) > len(palabras_largo):
        return False

    # Un solo token muy corto no basta para identificar a nadie.
    if len(palabras_corto) == 1 and len(palabras_corto[0]) < 4:
        return False

    for inicio in range(len(palabras_largo) - len(palabras_corto) + 1):

        if (
            palabras_largo[inicio: inicio + len(palabras_corto)]
            == palabras_corto
        ):
            return True

    return False


def _name_score(record: dict, target: dict) -> float:

    candidatos = [
        normalize(record.get("ff_name")),
        normalize(str(record.get("ff_slug") or "").replace("-", " ")),
    ]

    principales = _primary_aliases(target)

    mejor = 0.0

    for candidato in candidatos:

        if not candidato:
            continue

        for alias in _aliases(target):

            if candidato == alias:
                return 1.0

            # La contencion solo se prueba con el nombre ENTERO de
            # Biwenger, nunca con los trozos. Con trozos, el
            # "Andres" de Andres Castrin emparejaria con cualquier
            # Andres de la pagina: seria adivinar, no identificar.
            if alias in principales and (
                _contains_name(candidato, alias)
                or _contains_name(alias, candidato)
            ):
                mejor = max(mejor, 0.95)
                continue

            mejor = max(
                mejor,
                SequenceMatcher(None, candidato, alias).ratio(),
            )

    return mejor


def match_team(records: list[dict], targets: list[dict]) -> list[dict]:
    """
    Empareja los jugadores de una pagina con los de Biwenger.

    DOS LLAVES, NO UNA

        Hasta ahora la identidad se jugaba a parecido de nombre y
        punto: Jutgla entro con 0.86 y cualquiera por debajo del
        corte se perdia.

        FF publica el valor Biwenger de cada jugador
        (`data-valor-biwenger`). Con eso hay una segunda llave
        independiente: si el valor cuadra al euro, el nombre solo
        tiene que ser plausible. Y cuando dos jugadores del mismo
        equipo se parecen de nombre, el valor desempata.

    Se resuelve de mas seguro a menos, y cada jugador se asigna una
    sola vez.
    """

    libres = {target["id"]: target for target in targets}

    resultado = []

    def cerrar(record, target, metodo, score, margen):

        libres.pop(target["id"], None)

        resultado.append(
            {
                "record": record,
                "target": target,
                "method": metodo,
                "score": round(score, 3),

                # Distancia al segundo mejor candidato DEL MISMO
                # EQUIPO. Es lo que de verdad dice si la identidad
                # es solida: dentro de una plantilla de 25, un
                # nombre que gana por mucho no tiene con quien
                # confundirse.
                "margin": round(margen, 3),
            }
        )

    pendientes = list(records)

    # 1. Valor Biwenger exacto y nombre plausible.
    resto = []

    for record in pendientes:

        valor = record.get("ff_biwenger_value")

        elegido = None

        if valor:

            iguales = [
                target
                for target in libres.values()
                if target.get("price") == valor
            ]

            if len(iguales) == 1 and _name_score(record, iguales[0]) >= 0.45:
                elegido = iguales[0]

            elif len(iguales) > 1:

                puntuados = sorted(
                    (
                        (_name_score(record, target), target)
                        for target in iguales
                    ),
                    key=lambda par: par[0],
                    reverse=True,
                )

                if puntuados and puntuados[0][0] >= 0.7:
                    elegido = puntuados[0][1]

        if elegido is not None:
            cerrar(
                record,
                elegido,
                "VALUE_AND_NAME",
                _name_score(record, elegido),
                1.0,
            )
        else:
            resto.append(record)

    # 2. Nombre solo, y exigiendo mas.
    for record in resto:

        puntuados = sorted(
            (
                (_name_score(record, target), target)
                for target in libres.values()
            ),
            key=lambda par: par[0],
            reverse=True,
        )

        if not puntuados:
            continue

        score, target = puntuados[0]

        segundo = puntuados[1][0] if len(puntuados) > 1 else 0.0

        # Un empate entre dos nombres parecidos no se resuelve
        # tirando una moneda: se deja sin emparejar.
        if score >= 0.82 and score - segundo >= 0.04:
            cerrar(record, target, "NAME", score, score - segundo)

    return resultado


# ----------------------------------------------------------------
# EL TABLERO
# ----------------------------------------------------------------


def build_player_entry(match: dict, team_meta: dict, team_name: str) -> dict:

    record = match["record"]
    target = match["target"]

    probabilidad = record.get("probability")

    jerarquia = record.get("hierarchy_value")

    # 0 en FF es "sin definir", no Descarte.
    tiene_jerarquia = bool(jerarquia)

    estado = record.get("availability_code") or 0

    # ------------------------------------------------------
    # DOS DUDAS DISTINTAS, QUE NO HAY QUE MEZCLAR
    #
    # 1. ¿ES ESTE JUGADOR? Lo decide el EQUIPO y la distancia al
    #    segundo. El emparejamiento se hace dentro de una sola
    #    plantilla, asi que la pregunta no es "¿hay otro Javi
    #    Hernandez en la liga?" sino "¿hay otro en el Espanyol?".
    #    Si el mejor gana por mucho al segundo de su propio
    #    equipo, no tiene con quien confundirse.
    #
    # 2. ¿CUADRA EL VALOR? Es otra cosa. El valor Biwenger que
    #    publica FF va un dia por detras -desviacion mediana del
    #    0,65 %, percentil 90 del 3,7 % sobre 59 casos reales-,
    #    asi que un desvio grande dice que el DATO esta raro, no
    #    que el jugador este mal.
    #
    # Mezclarlas fue el error de la primera version: marcaba como
    # identidad dudosa a un jugador que era unico en su equipo,
    # solo porque su valor no cuadraba.
    # ------------------------------------------------------

    precio_biwenger = target.get("price")
    valor_ff = record.get("ff_biwenger_value")

    desvio = None

    if precio_biwenger and valor_ff:
        desvio = round(
            (valor_ff - precio_biwenger) / precio_biwenger * 100,
            1,
        )

    margen = match.get("margin")

    if (
        match["method"] == "VALUE_AND_NAME"
        or match["score"] >= 1.0
        or (margen is not None and margen >= IDENTITY_MARGIN)
    ):
        confianza = "ALTA"

    elif margen is not None and margen >= 0.04:
        confianza = "MEDIA"

    else:
        confianza = "BAJA"

    return {
        "player_id": target["id"],
        "player_name": target["name"],
        "team": team_name,
        "scope": target["scope"],

        "starter_probability": probabilidad,
        "consensus": vote_label(probabilidad),
        "source": "FUTBOLFANTASY",
        "source_coverage": 1,

        "hierarchy": (
            {
                "value": jerarquia,
                "label": (
                    record.get("hierarchy_label")
                    or HIERARCHY_LABELS.get(jerarquia)
                ),
                "franchise": jerarquia >= FRANCHISE_TIER,
            }
            if tiene_jerarquia
            else None
        ),

        "availability": {
            "code": estado,
            "label": AVAILABILITY_LABELS.get(estado, "SIN_CLASIFICAR"),
            "can_play": estado in AVAILABLE_CODES,
            "sanctioned": record.get("sanctioned"),
            "booked": record.get("booked"),
        },

        "market_flags": {
            "transferible": record.get("situation") in (2, 3),
            "cedible": record.get("situation") == 3,
        },

        "minutes": record.get("minutes"),
        "form": record.get("form"),

        "next_match": {
            "rival": record.get("next_rival"),
            "difficulty": record.get("next_difficulty"),
            "away": record.get("next_away"),
        },

        "team_context": {
            "coach": team_meta.get("coach"),
            "predictability": team_meta.get("predictability_percent"),
            "predictability_label": team_meta.get("predictability_label"),
            "season_predictability": team_meta.get(
                "season_predictability_percent"
            ),
            "rotation": team_meta.get("rotation_percent"),
            "rotation_label": team_meta.get("rotation_label"),
        },

        "ff": {
            "id": record.get("ff_id"),
            "slug": record.get("ff_slug"),
            "biwenger_value": record.get("ff_biwenger_value"),
            "biwenger_diff": record.get("ff_biwenger_diff"),
        },

        "match": {
            "method": match["method"],
            "score": match["score"],
            "margin": margen,
            "price_gap_percent": desvio,
            "confidence": confianza,
        },
    }


def fetch(session, url: str) -> str:

    response = session.get(url, headers=HEADERS, timeout=TIMEOUT)

    response.raise_for_status()

    return response.text


def load_absences(session, matchday: int) -> tuple[dict, dict]:
    """
    Lesionados y sancionados de toda la liga, en dos peticiones.

    Blindado: si estas paginas fallan, el tablero se construye
    igual y se dice que no hay partes. Es informacion que mejora
    la valoracion, no un requisito para valorar.
    """

    from src.intelligence import futbolfantasy_absences as bajas

    meta = {
        "injuries": 0,
        "suspensions": 0,
        "errors": [],
    }

    try:
        calendario = json.loads(
            bajas.CALENDAR_FILE.read_text(encoding="utf-8")
        )
    except Exception as error:
        meta["errors"].append(f"calendario: {error}")
        calendario = {}

    fechas = bajas.matchday_dates(calendario)

    ahora = datetime.now(timezone.utc)

    lesionados = {}
    sancionados = {}

    try:
        lesionados = bajas.parse_injuries(
            fetch(session, bajas.INJURIES_URL),
            current_matchday=matchday,
            fechas=fechas,
            today=ahora,
        )
        meta["injuries"] = len(lesionados)

    except Exception as error:
        meta["errors"].append(
            f"lesionados: {type(error).__name__}: {error}"
        )

    try:
        sancionados = bajas.parse_suspensions(
            fetch(session, bajas.SUSPENSIONS_URL)
        )
        meta["suspensions"] = len(sancionados)

    except Exception as error:
        meta["errors"].append(
            f"sancionados: {type(error).__name__}: {error}"
        )

    return (
        bajas.merge_absences(lesionados, sancionados),
        meta,
    )


def load_board(path: Path | None = None) -> dict | None:

    path = path or BOARD_FILE

    if not path.exists():
        return None

    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None

    return value if isinstance(value, dict) else None


def board_age_seconds(board: dict, now: datetime | None = None) -> float | None:

    updated = (board or {}).get("updated_at")

    if not updated:
        return None

    try:
        stamp = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
    except ValueError:
        return None

    return (
        (now or datetime.now(timezone.utc)) - stamp
    ).total_seconds()


def refresh_board(
    snapshot: dict,
    matchday: int,
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    force: bool = False,
    session=None,
) -> dict:
    """
    Baja FF para todos los equipos que hacen falta y escribe el
    tablero.

    SIN OBJETIVOS NO SE ESCRIBE NADA

        Un snapshot sin plantilla ni mercado es un snapshot roto,
        no una liga vacia. Se dice, se conserva el tablero anterior
        y no se pisa el disco. El fallo contrario -guardar un
        tablero de cero jugadores con error: null y servirlo
        despues como cache valida- ya paso una vez.
    """

    cache = load_board()

    objetivos = build_targets(snapshot)

    # ------------------------------------------------------
    # LA CACHE TIENE QUE COMPROBAR A QUIEN CUBRE
    #
    # El primer ciclo real -17/08/2026, 20:25- lo destapo: el
    # tablero de las 17:06 tenia hora y media, la jornada correcta
    # y 59 jugadores, asi que se sirvio como valido. Pero EL
    # MERCADO DE BIWENGER ROTA: de los 48 candidatos de ese
    # momento, 19 no estaban en el tablero. Lunin, Tenaglia,
    # Mendy... ninguno tenia pronostico, y la cabecera cayo de
    # 18/20 a 8/20 sin que nada fallase.
    #
    # Mirar la edad y la jornada no basta. Hay que mirar si cubre
    # a los jugadores de HOY.
    #
    # Y cuando no los cubre no se tira todo: se completa solo con
    # los equipos de los que faltan. Refrescar entero cada media
    # hora serian 22 paginas cada vez; asi suelen ser dos o tres.
    # ------------------------------------------------------

    cacheados: dict[int, dict] = {}

    completando = False

    if not force and cache:

        edad = board_age_seconds(cache)

        if (
            edad is not None
            and edad < ttl_seconds
            and cache.get("matchday") == matchday
            and (cache.get("players") or [])
        ):

            cacheados = {
                p["player_id"]: p
                for p in cache["players"]
                if p.get("player_id") is not None
            }

            pendientes = [
                objetivo
                for objetivo in objetivos
                if objetivo["id"] not in cacheados
            ]

            if not pendientes and objetivos:

                salida = dict(cache)
                salida["cache"] = {
                    "status": "HIT",
                    "age_seconds": round(edad, 1),
                    "ttl_seconds": ttl_seconds,
                    "error": None,
                }
                return salida

            if pendientes:
                completando = True
                objetivos_a_bajar = pendientes

    if not completando:
        cacheados = {}
        objetivos_a_bajar = objetivos

    if not objetivos:

        motivo = (
            "El snapshot llego sin plantilla ni mercado: no se "
            "construye tablero de titularidad y no se sobrescribe "
            "el anterior."
        )

        if cache and (cache.get("players") or []):
            salida = dict(cache)
            salida["cache"] = {
                "status": "STALE_FALLBACK",
                "age_seconds": board_age_seconds(cache),
                "ttl_seconds": ttl_seconds,
                "error": motivo,
            }
            return salida

        return {
            "version": "V12.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "matchday": matchday,
            "metadata": {},
            "players": [],
            "cache": {
                "status": "NO_TARGETS",
                "age_seconds": None,
                "ttl_seconds": ttl_seconds,
                "error": motivo,
            },
        }

    por_equipo: dict[str, list[dict]] = {}

    sin_equipo = []

    for objetivo in objetivos_a_bajar:

        if not objetivo.get("team"):
            sin_equipo.append(objetivo["name"])
            continue

        por_equipo.setdefault(objetivo["team"], []).append(objetivo)

    session = session or requests.Session()

    # Los partes de baja, una vez para toda la liga. Se cruzan por
    # slug de FF, que es exacto: misma fuente, misma clave.
    ausencias, ausencias_meta = load_absences(
        session,
        matchday,
    )

    jugadores = []
    equipos_meta = {}
    errores = []
    sin_slug = []
    paginas = 0
    metodos: dict[str, int] = {}

    for team_name, targets in sorted(por_equipo.items()):

        slug = team_slug(team_name)

        if not slug:
            sin_slug.append(team_name)
            continue

        url = f"{FF_BASE}/laliga/equipos/{slug}"

        try:
            html = fetch(session, url)
        except Exception as error:
            errores.append(
                f"{team_name}: {type(error).__name__}: {error}"
            )
            continue

        paginas += 1

        try:
            pagina = parse_team_page(html)
        except Exception as error:
            errores.append(
                f"{team_name}: parser: {type(error).__name__}: {error}"
            )
            continue

        equipos_meta[team_name] = pagina["team"]

        for match in match_team(pagina["players"], targets):

            metodos[match["method"]] = metodos.get(match["method"], 0) + 1

            entrada = build_player_entry(
                match,
                pagina["team"],
                team_name,
            )

            parte = ausencias.get(
                (entrada.get("ff") or {}).get("slug")
            )

            if parte:
                entrada["absence"] = parte

            jugadores.append(entrada)

    # Si el scrapeo entero se fue al garete, no se pisa lo que
    # habia: un tablero vacio recien escrito es peor que uno viejo,
    # porque parece dato.
    if not jugadores and cache and (cache.get("players") or []):

        salida = dict(cache)
        salida["cache"] = {
            "status": "STALE_FALLBACK",
            "age_seconds": board_age_seconds(cache),
            "ttl_seconds": ttl_seconds,
            "error": (
                "FutbolFantasy no devolvio ni un jugador emparejado."
            ),
        }
        return salida

    # Al completar, lo bajado ahora se suma a lo que ya habia. Se
    # conserva solo a quien sigue siendo objetivo: un jugador que
    # ya no esta en el mercado no tiene por que seguir ocupando
    # sitio en el tablero.
    if completando:

        vigentes = {objetivo["id"] for objetivo in objetivos}

        nuevos = {entry["player_id"] for entry in jugadores}

        jugadores = [
            entry
            for player_id, entry in cacheados.items()
            if player_id in vigentes and player_id not in nuevos
        ] + jugadores

    cubiertos = {entry["player_id"] for entry in jugadores}

    salida = {
        "version": "V12.0",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "matchday": matchday,

        "metadata": {
            "targets": len(objetivos),
            "targets_roster": sum(
                1 for o in objetivos if o["scope"] == "ROSTER"
            ),
            "targets_market": sum(
                1 for o in objetivos if o["scope"] == "MARKET"
            ),
            "matched": len(jugadores),
            "matched_roster": sum(
                1 for p in jugadores if p["scope"] == "ROSTER"
            ),
            "matched_market": sum(
                1 for p in jugadores if p["scope"] == "MARKET"
            ),
            "team_pages": paginas,
            "teams_requested": len(por_equipo),

            "absences": {
                **ausencias_meta,
                "matched": sum(
                    1 for p in jugadores if p.get("absence")
                ),
                "long_term": sum(
                    1
                    for p in jugadores
                    if (p.get("absence") or {}).get("matchdays_out")
                    and p["absence"]["matchdays_out"] >= 4
                ),
            },

            "methods": metodos,

            # DUDA DE IDENTIDAD: el nombre no gana con claridad a
            # otro del mismo equipo.
            "low_confidence": [
                {
                    "player": entry["player_name"],
                    "team": entry["team"],
                    "ff_slug": (entry.get("ff") or {}).get("slug"),
                    "score": (entry.get("match") or {}).get("score"),
                    "margin": (entry.get("match") or {}).get("margin"),
                }
                for entry in jugadores
                if (entry.get("match") or {}).get("confidence", "ALTA")
                != "ALTA"
            ],

            # DUDA DEL DATO: la identidad esta clara pero el valor
            # que publica FF no cuadra con el catalogo. Util para
            # no fiarse de `biwenger_value` en ese jugador; la
            # titularidad y la jerarquia siguen valiendo.
            "price_gaps": [
                {
                    "player": entry["player_name"],
                    "team": entry["team"],
                    "price_gap_percent": (
                        (entry.get("match") or {}).get(
                            "price_gap_percent"
                        )
                    ),
                }
                for entry in jugadores
                if (entry.get("match") or {}).get("price_gap_percent")
                is not None
                and abs(entry["match"]["price_gap_percent"])
                > PRICE_GAP_ALERT
            ],

            "no_slug": sorted(set(sin_slug)),
            "no_team": sorted(set(sin_equipo)),
            "unmatched": sorted(
                objetivo["name"]
                for objetivo in objetivos
                if objetivo["id"] not in cubiertos
            ),

            # Estados que FF ha servido y este modulo no sabe
            # traducir. Vacio es lo normal; si aparece algo, FF ha
            # cambiado y hay que mirarlo.
            "unknown_availability_codes": sorted(
                {
                    entry["availability"]["code"]
                    for entry in jugadores
                    if entry["availability"]["label"] == "SIN_CLASIFICAR"
                }
            ),

            "errors": errores,
        },

        "teams": equipos_meta,
        "players": jugadores,

        "cache": {
            "status": "TOPPED_UP" if completando else "REFRESHED",
            "age_seconds": 0.0,
            "ttl_seconds": ttl_seconds,
            "error": None,
        },
    }

    BOARD_FILE.parent.mkdir(parents=True, exist_ok=True)

    BOARD_FILE.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return salida
