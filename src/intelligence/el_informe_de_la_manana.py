"""
EL INFORME DE LA MAÑANA (18/10/2026)

POR QUE EXISTE

    El dueño (17-18/10): cada mañana, tras el reset de las 07:00 de
    Madrid, mirar a TODOS los jugadores nuevos del mercado como se miro
    a Carvajal —noticias, recomendaciones de las webs fantasy,
    probabilidad de titular, riesgo fisico, impulso del precio—, darle
    un peso a cada uno y sumarlo a la decision de pujar.

    Plan acordado: DOS NOTAS por jugador, con pesos MEDIDOS y no
    adivinados (laboratorio del 18/10):

        SUBE     revalorizacion esperada a 7 dias, en %. Para la cartera
                 y la rotacion.
        PUNTUA   puntos esperados en la primera jornada que empieza
                 cuando el jugador ya es tuyo. Para la mejora del once.

    FASE 1 (esto): SOLO OBSERVA. Se calcula, se apunta en su libro y se
    enseña en el panel. Ninguna ruta lo lee para pujar: eso es la fase
    2, detras de su propio interruptor, cuando los pesos se hayan vuelto
    a medir contra lo que apunta este libro.

LAS DOS FORMULAS (laboratorio del 18/10, intervalos al 95 % por jugador)

    SUBE = -1,0 + 4,5*C + 2,5*VUELTA + 3,0*BARATO

        C       cambio de precio de HOY en %, (P(d)/P(d-1) - 1)*100,
                recortado a [-5, +8]. Es casi todo: rho +0,63 en el
                mercado, +0,61 fuera de muestra.
        VUELTA  1 si FutbolFantasy publico una noticia de VUELTA del
                jugador en las ultimas 72 h (+2,1 [+0,6; +4,0] fuera de
                muestra en el catalogo).
        BARATO  1 si P(d) < 1.000.000 (+2 a +5,5: unos pocos que
                explotan; sube la media, no la probabilidad de subir).

        Medido en el catalogo (n=18.317): constante -1,55; C 4,68
        [4,39; 5,00]; VUELTA 1,85 [0,68; 3,05]; BARATO 2,69 [1,83;
        3,47]. Fuera de muestra (mercado de octubre): rho +0,625.
        Lectura: sube >= 2, el 67 % pasa de +2 %; sube <= 0, casi
        nunca.

    PUNTUA = 0,5 + 0,85*P*Q - 1,0*PRENSA_BAJA

        P            titular de FutbolFantasy / 100. Sin dato de FF: la
                     cuota de partidos jugados (jugados / jornadas
                     disputadas), y entonces se resta 1,2 si el estado
                     de Biwenger no es 'ok' (-1,17 [-1,43; -0,86]).
        Q            puntos por partido acercados a la mediana de su
                     posicion: (puntos + 2*R) / (jugados + 2), con R =
                     5,1 portero, 3,2 defensa, 3,5 medio y delantero.
        PRENSA_BAJA  1 si MARCA, MD o Relevo dieron BAJA o DUDA en las
                     ultimas 72 h (-1,0 [-1,5; -0,6], n=6; -2,0 en el
                     catalogo, n=27).

        Medido: k 0,85 [0,54; 1,21]; constante 0,54 [0,13; 0,97]
        (n=192). Fuera de muestra: rho +0,45, error medio 1,8 puntos.

    Carvajal (18/10): 3,2 M, +10 % hoy (C=8), titular 30 %, 0 partidos,
    defensa: sube = +35 (la mas alta del dia), puntua = 1,3. Sube alta y
    puntua baja: lo que el dueño esperaba.

LO QUE SE APUNTA Y NO PESA (peso 0, y por que)

    El laboratorio dice que no tienen efecto medible, o que no hay
    historia para medirlo. Se apuntan igual —es lo que la fase 1 tiene
    que volver a medir— pero NO entran en las notas:

        - las webs de mercado (FF, Analitica, Comuniate): publican el
          mismo numero que el cambio de hoy (correlacion 0,97-0,98);
        - los cambios a 3 y 7 dias y la racha: no suman fuera de
          muestra;
        - noticias FF de BAJA (el precio ya cae ese dia) y de
          TITULARIDAD, «Analisis Fantasy», SANCION y las
          recomendaciones tipo «ficha si sale»: sin efecto medible o
          sin historia;
        - jerarquia, minutos y parte de FF, indicadores de Jornada
          Perfecta (lesionado, duda, tip, editorial).

CUANDO

    Una vez por DIA DE MERCADO (el que va de un reset de las 07:00 de
    Madrid al siguiente, con el horario de verano bien puesto: el de
    `la_rotacion`). La primera vuelta que llega con la foto de DESPUES
    del reset lo hace; las demas del dia ven la linea DIA y se van.
    Una foto de antes del reset no se usa (la del libro del escaparate
    enseño por que: una foto vieja con la fecha de hoy ensucia el libro
    entero).

    Corre como paso propio del workflow, DESPUES de la rotacion: lee lo
    que la vuelta ya trajo (la foto, el tablero de FF, la prensa, el
    mercado de JP, el historico de precios). Para la fase 2 tendra que
    ir ANTES de `build_cycle_acquisition_board`, que es donde se decide.

QUIEN ES NUEVO

    Los del mercado de hoy (Computer y managers; lo nuestro no) que no
    estaban en el mercado del ultimo dia apuntado. Ese mercado sale de
    la linea DIA de este libro (lleva el mercado entero); si no hay
    —el primer dia—, del libro de la valoracion y del escaparate; si
    tampoco, todos cuentan como nuevos y la linea lo dice.

LAS NOTICIAS DE FUTBOLFANTASY: LO UNICO QUE SE PIDE A LA RED

    Todo lo demas ya lo trae la vuelta. Para VUELTA hace falta leer el
    bloque de noticias de la pagina del equipo en FF
    (`/laliga/equipos/{slug}`), que el proveedor de FF no lee. Una
    pagina por equipo de algun nuevo, una vez por dia (las del mismo
    equipo comparten pagina), con:

        - tiempo de espera por peticion, tope de paginas por vuelta,
          tope de tiempo total y corte tras varios fallos seguidos;
        - si la red falla, la señal FALTA (VUELTA = 0 y se dice), no
          es un error: el informe se escribe igual;
        - el HTML es un DATO DE FUERA: solo se le sacan titulares,
          fecha y enlace con un parser. Nada de lo que trae se ejecuta.

    Los titulares se clasifican con el clasificador del laboratorio de
    las noticias (E4, `lab/noticias/analizar.py`): BAJA / VUELTA /
    TITULARIDAD con las mismas reglas con las que se midio el peso de
    VUELTA. Encima, solo para observar: DUDA (separada de BAJA),
    SANCION, RECOMENDADO («ficha si sale», chollo...) y ANALISIS
    («Analisis Fantasy de ...»).

EL LIBRO: `data/intelligence/el_informe_de_la_manana.jsonl`

    Por dia de mercado, una linea `DIA` (el mercado entero, quien es
    nuevo, de donde salio la base, que se pudo leer) y una linea
    `JUGADOR` por cada nuevo: las dos notas, el por que, los terminos de
    las formulas y las señales que no pesan.

QUE NO HACE

    No puja, no vende, no toca el once, no escribe en Biwenger y no
    cambia ninguna decision. Solo escribe su libro. Nace APAGADO:
    `BORDALAS_EL_INFORME_DE_LA_MANANA`. Nunca lanza.
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata

from datetime import datetime, timedelta, timezone
from pathlib import Path


ENV = "BORDALAS_EL_INFORME_DE_LA_MANANA"
RAIZ = Path(__file__).parents[2]

DIRECTORIO = Path("data") / "intelligence"
LIBRO = DIRECTORIO / "el_informe_de_la_manana.jsonl"

# Los pesos de esta version, en cada linea: cuando se vuelvan a medir,
# se sabra con cuales se apunto cada nota.
PESOS = "laboratorio-2026-10-18"


# ============================================================
# LOS PESOS (laboratorio del 18/10/2026; ver la cabecera)
# ============================================================

# SUBE. Catalogo n=18.317: constante -1,55; C 4,68 [4,39; 5,00];
# VUELTA 1,85 [0,68; 3,05]; BARATO 2,69 [1,83; 3,47]. Redondeados a lo
# que el laboratorio propone; fuera de muestra rho +0,625.
SUBE_CONSTANTE = -1.0
SUBE_POR_PUNTO_DE_CAMBIO = 4.5
SUBE_VUELTA = 2.5
SUBE_BARATO = 3.0
CAMBIO_MINIMO = -5.0            # el cambio de hoy, recortado a [-5, +8] %
CAMBIO_MAXIMO = 8.0
BARATO_POR_DEBAJO_DE = 1_000_000

# PUNTUA. k 0,85 [0,54; 1,21] y constante 0,54 [0,13; 0,97] (n=192);
# prensa -1,0 [-1,5; -0,6] (n=6); estado no 'ok' -1,17 [-1,43; -0,86]
# (n=65, solo en la J7, y solo cuando FF no da titular).
PUNTUA_CONSTANTE = 0.5
PUNTUA_K = 0.85
PUNTUA_PRENSA_BAJA = -1.0
PUNTUA_ESTADO_NO_OK_SIN_FF = -1.2
# Mediana de puntos por partido de cada posicion (18/09) y cuantos
# partidos de esa mediana se suman para acercar a ella al de pocos.
R_POR_POSICION = {1: 5.1, 2: 3.2, 3: 3.5, 4: 3.5}
R_SIN_POSICION = 3.5
ENCOGIMIENTO = 2

# La ventana de las noticias (FF y prensa), como en el laboratorio.
VENTANA_HORAS = 72


# ============================================================
# LA RED: TOPES
# ============================================================

FF_BASE = "https://www.futbolfantasy.com"
TIMEOUT_SEGUNDOS = 12
MAXIMO_DE_PAGINAS = 20                   # los veinte equipos, como mucho
SEGUNDOS_PARA_LAS_NOTICIAS = 120         # el paso entero no puede pasar de aqui
FALLOS_SEGUIDOS_PARA_PARAR = 3           # FF nos corta: no se insiste
TAMANO_MAXIMO_HTML = 6_000_000           # la pagina del Celta pesaba 2,5 MB
MAXIMO_NOTICIAS_POR_PAGINA = 40
MAXIMO_NOTICIAS_POR_JUGADOR = 6
LARGO_MAXIMO_TITULAR = 200

# Una foto de los primeros minutos tras el reset puede no traer aun el
# mercado nuevo.
MINUTOS_TRAS_EL_RESET = 5

LINEAS_QUE_SE_GUARDAN = 20_000           # ~25 al dia: mas de dos años


def activa() -> bool:
    try:
        return str(os.environ.get(ENV, "")).strip().lower() in {"1", "true", "si", "yes"}
    except Exception:                               # noqa: BLE001
        return False


# ============================================================
# AYUDAS QUE NUNCA LANZAN
# ============================================================

def _int(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return defecto


def _num(x, defecto=None):
    try:
        if x is None or isinstance(x, bool):
            return defecto
        valor = float(x)
        return valor if valor == valor and abs(valor) != float("inf") else defecto
    except (TypeError, ValueError, OverflowError):
        return defecto


def _dict(x) -> dict:
    return x if isinstance(x, dict) else {}


def _lista(x) -> list:
    try:
        if isinstance(x, dict):
            x = list(x.values())
        if not isinstance(x, (list, tuple)):
            return []
        return [f for f in x if isinstance(f, dict)]
    except Exception:                               # noqa: BLE001
        return []


def _pid(x):
    if isinstance(x, dict):
        x = x.get("id")
    return _int(x)


def _es(x, decimales=1) -> str:
    """Un numero a la española, con signo."""
    try:
        return f"{float(x):+.{decimales}f}".replace(".", ",")
    except (TypeError, ValueError):
        return "?"


def _cuando(x) -> datetime | None:
    """ISO o datetime a datetime con zona (sin zona: UTC). None si no."""
    try:
        t = x if isinstance(x, datetime) else datetime.fromisoformat(
            str(x).strip().replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _utc(ahora) -> datetime:
    t = _cuando(ahora) if ahora is not None else None
    return t.astimezone(timezone.utc) if t else datetime.now(timezone.utc)


def _leer_json(ruta, defecto=None):
    try:
        valor = json.loads((RAIZ / ruta).read_text(encoding="utf-8-sig"))
        return valor
    except Exception:                               # noqa: BLE001
        return defecto


def _leer_jsonl(ruta) -> list:
    """Las lineas de un libro jsonl (las que se leen). Nunca lanza."""
    try:
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
    except Exception:                               # noqa: BLE001
        return []
    filas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            fila = json.loads(linea)
        except ValueError:
            continue
        if isinstance(fila, dict):
            filas.append(fila)
    return filas


def norm(texto) -> str:
    """Minusculas, sin tildes, solo letras, numeros y un espacio."""
    try:
        s = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
        return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s.lower()).split())
    except Exception:                               # noqa: BLE001
        return ""


# ============================================================
# LAS DOS NOTAS (puro)
# ============================================================

def el_cambio_de_hoy(precio, incremento) -> float | None:
    """(P(d)/P(d-1) - 1)*100 con P(d-1) = precio - incremento. None si no."""
    precio, incremento = _int(precio), _int(incremento)
    if not precio or incremento is None:
        return None
    antes = precio - incremento
    if antes <= 0:
        return None
    return (precio / antes - 1.0) * 100.0


def los_terminos(jugador_signals) -> dict:
    """
    Los terminos de las dos formulas, de las señales de un jugador. Puro.

    Entra (todo opcional): `precio`, `cambio_hoy_pct`, `vuelta_ff`
    (True / False / None = no se pudo leer), `titular_ff` (0-100),
    `jugados`, `jornadas`, `puntos`, `posicion` (1-4), `estado`,
    `prensa_baja` (True / False / None).
    """
    s = _dict(jugador_signals)
    precio = _int(s.get("precio"))
    cambio = _num(s.get("cambio_hoy_pct"))
    c = None if cambio is None else min(max(cambio, CAMBIO_MINIMO), CAMBIO_MAXIMO)
    barato = None if not precio or precio <= 0 else (1 if precio < BARATO_POR_DEBAJO_DE else 0)

    jugados = _int(s.get("jugados"))
    jugados = jugados if jugados is not None and jugados >= 0 else None
    jornadas = _int(s.get("jornadas"))
    jornadas = jornadas if jornadas and jornadas > 0 else None
    puntos = _num(s.get("puntos"))
    if puntos is None and jugados == 0:
        puntos = 0.0
    posicion = _int(s.get("posicion"))
    r = R_POR_POSICION.get(posicion, R_SIN_POSICION)
    q = ((puntos + ENCOGIMIENTO * r) / (jugados + ENCOGIMIENTO)
         if puntos is not None and jugados is not None else None)

    titular = _num(s.get("titular_ff"))
    if titular is not None and 0.0 <= titular <= 100.0:
        p, p_fuente = titular / 100.0, "FF"
    elif jugados is not None and jornadas:
        p, p_fuente = min(1.0, jugados / jornadas), "CUOTA"
    else:
        p, p_fuente = None, None

    estado = str(s.get("estado") or "").strip().lower() or None
    estado_no_ok = 1 if (p_fuente == "CUOTA" and estado and estado != "ok") else 0

    return {
        "C": None if c is None else round(c, 3),
        "cambio_hoy_pct": None if cambio is None else round(cambio, 3),
        "VUELTA": 1 if s.get("vuelta_ff") is True else 0,
        "vuelta_leida": s.get("vuelta_ff") in (True, False),
        "BARATO": barato,
        "P": None if p is None else round(p, 4),
        "P_fuente": p_fuente,
        "Q": None if q is None else round(q, 4),
        "R": r,
        "PRENSA_BAJA": 1 if s.get("prensa_baja") is True else 0,
        "prensa_leida": s.get("prensa_baja") in (True, False),
        "ESTADO_NO_OK": estado_no_ok,
        "estado": estado,
        "jugados": jugados,
        "jornadas": jornadas,
    }


def puntuar(jugador_signals) -> dict:
    """
    Las dos notas de un jugador, con el por que. PURO: ni disco, ni red,
    ni reloj. Nunca lanza.

        {"sube": % a 7 dias o None, "puntua": puntos o None,
         "por_que": [frases]}

    Sin el cambio de hoy no hay SUBE (es casi toda la nota); sin
    titularidad ni cuota de partidos, o sin puntos por partido, no hay
    PUNTUA. Lo que falta se dice en `por_que`, no se inventa.
    """
    salida = {"sube": None, "puntua": None, "por_que": []}
    try:
        t = los_terminos(jugador_signals)
        por_que = salida["por_que"]

        # SUBE
        if t["C"] is None or t["BARATO"] is None:
            por_que.append("sin el cambio de precio de hoy o sin precio: no hay nota de sube")
        else:
            sube = (SUBE_CONSTANTE + SUBE_POR_PUNTO_DE_CAMBIO * t["C"]
                    + SUBE_VUELTA * t["VUELTA"] + SUBE_BARATO * t["BARATO"])
            salida["sube"] = round(sube, 1)
            recorte = (f" (se cuenta {_es(t['C'])})"
                       if abs(t["C"] - t["cambio_hoy_pct"]) > 1e-9 else "")
            por_que.append(f"cambio de hoy {_es(t['cambio_hoy_pct'])} %{recorte}: "
                           f"{_es(SUBE_POR_PUNTO_DE_CAMBIO * t['C'])}")
            if t["VUELTA"]:
                por_que.append(f"FutbolFantasy da que VUELVE (72 h): {_es(SUBE_VUELTA)}")
            elif not t["vuelta_leida"]:
                por_que.append("noticias de FutbolFantasy sin leer: VUELTA cuenta 0")
            if t["BARATO"]:
                por_que.append(f"vale menos de 1 M: {_es(SUBE_BARATO)}")

        # PUNTUA
        if t["P"] is None or t["Q"] is None:
            por_que.append("sin titularidad ni partidos jugados: no hay nota de puntua")
        else:
            puntua = (PUNTUA_CONSTANTE + PUNTUA_K * t["P"] * t["Q"]
                      + PUNTUA_PRENSA_BAJA * t["PRENSA_BAJA"]
                      + PUNTUA_ESTADO_NO_OK_SIN_FF * t["ESTADO_NO_OK"])
            salida["puntua"] = round(puntua, 2)
            if t["P_fuente"] == "FF":
                de_donde = f"titular FF {round(t['P'] * 100)} %"
            else:
                de_donde = (f"sin titular de FF, juega {t['jugados']} de {t['jornadas']} "
                            f"jornadas ({round(t['P'] * 100)} %)")
            por_que.append(f"{de_donde} x {str(round(t['Q'], 2)).replace('.', ',')} puntos "
                           f"por partido: {_es(PUNTUA_K * t['P'] * t['Q'], 2)}")
            if t["ESTADO_NO_OK"]:
                por_que.append(f"Biwenger lo da '{t['estado']}': {_es(PUNTUA_ESTADO_NO_OK_SIN_FF)}")
            if t["PRENSA_BAJA"]:
                por_que.append(f"la prensa da BAJA o DUDA (72 h): {_es(PUNTUA_PRENSA_BAJA)}")
            elif not t["prensa_leida"]:
                por_que.append("sin informe de prensa: PRENSA_BAJA cuenta 0")
    except Exception as error:                      # noqa: BLE001
        salida["por_que"].append(f"no se pudo puntuar: {type(error).__name__}")
    return salida


# ============================================================
# LOS TITULARES (puro). Clasificador E4 del laboratorio de las
# noticias (`lab/noticias/analizar.py`), copiado tal cual: con el se
# midio el peso de VUELTA. Encima, las etiquetas que solo se observan.
# ============================================================

TRASPASO = re.compile(
    r"traspaso|fichaje|ficha por|cesion|cedido|oficial(mente)?|nuevo jugador|"
    r"acuerdo|oferta|va a por|mercado|salida|negocia|renueva|renovacion|contrato|clausula|"
    r"desconvoca|seleccion|convocatoria de|sub 2|sub 1|internacional")
BAJA = re.compile(
    r"\bsin (recuperar|poder contar|contar con)?\b|lesion|\bbaja|rotura|se pierde|"
    r"se perdera|enfermeria|no entrena|al margen|molestias|tocado|parte medico|"
    r"retirad|operad|intervenid|sufre|descart|duda|dudas|en el aire|no estara|"
    r"no viaja|no recibe|no llega|fuera de la lista|sigue(n)? sin|continua(n)? sin|"
    r"trabajo especifico|trabaja(n)? al margen|en solitario|recuperacion|pendiente de|"
    r"esguince|sobrecarga")
VUELTA = re.compile(
    r"recuperad|\brecupera\b|\brecuperan\b|vuelve|vuelven|regres|\balta\b|con el grupo|"
    r"disponible|incorpora|reaparece|pisa(n)? cesped|se ejercita|completa(n)? la sesion|"
    r"entra(n)? en la lista|convocad|ya entrena|buenas noticias|apto")
TITUL = re.compile(
    r"titular|\bonce\b|rotacion|rotaciones|suplencia|banquillo|alineacion|"
    r"suplente|sale de inicio|gana(r)? el puesto|pierde el puesto|revolucion")
HABLA = re.compile(
    r"\bhabla\b|\bexplica|\banaliza|entrevista|rueda de prensa|palabras de|atiende a")

# Solo se observan (peso 0): no estan en E4 y no hay historia para medirlas.
ANALISIS = re.compile(r"^analisis fantasy\b")
SANCION = re.compile(
    r"sancion|sancionad|expulsad|expulsion|suspendid|cumple ciclo|ciclo de amarillas|"
    r"tarjeta roja")
RECOMENDADO = re.compile(
    r"\bficha(lo|le)?\b(?! por)|\bfichar a\b|recomendad|\bchollo|imprescindible|"
    r"\bapuesta\b|consejo fantasy|a por el\b")
DUDA = re.compile(r"\bduda|en el aire|pendiente de")
BAJA_SEGURA = re.compile(
    r"lesion|\bbaja|rotura|se pierde|se perdera|no estara|operad|intervenid|esguince|"
    r"descart")

# Palabras que no sirven para reconocer a un jugador (E4).
PALABRAS_COMUNES = frozenset({
    "real", "sevilla", "betis", "celta", "villarreal", "valencia", "getafe",
    "girona", "levante", "elche", "osasuna", "athletic", "atletico", "madrid",
    "barcelona", "alaves", "espanyol", "mallorca", "oviedo", "rayo", "sociedad",
    "vuelve", "grupo", "sesion", "lista", "baja", "bajas", "entrenamiento",
    "martes", "lunes", "jueves", "viernes", "sabado", "domingo", "miercoles",
    "david", "pablo", "carlos", "sergio", "javi", "alex", "jose", "juan", "mario",
    "diego", "ivan", "dani", "nico", "jorge", "hugo", "alvaro", "raul", "marc",
    "iago", "luis", "adrian", "victor", "manu", "fran", "antonio", "unai", "jon"})

TIPOS = ("BAJA", "DUDA", "VUELTA", "TITULARIDAD", "SANCION", "RECOMENDADO", "ANALISIS")


def tipo_clausula(c) -> str | None:
    """E4: BAJA / VUELTA / TITULARIDAD / MIXTA / None de un trozo normalizado."""
    c = str(c or "")
    if TITUL.search(c) and not (BAJA.search(c) or VUELTA.search(c)):
        return "TITULARIDAD"
    b, v = BAJA.search(c), VUELTA.search(c)
    if re.search(r"duda(s)? entre|entre .* o ", c) and not re.search(r"lesion|molestias", c):
        return "TITULARIDAD"
    if re.search(r"no (ira|iran|entra|entran|estara|estaran) convocad|trabajo individual|"
                 r"gimnasio|no recibe|sin recuperar|sigue(n)? sin|continua(n)? sin|"
                 r"sigue(n)? al margen|continua(n)? (con su|en) recuperacion", c):
        return "BAJA"
    if v and not b:
        return "VUELTA"
    if b and not v:
        return "BAJA"
    if b and v:
        return "MIXTA"
    return None


def el_indice(jugadores) -> tuple:
    """
    `{pid: nombre}` de UN equipo -> (nombres completos, palabras sueltas).
    Las palabras: de 4 letras o mas y fuera de `PALABRAS_COMUNES` (E4).
    """
    completo, palabras = {}, {}
    try:
        for pid, nombre in _dict(jugadores).items():
            pid = _int(pid)
            trozos = norm(nombre).split()
            if pid is None or not trozos:
                continue
            completo.setdefault(" ".join(trozos), set()).add(pid)
            for w in trozos:
                if len(w) >= 4 and w not in PALABRAS_COMUNES:
                    palabras.setdefault(w, set()).add(pid)
    except Exception:                               # noqa: BLE001
        pass
    return completo, palabras


def emparejar(texto, indice) -> dict:
    """`{pid: posicion en el texto}` de los que se nombran sin ambiguedad (E4)."""
    encontrados = {}
    try:
        completo, palabras = indice
        t = " " + norm(texto) + " "
        for nombre, pids in completo.items():
            if len(nombre.split()) >= 2 and f" {nombre} " in t and len(pids) == 1:
                encontrados[next(iter(pids))] = t.index(f" {nombre} ")
        for w in set(t.split()):
            pids = palabras.get(w)
            if pids and len(pids) == 1:
                encontrados.setdefault(next(iter(pids)), t.index(f" {w} "))
    except Exception:                               # noqa: BLE001
        return {}
    return encontrados


def clasificar_titular(titular, indice) -> dict:
    """
    `{pid: tipo}` de un titular, para los del indice de su equipo.

    1. «Analisis Fantasy de X» -> ANALISIS (como en el laboratorio).
    2. E4: fuera traspasos, selecciones y ruedas de prensa; cada nombrado
       se lleva el trozo que va de su nombre al siguiente; «sin X» / «ni
       X» delante es BAJA. BAJA con duda y sin baja segura -> DUDA.
    3. Si E4 no dice nada: SANCION o RECOMENDADO sobre el titular entero.
    Nunca lanza.
    """
    tipos = {}
    try:
        nt = norm(titular)
        if not nt:
            return {}
        encontrados = emparejar(nt, indice)
        if not encontrados:
            return {}
        if ANALISIS.search(nt):
            return {pid: "ANALISIS" for pid in encontrados}

        if not (TRASPASO.search(nt) or HABLA.search(nt)):
            tnorm = " " + nt + " "
            tipo_global = tipo_clausula(nt)
            orden = sorted(encontrados.items(), key=lambda x: x[1])
            cortes = [p for _, p in orden] + [len(tnorm)]
            trozos = [tnorm[cortes[i]:cortes[i + 1]] for i in range(len(orden))]
            for i, (pid, pos) in enumerate(orden):
                tp, trozo_bueno = None, ""
                for trozo in trozos[i:]:
                    tp = tipo_clausula(trozo)
                    if tp:
                        trozo_bueno = trozo
                        break
                antes = tnorm[:pos]
                if (re.search(r"\bsin (recuperar a )?[a-z ,]*$| ni [a-z ]*$", antes)
                        and not re.search(r"\bcon\b[^,]*$", antes)):
                    tp, trozo_bueno = "BAJA", antes
                if tp is None and i == 0:
                    tp, trozo_bueno = tipo_global, nt
                if tp in (None, "MIXTA"):
                    continue
                if tp == "BAJA" and DUDA.search(trozo_bueno) and not BAJA_SEGURA.search(trozo_bueno):
                    tp = "DUDA"
                tipos[pid] = tp

        resto = [pid for pid in encontrados if pid not in tipos]
        if resto:
            extra = ("SANCION" if SANCION.search(nt)
                     else "RECOMENDADO" if RECOMENDADO.search(nt) else None)
            if extra:
                for pid in resto:
                    tipos[pid] = extra
    except Exception:                               # noqa: BLE001
        return {}
    return tipos


# ============================================================
# LA PAGINA DEL EQUIPO EN FF (puro: el HTML entra por argumento)
# ============================================================

_URL_DE_NOTICIA = re.compile(r"^https://www\.futbolfantasy\.com/laliga/noticias/\d+[-a-z0-9]*$")


def _texto_limpio(x) -> str:
    texto = " ".join(str(x or "").split())
    texto = "".join(ch for ch in texto if ch.isprintable())
    return texto[:LARGO_MAXIMO_TITULAR]


def _url_segura(href) -> str | None:
    try:
        href = str(href or "").strip()
        if href.startswith("/"):
            href = FF_BASE + href
        return href if _URL_DE_NOTICIA.match(href) else None
    except Exception:                               # noqa: BLE001
        return None


def la_fecha_de_ff(dia, hora, ahora) -> datetime | None:
    """
    «28/09» y «23:52» (hora de Madrid, sin año) a UTC. El año es el de
    `ahora`; si asi queda mas de dos dias en el futuro, el anterior.
    None si no se lee.
    """
    try:
        from src.actions.la_rotacion import la_hora_de_la_foto

        m = re.match(r"^\s*(\d{1,2})/(\d{1,2})\s*$", str(dia or ""))
        if not m:
            return None
        h = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", str(hora or "")) or None
        hh, mm = (int(h.group(1)), int(h.group(2))) if h else (12, 0)
        ahora = _utc(ahora)
        for anio in (ahora.year, ahora.year - 1):
            local = datetime(anio, int(m.group(2)), int(m.group(1)), hh, mm)
            cuando = la_hora_de_la_foto(local.isoformat())
            if cuando is not None and cuando <= ahora + timedelta(days=2):
                return cuando.astimezone(timezone.utc)
    except Exception:                               # noqa: BLE001
        return None
    return None


def leer_las_noticias(html, ahora) -> list:
    """
    Las noticias del bloque de la pagina de un equipo de FF:
    `[{"titular", "publicada" (ISO UTC o None), "url"}]`. Solo se leen
    el texto del titular, la fecha y el enlace; nada se ejecuta. Vacio
    si no hay bloque o el HTML no se entiende. Nunca lanza.
    """
    salida = []
    try:
        if not isinstance(html, str) or not html:
            return []
        from bs4 import BeautifulSoup, SoupStrainer

        sopa = BeautifulSoup(html[:TAMANO_MAXIMO_HTML], "html.parser",
                             parse_only=SoupStrainer("a", class_="noticia"))
        vistos = set()
        for a in sopa.find_all("a", class_="noticia"):
            if len(salida) >= MAXIMO_NOTICIAS_POR_PAGINA:
                break
            h = a.find(class_="titular")
            titular = _texto_limpio(h.get_text(" ") if h else "")
            if not titular:
                continue
            url = _url_segura(a.get("href"))
            clave = url or titular
            if clave in vistos:
                continue
            vistos.add(clave)
            dia = a.select_one(".date .day")
            hora = a.select_one(".date .time")
            cuando = la_fecha_de_ff(dia.get_text() if dia else None,
                                    hora.get_text() if hora else None, ahora)
            salida.append({"titular": titular,
                           "publicada": cuando.isoformat() if cuando else None,
                           "url": url})
    except Exception:                               # noqa: BLE001
        return salida
    return salida


def en_la_ventana(publicada, ahora, horas=VENTANA_HORAS) -> bool:
    cuando = _cuando(publicada)
    if cuando is None:
        return False
    ahora = _utc(ahora)
    return ahora - timedelta(hours=horas) <= cuando <= ahora + timedelta(hours=1)


def _bajar(url: str) -> str:
    """Una pagina de FF, con tiempo de espera y tope de tamaño. Lanza si falla."""
    import requests

    from src.intelligence.futbolfantasy_provider import HEADERS

    trozos, total = [], 0
    with requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS, stream=True) as r:
        r.raise_for_status()
        for trozo in r.iter_content(65536):
            trozos.append(trozo)
            total += len(trozo)
            if total >= TAMANO_MAXIMO_HTML:
                break
    return b"".join(trozos)[:TAMANO_MAXIMO_HTML].decode("utf-8", errors="replace")


def las_noticias_de_los_equipos(equipos, ahora, fetch=None, *, maximo_paginas=MAXIMO_DE_PAGINAS,
                                segundos=SEGUNDOS_PARA_LAS_NOTICIAS) -> dict:
    """
    Una pagina por equipo (`{slug: {pid: nombre}}`), con los topes de
    arriba. `{"por_jugador": {pid: [noticia con "tipo"]}, "leidos":
    {slugs}, "sin_leer": [slugs], "errores": [...], "paginas": n}`.

    Un equipo sin leer deja a sus jugadores SIN la señal (no a cero):
    quien puntua lo distingue. Nunca lanza.
    """
    salida = {"por_jugador": {}, "leidos": set(), "sin_leer": [], "errores": [], "paginas": 0}
    try:
        fetch = fetch or _bajar
        empezo = time.monotonic()
        seguidos = 0
        for slug in sorted(_dict(equipos)):
            jugadores = _dict(_dict(equipos).get(slug))
            if (salida["paginas"] >= maximo_paginas
                    or time.monotonic() - empezo > segundos
                    or seguidos >= FALLOS_SEGUIDOS_PARA_PARAR):
                salida["sin_leer"].append(slug)
                continue
            if not re.match(r"^[a-z0-9-]{2,40}$", str(slug)):
                salida["sin_leer"].append(str(slug))
                continue
            salida["paginas"] += 1
            try:
                html = fetch(f"{FF_BASE}/laliga/equipos/{slug}")
            except Exception as error:              # noqa: BLE001
                seguidos += 1
                salida["sin_leer"].append(slug)
                salida["errores"].append(f"{slug}: {type(error).__name__}: {str(error)[:120]}")
                continue
            seguidos = 0
            noticias = leer_las_noticias(html, ahora)
            salida["leidos"].add(slug)
            indice = el_indice(jugadores)
            for n in noticias:
                for pid, tipo in clasificar_titular(n["titular"], indice).items():
                    if pid in jugadores:
                        salida["por_jugador"].setdefault(pid, []).append({**n, "tipo": tipo})
    except Exception as error:                      # noqa: BLE001
        salida["errores"].append(f"{type(error).__name__}: {error}")
    return salida


# ============================================================
# QUIEN ES NUEVO (puro)
# ============================================================

def el_mercado_anterior(propio, hoy, valoracion=None, escaparate=None) -> dict:
    """
    El mercado del ultimo dia apuntado ANTES de `hoy` (texto ISO).

    1. La linea DIA mas reciente de este libro (lleva el mercado entero).
    2. Si no hay: la valoracion (todos los vendedores) y el escaparate
       (los del Computer) de su ultimo dia anterior a `hoy`, juntos.
    3. Si tampoco: `ids` None (todos cuentan como nuevos).

    `{"ids": set | None, "dia": texto | None, "base": ...}`. Nunca lanza.
    """
    try:
        hoy = str(hoy)
        dias = [f for f in _lista(propio)
                if f.get("tipo") == "DIA" and str(f.get("dia_de_mercado") or "") < hoy
                and str(f.get("dia_de_mercado") or "")]
        if dias:
            ultima = max(dias, key=lambda f: str(f.get("dia_de_mercado")))
            mercado = _dict(ultima.get("mercado"))
            ids = {_int(x) for x in (mercado.get("computer") or []) + (mercado.get("managers") or [])}
            return {"ids": {x for x in ids if x is not None},
                    "dia": str(ultima.get("dia_de_mercado")), "base": "EL_INFORME"}

        candidatos = {}
        for f in _lista(valoracion):
            dia = str(f.get("dia") or "")
            if dia and dia < hoy and _int(f.get("id")) is not None:
                candidatos.setdefault(dia, set()).add(_int(f.get("id")))
        for f in _lista(escaparate):
            dia = str(f.get("dia_de_mercado") or "")
            if dia and dia < hoy:
                for j in _lista(f.get("players")):
                    if _int(j.get("id")) is not None:
                        candidatos.setdefault(dia, set()).add(_int(j.get("id")))
        if candidatos:
            dia = max(candidatos)
            return {"ids": candidatos[dia], "dia": dia, "base": "VALORACION_Y_ESCAPARATE"}
    except Exception:                               # noqa: BLE001
        pass
    return {"ids": None, "dia": None, "base": "SIN_DIA_ANTERIOR"}


def los_nuevos(hoy_ids, anterior_ids) -> list:
    """Los de hoy que no estaban. Sin mercado anterior, todos. Nunca lanza."""
    try:
        hoy = {x for x in (_int(i) for i in (hoy_ids or [])) if x is not None}
        if anterior_ids is None:
            return sorted(hoy)
        antes = {x for x in (_int(i) for i in anterior_ids) if x is not None}
        return sorted(hoy - antes)
    except Exception:                               # noqa: BLE001
        return []


# ============================================================
# LAS SEÑALES DE UN JUGADOR (puro: todo entra por argumento)
# ============================================================

def la_prensa_de(informe, pid, ahora) -> dict:
    """BAJA / DUDA / VUELVE de la prensa RSS en 72 h, sin sujeto ambiguo."""
    items = []
    try:
        ficha = _dict(_dict(_dict(informe).get("players")).get(str(pid)))
        for item in _lista(ficha.get("items")):
            if item.get("kind") not in ("BAJA", "DUDA", "VUELVE") or item.get("ambiguous_subject"):
                continue
            if not en_la_ventana(item.get("published_at") or item.get("seen_at"), ahora):
                continue
            items.append({"fuente": item.get("source"), "tipo": item.get("kind"),
                          "titular": _texto_limpio(item.get("headline") or item.get("quote"))})
    except Exception:                               # noqa: BLE001
        pass
    return {"baja": any(i["tipo"] in ("BAJA", "DUDA") for i in items), "items": items[:4]}


def lo_de_ff(entrada) -> dict | None:
    """Lo que el tablero de FF sabe de un jugador, compacto. None sin entrada."""
    e = _dict(entrada)
    if not e:
        return None
    jer = _dict(e.get("hierarchy"))
    disp = _dict(e.get("availability"))
    aus = _dict(e.get("absence"))
    return {
        "titular": _num(e.get("starter_probability")),
        "jerarquia": jer.get("label") if jer else None,
        "jerarquia_valor": _num(jer.get("value")) if jer else None,
        "minutos": e.get("minutes") if isinstance(e.get("minutes"), (int, float)) else None,
        "disponible": disp.get("code"),
        "puede_jugar": disp.get("can_play"),
        "ausencia": ({k: aus.get(k) for k in ("type", "days_out", "severity",
                                             "return_matchday", "matchdays_out")}
                     if aus else None),
    }


def lo_de_jp(intel) -> dict | None:
    i = _dict(intel)
    if not i:
        return None
    return {"nota": _num(i.get("jp_market_score")), "accion": i.get("intelligence_action"),
            "tip": i.get("tip"), "lesionado": i.get("injured"), "duda": i.get("doubt"),
            "editorial": _num(i.get("editorial_score")),
            "articulos": _int(i.get("editorial_signal_count"))}


def la_fila(pid, *, dia, at, vendedor, pide, ficha, equipo, ff, prensa, jp, noticias,
            noticias_leidas, jornadas, cambio_hist) -> dict:
    """La linea JUGADOR del libro, con sus dos notas. Nunca lanza."""
    ficha = _dict(ficha)
    precio = _int(ficha.get("price")) or _int(pide)
    incremento = _int(ficha.get("priceIncrement"))
    cambio = el_cambio_de_hoy(precio, incremento)
    c_fuente = "BIWENGER" if cambio is not None else None
    if cambio is None and cambio_hist is not None:
        cambio, c_fuente = cambio_hist, "HISTORICO"
    jugados = None
    if ficha:
        jugados = (_int(ficha.get("playedHome"), 0) or 0) + (_int(ficha.get("playedAway"), 0) or 0)
    noticias = [n for n in (noticias or []) if isinstance(n, dict)]
    recientes = [n for n in noticias if en_la_ventana(n.get("publicada"), at)]
    vuelta = (any(n.get("tipo") == "VUELTA" for n in recientes) if noticias_leidas else None)
    señales = {
        "precio": precio,
        "cambio_hoy_pct": cambio,
        "vuelta_ff": vuelta,
        "titular_ff": (ff or {}).get("titular"),
        "jugados": jugados,
        "jornadas": jornadas,
        "puntos": ficha.get("points"),
        "posicion": ficha.get("position"),
        "estado": ficha.get("status"),
        "prensa_baja": None if prensa is None else bool(prensa.get("baja")),
    }
    notas = puntuar(señales)
    faltan = [nombre for nombre, falta in (
        ("cambio_de_hoy", cambio is None), ("tablero_ff", ff is None),
        ("titular_ff", (ff or {}).get("titular") is None),
        ("noticias_ff", not noticias_leidas), ("prensa", prensa is None),
        ("ficha_del_catalogo", not ficha)) if falta]
    return {
        "tipo": "JUGADOR",
        "dia_de_mercado": dia,
        "at": _utc(at).isoformat(timespec="seconds"),
        "id": pid,
        "nombre": ficha.get("name"),
        "equipo": equipo,
        "posicion": _int(ficha.get("position")),
        "vendedor": vendedor,
        "precio": precio,
        "pide": _int(pide),
        "sube": notas["sube"],
        "puntua": notas["puntua"],
        "por_que": notas["por_que"],
        "terminos": los_terminos(señales),
        "senales": {
            "incremento": incremento,
            "c_fuente": c_fuente,
            "puntos": _int(ficha.get("points")),
            "estado": ficha.get("status"),
            "ff": ff,
            "jp": jp,
            "prensa": (prensa or {}).get("items") if prensa is not None else None,
            "noticias_ff": ([{"tipo": n.get("tipo"), "titular": n.get("titular"),
                              "publicada": n.get("publicada"), "url": n.get("url")}
                             for n in recientes[:MAXIMO_NOTICIAS_POR_JUGADOR]]
                            if noticias_leidas else None),
        },
        "faltan": faltan,
        "pesos": PESOS,
    }


def _el_cambio_del_historico(serie, ahora) -> float | None:
    """C desde el historico: el ultimo precio de hoy contra el de ayer."""
    try:
        from src.actions.la_rotacion import el_precio_del_dia, el_reset_del_dia, el_dia_de_mercado

        dia = el_dia_de_mercado(ahora)
        hoy = el_reset_del_dia(dia).timestamp()
        ayer = el_reset_del_dia(dia - timedelta(days=1)).timestamp()
        p_hoy = el_precio_del_dia(serie, hoy, _utc(ahora).timestamp() + 1)
        p_ayer = el_precio_del_dia(serie, ayer, hoy)
        if not p_hoy or not p_ayer:
            return None
        return (p_hoy / p_ayer - 1.0) * 100.0
    except Exception:                               # noqa: BLE001
        return None


# ============================================================
# EL LIBRO
# ============================================================

def _escribir(texto, ruta) -> None:
    (RAIZ / ruta).parent.mkdir(parents=True, exist_ok=True)
    (RAIZ / ruta).write_text(texto, encoding="utf-8")


def apuntar(lineas, ruta=None) -> bool:
    """Añade las lineas al libro (se guardan las ultimas
    `LINEAS_QUE_SE_GUARDAN`). True si se escribio. Nunca lanza."""
    try:
        nuevas = [json.dumps(f, ensure_ascii=False, separators=(",", ":"))
                  for f in lineas if isinstance(f, dict)]
        if not nuevas:
            return False
        try:
            viejas = [x for x in (RAIZ / (ruta or LIBRO)).read_text(encoding="utf-8").splitlines()
                      if x.strip()]
        except FileNotFoundError:
            viejas = []
        _escribir("\n".join((viejas + nuevas)[-LINEAS_QUE_SE_GUARDAN:]) + "\n", ruta or LIBRO)
        return True
    except Exception:                               # noqa: BLE001
        return False


def el_ultimo_informe(ruta=None, maximo=40) -> dict:
    """
    El ultimo dia apuntado, para el panel: los nuevos de ese dia de mas
    a menos SUBE. Solo lee el libro, y apagado ni eso (un informe de
    cuando estaba encendido seria viejo). Nunca lanza.
    """
    try:
        if not activa():
            return {"available": False, "activa": False, "jugadores": [],
                    "reason": f"Apagado: `{ENV}`."}
        filas = _leer_jsonl(ruta or LIBRO)
        dias = [f for f in filas if f.get("tipo") == "DIA"]
        if not dias:
            return {"available": False, "activa": activa(), "jugadores": [],
                    "reason": "Todavia no hay ningun informe apuntado."}
        ultimo = dias[-1]
        dia = ultimo.get("dia_de_mercado")
        jugadores = [f for f in filas if f.get("tipo") == "JUGADOR" and f.get("dia_de_mercado") == dia]
        jugadores.sort(key=lambda f: (_num(f.get("sube")) is None, -(_num(f.get("sube")) or 0.0)))
        return {
            "available": True,
            "activa": activa(),
            "dia_de_mercado": dia,
            "at": ultimo.get("at"),
            "base": ultimo.get("base"),
            "n_mercado": ultimo.get("n_mercado"),
            "n_nuevos": ultimo.get("n_nuevos"),
            "noticias": ultimo.get("noticias"),
            "pesos": ultimo.get("pesos"),
            "observador": True,
            "jugadores": [{"id": f.get("id"), "nombre": f.get("nombre"), "equipo": f.get("equipo"),
                           "vendedor": f.get("vendedor"), "precio": f.get("precio"),
                           "sube": f.get("sube"), "puntua": f.get("puntua"),
                           "por_que": (f.get("por_que") or [])[:4], "faltan": f.get("faltan")}
                          for f in jugadores[:maximo]],
        }
    except Exception as error:                      # noqa: BLE001
        return {"available": False, "activa": activa(), "jugadores": [],
                "reason": f"No se pudo leer el informe: {type(error).__name__}"}


# ============================================================
# EN CADA VUELTA
# ============================================================

def correr(*, ahora=None, snapshot=None, libro_ruta=None, tablero_ff=None, prensa=None,
           jp=None, historico=None, jornadas=None, valoracion=None, escaparate=None,
           fetch=None) -> dict:
    """
    El informe de esta mañana, si toca. Nunca lanza.

    Lo que no se pasa se lee de produccion: la ultima foto, el tablero
    de FF, el informe de prensa, el mercado de JP, el historico de
    precios, las jornadas disputadas, el libro de la valoracion y el del
    escaparate (solo si este libro no tiene dia anterior), y las paginas
    de FF con `_bajar`. Apagado, no lee ni escribe nada. Solo escribe
    en `libro_ruta` (por defecto, `LIBRO`).
    """
    salida = {"activa": activa(), "motivo": None, "dia_de_mercado": None, "nuevos": [],
              "jugadores": [], "escrito": False}
    try:
        if not salida["activa"]:
            salida["motivo"] = "APAGADO"
            return salida

        from src.actions.la_orden_del_gestor import leer_la_foto
        from src.actions.la_rotacion import el_dia_de_mercado, la_hora_de_la_foto, los_resets

        ahora = _utc(ahora)
        hoy = el_dia_de_mercado(ahora).isoformat()
        salida["dia_de_mercado"] = hoy
        ruta = libro_ruta or LIBRO
        propio = _leer_jsonl(ruta)

        # UNA VEZ POR DIA DE MERCADO.
        if any(f.get("tipo") == "DIA" and f.get("dia_de_mercado") == hoy for f in propio):
            salida["motivo"] = "YA_HECHO_HOY"
            return salida

        if snapshot is None:
            from src.actions.la_mejora_del_once import _la_ultima_foto

            snapshot = _la_ultima_foto()
        snapshot = _dict(snapshot)

        # LA FOTO TIENE QUE SER DE DESPUES DEL RESET DE HOY.
        foto_at = la_hora_de_la_foto(snapshot.get("timestamp"))
        ultimo_reset, _ = los_resets(ahora)
        salida["foto_at"] = foto_at.isoformat() if foto_at else None
        if foto_at is None:
            salida["motivo"] = "SIN_HORA_DE_LA_FOTO"
            return salida
        if foto_at < ultimo_reset + timedelta(minutes=MINUTOS_TRAS_EL_RESET):
            salida["motivo"] = "FOTO_DE_ANTES_DEL_RESET"
            return salida

        yo = _pid(_dict(_dict(snapshot.get("league")).get("user")))
        foto = leer_la_foto(snapshot, yo)
        computer = {k: v for k, v in _dict(foto.get("mercado")).items() if _int(k) is not None}
        managers = {k: v for k, v in _dict(foto.get("de_managers")).items() if _int(k) is not None}
        if not computer and not managers:
            salida["motivo"] = "MERCADO_VACIO"
            return salida

        # QUIEN ES NUEVO.
        if not any(f.get("tipo") == "DIA" for f in propio) and (valoracion is None or escaparate is None):
            from src.intelligence import libro_de_la_valoracion, libro_del_escaparate

            valoracion = _leer_jsonl(libro_de_la_valoracion.LIBRO) if valoracion is None else valoracion
            escaparate = _leer_jsonl(libro_del_escaparate.LIBRO) if escaparate is None else escaparate
        anterior = el_mercado_anterior(propio, hoy, valoracion, escaparate)
        nuevos = los_nuevos(set(computer) | set(managers), anterior["ids"])
        salida["nuevos"] = nuevos
        salida["base"] = anterior["base"]

        # LO QUE YA TRAJO LA VUELTA.
        catalogo = _dict(_dict(_dict(snapshot.get("catalog")).get("data")).get("players"))
        equipos_cat = _dict(_dict(_dict(snapshot.get("catalog")).get("data")).get("teams"))
        if nuevos and tablero_ff is None:
            from src.intelligence.futbolfantasy_provider import BOARD_FILE

            tablero_ff = _leer_json(BOARD_FILE, None)
        if nuevos and prensa is None:
            from src.intelligence.scout.press import REPORT_FILE

            prensa = _leer_json(REPORT_FILE, None)
        if nuevos and jp is None:
            from src.intelligence.jornada_perfecta_market_provider import DATA_FILE

            jp = _leer_json(DATA_FILE, None)
        if nuevos and jornadas is None:
            from src.actions.la_rotacion import las_jornadas_jugadas

            jornadas = las_jornadas_jugadas(catalogo)

        ff_por_id = {}
        for e in _lista(_dict(tablero_ff).get("players")):
            if _int(e.get("player_id")) is not None:
                ff_por_id[_int(e.get("player_id"))] = e
        jp_por_id = {}
        try:
            if _dict(jp).get("players"):
                from src.intelligence.jornada_perfecta_market_intelligence import (
                    build_all_jp_market_intelligence, intelligence_by_biwenger_id,
                )

                jp_por_id = intelligence_by_biwenger_id(
                    {"players": build_all_jp_market_intelligence(_dict(jp))})
        except Exception:                           # noqa: BLE001
            jp_por_id = {}

        # LAS NOTICIAS: una pagina por equipo de algun nuevo.
        from src.intelligence.futbolfantasy_provider import team_slug

        def _equipo(pid):
            ficha = _dict(catalogo.get(str(pid)))
            nombre = _dict(equipos_cat.get(str(ficha.get("teamID")))).get("name")
            return ficha.get("teamID"), nombre, (team_slug(nombre) if nombre else None)

        por_slug = {}
        for pid in nuevos:
            team_id, _, slug = _equipo(pid)
            if slug and team_id is not None:
                por_slug.setdefault(slug, team_id)
        equipos = {}
        for slug, team_id in por_slug.items():
            equipos[slug] = {_int(k): _dict(f).get("name") for k, f in catalogo.items()
                             if _int(k) is not None and _dict(f).get("teamID") == team_id
                             and _dict(f).get("name")}
        noticias = (las_noticias_de_los_equipos(equipos, ahora, fetch) if equipos
                    else {"por_jugador": {}, "leidos": set(), "sin_leer": [], "errores": [],
                          "paginas": 0})

        historico_players = None
        filas = []
        for pid in nuevos:
            ficha = _dict(catalogo.get(str(pid)))
            team_id, nombre_equipo, slug = _equipo(pid)
            cambio_hist = None
            if el_cambio_de_hoy(ficha.get("price"), ficha.get("priceIncrement")) is None:
                if historico_players is None:
                    if historico is None:
                        from src.actions.la_rotacion import HISTORICO

                        historico = _leer_json(HISTORICO, {})
                    historico_players = _dict(_dict(historico).get("players"))
                cambio_hist = _el_cambio_del_historico(historico_players.get(str(pid)), ahora)
            vendedor = "COMPUTER" if pid in computer else "MANAGER"
            pide = computer.get(pid) if pid in computer else _dict(managers.get(pid)).get("precio")
            filas.append(la_fila(
                pid, dia=hoy, at=ahora, vendedor=vendedor, pide=pide, ficha=ficha,
                equipo=nombre_equipo, ff=lo_de_ff(ff_por_id.get(pid)),
                prensa=la_prensa_de(prensa, pid, ahora) if prensa is not None else None,
                jp=lo_de_jp(jp_por_id.get(pid)),
                noticias=noticias["por_jugador"].get(pid),
                noticias_leidas=slug in noticias["leidos"], jornadas=jornadas,
                cambio_hist=cambio_hist))

        dia_linea = {
            "tipo": "DIA",
            "dia_de_mercado": hoy,
            "at": ahora.isoformat(timespec="seconds"),
            "foto_at": foto_at.isoformat(timespec="seconds"),
            "mercado": {"computer": sorted(computer), "managers": sorted(managers)},
            "n_mercado": len(computer) + len(managers),
            "dia_anterior": anterior["dia"],
            "base": anterior["base"],
            "nuevos": nuevos,
            "n_nuevos": len(nuevos),
            "jornadas": jornadas,
            "fuentes": {
                "tablero_ff": _dict(tablero_ff).get("updated_at") if tablero_ff else None,
                "prensa": _dict(prensa).get("generated_at") if prensa else None,
                "jp": _dict(jp).get("updated_at") if jp else None,
            },
            "noticias": {"paginas": noticias["paginas"], "leidas": sorted(noticias["leidos"]),
                         "sin_leer": noticias["sin_leer"], "errores": noticias["errores"][:10]},
            "pesos": PESOS,
            "observador": True,
        }
        salida["jugadores"] = filas
        salida["dia"] = dia_linea
        salida["escrito"] = apuntar([dia_linea] + filas, ruta)
        salida["motivo"] = "APUNTADO" if salida["escrito"] else "NO_SE_PUDO_ESCRIBIR"

    except Exception as error:                      # noqa: BLE001
        salida["motivo"] = f"ERROR: {type(error).__name__}: {error}"
    return salida


def el_parte(r) -> list:
    """Las lineas de la vuelta, para el log. Nunca lanza."""
    lineas = []
    try:
        r = _dict(r)
        lineas.append(f"  {r.get('motivo')} (dia de mercado {r.get('dia_de_mercado')})")
        d = _dict(r.get("dia"))
        if d:
            n = _dict(d.get("noticias"))
            lineas.append(f"  Mercado {d.get('n_mercado')}, nuevos {d.get('n_nuevos')} "
                          f"(contra {d.get('dia_anterior')}, {d.get('base')}); paginas de FF "
                          f"{n.get('paginas')}, sin leer {n.get('sin_leer') or '-'}")
            for e in n.get("errores") or []:
                lineas.append(f"      {e}")
        filas = sorted(_lista(r.get("jugadores")),
                       key=lambda f: (_num(f.get("sube")) is None, -(_num(f.get("sube")) or 0.0)))
        for f in filas:
            lineas.append(f"  {str(f.get('nombre') or f.get('id'))[:22]:22s} {f.get('vendedor'):8s} "
                          f"{f.get('precio') or 0:>11,} sube {f.get('sube')!s:>6} "
                          f"puntua {f.get('puntua')!s:>5}")
            for motivo in (f.get("por_que") or [])[:4]:
                lineas.append(f"      {motivo}")
        lineas.append("  (Solo observa: ninguna puja lee este informe.)")
    except Exception as error:                      # noqa: BLE001
        lineas.append(f"  (el informe no se pudo escribir: {type(error).__name__})")
    return lineas


def main() -> int:
    r = correr()
    print("=" * 100)
    print("EL INFORME DE LA MAÑANA")
    print("=" * 100)
    for linea in el_parte(r):
        print(linea)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
