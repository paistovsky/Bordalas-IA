"""
Ninguna guardia depende del reloj del sistema.

SINTOMA (14/09/2026, 00:0x)

    `test_el_cartel_dice_lo_que_pasa_en_una_frase` paso todo el
    13/09 en verde y se puso roja al cambiar la fecha. Nadie toco
    el codigo: solo paso el tiempo.

    La frase del cartel decia "hoy a las 10:08" a las 23:59 y
    "AYER a las 10:08" a las 00:01, porque `_cuando` leia
    `datetime.now()`. La guardia compara la frase entera contra
    un texto fijo, asi que comparaba contra el reloj.

CONSECUENCIA

    Una verja que se pone roja sola no se puede creer. Y lo peor
    no es la falsa alarma: es que la siguiente vez que se ponga
    roja DE VERDAD, el primer pensamiento va a ser "sera la hora
    otra vez". Un aviso que cria lobos deja de ser un aviso.

DOCTRINA 50

    Una guardia que depende del reloj del sistema falla sola a
    medianoche. No hace falta que nadie toque el codigo: basta
    con que pase el tiempo.

LA REGLA QUE SE VIGILA, Y POR QUE ES ESTA

    NO es "ninguna prueba puede llamar a `datetime.now()`". Hay
    cuatro que lo hacen y estan bien: fabrican una marca
    RELATIVA —"algo que paso hace treinta segundos"— y luego
    afirman sobre la DIFERENCIA. Esa afirmacion vale lo mismo a
    las tres de la tarde que a las tres de la mañana. Prohibirlo
    obligaria a reescribirlas sin ganar nada, y una guardia que
    molesta sin motivo acaba relajada.

    La forma peligrosa es otra y es precisa:

        UNA FUNCION QUE CONVIERTE UNA MARCA DE TIEMPO EN UNA
        PALABRA RELATIVA —"hoy", "ayer", "hace N dias"— TIENE
        QUE RECIBIR LA HORA DE REFERENCIA.

    Porque esa palabra acaba comparada contra un texto fijo, y
    entonces el texto fijo compite contra el calendario.

    MEDIDO: la verja entera corrida con el reloj congelado en
    seis instantes —21:00 y 22:30 UTC del 13/09 (los dos lados
    de la medianoche de Madrid), el 14 a las 03:00, una semana
    despues, el cambio de mes y el 31/12 con el horario de
    invierno— da 128 en verde en los seis. Antes del arreglo, el
    cartel fallaba en cinco de los seis.

REGLA 23

    No lee estado externo: solo el codigo del repositorio.
"""

from __future__ import annotations

import ast
import io
from pathlib import Path


RAIZ = Path(__file__).parents[2]

FUENTE = RAIZ / "src"


# Las palabras que delatan una funcion que habla en relativo.
PALABRAS_RELATIVAS = (
    "hoy",
    "ayer",
    "hace",
    "mañana",
    "manana",
)

# COPIAS MUERTAS QUE NO SE EJECUTAN.
#
#     `dashboard_state_PRE_*` son fotos de versiones anteriores
#     que nadie importa. Señalarlas seria ruido permanente, y el
#     ruido es lo que hace que alguien acabe apagando la guardia.
COPIAS_MUERTAS = ("_PRE_", "_BACKUP")

# Como se puede llamar el parametro por el que entra la hora.
NOMBRES_DE_LA_HORA = (
    "ahora",
    "momento",
    "momento_utc",
    "referencia",
    "hoy",
    "at",
    "now",
)

# Las llamadas que leen el reloj del sistema.
DEL_RELOJ = ("now", "utcnow", "today")


# GUARDIAS QUE LLAMAN AL RELOJ, Y POR QUE PUEDEN.
#
#     Cada una con su motivo. Todas hacen lo mismo: construyen
#     una marca relativa a "ahora" y afirman sobre la diferencia,
#     no sobre una palabra. El resultado no cambia con la hora, y
#     esta medido: sobreviven a los seis instantes del barrido.
#
#     Si añades una aqui, escribe POR QUE. Una lista de
#     excepciones sin motivos es donde se esconde el fallo de
#     mañana.
PUEDEN_MIRAR_EL_RELOJ = {
    "test_dashboard_truth_v1.py": (
        "fabrica una marca de hace N segundos y comprueba que "
        "`_edad_en_segundos` devuelve ~N. La resta vale igual a "
        "cualquier hora."
    ),
    "test_futbolfantasy_source_v12.py": (
        "sella un fixture de cache como recien escrito para que "
        "el TTL no lo dé por caducado. No afirma sobre la fecha."
    ),
    "test_jornada_del_tablero_v1.py": (
        "usa `AHORA` como origen para construir tableros de hace "
        "N horas; las aserciones son sobre la jornada, no sobre "
        "el dia."
    ),
    "test_multisource_starter_v1124.py": (
        "misma forma: marcas relativas a `now` y aserciones "
        "sobre frescura, no sobre una palabra."
    ),
}


def _sin_docstring(funcion: ast.FunctionDef) -> ast.Module:
    """
    El cuerpo de la funcion sin su docstring.

    Ocho guardias de esta casa se han puesto rojas por el texto
    que las explicaba. Una que dijera "hace" en su docstring no
    puede contar como una funcion que habla en relativo.
    """

    cuerpo = list(funcion.body)

    if (
        cuerpo
        and isinstance(cuerpo[0], ast.Expr)
        and isinstance(cuerpo[0].value, ast.Constant)
        and isinstance(cuerpo[0].value.value, str)
    ):
        cuerpo = cuerpo[1:]

    return ast.Module(body=cuerpo, type_ignores=[])


def _lee_el_reloj(cuerpo: ast.Module) -> bool:
    """
    ¿Llama a `datetime.now()`, `utcnow()` o `date.today()`?

    Se mira el ARBOL, no el texto del volcado: `today` puede ser
    tambien un nombre de variable, y contarlo seria un falso.
    """

    for nodo in ast.walk(cuerpo):

        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr in DEL_RELOJ
        ):
            return True

    return False


def _habla_en_relativo(cuerpo: ast.Module) -> bool:
    """
    ¿Produce una PALABRA relativa: "hoy", "ayer", "hace N dias"?

    DOS AJUSTES, Y LOS DOS HICIERON FALTA (14/09/2026)

        1. SOLO EN LITERALES DE TEXTO. La primera version buscaba
           las palabras en `ast.dump()` del cuerpo entero, y eso
           caza tambien los NOMBRES: una variable llamada `hoy`
           sale como `Name(id='hoy')` y un parametro como
           `arg='hoy'`. Señalo cuatro funciones y TRES ERAN
           FALSAS: `manager_scoreboard` llama `hoy` al precio de
           hoy, y `podar` y `load_corrections` reciben un
           parametro con ese nombre.

        2. LA PALABRA TIENE QUE SER EL LITERAL, no ir dentro de
           una frase. Buscando "hace " en cualquier sitio salian
           36, casi todas por prosa corriente —"lo que hace",
           "no se hace"—. Lo que delata a esta familia es un
           literal que ES la palabra: "hoy", "ayer", o el trozo
           fijo de `f"hace {dias} dias"`.

        Un detector con falsos es un detector que alguien apaga,
        y uno que no caza nada es peor.
    """

    for nodo in ast.walk(cuerpo):

        if not isinstance(nodo, ast.Constant):
            continue

        if not isinstance(nodo.value, str):
            continue

        texto = nodo.value.strip().lower()

        for palabra in PALABRAS_RELATIVAS:

            if texto == palabra or texto.startswith(
                palabra + " "
            ):
                return True

    return False


def las_que_hablan_en_relativo() -> list:
    """
    Cada funcion de `src/` que convierte una marca en palabras.

    Se recorre el arbol entero: una funcion nueva entra aqui sola
    el dia que alguien la escriba, que es lo que hace de esto un
    mecanismo y no un recordatorio.
    """

    encontradas = []

    for fichero in sorted(FUENTE.rglob("*.py")):

        if fichero.name.startswith("test_"):
            continue

        if any(m in fichero.name for m in COPIAS_MUERTAS):
            continue

        try:
            arbol = ast.parse(
                io.open(fichero, encoding="utf-8").read()
            )

        except SyntaxError:
            continue

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, ast.FunctionDef):
                continue

            cuerpo = _sin_docstring(nodo)

            if not _habla_en_relativo(cuerpo):
                continue

            argumentos = [
                a.arg
                for a in (
                    nodo.args.args + nodo.args.kwonlyargs
                )
            ]

            encontradas.append(
                {
                    "fichero": fichero.relative_to(
                        RAIZ
                    ).as_posix(),
                    "funcion": nodo.name,
                    "lee_el_reloj": _lee_el_reloj(cuerpo),
                    "recibe_la_hora": any(
                        a in NOMBRES_DE_LA_HORA
                        for a in argumentos
                    ),
                    "argumentos": argumentos,
                }
            )

    return encontradas


def las_guardias() -> list:
    return sorted(FUENTE.rglob("test_*.py"))


def test_ninguna_guardia_mira_el_reloj() -> None:
    """
    LA HORA ENTRA POR LA PUERTA.

    Toda funcion que convierta una marca de tiempo en una palabra
    relativa tiene que recibir la hora contra la que compara. Si
    la busca ella, lo que diga depende de cuando se pregunte — y
    lo que diga acaba comparado contra un texto fijo.
    """

    hablan = las_que_hablan_en_relativo()

    # REGLA 24: con la lista vacia esto pasaria siempre.
    assert len(hablan) >= 3, (
        f"solo se han encontrado {len(hablan)} funciones que "
        f"hablen en relativo: el recorrido no esta mirando donde "
        f"dice"
    )

    # NI UNA LLAMADA AL RELOJ, aunque reciba la hora.
    #
    #     La primera version de esta guardia pedia "lee el reloj
    #     Y NO recibe la hora". Se probo devolviendole el reloj a
    #     `_cuando` como RESPALDO —`ahora or datetime.now()`— y
    #     esta guardia lo dejo pasar: el parametro seguia ahi.
    #
    #     Un respaldo que mira el reloj es la misma bomba con
    #     otro nombre, y la peor de todas: solo estalla el dia
    #     que alguien se olvide de pasar la hora, que es justo el
    #     dia en que nadie lo esta mirando.
    #
    #     Si recibe la hora, no tiene ninguna razon para buscarla.
    tocan_el_reloj = [f for f in hablan if f["lee_el_reloj"]]

    assert not tocan_el_reloj, (
        f"{len(tocan_el_reloj)} funcion(es) convierten una marca "
        f"de tiempo en palabras y leen el reloj del sistema. Lo "
        f"que digan cambia a medianoche, y la guardia que lo "
        f"compare contra un texto fijo se pondra roja sola: "
        + " · ".join(
            f"{f['fichero']}::{f['funcion']} "
            f"args={f['argumentos']} "
            f"recibe_la_hora={f['recibe_la_hora']}"
            for f in tocan_el_reloj
        )
        + ". Se le pasa la hora, como `permite_escribir`. Y "
        "sin hora se dice que no se sabe: un respaldo que mira "
        "el reloj es la misma bomba con otro nombre."
    )


def test_el_cartel_del_carril_no_depende_de_la_hora() -> None:
    """
    LA QUE NOS MORDIO, CLAVADA.

    `_cuando` es la funcion que se puso roja sola. Queda aqui con
    nombre y apellido para que, si alguien le devuelve el reloj,
    lo diga la verja y no el calendario.
    """

    from datetime import datetime, timezone

    from src.actions.escaparate_executor import _cuando

    LA_MARCA = "2026-09-13T08:08:00+00:00"

    # 1. LA MISMA FOTO, LA MISMA FRASE. Todo el dia de Madrid.
    #
    #    Madrid va dos horas por delante en septiembre: el dia
    #    cambia a las 22:00 UTC, y 21:59 es la ultima hora que
    #    sigue siendo "hoy".
    frases = {
        _cuando(
            LA_MARCA,
            datetime(2026, 9, 13, h, m, tzinfo=timezone.utc),
        )
        for h, m in (
            (6, 30),
            (12, 0),
            (17, 17),
            (21, 0),
            (21, 59),
        )
    }

    assert frases == {"hoy a las 10:08"}, (
        f"la frase cambia segun la hora a la que se pregunte: "
        f"{sorted(frases)}"
    )

    # 2. Y AL DIA SIGUIENTE DICE "AYER".
    #
    #    La palabra no sobra: es la que dice si el jugador lleva
    #    dos horas o veintiseis sin publicar.
    assert _cuando(
        LA_MARCA,
        datetime(2026, 9, 13, 22, 0, tzinfo=timezone.utc),
    ) == "ayer a las 10:08"

    # 3. SIN REFERENCIA, LA FECHA ENTERA Y NINGUN "HOY".
    #
    #    El respaldo NO puede ser mirar el reloj: seria la misma
    #    bomba con otro nombre.
    assert _cuando(LA_MARCA) == "el 13/09 a las 10:08"

    # 4. Y NO QUEDA NI UNA LLAMADA AL RELOJ DENTRO.
    fuente = (
        RAIZ / "src" / "actions" / "escaparate_executor.py"
    ).read_text(encoding="utf-8")

    arbol = ast.parse(fuente)

    funcion = next(
        n
        for n in ast.walk(arbol)
        if isinstance(n, ast.FunctionDef) and n.name == "_cuando"
    )

    assert not _lee_el_reloj(_sin_docstring(funcion)), (
        "`_cuando` ha vuelto a mirar el reloj del sistema"
    )


def test_las_que_miran_el_reloj_constan_con_su_motivo() -> None:
    """
    LAS CUATRO QUE PUEDEN, Y POR QUE PUEDEN.

    No se prohibe llamar al reloj en una prueba: hay cuatro que
    fabrican una marca relativa y afirman sobre la DIFERENCIA, y
    eso vale igual a cualquier hora.

    Lo que no vale es que nadie sepa cual es cual. Una quinta que
    aparezca sin motivo escrito para esta verja.
    """

    guardias = las_guardias()

    # REGLA 24.
    assert len(guardias) >= 100, (
        f"solo se han encontrado {len(guardias)} guardias: el "
        f"recorrido no esta mirando donde dice"
    )

    miran = {}

    for fichero in guardias:

        try:
            arbol = ast.parse(
                io.open(fichero, encoding="utf-8").read()
            )

        except SyntaxError:
            continue

        tocan = set()

        for nodo in ast.walk(arbol):

            if not isinstance(nodo, ast.Call):
                continue

            if isinstance(nodo.func, ast.Attribute):

                if nodo.func.attr in DEL_RELOJ:
                    tocan.add(f"{nodo.func.attr}()")

                elif nodo.func.attr in (
                    "time",
                    "monotonic",
                ) and getattr(nodo.func.value, "id", "") == "time":
                    tocan.add(f"time.{nodo.func.attr}()")

        if tocan:
            miran[fichero.name] = sorted(tocan)

    nuevas = sorted(
        n for n in miran if n not in PUEDEN_MIRAR_EL_RELOJ
    )

    assert not nuevas, (
        f"{len(nuevas)} guardia(s) llaman al reloj del sistema y "
        f"no constan:\n"
        + "\n".join(
            f"   {n}  ->  {', '.join(miran[n])}" for n in nuevas
        )
        + "\n\nSi lo que afirman es una DIFERENCIA y no una "
        "palabra, se apuntan en `PUEDEN_MIRAR_EL_RELOJ` con su "
        "motivo. Si afirman una palabra, se les pasa la hora."
    )

    # Y LAS QUE SOBRAN TAMBIEN SE DICEN. Una excepcion de una
    # guardia que ya no mira el reloj es basura que acaba
    # tapando el caso de mañana.
    sobran = sorted(
        n for n in PUEDEN_MIRAR_EL_RELOJ if n not in miran
    )

    assert not sobran, (
        f"estas excepciones ya no hacen falta: {sobran}"
    )

    for nombre, motivo in PUEDEN_MIRAR_EL_RELOJ.items():
        assert (motivo or "").strip(), (
            f"la excepcion de `{nombre}` no dice por que"
        )


TESTS = [
    test_ninguna_guardia_mira_el_reloj,
    test_el_cartel_del_carril_no_depende_de_la_hora,
    test_las_que_miran_el_reloj_constan_con_su_motivo,
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
        f"EL RELOJ DE LAS GUARDIAS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
