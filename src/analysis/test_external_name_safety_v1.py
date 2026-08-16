"""
Nombres que rompen la busqueda externa.

QUE PASO EL 16/08/2026
    Al arreglar el techo de puja, diez jugadores pasaron a
    action == PUJAR. Esa es la unica rama que consulta el estado
    externo del jugador. Y al consultarlo:

        RuntimeError: API-Football error: {'search': 'The Search
        field may only contain alpha-numeric characters and
        spaces.'}

    El ciclo entero se caia. `calculate_intelligent_bids` se llama
    desde `autopilot.run_cycle`, asi que no era un aviso: era una
    parada de produccion.

LA CAUSA
    `normalize_name` usaba NFKD, que descompone los acentos
    -Angel, Oskarsson, Jutgla- pero no las letras que son un
    caracter propio. La o barrada de Sorloth sobrevivia intacta.

    En el catalogo quedaban cinco nombres que la API rechazaba:
    Sorloth, El-Abdellaoui, Etienne Eto'o, Sainz-Maza y
    Kang-in Lee.

LO IMPORTANTE DE ESTE CASO
    El fallo era anterior. Llevaba ahi dormido porque el techo de
    puja roto -45 % del saldo, 107.985 EUR- hacia que ningun
    jugador llegase nunca a PUJAR, asi que esa rama no se
    ejecutaba.

    Un bug tapado por otro bug. Arreglar el primero desperto el
    segundo.

Ejecutar:
    python -m src.analysis.test_external_name_safety_v1
"""

import re

import src.analysis.intelligent_bid_engine as motor

from src.intelligence.api_football import normalize_name


# Lo que la API acepta: alfanumericos y espacios.
PERMITIDO = re.compile(r"^[a-z0-9 ]*$")

# Los cinco del catalogo del 16/08/2026.
NOMBRES_QUE_ROMPIAN = [
    ("Sørloth", "sorloth"),
    ("El-Abdellaoui", "el abdellaoui"),
    ("Etienne Eto'o", "etienne etoo"),
    ("Sainz-Maza", "sainz maza"),
    ("Kang-in Lee", "kang in lee"),
]

# Los que ya funcionaban y no se pueden romper.
NOMBRES_QUE_YA_IBAN = [
    ("Ángel Pérez", "angel perez"),
    ("Óskarsson", "oskarsson"),
    ("Jutglà", "jutgla"),
    ("Comesaña", "comesana"),
    ("Tenaglia", "tenaglia"),
    ("Toni Martínez", "toni martinez"),
]


# ============================================================
# LA CAUSA
# ============================================================

def test_los_cinco_nombres_que_rompian() -> None:
    for original, esperado in NOMBRES_QUE_ROMPIAN:

        obtenido = normalize_name(original)

        assert obtenido == esperado, (
            f"{original} deberia normalizarse a '{esperado}' y "
            f"salio '{obtenido}'."
        )
        assert PERMITIDO.match(obtenido), (
            f"'{obtenido}' sigue trayendo caracteres que la API "
            f"rechaza."
        )

    print("  OK  los cinco nombres del catalogo ya pasan")


def test_la_o_barrada_no_la_descompone_nfkd() -> None:
    """
    El caso concreto, y la razon de que NFKD no bastara.
    """
    import unicodedata

    solo_nfkd = "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", "Sørloth")
        if not unicodedata.combining(caracter)
    ).lower()

    assert solo_nfkd == "sørloth", (
        "Si NFKD empezara a descomponer la o barrada, este test "
        "deja de tener sentido, pero el arreglo seguiria siendo "
        "correcto."
    )
    assert normalize_name("Sørloth") == "sorloth"

    print("  OK  NFKD no basta; el mapa explicito si")


def test_no_se_rompen_los_que_ya_funcionaban() -> None:
    for original, esperado in NOMBRES_QUE_YA_IBAN:

        obtenido = normalize_name(original)

        assert obtenido == esperado, (
            f"REGRESION: {original} salia '{esperado}' y ahora "
            f"sale '{obtenido}'."
        )

    print("  OK  los acentos normales siguen igual")


def test_los_guiones_separan_palabras() -> None:
    """
    Un guion separa. Borrarlo pegaria las palabras y la busqueda
    encontraria menos, no mas.
    """
    assert normalize_name("Kang-in Lee") == "kang in lee"
    assert normalize_name("Sainz-Maza") == "sainz maza"

    print("  OK  los guiones se convierten en espacio, no se borran")


def test_los_apostrofos_se_borran() -> None:
    """
    Un apostrofo no separa palabras: Eto'o es una sola.
    """
    assert normalize_name("Etienne Eto'o") == "etienne etoo"
    assert normalize_name("N’Diaye") == "ndiaye"

    print("  OK  los apostrofos se borran, no separan")


def test_cualquier_nombre_sale_utilizable() -> None:
    """
    La garantia general: salga lo que salga del catalogo, lo que
    devuelve normalize_name cumple el contrato de la API.
    """
    casos = [
        "Sørloth",
        "Etienne Eto'o",
        "Kang-in Lee",
        "Ángel Pérez",
        "Łukasz",
        "Þórsson",
        "Ødegaard",
        "Müller",
        "Nº 10",
        "J.  R.  Smith",
        "  espacios  raros  ",
        "123",
        "",
        "!!!",
    ]

    for nombre in casos:
        obtenido = normalize_name(nombre)

        assert PERMITIDO.match(obtenido), (
            f"'{nombre}' produce '{obtenido}', que la API "
            f"rechazaria."
        )
        assert "  " not in obtenido, (
            f"'{obtenido}' trae espacios dobles."
        )
        assert obtenido == obtenido.strip()

    print("  OK  cualquier nombre sale en un formato que la API acepta")


def test_no_lanza_con_entradas_raras() -> None:
    for entrada in (None, "", "   "):
        assert normalize_name(entrada) == ""

    print("  OK  no lanza con entradas vacias")


# ============================================================
# LA RED DE SEGURIDAD
# ============================================================

def test_un_fallo_externo_no_tumba_la_evaluacion() -> None:
    """
    El estado externo es informacion de apoyo, no una decision. Si
    la API vuelve a cambiar de opinion sobre lo que acepta, la
    puja tiene que evaluarse igual.
    """
    previos = {
        "bids": motor.calculate_bid_recommendations,
        "externo": motor.get_external_player_status,
    }

    def explota(snapshot, player):
        raise RuntimeError(
            "API-Football error: {'search': 'The Search field "
            "may only contain alpha-numeric characters and "
            "spaces.'}"
        )

    motor.calculate_bid_recommendations = lambda snapshot: [
        {
            "id": 41100,
            "name": "Sørloth",
            "market_price": 4_830_000,
            "player_price": 4_830_000,
            "final_score": 75,
            "suggested_bid": 5_120_000,
            "action": "PUJAR",
            "own_player": False,
        }
    ]
    motor.get_external_player_status = explota

    try:
        resultado = motor.calculate_intelligent_bids(
            {
                "league": {"user": {"id": 14175949}},
                "my_team": [],
                "market": {
                    "sales": [],
                    "offers": [],
                    "status": {
                        "balance": 239_968,
                        "maximumBid": 12_414_968,
                    },
                },
            },
            allow_external_checks=True,
        )

    finally:
        motor.calculate_bid_recommendations = previos["bids"]
        motor.get_external_player_status = previos["externo"]

    assert len(resultado) == 1, (
        "REGRESION: un fallo de la API externa volvio a tumbar la "
        "evaluacion entera. Esto para el ciclo de produccion."
    )

    jugador = resultado[0]

    assert jugador["action"] == "PUJAR", (
        "Sin dato externo no se penaliza: se evalua igual."
    )
    assert (
        jugador["external_status"]["external_available"] is False
    )
    assert "error" in jugador["external_status"], (
        "El fallo tiene que quedar registrado, no desaparecer."
    )

    print(
        "  OK  un fallo de la API externa no tumba el ciclo, "
        "y queda anotado"
    )


# ============================================================

TESTS = [
    test_los_cinco_nombres_que_rompian,
    test_la_o_barrada_no_la_descompone_nfkd,
    test_no_se_rompen_los_que_ya_funcionaban,
    test_los_guiones_separan_palabras,
    test_los_apostrofos_se_borran,
    test_cualquier_nombre_sale_utilizable,
    test_no_lanza_con_entradas_raras,
    test_un_fallo_externo_no_tumba_la_evaluacion,
]


def main() -> None:
    print("=" * 60)
    print(" NOMBRES Y BUSQUEDA EXTERNA")
    print("=" * 60)

    fallos = 0

    for test in TESTS:
        print(f"\n{test.__name__}")
        try:
            test()
        except AssertionError as error:
            fallos += 1
            print(f"  FALLO  {error}")

    print("\n" + "=" * 60)
    if fallos:
        print(f" {fallos}/{len(TESTS)} TESTS FALLIDOS")
        raise SystemExit(1)
    print(f" {len(TESTS)}/{len(TESTS)} TESTS OK")
    print("=" * 60)


if __name__ == "__main__":
    main()
