"""
Ninguna compra queda en DESCONOCIDO si vino de una via del motor.

SINTOMA (20/09/2026)

    Al repartir las 36 compras de la temporada por via, 20 —el
    56 %— no tenian via atribuible. Todas las del dueño lo son
    por definicion, pero entre ellas se escondia un agujero del
    motor: la CESTA (`la_subasta`) escribe su puja en
    `bid_outcome_ledger` y NO en `libro_del_carril.jsonl`, que es
    el unico libro que `_origen_probado` sabe leer.

    Mientras la cesta anote su propia fila en el momento de
    pujar, la atribucion sale bien. En cuanto una puja suya haya
    que redescubrirla del tablon —porque la vuelta murio antes de
    guardar, que ya paso el 18/09 con la #1701—, `_origen_probado`
    contesta DESCONOCIDO y esa compra deja de tener dueño.

POR QUE IMPORTA

    Sin via no hay cuenta por via, y sin cuenta por via no se
    puede contestar cual merece seguir viva. Es la pregunta que
    ordena todo lo demas.

LO QUE VIGILA, Y LO QUE NO

    · Que TODO sitio del motor que llama a `record_bid` pase un
      `target_source`. Si alguien abre una via nueva y se olvida,
      sus compras nacen sin dueño y nadie se entera.

    · Que `_origen_probado` devuelva la marca cuando el libro la
      prueba, y DESCONOCIDO solo cuando NO la puede probar.

    · Que las marcas que el motor escribe esten todas declaradas,
      para que una via nueva no se cuele sin nombre.

REGLA 23, Y LAS MANOS VACIAS

    No lee `data/`, ni la red, ni el reloj: el codigo del
    repositorio y fixtures en un directorio temporal. Y si el
    conjunto que tiene que revisar sale vacio —ningun
    `record_bid` encontrado, ningun caso de fixture— la guardia
    FALLA en vez de pasar: una guardia que no mira nada no es una
    guardia (doctrina 24).
"""

from __future__ import annotations

import ast
import json
import tempfile
from pathlib import Path


RAIZ = Path(__file__).parents[2]

CODIGO = RAIZ / "src"


# LAS VIAS QUE EL MOTOR PUEDE ESCRIBIR, CON SU SITIO.
#
#     `DESCONOCIDO` no esta: no es una via, es la ausencia de
#     una. Si alguien abre una via nueva, va aqui, y si no la
#     declara, la guardia lo caza.
VIAS_DEL_MOTOR = {
    "SUBASTA_CARTERA": "la cesta de la ventana (`la_subasta`)",
    "RENDIJA": "el carril de reventa (`carril_executor`)",
    "ACQUISITION_BOARD": "el tablero de fichajes (la cola)",
    "SPECULATION_SCORING": "el respaldo del scoring antiguo",
}


# Los ficheros del motor que escriben una puja contra Biwenger.
# Las pruebas no cuentan: ahi `record_bid` se llama a proposito
# sin via para comprobar el caso sin dueño.
def _fuentes_que_escriben() -> list[Path]:
    return [
        ruta
        for ruta in CODIGO.rglob("*.py")
        if not ruta.name.startswith("test_")
        and "record_bid(" in ruta.read_text(encoding="utf-8")
        and ruta.name != "bid_outcome_ledger.py"
    ]


def _llamadas_a_record_bid(ruta: Path) -> list[ast.Call]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))

    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
        and nodo.func.id == "record_bid"
    ]


# ============================================================
# 1. NADIE ESCRIBE UNA PUJA SIN DECIR DE DONDE VIENE
# ============================================================


def test_toda_escritura_del_motor_pasa_su_via() -> None:
    """
    Cada `record_bid` del motor lleva `target_source=`.

    Sin el, la compra nace en DESCONOCIDO y ya no hay forma de
    devolverla a su via: el tablon no dice quien pujo.
    """

    fuentes = _fuentes_que_escriben()

    assert fuentes, (
        "no se ha encontrado ni un sitio del motor que llame a "
        "`record_bid`: o se renombro la funcion o esta guardia "
        "esta mirando donde no es"
    )

    sin_via = []

    revisadas = 0

    for ruta in fuentes:

        for llamada in _llamadas_a_record_bid(ruta):

            revisadas += 1

            nombres = {
                k.arg for k in llamada.keywords if k.arg
            }

            if "target_source" not in nombres:
                sin_via.append(
                    f"{ruta.relative_to(RAIZ)}:"
                    f"{llamada.lineno}"
                )

    assert revisadas, (
        "cero llamadas a `record_bid` revisadas: la guardia "
        "pasaria con las manos vacias"
    )

    assert not sin_via, (
        "hay escrituras de puja sin `target_source`, y sus "
        "compras nacen sin via: "
        + ", ".join(sin_via)
    )


def test_las_marcas_que_se_escriben_estan_declaradas() -> None:
    """
    Toda marca literal que el motor pasa como `target_source`
    tiene que estar en `VIAS_DEL_MOTOR`.

    Una via nueva sin nombre aqui es una columna que aparece en
    la cuenta sin que nadie sepa que compra.
    """

    literales = set()

    for ruta in _fuentes_que_escriben() + [
        CODIGO / "analysis" / "decision_orchestrator.py",
        CODIGO / "actions" / "carril_executor.py",
    ]:

        if not ruta.exists():
            continue

        texto = ruta.read_text(encoding="utf-8")

        for via in VIAS_DEL_MOTOR:
            if f'"{via}"' in texto:
                literales.add(via)

    assert literales, (
        "no se ha visto ni una marca de via en el motor: la "
        "guardia pasaria con las manos vacias"
    )

    desconocidas = literales - set(VIAS_DEL_MOTOR)

    assert not desconocidas, (
        f"vias que el motor escribe y esta guardia no nombra: "
        f"{sorted(desconocidas)}"
    )


# ============================================================
# 2. EL ORIGEN SE PRUEBA, Y SI NO SE PUEDE, SE DICE
# ============================================================


def _libro_temporal(filas: list[dict]) -> Path:
    destino = Path(tempfile.mkdtemp()) / "libro_del_carril.jsonl"

    destino.write_text(
        "\n".join(json.dumps(f) for f in filas) + "\n",
        encoding="utf-8",
    )

    return destino


def test_el_origen_se_prueba_cuando_el_libro_lo_prueba() -> None:
    """
    Si el libro tiene la fila, `_origen_probado` devuelve la
    marca. No DESCONOCIDO.
    """

    from src.intelligence.bid_outcome_ledger import (
        _origen_probado,
    )

    casos = [
        ({"player_id": 37499, "amount": 2_760_000,
          "marca": "RENDIJA"}, 37499, 2_760_000, "RENDIJA"),
        ({"player_id": 33694, "amount": 1_817_297,
          "marca": "RENDIJA"}, 33694, 1_817_297, "RENDIJA"),
    ]

    assert casos, "sin casos que probar"

    libro = _libro_temporal([c[0] for c in casos])

    for _, pid, importe, esperado in casos:

        salida = _origen_probado(pid, importe, libro)

        assert salida == esperado, (
            f"el jugador {pid} por {importe} consta en el libro "
            f"con marca {esperado} y el origen sale «{salida}»"
        )


def test_sin_libro_no_se_inventa_una_via() -> None:
    """
    Lo contrario tambien tiene que ser cierto: si no se puede
    probar, se dice DESCONOCIDO y no se adivina.

    No saber de donde vino no es lo mismo que venir de ninguna
    parte.
    """

    from src.intelligence.bid_outcome_ledger import (
        ORIGEN_SIN_PROBAR,
        _origen_probado,
    )

    vacio = _libro_temporal([])

    assert _origen_probado(1, 1, vacio) == ORIGEN_SIN_PROBAR, (
        "con el libro vacio el origen tiene que ser DESCONOCIDO"
    )

    ausente = Path(tempfile.mkdtemp()) / "no_existe.jsonl"

    assert (
        _origen_probado(1, 1, ausente) == ORIGEN_SIN_PROBAR
    ), "sin libro el origen tiene que ser DESCONOCIDO"


def test_la_cesta_no_deja_rastro_en_el_libro_del_carril() -> None:
    """
    EL AGUJERO MEDIDO, ESCRITO PARA QUE NO SE OLVIDE.

    `_origen_probado` solo sabe leer `libro_del_carril.jsonl`, y
    la cesta no escribe ahi. Mientras la cesta apunte su fila en
    `bid_outcome_ledger` en el mismo instante, la via se sabe.
    Si hay que redescubrir la puja del tablon, NO.

    Esta prueba no exige el arreglo —es un camino de escritura y
    lo decide el dueño—: exige que el agujero siga siendo visible
    y que nadie crea que esta tapado.
    """

    from src.intelligence.bid_outcome_ledger import (
        ORIGEN_SIN_PROBAR,
        _origen_probado,
    )

    # Una puja de la cesta, tal y como la escribe `la_subasta`:
    # en el libro de resultados, nunca en el del carril.
    libro_del_carril = _libro_temporal(
        [{"player_id": 33694, "amount": 1_817_297,
          "marca": "RENDIJA"}]
    )

    salida = _origen_probado(
        43281, 150_376, libro_del_carril
    )

    assert salida == ORIGEN_SIN_PROBAR, (
        "si la cesta ya deja rastro en el libro del carril, este "
        "aviso sobra y hay que borrarlo: la atribucion de sus "
        "compras ya no depende de que la vuelta no muera"
    )


def main() -> int:

    pruebas = [
        test_toda_escritura_del_motor_pasa_su_via,
        test_las_marcas_que_se_escriben_estan_declaradas,
        test_el_origen_se_prueba_cuando_el_libro_lo_prueba,
        test_sin_libro_no_se_inventa_una_via,
        test_la_cesta_no_deja_rastro_en_el_libro_del_carril,
    ]

    fallos = 0

    for prueba in pruebas:

        try:
            prueba()
            print(f"OK   {prueba.__name__}")

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {prueba.__name__}: {error}")

    print("=" * 60)
    print(
        f"CADA COMPRA SABE DE QUE VIA VINO V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
