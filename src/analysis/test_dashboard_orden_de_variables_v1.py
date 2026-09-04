"""
Ninguna variable del dashboard se usa antes de existir.

SINTOMA (05/09/2026, en esta misma noche)

    Al añadir dos bloques nuevos a `build_dashboard_state` se
    reordeno codigo sin querer, y `build_acquisition_board` quedo
    llamandose con `exposure` antes de que `exposure` existiera.

        UnboundLocalError: cannot access local variable
        'exposure' where it is not associated with a value

    El fichero seguia compilando. La puerta seguia en verde con
    sus 58 guardias. Y `status.json` se generaba SIN los cinco
    bloques nuevos.

CAUSA

    Dos cosas a la vez:

    1. `build_dashboard_state` es una funcion larga de mas de
       trescientas lineas donde el orden de las asignaciones es
       la unica cosa que sostiene el resultado, y no habia nada
       que lo comprobase.

    2. Las guardias que escribi esa noche comprobaban el orden
       leyendo el TEXTO del fichero -`fuente.index(a) <
       fuente.index(b)`-. Eso pasa igual de verde con el codigo
       roto: el texto estaba en orden, la ejecucion no.

CONSECUENCIA

    Un fallo asi no se ve. El dashboard se genera, dice "OK",
    escribe su fichero y le faltan bloques enteros. Es
    exactamente el fallo silencioso que mas caro sale: el dueño
    mira una pantalla incompleta creyendo que esta completa.

    Esta guardia lee el arbol de la funcion y recorre las
    asignaciones en el orden en que se ejecutan. No hace falta
    generar el dashboard ni tener datos: es gratis y corre en
    cada ciclo.
"""

from __future__ import annotations

import ast

from pathlib import Path


VIGILADAS = [
    ("src/telemetry/dashboard_state.py", "build_dashboard_state"),
]


# ============================================================
# EL DETECTOR
# ============================================================


def _nombres_asignados(nodo: ast.AST) -> set:
    """Lo que ESTA sentencia deja definido al terminar."""

    nombres = set()

    for objetivo in ast.walk(nodo):

        if isinstance(objetivo, ast.Name) and isinstance(
            objetivo.ctx, (ast.Store, ast.Del)
        ):
            nombres.add(objetivo.id)

        elif isinstance(objetivo, ast.alias):
            nombres.add((objetivo.asname or objetivo.name).split(".")[0])

        elif isinstance(objetivo, ast.ExceptHandler) and objetivo.name:
            nombres.add(objetivo.name)

    return nombres


def _nombres_leidos(nodo: ast.AST) -> set:
    """
    Lo que esta sentencia lee, sin contar lo que ata por su
    cuenta.

    Una comprension crea su propia variable -`for f in filas`-, y
    contarla como lectura daria un falso positivo en cada
    `[x for x in ...]`.
    """

    atados = set()

    for hijo in ast.walk(nodo):

        if isinstance(
            hijo,
            (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
        ):
            for generador in hijo.generators:
                for objetivo in ast.walk(generador.target):
                    if isinstance(objetivo, ast.Name):
                        atados.add(objetivo.id)

        elif isinstance(hijo, ast.Lambda):
            for argumento in hijo.args.args:
                atados.add(argumento.arg)

    return {
        hijo.id
        for hijo in ast.walk(nodo)
        if isinstance(hijo, ast.Name)
        and isinstance(hijo.ctx, ast.Load)
        and hijo.id not in atados
    }


def usos_antes_de_asignar(funcion: ast.FunctionDef) -> list:
    """
    Nombres locales leidos antes de tener valor, con su linea.

    Solo mira los nombres que la propia funcion asigna: lo que
    viene de fuera -imports del modulo, constantes, funciones- no
    es cosa suya.
    """

    locales = set()

    for sentencia in funcion.body:
        locales |= _nombres_asignados(sentencia)

    for argumento in funcion.args.args:
        locales.discard(argumento.arg)

    definidos = {a.arg for a in funcion.args.args}

    problemas = []

    def acusar(nodos, linea: int) -> None:
        """Lo que se lee AQUI y todavia no tiene valor."""

        for nodo in nodos:

            if nodo is None:
                continue

            for nombre in sorted(_nombres_leidos(nodo)):
                if nombre in locales and nombre not in definidos:
                    problemas.append((nombre, linea))

    def recorrer(cuerpo: list) -> None:
        """
        En el orden en que se ejecuta, y solo lo que se ejecuta
        en cada momento.

        LA PARTE QUE HAY QUE HACER BIEN

            De una sentencia compuesta NO se puede mirar el
            subarbol entero de golpe: un `for offer in ofertas`
            usa `offer` dentro del cuerpo, y el `import` de un
            `try` define el nombre que ese mismo `try` usa dos
            lineas mas abajo. Mirarlo todo junto acusa a los dos
            y la guardia se vuelve inservible por ruidosa.

            Asi que de cada compuesta se mira SOLO su cabecera
            -la condicion, el iterable, el contexto-, se atan sus
            variables, y despues se entra.
        """

        for sentencia in cuerpo:

            if isinstance(sentencia, (ast.FunctionDef,
                                      ast.AsyncFunctionDef,
                                      ast.ClassDef)):
                # Lo de dentro se ejecuta cuando se llame, no
                # aqui.
                definidos.add(sentencia.name)
                continue

            if isinstance(sentencia, (ast.If, ast.While)):
                acusar([sentencia.test], sentencia.lineno)
                recorrer(sentencia.body)
                recorrer(sentencia.orelse)

            elif isinstance(sentencia, (ast.For, ast.AsyncFor)):
                acusar([sentencia.iter], sentencia.lineno)
                definidos.update(_nombres_asignados(sentencia.target))
                recorrer(sentencia.body)
                recorrer(sentencia.orelse)

            elif isinstance(sentencia, (ast.With, ast.AsyncWith)):
                acusar(
                    [item.context_expr for item in sentencia.items],
                    sentencia.lineno,
                )
                for item in sentencia.items:
                    if item.optional_vars is not None:
                        definidos.update(
                            _nombres_asignados(item.optional_vars)
                        )
                recorrer(sentencia.body)

            elif isinstance(sentencia, ast.Try):
                recorrer(sentencia.body)
                for manejador in sentencia.handlers:
                    if manejador.name:
                        definidos.add(manejador.name)
                    recorrer(manejador.body)
                recorrer(sentencia.orelse)
                recorrer(sentencia.finalbody)

            else:
                acusar([sentencia], sentencia.lineno)

            definidos.update(_nombres_asignados(sentencia))

    recorrer(funcion.body)

    return problemas


def _funcion(ruta: str, nombre: str) -> ast.FunctionDef:
    arbol = ast.parse(Path(ruta).read_text(encoding="utf-8"))

    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            return nodo

    raise AssertionError(f"no existe {nombre} en {ruta}")


# ============================================================
# 1. QUE EL DETECTOR DETECTE
# ============================================================


def test_el_detector_pilla_el_fallo_de_esta_noche() -> None:
    """
    Una guardia que no se ha visto fallar no protege de nada.
    Este es el codigo roto, reducido.
    """

    roto = ast.parse(
        "def f():\n"
        "    board = build(available=exposure.get('x'))\n"
        "    exposure = compact()\n"
        "    return board, exposure\n"
    ).body[0]

    problemas = usos_antes_de_asignar(roto)

    assert problemas, "no vio el UnboundLocalError"
    assert problemas[0][0] == "exposure"


def test_el_detector_no_se_inventa_fallos() -> None:
    bueno = ast.parse(
        "def f():\n"
        "    exposure = compact()\n"
        "    board = build(available=exposure.get('x'))\n"
        "    return board\n"
    ).body[0]

    assert usos_antes_de_asignar(bueno) == []


def test_una_comprension_no_es_un_fallo() -> None:
    """`[f for f in filas]` ata `f` sola: no es una lectura."""

    caso = ast.parse(
        "def f(filas):\n"
        "    salida = [x for x in filas if x]\n"
        "    parejas = {k: v for k, v in filas}\n"
        "    orden = sorted(filas, key=lambda item: item.get('a'))\n"
        "    return salida, parejas, orden\n"
    ).body[0]

    assert usos_antes_de_asignar(caso) == []


def test_lo_de_fuera_de_la_funcion_no_cuenta() -> None:
    """Constantes e imports del modulo no son variables locales."""

    caso = ast.parse(
        "def f():\n"
        "    return CONSTANTE_DEL_MODULO + otra_funcion()\n"
    ).body[0]

    assert usos_antes_de_asignar(caso) == []


def test_lo_asignado_dentro_de_un_try_cuenta_despues() -> None:
    caso = ast.parse(
        "def f():\n"
        "    try:\n"
        "        valor = calcular()\n"
        "    except Exception:\n"
        "        valor = None\n"
        "    return valor\n"
    ).body[0]

    assert usos_antes_de_asignar(caso) == []


# ============================================================
# 2. Y QUE EL DASHBOARD ESTE LIMPIO
# ============================================================


def test_el_dashboard_no_usa_nada_antes_de_tenerlo() -> None:
    for ruta, nombre in VIGILADAS:

        problemas = usos_antes_de_asignar(_funcion(ruta, nombre))

        assert not problemas, (
            f"{ruta}:{nombre} usa variables antes de asignarlas: "
            + ", ".join(
                f"`{var}` en la linea {linea}"
                for var, linea in problemas
            )
            + ". El fichero compila y el dashboard se genera igual, "
            "pero le faltan bloques enteros."
        )


def test_los_cinco_bloques_nuevos_llegan_al_json() -> None:
    """
    El fallo de esta noche se noto porque faltaban estos. Que
    esten escritos en el `return` no basta -tambien lo estaban
    entonces-, pero es la otra mitad de la comprobacion.
    """

    fuente = Path("src/telemetry/dashboard_state.py").read_text(
        encoding="utf-8"
    )

    for clave in (
        '"race": race',
        '"season_horizon": season_horizon',
        '"roster_expansion": roster_expansion',
        '"rival_squads": rival_squads',
        '"bid_outcomes": bid_outcome_summary()',
    ):
        assert clave in fuente, f"falta {clave} en el estado publicado"


TESTS = [
    test_el_detector_pilla_el_fallo_de_esta_noche,
    test_el_detector_no_se_inventa_fallos,
    test_una_comprension_no_es_un_fallo,
    test_lo_de_fuera_de_la_funcion_no_cuenta,
    test_lo_asignado_dentro_de_un_try_cuenta_despues,
    test_el_dashboard_no_usa_nada_antes_de_tenerlo,
    test_los_cinco_bloques_nuevos_llegan_al_json,
]


def main() -> None:
    fallos = 0
    for test in TESTS:
        try:
            test()
            print(f"OK   {test.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"FALLA {test.__name__}: {exc}")

    print("=" * 60)
    print(f"ORDEN DE VARIABLES V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
