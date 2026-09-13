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

# El guion que comprueba el orden, con node.
GUION_DEL_ORDEN = 'import { porInteres, accionDe } from "./src/lib/orden.js";\n\nconst filas = [\n  { id: 1, name: "de un rival", decision: "MERCADO_DE_RIVAL" },\n  { id: 2, name: "sin caja 1",  decision: "SUPERA_PRESUPUESTO" },\n  { id: 3, name: "no vale",     decision: "SIN_VALOR" },\n  { id: 4, name: "CON PUJA",    decision: "MERCADO_DE_RIVAL", live_bid: 2760000 },\n  { id: 5, name: "sin caja 2",  decision: "SUPERA_PRESUPUESTO" },\n  { id: 6, name: "a pujar",     decision: "BID" }\n];\n\nconst f = porInteres(filas);\n\nconsole.log(JSON.stringify({\n  primera: f[0].name,\n  cuantas: f.length,\n  orden: f.map((x) => x.name),\n  acciones: f.map(accionDe),\n  vacia: porInteres([]).length,\n  rota: porInteres(null).length\n}));\n'


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

LAS_ONCE = (
    "QUIÉN",
    "EST.",
    "PTS",
    "TITULAR",
    "CUÁNTO CUESTA",
    "QUIÉN LO VENDE",
    "TERMINA EN",
    "ACCIÓN",
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


def test_el_cuadro_tiene_las_columnas_del_diseño() -> None:
    """
    Once, en este orden, y las del diseño aprobado.

    Eran doce sin sentido; se quedaron en cinco; y el diseño las
    devuelve a once, pero ahora todas se leen: estado, puntos,
    titularidad, quien vende, cuando termina y que se va a hacer.
    """

    cabeceras = _cabeceras()

    assert cabeceras == list(LAS_ONCE), cabeceras


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

    assert 'fila.decision === "BID"' in cuerpo, (
        "la columna no mira la decision: pintaria un importe que "
        "el motor no va a pujar"
    )

    assert "formatEuros(fila.bid)" in cuerpo, (
        "no pinta el importe cuando la decision es BID"
    )

    assert "no pujaríamos" in cuerpo, cuerpo[:0]


def test_para_que_nunca_sale_en_blanco() -> None:
    """
    "No se sabe" y "no vale" son cosas distintas, y un hueco en
    blanco las dice las dos a la vez.
    """

    # `paraQueDe` y `accionDe` viven en `orden.js` desde el
    # diseño de los dos cuadros: se prueban donde estan.
    orden = ORDEN.read_text(encoding="utf-8")

    trozo = orden[orden.index("export function paraQueDe(") :]

    for caso in ("para revender", "para el once"):
        assert caso in trozo, (
            f"`paraQueDe` no contempla «{caso}»"
        )

    # Y SIEMPRE devuelve algo: sin via conocida, un guion, que es
    # decir "no se sabe" y no dejar un hueco.
    assert 'return "—"' in trozo, (
        "hay un camino que deja la celda vacia"
    )

    # LA ACCION TAMPOCO. Ocho estados, todos con palabras.
    accion = orden[
        orden.index("export function accionDe(") : orden.index(
            "const ESCALON"
        )
    ]

    for caso in (
        "puja puesta",
        "pujar",
        "no hay caja",
        "rinde poco",
        "lo vende un rival",
        "no vale",
        "no disponible",
        "no compensa",
    ):
        assert caso in accion, (
            f"`accionDe` no contempla «{caso}»"
        )

    assert '"sin decidir"' in accion, (
        "sin decision la celda se quedaria vacia"
    )


def test_el_por_que_enseña_la_frase_entera() -> None:
    """
    La frase ya se escribia y la pantalla se la tragaba.

    Y la del once se añade: es la que explica lo que las columnas
    quitadas decidian —"sustituiria a un titular confirmado por
    alguien que esta al 30 %"—.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    trozo = fuente[fuente.index("function porQue(") :][:900]

    assert "fila.reason" in trozo, (
        "no enseña el motivo del motor"
    )

    assert "fila.xi_reason" in trozo, (
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
    UNA SOLA LISTA, DE MAYOR A MENOR INTERES.

    Estuvo agrupada por "para que" una tarde. El dueño lo vio y
    prefiere lista corrida: lo que quiere saber no es de que tipo
    es cada fila, sino CUANTO LE FALTA A PEPE PARA ACTUAR.

        0  puja puesta
        1  pujar
        2  no compensa · rinde poco · no hay caja
        3  lo vende un rival
        4  no vale · no disponible

    Y dentro de cada escalon, el orden en que LLEGA — que ya es
    el del motor. Cero puntuaciones inventadas.

    Se ejecuta de verdad con `node`.
    """

    if shutil.which("node") is None:
        print("     AVISO: sin `node` no se puede ejecutar.")
        return

    carpeta = RAIZ / "dashboard-v8"

    fichero = carpeta / "_orden_de_prueba.mjs"

    try:
        fichero.write_text(GUION_DEL_ORDEN, encoding="utf-8")

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

    # REGLA 24: si el fixture llegara vacio, esto no probaria
    # nada. Seis filas, una con puja.
    assert visto["cuantas"] == 6, visto

    assert visto["primera"] == "CON PUJA", (
        f"la primera fila es «{visto['primera']}»: lo que esta "
        f"en juego no se lee primero"
    )

    # EL ESCALON MANDA, y dentro de el se conserva la llegada.
    assert visto["orden"] == [
        "CON PUJA",
        "a pujar",
        "sin caja 1",
        "sin caja 2",
        "de un rival",
        "no vale",
    ], (
        f"el orden no sigue el escalon de accion: "
        f"{visto['orden']}"
    )

    # LA ACCION, EN CRISTIANO y nunca vacia.
    assert visto["acciones"] == [
        "puja puesta",
        "pujar",
        "no hay caja",
        "no hay caja",
        "lo vende un rival",
        "no vale",
    ], visto

    # Nunca lanza.
    assert visto["vacia"] == 0, visto
    assert visto["rota"] == 0, visto


def test_la_tabla_usa_ese_orden_y_no_otro() -> None:
    """
    Que la funcion exista no basta: la tabla tiene que recorrerla
    a ella y no a la lista cruda.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    assert "porInteres(" in fuente, (
        "la tabla no ordena por interes"
    )

    assert "filas.map(" in fuente, (
        "la tabla recorre otra cosa: el orden no se aplicaria"
    )

    assert ORDEN.exists(), "no existe `orden.js`"


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


def test_la_cuenta_atras_es_por_fila() -> None:
    """
    CADA VENTA TIENE SU HORA DE FIN, Y NO ES LA DEL RESET.

    La cuenta atras usaba el reset para todas. Hoy todas vencen
    ahi, asi que daba igual — y por eso nadie lo habria notado.
    El dia que un rival publique algo con otro vencimiento, el
    numero seria falso.

    Cada venta trae su `until` en `market.sales`. Esta guardia
    exige que la fila lo lleve y que la pantalla lo use.
    """

    # 1. LA TELEMETRIA LO PUBLICA POR FILA.
    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '_fila["until"]' in estado, (
        "la telemetria no publica la hora de fin de cada venta: "
        "la cuenta atras tendria que inventarsela"
    )

    assert "market" in estado and "sales" in estado

    # 2. Y SALE DEL `until` DE SU VENTA, no del reset.
    fuente = MERCADO.read_text(encoding="utf-8")

    cuerpo = fuente[
        fuente.index("<tbody>") : fuente.index("</tbody>")
    ]

    assert "until={fila.until}" in cuerpo, (
        "la cuenta atras no usa el `until` de la fila"
    )

    for del_reset in (
        "marketClock",
        "seconds_to_reset",
        "hours_to_reset",
    ):
        assert del_reset not in cuerpo, (
            f"la cuenta atras vuelve a usar `{del_reset}`: seria "
            f"la misma para todas las filas"
        )

    # 3. DOS VENCIMIENTOS DISTINTOS DAN DOS CUENTAS DISTINTAS.
    #    Se comprueba sobre la funcion que las calcula.
    componente = fuente[
        fuente.index("function CuentaAtras(") :
    ][:1400]

    assert "setInterval" in componente, (
        "la cuenta atras no corre: se quedaria congelada"
    )

    assert "Number(until)" in componente, componente[:0]

    # Sin `until` NO se pinta un cero.
    assert "sin dato" in componente, (
        "sin hora de fin pintaria un cero, que se lee como "
        "«vence ya»"
    )

    # Y en ambar por debajo de una hora.
    assert "3600" in componente, (
        "no avisa cuando queda menos de una hora"
    )


def test_las_columnas_nuevas_salen_del_catalogo() -> None:
    """
    PUNTOS Y PARTIDOS JUGADOS, DE DONDE VIENEN.

    `acquisition.targets` no trae `points` ni los partidos: estan
    en `catalog.data.players[id]`, que YA SE PIDE en el ciclo.
    Es juntarlo, no pedir mas.

    Y no se calcula nada: se copia.
    """

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert "_catalogo_por_id" in estado, (
        "no hay de donde sacar los puntos"
    )

    for campo in ("points", "playedHome", "playedAway"):
        assert campo in estado, (
            f"la telemetria no lee `{campo}` del catalogo"
        )

    assert '_fila["points"]' in estado, (
        "los puntos no llegan a la fila"
    )

    assert '_fila["played"]' in estado, (
        "los partidos jugados no llegan a la fila"
    )

    # LA PANTALLA LOS PINTA.
    fuente = MERCADO.read_text(encoding="utf-8")

    cuerpo = fuente[
        fuente.index("<tbody>") : fuente.index("</tbody>")
    ]

    assert "fila.points" in cuerpo, "no se pintan los puntos"

    assert "fila.starter_probability" in cuerpo, (
        "no se pinta la titularidad"
    )

    assert "fila.status" in cuerpo, "no se pinta el estado"

    assert "fila.team_id" in cuerpo, "no se pinta el escudo"


def test_el_sancionado_no_se_inventa_la_tarjeta() -> None:
    """
    Biwenger dice `sanctioned` y NO dice si fue doble amarilla o
    roja directa.

    Se pinta tarjeta roja para los dos. Inventar la distincion
    seria peor que no tenerla: parece un dato y no lo es.
    """

    fuente = MERCADO.read_text(encoding="utf-8")

    estado = fuente[
        fuente.index("function Estado(") :
    ][:1200]

    assert "sanctioned" in estado, estado[:0]

    assert "card red" in estado, (
        "el sancionado no se pinta con tarjeta"
    )

    for inventado in ("amarilla", "doble", "directa"):
        assert inventado not in estado.lower(), (
            f"se inventa la distincion `{inventado}`, que "
            f"Biwenger no publica"
        )


TESTS = [
    test_el_cuadro_tiene_las_columnas_del_diseño,
    test_las_que_sobraban_ya_no_se_pintan,
    test_pujariamos_nunca_sale_en_blanco,
    test_para_que_nunca_sale_en_blanco,
    test_el_por_que_enseña_la_frase_entera,
    test_el_que_tiene_puja_va_primero,
    test_la_tabla_usa_ese_orden_y_no_otro,
    test_el_orden_del_carril_lo_publica_el_motor,
    test_la_cuenta_atras_es_por_fila,
    test_las_columnas_nuevas_salen_del_catalogo,
    test_el_sancionado_no_se_inventa_la_tarjeta,
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
