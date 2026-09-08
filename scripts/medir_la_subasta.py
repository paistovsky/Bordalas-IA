"""
Cuantos jugadores se llevan sin competencia, y cuanto cuesta ganar.

LA PREGUNTA DEL DUEÑO (10/09/2026)

    "Si yo no pujo nada, pero cinco minutos antes entro y le meto
     una puja, me lo puedo llevar. Imaginate ganar seis jugadores
     asi: al dia siguiente tienes 20k x 6 gratis."

    Ese numero dimensiona la idea entera. Si cada mañana hay seis
    jugadores que suben y nadie puja por ellos, esto es la liga.
    Si hay uno cada tres dias, es otra cosa.

DE DONDE SALE, Y POR QUE ES BUENO

    Del tablon de la liga, que ya esta en disco. Cada evento de
    tipo `market` es una subasta resuelta y trae LA LISTA DE
    PUJAS: quien pujo, cuanto, y quien se lo llevo.

    No hay que estimar la competencia: esta escrita.

NI UNA LLAMADA A BIWENGER

    Todo sale de `board_events.json`, que el ciclo ya guarda.

COMO SE USA

    python -m scripts.medir_la_subasta
"""

from __future__ import annotations

import json
import statistics

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


TABLON = (
    Path(__file__).parent.parent
    / "data"
    / "rival_intelligence"
    / "board_events.json"
)


# Cuando se considera que una compra se cerro "a precio de
# mercado". Biwenger mueve los precios en saltos de 10.000, asi
# que por debajo de esto la prima es ruido de redondeo y no una
# puja de verdad.
#
# No es un umbral de decision: solo sirve para contar. Ninguna
# maquina lee este numero.
PRIMA_QUE_ES_RUIDO = 0.005


def euros(valor) -> str:
    try:
        return f"{int(valor or 0):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def cargar(path: Path | None = None) -> list:
    """El tablon, o una lista vacia. Nunca lanza."""

    try:
        datos = json.loads(
            (path or TABLON).read_text(encoding="utf-8")
        )

        return datos if isinstance(datos, list) else []

    except Exception:                               # noqa: BLE001
        return []


def subastas(eventos: list | None) -> list:
    """
    Cada compra al Computer, con su competencia.

    `{fecha, jugador, comprador, pagado, rivales, mejor_rival}`.

    `rivales` son las OTRAS pujas: la del ganador no cuenta como
    competencia contra si mismo.
    """

    salida = []

    for evento in (eventos or []):

        if not isinstance(evento, dict):
            continue

        if evento.get("type") != "market":
            continue

        contenido = evento.get("content")

        trozos = (
            contenido
            if isinstance(contenido, list)
            else [contenido]
        )

        for trozo in trozos:

            if not isinstance(trozo, dict):
                continue

            comprador = trozo.get("to") or {}

            pujas = [
                p
                for p in (trozo.get("bids") or [])
                if isinstance(p, dict)
            ]

            ganador = comprador.get("id")

            rivales = [
                p
                for p in pujas
                if (p.get("user") or {}).get("id") != ganador
            ]

            salida.append({
                "fecha": evento.get("date"),
                "jugador": trozo.get("player"),
                "comprador": comprador.get("name"),
                "comprador_id": ganador,
                "pagado": trozo.get("amount"),
                "pujas": len(pujas),
                "rivales": len(rivales),
                "mejor_rival": max(
                    (
                        int(p.get("amount") or 0)
                        for p in rivales
                    ),
                    default=None,
                ),
            })

    return salida


def precio_del_dia(
    historico: dict | None,
    jugador,
    fecha,
):
    """
    El precio de mercado de ese jugador ESE DIA.

    Sin historico no se inventa: devuelve None y esa subasta
    queda fuera del reparto de primas en vez de ensuciarlo.
    """

    try:
        ficha = (historico or {}).get(str(jugador))

        if not ficha:
            return None

        dia = datetime.fromtimestamp(int(fecha)).date()

        mejor = None

        for marca, precio in zip(
            ficha.get("t") or [], ficha.get("p") or []
        ):

            cuando = datetime.fromtimestamp(marca).date()

            if cuando <= dia and (
                mejor is None or cuando > mejor[0]
            ):
                mejor = (cuando, precio)

        return mejor[1] if mejor else None

    except Exception:                               # noqa: BLE001
        return None


def main() -> None:

    eventos = cargar()

    if not eventos:
        print(
            "Sin tablon en disco: no hay subastas que medir."
        )
        return

    ventas = subastas(eventos)

    print()
    print("=" * 74)
    print("LA SUBASTA, MEDIDA SOBRE EL TABLON")
    print("=" * 74)
    print()

    fechas = [v["fecha"] for v in ventas if v["fecha"]]

    if fechas:
        print(
            f"  Ventana: "
            f"{datetime.fromtimestamp(min(fechas)):%d/%m/%Y} a "
            f"{datetime.fromtimestamp(max(fechas)):%d/%m/%Y}"
        )

    print(f"  Compras al Computer: {len(ventas)}")

    # ==========================================================
    # 0.1 — CUANTOS SIN COMPETENCIA
    # ==========================================================

    sin_rival = [v for v in ventas if v["rivales"] == 0]

    print()
    print("-" * 74)
    print("0.1  CUANTOS SE LLEVAN SIN COMPETENCIA")
    print("-" * 74)
    print()
    print(
        f"  SIN NINGUN RIVAL:  {len(sin_rival)} de "
        f"{len(ventas)} "
        f"({100 * len(sin_rival) / max(len(ventas), 1):.0f} %)"
    )

    reparto = Counter(v["rivales"] for v in ventas)

    print()
    print("  RIVALES   SUBASTAS")
    print("  " + "-" * 22)

    for rivales in sorted(reparto):
        print(f"  {rivales:>7}   {reparto[rivales]:>8}")

    if fechas:

        dias = max(
            1,
            (
                datetime.fromtimestamp(max(fechas)).date()
                - datetime.fromtimestamp(min(fechas)).date()
            ).days,
        )

        print()
        print(
            f"  Ritmo: {len(sin_rival) / dias:.2f} jugadores "
            f"sin competencia AL DIA "
            f"({len(sin_rival)} en {dias} dias)"
        )

    # ==========================================================
    # QUIEN PUJA, Y CUANTO PAGA DE MAS
    # ==========================================================

    print()
    print("-" * 74)
    print("EL REPARTO DE PRIMAS, POR COMPRADOR")
    print("-" * 74)

    historico = _historico_local()

    por_comprador = defaultdict(list)

    con_precio = 0

    for venta in ventas:

        mercado = precio_del_dia(
            historico, venta["jugador"], venta["fecha"]
        )

        if not mercado:
            continue

        con_precio += 1

        prima = (
            int(venta["pagado"] or 0) - int(mercado)
        ) / int(mercado)

        venta["prima"] = prima

        por_comprador[venta["comprador"]].append(venta)

    print()

    if not con_precio:
        print(
            "  Sin historico de precios local no se puede medir "
            "la prima.\n  Se mide la competencia igual, que es "
            "lo que decide."
        )

    else:

        print(
            f"  {'COMPRADOR':<32}{'COMPRAS':>8}"
            f"{'PRIMA MEDIANA':>15}{'SIN RIVAL':>11}"
        )
        print("  " + "-" * 68)

        for nombre, suyas in sorted(
            por_comprador.items(),
            key=lambda par: -len(par[1]),
        ):

            primas = [v["prima"] for v in suyas]

            limpias = sum(
                1 for v in suyas if v["rivales"] == 0
            )

            print(
                f"  {str(nombre)[:32]:<32}{len(suyas):>8}"
                f"{100 * statistics.median(primas):>14.2f} %"
                f"{limpias:>11}"
            )

        print()
        print(
            f"  (prima = pagado / precio de mercado de ese dia "
            f"- 1, sobre {con_precio} compras con historico)"
        )

    # ==========================================================
    # LOS QUE VALEN: SIN RIVAL Y SUBIENDO
    # ==========================================================

    print()
    print("-" * 74)
    print("Y DE LOS QUE NADIE PUJA, CUANTOS VENIAN SUBIENDO")
    print("-" * 74)

    subiendo = 0
    medibles = 0

    for venta in sin_rival:

        movimiento = _venia_subiendo(
            historico, venta["jugador"], venta["fecha"]
        )

        if movimiento is None:
            continue

        medibles += 1

        if movimiento > 0:
            subiendo += 1

    print()

    if not medibles:
        print(
            "  Sin historico local no se puede decir. Es la "
            "mitad que decide\n  si la idea vale: un jugador "
            "gratis que baja no es un regalo."
        )

    else:
        print(
            f"  De los {len(sin_rival)} sin competencia, "
            f"{medibles} tienen historico:"
        )
        print(
            f"    VENIAN SUBIENDO: {subiendo} "
            f"({100 * subiendo / medibles:.0f} %)"
        )
        print(f"    venian planos o bajando: {medibles - subiendo}")

        if fechas:
            print()
            print(
                f"    -> {subiendo / dias:.2f} jugadores AL DIA "
                f"sin competencia Y subiendo"
            )

    print()
    print("  Ni una llamada a Biwenger: todo del tablon en disco.")


def _historico_local() -> dict:
    """
    El almacen de precios del ciclo, si esta.

    Se lee con la forma del almacen -`{players: {id: {t, p}}}`-
    y si no esta, se sigue sin el: la competencia se mide igual.
    """

    try:
        from src.analysis.hold_backtest import STORE

        datos = json.loads(
            STORE.read_text(encoding="utf-8")
        )

        return (datos or {}).get("players") or {}

    except Exception:                               # noqa: BLE001
        return {}


def _venia_subiendo(historico, jugador, fecha):
    """
    El movimiento del precio el dia ANTES de la subasta.

    None si no hay dos precios que comparar. No se inventa: un
    jugador sin historico no cuenta ni a favor ni en contra.
    """

    try:
        ficha = (historico or {}).get(str(jugador))

        if not ficha:
            return None

        dia = datetime.fromtimestamp(int(fecha)).date()

        por_dia = {}

        for marca, precio in zip(
            ficha.get("t") or [], ficha.get("p") or []
        ):
            por_dia[
                datetime.fromtimestamp(marca).date()
            ] = precio

        anteriores = sorted(
            d for d in por_dia if d <= dia
        )

        if len(anteriores) < 2:
            return None

        return (
            por_dia[anteriores[-1]] - por_dia[anteriores[-2]]
        )

    except Exception:                               # noqa: BLE001
        return None


if __name__ == "__main__":
    main()
