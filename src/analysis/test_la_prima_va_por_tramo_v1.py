"""
La prima del Computer es una curva, no una constante.

EL HALLAZGO (20/09/2026)

    `candidatos_en_modo_cartera` metia UNA mediana —+2,34 %— para
    todos los precios. Como la ganancia sale de
    `precio x (1 + prima) - precio x (1 + 0,0025)`, el precio se
    cancela y el rendimiento por euro salia CONSTANTE: 0,020841
    para 150.000 y 0,020848 para 24.900.000.

    DOCTRINA 98. Un ratio constante no delata al ratio: delata a
    su entrada.

LO MEDIDO, n = 194 VENTAS AL COMPUTER FECHADAS

    0-1.500.000          +1,36 %   n=74   73 % en verde
    1.500.000-3.000.000  +1,78 %   n=51   75 %
    3.000.000-6.000.000  +2,63 %   n=53   87 %
    6.000.000+           +4,26 %   n=16   94 %

    Con la curva puesta, la dispersion del rendimiento por euro
    sobre los candidatos REALES pasa del 0,019 % al 72,3 %.

LO QUE ESTA GUARDIA VIGILA

    · Que dos candidatos de precio muy distinto NO reciban la
      misma prima esperada.
    · Que un tramo sin masa se declare SIN CALIBRAR y caiga a la
      mediana global, en vez de inventarse un numero.
    · Que apagado el interruptor el comportamiento sea
      EXACTAMENTE el de antes.

REGLA 23 Y DOCTRINA 24

    No lee `data/`, ni `diagnostico/`, ni la red, ni el reloj: la
    curva se construye aqui con ventas de mentira. Y si la
    muestra cayera entera en un tramo, o si todos los tramos
    tuvieran masa, la guardia FALLA en vez de pasar: no habria
    comprobado lo que dice comprobar.
"""

from __future__ import annotations

import os

from src.analysis.computer_resale_premium import (
    CORTES_DE_LA_PRIMA,
    ENV_POR_TRAMO,
    MIN_SAMPLES,
    medir_la_prima_por_tramo,
    prima_del_tramo,
)

from src.analysis.la_subasta import (
    _por_euro,
    candidatos_en_modo_cartera,
)


# Precios que caen en los cuatro tramos, para que la curva tenga
# de donde salir.
PRECIOS_CON_MASA = (
    [300_000] * 20
    + [2_000_000] * 20
    + [4_000_000] * 20
    + [8_000_000] * 20
)


# La misma reparticion, pero dejando el tramo de arriba con tres
# ventas: por debajo de `MIN_SAMPLES`.
PRECIOS_CON_UN_TRAMO_FLACO = (
    [300_000] * 20
    + [2_000_000] * 20
    + [4_000_000] * 20
    + [8_000_000] * 3
)


def _ventas(precios, prima_por_precio) -> tuple:
    """Eventos del tablon de mentira, con su buscador de precios."""

    eventos = []

    precio_de = {}

    for i, precio in enumerate(precios):

        pid = 9_000 + i

        precio_de[pid] = precio

        eventos.append({
            "event_id": f"f{i}",
            "date": 1_786_000_000 + i * 3_600,
            "type": "transfer",
            "content": [
                {
                    "player": pid,
                    "from": {"id": 14175949, "name": "Pepe"},
                    "amount": int(
                        precio * (1 + prima_por_precio(precio, i))
                    ),
                }
            ],
        })

    def price_at(player_id, _cuando):
        return precio_de.get(int(player_id), 0)

    return eventos, price_at


# Cada cuantas ventas sale una en rojo, por tramo. Abajo mas a
# menudo que arriba, como lo medido (73 % en verde abajo, 94 %
# arriba): asi la tasa de acierto tiene de donde salir distinta.
UNA_EN_ROJO_CADA = ((1_500_000, 3), (3_000_000, 4), (6_000_000, 6))


def _prima_de_mentira(precio, i=0) -> float:
    """Sube con el precio, como la medida, y falla a veces."""

    cada = 10

    base = 0.05

    for techo, salto in UNA_EN_ROJO_CADA:
        if precio < techo:
            cada = salto
            base = {1_500_000: 0.01, 3_000_000: 0.02,
                    6_000_000: 0.03}[techo]
            break

    if i % cada == 0:
        return -base

    return base


def _curva(precios=PRECIOS_CON_MASA) -> dict:
    eventos, price_at = _ventas(precios, _prima_de_mentira)

    return medir_la_prima_por_tramo(eventos, price_at)


def _dispersion(listos) -> float:
    """Cuanto se separan los rendimientos, en tanto por ciento."""

    ratios = sorted(_por_euro(c) for c in listos)

    if not ratios or ratios[-1] <= 0:
        return 0.0

    return 100.0 * (ratios[-1] - ratios[0]) / ratios[-1]


def _candidatos(precios) -> list:
    return [
        {"id": 100 + i, "name": f"P{p}", "market_price": p}
        for i, p in enumerate(precios)
    ]


# ============================================================
# 1. LA MUESTRA TIENE QUE ABARCAR TRAMOS
# ============================================================


def test_sin_varios_tramos_no_se_comprueba_nada() -> None:
    """Doctrina 24, aplicada a esta guardia."""

    curva = _curva()

    assert curva["available"], curva.get("reason")

    con_masa = [t for t in curva["tramos"] if t["calibrado"]]

    assert len(con_masa) >= 3, (
        f"la curva de prueba solo tiene {len(con_masa)} tramo(s) "
        f"calibrado(s): con menos de tres no se puede ver si la "
        f"prima distingue el tamaño"
    )

    # Y el caso que el dueño pidio: si todos los candidatos
    # cayeran en el mismo tramo, esto tiene que saltar.
    de_un_tramo = {
        prima_del_tramo(curva, p)["etiqueta"]
        for p in (300_000, 8_000_000)
    }

    assert len(de_un_tramo) == 2, (
        "los dos precios extremos caen en el mismo tramo: la "
        "guardia estaria comprobando una sola celda"
    )


# ============================================================
# 2. LA PRIMA VA POR TRAMO
# ============================================================


def test_la_prima_va_por_tramo() -> None:
    """
    LA PRUEBA QUE DA NOMBRE AL FICHERO.

    Dos candidatos de precio muy distinto no reciben la misma
    prima esperada.
    """

    curva = _curva()

    barata = prima_del_tramo(curva, 300_000)
    cara = prima_del_tramo(curva, 8_000_000)

    assert barata["percent"] is not None, barata["reason"]
    assert cara["percent"] is not None, cara["reason"]

    assert barata["percent"] != cara["percent"], (
        f"un jugador de 300.000 y uno de 8.000.000 reciben la "
        f"MISMA prima ({barata['percent']} %): la entrada sigue "
        f"siendo una constante (doctrina 98)"
    )

    assert cara["percent"] > barata["percent"], (
        f"la prima del tramo alto ({cara['percent']} %) no es "
        f"mayor que la del bajo ({barata['percent']} %): la "
        f"curva se ha dado la vuelta y eso hay que mirarlo antes "
        f"de fiarse"
    )


def test_con_la_curva_el_ratio_deja_de_ser_plano() -> None:
    """
    Lo que cierra el diagnostico: con la entrada dejando de ser
    constante, el rendimiento por euro deja de serlo.
    """

    curva = _curva()

    precios = (300_000, 2_000_000, 4_000_000, 8_000_000)

    candidatos = _candidatos(precios)

    antes = os.environ.get(ENV_POR_TRAMO)

    try:
        os.environ[ENV_POR_TRAMO] = "0"

        plana = candidatos_en_modo_cartera(
            candidatos, 0.0234, curva=curva
        )

        dispersion_plana = _dispersion(plana)

        # Lo medido sobre candidatos reales: 0,019 % y 0,034 %.
        assert dispersion_plana < 0.5, (
            f"con la prima plana el ratio ya se separa un "
            f"{dispersion_plana:.3f} %: el hallazgo del 20/09 se "
            f"ha quedado viejo y hay que volver a medirlo"
        )

        os.environ[ENV_POR_TRAMO] = "1"

        por_tramo = candidatos_en_modo_cartera(
            candidatos, 0.0234, curva=curva
        )

        dispersion_curva = _dispersion(por_tramo)

        assert dispersion_curva > 20.0, (
            f"con la curva puesta el ratio solo se separa un "
            f"{dispersion_curva:.3f} %: la curva no esta llegando "
            f"a `candidatos_en_modo_cartera`"
        )

        assert len({round(_por_euro(c), 4) for c in por_tramo})             == len(precios), (
                "un precio de cada tramo deberia dar un "
                "rendimiento distinto"
            )

    finally:

        if antes is None:
            os.environ.pop(ENV_POR_TRAMO, None)

        else:
            os.environ[ENV_POR_TRAMO] = antes


# ============================================================
# 3. UN TRAMO SIN MASA SE DECLARA
# ============================================================


def test_un_tramo_sin_masa_se_declara() -> None:
    """
    Un tramo por debajo de `MIN_SAMPLES` sale SIN CALIBRAR y usa
    la mediana global. Un numero inventado para un tramo vacio es
    peor que no tener tramos.
    """

    curva = _curva(PRECIOS_CON_UN_TRAMO_FLACO)

    flacos = [t for t in curva["tramos"] if not t["calibrado"]]

    # Doctrina 24: si el fixture no consigue un tramo flaco, esta
    # prueba no ha comprobado nada y lo dice.
    assert flacos, (
        f"todos los tramos tienen masa (>= {MIN_SAMPLES}): la "
        f"prueba no llega a ver el caso que vino a mirar. "
        f"Ajusta `PRECIOS_CON_UN_TRAMO_FLACO`"
    )

    for tramo in flacos:

        assert tramo["median_percent"] is None, (
            f"el tramo {tramo['etiqueta']} tiene "
            f"{tramo['n']} venta(s) y aun asi publica un numero "
            f"propio: {tramo['median_percent']} %"
        )

        assert "sin calibrar" in tramo["reason"].lower(), (
            f"el tramo {tramo['etiqueta']} no dice que esta sin "
            f"calibrar: {tramo['reason']}"
        )

    # Y quien lo use cae a la global, no a cero.
    alto = prima_del_tramo(curva, 8_000_000)

    assert alto["calibrado"] is False
    assert alto["percent"] == curva["global_percent"], (
        f"un tramo sin masa deberia usar la mediana global "
        f"({curva['global_percent']} %) y usa {alto['percent']}"
    )

    assert "global" in alto["reason"].lower(), alto["reason"]


def test_la_tasa_de_acierto_tambien_va_por_tramo() -> None:
    """
    77 % abajo y 94 % arriba no es el mismo numero, y hasta hoy
    se publicaba uno solo.
    """

    curva = _curva()

    ratios = {
        t["positive_ratio"]
        for t in curva["tramos"]
        if t["calibrado"]
    }

    assert len(ratios) >= 2, (
        f"la tasa de venta en verde sale igual en todos los "
        f"tramos ({ratios}): sigue siendo una sola"
    )

    assert curva["global_positive_ratio"] is not None, (
        "la curva no publica la tasa global"
    )


# ============================================================
# 4. APAGADO, NO CAMBIA NADA
# ============================================================


def test_apagado_se_comporta_como_ayer() -> None:
    """
    El interruptor entrega la curva APAGADA. Con el apagado, la
    prima que se aplica es la que entra por la puerta, sea cual
    sea la curva.
    """

    curva = _curva()

    candidatos = _candidatos((300_000, 8_000_000))

    antes = os.environ.get(ENV_POR_TRAMO)

    try:
        os.environ.pop(ENV_POR_TRAMO, None)

        sin_curva = candidatos_en_modo_cartera(candidatos, 0.0234)

        con_curva_apagada = candidatos_en_modo_cartera(
            candidatos, 0.0234, curva=curva
        )

        for a, b in zip(sin_curva, con_curva_apagada):

            assert a["expected_value"] == b["expected_value"], (
                f"pasar la curva con el interruptor apagado "
                f"cambia la ganancia de {a['name']}: "
                f"{a['expected_value']} -> {b['expected_value']}"
            )

            assert b["prima_aplicada_percent"] == 2.34, (
                f"apagado, la prima aplicada deberia ser la que "
                f"entra (2,34 %) y es "
                f"{b['prima_aplicada_percent']} %"
            )

    finally:

        if antes is None:
            os.environ.pop(ENV_POR_TRAMO, None)

        else:
            os.environ[ENV_POR_TRAMO] = antes


def test_los_cortes_son_los_de_la_casa() -> None:
    """
    1.500.000 y 3.000.000 son `CORTES_DE_PRECIO`, la rejilla que
    la pelea ya usa. Dos rejillas distintas para el mismo eje,
    multiplicandose en el mismo sitio, serian una arbitrariedad
    escondida.
    """

    from src.analysis.la_subasta import CORTES_DE_PRECIO

    for corte in CORTES_DE_PRECIO:

        assert corte in CORTES_DE_LA_PRIMA, (
            f"{corte:,} esta en la rejilla de la pelea y no en la "
            f"de la prima: las dos se multiplican en `_por_euro`"
        ).replace(",", ".")


def main() -> int:

    pruebas = [
        test_sin_varios_tramos_no_se_comprueba_nada,
        test_la_prima_va_por_tramo,
        test_con_la_curva_el_ratio_deja_de_ser_plano,
        test_un_tramo_sin_masa_se_declara,
        test_la_tasa_de_acierto_tambien_va_por_tramo,
        test_apagado_se_comporta_como_ayer,
        test_los_cortes_son_los_de_la_casa,
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
        f"LA PRIMA VA POR TRAMO V1: "
        f"{len(pruebas) - fallos}/{len(pruebas)} OK"
    )
    print("=" * 60)

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
