"""
El carril comia de un plato vacio, y la nota estaba al lado.

SINTOMA (12/09/2026, foto de las 14:22)

    Dos dias encendido, llamado y con dinero. VIAJES COMPLETADOS,
    0. No era ninguna de sus cinco puertas: LE LLEGABA LA LISTA
    DE CANDIDATOS VACIA.

    La misma foto, la misma vuelta, el mismo segundo:

        la pantalla   Trent        2.760.000  +2,67 %
                      Ruben Garcia 2.680.000  +1,57 %
                      y tres que pasan el tope de 3.000.000

        el ejecutor   "El carril podia pujar y no hay a quien:
                       0 llegan al suelo (+1 %), 0 fuera. No
                       habia candidatos que mirar."

    Cinco en el panel, cero en el ejecutor. No es un desacuerdo
    de criterio: son DOS LISTAS DISTINTAS, y la del ejecutor esta
    vacia.

CAUSA

    `_correr_el_carril` leia `cycle["state"]`, y `run_cycle` no
    devuelve eso: devuelve {snapshot, result, execution,
    post_action}. El docstring de `_estado_publicado`, ochenta
    lineas mas arriba en el MISMO fichero, lo avisaba con estas
    palabras:

        "Leer `cycle["state"]` -o incluso `result["state"]`-
         buscando `acquisition` devuelve vacio: cero candidatos,
         cero pujas y ni un error en el log. Encendido y mudo,
         que es la peor forma de estar apagado."

    No se caia solo `objetivos`. Se caia todo lo que sale de ahi:
    `caja` None, `comprometido` None, `presupuesto` None, y la
    curva cayendo a su defecto -prima de puja 0,00 %-.

    LA PRUEBA CRUZADA: `la_subasta` SI compro esa mañana, y
    `_pujar_en_el_reset` era la unica funcion del fichero que
    llamaba a `_estado_publicado`. La que come del plato lleno
    actua; la que come del vacio no. No eran dos teorias
    compitiendo: una nunca se sento a la mesa.

CONSECUENCIA

    Dos guardias. La primera caza este fallo; la segunda impide
    que aparezca en la ruta de al lado.

REGLA 24

    El fixture TRAE CANDIDATOS PAGABLES. Una guardia que pasara
    con la lista vacia es exactamente la que no habria detectado
    esto.

REGLA 23

    No lee estado externo: el `cycle` se construye aqui, entero,
    y las llamadas a la red estan interceptadas.
"""

from __future__ import annotations

import ast

from pathlib import Path


RAIZ = Path(__file__).parents[2]

CICLO = RAIZ / "src" / "v10_full_autonomous_live.py"


def _codigo_vivo(fuente: str) -> str:
    """
    El codigo que SE EJECUTA, sin comentarios ni docstrings.

    Van cinco guardias tropezando con lo mismo: el fallo esta
    contado por escrito —aqui, literalmente, "leer
    `cycle["state"]` devuelve vacio"— y la guardia lee esa nota
    como si fuera codigo vivo.

    Una guardia que obligue a borrar la explicacion para pasar
    hace daño: la proxima persona se encuentra el arreglo sin el
    motivo. Asi que se quitan los DOS, y los docstrings por el
    arbol y no a ojo.
    """

    fuera = set()

    try:
        arbol = ast.parse(fuente)

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

            if not cuerpo:
                continue

            primero = cuerpo[0]

            if (
                isinstance(primero, ast.Expr)
                and isinstance(primero.value, ast.Constant)
                and isinstance(primero.value.value, str)
            ):
                fuera.update(
                    range(
                        primero.lineno,
                        (primero.end_lineno or primero.lineno)
                        + 1,
                    )
                )

    except SyntaxError:
        pass

    return chr(10).join(
        linea
        for numero, linea in enumerate(
            fuente.splitlines(), start=1
        )
        if numero not in fuera
        and not linea.strip().startswith("#")
    )


# Los candidatos de la foto de las 14:22 del 12/09/2026, tal
# cual. Dos pagables por debajo del tope de 3.000.000 y tres que
# lo pasan.
CANDIDATOS = [
    {
        "id": 101,
        "name": "Trent",
        "position": 2,
        "market_price": 2_760_000,
        "status": "ok",
        "outside_computer_market": False,
    },
    {
        "id": 102,
        "name": "Ruben Garcia",
        "position": 3,
        "market_price": 2_680_000,
        "status": "ok",
        "outside_computer_market": False,
    },
    {
        "id": 103,
        "name": "Cancelo",
        "position": 2,
        "market_price": 5_970_000,
        "status": "ok",
        "outside_computer_market": False,
    },
]

CAJA = 4_333_406                 # medida el 12/09

COMPROMETIDO = 0

CURVA = 1.0029


def _cycle_de_forma_real() -> dict:
    """
    Un `cycle` con la forma que devuelve `run_cycle`.

    Lo que importa es que NO tiene `state` en la raiz: ese era el
    sitio donde el carril buscaba y donde no hay nada.
    """

    return {
        # Sin `snapshot_file`: una ruta a `data/` dentro de una
        # guardia de la verja la hace sospechosa aunque no se lea
        # (regla 23), y `test_verja_determinista_v1` lo caza.
        "snapshot": {"market": [], "players": []},
        "result": {
            "state": {
                "balance": CAJA,
                "phase": "NORMAL",
                "operations_locked": False,
                "hours_to_deadline": 30.0,
                "speculation": {
                    "budget": {
                        "available_budget": 2_109_030,
                        "enabled": True,
                    },
                    "acquisition_budget": {
                        "available_budget": 6_765_106,
                        "enabled": True,
                    },
                    "bid_exposure": {
                        "committed_total": COMPROMETIDO,
                        "committed_operations": 0,
                    },
                },
            },
            "action": "MONITOR_OFFERS",
        },
        "execution": {},
        "post_action": None,
    }


def _tablero_de_mentira() -> dict:
    """El tablero que `_estado_publicado` devolveria hoy."""

    return {
        "targets": CANDIDATOS,
        "budgets": {"speculation": 2_109_030},
        "premium_model": {"curve": [[CURVA, 0]]},
    }


def _lo_que_recibe_correr(monkey_estado=True) -> dict:
    """
    Llama a `_correr_el_carril` y devuelve los argumentos con que
    LLEGO a `correr`, sin ejecutar nada real.

    No toca la red: se sustituyen `_estado_publicado` y `correr`.
    """

    import src.v10_full_autonomous_live as ciclo

    import src.actions.carril_executor as ejecutor

    visto = {}

    def _falso_correr(**kwargs):
        visto.update(kwargs)

        return {"available": True, "executed": False}

    def _falso_estado(cycle):
        publicado = ciclo._estado_publicado.__wrapped__(cycle) \
            if hasattr(ciclo._estado_publicado, "__wrapped__") \
            else None

        estado = ((cycle or {}).get("result") or {}).get(
            "state"
        ) or {}

        return {
            "acquisition": _tablero_de_mentira(),
            "exposure": {},
            "market_clock": {},
            "rival_intelligence": {},
            "solvency_clock": None,
            "operations_locked": False,
            "phase": estado.get("phase"),
            "balance": estado.get("balance"),
            "speculation": estado.get("speculation") or {},
        }

    original_correr = ejecutor.correr

    original_estado = ciclo._estado_publicado

    original_cierres = ciclo._cierres_de_viajes

    try:
        ejecutor.correr = _falso_correr

        if monkey_estado:
            ciclo._estado_publicado = _falso_estado

        ciclo._cierres_de_viajes = lambda: []

        ciclo._correr_el_carril(
            _cycle_de_forma_real(), "MONITOR_OFFERS"
        )

    finally:
        ejecutor.correr = original_correr
        ciclo._estado_publicado = original_estado
        ciclo._cierres_de_viajes = original_cierres

    return visto


# ============================================================
# 1. EL PLATO NO PUEDE LLEGAR VACIO
# ============================================================


def test_el_carril_no_come_de_un_plato_vacio() -> None:
    """
    Campo por campo, lo que recibe `correr`.

    Cada uno de estos cinco llegaba vacio el 12/09, y ninguno
    daba error: el carril decia "no hay a quien pujar" y se
    quedaba tan tranquilo.
    """

    visto = _lo_que_recibe_correr()

    assert visto, "no se llego a llamar a `correr`"

    # 1. LOS CANDIDATOS. Llegaba `[]`.
    objetivos = visto.get("objetivos")

    assert objetivos, (
        "`objetivos` llega vacio: es el fallo del 12/09, el "
        "carril no tiene a quien mirar y no lo dice como error"
    )

    # Regla 24: y con candidatos de verdad, no con una lista de
    # relleno que pasaria igual.
    assert len(objetivos) == len(CANDIDATOS), objetivos

    assert any(
        o.get("market_price", 0) <= 3_000_000
        for o in objetivos
    ), (
        "el fixture no trae ni un candidato PAGABLE: esta "
        "guardia pasaria sin comprobar nada"
    )

    # 2. LA CAJA. Llegaba `None`, y sin caja el bolsillo del
    #    carril vale 0 y no se puja.
    assert visto.get("caja") == CAJA, visto.get("caja")

    # 3. LO COMPROMETIDO. Llegaba `None`.
    assert visto.get("comprometido") is not None, (
        "`comprometido` llega None: el carril no descontaria lo "
        "ya apartado en pujas vivas"
    )

    assert visto["comprometido"] == COMPROMETIDO

    # 4. EL PRESUPUESTO. Llegaba `None`.
    assert visto.get("presupuesto") is not None, (
        "`presupuesto` llega None"
    )

    # 5. LA CURVA. Caia a su defecto `[[1.0, 0]]`, o sea una
    #    prima de puja del 0,00 % — que no es "no hay prima": es
    #    "no se leyo el tablero".
    assert visto.get("curva") == CURVA, visto.get("curva")

    prima = visto.get("prima_de_puja")

    assert prima not in (None, 0, 0.0), (
        f"`prima_de_puja` llega {prima}: es el defecto de la "
        f"curva, no la curva calibrada del tablero"
    )

    assert abs(prima - 0.29) < 0.01, prima


def test_el_carril_no_busca_el_estado_por_su_cuenta() -> None:
    """
    EL FALLO, EN EL CODIGO Y NO EN EL COMPORTAMIENTO.

    `run_cycle` devuelve {snapshot, result, execution,
    post_action}: `cycle["state"]` NO EXISTE, y leerlo devuelve
    `{}` sin quejarse. Si alguien vuelve a escribirlo, esto se
    pone rojo el mismo dia.
    """

    # Sin comentarios NI DOCSTRINGS: los dos cuentan el
    # incidente y los dos nombran la expresion. Ver
    # `_codigo_vivo`.
    codigo = _codigo_vivo(CICLO.read_text(encoding="utf-8"))

    for trampa in (
        'cycle or {}).get("state")',
        'cycle.get("state")',
        'cycle["state"]',
    ):
        assert trampa not in codigo, (
            f"alguien vuelve a leer `{trampa}`: `run_cycle` no "
            f"devuelve `state` en la raiz y eso da vacio sin "
            f"error"
        )


# ============================================================
# 2. LAS DOS RUTAS, EL MISMO TABLERO
# ============================================================


def test_las_dos_rutas_leen_el_mismo_tablero() -> None:
    """
    LA HERMANA, Y LA QUE IMPIDE QUE VUELVA A PASAR AL LADO.

    El mismo `cycle` por las dos rutas, y el `acquisition` que ve
    cada una tiene que ser EL MISMO OBJETO DE DATOS. Si un dia
    alguien añade una tercera ruta con su propio `.get("state")`,
    esta guardia se pone roja.
    """

    import src.v10_full_autonomous_live as ciclo

    cycle = _cycle_de_forma_real()

    tablero = _tablero_de_mentira()

    vistos = []

    def _falso_estado(c):
        estado = ((c or {}).get("result") or {}).get(
            "state"
        ) or {}

        publicado = {
            "acquisition": tablero,
            "exposure": {},
            "market_clock": {},
            "rival_intelligence": {},
            "solvency_clock": None,
            "operations_locked": False,
            "phase": estado.get("phase"),
            "balance": estado.get("balance"),
            "speculation": estado.get("speculation") or {},
        }

        vistos.append(publicado)

        return publicado

    original = ciclo._estado_publicado

    original_cierres = ciclo._cierres_de_viajes

    import src.actions.carril_executor as ejecutor

    original_correr = ejecutor.correr

    try:
        ciclo._estado_publicado = _falso_estado

        ciclo._cierres_de_viajes = lambda: []

        ejecutor.correr = lambda **k: {"available": True}

        ciclo._correr_el_carril(cycle, "MONITOR_OFFERS")

        ciclo._pujar_en_el_reset(cycle)

    finally:
        ciclo._estado_publicado = original
        ciclo._cierres_de_viajes = original_cierres
        ejecutor.correr = original_correr

    assert len(vistos) == 2, (
        f"solo {len(vistos)} de las dos rutas ha pedido el "
        f"tablero: la otra se lo arma por su cuenta, que es "
        f"exactamente el fallo del 12/09"
    )

    # EL MISMO OBJETO DE DATOS, no dos iguales por casualidad.
    assert vistos[0]["acquisition"] is vistos[1]["acquisition"]

    assert vistos[0]["acquisition"] is tablero


def test_solo_hay_una_puerta_al_tablero() -> None:
    """
    Un solo sitio decide que es "el tablero de esta vuelta".

    Del arbol, no de un grep: se cuentan las funciones del ciclo
    que llaman a `_estado_publicado` y se comprueba que las dos
    rutas que escriben estan entre ellas.
    """

    arbol = ast.parse(CICLO.read_text(encoding="utf-8"))

    quien_lo_llama = set()

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.FunctionDef):
            continue

        for hijo in ast.walk(nodo):

            if (
                isinstance(hijo, ast.Call)
                and isinstance(hijo.func, ast.Name)
                and hijo.func.id == "_estado_publicado"
            ):
                quien_lo_llama.add(nodo.name)

    for ruta in ("_pujar_en_el_reset", "_correr_el_carril"):
        assert ruta in quien_lo_llama, (
            f"`{ruta}` no pide el tablero por la puerta buena: "
            f"se lo arma por su cuenta y comera de un plato "
            f"vacio"
        )

    # Regla 24: si mañana no quedara ninguna, esto no puede pasar
    # en vacio.
    assert len(quien_lo_llama) >= 2, quien_lo_llama


# ============================================================
# 3. Y LO QUE `_estado_publicado` TIENE QUE PUBLICAR
# ============================================================


def test_el_tablero_publica_tambien_el_dinero() -> None:
    """
    `balance` y `speculation` SI vienen en `result["state"]`, y
    `_estado_publicado` ya los usaba por dentro para el reloj de
    solvencia — pero no los publicaba.

    Sin publicarlos, el carril tenia que ir a buscarlos por su
    cuenta, que es como se cayo en el agujero. Un tercer camino a
    los mismos datos es un cuarto fallo esperando.
    """

    import src.v10_full_autonomous_live as ciclo

    publicado = ciclo._estado_publicado(_cycle_de_forma_real())

    for campo in (
        "acquisition",
        "balance",
        "speculation",
        "market_clock",
        "rival_intelligence",
    ):
        assert campo in publicado, (
            f"`_estado_publicado` no publica `{campo}`: quien lo "
            f"necesite se lo buscara por su cuenta"
        )

    # Y los trae del sitio bueno, no vacios.
    assert publicado["balance"] == CAJA, publicado["balance"]

    assert (
        publicado["speculation"]["bid_exposure"][
            "committed_total"
        ]
        == COMPROMETIDO
    ), publicado["speculation"]

    # Forma fija aunque falte todo: nunca lanza.
    for roto in ({}, {"result": {}}, {"result": {"state": {}}}):
        vacio = ciclo._estado_publicado(roto)

        assert isinstance(vacio, dict), roto

        assert "balance" in vacio, roto


TESTS = [
    test_el_carril_no_come_de_un_plato_vacio,
    test_el_carril_no_busca_el_estado_por_su_cuenta,
    test_las_dos_rutas_leen_el_mismo_tablero,
    test_solo_hay_una_puerta_al_tablero,
    test_el_tablero_publica_tambien_el_dinero,
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
        f"EL PLATO DEL CARRIL V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
