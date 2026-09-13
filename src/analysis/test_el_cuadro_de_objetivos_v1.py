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

# El guion que comprueba los bloques, con node.
GUION_DE_BLOQUES = 'import { agrupado } from "./src/lib/orden.js";\n\nconst filas = [\n  { id: 10, name: "once 1",     intent: "XI_UPGRADE" },\n  { id: 11, name: "once 2",     intent: "XI_UPGRADE" },\n  { id: 20, name: "revender A", intent: "SPECULATION" },\n  { id: 21, name: "revender B", intent: "SPECULATION" },\n  { id: 22, name: "revender C", intent: "SPECULATION" },\n  { id: 30, name: "basura",     decision: "SIN_VALOR" }\n];\n\nconst bloques = agrupado(filas, [22, 21, 20]);\n\nconst de = (clave) =>\n  (bloques.find((b) => b.clave === clave) || { filas: [] })\n    .filas.map((f) => f.name);\n\nconsole.log(JSON.stringify({\n  claves: bloques.map((b) => b.clave),\n  once: de("once"),\n  revender: de("revender"),\n  noVale: de("noVale"),\n  sinOrden: agrupado(filas, [])\n    .find((b) => b.clave === "revender")\n    .filas.map((f) => f.name)\n}));\n'


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
    # El cuerpo son ahora VARIOS `<tbody>`, uno por bloque, asi
    # que se mira desde donde empieza el mapa de bloques.
    cuerpo = fuente[
        fuente.index("bloques.map(") : fuente.index("</table>")
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
import { agrupado } from "./src/lib/orden.js";

const filas = [
  { id: 1, name: "sin puja A", live_bid: 0, intent: "SPECULATION" },
  { id: 2, name: "sin puja B", live_bid: 0, intent: "SPECULATION" },
  { id: 3, name: "CON PUJA",   live_bid: 2760000, intent: "SPECULATION" },
  { id: 4, name: "sin puja C", live_bid: 0, intent: "SPECULATION" }
];

const bloques = agrupado(filas, [1, 2, 4]);

console.log(JSON.stringify({
  primerBloque: bloques[0].clave,
  primera: bloques[0].filas[0].name,
  cuantas: bloques.reduce((n, b) => n + b.filas.length, 0),
  resto: bloques[1].filas.map((f) => f.name),
  vacia: agrupado([], []).length,
  rota: agrupado(null, null).length
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

    assert visto["primerBloque"] == "conPuja", visto

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
        f"el resto no sigue el orden del carril: "
        f"{visto['resto']}"
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

    assert "agrupado(" in fuente, (
        "la tabla no agrupa por «para que»"
    )

    assert "bloque.filas.map(" in fuente, (
        "la tabla recorre otra cosa: el orden no se aplicaria"
    )

    assert ORDEN.exists(), "no existe `orden.js`"


def test_cada_bloque_usa_su_propio_orden() -> None:
    """
    NO HAY UN ORDEN UNICO PORQUE NO HAY UN SOLO INTERES.

    "Para el once" se mide en PUNTOS y "para revender" en PRIMA
    DEL COMPUTER, y no tenemos el cambio entre las dos unidades.
    Ordenar los sesenta por uno solo haria que la mitad de las
    filas salieran ordenadas por un criterio que no decide sobre
    ellas.

        el once      conserva el orden de LLEGADA, que ya es el
                     del tablon
        revender     por `orden_del_carril`, la lista de ids que
                     publica la telemetria llamando a
                     `orden_de_preferencia`, la MISMA funcion del
                     motor

    Si algun dia alguien unifica los dos ordenes, esta guardia se
    pone roja y se habla antes, en vez de enterarse por la
    pantalla.
    """

    if shutil.which("node") is None:
        print("     AVISO: sin `node` no se puede ejecutar.")
        return

    carpeta = RAIZ / "dashboard-v8"

    fichero = carpeta / "_bloques_de_prueba.mjs"

    try:
        fichero.write_text(GUION_DE_BLOQUES, encoding="utf-8")

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

    # REGLA 24: si el fixture no trajera los tres bloques, esto
    # no probaria nada.
    assert visto["claves"] == ["once", "revender", "noVale"], (
        visto
    )

    # EL ONCE: orden de llegada, que es el del TABLON.
    assert visto["once"] == ["once 1", "once 2"], (
        f"el bloque del once ha cambiado de orden: "
        f"{visto['once']}. Ese orden es el del tablon y la "
        f"pantalla no puede tener otro"
    )

    # REVENDER: el del CARRIL, aunque llegue al reves.
    assert visto["revender"] == [
        "revender C",
        "revender B",
        "revender A",
    ], (
        f"el bloque de revender no usa el orden del carril: "
        f"{visto['revender']}"
    )

    # NO VALE, al final.
    assert visto["noVale"] == ["basura"], visto

    # Y SIN LA LISTA DEL MOTOR no se inventa un orden: se queda
    # como llega.
    assert visto["sinOrden"] == [
        "revender A",
        "revender B",
        "revender C",
    ], (
        f"sin el orden del motor la pantalla se ha inventado "
        f"uno: {visto['sinOrden']}"
    )


def test_cada_bloque_lleva_su_numero() -> None:
    """
    Hoy no se ve cuantos hay de cada cosa, y es informacion
    gratis.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    assert "bloque.titulo" in fuente, (
        "los bloques no llevan cabecera"
    )

    assert "bloque.filas.length" in fuente, (
        "la cabecera no dice cuantos hay"
    )

    assert "bloques.map(" in fuente, (
        "la tabla no recorre los bloques"
    )


def test_el_orden_del_carril_lo_publica_el_motor() -> None:
    """
    LA PANTALLA NO REIMPLEMENTA LA TABLA DE PRIMAS MEDIDAS.

    `expected_buyback_percent` sale de 34 recompras medidas. Si
    la pantalla ordenara por su cuenta, esa tabla viviria en dos
    sitios y el dia que se remida cambiaria uno solo.

    La telemetria llama a `orden_de_preferencia` —la del motor— y
    publica el resultado como lista de ids.
    """

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert "orden_del_carril" in estado, (
        "la telemetria no publica el orden del carril"
    )

    assert "orden_de_preferencia(" in estado, (
        "no se usa la funcion del motor"
    )

    # Y la pantalla lo LEE, no lo calcula.
    orden = ORDEN.read_text(encoding="utf-8")

    for inventado in (
        "expected_buyback_percent",
        "3.67",
        "2.85",
        "1.52",
    ):
        assert inventado not in orden, (
            f"`orden.js` lleva `{inventado}`: la tabla de primas "
            f"medidas viviria en dos sitios"
        )


TESTS = [
    test_el_cuadro_tiene_cinco_columnas,
    test_las_que_sobraban_ya_no_se_pintan,
    test_pujariamos_nunca_sale_en_blanco,
    test_para_que_nunca_sale_en_blanco,
    test_el_por_que_enseña_la_frase_entera,
    test_el_que_tiene_puja_va_primero,
    test_la_tabla_usa_ese_orden_y_no_otro,
    test_cada_bloque_usa_su_propio_orden,
    test_cada_bloque_lleva_su_numero,
    test_el_orden_del_carril_lo_publica_el_motor,
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
