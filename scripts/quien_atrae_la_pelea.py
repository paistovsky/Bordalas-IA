"""
Que distingue a un jugador disputado de uno que nadie mira.

LA PREGUNTA (11/09/2026)

    Pepe entra en subasta disputada el 76 % de las veces. Pollo
    el 51 %. Prinzipote el 17 %.

    Cuando varios pujan a ciegas por el mismo jugador, el que
    gana suele ser el que mas se equivoco al valorarlo. Y hay una
    ironia en el diseño: la señal que nos hace fijarnos en
    alguien -que esta subiendo- es la misma que hace que los
    demas se fijen.

    Si algo predice la pelea, evitarla pasa a ser un objetivo del
    calculo y no un efecto secundario.

DE DONDE SALE

    De las 156 subastas del tablon, que traen la lista de pujas
    de cada una. La competencia no se estima: esta escrita.

    Los rasgos salen del historico de precios y del catalogo, los
    dos en disco.

NO DECIDE NADA

    Mide y publica. Esta noche no cambia como se eligen los
    objetivos.

COMO SE USA

    python -m scripts.quien_atrae_la_pelea
"""

from __future__ import annotations

import json
import statistics

from datetime import datetime
from pathlib import Path

from scripts.medir_la_subasta import (
    _historico_local,
    _venia_subiendo,
    cargar,
    precio_del_dia,
    subastas,
)


ESTADO = (
    Path(__file__).parent.parent
    / "diagnostico"
    / "status.json"
)


# Cuantas subastas hacen falta en un grupo para publicar su
# porcentaje. Por debajo se enseña el crudo y se dice que no
# llega: un 100 % de dos casos no es un 100 %.
MUESTRA_MINIMA = 12


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def _catalogo() -> dict:
    """
    El catalogo del ultimo snapshot que produccion publico.

    Aporta equipo y puntos. Si no esta, esos rasgos salen sin
    medir en vez de inventados.
    """

    try:
        estado = json.loads(
            ESTADO.read_text(encoding="utf-8")
        )

        # El escaparate y la plantilla traen fichas completas.
        fichas = {}

        for bloque, clave in (
            (estado.get("acquisition") or {}, "targets"),
            (estado.get("roster") or {}, "players"),
        ):
            for ficha in (bloque.get(clave) or []):
                if isinstance(ficha, dict) and ficha.get("id"):
                    fichas[int(ficha["id"])] = ficha

        return fichas

    except Exception:                               # noqa: BLE001
        return {}


def rasgos(subasta: dict, historico: dict, catalogo: dict) -> dict:
    """
    Los rasgos de un jugador el dia de su subasta.

    Forma fija: las mismas claves siempre, con `None` donde no
    se sabe. Nunca lanza.
    """

    salida = {
        "disputada": None,
        "precio": None,
        "subida": None,
        "subida_percent": None,
        "equipo": None,
        "puntos_temporada_pasada": None,
        "titular": None,
    }

    try:
        salida["disputada"] = bool(subasta.get("rivales"))

        precio = precio_del_dia(
            historico, subasta.get("jugador"), subasta.get("fecha")
        )

        salida["precio"] = precio

        subida = _venia_subiendo(
            historico, subasta.get("jugador"), subasta.get("fecha")
        )

        salida["subida"] = subida

        if precio and subida is not None:
            salida["subida_percent"] = round(
                100 * subida / precio, 3
            )

        ficha = catalogo.get(int(subasta.get("jugador") or 0))

        if ficha:
            salida["equipo"] = ficha.get("team") or ficha.get(
                "team_id"
            )
            salida["puntos_temporada_pasada"] = ficha.get(
                "points_last_season"
            ) or ficha.get("last_season_points")
            salida["titular"] = ficha.get(
                "starter_probability"
            )

        return salida

    except Exception:                               # noqa: BLE001
        return salida


def _comparar(nombre, disputadas, tranquilas, formato="{:.0f}"):
    """Una fila de la tabla: el rasgo en los dos grupos."""

    def resumen(valores):
        limpios = [v for v in valores if v is not None]

        if len(limpios) < MUESTRA_MINIMA:
            return f"n={len(limpios)}", None

        return (
            formato.format(statistics.median(limpios)),
            statistics.median(limpios),
        )

    izq, a = resumen(disputadas)
    der, b = resumen(tranquilas)

    if a is None or b is None:
        cociente = ""

    elif b == 0:
        cociente = "  (el otro es 0)"

    else:
        cociente = f"  x{a / b:.2f}"

    return f"  {nombre:<28}{izq:>14}{der:>14}{cociente}"


def main() -> None:

    eventos = cargar()

    if not eventos:
        print("Sin tablon en disco.")
        return

    historico = _historico_local()
    catalogo = _catalogo()

    ventas = subastas(eventos)

    medidas = [
        rasgos(v, historico, catalogo) for v in ventas
    ]

    disputadas = [m for m in medidas if m["disputada"]]
    tranquilas = [m for m in medidas if not m["disputada"]]

    print()
    print("=" * 74)
    print("QUE DISTINGUE A UN JUGADOR DISPUTADO")
    print("=" * 74)
    print()
    print(f"  Subastas: {len(ventas)}")
    print(
        f"    disputadas (algun rival): {len(disputadas)} "
        f"({100 * len(disputadas) / max(len(ventas), 1):.0f} %)"
    )
    print(f"    sin nadie mas:            {len(tranquilas)}")
    print(f"  Catalogo con fichas:        {len(catalogo)}")

    print()
    print(
        f"  {'RASGO (mediana)':<28}{'DISPUTADAS':>14}"
        f"{'TRANQUILAS':>14}"
    )
    print("  " + "-" * 60)

    print(
        _comparar(
            "precio",
            [m["precio"] for m in disputadas],
            [m["precio"] for m in tranquilas],
            "{:,.0f}",
        ).replace(",", ".")
    )

    print(
        _comparar(
            "subia el dia antes (EUR)",
            [m["subida"] for m in disputadas],
            [m["subida"] for m in tranquilas],
            "{:,.0f}",
        ).replace(",", ".")
    )

    print(
        _comparar(
            "subia el dia antes (%)",
            [m["subida_percent"] for m in disputadas],
            [m["subida_percent"] for m in tranquilas],
            "{:.3f}",
        )
    )

    print(
        _comparar(
            "puntos temporada pasada",
            [
                m["puntos_temporada_pasada"]
                for m in disputadas
            ],
            [
                m["puntos_temporada_pasada"]
                for m in tranquilas
            ],
        )
    )

    # ==========================================================
    # EL CORTE QUE MAS SEPARA
    # ==========================================================
    #
    #     Si el precio o la subida predicen la pelea, tiene que
    #     haber un corte donde el porcentaje de disputadas salte.
    #     Se prueban varios y se enseña la curva entera: un solo
    #     corte elegido a posteriori es una opinion con formato de
    #     dato.

    for etiqueta, clave, cortes, formato in (
        (
            "PRECIO",
            "precio",
            (300_000, 700_000, 1_500_000, 3_000_000, 6_000_000),
            "{:,.0f}",
        ),
        (
            "SUBIDA DEL DIA ANTES (%)",
            "subida_percent",
            (0.0, 0.25, 0.5, 1.0, 2.0),
            "{:.2f}",
        ),
    ):

        print()
        print("-" * 74)
        print(f"POR {etiqueta}")
        print("-" * 74)
        print()
        print(
            f"  {'TRAMO':<24}{'SUBASTAS':>10}"
            f"{'DISPUTADAS':>12}{'%':>8}"
        )
        print("  " + "-" * 54)

        con_dato = [
            m for m in medidas if m[clave] is not None
        ]

        bordes = [None, *cortes, None]

        for i in range(len(bordes) - 1):

            bajo, alto = bordes[i], bordes[i + 1]

            grupo = [
                m
                for m in con_dato
                if (bajo is None or m[clave] >= bajo)
                and (alto is None or m[clave] < alto)
            ]

            if not grupo:
                continue

            peleadas = sum(1 for m in grupo if m["disputada"])

            nombre = (
                f"< {formato.format(alto)}"
                if bajo is None
                else f">= {formato.format(bajo)}"
                if alto is None
                else f"{formato.format(bajo)} a "
                f"{formato.format(alto)}"
            ).replace(",", ".")

            porcentaje = (
                f"{100 * peleadas / len(grupo):.0f} %"
                if len(grupo) >= MUESTRA_MINIMA
                else "n<" + str(MUESTRA_MINIMA)
            )

            print(
                f"  {nombre:<24}{len(grupo):>10}"
                f"{peleadas:>12}{porcentaje:>8}"
            )

    print()
    print(
        f"  (los tramos con menos de {MUESTRA_MINIMA} subastas "
        f"no publican porcentaje)"
    )

    print()
    print("  No decide nada. Ni una llamada a Biwenger.")


if __name__ == "__main__":
    main()
