"""
El cuadro de objetivos estaba escrito para quien lo programo.

SINTOMA (13/09/2026)

    Doce columnas —ojeador, diverge, se paga solo, con su
    confianza, tener, puesto, sustituye, solo mirar...— y el
    dueño no entendia ninguna. No le faltaba contexto: el cuadro
    hablaba nuestro idioma.

    Y la columna MAS IMPORTANTE, PUJARIAMOS, estaba en blanco
    todos los dias.

LO QUE SE MIDIO SOBRE POR QUE ESTABA VACIA

    NO ESTABA ROTA. `bid` vale 0 porque ninguna fila llega a
    `decision: BID`. Medido sobre el tablero real:

        MERCADO_DE_RIVAL          40 de 60
        SIN_VALOR                  7
        RENDIMIENTO_INSUFICIENTE   5
        SUPERA_PRESUPUESTO         4
        NO_DISPONIBLE              4

    Dos tercios mueren porque la compra a managers esta cerrada
    por regla del dueño, y el resto por valor, rendimiento o
    presupuesto —con el saldo en -1.299.834—.

    O sea que el cero era VERDAD. Lo que estaba mal era
    enseñarlo en blanco: un hueco se lee como un dato que falta,
    no como "no pujariamos".

CINCO COLUMNAS

    QUIEN · CUANTO CUESTA · PARA QUE · PUJARIAMOS · POR QUE

    Y dos de ellas NUNCA vacias, porque "no se sabe" y "no vale"
    son cosas distintas y un hueco las dice las dos.

REGLA 23

    No lee estado externo: las filas se construyen aqui.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile

from pathlib import Path


RAIZ = Path(__file__).parents[2]

MERCADO = RAIZ / "dashboard-v8" / "src" / "pages" / "MarketPage.jsx"

ORDEN = RAIZ / "dashboard-v8" / "src" / "lib" / "orden.js"


# Las que el dueño mando fuera, con sus palabras: "no quiero
# verlo, no me sirve".
FUERA = (
    "OJEADOR",
    "DIVERGE",
    "SE PAGA SOLO",
    "GANAR",
    "BOLSILLO",
    "CON SU CONFIANZA",
    "TENER",
    "PUESTO",
    "SUSTITUYE",
    "SOLO MIRAR",
)

LAS_CINCO = (
    "QUIÉN",
    "CUÁNTO CUESTA",
    "PARA QUÉ",
    "PUJARÍAMOS",
    "POR QUÉ",
)


def _cabeceras() -> list:
    """Las columnas que pinta la tabla de objetivos."""

    fuente = MERCADO.read_text(encoding="utf-8")

    trozo = fuente[
        fuente.index("<thead>") : fuente.index("</thead>")
    ]

    return [
        c.strip()
        for c in re.findall(r"<th[^>]*>([^<]*)</th>", trozo)
    ]


# ============================================================
# 1. CINCO COLUMNAS, NI UNA MAS
# ============================================================


def test_el_cuadro_tiene_cinco_columnas() -> None:
    """Ni una mas. Eran doce."""

    cabeceras = _cabeceras()

    assert cabeceras == list(LAS_CINCO), cabeceras


def test_las_que_sobraban_ya_no_se_pintan() -> None:
    """
    "No quiero verlo, no me sirve."

    NO SE HAN BORRADO: siguen calculandose y se ven en
    AUDITORIA. Lo que no pueden es estar donde el dueño decide.
    """

    cabeceras = " · ".join(_cabeceras()).upper()

    siguen = [f for f in FUERA if f in cabeceras]

    assert not siguen, (
        f"el cuadro sigue pintando {siguen}"
    )

    # Y LO QUE SE FUE DE MERCADO, ESTA EN AUDITORIA. Quitar la
    # caja no es borrar el calculo.
    auditoria = (
        RAIZ / "dashboard-v8" / "src" / "pages" / "AuditPage.jsx"
    ).read_text(encoding="utf-8")

    mercado = MERCADO.read_text(encoding="utf-8")

    for panel in (
        "ViaTenerPanel",
        "SeasonHorizonPanel",
        "RosterExpansionPanel",
    ):
        assert panel in auditoria, (
            f"`{panel}` se fue de MERCADO y no esta en "
            f"AUDITORIA: se ha borrado un calculo en vez de "
            f"moverlo"
        )

        assert panel not in mercado, (
            f"`{panel}` sigue en MERCADO"
        )


def test_pujariamos_nunca_sale_en_blanco() -> None:
    """
    LA COLUMNA MAS IMPORTANTE, Y LA QUE NO PONIA NADA NUNCA.

    No estaba rota: `bid` vale 0 porque ninguna fila llega a
    `decision: BID` —dos tercios mueren en MERCADO_DE_RIVAL,
    que es una puerta cerrada por regla del dueño—.

    El cero era verdad. Lo que estaba mal era enseñarlo en
    blanco: un hueco se lee como un dato que falta.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    assert "no pujaríamos" in fuente, (
        "la columna no dice «no pujaríamos» cuando no se puja: "
        "se queda en blanco y parece que falta el dato"
    )

    # Y cuando SI se puja, sale el importe. Se mira el CUERPO de
    # la tabla, no la cabecera: "PUJARÍAMOS" sale en las dos y
    # la primera rebanada cogia la de arriba.
    cuerpo = fuente[
        fuente.index("<tbody>") : fuente.index("</tbody>")
    ]

    assert 'target.decision === "BID"' in cuerpo, (
        "la columna no mira la decision: pintaria un importe que "
        "el motor no va a pujar"
    )

    assert "formatEuros(target.bid)" in cuerpo, (
        "no pinta el importe cuando la decision es BID"
    )

    assert "no pujaríamos" in cuerpo, cuerpo[:0]


def test_para_que_nunca_sale_en_blanco() -> None:
    """
    "No se sabe" y "no vale" son cosas distintas, y un hueco en
    blanco las dice las dos a la vez.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    trozo = fuente[
        fuente.index("function paraQue(") : fuente.index(
            "function porQue("
        )
    ]

    for caso in (
        "para revender",
        "para el once",
        "no vale",
        "no se sabe",
    ):
        assert caso in trozo, (
            f"`paraQue` no contempla «{caso}»"
        )

    # Y SIEMPRE devuelve algo: no hay camino que acabe vacio.
    assert "return" in trozo

    assert '""' not in trozo.replace('String(target.intent || "")', "").replace(
        'String(target.decision || "")', ""
    ), "hay un camino que devuelve cadena vacia"


def test_el_por_que_enseña_la_frase_entera() -> None:
    """
    La frase ya se escribia y la pantalla se la tragaba.

    Y la del once se añade: es la que explica lo que las columnas
    quitadas decidian —"sustituiria a un titular confirmado por
    alguien que esta al 30 %"—.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    trozo = fuente[fuente.index("function porQue(") :][:900]

    assert "target.reason" in trozo, trozo[:0]

    assert "target.xi_reason" in trozo, (
        "no enseña el motivo del once, que es donde vive la "
        "explicacion que el dueño entendio"
    )

    assert "Sin motivo publicado" in trozo, (
        "sin motivo se quedaria en blanco"
    )


# ============================================================
# 2. EL ORDEN
# ============================================================


def test_el_que_tiene_puja_va_primero() -> None:
    """
    LO QUE ESTA EN JUEGO SE LEE PRIMERO.

    En el orden del propio motor el que tiene puja viva va el
    ULTIMO: la clave lleva `bool(has_live_bid)` y `False` va
    antes que `True`. Tiene sentido para el motor —con ese ya no
    hay nada que hacer— y ninguno para quien mira.

    Se ejecuta de verdad con `node`.
    """

    if shutil.which("node") is None:
        print("     AVISO: sin `node` no se puede ejecutar.")
        return

    guion = """
import { conPujaPrimero } from "./src/lib/orden.js";

const filas = [
  { name: "sin puja A", live_bid: 0 },
  { name: "sin puja B", live_bid: 0 },
  { name: "CON PUJA",   live_bid: 2760000 },
  { name: "sin puja C", live_bid: 0 }
];

const ordenadas = conPujaPrimero(filas);

console.log(JSON.stringify({
  primera: ordenadas[0].name,
  cuantas: ordenadas.length,
  resto: ordenadas.slice(1).map((f) => f.name),
  vacia: conPujaPrimero([]).length,
  rota: conPujaPrimero(null).length
}));
"""

    carpeta = RAIZ / "dashboard-v8"

    fichero = carpeta / "_orden_de_prueba.mjs"

    try:
        fichero.write_text(guion, encoding="utf-8")

        salida = subprocess.run(
            ["node", str(fichero)],
            cwd=str(carpeta),
            capture_output=True,
            text=True,
            timeout=120,
        )

    finally:
        if fichero.exists():
            fichero.unlink()

    assert salida.returncode == 0, (
        salida.stdout + salida.stderr
    )

    visto = json.loads(salida.stdout.strip().splitlines()[-1])

    assert visto["primera"] == "CON PUJA", (
        f"la primera fila es «{visto['primera']}»: lo que esta "
        f"en juego no se lee primero"
    )

    # REGLA 24: si el fixture llegara vacio, esto no probaria
    # nada. Cuatro filas, y una con puja.
    assert visto["cuantas"] == 4, visto

    # Y EL RESTO CONSERVA SU ORDEN. La pantalla no puede tener
    # una opinion propia sobre a quien pujar.
    assert visto["resto"] == [
        "sin puja A",
        "sin puja B",
        "sin puja C",
    ], (
        f"el resto ha cambiado de orden: {visto['resto']}. Eso "
        f"seria una puntuacion nueva, y la pantalla no puede "
        f"tener una"
    )

    # Nunca lanza.
    assert visto["vacia"] == 0, visto
    assert visto["rota"] == 0, visto


def test_la_tabla_usa_ese_orden_y_no_otro() -> None:
    """
    Que la funcion exista no basta: la tabla tiene que recorrerla
    a ella y no a la lista cruda.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    assert "conPujaPrimero(acquisition.targets)" in fuente, (
        "la tabla no ordena por la funcion"
    )

    assert "ordenados.map(" in fuente, (
        "la tabla recorre otra cosa: el orden no se aplicaria"
    )

    assert ORDEN.exists(), "no existe `orden.js`"


TESTS = [
    test_el_cuadro_tiene_cinco_columnas,
    test_las_que_sobraban_ya_no_se_pintan,
    test_pujariamos_nunca_sale_en_blanco,
    test_para_que_nunca_sale_en_blanco,
    test_el_por_que_enseña_la_frase_entera,
    test_el_que_tiene_puja_va_primero,
    test_la_tabla_usa_ese_orden_y_no_otro,
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
        f"EL CUADRO DE OBJETIVOS V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
