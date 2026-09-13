"""
Lo que MERCADO enseña, y lo que no puede enseñar dos veces.

DE DONDE SALEN ESTAS GUARDIAS (13/09/2026, noche)

    El dueño abrio la pantalla de verdad e hizo fotos. Seis
    cosas mal, y ninguna la habia cazado nada.

LO QUE VIGILAN

    1. Que ningun porcentaje de la pantalla pueda salir por
       encima de 100. En TITULAR salia `10000%`.

    2. Que no haya dos cuadros pintando las mismas catorce
       ofertas.

    3. Que lo que la telemetria publica llegue al lector. Los
       dos cuadros nuevos salieron vacios con el dato delante:
       `normalizeStatus` es una lista blanca y no los nombraba.

    4. Que los tres cuadros lleven scroll y no recorten.

REGLA 23

    No lee estado externo: solo los ficheros del repositorio.
"""

from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).parents[2]

FUENTE = RAIZ / "dashboard-v8" / "src"

MERCADO = FUENTE / "pages" / "MarketPage.jsx"

STATUS_JS = FUENTE / "lib" / "status.js"

LIGA = FUENTE / "components" / "TodaLaLigaPanel.jsx"

VENTA = FUENTE / "components" / "LoNuestroALaVentaPanel.jsx"


def _sin_comentarios(texto: str) -> str:
    texto = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)

    return re.sub(r"(?m)^\s*//.*$", " ", texto)


# ============================================================
# 1. NINGUN PORCENTAJE PASA DE 100
# ============================================================


def test_ningun_porcentaje_pasa_de_100() -> None:
    """
    UN PORCENTAJE QUE SE SALE DE 0-100 NO ES UN NUMERO GRANDE:
    ES UN NUMERO ROTO.

    SINTOMA

        En TITULAR salian `10000%`, `8000%`, `7000%`, `5000%`.

    CAUSA

        `starter_probability` lo publica el motor de 0 a 100.
        MERCADO lo multiplicaba otra vez por cien. Los otros tres
        sitios que pintan ese mismo campo —`SquadTable`,
        `DoctrinaPanel` y `PosiblesCambiosPanel`— lo redondean y
        ya esta: cuatro lectores, uno se salia.

    CONSECUENCIA

        Un numero imposible en pantalla hace dudar de TODA la
        tabla, no solo de esa columna. Y la barra de al lado
        estaba igual de rota —con `width: 10000%` el navegador
        la recorta y parece llena—, asi que el error se veia una
        vez y estaba dos.

    ESTA GUARDIA MIRA EL CODIGO, no un numero de hoy: hoy las
    sesenta filas traen `null` y la columna dice "sin dato". El
    dia que el dato vuelva, el fallo volveria con el.
    """

    fuente = _sin_comentarios(
        MERCADO.read_text(encoding="utf-8")
    )

    # 1. NADIE MULTIPLICA UNA PROBABILIDAD POR CIEN.
    #
    #    `win_probability` si viene de 0 a 1 y se multiplica en
    #    otros paneles: aqui se vigila el campo que viene ya en
    #    porcentaje.
    for multiplica in (
        "starter_probability) * 100",
        "starter_probability * 100",
        "probabilidad) * 100",
        "probabilidad * 100",
    ):
        assert multiplica not in fuente, (
            f"MERCADO vuelve a multiplicar por cien un dato que "
            f"ya viene de 0 a 100: `{multiplica}`"
        )

    # 2. Y HAY UN FRENO EXPLICITO.
    #
    #    No basta con quitar la multiplicacion: si el motor
    #    publicara algo raro, la pantalla tiene que decirlo en
    #    vez de pintarlo.
    titular = fuente[fuente.index("function Titular(") :][:1600]

    assert "fuera de rango" in titular, (
        "la celda de TITULAR no frena un porcentaje imposible: "
        "pintaria 10000 % otra vez sin avisar"
    )

    assert "> 100" in titular, (
        "no hay ningun tope de 100 en la celda de TITULAR"
    )

    # 3. LAS CELDAS DE PORCENTAJE DE ESTA PANTALLA, UNA A UNA.
    celdas = _celdas_de_porcentaje()

    # REGLA 24: con la lista vacia esto no probaria nada.
    assert len(celdas) >= 3, (
        f"solo se han encontrado {len(celdas)} celdas de "
        f"porcentaje: la guardia no esta mirando donde dice"
    )

    # SOLO `starter_probability`.
    #
    #     `win_probability` SI viene de 0 a 1 —medido hoy sobre
    #     las 41 filas que lo traen: todas entre 0,0 y 0,0— y
    #     multiplicarlo por cien es correcto. Meterlo en la misma
    #     lista convertiria esta guardia en un falso permanente.
    malas = {
        donde: expresion
        for donde, expresion in celdas.items()
        if "* 100" in expresion
        and "starter_probability" in expresion
    }

    assert not malas, (
        "estas celdas multiplican por cien una probabilidad que "
        "ya viene en porcentaje:\n"
        + "\n".join(f"   {k}: {v}" for k, v in malas.items())
    )


def _celdas_de_porcentaje() -> dict:
    """
    Cada trozo de JSX que pinta un `%`, con su fichero y linea.

    Se busca el simbolo en el texto pintado, que es lo que ve el
    dueño: no hace falta adivinar como se llama la variable.
    """

    celdas = {}

    for fichero in sorted(FUENTE.rglob("*.jsx")):

        texto = _sin_comentarios(
            fichero.read_text(encoding="utf-8")
        )

        for numero, linea in enumerate(
            texto.splitlines(), start=1
        ):
            if "%" not in linea:
                continue

            # El `%` de una plantilla de anchura CSS no es un
            # porcentaje que se lea: es el ancho de una barra.
            if "width" in linea:
                continue

            if "100" not in linea and "pct" not in linea:
                continue

            donde = (
                f"{fichero.relative_to(RAIZ).as_posix()}:"
                f"{numero}"
            )

            celdas[donde] = linea.strip()

    return celdas


# ============================================================
# 2. NO HAY DOS CUADROS CON LAS MISMAS OFERTAS
# ============================================================


def test_no_hay_dos_cuadros_con_las_mismas_ofertas() -> None:
    """
    «OFERTAS RECIBIDAS» Y «LO NUESTRO A LA VENTA» SON EL MISMO
    DATO: las mismas catorce filas.

    CONSECUENCIA DE QUE CONVIVAN

        Dos tablas con las mismas filas y columnas distintas
        —una con reloj por fila, la otra con uno solo para
        todas— acaban enseñando numeros que no coinciden. Y
        entonces no se cree ninguna de las dos.

    El viejo se queda como RESPALDO, para el dia que la
    telemetria no publique el nuevo: mejor la tabla vieja que un
    hueco. Pero no a la vez.
    """

    fuente = _sin_comentarios(
        MERCADO.read_text(encoding="utf-8")
    )

    # 1. LOS DOS ESTAN EN LA PAGINA.
    assert "<OffersPanel" in fuente, (
        "el cuadro de respaldo ha desaparecido: el dia que la "
        "telemetria falle no habria nada"
    )

    assert "<LoNuestroALaVentaPanel" in fuente, (
        "el cuadro nuevo no esta montado"
    )

    # 2. EL VIEJO VA CONDICIONADO A QUE EL NUEVO NO TENGA DATOS.
    i = fuente.index("<OffersPanel")

    antes = fuente[max(0, i - 500) : i]

    assert "loNuestroALaVenta" in antes, (
        "`OffersPanel` se pinta sin mirar si el cuadro nuevo "
        "tiene datos: los dos saldrian a la vez con las mismas "
        "catorce filas"
    )

    assert "!data.loNuestroALaVenta?.available" in antes, (
        "la condicion no es «el nuevo no tiene datos»:\n"
        + antes[-300:]
    )

    # 3. Y EL NUEVO SE PINTA SIEMPRE.
    #
    #    Si tambien fuera condicional, podria no salir ninguno de
    #    los dos y la pagina se quedaria sin nada. El cuadro
    #    nuevo ya se apaga solo por dentro: cuando no hay datos
    #    dice por que, que es lo que se quiere ver.
    j = fuente.index("<LoNuestroALaVentaPanel")

    linea = fuente[:j].rsplit(chr(10), 1)[-1]

    assert "&&" not in linea and "?" not in linea, (
        f"el cuadro nuevo se pinta bajo condicion: podrian "
        f"apagarse los dos: {linea.strip()}"
    )


# ============================================================
# 3. LO QUE SE PUBLICA, LLEGA
# ============================================================


def test_lo_que_publica_la_telemetria_llega_al_cuadro() -> None:
    """
    `normalizeStatus` ES UNA LISTA BLANCA.

    SINTOMA (13/09/2026, noche)

        `todaLaLiga` se publicaba con `available: true` y 570
        jugadores dentro, y el cuadro decia «No se ha podido
        montar la lista de la liga».

    CAUSA

        Esa funcion copia clave por clave y tira todo lo que no
        este nombrado. El dato llegaba al navegador, entraba en
        `raw` y moria ahi. Y con el moria `reason`, asi que el
        cuadro ni siquiera podia decir por que estaba vacio: se
        veia igual que una averia de datos.

    MISMO NOMBRE A LOS DOS LADOS (doctrina 39). Si la telemetria
    publica `todaLaLiga`, el lector recoge `todaLaLiga`.
    """

    publicado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    lector = STATUS_JS.read_text(encoding="utf-8")

    # REGLA 24.
    assert len(lector) > 1000, "no se ha leido `status.js`"

    for clave in ("todaLaLiga", "loNuestroALaVenta"):

        assert f'"{clave}"' in publicado, (
            f"la telemetria no publica `{clave}`"
        )

        assert f"raw.{clave}" in lector, (
            f"`normalizeStatus` no recoge `{clave}`: el cuadro "
            f"lo leeria como undefined y saldria vacio con el "
            f"dato publicado"
        )

    # Y CADA CUADRO LEE EL NOMBRE QUE EL LECTOR DEJA.
    assert "data.todaLaLiga" in LIGA.read_text(
        encoding="utf-8"
    ), "el cuadro de la liga no lee `data.todaLaLiga`"

    assert "data.loNuestroALaVenta" in VENTA.read_text(
        encoding="utf-8"
    ), "el cuadro de la venta no lee `data.loNuestroALaVenta`"


def test_el_escaparate_dice_por_que_no_publico() -> None:
    """
    UN CARTEL ROJO SIN MOTIVO NO SE PUEDE ARREGLAR.

    SINTOMA (13/09/2026, noche)

        «Trent esta comprado para revender y no esta a la venta.
        Lo compramos hoy a las 10:08 y sigue sin publicar». Diez
        horas. Ninguna pantalla decia POR QUE.

    CAUSA

        El escaparate calcula su veredicto —zona de silencio,
        ningun viaje abierto, no se sabe quienes son los
        titulares, es TITULAR, sin valor de mercado— y lo escribe
        en `v10_full_autonomous_status.json`, que ninguna
        pantalla lee.

    Es telemetria: se copia lo que el ciclo ya decidio.
    """

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert '"por_que_no_se_publico"' in estado, (
        "el veredicto del escaparate no se publica: el cartel "
        "rojo seguiria sin explicacion"
    )

    assert '"saltados"' in estado, (
        "no se publica el motivo de CADA jugador saltado, que es "
        "lo que contesta «¿y por que Trent no?»"
    )

    # CON SU EDAD. Ese fichero solo se reescribe cuando el motor
    # con permiso ejecuta, y el observador corre mucho mas a
    # menudo: sin la edad, un motivo de ayer se lee como el de
    # ahora.
    i = estado.index('"por_que_no_se_publico"')

    bloque = estado[i : i + 2200]

    assert "age_seconds" in bloque, (
        "el veredicto se publica sin su edad: un motivo de ayer "
        "se leeria como el de este ciclo"
    )


def test_la_lista_de_publicaciones_tiene_sus_filas() -> None:
    """
    `compact_listings` NO TENIA CLAVE `rows`.

    SINTOMA

        Dos sitios la pedian —el escaparate, para saber que ya
        esta en venta, y `viajes_sin_listar`, para lo mismo— y
        los dos recibian `[]` SIEMPRE.

    CONSECUENCIA

        La comprobacion de «esto ya esta publicado» no podia dar
        que si nunca. El escaparate no sabe distinguir un jugador
        en venta de uno que no lo esta, que es justo lo unico que
        necesita saber.

    Un dato, un nombre: la lista se llama `rows` y sale de
    `compact_listings`.
    """

    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    i = estado.index("def compact_listings(")

    cuerpo = estado[i : estado.index("def ", i + 10)]

    assert '"rows"' in cuerpo, (
        "`compact_listings` sigue sin publicar `rows`: los dos "
        "sitios que la piden reciben lista vacia siempre"
    )

    assert '"player_id"' in cuerpo, (
        "las filas no llevan `player_id`: habria que cruzarlas "
        "por nombre"
    )

    # NADIE PIDE UNA CLAVE QUE NO SE DEVUELVE.
    #
    #     Esta es la regla, y no "todos piden `rows`": hay un
    #     sitio que pide `renew_required` y hace bien. Lo que no
    #     puede pasar es pedir un nombre que esta funcion no
    #     devuelve, porque eso da `[]` en silencio y para
    #     siempre.
    devueltas = set(
        re.findall(r'^\s{8}"([a-z_]+)":', cuerpo, re.M)
    )

    # REGLA 24: sin claves leidas esto no probaria nada.
    assert "rows" in devueltas and len(devueltas) >= 3, (
        f"no se han leido las claves de `compact_listings`: "
        f"{sorted(devueltas)}"
    )

    for fichero in (
        RAIZ / "src" / "telemetry" / "dashboard_state.py",
        RAIZ / "src" / "v10_full_autonomous_live.py",
    ):
        texto = fichero.read_text(encoding="utf-8")

        # EL `.get` TIENE QUE COLGAR DE ESTA LLAMADA.
        #
        #     Una ventana suelta de 120 caracteres cazaba el
        #     `.get("offers")` del argumento SIGUIENTE, que es de
        #     otro diccionario. Entre el cierre y el `.get` solo
        #     caben espacios, saltos, un `or {}` y su parentesis.
        for pedida in re.finditer(
            r"compact_listings\([^)]{0,80}\)"
            r"\s*(?:or\s*\{\s*\})?\s*\)?"
            r'\s*\.get\(\s*"([a-z_]+)"',
            texto,
            re.S,
        ):
            assert pedida.group(1) in devueltas, (
                f"{fichero.name} le pide a `compact_listings` la "
                f"clave `{pedida.group(1)}`, que esa funcion no "
                f"devuelve: recibiria una lista vacia en silencio "
                f"y para siempre. Devuelve "
                f"{sorted(devueltas)}."
            )


# ============================================================
# 4. LOS TRES CUADROS, CON SCROLL Y SIN RECORTE
# ============================================================


def test_los_tres_cuadros_no_recortan_filas() -> None:
    """
    UN RECORTE ES UNA RESPUESTA INCOMPLETA.

    El de objetivos enseñaba 60 de 62 —«2 se quedan fuera por el
    tope de la lista»— y el de la liga 120 de 570. Con scroll
    dentro del cuadro no hace falta ninguno.

    Y LA CABECERA SE QUEDA FIJA: una tabla de 570 filas sin
    cabecera no se puede leer.
    """

    hoja = (FUENTE / "styles.css").read_text(encoding="utf-8")

    assert ".scroll-y" in hoja, (
        "no existe el marco de scroll"
    )

    assert "position:sticky" in hoja, (
        "la cabecera no se queda fija al bajar"
    )

    for fichero in (MERCADO, LIGA, VENTA):

        texto = _sin_comentarios(
            fichero.read_text(encoding="utf-8")
        )

        assert 'className="scroll-y"' in texto, (
            f"{fichero.name} no lleva scroll: o recorta o se "
            f"hace infinita"
        )

        # NI UN `slice` SOBRE LAS FILAS.
        for corte in re.findall(
            r"\.slice\(\s*0\s*,\s*(\d+)\s*\)", texto
        ):
            assert int(corte) >= 500, (
                f"{fichero.name} recorta a {corte} filas: el "
                f"cuadro de la liga tiene 570 y el de objetivos "
                f"62"
            )

    # Y LA TELEMETRIA NO PIDE UN TOPE PEQUEÑO.
    estado = (
        RAIZ / "src" / "telemetry" / "dashboard_state.py"
    ).read_text(encoding="utf-8")

    assert "FILAS_DEL_CUADRO" in estado, (
        "la telemetria no dice cuantas filas pide"
    )

    encontrado = re.search(
        r"FILAS_DEL_CUADRO = ([\d_]+)", estado
    )

    assert encontrado, "no se encuentra el numero"

    assert int(encontrado.group(1).replace("_", "")) >= 570, (
        f"la telemetria pide {encontrado.group(1)} filas y el "
        f"catalogo tiene 570"
    )


TESTS = [
    test_ningun_porcentaje_pasa_de_100,
    test_no_hay_dos_cuadros_con_las_mismas_ofertas,
    test_lo_que_publica_la_telemetria_llega_al_cuadro,
    test_el_escaparate_dice_por_que_no_publico,
    test_la_lista_de_publicaciones_tiene_sus_filas,
    test_los_tres_cuadros_no_recortan_filas,
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
        f"LA PANTALLA DE MERCADO V1: {len(TESTS) - fallos}/"
        f"{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
