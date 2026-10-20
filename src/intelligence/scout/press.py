"""
El ojeador de prensa: lo unico que no copia el precio de
Biwenger.

POR QUE ESTA PIEZA Y NO OTRA

    Las cuatro fuentes que ya lee Pepe son webs de mercado, y el
    06/09/2026 se midio lo que valen juntas:

        cero discrepancias de direccion en 288 jugadores,
        cifras identicas al tercer decimal

    Son la MISMA medida repetida tres veces. Su acuerdo es
    redundancia, no corroboracion: dicen que hemos leido bien el
    precio de Biwenger, que ya teniamos.

    La prensa es otra cosa. Un entrenador que anuncia rotaciones,
    un parte medico, un tocado en el calentamiento: eso todavia
    no esta en ningun precio, y ahi es donde hay ventaja.

LO QUE SE MIDIO AL ABRIR LOS CANALES (05/09/2026, 17:50)

        MARCA             48 items   ultima: hoy 17:46      VALE
        MUNDO DEPORTIVO  100 items   ultima: hoy 17:30      VALE
        RELEVO            15 items   ultima: ayer 08:04     VALE
        SPORT             49 items   ultima: hoy 17:37      (no pedido)

        AS                68 items   ultima: 16/11/2022     MUERTO

    AS responde 200, trae 68 noticias bien formadas y su ultima
    entrada es de hace CUATRO AÑOS. Es el caso mas peligroso de
    todos: una fuente que parece viva. Tiene su modulo, apagado a
    proposito, con la fecha dentro.

    De 163 titulares de las tres que valen, 68 mencionan a un
    activo de Biwenger. Ese es el rendimiento real.

LO QUE ES DATO Y LO QUE ES DEDUCCION

    Se separan a proposito y viajan marcados:

        DATO       el titular, la frase, el enlace y la fecha.
                   Es lo que publico el medio, literal.
        DEDUCCION  `kind` y `direction`. Los pone este fichero
                   con reglas de palabras clave, y por eso cada
                   señal lleva `deduced: True` y la frase exacta
                   que la disparo.

    El encargo lo dice sin rodeos: "Nada de prediccion. La prensa
    informa de hechos y declaraciones. Si el modelo deduce algo,
    que quede marcado como deduccion y no como dato."

LA CONFIANZA NO SE INVENTA

    Ningun periodico publica un porcentaje de fiabilidad. Asi que
    `confidence` va a `None` con su motivo al lado, igual que se
    hizo con las webs de precio. Una confianza inventada seria
    peor que ninguna: parece medida.

EL EMPAREJAMIENTO NO ADIVINA

    Un titular no trae un `player_id`. Se busca al reves: cada
    nombre del catalogo de Biwenger se busca dentro del texto,
    con tres candados.

        1. Cuatro letras minimo. "Oso" y "Sow" existen en el
           catalogo y aparecerian en cualquier frase.
        2. En mayuscula en el texto original. Asi "cabello" es
           pelo y "Cabello" es el jugador. Son dos de los 569
           nombres que ademas son palabra corriente en
           castellano; el otro es "Molina".
        3. Nombre unico en el catalogo. Solo hay uno repetido
           -Moussa Diarra, dos fichas- y con ese no se adivina:
           va a `unmatched`.

    Lo que no pasa los tres candados no entra. Nunca se elige "el
    mas probable".

    Y el catalogo trae ENTRENADORES (`position` 5): Simeone,
    Pellegrini, Corberan, Bordalas. En Biwenger se fichan, asi
    que una noticia sobre un entrenador es una noticia sobre un
    activo y entra igual.

DOS VECES AL DIA

    Las noticias no cambian cada quince minutos y el ciclo dura
    dos. TTL de doce horas, con la misma mecanica que el informe
    de mercado: si lo de disco vale, no se sale a la calle.

ESTO NO DECIDE NADA

    Se publica AL LADO de lo que decide Pepe. No hay ni un
    importador de este modulo en ninguna ruta de decision, y hay
    guardia que lo comprueba con `ast`.
"""

from __future__ import annotations

import html
import re
import unicodedata

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from src.intelligence.scout.common import (
    DO_NOT_RETRY,
    HEADERS,
    TIMEOUT_SECONDS,
    now_iso,
    source_result,
)

from src.intelligence.scout.matching import build_targets


VERSION = "V1.0"

SOURCE = "PRENSA"

REPORT_FILE = Path("data") / "intelligence" / "press_report.json"


# Doce horas: dos pasadas al dia, como pide el encargo.
DEFAULT_TTL_SECONDS = 12 * 3600


# Una noticia de hace tres dias ya no mueve un precio de hoy.
MAX_ITEM_AGE_HOURS = 72


# ============================================================
# LOS CANALES
# ============================================================
#
#     `enabled: False` no es un fallo: es una fuente que se ha
#     mirado y se ha decidido no usar, con el motivo dentro. El
#     mismo patron que `jornada_perfecta_market.py`.

FEEDS = {
    "MARCA": {
        "url": (
            "https://e00-marca.uecdn.es/rss/futbol/"
            "primera-division.xml"
        ),
        "enabled": True,
        "note": "Primera Division. 48 titulares, al dia.",
    },
    "MUNDO_DEPORTIVO": {
        "url": "https://www.mundodeportivo.com/feed/rss/futbol/",
        "enabled": True,
        "note": "Futbol general. 100 titulares, al dia.",
    },
    "RELEVO": {
        "url": "https://www.relevo.com/rss/",
        "enabled": True,
        "note": (
            "Portada. 15 titulares, menos volumen y mas reportaje."
        ),
    },
    "AS": {
        "url": "https://as.com/rss/futbol/primera.xml",
        "enabled": False,
        "note": (
            "APAGADO A PROPOSITO. Responde 200 y trae 68 noticias "
            "bien formadas, y la mas reciente es del 16/11/2022: "
            "el canal lleva cuatro años sin actualizarse. Se probo "
            "tambien /rss/portada.xml y "
            "/rss/tags/competiciones/primera_division.xml, los dos "
            "404. Leerlo seria meter titulares de hace cuatro años "
            "como si fueran de hoy."
        ),
    },
}


# ============================================================
# LAS REGLAS DE DEDUCCION
# ============================================================
#
#     Orden a proposito: lo que quita puntos manda sobre lo que
#     los explica. Una noticia que dice "baja" y "once" en la
#     misma frase importa por la baja.
#
#     "Tocado" se quedo FUERA. En castellano futbolistico
#     significa las dos cosas y se vio en vivo:
#
#         "Funes: no podemos amedrentarnos porque nos hayan
#          TOCADO el Atletico y el Real Madrid"
#
#     Eso no es un jugador tocado, es un sorteo. Una palabra que
#     falla en el primer titular que la contiene no entra.

BAJA = "BAJA"
DUDA = "DUDA"
VUELVE = "VUELVE"
ALINEACION = "ALINEACION"
FICHAJE = "FICHAJE"
MENCION = "MENCION"

UP = "UP"
DOWN = "DOWN"
FLAT = "FLAT"


REGLAS = (
    (
        BAJA,
        DOWN,
        r"\b(baja|bajas|lesion|lesionado|lesionada|lesionarse"
        r"|se pierde|sancion|sancionado|expulsad\w*|rotura"
        r"|operad\w*|parte medico|no estara|causa baja"
        r"|se rompe|fuera .{0,20}semanas)\b",
    ),
    (
        DUDA,
        DOWN,
        r"\b(duda|dudas|molestias|en el aire|no se entren\w*"
        r"|entrena al margen|entrenamiento al margen"
        r"|pendiente de(?: la)? evolucion|prueba de esfuerzo)\b",
    ),
    (
        VUELVE,
        UP,
        r"\b(vuelve|regresa|reaparece|alta medica|recuperad\w*"
        r"|ya entrena|vuelve a entrenar|se reincorpora)\b",
    ),
    (
        ALINEACION,
        FLAT,
        r"\b(once|onces|alineacion|alineaciones|convocatoria"
        r"|convocad\w*|titular|titulares|titularidad|rotacion"
        r"|rotaciones|descansar\w*|suplente|suplentes"
        r"|lista de)\b",
    ),
    (
        FICHAJE,
        FLAT,
        r"\b(fichaje|fichar|fichado|traspaso|cesion|cedido"
        r"|renueva|renovacion|oferta por|interes en|se marcha"
        r"|adios a|salida de)\b",
    ),
)


# Cuatro letras. Por debajo hay nombres del catalogo -"Oso",
# "Sow"- que salen en cualquier frase.
MIN_NAME_LENGTH = 4


# ============================================================
# LA BAJA ES DE QUIEN LA TIENE MAS CERCA (19/10/2026)
# ============================================================
#
#     El caso real, el que le costo 1,0 xP a Yamal en el informe
#     de la mañana -su PRENSA_BAJA- (laboratorio del 19/10):
#
#         "Nuno Mendes , su antidoto para frenar a un Lamine
#          Yamal en un momento de juego magnifico, esta lesionado
#          y Digne, su alternativa natural, ..."
#
#     El lesionado es Nuno Mendes, del PSG. Ni el ni Digne estan
#     en el catalogo de Biwenger, asi que la frase tenia UN solo
#     activo y el candado de los dos sujetos no salto: la regla
#     vio "lesionado" y se lo colgo al unico que conocia.
#
#     Ahora una palabra de BAJA o de DUDA solo cuenta para el
#     jugador si ningun OTRO nombre propio de la frase -del
#     catalogo o no- esta mas cerca de ella, en palabras. A
#     igualdad, cuenta: el empate no es "otro mas cerca". Basta
#     con que UNA de las palabras de la regla sea suya ("bajas
#     sensibles, siendo la de Aubameyang la mas dura al tener que
#     ser operado": "operado" es suya). Si no cuenta, se sigue con
#     las reglas de abajo, pero SOLO con las que no suben
#     (ALINEACION, FICHAJE) o MENCION: una baja apartada nunca se
#     da la vuelta en VUELVE/UP. Se vio: "Arda Güler regresa de
#     Turquia con molestias" era DUDA y, con "Turquia" mas cerca de
#     "molestias", salia VUELVE; el "regresa" va pegado al sujeto y
#     la proximidad no lo aparta. "Canales regresa y el central
#     cubre la baja de Vivian", con Vivian fuera del catalogo, queda
#     en MENCION: ni resta ni suma. Yamal: "lesionado" esta a una
#     palabra de Digne y a siete de el; se queda en ALINEACION por
#     "suplentes", que es FLAT y no resta. El item lo dice en
#     `keyword_reason`.
#
#     QUE ES UN NOMBRE PROPIO AQUI. Palabras en mayuscula
#     seguidas ("Nuno Mendes", "Frenkie de Jong"), sin los
#     equipos -los del catalogo y los de `NO_SON_PERSONAS`-, ni
#     las palabras que van en mayuscula por ir al principio
#     ("Alarma con la lesion de Guruzeta": "Alarma" no es nadie).
#     Salvo que la primera palabra, sola, tenga pinta de sujeto: una
#     coma detras ("Dembele, lesionado, no podra medirse a Yamal") o
#     un verbo (es, se, sera, esta, sufre) o una palabra de las
#     reglas justo despues. Si ella misma es una palabra de las
#     reglas ("Lesionado, Pedri se pierde..."), no.
#     Medido sobre las 75 BAJA/DUDA de la prensa de los artefactos
#     del 13 y el 19/10, con el catalogo de ese dia: cambian 9. Ocho
#     eran de otro (Yamal; Redondo, por la baja de Vicky Lopez; la
#     sancion de Vinicius, colgada a Mourinho y a Saliba; el
#     expulsado Marin, a Nsongo; Morata, a Cordoba; la baja de
#     Yangel, a Matarazzo; las de Zaka y Casado, a Hidalgo) y
#     Raphinha pasa de BAJA a DUDA: "lesionado" era de Frenkie de
#     Jong y sus "molestias" si son suyas. Ninguna de las otras 66
#     cambia. Siguen mal las que no tienen otro nombre cerca ("sin
#     duda", "el jugador estara tres meses de baja, como señalo
#     ... Luis Garcia Plaza"). Con lo que se añadio esa noche (la
#     lista de abajo, la primera palabra con pinta de sujeto, nada de
#     VUELVE tras una baja apartada), sobre las 21 BAJA/DUDA de un
#     solo sujeto de los informes de prensa del 12 al 18/10 que se
#     conservan, cambian las mismas dos de antes (Morata, Raphinha).
#
#     LO QUE NO ARREGLA, dicho claro. Es proximidad, no
#     gramatica: sin "y Digne" detras, Yamal quedaria mas cerca
#     de "lesionado" que Nuno Mendes y seguiria siendo BAJA. Y una
#     palabra en mayuscula que no es una persona -un estadio, una
#     ciudad que no esta en la lista- cuenta como "otro nombre":
#     si esta mas cerca, la baja verdadera se pierde (queda en
#     MENCION o en lo FLAT de la frase; nunca en VUELVE). Por eso la
#     lista de abajo existe y por eso solo se aplica a BAJA y DUDA,
#     las dos que restan puntos. Y el empate es del sujeto: "Hakimi
#     es baja y Yamal tendra via libre" sigue siendo BAJA de Yamal
#     ("baja" esta a una palabra de cada uno).

PROXIMIDAD = (BAJA, DUDA)


# Lo que va en mayuscula sin ser un nombre: articulos y palabras
# que abren frase, y el "Leer" que Mundo Deportivo pega al final
# de cada entradilla. Se quitan de las puntas de cada nombre.
NO_ABREN_NOMBRE = frozenset({
    "el", "la", "los", "las", "lo", "un", "una", "unos", "unas",
    "al", "del", "de", "y", "e", "o", "u", "a", "en", "con", "sin",
    "por", "para", "ante", "tras", "segun", "desde", "hasta", "sobre",
    "entre", "contra", "hacia", "pero", "aunque", "si", "no", "que",
    "como", "cuando", "donde", "quien", "cual", "ya", "asi", "solo",
    "tambien", "mas", "este", "esta", "estos", "estas", "ese", "esa",
    "esos", "esas", "aquel", "su", "sus", "mi", "otro", "otra", "hoy",
    "ayer", "manana", "leer", "ver", "video", "directo", "oficial",
    "ultima", "hora", "jornada",
})


# Lo que une dos trozos de un mismo nombre: "Frenkie de Jong",
# "Luis de la Fuente", "Marc-Andre ter Stegen".
UNEN_NOMBRE = frozenset({
    "de", "del", "la", "las", "los", "da", "das", "do", "dos", "van",
    "von", "der", "den", "di", "du", "ter", "le",
})


# Nombres propios que no son personas y salen en los titulares:
# clubes de LaLiga (por si el catalogo llega sin equipos) y de
# fuera, selecciones, competiciones, estadios y ciudades. Sin
# acentos y en minuscula, palabra a palabra: un nombre cuyas
# palabras estan TODAS aqui (o en los equipos del catalogo) no es
# una persona. No pretende ser completa: es lo visto en los
# titulares de octubre.
NO_SON_PERSONAS = frozenset({
    # LaLiga
    "alaves", "athletic", "atletico", "atleti", "barcelona", "barca",
    "betis", "celta", "elche", "espanyol", "getafe", "girona",
    "levante", "mallorca", "osasuna", "oviedo", "rayo", "vallecano",
    "real", "madrid", "sociedad", "sevilla", "valencia", "villarreal",
    "racing", "deportivo", "malaga", "leganes", "cordoba", "sanse",
    "submarino", "amarillo", "rojiblanco", "rojillos", "leones",
    "club", "fc", "cf", "ud", "cd", "sd", "rcd", "rc", "ca", "sad",
    # Fuera
    "psg", "paris", "napoles", "galatasaray", "manchester", "united",
    "city", "bournemouth", "estrasburgo", "roma", "lazio", "juventus",
    "milan", "inter", "bayern", "dortmund", "liverpool", "chelsea",
    "arsenal", "tottenham", "benfica", "oporto", "porto", "sporting",
    "ajax", "psv", "brujas", "leverkusen", "monaco", "marsella",
    "lyon", "napoli", "atalanta", "newcastle", "aston", "villa",
    # Champions y Europa League de octubre (19/10/2026): "Militao,
    # que se retiro con molestias ante el Olympiacos, es duda".
    "olympiacos", "olympiakos", "olympique", "copenhague", "celtic",
    "rangers", "salzburgo", "shakhtar", "dinamo", "zagreb", "slavia",
    "sparta", "praga", "qarabag", "bodo", "glimt", "union", "gilloise",
    "eintracht", "frankfurt", "leipzig", "stuttgart", "feyenoord",
    "pafos", "kairat", "almaty", "fenerbahce",
    # Selecciones y paises
    "espana", "seleccion", "roja", "sub", "brasil", "argentina",
    "francia", "italia", "alemania", "inglaterra", "portugal",
    "belgica", "holanda", "paises", "bajos", "croacia", "marruecos",
    "uruguay", "colombia", "mexico", "estados", "unidos", "guinea",
    "bisau", "nigeria", "albania", "indonesia", "suiza", "suecia",
    "noruega", "dinamarca", "japon", "senegal", "ghana", "camerun",
    # Los rivales de las ventanas de selecciones (19/10/2026): "Arda
    # Güler regresa de Turquia con molestias".
    "turquia", "georgia", "ecuador", "bulgaria", "serbia", "grecia",
    "escocia", "gales", "irlanda", "austria", "hungria", "polonia",
    "chequia", "eslovaquia", "eslovenia", "rumania", "ucrania",
    "kosovo", "islandia", "finlandia", "chipre", "peru", "chile",
    "paraguay", "venezuela", "bolivia", "canada", "egipto", "argelia",
    "tunez", "corea", "australia", "qatar",
    # Partidos con nombre: "Kubo, con un esguince, es duda para el
    # Clasico" (19/10/2026)
    "clasico", "derbi",
    # Competiciones y organismos
    "laliga", "liga", "ea", "sports", "hypermotion", "primera",
    "segunda", "division", "champions", "league", "europa",
    "conference", "copa", "rey", "supercopa", "mundial", "eurocopa",
    "uefa", "fifa", "rfef", "csd", "var", "comite", "competicion",
    "disciplina", "federacion", "apelacion", "tad",
    # Estadios y ciudades
    "bernabeu", "santiago", "metropolitano", "camp", "nou",
    "montjuic", "mestalla", "anoeta", "reale", "arena", "cartuja",
    "sadar", "vallecas", "lezama", "balaidos", "riazor", "abanca",
    "ciutat", "estadio", "stadium", "rcde", "coliseum", "ipurua",
    "mendizorroza", "ceramica", "pizjuan", "villamarin", "zorrilla",
    "tartiere", "sardinero", "rosaleda", "vitoria", "donostia",
    "bilbao", "vigo", "coruna", "pamplona", "estambul", "ali", "sami",
    "yen", "londres", "munich",
    # Estadios y ciudades deportivas que faltaban (19/10/2026):
    # "Sancet se lesiona en San Mames y sera baja". Con "san" y
    # "son" no se pierde a nadie con apellido: un nombre sale solo si
    # TODAS sus palabras estan aqui ("San Mames" y "Son Moix" si;
    # "Heung-min Son", no).
    "san", "mames", "son", "moix", "montilivi", "valdebebas",
    "zubieta", "paterna", "butarque", "lasesarre", "majadahonda",
    "rozas", "clairefontaine",
    # Medios y programas
    "marca", "sport", "relevo", "mundo", "cope", "ser", "onda", "cero",
    "partidazo", "chiringuito", "movistar", "dazn",
})


CONFIDENCE_BASIS = (
    "Ningun periodico publica una fiabilidad. La direccion es una "
    "deduccion nuestra a partir de la frase citada, no un dato "
    "del medio."
)


# ============================================================
# UTILIDADES
# ============================================================


def plano(texto: str) -> str:
    """Minusculas y sin acentos, para buscar."""

    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )


def limpiar(bruto: str) -> str:
    """
    Un campo de RSS, convertido en texto legible.

    Los medios meten CDATA, HTML, entidades y hasta un pixel de
    seguimiento dentro del `description`. La cita tiene que poder
    leerla una persona.
    """

    texto = re.sub(
        r"<!\[CDATA\[(.*?)\]\]>",
        r"\1",
        bruto,
        flags=re.S,
    )

    # DOS PASADAS, Y EN ESTE ORDEN (05/09/2026)
    #
    #     Mundo Deportivo mete HTML ESCAPADO dentro del CDATA:
    #     `&lt;b&gt;Vivian&lt;/b&gt;`. Quitando etiquetas primero
    #     y desescapando despues, las etiquetas reaparecen y la
    #     cita sale con etiquetas dentro. Se vio en la primera
    #     ejecucion en vivo.
    for _ in range(2):
        texto = html.unescape(texto)
        texto = re.sub(r"<[^>]+>", " ", texto)

    texto = texto.replace("\xa0", " ")

    return re.sub(r"\s+", " ", texto).strip()


def _campo(bloque: str, etiqueta: str) -> str:
    encontrado = re.search(
        rf"<{etiqueta}[^>]*>(.*?)</{etiqueta}>",
        bloque,
        flags=re.S,
    )

    return limpiar(encontrado.group(1)) if encontrado else ""


def _fecha(texto: str):
    if not texto:
        return None

    try:
        fecha = parsedate_to_datetime(texto)

    except (TypeError, ValueError):
        return None

    if fecha is None:
        return None

    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)

    return fecha


def fetch_xml(session, url: str) -> tuple:
    """
    Baja un RSS y lo decodifica BIEN. Devuelve `(texto, error)`.

    POR QUE NO SE USA `common.fetch`

        `common.fetch` devuelve `respuesta.text`, y ahi `requests`
        adivina la codificacion. Cuando la cabecera es
        `Content-Type: text/xml` SIN charset —que es justo lo que
        manda Marca— la norma HTTP antigua dice ISO-8859-1, y
        `requests` la aplica.

        Resultado en la primera ejecucion en vivo:

            "Etta Eyong podrÃ­a ser baja"

        El XML declara `encoding="UTF-8"` en su primera linea. Se
        lee esa declaracion y se hace caso; si no la trae, UTF-8,
        que es lo que usan los tres canales vivos.

        Una cita con la codificacion rota no es una cita literal.

    Nunca lanza y nunca reintenta, igual que `common.fetch`: un
    ojeador que tumba el ciclo no es un ojeador.
    """

    try:
        respuesta = session.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )

    except Exception as error:                      # noqa: BLE001
        return (None, f"{type(error).__name__}: {error}")

    if respuesta.status_code in DO_NOT_RETRY:
        return (
            None,
            f"HTTP {respuesta.status_code}: la web dice que no. "
            f"Se anota y no se reintenta.",
        )

    if respuesta.status_code != 200:
        return (None, f"HTTP {respuesta.status_code}")

    crudo = respuesta.content

    declarada = re.search(
        rb"encoding=.([A-Za-z0-9_-]+)",
        crudo[:200],
    )

    codificacion = (
        declarada.group(1).decode("ascii", "replace")
        if declarada
        else "utf-8"
    )

    try:
        return (crudo.decode(codificacion, "replace"), None)

    except LookupError:
        return (crudo.decode("utf-8", "replace"), None)


def parse_items(xml: str | None) -> list:
    """
    Los `<item>` de un RSS, con lo poco que hace falta.

    Nunca lanza: un feed roto devuelve lista vacia y quien llame
    lo anota como fuente sin datos.
    """

    if not xml:
        return []

    noticias = []

    for bloque in re.findall(r"<item[ >].*?</item>", xml, flags=re.S):

        titulo = _campo(bloque, "title")

        if not titulo:
            continue

        noticias.append(
            {
                "title": titulo,
                "summary": _campo(bloque, "description"),
                "url": _campo(bloque, "link"),
                "published_raw": _campo(bloque, "pubDate"),
                "published_at": _fecha(_campo(bloque, "pubDate")),
            }
        )

    return noticias


def frases(texto: str) -> list:
    """
    El texto partido en frases.

    La cita que se guarda es la frase que dispara la regla, no el
    articulo entero: es lo unico que permite discutir un fallo
    dentro de un mes sin volver a abrir el enlace.
    """

    if not texto:
        return []

    trozos = re.split(r"(?<=[\.\?\!:])\s+|\s+\|\s+", texto)

    return [t.strip() for t in trozos if t and t.strip()]


def classify(frase: str, sujeto: str | None = None,
             equipos=frozenset()) -> tuple:
    """
    Que clase de noticia es. ESTO ES UNA DEDUCCION.

    Devuelve `(kind, direction)`. `MENCION` cuando el jugador sale
    pero no hay ninguna palabra que diga nada: nombrar a alguien
    no es una señal.

    Con `sujeto` (el nombre del catalogo del unico activo de la
    frase), una palabra de BAJA o DUDA solo cuenta si ningun otro
    nombre propio esta mas cerca de ella (`de_quien_es`). Sin
    `sujeto`, como siempre.
    """

    return clasificar(frase, sujeto, equipos)["clase"]


def _palabras(texto: str) -> list:
    """`[(inicio, fin, palabra)]` de un texto, en orden."""

    return [
        (m.start(), m.end(), m.group(0))
        for m in re.finditer(r"\w+(?:['’\-]\w+)*", texto)
    ]


def _indice_de(palabras: list, posicion: int) -> int:
    """La palabra que contiene (o sigue a) un caracter."""

    for indice, (inicio, fin, _) in enumerate(palabras):

        if posicion < fin:
            return indice

    return max(len(palabras) - 1, 0)


# Lo que, detras de la primera palabra de la frase, dice que es el
# sujeto: "Dembele es baja", "Hakimi se pierde el partido".
VERBOS_DE_SUJETO = frozenset({
    "es", "se", "sera", "esta", "estara", "sufre",
})


def _abre_como_sujeto(frase: str, palabras: list) -> bool:
    """
    ¿La primera palabra de la frase, sola, tiene pinta de nombre?
    Si detras va una coma ("Dembele, lesionado, ..."), uno de
    `VERBOS_DE_SUJETO` o una palabra de las `REGLAS` ("Dembele
    lesionado"). Nunca si ella misma es una palabra de las reglas
    ("Lesionado, Pedri se pierde el Clasico") ni si no hay nada
    detras. Nunca lanza.
    """

    try:
        if len(palabras) < 2:
            return False

        primera = plano(palabras[0][2])

        if any(re.search(patron, primera) for _, _, patron in REGLAS):
            return False

        entre = frase[palabras[0][1]:palabras[1][0]].strip()

        if entre.startswith(","):
            return True

        if entre:
            return False

        siguiente = plano(palabras[1][2])

        return siguiente in VERBOS_DE_SUJETO or any(
            re.search(patron, siguiente) for _, _, patron in REGLAS
        )

    except Exception:                               # noqa: BLE001
        return False


def nombres_propios(frase: str, equipos=frozenset()) -> list:
    """
    Los nombres propios de una frase que pueden ser personas.

    `[(primera, ultima, texto)]`, con las posiciones en PALABRAS.
    Palabras en mayuscula seguidas (con `UNEN_NOMBRE` en medio:
    "Frenkie de Jong"), sin las de `NO_ABREN_NOMBRE` en las puntas,
    sin la primera de la frase si va sola ("Alarma con la lesion
    de Guruzeta") salvo que tenga pinta de sujeto ("Dembele,
    lesionado, ...": `_abre_como_sujeto`) y sin los que son todo
    equipo o lugar (`NO_SON_PERSONAS` y las palabras de `equipos`).
    Nunca lanza.
    """

    try:
        palabras = _palabras(frase)

        def mayuscula(i):
            return palabras[i][2][:1].isupper()

        def pegada(i):
            # Solo espacios entre la palabra i-1 y la i: una coma
            # corta el nombre ("Digne, su alternativa").
            return not frase[palabras[i - 1][1]:palabras[i][0]].strip()

        trozos = []
        i = 0

        while i < len(palabras):

            if not mayuscula(i):
                i += 1
                continue

            fin = i

            while True:
                j = fin + 1

                # Los que unen: solo si detras viene otra mayuscula.
                while (
                    j < len(palabras)
                    and pegada(j)
                    and not mayuscula(j)
                    and plano(palabras[j][2]) in UNEN_NOMBRE
                ):
                    j += 1

                if j < len(palabras) and pegada(j) and mayuscula(j):
                    fin = j
                    continue

                break

            trozos.append((i, fin))
            i = fin + 1

        nombres = []
        fuera = NO_SON_PERSONAS | frozenset(equipos or ())

        for primera, ultima in trozos:

            while primera <= ultima and plano(
                palabras[primera][2]
            ) in NO_ABREN_NOMBRE:
                primera += 1

            while ultima >= primera and plano(
                palabras[ultima][2]
            ) in NO_ABREN_NOMBRE:
                ultima -= 1

            if primera > ultima:
                continue

            # La primera palabra de la frase va en mayuscula por ir
            # la primera. Sola, no dice que sea un nombre... salvo
            # que tenga pinta de sujeto (`_abre_como_sujeto`).
            if (
                primera == 0
                and ultima == 0
                and not _abre_como_sujeto(frase, palabras)
            ):
                continue

            sueltas = [
                trozo
                for k in range(primera, ultima + 1)
                for trozo in re.split(r"['’\-]", plano(palabras[k][2]))
                if trozo and trozo not in UNEN_NOMBRE
            ]

            if sueltas and all(trozo in fuera for trozo in sueltas):
                continue

            nombres.append(
                (
                    primera,
                    ultima,
                    frase[palabras[primera][0]:palabras[ultima][1]],
                )
            )

        return nombres

    except Exception:                               # noqa: BLE001
        return []


def de_quien_es(frase: str, patron: str, sujeto: str,
                equipos=frozenset()) -> dict:
    """
    ¿Es del `sujeto` alguna palabra de `patron` en la frase?

    `{"suya", "palabra", "mas_cerca"}`. `suya` es True si en alguna
    aparicion de la regla ningun otro nombre propio esta MAS cerca
    (en palabras) que el sujeto; a igualdad, suya. Si no, False, y
    `palabra` y `mas_cerca` dicen cual y de quien. Si no se
    encuentra al sujeto en la frase, suya (lo de siempre). Nunca
    lanza.
    """

    salida = {"suya": True, "palabra": None, "mas_cerca": None}

    try:
        texto = plano(frase)
        palabras = _palabras(frase)
        buscable = plano(sujeto or "")

        # Donde esta el sujeto: cada aparicion en mayuscula, como en
        # `mentions`.
        suyas = [
            (
                _indice_de(palabras, m.start()),
                _indice_de(palabras, m.end() - 1),
            )
            for m in re.finditer(
                r"(?<![a-z0-9])" + re.escape(buscable) + r"(?![a-z0-9])",
                texto,
            )
            if buscable and frase[m.start()].isupper()
        ]

        if not suyas:
            return salida

        otros = [
            (primera, ultima, nombre)
            for primera, ultima, nombre in nombres_propios(frase, equipos)
            if not any(
                primera <= fin and inicio <= ultima
                for inicio, fin in suyas
            )
        ]

        if not otros:
            return salida

        def distancia(tramo, primera, ultima):
            inicio, fin = tramo

            if ultima < inicio:
                return inicio - ultima - 1

            if primera > fin:
                return primera - fin - 1

            return 0

        primera_ajena = None

        for m in re.finditer(patron, texto):

            tramo = (
                _indice_de(palabras, m.start()),
                _indice_de(palabras, m.end() - 1),
            )

            mia = min(distancia(tramo, a, b) for a, b in suyas)

            ajena, quien = min(
                (distancia(tramo, a, b), nombre)
                for a, b, nombre in otros
            )

            if mia <= ajena:
                return salida

            if primera_ajena is None:
                primera_ajena = (frase[m.start():m.end()], quien)

        if primera_ajena is None:
            return salida

        return {
            "suya": False,
            "palabra": primera_ajena[0],
            "mas_cerca": primera_ajena[1],
        }

    except Exception:                               # noqa: BLE001
        return salida


def clasificar(frase: str, sujeto: str | None = None,
               equipos=frozenset()) -> dict:
    """
    `classify` con el por que: `{"clase": (kind, direction),
    "ajena": None | {"kind", "palabra", "mas_cerca"}}`. `ajena` es la
    primera palabra de BAJA o DUDA que se salto por estar mas cerca
    de otro nombre. Con una `ajena`, las reglas que suben (VUELVE) ya
    no cuentan: la baja apartada no se da la vuelta. Nunca lanza.
    """

    texto = plano(frase)
    ajena = None

    for clase, direccion, patron in REGLAS:

        if not re.search(patron, texto):
            continue

        # UNA BAJA APARTADA NO SE DA LA VUELTA (19/10/2026). "Arda
        # Güler regresa de Turquia con molestias" era DUDA; con
        # "molestias" mas cerca de "Turquia", el "regresa" -pegado al
        # sujeto- la convertia en VUELVE/UP. Solo lo FLAT o MENCION.
        if ajena is not None and direccion == UP:
            continue

        if sujeto and clase in PROXIMIDAD:

            quien = de_quien_es(frase, patron, sujeto, equipos)

            if not quien["suya"]:
                if ajena is None:
                    ajena = {
                        "kind": clase,
                        "palabra": quien["palabra"],
                        "mas_cerca": quien["mas_cerca"],
                    }
                continue

        return {"clase": (clase, direccion), "ajena": ajena}

    return {"clase": (MENCION, FLAT), "ajena": ajena}


# ============================================================
# EL INDICE DEL CATALOGO
# ============================================================


def build_index(targets: list | None) -> dict:
    """
    `{nombre_plano: [jugadores]}`.

    Se guardan tambien los repetidos para poder decir "ambiguo"
    en vez de elegir uno.
    """

    indice: dict[str, list] = {}

    for objetivo in (targets or []):

        nombre = (objetivo or {}).get("name")

        if not nombre:
            continue

        indice.setdefault(plano(nombre), []).append(objetivo)

    return indice


def palabras_de_equipos(catalog: dict | None) -> frozenset:
    """
    Las palabras de los nombres de los equipos del catalogo, sin
    acentos: "Rayo Vallecano" -> {"rayo", "vallecano"}. Un nombre
    propio hecho solo de estas no es una persona. Nunca lanza.
    """

    try:
        equipos = ((catalog or {}).get("data") or {}).get("teams") or {}

        if isinstance(equipos, dict):
            equipos = list(equipos.values())

        return frozenset(
            palabra
            for equipo in equipos
            if isinstance(equipo, dict)
            for palabra in re.split(
                r"[\s'’\-\.]+",
                plano(str(equipo.get("name") or "")),
            )
            if palabra
        )

    except Exception:                               # noqa: BLE001
        return frozenset()


def mentions(texto: str, indice: dict) -> tuple:
    """
    `(emparejados, dudosos)` para un texto.

    Los tres candados del docstring de arriba, aplicados aqui y
    en ningun otro sitio.
    """

    if not texto or not indice:
        return ([], [])

    buscable = plano(texto)

    emparejados = []
    dudosos = []

    for nombre, jugadores in indice.items():

        if len(nombre) < MIN_NAME_LENGTH:
            continue

        encontrado = re.search(
            r"(?<![a-z0-9])" + re.escape(nombre) + r"(?![a-z0-9])",
            buscable,
        )

        if not encontrado:
            continue

        # CANDADO 2: en el texto original tiene que ir en
        # mayuscula. "cabello" es pelo; "Cabello" es el jugador.
        inicial = texto[encontrado.start()]

        if not inicial.isupper():
            continue

        # CANDADO 3: un nombre que vale para dos fichas no se
        # adivina.
        if len(jugadores) > 1:
            dudosos.append(
                {
                    "name": jugadores[0]["name"],
                    "reason": (
                        f"«{jugadores[0]['name']}» corresponde a "
                        f"{len(jugadores)} fichas de Biwenger: no "
                        f"se adivina cual."
                    ),
                }
            )
            continue

        emparejados.append(jugadores[0])

    return (emparejados, dudosos)


# ============================================================
# EL OJEADOR
# ============================================================


def scout(
    feed: str,
    *,
    session=None,
    xml: str | None = None,
) -> dict:
    """
    Un canal. Misma forma de respuesta que los demas ojeadores.
    """

    configuracion = FEEDS.get(feed) or {}

    if not configuracion:
        return source_result(
            feed,
            ok=False,
            error=f"Canal desconocido: {feed}.",
        )

    if not configuracion.get("enabled", False):
        return source_result(
            feed,
            ok=False,
            error=configuracion.get("note"),
            note=configuracion.get("note"),
        )

    if xml is None:

        if session is None:
            import requests

            session = requests.Session()

        xml, error = fetch_xml(session, configuracion["url"])

        if error:
            return source_result(
                feed,
                ok=False,
                error=error,
                note=configuracion.get("note"),
            )

    noticias = parse_items(xml)

    return source_result(
        feed,
        ok=True,
        records=noticias,
        note=configuracion.get("note"),
    )


def _reciente(noticia: dict, ahora: datetime) -> bool:
    fecha = noticia.get("published_at")

    if fecha is None:
        # Sin fecha no se descarta: se deja pasar y se dice que no
        # la trae. Tirar una noticia por no llevar sello seria
        # perder informacion por un fallo del medio.
        return True

    return (ahora - fecha) <= timedelta(hours=MAX_ITEM_AGE_HOURS)


def build_press_report(
    catalog: dict | None,
    *,
    session=None,
    xml_by_feed: dict | None = None,
    now: datetime | None = None,
) -> dict:
    """
    Lo que dice la prensa hoy de la gente de Biwenger.

    NUNCA LANZA. `xml_by_feed` existe para las guardias: se le
    pasan feeds en disco y no se toca la red.
    """

    ahora = now or datetime.now(timezone.utc)

    try:
        objetivos = build_targets(catalog)
        indice = build_index(objetivos)
        equipos = palabras_de_equipos(catalog)

        fuentes = {}
        por_jugador: dict[str, dict] = {}
        sin_emparejar = []
        titulares = 0
        viejos = 0

        # CON FEEDS EN LA MANO NO SE SALE A LA CALLE
        #
        #     Si se pasan XML de prueba, se leen SOLO esos. La
        #     primera version recorria los cuatro canales y se
        #     bajaba de internet los que no le habian dado, asi
        #     que una guardia que creia estar leyendo un titular
        #     inventado se traia ademas las noticias de hoy de
        #     Mundo Deportivo. La puerta dejaba de ser
        #     determinista y ademas dependia de que Marca
        #     estuviera de pie.
        canales = (
            list(xml_by_feed)
            if xml_by_feed is not None
            else list(FEEDS)
        )

        for feed in canales:

            try:
                resultado = scout(
                    feed,
                    session=session,
                    xml=(xml_by_feed or {}).get(feed),
                )

            except Exception as error:              # noqa: BLE001
                resultado = source_result(
                    feed,
                    ok=False,
                    error=f"{type(error).__name__}: {error}",
                )

            noticias = resultado.get("records") or []

            emparejadas = 0

            for noticia in noticias:

                titulares += 1

                if not _reciente(noticia, ahora):
                    viejos += 1
                    continue

                señales = _senales_de(
                    noticia, indice, feed, equipos
                )

                if not señales:

                    sin_emparejar.append(
                        {
                            "source": feed,
                            "title": noticia["title"],
                            "url": noticia.get("url"),
                            "reason": (
                                "Ningun nombre del catalogo de "
                                "Biwenger aparece en el titular "
                                "con las tres condiciones de "
                                "emparejamiento."
                            ),
                        }
                    )
                    continue

                emparejadas += 1

                for señal in señales:

                    clave = str(señal.pop("player_id"))

                    ficha = por_jugador.setdefault(
                        clave,
                        {
                            "player_name": señal.pop("player_name"),

                            # Hace falta para el libro de acierto:
                            # una prediccion se puntua contra el
                            # precio que tenia cuando se dijo.
                            "market_price": señal.pop(
                                "market_price", 0
                            ),
                            "items": [],
                        },
                    )

                    señal.pop("player_name", None)
                    señal.pop("market_price", None)

                    ficha["items"].append(señal)

            fuentes[feed] = {
                "ok": bool(resultado.get("ok")),
                "enabled": bool(
                    (FEEDS.get(feed) or {}).get("enabled")
                ),
                "items": len(noticias),
                "matched": emparejadas,
                "error": resultado.get("error"),
                "note": resultado.get("note"),
                "url": (FEEDS.get(feed) or {}).get("url"),
                "fetched_at": resultado.get("fetched_at"),
            }

        con_señal = {
            clave: ficha
            for clave, ficha in por_jugador.items()
            if any(
                item["kind"] != MENCION
                for item in ficha["items"]
            )
        }

        vivas = [f for f in FEEDS.values() if f.get("enabled")]

        return {
            "version": VERSION,
            "available": bool(por_jugador) or bool(sin_emparejar),
            "generated_at": now_iso(),

            "sources": fuentes,
            "feeds_enabled": len(vivas),

            "headlines": titulares,
            "too_old": viejos,
            "max_item_age_hours": MAX_ITEM_AGE_HOURS,

            "players": por_jugador,
            "players_with_signal": len(con_señal),
            "players_mentioned": len(por_jugador),

            # EL CRUDO SE GUARDA ENTERO (09/09/2026)
            #
            #     Estaba cortado en 60 con `unmatched_total: 95`:
            #     35 titulares se tiraban cada dia.
            #
            #     Y eran los peores de perder. Un titular sin
            #     emparejar es uno en el que no se reconocio
            #     ningun nombre — que es exactamente donde se
            #     esconde "el Malaga busca a fulano" cuando el
            #     emparejador falla.
            #
            #     Ahora que el archivo diario guarda este informe
            #     tal cual, cortar aqui es perder para siempre lo
            #     que mañana permitiria reclasificar hacia atras
            #     con clases nuevas.
            #
            #     La pantalla ya recorta por su cuenta a 12, asi
            #     que esto no le añade ni una linea.
            "unmatched": sin_emparejar,
            "unmatched_total": len(sin_emparejar),

            # Que se pinte solo, para que nadie lo lea como un
            # pronostico de la casa.
            "observer_only": True,
            "confidence_basis": CONFIDENCE_BASIS,
            "caveat": (
                "El titular, la frase y el enlace son DATO: es lo "
                "que publico el medio. La clase de noticia y la "
                "direccion son DEDUCCION nuestra a partir de "
                "palabras clave, y viajan marcadas."
            ),
        }

    except Exception as error:                      # noqa: BLE001
        return {
            "version": VERSION,
            "available": False,
            "generated_at": now_iso(),
            "reason": (
                f"El ojeador de prensa no pudo trabajar: "
                f"{type(error).__name__}: {error}"
            ),
            "sources": {},
            "players": {},
            "unmatched": [],
        }


def _senales_de(noticia: dict, indice: dict, feed: str,
                equipos=frozenset()) -> list:
    """
    Las señales de UNA noticia, frase a frase.

    UNA FRASE CON DOS NOMBRES NO SE CLASIFICA (05/09/2026)

        En la primera ejecucion en vivo salio esto:

            "El centrocampista navarro regresa despues de
             perderse los dos ultimos encuentros por una leve
             lesion muscular, el central cubre la baja de Vivian"

        Una sola frase, tres nombres del catalogo -Canales, Peio
        Canales y Vivian- y la regla le colgaba BAJA a los tres.
        Solo uno es la baja; el otro justamente REGRESA.

        Lo mismo con "Simeone no podra contar con...", que
        convertia al entrenador en lesionado.

        Asi que cuando una frase nombra a mas de un activo, la
        clase NO se afirma: el item se queda en MENCION, con la
        cita entera y diciendo por que. La informacion no se
        pierde -el dueño lee la frase- pero no se inventa un
        sujeto.

        Es la misma regla que el resto de la casa: lo que no
        empareja con confianza no se adivina.
    """

    señales = []

    candidatas = frases(noticia["title"]) + frases(
        noticia.get("summary") or ""
    )

    vistos = set()

    for frase in candidatas:

        jugadores, _dudosos = mentions(frase, indice)

        if not jugadores:
            continue

        # EL SUJETO TIENE QUE SER UNO SOLO.
        sujeto_unico = len(jugadores) == 1

        # Y LA BAJA, SUYA (19/10/2026): con un solo activo, una
        # palabra de BAJA o DUDA que esta mas cerca de otro nombre
        # -Nuno Mendes, Digne- no se le cuelga a el.
        deduccion = (
            clasificar(frase, jugadores[0]["name"], equipos)
            if sujeto_unico
            else {"clase": (MENCION, FLAT), "ajena": None}
        )

        clase, direccion = deduccion["clase"]

        ajena = deduccion["ajena"]

        motivo = (
            None
            if sujeto_unico
            else (
                f"La frase nombra a {len(jugadores)} activos "
                f"({', '.join(j['name'] for j in jugadores)}): no "
                f"se afirma a cual se refiere la noticia."
            )
        )

        for jugador in jugadores:

            if jugador["id"] in vistos:
                continue

            vistos.add(jugador["id"])

            señales.append(
                {
                    "player_id": jugador["id"],
                    "player_name": jugador["name"],
                    "market_price": jugador.get("price"),

                    "source": feed,
                    "kind": clase,
                    "direction": direccion,

                    # NUNCA inventada.
                    "confidence": None,
                    "confidence_basis": CONFIDENCE_BASIS,

                    # DATO: literal, del medio.
                    "quote": frase,
                    "headline": noticia["title"],
                    "url": noticia.get("url"),
                    "published_at": (
                        noticia["published_at"].isoformat()
                        if noticia.get("published_at")
                        else None
                    ),

                    # DEDUCCION: la ponemos nosotros, y solo
                    # cuando hay un unico sujeto en la frase.
                    "deduced": True,
                    "deduced_from": (
                        "Palabras clave sobre la frase citada."
                        if sujeto_unico
                        else "No se deduce nada: sujeto ambiguo."
                    ),
                    "subjects_in_quote": len(jugadores),
                    "ambiguous_subject": not sujeto_unico,
                    "ambiguous_reason": motivo,

                    # La palabra de BAJA o DUDA que NO se le
                    # atribuyo, y por que. None si no hubo ninguna.
                    "keyword_reason": (
                        f"«{ajena['palabra']}» ({ajena['kind']}) esta "
                        f"mas cerca de «{ajena['mas_cerca']}» que de "
                        f"{jugador['name']}: no se le atribuye."
                        if ajena
                        else None
                    ),

                    "seen_at": now_iso(),
                }
            )

    return señales


# ============================================================
# DOS VECES AL DIA
# ============================================================


def _load(path: Path):
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))

    except Exception:                               # noqa: BLE001
        return None


def save_press_report(informe: dict, path: Path | None = None) -> None:
    destino = path or REPORT_FILE

    try:
        import json

        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(informe, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )

    except Exception:                               # noqa: BLE001
        # Un ojeador que no puede escribir su fichero sigue
        # sirviendo lo que trae. No es motivo para nada mas.
        pass


def age_seconds(informe: dict | None, now: datetime | None = None):
    if not informe:
        return None

    marca = informe.get("generated_at")

    if not marca:
        return None

    try:
        generado = datetime.fromisoformat(marca)

    except (TypeError, ValueError):
        return None

    if generado.tzinfo is None:
        generado = generado.replace(tzinfo=timezone.utc)

    ahora = now or datetime.now(timezone.utc)

    return (ahora - generado).total_seconds()


def refresh_press(
    catalog: dict | None,
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    force: bool = False,
    session=None,
    path: Path | None = None,
    now: datetime | None = None,
) -> dict:
    """
    El informe de prensa, de disco si vale y de la calle si no.

    NUNCA LANZA. Si algo va mal se devuelve lo ultimo que hubiera
    y, si no hay nada, un informe que dice por que.
    """

    destino = path or REPORT_FILE

    try:
        anterior = _load(destino)

        edad = age_seconds(anterior, now=now)

        if (
            not force
            and anterior
            and edad is not None
            and edad < ttl_seconds
        ):
            salida = dict(anterior)
            salida["cache"] = {
                "status": "HIT",
                "age_seconds": round(edad, 1),
                "ttl_seconds": ttl_seconds,
            }
            return salida

        nuevo = build_press_report(
            catalog,
            session=session,
            now=now,
        )

        # Un informe recien escrito sin ni un titular es peor que
        # uno de hace doce horas: parece dato y no lo es.
        if not nuevo.get("headlines") and anterior:

            salida = dict(anterior)
            salida["cache"] = {
                "status": "STALE_FALLBACK",
                "age_seconds": round(edad or 0, 1),
                "ttl_seconds": ttl_seconds,
                "error": (
                    "Ningun canal trajo titulares: se conserva el "
                    "informe anterior."
                ),
            }
            return salida

        save_press_report(nuevo, destino)

        nuevo["cache"] = {
            "status": "REFRESHED",
            "age_seconds": 0.0,
            "ttl_seconds": ttl_seconds,
        }

        return nuevo

    except Exception as error:                      # noqa: BLE001
        return {
            "version": VERSION,
            "available": False,
            "generated_at": now_iso(),
            "reason": (
                f"El ojeador de prensa no pudo trabajar: "
                f"{type(error).__name__}: {error}"
            ),
            "sources": {},
            "players": {},
            "unmatched": [],
            "cache": {"status": "ERROR"},
        }


# ============================================================
# AL LIBRO DE ACIERTO
# ============================================================
#
#     "Precedente: FutbolFantasy saca 0,3365 de Brier en
#      pronosticos de titular — peor que tirar una moneda.
#      Ninguna fuente entra por prestigio."
#
#     Asi que la prensa tampoco. Cada señal se apunta con el
#     precio del jugador ese dia y en tres jornadas se sabra si
#     una baja publicada movio el precio o no movio nada.

# El horizonte de la casa para una apuesta de precio. Una baja se
# nota en el mercado en uno o dos dias; tres da margen sin dejar
# la prediccion abierta tanto que se cumpla sola.
ACCURACY_HORIZON_DAYS = 3


# FLAT no es una apuesta. Una noticia de alineacion o de fichaje
# dice algo del jugador, pero no dice hacia donde va su precio, y
# apuntarla como prediccion inflaria el acierto con casos que no
# se pueden fallar.
SCORABLE_KINDS = (BAJA, DUDA, VUELVE)


def as_accuracy_report(informe: dict | None) -> dict:
    """
    El informe de prensa con la forma que espera el libro.

    Se reutiliza `accuracy.record_report` tal cual: una copia del
    libro para la prensa seria una segunda forma de contar los
    aciertos, y con dos formas siempre gana la que mejor queda.
    """

    jugadores = {}

    for clave, ficha in ((informe or {}).get("players") or {}).items():

        señales = []

        for item in ficha.get("items") or []:

            if item.get("kind") not in SCORABLE_KINDS:
                continue

            if item.get("ambiguous_subject"):
                continue

            señales.append(
                {
                    # La fuente lleva el medio dentro: en dos
                    # semanas se podra ver si Marca acierta mas
                    # que Mundo Deportivo, que es justo lo que
                    # hay que saber.
                    "source": f"PRENSA_{item.get('source')}",
                    "direction": item.get("direction"),
                    "horizon_days": ACCURACY_HORIZON_DAYS,
                    "confidence": None,
                    "observed": False,
                    "seen_at": item.get("seen_at"),
                    "quote": item.get("quote"),
                }
            )

        if not señales:
            continue

        jugadores[clave] = {
            "player_name": ficha.get("player_name"),
            "market_price": ficha.get("market_price"),
            "signals": señales,
        }

    return {
        "version": VERSION,
        "source": SOURCE,
        "players": jugadores,
    }


# ============================================================
# LO QUE VE EL DUEÑO
# ============================================================


def load_press_report(path: Path | None = None):
    return _load(path or REPORT_FILE)


def build_press_block(informe: dict | None) -> dict:
    """
    El bloque compacto para el dashboard.

    Se ordena por lo que MAS importa: primero lo que quita
    puntos, y dentro de eso lo mas caro, que es donde un fallo
    cuesta mas dinero. Las menciones sin señal no suben a la
    portada: se cuentan y ya.
    """

    if not informe:
        return {
            "available": False,
            "observer_only": True,
            "reason": (
                "Todavia no hay informe de prensa en disco. Se "
                "genera en el ciclo, dos veces al dia."
            ),
            "sources": {},
            "items": [],
            "unmatched": [],
        }

    PESO = {BAJA: 0, DUDA: 1, VUELVE: 2, ALINEACION: 3, FICHAJE: 4}

    filas = []

    for clave, ficha in (informe.get("players") or {}).items():

        for item in ficha.get("items") or []:

            if item.get("kind") == MENCION:
                continue

            filas.append(
                {
                    "player_id": int(clave),
                    "player_name": ficha.get("player_name"),
                    "market_price": ficha.get("market_price"),
                    **item,
                }
            )

    filas.sort(
        key=lambda f: (
            PESO.get(f["kind"], 9),
            -int(f.get("market_price") or 0),
        )
    )

    return {
        "available": bool(informe.get("available")),
        "observer_only": True,
        "reason": informe.get("reason"),

        "generated_at": informe.get("generated_at"),
        "cache": informe.get("cache"),

        "sources": informe.get("sources") or {},
        "feeds_enabled": informe.get("feeds_enabled"),

        "headlines": informe.get("headlines"),
        "players_mentioned": informe.get("players_mentioned"),
        "players_with_signal": informe.get("players_with_signal"),

        "items": filas[:30],
        "items_total": len(filas),

        "unmatched": (informe.get("unmatched") or [])[:12],
        "unmatched_total": informe.get("unmatched_total"),

        "confidence_basis": informe.get("confidence_basis"),
        "caveat": informe.get("caveat"),
    }
