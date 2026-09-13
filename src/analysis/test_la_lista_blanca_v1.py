"""
Ninguna clave publicada se pierde por el camino.

SINTOMA (13/09/2026, noche)

    Dos cuadros construidos, medidos y con guardias propias
    salieron VACIOS en la pantalla del dueño. `todaLaLiga` viajaba
    con `available: true` y 570 jugadores dentro.

CAUSA

    `normalizeStatus()` es una LISTA BLANCA: copia clave por
    clave y tira todo lo que no este nombrado. El dato llegaba al
    navegador, entraba en `raw` y moria ahi.

    Y con el moria `reason`, asi que el cuadro ni siquiera podia
    decir por que estaba vacio: se veia igual que una averia de
    datos. Una tarde buscando en el sitio equivocado.

CONSECUENCIA

    Es un fallo que NO AVISA. No hay excepcion, ni consola, ni
    build roto: la telemetria publica bien, el lector calla, y el
    cuadro enseña su mensaje de "no hay datos" como si el motor
    no hubiera calculado nada.

    Cada bloque nuevo que se publique muere igual mientras nadie
    se acuerde de nombrarlo aqui. Acordarse no es un mecanismo.

LO QUE VIGILA

    Que toda clave de primer nivel que `build_dashboard_state`
    publica este nombrada en `normalizeStatus`. Si una no se
    pinta a proposito, va en `NO_SE_PINTAN` CON SU MOTIVO: una
    lista de excepciones sin motivos es donde se esconde el fallo
    de mañana.

REGLA 23

    No lee `data/` ni ningun estado externo: solo el codigo del
    repositorio. Por eso las claves se sacan del fichero fuente y
    no de un `status.json`, que ademas seria el de una foto
    concreta y no diria nada del dia que se añada la siguiente.
"""

from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).parents[2]

TELEMETRIA = RAIZ / "src" / "telemetry" / "dashboard_state.py"

LECTOR = RAIZ / "dashboard-v8" / "src" / "lib" / "status.js"


# CLAVES QUE SE PUBLICAN Y NO SE PINTAN, CON SU MOTIVO.
#
#     Publicar sin pintar es legitimo: hay datos que estan ahi
#     para el que lea el JSON a mano o para una pantalla futura.
#     Lo que no es legitimo es que nadie sepa cual es cual.
#
#     Si añades una aqui, escribe POR QUE. El dia que alguien
#     borre el motivo, esta lista vuelve a ser un cajon.
NO_SE_PINTAN = {
    # El estado del jugador franquicia. Hoy sale NO_FRANCHISE y
    # no hay ningun cuadro que lo enseñe; se publica para poder
    # mirarlo en el JSON cuando se active.
    "franchise": "sin cuadro todavia; se mira en el JSON",

    # El orden de preferencia interno del motor. La pantalla
    # enseña el resultado (el orden de las filas), no la lista.
    "preferencia": "la pantalla enseña el orden, no la lista",

    # El libro de publicaciones del escaparate. Lo que se ve es
    # `listings`, que es la foto de Biwenger; esto es nuestra
    # memoria de lo que apuntamos.
    "publicacion": "memoria propia; la pantalla enseña la foto",

    # La segunda opinion a horizonte de temporada. Vive en
    # AUDITORIA a traves de `seasonHorizon`, con otro nombre.
    "sombra": "se pinta via `seasonHorizon`",
}


def _bloque_equilibrado(texto: str, desde: int) -> str:
    """
    El contenido de un `{...}`, contando llaves.

    Hace falta contar: dentro hay diccionarios anidados, y una
    regex que corte en la primera llave de cierre se lleva medio
    diccionario.
    """

    inicio = texto.index("{", desde)

    hondo = 0

    for i in range(inicio, len(texto)):

        if texto[i] == "{":
            hondo += 1

        elif texto[i] == "}":
            hondo -= 1

            if hondo == 0:
                return texto[inicio + 1 : i]

    raise AssertionError("el diccionario no cierra")


def claves_publicadas() -> set:
    """
    Las claves de primer nivel del estado que se publica.

    Dos formas, y las dos cuentan:

        dashboard = { "x": ... }        el literal
        dashboard["y"] = ...            lo que se añade despues

    La segunda existe de verdad —`consistency` se añade al final,
    cuando ya se puede comprobar contra el resto— y olvidarla
    dejaria un agujero justo del tamaño de esa clave.
    """

    fuente = TELEMETRIA.read_text(encoding="utf-8")

    bloque = _bloque_equilibrado(
        fuente, fuente.index("    dashboard = {")
    )

    # Primer nivel = ocho espacios de sangria. Las anidadas van
    # mas adentro y no son claves del estado.
    claves = set(
        re.findall(
            r'(?m)^        "([A-Za-z_][A-Za-z0-9_]*)":', bloque
        )
    )

    claves |= set(
        re.findall(
            r'dashboard\[\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\]\s*=',
            fuente,
        )
    )

    return claves


def claves_recogidas() -> set:
    """
    Lo que `normalizeStatus` nombra de `raw`.

    Se leen las dos formas —`raw.x` y `raw["x"]`— porque las dos
    valen y mezclarlas es normal.
    """

    lector = LECTOR.read_text(encoding="utf-8")

    return set(
        re.findall(r"raw\.([A-Za-z_][A-Za-z0-9_]*)", lector)
    ) | set(
        re.findall(
            r'raw\[\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*\]', lector
        )
    )


def test_ninguna_clave_publicada_se_pierde() -> None:
    """
    LO QUE SE PUBLICA, SE RECOGE.

    Y si no se recoge a proposito, consta con su motivo. La
    alternativa —acordarse— ya fallo dos veces en un dia.
    """

    publicadas = claves_publicadas()

    recogidas = claves_recogidas()

    # REGLA 24: con cualquiera de las dos listas vacia, esto
    # pasaria siempre y no probaria nada.
    assert len(publicadas) >= 40, (
        f"solo se han leido {len(publicadas)} claves publicadas: "
        f"el extractor no esta mirando donde dice"
    )

    assert len(recogidas) >= 40, (
        f"solo se han leido {len(recogidas)} claves recogidas: "
        f"el extractor no esta mirando `status.js`"
    )

    perdidas = sorted(
        clave
        for clave in publicadas
        if clave not in recogidas and clave not in NO_SE_PINTAN
    )

    assert not perdidas, (
        f"{len(perdidas)} clave(s) se publican y `normalizeStatus`"
        f" no las nombra: el dato llega al navegador, entra en "
        f"`raw` y muere ahi. El cuadro que las lea saldra vacio "
        f"sin decir por que.\n"
        + "\n".join(f"   raw.{c}" for c in perdidas)
        + "\n\nO se recogen en `dashboard-v8/src/lib/status.js`, "
        "o se apuntan en `NO_SE_PINTAN` con su motivo."
    )


def test_las_excepciones_siguen_existiendo() -> None:
    """
    UNA EXCEPCION DE UNA CLAVE QUE YA NO SE PUBLICA ES BASURA.

    Y peor que basura: el dia que alguien vuelva a publicar una
    clave con ese nombre, entraria en la lista de "no se pinta a
    proposito" sin que nadie lo haya decidido.

    Cada excepcion, ademas, con su motivo escrito.
    """

    publicadas = claves_publicadas()

    assert publicadas, "no se han leido las claves publicadas"

    sobran = sorted(
        clave
        for clave in NO_SE_PINTAN
        if clave not in publicadas
    )

    assert not sobran, (
        f"estas excepciones son de claves que ya no se publican: "
        f"{sobran}. Se quitan de `NO_SE_PINTAN`, o el dia que "
        f"alguien reutilice el nombre entraria sola."
    )

    sin_motivo = sorted(
        clave
        for clave, motivo in NO_SE_PINTAN.items()
        if not (motivo or "").strip()
    )

    assert not sin_motivo, (
        f"estas excepciones no dicen por que: {sin_motivo}. Una "
        f"lista de excepciones sin motivos es donde se esconde "
        f"el fallo de mañana."
    )


def test_los_cuadros_que_ya_fallaron_siguen_enchufados() -> None:
    """
    LOS DOS QUE MURIERON AQUI, CON NOMBRE Y APELLIDO.

    `todaLaLiga` y `loNuestroALaVenta` salieron vacios el 13/09
    por esta funcion. Quedan clavados en una guardia para que, si
    alguien limpia `normalizeStatus`, la verja lo diga antes que
    el dueño.
    """

    recogidas = claves_recogidas()

    for clave in ("todaLaLiga", "loNuestroALaVenta"):
        assert clave in recogidas, (
            f"`{clave}` ha vuelto a desaparecer del lector: su "
            f"cuadro saldra vacio con el dato publicado, igual "
            f"que el 13/09"
        )


TESTS = [
    test_ninguna_clave_publicada_se_pierde,
    test_las_excepciones_siguen_existiendo,
    test_los_cuadros_que_ya_fallaron_siguen_enchufados,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(
        f"LA LISTA BLANCA V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
