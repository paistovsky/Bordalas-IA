"""
Que guardias de la verja dependen de algo que no controlan.

EL INCIDENTE QUE LO PIDE (08/09/2026)

    `test_ojeador_prensa_v1` se puso rojo un martes a las 17:00.
    Nadie habia tocado nada: su feed de mentira llevaba
    `pubDate` fijo del 05/09 y la funcion leia la hora REAL.
    Con `MAX_ITEM_AGE_HOURS = 72`, el fixture cumplio tres dias
    y cuatro pruebas cayeron de golpe.

    Es el peor tipo de rojo: no falla cuando alguien rompe algo,
    falla un dia cualquiera. Y el que lo mire buscara el fallo
    en su propio cambio, que es justo donde no esta.

LA REGLA, AMPLIADA

    Teniamos "ninguna guardia lee `data/`". Lo correcto es:

        NINGUNA GUARDIA LEE ESTADO EXTERNO
        —ni el disco, ni la red, ni el reloj—.
        Si necesita una hora o un fichero, se los pasan.

QUE HACE ESTO

    Recorre las guardias que declara `run_validation_gate.py` y
    marca, con `ast`, tres cosas distintas:

        RELOJ    `datetime.now`, `time.time`, `date.today`...
        DISCO    rutas al estado o a snapshots
        RED      `requests`, `session.get`, clientes

    Y separa lo urgente de lo demas: una guardia que lee el
    reloj Y compara contra una fecha escrita a mano es una bomba
    de relojeria. Una que lee el reloj para sellar un fichero
    temporal, no.

QUE NO HACE

    No juzga solo: marca candidatos con su linea para que un
    humano decida. Un escaner que dijera "esta bien" sin mirar
    seria justo el genero de dato que este proyecto persigue.

COMO SE USA

    python -m scripts.guardias_que_leen_el_mundo
"""

from __future__ import annotations

import ast
import re

from pathlib import Path


RAIZ = Path(__file__).parent.parent

PUERTA = RAIZ / "scripts" / "run_validation_gate.py"


# ============================================================
# QUE SE BUSCA
# ============================================================


# El reloj de pared. Cualquiera de estas SIN argumento fijo
# significa "esta prueba depende de cuando se ejecute".
RELOJ = {
    "now",
    "today",
    "utcnow",
    "time",
    "monotonic",
    "fromtimestamp",
    "timestamp",
}


# Lo que de verdad importa: una fecha escrita a mano en el
# fichero. Reloj + fecha fija = bomba de relojeria, porque la
# distancia entre las dos crece sola.
FECHA_ESCRITA = re.compile(
    r"\b20\d{2}[-/ ]?(0[1-9]|1[0-2])[-/ ]?([0-2]\d|3[01])\b"
    r"|\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s"
    r"|datetime\(\s*20\d{2}\s*,"
)


# El disco. `ESTADO` se parte para que este fichero no se
# denuncie a si mismo.
ESTADO = "dat" + "a"

DISCO = {
    ESTADO + "/",
    ESTADO + "\\\\",
    "snapshot_",
    "get_latest_snapshot",
    "load_raw_snapshot",
}


# La red.
RED = {
    "requests",
    "urlopen",
    "BiwengerClient",
    "cliente_del_ciclo",
    "biwenger.as.com",
}


def guardias_de_la_puerta() -> list[str]:
    """Los modulos que la verja declara, en su orden."""

    try:
        fuente = PUERTA.read_text(encoding="utf-8")

        return re.findall(r'"(src\.[A-Za-z0-9_.]+)"', fuente)

    except Exception:                               # noqa: BLE001
        return []


def _ruta_de(modulo: str) -> Path:
    return RAIZ / (modulo.replace(".", "/") + ".py")


def _docstrings(arbol: ast.AST) -> set:
    """
    Los docstrings quedan fuera: uno que EXPLICA el fallo no lo
    comete, y estos lo explican.
    """

    fuera = set()

    for nodo in ast.walk(arbol):

        if not isinstance(
            nodo,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            continue

        cuerpo = getattr(nodo, "body", None) or []

        if (
            cuerpo
            and isinstance(cuerpo[0], ast.Expr)
            and isinstance(cuerpo[0].value, ast.Constant)
            and isinstance(cuerpo[0].value.value, str)
        ):
            fuera.add(id(cuerpo[0].value))

    return fuera


# ============================================================
# EL PECADO NO ES LLAMAR AL RELOJ: ES NO PASAR LA HORA
# ============================================================
#
#     La primera version de este escaner buscaba
#     `datetime.now()` dentro de las guardias, y dio LIMPIA a
#     `test_ojeador_prensa_v1` — la unica que sabemos que
#     exploto sola.
#
#     Y con razon: esa guardia NUNCA llama al reloj. Llama a
#     `press.build_press_report(...)` sin pasar `now`, y es
#     PRODUCCION la que mira la hora. El pecado es de omision.
#
#     Un escaner que no detecta el unico incidente que existe no
#     vale para nada, asi que se busca lo que de verdad pasa:
#     una guardia que llama a una funcion que ACEPTA la hora y
#     no se la da.
PARAMETROS_DE_HORA = {
    "now",
    "ahora",
    "now_ts",
    "ahora_ts",
    "now_iso",
    "cuando",
    "at",
}


def funciones_que_aceptan_la_hora() -> dict:
    """
    `{nombre: parametro}` de todo `src/` que no sea guardia.

    Se construye leyendo el codigo, no a mano: el dia que
    alguien añada una funcion con `now=None`, entra sola.
    """

    encontradas = {}

    try:
        for ruta in (RAIZ / "src").rglob("*.py"):

            if ruta.name.startswith("test_"):
                continue

            try:
                arbol = ast.parse(
                    ruta.read_text(encoding="utf-8")
                )

            except Exception:                       # noqa: BLE001
                continue

            for nodo in ast.walk(arbol):

                if not isinstance(
                    nodo,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                ):
                    continue

                argumentos = nodo.args

                nombres = [
                    a.arg
                    for a in (
                        list(argumentos.args)
                        + list(argumentos.kwonlyargs)
                    )
                ]

                for nombre in nombres:

                    if nombre in PARAMETROS_DE_HORA:
                        encontradas[nodo.name] = nombre
                        break

        return encontradas

    except Exception:                               # noqa: BLE001
        return {}


def _hora_omitida(nodo: ast.Call, aceptan: dict):
    """
    La llamada es a una funcion que acepta la hora y no se la
    pasa, o se la pasa como `None`.

    `None` explicito cuenta igual: `now=None` acaba en
    `datetime.now()` dentro.
    """

    funcion = nodo.func

    nombre = getattr(funcion, "attr", None) or getattr(
        funcion, "id", None
    )

    if nombre not in aceptan:
        return None

    parametro = aceptan[nombre]

    for clave in nodo.keywords:

        if clave.arg != parametro:
            continue

        # Se la pasa. Si es `None` pelado, no cuenta.
        if (
            isinstance(clave.value, ast.Constant)
            and clave.value.value is None
        ):
            return f"{nombre}({parametro}=None)"

        return None

    return f"{nombre}() sin {parametro}"


def _llamada_al_reloj(nodo: ast.Call) -> str | None:
    """
    `datetime.now()` SIN argumentos. Con argumentos es una fecha
    construida a mano, que es justo lo contrario del problema.
    """

    funcion = nodo.func

    nombre = getattr(funcion, "attr", None) or getattr(
        funcion, "id", None
    )

    if nombre not in RELOJ:
        return None

    # `datetime(2026, 9, 5)` o `fromtimestamp(1788600000)` son
    # deterministas: llevan el instante dentro.
    if nodo.args or nodo.keywords:
        return None

    return str(nombre)


def analizar(modulo: str, aceptan_la_hora: dict | None = None) -> dict:
    """
    `{modulo, reloj, disco, red, fechas, veredicto, por_que}`.

    Forma fija. Nunca lanza.
    """

    vacio = {
        "modulo": modulo,
        "existe": False,
        "reloj": [],
        "omitida": [],
        "disco": [],
        "red": [],
        "fechas": 0,
        "veredicto": "NO_SE_PUDO_LEER",
        "por_que": None,
    }

    try:
        ruta = _ruta_de(modulo)

        if not ruta.exists():
            return vacio

        fuente = ruta.read_text(encoding="utf-8")

        arbol = ast.parse(fuente)

        fuera = _docstrings(arbol)

        reloj = []
        disco = []
        red = []
        omitida = []

        aceptan = aceptan_la_hora or {}

        for nodo in ast.walk(arbol):

            if isinstance(nodo, ast.Call):

                nombre = _llamada_al_reloj(nodo)

                if nombre:
                    reloj.append(
                        f"{nombre}() linea {nodo.lineno}"
                    )

                falta = _hora_omitida(nodo, aceptan)

                if falta:
                    omitida.append(
                        f"{falta} linea {nodo.lineno}"
                    )

            if isinstance(nodo, ast.Constant) and isinstance(
                nodo.value, str
            ):

                if id(nodo) in fuera:
                    continue

                for aguja in DISCO:
                    if aguja in nodo.value:
                        disco.append(
                            f"{aguja!r} linea {nodo.lineno}"
                        )
                        break

                for aguja in RED:
                    if aguja in nodo.value:
                        red.append(
                            f"{aguja!r} linea {nodo.lineno}"
                        )
                        break

            if isinstance(nodo, (ast.Import, ast.ImportFrom)):

                texto = ast.unparse(nodo)

                for aguja in RED:
                    if aguja in texto:
                        red.append(
                            f"import {aguja} linea {nodo.lineno}"
                        )
                        break

        # Las fechas escritas a mano, en el fichero entero: si
        # hay reloj Y fechas fijas, la distancia entre las dos
        # crece sola.
        fechas = len(FECHA_ESCRITA.findall(fuente))

        veredicto, por_que = _juzgar(
            reloj, omitida, disco, red, fechas
        )

        return {
            "modulo": modulo,
            "existe": True,
            "reloj": sorted(set(reloj)),
            "omitida": sorted(set(omitida)),
            "disco": sorted(set(disco)),
            "red": sorted(set(red)),
            "fechas": fechas,
            "veredicto": veredicto,
            "por_que": por_que,
        }

    except Exception as error:                      # noqa: BLE001
        return {
            **vacio,
            "existe": True,
            "por_que": f"{type(error).__name__}: {error}",
        }


def _juzgar(reloj, omitida, disco, red, fechas) -> tuple:
    """
    Urgente es solo lo que puede ponerse rojo SOLO.

    LA FIRMA DE UNA BOMBA

        El reloj de pared -leido aqui o dentro de la funcion a
        la que no se le pasa la hora- CONTRA una fecha escrita a
        mano en el fichero. La distancia entre las dos crece
        cada dia hasta cruzar algun liston, y ese dia la
        guardia se pone roja sin que nadie haya tocado nada.

        Es exactamente lo que le paso a
        `test_ojeador_prensa_v1` el 08/09 a las 17:00.

    Lo demas -leer disco, importar la red- es deuda, pero no
    explota sin que nadie toque nada.
    """

    if omitida and fechas:
        return (
            "BOMBA_DE_RELOJERIA",
            (
                f"no pasa la hora en {len(omitida)} llamada(s) "
                f"-la lee produccion- y tiene {fechas} fecha(s) "
                f"escritas a mano: la distancia entre las dos "
                f"crece sola"
            ),
        )

    if reloj and fechas:
        return (
            "BOMBA_DE_RELOJERIA",
            (
                f"lee el reloj de pared ({len(reloj)} sitios) y "
                f"tiene {fechas} fecha(s) escritas a mano: la "
                f"distancia entre las dos crece sola"
            ),
        )

    if omitida:
        return (
            "HORA_OMITIDA_SIN_FECHA_FIJA",
            (
                f"no pasa la hora en {len(omitida)} llamada(s), "
                f"pero no hay fechas fijas contra las que "
                f"chocar: revisar, probablemente inofensivo"
            ),
        )

    if reloj:
        return (
            "RELOJ_SIN_FECHA_FIJA",
            (
                f"lee el reloj ({len(reloj)} sitios) pero no hay "
                f"fechas fijas con las que compararse: revisar, "
                f"probablemente inofensivo"
            ),
        )

    if disco:
        return (
            "LEE_DISCO",
            (
                f"{len(disco)} referencia(s) al estado: no "
                f"explota sola, pero depende de lo que haya en "
                f"la maquina"
            ),
        )

    if red:
        return (
            "TOCARIA_LA_RED",
            (
                f"{len(red)} referencia(s) a la red: revisar que "
                f"esten todas sustituidas"
            ),
        )

    return ("LIMPIA", None)


ORDEN = [
    "BOMBA_DE_RELOJERIA",
    "HORA_OMITIDA_SIN_FECHA_FIJA",
    "RELOJ_SIN_FECHA_FIJA",
    "LEE_DISCO",
    "TOCARIA_LA_RED",
    "NO_SE_PUDO_LEER",
    "LIMPIA",
]


def main() -> None:

    modulos = guardias_de_la_puerta()

    print()
    print("=" * 74)
    print("GUARDIAS QUE DEPENDEN DE ALGO QUE NO CONTROLAN")
    print("=" * 74)
    print()
    print(f"  Guardias en la verja: {len(modulos)}")

    aceptan = funciones_que_aceptan_la_hora()

    print(
        f"  Funciones de produccion que aceptan la hora: "
        f"{len(aceptan)}"
    )

    informes = [analizar(m, aceptan) for m in modulos]

    por_veredicto = {}

    for informe in informes:
        por_veredicto.setdefault(
            informe["veredicto"], []
        ).append(informe)

    print()
    print("  RESUMEN")
    print("  " + "-" * 60)

    for veredicto in ORDEN:

        cuantas = len(por_veredicto.get(veredicto, []))

        if cuantas:
            print(f"  {veredicto:<24}{cuantas:>4}")

    for veredicto in ORDEN:

        grupo = por_veredicto.get(veredicto) or []

        if not grupo or veredicto == "LIMPIA":
            continue

        print()
        print("=" * 74)
        print(veredicto)
        print("=" * 74)

        for informe in grupo:

            print()
            print(f"  {informe['modulo'].split('.')[-1]}")
            print(f"    {informe['por_que']}")

            for etiqueta, cosas in (
                ("HORA OMITIDA", informe["omitida"]),
                ("reloj", informe["reloj"]),
                ("disco", informe["disco"]),
                ("red", informe["red"]),
            ):
                for cosa in cosas[:4]:
                    print(f"      {etiqueta}: {cosa}")

                if len(cosas) > 4:
                    print(
                        f"      {etiqueta}: ...y "
                        f"{len(cosas) - 4} mas"
                    )

    print()
    print("=" * 74)
    print(
        f"  LIMPIAS: {len(por_veredicto.get('LIMPIA', []))} "
        f"de {len(modulos)}"
    )
    print("=" * 74)


if __name__ == "__main__":
    main()
