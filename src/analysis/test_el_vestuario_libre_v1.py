"""
El vestuario libre: la lista de la compra, y que NO puja.

EL PUNTO CIEGO (14/09/2026)

    Pepe no podia querer a nadie que no estuviera HOY en el
    escaparate. Su universo eran los veinte que el Computer saca
    cada mañana; los 450 libres restantes no existian en ninguna
    parte de su cabeza.

    Medido en la foto del 13/09: 570 en el catalogo, 120 con
    dueño, 450 libres. De ellos 148 nos mejorarian el once.

LO QUE SE PRUEBA AQUI

    1. Que la lista no esta vacia NI es el catalogo entero, y que
       ninguno de los nuestros aparece en ella.

    2. Que el modulo NO PUJA: ni llama a un ejecutor, ni lo
       importa, ni escribe en ninguna parte. Es una lista para
       mirar y tiene que poder demostrarse.

    3. Que un VIGILADO no se salta el liston: la marca cambia
       donde se ve, no si se puja.

REGLA 23

    No se lee estado de produccion: el catalogo, las plantillas y
    el mercado se construyen aqui.

REGLA 24

    Ninguna pasa con las manos vacias.
"""

from __future__ import annotations

import ast

from pathlib import Path

from src.analysis.el_vestuario_libre import (
    NOS_SUMA_MINIMO,
    PARTIDOS_PARA_JUZGAR,
    el_vestuario_libre,
)
from src.analysis.toda_la_liga import toda_la_liga


RAIZ = Path(__file__).parents[2]

MODULO = (
    RAIZ / "src" / "analysis" / "el_vestuario_libre.py"
)


# ============================================================
# UNA LIGA DE MENTIRA, CON LAS OCHO PLANTILLAS
# ============================================================
#
# Ocho plantillas de cinco y un catalogo de sesenta: lo justo
# para que "ni vacia ni el catalogo entero" signifique algo.

NUESTRO_ID = 14175949

CUANTOS = 60

NUESTROS = [1, 2, 3, 4, 5]


def _catalogo() -> dict:
    """Sesenta jugadores, con puntos que van de menos a mas."""

    catalogo = {}

    for pid in range(1, CUANTOS + 1):

        catalogo[pid] = {
            "id": pid,
            "name": f"Jugador {pid}",
            # 1 portero de cada diez, luego def, med y del.
            "position": 1 if pid % 10 == 0 else (pid % 3) + 2,
            "points": pid,
            "price": 1_000_000,
            "playedHome": 3,
            "playedAway": 2,
            "status": "ok",
            "teamID": 1,
        }

    return catalogo


def _once() -> list:
    """Nuestro once. Fija la vara de cada posicion."""

    catalogo = _catalogo()

    return [
        {
            "id": pid,
            "name": catalogo[pid]["name"],
            "position": catalogo[pid]["position"],
            "points": catalogo[pid]["points"],
        }
        for pid in NUESTROS
    ]


def _managers() -> list:
    """Las SIETE plantillas rivales, de cinco cada una."""

    return [
        {
            "user_id": 20000 + n,
            "name": f"Rival {n}",
            "roster": [
                {"id": pid}
                for pid in range(
                    6 + n * 5, 6 + n * 5 + 5
                )
            ],
        }
        for n in range(7)
    ]


def _liga(en_el_mercado=None) -> dict:
    return toda_la_liga(
        catalogo=_catalogo(),
        once=_once(),
        nuestra_plantilla=[{"id": pid} for pid in NUESTROS],
        managers=_managers(),
        en_el_mercado=en_el_mercado,
        nuestro_id=NUESTRO_ID,
    )


def _vestuario(en_el_mercado=None) -> dict:
    return el_vestuario_libre(
        _liga(en_el_mercado),
        nuestra_plantilla=[{"id": pid} for pid in NUESTROS],
        managers=_managers(),
        en_el_mercado=en_el_mercado,
    )


# ============================================================
# 1. NI VACIA NI EL CATALOGO ENTERO
# ============================================================


def test_el_vestuario_libre_no_esta_vacio() -> None:
    """La lista tiene que ser un recorte, no un extremo.

    LOS DOS EXTREMOS SON EL MISMO FALLO

        VACIA  -> nos hemos quedado sin lista de la compra y no
                  se nota: la pantalla enseña cero y parece que
                  no hay nadie libre.

        ENTERA -> no se ha restado ninguna plantilla y la lista
                  dice que se puede fichar a cualquiera, incluido
                  el que ya es nuestro.

        El segundo es el que ya cazo `_las_ocho_plantillas` en el
        cuadro de al lado: una plantilla que llega vacia hace que
        sus jugadores se cuenten como libres, y un libre es
        alguien a quien se puede fichar.
    """

    catalogo = _catalogo()

    # REGLA 24: sin catalogo esto no probaria nada.
    assert catalogo, "el catalogo llego vacio"

    assert len(catalogo) == CUANTOS, len(catalogo)

    vestuario = _vestuario()

    assert vestuario["available"], vestuario["reason"]

    libres = vestuario["libres"]

    # NI VACIA.
    assert libres > 0, (
        "no quedo ni un libre: o se restaron plantillas de mas o "
        "el catalogo no llego"
    )

    # NI EL CATALOGO ENTERO.
    assert libres < len(catalogo), (
        f"salieron libres los {libres} del catalogo entero: no "
        f"se ha restado ninguna plantilla"
    )

    # Y LA CUENTA CUADRA: 5 nuestros + 35 de siete rivales = 40.
    assert vestuario["con_dueno"] == 40, vestuario

    assert libres == CUANTOS - 40, vestuario

    # NINGUNO DE LOS NUESTROS ESTA EN LA LISTA.
    de_la_lista = {p["id"] for p in vestuario["players"]}

    assert de_la_lista, "la lista de los primeros llego vacia"

    for pid in NUESTROS:
        assert pid not in de_la_lista, (
            f"el jugador {pid} es nuestro y sale como libre"
        )

    # NI NINGUNO DE UN RIVAL.
    de_rivales = {
        j["id"]
        for m in _managers()
        for j in m["roster"]
    }

    assert de_rivales, "las plantillas rivales llegaron vacias"

    assert not (de_la_lista & de_rivales), (
        f"salen jugadores que ya tienen dueño: "
        f"{sorted(de_la_lista & de_rivales)}"
    )

    # LOS CORTES VAN PUBLICADOS, no escondidos en el codigo.
    cortes = vestuario["cortes"]

    assert cortes["partidos_para_juzgar"] == PARTIDOS_PARA_JUZGAR, cortes
    assert cortes["nos_suma_minimo"] == NOS_SUMA_MINIMO, cortes

    # Y cuantos se enseñan de cada puesto, que tambien decide lo
    # que se ve y por tanto tiene que estar a la vista.
    assert cortes["por_posicion"] >= 1, cortes

    # Y SIN PLANTILLAS SE ABSTIENE, en vez de devolver el
    # catalogo entero como lista de la compra.
    a_ciegas = el_vestuario_libre(
        _liga(), nuestra_plantilla=None, managers=None
    )

    assert not a_ciegas["available"], a_ciegas

    assert "plantilla" in (a_ciegas["reason"] or "").lower(), (
        a_ciegas["reason"]
    )


# ============================================================
# 2. LA LISTA NO PUJA
# ============================================================


def test_la_lista_no_puja() -> None:
    """Es una lista para mirar, y se demuestra leyendo el arbol.

    EL ENCARGO LO DICE CON ESTAS PALABRAS: "Ninguna puja nueva
    por esta via. Ni una." Y esto no se prueba diciendolo en un
    comentario: se prueba comprobando que el modulo no puede.
    """

    fuente = MODULO.read_text(encoding="utf-8")

    # REGLA 24.
    assert fuente, "el modulo llego vacio"

    arbol = ast.parse(fuente)

    # 1. NO IMPORTA NADA QUE ESCRIBA.
    importados = []

    for nodo in ast.walk(arbol):

        if isinstance(nodo, ast.Import):
            importados.extend(a.name for a in nodo.names)

        elif isinstance(nodo, ast.ImportFrom):
            importados.append(nodo.module or "")
            importados.extend(a.name for a in nodo.names)

    prohibidos = (
        "executor",
        "client",
        "requests",
        "urllib",
        "http",
        "biwenger",
        "autopilot",
        "orchestrator",
    )

    for nombre in importados:
        for prohibido in prohibidos:
            assert prohibido not in (nombre or "").lower(), (
                f"el vestuario importa `{nombre}`: una lista para "
                f"mirar no necesita nada que escriba"
            )

    # 2. NI LLAMA A NADA QUE ESCRIBA. Se miran los nombres de
    #    todas las llamadas, sea `puja(...)` o `x.puja(...)`.
    llamadas = []

    for nodo in ast.walk(arbol):

        if not isinstance(nodo, ast.Call):
            continue

        objetivo = nodo.func

        if isinstance(objetivo, ast.Name):
            llamadas.append(objetivo.id)

        elif isinstance(objetivo, ast.Attribute):
            llamadas.append(objetivo.attr)

    # REGLA 24: si no se leyo ninguna llamada, este bloque seria
    # verde sin haber mirado nada.
    assert llamadas, "no se leyo ninguna llamada del modulo"

    escrituras = (
        "post",
        "put",
        "patch",
        "delete",
        "bid",
        "pujar",
        "ofertar",
        "vender",
        "comprar",
        "write_text",
        "write_bytes",
        "dump",
        "unlink",
        "mkdir",
        "open",
    )

    for nombre in llamadas:
        assert nombre.lower() not in escrituras, (
            f"el vestuario llama a `{nombre}`: tiene que ser "
            f"una lista que solo mira"
        )

    # 3. Y LO DICE EN SU PROPIA CABECERA, para quien lo abra.
    assert "NO PUJA" in fuente, (
        "el modulo ya no declara que no puja"
    )


# ============================================================
# 3. UN VIGILADO NO SALTA EL LISTON
# ============================================================


def test_un_vigilado_no_salta_el_liston() -> None:
    """La marca cambia DONDE SE VE, no si se puja.

    Un vigilado que aparece en el mercado pasa por el mismo
    liston que cualquier otro. Lo unico que cambia es que Pepe lo
    mira, que es justo lo que no pasaba antes.
    """

    vestuario = _vestuario()

    assert vestuario["available"], vestuario["reason"]

    primeros = vestuario["players"]

    # REGLA 24.
    assert primeros, "no salio ningun vigilado"

    # TODOS LOS DE LA LISTA VAN MARCADOS, y ninguno trae nada
    # que se parezca a una autorizacion.
    for jugador in primeros:

        assert jugador["vigilado"] is True, jugador

        for campo in (
            "bid",
            "puja",
            "decision",
            "autorizado",
            "bid_cap",
        ):
            assert campo not in jugador, (
                f"un vigilado trae `{campo}`: la lista se esta "
                f"pareciendo a una orden"
            )

    # HOY NO ESTA EN EL MERCADO.
    uno = primeros[0]

    assert uno["en_el_mercado"] is False, uno

    # Y MAÑANA APARECE. La marca de vigilado NO cambia, y lo
    # unico que cambia es `en_el_mercado`.
    con_mercado = _vestuario(en_el_mercado={uno["id"]})

    assert con_mercado["available"], con_mercado["reason"]

    mismo = [
        p for p in con_mercado["players"] if p["id"] == uno["id"]
    ]

    assert mismo, (
        "el vigilado desaparecio de la lista al salir al "
        "escaparate: es justo cuando hace falta verlo"
    )

    mismo = mismo[0]

    assert mismo["vigilado"] is True, mismo

    assert mismo["en_el_mercado"] is True, mismo

    # Y EL RECUENTO LO DICE.
    assert (
        con_mercado["recuento"]["en_el_mercado_hoy"] >= 1
    ), con_mercado["recuento"]

    # NI UN NUMERO DE PUJA HA APARECIDO POR EL CAMINO.
    assert mismo.keys() == uno.keys(), (
        f"salir al escaparate le ha añadido campos: "
        f"{set(mismo) ^ set(uno)}"
    )

    for campo, valor in uno.items():
        if campo == "en_el_mercado":
            continue

        assert mismo[campo] == valor, (
            f"salir al escaparate le ha cambiado `{campo}`: "
            f"{valor} -> {mismo[campo]}. La marca cambia donde "
            f"se ve, no lo que vale."
        )


# ============================================================
# 4. SE ORDENA POR LO QUE SUMA, NO POR LO QUE CUESTA
# ============================================================


def test_la_lista_ordena_por_lo_que_suma() -> None:
    """El caro que suma mucho va antes que el barato que suma poco.

    EL FALLO (14/09/2026)

        La primera version ordenaba por `calidad_precio`, y el
        segundo de los veinte salia Herrando: 10 puntos, 3
        partidos, 350.000 EUR, nos suma +3. Estaba ahi por
        BARATO.

        `calidad_precio` divide por el precio, asi que el barato
        gana siempre. Y esta lista no contesta "quien sale a
        cuenta" —esa la contesta el carril— sino A QUIEN
        QUEREMOS.

        Con el orden nuevo Herrando cayo del puesto 2 de la lista
        entera al 46 de 59 defensas. Sin tocar ningun umbral.
    """

    # Dos de la misma posicion: uno baratisimo que suma poco y
    # otro caro que suma mucho. Por calidad-precio ganaria el
    # primero; por lo que nos suma, el segundo.
    barato = {
        "id": 901,
        "name": "Barato",
        "position": 2,
        "points": 10,
        "played": 5,
        "price": 100_000,
        "de_quien": "libre",
        "nos_suma": 3,
        "calidad_precio": 30.0,
        "vara_nombre": "Nuestro peor DEF",
        "vara_puntos": 7,
    }

    caro = {
        **barato,
        "id": 902,
        "name": "Caro",
        "points": 40,
        "price": 6_000_000,
        "nos_suma": 33,
        "calidad_precio": 5.5,
    }

    # REGLA 24: si los dos sumaran igual, esto no probaria nada.
    assert caro["nos_suma"] > barato["nos_suma"], (caro, barato)

    assert (
        barato["calidad_precio"] > caro["calidad_precio"]
    ), "el barato tiene que ganar por calidad-precio, o esta "        "prueba no distingue los dos ordenes"

    liga = {
        "available": True,
        "players": [barato, caro],
        "reason": None,
    }

    vestuario = el_vestuario_libre(
        liga,
        nuestra_plantilla=[{"id": 1}],
        managers=[{"user_id": 2, "roster": [{"id": 3}]}],
    )

    assert vestuario["available"], vestuario["reason"]

    filas = vestuario["players"]

    # REGLA 24.
    assert filas, "la lista llego vacia"

    assert len(filas) == 2, filas

    assert filas[0]["name"] == "Caro", (
        f"va primero el barato que suma +{filas[0]['nos_suma']}: "
        f"se sigue ordenando por lo que cuesta y no por lo que "
        f"suma"
    )

    assert filas[1]["name"] == "Barato", filas

    # Y EL PRECIO SIGUE ESTANDO, de columna.
    for fila in filas:
        assert fila["price"] > 0, fila
        assert fila["calidad_precio"] is not None, fila


# ============================================================
# 5. CADA POSICION CONTRA SU PROPIA VARA
# ============================================================


def test_cada_posicion_tiene_su_vara() -> None:
    """La resta de cada uno es contra el peor titular de SU puesto.

    No se puede fichar a un defensa para mejorar la delantera. La
    vara es por posicion por construccion, y esta guardia impide
    que se mezclen: si algun dia se restara contra una vara
    global, un delantero de 20 puntos pareceria mejorar la
    porteria.
    """

    liga = _liga()

    assert liga["available"], liga["reason"]

    vara = liga.get("vara") or {}

    # REGLA 24: sin vara no hay nada contra lo que restar.
    assert vara, "la vara llego vacia"

    assert len(vara) >= 2, (
        f"esta prueba necesita varias posiciones con vara y solo "
        f"hay {len(vara)}"
    )

    vestuario = _vestuario()

    filas = vestuario["players"]

    assert filas, "la lista llego vacia"

    # LAS VARAS TIENEN QUE SER DISTINTAS ENTRE SI, o comprobar
    # que cada uno usa la suya no probaria nada.
    puntos_de_vara = {
        v["points"] for v in vara.values()
    }

    assert len(puntos_de_vara) > 1, (
        f"todas las varas valen lo mismo ({puntos_de_vara}): "
        f"esta prueba no distinguiria una de otra"
    )

    for fila in filas:

        # La vara se publica por ETIQUETA de posicion —"DEF"—,
        # no por su numero.
        referencia = vara.get(fila["posicion"])

        assert referencia, (fila, vara)

        # 1. EL NOMBRE DE LA VARA ES EL DE SU POSICION.
        assert fila["vara_nombre"] == referencia["name"], (
            f"{fila['name']} ({fila['posicion']}) se compara con "
            f"{fila['vara_nombre']} y no con "
            f"{referencia['name']}"
        )

        assert fila["vara_puntos"] == referencia["points"], fila

        # 2. Y LA RESTA CUADRA. Es la comprobacion de verdad: el
        #    nombre podria ser el bueno y el numero salir de otro
        #    sitio.
        assert (
            fila["nos_suma"]
            == fila["points"] - referencia["points"]
        ), (
            f"{fila['name']}: {fila['points']} - "
            f"{referencia['points']} != {fila['nos_suma']}"
        )

    # Y CADA PUESTO SALE EN SU GRUPO.
    for clave, grupo in (vestuario["por_puesto"] or {}).items():
        for fila in grupo:
            assert fila["posicion"] == clave, (clave, fila)


TESTS = [
    test_el_vestuario_libre_no_esta_vacio,
    test_la_lista_ordena_por_lo_que_suma,
    test_cada_posicion_tiene_su_vara,
    test_la_lista_no_puja,
    test_un_vigilado_no_salta_el_liston,
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
        f"EL VESTUARIO LIBRE V1: "
        f"{len(TESTS) - fallos}/{len(TESTS)} OK"
    )
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
