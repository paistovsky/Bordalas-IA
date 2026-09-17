"""
El carry: las tres piezas, el tope que viaja con la vía, y la verja limpia.

QUE SE PRUEBA AQUI

    1. `test_la_verja_no_escribe_en_los_libros`
       Un escritor de libros al que le llega una foto que no es de
       este reset NO escribe. Falla si no hay ningún libro que
       comprobar.

    2. `test_el_carry_lleva_sus_tres_piezas`
       El coste publicado nombra las tres, cada una con su `n`.
       Falla si alguna llega vacía.

    3. `test_la_via_del_once_no_pierde_su_tope`
       Con la fórmula nueva, una operación de fichaje sigue
       teniendo tope de prima. Falla si el tope llega a `None`.

    4. `test_la_deriva_no_se_promedia_entre_direcciones`
       Sin saber qué hizo el precio la víspera no se devuelve la
       media de las tres: +7,43 % y −11,71 % no tienen media útil.

    5. `test_el_horizonte_sale_de_donde_gira_la_curva`

    6. `test_esto_sigue_apagado`

POR QUE LA GUARDIA 1 NO CORRE LA VERJA ENTERA

    Correr las 150 guardias desde dentro de una guardia duplica
    la verja —medido en esta casa: no termina en diez minutos— y
    además ESCRIBIRÍA en los libros de verdad, que es justo lo
    que se quiere impedir.

    Así que se prueba la causa, no el síntoma: el escritor recibe
    una foto vieja y tiene que negarse. Esa es la condición que
    hace que la verja no ensucie, y se puede comprobar en
    milisegundos y sin tocar `data/`.

    El síntoma se midió a mano el 17/09, antes y después del
    arreglo, y está en el informe.

REGLA 23 / DOCTRINA 50: NI DISCO, NI RED, NI RELOJ

    El libro se prueba contra una ruta temporal que la guardia
    crea y borra. Los instantes entran por argumento. Las
    constantes de deriva son las medidas, no se releen del disco.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.analysis.el_carry import (
    DERIVA,
    LIBROS_QUE_LA_VERJA_TOCABA,
    PENDIENTES_DE_ARREGLAR,
    DIRECCIONES,
    ENCENDIDO,
    HORIZONTE_DIAS,
    TOPE_DE_PRIMA_DE_FICHAJE,
    coste_de_fichar,
    deriva_esperada,
    esta_encendido,
    que_cambia,
    tres_piezas,
)
from src.analysis.rival_bid_model import PRIMA_MAXIMA_DE_PUJA
from src.intelligence.libro_del_escaparate import (
    apuntar_el_escaparate,
)


# ============================================================
# LOS FIXTURES
# ============================================================

ESCAPARATE = [
    {
        "id": 18398,
        "name": "Budimir",
        "position": 4,
        "market_price": 11_990_000,
        "points": 45,
        "played": 6,
        "starter_probability": 90.0,
    },
    {
        "id": 3720,
        "name": "Miguel Román",
        "position": 3,
        "market_price": 3_720_000,
        "points": 28,
        "played": 6,
        "starter_probability": 50.0,
    },
]


# ============================================================
# 1. LA VERJA NO ESCRIBE EN LOS LIBROS
# ============================================================


def test_la_verja_no_escribe_en_los_libros():
    """
    Un escritor al que le llega una foto vieja no escribe.
    """

    assert LIBROS_QUE_LA_VERJA_TOCABA, (
        "no hay ningún libro que comprobar: si esta lista se vacía "
        "sin que nadie la haya arreglado, esta guardia deja de "
        "probar nada"
    )

    with tempfile.TemporaryDirectory() as carpeta:

        libro = Path(carpeta) / "libro_del_escaparate.jsonl"

        # LA FOTO DE LA VERJA: el fixture del 13/09, corriendo hoy.
        # Es exactamente lo que pasó: el libro nació el 17/09 y la
        # primera línea que tuvo traía los veinte del 13/09.
        vieja = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-17T12:07:39",
            foto_at="2026-09-13T17:17:17",
            ruta=libro,
        )

        assert vieja["written"] is False, (
            "una foto del 13/09 corriendo el 17/09 ha escrito en el "
            "libro: eso es lo que la verja llevaba haciendo"
        )

        assert vieja["foto_dia_de_mercado"] == "2026-09-13"
        assert vieja["dia_de_mercado"] == "2026-09-17"

        assert "no se apunta" in vieja["reason"]

        # SIN SELLO TAMPOCO. «Si no me llega el dato me porto como
        # antes» es como se cuela una foto vieja.
        sin_sello = apuntar_el_escaparate(
            ESCAPARATE, at="2026-09-17T12:07:39", ruta=libro
        )

        assert sin_sello["written"] is False, (
            "sin saber de cuándo es la foto no se puede apuntar: "
            "ante la duda, perder un reset es más barato que meter "
            "uno falso"
        )

        # Y CON LA FOTO DE ESTE RESET, SÍ. Si no escribiera nunca,
        # la guardia estaría verde por un libro que no sirve.
        buena = apuntar_el_escaparate(
            ESCAPARATE,
            at="2026-09-17T07:30:55",
            foto_at="2026-09-17T07:23:08",
            ruta=libro,
        )

        assert buena["written"] is True, (
            "con la foto de este reset tiene que escribir, o el "
            "arreglo ha roto el libro en vez de limpiarlo"
        )

        lineas = [
            json.loads(l)
            for l in libro.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]

        assert len(lineas) == 1, (
            f"tres intentos, uno válido: una línea, no {len(lineas)}"
        )

        # Y LA LINEA LLEVA DE CUANDO ES LA FOTO, para que si algún
        # día vuelve a colarse una vieja se vea sin deducirlo.
        assert lineas[0]["foto_at"].startswith("2026-09-17"), (
            "la línea tiene que decir de cuándo es la foto"
        )

    # Y los que siguen sin arreglar salen nombrados, no escondidos.
    for ruta, que in LIBROS_QUE_LA_VERJA_TOCABA.items():
        assert que, f"{ruta} está en la lista sin decir qué escribe"

    assert len(PENDIENTES_DE_ARREGLAR) == 4, (
        f"el 17/09 quedaban cuatro libros sin arreglar y ahora hay "
        f"{len(PENDIENTES_DE_ARREGLAR)}: si han cambiado, hay que "
        f"decirlo en `el_carry.LIBROS_QUE_LA_VERJA_TOCABA`"
    )

    print("  OK  una foto que no es de este reset no entra en el libro")


# ============================================================
# 2. LAS TRES PIEZAS
# ============================================================


def test_el_carry_lleva_sus_tres_piezas():
    """
    Y cada una con su `n`, su plazo y su fuente.
    """

    carry = tres_piezas(4_000_000, "SUBIA")

    assert carry["available"]

    piezas = carry["piezas"]

    assert set(piezas) == {"prima", "deriva", "oportunidad"}, (
        f"el carry tiene TRES piezas: {sorted(piezas)}"
    )

    for nombre, pieza in piezas.items():

        assert pieza.get("nombre"), f"{nombre} sale sin nombre"

        assert pieza.get("percent") is not None, (
            f"{nombre} sale sin número"
        )

        assert pieza.get("n"), (
            f"{nombre} sale sin `n`: un agregado sin su `n` es una "
            f"anécdota (doctrina 55)"
        )

        assert pieza.get("plazo"), (
            f"{nombre} sale sin plazo: un porcentaje sin su plazo "
            f"no es un rendimiento (doctrina 53)"
        )

        assert pieza.get("fuente"), (
            f"{nombre} sale sin decir de dónde viene"
        )

    # LA SUMA ES LA SUMA.
    esperado = (
        piezas["prima"]["percent"]
        + piezas["deriva"]["percent"]
        + piezas["oportunidad"]["percent"]
    )

    assert abs(carry["carry_percent"] - esperado) < 1e-6

    # LA DERIVA ENTRA CON EL SIGNO CAMBIADO: si el precio sube, la
    # tenencia DEVUELVE dinero. Si esto se invirtiera, el carry
    # diría que tener a los que suben cuesta.
    assert piezas["deriva"]["percent"] < 0, (
        "quien venía subiendo devuelve dinero mientras se tiene: "
        "la deriva entra al carry con el signo cambiado"
    )

    assert carry["paga"] is True, (
        "a diez días, tener a uno que subía devuelve más de lo que "
        "cuestan la prima y la oportunidad juntas"
    )

    assert "DEVUELVE" in carry["reason"]

    # Y AL REVES: el que bajaba cuesta, y mucho.
    cayendo = tres_piezas(4_000_000, "BAJABA")

    assert cayendo["paga"] is False
    assert cayendo["carry_percent"] > 10, (
        "quien venía bajando cuesta más del 10 % a diez días: si "
        "no, el fixture no distingue las dos direcciones"
    )

    # ------------------------------------------------
    # UNA PIEZA VACIA: MUERDE AQUI
    # ------------------------------------------------
    sin_direccion = tres_piezas(4_000_000, None)

    assert sin_direccion["available"] is False, (
        "sin la deriva no se publica un carry: un coste al que le "
        "falta una pieza no es un coste, es media cuenta"
    )

    assert sin_direccion["piezas"]["deriva"]["percent"] is None

    assert tres_piezas(0, "SUBIA")["available"] is False

    print("  OK  el carry sale con sus tres piezas, cada una con su `n`")


# ============================================================
# 3. EL TOPE VIAJA CON LA VIA
# ============================================================


def test_la_via_del_once_no_pierde_su_tope():
    """
    Doctrina 69: el freno va en la misma línea que el valor.
    """

    coste = coste_de_fichar(4_000_000, "SUBIA")

    assert coste["available"]

    assert coste["tope_de_prima"] is not None, (
        "una operación de fichaje SIN tope de prima es exactamente "
        "el freno huérfano que nos ha mordido cuatro veces esta "
        "semana"
    )

    assert coste["sin_tope"] is False

    # Y NO ES UN NUMERO NUEVO: es el de la otra vía.
    assert coste["tope_de_prima"] == PRIMA_MAXIMA_DE_PUJA, (
        "el tope de la vía del once no puede ser un umbral nuevo: "
        "se extiende el que ya hay"
    )

    assert TOPE_DE_PRIMA_DE_FICHAJE == PRIMA_MAXIMA_DE_PUJA

    # EL TECHO EN EUROS, PUBLICADO AL LADO DEL COSTE.
    assert coste["tope_de_prima_euros"] == round(
        4_000_000 * (1 + PRIMA_MAXIMA_DE_PUJA)
    )

    assert coste["tope_de_prima_euros"] > 4_000_000, (
        "el techo tiene que estar por encima del precio, o no hay "
        "puja posible"
    )

    # Y EL COSTE BAJA DE VERDAD: si no bajara, no habría nada que
    # frenar y la guardia no probaría nada.
    assert coste["coste_nuevo"] < coste["coste_viejo"], (
        "con el carry el coste tiene que ser menor que el importe "
        "entero, o esta fórmula no cambia nada"
    )

    assert coste["ahorro"] > 0

    # ------------------------------------------------
    # PEDIRLO SIN TOPE SE PUEDE, PERO SALE MARCADO
    # ------------------------------------------------
    desnudo = coste_de_fichar(4_000_000, "SUBIA", tope_de_prima=None)

    assert desnudo["sin_tope"] is True
    assert desnudo["tope_de_prima_euros"] is None
    assert "SIN TOPE" in desnudo["reason"], (
        "si alguien pide la fórmula sin tope, el motivo tiene que "
        "decirlo con esas palabras"
    )

    print("  OK  la vía del once conserva su tope, y es el que ya había")


# ============================================================
# 4. LA DERIVA NO SE PROMEDIA
# ============================================================


def test_la_deriva_no_se_promedia_entre_direcciones():
    """
    +7,43 % y −11,71 % no tienen media que describa a nadie.
    """

    subiendo = deriva_esperada("SUBIA", 10)
    bajando = deriva_esperada("BAJABA", 10)
    plano = deriva_esperada("PLANO", 10)

    for salida in (subiendo, bajando, plano):
        assert salida["available"]
        assert salida["n"] > 1000, (
            f"la deriva de {salida['direccion']} sale con n="
            f"{salida['n']}: muestra corta para una tabla que "
            f"decide"
        )
        assert salida["fuente"]

    # LAS TRES SON DISTINTAS. Si no lo fueran, condicionar no
    # serviría de nada.
    assert subiendo["percent"] > 5
    assert bajando["percent"] < -10
    assert plano["percent"] == 0

    assert subiendo["percent"] - bajando["percent"] > 15, (
        "entre subir y bajar hay diecinueve puntos a diez días: si "
        "el fixture no los separa, el carry podría ser un solo "
        "número y no lo es"
    )

    # ------------------------------------------------
    # SIN DIRECCION NO SE INVENTA UNA MEDIA
    # ------------------------------------------------
    for desconocida in (None, "", "LO_QUE_SEA"):
        salida = deriva_esperada(desconocida, 10)

        assert salida["available"] is False, (
            f"con dirección {desconocida!r} se ha devuelto una "
            f"deriva: la media de las tres no describe a ningún "
            f"jugador"
        )

        assert salida["percent"] is None
        assert salida["n"] == 0

    print("  OK  la deriva va condicionada, y sin dirección no se inventa")


# ============================================================
# 5. EL HORIZONTE
# ============================================================


def test_el_horizonte_sale_de_donde_gira_la_curva():
    """
    Diez días porque es donde la deriva del que sube deja de
    crecer, no porque nos guste.
    """

    tabla = DERIVA["SUBIA"]

    assert HORIZONTE_DIAS in tabla

    mejor = max(tabla, key=lambda h: tabla[h][0])

    assert mejor == HORIZONTE_DIAS, (
        f"el horizonte tiene que ser donde la deriva es máxima "
        f"({mejor}), y está puesto en {HORIZONTE_DIAS}"
    )

    # Y DESPUES DEVUELVE. Si siguiera subiendo, el horizonte sería
    # otro y esta guardia lo diría.
    assert tabla[14][0] < tabla[10][0] < tabla[21][0] + 99, (
        "a catorce días la deriva del que sube ya es menor que a "
        "diez: esa es la razón del horizonte"
    )

    assert tabla[14][0] < tabla[10][0]
    assert tabla[21][0] < tabla[14][0]

    # El que baja NO satura: sigue cayendo. Por eso el horizonte
    # no se puede sacar de él.
    cayendo = DERIVA["BAJABA"]

    assert cayendo[21][0] < cayendo[10][0] < cayendo[1][0], (
        "el que baja sigue bajando a veintiún días: el horizonte "
        "sale del que sube, no de la media de los dos"
    )

    # Un horizonte que no está en la tabla cae al más cercano, y
    # se dice cuál se usó.
    cerca = deriva_esperada("SUBIA", 9)

    assert cerca["horizonte_pedido"] == 9
    assert cerca["horizonte_usado"] == 10, (
        "si se pide un plazo que no está medido, se usa el más "
        "cercano Y SE DICE cuál"
    )

    print("  OK  el horizonte es donde gira la curva, y se dice")


# ============================================================
# 6. APAGADO
# ============================================================


def test_esto_sigue_apagado():

    assert ENCENDIDO is False, (
        "la fórmula se construye apagada: solo el arreglo del "
        "libro entra en producción"
    )

    assert esta_encendido() is False

    # Pero calcula.
    assert tres_piezas(1_000_000, "SUBIA")["available"]
    assert coste_de_fichar(1_000_000, "SUBIA")["available"]

    assert que_cambia(
        [
            {
                "name": "X",
                "market_price": 1_000_000,
                "xi_value": 900_000,
                "direccion": "SUBIA",
            }
        ],
        bolsillo_de_fichar=10_000_000,
        techo_de_biwenger=10_000_000,
    )["available"]

    print("  OK  el carry calcula, se publica y sigue apagado")


TESTS = [
    test_la_verja_no_escribe_en_los_libros,
    test_el_carry_lleva_sus_tres_piezas,
    test_la_via_del_once_no_pierde_su_tope,
    test_la_deriva_no_se_promedia_entre_direcciones,
    test_el_horizonte_sale_de_donde_gira_la_curva,
    test_esto_sigue_apagado,
]


def main() -> None:
    fallos = 0

    for test in TESTS:
        try:
            test()

        except AssertionError as error:
            fallos += 1
            print(f"FALLA {test.__name__}: {error}")

    print("=" * 60)
    print(f"EL CARRY V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
