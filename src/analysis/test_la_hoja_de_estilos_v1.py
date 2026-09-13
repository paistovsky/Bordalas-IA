"""
Toda clase que la pantalla emite existe en la hoja de estilos.

SINTOMA (12 y 13/09/2026)

    En QUIEN LO VENDE, el Computer y un rival salian los dos en
    morado. No era un error de color: la clase `.comp` existia y
    la del Computer en ESTE cuadro no, asi que el texto heredaba
    el morado del contenedor.

    Dos dias seguidos con lo mismo. El cuadro de la liga se monto
    sin NUEVE de sus clases y salia en texto plano: `i-top`,
    `i-chollo`, `i-nada`, `i-nuestro`, `pos-d`, `neg-d`, `ref`,
    `res` y las de cuadrar o no cuadrar.

CAUSA

    Una clase que no existe no da error en ninguna parte. El
    navegador no avisa, la consola no dice nada y la pantalla se
    pinta: simplemente hereda lo que haya encima. El fallo es
    INVISIBLE en todas las herramientas menos en el ojo del dueño.

CONSECUENCIA

    La regla de la casa es que un dato que no se sabe se DICE. Un
    indicador que se pinta del color equivocado dice otra cosa —y
    dice algo, que es peor que no decir nada: "esto se puede
    comprar" y "esto es el escaparate de otro" se veian iguales.

DOCTRINA 47

    Una clase emitida que no existe en la hoja es una mentira
    silenciosa. Se caza aqui, no en la pantalla del dueño.

LO QUE NO MIRA

    Las clases que vienen de Tailwind y las de utilidad de la
    propia hoja. Se listan en `DE_FUERA` con su motivo.

REGLA 23

    No lee estado externo: solo los ficheros del repositorio.
"""

from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).parents[2]

FUENTE = RAIZ / "dashboard-v8" / "src"

HOJA = FUENTE / "styles.css"


# CLASES QUE NO TIENEN QUE ESTAR EN LA HOJA, y por que.
#
#     Cada una con su motivo escrito. Una lista de excepciones
#     sin motivos se convierte en el sitio donde se esconde el
#     fallo de mañana.
DE_FUERA = {
    # Tailwind las genera al compilar; no estan escritas a mano.
    "flex", "grid", "hidden", "block", "inline", "relative",
    "absolute", "fixed", "sticky", "truncate", "uppercase",

    # Vienen del `@import "tailwindcss"` de la primera linea.
    "container", "sr-only",
}

# Prefijos de utilidad de Tailwind: `mt-2`, `text-xs`, `w-full`.
DE_TAILWIND = re.compile(
    r"^(m|p)(t|b|l|r|x|y)?-|"
    r"^(text|bg|border|w|h|min|max|gap|flex|grid|col|row|"
    r"justify|items|self|space|rounded|shadow|opacity|z|"
    r"overflow|font|leading|tracking)-"
)


# Un literal de texto de JavaScript: comilla doble, simple o
# invertida. Se arma con `chr()` porque las tres juntas no caben
# en ninguna forma de cadena de Python sin escapar algo.
COMILLAS = (
    "[" + chr(34) + chr(39) + chr(96) + "]"
    "([^" + chr(34) + chr(39) + chr(96) + "]*)"
    "[" + chr(34) + chr(39) + chr(96) + "]"
)


def _clases_de_la_hoja() -> set:
    """
    Las clases DEFINIDAS en la hoja.

    Se quitan los comentarios antes de mirar: esta casa lleva
    ocho guardias puestas rojas por el texto que las explicaba, y
    un comentario que menciona `.i-top` no lo define.
    """

    css = HOJA.read_text(encoding="utf-8")

    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)

    return set(re.findall(r"\.([A-Za-z][A-Za-z0-9_-]*)", css))


def _sin_comentarios(texto: str) -> str:
    texto = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", texto)


def _expresiones_de_clase(texto: str) -> list:
    """
    Cada `className=...` entero, con sus llaves equilibradas.

    Hace falta contar llaves a mano: dentro de un `className={}`
    hay ternarios, plantillas y accesos a tablas, y una regex que
    corte en la primera llave se lleva media expresion.

    SOLO SE MIRA AQUI DENTRO. La primera version cazaba tambien
    los respaldos `|| "Computer"` de cualquier sitio, y sacaba
    quince clases que no eran clases sino texto de pantalla: una
    guardia con ruido es una guardia que alguien relaja.
    """

    expresiones = []

    for encontrado in re.finditer(r"className=", texto):

        i = encontrado.end()

        if i < len(texto) and texto[i] in (chr(34), chr(39)):

            comilla = texto[i]

            fin = texto.find(comilla, i + 1)

            if fin > 0:
                expresiones.append(texto[i + 1:fin])

            continue

        if i >= len(texto) or texto[i] != "{":
            continue

        hondo = 0

        for j in range(i, min(len(texto), i + 600)):

            if texto[j] == "{":
                hondo += 1

            elif texto[j] == "}":
                hondo -= 1

                if hondo == 0:
                    expresiones.append(texto[i + 1:j])
                    break

    return expresiones


def _de_la_expresion(expresion: str) -> set:
    """
    Las clases de una expresion de `className`.

    Todo literal de texto que aparezca ahi dentro es una clase:
    los de un ternario, los de un respaldo `|| "x"` y la parte
    fija de una plantilla.

    SIN LITERAL NO SE EMITE NADA. La version anterior, cuando la
    expresion era solo una variable —`className={tono}`—, se
    tragaba el nombre de la variable y lo daba por clase: salian
    `.tono`, `.cls`, `.clase`, `.num`. Lo que decide una variable
    en tiempo de ejecucion no se puede leer desde aqui, y fingir
    que si llena la guardia de falsos.
    """

    clases = set()

    # LO QUE SE COMPARA NO ES UNA CLASE.
    #
    #     `className={x === "CAJA" ? "a" : "b"}` emite `a` o `b`.
    #     "CAJA" es el estado del motor con el que se compara, y
    #     contarlo como clase sacaba once falsos: CAJA, CLOSING,
    #     LOST, WON, NO_JUEGA... Se quitan los dos lados de cada
    #     comparacion antes de mirar.
    expresion = re.sub(
        r"[!=]==?\s*" + COMILLAS, " ", expresion
    )

    for trozo in re.findall(COMILLAS, expresion):

        # Lo que sale de `${}` no se puede leer desde aqui.
        trozo = re.sub(r"\$\{[^}]*\}", " ", trozo)

        for clase in trozo.split():

            # `plan2-` es el trozo fijo de `plan2-${tono}`: la
            # clase de verdad la arma el navegador.
            if clase.endswith("-"):
                continue

            if re.fullmatch(r"[a-zA-Z][A-Za-z0-9_-]*", clase):
                clases.add(clase)

    return clases


def _clases_emitidas() -> dict:
    """
    Las clases que el JSX pinta, con el fichero de cada una.

    Solo lo que va dentro de un `className`. Un texto que dice
    "Computer" en un respaldo de pantalla no es una clase, y
    contarlo como tal llena la guardia de falsos que acaban
    apagandola.
    """

    emitidas = {}

    for fichero in sorted(FUENTE.rglob("*.jsx")):

        texto = _sin_comentarios(
            fichero.read_text(encoding="utf-8")
        )

        for expresion in _expresiones_de_clase(texto):

            for clase in _de_la_expresion(expresion):

                emitidas.setdefault(clase, set()).add(
                    fichero.relative_to(RAIZ).as_posix()
                )

    return emitidas


# El VALOR de una entrada de tabla: lo que va detras de los dos
# puntos. Si es una lista, su primer elemento — que en las tablas
# de este panel es la clase y los otros son el rombo y el texto.
VALOR = re.compile(
    r":\s*(?:\[\s*)?"
    + COMILLAS
)


def _tablas(texto: str) -> list:
    """
    Cada `const NOMBRE = {...}` con su bloque, contando llaves.

    Hace falta contar: `const POS = { 1: "por", 2: "def" };`
    cierra en la MISMA linea. Anclar el cierre a un `};` a
    principio de linea se saltaba ese y cogia el siguiente,
    tragandose ciento cuarenta y ocho lineas de codigo y sacando
    como clase cualquier texto que hubiera por el camino.
    """

    tablas = []

    for encontrado in re.finditer(
        r"(?m)^const ([A-Z][A-Z_0-9]*) = \{", texto
    ):
        i = encontrado.end() - 1

        hondo = 0

        for j in range(i, len(texto)):

            if texto[j] == "{":
                hondo += 1

            elif texto[j] == "}":
                hondo -= 1

                if hondo == 0:
                    tablas.append(
                        (encontrado.group(1), texto[i + 1:j])
                    )
                    break

    return tablas


def _clases_de_las_tablas() -> dict:
    """
    Las clases que salen de una tabla de traduccion.

    `const TONO = {"pedir otra oferta": "d-reroll", ...}` pinta
    `d-reroll` sin que aparezca nunca en un `className`. Son
    justo las que se olvidan, porque no se ven al leer el JSX.

    DOS FILTROS, Y LOS DOS HACEN FALTA

        1. Solo las tablas cuyo nombre aparece dentro de un
           `className`. Este panel tiene tambien tablas de texto
           —de una etiqueta del motor a una frase en cristiano— y
           sus valores son frases, no clases.

        2. Solo el VALOR, nunca la clave. En `TONO` las claves
           son las frases y los valores las clases: mirar las dos
           sacaba `.conservamos`, `.deuda` y `.nunca`, que son
           palabras sueltas de una frase.
    """

    emitidas = {}

    for fichero in sorted(FUENTE.rglob("*.jsx")):

        texto = _sin_comentarios(
            fichero.read_text(encoding="utf-8")
        )

        dentro_de_clase = " ".join(
            _expresiones_de_clase(texto)
        )

        for nombre, bloque in _tablas(texto):

            if nombre not in dentro_de_clase:
                continue

            for valor in VALOR.findall(bloque):

                for clase in valor.split():

                    if re.fullmatch(
                        r"[a-z][a-z0-9_-]*", clase
                    ):
                        emitidas.setdefault(
                            clase, set()
                        ).add(
                            fichero.relative_to(
                                RAIZ
                            ).as_posix()
                        )

    return emitidas


def test_toda_clase_emitida_existe_en_la_hoja() -> None:
    """
    NINGUNA CLASE SE PINTA SIN ESTAR DEFINIDA.

    Una clase que no existe no da error: hereda el color del
    contenedor y la pantalla miente en silencio. Es la unica
    familia de fallos de este panel que ninguna herramienta caza.
    """

    de_la_hoja = _clases_de_la_hoja()

    # REGLA 24: con la hoja vacia esto pasaria siempre.
    assert len(de_la_hoja) > 100, (
        f"solo se han leido {len(de_la_hoja)} clases de la hoja: "
        f"o no se esta leyendo, o la hoja se ha vaciado"
    )

    emitidas = _clases_emitidas()

    assert len(emitidas) > 50, (
        f"solo se han leido {len(emitidas)} clases emitidas: la "
        f"guardia no esta mirando el JSX"
    )

    faltan = {}

    for clase, ficheros in sorted(emitidas.items()):

        if clase in DE_FUERA or DE_TAILWIND.match(clase):
            continue

        if clase not in de_la_hoja:
            faltan[clase] = sorted(ficheros)

    assert not faltan, (
        f"{len(faltan)} clase(s) se pintan y no existen en la "
        f"hoja de estilos: heredan el color de lo que tengan "
        f"encima y la pantalla miente sin avisar.\n"
        + "\n".join(
            f"   .{clase}  <- {', '.join(donde)}"
            for clase, donde in faltan.items()
        )
    )


def test_las_clases_de_las_tablas_tambien_existen() -> None:
    """
    LAS QUE SALEN DE UNA TABLA SON LAS QUE SE OLVIDAN.

    `TONO_ETIQUETA` y `TONO` traducen una etiqueta del motor a
    una clase. Esa clase no aparece en ningun `className` del
    fichero: leyendo el JSX no se ve que exista.

    Nueve de las diez que faltaban en dos dias eran de este tipo.
    """

    de_la_hoja = _clases_de_la_hoja()

    de_tablas = _clases_de_las_tablas()

    # REGLA 24.
    assert de_tablas, (
        "no se ha leido ninguna clase de las tablas de "
        "traduccion: la guardia no esta mirando donde dice"
    )

    faltan = {
        clase: sorted(ficheros)
        for clase, ficheros in sorted(de_tablas.items())
        if clase not in de_la_hoja
        and clase not in DE_FUERA
        and not DE_TAILWIND.match(clase)
    }

    assert not faltan, (
        f"{len(faltan)} clase(s) salen de una tabla de "
        f"traduccion y no existen en la hoja:\n"
        + "\n".join(
            f"   .{clase}  <- {', '.join(donde)}"
            for clase, donde in faltan.items()
        )
    )


def test_el_computer_y_el_rival_no_son_del_mismo_color() -> None:
    """
    «esto se puede comprar» y «esto es el escaparate de otro»
    NO pueden verse igual.

    Es la unica distincion que hace util la columna. Si los dos
    salen morados, la columna no dice nada.
    """

    css = re.sub(
        r"/\*.*?\*/",
        " ",
        HOJA.read_text(encoding="utf-8"),
        flags=re.S,
    )

    def color_de(clase):
        for regla in re.findall(
            rf"\.{clase}\s*\{{([^}}]*)\}}", css
        ):
            encontrado = re.search(
                r"color:\s*([^;}]+)", regla
            )

            if encontrado:
                return encontrado.group(1).strip()

        return None

    computer = color_de("comp")

    rival = color_de("riv")

    assert computer, (
        "`.comp` no define color: el Computer heredara el del "
        "contenedor, que hoy es el morado del rival"
    )

    assert rival, "`.riv` no define color"

    assert computer != rival, (
        f"el Computer y el rival salen del mismo color "
        f"({computer}): la columna QUIEN LO VENDE deja de "
        f"distinguir lo que se puede comprar de lo que no"
    )


TESTS = [
    test_toda_clase_emitida_existe_en_la_hoja,
    test_las_clases_de_las_tablas_tambien_existen,
    test_el_computer_y_el_rival_no_son_del_mismo_color,
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
        f"LA HOJA DE ESTILOS V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
