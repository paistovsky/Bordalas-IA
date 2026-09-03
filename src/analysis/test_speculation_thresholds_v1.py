"""
Los umbrales de especulacion, atados al margen que existe de verdad.

SINTOMA

    Pepe llevaba seis dias sin fichar ni especular. El tablero traia
    22 candidatos y ninguno accionable: doce se caian con
    "RENDIMIENTO_INSUFICIENTE" y el mismo numero repetido, 0,22 %.

CAUSA

    Ese 0,22 % no es una estimacion por jugador: es una constante, y
    es el margen real del negocio. La rueda no consiste en adivinar
    que jugador sube, sino en arbitraje: se compra a mercado y el
    Computer recompra por encima -mediana +1,98 %, positivo en el
    78 % de 90 ventas medidas-.

    Los dos umbrales estaban puestos para otro negocio: se exigia un
    3 % de rendimiento (catorce veces el margen que existe) y 25.000
    EUR de ganancia (cuando el tope por operacion permite como mucho
    unos 3.080 EUR). Entre los dos, la rueda no podia girar ni una
    vez.

CONSECUENCIA

    Mientras tanto los rivales daban 38 y 31 vueltas a esa misma
    rueda. La diferencia de revalorizacion era de un millon.

QUE VIGILA ESTA GUARDIA

    Que los umbrales sigan siendo compatibles con el margen medido.
    Si alguien vuelve a subirlos "porque 3 % suena mas prudente", la
    rueda se para otra vez en silencio y nadie se entera hasta que
    pasan semanas. Aqui se entera en el mismo ciclo.
"""

from __future__ import annotations

from src.analysis.rival_bid_model import (
    MIN_SPECULATION_EXPECTED_VALUE,
    MIN_SPECULATION_YIELD,
)

# Medido el 03/09/2026 sobre 90 ventas al Computer con precio
# conocido: mediana +1,98 % sobre mercado. El rendimiento neto que
# el motor calcula para cualquier candidato es 0,22 %.
MARGEN_MEDIDO = 0.0022

# Tope por operacion: 40 % de un bolsillo especulativo de ~3,5 M.
TOPE_POR_OPERACION = 1_400_000

# Una operacion tipica de las que aparecen en el tablero.
OPERACION_TIPICA = 2_000_000


def test_el_umbral_de_rendimiento_cabe_en_el_margen_real() -> None:
    assert MIN_SPECULATION_YIELD < MARGEN_MEDIDO, (
        f"Se exige un {MIN_SPECULATION_YIELD * 100:.2f} % cuando el "
        f"negocio rinde {MARGEN_MEDIDO * 100:.2f} %. Con este umbral "
        "no pasa ni un candidato: la rueda queda parada."
    )


def test_el_umbral_deja_margen_por_si_el_computer_paga_menos() -> None:
    """No vale rozarlo: si baja la prima, queremos que cierre, no que
    siga comprando con margen cero."""
    assert MIN_SPECULATION_YIELD >= MARGEN_MEDIDO * 0.5, (
        "El umbral esta tan bajo que aunque el Computer dejara de "
        "pagar prima seguiriamos comprando."
    )


def test_la_ganancia_minima_es_alcanzable_con_el_tope_por_operacion() -> None:
    maxima_posible = TOPE_POR_OPERACION * MARGEN_MEDIDO
    assert MIN_SPECULATION_EXPECTED_VALUE < maxima_posible, (
        f"Se exigen {MIN_SPECULATION_EXPECTED_VALUE:,} EUR de ganancia "
        f"pero el tope por operacion solo permite ganar "
        f"{maxima_posible:,.0f} EUR. Es inalcanzable por construccion."
    ).replace(",", ".")


def test_una_operacion_tipica_pasa_las_dos_puertas() -> None:
    ganancia = OPERACION_TIPICA * MARGEN_MEDIDO
    assert MARGEN_MEDIDO >= MIN_SPECULATION_YIELD, "no pasa la puerta del rendimiento"
    assert ganancia >= MIN_SPECULATION_EXPECTED_VALUE, (
        f"Una operacion de {OPERACION_TIPICA:,} EUR deja "
        f"{ganancia:,.0f} EUR y no llega al minimo de "
        f"{MIN_SPECULATION_EXPECTED_VALUE:,}."
    ).replace(",", ".")


def test_las_migajas_se_siguen_descartando() -> None:
    """El ciclo ejecuta una accion por vuelta: gastarla en 337 EUR no."""
    migaja = 150_000 * MARGEN_MEDIDO
    assert migaja < MIN_SPECULATION_EXPECTED_VALUE, (
        f"Una operacion de 150.000 EUR deja {migaja:.0f} EUR y estaria "
        "pasando. Eso es quemar el turno del ciclo en ruido."
    )


TESTS = [
    test_el_umbral_de_rendimiento_cabe_en_el_margen_real,
    test_el_umbral_deja_margen_por_si_el_computer_paga_menos,
    test_la_ganancia_minima_es_alcanzable_con_el_tope_por_operacion,
    test_una_operacion_tipica_pasa_las_dos_puertas,
    test_las_migajas_se_siguen_descartando,
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
    print(f"UMBRALES DE ESPECULACION V1: {len(TESTS) - fallos}/{len(TESTS)} OK")
    print("=" * 60)

    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
